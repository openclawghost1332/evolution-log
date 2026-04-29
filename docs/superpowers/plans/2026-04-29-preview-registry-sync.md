# Preview Registry Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Detect preview registry timestamp drift against published project metadata and repair the current stale registry entry.

**Architecture:** Extend `scripts/cycle_audit.py` so it indexes preview entries by `path` and compares each matching `publishedProjects[].updatedAt` value against the registry entry `updatedAt`, normalizing timestamps before comparison. Cover the new behavior with one focused regression test, then update the real registry file so the workspace audit returns clean.

**Tech Stack:** Python 3, unittest, JSON workspace metadata

---

### Task 1: Add preview timestamp drift detection and repair current metadata

**Files:**
- Modify: `tests/test_cycle_audit.py`
- Modify: `scripts/cycle_audit.py`
- Modify: `previews/registry.json`
- Verify: `status/state.json`

- [ ] **Step 1: Write the failing test**

```python
    def test_audit_workspace_flags_preview_timestamp_drift(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_healthy_cycle_files(root)
            self._write_healthy_state(root)
            registry_dir = root / "previews"
            registry_dir.mkdir(exist_ok=True)
            (registry_dir / "registry.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "previews": [
                            {
                                "slug": "work-scoring-helper",
                                "path": "previews/work-scoring-helper",
                                "status": "ready",
                                "updatedAt": "2026-04-28T22:47:20.000Z",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = audit_workspace(root)

        self.assertFalse(report["ok"])
        self.assertIn(
            "Preview registry metadata is stale for work-scoring-helper: previews/registry.json updatedAt does not match status/state.json publishedProjects updatedAt",
            report["issues"],
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_cycle_audit.py -k preview_timestamp_drift -v`
Expected: FAIL because `audit_workspace()` does not yet compare registry and published project timestamps.

- [ ] **Step 3: Write minimal implementation**

```python
    registered_previews: dict[str, dict[str, Any]] = {}
    ...
                    registered_previews[preview_path] = preview
    ...
    for project in published_projects:
        source = project.get("source")
        if source and source not in registered_preview_paths:
            issues.append(
                f"Published project source is not registered in previews/registry.json: {source}"
            )
            continue

        if not source:
            continue

        preview = registered_previews.get(source)
        preview_updated_at = _normalize_timestamp((preview or {}).get("updatedAt"))
        project_updated_at = _normalize_timestamp(project.get("updatedAt"))
        if preview and preview_updated_at != project_updated_at:
            issues.append(
                f"Preview registry metadata is stale for {preview.get('slug', source)}: "
                "previews/registry.json updatedAt does not match "
                "status/state.json publishedProjects updatedAt"
            )
```

Then update `previews/registry.json` to:

```json
{
  "version": 1,
  "previews": [
    {
      "slug": "work-scoring-helper",
      "title": "OpenClaw Work Scoring Helper",
      "description": "A tiny static tool for scoring and preset-ranking candidate cycle ideas with the Evolution Lab rubric.",
      "path": "previews/work-scoring-helper",
      "url": "/preview/work-scoring-helper/",
      "status": "ready",
      "updatedAt": "2026-04-29T07:45:44Z",
      "repository": "https://github.com/openclawghost1332/work-scoring-helper"
    }
  ]
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_cycle_audit.py -v`
Expected: PASS, including the new drift regression.

Run: `python3 scripts/cycle_audit.py --root .`
Expected: JSON output with `"ok": true` and no preview timestamp drift issue.

- [ ] **Step 5: Commit**

```bash
git add tests/test_cycle_audit.py scripts/cycle_audit.py previews/registry.json docs/superpowers/specs/2026-04-29-preview-registry-sync-design.md docs/superpowers/plans/2026-04-29-preview-registry-sync.md
git commit -m "feat: detect preview registry timestamp drift"
```
