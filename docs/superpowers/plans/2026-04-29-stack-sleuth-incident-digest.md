# Stack Sleuth Incident Digest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reusable multi-trace incident digest engine to Stack Sleuth so repeated traces collapse into ranked incident groups across the CLI and browser demo.

**Architecture:** Keep the existing single-trace pipeline intact, then layer a digest module on top that splits a raw blob into trace chunks, analyzes each chunk with `analyzeTrace()`, groups reports by `signature`, and renders digest summaries for text, Markdown, JSON, and browser UI. The CLI becomes a thin mode selector, while the browser switches between single-trace and digest views based on how many valid traces were detected.

**Tech Stack:** Vanilla JavaScript ES modules, Node.js built-in test runner, static HTML/CSS browser UI, zero runtime dependencies.

---

## File Structure

- Modify: `projects/stack-sleuth/src/analyze.js`
  - Keep single-trace helpers intact, add digest rendering helpers and shared frame/summary formatting exports where needed.
- Create: `projects/stack-sleuth/src/digest.js`
  - Own trace chunk splitting, multi-trace analysis orchestration, signature grouping, and digest sorting.
- Modify: `projects/stack-sleuth/bin/stack-sleuth.js`
  - Detect `--digest`, choose single-trace versus digest rendering, and emit JSON/Markdown/text output.
- Modify: `projects/stack-sleuth/src/examples.js`
  - Add a bundled repeated-incident example input for the browser demo.
- Modify: `projects/stack-sleuth/src/main.js`
  - Swap between single-trace card rendering and digest rendering, update button wiring, and copy the visible report.
- Modify: `projects/stack-sleuth/index.html`
  - Add a digest summary section and a multi-trace example button without replacing the current card layout.
- Test: `projects/stack-sleuth/tests/digest.test.mjs`
  - Cover chunk splitting, grouping, ordering, representative selection, and merged tags.
- Modify: `projects/stack-sleuth/tests/analyze.test.mjs`
  - Add digest renderer coverage next to existing summary tests.
- Modify: `projects/stack-sleuth/tests/cli.test.mjs`
  - Add `--digest`, auto-digest, JSON digest, and Markdown digest coverage.
- Modify: `projects/stack-sleuth/tests/examples.test.mjs`
  - Assert the new multi-trace example exists and is distinct.
- Modify: `projects/stack-sleuth/tests/readme.test.mjs`
  - Update README contract expectations for digest usage.
- Modify: `projects/stack-sleuth/README.md`
  - Document multi-trace digest behavior in browser and CLI.

### Task 1: Add failing digest-engine tests

**Files:**
- Create: `projects/stack-sleuth/tests/digest.test.mjs`
- Modify: `projects/stack-sleuth/tests/examples.test.mjs`
- Test: `projects/stack-sleuth/tests/digest.test.mjs`

- [ ] **Step 1: Write the failing digest engine test file**

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import {
  splitTraceChunks,
  analyzeTraceDigest,
  renderDigestTextSummary,
  renderDigestMarkdownSummary
} from '../src/digest.js';

const repeatedJavascriptTrace = `TypeError: Cannot read properties of undefined (reading 'name')
    at renderProfile (/app/src/profile.js:88:17)
    at updateView (/app/src/view.js:42:5)
    at processTicksAndRejections (node:internal/process/task_queues:95:5)`;

const repeatedPythonTrace = `Traceback (most recent call last):
  File "app.py", line 42, in <module>
    run()
  File "service.py", line 17, in run
    return user["email"]
KeyError: 'email'`;

const multiTraceInput = [
  repeatedJavascriptTrace,
  repeatedJavascriptTrace,
  repeatedPythonTrace
].join('\n\n');

test('splitTraceChunks separates repeated runtime-shaped traces', () => {
  assert.deepEqual(splitTraceChunks(multiTraceInput), [
    repeatedJavascriptTrace,
    repeatedJavascriptTrace,
    repeatedPythonTrace
  ]);
});

