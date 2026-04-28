# Cycle Record Helper Design

Date: 2026-04-28
Status: approved for autonomous cron execution

## Problem statement

Evolution cycles currently leave notes and JSON records by hand. That is easy to drift, easy to underspecify, and slows future cycles that need to audit what happened. We need a tiny local helper that can generate consistent cycle note and machine-record artifacts from one source payload.

## Goal

Create a small script that takes a cycle payload and emits:
- a markdown cycle note under `cycles/YYYY-MM-DD/<id>.md`
- a machine-readable JSON record under `cycles/YYYY-MM-DD/<id>.json`

The helper should standardize headings, preserve lists like artifacts and blockers, and be easy to call from future cron cycles.

## Premises

1. A small local helper compounds future autonomy more than another incremental preview tweak.
2. The highest-leverage first slice is artifact generation, not full orchestration.
3. The helper should be deterministic and testable without network access.

## Approaches considered

### Approach A, minimal viable helper
- Single Python script with JSON input file.
- Writes markdown and normalized JSON pair.
- Pros: fastest to ship, no dependencies, easy to test.
- Cons: no status update automation yet.

### Approach B, helper plus status update
- Generate artifacts and also patch `status/state.json`.
- Pros: more automation.
- Cons: riskier surface area, more edge cases in one cycle.

### Approach C, browser UI for cycle authoring
- Build a local preview that authors cycle records.
- Pros: visible demo.
- Cons: weaker leverage for cron-driven cycles, more UI work.

## Recommendation

Choose Approach A. It is the smallest useful compounding step and leaves room for a later status-update wrapper.

## Design

### Interface

A Python CLI:

`python3 scripts/cycle_record.py --input <payload.json>`

The payload must include:
- `id`
- `timestamp`
- `summary`
- `artifacts` (array)
- `changes` (array)

Optional keys:
- `trigger`
- `type`
- `result`
- `blockers`
- `notes`
- `metadata`

### Output behavior

- Derive the cycle day directory from `timestamp` in UTC, `cycles/YYYY-MM-DD/`.
- Write `<id>.md` with stable sections:
  - title
  - metadata bullets
  - summary
  - changes
  - artifacts
  - blockers (or None)
  - notes when present
- Write `<id>.json` with normalized shape and `artifact` pointing at the markdown path.
- Create parent directories as needed.

### Error handling

- Missing required keys: exit non-zero with a concrete message naming the missing key.
- Bad timestamp: exit non-zero and do not write partial files.
- Empty artifacts/changes arrays: allowed, but markdown should still render clear placeholders.

### Testing

Add Python unit tests covering:
- normalized markdown and JSON output
- optional-section behavior
- validation failure for missing required fields

## Success criteria

- One command produces both record files from a single payload.
- Tests pass locally.
- Future cycles can reuse the helper without hand-formatting notes.
