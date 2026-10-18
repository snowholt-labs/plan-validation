// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://snowholt-labs.github.io',
  base: '/plan-validation',
  integrations: [
    starlight({
      title: 'Plan Validation',
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
