import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_write_cycle_record_includes_git_metadata_in_json_and_markdown(self):
        payload = {
            "id": "20260428T234100Z-cycle-record-helper",
            "timestamp": "2026-04-28T23:41:00Z",
            "summary": "Ship a helper for consistent cycle notes.",
            "changes": ["Added a cycle record helper script."],
            "artifacts": ["scripts/cycle_record.py", "tests/test_cycle_record.py"],
            "blockers": [],
            "metadata": {"source": "cron"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True, capture_output=True)
            tracked = root / "tracked.txt"
            tracked.write_text("tracked\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=root, check=True, capture_output=True)
            tracked.write_text("tracked and dirty\n", encoding="utf-8")

            result = write_cycle_record(payload, root)
            markdown = Path(root, result["artifact"]).read_text(encoding="utf-8")
            machine = json.loads(Path(root, result["json"]).read_text(encoding="utf-8"))

        self.assertEqual(machine["metadata"]["source"], "cron")
        self.assertIn("git", machine["metadata"])
        self.assertRegex(machine["metadata"]["git"]["head"], r"^[0-9a-f]{40}$")
        self.assertTrue(machine["metadata"]["git"]["dirty"])
        self.assertIn("## Details", markdown)
        self.assertIn("- source: cron", markdown)
        self.assertIn("- git.head:", markdown)
        self.assertIn("- git.dirty: true", markdown)

    def test_write_cycle_record_gracefully_skips_git_metadata_when_git_unavailable(self):
        payload = {
            "id": "20260428T234100Z-cycle-record-helper",
            "timestamp": "2026-04-28T23:41:00Z",
            "summary": "Ship a helper for consistent cycle notes.",
            "changes": ["Added a cycle record helper script."],
            "artifacts": ["scripts/cycle_record.py"],
            "blockers": [],
            "metadata": {"source": "cron"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch("subprocess.run", side_effect=FileNotFoundError):
                result = write_cycle_record(payload, Path(tmpdir))

            markdown = Path(tmpdir, result["artifact"]).read_text(encoding="utf-8")
            machine = json.loads(Path(tmpdir, result["json"]).read_text(encoding="utf-8"))

        self.assertEqual(machine["metadata"], {"source": "cron"})
        self.assertIn("## Details", markdown)
        self.assertIn("- source: cron", markdown)
        self.assertNotIn("git.head", markdown)
        self.assertNotIn("git.dirty", markdown)

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

    def test_write_cycle_record_updates_state_in_started_mode(self):
        payload = {
            "id": "20260428T234100Z-cycle-record-helper",
            "timestamp": "2026-04-28T23:41:00Z",
            "summary": "Ship a helper for consistent cycle notes.",
            "changes": ["Added a cycle record helper script."],
            "artifacts": ["scripts/cycle_record.py", "tests/test_cycle_record.py"],
            "blockers": ["Waiting on review."],
        }
        initial_state = {
            "currentCycle": None,
            "lastCompletedCycle": {"id": "older"},
            "openBlockers": ["Keep existing blockers."],
            "updatedAt": "2026-04-28T00:00:00Z",
            "focus": {"mode": "ship"},
            "quarantine": {"active": False},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            state_path = root / "status" / "state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(initial_state), encoding="utf-8")

            write_cycle_record(payload, root, state_path=Path("status/state.json"), state_mode="started")
            state = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(
            state["currentCycle"],
            {
                "id": payload["id"],
                "summary": payload["summary"],
                "artifact": "cycles/2026-04-28/20260428T234100Z-cycle-record-helper.md",
                "startedAt": "2026-04-28T23:41:00Z",
            },
        )
        self.assertEqual(state["lastCompletedCycle"], {"id": "older"})
        self.assertEqual(state["openBlockers"], ["Keep existing blockers."])
        self.assertEqual(state["updatedAt"], "2026-04-28T23:41:00Z")
        self.assertEqual(state["focus"], {"mode": "ship"})
        self.assertEqual(state["quarantine"], {"active": False})

    def test_write_cycle_record_updates_state_in_completed_mode(self):
        payload = {
            "id": "20260428T234100Z-cycle-record-helper",
            "timestamp": "2026-04-28T23:41:00Z",
            "summary": "Ship a helper for consistent cycle notes.",
            "changes": ["Added a cycle record helper script."],
            "artifacts": ["scripts/cycle_record.py", "tests/test_cycle_record.py"],
            "blockers": ["Waiting on publish guard."],
        }
        initial_state = {
            "currentCycle": {"id": "in-flight"},
            "lastCompletedCycle": {"id": "older"},
            "openBlockers": ["Keep existing blockers."],
            "updatedAt": "2026-04-28T00:00:00Z",
            "github": {"org": "openclawghost1332"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            state_path = root / "status" / "state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(initial_state), encoding="utf-8")

            write_cycle_record(payload, root, state_path=Path("status/state.json"), state_mode="completed")
            state = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(state["currentCycle"], None)
        self.assertEqual(
            state["lastCompletedCycle"],
            {
                "id": payload["id"],
                "summary": payload["summary"],
                "artifact": "cycles/2026-04-28/20260428T234100Z-cycle-record-helper.md",
                "completedAt": "2026-04-28T23:41:00Z",
            },
        )
        self.assertEqual(state["openBlockers"], payload["blockers"])
        self.assertEqual(state["updatedAt"], "2026-04-28T23:41:00Z")
        self.assertEqual(state["github"], {"org": "openclawghost1332"})

    def test_write_cycle_record_renders_incidents_only_when_provided(self):
        payload = {
            "id": "20260429T124100Z-cycle-record-incident-sync",
            "timestamp": "2026-04-29T12:41:00Z",
            "summary": "Sync incidents through the cycle record helper.",
            "changes": ["Added incident sync support."],
            "artifacts": ["scripts/cycle_record.py", "tests/test_cycle_record.py"],
            "blockers": [],
            "incidents": ["Preview registry drift detected and repaired."],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            result = write_cycle_record(payload, Path(tmpdir))
            markdown = Path(tmpdir, result["artifact"]).read_text(encoding="utf-8")
            machine = json.loads(Path(tmpdir, result["json"]).read_text(encoding="utf-8"))

        self.assertIn("## Incidents", markdown)
        self.assertIn("Preview registry drift detected and repaired.", markdown)
        self.assertEqual(machine["incidents"], payload["incidents"])

    def test_write_cycle_record_completed_mode_updates_incidents_when_provided(self):
        payload = {
            "id": "20260429T124100Z-cycle-record-incident-sync",
            "timestamp": "2026-04-29T12:41:00Z",
            "summary": "Sync incidents through the cycle record helper.",
            "changes": ["Added incident sync support."],
            "artifacts": ["scripts/cycle_record.py", "tests/test_cycle_record.py"],
            "blockers": [],
            "incidents": ["Preview registry drift detected and repaired."],
        }
        initial_state = {
            "currentCycle": {"id": "in-flight"},
            "lastCompletedCycle": {"id": "older"},
            "openBlockers": [],
            "incidents": ["Older incident."],
            "updatedAt": "2026-04-29T00:00:00Z",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            state_path = root / "status" / "state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(initial_state), encoding="utf-8")

            write_cycle_record(payload, root, state_path=Path("status/state.json"), state_mode="completed")
            state = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(state["incidents"], payload["incidents"])

    def test_write_cycle_record_completed_mode_preserves_incidents_when_omitted(self):
        payload = {
            "id": "20260429T124100Z-cycle-record-incident-sync",
            "timestamp": "2026-04-29T12:41:00Z",
            "summary": "Do not overwrite incidents when none are provided.",
            "changes": ["Guarded incident sync behind explicit payload data."],
            "artifacts": ["scripts/cycle_record.py", "tests/test_cycle_record.py"],
            "blockers": [],
        }
        initial_state = {
            "currentCycle": {"id": "in-flight"},
            "lastCompletedCycle": {"id": "older"},
            "openBlockers": [],
            "incidents": ["Older incident."],
            "updatedAt": "2026-04-29T00:00:00Z",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            state_path = root / "status" / "state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(initial_state), encoding="utf-8")

            write_cycle_record(payload, root, state_path=Path("status/state.json"), state_mode="completed")
            state = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(state["incidents"], ["Older incident."])

    def test_write_cycle_record_completed_mode_syncs_matching_preview_registry_timestamp(self):
        payload = {
            "id": "20260429T094100Z-cycle-record-preview-sync",
            "timestamp": "2026-04-29T09:41:00Z",
            "summary": "Sync preview metadata during completed cycle recording.",
            "changes": ["Added preview registry sync to cycle record helper."],
            "artifacts": ["scripts/cycle_record.py", "tests/test_cycle_record.py"],
            "blockers": [],
        }
        initial_state = {
            "currentCycle": {"id": "in-flight"},
            "lastCompletedCycle": {"id": "older"},
            "openBlockers": [],
            "updatedAt": "2026-04-29T00:00:00Z",
            "publishedProjects": [
                {
                    "name": "work-scoring-helper",
                    "source": "previews/work-scoring-helper",
                    "updatedAt": "2026-04-29T09:30:00Z",
                }
            ],
        }
        initial_registry = {
            "previews": [
                {
                    "slug": "work-scoring-helper",
                    "path": "previews/work-scoring-helper",
                    "updatedAt": "2026-04-29T07:45:44Z",
                    "title": "OpenClaw Work Scoring Helper",
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            state_path = root / "status" / "state.json"
            registry_path = root / "previews" / "registry.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(initial_state), encoding="utf-8")
            registry_path.write_text(json.dumps(initial_registry), encoding="utf-8")

            write_cycle_record(payload, root, state_path=Path("status/state.json"), state_mode="completed")

            registry = json.loads(registry_path.read_text(encoding="utf-8"))

        self.assertEqual(
            registry["previews"][0]["updatedAt"],
            "2026-04-29T09:30:00Z",
        )

    def test_write_cycle_record_completed_mode_upserts_published_project_from_metadata(self):
        payload = {
            "id": "20260429T104100Z-cycle-record-project-sync",
            "timestamp": "2026-04-29T10:41:00Z",
            "summary": "Sync published project metadata during completed cycle recording.",
            "changes": ["Added published project upsert to cycle record helper."],
            "artifacts": ["scripts/cycle_record.py", "tests/test_cycle_record.py"],
            "blockers": [],
            "metadata": {
                "publishedProject": {
                    "name": "work-scoring-helper",
                    "url": "https://github.com/openclawghost1332/work-scoring-helper",
                    "source": "previews/work-scoring-helper",
                    "updatedAt": "2026-04-29T10:41:00Z",
                }
            },
        }
        initial_state = {
            "currentCycle": {"id": "in-flight"},
            "lastCompletedCycle": {"id": "older"},
            "openBlockers": [],
            "updatedAt": "2026-04-29T00:00:00Z",
            "publishedProjects": [
                {
                    "name": "work-scoring-helper",
                    "source": "previews/work-scoring-helper",
                    "updatedAt": "2026-04-29T09:30:00Z",
                }
            ],
        }
        initial_registry = {
            "previews": [
                {
                    "slug": "work-scoring-helper",
                    "path": "previews/work-scoring-helper",
                    "updatedAt": "2026-04-29T07:45:44Z",
                    "title": "OpenClaw Work Scoring Helper",
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            state_path = root / "status" / "state.json"
            registry_path = root / "previews" / "registry.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(initial_state), encoding="utf-8")
            registry_path.write_text(json.dumps(initial_registry), encoding="utf-8")

            write_cycle_record(payload, root, state_path=Path("status/state.json"), state_mode="completed")

            state = json.loads(state_path.read_text(encoding="utf-8"))
            registry = json.loads(registry_path.read_text(encoding="utf-8"))

        self.assertEqual(
            state["publishedProjects"][0],
            {
                "name": "work-scoring-helper",
                "url": "https://github.com/openclawghost1332/work-scoring-helper",
                "source": "previews/work-scoring-helper",
                "updatedAt": "2026-04-29T10:41:00Z",
            },
        )
        self.assertEqual(registry["previews"][0]["updatedAt"], "2026-04-29T10:41:00Z")

    def test_write_cycle_record_started_mode_does_not_upsert_published_project_from_metadata(self):
        payload = {
            "id": "20260429T104100Z-cycle-record-project-sync",
            "timestamp": "2026-04-29T10:41:00Z",
            "summary": "Do not mutate published project metadata on cycle start.",
            "changes": ["Guarded published project sync to completed mode only."],
            "artifacts": ["scripts/cycle_record.py", "tests/test_cycle_record.py"],
            "blockers": [],
            "metadata": {
                "publishedProject": {
                    "name": "work-scoring-helper",
                    "url": "https://github.com/openclawghost1332/work-scoring-helper",
                    "source": "previews/work-scoring-helper",
                    "updatedAt": "2026-04-29T10:41:00Z",
                }
            },
        }
        initial_state = {
            "currentCycle": None,
            "lastCompletedCycle": {"id": "older"},
            "openBlockers": [],
            "updatedAt": "2026-04-28T00:00:00Z",
            "publishedProjects": [
                {
                    "name": "work-scoring-helper",
                    "source": "previews/work-scoring-helper",
                    "updatedAt": "2026-04-29T09:30:00Z",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            state_path = root / "status" / "state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(initial_state), encoding="utf-8")

            write_cycle_record(payload, root, state_path=Path("status/state.json"), state_mode="started")
            state = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(state["currentCycle"]["id"], payload["id"])
        self.assertEqual(
            state["publishedProjects"],
            [
                {
                    "name": "work-scoring-helper",
                    "source": "previews/work-scoring-helper",
                    "updatedAt": "2026-04-29T09:30:00Z",
                }
            ],
        )

    def test_write_cycle_record_started_mode_does_not_require_preview_registry(self):
        payload = {
            "id": "20260428T234100Z-cycle-record-helper",
            "timestamp": "2026-04-28T23:41:00Z",
            "summary": "Ship a helper for consistent cycle notes.",
            "changes": ["Added a cycle record helper script."],
            "artifacts": ["scripts/cycle_record.py", "tests/test_cycle_record.py"],
            "blockers": [],
        }
        initial_state = {
            "currentCycle": None,
            "lastCompletedCycle": {"id": "older"},
            "openBlockers": [],
            "updatedAt": "2026-04-28T00:00:00Z",
            "publishedProjects": [
                {
                    "name": "work-scoring-helper",
                    "source": "previews/work-scoring-helper",
                    "updatedAt": "2026-04-29T09:30:00Z",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            state_path = root / "status" / "state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(initial_state), encoding="utf-8")

            write_cycle_record(payload, root, state_path=Path("status/state.json"), state_mode="started")
            state = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(state["currentCycle"]["id"], payload["id"])

    def test_main_rejects_state_mode_without_state_path(self):
        payload = {
            "id": "20260428T234100Z-cycle-record-helper",
            "timestamp": "2026-04-28T23:41:00Z",
            "summary": "Ship a helper for consistent cycle notes.",
            "changes": ["Added a cycle record helper script."],
            "artifacts": ["scripts/cycle_record.py", "tests/test_cycle_record.py"],
            "blockers": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir, "payload.json")
            input_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "--state-mode requires --state"):
                main(["--input", str(input_path), "--root", tmpdir, "--state-mode", "started"])

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
