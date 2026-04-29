# Stack Sleuth hotspot radar CEO review summary

Date: 2026-04-29
Mode: SELECTIVE EXPANSION

## Nuclear scope challenge
- Right problem: yes. Stack Sleuth can already explain incidents and compare batches, but it still does not answer the triage question that decides the next action: which application paths are repeatedly implicated across the noise?
- Doing nothing leaves the product as a signature viewer instead of a blast-radius prioritization tool.
- Twelve-month ideal: Stack Sleuth becomes a deterministic incident triage toolkit with reusable layers for explain, digest, compare, and suspect-surface ranking. This cycle moves straight toward that shape.

## Alternatives reviewed
1. Minimal viable: digest-only top culprit file counts.
2. Ideal architecture: shared hotspot engine reused by single-trace, digest, regression, CLI, and browser flows.
3. Overreach path: repo-aware ownership or blame enrichment using git/package metadata.

Recommendation: ship the shared hotspot engine plus browser and CLI output now, and explicitly defer repo-aware enrichment.

## Strongest challenges
1. Keep hotspot normalization explainable. Users should understand why `/app/src/billing/invoice.js` and `/app/src/billing/index.js` may collapse into a shared surface or not.
2. Do not bury incident-level details. Hotspots should guide triage, not replace signatures.
3. Hold the line on scope. No git access, no owner databases, no persistence in this cycle.

## Accepted scope
- Shared hotspot extraction from culprit and support frames
- Ranked hotspot summaries for single-trace, digest, and regression workflows
- Regression hotspot shifts that classify new, recurring, resolved, volume-up, and volume-down suspect surfaces
- Browser cards for suspect hotspots and hotspot shifts
- CLI text, Markdown, and JSON output that includes hotspot data
- Tests, docs, public repo update, and preview mirror

## Deferred
- Git blame, commit suspect scoring, and package-owner maps
- Historical hotspot trends across many runs
- Importing structured telemetry or source maps
- Package publishing

## Not in scope
- Hosted backend
- Upload storage
- User accounts
- AI remediation suggestions