# Stack Sleuth hotspot radar scoping notes

Date: 2026-04-29
Mode: Builder

Chosen direction: extend `stack-sleuth` with shared suspect-hotspot analysis so single traces, incident digests, and regression comparisons all surface the files or modules that keep showing up across failures.

Why this won:
- It compounds the strongest public repo instead of starting another shallow toy.
- Regression Radar now answers what changed between batches, but it still leaves a human to manually infer where to look first across multiple incidents.
- A hotspot layer creates a reusable engine that can power browser, CLI, and future package or ownership integrations.
- "What file path is lighting up across this release?" is outsider-legible and immediately useful.

Approaches considered:
1. Minimal viable: add a single top-culprit file summary for digest mode only.
2. Recommended: build a shared hotspot engine that rolls culprit and support frames into ranked suspect hotspots for single-trace, digest, and regression workflows.
3. Overreach path: enrich traces with git blame, package manifests, or deploy metadata.

Recommendation: ship the shared hotspot engine now. It gives Stack Sleuth a real blast-radius view without needing external services or repo-specific metadata.

Rejected directions:
- Another brand-new micro-repo, because Stack Sleuth has a clearer path to becoming a serious debugging tool.
- Git blame or owner-map integrations, because they would either be brittle or explode the one-cycle scope budget.
- Hosted history or dashboards, because deterministic local analysis is still the right wedge.