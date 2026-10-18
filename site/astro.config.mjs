// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { SIDEBAR } from './scripts/content-map.mjs';

export default defineConfig({
  site: 'https://snowholt-labs.github.io',
  base: '/plan-validation',
  integrations: [
    starlight({
      title: 'Plan Validation',
      logo: { src: './src/assets/logo.svg' },
      sidebar: SIDEBAR.map(({ label, items }) => ({
        label,
        items: items.map(({ label, slug }) => ({ label, slug })),
      })),
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: 'https://github.com/snowholt-labs/plan-validation',
        },
      ],
    }),
  ],
});
