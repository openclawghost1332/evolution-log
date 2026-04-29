# Cycle Audit Preview Registry Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in repair mode to `scripts/cycle_audit.py` that syncs matching preview registry timestamps from published project metadata.

**Architecture:** Extend the existing dependency-free audit helper with one small write helper that loads `previews/registry.json`, matches entries by `path/source`, and updates only `updatedAt` fields when explicitly requested. Keep default audit behavior read-only and surface repair counts in the JSON report.

**Tech Stack:** Python 3, argparse, json, unittest

---

### Task 1: Define repair-mode behavior with failing tests

**Files:**
- Modify: `tests/test_cycle_audit.py`
- Test: `tests/test_cycle_audit.py`

- [ ] **Step 1: Write the failing tests**

```python
    def test_audit_workspace_repairs_preview_timestamp_drift_when_requested(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_healthy_cycle_files(root)
            self._write_healthy_state(root, project_updated_at="2026-04-29T07:45:44Z")
            self._write_preview_registry(root, updated_at="2026-04-28T22:47:20.000Z")

            report = audit_workspace(root, repair_preview_registry=True)
            registry = json.loads((root / "previews" / "registry.json").read_text(encoding="utf-8"))

        self.assertTrue(report["ok"])
        self.assertEqual(report["repairedPreviewCount"], 1)
        self.assertEqual(registry["previews"][0]["updatedAt"], "2026-04-29T07:45:44Z")
        self.assertEqual(report["issues"], [])

    def test_audit_workspace_reports_zero_repairs_without_matching_drift(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_healthy_cycle_files(root)
            self._write_healthy_state(root)
            self._write_preview_registry(root)

            report = audit_workspace(root, repair_preview_registry=True)

        self.assertTrue(report["ok"])
        self.assertEqual(report["repairedPreviewCount"], 0)
        self.assertEqual(report["issues"], [])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_cycle_audit.CycleAuditTests.test_audit_workspace_repairs_preview_timestamp_drift_when_requested tests.test_cycle_audit.CycleAuditTests.test_audit_workspace_reports_zero_repairs_without_matching_drift -v`
Expected: FAIL because `audit_workspace()` does not yet accept `repair_preview_registry` or rewrite `previews/registry.json`.

- [ ] **Step 3: Commit the red test state**

```bash
git add tests/test_cycle_audit.py docs/superpowers/specs/2026-04-29-cycle-audit-preview-repair-design.md docs/superpowers/plans/2026-04-29-cycle-audit-preview-repair.md
git commit -m "test: define cycle audit preview repair behavior"
```

### Task 2: Implement minimal repair support in the audit helper

**Files:**
- Modify: `scripts/cycle_audit.py`
- Test: `tests/test_cycle_audit.py`

- [ ] **Step 1: Write the minimal implementation**

```python
def _repair_preview_registry(root: Path, state: dict[str, Any]) -> int:
    registry_path = root / "previews" / "registry.json"
    if not registry_path.exists():
        return 0

    registry = _read_json(registry_path)
    previews = registry.get("previews")
    if not isinstance(previews, list):
        return 0

    preview_by_path = {
        preview.get("path"): preview
        for preview in previews
        if isinstance(preview, dict) and preview.get("path")
    }

    repaired = 0
    for project in state.get("publishedProjects", []):
        if not isinstance(project, dict):
            continue
        source = project.get("source")
        updated_at = project.get("updatedAt")
        preview = preview_by_path.get(source)
        if preview and updated_at and preview.get("updatedAt") != updated_at:
            preview["updatedAt"] = updated_at
            repaired += 1

    if repaired:
        registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

    return repaired


def audit_workspace(root: Path, repair_preview_registry: bool = False) -> dict[str, Any]:
    state = _read_json(root / "status" / "state.json")
    repaired_preview_count = 0
    if repair_preview_registry:
        repaired_preview_count = _repair_preview_registry(root, state)

    # existing audit logic here

    return {
        # existing fields,
        "repairedPreviewCount": repaired_preview_count,
    }
```

- [ ] **Step 2: Add CLI plumbing for the opt-in flag**

```python
    parser.add_argument("--repair-preview-registry", action="store_true")
    report = audit_workspace(
        Path(args.root),
        repair_preview_registry=args.repair_preview_registry,
    )
```

- [ ] **Step 3: Run focused tests to verify they pass**

Run: `python3 -m unittest tests.test_cycle_audit -v`
Expected: PASS for existing audit coverage plus new repair-mode coverage.

- [ ] **Step 4: Commit the implementation**

```bash
git add scripts/cycle_audit.py tests/test_cycle_audit.py
git commit -m "feat: add cycle audit preview repair mode"
```

### Task 3: Verify the real workspace and document the shipped artifact

**Files:**
- Modify: `cycles/2026-04-29/<cycle-id>.md`
- Modify: `cycles/2026-04-29/<cycle-id>.json`
- Modify: `status/state.json`

- [ ] **Step 1: Run the real audit in read-only mode**

Run: `python3 scripts/cycle_audit.py --root .`
Expected: JSON output succeeds and still reflects the workspace accurately.

- [ ] **Step 2: Run the real audit in repair mode**

Run: `python3 scripts/cycle_audit.py --root . --repair-preview-registry`
Expected: JSON output succeeds, with `repairedPreviewCount` equal to `0` if the workspace is already converged.

- [ ] **Step 3: Record the cycle with the shipped artifact**

```json
{
  "id": "20260429T114100Z-cycle-audit-preview-repair",
  "timestamp": "2026-04-29T11:41:00Z",
  "summary": "Added opt-in preview registry repair mode to the cycle audit helper.",
  "artifacts": [
    "scripts/cycle_audit.py",
    "tests/test_cycle_audit.py",
    "docs/superpowers/specs/2026-04-29-cycle-audit-preview-repair-design.md",
    "docs/superpowers/plans/2026-04-29-cycle-audit-preview-repair.md"
  ],
  "changes": [
    "Added a repair helper that syncs preview registry timestamps from published project metadata.",
    "Extended cycle audit reporting with repaired preview counts.",
    "Covered the new repair path with focused unittest coverage."
  ],
  "trigger": "cron:evolution-cycle",
  "type": "autonomy-improvement",
  "result": "shipped",
  "blockers": [],
  "notes": [
    "Repair mode stays opt-in so the default audit remains read-only."
  ]
}
```

- [ ] **Step 4: Commit the recorded cycle state**

```bash
git add cycles/2026-04-29 status/state.json
git commit -m "docs: record cycle audit preview repair"
```
