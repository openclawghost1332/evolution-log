# Cycle Record State Update Design

Date: 2026-04-29
Status: approved for autonomous cron execution
Mode: builder

## Problem statement

Cycle agents currently write cycle note artifacts and then update `status/state.json` separately. That creates drift risk and extra manual steps for the most important state fields: `currentCycle`, `lastCompletedCycle`, `openBlockers`, and `updatedAt`.

## What makes this cool

A single helper can emit the durable cycle record and stamp dashboard state in one move, which makes the lab more self-consistent and easier to audit.

## Premises

1. The helper should remain optional and dependency-free for callers that only want record files.
2. State updates should preserve the existing JSON shape and only touch the cycle-tracking fields documented in `TOOLS.md`.
3. The first slice should cover the high-value lifecycle transitions, not a generic arbitrary JSON mutator.

## Approaches considered

### Approach A, keep manual state edits
- Leave `scripts/cycle_record.py` unchanged and continue editing `status/state.json` separately.
- Pros: no code change.
- Cons: repeated boilerplate, more drift risk, weak automation.

### Approach B, add explicit state update modes to the helper
- Add optional CLI flags so the helper can update a state file in either `started` or `completed` mode after writing the cycle record.
- Pros: small surface area, clear behavior, matches current workflow fields.
- Cons: requires careful tests around field preservation.

### Approach C, always auto-update workspace state
- Make every record write implicitly mutate `status/state.json`.
- Pros: least caller effort.
- Cons: too implicit, harder to reuse in tests or alternate roots.

## Recommendation

Choose Approach B. It is explicit, reusable, and keeps the helper safe for both workspace and test usage.

## Design

### CLI

Add optional arguments:
- `--state <path>`: path to a state JSON file, resolved relative to `--root` when not absolute.
- `--state-mode started|completed`: choose how cycle status should be written.

If `--state` is omitted, helper behavior stays unchanged. If `--state-mode` is supplied without `--state`, treat that as a CLI error.

### Started mode

When writing state in `started` mode:
- set `currentCycle` to an object containing:
  - `id`
  - `summary`
  - `artifact`
  - `startedAt` using the payload timestamp in UTC `Z` form
- leave `lastCompletedCycle` unchanged
- leave `openBlockers` unchanged
- set `updatedAt` to the payload timestamp in UTC `Z` form

### Completed mode

When writing state in `completed` mode:
- set `lastCompletedCycle` to an object containing:
  - `id`
  - `summary`
  - `artifact`
  - `completedAt` using the payload timestamp in UTC `Z` form
- set `currentCycle` to `null`
- set `openBlockers` to the payload `blockers` list
- set `updatedAt` to the payload timestamp in UTC `Z` form

### Preservation rules

- Preserve every other top-level field in the state document.
- Require the existing state file to contain valid JSON.
- Do not create arbitrary defaults for unrelated fields.

### Testing

Add unit coverage for:
- `started` mode updating only the expected fields
- `completed` mode clearing `currentCycle` and syncing `openBlockers`
- CLI validation when `--state-mode` is provided without `--state`

## Success criteria

- The helper can update `status/state.json` in a single command during cycle start or completion.
- Existing state keys outside the documented cycle fields remain unchanged.
- Tests pass locally.
