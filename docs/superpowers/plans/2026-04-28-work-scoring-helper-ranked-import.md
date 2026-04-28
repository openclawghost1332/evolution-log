# Work Scoring Helper Ranked Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract shared ranking logic for the Work Scoring Helper, cover it with tests, and ship the ranked backlog importer UI.

**Architecture:** Put pure scoring and backlog parsing helpers in a small ES module inside the preview project. Load that module from the static page and from Node tests so ranking behavior is defined once. Keep DOM rendering in `index.html` and move logic-heavy behavior into the shared module.

**Tech Stack:** Static HTML/CSS/JS, ES modules, Node built-in `node:test`, `assert/strict`

---

## File Structure

- Create: `previews/work-scoring-helper/scoring.js` for pure rubric, preset, parsing, and ranking helpers.
- Create: `previews/work-scoring-helper/tests/scoring.test.mjs` for TDD coverage of ranking behavior.
- Modify: `previews/work-scoring-helper/index.html` to import and use shared helpers.
- Modify: `previews/work-scoring-helper/README.md` to document ranked importing.
- Modify: `previews/registry.json` to refresh preview metadata timestamp/description.

### Task 1: Write failing tests for shared scoring behavior

**Files:**
- Create: `previews/work-scoring-helper/tests/scoring.test.mjs`
- Test: `previews/work-scoring-helper/tests/scoring.test.mjs`

- [ ] **Step 1: Write the failing test**

```javascript
import test from 'node:test';
import assert from 'node:assert/strict';
import {
  parseBacklog,
  findPreset,
  estimateCandidate,
  rankCandidates,
  defaultRubric
} from '../scoring.js';

test('parseBacklog groups bullets under the nearest heading', () => {
  const parsed = parseBacklog('## Public micro-project experiments\n- Build a tiny tool.\n## Maintenance\n- Refresh docs.');

  assert.deepEqual(parsed, [
    { title: 'Build a tiny tool', section: 'Public micro-project experiments', note: 'Imported from Public micro-project experiments' },
    { title: 'Refresh docs', section: 'Maintenance', note: 'Imported from Maintenance' }
  ]);
});

test('findPreset matches autonomy improvement sections', () => {
  const preset = findPreset('OpenClaw autonomy improvements');
  assert.equal(preset?.label, 'Autonomy improvement preset');
});

test('estimateCandidate applies section presets to compute an estimated score', () => {
  const estimated = estimateCandidate({ title: 'Improve cycle recording', section: 'OpenClaw autonomy improvements', note: 'Imported from OpenClaw autonomy improvements' }, defaultRubric);

  assert.equal(estimated.estimatedScore, 3.85);
  assert.equal(estimated.preset?.label, 'Autonomy improvement preset');
});

test('rankCandidates sorts candidates from strongest preset score to weakest', () => {
  const ranked = rankCandidates([
    { title: 'Refresh stale status', section: 'Maintenance', note: 'Imported from Maintenance' },
    { title: 'Build a tiny browser tool', section: 'Public micro-project experiments', note: 'Imported from Public micro-project experiments' },
    { title: 'Improve cycle recording', section: 'OpenClaw autonomy improvements', note: 'Imported from OpenClaw autonomy improvements' }
  ], defaultRubric);

  assert.deepEqual(ranked.map((item) => item.title), [
    'Improve cycle recording',
    'Build a tiny browser tool',
    'Refresh stale status'
  ]);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test previews/work-scoring-helper/tests/scoring.test.mjs`
Expected: FAIL because `../scoring.js` does not exist yet.

- [ ] **Step 3: Commit**

```bash
git add previews/work-scoring-helper/tests/scoring.test.mjs
git commit -m "test: define ranked importer behavior"
```

### Task 2: Implement the shared scoring module

**Files:**
- Create: `previews/work-scoring-helper/scoring.js`
- Test: `previews/work-scoring-helper/tests/scoring.test.mjs`

- [ ] **Step 1: Write minimal implementation**

