# Cycle Record Preview Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `scripts/cycle_record.py --state-mode completed` sync matching preview registry timestamps from `status/state.json` published project metadata.

**Architecture:** Extend the existing completed-mode state update flow with a tiny helper that loads `previews/registry.json`, indexes preview entries by `path`, and copies each matching `publishedProjects[].updatedAt` value into the registry entry. Keep the sync opt-in through completed-mode only, and prove it with one focused regression test plus the existing audit suite.

**Tech Stack:** Python 3, `unittest`, JSON file mutation, existing cycle helpers.

---

### Task 1: Add failing regression coverage for completed-mode preview syncing

**Files:**
- Modify: `tests/test_cycle_record.py`
- Test: `tests/test_cycle_record.py`

- [ ] **Step 1: Write the failing test**

```python
    def test_write_cycle_record_completed_mode_syncs_matching_preview_registry_timestamp(self):
        payload = {
            "id": "20260429T094100Z-cycle-record-preview-sync",
            "timestamp": "2026-04-29T09:41:00Z",
            "summary": "Sync preview metadata during completed cycle recording.",
            "changes": ["Added preview registry sync to cycle record helper."],
            "artifacts": ["scripts/cycle_record.py", "tests/test_cycle_record.py"],
            "blockers": [],
        }
        initial_state = {
            "currentCycle": {"id": "in-flight"},
            "lastCompletedCycle": {"id": "older"},
            "openBlockers": [],
            "updatedAt": "2026-04-29T00:00:00Z",
            "publishedProjects": [
                {
                    "name": "work-scoring-helper",
                    "source": "previews/work-scoring-helper",
                    "updatedAt": "2026-04-29T09:30:00Z",
                }
            ],
        }
        initial_registry = {
            "previews": [
                {
                    "slug": "work-scoring-helper",
                    "path": "previews/work-scoring-helper",
                    "updatedAt": "2026-04-29T07:45:44Z",
                    "title": "OpenClaw Work Scoring Helper",
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            state_path = root / "status" / "state.json"
            registry_path = root / "previews" / "registry.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(initial_state), encoding="utf-8")
            registry_path.write_text(json.dumps(initial_registry), encoding="utf-8")

            write_cycle_record(payload, root, state_path=Path("status/state.json"), state_mode="completed")

            registry = json.loads(registry_path.read_text(encoding="utf-8"))

        self.assertEqual(
            registry["previews"][0]["updatedAt"],
            "2026-04-29T09:30:00Z",
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_completed_mode_syncs_matching_preview_registry_timestamp -v`
Expected: FAIL because `write_cycle_record(..., state_mode="completed")` updates `status/state.json` but does not yet rewrite `previews/registry.json`.

- [ ] **Step 3: Write minimal implementation**

```python
def _sync_preview_registry_from_state(root: Path, state: dict[str, Any]) -> None:
    registry_path = root / "previews" / "registry.json"
    if not registry_path.exists():
        return

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    previews = registry.get("previews")
    if not isinstance(previews, list):
        return

    preview_by_path = {
        preview.get("path"): preview
        for preview in previews
        if isinstance(preview, dict) and preview.get("path")
    }
    changed = False
    for project in state.get("publishedProjects", []):
        source = project.get("source")
        updated_at = project.get("updatedAt")
        preview = preview_by_path.get(source)
        if preview and updated_at and preview.get("updatedAt") != updated_at:
            preview["updatedAt"] = updated_at
            changed = True

    if changed:
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
```

Then call it from `_update_state_file(...)` only inside the `completed` branch after state fields are updated and before returning.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_completed_mode_syncs_matching_preview_registry_timestamp -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_cycle_record.py scripts/cycle_record.py
git commit -m "feat: sync preview registry on cycle completion"
```

### Task 2: Document and verify the completed-mode sync behavior

**Files:**
- Modify: `README.md`
- Test: `tests/test_cycle_record.py`, `tests/test_cycle_audit.py`

- [ ] **Step 1: Write the failing documentation-oriented test expectation**

```python
    def test_write_cycle_record_started_mode_does_not_require_preview_registry(self):
        payload = {
            "id": "20260428T234100Z-cycle-record-helper",
            "timestamp": "2026-04-28T23:41:00Z",
            "summary": "Ship a helper for consistent cycle notes.",
            "changes": ["Added a cycle record helper script."],
            "artifacts": ["scripts/cycle_record.py", "tests/test_cycle_record.py"],
            "blockers": [],
        }
        initial_state = {
            "currentCycle": None,
            "lastCompletedCycle": {"id": "older"},
            "openBlockers": [],
            "updatedAt": "2026-04-28T00:00:00Z",
            "publishedProjects": [
                {
                    "name": "work-scoring-helper",
                    "source": "previews/work-scoring-helper",
                    "updatedAt": "2026-04-29T09:30:00Z",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            state_path = root / "status" / "state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(initial_state), encoding="utf-8")

            write_cycle_record(payload, root, state_path=Path("status/state.json"), state_mode="started")
            state = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(state["currentCycle"]["id"], payload["id"])
```

- [ ] **Step 2: Run test to verify it fails or stays green for the right reason**

Run: `python3 -m unittest tests.test_cycle_record.CycleRecordTests.test_write_cycle_record_started_mode_does_not_require_preview_registry -v`
Expected: PASS already, confirming the new sync behavior should remain limited to completed mode.

- [ ] **Step 3: Write minimal documentation update**

```markdown
Optional flags:
- `--root <dir>` writes the `cycles/YYYY-MM-DD/` output tree somewhere other than the workspace root.
- `--state <path>` updates an existing state JSON file after writing the record.
- `--state-mode started|completed` chooses whether to stamp `currentCycle` or `lastCompletedCycle` style fields. `--state-mode` requires `--state`.
- In `completed` mode, matching `previews/registry.json` entries are also refreshed from `publishedProjects[].updatedAt` when the registry file exists.
```

- [ ] **Step 4: Run the full verification suite**

Run: `python3 -m unittest tests.test_cycle_record tests.test_cycle_audit -v && python3 scripts/cycle_audit.py --root /home/node/.openclaw/workspace`
Expected: PASS for the unit suites, then a JSON audit report with `"ok": true` and no issues.

- [ ] **Step 5: Commit**

```bash
git add README.md tests/test_cycle_record.py scripts/cycle_record.py
git commit -m "docs: explain cycle record preview sync"
```