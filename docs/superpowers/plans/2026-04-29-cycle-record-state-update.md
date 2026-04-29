# Cycle Record State Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let `scripts/cycle_record.py` optionally update `status/state.json` in explicit `started` and `completed` modes while preserving the existing state document shape.

**Architecture:** Keep record generation unchanged by default, then add a focused state-update helper that mutates only the documented cycle fields after a successful record write. Drive the change through CLI flags and unit tests so both direct function use and command-line usage stay predictable.

**Tech Stack:** Python 3, `argparse`, `json`, `pathlib`, `unittest`

---

### Task 1: Add failing tests for state update behavior

**Files:**
- Modify: `tests/test_cycle_record.py`
- Test: `tests/test_cycle_record.py`

- [ ] **Step 1: Write the failing tests**

```python
    def test_write_cycle_record_updates_state_in_started_mode(self):
        ...

    def test_write_cycle_record_updates_state_in_completed_mode(self):
        ...

    def test_main_rejects_state_mode_without_state_path(self):
        ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_updates_state_in_started_mode tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_updates_state_in_completed_mode tests.test_cycle_record.CycleRecordTests.test_main_rejects_state_mode_without_state_path -v`
Expected: FAIL because `write_cycle_record()` has no state update support and the CLI does not validate the new flags.

- [ ] **Step 3: Write minimal implementation**

```python
# extend write_cycle_record(..., state_path=None, state_mode=None)
# add _update_state_file(...) for started/completed
# add argparse flags for --state and --state-mode
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_updates_state_in_started_mode tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_updates_state_in_completed_mode tests.test_cycle_record.CycleRecordTests.test_main_rejects_state_mode_without_state_path -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_cycle_record.py scripts/cycle_record.py
git commit -m "feat: add cycle record state update modes"
```

### Task 2: Verify full helper behavior and document the CLI

**Files:**
- Modify: `scripts/cycle_record.py`
- Modify: `README.md`
- Test: `tests/test_cycle_record.py`

- [ ] **Step 1: Write the failing documentation expectation**

```python
# update CLI test expectations if needed so new flags are exercised
```

- [ ] **Step 2: Run tests to verify current expectations are covered**

Run: `python3 -m unittest tests.test_cycle_record -v`
Expected: PASS only after state update support is complete.

- [ ] **Step 3: Write minimal documentation implementation**

```markdown
python3 scripts/cycle_record.py --input payload.json --state status/state.json --state-mode completed
```

- [ ] **Step 4: Run tests to verify it stays green**

Run: `python3 -m unittest tests.test_cycle_record -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md scripts/cycle_record.py tests/test_cycle_record.py
git commit -m "docs: describe cycle record state sync"
```
