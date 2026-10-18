# AGENTS.md

Guidance for coding agents (Codex, Claude Code and others) working in this repository.

## What this is

A dual-host agent plugin (Claude Code plugin + Codex skills) shipping three skills: `validate-plan`, `validation-args` and `revise-prompt`. Most of the product is Markdown instructions in `skills/*/SKILL.md` and `skills/validate-plan/references/`. The executable product code is the stdlib-only report renderer, `skills/validate-plan/scripts/render_report.py`, and `skills/validate-plan/assets/report.js`, which is inlined as a script into every generated report.

## Commands

Python 3.10+, standard library only. No install step. CI (`.github/workflows/ci.yml`) runs the equivalent of:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py'
python3 scripts/check_package.py
python3 scripts/demo.py --output "$(mktemp -d)/demo"   # the output directory must not already exist
```

Single test: append `-k <test_name>` to the unittest command (the test imports `render_report` directly, so keep `-s skills/validate-plan/scripts`).

For the documentation site (Node), run the following. The Python tooling needs no Node.

```bash
cd site && npm ci && npm test && npm run build
```

If Claude Code is installed, also run `claude plugin validate .` and `claude plugin validate .claude-plugin/plugin.json`.

## Architecture

- **Packaging.** `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and `.codex-plugin/plugin.json` must share the same name and version. Each skill needs `SKILL.md` frontmatter whose `name` matches its directory, and an `agents/openai.yaml` (Codex metadata). `validate-plan` sets `disable-model-invocation: true` and `allow_implicit_invocation: false`; keep it explicit-only. No script checks these two flags, so review them by hand.
- **`scripts/check_package.py`** checks matching manifest names and versions, skill frontmatter, that each `agents/openai.yaml` exists, relative Markdown links (outside fenced code), symlinks in shipped directories, leaked home-directory paths in Markdown (including the site pages in `site/src/content/`), that manifest icon paths exist, that shipped SVGs have no active or linked content, and that the report favicon matches `assets/plan-validation.svg`. Use placeholders like `<skill-directory>` in docs.
- **Report pipeline.** The agent writes `report.md` (eight numbered sections defined in `references/report-contract.md`) and `context.json` (shape in `references/html-report.md`). `render_report.py --report --context --output .../report.html` validates and writes `report.html`, a copy of `report.md`, and `handoff.txt`. It rejects a report rather than repairing it: wrong verdict wording, a `Ready` verdict without `review_status: complete`, non-5% confidence, score arithmetic errors, a missing or >80-word handoff (format v2; a backtick-quoted absolute path counts as one word), or a `Not ready` handoff that contains an "implement" instruction or lacks `Do not start dependent implementation`. `assets/report.css` and `report.js` are inlined, and `assets/favicon.svg` is embedded as a base64 data URI (allowed by the CSP's `img-src data:`), so the HTML stays self-contained (no external scripts, fonts or analytics). Raw HTML in the report is escaped.
- **Format versions.** `context.format_version` 1 is legacy, 2 is current (adds the "Feature at a glance" diagram and "Decisions made without your reply"). Version 2 also enforces the exact source section headings. New reports (`kind: new`) must use version 2; version 1 renders only saved reports. Do not migrate old reports.
- **Demo.** `scripts/demo.py` runs `examples/retry/checks.py` against `uncapped.py` (must fail with `64 != 30`) and `corrected.py` (must pass), then renders a labeled Not ready example through the real renderer. Changing the fixture or the renderer contract can break the demo.

## Conventions

- Skill text is behavioral contract: changes to permissions, research approval, evidence labels or report semantics affect agent behavior. Check them against `docs/evaluation.md`. Renderer tests do not validate agent behavior.
- For renderer or `report.js` changes, add a regression for the observable failure. Do not test wording for its own sake.
- Do not add runtime dependencies without maintainer agreement.
- User documentation lives in `site/src/content/docs/` and is published as the documentation site. `docs/` still holds `evaluation.md` and `verification.md`. Root files (`CHANGELOG.md`, `SECURITY.md`, `CONTRIBUTING.md`, `examples/README.md`, `examples/safety-cases.md`) are synced into the site at build time; edit them at the root, not in the synced copies. `dist/`, `publication-notes/`, `superpowers-comparison/` and `2026-10-14-superpowers-validate-plan-research/` are gitignored local material, not part of the package.

## Git workflow

- Never push directly to `main`. Every change goes through a branch and a pull request.
- Every PR into `main` is merged with a merge commit, never squash. Only phase PRs into a plan branch are squash merged.
- Ask the maintainer before any merge. Confirm CI passed on the PR head (`gh pr checks <number>`) before asking. GitHub requires a PR and the `verify` check for `main` and `plan/**` branches; other branches are not protected.
- "Code and security review" below means a code review and a security review of the PR diff, with findings fixed or explicitly accepted. In Claude Code, run `/code-review` and `/security-review`; in other hosts, use an equivalent independent review.

### Plan work

1. Create a plan branch from `main` named `plan/<topic>` (the protection rule matches only this prefix), and a GitHub milestone named after the plan.
2. Implement each phase on its own branch from the plan branch and open a PR into the plan branch.
3. Squash merge the phase PR after CI and code and security review pass.
4. When all phases are merged, open a PR from the plan branch into `main`. Run code and security review on the full diff to catch cross-phase issues. After CI passes, merge with a merge commit (not squash), so each phase stays visible in history.

### Other changes

Use a short-lived branch and a PR into `main`. Merge with a merge commit (not squash) after CI and code and security review pass.

### Releases

1. Open a dedicated release PR, for example from `release/vX.Y.Z`. It contains only release changes: the version bump in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and `.codex-plugin/plugin.json`, the `CHANGELOG.md` entry, and docs that name the release (such as the tag in `site/src/content/docs/get-started.md` and the release checks in `docs/verification.md`).
2. Merge with a merge commit (not squash) after CI and code and security review pass.
3. Tag `vX.Y.Z` on the merged `main` commit, then publish the GitHub release.

### Pull request metadata

- Write the body with the sections of `.github/PULL_REQUEST_TEMPLATE.md`: Problem and resulting behavior, Verification, Scope and permissions.
- Use existing labels only: `bug`, `enhancement`, `documentation`, `accessibility`.
- Add the plan's milestone to phase PRs and the plan-to-`main` PR. Other PRs get no milestone. The repository has no GitHub project.
