---
name: claude-account-observatory
description: 为 Claude 账号受限观察站在本机生成可预览的脱敏研究结果，适用于参与者请求整理自己的留存使用指标和方法版本。只生成本机结果，不上传原始聊天，不判断封禁原因。
---

# Claude 账号受限观察站 · 本机参与 Skill

Skill 1.0.0，调用提示词 1.0.0、提取器 1.0.0，遵循协议 1.0.0 和结果格式 1.1。完整 Skill 目录包含本文件、`tools/`、`study-schema.json`、`protocol-v1.0.0.txt` 与 `versions.json`；只复制本文件不能完成提取。

## 生成一份可核对的结果

先阅读 [统一说明与固定提示词](tools/统一提取提示词.txt)。版本/字段有疑问时查 [研究协议](protocol-v1.0.0.txt) 和 [严格结果格式](study-schema.json)。文件指纹见 [发布清单](versions.json)；校验只说明下载内容一致，不验证本人经历或工具实际运行。

明确用户希望参与的账号与窗口：正常组为最近14个完整本机日，期间未受限、有实际使用；受限/恢复组为第一次受限日之前14个完整本机日，排除当天。首次受限日让用户在本机输入，不要求粘贴聊天或凭据。用户已经给出窗口/目录时直接使用，不重复询问。

在用户选定的本机输出目录运行随 Skill 提供的固定脚本，脚本路径相对 Skill 根目录解析；输出选尚不存在的文件。仅用已有 Python 3 标准库，不安装软件/依赖，不改认证、代理、系统或工具配置。

```sh
# 正常组（ROOT 是实际 Skill 根目录；OUTPUT 是用户的本机输出文件）
python3 "$ROOT/tools/claude-study-extract.py" --prompt-version 1.0.0 --skill-version 1.0.0 --output "$OUTPUT"

# 受限/恢复组，DATE 由用户在本机确定
python3 "$ROOT/tools/claude-study-extract.py" --anchor "$DATE" --prompt-version 1.0.0 --skill-version 1.0.0 --output "$OUTPUT"
```

上面的变量是说明占位符，不要原样执行；使用真实本机绝对路径和用户选择的日期。默认只读 `~/.claude/projects` 元数据；用户选择其他目录则加 `--root`。可选路由统计只有用户选择该资料时加 `--gateway-routing`，不要自动探查网关/认证配置。多账号无法分离时保留未知，不把全机日志标为单账号完整窗。

只让固定脚本读取元数据。不要用助手工具逐行读取/总结原始聊天，也不要把日志内容放入云模型、调试输出或其他服务。不得修改计数规则、补猜字段、猜测封禁原因或生成风险分。设置、登录文件、密钥/凭据不在范围内。

结果的人工字段保持 `unknown`、`consent_aggregate=false`。提醒本人核对并补充事实；没有日志不能当作零，使用量只是留存记录统计。版本标识表示来源声明，不能说已验证用户确实用了某模型/提示词。

运行失败时只报告不含路径/原文/凭据的错误类别，保留原始文件，不覆盖结果、不自动上传重试。没有 Python 或没有可分离日志时，用户可以在网页手动填已确认事实。

## 交付与本人提交

交付本机结果文件位置、实际组件版本、哪些类别包含在结果中、哪些事实仍未知。可以读取刚生成的严格结果 JSON 做本机预览，不读取原始资料进行二次分析。用户自行到[观察站](https://account-restriction-observatory.jackchen815.chatgpt.site)导入、核对、授权提交；本 Skill 不发送结果、不自动勾选授权，也不代填邀请码或操作管理回执。

提示参与者保存独立结果与回执。聊天、账号、截图、邀请码、回执和真实个人结果不进入 GitHub。需要提出方法问题时仅使用合成样例。

## 社区改进

[GitHub 正本](https://github.com/thejackchen/claude-account-observatory)接受 Fork、Issue 和 PR。发布版固定，修改提示词/Skill/脚本须新版本；未登记的改写版用 `unknown`，不能沿用未修改的官方版本声明。第一次发布前后代码/文档使用 MIT，参与记录另受研究授权约束。
