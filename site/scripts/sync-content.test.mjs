import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { SIDEBAR, SYNCED } from './content-map.mjs';
import { rewriteLinks, syncContent, toPage } from './sync-content.mjs';

test('wiki links become site links', () => {
  assert.equal(rewriteLinks('[a](https://github.com/snowholt-labs/plan-validation/wiki/Usage)', 'SECURITY.md'),
    '[a](/plan-validation/first-run/)');
  assert.equal(rewriteLinks('[a](https://github.com/snowholt-labs/plan-validation/wiki/Safety-and-Limitations#data)', 'SECURITY.md'),
    '[a](/plan-validation/safety-and-limitations/#data)');
  assert.equal(rewriteLinks('[w](https://github.com/snowholt-labs/plan-validation/wiki)', 'README.md'),
    '[w](/plan-validation/)');
});
test('relative links to synced sources become site links', () => {
  assert.equal(rewriteLinks('[c](safety-cases.md)', 'examples/README.md'), '[c](/plan-validation/examples/safety-cases/)');
});
test('other relative links point at GitHub', () => {
  assert.equal(rewriteLinks('[s](../scripts/demo.py)', 'examples/README.md'),
    '[s](https://github.com/snowholt-labs/plan-validation/blob/main/scripts/demo.py)');
  assert.equal(rewriteLinks('[l](LICENSE)', 'CONTRIBUTING.md'),
    '[l](https://github.com/snowholt-labs/plan-validation/blob/main/LICENSE)');
});
test('fenced code is untouched', () => {
  const md = '```md\n[x](https://github.com/snowholt-labs/plan-validation/wiki/Usage)\n```';
  assert.equal(rewriteLinks(md, 'SECURITY.md'), md);
});
test('external and anchor links are untouched', () => {
  for (const l of ['[x](https://example.com)', '[x](#trust-boundaries)', '[x](mailto:a@b.c)'])
    assert.equal(rewriteLinks(l, 'SECURITY.md'), l);
});
test('toPage strips the H1 and adds front matter and the generated note', () => {
  const out = toPage('# Security policy\n\nText', { source: 'SECURITY.md', slug: 'security', title: 'Security and permissions', description: 'd' });
  assert.match(out, /^---\ntitle: Security and permissions\ndescription: d\n---\n/);
  assert.match(out, /Generated from SECURITY.md/);
  assert.doesNotMatch(out, /^# Security policy/m);
});
test('syncContent writes every synced page', async () => {
  const tmp = await mkdtemp(path.join(tmpdir(), 'sync-content-'));
  try {
    const repoRoot = path.join(tmp, 'repo');
    const siteDir = path.join(tmp, 'site');
    await mkdir(path.join(repoRoot, 'examples'), { recursive: true });
    await mkdir(path.join(repoRoot, 'assets'), { recursive: true });
    for (const entry of SYNCED) await writeFile(path.join(repoRoot, entry.source), '# Stub\n\nBody\n');
    await writeFile(path.join(repoRoot, 'assets/plan-validation-small.svg'), '<svg xmlns="http://www.w3.org/2000/svg"/>');
    const written = await syncContent(repoRoot, siteDir);
    const docs = path.join(siteDir, 'src/content/docs');
    assert.deepEqual(written.sort(), [
      path.join(docs, 'changelog.md'),
      path.join(docs, 'contributing.md'),
      path.join(docs, 'examples/index.md'),
      path.join(docs, 'examples/safety-cases.md'),
      path.join(docs, 'security.md'),
    ]);
    for (const file of written) assert.match(await readFile(file, 'utf8'), /^---\ntitle: /);
    const svg = '<svg xmlns="http://www.w3.org/2000/svg"/>';
    assert.equal(await readFile(path.join(siteDir, 'public/favicon.svg'), 'utf8'), svg);
    assert.equal(await readFile(path.join(siteDir, 'src/assets/logo.svg'), 'utf8'), svg);
  } finally {
    await rm(tmp, { recursive: true, force: true });
  }
});
test('unmapped wiki page fails instead of shipping a dead link', () => {
  assert.throws(() => rewriteLinks('[x](https://github.com/snowholt-labs/plan-validation/wiki/Nope)', 'SECURITY.md'), /unmapped wiki page/);
});
test('relative link to a synced source keeps its anchor', () => {
  assert.equal(rewriteLinks('[s](../SECURITY.md#reporting)', 'examples/README.md'), '[s](/plan-validation/security/#reporting)');
});
test('the examples notice is added', () => {
  assert.match(toPage('# T\n\nx', SYNCED.find((e) => e.slug === 'examples')), /:::note\nAuthored example fixture, not a benchmark\.\n:::/);
});
test('a relative link outside the repository fails', () => {
  assert.throws(() => rewriteLinks('[x](../../outside.md)', 'examples/README.md'), /leaves the repository/);
});
test('the sidebar has four groups with the planned order', () => {
  assert.deepEqual(SIDEBAR.map((g) => g.label), ['Start', 'Learn', 'Trust', 'Project']);
  assert.deepEqual(SIDEBAR.flatMap((g) => g.items.map((i) => i.slug)), [
    'index', 'get-started', 'first-run', 'features', 'examples', 'reports-and-handoffs',
    'security', 'safety-and-limitations', 'troubleshooting', 'changelog', 'contributing',
  ]);
});
