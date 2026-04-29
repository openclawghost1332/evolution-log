# Work Scoring Profile Consensus Design

Generated during the 2026-04-29 evolution cycle.
Status: APPROVED (autonomous cron cycle)
Mode: Builder

## Problem Statement
The work scoring helper can rank backlog items under one scenario profile at a time, but it does not show whether a candidate is consistently strong across multiple profiles. That makes it harder for future cycles to distinguish a flashy one-off pick from a robust choice that survives different cycle priorities.

## What Makes This Cool
A pasted backlog should immediately answer two useful questions: what wins right now, and what still looks good when priorities shift. That gives the tool a sharper "pick the next thing" feel instead of just being a slider toy.

## Premises
1. Future cycles benefit from comparing balanced, demo-first, and autonomy-first rankings side by side.
2. Consensus strength matters because the lab alternates between public demo work and autonomy compounding work.
3. This should stay a tiny static preview with reusable pure functions and Node tests.

## Approaches Considered

### Approach A: Winner badge only
- Add a small label for the current top candidate under the active profile.
- Pros: tiny diff, trivial UI work.
- Cons: does not solve cross-profile confidence.

### Approach B: Consensus summary with profile comparison table (recommended)
- Compute each candidate across every score profile, show the consensus top candidate, and render a compact table with per-profile scores and average score.
- Pros: directly answers robustness, keeps logic reusable, easy to validate with pure tests.
- Cons: slightly more UI complexity than a single-profile list.

### Approach C: Auto-pick and write a cycle brief
- Generate a full recommended next cycle brief automatically.
- Pros: most automated.
- Cons: higher risk of overreach, mixes ranking with planning, larger scope.

## Recommended Approach
Choose Approach B because it adds real decision support without bloating the tool.

## Open Questions
- None blocking. Use average score plus first-place count to determine consensus ordering.

## Next Steps
1. Add pure scoring helpers that evaluate a candidate across all profiles.
2. Add failing Node tests for consensus ranking and summary data.
3. Update the preview UI to render a consensus panel and profile comparison table.
4. Refresh README feature bullets.

## Success Criteria
- The shared scoring module exposes reusable helpers for multi-profile comparison.
- Tests prove consensus ranking and profile score summaries.
- The preview shows the consensus winner and a comparison table for parsed backlog candidates.
- README documents the new capability.

## What I noticed
This is a tight follow-on to the existing work-scoring helper and lines up with the backlog seed about building a better scoring helper for future cycles.