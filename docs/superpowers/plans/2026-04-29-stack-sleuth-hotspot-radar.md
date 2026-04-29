# Stack Sleuth Hotspot Radar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend Stack Sleuth with shared suspect-hotspot analysis that surfaces ranked files or modules across single-trace, digest, and regression workflows in the engine, CLI, browser demo, and docs.

**Architecture:** Add a new `src/hotspots.js` layer that derives deterministic hotspot summaries from culprit and support frames, then reuse it from `analyzeTrace`, `analyzeTraceDigest`, and `analyzeRegression`. Keep extraction logic, renderer updates, and browser presentation separated so text, Markdown, JSON, and the demo all share the same normalized hotspot payloads.

**Tech Stack:** Vanilla JavaScript, Node.js test runner, static browser UI, existing Stack Sleuth CLI/demo structure

---

### Task 1: Build the shared hotspot engine with TDD

**Files:**
- Create: `projects/stack-sleuth/src/hotspots.js`
- Create: `projects/stack-sleuth/tests/hotspots.test.mjs`
- Modify: `projects/stack-sleuth/src/analyze.js`
- Modify: `projects/stack-sleuth/src/digest.js`
- Modify: `projects/stack-sleuth/src/regression.js`

- [ ] **Step 1: Write the failing hotspot tests**

```javascript
import test from 'node:test';
import assert from 'node:assert/strict';
import {
  extractReportHotspots,
  summarizeDigestHotspots,
  compareHotspots
} from '../src/hotspots.js';

test('extractReportHotspots ranks culprit and support surfaces with normalized labels', () => {
  const hotspots = extractReportHotspots({ culpritFrame, supportFrames });

  assert.deepEqual(hotspots[0], {
    key: 'billing/invoice.js',
    label: 'billing/invoice.js',
    culpritHits: 1,
    supportHits: 0,
    totalHits: 1,
    traceCount: 1,
    signatures: []
  });
});

test('summarizeDigestHotspots multiplies hotspot counts by incident frequency', () => {
  const hotspots = summarizeDigestHotspots(digest);
  assert.equal(hotspots[0].traceCount, 3);
});

test('compareHotspots classifies hotspot shifts across baseline and candidate batches', () => {
  const comparison = compareHotspots(baselineHotspots, candidateHotspots);
  assert.equal(comparison[0].status, 'new');
  assert.equal(comparison[1].status, 'volume-up');
});
```

- [ ] **Step 2: Run the hotspot test file and verify it fails for the missing module**

Run: `cd /home/node/.openclaw/workspace/projects/stack-sleuth && node --test tests/hotspots.test.mjs`
Expected: FAIL with a module-not-found or missing-export error for `src/hotspots.js`

- [ ] **Step 3: Write the minimal hotspot engine and wire it into analysis payloads**

```javascript
export function extractReportHotspots(report) {
  const frames = [report.culpritFrame, ...(report.supportFrames ?? [])].filter((frame) => frame?.file);
  const byKey = new Map();

  frames.forEach((frame, index) => {
    const key = toHotspotKey(frame.file);
    if (!key) return;
    const hotspot = byKey.get(key) ?? createHotspot(key);
    hotspot.traceCount = 1;
    if (index === 0) hotspot.culpritHits += 1;
    else hotspot.supportHits += 1;
    byKey.set(key, hotspot);
  });

  return [...byKey.values()].map(finalizeHotspot).sort(compareHotspotTotals);
}
```

- [ ] **Step 4: Run the hotspot tests and the related engine tests until they pass**

Run: `cd /home/node/.openclaw/workspace/projects/stack-sleuth && node --test tests/hotspots.test.mjs tests/diagnose.test.mjs tests/regression.test.mjs`
Expected: PASS with hotspot extraction and aggregation coverage green

- [ ] **Step 5: Commit the engine slice**

```bash
cd /home/node/.openclaw/workspace/projects/stack-sleuth
git add src/hotspots.js src/analyze.js src/digest.js src/regression.js tests/hotspots.test.mjs
git commit -m "feat: add stack sleuth hotspot engine"
```

### Task 2: Surface hotspots through summaries, CLI, and browser state with TDD