test('analyzeTraceDigest groups reports by signature and sorts by repeat count', () => {
  const digest = analyzeTraceDigest(multiTraceInput);

  assert.equal(digest.totalTraces, 3);
  assert.equal(digest.groupCount, 2);
  assert.equal(digest.groups[0].count, 2);
  assert.equal(digest.groups[0].signature, 'javascript|TypeError|app/src/profile.js:88|nullish-data,undefined-property-access');
  assert.equal(digest.groups[0].representative.errorName, 'TypeError');
  assert.deepEqual(digest.groups[0].tags, ['nullish-data', 'undefined-property-access']);
  assert.equal(digest.groups[1].count, 1);
  assert.equal(digest.groups[1].runtime, 'python');
});

test('digest renderers produce copy-ready text and markdown summaries', () => {
  const digest = analyzeTraceDigest(multiTraceInput);
  const text = renderDigestTextSummary(digest);
  const markdown = renderDigestMarkdownSummary(digest);

  assert.match(text, /Stack Sleuth Incident Digest/);
  assert.match(text, /Total traces: 3/);
  assert.match(text, /Unique incidents: 2/);
  assert.match(text, /2x javascript TypeError/);

  assert.match(markdown, /^# Stack Sleuth Incident Digest/m);
  assert.match(markdown, /- \*\*Total traces:\*\* 3/);
  assert.match(markdown, /## Incident 1 \(2 traces\)/);
  assert.match(markdown, /`javascript\|TypeError\|app\/src\/profile\.js:88\|nullish-data,undefined-property-access`/);
});

test('single valid trace produces a one-group digest', () => {
  const digest = analyzeTraceDigest(repeatedJavascriptTrace);

  assert.equal(digest.totalTraces, 1);
  assert.equal(digest.groupCount, 1);
  assert.equal(digest.groups[0].count, 1);
});
```

- [ ] **Step 2: Run the digest tests to verify they fail**

Run: `cd /home/node/.openclaw/workspace/projects/stack-sleuth && node --test tests/digest.test.mjs`
Expected: FAIL with a module-not-found or missing-export error for `../src/digest.js`.

- [ ] **Step 3: Extend the example coverage with a failing multi-trace assertion**

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { examples } from '../src/examples.js';

test('examples expose distinct single-trace and multi-trace demos', () => {
  const labels = examples.map((item) => item.label);

  assert.ok(labels.includes('JavaScript undefined property'));
  assert.ok(labels.includes('Python missing key'));
  assert.ok(labels.includes('Repeated incident digest'));

  const digestExample = examples.find((item) => item.label === 'Repeated incident digest');
  assert.match(digestExample.caption, /repeat/i);
  assert.match(digestExample.trace, /TypeError:/);
  assert.match(digestExample.trace, /KeyError:/);
});
```

- [ ] **Step 4: Run the example test to verify it fails**

Run: `cd /home/node/.openclaw/workspace/projects/stack-sleuth && node --test tests/examples.test.mjs`
Expected: FAIL because the `Repeated incident digest` example does not exist yet.

- [ ] **Step 5: Commit the red tests**

```bash
cd /home/node/.openclaw/workspace/projects/stack-sleuth
git add tests/digest.test.mjs tests/examples.test.mjs
git commit -m "test: add incident digest coverage"
```

### Task 2: Implement the digest engine and renderers

**Files:**
- Create: `projects/stack-sleuth/src/digest.js`
- Modify: `projects/stack-sleuth/src/analyze.js`
- Modify: `projects/stack-sleuth/src/examples.js`
- Test: `projects/stack-sleuth/tests/digest.test.mjs`

- [ ] **Step 1: Create the minimal digest engine to satisfy the new tests**

```js
import { analyzeTrace } from './analyze.js';

export function splitTraceChunks(input) {
  return String(input ?? '')
    .trim()
    .split(/\n\s*\n(?=(?:Traceback \(most recent call last\):|[A-Za-z_$][\w$]*:|\S.+:\d+:in `))/)
    .map((chunk) => chunk.trim())
    .filter(Boolean);
}

