import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { checkSite } from './check-site.mjs';

const BASE = '/plan-validation/';
const SITE = 'https://snowholt-labs.github.io/plan-validation/';
const REPO = 'https://github.com/snowholt-labs/plan-validation';

async function write(dir, files) {
  for (const [name, body] of Object.entries(files)) {
    await mkdir(path.dirname(path.join(dir, name)), { recursive: true });
    await writeFile(path.join(dir, name), body);
  }
}

async function check(files, repoFiles = {}) {
  const tmp = await mkdtemp(path.join(tmpdir(), 'check-site-'));
  try {
    const distDir = path.join(tmp, 'dist');
    const repoRoot = path.join(tmp, 'repo');
    await mkdir(distDir);
    await mkdir(repoRoot);
    await write(distDir, files);
    await write(repoRoot, repoFiles);
    return await checkSite(distDir, BASE, repoRoot);
  } finally {
    await rm(tmp, { recursive: true, force: true });
  }
}

test('missing internal target is reported', async () => {
  const errs = await check({ 'index.html': '<a href="/plan-validation/nope/">x</a>' });
  assert.equal(errs.length, 1);
  assert.match(errs[0], /nope/);
});
test('root-relative link missing base', async () => {
  const errs = await check({ 'index.html': '<a href="/get-started/">x</a>' });
  assert.match(errs.join('\n'), /missing base/);
});
test('existing targets, anchors, external links and .md files pass', async () => {
  const errs = await check({
    'index.html': '<a href="/plan-validation/get-started/">a</a><a href="#x">b</a>' +
      `<a href="${REPO}">c</a><a href="/plan-validation/get-started.md">d</a>`,
    'get-started/index.html': '<p>x</p>',
    'get-started.md': '# Get started\n',
  });
  assert.deepEqual(errs, []);
});
test('home path leak is reported', async () => {
  const errs = await check({ 'index.html': `<p>${'/' + 'home/alice/project'}/plan.md</p>` });
  assert.match(errs.join('\n'), /leak/);
});
test('third-party asset is reported', async () => {
  for (const html of ['<link rel="stylesheet" href="https://fonts.googleapis.com/x">',
    '<script src="https://cdn.example/x.js"></script>']) {
    const errs = await check({ 'index.html': html });
    assert.match(errs.join('\n'), /third-party/, html);
  }
});
test('data URIs are not third-party', async () => {
  const errs = await check({
    'index.html': '<img src="data:image/svg+xml;base64,PHN2Zy8+">',
    'style.css': 'a{background:url(data:image/png;base64,AAAA)}',
  });
  assert.deepEqual(errs, []);
});
test('install commands must match get-started', async () => {
  const code = 'claude plugin marketplace add a/b\u007fclaude plugin install X';
  const errs = await check({
    'index.html': `<div class="copy"><button data-code="${code}">Copy</button></div>`,
    'get-started.md': '# Get started\n\n```bash\nclaude plugin marketplace add a/b\n```\n',
  });
  assert.equal(errs.length, 1);
  assert.match(errs[0], /install/);
  assert.match(errs[0], /claude plugin install X/);
});
test('Starlight head output for the site origin passes', async () => {
  const errs = await check({
    'index.html': `<link rel="canonical" href="${SITE}"><meta property="og:url" content="${SITE}">` +
      '<link rel="sitemap" href="/plan-validation/sitemap-index.xml">' +
      '<link rel="shortcut icon" href="/plan-validation/favicon.svg" type="image/svg+xml">',
    'sitemap-index.xml': '<sitemapindex/>',
    'favicon.svg': '<svg/>',
  });
  assert.deepEqual(errs, []);
});
test('missing default favicon is reported', async () => {
  const errs = await check({ 'index.html': '<link rel="shortcut icon" href="/plan-validation/favicon.svg">' });
  assert.match(errs.join('\n'), /favicon/);
});
test('retired wiki links are reported', async () => {
  for (const href of [`${REPO}/wiki/Usage`, `${REPO}/tree/main/docs/wiki`]) {
    const errs = await check({ 'index.html': `<a href="${href}">w</a>` }, { 'docs/wiki/Home.md': '# Home\n' });
    assert.match(errs.join('\n'), /wiki/, href);
  }
});
test('llms.txt links must resolve', async () => {
  const errs = await check({ 'llms.txt': `# Plan Validation\n\n- [Security](${SITE}security.md): d\n` });
  assert.match(errs.join('\n'), /security\.md/);
});
test('relative link to missing page is reported', async () => {
  const errs = await check({ 'get-started/index.html': '<a href="../nope/">x</a>' });
  assert.match(errs.join('\n'), /nope/);
});
test('404 canonical resolves to 404.html', async () => {
  const errs = await check({ '404.html': `<link rel="canonical" href="${SITE}404/">` });
  assert.deepEqual(errs, []);
});
test('skip link target must exist', async () => {
  const errs = await check({ 'index.html': '<a class="sl-skip-link" href="#_top">Skip</a><main>x</main>' });
  assert.match(errs.join('\n'), /skip link/);
});
test('GitHub file links must exist', async () => {
  const errs = await check({
    'index.html': `<a href="${REPO}/blob/main/nope.md">n</a><a href="${REPO}/blob/main/LICENSE#l1">l</a>` +
      `<a href="${REPO}/tree/main/examples">e</a><a href="${REPO}/releases">r</a>`,
  }, { LICENSE: 'MIT\n', 'examples/README.md': '# Examples\n' });
  assert.equal(errs.length, 1);
  assert.match(errs[0], /nope\.md/);
});
