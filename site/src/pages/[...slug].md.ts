import type { APIRoute, GetStaticPaths } from 'astro';
import { getCollection } from 'astro:content';
import notice from '../../../NOTICE?raw';
import { BASE, SIDEBAR, attribution } from '../../scripts/content-map.mjs';

export const prerender = true;

export const getStaticPaths = (async () => {
  const entries = await getCollection('docs');
  return entries.map((entry) => ({ params: { slug: entry.id }, props: { entry } }));
}) satisfies GetStaticPaths;

function landing(site: URL | undefined): string {
  return SIDEBAR.flatMap((group) => group.items)
    .map(({ label, slug }) => `- [${label}](${new URL(BASE + (slug === 'index' ? '' : slug + '/'), site)})`)
    .join('\n');
}

export const GET: APIRoute = ({ props, site }) => {
  const { entry } = props;
  const { title, description } = entry.data;
  const body = entry.id === 'index' ? `${description}\n\n${landing(site)}\n` : entry.body;
  return new Response(`# ${title}\n\n${body.trimEnd()}\n\n---\n\n${attribution(notice)}\n`, {
    headers: { 'Content-Type': 'text/markdown; charset=utf-8' },
  });
};
