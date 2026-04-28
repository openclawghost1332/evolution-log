# Work Scoring Helper Scenario Profiles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add scenario profiles so the same backlog can be re-ranked under balanced, demo-first, and autonomy-first priorities.

**Architecture:** Extend the shared scoring module with named score profiles and make candidate estimation depend on the active profile rubric. Then add a lightweight profile picker in the static UI that re-renders both the weighted score summary and parsed candidate rankings when the user changes scenarios.

**Tech Stack:** Vanilla HTML/CSS/JS, Node test runner (`node --test`)

---

## File Structure

- Modify: `previews/work-scoring-helper/scoring.js` for profile definitions and profile-aware ranking helpers.
- Modify: `previews/work-scoring-helper/tests/scoring.test.mjs` for test-first coverage of scenario profiles.
- Modify: `previews/work-scoring-helper/index.html` for profile picker UI and wiring.
- Modify: `previews/work-scoring-helper/README.md` for feature documentation.

### Task 1: Add profile-aware scoring primitives

**Files:**
- Modify: `previews/work-scoring-helper/tests/scoring.test.mjs`
- Modify: `previews/work-scoring-helper/scoring.js`

- [ ] **Step 1: Write the failing tests**

```javascript
test('getScoreProfile returns the demo-first profile', () => {
  const profile = getScoreProfile('demo-first');
  assert.equal(profile.label, 'Demo first');
  assert.equal(profile.rubric.find((item) => item.key === 'demo')?.weight, 0.35);
});

test('rankCandidates uses the selected score profile', () => {
  const candidates = [
    { title: 'Build flashy preview', section: 'Public micro-project experiments', note: 'Imported from Public micro-project experiments' },
    { title: 'Improve internal recorder', section: 'OpenClaw autonomy improvements', note: 'Imported from OpenClaw autonomy improvements' }
  ];

  const balanced = rankCandidates(candidates, getScoreProfile('balanced').rubric);
  const autonomy = rankCandidates(candidates, getScoreProfile('autonomy-first').rubric);

  assert.notDeepEqual(
    balanced.map((item) => item.title),
    autonomy.map((item) => item.title)
  );
  assert.equal(autonomy[0].title, 'Improve internal recorder');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test previews/work-scoring-helper/tests/scoring.test.mjs`
Expected: FAIL with missing `getScoreProfile` export or incorrect ranking behavior.

- [ ] **Step 3: Write minimal implementation**

```javascript
export const scoreProfiles = [
  {
    id: 'balanced',
    label: 'Balanced',
    description: 'Use the lab default weighting.',
    rubric: defaultRubric.map((item) => ({ ...item }))
  },
  {
    id: 'demo-first',
    label: 'Demo first',
    description: 'Favor public demo punch and novelty.',
    rubric: defaultRubric.map((item) => item.key === 'demo'
      ? { ...item, weight: 0.35 }
      : item.key === 'novelty'
        ? { ...item, weight: 0.25 }
        : item.key === 'compound'
          ? { ...item, weight: 0.05 }
          : item.key === 'usefulness'
            ? { ...item, weight: 0.10 }
            : { ...item, weight: 0.25 })
  },
  {
    id: 'autonomy-first',
    label: 'Autonomy first',
    description: 'Favor OpenClaw usefulness and compounding autonomy gains.',
    rubric: defaultRubric.map((item) => item.key === 'usefulness'
      ? { ...item, weight: 0.30 }
      : item.key === 'compound'
        ? { ...item, weight: 0.25 }
        : item.key === 'demo'
          ? { ...item, weight: 0.10 }
          : item.key === 'novelty'
            ? { ...item, weight: 0.15 }
            : { ...item, weight: 0.20 })
  }
];

export function getScoreProfile(profileId = 'balanced') {
  return scoreProfiles.find((profile) => profile.id === profileId) || scoreProfiles[0];
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test previews/work-scoring-helper/tests/scoring.test.mjs`
Expected: PASS for new scenario profile tests and existing tests.

- [ ] **Step 5: Commit**

```bash
git add previews/work-scoring-helper/scoring.js previews/work-scoring-helper/tests/scoring.test.mjs
git commit -m "feat: add scoring scenario profiles"
```

### Task 2: Add scenario picker UI and docs

**Files:**
- Modify: `previews/work-scoring-helper/index.html`
- Modify: `previews/work-scoring-helper/README.md`
- Test: `previews/work-scoring-helper/tests/scoring.test.mjs`

- [ ] **Step 1: Write the failing test**

```javascript
test('scoreProfiles expose the UI-ready labels in stable order', () => {
  assert.deepEqual(scoreProfiles.map((profile) => profile.label), [
    'Balanced',
    'Demo first',
    'Autonomy first'
  ]);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test previews/work-scoring-helper/tests/scoring.test.mjs`
Expected: FAIL until `scoreProfiles` is exported in the expected shape.

- [ ] **Step 3: Write minimal implementation**

```html
<label for="profileSelect">Scenario profile</label>
<select id="profileSelect">
  <option value="balanced">Balanced</option>
  <option value="demo-first">Demo first</option>
  <option value="autonomy-first">Autonomy first</option>
</select>
<p id="profileHint" class="hint">Balanced: use the lab default weighting.</p>
```

```javascript
let activeProfile = getScoreProfile('balanced');

function setActiveProfile(profileId) {
  activeProfile = getScoreProfile(profileId);
  profileHintEl.textContent = `${activeProfile.label}: ${activeProfile.description}`;
  computeScore();
  renderCandidates();
}

const total = scoreValues(values, activeProfile.rubric);
const items = rankCandidates(loadCandidates(), activeProfile.rubric);
```

Update the README feature list and usage text to mention scenario profiles and what they do.

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test previews/work-scoring-helper/tests/scoring.test.mjs`
Expected: PASS with scenario profile exports and all prior coverage still green.

- [ ] **Step 5: Commit**

```bash
git add previews/work-scoring-helper/index.html previews/work-scoring-helper/README.md previews/work-scoring-helper/tests/scoring.test.mjs
git commit -m "feat: add scenario picker to work scoring helper"
```

## Self-Review
- Spec coverage: profiles, profile-aware ranking, UI picker, and docs are all mapped to tasks.
- Placeholder scan: no TODO/TBD markers remain.
- Type consistency: profile ids, labels, and helper names are consistent across tasks.
