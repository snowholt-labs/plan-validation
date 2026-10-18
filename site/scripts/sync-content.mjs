import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { BASE, REPO_URL, SYNCED, WIKI_PAGES } from './content-map.mjs';

const WIKI = REPO_URL + '/wiki';
const LOGO_SOURCE = 'assets/plan-validation.svg';

function siteHref(slug, hash) {
  return BASE + (slug ? slug + '/' : '') + hash;
}

function rewriteTarget(target, sourcePath) {
  if (target === WIKI || target.startsWith(WIKI + '/') || target.startsWith(WIKI + '#')) {
    const rest = target.slice(WIKI.length).replace(/^\//, '');
    const [page, hash = ''] = rest.split('#');
    if (!(page in WIKI_PAGES)) throw new Error(`${sourcePath}: unmapped wiki page ${page}`);
    return siteHref(WIKI_PAGES[page], hash ? '#' + hash : '');
  }
  if (/^[a-z][a-z0-9+.-]*:/i.test(target) || target.startsWith('#') || target.startsWith('/')) return target;
  const [rel, hash = ''] = target.split('#');
  const resolved = path.posix.normalize(path.posix.join(path.posix.dirname(sourcePath), rel));
  if (resolved.startsWith('..')) throw new Error(`${sourcePath}: link leaves the repository: ${target}`);
  const synced = SYNCED.find((e) => e.source === resolved);
  if (synced) return siteHref(synced.slug, hash ? '#' + hash : '');
  return `${REPO_URL}/blob/main/${resolved}${hash ? '#' + hash : ''}`;
}

export function rewriteLinks(markdown, sourcePath) {
  const parts = markdown.split(/(^```[^\n]*\n[\s\S]*?^```[^\n]*$)/m);
  return parts
    .map((part, i) =>
      i % 2 ? part : part.replace(/\]\(([^)\s]+)\)/g, (_, t) => `](${rewriteTarget(t, sourcePath)})`)
    )
    .join('');
}

function yamlValue(value) {
  return value.includes(':') ? JSON.stringify(value) : value;
}

export function toPage(markdown, entry) {
  const body = markdown.replace(/^# .*\n+/m, '');
  const notice = entry.notice ? `:::note\n${entry.notice}\n:::\n\n` : '';
  return (
    `---\ntitle: ${yamlValue(entry.title)}\ndescription: ${yamlValue(entry.description)}\n---\n` +
    `<!-- Generated from ${entry.source}. Edit that file, not this one. -->\n\n` +
    rewriteLinks(notice + body, entry.source)
  );
}

export async function syncContent(repoRoot, siteDir) {
  const docsDir = path.join(siteDir, 'src/content/docs');
  const written = [];
  for (const entry of SYNCED) {
    const markdown = await readFile(path.join(repoRoot, entry.source), 'utf8');
    const out = path.join(docsDir, entry.slug === 'examples' ? 'examples/index.md' : entry.slug + '.md');
    await mkdir(path.dirname(out), { recursive: true });
    await writeFile(out, toPage(markdown, entry));
    written.push(out);
  }
  const logo = path.join(repoRoot, LOGO_SOURCE);
  for (const target of ['src/assets/logo.svg', 'public/favicon.svg']) {
    const out = path.join(siteDir, target);
    await mkdir(path.dirname(out), { recursive: true });
    await copyFile(logo, out);
  }
  return written;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const written = await syncContent('..', '.');
  console.log(written.join('\n'));
}
