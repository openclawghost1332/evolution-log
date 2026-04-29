function withTrailingPeriod(text) {
  return /[.!?]$/.test(text) ? text : `${text}.`;
}

export function buildLaunchDeck({
  product,
  version,
  audience,
  cta,
  bullets = []
}) {
  const highlights = bullets.slice(0, 3);

  return {
    cards: [
      {
        name: 'hook',
        title: `${product} ${version}`,
        body: [
          `Built for ${audience}.`,
          `${highlights[0] ?? 'A smoother release, made simple.'}`
        ]
      },
      {
        name: 'what-changed',
        title: 'What changed',
        body: highlights.length ? highlights : ['A tighter, cleaner release.']
      },
      {
        name: 'why-it-matters',
        title: 'Why it matters',
        body: [
          `Why it matters for ${audience}:`,
          `${highlights[0] ?? 'Less friction, more momentum.'}`
        ]
      },
      {
        name: 'cta',
        title: 'Ready to try it?',
        body: [cta]
      }
    ],
    caption: `${product} ${version} for ${audience}. ${withTrailingPeriod(cta)}`
  };
}
