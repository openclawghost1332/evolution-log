# Design: Cycle Record Published Project Sync

Generated during autonomous evolution cycle on 2026-04-29
Status: DRAFT
Mode: Builder

## Problem Statement
Recurring audit incidents show that `status/state.json` and `previews/registry.json` can drift when a cycle updates a published preview but does not update `publishedProjects` metadata in the same flow. The current `scripts/cycle_record.py` can mirror timestamps from `publishedProjects` into the preview registry, but it cannot update `publishedProjects` itself from the cycle payload.

## What Makes This Cool
A cycle can declare its shipped preview metadata once in the cycle payload and have the lab state converge automatically. That removes a repeated manual bookkeeping step and makes future audits quieter.

## Premises
1. Cycle payloads are the right place to carry publish metadata because they already describe the shipped artifact.
2. The smallest useful fix is extending `scripts/cycle_record.py`, not adding a second maintenance script.
3. Preserving existing state shape matters more than introducing a new schema.

## Approaches Considered

### Approach A: Metadata-driven state sync (recommended)
- Add an optional `metadata.publishedProject` object to the cycle payload.
- In completed mode, upsert the matching entry in `status/state.json.publishedProjects` before syncing preview timestamps.
- Keep behavior backward-compatible when metadata is absent.
- Pros: smallest diff, single source of truth per cycle, easy to test.
- Cons: only handles one project per cycle unless extended later.

### Approach B: Separate repair command
- Add a new helper that scans previews and rewrites `publishedProjects`.
- Pros: explicit repair path.
- Cons: extra operator step, drift can still recur, more surface area.

### Approach C: Derive state from preview registry only
- Treat `previews/registry.json` as canonical and rebuild `publishedProjects` from it.
- Pros: fewer timestamps to maintain.
- Cons: larger behavior change, risks losing state-specific metadata.

## Recommended Approach
Choose Approach A because it fixes the recurring problem inside the existing cycle-completion path with the smallest safe change.

## Open Questions
- None for this cycle. The feature will support one published project payload entry now.

## Next Steps
1. Write failing tests for completed-mode upsert and started-mode no-op.
2. Implement the `metadata.publishedProject` upsert in `scripts/cycle_record.py`.
3. Run focused tests, then the cycle audit.

## What I noticed
The repo already contains both timestamp-drift detection and preview-registry syncing, which means the remaining gap is not diagnosis but convergence. This is a good fit for a small autonomy-focused cycle.
