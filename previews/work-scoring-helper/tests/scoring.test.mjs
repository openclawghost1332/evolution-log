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
