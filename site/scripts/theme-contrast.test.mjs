import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const css = await readFile(new URL('../src/styles/theme.css', import.meta.url), 'utf8');

// Collect the --pv-* hex tokens declared in the block opened by `selector`.
function tokens(selector) {
  const start = css.indexOf(`${selector} {`);
  assert.notEqual(start, -1, `missing block: ${selector}`);
  const block = css.slice(start, css.indexOf('}', start));
  return Object.fromEntries([...block.matchAll(/--pv-([\w-]+):\s*(#[0-9a-f]{6})\b/gi)].map((m) => [m[1], m[2]]));
}

function luminance(hex) {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a, b) {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

const PAIRS = [
  ['ink', 'paper'],
  ['muted', 'paper'],
  ['plum', 'paper'],
  ['plum-deep', 'rose'],
  ['paper', 'plum'],
  ['amber', 'amber-tint'],
  ['mint', 'mint-tint'],
  ['plum-deep', 'paper'],
  ['paper', 'plum-deep'],
  ['plum', 'blush'],
  ['muted', 'blush'],
  ['plum-deep', 'blush'],
  ['ink', 'surface'],
  ['muted', 'surface'],
  ['amber', 'surface'],
];

// WCAG 1.4.11: interactive boundaries against every background they sit on.
const BORDER_PAIRS = [
  ['border', 'paper'],
  ['border', 'surface'],
  ['border', 'blush'],
];

for (const [name, selector] of [['light', ":root[data-theme='light']"], ['dark', ':root']]) {
  test(`${name} theme meets WCAG AA text contrast`, () => {
    const t = tokens(selector);
    for (const [fg, bg] of PAIRS) {
      assert.ok(t[fg] && t[bg], `${name}: missing --pv-${fg} or --pv-${bg}`);
      const ratio = contrast(t[fg], t[bg]);
      assert.ok(ratio >= 4.5, `${name}: ${fg} ${t[fg]} on ${bg} ${t[bg]} is ${ratio.toFixed(2)}, need 4.5`);
    }
  });
  test(`${name} theme meets 3:1 contrast for interactive borders`, () => {
    const t = tokens(selector);
    for (const [fg, bg] of BORDER_PAIRS) {
      assert.ok(t[fg] && t[bg], `${name}: missing --pv-${fg} or --pv-${bg}`);
      const ratio = contrast(t[fg], t[bg]);
      assert.ok(ratio >= 3, `${name}: ${fg} ${t[fg]} on ${bg} ${t[bg]} is ${ratio.toFixed(2)}, need 3`);
    }
  });
}
