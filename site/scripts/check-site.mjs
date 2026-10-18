import { readFile, readdir, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { CREATOR, REPO_URL, attribution } from './content-map.mjs';

const ORIGIN = 'https://snowholt-labs.github.io';
const LEAK = /\/(?:home|Users)\/[^/\s]+\//;
const WIKI = new RegExp(`^${REPO_URL}/(?:wiki|(?:tree|blob)/main/docs/wiki)(?:[/?#]|$)`);
const REPO_FILE = new RegExp(`^${REPO_URL}/(?:blob|tree)/main/([^?#]+)`);
const LOADING_REL = new Set(['stylesheet', 'preload', 'modulepreload', 'prefetch', 'preconnect', 'dns-prefetch',
  'icon', 'manifest']);
const INSTALL = /^(?:claude plugin|\$skill-installer)/;
const CREDIT = `Created by ${CREATOR}`;
const LICENSE_LINKS = ['LICENSE', 'NOTICE'].map((file) => `${REPO_URL}/blob/main/${file}`);

function missingLicenseLinks(html) {
  const hrefs = tags(html).filter((t) => t.name === 'a').map((t) => t.attrs.href);
  return LICENSE_LINKS.filter((link) => !hrefs.includes(link)).map((link) => link.split('/').pop());
}
// Every rehearsal sheet line in the spec (docs/superpowers/specs/2026-10-18-docs-site-design.md), checked inside
// the sheet's <figure data-rehearsal-sheet>. The caption keeps "not a benchmark" on the sheet itself.
const SHEET = [
  'plan.md: retry delay (one phase, one task)',
  'R1: attempt 0 returns 1 second, covered by Task 1',
  'R2: the delay doubles, covered by Task 1',
  'R3: the 30-second cap has no task in the plan',
  'Acceptance check on the uncapped code failed: 64 != 30',
  'No independent review has run yet',
  'Not ready',
  'Missing cap and no review',
  'Authored example fixture, not a benchmark',
];
const SHEET_FIGURE = /<figure\b(?:"[^"]*"|'[^']*'|[^'">])*\bdata-rehearsal-sheet\b(?:"[^"]*"|'[^']*'|[^'">])*>[\s\S]*?<\/figure>/i;

async function walk(dir) {
  const out = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...(await walk(p)));
    else out.push(p);
  }
  return out;
}

async function exists(p) {
  try {
    await stat(p);
    return true;
  } catch {
    return false;
  }
}

