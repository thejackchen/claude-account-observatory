#!/usr/bin/env python3
"""Offline Claude observation metadata extractor. Python 3 standard library only.

Reads JSONL metadata; never sends network requests or outputs conversation content.
See 统一提取提示词.txt for scope, limits, and manual review instructions.
"""

import argparse
from collections import Counter
from datetime import date, datetime, timedelta
import gzip
import json
import os
from pathlib import Path
import re
import sys


SCHEMA_VERSION = "1.1"
PROTOCOL_VERSION = "1.0.0"
EXTRACTOR_VERSION = "1.0.0"
PROMPT_VERSIONS = ("1.0.0", "not_used", "unknown")
SKILL_VERSION = "1.0.0"
SKILL_VERSIONS = (SKILL_VERSION, "not_used", "unknown")

REPORTED = (
    "status", "notice_category", "physical_region", "exit_region",
    "window_complete", "recruitment", "network_kind", "account_origin",
    "plan", "payment", "gift_card", "credential_use", "client",
    "client_integrity", "automation", "prior_warning", "appeal",
    "other_accounts_in_study",
)
VERSION = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,5}$")


def parse_time(value):
    """Convert recorded time to the computer's current local timezone."""
    try:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            seconds = value / 1000 if value > 100000000000 else value
            return datetime.fromtimestamp(seconds).astimezone()
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone()
    except (ValueError, OverflowError, OSError):
        pass
    return None


def jsonl_files(root, routing=False):
    """Do not follow symlinks or inspect configuration/credential files."""
    def allowed(path):
        name = path.name
        return (name.startswith("routing") and
                (name.endswith(".jsonl") or name.endswith(".jsonl.gz"))) if routing else name.endswith(".jsonl")

    if root.is_symlink():
        return
    if root.is_file():
        if allowed(root):
            yield root
        return
    if not root.is_dir():
        return
    for folder, directories, filenames in os.walk(root, followlinks=False):
        directories[:] = sorted(name for name in directories if not Path(folder, name).is_symlink())
        for name in sorted(filenames):
            path = Path(folder, name)
            if allowed(path) and not path.is_symlink():
                yield path


