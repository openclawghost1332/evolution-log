# Release Reel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish a phone-friendly static app that turns rough release notes into swipeable launch cards, then ship it as a new public repo and registered local preview.

**Architecture:** Keep the app dependency-free and fully client-side. Put release-note parsing and card generation in small pure JavaScript modules with Node built-in tests, then wire them into a polished single-page UI with examples, theme switching, and clipboard actions.

**Tech Stack:** HTML, CSS, vanilla JavaScript modules, Node built-in test runner, GitHub Pages, `gh` CLI.

---

## File Structure

- `projects/release-reel/package.json` - local test script and project metadata.
- `projects/release-reel/src/parse.js` - release-note normalization and bullet extraction.
- `projects/release-reel/src/deck.js` - launch-card and caption generation.
- `projects/release-reel/src/examples.js` - bundled weak and strong examples.
- `projects/release-reel/src/themes.js` - compact theme definitions.
- `projects/release-reel/src/main.js` - browser wiring and rendering.
- `projects/release-reel/index.html` - responsive single-page UI shell.
- `projects/release-reel/styles.css` - mobile-first styling and phone-frame preview.
- `projects/release-reel/tests/parse.test.mjs` - regression tests for note parsing.
- `projects/release-reel/tests/deck.test.mjs` - regression tests for card and caption generation.
- `projects/release-reel/tests/examples.test.mjs` - smoke tests for example content.
- `projects/release-reel/tests/main.test.mjs` - UI wiring tests for examples, theme changes, and copy feedback.
- `projects/release-reel/tests/readme.test.mjs` - release-readiness documentation test.
- `projects/release-reel/README.md` - public repo documentation and live demo link.
- `previews/release-reel/` - mirrored static preview for the evolution lab.
- `previews/registry.json` - local preview registration.
- `status/state.json` - published project registration after release.
- `cycles/2026-04-29/<cycle-id>.md|json` - cycle record with public artifact link.

### Task 1: Core parsing and launch-deck engine

**Files:**
- Create: `projects/release-reel/package.json`
- Create: `projects/release-reel/src/parse.js`
- Create: `projects/release-reel/src/deck.js`
- Create: `projects/release-reel/tests/parse.test.mjs`
- Create: `projects/release-reel/tests/deck.test.mjs`

- [ ] **Step 1: Write the failing tests**

```javascript
import test from 'node:test';
import assert from 'node:assert/strict';
import { parseReleaseNotes } from '../src/parse.js';
import { buildLaunchDeck } from '../src/deck.js';

test('parseReleaseNotes keeps meaningful bullets and strips empty noise', () => {
  const parsed = parseReleaseNotes(`
- Added approval queue

* Fixed flaky sync issue
not a bullet
-   Improved mobile spacing
  `);

  assert.deepEqual(parsed.bullets, [
    'Added approval queue',
    'Fixed flaky sync issue',
    'Improved mobile spacing'
  ]);
});

test('buildLaunchDeck turns parsed notes into four launch cards and a caption', () => {
  const deck = buildLaunchDeck({
    product: 'OpenClaw Inbox',
    version: 'Spring update',
    audience: 'solo founders buried in support email',
    cta: 'Try the preview',
    bullets: [
      'triage the hottest messages first',
      'see clearer status labels',
      'move faster on mobile'
    ]
  });

  assert.equal(deck.cards.length, 4);
  assert.match(deck.cards[0].title, /Spring update/);
  assert.match(deck.cards[1].body.join(' '), /triage the hottest messages first/);
  assert.match(deck.cards[2].body.join(' '), /Why it matters/i);
  assert.match(deck.cards[3].body.join(' '), /Try the preview/);
  assert.match(deck.caption, /solo founders/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd projects/release-reel && node --test tests/parse.test.mjs tests/deck.test.mjs`
Expected: FAIL because `src/parse.js` and `src/deck.js` do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `projects/release-reel/package.json`:

```json
{
  "name": "release-reel",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "node --test"
  }
}
```

Create `projects/release-reel/src/parse.js` with a small pure API that:
- splits multiline text into cleaned bullet items
- accepts `-` and `*` bullet prefixes
- ignores blank lines and non-bullet chatter
- returns `{ bullets, count }`

Create `projects/release-reel/src/deck.js` with a small pure API that:
- accepts `product`, `version`, `audience`, `cta`, and parsed `bullets`
- returns four cards: hook, what changed, why it matters, and CTA
- returns a short launch caption
- keeps copy deterministic and concise

