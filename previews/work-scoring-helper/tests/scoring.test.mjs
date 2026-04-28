import test from 'node:test';
import assert from 'node:assert/strict';
import {
  parseBacklog,
  findPreset,
  estimateCandidate,
  rankCandidates,
  defaultRubric,
  formatIdeaBrief,
  buildCandidateBrief,
  getScoreProfile,
  scoreProfiles
} from '../scoring.js';

test('parseBacklog groups bullets under the nearest heading', () => {
  const parsed = parseBacklog('## Public micro-project experiments\n- Build a tiny tool.\n## Maintenance\n- Refresh docs.');

  assert.deepEqual(parsed, [
    {
      title: 'Build a tiny tool',
      section: 'Public micro-project experiments',
      note: 'Imported from Public micro-project experiments'
    },
    {
      title: 'Refresh docs',
      section: 'Maintenance',
      note: 'Imported from Maintenance'
    }
  ]);
});

test('findPreset matches autonomy improvement sections', () => {
  const preset = findPreset('OpenClaw autonomy improvements');
  assert.equal(preset?.label, 'Autonomy improvement preset');
});

test('estimateCandidate applies section presets to compute an estimated score', () => {
  const estimated = estimateCandidate({
    title: 'Improve cycle recording',
    section: 'OpenClaw autonomy improvements',
    note: 'Imported from OpenClaw autonomy improvements'
  }, defaultRubric);

  assert.equal(estimated.estimatedScore, 3.92);
  assert.equal(estimated.preset?.label, 'Autonomy improvement preset');
});

test('rankCandidates sorts candidates from strongest preset score to weakest', () => {
  const ranked = rankCandidates([
    {
      title: 'Refresh stale status',
      section: 'Maintenance',
      note: 'Imported from Maintenance'
    },
    {
      title: 'Build a tiny browser tool',
      section: 'Public micro-project experiments',
      note: 'Imported from Public micro-project experiments'
    },
    {
      title: 'Improve cycle recording',
      section: 'OpenClaw autonomy improvements',
      note: 'Imported from OpenClaw autonomy improvements'
    }
  ], defaultRubric);

  assert.deepEqual(ranked.map((item) => item.title), [
    'Improve cycle recording',
    'Build a tiny browser tool',
    'Refresh stale status'
  ]);
});

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
  const demoFirst = rankCandidates(candidates, getScoreProfile('demo-first').rubric);

  assert.notDeepEqual(
    balanced.map((item) => item.title),
    demoFirst.map((item) => item.title)
  );
  assert.equal(demoFirst[0].title, 'Build flashy preview');
});

test('scoreProfiles expose the UI-ready labels in stable order', () => {
  assert.deepEqual(scoreProfiles.map((profile) => profile.label), [
    'Balanced',
    'Demo first',
    'Autonomy first'
  ]);
});