def records(path, scan_state):
    opener = gzip.open if path.name.endswith(".gz") else open
    try:
        with opener(path, "rt", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except (ValueError, RecursionError):
                    scan_state["incomplete"] = True
                    continue
                if isinstance(record, dict):
                    yield line_number, record
    except (OSError, UnicodeError, EOFError):
        # Never echo an exception: it could expose source paths or raw text.
        scan_state["incomplete"] = True


def bucket(number, limits):
    if number == 0:
        return "0"
    for maximum, label in limits:
        if maximum is None or number <= maximum:
            return label
    raise ValueError("invalid bucket definition")


def response_key(record, message, fallback):
    # Request/message IDs group stream chunks; UUID also identifies retained copies.
    for value in (record.get("requestId"), message.get("id"), record.get("uuid")):
        if isinstance(value, str) and value:
            return value
    return fallback


def extract(root, anchor, gateway_root=None, prompt_version="not_used", skill_version="not_used"):
    # Prompt provenance is the participant's declaration, not verified execution.
    if prompt_version not in PROMPT_VERSIONS:
        raise ValueError("unregistered prompt version")
    if skill_version not in SKILL_VERSIONS:
        raise ValueError("unregistered skill version")
    start = anchor - timedelta(days=14)
    normal = {}
    errors = set()
    versions = []
    state = {"incomplete": False}
    has_metadata = False
    for file_number, path in enumerate(jsonl_files(root)):
        for line_number, record in records(path, state):
            time = parse_time(record.get("timestamp"))
            if time is None:
                continue
            has_metadata = True
            if not start <= time.date() < anchor:
                continue
            version = record.get("version")
            if isinstance(version, str) and VERSION.fullmatch(version):
                versions.append((time, version))
            message = record.get("message")
            if not isinstance(message, dict):
                message = {}
            key = response_key(record, message, (file_number, line_number))
            error = (record.get("isApiErrorMessage") is True or
                     record.get("type") == "api_error" or
                     (record.get("type") == "system" and record.get("subtype") == "api_error"))
            if error:
                errors.add(key)
                continue
            if record.get("type") != "assistant" or message.get("model") == "<synthetic>":
                continue
            # Earliest timestamp makes counts independent of retained-copy ordering.
            if key not in normal or time < normal[key]:
                normal[key] = time

    metrics = {key: "unknown" for key in (
        "responses_bucket", "peak_daily_bucket", "active_days_bucket",
        "overnight_days_bucket", "error_events_bucket", "cli_version",
        "gateway_claude_activity",
    )}
    metrics["log_coverage"] = "retained_logs" if has_metadata else "no_logs"
    if has_metadata:
        daily = Counter(time.date() for time in normal.values())
        overnight = {time.date() for time in normal.values() if time.hour < 6}
        days_limits = [(3, "1_3"), (7, "4_7"), (None, "8_14")]
        metrics.update({
            "responses_bucket": bucket(len(normal), [(99, "1_99"), (999, "100_999"), (9999, "1000_9999"), (None, "10000_plus")]),
            "peak_daily_bucket": bucket(max(daily.values(), default=0), [(99, "1_99"), (999, "100_999"), (None, "1000_plus")]),
            "active_days_bucket": bucket(len(daily), days_limits),
            "overnight_days_bucket": bucket(len(overnight), days_limits),
            "error_events_bucket": bucket(len(errors), [(9, "1_9"), (99, "10_99"), (None, "100_plus")]),
            "cli_version": max(versions, key=lambda item: item[0])[1] if versions else "unknown",
        })
    if state["incomplete"] and has_metadata:
        metrics["log_coverage"] = "partial"

    if gateway_root is not None:
        gateway_state = {"incomplete": False}
        for path in jsonl_files(gateway_root, routing=True):
            for _, record in records(path, gateway_state):
                provider = record.get("provider")
                time = parse_time(record.get("time", record.get("timestamp", record.get("ts"))))
                if (isinstance(provider, str) and provider.lower() == "claude" and
                        time is not None and start <= time.date() < anchor):
                    metrics["gateway_claude_activity"] = "yes"
                    break
            if metrics["gateway_claude_activity"] == "yes":
                break
        # Absence of retained rows cannot establish absence of intermediary use.

    result = {field: "unknown" for field in REPORTED}
    result.update({"schema_version": SCHEMA_VERSION, "provider": "claude",
                   "anchor_month": anchor.strftime("%Y-%m"), "window_days": 14,
                   "source": "local_script", "metrics": metrics,
                   "provenance": {"protocol_version": PROTOCOL_VERSION,
                                  "prompt_version": prompt_version,
                                  "extractor_version": EXTRACTOR_VERSION,
                                  "skill_version": skill_version},
                   "consent_aggregate": False})
    return result


def main():
    parser = argparse.ArgumentParser(description="只读统计本机留存 Claude 日志；不联网、不上传、不输出聊天文本。")
    parser.add_argument("--anchor", help="首次受限日 YYYY-MM-DD；默认本机今天（不统计当天）")
    parser.add_argument("--output", required=True, help="本人核对用的结果 JSON 文件（不能覆盖已有文件）")
    parser.add_argument("--root", default=str(Path.home() / ".claude" / "projects"), help="只读项目日志目录")
    parser.add_argument("--gateway-routing", help="可选：只读 Magpie routing 日志目录")
    parser.add_argument("--prompt-version", choices=PROMPT_VERSIONS, default="not_used", help="参与者声明提示词版本；未使用为 not_used，不确定或未注册改版为 unknown；不会验证执行过程")
    parser.add_argument("--skill-version", choices=SKILL_VERSIONS, default="not_used", help="参与者声明 Skill 版本；未使用为 not_used，不确定或未注册改版为 unknown；不会验证执行过程")
    args = parser.parse_args()
    try:
        anchor = date.fromisoformat(args.anchor) if args.anchor else date.today()
    except ValueError:
        parser.exit(2, "日期格式不正确，请使用 YYYY-MM-DD。\n")
    root = Path(args.root).expanduser()
    output = Path(args.output).expanduser()
    if output.suffix.lower() != ".json":
        parser.exit(2, "输出文件必须是 .json，请不要选择原始日志文件。\n")
    try:
        gateway = Path(args.gateway_routing).expanduser() if args.gateway_routing else None
        result = extract(root, anchor, gateway, args.prompt_version, args.skill_version)
        # Exclusive create prevents overwriting user data; 0600 protects local result.
        descriptor = os.open(str(output), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except (OSError, ValueError):
        parser.exit(2, "未能写入结果。请选一个未存在、可写的 .json 文件；原始日志未修改。\n")
    print("已生成本机核对结果：" + str(output.resolve()))
    print("只含分桶指标和未知人工字段；未联网、未上传。请本人预览、核对后在网页导入。")
    print("不能自动区分多个账号或证明日志完整；混合账号请选对应日志目录或标注不完整。")
    print("提示词与 Skill 版本仅由参与者声明，不证明执行过程；请核对版本来源。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("已停止；没有上传任何数据。")
