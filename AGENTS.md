# AGENTS.md

Guidance for coding agents (Codex, Claude Code and others) working in this repository.

## What this is

A dual-host agent plugin (Claude Code plugin + Codex skills) shipping three skills: `validate-plan`, `validation-args` and `revise-prompt`. Most of the product is Markdown instructions in `skills/*/SKILL.md` and `skills/validate-plan/references/`. The executable product code is the stdlib-only report renderer, `skills/validate-plan/scripts/render_report.py` with its diagram module `diagrams.py`, and the scripts inlined into generated reports: `skills/validate-plan/assets/report.js` (versions 1–3) and `report-v4.js` (versions 4 and 5).

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
- **`scripts/check_package.py`** checks matching manifest names and versions, skill frontmatter, that each `agents/openai.yaml` exists, relative Markdown links (outside fenced code), symlinks in shipped directories, leaked home-directory paths in Markdown (including the site pages in `site/src/content/`), that `userConfig.publish_artifact` in the Claude Code manifest is a non-sensitive boolean that defaults to `false`, with a title and description, that validate-plan's `SKILL.md` keeps the `Publish setting` line and both `SKILL.md` and `references/html-report.md` keep the publish gate sentence, that manifest icon paths exist, that shipped SVGs have no active or linked content, and that the report favicon matches `assets/plan-validation.svg`. Use placeholders like `<skill-directory>` in docs.
- **Report pipeline.** The agent writes `report.md` (eight numbered sections defined in `references/report-contract.md`) and `context.json` (shape in `references/html-report.md`). `render_report.py --report --context --output .../report.html` validates and writes `report.html`, a copy of `report.md`, and `handoff.txt`. It rejects a report rather than repairing it: wrong verdict wording, a `Ready` verdict without `review_status: complete`, non-5% confidence, score arithmetic errors, a missing or >80-word handoff (format v2 and later; a backtick-quoted absolute path counts as one word, and in version 4 and later only one without spaces, or a recorded PLAN or SPEC path or this run's `report.md` or `context.json` quoted exactly), or a `Not ready` handoff that contains an "implement" instruction or lacks `Do not start dependent implementation`. Versions 3 and later also check the phase grouping (every task once, in order; safe, unique phase IDs; consistent flags; waiting order) and one prompt per ready phase that stops at its own phase and, after the first in a new report, confirms the previous phase is merged, and writes a `handoff-phase-<id>.txt` per ready phase beside `handoff.txt`, deleting earlier ones first. Versions 4 and 5 (`page_v4`) draw the diagrams as inline SVG through `diagrams.py` (beside the renderer), which checks that every label fits and nothing overlaps, and inlines `assets/report-v4.css`, `assets/report-v4.js` and the decorative `assets/report-icon.svg` instead. Version 5 rejects `validation_run` and `rerun`, and in a new report rejects "run validation again first" in section 8 unless `do not need to`, `never have to`, `don't need to` (any of `not`, `never` or `n't` followed by `need to` or `have to`) or `no need to` comes right before it; its drift warning names no run. A version 5 render, and any new render, deletes an earlier `rerun.txt`. Saved version 4 reports keep their run fields: the renderer still checks `validation_run` and the `rerun` recommendation, starts `handoff.txt` and each phase prompt file with a held note while a `yes` holds the ready phases (JSON `handoff_held`), and a saved version 4 re-render keeps its existing `rerun.txt`. `assets/report.css` and `report.js` (versions 1–3) are inlined, and `assets/favicon.svg` is embedded as a base64 data URI (allowed by the CSP's `img-src data:`), so the HTML stays self-contained (no external scripts, fonts or analytics). Raw HTML in the report is escaped.
- **Format versions.** `context.format_version` 1 is legacy; 2 (adds the "Feature at a glance" diagram and "Decisions made without your reply", and enforces the exact source section headings) now renders saved reports only; 3 (adds the task inventory, the phase grouping and one prompt per ready phase) now renders saved reports only; 4 (drops `feature` for 1–3 data-drawn `diagrams`, and adds `project`, `audience`, `title_accent`, `open_decisions`, `watch_list`, `validation_run`, `rerun`, `rerun.txt`, held prompts and the tabbed page) now renders saved reports only; 5 is current (version 4 without `validation_run`, `rerun`, `rerun.txt` or held prompts). New reports (`kind: new`) must use version 5; versions 1–4 render only saved reports. Versions 1–3 output is frozen by `test_legacy_output_is_frozen`, and saved version 4 output by `test_v4_saved_output_is_frozen`; neither test's digests are ever re-pinned. Do not migrate old reports.
- **Demo.** `scripts/demo.py` runs `examples/retry/checks.py` against `uncapped.py` (must fail with `64 != 30`) and `corrected.py` (must pass), then renders a labeled Not ready example through the real renderer. Changing the fixture or the renderer contract can break the demo.

