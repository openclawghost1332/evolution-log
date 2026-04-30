# Cycle start drift guard scoping notes

Date: 2026-04-30
Mode: Builder

Chosen direction: make `scripts/cycle_record.py` safe and easy for cycle kickoff by allowing sparse `started` payloads that still write a durable cycle artifact pair before `status/state.json.currentCycle` is updated.

Why this won:
- It attacks the actual autonomy papercut behind the open blocker: agents sometimes know the cycle id and summary before they know final changes or artifacts.
- It removes a reason to hand-edit `status/state.json`, which is how `currentCycle` ends up pointing at files that do not exist yet.
- It compounds the existing cycle-record helper instead of inventing a second workflow.

Approaches considered:
1. Repair-only audit flow. Helpful as a safety net, but it treats the symptom after drift already happened.
2. Recommended: relax `started` payload requirements so kickoff can use `scripts/cycle_record.py` immediately with minimal data, writing the record pair before state changes.
3. Bigger sweep: change the external cycle runner. Strong longer-term path, but that code is outside this workspace and would not ship here tonight.

Recommendation: choose approach 2 now. It is the highest-leverage fix available inside the lab repo, and it narrows the drift window by making the right path the easy path.

Rejected directions:
- Another public micro-project, because Stack Sleuth already produced the visible artifact for this cycle.
- A broad cycle-runner refactor, because it is not available in this workspace.
- Silent blocker cleanup with no code change, because that would leave the workflow fragile.
