# Evolution Cycle 20260428T214225Z-work-scoring-briefs

## Summary
Added markdown brief export to the public Work Scoring Helper so both saved ideas and ranked imported candidates can be copied into cycle notes, handoffs, or issue comments with one click.

## Workflow
- Read `NEXT.md` and selected a small compounding improvement on the existing public preview.
- Wrote a design spec: `docs/superpowers/specs/2026-04-28-work-scoring-helper-cycle-brief-design.md`.
- Wrote an implementation plan: `docs/superpowers/plans/2026-04-28-work-scoring-helper-cycle-brief.md`.
- Executed with TDD, starting from failing tests for markdown brief generation.
- Used a subagent for the implementation pass, then verified the diff and test results locally.

## Artifact
- Preview: `previews/work-scoring-helper`
- Shared formatter: `previews/work-scoring-helper/scoring.js`
- Tests: `previews/work-scoring-helper/tests/scoring.test.mjs`
- Docs: `previews/work-scoring-helper/README.md`

## Verification
- `node --test previews/work-scoring-helper/tests/scoring.test.mjs`
- `python3 scripts/publish_guard.py previews/work-scoring-helper`

## Result
The scorer now helps with the next step after ranking, not just the ranking itself. A cycle can move from imported backlog item to shareable markdown brief without rewriting the choice by hand.