## Conventions

- Skill text is behavioral contract: changes to permissions, research approval, evidence labels or report semantics affect agent behavior. Check them against `docs/evaluation.md`. Renderer tests do not validate agent behavior.
- For renderer, `diagrams.py`, `report.js` or `report-v4.js` changes, add a regression for the observable failure. Do not test wording for its own sake.
- Do not add runtime dependencies without maintainer agreement.
- User documentation lives in `site/src/content/docs/` and is published as the documentation site. `docs/` still holds `evaluation.md` and `verification.md`. Root files (`CHANGELOG.md`, `SECURITY.md`, `CONTRIBUTING.md`, `examples/README.md`, `examples/safety-cases.md`) are synced into the site at build time; edit them at the root, not in the synced copies. `dist/` and other gitignored folders are local material, not part of the package.

## Git workflow

These rules override an agent's own or global instructions for this repo: use this repo's template, labels and merge methods, and add no extra PR sections, labels or tracking issues.

- `main` and `plan/**` require a PR, the `verify` check and the `review/code` and `review/security` commit statuses (the `Required reviews` ruleset). Other branches are not protected.
- Every PR into `main` is merged with a merge commit, never squash. Only phase PRs into a plan branch are squash merged.
- Ask the maintainer before any merge, and first confirm on the PR head that CI passed (`gh pr checks <number>`), that `review/code` and `review/security` are `success`, and that both comment reviews name that head.
- Code and security review means a code review and a security review of the PR diff, with findings fixed, explicitly accepted or parked as the plan's Phase workflow allows (in Claude Code, `/code-review`, always typed with the level that step 9 of the current Phase workflow block in `skills/validate-plan/references/phase-workflow.md` types, for every PR, including PRs outside a plan and phases of plans on an older block, and `/security-review`, both aimed at the PR's base..head range with step 9's read-only subagent fallback; in other hosts, an equivalent independent review). A plan's docs PR may reuse the validation run's reviews, and later pushes to a phase PR get change-only reviews (see below).
- Every PR into `main` or `plan/**` gets both reviews, docs-only PRs included. A plan's docs PR reuses the validation run's code and security reviews when it changes only the plan and spec, both hash to the final values in the report's `context.json`, and section 7 records what each review read ("Reuse on the docs PR" in `skills/validate-plan/references/validation-reviews.md`). Each comment review then adds a `Reused:` line with the hash its review read and the final hash, and `Scope:` lines naming what covered the difference: each validation fix and any end-of-run answer edits, with the reviews that covered them. Otherwise each review runs once, typed and targeted as Phase workflow step 9 types and targets them, on what differs from the text it read or on the full plan and spec, plus any other changed files. A docs-only phase PR gets the code review and the security review once each on its final head, typed and targeted as Phase workflow step 9 types and targets them for a code phase. A finding whose fix would change a security or privacy boundary, a permission or an external action goes to the maintainer; one that only disagrees with a decision the maintainer recorded is rejected with that decision as evidence.
- Post each review's result as its own comment review (`gh pr review <number> --comment --body-file <file>`), starting with `## Code review` or `## Security review` and the lines `Result: pass|fail`, `Head: <full sha>` and `Base: <branch> <sha>`. Then set the matching `review/code` or `review/security` commit status on the reviewed head, `success` only when every finding is fixed, explicitly accepted, or parked under the plan's Phase workflow and listed first in the code comment review (a security finding is never parked). Each comment review names the current head in `Head:` and lists in `Scope:` lines what each review saw: the full review's head, and each later fix or change range with its reviewer. After a new push to a phase PR (a fix, base change or conflict fix), the change goes through the Phase workflow's steps 2–8, and the new head gets a `## Code review` whose `Scope:` names that change and links the full review, a `## Security review` of that change only, targeted as Phase workflow step 9 says, and both statuses. Every other PR, including every PR into `main`, needs both full reviews again after a new push.

