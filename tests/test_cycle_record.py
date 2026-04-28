import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts.cycle_record import main, write_cycle_record


class CycleRecordTests(unittest.TestCase):
    def test_write_cycle_record_creates_markdown_and_json_pair(self):
        payload = {
            "id": "20260428T234100Z-cycle-record-helper",
            "timestamp": "2026-04-28T23:41:00Z",
            "summary": "Ship a helper for consistent cycle notes.",
            "changes": ["Added a cycle record helper script."],
            "artifacts": ["scripts/cycle_record.py", "tests/test_cycle_record.py"],
            "blockers": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            result = write_cycle_record(payload, Path(tmpdir))
            markdown = Path(tmpdir, result["artifact"]).read_text()
            machine = json.loads(Path(tmpdir, result["json"]).read_text())

        self.assertIn("# Cycle Record", markdown)
        self.assertIn("Ship a helper for consistent cycle notes.", markdown)
        self.assertEqual(machine["artifact"], result["artifact"])

    def test_write_cycle_record_renders_placeholders_for_empty_lists(self):
        payload = {
            "id": "20260428T234100Z-cycle-record-helper",
            "timestamp": "2026-04-28T23:41:00Z",
            "summary": "Ship a helper for consistent cycle notes.",
            "changes": [],
            "artifacts": [],
            "blockers": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            result = write_cycle_record(payload, Path(tmpdir))
            markdown = Path(tmpdir, result["artifact"]).read_text()

        self.assertIn("## Changes\n- None.", markdown)
        self.assertIn("## Artifacts\n- None.", markdown)
        self.assertIn("## Blockers\n- None.", markdown)

    def test_write_cycle_record_rejects_missing_required_keys(self):
        payload = {
            "timestamp": "2026-04-28T23:41:00Z",
            "summary": "Ship a helper for consistent cycle notes.",
            "changes": ["Added a cycle record helper script."],
            "artifacts": ["scripts/cycle_record.py"],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(ValueError, "Missing required field: id"):
                write_cycle_record(payload, Path(tmpdir))

    def test_write_cycle_record_rejects_bad_timestamp_without_writing_files(self):
        payload = {
            "id": "20260428T234100Z-cycle-record-helper",
            "timestamp": "not-a-timestamp",
            "summary": "Ship a helper for consistent cycle notes.",
            "changes": ["Added a cycle record helper script."],
            "artifacts": ["scripts/cycle_record.py"],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with self.assertRaisesRegex(ValueError, "Invalid timestamp: not-a-timestamp"):
                write_cycle_record(payload, root)

            self.assertFalse(any(root.rglob("*.md")))
            self.assertFalse(any(root.rglob("*.json")))

    def test_main_reads_input_file_and_writes_records(self):
        payload = {
            "id": "20260428T234100Z-cycle-record-helper",
            "timestamp": "2026-04-28T23:41:00Z",
            "summary": "Ship a helper for consistent cycle notes.",
            "changes": ["Added a cycle record helper script."],
            "artifacts": ["scripts/cycle_record.py", "tests/test_cycle_record.py"],
            "blockers": [],
            "notes": ["Ready for future cron reuse."],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir, "payload.json")
            input_path.write_text(json.dumps(payload))
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--input", str(input_path), "--root", tmpdir])

            self.assertEqual(exit_code, 0)
            output = json.loads(stdout.getvalue())
            self.assertTrue(Path(tmpdir, output["artifact"]).exists())
            self.assertTrue(Path(tmpdir, output["json"]).exists())


if __name__ == "__main__":
    unittest.main()