export function analyzeTraceDigest(input) {
  const chunks = splitTraceChunks(input);
  const reports = chunks.map((chunk) => analyzeTrace(chunk)).filter((report) => !report.empty);
  const groupsBySignature = new Map();

  reports.forEach((report, index) => {
    const existing = groupsBySignature.get(report.signature);
    if (existing) {
      existing.count += 1;
      existing.tags = Array.from(new Set([...existing.tags, ...report.diagnosis.tags])).sort();
      return;
    }

    groupsBySignature.set(report.signature, {
      signature: report.signature,
      runtime: report.runtime,
      errorName: report.errorName,
      count: 1,
      firstSeenIndex: index,
      tags: [...report.diagnosis.tags],
      representative: report
    });
  });

  const groups = [...groupsBySignature.values()].sort((a, b) => b.count - a.count || a.firstSeenIndex - b.firstSeenIndex);

  return {
    totalTraces: reports.length,
    groupCount: groups.length,
    groups,
    traces: reports
  };
}
```

- [ ] **Step 2: Add digest text and Markdown renderers**

```js
export function renderDigestTextSummary(digest) {
  return [
    'Stack Sleuth Incident Digest',
    `Total traces: ${digest.totalTraces}`,
    `Unique incidents: ${digest.groupCount}`,
    '',
    ...digest.groups.flatMap((group, index) => [
      `Incident ${index + 1}: ${group.count}x ${group.runtime} ${group.errorName}`,
      `Signature: ${group.signature}`,
      `Culprit: ${formatFrame(group.representative.culpritFrame)}`,
      `Tags: ${group.tags.join(', ')}`,
      `Summary: ${group.representative.diagnosis.summary}`,
      ''
    ])
  ].join('\n').trim();
}

export function renderDigestMarkdownSummary(digest) {
  return [
    '# Stack Sleuth Incident Digest',
    '',
    `- **Total traces:** ${digest.totalTraces}`,
    `- **Unique incidents:** ${digest.groupCount}`,
    '',
    ...digest.groups.flatMap((group, index) => [
      `## Incident ${index + 1} (${group.count} traces)`,
      '',
      `- **Runtime:** ${group.runtime}`,
      `- **Error:** ${group.errorName}: ${group.representative.message}`,
      `- **Signature:** \`${group.signature}\``,
      `- **Culprit:** \`${formatFrame(group.representative.culpritFrame)}\``,
      `- **Tags:** ${group.tags.join(', ')}`,
      '',
      group.representative.diagnosis.summary,
      ''
    ])
  ].join('\n').trim();
}
```

- [ ] **Step 3: Export any shared formatting helpers needed by the digest module and add the repeated incident example**

```js
export function formatFrame(frame) {
  if (!frame?.file) {
    return 'No application frame detected';
  }

  const location = frame.line ? `${frame.file}:${frame.line}` : frame.file;
  return frame.functionName ? `${frame.functionName} (${location})` : location;
}
```

```js
{
  label: 'Repeated incident digest',
  caption: 'Two repeated frontend failures and one backend key miss collapse into a ranked incident digest.',
  trace: `${javascriptTrace}\n\n${javascriptTrace}\n\n${pythonTrace}`
}
```

- [ ] **Step 4: Run the focused tests to verify they pass**

Run: `cd /home/node/.openclaw/workspace/projects/stack-sleuth && node --test tests/digest.test.mjs tests/examples.test.mjs tests/analyze.test.mjs`
Expected: PASS for all targeted digest and renderer tests.

- [ ] **Step 5: Commit the engine slice**

```bash
cd /home/node/.openclaw/workspace/projects/stack-sleuth
git add src/digest.js src/analyze.js src/examples.js tests/digest.test.mjs tests/examples.test.mjs tests/analyze.test.mjs
git commit -m "feat: add incident digest engine"
```

### Task 3: Wire digest support into the CLI

**Files:**
- Modify: `projects/stack-sleuth/bin/stack-sleuth.js`
- Modify: `projects/stack-sleuth/tests/cli.test.mjs`
- Test: `projects/stack-sleuth/tests/cli.test.mjs`

- [ ] **Step 1: Add failing CLI tests for digest mode and auto-digest**

```js
const multiTraceInput = [sampleTrace, sampleTrace, `Traceback (most recent call last):
  File "app.py", line 42, in <module>
    run()
  File "service.py", line 17, in run
    return user["email"]
KeyError: 'email'`].join('\n\n');

