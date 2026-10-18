import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { checkNotices, checkSite } from './check-site.mjs';

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

async function notices(files, repoFiles = { 'README.md': README, NOTICE }) {
  const tmp = await mkdtemp(path.join(tmpdir(), 'check-notices-'));
  try {
    const distDir = path.join(tmp, 'dist');
    const repoRoot = path.join(tmp, 'repo');
    await mkdir(distDir);
    await mkdir(repoRoot);
    await write(distDir, files);
    await write(repoRoot, repoFiles);
    return await checkNotices(distDir, repoRoot);
  } finally {
    await rm(tmp, { recursive: true, force: true });
  }
}

const PILOT = 'the renderer is tested separately. The example is an authored fixture\u2014not a benchmark or a claim.';
const README = `# Plan Validation\n\n> **Pilot release:** ${PILOT}\n`;
const CREDIT = 'Plan Validation was created by Nariman Jafari (Lumina). Keep the NOTICE file.';
const NOTICE = `Plan Validation\nCopyright 2026 Nariman Jafari (Lumina)\n\n${CREDIT.replace('Lumina). ', 'Lumina).\n')}\n`;
const LINKS = `<a href="${REPO}/blob/main/LICENSE">LICENSE</a> <a href="${REPO}/blob/main/NOTICE">NOTICE</a>`;
const FOOTER = `<footer><p>Created by Nariman Jafari (Lumina) and maintained at <a href="#">the repository</a>.</p><p>${LINKS}</p></footer>`;
const LANDING = {
  pilot: `<blockquote><p><strong>Pilot release:</strong> ${PILOT}</p></blockquote>`,
  sheet: '<figure class="sheet" data-rehearsal-sheet><header><p>plan.md: retry delay (one phase, one task)</p></header><ol>' +
    '<li><span class="sr-only">Pass: </span><span>R1: attempt 0 returns 1 second, covered by Task 1</span></li>' +
    '<li><span>R2: the delay doubles, covered by Task 1</span></li>' +
    '<li><span class="sr-only">Fail: </span><span>R3: the 30-second cap has no task in the plan</span></li>' +
    '<li><span>Acceptance check on the uncapped code failed: <code>64 != 30</code></span></li>' +
    '<li><span>No independent review has run yet</span></li></ol>' +
    '<p><span>Not ready</span> <span>Missing cap and no review</span></p>' +
    '<figcaption>Authored example fixture, not a benchmark.</figcaption></figure>',
  install: '<div class="copy"><button data-code="claude plugin install X\u007fclaude plugin list">Copy</button></div>',
  credit: `<h2>Credits and license</h2><p>${CREDIT}</p><p>${LINKS}</p>`,
};

