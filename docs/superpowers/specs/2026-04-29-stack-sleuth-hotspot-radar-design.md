# Stack Sleuth Hotspot Radar Design

Date: 2026-04-29
Status: approved for autonomous cron execution

## Problem statement
Stack Sleuth can already explain a single trace, group repeated incidents, and compare two batches with Regression Radar. But once several incidents surface, the user still has to manually infer the blast radius. The next slice should answer a sharper triage question: which application files or modules keep showing up across these failures, and how did that suspect surface shift between baseline and candidate batches?

## Approaches considered
1. Minimal viable, count only top culprit files for digest mode. Fastest, but too narrow and not reusable.
2. Recommended, add a shared hotspot engine that ranks suspect surfaces from culprit and support frames and reuses it in single-trace, digest, and regression workflows.
3. Overreach, enrich traces with git blame, owner maps, or deploy metadata. Strong future direction, but too much external coupling for this cycle.

## Chosen approach
Ship a shared hotspot engine that normalizes application frame paths into ranked suspect hotspots. Single-trace analysis should expose the local suspect surface around one failure. Incident digests should aggregate hotspot counts across repeated incidents. Regression Radar should compare baseline and candidate hotspot maps so a user can see not only which signatures changed, but also which application surfaces are heating up or cooling down.

## Architecture
The product becomes four layered pieces:
1. trace parsing and diagnosis
2. single-trace report normalization
3. digest and regression aggregation
4. new hotspot extraction and comparison shared across all of the above

`src/hotspots.js` should stay independent from UI rendering. It should accept normalized reports or digest groups, compute deterministic hotspot summaries, and return JSON-friendly structures. `analyzeTrace`, `analyzeTraceDigest`, and `analyzeRegression` can then attach hotspot summaries without duplicating rules.

## Components
- `src/hotspots.js`: normalize frame paths, rank single-report hotspots, aggregate digest hotspots, compare regression hotspot shifts
- `src/analyze.js`: attach single-trace hotspots and render them in text and Markdown summaries
- `src/digest.js`: add aggregated digest hotspots and render them in text and Markdown summaries
- `src/regression.js`: attach hotspot shifts and render them in text and Markdown summaries
- `bin/stack-sleuth.js`: preserve existing routing while surfacing enriched JSON/text/Markdown payloads
- `src/main.js`: show suspect hotspots for explain and digest flows plus hotspot shifts for regression mode
- `index.html` and `styles.css`: add cards without breaking the current phone-friendly layout
- `src/examples.js`, `README.md`, and tests: keep public demos and docs aligned

## Data flow
1. Parse a trace into a report with culprit and support frames.
2. Hotspot extraction normalizes application paths into stable labels such as `billing/invoice.js` or `service.py`.
3. Single-trace analysis ranks hotspots by culprit hits first, then support hits.
4. Digest aggregation multiplies hotspot counts by incident frequency so repeated failures surface the hottest paths.
5. Regression comparison builds hotspot maps for baseline and candidate digests, classifies shifts with the same new/recurring/resolved/volume-up/volume-down vocabulary, and ranks the most urgent suspect surfaces first.
6. Browser and CLI render hotspot sections alongside incident-level details.

## Hotspot behavior
- Use only application-facing file paths from culprit and support frames. Internal runtime frames stay excluded.
- Keep normalization deterministic and explainable. Prefer concise path labels over opaque hashes.
- Preserve incident signatures. Hotspots guide where to look first, but signatures still anchor exact failures.
- JSON output should include hotspot arrays that downstream tools can reuse.

## Browser behavior
- Keep the current explain, digest, and regression flows intact.
- Add a suspect-hotspots card for single-trace and digest modes.
- Add a hotspot-shifts card for regression mode.
- Empty states should explain what will appear there instead of showing stale results.

## CLI behavior
- Preserve current single-trace, digest, and compare modes.
- Text and Markdown summaries should add compact hotspot sections.
- JSON mode should expose the structured hotspot arrays without special flags.

## Error handling
- Reports with no application frames should return empty hotspot arrays, not crash.
- Digest and regression rendering must tolerate zero hotspots.
- Path normalization must handle POSIX paths, Windows paths, and file URLs consistently.

## Testing
Follow TDD throughout.
- hotspot-engine tests for normalization, ranking, digest aggregation, and regression shift classification
- summary renderer tests for single-trace, digest, and regression hotspot sections
- browser-copy, example, README, and CLI tests to keep the public surface honest
- full `npm test` before publish

## Success criteria
- A user can spot the hottest suspect files or modules without manually scanning every incident.
- Regression Radar highlights both signature shifts and suspect-surface shifts between batches.
- The public repo reads like a real blast-radius debugging tool, not just a trace explainer.