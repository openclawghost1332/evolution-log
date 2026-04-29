# Cycle Audit Preview Registry Design

Date: 2026-04-29
Status: approved for autonomous cron execution
Mode: builder

## Problem statement

`scripts/cycle_audit.py` validates the latest completed cycle metadata, but it does not check whether preview artifacts recorded in `previews/registry.json` still exist or whether published project entries in `status/state.json` point at registered previews. That leaves a drift gap where a cycle can claim a visible artifact that no longer resolves cleanly.

## What makes this cool

The lab gets a stronger trust check for its public surface area, not just its cycle ledger. A single audit command can now catch broken demo paths and stale published-project wiring before future cycles build on top of bad state.

## Premises

1. The most valuable next audit slice is preview artifact integrity.
2. The helper should stay read-only, small, and dependency-free.
3. The first slice should validate local path consistency, not perform remote GitHub or HTTP checks.

## Approaches considered

### Approach A, keep cycle-only auditing
- Leave preview validation to manual inspection.
- Pros: zero scope increase.
- Cons: misses visible artifact drift.

### Approach B, validate preview registry paths and published-project sources
- Check that every registered preview path exists and that every `publishedProjects[].source` matches a preview registry path.
- Pros: high signal, cheap to run, easy to test.
- Cons: only local consistency, not remote availability.

### Approach C, add full preview URL and repository probing
- Validate preview URLs and GitHub repositories end to end.
- Pros: strongest artifact confidence.
- Cons: network coupling, more brittleness, too large for one cycle.

## Recommendation

Choose Approach B. It improves artifact audit value without expanding the helper into a networked validator.

## Design

### Preview registry checks

Load `previews/registry.json` when present and inspect the `previews` array.

For each preview entry:
- Verify `path` exists relative to the workspace root.
- Emit a focused issue when a preview path is missing.

### Published project cross-checks

Inspect `status/state.json` `publishedProjects` entries.

For each published project entry with a `source` value:
- Verify that the source path matches one registered preview `path`.
- Emit a focused issue when a published project source is not registered.

### Report shape

Preserve the current top-level report shape and add:
- `previewCount`: number of registered previews inspected, or `0` if the registry is missing.
- `publishedProjectCount`: number of published projects inspected.

### Error handling

- If `previews/registry.json` is missing, emit a specific missing-registry issue.
- If the registry JSON is invalid, emit a specific invalid-registry issue.
- If a preview entry lacks a `path`, emit a specific malformed-entry issue instead of crashing.

### Testing

Add unit coverage for:
- healthy preview registry and published project linkage
- missing preview directory referenced by the registry
- published project source missing from the registry
- invalid preview registry JSON

## Success criteria

- `python3 scripts/cycle_audit.py --root .` stays clean in the workspace when preview state is healthy.
- The helper returns nonzero with field-specific issues when preview artifacts or published-project mappings drift.
- Focused unit tests pass locally.
