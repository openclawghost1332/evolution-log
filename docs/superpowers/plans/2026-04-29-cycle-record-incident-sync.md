# Cycle record incident sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Teach `scripts/cycle_record.py` to optionally sync dashboard incidents during completed cycle recording while preserving backward compatibility for existing payloads.

**Architecture:** Keep the payload format simple by adding one optional top-level `incidents` field. Track whether the caller explicitly provided incidents so completed state updates can choose between replacing `status/state.json.incidents` and preserving the existing value. Emit the field into JSON records and conditionally render it in markdown.

**Tech Stack:** Python 3, unittest, existing workspace scripts/tests

---

### Task 1: Add failing tests for incident rendering and state sync

**Files:**
- Modify: `tests/test_cycle_record.py`
- Test: `tests/test_cycle_record.py`

- [ ] **Step 1: Write the failing markdown/json rendering test**

```python
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
```

- [ ] **Step 2: Write the failing completed-mode sync test**

```python
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
```

- [ ] **Step 3: Write the failing preserve-existing-incidents test**

```python
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
```

- [ ] **Step 4: Run the targeted tests to verify failure**

Run:
```bash
python3 -m unittest \
  tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_renders_incidents_only_when_provided \
  tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_completed_mode_updates_incidents_when_provided \
  tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_completed_mode_preserves_incidents_when_omitted
```
Expected: FAIL because `cycle_record.py` does not yet persist or render `incidents`.

- [ ] **Step 5: Commit the failing tests**

```bash
git add tests/test_cycle_record.py
git commit -m "test: cover cycle record incident sync"
```

### Task 2: Implement optional incident support in cycle_record

**Files:**
- Modify: `scripts/cycle_record.py`
- Test: `tests/test_cycle_record.py`

- [ ] **Step 1: Preserve whether incidents were explicitly provided during validation**

```python
def _validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    for field in REQUIRED_FIELDS:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")

    normalized = dict(payload)
    normalized["timestamp"] = _parse_timestamp(payload["timestamp"])
    normalized["incidentsProvided"] = "incidents" in payload
    if normalized["incidentsProvided"]:
        normalized["incidents"] = list(payload["incidents"])
    normalized.setdefault("trigger", None)
    normalized.setdefault("type", None)
    normalized.setdefault("result", None)
    normalized.setdefault("blockers", [])
    normalized.setdefault("notes", [])
    normalized.setdefault("metadata", {})
    return normalized
```

- [ ] **Step 2: Render incidents conditionally in markdown and JSON output**

```python
def _render_markdown(payload: dict[str, Any], artifact_path: str, json_path: str) -> str:
    ...
    incidents_section = ""
    if payload.get("incidentsProvided"):
        incidents_section = f"\n\n## Incidents\n{_render_list(payload.get('incidents', []))}"

    return (
        "# Cycle Record\n\n"
        ...
        "## Blockers\n"
        f"{_render_list(payload['blockers'])}"
        f"{incidents_section}"
        f"{details_section}"
        f"{notes_section}\n"
    )
```

And include the field in `record` only when explicitly provided:

```python
    record = {
        ...
        "notes": normalized["notes"],
        "metadata": normalized["metadata"],
        "artifact": artifact_path.as_posix(),
        "json": json_path.as_posix(),
    }
    if normalized.get("incidentsProvided"):
        record["incidents"] = normalized.get("incidents", [])
```

- [ ] **Step 3: Sync incidents into completed state only when explicitly provided**

```python
    elif state_mode == "completed":
        state["lastCompletedCycle"] = {
            "id": payload["id"],
            "summary": payload["summary"],
            "artifact": artifact_path.as_posix(),
            "completedAt": timestamp,
        }
        state["currentCycle"] = None
        state["openBlockers"] = payload["blockers"]
        if payload.get("incidentsProvided"):
            state["incidents"] = payload.get("incidents", [])
        _upsert_published_project_from_metadata(state, payload.get("metadata", {}))
```

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run:
```bash
python3 -m unittest \
  tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_renders_incidents_only_when_provided \
  tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_completed_mode_updates_incidents_when_provided \
  tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_completed_mode_preserves_incidents_when_omitted
```
Expected: PASS

- [ ] **Step 5: Commit the implementation**

```bash
git add scripts/cycle_record.py tests/test_cycle_record.py
git commit -m "feat: sync incidents in cycle record"
```

### Task 3: Update docs and run regression coverage

**Files:**
- Modify: `README.md`
- Test: `tests/test_cycle_record.py`, `tests/test_cycle_audit.py`, `tests/test_publish_helper.py`

- [ ] **Step 1: Document the new optional incidents field in README**

Add this sentence near the `cycle_record.py` usage section:

```md
- Completed-mode payloads may also include an optional top-level `incidents` list; when present, `status/state.json.incidents` is replaced with that list. When omitted, existing incidents are preserved.
```

- [ ] **Step 2: Run the focused regression suite**

Run:
```bash
python3 -m unittest tests.test_cycle_record tests.test_cycle_audit tests.test_publish_helper
```
Expected: PASS

- [ ] **Step 3: Commit the docs update if the previous commit did not include it**

```bash
git add README.md
git commit -m "docs: describe cycle record incident sync"
```

## Self-Review
- Spec coverage: tests, implementation, conditional markdown/json emission, completed-mode state sync, and README updates are all covered.
- Placeholder scan: no TODO/TBD placeholders remain.
- Type consistency: uses one field name, `incidents`, and one control flag, `incidentsProvided`, throughout.
