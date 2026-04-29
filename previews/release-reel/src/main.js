import { buildLaunchDeck } from './deck.js';
import { examples } from './examples.js';
import { parseReleaseNotes } from './parse.js';
import { themes, themeNames } from './themes.js';

function query(selector) {
  return globalThis.document?.querySelector(selector) ?? null;
}

const elements = {
  form: query('[data-reel-form]'),
  product: query('#product'),
  version: query('#version'),
  audience: query('#audience'),
  cta: query('#cta'),
  notes: query('#notes'),
  theme: query('#theme'),
  build: query('[data-build]'),
  copy: query('[data-copy]'),
  preview: query('[data-preview]'),
  caption: query('[data-caption]'),
  titles: Array.from({ length: 4 }, (_, index) => query(`[data-card-title="${index}"]`)),
  bodies: Array.from({ length: 4 }, (_, index) => query(`[data-card-body="${index}"]`))
};

function readForm() {
  return {
    product: elements.product?.value?.trim() ?? '',
    version: elements.version?.value?.trim() ?? '',
    audience: elements.audience?.value?.trim() ?? '',
    cta: elements.cta?.value?.trim() ?? '',
    notes: elements.notes?.value ?? '',
    theme: elements.theme?.value ?? themeNames[0]
  };
}

function populateThemeOptions() {
  if (!elements.theme) {
    return;
  }

  elements.theme.innerHTML = themeNames
    .map((name) => `<option${name === elements.theme.value ? ' selected' : ''}>${name}</option>`)
    .join('');

  if (!elements.theme.value || !themeNames.includes(elements.theme.value)) {
    elements.theme.value = themeNames[0];
  }
}

function applyTheme(themeName) {
  const resolvedThemeName = themeNames.includes(themeName) ? themeName : themeNames[0];
  const theme = themes[resolvedThemeName];

  if (elements.preview) {
    elements.preview.dataset.theme = resolvedThemeName;
    elements.preview.style?.setProperty('--preview-background', theme.background);
    elements.preview.style?.setProperty('--preview-accent', theme.accent);
    elements.preview.style?.setProperty('--preview-glow', theme.glow);
  }

  if (elements.theme) {
    elements.theme.value = resolvedThemeName;
  }
}

function renderDeck(deck) {
  deck.cards.forEach((card, index) => {
    if (elements.titles[index]) {
      elements.titles[index].textContent = card.title;
    }
    if (elements.bodies[index]) {
      elements.bodies[index].textContent = card.body.join('\n');
    }
  });

  if (elements.caption) {
    elements.caption.textContent = deck.caption;
  }
}

function buildFromForm() {
  const { product, version, audience, cta, notes, theme } = readForm();
  const parsed = parseReleaseNotes(notes);
  const deck = buildLaunchDeck({
    product,
    version,
    audience,
    cta,
    bullets: parsed.bullets
  });

  applyTheme(theme);
  renderDeck(deck);
  return deck;
}

function loadExample(label) {
  const example = examples.find((item) => item.label === label);
  if (!example) {
    return null;
  }

  if (elements.product) elements.product.value = example.product;
  if (elements.version) elements.version.value = example.version;
  if (elements.audience) elements.audience.value = example.audience;
  if (elements.cta) elements.cta.value = example.cta;
  if (elements.notes) elements.notes.value = example.notes;

  return buildFromForm();
}

async function copyCaption() {
  const text = elements.caption?.textContent ?? '';
  const writeText = globalThis.navigator?.clipboard?.writeText;

  if (typeof writeText !== 'function') {
    if (elements.copy) elements.copy.textContent = 'Copy failed';
    return false;
  }

  try {
    await writeText.call(globalThis.navigator.clipboard, text);
    if (elements.copy) {
      elements.copy.textContent = 'Copied';
      globalThis.setTimeout?.(() => {
        elements.copy.textContent = 'Copy caption';
      }, 1200);
    }
    return true;
  } catch {
    if (elements.copy) elements.copy.textContent = 'Copy failed';
    return false;
  }
}

function wireButton(selector, handler) {
  const node = query(selector);
  node?.addEventListener?.('click', handler);
}

elements.build?.addEventListener?.('click', () => {
  buildFromForm();
});

elements.theme?.addEventListener?.('change', () => {
  applyTheme(elements.theme?.value ?? themeNames[0]);
});

wireButton('[data-load="Rough notes"]', () => loadExample('Rough notes'));
wireButton('[data-load="Sharp update"]', () => loadExample('Sharp update'));
elements.copy?.addEventListener?.('click', () => copyCaption());

populateThemeOptions();
applyTheme(elements.theme?.value ?? themeNames[0]);

export { applyTheme, buildFromForm, copyCaption, loadExample, populateThemeOptions, readForm };