### Plan work

This repo follows the per-phase workflow published in `site/src/content/docs/phased-implementation.md`, and every docs-only PR also gets both reviews. Each phase follows the plan's Phase workflow section; the bullets below add this repository's specifics to its review and delivery steps, not extra review rounds. A plan whose Phase workflow lacks the `<!-- phase-workflow: 2 -->` marker gets a docs PR that swaps in the current block before its next phase starts, with `Replaced on <date>: workflow steps only, no scope change.` under the heading; that PR lists any task that crosses a boundary without integration test infrastructure, for the maintainer to approve or defer.

- A plan uses a `plan/<topic>` branch (the protection rule matches only this prefix) and a milestone named after the plan. Implement each phase in its own fresh session, on its own branch with a PR into the plan branch. Start a phase only after the previous one is merged into the plan branch; confirm this first and stop if it is not. Merged earlier phases and ticked task checkboxes are expected; reconcile any other plan, spec or approval change with the validation report first.
- Phase review, before opening the PR: the Phase workflow's review loop and readiness check (steps 4–8), with no round cap; a problem that keeps returning follows its stuck rule. List minor items in the code comment review; the end-of-phase report asks the maintainer to fix or skip each, and skipped or unanswered ones are saved as action points for the plan-to-`main` review.
- Run the code review and the security review once each on every phase's final head, typed and targeted as Phase workflow step 9 types and targets them, whether or not the validation report flags it as security-sensitive.
- Open the PR, wait for CI to pass (fix failures before going on), post both comment reviews and their `review/*` statuses, then stop and print the next phase's prompt from the report, after the design-update prompt when a finding was parked (Phase workflow step 10). The maintainer merges and starts the next phase.
- The plan-to-`main` PR gets a full code and security review of the whole diff, which also resolves the saved action points and checks that every entry under the plan's `## Parked findings` names a fixing task that is done.

### Other changes

Use a short-lived branch and a PR into `main`. Merge with a merge commit (not squash) after CI and code and security review.

### Releases

1. Open a dedicated release PR, for example from `release/vX.Y.Z`. It contains only release changes: the version bump in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and `.codex-plugin/plugin.json`, the `CHANGELOG.md` entry, and docs that name the release (such as the tag in `site/src/content/docs/get-started.md` and the release checks in `docs/verification.md`).
2. Merge it with a merge commit after CI and code and security review.
3. Tag `vX.Y.Z` on the merged `main` commit, then publish the GitHub release.

### Pull request metadata

- Write the body with the sections of `.github/PULL_REQUEST_TEMPLATE.md`: Tracking, Problem and resulting behavior, Verification, Scope and permissions, Reviews.
- In the Tracking block, `Plan issue:` stays `none`: this repo opens no plan tracking issues.
- Use existing labels only: `bug`, `enhancement`, `documentation`, `accessibility`.
- Add the plan's milestone to phase PRs and the plan-to-`main` PR. Other PRs get no milestone. The repository has no GitHub project.
