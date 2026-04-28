# Work Scoring Helper

A tiny static tool for ranking candidate Evolution Lab ideas using the cycle rubric:

- Novelty
- One-cycle feasibility
- Public demo value
- OpenClaw usefulness
- Compounding autonomy value

## Current features

- Paste markdown from `NEXT.md` or another backlog.
- Parse bullet items into candidate cards grouped by section heading.
- Preset-rank imported candidates so the strongest backlog option floats to the top immediately.
- Click any parsed candidate to send it straight into the scorer.
- Apply section-aware default rubric suggestions when using imported candidates.
- Export saved scored ideas as JSON.
- Import saved JSON bundles back into the browser tool.
- Reuse shared ranking logic from `scoring.js`, with Node tests in `tests/scoring.test.mjs`.

Open `index.html` in the preview host to score ideas, compare options, keep lightweight decision notes in local storage, move saved ideas between browsers or sessions, and start from smarter default scores plus instant preset-based ranking for backlog sections.
