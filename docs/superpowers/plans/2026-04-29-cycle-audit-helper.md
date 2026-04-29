# Cycle Audit Helper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a small audit CLI that checks cycle artifact and `status/state.json` consistency so future evolution cycles can catch drift fast.

**Architecture:** Add a focused Python helper that loads `status/state.json`, validates the referenced cycle artifact paths, inspects the latest cycle JSON record, and prints a small machine-readable summary. Keep logic in a single script with a few pure helper functions so unittest coverage can exercise drift cases cheaply.

**Tech Stack:** Python 3, `argparse`, `json`, `pathlib`, `unittest`

---

### Task 1: Add failing audit tests and implement the helper

**Files:**
- Create: `scripts/cycle_audit.py`
- Create: `tests/test_cycle_audit.py`
- Modify: `README.md`
- Test: `tests/test_cycle_audit.py`

- [ ] **Step 1: Write the failing test**

```python
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
            record.write_text(json.dumps({
                "id": "20260429T034100Z-cycle-audit",
                "artifact": "cycles/2026-04-29/20260429T034100Z-cycle-audit.md",
                "json": "cycles/2026-04-29/20260429T034100Z-cycle-audit.json"
            }), encoding="utf-8")
            state_dir = root / "status"
            state_dir.mkdir()
            (state_dir / "state.json").write_text(json.dumps({
                "currentCycle": None,
                "lastCompletedCycle": {
                    "id": "20260429T034100Z-cycle-audit",
                    "artifact": "cycles/2026-04-29/20260429T034100Z-cycle-audit.md",
                    "completedAt": "2026-04-29T03:41:00Z"
                },
                "openBlockers": [],
                "updatedAt": "2026-04-29T03:41:00Z"
            }), encoding="utf-8")

            report = audit_workspace(root)

        self.assertTrue(report["ok"])
        self.assertEqual(report["latestCycleId"], "20260429T034100Z-cycle-audit")
        self.assertEqual(report["issues"], [])

    def test_audit_workspace_flags_missing_state_artifact(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "status").mkdir()
            (root / "status" / "state.json").write_text(json.dumps({
                "currentCycle": None,
                "lastCompletedCycle": {
                    "id": "missing-cycle",
                    "artifact": "cycles/2026-04-29/missing-cycle.md",
                    "completedAt": "2026-04-29T03:41:00Z"
                },
                "openBlockers": [],
                "updatedAt": "2026-04-29T03:41:00Z"
            }), encoding="utf-8")

            report = audit_workspace(root)

        self.assertFalse(report["ok"])
        self.assertIn("Missing status-referenced artifact", report["issues"][0])

    def test_main_prints_json_and_nonzero_exit_on_issues(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "status").mkdir()
            (root / "status" / "state.json").write_text(json.dumps({
                "currentCycle": None,
                "lastCompletedCycle": None,
                "openBlockers": [],
                "updatedAt": "2026-04-29T03:41:00Z"
            }), encoding="utf-8")
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--root", tmpdir])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertFalse(payload["ok"])
        self.assertGreaterEqual(len(payload["issues"]), 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_cycle_audit -v`
Expected: FAIL with `ModuleNotFoundError` or missing `audit_workspace` / `main` imports.

- [ ] **Step 3: Write minimal implementation**

```python
import argparse
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_workspace(root: Path) -> dict[str, Any]:
    state = _read_json(root / "status" / "state.json")
    issues: list[str] = []
    last_completed = state.get("lastCompletedCycle")
    latest_cycle_id = None

    if not last_completed:
        issues.append("status/state.json has no lastCompletedCycle entry")
    else:
        latest_cycle_id = last_completed.get("id")
        artifact_rel = last_completed.get("artifact")
        if not artifact_rel or not (root / artifact_rel).exists():
            issues.append(f"Missing status-referenced artifact: {artifact_rel}")

        json_rel = None
        if artifact_rel and artifact_rel.endswith(".md"):
            json_rel = artifact_rel[:-3] + ".json"
            if not (root / json_rel).exists():
                issues.append(f"Missing sibling cycle json: {json_rel}")

    return {
        "ok": not issues,
        "latestCycleId": latest_cycle_id,
        "issues": issues,
        "updatedAt": state.get("updatedAt"),
        "openBlockerCount": len(state.get("openBlockers", [])),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    report = audit_workspace(Path(args.root))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_cycle_audit -v`
Expected: PASS for all three audit tests.

- [ ] **Step 5: Document usage**

```markdown
## Cycle audit helper

Validate that `status/state.json` points at real cycle artifacts and report basic drift signals.

```bash
python3 scripts/cycle_audit.py --root .
```
```

- [ ] **Step 6: Run the focused tests again**

Run: `python3 -m unittest tests.test_cycle_audit tests.test_cycle_record -v`
Expected: PASS with pristine output.

- [ ] **Step 7: Commit**

```bash
git add README.md scripts/cycle_audit.py tests/test_cycle_audit.py
git commit -m "feat: add cycle audit helper"
```

## Self-review

- Spec coverage: covers healthy state, missing artifact drift, and CLI exit behavior.
- Placeholder scan: no TODO/TBD markers remain.
- Type consistency: `audit_workspace()` returns `ok`, `latestCycleId`, `issues`, `updatedAt`, and `openBlockerCount`; tests and CLI use the same keys.