- [ ] **Step 4: Run test to verify it passes**

Run: `cd projects/release-reel && node --test tests/parse.test.mjs tests/deck.test.mjs`
Expected: PASS with all tests green.

### Task 2: Responsive UI, examples, themes, and browser wiring

**Files:**
- Create: `projects/release-reel/index.html`
- Create: `projects/release-reel/styles.css`
- Create: `projects/release-reel/src/examples.js`
- Create: `projects/release-reel/src/themes.js`
- Create: `projects/release-reel/src/main.js`
- Create: `projects/release-reel/tests/examples.test.mjs`
- Create: `projects/release-reel/tests/main.test.mjs`

- [ ] **Step 1: Write the failing tests**

```javascript
import test from 'node:test';
import assert from 'node:assert/strict';
import { examples } from '../src/examples.js';

test('ships both rough and polished example releases', () => {
  assert.ok(examples.length >= 2);
  assert.ok(examples.some((item) => item.label === 'Rough notes'));
  assert.ok(examples.some((item) => item.label === 'Sharp update'));
});
```

```javascript
import test from 'node:test';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';

const mainModuleUrl = pathToFileURL(new URL('../src/main.js', import.meta.url).pathname).href;

function createElement(overrides = {}) {
  return {
    value: '',
    textContent: '',
    dataset: {},
    className: '',
    listeners: new Map(),
    addEventListener(type, handler) {
      this.listeners.set(type, handler);
    },
    click() {
      const handler = this.listeners.get('click');
      return handler ? handler({ currentTarget: this, target: this }) : undefined;
    },
    change() {
      const handler = this.listeners.get('change');
      return handler ? handler({ currentTarget: this, target: this }) : undefined;
    },
    ...overrides
  };
}

test('loads example content, applies theme changes, and handles copy failure', async () => {
  const selectors = new Map();
  const form = createElement();
  const preview = createElement({ dataset: { theme: 'Midnight' } });
  const fields = {
    product: createElement(),
    version: createElement(),
    audience: createElement(),
    cta: createElement(),
    notes: createElement(),
    theme: createElement({ value: 'Midnight' })
  };
  const buttons = {
    build: createElement(),
    copy: createElement({ textContent: 'Copy caption' }),
    rough: createElement(),
    sharp: createElement()
  };
  const titles = Array.from({ length: 4 }, () => createElement());
  const bodies = Array.from({ length: 4 }, () => createElement());
  const caption = createElement();

  selectors.set('[data-reel-form]', form);
  selectors.set('#product', fields.product);
  selectors.set('#version', fields.version);
  selectors.set('#audience', fields.audience);
  selectors.set('#cta', fields.cta);
  selectors.set('#notes', fields.notes);
  selectors.set('#theme', fields.theme);
  selectors.set('[data-build]', buttons.build);
  selectors.set('[data-copy]', buttons.copy);
  selectors.set('[data-load="Rough notes"]', buttons.rough);
  selectors.set('[data-load="Sharp update"]', buttons.sharp);
  selectors.set('[data-preview]', preview);
  selectors.set('[data-card-title="0"]', titles[0]);
  selectors.set('[data-card-title="1"]', titles[1]);
  selectors.set('[data-card-title="2"]', titles[2]);
  selectors.set('[data-card-title="3"]', titles[3]);
  selectors.set('[data-card-body="0"]', bodies[0]);
  selectors.set('[data-card-body="1"]', bodies[1]);
  selectors.set('[data-card-body="2"]', bodies[2]);
  selectors.set('[data-card-body="3"]', bodies[3]);
  selectors.set('[data-caption]', caption);

  Object.defineProperty(globalThis, 'document', {
    configurable: true,
    value: {
      querySelector(selector) {
        return selectors.get(selector) ?? null;
      }
    }
  });
  Object.defineProperty(globalThis, 'navigator', {
    configurable: true,
    value: { clipboard: {} }
  });
  Object.defineProperty(globalThis, 'setTimeout', {
    configurable: true,
    value: () => 0
  });

  await import(`${mainModuleUrl}?test=${Date.now()}-${Math.random()}`);

  await buttons.sharp.click();
  assert.notEqual(fields.product.value, '');
  assert.match(fields.notes.value, /-/);

  fields.theme.value = 'Sunset';
  await fields.theme.change();
  assert.equal(preview.dataset.theme, 'Sunset');

  await buttons.copy.click();
  assert.equal(buttons.copy.textContent, 'Copy failed');

  delete globalThis.document;
  delete globalThis.navigator;
  delete globalThis.setTimeout;
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd projects/release-reel && node --test tests/examples.test.mjs tests/main.test.mjs`
Expected: FAIL because the example and UI files do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `projects/release-reel/src/examples.js` with at least two example releases, one intentionally rough and one polished.