function decode(value) {
  return value
    .replace(/&#x([0-9a-f]+);/gi, (_, n) => String.fromCodePoint(parseInt(n, 16)))
    .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&');
}

function attributes(source) {
  const attrs = {};
  for (const m of source.matchAll(/(?:^|\s)([\w:-]+)\s*=\s*("[^"]*"|'[^']*'|[^\s"'>]+)/g)) {
    attrs[m[1].toLowerCase()] = decode(m[2].replace(/^["']|["']$/g, ''));
  }
  return attrs;
}

function tags(html) {
  const stripped = html.replace(/<!--[\s\S]*?-->/g, '').replace(/(<script\b[^>]*>)[\s\S]*?<\/script>/gi, '$1');
  return [...stripped.matchAll(/<([a-z][\w-]*)\b((?:"[^"]*"|'[^']*'|[^'">])*)>/gi)].map((m) => ({
    name: m[1].toLowerCase(),
    attrs: attributes(m[2]),
  }));
}

function cssRefs(css) {
  const refs = [];
  for (const m of css.matchAll(/url\(\s*(['"]?)([^'")]+)\1\s*\)/g)) refs.push({ url: m[2].trim(), loads: true });
  for (const m of css.matchAll(/@import\s+['"]([^'"]+)['"]/g)) refs.push({ url: m[1], loads: true });
  return refs;
}

function htmlRefs(html, tagList) {
  const refs = [];
  for (const { name, attrs } of tagList) {
    if (attrs.href !== undefined) {
      const rel = (attrs.rel || '').toLowerCase().split(/\s+/);
      refs.push({ url: attrs.href, loads: name === 'link' && rel.some((r) => LOADING_REL.has(r)) });
    }
    if (attrs.src !== undefined) refs.push({ url: attrs.src, loads: true });
    if (attrs.poster !== undefined) refs.push({ url: attrs.poster, loads: true });
    if (name === 'object' && attrs.data !== undefined) refs.push({ url: attrs.data, loads: true });
    if (attrs.srcset !== undefined) {
      for (const part of attrs.srcset.split(',')) refs.push({ url: part.trim().split(/\s+/)[0], loads: true });
    }
    if (attrs.style !== undefined) refs.push(...cssRefs(attrs.style));
  }
  for (const m of html.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/gi)) refs.push(...cssRefs(m[1]));
  return refs;
}

function markdownRefs(text) {
  return [...text.matchAll(/\]\(([^)\s]+)\)/g)].map((m) => ({ url: m[1], loads: false }));
}

function targets(distDir, base, url) {
  let clean = url.split(/[?#]/)[0].slice(base.length);
  try {
    clean = decodeURIComponent(clean);
  } catch {
    // Keep the raw path; the lookup below reports it as missing.
  }
  if (path.posix.extname(clean)) return [path.join(distDir, clean)];
  const dir = clean.replace(/\/$/, '');
  return dir ? [path.join(distDir, dir, 'index.html'), path.join(distDir, dir + '.html')] : [path.join(distDir, 'index.html')];
}

async function checkExternal(rel, url, loads, repoRoot) {
  if (loads) return [`${rel}: third-party asset ${url}`];
  if (WIKI.test(url)) return [`${rel}: link to the retired wiki ${url}`];
  const file = url.match(REPO_FILE);
  if (!file) return [];
  let repoPath = file[1].replace(/\/$/, '');
  try {
    repoPath = decodeURIComponent(repoPath);
  } catch {
    // Keep the raw path; the lookup below reports it as missing.
  }
  return (await exists(path.join(repoRoot, repoPath))) ? [] : [`${rel}: GitHub link to missing repository path ${repoPath}`];
}

async function checkRef(distDir, base, repoRoot, rel, { url, loads }) {
  if (!url) return [];
  if (url === ORIGIN + base.replace(/\/$/, '') || url.startsWith(ORIGIN + base)) url = url.slice(ORIGIN.length);
  if (/^(?:https?:)?\/\//i.test(url)) return checkExternal(rel, url, loads, repoRoot);
  if (url.startsWith('#') || /^[a-z][a-z0-9+.-]*:/i.test(url)) return [];
  if (!url.startsWith('/')) {
    const dir = path.posix.dirname(rel.split(path.sep).join('/'));
    const [pathname, ...rest] = url.split(/(?=[?#])/);
    const joined = path.posix.join(base, dir, pathname) + (pathname.endsWith('/') ? '/' : '');
    url = joined.replace(/\/{2,}/g, '/') + rest.join('');
  }
  if (url === base.replace(/\/$/, '')) url = base;
  if (!url.startsWith(base)) return [`${rel}: root-relative link missing base ${url}`];
  const found = await Promise.all(targets(distDir, base, url).map(exists));
  return found.some(Boolean) ? [] : [`${rel}: missing internal target ${url}`];
}

function checkSkipLink(rel, tagList) {
  const skip = tagList.find((t) => t.name === 'a' && /(?:^|\s)sl-skip-link(?:\s|$)/.test(t.attrs.class || ''));
  if (!skip || !(skip.attrs.href || '').startsWith('#')) return [];
  const id = skip.attrs.href.slice(1);
  return tagList.some((t) => t.attrs.id === id) ? [] : [`${rel}: skip link target #${id} missing`];
}

// Code block lines from Expressive Code's copy-button data-code, which joins lines with \u007f.
function installLines(tagList) {
  return tagList
    .filter((t) => t.attrs['data-code'] !== undefined)
    .flatMap((t) => t.attrs['data-code'].split(/[\u007f\n]/))
    .map((line) => line.trim())
    .filter((line) => INSTALL.test(line));
}

async function checkInstall(distDir, tagList) {
  let guide = '';
  try {
    guide = await readFile(path.join(distDir, 'get-started.md'), 'utf8');
  } catch {
    // A missing guide leaves every install command unmatched.
  }
  return installLines(tagList).filter((line) => !guide.includes(line)).map((line) => `index.html: install command not in get-started.md: ${line}`);
}

export async function checkSite(distDir, base, repoRoot) {
  const errors = [];
  for (const file of await walk(distDir)) {
    const rel = path.relative(distDir, file);
    const isHtml = file.endsWith('.html');
    if (!isHtml && !file.endsWith('.css') && rel !== 'llms.txt') continue;
    const text = await readFile(file, 'utf8');
    if (LEAK.test(text)) errors.push(`${rel}: home path leak`);
    let refs;
    if (isHtml) {
      const tagList = tags(text);
      refs = htmlRefs(text, tagList);
      errors.push(...checkSkipLink(rel, tagList));
      if (rel === 'index.html') errors.push(...(await checkInstall(distDir, tagList)));
    } else {
      refs = rel === 'llms.txt' ? markdownRefs(text) : cssRefs(text);
    }
    for (const ref of refs) errors.push(...(await checkRef(distDir, base, repoRoot, rel, ref)));
  }
  return errors;
}

// Visible text: no comments, scripts, styles or tags, entities decoded, whitespace collapsed.
function pageText(html) {
  const stripped = html
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/<(script|style)\b[\s\S]*?<\/\1>/gi, '')
    .replace(/<\/?[a-z][\w-]*\b(?:"[^"]*"|'[^']*'|[^'">])*>/gi, '');
  return decode(stripped).replace(/\s+/g, ' ');
}

async function readText(file) {
  try {
    return await readFile(file, 'utf8');
  } catch {
    return '';
  }
}

export async function checkNotices(distDir, repoRoot) {
  const errors = [];
  const pilotLine = (await readText(path.join(repoRoot, 'README.md'))).match(/^>\s*\*\*Pilot release:\*\*.*$/m);
  const pilot = pilotLine && pilotLine[0].replace(/^>\s*/, '').replace(/\*\*|`/g, '').replace(/\s+/g, ' ').trim();
  const landingHtml = await readText(path.join(distDir, 'index.html'));
  const landing = pageText(landingHtml);
  if (!pilot) errors.push('README.md: pilot release notice not found');
  else if (!landing.includes(pilot)) errors.push('index.html: README pilot release notice missing');
  const figure = landingHtml.match(SHEET_FIGURE);
  if (!figure) errors.push('index.html: rehearsal sheet <figure data-rehearsal-sheet> missing');
  else {
    const sheet = pageText(figure[0]);
    const missing = SHEET.filter((line) => !sheet.includes(line));
    if (missing.length) errors.push(`index.html: rehearsal sheet missing ${missing.map((l) => `"${l}"`).join(', ')}`);
    if (/fix proposed/i.test(sheet)) errors.push('index.html: rehearsal sheet says "fix proposed"');
  }
  if (!installLines(tags(landingHtml)).length) errors.push('index.html: landing install block has no install command');
  // The landing page's "not a benchmark" label is part of the sheet check above.
  const examples = path.join('examples', 'index.html');
  if (!/not a benchmark/i.test(pageText(await readText(path.join(distDir, examples))))) {
    errors.push(`${examples}: "not a benchmark" notice missing`);
  }
  // The NOTICE attribution must reach readers of the landing page and agents reading llms.txt or a Markdown copy.
  const credit = attribution(await readText(path.join(repoRoot, 'NOTICE')));
  if (!credit) errors.push('NOTICE: attribution paragraph not found');
  else if (!landing.includes(credit)) errors.push('index.html: NOTICE attribution missing');
  const landingMain = landingHtml.replace(/<footer\b[\s\S]*?<\/footer>/gi, '');
  const landingLinks = missingLicenseLinks(landingMain);
  if (landingLinks.length) errors.push(`index.html: credits section missing ${landingLinks.join(' and ')} link`);
  for (const file of await walk(distDir)) {
    const name = path.relative(distDir, file);
    if (credit && (file.endsWith('.md') || name === 'llms.txt')) {
      if (!(await readFile(file, 'utf8')).replace(/\s+/g, ' ').includes(credit)) errors.push(`${name}: NOTICE attribution missing`);
    }
    if (!file.endsWith('.html')) continue;
    const footers = [...(await readFile(file, 'utf8')).matchAll(/<footer\b[\s\S]*?<\/footer>/gi)].map((m) => m[0]);
    if (!footers.some((footer) => pageText(footer).includes(CREDIT))) errors.push(`${name}: footer "${CREDIT}" line missing`);
    if (!footers.some((footer) => !missingLicenseLinks(footer).length)) errors.push(`${name}: footer LICENSE and NOTICE links missing`);
  }
  return errors;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const errors = [...(await checkSite('dist', '/plan-validation/', '..')), ...(await checkNotices('dist', '..'))];
  if (errors.length) {
    console.error(errors.join('\n'));
    process.exit(1);
  }
}
