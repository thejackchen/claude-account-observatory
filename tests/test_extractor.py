"""Synthetic fixtures only. Never reads a participant's ~/.claude directory."""
from datetime import date, datetime, timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/claude-study-extract.py"
spec = importlib.util.spec_from_file_location("extractor", SCRIPT)
extractor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extractor)


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.logs = Path(self.temp.name) / "projects"
        self.logs.mkdir()
        self.anchor = date(2026, 10, 1)

    def row(self, day, key, hour=3):
        return {"type": "assistant", "requestId": key, "uuid": "row-" + key,
                "timestamp": datetime.combine(day, datetime.min.time()).replace(hour=hour).isoformat(),
                "version": "2.1.284", "message": {"id": key, "model": "claude-synthetic-test",
                "content": "SYNTHETIC_PRIVATE_MARKER email@example.invalid 192.0.2.1"}}

    def write(self, rows, name="session.jsonl"):
        (self.logs / name).write_text("\n".join(json.dumps(row) for row in rows) + "\n")

    def test_window_stream_dedup_and_private_content(self):
        start = self.anchor - timedelta(days=14)
        rows = [self.row(start, str(i)) for i in range(99)]
        duplicate = dict(rows[0], uuid="different-stream-chunk")
        rows += [duplicate, self.row(start - timedelta(days=1), "before"), self.row(self.anchor, "after")]
        self.write(rows)
        self.write(rows[:5], "copy.jsonl")
        result = extractor.extract(self.logs, self.anchor)
        self.assertEqual(result["metrics"]["responses_bucket"], "1_99")
        self.assertEqual(result["metrics"]["active_days_bucket"], "1_3")
        text = json.dumps(result)
        for forbidden in ("SYNTHETIC_PRIVATE_MARKER", "example.invalid", "192.0.2.1", str(self.logs), "requestId", "uuid"):
            self.assertNotIn(forbidden, text)
        self.assertFalse(result["consent_aggregate"])
        self.assertEqual(result["window_complete"], "unknown")

    def test_synthetic_responses_and_errors_are_separate(self):
        rows = []
        for i in range(10):
            row = self.row(self.anchor - timedelta(days=1), str(i))
            row["message"]["model"] = "<synthetic>"
            row["isApiErrorMessage"] = True
            rows.append(row)
        self.write(rows)
        result = extractor.extract(self.logs, self.anchor)
        self.assertEqual(result["metrics"]["responses_bucket"], "0")
        self.assertEqual(result["metrics"]["error_events_bucket"], "10_99")

    def test_missing_logs_are_unknown(self):
        result = extractor.extract(self.logs / "absent", self.anchor)
        self.assertEqual(result["metrics"]["log_coverage"], "no_logs")
        for key, value in result["metrics"].items():
            if key != "log_coverage": self.assertEqual(value, "unknown")
        self.assertEqual(result["provenance"], {"protocol_version": "1.0.0", "prompt_version": "not_used", "extractor_version": "1.0.0", "skill_version": "not_used"})

    def test_skill_entrypoint_flags_and_exclusive_output(self):
        output = Path(self.temp.name) / "result.json"
        command = [sys.executable, str(SCRIPT), "--root", str(self.logs), "--anchor", self.anchor.isoformat(),
                   "--output", str(output), "--prompt-version", "1.0.0", "--skill-version", "1.0.0"]
        run = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(output.read_text())
        self.assertEqual(result["provenance"]["skill_version"], "1.0.0")
        self.assertEqual(result["provenance"]["prompt_version"], "1.0.0")
        original = output.read_bytes()
        retry = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(retry.returncode, 2)
        self.assertEqual(output.read_bytes(), original)

    def test_result_fields_match_public_schema(self):
        result = extractor.extract(self.logs, self.anchor)
        schema = json.loads((ROOT / "study-schema.json").read_text())
        self.assertEqual(set(result), set(schema["required"]))
        self.assertFalse(schema["additionalProperties"])
        for name in ("metrics", "provenance"):
            nested = schema["properties"][name]
            self.assertEqual(set(result[name]), set(nested["required"]))
            self.assertFalse(nested["additionalProperties"])
            for key, value in result[name].items():
                enum = nested["properties"][key].get("enum")
                if enum is not None: self.assertIn(value, enum)

    def test_released_artifacts_match_manifest(self):
        manifest = json.loads((ROOT / "versions.json").read_text())
        self.assertEqual(manifest["release"], "v1.0.0")
        for artifact in manifest["artifacts"]:
            path = (ROOT / artifact["path"]).resolve()
            self.assertTrue(path.is_relative_to(ROOT.resolve()))
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), artifact["sha256"], artifact["path"])


if __name__ == "__main__":
    unittest.main()
