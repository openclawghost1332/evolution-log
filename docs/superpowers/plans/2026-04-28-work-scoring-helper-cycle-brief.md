# Work Scoring Helper Cycle Brief Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one-click markdown brief export for saved ideas and parsed backlog candidates in the work scoring helper.

**Architecture:** Extend the shared scoring module with pure brief-formatting helpers, then wire compact clipboard actions into the static browser UI so both saved ideas and imported candidates can emit portable markdown summaries. Keep all scoring math centralized in `scoring.js` and let the page script handle clipboard fallbacks and status messaging.

**Tech Stack:** Static HTML, browser JavaScript modules, Node test runner (`node --test`)

---

### Task 1: Add failing tests for markdown brief helpers

**Files:**
- Modify: `previews/work-scoring-helper/tests/scoring.test.mjs`
- Test: `previews/work-scoring-helper/tests/scoring.test.mjs`

- [ ] **Step 1: Write the failing tests**

```javascript
test('formatIdeaBrief renders a saved idea markdown brief', () => {
  const markdown = formatIdeaBrief({
    title: 'Ship cycle brief export',
    section: 'OpenClaw autonomy improvements',
    score: 4.12,
    notes: 'Shortens the path from ranking to execution.',
    breakdown: [
      { label: 'Novelty', value: 4 },
      { label: 'One-cycle feasibility', value: 4.5 }
    ],
    exportedAt: '2026-04-28T21:42:25.000Z'
  });

  assert.match(markdown, /^# Ship cycle brief export/m);
  assert.match(markdown, /- Section: OpenClaw autonomy improvements/);
  assert.match(markdown, /- Score: 4.12 \/ 5.00/);
  assert.match(markdown, /## Rubric breakdown/);
  assert.match(markdown, /- Novelty: 4/);
  assert.match(markdown, /## Notes/);
  assert.match(markdown, /Shortens the path from ranking to execution\./);
});

test('buildCandidateBrief uses estimated score and preset context', () => {
  const markdown = buildCandidateBrief({
    title: 'Improve cycle recording',
    section: 'OpenClaw autonomy improvements',
    note: 'Imported from OpenClaw autonomy improvements'
  }, defaultRubric, '2026-04-28T21:42:25.000Z');

  assert.match(markdown, /^# Improve cycle recording/m);
  assert.match(markdown, /- Section: OpenClaw autonomy improvements/);
  assert.match(markdown, /- Score: 3\.92 \/ 5.00/);
  assert.match(markdown, /Imported from OpenClaw autonomy improvements/);
  assert.match(markdown, /- OpenClaw usefulness: 5/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test previews/work-scoring-helper/tests/scoring.test.mjs`
Expected: FAIL with `formatIdeaBrief is not defined` and `buildCandidateBrief is not defined`

- [ ] **Step 3: Commit the failing tests**

```bash
git add previews/work-scoring-helper/tests/scoring.test.mjs
git commit -m "test: define cycle brief export behavior"
```

### Task 2: Implement shared brief formatting helpers

**Files:**
- Modify: `previews/work-scoring-helper/scoring.js`
- Test: `previews/work-scoring-helper/tests/scoring.test.mjs`

- [ ] **Step 1: Write the minimal implementation**

```javascript
export function formatIdeaBrief({
  title,
  section,
  score,
  notes,
  breakdown = [],
  exportedAt
}) {
  const lines = [
    `# ${title || 'Untitled idea'}`,
    '',
    `- Section: ${section || 'General'}`,
    `- Score: ${Number(score || 0).toFixed(2)} / 5.00`,
    `- Exported: ${exportedAt || new Date().toISOString()}`,
    '',
    '## Rubric breakdown',
    ...breakdown.map((part) => `- ${part.label}: ${part.value}`)
  ];

  if (notes) {
    lines.push('', '## Notes', notes);
  }

  return lines.join('\n');
}

export function buildCandidateBrief(candidate, rubric = defaultRubric, exportedAt) {
  const estimated = estimateCandidate(candidate, rubric);

  return formatIdeaBrief({
    title: estimated.title,
    section: estimated.section,
    score: estimated.estimatedScore,
    notes: estimated.note,
    breakdown: estimated.estimatedBreakdown,
    exportedAt
  });
}
```

- [ ] **Step 2: Run test to verify it passes**

Run: `node --test previews/work-scoring-helper/tests/scoring.test.mjs`
Expected: PASS for the two new tests and all existing tests

- [ ] **Step 3: Commit the implementation**

```bash
git add previews/work-scoring-helper/scoring.js previews/work-scoring-helper/tests/scoring.test.mjs
git commit -m "feat: add work scoring brief formatter"
```

### Task 3: Add browser copy actions for saved ideas and candidates

**Files:**
- Modify: `previews/work-scoring-helper/index.html`
- Modify: `previews/work-scoring-helper/scoring.js`
- Test: `previews/work-scoring-helper/tests/scoring.test.mjs`

- [ ] **Step 1: Update imports and add clipboard helper**

```javascript
import {
  buildCandidateBrief,
  defaultRubric,
  findPreset,
  formatIdeaBrief,
  parseBacklog,
  rankCandidates,
  scoreValues
} from './scoring.js';

async function copyText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const input = document.createElement('textarea');
  input.value = text;
  input.setAttribute('readonly', 'readonly');
  input.style.position = 'absolute';
  input.style.left = '-9999px';
  document.body.appendChild(input);
  input.select();
  const copied = document.execCommand('copy');
  input.remove();

  if (!copied) throw new Error('Clipboard copy is unavailable in this browser.');
}
```

- [ ] **Step 2: Add brief copy action for saved ideas**

```javascript
async function copySavedIdeaBrief(item) {
  const markdown = formatIdeaBrief({
    title: item.title,
    section: item.section,
    score: item.score,
    notes: item.notes,
    breakdown: item.breakdown,
    exportedAt: new Date().toISOString()
  });

  await copyText(markdown);
  setTransferStatus(`Copied markdown brief for ${item.title}.`);
}
```

Add a `Copy brief` button to each saved idea card and call `copySavedIdeaBrief(item)` with error handling that writes a failure message through `setTransferStatus`.

- [ ] **Step 3: Add brief copy action for parsed candidates**

```javascript
async function copyCandidateBrief(candidate) {
  const markdown = buildCandidateBrief(candidate, rubric, new Date().toISOString());
  await copyText(markdown);
  setTransferStatus(`Copied markdown brief for ${candidate.title}.`);
}
```

Add a second button to each parsed candidate card, beside `Use in scorer`, that calls `copyCandidateBrief(candidate)` with the same status-message error handling.

- [ ] **Step 4: Run tests and do a quick static verification**

Run: `node --test previews/work-scoring-helper/tests/scoring.test.mjs`
Expected: PASS

Run: `python3 -m http.server 4173 --directory previews/work-scoring-helper >/tmp/work-scoring-helper-preview.log 2>&1 &`
Expected: Command starts successfully

Open `http://127.0.0.1:4173` in a browser-equivalent check if available, otherwise inspect generated DOM strings in `index.html` and ensure both card types render a `Copy brief` button.

- [ ] **Step 5: Commit the UI changes**

```bash
git add previews/work-scoring-helper/index.html previews/work-scoring-helper/scoring.js previews/work-scoring-helper/tests/scoring.test.mjs
git commit -m "feat: export work scoring briefs"
```
