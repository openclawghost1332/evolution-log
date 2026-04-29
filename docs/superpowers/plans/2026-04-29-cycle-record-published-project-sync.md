# Cycle Record Published Project Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let completed cycle recording upsert one published project entry from payload metadata into `status/state.json`, then sync the preview registry from the updated state.

**Architecture:** Extend `scripts/cycle_record.py` with one helper that normalizes and upserts an optional `metadata.publishedProject` record during completed-state updates. Keep the existing preview registry sync path, but run it against the newly updated state so preview timestamps converge in one write flow.

**Tech Stack:** Python 3, unittest, JSON file mutation

---

### Task 1: Add regression tests for published project sync

**Files:**
- Modify: `tests/test_cycle_record.py`
- Test: `tests/test_cycle_record.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_completed_mode_upserts_published_project_from_metadata -v`
Expected: FAIL because `publishedProjects[0]["updatedAt"]` stays stale or the new entry is missing.

- [ ] **Step 3: Add a started-mode guard test**

```python
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
```

- [ ] **Step 4: Run both tests to verify red state**

Run: `python3 -m unittest tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_completed_mode_upserts_published_project_from_metadata tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_started_mode_does_not_upsert_published_project_from_metadata -v`
Expected: first FAILS for missing upsert, second may PASS already.

### Task 2: Implement published project upsert in cycle record helper

**Files:**
- Modify: `scripts/cycle_record.py`
- Test: `tests/test_cycle_record.py`

- [ ] **Step 1: Write minimal implementation**

```python
def _upsert_published_project_from_metadata(state: dict[str, Any], metadata: dict[str, Any]) -> None:
    project = metadata.get("publishedProject")
    if not isinstance(project, dict):
        return
    source = project.get("source")
    if not source:
        return
    published_projects = state.setdefault("publishedProjects", [])
    if not isinstance(published_projects, list):
        return
    for index, existing in enumerate(published_projects):
        if isinstance(existing, dict) and existing.get("source") == source:
            published_projects[index] = {**existing, **project}
            return
    published_projects.append(project)
```

- [ ] **Step 2: Call the helper only in completed mode before preview sync**

```python
    elif state_mode == "completed":
        state["lastCompletedCycle"] = {
            ...
        }
        state["currentCycle"] = None
        state["openBlockers"] = payload["blockers"]
        _upsert_published_project_from_metadata(state, payload.get("metadata", {}))
```

- [ ] **Step 3: Run the focused tests to verify they pass**

Run: `python3 -m unittest tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_completed_mode_upserts_published_project_from_metadata tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_started_mode_does_not_upsert_published_project_from_metadata -v`
Expected: PASS

- [ ] **Step 4: Run the full cycle record test module**

Run: `python3 -m unittest tests.test_cycle_record -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/cycle_record.py tests/test_cycle_record.py docs/superpowers/specs/2026-04-29-cycle-record-published-project-sync-design.md docs/superpowers/plans/2026-04-29-cycle-record-published-project-sync.md
git commit -m "feat: sync published project metadata in cycle record"
```
