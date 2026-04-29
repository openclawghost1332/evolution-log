# Cycle Record Git Metadata Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Auto-stamp git HEAD and dirty-state metadata into generated cycle records and render metadata details in markdown.

**Architecture:** Extend the existing dependency-free Python helper with a small git metadata probe that shells out to `git`, merge detected values into the record metadata, and render metadata in a dedicated markdown section. Drive the change with focused `unittest` coverage using mocks for git subprocess behavior.

**Tech Stack:** Python 3 standard library, `unittest`, `unittest.mock`, subprocess, JSON

---

### Task 1: Add failing tests for git metadata capture and markdown rendering

**Files:**
- Modify: `tests/test_cycle_record.py`
- Test: `tests/test_cycle_record.py`

- [ ] **Step 1: Write the failing tests**

```python
    @patch("scripts.cycle_record.subprocess.run")
    def test_write_cycle_record_stamps_detected_git_metadata(self, mock_run):
        ...

    @patch("scripts.cycle_record.subprocess.run", side_effect=OSError("git missing"))
    def test_write_cycle_record_keeps_existing_metadata_when_git_unavailable(self, _mock_run):
        ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_cycle_record -v`
Expected: FAIL because git metadata detection and metadata markdown rendering do not exist yet

- [ ] **Step 3: Write minimal implementation**

```python
# add a helper that probes git HEAD and dirty state
# merge detected values into metadata
# render a metadata details section when metadata is present
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_cycle_record -v`
Expected: PASS for the new git metadata tests and all existing tests

- [ ] **Step 5: Commit**

```bash
git add tests/test_cycle_record.py scripts/cycle_record.py
git commit -m "feat: stamp git metadata in cycle records"
```

### Task 2: Document the new metadata behavior

**Files:**
- Modify: `README.md`
- Modify: `scripts/cycle_record.py`
- Test: `tests/test_cycle_record.py`

- [ ] **Step 1: Write the failing test**

```python
    def test_markdown_renders_metadata_details_section(self):
        ...
```

- [ ] **Step 2: Run tests to verify it fails**

Run: `python3 -m unittest tests.test_cycle_record -v`
Expected: FAIL because metadata details rendering is incomplete or unstable

- [ ] **Step 3: Write minimal implementation**

```python
# make metadata detail rendering stable and update README usage text
```

- [ ] **Step 4: Run tests to verify it passes**

Run: `python3 -m unittest tests.test_cycle_record -v`
Expected: PASS for all tests

- [ ] **Step 5: Commit**

```bash
git add README.md scripts/cycle_record.py tests/test_cycle_record.py
git commit -m "docs: explain cycle record git metadata"
```