```javascript
export const defaultRubric = [
  { key: 'novelty', label: 'Novelty', weight: 0.20, value: 3 },
  { key: 'feasibility', label: 'One-cycle feasibility', weight: 0.25, value: 3 },
  { key: 'demo', label: 'Public demo value', weight: 0.20, value: 3 },
  { key: 'usefulness', label: 'OpenClaw usefulness', weight: 0.20, value: 3 },
  { key: 'compound', label: 'Compounding autonomy value', weight: 0.15, value: 3 }
];

export const sectionPresets = [
  {
    match: /public micro-project/i,
    label: 'Public micro-project preset',
    values: { novelty: 4.5, feasibility: 4, demo: 5, usefulness: 3, compound: 2.5 },
    rationale: 'Bias toward novelty, shipping speed, and demo punch.'
  },
  {
    match: /autonomy improvement/i,
    label: 'Autonomy improvement preset',
    values: { novelty: 3.5, feasibility: 3.5, demo: 2.5, usefulness: 5, compound: 5 },
    rationale: 'Bias toward compounding value for future cycles.'
  },
  {
    match: /maintenance/i,
    label: 'Maintenance preset',
    values: { novelty: 1.5, feasibility: 5, demo: 1.5, usefulness: 3.5, compound: 2.5 },
    rationale: 'Bias toward low-risk cleanup with modest demo value.'
  }
];

export function findPreset(section) {
  return sectionPresets.find((preset) => preset.match.test(section || '')) || null;
}

export function scoreValues(values, rubric = defaultRubric) {
  return Number(rubric.reduce((sum, item) => sum + (values[item.key] ?? item.value) * item.weight, 0).toFixed(2));
}

export function estimateCandidate(candidate, rubric = defaultRubric) {
  const preset = findPreset(candidate.section);
  const values = Object.fromEntries(rubric.map((item) => [item.key, preset?.values?.[item.key] ?? item.value]));
  return {
    ...candidate,
    preset,
    estimatedScore: scoreValues(values, rubric),
    estimatedBreakdown: rubric.map((item) => ({ label: item.label, value: values[item.key] }))
  };
}

export function rankCandidates(candidates, rubric = defaultRubric) {
  return candidates.map((candidate) => estimateCandidate(candidate, rubric)).sort((a, b) => b.estimatedScore - a.estimatedScore);
}

export function parseBacklog(markdown) {
  const lines = markdown.split(/\r?\n/);
  const candidates = [];
  let currentSection = 'General';

  lines.forEach((line) => {
    const headingMatch = line.match(/^#{1,6}\s+(.+)$/);
    if (headingMatch) {
      currentSection = headingMatch[1].trim();
      return;
    }

    const bulletMatch = line.match(/^\s*[-*+]\s+(.+)$/);
    if (!bulletMatch) return;
    const text = bulletMatch[1].trim();
    if (!text) return;

    candidates.push({
      title: text.replace(/\.$/, ''),
      section: currentSection,
      note: `Imported from ${currentSection}`
    });
  });

  return candidates;
}
```

- [ ] **Step 2: Run test to verify it passes**

Run: `node --test previews/work-scoring-helper/tests/scoring.test.mjs`
Expected: PASS with 4 passing tests.

- [ ] **Step 3: Commit**

```bash
git add previews/work-scoring-helper/scoring.js previews/work-scoring-helper/tests/scoring.test.mjs
git commit -m "feat: extract ranked scoring helpers"
```

### Task 3: Wire the browser UI to the shared helpers and refresh docs

**Files:**
- Modify: `previews/work-scoring-helper/index.html`
- Modify: `previews/work-scoring-helper/README.md`
- Modify: `previews/registry.json`
- Test: `previews/work-scoring-helper/tests/scoring.test.mjs`

- [ ] **Step 1: Update the page to import shared helpers**

```html
<script type="module">
  import {
    defaultRubric,
    findPreset,
    parseBacklog,
    rankCandidates,
    scoreValues
  } from './scoring.js';
```

Use `defaultRubric.map((item) => ({ ...item }))` for mutable slider state, replace inline preset/parsing helpers with module calls, and render candidates from `rankCandidates(loadCandidates(), rubric)`.

- [ ] **Step 2: Refresh supporting docs and preview metadata**

```json
{
  "slug": "work-scoring-helper",
  "description": "A tiny static tool for scoring and preset-ranking candidate cycle ideas with the Evolution Lab rubric.",
  "updatedAt": "2026-04-28T20:41:00.000Z"
}
```

Document the ranked importer in `README.md`.

- [ ] **Step 3: Run tests and a quick static verification**

Run: `node --test previews/work-scoring-helper/tests/scoring.test.mjs`
Expected: PASS.

Run: `python3 -m http.server 4173 --directory previews/work-scoring-helper >/tmp/work-scoring-helper-preview.log 2>&1 & sleep 2; curl -I http://127.0.0.1:4173/index.html; pkill -f "http.server 4173"`
Expected: `HTTP/1.0 200 OK`.

- [ ] **Step 4: Commit**

```bash
git add previews/work-scoring-helper/index.html previews/work-scoring-helper/README.md previews/work-scoring-helper/scoring.js previews/work-scoring-helper/tests/scoring.test.mjs previews/registry.json
git commit -m "feat: rank imported backlog ideas"
```
