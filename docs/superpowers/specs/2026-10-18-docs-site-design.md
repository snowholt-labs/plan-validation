# Documentation site design

Date: 2026-10-18. Status: approved by the maintainer on 2026-10-18.

## Intent

Replace the GitHub wiki with one documentation website at `https://snowholt-labs.github.io/plan-validation/`, in the spirit of the [Rust learn page](https://rust-lang.org/learn/#learn-use): a landing page that explains the project quickly and offers clear buttons to Get started, Features, Examples, Security, Changelog and the rest of the docs.

The site becomes the single home for user documentation, so the docs cannot drift between two places. It serves two audiences:

- Technical users deciding whether to install the plugin, then learning to use it.
- AI agents and bots reading the docs, which need plain Markdown and an `llms.txt` index.

## Goals

- A landing page that follows the approved mockup: [`2026-10-18-docs-site-mockup.html`](2026-10-18-docs-site-mockup.html).
- Every current wiki page published on the site, with working links between pages.
- Pages for Features, Examples, Security and Changelog, built from existing repository content.
- Offline site search with no third-party service.
- `llms.txt` plus a raw Markdown version of each page for agents.
- Automatic deployment to GitHub Pages from `main`.
- Light and dark themes that both keep the plum identity.

## Non-goals

- A custom domain. The `github.io` address is enough for now.
- Versioned docs (one version per release).
- Analytics, cookies, comments, newsletter sign-up or any tracking. *(Superseded on 2026-10-25 by the maintainer: the site may load Google Analytics, only after a visitor accepts it in a consent banner.)*
- Rewriting the documentation content beyond what moving it requires (link fixes, front matter, splitting the new pages out of existing text).
- Translations.

## Anti-goals

The site fails, even if it builds, if it:

- Makes claims the project does not support. The pilot-release notice, the "not a benchmark" wording on the example, and the "not affiliated with Anthropic, OpenAI or Superpowers" statement must stay visible where they appear today. *(Superseded on 2026-10-18 by the maintainer: the "not affiliated" line was removed from the site.)*
- Contacts third parties at runtime: no externally hosted fonts, scripts or images. This matches the self-contained, no-analytics stance of the generated reports. *(Superseded on 2026-10-25 by the maintainer: Google Analytics may load after a visitor's consent; the static HTML still loads no third-party asset.)*
- Leaves two editable copies of the same content (for example `CHANGELOG.md` and a hand-copied changelog page).
- Affects the shipped plugin's behavior: no change to the skills, manifests or the `verify` check's runtime, and no build output or `node_modules` committed. (The marketplace installs the repository root, `"source": "./"`, so the site's source files will be present in installs, just as `docs/` and `examples/` are today. Builder's-call note: this is accepted; moving the plugin into a subfolder is out of scope.)
- Looks like a stock Starlight theme with a color swap. The approved custom layout is the point.

## Decisions made

Decided by the maintainer:

- **Design:** the approved mockup. Plum feminine-tech identity from the existing icon (`assets/plan-validation-small.svg`, `#873f63`), left sidebar of grouped icon buttons, Rust-style rows of buttons on the left with descriptions on the right, and a richer page than a minimal landing.
- **Hosting:** GitHub Pages at the project `github.io` address.
- **Wiki:** the site replaces the wiki and becomes the single home.
- **Generator:** Astro Starlight, approved 2026-10-18 after a dependency comparison (Starlight 0.42.6 released 2026-10-08, Astro 7.4.0, MIT). VitePress, MkDocs Material, Docusaurus and a hand-built generator were compared and rejected.
- **Attribution:** the site footer credits `snowholt` as creator and maintainer, matching the README credit line and linking to `https://github.com/snowholt`. No other personal name appears. The existing `snowholt` uses in LICENSE, the manifests and the `snowholt-plugins` marketplace stay unchanged. *Superseded on 2026-10-18 by the maintainer: the project is relicensed under Apache-2.0 with a NOTICE file, and the credit reads "Nariman Jafari (Lumina)" in LICENSE/NOTICE, the README, the manifests, the footer, the landing page, `llms.txt` and the Markdown page copies. The `snowholt-plugins` marketplace owner is unchanged.*

## Design reference

The mockup is the visual source of truth for the landing page and the page shell.

| Token | Value | Use |
| --- | --- | --- |
| Paper | `#fbf6f8` | Page background |
| Blush | `#f6e4ec` | Hover, tints, release card |
| Rose | `#f1cfdf` | Secondary row buttons |
| Plum | `#873f63` | Brand, primary buttons, active sidebar item |
| Plum deep | `#5e2645` | Headline, pressed states |
| Ink | `#2b1622` | Body text, code block background |
| Mint / amber | `#1f7a5a` / `#a2560b` with tints | Pass and fail marks only, never decoration |

Typefaces: Bricolage Grotesque (headings and buttons), Atkinson Hyperlegible (body), JetBrains Mono (code, with ligatures off so `!=` reads literally). All three are SIL Open Font License; self-host them.

Page shell, all pages:

- Sticky top bar: logo and version badge, search, links to Docs, Examples, Changelog and GitHub, and a "Get started" button.
- Left sidebar of icon buttons in four groups: **Start** (Overview, Get started, Your first run), **Learn** (Features, Examples, Reports and handoffs), **Trust** (Security and permissions, Safety and limitations, Troubleshooting), **Project** (Changelog, Contributing). Below them, a "Reading this as an agent?" box links to `llms.txt` and the current page as Markdown.
- Right "On this page" rail and a latest-release card on wide screens.
- Sentence-case labels throughout. No all-caps button text, even though the Rust reference uses it.

Landing page, top to bottom:

1. Headline "Rehearse the plan before you hand it to a coding agent." and a short lede.
2. A short pilot-release notice under the lede, using the README's wording.
3. The rehearsal sheet: the retry fixture's plan with checks ticking in, then a verdict stamp. It plays once on load and stays static when reduced motion is requested. It is hand-written HTML, labeled as an authored example fixture, not a benchmark. **Its lines must match the fixture and the demo** ([`examples/README.md`](../../../examples/README.md), `examples/retry/`), replacing every line in the mockup:
   - Header: "plan.md: retry delay (one phase, one task)".
   - Pass: "R1: attempt 0 returns 1 second, covered by Task 1".
   - Pass: "R2: the delay doubles, covered by Task 1".
   - Fail: "R3: the 30-second cap has no task in the plan".
   - Fail: "Acceptance check on the uncapped code failed: `64 != 30`".
   - Fail: "No independent review has run yet".
   - Stamp: "Not ready", subline "Missing cap and no review". No "fix proposed" wording.
4. "Where to go next" rows: Get started (primary), Features, See the example, Security and permissions, Reports and handoffs, Changelog.
5. Install block with Claude Code and Codex tabs and a copy button, using the commands in `docs/wiki/Installation.md`.

Required notices (builder's call on exact placement, these override the mockup where it lacks them): the pilot-release notice on the landing page; "not a benchmark" on the rehearsal sheet and the Examples page; "independent project, not affiliated with Anthropic, OpenAI or Superpowers" in the site footer. The mockup's "A real report" wording becomes "the example report". `examples/README.md` currently says "comparative benchmark" rather than "not a benchmark", so the Examples page adds that notice itself at build time (a generated aside), leaving `examples/README.md` as the single source of its text. *(Superseded on 2026-10-18 by the maintainer: the "not affiliated" line was removed from the site.)*

Quality floor: responsive down to a 360px phone, visible keyboard focus, reduced motion respected, WCAG AA contrast in both themes, and a skip link.

## Content sources

| Site page | Source |
| --- | --- |
| Overview (landing) | New, from `README.md` and `docs/wiki/Home.md` |
| Get started | `docs/wiki/Installation.md` |
| Your first run | `docs/wiki/Usage.md` |
| Features | New, from the README's "Why use it?" and "The three skills" sections |
| Examples | `examples/README.md` and `examples/safety-cases.md` |
| Reports and handoffs | `docs/wiki/Reports-and-Handoffs.md` |
| Security and permissions | `SECURITY.md` |
| Safety and limitations | `docs/wiki/Safety-and-Limitations.md` |
| Troubleshooting | `docs/wiki/Troubleshooting.md` |
| Changelog | `CHANGELOG.md` |
| Contributing | `CONTRIBUTING.md` |

Overview and Features are short, hand-written site summaries that link to the full pages; they are not copies of the README, and the README stays the GitHub-facing summary (builder's-call note). The landing install block repeats the Claude Code and Codex install commands; a build-time check must fail if those commands no longer appear verbatim in the Get started page.

Root files that GitHub itself displays (`README.md`, `CHANGELOG.md`, `SECURITY.md`, `CONTRIBUTING.md`) stay where they are and remain the source; the site renders them at build time. The wiki pages move into the site's content folder and `docs/wiki/` is removed, so each page has exactly one editable copy.

## Repository and tooling constraints

- The site lives in its own top-level folder (suggested name `site/`) with its own `package.json` and lockfile. The Python tooling stays stdlib-only and unaffected.
- Pin Starlight, Astro and every plugin to exact versions in the lockfile. Starlight is pre-1.0, so treat minor updates as possibly breaking.
- Each additional package beyond Starlight and Astro is a new dependency and needs the maintainer's approval with a comparison, per the global dependency rules. The research found `starlight-llms-txt` 0.12.0 (by Starlight's lead maintainer) as the likely `llms.txt` choice; it still needs that approval. The implementation plan builds `llms.txt`, per-page Markdown and link checking with small dependency-free scripts instead, so neither `starlight-llms-txt` nor a link-validator plugin is needed.
- `scripts/check_package.py` must keep passing. It scans `docs/` Markdown for broken relative links and leaked home paths, and fails on symlinks in shipped folders.
- CI: add a separate site build job on pull requests, without making the existing `verify` job depend on Node. The build must also fail on broken internal links. Deploy with the official GitHub Pages actions on pushes to `main` only, with least-privilege permissions (`pages: write` and `id-token: write` on the deploy job only).
- Link and leak checks: after the wiki pages leave `docs/`, `check_package.py` no longer covers them. The site build takes over internal link checking (the plan's dependency-free checker; a link-validator plugin would need dependency approval), and the home-path leak check must be extended to the site's content folder.
- Follow the repository's plan workflow in `AGENTS.md`: a `plan/docs-site` branch, phase PRs squash merged into it, then a merge-commit PR into `main`.

## GitHub settings

These change settings outside the repository, so each needs the maintainer's go-ahead when the plan reaches it:

- Enable Pages with "GitHub Actions" as the source, before the first deploy.
- Add the site build as a required status check on `main` and `plan/**`, so a broken site actually blocks merging.

The site may be public before cutover; the wiki keeps working until then.

## Cutover

After the site is live and checked:

1. Replace every `github.com/snowholt-labs/plan-validation/wiki/...` link in `README.md`, `SECURITY.md` and the moved pages with site links.
2. Set the repository homepage to the site URL (it currently points to the wiki).
3. Replace the wiki with one Home page that links to the site, then disable the wiki in repository settings.

Steps 2 and 3 change GitHub settings outside the repository, so they need the maintainer's go-ahead at the time.

## Left to the builder

- How root Markdown files are pulled into Starlight (content loader, build-time copy into an ignored folder, or another approach), as long as there is one editable copy.
- How per-page Markdown is served (the research found no native Starlight feature; a small endpoint is the expected route).
- Starlight component overrides versus custom components for each part of the shell.
- The dark palette, derived from the light tokens and meeting AA contrast.
- Node version (a current LTS) and package manager.
- Page order within each sidebar group and the wording of short page descriptions.
