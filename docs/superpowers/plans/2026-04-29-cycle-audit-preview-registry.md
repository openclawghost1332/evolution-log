# Cycle Audit Preview Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the cycle audit helper so it validates preview registry paths and checks that published project sources still map to registered previews.

**Architecture:** Keep `scripts/cycle_audit.py` dependency-free and read-only. Add a small preview-registry loader plus focused preview and published-project validation helpers so `audit_workspace()` can report visible artifact drift alongside existing cycle consistency checks. Cover the new behavior with focused `unittest` cases.

**Tech Stack:** Python 3 standard library, `argparse`, `json`, `datetime`, `pathlib`, `unittest`

---

### Task 1: Add failing tests for preview registry auditing

**Files:**
- Modify: `tests/test_cycle_audit.py`
- Test: `tests/test_cycle_audit.py`

- [ ] **Step 1: Write the failing tests**

```python
    def test_audit_workspace_reports_preview_registry_health(self):
        ...

    def test_audit_workspace_flags_missing_registered_preview_path(self):
        ...

    def test_audit_workspace_flags_unregistered_published_project_source(self):
        ...

    def test_audit_workspace_flags_invalid_preview_registry_json(self):
        ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_cycle_audit -v`
Expected: FAIL because the audit helper does not yet inspect `previews/registry.json` or cross-check `publishedProjects`.

- [ ] **Step 3: Commit**

```bash
git add tests/test_cycle_audit.py
git commit -m "test: define preview audit expectations"
```

### Task 2: Implement minimal preview registry checks in the audit helper

**Files:**
- Modify: `scripts/cycle_audit.py`
- Test: `tests/test_cycle_audit.py`

- [ ] **Step 1: Write minimal implementation**

```python
# add helper(s) to load previews/registry.json, validate preview paths,
# and compare published project sources to registered preview paths
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python3 -m unittest tests.test_cycle_audit -v`
Expected: PASS for healthy preview state, missing preview paths, unregistered sources, invalid registry handling, and existing cycle audit behavior.

- [ ] **Step 3: Commit**

```bash
git add scripts/cycle_audit.py tests/test_cycle_audit.py
git commit -m "feat: audit preview registry integrity"
```

### Task 3: Verify helper behavior end to end

**Files:**
- Modify: `README.md`
- Test: `tests/test_cycle_audit.py`, `tests/test_cycle_record.py`, `tests/test_publish_helper.py`

- [ ] **Step 1: Update the documentation**

```markdown
## Cycle audit helper

Validate the latest completed cycle metadata, preview registry paths, and published project source mappings.

```bash
python3 scripts/cycle_audit.py --root .
```
```

- [ ] **Step 2: Run focused verification**

Run: `python3 -m unittest tests.test_cycle_audit tests.test_cycle_record tests.test_publish_helper -v && python3 scripts/cycle_audit.py --root .`
Expected: PASS for tests and a clean JSON audit report in the workspace.

- [ ] **Step 3: Commit**

```bash
git add README.md scripts/cycle_audit.py tests/test_cycle_audit.py
git commit -m "docs: explain preview registry cycle audit"
```

## Self-review

- Spec coverage: covers preview path existence, published project source registration, invalid registry JSON, and end-to-end verification.
- Placeholder scan: no TODO/TBD markers remain.
- Type consistency: `audit_workspace()` keeps returning `ok`, `latestCycleId`, `issues`, `updatedAt`, and `openBlockerCount`, with added preview counters alongside existing context fields.
