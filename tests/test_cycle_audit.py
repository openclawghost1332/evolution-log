import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts.cycle_audit import audit_workspace, main


class CycleAuditTests(unittest.TestCase):
    def test_audit_workspace_reports_healthy_cycle_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            day_dir = root / "cycles" / "2026-04-29"
            day_dir.mkdir(parents=True)
            artifact = day_dir / "20260429T034100Z-cycle-audit.md"
            record = day_dir / "20260429T034100Z-cycle-audit.json"
            artifact.write_text("# Cycle Record\n", encoding="utf-8")
            record.write_text(
                json.dumps(
                    {
                        "id": "20260429T034100Z-cycle-audit",
                        "artifact": "cycles/2026-04-29/20260429T034100Z-cycle-audit.md",
                        "json": "cycles/2026-04-29/20260429T034100Z-cycle-audit.json",
                    }
                ),
                encoding="utf-8",
            )
            state_dir = root / "status"
            state_dir.mkdir()
            (state_dir / "state.json").write_text(
                json.dumps(
                    {
                        "currentCycle": None,
                        "lastCompletedCycle": {
                            "id": "20260429T034100Z-cycle-audit",
                            "artifact": "cycles/2026-04-29/20260429T034100Z-cycle-audit.md",
                            "completedAt": "2026-04-29T03:41:00Z",
                        },
                        "openBlockers": [],
                        "updatedAt": "2026-04-29T03:41:00Z",
                    }
                ),
                encoding="utf-8",
            )

            report = audit_workspace(root)

        self.assertTrue(report["ok"])
        self.assertEqual(report["latestCycleId"], "20260429T034100Z-cycle-audit")
        self.assertEqual(report["issues"], [])

    def test_audit_workspace_flags_missing_state_artifact(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "status").mkdir()
            (root / "status" / "state.json").write_text(
                json.dumps(
                    {
                        "currentCycle": None,
                        "lastCompletedCycle": {
                            "id": "missing-cycle",
                            "artifact": "cycles/2026-04-29/missing-cycle.md",
                            "completedAt": "2026-04-29T03:41:00Z",
                        },
                        "openBlockers": [],
                        "updatedAt": "2026-04-29T03:41:00Z",
                    }
                ),
                encoding="utf-8",
            )

            report = audit_workspace(root)

        self.assertFalse(report["ok"])
        self.assertIn("Missing status-referenced artifact", report["issues"][0])

    def test_main_prints_json_and_nonzero_exit_on_issues(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "status").mkdir()
            (root / "status" / "state.json").write_text(
                json.dumps(
                    {
                        "currentCycle": None,
                        "lastCompletedCycle": None,
                        "openBlockers": [],
                        "updatedAt": "2026-04-29T03:41:00Z",
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", tmpdir])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["ok"])
        self.assertGreaterEqual(len(payload["issues"]), 1)


if __name__ == "__main__":
    unittest.main()