test('CLI supports --digest output', () => {
  const result = runCli(['--digest'], { input: multiTraceInput });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Stack Sleuth Incident Digest/);
  assert.match(result.stdout, /Total traces: 3/);
  assert.match(result.stdout, /Incident 1: 2x javascript TypeError/);
});

test('CLI auto-promotes multi-trace stdin into digest output', () => {
  const result = runCli([], { input: multiTraceInput });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Stack Sleuth Incident Digest/);
});

test('CLI supports --digest --json output', () => {
  const result = runCli(['--digest', '--json'], { input: multiTraceInput });

  assert.equal(result.status, 0, result.stderr);
  assert.equal(JSON.parse(result.stdout).groupCount, 2);
});
```

- [ ] **Step 2: Run the CLI test file to verify the new expectations fail**

Run: `cd /home/node/.openclaw/workspace/projects/stack-sleuth && node --test tests/cli.test.mjs`
Expected: FAIL because the CLI does not recognize `--digest` or auto-render digest output yet.

- [ ] **Step 3: Implement CLI digest mode with minimal branching**

```js
import {
  analyzeTrace,
  renderTextSummary,
  renderMarkdownSummary
} from '../src/analyze.js';
import {
  analyzeTraceDigest,
  renderDigestTextSummary,
  renderDigestMarkdownSummary,
  splitTraceChunks
} from '../src/digest.js';

const wantsDigest = args.includes('--digest');
const chunkCount = splitTraceChunks(input).length;
const useDigest = wantsDigest || chunkCount > 1;

if (useDigest) {
  const digest = analyzeTraceDigest(input);

  if (digest.totalTraces === 0) {
    fail('No trace provided. Pipe a stack trace or pass a file path.');
  }

  if (mode === 'json') {
    process.stdout.write(`${JSON.stringify(digest, null, 2)}\n`);
  } else if (mode === 'markdown') {
    process.stdout.write(`${renderDigestMarkdownSummary(digest)}\n`);
  } else {
    process.stdout.write(`${renderDigestTextSummary(digest)}\n`);
  }
} else {
  const report = analyzeTrace(input);
  // keep current single-trace branch here
}
```

- [ ] **Step 4: Re-run the CLI test file to verify it passes**

Run: `cd /home/node/.openclaw/workspace/projects/stack-sleuth && node --test tests/cli.test.mjs`
Expected: PASS, including the new digest scenarios.

- [ ] **Step 5: Commit the CLI integration**

```bash
cd /home/node/.openclaw/workspace/projects/stack-sleuth
git add bin/stack-sleuth.js tests/cli.test.mjs
git commit -m "feat: add digest cli output"
```

### Task 4: Add browser digest presentation and docs

**Files:**
- Modify: `projects/stack-sleuth/index.html`
- Modify: `projects/stack-sleuth/src/main.js`
- Modify: `projects/stack-sleuth/README.md`
- Modify: `projects/stack-sleuth/tests/readme.test.mjs`
- Test: `projects/stack-sleuth/tests/readme.test.mjs`

- [ ] **Step 1: Add failing README coverage for digest usage**

```js
test('README documents browser and CLI workflows, including incident digest mode', () => {
  const readme = fs.readFileSync(new URL('../README.md', import.meta.url), 'utf8');
  assert.match(readme, /Incident Digest/i);
  assert.match(readme, /--digest/);
  assert.match(readme, /multiple traces|repeated traces/i);
});
```

- [ ] **Step 2: Run the README contract test to verify it fails**

Run: `cd /home/node/.openclaw/workspace/projects/stack-sleuth && node --test tests/readme.test.mjs`
Expected: FAIL because the README does not mention digest mode yet.

- [ ] **Step 3: Add the minimal browser digest UI and wiring**

```html
<button id="load-digest-button" type="button" class="secondary">Load digest example</button>
<article class="card result-card wide">
  <span class="result-label">Incident digest</span>
  <ul id="digest-groups-value" class="checklist">
    <li>Repeated incidents will appear here when Stack Sleuth detects multiple traces.</li>
  </ul>