**Files:**
- Modify: `projects/stack-sleuth/src/analyze.js`
- Modify: `projects/stack-sleuth/src/digest.js`
- Modify: `projects/stack-sleuth/src/regression.js`
- Modify: `projects/stack-sleuth/bin/stack-sleuth.js`
- Modify: `projects/stack-sleuth/src/main.js`
- Modify: `projects/stack-sleuth/index.html`
- Modify: `projects/stack-sleuth/styles.css`
- Modify: `projects/stack-sleuth/tests/cli.test.mjs`
- Modify: `projects/stack-sleuth/tests/browser-copy.test.mjs`

- [ ] **Step 1: Write the failing public-surface tests**

```javascript
test('single-trace and digest summaries include suspect hotspots', () => {
  const report = analyzeTrace(sampleTrace);
  assert.match(renderTextSummary(report), /Suspect hotspots/i);
});

test('regression summaries include hotspot shifts', () => {
  const radar = analyzeRegression({ baseline, candidate });
  assert.match(renderRegressionTextSummary(radar), /Hotspot shifts/i);
});

test('browser copy mentions suspect hotspots and hotspot shifts', () => {
  assert.match(indexHtml, /Suspect hotspots/i);
  assert.match(indexHtml, /Hotspot shifts/i);
});
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `cd /home/node/.openclaw/workspace/projects/stack-sleuth && node --test tests/cli.test.mjs tests/browser-copy.test.mjs tests/hotspots.test.mjs`
Expected: FAIL because hotspot sections are not rendered yet

- [ ] **Step 3: Implement minimal renderer and browser state updates**

```javascript
const hotspotItems = report.hotspots?.length
  ? report.hotspots.map((hotspot) => `${hotspot.traceCount}x ${hotspot.label}`)
  : ['No suspect hotspots detected yet.'];

hotspotsValue.replaceChildren(...buildListItems(hotspotItems));
```

- [ ] **Step 4: Re-run the focused tests until they pass**

Run: `cd /home/node/.openclaw/workspace/projects/stack-sleuth && node --test tests/cli.test.mjs tests/browser-copy.test.mjs tests/regression.test.mjs`
Expected: PASS with hotspot sections visible in text, Markdown, JSON, and browser copy

- [ ] **Step 5: Commit the surface slice**

```bash
cd /home/node/.openclaw/workspace/projects/stack-sleuth
git add bin/stack-sleuth.js src/main.js index.html styles.css tests/cli.test.mjs tests/browser-copy.test.mjs
git commit -m "feat: show stack sleuth suspect hotspots"
```

### Task 3: Update examples, docs, and verification for the public artifact

**Files:**
- Modify: `projects/stack-sleuth/src/examples.js`
- Modify: `projects/stack-sleuth/README.md`
- Modify: `projects/stack-sleuth/tests/examples.test.mjs`
- Modify: `projects/stack-sleuth/tests/readme.test.mjs`

- [ ] **Step 1: Write the failing docs/tests for hotspot positioning**

```javascript
test('examples describe hotspot-oriented regression triage', () => {
  const regressionExample = examples.find((item) => item.label === 'Regression radar');
  assert.match(regressionExample.caption, /hotspot|blast radius|suspect/i);
});

test('README documents suspect hotspots in browser and CLI workflows', () => {
  const readme = fs.readFileSync(readmePath, 'utf8');
  assert.match(readme, /suspect hotspots/i);
  assert.match(readme, /hotspot shifts/i);
});
```

- [ ] **Step 2: Run the docs/tests and verify they fail**

Run: `cd /home/node/.openclaw/workspace/projects/stack-sleuth && node --test tests/examples.test.mjs tests/readme.test.mjs`
Expected: FAIL because the public copy does not mention hotspots yet

- [ ] **Step 3: Update examples and README with hotspot workflows**

```markdown
Regression Radar now includes hotspot shifts so you can see not only which signatures changed, but also which files or modules are heating up across the candidate batch.
```

- [ ] **Step 4: Run the full suite and make sure it passes**

Run: `cd /home/node/.openclaw/workspace/projects/stack-sleuth && npm test`
Expected: PASS with all Stack Sleuth tests green

- [ ] **Step 5: Commit the docs slice**

```bash
cd /home/node/.openclaw/workspace/projects/stack-sleuth
git add src/examples.js README.md tests/examples.test.mjs tests/readme.test.mjs
git commit -m "docs: add stack sleuth hotspot workflows"
```
