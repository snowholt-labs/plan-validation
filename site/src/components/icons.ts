// Inner SVG markup for a 24x24 stroked icon, keyed by page slug ('index' is the landing page).
export const ICONS: Record<string, string> = {
  index: '<path d="M3 11 12 4l9 7v9H3z"/>',
  'get-started': '<path d="M12 3v12m0 0-4-4m4 4 4-4M4 19h16"/>',
  'first-run': '<path d="m6 4 14 8-14 8z"/>',
  features: '<path d="M12 3l2.5 5.5L20 9l-4 4 1 6-5-3-5 3 1-6-4-4 5.5-.5z"/>',
  examples: '<rect x="4" y="3" width="16" height="18" rx="3"/><path d="M8 8h8M8 12h8M8 16h5"/>',
  'reports-and-handoffs': '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  'phased-implementation': '<path d="M3 20h5v-5h5v-5h5V5h3"/>',
  security: '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/>',
  'safety-and-limitations': '<path d="M12 3 2 20h20zM12 10v4m0 3v.5"/>',
  troubleshooting: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6M12 17v.5"/>',
  changelog: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  contributing: '<path d="M12 21s-7-4.5-7-10a4 4 0 0 1 7-2.5A4 4 0 0 1 19 11c0 5.5-7 10-7 10z"/>',
};

// Join the site base and a site-relative path with exactly one slash.
export function withBase(path: string): string {
  return `${import.meta.env.BASE_URL.replace(/\/+$/, '')}/${path.replace(/^\/+/, '')}`;
}
