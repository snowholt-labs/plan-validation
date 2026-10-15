# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Branch, PR, merge and release rules are in AGENTS.md (shared with Codex):

@AGENTS.md

## What this is

A dual-host agent plugin (Claude Code plugin + Codex skills) shipping three skills: `validate-plan`, `validation-args` and `revise-prompt`. Most of the product is Markdown instructions in `skills/*/SKILL.md` and `skills/validate-plan/references/`. The only executable product code is the stdlib-only HTML report renderer, `skills/validate-plan/scripts/render_report.py`.

## Commands

Python 3.10+, standard library only. No install step. These three are what CI runs:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py'
python3 scripts/check_package.py
python3 scripts/demo.py --output /tmp/plan-validation-demo   # output dir must not already exist
```

Single test: append `-k <test_name>` to the unittest command (the test imports `render_report` directly, so keep `-s skills/validate-plan/scripts`).

If Claude Code is installed, also run `claude plugin validate .` and `claude plugin validate .claude-plugin/plugin.json`.

## Architecture

- **Packaging.** `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and `.codex-plugin/plugin.json` must share the same name and version; bump all three together for a release. Each skill needs `SKILL.md` frontmatter whose `name` matches its directory and an `agents/openai.yaml` (Codex metadata, including `allow_implicit_invocation`). `validate-plan` sets `disable-model-invocation: true` and `allow_implicit_invocation: false`; keep it explicit-only.
- **`scripts/check_package.py`** enforces the above, plus: no broken relative Markdown links (outside fenced code), no symlinks in shipped directories, and no leaked `/home/<user>/` or `/Users/<user>/` paths in Markdown. Use placeholders like `<skill-directory>` in docs.
- **Report pipeline.** The agent writes `report.md` (eight numbered sections defined in `references/report-contract.md`) and `context.json` (shape in `references/html-report.md`). `render_report.py --report --context --output .../report.html` validates and writes `report.html`, a copy of `report.md`, and `handoff.txt`. It rejects a report rather than repairing it: wrong verdict wording, a `Ready` verdict without `review_status: complete`, non-5% confidence, score arithmetic errors, a missing or >80-word handoff (format v2), or a `Not ready` handoff lacking `Do not start dependent implementation`. `assets/report.css` and `report.js` are inlined so the HTML stays self-contained (no external scripts, fonts or analytics). Raw HTML in the report is escaped.
- **Format versions.** `context.format_version` 1 is legacy, 2 is current (adds the "Feature at a glance" diagram and "Decisions made without your reply"). Keep v1 reports rendering; do not migrate old reports.
- **Demo.** `scripts/demo.py` runs `examples/retry/checks.py` against `uncapped.py` (must fail with `64 != 30`) and `corrected.py` (must pass), then renders a labeled Not ready example through the real renderer. Changing the fixture or the renderer contract can break the demo.

## Conventions

- Skill text is behavioral contract: changes to permissions, research approval, evidence labels or report semantics affect agent behavior. Check them against `docs/evaluation.md`. Renderer tests do not validate agent behavior.
- For renderer changes, add a regression for the observable failure. Do not test wording for its own sake.
- Do not add runtime dependencies without maintainer agreement.
- `docs/wiki/` is the source for the GitHub wiki. `dist/`, `publication-notes/`, `superpowers-comparison/` and `2026-10-14-superpowers-validate-plan-research/` are gitignored local material, not part of the package.
- PRs use `.github/PULL_REQUEST_TEMPLATE.md` sections: Problem and resulting behavior, Verification, Scope and permissions.
