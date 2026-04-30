# Cycle Start Drift Guard Design

Date: 2026-04-30
Status: Approved for implementation
Project: lab workspace reliability

## Summary
Adjust `scripts/cycle_record.py` so `--state-mode started` can write a durable kickoff record from a sparse payload, making it easy to create the cycle artifact pair before `status/state.json.currentCycle` points at it.

## Goals
- Let started-mode cycle recording work with only kickoff-safe fields.
- Preserve strict record requirements for non-started and completed writes.
- Keep markdown, JSON, and state-sync output stable and deterministic.
- Reduce the incentive to hand-edit `status/state.json` during cycle kickoff.

## Non-goals
- Refactoring the external cycle runner.
- Repairing already-broken current-cycle entries.
- Changing completed-cycle state semantics.

## Problem
The helper currently requires `artifacts` and `changes` for every payload. At cycle kickoff, those lists may not be known yet. When kickoff data is incomplete, agents can fall back to manually updating `status/state.json`, which recreates the exact drift bug the audit helper reports: `currentCycle` can reference a missing artifact.

## Design
1. Teach payload normalization about context. In `started` mode, require only `id`, `timestamp`, and `summary`.
2. Default omitted kickoff lists to empty arrays: `changes`, `artifacts`, `blockers`, and `notes`.
3. Preserve the existing stricter validation for writes that are not explicitly `started` mode.
4. Continue to render `- None.` placeholders in markdown and emit empty arrays in JSON so output stays explicit.
5. Keep state updates unchanged: after record files are written, `currentCycle` points at the just-written markdown path.

## Testing
- Started mode accepts a payload with only `id`, `timestamp`, and `summary`, then writes markdown, JSON, and state.
- Completed mode still rejects payloads missing `changes` or `artifacts`.
- Existing started/completed state-sync behavior remains green.

## Success criteria
- A kickoff payload can immediately create `cycles/YYYY-MM-DD/<id>.md` and `.json` without inventing fake final artifacts.
- `python3 -m unittest tests.test_cycle_record tests.test_cycle_audit -v` stays green.
- README documents the safer kickoff path.
