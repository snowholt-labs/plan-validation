export const REPO_URL = 'https://github.com/snowholt-labs/plan-validation';
export const BASE = '/plan-validation/';

export const WIKI_PAGES = {
  '': '',
  Home: '',
  Installation: 'get-started',
  Usage: 'first-run',
  'Reports-and-Handoffs': 'reports-and-handoffs',
  'Safety-and-Limitations': 'safety-and-limitations',
  Troubleshooting: 'troubleshooting',
};

export const SYNCED = [
  {
    source: 'CHANGELOG.md',
    slug: 'changelog',
    title: 'Changelog',
    description: 'Release history for Plan Validation.',
  },
  {
    source: 'SECURITY.md',
    slug: 'security',
    title: 'Security and permissions',
    description: 'What Plan Validation can read and write, and how to report a vulnerability.',
  },
  {
    source: 'CONTRIBUTING.md',
    slug: 'contributing',
    title: 'Contributing',
    description: 'How to propose a change and what a pull request needs.',
  },
  {
    source: 'examples/README.md',
    slug: 'examples',
    title: 'Examples',
    description: 'A reproducible retry example that shows a failing and a corrected requirement check.',
    notice: 'Authored example fixture, not a benchmark.',
  },
  {
    source: 'examples/safety-cases.md',
    slug: 'examples/safety-cases',
    title: 'Representative permission and prompt cases',
    description: 'Synthetic exercises for checking permission and prompt handling in an isolated repository.',
  },
];

export const SIDEBAR = [
  {
    label: 'Start',
    items: [
      { label: 'Overview', slug: 'index' },
      { label: 'Get started', slug: 'get-started' },
      { label: 'Your first run', slug: 'first-run' },
    ],
  },
  {
    label: 'Learn',
    items: [
      { label: 'Features', slug: 'features' },
      { label: 'Examples', slug: 'examples' },
      { label: 'Reports and handoffs', slug: 'reports-and-handoffs' },
    ],
  },
  {
    label: 'Trust',
    items: [
      { label: 'Security and permissions', slug: 'security' },
      { label: 'Safety and limitations', slug: 'safety-and-limitations' },
      { label: 'Troubleshooting', slug: 'troubleshooting' },
    ],
  },
  {
    label: 'Project',
    items: [
      { label: 'Changelog', slug: 'changelog' },
      { label: 'Contributing', slug: 'contributing' },
    ],
  },
];
