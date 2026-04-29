export const defaultRubric = [
  { key: 'novelty', label: 'Novelty', weight: 0.20, value: 3 },
  { key: 'feasibility', label: 'One-cycle feasibility', weight: 0.25, value: 3 },
  { key: 'demo', label: 'Public demo value', weight: 0.20, value: 3 },
  { key: 'usefulness', label: 'OpenClaw usefulness', weight: 0.20, value: 3 },
  { key: 'compound', label: 'Compounding autonomy value', weight: 0.15, value: 3 }
];

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

export const sectionPresets = [
  {
    match: /public micro-project/i,
    label: 'Public micro-project preset',
    values: { novelty: 4.5, feasibility: 4, demo: 5, usefulness: 3, compound: 2 },
    rationale: 'Bias toward novelty, shipping speed, and demo punch.'
  },
  {
    match: /autonomy improvement/i,
    label: 'Autonomy improvement preset',
    values: { novelty: 4, feasibility: 3.5, demo: 2.5, usefulness: 5, compound: 5 },
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
  return candidates
    .map((candidate) => estimateCandidate(candidate, rubric))
    .sort((a, b) => b.estimatedScore - a.estimatedScore);
}

export function summarizeCandidateProfiles(candidate) {
  const profileScores = scoreProfiles.map((profile) => ({
    profileId: profile.id,
    profileLabel: profile.label,
    score: estimateCandidate(candidate, profile.rubric).estimatedScore
  }));
  const averageScore = Number((profileScores.reduce((sum, item) => sum + item.score, 0) / profileScores.length).toFixed(2));
  const balancedScore = profileScores.find((item) => item.profileId === 'balanced')?.score ?? averageScore;

  return {
    ...candidate,
    profileScores,
    averageScore,
    balancedScore
  };
}

export function rankCandidatesByConsensus(candidates) {
  const summaries = candidates.map((candidate) => summarizeCandidateProfiles(candidate));
  const winsByTitle = new Map(summaries.map((candidate) => [candidate.title, 0]));

  scoreProfiles.forEach((profile) => {
    const bestScore = summaries.reduce((max, candidate) => Math.max(max, candidate.profileScores.find((item) => item.profileId === profile.id)?.score ?? 0), Number.NEGATIVE_INFINITY);

    summaries.forEach((candidate) => {
      const profileScore = candidate.profileScores.find((item) => item.profileId === profile.id)?.score ?? 0;
      if (profileScore === bestScore) {
        winsByTitle.set(candidate.title, (winsByTitle.get(candidate.title) ?? 0) + 1);
      }
    });
  });

  return summaries
    .map((candidate) => ({
      ...candidate,
      profileWinCount: winsByTitle.get(candidate.title) ?? 0
    }))
    .sort((a, b) => b.averageScore - a.averageScore || b.profileWinCount - a.profileWinCount || b.balancedScore - a.balancedScore || a.title.localeCompare(b.title));
}

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
    if (!bulletMatch) {
      return;
    }

    const text = bulletMatch[1].trim();
    if (!text) {
      return;
    }

    candidates.push({
      title: text.replace(/\.$/, ''),
      section: currentSection,
      note: `Imported from ${currentSection}`
    });
  });

  return candidates;
}
