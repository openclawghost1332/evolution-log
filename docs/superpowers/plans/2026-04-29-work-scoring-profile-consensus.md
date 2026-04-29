# Work Scoring Profile Consensus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add consensus ranking and cross-profile comparison to the work scoring helper so future cycles can see which backlog item stays strong across multiple priority mixes.

**Architecture:** Extend `scoring.js` with pure helpers that score candidates across all profiles and return UI-ready comparison data. Keep the browser UI in `index.html` as a thin renderer over those helpers, then document the new behavior in the preview README.

**Tech Stack:** Static HTML, browser-side ES modules, Node test runner.

---

### Task 1: Add consensus scoring helpers and tests

**Files:**
- Modify: `previews/work-scoring-helper/tests/scoring.test.mjs`
- Modify: `previews/work-scoring-helper/scoring.js`

- [ ] **Step 1: Write the failing tests**

```javascript
test('summarizeCandidateProfiles returns per-profile scores and average score', () => {
  const summary = summarizeCandidateProfiles({
    title: 'Improve cycle recording',
    section: 'OpenClaw autonomy improvements',
    note: 'Imported from OpenClaw autonomy improvements'
  });

  assert.equal(summary.profileScores.length, 3);
  assert.equal(summary.profileScores[0].profileId, 'balanced');
  assert.equal(typeof summary.averageScore, 'number');
});

test('rankCandidatesByConsensus orders candidates by average score and profile wins', () => {
  const ranked = rankCandidatesByConsensus([
    { title: 'Build flashy preview', section: 'Public micro-project experiments', note: 'Imported from Public micro-project experiments' },
    { title: 'Improve internal recorder', section: 'OpenClaw autonomy improvements', note: 'Imported from OpenClaw autonomy improvements' }
  ]);

  assert.equal(ranked[0].title, 'Improve internal recorder');
  assert.equal(typeof ranked[0].profileWinCount, 'number');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test previews/work-scoring-helper/tests/scoring.test.mjs`
Expected: FAIL with missing export or undefined helper errors.

- [ ] **Step 3: Write minimal implementation**

```javascript
export function summarizeCandidateProfiles(candidate) {
  const profileScores = scoreProfiles.map((profile) => ({
    profileId: profile.id,
    profileLabel: profile.label,
    score: estimateCandidate(candidate, profile.rubric).estimatedScore
  }));

  return {
    ...candidate,
    profileScores,
    averageScore: Number((profileScores.reduce((sum, item) => sum + item.score, 0) / profileScores.length).toFixed(2))
  };
}
```

Add a consensus rank helper that sorts by average score, then profile win count, then balanced score.

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test previews/work-scoring-helper/tests/scoring.test.mjs`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add previews/work-scoring-helper/scoring.js previews/work-scoring-helper/tests/scoring.test.mjs
git commit -m "feat: add work scoring consensus helpers"
```

### Task 2: Render consensus comparison in the preview and docs

**Files:**
- Modify: `previews/work-scoring-helper/index.html`
- Modify: `previews/work-scoring-helper/README.md`
- Test: `previews/work-scoring-helper/tests/scoring.test.mjs`

- [ ] **Step 1: Write the failing test**

Add an assertion that consensus helper output includes data needed by the UI:

```javascript
test('rankCandidatesByConsensus returns table-ready profile labels', () => {
  const ranked = rankCandidatesByConsensus([
    { title: 'Build flashy preview', section: 'Public micro-project experiments', note: 'Imported from Public micro-project experiments' }
  ]);

  assert.deepEqual(ranked[0].profileScores.map((item) => item.profileLabel), [
    'Balanced',
    'Demo first',
    'Autonomy first'
  ]);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test previews/work-scoring-helper/tests/scoring.test.mjs`
Expected: FAIL until helper output matches the UI contract.

- [ ] **Step 3: Write minimal implementation**

Update `index.html` to:

```javascript
import { rankCandidatesByConsensus } from './scoring.js';
```

Render a new panel that shows:
- consensus winner title
- average score
- profile win count
- table of all candidates with Balanced, Demo first, Autonomy first, Average, and Wins columns

Update `README.md` feature bullets to mention cross-profile consensus ranking.

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test previews/work-scoring-helper/tests/scoring.test.mjs`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add previews/work-scoring-helper/index.html previews/work-scoring-helper/README.md previews/work-scoring-helper/tests/scoring.test.mjs
git commit -m "feat: show consensus work scoring comparison"
```