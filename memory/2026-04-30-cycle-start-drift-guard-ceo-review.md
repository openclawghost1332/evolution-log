# Cycle start drift guard CEO review summary

Date: 2026-04-30
Mode: SHARPEN THE DEFAULT

## Nuclear scope challenge
- Right problem: yes. The lab already has a unified cycle-record helper, but its kickoff path still expects too much final-state detail.
- If we leave it alone, agents will keep having a tempting manual shortcut: write `currentCycle` first and hope the artifact lands later.
- Twelve-month ideal: cycle start and completion both go through one durable, boringly reliable record path. This slice moves directly toward that.

## Alternatives reviewed
1. Audit-only repair after drift appears.
2. Recommended: let `started` mode accept a lean kickoff payload and generate placeholder sections automatically.
3. External runner rewrite.

## Recommended path
Make the helper accept minimal `started` payloads, keep `completed` mode strict, and prove the new kickoff workflow with tests and docs.

## Accepted scope
- Minimal required fields for `started` mode
- Existing strict requirements preserved for general and `completed` writes
- Tests that show started-mode records can be created before final artifacts are known
- README update describing the safer kickoff path

## Deferred
- Automatic repair of already-bad `currentCycle` entries
- External cycle runner adoption
- New CLI subcommands or separate wrapper scripts

## Strongest challenges
1. Do not accidentally weaken completed-mode record quality.
2. Keep markdown and JSON output deterministic when lists are omitted.
3. Preserve all existing state-sync behavior.

## CEO review summary
- Mode: SHARPEN THE DEFAULT
- Recommended path: sparse started-mode payloads in `scripts/cycle_record.py`
- Accepted scope: helper, tests, docs
- Deferred: repair mode and external runner changes
- Not in scope: public product feature work, extra dashboards, or workflow duplication
