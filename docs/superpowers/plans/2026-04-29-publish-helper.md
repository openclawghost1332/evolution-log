# Publish Helper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a small helper CLI that verifies quarantine is off and runs the publish guard for one or more artifact paths.

**Architecture:** Keep the new behavior in a dedicated `scripts/publish_helper.py` module with a tiny CLI. It will call the existing control status command, parse its JSON, then run `scripts/publish_guard.py` as a subprocess. Tests cover pure helper behavior and CLI exit codes. Documentation updates point future cycles at the wrapper instead of the raw multi-command checklist.

**Tech Stack:** Python 3 standard library, unittest, subprocess, pathlib

---

## File Structure
- Create: `scripts/publish_helper.py` for quarantine-aware publish readiness checks.
- Create: `tests/test_publish_helper.py` for unit and CLI tests.
- Modify: `README.md` to document the helper.
- Modify: `AGENTS.md` and `TOOLS.md` to recommend the helper as the default pre-publish command.

### Task 1: Add failing tests for publish helper behavior

**Files:**
- Create: `tests/test_publish_helper.py`
- Test: `tests/test_publish_helper.py`

- [ ] **Step 1: Write the failing tests**

```python
import contextlib
import io
import json
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_publish_helper -v`
Expected: FAIL with `ModuleNotFoundError` or missing `publish_helper` attributes.

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PublishCheckResult:
    exit_code: int
    message: str


def _read_control_status() -> dict:
    return {}


def check_publish_ready(paths: list[Path]) -> PublishCheckResult:
    return PublishCheckResult(1, "not implemented")


def main(argv: list[str] | None = None) -> int:
    return 0
```

- [ ] **Step 4: Run test to verify it still fails for the right reasons**

Run: `python3 -m unittest tests.test_publish_helper -v`
Expected: FAIL on assertions about quarantine, missing path, subprocess invocation, and printed output.

- [ ] **Step 5: Commit**

```bash
git add tests/test_publish_helper.py scripts/publish_helper.py
git commit -m "test: scaffold publish helper coverage"
```

### Task 2: Implement publish helper logic until tests pass

**Files:**
- Modify: `scripts/publish_helper.py`
- Test: `tests/test_publish_helper.py`

- [ ] **Step 1: Make the quarantine test pass**

```python
def check_publish_ready(paths: list[Path]) -> PublishCheckResult:
    status = _read_control_status()
    if status.get("quarantine"):
        return PublishCheckResult(1, "publish_helper: blocked, quarantine is active")
    return PublishCheckResult(1, "publish_helper: paths not checked")
```

- [ ] **Step 2: Run the single test**

Run: `python3 -m unittest tests.test_publish_helper.PublishHelperTests.test_check_publish_ready_blocks_when_quarantine_is_active -v`
Expected: PASS

- [ ] **Step 3: Make the missing-path test pass**

```python
def check_publish_ready(paths: list[Path]) -> PublishCheckResult:
    status = _read_control_status()
    if status.get("quarantine"):
        return PublishCheckResult(1, "publish_helper: blocked, quarantine is active")

    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        return PublishCheckResult(1, f"publish_helper: missing paths: {', '.join(missing)}")

    return PublishCheckResult(1, "publish_helper: guard not run")
```

- [ ] **Step 4: Run the missing-path test**

Run: `python3 -m unittest tests.test_publish_helper.PublishHelperTests.test_check_publish_ready_reports_missing_artifact_paths -v`
Expected: PASS

- [ ] **Step 5: Make the guard-run and CLI tests pass**

```python
import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

CONTROL_STATUS_COMMAND = ["node", "/opt/openclaw-evolution/bin/control.mjs", "status"]
PUBLISH_GUARD_COMMAND = [sys.executable, "scripts/publish_guard.py"]


def _read_control_status() -> dict:
    completed = subprocess.run(
        CONTROL_STATUS_COMMAND,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def check_publish_ready(paths: list[Path]) -> PublishCheckResult:
    status = _read_control_status()
    if status.get("quarantine"):
        return PublishCheckResult(1, "publish_helper: blocked, quarantine is active")

    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        return PublishCheckResult(1, f"publish_helper: missing paths: {', '.join(missing)}")

    completed = subprocess.run(
        [*PUBLISH_GUARD_COMMAND, *[str(path) for path in paths]],
        capture_output=True,
        text=True,
    )
    output = completed.stdout.strip() or completed.stderr.strip() or "publish_helper: no output"
    return PublishCheckResult(completed.returncode, output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run quarantine and publish guard checks before publishing.")
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    result = check_publish_ready([Path(path) for path in args.paths])
    print(result.message)
    return result.exit_code
```

- [ ] **Step 6: Run all publish helper tests**

Run: `python3 -m unittest tests.test_publish_helper -v`
Expected: PASS

- [ ] **Step 7: Refactor for clearer error messages and subprocess failures while keeping tests green**

```python
try:
    status = _read_control_status()
except RuntimeError as exc:
    return PublishCheckResult(1, f"publish_helper: unable to read control status: {exc}")
```

- [ ] **Step 8: Re-run tests**

Run: `python3 -m unittest tests.test_publish_helper -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add scripts/publish_helper.py tests/test_publish_helper.py
git commit -m "feat: add publish helper"
```

### Task 3: Document the new helper and verify the full test suite

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `TOOLS.md`
- Test: `tests/test_publish_helper.py`
- Test: `tests/test_cycle_record.py`
- Test: `tests/test_cycle_audit.py`

- [ ] **Step 1: Update docs to use the helper**

```md
## Publish helper

Run the quarantine check and publish guard together before public publishing:

```bash
python3 scripts/publish_helper.py previews/work-scoring-helper
```
```

- [ ] **Step 2: Run focused tests**

Run: `python3 -m unittest tests.test_publish_helper tests.test_cycle_record tests.test_cycle_audit -v`
Expected: PASS

- [ ] **Step 3: Smoke-test the helper against a real artifact**

Run: `python3 scripts/publish_helper.py previews/work-scoring-helper`
Expected: `publish_guard: OK`

- [ ] **Step 4: Commit**

```bash
git add README.md AGENTS.md TOOLS.md scripts/publish_helper.py tests/test_publish_helper.py
git commit -m "docs: wire publish helper into lab workflow"
```
