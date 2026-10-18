// @ts-check
import { defineConfig, fontProviders } from 'astro/config';
import starlight from '@astrojs/starlight';
import { SIDEBAR } from './scripts/content-map.mjs';

export default defineConfig({
  site: 'https://snowholt-labs.github.io',
  base: '/plan-validation',
  fonts: [
    {
      provider: fontProviders.fontsource(),
      name: 'Bricolage Grotesque',
      cssVariable: '--pv-font-display',
      weights: [500, 700, 800],
      styles: ['normal'],
      subsets: ['latin'],
    },
    {
      provider: fontProviders.fontsource(),
      name: 'Atkinson Hyperlegible',
      cssVariable: '--pv-font-body',
      weights: [400, 700],
      styles: ['normal'],
      subsets: ['latin'],
    },
    {
      provider: fontProviders.fontsource(),
      name: 'JetBrains Mono',
      cssVariable: '--pv-font-mono',
      weights: [400, 600],
      styles: ['normal'],
      subsets: ['latin'],
    },
  ],
  integrations: [
    starlight({
      title: 'Plan Validation',
      logo: { src: './src/assets/logo.svg' },
      customCss: ['./src/styles/theme.css'],
      components: { Head: './src/components/Head.astro' },
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
