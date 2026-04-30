# Cycle Start Drift Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `scripts/cycle_record.py` safe for early cycle kickoff by allowing sparse `started` payloads while keeping completed records strict.

**Architecture:** Add state-mode-aware payload normalization so started-mode writes can fill in empty list defaults without requiring final cycle details. Cover the new behavior with focused `unittest` cases and document the kickoff workflow in `README.md`.

**Tech Stack:** Python 3 standard library, `argparse`, `json`, `pathlib`, `unittest`

---

### Task 1: Add failing tests for sparse started-mode payloads

**Files:**
- Modify: `tests/test_cycle_record.py`

- [ ] Add a test proving `write_cycle_record(..., state_mode="started")` accepts a payload with only `id`, `timestamp`, and `summary` and still writes markdown, JSON, and state.
- [ ] Add a test proving completed mode still rejects a sparse payload missing `changes` and `artifacts`.
- [ ] Run: `python3 -m unittest tests.test_cycle_record -v`
- [ ] Expected: FAIL before implementation.

### Task 2: Implement mode-aware payload normalization

**Files:**
- Modify: `scripts/cycle_record.py`
- Modify: `tests/test_cycle_record.py`

- [ ] Add validation logic that treats `started` mode as kickoff-safe and fills omitted lists with empty arrays.
- [ ] Keep non-started writes strict about required fields.
- [ ] Run: `python3 -m unittest tests.test_cycle_record -v`
- [ ] Expected: PASS with existing behavior preserved.

### Task 3: Document and verify the safer kickoff path

**Files:**
- Modify: `README.md`

- [ ] Update the cycle-record helper docs to explain that started mode can use a sparse kickoff payload.
- [ ] Run: `python3 -m unittest tests.test_cycle_record tests.test_cycle_audit -v && python3 scripts/cycle_audit.py --root .`
- [ ] Expected: PASS and a healthy audit report in the worktree.

## Self-review
- The fix narrows the drift path without weakening completed-cycle data quality.
- Markdown and JSON outputs stay explicit for empty lists.
- No new wrapper scripts or duplicate workflows are introduced.