function site(landing = {}, pages = {}) {
  const parts = { ...LANDING, ...landing };
  return {
    'index.html': `<main>${parts.pilot}${parts.sheet}${parts.install}${parts.credit}${FOOTER}</main>`,
    'llms.txt': `# Plan Validation\n\n${CREDIT}\n`,
    'get-started.md': `# Get started\n\nInstall.\n\n---\n\n${CREDIT}\n`,
    'examples/index.html': `<main><aside><p>Authored example fixture, not a benchmark.</p></aside>${FOOTER}</main>`,
    'get-started/index.html': `<main><p>Install</p>${FOOTER}</main>`,
    ...pages,
  };
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
test('install line after a quoted > is still checked', async () => {
  const errs = await check({
    'index.html': '<button data-code="echo x >&amp;2\u007fclaude plugin install X">Copy</button>',
    'get-started.md': '# Get started\n',
  });
  assert.match(errs.join('\n'), /install.*claude plugin install X/);
});
test('third-party src after a quoted > is reported', async () => {
  const errs = await check({ 'index.html': '<img alt="a > b" src="https://cdn.example/x.png">' });
  assert.match(errs.join('\n'), /third-party/);
});
test('complete notices pass', async () => {
  assert.deepEqual(await notices(site()), []);
});
test('pilot notice required on landing', async () => {
  const errs = await notices(site({ pilot: '<p>Pilot release: tested.</p>' }));
  assert.equal(errs.length, 1);
  assert.match(errs[0], /pilot/i);
});
test('rehearsal sheet matches the fixture', async () => {
  const sheets = [
    LANDING.sheet.replace('64 != 30', '64 != 31'),
    LANDING.sheet.replace('Missing cap and no review', '1 blocker'),
    LANDING.sheet.replace('Not ready', 'Ready'),
    LANDING.sheet.replace('R3: the 30-second cap', 'R3: the cap'),
    LANDING.sheet.replace('R1: attempt 0 returns 1 second', 'R1: attempt 0 returns 2 seconds'),
    LANDING.sheet.replace('No independent review has run yet', 'Review passed'),
    LANDING.sheet.replace('one phase, one task', 'two phases'),
    // Lines outside the sheet's figure do not count.
    LANDING.sheet.replace('<span>Not ready</span>', '<span>Ready</span>') + '<p>Not ready</p>',
    LANDING.sheet.replace(' data-rehearsal-sheet', ''),
    LANDING.sheet.replace('Missing cap and no review', 'Missing cap and no review, fix proposed'),
    // The pilot notice also says "not a benchmark", so the sheet's own label is checked here.
    LANDING.sheet.replace(/<figcaption>.*<\/figcaption>/, ''),
  ];
  for (const sheet of sheets) {
    const errs = await notices(site({ sheet }));
    assert.equal(errs.length, 1, sheet);
    assert.match(errs[0], /rehearsal/, sheet);
  }
});
test('benchmark disclaimer required', async () => {
  // The landing page's label is covered by the rehearsal sheet test; this checks the Examples page alone.
  const errs = await notices(site({}, { 'examples/index.html': `<main><p>A comparative benchmark.</p>${FOOTER}</main>` }));
  assert.equal(errs.length, 1);
  assert.match(errs[0], /examples.*benchmark/);
});
test('landing install block required', async () => {
  const errs = await notices(site({ install: '<button data-code="/plan-validation:validate-plan">Copy</button>' }));
  assert.equal(errs.length, 1);
  assert.match(errs[0], /install/);
});
test('creator credit required in every footer', async () => {
  const page = FOOTER.replace('Created by Nariman Jafari (Lumina)', 'Created by snowholt');
  const errs = await notices(site({}, { 'get-started/index.html': `<main><p>Install</p>${page}</main>` }));
  assert.equal(errs.length, 1);
  assert.match(errs[0], /get-started.*Created by Nariman Jafari \(Lumina\)/);
});
test('NOTICE attribution required on the landing page, llms.txt and Markdown copies', async () => {
  const cases = [
    [site({ credit: `<h2>Credits and license</h2>${LINKS}` }), /index\.html: NOTICE/],
    [site({}, { 'llms.txt': '# Plan Validation\n' }), /llms\.txt: NOTICE/],
    [site({}, { 'get-started.md': '# Get started\n\nInstall.\n' }), /get-started\.md: NOTICE/],
  ];
  for (const [files, error] of cases) {
    const errs = await notices(files);
    assert.equal(errs.length, 1, String(error));
    assert.match(errs[0], error);
  }
});
test('NOTICE without an attribution paragraph is reported', async () => {
  const errs = await notices(site(), { 'README.md': README, NOTICE: 'Plan Validation\n' });
  assert.equal(errs.length, 1);
  assert.match(errs[0], /NOTICE: attribution paragraph not found/);
});
test('LICENSE and NOTICE links required in the footer and the landing credits', async () => {
  for (const file of ['LICENSE', 'NOTICE']) {
    const without = (html) => html.replace(new RegExp(`<a href="[^"]*/${file}">${file}</a>`), '');
    const footerErrs = await notices(site({}, { 'get-started/index.html': `<main><p>Install</p>${without(FOOTER)}</main>` }));
    assert.equal(footerErrs.length, 1, file);
    assert.match(footerErrs[0], /get-started.*footer LICENSE and NOTICE links/);
    const landingErrs = await notices(site({ credit: without(LANDING.credit) }));
    assert.equal(landingErrs.length, 1, file);
    assert.match(landingErrs[0], new RegExp(`index\\.html: credits section missing ${file} link`));
  }
});
