# Cycle Record Helper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tiny local CLI that generates paired cycle markdown and JSON artifacts from one payload.

**Architecture:** Use a single dependency-free Python module in `scripts/` with a thin CLI wrapper and pure helper functions for validation, normalization, markdown rendering, and file output. Cover the behavior with Python `unittest` tests that drive implementation through failing tests first.

**Tech Stack:** Python 3 standard library, `unittest`, JSON, filesystem writes

---

### Task 1: Add failing tests for normalized record generation

**Files:**
- Create: `tests/test_cycle_record.py`
- Test: `tests/test_cycle_record.py`

- [ ] **Step 1: Write the failing test**

```python
import json
import tempfile
import unittest
from pathlib import Path

from scripts.cycle_record import write_cycle_record


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_cycle_record -v`
Expected: FAIL with `ModuleNotFoundError` or missing `write_cycle_record`

- [ ] **Step 3: Write minimal implementation**

```python
# create scripts/cycle_record.py with write_cycle_record(payload, root)
# returning {"artifact": "...md", "json": "...json"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_cycle_record -v`
Expected: PASS for `test_write_cycle_record_creates_markdown_and_json_pair`

- [ ] **Step 5: Commit**

```bash
git add tests/test_cycle_record.py scripts/cycle_record.py
git commit -m "feat: add cycle record helper"
```

### Task 2: Add validation and optional-section tests

**Files:**
- Modify: `tests/test_cycle_record.py`
- Modify: `scripts/cycle_record.py`
- Test: `tests/test_cycle_record.py`

- [ ] **Step 1: Write the failing tests**

```python
    def test_write_cycle_record_renders_none_for_empty_blockers(self):
        ...

    def test_write_cycle_record_rejects_missing_required_keys(self):
        ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_cycle_record -v`
Expected: FAIL because empty blockers and validation are not implemented yet

- [ ] **Step 3: Write minimal implementation**

```python
# validate id, timestamp, summary, changes, artifacts
# render "- None." when blockers is empty
# raise ValueError("Missing required field: ...") for missing keys
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_cycle_record -v`
Expected: PASS for all tests

- [ ] **Step 5: Commit**

```bash
git add tests/test_cycle_record.py scripts/cycle_record.py
git commit -m "test: cover cycle record validation"
```

### Task 3: Add CLI entrypoint and documentation

**Files:**
- Modify: `scripts/cycle_record.py`
- Modify: `README.md`
- Test: `tests/test_cycle_record.py`

- [ ] **Step 1: Write the failing test**

```python
    def test_main_reads_input_file_and_writes_records(self):
        ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_cycle_record -v`
Expected: FAIL because `main()` does not parse `--input`

- [ ] **Step 3: Write minimal implementation**

```python
# add argparse CLI supporting --input and optional --root
# document usage in README.md
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_cycle_record -v`
Expected: PASS for all tests

- [ ] **Step 5: Commit**

```bash
git add scripts/cycle_record.py tests/test_cycle_record.py README.md
git commit -m "docs: document cycle record helper"
```