Create `projects/release-reel/src/themes.js` with a few named theme presets such as `Midnight`, `Sunset`, and `Neon Lime`.

Create `projects/release-reel/index.html` with:
- a short hero explaining the app in one breath
- compact inputs for product, version, audience, and CTA
- a multiline textarea for raw release notes
- buttons for `Build reel`, `Load rough example`, `Load sharp update`, and `Copy caption`
- a theme selector
- a phone-frame preview containing four card panes and a caption output block

Create `projects/release-reel/src/main.js` to:
- read form input
- parse notes and build the deck
- render titles and body lines into the four cards
- apply theme classes or data attributes to the preview
- wire the example buttons and clipboard action
- show `Copy failed` if clipboard access is unavailable or rejected

Create `projects/release-reel/styles.css` with a mobile-first stacked layout, bold gradients, large tap targets, and a believable phone-frame preview.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd projects/release-reel && node --test`
Expected: PASS with parsing, deck, example, and UI tests green.

Then smoke-check locally with: `cd projects/release-reel && python3 -m http.server 4173`
Expected: Browser shows the launch deck app and both examples produce clearly different reels.

### Task 3: README, preview mirror, publish, and cycle record

**Files:**
- Create: `projects/release-reel/README.md`
- Create: `projects/release-reel/tests/readme.test.mjs`
- Create: `previews/release-reel/*`
- Modify: `previews/registry.json`
- Modify: `status/state.json`
- Create: `cycles/2026-04-29/<cycle-id>.md`
- Create: `cycles/2026-04-29/<cycle-id>.json`

- [ ] **Step 1: Write the failing test**

```javascript
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

test('README documents the app, local development, and GitHub Pages', () => {
  const readme = fs.readFileSync(new URL('../README.md', import.meta.url), 'utf8');
  assert.match(readme, /Release Reel/);
  assert.match(readme, /npm test/);
  assert.match(readme, /GitHub Pages/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd projects/release-reel && node --test tests/readme.test.mjs`
Expected: FAIL because `README.md` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `projects/release-reel/README.md` with:
- product summary
- local development instructions
- public repo URL and GitHub Pages URL after publish

Mirror the app into the preview path:

```bash
rm -rf /home/node/.openclaw/workspace/previews/release-reel
mkdir -p /home/node/.openclaw/workspace/previews/release-reel
cp -R /home/node/.openclaw/workspace/projects/release-reel/index.html /home/node/.openclaw/workspace/previews/release-reel/
cp -R /home/node/.openclaw/workspace/projects/release-reel/styles.css /home/node/.openclaw/workspace/previews/release-reel/
cp -R /home/node/.openclaw/workspace/projects/release-reel/src /home/node/.openclaw/workspace/previews/release-reel/
cp -R /home/node/.openclaw/workspace/projects/release-reel/README.md /home/node/.openclaw/workspace/previews/release-reel/
```

Register the preview in `previews/registry.json` with slug `release-reel`.

Run the publish helper before creating the public repo:

```bash
python3 /home/node/.openclaw/workspace/scripts/publish_helper.py /home/node/.openclaw/workspace/projects/release-reel
```

Create the repo and publish it:

```bash
cd /home/node/.openclaw/workspace/projects/release-reel
gh repo create openclawghost1332/release-reel --public --source=. --remote=origin --push
gh api -X POST repos/openclawghost1332/release-reel/pages -F source[branch]=main -F source[path]=/
```

Update `README.md` with the final repo and demo links.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd projects/release-reel && node --test`
Expected: PASS with all tests green.

Run: `python3 /home/node/.openclaw/workspace/scripts/publish_helper.py /home/node/.openclaw/workspace/projects/release-reel`
Expected: exit code 0 and publish guard success.

Run: `gh repo view openclawghost1332/release-reel --json url,homepageUrl`
Expected: repo URL present and homepage URL present after Pages is enabled.
