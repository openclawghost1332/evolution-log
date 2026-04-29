import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts.cycle_audit import audit_workspace, main


class CycleAuditTests(unittest.TestCase):
    def _write_healthy_state(
        self,
        root: Path,
        *,
        source: str = "previews/work-scoring-helper",
        project_updated_at: str = "2026-04-28T22:47:20.000Z",
    ) -> None:
        state_dir = root / "status"
        state_dir.mkdir(exist_ok=True)
        (state_dir / "state.json").write_text(
            json.dumps(
                {
                    "currentCycle": None,
                    "lastCompletedCycle": {
                        "id": "20260429T034100Z-cycle-audit",
                        "summary": "Validated cycle state consistency.",
                        "artifact": "cycles/2026-04-29/20260429T034100Z-cycle-audit.md",
                        "completedAt": "2026-04-29T03:41:00Z",
                    },
                    "openBlockers": [],
                    "publishedProjects": [
                        {
                            "name": "work-scoring-helper",
                            "source": source,
                            "url": "https://example.com/work-scoring-helper",
                            "updatedAt": project_updated_at,
                        }
                    ],
                    "updatedAt": "2026-04-29T03:41:00Z",
                }
            ),
            encoding="utf-8",
        )

    def _write_healthy_cycle_files(self, root: Path) -> None:
        day_dir = root / "cycles" / "2026-04-29"
        day_dir.mkdir(parents=True)
        artifact = day_dir / "20260429T034100Z-cycle-audit.md"
        record = day_dir / "20260429T034100Z-cycle-audit.json"
        artifact.write_text("# Cycle Record\n", encoding="utf-8")
        record.write_text(
            json.dumps(
                {
                    "id": "20260429T034100Z-cycle-audit",
                    "timestamp": "2026-04-29T03:41:00Z",
                    "summary": "Validated cycle state consistency.",
                    "artifact": "cycles/2026-04-29/20260429T034100Z-cycle-audit.md",
                    "json": "cycles/2026-04-29/20260429T034100Z-cycle-audit.json",
                }
            ),
            encoding="utf-8",
        )

    def _write_preview_registry(
        self,
        root: Path,
        *,
        path: str = "previews/work-scoring-helper",
        updated_at: str = "2026-04-28T22:47:20.000Z",
    ) -> None:
        preview_dir = root / path
        preview_dir.mkdir(parents=True)
        registry_dir = root / "previews"
        registry_dir.mkdir(exist_ok=True)
        (registry_dir / "registry.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "previews": [
                        {
                            "slug": "work-scoring-helper",
                            "path": path,
                            "status": "ready",
                            "updatedAt": updated_at,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def test_audit_workspace_reports_healthy_cycle_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_healthy_cycle_files(root)
            self._write_healthy_state(root)
            self._write_preview_registry(root)

            report = audit_workspace(root)

        self.assertTrue(report["ok"])
        self.assertEqual(report["latestCycleId"], "20260429T034100Z-cycle-audit")
        self.assertEqual(report["checkedRecord"], "cycles/2026-04-29/20260429T034100Z-cycle-audit.json")
        self.assertEqual(report["stateSummary"], "Validated cycle state consistency.")
        self.assertEqual(report["previewCount"], 1)
        self.assertEqual(report["publishedProjectCount"], 1)
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
                        "publishedProjects": [],
                        "updatedAt": "2026-04-29T03:41:00Z",
                    }
                ),
                encoding="utf-8",
            )
            self._write_preview_registry(root)

            report = audit_workspace(root)

        self.assertFalse(report["ok"])
        self.assertIn("Missing status-referenced artifact", report["issues"][0])

    def test_audit_workspace_flags_state_and_record_field_mismatches(self):
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
                        "id": "20260429T034100Z-cycle-audit-record",
                        "timestamp": "2026-04-29T03:42:30+00:00",
                        "summary": "Record says something else.",
                        "artifact": "cycles/2026-04-29/20260429T034100Z-cycle-audit-renamed.md",
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
                            "summary": "Status summary wins.",
                            "artifact": "cycles/2026-04-29/20260429T034100Z-cycle-audit.md",
                            "completedAt": "2026-04-29T03:41:00Z",
                        },
                        "openBlockers": [],
                        "publishedProjects": [],
                        "updatedAt": "2026-04-29T03:41:00Z",
                    }
                ),
                encoding="utf-8",
            )
            self._write_preview_registry(root)

            report = audit_workspace(root)

        self.assertFalse(report["ok"])
        self.assertIn(
            "lastCompletedCycle.id does not match sibling cycle json id",
            report["issues"],
        )
        self.assertIn(
            "lastCompletedCycle.artifact does not match sibling cycle json artifact",
            report["issues"],
        )
        self.assertIn(
            "lastCompletedCycle.summary does not match sibling cycle json summary",
            report["issues"],
        )
        self.assertIn(
            "lastCompletedCycle.completedAt does not match sibling cycle json timestamp",
            report["issues"],
        )

    def test_audit_workspace_flags_invalid_sibling_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            day_dir = root / "cycles" / "2026-04-29"
            day_dir.mkdir(parents=True)
            artifact = day_dir / "20260429T034100Z-cycle-audit.md"
            record = day_dir / "20260429T034100Z-cycle-audit.json"
            artifact.write_text("# Cycle Record\n", encoding="utf-8")
            record.write_text("{not valid json", encoding="utf-8")
            state_dir = root / "status"
            state_dir.mkdir()
            (state_dir / "state.json").write_text(
                json.dumps(
                    {
                        "currentCycle": None,
                        "lastCompletedCycle": {
                            "id": "20260429T034100Z-cycle-audit",
                            "summary": "Status summary wins.",
                            "artifact": "cycles/2026-04-29/20260429T034100Z-cycle-audit.md",
                            "completedAt": "2026-04-29T03:41:00Z",
                        },
                        "openBlockers": [],
                        "publishedProjects": [],
                        "updatedAt": "2026-04-29T03:41:00Z",
                    }
                ),
                encoding="utf-8",
            )
            self._write_preview_registry(root)

            report = audit_workspace(root)

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["issues"],
            ["Invalid sibling cycle json: cycles/2026-04-29/20260429T034100Z-cycle-audit.json"],
        )

    def test_audit_workspace_flags_missing_registered_preview_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_healthy_cycle_files(root)
            self._write_healthy_state(root)
            registry_dir = root / "previews"
            registry_dir.mkdir(exist_ok=True)
            (registry_dir / "registry.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "previews": [
                            {
                                "slug": "work-scoring-helper",
                                "status": "ready",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = audit_workspace(root)

        self.assertFalse(report["ok"])
        self.assertIn("Preview entry missing path: work-scoring-helper", report["issues"])

    def test_audit_workspace_flags_unregistered_published_project_source(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_healthy_cycle_files(root)
            self._write_healthy_state(root, source="previews/not-registered")
            self._write_preview_registry(root)

            report = audit_workspace(root)

        self.assertFalse(report["ok"])
        self.assertIn(
            "Published project source is not registered in previews/registry.json: previews/not-registered",
            report["issues"],
        )

    def test_audit_workspace_flags_invalid_preview_registry_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_healthy_cycle_files(root)
            self._write_healthy_state(root)
            registry_dir = root / "previews"
            registry_dir.mkdir(exist_ok=True)
            (registry_dir / "registry.json").write_text("{not valid json", encoding="utf-8")

            report = audit_workspace(root)

        self.assertFalse(report["ok"])
        self.assertIn("Invalid preview registry json: previews/registry.json", report["issues"])

    def test_audit_workspace_flags_preview_timestamp_drift(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_healthy_cycle_files(root)
            self._write_healthy_state(root, project_updated_at="2026-04-29T07:45:44Z")
            registry_dir = root / "previews"
            registry_dir.mkdir(exist_ok=True)
            (root / "previews" / "work-scoring-helper").mkdir(parents=True, exist_ok=True)
            (registry_dir / "registry.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "previews": [
                            {
                                "slug": "work-scoring-helper",
                                "path": "previews/work-scoring-helper",
                                "status": "ready",
                                "updatedAt": "2026-04-28T22:47:20.000Z",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = audit_workspace(root)

        self.assertFalse(report["ok"])
        self.assertIn(
            "Preview registry metadata is stale for work-scoring-helper: previews/registry.json updatedAt does not match status/state.json publishedProjects updatedAt",
            report["issues"],
        )

    def test_audit_workspace_repairs_preview_timestamp_drift_when_requested(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_healthy_cycle_files(root)
            self._write_healthy_state(root, project_updated_at="2026-04-29T07:45:44Z")
            self._write_preview_registry(root, updated_at="2026-04-28T22:47:20.000Z")

            report = audit_workspace(root, repair_preview_registry=True)
            registry = json.loads((root / "previews" / "registry.json").read_text(encoding="utf-8"))

        self.assertTrue(report["ok"])
        self.assertEqual(report["repairedPreviewCount"], 1)
        self.assertEqual(registry["previews"][0]["updatedAt"], "2026-04-29T07:45:44Z")
        self.assertEqual(report["issues"], [])

    def test_audit_workspace_reports_zero_repairs_without_matching_drift(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_healthy_cycle_files(root)
            self._write_healthy_state(root)
            self._write_preview_registry(root)

            report = audit_workspace(root, repair_preview_registry=True)

        self.assertTrue(report["ok"])
        self.assertEqual(report["repairedPreviewCount"], 0)
        self.assertEqual(report["issues"], [])

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
                        "publishedProjects": [],
                        "updatedAt": "2026-04-29T03:41:00Z",
                    }
                ),
                encoding="utf-8",
            )
            self._write_preview_registry(root)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", tmpdir])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["ok"])
        self.assertGreaterEqual(len(payload["issues"]), 1)


if __name__ == "__main__":
    unittest.main()
