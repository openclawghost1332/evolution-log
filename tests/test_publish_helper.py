import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import publish_helper


class PublishHelperTests(unittest.TestCase):
    def test_check_publish_ready_blocks_when_quarantine_is_active(self):
        with mock.patch("scripts.publish_helper._read_control_status", return_value={"quarantine": True}):
            result = publish_helper.check_publish_ready([Path("previews/demo")])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("quarantine is active", result.message)

    def test_check_publish_ready_reports_missing_artifact_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            missing = root / "missing"
            with mock.patch("scripts.publish_helper._read_control_status", return_value={"quarantine": False}):
                result = publish_helper.check_publish_ready([missing])

        self.assertEqual(result.exit_code, 1)
        self.assertIn(str(missing), result.message)

    def test_check_publish_ready_runs_publish_guard_for_existing_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            artifact = root / "artifact.txt"
            artifact.write_text("safe\n", encoding="utf-8")
            completed = mock.Mock(returncode=0, stdout="publish_guard: OK\n", stderr="")
            with mock.patch("scripts.publish_helper._read_control_status", return_value={"quarantine": False}):
                with mock.patch("subprocess.run", return_value=completed) as run_mock:
                    result = publish_helper.check_publish_ready([artifact])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("publish_guard: OK", result.message)
        run_mock.assert_called_once()

    def test_main_prints_message_and_returns_guard_exit_code(self):
        with mock.patch("scripts.publish_helper.check_publish_ready") as check_mock:
            check_mock.return_value = publish_helper.PublishCheckResult(3, "guard failed")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = publish_helper.main(["previews/demo"])

        self.assertEqual(exit_code, 3)
        self.assertEqual(stdout.getvalue().strip(), "guard failed")


if __name__ == "__main__":
    unittest.main()
