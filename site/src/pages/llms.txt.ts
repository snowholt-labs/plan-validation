import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import notice from '../../../NOTICE?raw';
import { BASE, REPO_URL, SIDEBAR, attribution } from '../../scripts/content-map.mjs';

export const prerender = true;

const SUMMARY = 'Rehearse the plan before you hand it to a coding agent.';

export const GET: APIRoute = async ({ site }) => {
  const entries = await getCollection('docs');
  const byId = new Map(entries.map((entry) => [entry.id, entry]));
  const sidebar = SIDEBAR.flatMap((group) => group.items.map((item) => item.slug));
  const order = sidebar.flatMap((slug) => [
    slug,
    ...entries.map((e) => e.id).filter((id) => id.startsWith(slug + '/') && !sidebar.includes(id)).sort(),
  ]);
  order.push(...entries.map((e) => e.id).filter((id) => !order.includes(id)).sort());
  const lines = order
    .filter((id) => byId.has(id))
    .map((id) => {
      const { title, description } = byId.get(id)!.data;
      return `- [${title}](${new URL(`${BASE}${id}.md`, site)}): ${description}`;
    });
  const license = `License: [Apache-2.0](${REPO_URL}/blob/main/LICENSE). Credit: [NOTICE](${REPO_URL}/blob/main/NOTICE).`;
  const body = `# Plan Validation\n\n> ${SUMMARY}\n\n${attribution(notice)}\n\n${license}\n\n## Docs\n\n${lines.join('\n')}\n`;
  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