</article>
```

```js
import { analyzeTrace } from './analyze.js';
import { analyzeTraceDigest, splitTraceChunks } from './digest.js';

const digestGroupsValue = document.querySelector('#digest-groups-value');
const loadDigestButton = document.querySelector('#load-digest-button');
const digestExample = examples.find((item) => item.label === 'Repeated incident digest');

function renderDiagnosis() {
  const traceText = traceInput.value.trim();
  const chunkCount = splitTraceChunks(traceText).length;

  if (chunkCount > 1) {
    const digest = analyzeTraceDigest(traceText);
    runtimeValue.textContent = `${digest.groupCount} grouped incident${digest.groupCount === 1 ? '' : 's'}`;
    headlineValue.textContent = `${digest.totalTraces} traces collapsed into ${digest.groupCount} incident groups`;
    digestGroupsValue.replaceChildren(...buildListItems(
      digest.groups.map((group) => `${group.count}x ${group.errorName} at ${formatFrame(group.representative.culpritFrame)}`)
    ));
    return;
  }

  // keep existing single-trace rendering path here
}

loadDigestButton?.addEventListener('click', () => loadExample(digestExample));
```

- [ ] **Step 4: Update README usage examples and run the full test suite**

Run: `cd /home/node/.openclaw/workspace/projects/stack-sleuth && npm test`
Expected: PASS for the entire suite after README, browser wiring, and digest rendering are aligned.

- [ ] **Step 5: Commit the browser and docs slice**

```bash
cd /home/node/.openclaw/workspace/projects/stack-sleuth
git add index.html src/main.js README.md tests/readme.test.mjs
git commit -m "feat: add incident digest browser workflow"
```

### Task 5: Final verification and publish prep

**Files:**
- Modify: `projects/stack-sleuth/README.md` if verification reveals wording drift

- [ ] **Step 1: Sanity-check the digest CLI manually**

Run:

```bash
cd /home/node/.openclaw/workspace/projects/stack-sleuth
printf "TypeError: Cannot read properties of undefined (reading 'name')\n    at renderProfile (/app/src/profile.js:88:17)\n    at updateView (/app/src/view.js:42:5)\n\nTypeError: Cannot read properties of undefined (reading 'name')\n    at renderProfile (/app/src/profile.js:88:17)\n    at updateView (/app/src/view.js:42:5)\n\nTraceback (most recent call last):\n  File \"app.py\", line 42, in <module>\n    run()\n  File \"service.py\", line 17, in run\n    return user[\"email\"]\nKeyError: 'email'" | node ./bin/stack-sleuth.js --digest --markdown
```

Expected: Markdown digest with 3 total traces and 2 incident groups.

- [ ] **Step 2: Run the publish guard wrapper for the project**

Run: `cd /home/node/.openclaw/workspace && python3 scripts/publish_helper.py projects/stack-sleuth`
Expected: PASS with no secret or host-path findings.

- [ ] **Step 3: Check project git status and recent commits**

Run: `cd /home/node/.openclaw/workspace/projects/stack-sleuth && git status --short && git log --oneline -n 5`
Expected: Clean working tree and the new digest commits present.

- [ ] **Step 4: If verification reveals drift, fix the exact file and rerun the affected test command**

```bash
cd /home/node/.openclaw/workspace/projects/stack-sleuth
npm test
```

Expected: PASS after any last-mile fixes.

- [ ] **Step 5: Commit any final polish**

```bash
cd /home/node/.openclaw/workspace/projects/stack-sleuth
git add README.md src/main.js index.html tests/readme.test.mjs
git commit -m "chore: polish incident digest release"
```
