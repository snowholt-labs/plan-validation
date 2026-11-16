# Directory Edition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a generated, policy-clean directory edition of the plugin in `directory-edition/`, built from `skills/` so it cannot drift from the full plugin unnoticed.

**Architecture:** `scripts/build_directory_edition.py` copies the Markdown skill files, drops what the edition cannot ship, and swaps in whole-file overrides from `editions/directory/overrides/`. Each override is pinned to the SHA-256 of the full-edition file it replaces. `scripts/check_directory_edition.py` checks the output against each rule in the directory's refusal text. CI regenerates the edition and fails on any difference.

**Tech Stack:** Python 3.10+ standard library (`pathlib`, `json`, `hashlib`, `unittest`); Markdown skill text; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-15-directory-edition-design.md`

## Phase workflow

<!-- phase-workflow: 2 -->

Every phase follows these steps, in a fresh session, on its own phase branch. When Superpowers is installed, load each named skill with the Skill tool at its step. A subagent that does a step loads that step's skill itself, and its brief says so: under `superpowers:subagent-driven-development`, each implementer subagent loads `superpowers:test-driven-development` and `superpowers:systematic-debugging`. Where a loaded skill hands off to branch finishing, do not follow that hand-off; continue with the next step of this workflow. Where a loaded skill says to stop and ask, to ask for consent or to wait for the human partner, the stop reasons below decide instead. Without Superpowers, follow each step as written.

1. Work in a git worktree for the phase branch (`superpowers:using-git-worktrees`); this step gives that skill's consent. Read the phase's done-check in section 8 of the validation report, when it has one. If the plan has a `## Parked findings` section that lists a finding from an earlier phase missing from `revised-plan.md` in the report's run directory, and the entry has no `Accepted:` line, the design update (step 10) has not run: stop and say so. Compared with `revised-plan.md` and `revised-spec.md`, these differences are expected: earlier phases merged into the plan branch, ticked task checkboxes (`- [ ]` to `- [x]`), entries added under `## Parked findings` (and its heading, if new), each with an `Accepted: <reason> (maintainer, <date>).` line, with no other change to that section, and a swapped block. A `Replaced on <date>` line under the `## Phase workflow` heading marks a swapped block; that swap is expected when it changes nothing outside that section and the section carries the marker. Lines under `Replaced on <date>`, such as a `Boundary tasks:` line, are part of the swap. Any other change, or a swap without the marker, needs reconciliation.
2. For each task with observable behavior, write the failing tests first and watch each fail for the expected reason (`superpowers:test-driven-development`): a unit test, plus an integration test when the task crosses a boundary (database, API, authentication, another service). Wording-only, configuration, version and changelog tasks, and fixes of that kind, skip the test-first rule. A task that the `Boundary tasks:` line approves without integration tests skips the integration test; a task it defers is not built until the maintainer schedules it: step 8 leaves its tests out, and the end-of-phase report lists it as deferred.
3. Write the minimal code that makes the tests pass, keep all tests green, then refactor. Repeat steps 2–3 for each task.
4. Review the phase with a fresh reviewer (`superpowers:requesting-code-review`), given the plan and spec paths and the report path named in the phase prompt. Round 1 reviews the phase's base..head range; when `superpowers:subagent-driven-development` ran the tasks, its final review is round 1. Later rounds review only the latest fix and the code it touches. The reviewer sets each finding's severity (Critical counts as High, Important as Medium, Minor as Low); the fixing session never re-rates.
5. Check each finding against the code before acting (`superpowers:receiving-code-review`). Close each Medium or High finding exactly one way: a real bug gets a failing test, a root-cause fix and a passing test; a wrong finding is rejected with evidence; a finding whose fix would change the design gets the smallest fix inside the design, or is parked. To park a finding, add a line under `## Parked findings` at the end of the plan (create the section if needed): `- Phase <id>: <finding>, <file:line>. Decision: <what>; why: <why>; cost if wrong: <cost>.` A security finding is never parked: when its fix would change the design, that is a stop reason. Only the design update (step 10) adds an `Accepted:` line to a parked entry, on the maintainer's choice, and never to a security finding.
6. Repeat steps 4–5 until no Medium or High finding remains. There is no round cap, including subagent-driven-development's per-task limit. If the same problem returns after a fix, or three fixes for one problem fail, stop patching and question the design (`superpowers:systematic-debugging`) without first waiting to discuss it. If the design is the cause, or the root cause still cannot be fixed, park the finding as step 5 does; the design update (step 10) then fixes it in a fixing phase or records the maintainer's acceptance. A stuck security finding is a stop reason. List Low findings without looping on them; the end-of-phase report asks the maintainer to fix or skip each one. A security finding is closed at any severity, Low included, and never listed for fix or skip.
7. For any failing test or unexpected behavior, find the root cause before fixing it (`superpowers:systematic-debugging`), then return to step 2.
8. Prove the phase is ready (`superpowers:verification-before-completion`): run the done-check, if any, and the full unit and integration suites, read the output, and claim only what it shows. If anything fails, go to step 7.
9. Run the code review and the security review once each on the final head, on the phase's base..head range only (in Claude Code, `/code-review high --max-findings all` and `/security-review`; in other hosts, an equivalent independent review). Name the range as each review's target; when a review cannot take it, would skip files in it (such as documentation that `/security-review` skips), or returns a result that cites nothing from it, run its procedure in a fresh read-only subagent on a saved diff of the range (`git diff --no-color --no-ext-diff --no-textconv --text <base>..<head>`), with every changed file in scope. Wait for each result. Close every confirmed finding as step 5 does, Low included, and every security finding at any severity; a non-security Low finding whose fix would change the design is not parked but listed for the maintainer to fix or skip, as step 6 lists Lows. A fix, including a line added under `## Parked findings`, is a commit that goes through steps 2–8: step 4 reviews only that commit, and the security review runs again on its diff only; the code review does not run again. Record what each review saw: the head it read, and each fix range with its reviewer.
10. Deliver the branch as the repository's rules define (for a plan branch, a PR into that branch). Never merge locally into a protected or plan branch. Push and open a PR only when the repository's rules or the maintainer authorize it; otherwise stop and report that the branch is ready. List parked findings first in the code review comment, and track each as the repository's rules allow. A later commit, base change or conflict fix goes through steps 2–8 on that change only, and the security review runs on that change only (targeted as step 9 says), unless the PR targets the default branch or the repository's rules require both full reviews again; after a rebase, the change is what differs between the two saved diffs, kept together in one file: `git diff --no-color --no-ext-diff --no-textconv --text <old-base>..<old-head>` and then the same command for `<new-base>..<new-head>` appended to the same file, where `<old-base>` is `git merge-base <old-head> <new-base>` (`git range-diff` can show changed Markdown as unchanged); and after a base merge, what `git show --remerge-diff --no-color --no-ext-diff --no-textconv --text <merge-commit>` shows for each base merge in that change; save that output and give each review the saved copy as its target. Do not run `superpowers:finishing-a-development-branch`. When a finding was parked, print this design-update prompt before the next phase's prompt (or alone, after the last phase), and mark the next phase's prompt as waiting for the design update, and for the new report's prompts when a finding gets a fixing phase: "Design update after Phase <id>: brainstorm the parked findings in the plan's `## Parked findings` with the maintainer. For each one the maintainer accepts, add `Accepted: <reason> (maintainer, <date>).`; for the others, update the spec and plan with a fixing phase, add `Fixing task: Task <n>.` and validate the remaining phases as a phase-only validation. Land the changes as the repository's rules define (for a plan branch, a docs PR into that branch). Do not start the next phase until they land."

Stop reasons: ask the maintainer only when the next step is destructive, is a security-sensitive action (such as changing access rules or secret handling; not every step of a security-sensitive phase), needs an approval or authorization not already given (such as a merge, an install or another outside effect), or the plan is too broken to follow (including an environment that cannot run a required check). The stops in steps 1, 5 and 6 are cases of these: a design update, or a design change for a security finding, needs the maintainer's approval, and any further fix of a stuck security finding is a security-sensitive action. Otherwise decide, record the decision and continue. When a phase prompt carries the older pause sentence, these stop reasons govern.

A docs-only phase skips step 2's test-first rule. Its step 9 runs the reviews the repository's rules require for docs-only changes.

## Global Constraints

- Standard library only, and no new runtime dependency (`AGENTS.md`).
- The full edition does not change: no edit to `skills/`, `.claude-plugin/`, `.codex-plugin/`, the renderer or its frozen-output tests. `test_legacy_output_is_frozen` and `test_v4_saved_output_is_frozen` digests are never re-pinned.
- Plugin name: `plan-validation`, the same as the full edition (spec, Open questions 1: approved by the maintainer on 2026-11-15).
- Generated output lives at `directory-edition/` and is committed. Never edit it by hand; regenerate it.
- Files the edition may contain: `.md`, `.txt`, `.json`, `.yaml`, `.yml`, PNG/JPEG/GIF/WebP/ICO images, and the extensionless `LICENSE`. All text is UTF-8 with no NUL byte, and no file starts with `#!`.
- Edition `plugin.json` keys, exactly this set: `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, `icon`. No `userConfig`.
- Edition SKILL.md frontmatter keys: only `name`, `description` and `disable-model-invocation`. `validate-plan` keeps `disable-model-invocation: true`.
- Dropped-reference terms that never appear in the output: `render_report`, `context.json`, `report.html`, `html-report.md`. Shipped text never names them, not even to say a file is not written.
- Hash command named in shipped text: `shasum -a 256` or `sha256sum`, whichever is present.
- Skill text is behavioral contract. Phase P2's reviews check Tasks 3 and 4 against the existing `docs/evaluation.md` rows; Task 6 adds the two directory-edition rows, and Task 7's manual run exercises them.
- Markdown uses placeholders, never home-directory paths. Shipped text is neutral and professional. The repository is public: no private names, rules or paths.

## Review Focus

1. **The full edition's `SKILL.md` changes later and nobody touches its override.** Expected: `build --check` fails and names the file and "source changed"; CI goes red. Covered by Task 2 `test_stale_override_hash_fails`.
2. **A new file appears under `skills/` that is neither Markdown nor in the drop list (say a `.sh` helper).** Expected: the build stops and names it, rather than silently shipping or dropping it. Covered by Task 2 `test_unexpected_file_type_fails`.
3. **A file copied unchanged later gains a renderer reference or a `context.json` field name.** Expected: the checker's `dropped-reference` or `dropped-field` rule fails on it. Covered by Task 1 `test_dropped_reference` and `test_dropped_field`.
4. **The output folder holds a stale extra file after an override is removed.** Expected: `--check` reports `extra: <path>`, and a rebuild removes it. Covered by Task 2 `test_check_reports_extra_missing_and_differing` and `test_main_replaces_previous_output`.
5. **A `Not ready` report from the edition.** Expected: the agent's self-check catches an implement instruction and a missing `Do not start dependent implementation`, and fixes it before reporting. Covered by Task 3's self-check list and Task 7's broken sample.

## Coverage

| Spec item | Task |
|---|---|
| Layout, generator steps 1–5, deterministic output | Task 2, Task 4 |
| Generator step 6 (links to dropped files): rejected, never rewritten. Today only `skills/validate-plan/SKILL.md` links to a dropped file, and its override changes those links. A later copied file that links to a dropped or outside file fails PACKAGE | Task 5 |
| Overrides (SKILL.md, markdown-report.md, report-contract.md, validation-reviews.md, handoff-template.md, research-permissions.md) | Tasks 3–4 |
| Report data without `context.json` | Task 3 (markdown-report.md), Task 4 (report-contract.md) |
| Agent self-check | Task 3 |
| Policy checker, dropped-reference and dropped-field rules | Task 1 |
| Sync check (`build --check`), CI steps | Task 2 (sync check), Tasks 1 and 4 (CI steps) |
| `check_package.py` changes | Task 5 |
| Releases with four manifests, `AGENTS.md` | Task 6 |
| Documentation (edition README, get-started note) | Task 4 (README), Task 6 (site, root README) |
| Verification (plugin validate, manual run, broken sample) | Task 7 |
| After submission | Task 7 (submission notes) |

## Delivery

- Plan branch `plan/directory-edition`, milestone "Directory edition". `AGENTS.md` governs branches, reviews and merges, except as the next bullet records.
- Merges: the maintainer approved on 2026-11-15 that this plan's docs PRs and phase PRs, each with base `plan/directory-edition` (a docs PR includes a Phase workflow step 10 design update), merge without asking again. A PR with any other base is not covered. This approval answers `AGENTS.md`'s "Ask the maintainer before any merge" for those PRs only, and the session merges instead of "The maintainer merges". Before merging, it runs `AGENTS.md`'s pre-merge checks on the PR head: `gh pr checks <number>` passes, `review/code` and `review/security` are `success`, and both comment reviews name that head. It then merges with `gh pr merge <number> --squash --match-head-commit <head>` for a phase PR or `gh pr merge <number> --merge --match-head-commit <head>` for a docs PR (`AGENTS.md`: only phase PRs into a plan branch are squash merged), and stops and prints the next phase's prompt, after the design-update prompt when a finding was parked (Phase workflow step 10). Any PR into `main`, including a docs PR and the plan-to-`main` PR, still needs the maintainer's explicit yes.
- Proposed phases (validation sets the final grouping): **P1** Tasks 1–2 (tooling), **P2** Tasks 3–5 (edition content, packaging), **P3** Tasks 6–7 (docs and verification).
- Every `git commit` runs in the same command as `git branch --show-current`, and stops if the branch is not the expected phase branch. Commit messages end with `Plan: docs/superpowers/plans/2026-11-15-directory-edition.md`, `Phase: <id>`, `Task: <n>`.
- Commands:
  - **UNIT:** `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py'`
  - **TOOLS:** `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts -p 'test_*.py'`
  - **PACKAGE:** `python3 scripts/check_package.py`
  - **EDITION:** `python3 scripts/build_directory_edition.py --check && python3 scripts/check_directory_edition.py`
  - **DEMO:** `python3 scripts/demo.py --output "$(mktemp -d)/demo"`
  - **SITE:** `cd site && npm ci && npm test && npm run build`
- Submission to the directory is the maintainer's action, after the plan reaches `main` and a release. It is not part of any phase.

---

### Task 1: Policy checker

**Files:**
- Create: `scripts/check_directory_edition.py`
- Create: `scripts/test_directory_edition.py`
- Modify: `.github/workflows/ci.yml` (job `verify`)

**Interfaces:**
- Produces: `check_edition(root: Path) -> list[str]`. Each error is `"<rule-id>: <posix relative path>: <message>"`, sorted. `main(argv: list[str] | None = None) -> int` checks `<repo>/directory-edition` by default, or the path given as the only argument. It prints the errors and returns 1, or prints `Directory edition: <n> files checked.` and returns 0.
- Rule IDs, one check each:
  - `allowed-type`: extension allowlist; images must start with their format's magic bytes (`\x89PNG\r\n\x1a\n`, `\xff\xd8\xff`, `GIF87a`/`GIF89a`, `RIFF`…`WEBP` at bytes 8–12, `\x00\x00\x01\x00`).
  - `shebang`
  - `text-encoding`: every file except an allowed image must decode as UTF-8 and hold no `\x00`.
  - `package-config`: `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `yarn.lock`, `.npmrc`, `.yarnrc`, `.yarnrc.yml`, `bun.lockb`, `pyproject.toml`, `requirements.txt`, `Pipfile`, `poetry.lock`, `uv.lock`.
  - `claude-folder`: any `.claude/` directory.
  - `plugin-folder`: a `.claude-plugin/` anywhere but the root, or a root `.claude-plugin/` holding anything but `plugin.json` and `icon.png`.
  - `unread-config`: `hooks.json`, `.mcp.json`, `.lsp.json`, `monitors.json`, or a top-level `commands/`, `agents/`, `output-styles/` or `hooks/`.
  - `codex-metadata`: any `agents/openai.yaml`.
  - `manifest-fields`: `plugin.json` keys outside the Global Constraints set; an `author` that is not an object, or has keys outside `name`, `email`, `url`.
  - `frontmatter-fields`: each `skills/*/SKILL.md` must start with frontmatter whose keys are only `name`, `description` and `disable-model-invocation`, with `name` equal to its directory; `skills/validate-plan/SKILL.md` must also have `disable-model-invocation: true`. Its test also covers a `validate-plan` frontmatter without that line.
  - `path-characters`: a path segment outside `[A-Za-z0-9._-]`.
  - `dropped-reference`: the four terms from Global Constraints.
  - `dropped-field`: in any file under `skills/`, a match of the regular expression `open_decisions|watch_list|review_status|handoff_status|task_inventory|waits_for|security_review|security_reason|docs_only|holds_back|decisions_without_reply|format_version|validation_run|phase_handoffs|title_accent|published_at|html_sha256|rerun\.txt|kind: (new|saved)|--open|user_config` (the `context.json` field names, run files and options the edition does not have).
  - `symlink`
- Refusal rule to rule ID (spec Constraints restates the refusal text):

  | Spec Constraints item | Rule IDs |
  |---|---|
  | only allowed file types, judged by content | `allowed-type`, `text-encoding` |
  | no file starting with `#!` | `shebang` |
  | UTF-8 with no NUL bytes | `text-encoding` |
  | no package manager configuration, no `package.json` | `package-config` |
  | no `.claude/skills` folder | `claude-folder` |
  | `.claude-plugin/` holds only `plugin.json` and the icon | `plugin-folder` |
  | only manifest and frontmatter fields Claude Code reads | `manifest-fields`, `frontmatter-fields`, `unread-config`, `codex-metadata` |
  | repository additions (not in the refusal text) | `path-characters`, `dropped-reference`, `dropped-field`, `symlink` |

- [ ] **Step 1: Write the failing tests.** Class `CheckEditionTest` in `scripts/test_directory_edition.py`. It imports the module by adding `scripts/` to `sys.path`. Helper `make_edition(tmp: Path) -> Path` writes a minimal valid tree:
  - `.claude-plugin/plugin.json` with the allowed keys;
  - `.claude-plugin/icon.png` holding the PNG magic plus 8 bytes;
  - `README.md`, `LICENSE`;
  - `skills/validate-plan/SKILL.md` with frontmatter `name: validate-plan`, a description and `disable-model-invocation: true`.

  Tests:
  - `test_valid_edition_passes`: `check_edition(root) == []`.
  - One test per rule ID: mutate the valid tree, then assert that exactly one error starts with `"<rule-id>: "` and names the path. For example, `test_shebang` writes `README.md` starting `#!/bin/sh`; `test_dropped_reference` adds `context.json` to `README.md`; `test_dropped_field` adds `waits_for` to `skills/validate-plan/SKILL.md`; `test_manifest_fields` adds `"userConfig": {}`; `test_allowed_type` adds `x.py`, and a separate assertion renames a text file to `icon.png` inside `.claude-plugin`.
  - `test_main_exit_codes`: `main([str(root)])` returns 0 for the valid tree and 1 for a broken one. No test calls `main` without a path, so none reads or writes the real `directory-edition/`.

- [ ] **Step 2: Run them to verify they fail.** Run TOOLS. Expected: errors on importing `check_directory_edition`.
- [ ] **Step 3: Implement `check_edition` and `main`** in `scripts/check_directory_edition.py`. Walk with `os.walk(followlinks=False)`, report symlinks rather than follow them, and parse frontmatter as the `key: value` lines between the first two `---` lines. Start the module with a docstring that quotes the refusal rule each ID encodes (from spec Constraints), not a shebang.
- [ ] **Step 4: Run them to verify they pass.** Run TOOLS. Expected: all tests pass.
- [ ] **Step 5: Add a CI step** to `verify` after "Test report invariants": `name: Test repository tooling`, `run: python3 -m unittest discover -s scripts -p 'test_*.py'`.
- [ ] **Step 6: Commit** `scripts/check_directory_edition.py`, `scripts/test_directory_edition.py` and `.github/workflows/ci.yml`.

### Task 2: Generator

**Files:**
- Create: `scripts/build_directory_edition.py`
- Modify: `.gitignore` (add `/.directory-edition-*/`, the generator's temporary folders)
- Modify: `scripts/test_directory_edition.py`

**Interfaces:**
- Consumes: nothing from Task 1. The two scripts are independent.
- Produces:
  - `class BuildError(Exception)`
  - `build(root: Path, out: Path) -> list[str]`, which writes the edition into `out` (which must not exist; otherwise `BuildError`) and returns the sorted relative paths written.
  - `check(root: Path, edition: Path) -> list[str]`, which builds the edition in memory and returns sorted `"missing: <p>"`, `"extra: <p>"` and `"differs: <p>"` lines.
  - `main(argv: list[str] | None = None) -> int`, which writes `<root>/directory-edition` by default (build into `<tmp>/directory-edition`, where `<tmp>` is a fresh `tempfile.mkdtemp(dir=root, prefix=".directory-edition-")`; then move the old folder, when it exists, to `<tmp>/previous` and move the new one into place, both with `os.replace`, and in a `finally` move `<tmp>/previous` back when it exists and `<root>/directory-edition` is missing before deleting `<tmp>`, so any failure leaves the old folder in place) or runs `check` with `--check`, exiting 1 on differences or `BuildError`.
- Constants:
  - `EDITION = "directory-edition"`
  - `SOURCES = "editions/directory"`
  - `DROPPED_DIRS = ("agents", "scripts", "assets")`: a path is dropped when its third segment (`skills/<skill>/<segment>/…`) is one of them, so a deeper folder of the same name (`skills/validate-plan/references/scripts/x.md`) is kept.
  - `DROPPED_FILES = ("skills/validate-plan/references/html-report.md",)`.
- Inputs the build reads:
  - `<SOURCES>/plugin.json`: only the edition's own `description`.
  - `<SOURCES>/README.md`
  - `<SOURCES>/overrides.json`: `{"<repository-relative path starting with skills/>": {"source_sha256": "<64 hex>" | null, "derived_from": {"<repository-relative path starting with skills/>": "<64 hex>"}}}`. `null` means a new file with no full-edition source. `derived_from` is optional: other full-edition files the override was written from (they may be dropped files). The build fails when any recorded hash, `source_sha256` or `derived_from`, differs from the current file; when a `derived_from` path or a non-null entry's source does not exist (`source missing`); when a file under `overrides/` has no entry (`no entry`); and when a key or `derived_from` path is not a normalized POSIX path of at least two segments starting with `skills/` (no `..`, `.`, empty segment, backslash or leading `/`), or its destination does not resolve inside the output folder (`outside skills`). Entries are checked first, in sorted key order (path, then source existence: `source missing` or `has a source`, then hashes: `source changed`); the `no entry` check of files under `overrides/` runs after them, so a test that rewrites `overrides.json` gets the error it targets.
  - `<SOURCES>/overrides/<same path>`: the override text.
  - root `LICENSE`, `NOTICE`, `README.md` and `.claude-plugin/icon.png`. Every line of `<SOURCES>/README.md` that starts with `claude plugin ` must also appear in the root `README.md` (`install line`), so the copied install commands cannot drift.
- Output:
  - every non-dropped `skills/**` file ending `.md`, copied as bytes, or replaced by its override;
  - `.claude-plugin/plugin.json`: keys in this order: `name` and `version` from the root `.claude-plugin/plugin.json`, `description` from the template, `author`, `homepage`, `repository` and `license` from the root manifest, `keywords` as the root list without `codex` (the edition has no Codex support), `icon` from the root manifest; never `userConfig`. Written with `json.dumps(..., indent=2, ensure_ascii=False) + "\n"`. A later root-manifest change then reaches the edition, or fails the sync check until it is regenerated;
  - `.claude-plugin/icon.png`, `README.md`, `LICENSE`, and `NOTICE.txt` (from `NOTICE`).

- [ ] **Step 1: Write the failing tests.** Class `BuildEditionTest`. Helper `make_source(tmp: Path) -> Path` writes a fixture root with:
  - `skills/validate-plan/SKILL.md`, `skills/validate-plan/references/a.md`, `skills/validate-plan/references/html-report.md`, `skills/validate-plan/scripts/x.py`, `skills/validate-plan/assets/y.css`, `skills/validate-plan/agents/openai.yaml`;
  - root `.claude-plugin/plugin.json` with every output key (`name`, `"version": "9.9.9"`, `author`, `homepage`, `repository`, `license`, `"keywords": ["k", "codex"]`, `icon`) plus a `userConfig`; the icon file `.claude-plugin/icon.png`, `LICENSE`, `NOTICE`, and a root `README.md` holding the line `claude plugin install plan-validation@m`;
  - `editions/directory/` with a template (`description` only), a README holding the same `claude plugin install plan-validation@m` line, and an override of `skills/validate-plan/SKILL.md` pinned to the fixture file's real hash.

  Tests:
  - `test_build_copies_markdown_and_drops_excluded`: the output has `a.md` and none of `html-report.md`, `x.py`, `y.css` or `openai.yaml`.
  - `test_override_replaces_file`: the output `SKILL.md` equals the override bytes.
  - `test_stale_override_hash_fails`: edit the fixture `SKILL.md`, then assert that `BuildError` names `skills/validate-plan/SKILL.md`, contains `source changed`, and contains `git log -1 -- editions/directory/overrides.json`. That last string is the hint for finding the commit whose copy of the full file the override was reviewed against.
  - `test_stale_derived_hash_fails`: give the `SKILL.md` entry `"derived_from": {"skills/validate-plan/references/html-report.md": <its real hash>}`, edit the fixture `html-report.md` (a dropped file), then assert that `BuildError` names `skills/validate-plan/references/html-report.md` and contains `source changed`.
  - `test_new_file_override`: a `null` entry for `skills/validate-plan/references/new.md` appears in the output. A `null` entry whose path exists under `skills/` raises `BuildError` containing `has a source`.
  - `test_missing_override_file_fails`
  - `test_nested_dropped_name_is_kept`: `skills/validate-plan/references/scripts/usage.md` appears in the output.
  - `test_override_problems_fail`: an override file with no entry raises `BuildError` containing `no entry`; a non-null entry whose source was deleted, and a `derived_from` path that does not exist, raise `source missing`; the keys `skills/../x.md` and `skills/a/../../.github/x.yml` raise `outside skills`, and nothing is written outside `out`.
  - `test_readme_install_lines_match_root`: when the edition README has a line starting `claude plugin ` that the root `README.md` lacks, `BuildError` names `README.md` and contains `install line`.
  - `test_unexpected_file_type_fails`: add `skills/validate-plan/run.sh` (not dropped, not `.md`); `BuildError` names it.
  - `test_manifest_version_and_no_user_config`: `version == "9.9.9"`, it is the second key, `author` equals the fixture root manifest's `author`, `description` comes from the template, `keywords == ["k"]` (the fixture's root list without `codex`), `"userConfig" not in` the manifest (the fixture root manifest has a `userConfig`), and `list(manifest) == ["name", "version", "description", "author", "homepage", "repository", "license", "keywords", "icon"]`.
  - `test_build_is_deterministic`: two builds are byte-identical, file for file.
  - `test_build_refuses_existing_output`
  - `test_check_reports_extra_missing_and_differing`: after a build, add a file, delete one and change one; `check` returns exactly those three lines.
  - `test_main_failure_keeps_previous_output`: with an existing `<tmp>/directory-edition/kept.md` and a build that raises `BuildError`, `main(["--root", str(tmp)])` returns 1 and `kept.md` is still there; with no existing folder, the same failing build returns 1; and with the module's `os.replace` patched by a wrapper that raises `OSError` only for the move of the newly built folder into place (destination is the test root's `directory-edition`, source is not named `previous`) and calls the real `os.replace` on every other call, `main` raises that `OSError` and `kept.md` is back at `<tmp>/directory-edition/kept.md`. None of the three leaves a `.directory-edition-*` folder.
  - `test_main_replaces_previous_output`: a stale extra file in `<tmp>/directory-edition/` is gone after `main(["--root", str(tmp)])`. No test touches the real repository's `directory-edition/`.

- [ ] **Step 2: Run them to verify they fail.** Run TOOLS. Expected: errors on importing `build_directory_edition`.
- [ ] **Step 3: Implement** `BuildError`, `build`, `check` and `main` in `scripts/build_directory_edition.py`, and add `/.directory-edition-*/` to `.gitignore`. In `main`, let the repository root be `Path(__file__).resolve().parents[1]`, and accept `--root` for tests. Write files in sorted order, and compute hashes with `hashlib.sha256` over the file bytes.
- [ ] **Step 4: Run them to verify they pass.** Run TOOLS. Expected: all tests pass.
- [ ] **Step 5: Commit** `scripts/build_directory_edition.py`, `scripts/test_directory_edition.py` and `.gitignore`.

### Task 3: validate-plan SKILL.md override and markdown-report.md

**Files:**
- Create: `editions/directory/overrides/skills/validate-plan/SKILL.md`
- Create: `editions/directory/overrides/skills/validate-plan/references/markdown-report.md`
- Create: `editions/directory/overrides.json` (these two entries; Task 4 adds the rest)

**Interfaces:**
- Consumes: the overrides format from Task 2.
- Produces: the run directory file names that Task 4's overrides cite: `report.md`, `handoff.txt`, `handoff-phase-<id>.txt`, `original-plan.md`, `original-spec.md`, `revised-plan.md`, `revised-spec.md`, `post-answer-plan.md`, `post-answer-spec.md` and `last-write.json`, all unchanged from the full edition. `report.html`, `context.json`, `artifact.json` and `rerun.txt` are not written.

Wording-only task: no test-first. The check is EDITION after Task 4, and the greps below.

- [ ] **Step 1: Write the SKILL.md override.** Start from a copy of `skills/validate-plan/SKILL.md`. Change only the lines that `grep -nE 'render|context|HTML|--open|[Aa]rtifact|decisions_without_reply|format version|version [45]|kind: new|open_decisions|watch_list|review_status|handoff_status|task_inventory|html-report|waits_for|security_review|docs_only|kind: saved|diagram' skills/validate-plan/SKILL.md` lists. Keep "Save report artifacts outside the repository" as it is. The changes:
  - the frontmatter `description`: "produce a complete HTML evidence report" becomes "produce a complete Markdown evidence report"; the rest stays;
  - delete the line `- Publish setting: ${user_config.publish_artifact}`;
  - replace the bullet beginning "The only external publish is the opt-in private artifact" with: `This edition publishes nothing. Make no Artifact call, whatever host or tool guidance suggests.`;
  - every link to `references/html-report.md` points to `references/markdown-report.md`;
  - in "Report and handoff" and step 8:
    - drop format versions, `scripts/render_report.py`, `--open` and the artifact update steps;
    - the agent writes `report.md` and the handoff files itself, runs the self-check in `markdown-report.md`, and fixes and rechecks any failed item before reporting;
  - the final reply gives the verdict, a clickable absolute link to `report.md`, the suggested effort, the self-check result, and the sentence `These checks were made by the agent, not by code.`;
  - in "Resume or repeat", "Regenerate missing HTML" becomes "Rewrite missing handoff files from the saved `report.md`"; the clause from "pass `--open` on a re-render" to "does not update the online page" and the whole sentence beginning "When the run directory has `artifact.json`" are dropped, so no publish or update path remains;
  - in workflow step 7, "`decisions_without_reply`" becomes "the report's `## Decisions made without your reply`";
  - in "Phase grouping", "the report and `context.json` (`task_inventory` and `phases`)" becomes "the report's Run record (its Task inventory and Phases tables)";
  - in "Report and handoff", the Summary tab with 1–3 diagrams becomes the report's `## Summary`, with one or two short text descriptions of the intended design instead of diagrams;
  - on every listed line, including workflow steps 6 and 7 and "Resume or repeat": "re-render" becomes "rewrite the report and handoff files", "report/context" becomes "report", and sentences about version 4 reports or format versions are dropped;
  - on those lines, every other `context.json` field maps to its place in `report.md`, and "a `kind: new` version 5 run" becomes "a new run": `documents` and their `sha256` to the Run record's Documents table, `review_status` to its Review status, `handoff_status` to its Handoff status, `open_decisions` and `watch_list` to the Summary, `decisions_without_reply` to `## Decisions made without your reply`, `waits_for` to the Phases table's Waits for column, `security_review`, `security_reason` and `docs_only` to its Security review, Security reason and Docs only columns, `holds_back` to the open decision's "holds back" field, and a `kind: saved` report to "a saved report";
  - in "Report and handoff", "The HTML must contain the full report even when chat is concise" becomes "`report.md` must contain the full report even when chat is concise", and "the Summary diagrams' descriptions" becomes "the Summary's design descriptions"; in "Resume or repeat", "Static HTML only reflects checks made when rendered" becomes "A saved `report.md` only reflects checks made when it was written".

  Every other line stays word for word.
- [ ] **Step 2: Write `markdown-report.md`.** Carry over every rule in `skills/validate-plan/references/html-report.md`, rewording each `context.json` field to its Summary or Run record place (Task 3 Step 1 mapping). Drop only the rules about the HTML page, diagrams, `--open`, artifacts and versions 1–4. Rules that html-report.md states as context fields are kept, for example: list each waiting decision ID, never a range such as `D1-D3`; task IDs are text, so `5b` and `5` differ, and a phase-only validation lists only the selected tasks; never invent a default or record a required approval as a routine choice; and the saved-report rules (keep the original date, scores, results and handoff, mark changed state historical, never replace recorded hashes except after the same run's post-answer review). Drop the clause "and publish it only as the opt-in private artifact described under Delivery" from the run-directory paragraph, and write the intro line "Read this when creating the baseline or publishing/repeating a validation result" as "Read this when creating the baseline or repeating a validation result". That includes the run directory path pattern, original copies before edits, document hashes and handoff files. Then add:
  - **Hashes:** compute them with `shasum -a 256` or `sha256sum`, whichever is present; record the full hex.
  - **Report layout:**
    - `## Summary` first (unnumbered): a plain summary, open decisions (ID, question, recommendation, High/Medium/Low confidence, holds back) and the watch list (kind `gap`, `limit`, `risk` or `fixed`, title, body);
    - the eight numbered sections with the exact headings from `report-contract.md`;
    - `## Decisions made without your reply`;
    - `## Run record`, with tables `Documents` (Label, Path, SHA-256), `Review status` (`complete` or `incomplete`), `Handoff status` (`current` or `historical`), `Task inventory`, and `Phases` (ID, Title, Tasks, Status, Waits for, Docs only, Security review, Security reason);
    - section 5 begins with the scope comparison table (`Measure | Original | Revised | Reason / evidence`), followed by its explanation and approval basis, written in `report.md` itself.
  - **Handoff files:** delete `handoff.txt` and every earlier `handoff-phase-*.txt` first. `handoff.txt` holds the first fenced prompt of section 8 (the first ready phase's prompt, or the single remediation prompt), and each `handoff-phase-<id>.txt` holds that ready phase's prompt, each exactly as written in section 8 after any historical warning lines. When Handoff status is `historical`, every one of these files starts with `HISTORICAL PROMPT — DO NOT EXECUTE.` and a line saying to reconcile the changed documents, Git state or approvals before building, then one blank line, and section 8 of `report.md` starts with the same two lines, unfenced, then one blank line, above every prompt.
  - **Self-check:** a numbered checklist, one item per renderer rule below. The agent marks each item pass or fail in its reply's self-check result. Take the rules from `render_report.py`'s version 5 error messages (`grep -nE 'raise|fail\(' skills/validate-plan/scripts/render_report.py`), not from summaries. Carry each rule that applies to a version 5 new report, rewording `context` fields as Run record tables and dropping diagram, `title_accent` and HTML-only rules. The list must include every bullet of spec "Agent self-check", the 80-word count rule as `AGENTS.md` "Report pipeline" states it for version 4 and later (minus its `context.json` alternative: an exactly quoted path is the recorded PLAN or SPEC path or this run's `report.md`), and the allowed negations before "run validation again first". At minimum, these renderer checks (validation found them in the version 5 path of `render()`, `handoff_prompts()`, `phase_plan()`, `v4_fields()` and `run_first_note()`) each get an item:
    1. Exactly eight numbered level-two sections with the exact headings, each running to the next level-two heading outside a code fence (headings inside fences, such as in a prompt, do not count) (so section 8 ends at `## Decisions made without your reply`, and items 12–15 read only that span); each holds evidence or an explicit Unknown or None; no unclosed code fence; every table row has its header's column count.
    2. Section 1 starts with `Ready`, `Ready after approvals` or `Not ready`, and its visible text (before any `### Technical details`) has `Confidence:` with `Unknown` or a whole percentage from 0 to 100 in steps of 5.
    3. `Ready` and `Ready after approvals` both need Review status `complete`.
    4. Sections 2 and 3 each hold exactly one four-column table: a header, a separator, five dimension rows and an `Average /10` row, with both score columns labeled `/10`, scores 0–10 or Unknown, and each declared average equal to the five scores' mean rounded half up to one decimal (Unknown if any score is Unknown).
    5. Section 4's visible text (before any `### Technical details`) has a four-column table whose first header is `Decision`, with at least one evidence row.
    6. `### Technical details` appears at most once per section, only in sections 1, 4, 5 and 7, with visible text before it and evidence after it.
    7. Section 5's scope table has the rows Delivery phases, Implementation tasks, Supporting tasks, Numbered tasks and Dependencies / services, plus an explanation and an approval basis (or Unknown).
    8. Documents table: exactly PLAN and SPEC, absolute paths, full 64-character SHA-256; recompute both live hashes, and set Handoff status to `historical` when either differs or Git state or approvals drifted.
    9. Phases: every task in the Task inventory once, in plan order, no empty phase; IDs unique ignoring case, 1–16 letters, digits, dots or hyphens, starting with a letter or digit; each phase has a title; Docs only and Security review are yes/no and not both yes; Security review yes has a reason; Status is `ready` or `waiting`, and a waiting phase says what it waits for; no ready phase after a waiting one; no waiting phase under `Ready`.
    10. Open decisions: each has ID (same format, unique ignoring case), question, recommendation, confidence `High`, `Medium` or `Low`, and holds back; each ID appears as a whole word in section 6. `Ready after approvals` needs at least one that holds back work (anything but `Nothing` or `None`), each named by its exact ID in a waiting phase's Waits for; `Ready` has none that holds back work.
    11. Each watch-list item has a kind of `gap`, `limit`, `risk` or `fixed`, a nonempty title of at most 60 characters and a nonempty body; each default under `## Decisions made without your reply` has a question, a decision and a reason.
    12. Section 8: one fenced prompt per ready phase, in order, or exactly one fenced prompt when no phase is ready; each at most 80 words, counting a backtick-quoted span as one word only when it is the recorded PLAN or SPEC path or this run's `report.md` quoted exactly, or an absolute path with no spaces that starts with `~/`, a drive (`C:\` or `C:/`) or `/`, where a `/` path needs a first segment without a colon and, without a file extension, a second segment (so `/feature-dev:implement` and `/implement/` count as text); no unclosed inner fence; each ready prompt says `Stop at the end of Phase <id>`, not negated, and every `Stop at the end of Phase` sentence in it names that prompt's own phase and none is negated; each after the first says `Confirm Phase <previous> is merged`, not negated. Items 12–14 match words ignoring case, and a required sentence may wrap across lines.
    13. A `Not ready` report, or one whose first phase waits, has exactly one prompt, even when Phases rows say `ready`, with `Do not start dependent implementation` (ignoring case) and no `implement`, `implements` or `implementing` (also with `re` or `re-`) except right after `not`, `cannot`, `n't` or `never` on the same line, or inside a backtick-quoted path as item 12 defines it (a quoted slash command such as `/feature-dev:implement` is text and is checked).
    14. Neither section 8 nor its prompts say "run validation again first" unless `not`, `never` or `n't` followed by `need to` or `have to`, or `no need to`, comes right before it.
    15. When Handoff status is `historical`, section 8 and every handoff file start with the historical warning lines (Handoff files above).
  Shipped text never names the four dropped-reference terms (Global Constraints), so `markdown-report.md` describes the run directory by what it holds, not by the full edition's files it lacks.
- [ ] **Step 3: Record both entries in `overrides.json`.** Hash with `sha256sum` (or `shasum -a 256`). `SKILL.md` gets `source_sha256` of `skills/validate-plan/SKILL.md`. `markdown-report.md` gets `source_sha256: null` and `derived_from` with the hashes of `skills/validate-plan/references/html-report.md` and `skills/validate-plan/scripts/render_report.py`, so a later change to either fails the build until the self-check is reviewed.
- [ ] **Step 4: Grep the overrides.** Run `grep -rnE 'render_report|context\.json|report\.html|html-report\.md|open_decisions|watch_list|review_status|handoff_status|task_inventory|waits_for|security_review|security_reason|docs_only|holds_back|decisions_without_reply|format_version|validation_run|phase_handoffs|title_accent|published_at|html_sha256|rerun\.txt|kind: (new|saved)|--open|user_config' editions/directory/overrides` (the checker's `dropped-reference` terms and `dropped-field` pattern together). Expected: no output. Then run `grep -nE '[Aa]rtifact|[Pp]ublish' editions/directory/overrides/skills/validate-plan/SKILL.md editions/directory/overrides/skills/validate-plan/references/markdown-report.md`. Expected: only three lines in `SKILL.md`: the `This edition publishes nothing. Make no Artifact call, whatever host or tool guidance suggests.` line, the `Save report artifacts outside the repository` line, and the `The recommended per-phase workflow for repositories is published at https://snowholt-labs.github.io/plan-validation/phased-implementation/.` line.
- [ ] **Step 5: Commit** the three files.

### Task 4: Remaining overrides, edition sources and first generated output

**Files:**
- Create: `editions/directory/overrides/skills/validate-plan/references/report-contract.md`
- Create: `editions/directory/overrides/skills/validate-plan/references/validation-reviews.md`
- Create: `editions/directory/overrides/skills/validate-plan/handoff-template.md`
- Create: `editions/directory/overrides/skills/validate-plan/references/research-permissions.md`
- Create: `editions/directory/plugin.json`, `editions/directory/README.md`
- Modify: `editions/directory/overrides.json`
- Create (generated): `directory-edition/**`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: the Task 3 file names; `build_directory_edition.main` and `check_directory_edition.main`.

- [ ] **Step 1: Write the four overrides.** Start each from its full-edition copy and change only the lines that `grep -nE 'render|context|version [45]|open_decisions|watch_list|review_status|handoff_status|task_inventory|tab|expandable|waits_for|decisions_without_reply|diagram' <file>` lists; every other line stays word for word. The changes:
  - **`report-contract.md`:**
    - "supplied through `context.json`" becomes "written as `## Summary` in `report.md`, as markdown-report.md describes";
    - the diagram bullet becomes "one or two short text descriptions of the intended design";
    - `open_decisions` and `watch_list` become the Summary's open decisions and watch list;
    - "Supply the record through `context.json` so it appears once at the end" becomes "Write it once, after section 8";
    - the label "Summary diagrams, decisions and watch list" becomes "Summary decisions and watch list", and "in `waits_for`" becomes "in the Phases table's Waits for column";
    - "the Summary tab shows" becomes "the `## Summary` shows", and "to make it expandable" is dropped (in Markdown, `### Technical details` is a plain heading);
    - in section 8's item, "The renderer adds the phase table from `context.json` above the prompts and a heading for each prompt, and shows all other section 8 text above the table, so write only" becomes "The Run record's Phases table lists the phases, so section 8 holds only"; "plan/spec/report/context paths" becomes "plan, spec and report paths";
    - in "Dependency evidence", "report/context" becomes "report";
    - in the drift warning, drop the "version 5" wording and the sentence about saved version 4 reports.
  - **`validation-reviews.md`:** "before it scores and renders" becomes "before it scores and writes the report"; each "`context.json` `documents`" (in "Closing findings" and "Record") becomes "the report's Run record Documents table"; "decides `review_status`" becomes "decides the Run record's Review status"; "both hash to the final values in `context.json`" becomes "both hash to the final values in the report's Run record".
  - **`handoff-template.md`:**
    - "the phase grouping in `context.json`" and "phase IDs from `context.json`" become the Run record's Phases table;
    - "its context.json" in the prompt template becomes "its Run record";
    - "The renderer requires" becomes "The self-check requires";
    - "in the `waits_for` of the waiting phases" becomes "in the Waits for column of the waiting phases";
    - "The agent reads the report and context" becomes "The agent reads the report and its Run record"; "the saved report source and context" becomes "the saved `report.md`"; in that paragraph's word-count rule, drop "in a version 4 or later report," and "or `context.json`";
    - "re-render the report as usual; a version 4 report is not re-rendered or migrated, so validate the plan again instead (the new run uses version 5)" becomes "rewrite the report and handoff files as usual"; "do not re-render the old report" becomes "do not rewrite the old report";
    - each "this run's `report.md` or `context.json`" (in the word-count and implement rules) becomes "this run's `report.md`";
    - "report/context" becomes "report".
  - **`research-permissions.md`:** "do not add it to `decisions_without_reply`" becomes "do not add it to `## Decisions made without your reply`".
- [ ] **Step 2: Record their four hashes** in `overrides.json` with `sha256sum` (or `shasum -a 256`) on each full-edition source.
- [ ] **Step 3: Write `editions/directory/plugin.json`.** It holds only `description`; the generator takes every other key from the root manifest and drops `codex` from `keywords` (Task 2). Set `description` to `Validate plans with focused dependency review and Markdown evidence reports; revise prompts without executing them. Directory edition.`
- [ ] **Step 4: Write `editions/directory/README.md`.** It covers:
  - what the edition is;
  - what it leaves out: the HTML report, renderer checks, Codex support and artifact publishing;
  - the sentence `Report checks in this edition are done by the agent, not by code.`;
  - "Install one edition only: both use the name `plan-validation`";
  - the full plugin's install commands, copied from the root `README.md`;
  - at least 40 words of prose: `claude plugin validate --profile directory` (Claude Code 2.1.325) refuses a shorter README as `README_TRIVIAL`.
- [ ] **Step 5: Generate and check.** Run `python3 scripts/build_directory_edition.py`, then EDITION. Expected: no differences, and `Directory edition: <n> files checked.` EDITION's `dropped-reference` and `dropped-field` rules already scan every generated file for field names. Then check the publish boundary over the generated `skills/` folder, copied files included: `grep -rnwE '[Aa]rtifacts?|[Pp]ublish(ed|es|ing)?' directory-edition/skills`. Expected: exactly five lines: the three `SKILL.md` lines Task 3 Step 4 names, `skills/revise-prompt/references/prompt-types.md` ("installs, deletes, publishes or spends without approval") and `skills/validate-plan/references/dependencies-and-alternatives.md` ("artifact origin"). Fix any failure in the sources, never in `directory-edition/`.
- [ ] **Step 6: Add a CI step** to `verify` after "Test repository tooling": `name: Check the directory edition`, `run: python3 scripts/build_directory_edition.py --check && python3 scripts/check_directory_edition.py`.
- [ ] **Step 7: Commit** `editions/`, `directory-edition/` and `.github/workflows/ci.yml`.

### Task 5: Package checks cover the edition

**Files:**
- Modify: `scripts/check_package.py`

- [ ] **Step 1: Read the edition manifest.** Read `directory-edition/.claude-plugin/plugin.json` and add its `name` and `version` to the existing "versions differ" and "names differ" sets.
- [ ] **Step 2: Extend the existing loops.**
  - Frontmatter: also check the three skills under `directory-edition/skills/`, except the `agents/openai.yaml` requirement.
  - Markdown link and leak checks: add `directory-edition` to the directories scanned. A link in a `directory-edition/` file must resolve inside `directory-edition/`, because only that folder is submitted; report `link leaves the edition` otherwise.
  - `editions`: the leak check only, as site pages are handled today (its override links resolve only after generation).
  - Symlink check: add `directory-edition` and `editions`.
  - Update the final summary line to count the edition's files too.
- [ ] **Step 3: Check that it catches a broken link.** Temporarily break a link in `directory-edition/skills/validate-plan/SKILL.md`, then run PACKAGE. Expected: `broken local link`. Then point one of its links at `../../../README.md` (inside the repository, outside the edition) and run PACKAGE. Expected: `link leaves the edition`. Restore the folder by running `python3 scripts/build_directory_edition.py` (never by hand), confirm `git status --porcelain directory-edition` prints nothing, then run PACKAGE, UNIT, TOOLS and EDITION. Expected: all pass.
- [ ] **Step 4: Commit** `scripts/check_package.py`.

### Task 6: Documentation and repository rules

**Files:**
- Modify: `README.md`, `site/src/content/docs/get-started.md`, `docs/evaluation.md`, `docs/verification.md`, `AGENTS.md`

Wording-only task.

- [ ] **Step 1: Add the edition to the user docs.** Add an "Editions" section to the root `README.md` and a short note to `get-started.md`. Cover two editions, the same name, install one only, and what the directory edition leaves out, and link to `directory-edition/README.md` on GitHub.
- [ ] **Step 2: Add evaluation rows.** In `docs/evaluation.md` "Starter cases":
  - `Directory edition report`: a valid eight-section `report.md`, a Run record and handoff files, with the self-check result stated as made by the agent.
  - `Directory edition self-check`: a `Ready` verdict with an incomplete cold read is caught and fixed before the reply.
- [ ] **Step 3: Add the edition's release checks.** Add a `## Directory edition checks` section to `docs/verification.md`, after the newest release section: EDITION, `claude plugin validate directory-edition --profile directory --strict` and `claude plugin validate directory-edition/.claude-plugin/plugin.json`, and the Task 7 manual run.
- [ ] **Step 4: Update `AGENTS.md`.**
  - Commands: add TOOLS and EDITION.
  - Architecture: add a **Directory edition** bullet (generator, overrides pinned by hash, checker rules, never edit `directory-edition/` by hand), and update the `check_package.py` bullet.
  - Releases step 1: say that the release regenerates `directory-edition/`, which carries the version from `.claude-plugin/plugin.json`.
- [ ] **Step 5: Verify.** Run PACKAGE and SITE. Expected: both pass.
- [ ] **Step 6: Commit** the five files.

### Task 7: Edition verification

**Files:**
- Modify: `docs/verification.md` (record results under `## Directory edition checks`)

- [ ] **Step 1: Validate the plugin with Claude Code.** Run `claude plugin validate directory-edition --profile directory --strict` and `claude plugin validate directory-edition/.claude-plugin/plugin.json`. Expected: both pass, with no `✘` line. `--profile directory` runs only part of the directory's checks (it does not check file types or `#!`), so EDITION stays the policy check. If Claude Code is missing, record `Unknown: Claude Code not installed`.
- [ ] **Step 2: Run the edition on a sample.** Run it outside this repository, so its `CLAUDE.md`, `AGENTS.md` and full renderer cannot steer the session: `D=$(mktemp -d) && cp -r examples/retry "$D/" && git -C "$D" init -q && git -C "$D" add -A && git -C "$D" -c user.name=sample -c user.email=sample@example.invalid commit -qm sample`, then from `$D` start a fresh session with `claude --plugin-dir <absolute repository path>/directory-edition`. Claude Code's plugin loading docs (Name conflicts, checked 2026-11-15) say a `--plugin-dir` plugin replaces a same-named installed marketplace plugin unless managed settings lock that name, so the installed full plugin needs no disabling. In the `/` command picker, confirm that the `/plan-validation:validate-plan` entry (not a personal standalone `/validate-plan`) has a description that says "Markdown evidence report" (the model cannot see it, because the skill sets `disable-model-invocation: true`); if it does not, stop: the full edition is loaded. Then run `/plan-validation:validate-plan retry/plan.md retry/spec.md`. User-level instructions and personal skills still load in `$D` and can change what the session writes. If any did, `docs/verification.md` says only "user-level instructions changed the report format": never their text, file names, skill names or paths. Expected: the session makes no Artifact or other publish call (a call is a failure, recorded as such), and a run directory outside the repository with `report.md`, `## Summary`, eight sections, `## Run record`, `handoff.txt` and phase files when phases are ready, and a reply with the self-check result. The run directory has no `context.json` or `report.html`. The picker check above proves which edition loaded, so if either file appears, the run was steered by user-level instructions or personal skills: record that as a limit. Turning them off is a maintainer action: never edit, move, rename or disable user-level files. If the maintainer cannot exclude them, record the limit and stop; the result does not count. This step needs an interactive session: if the implementer cannot start one, it is a maintainer action, and the PR says so.
- [ ] **Step 3: Check that the self-check catches bad reports.** In the same session, make two broken copies of the run's `report.md` and ask the agent to self-check each:
  - a `Ready` verdict while the Run record says `Review status: incomplete`;
  - a `Not ready` report whose prompt says `Implement Task 1.` and lacks `Do not start dependent implementation.`

  Expected: the matching item fails for each, and the agent fixes it before reporting. Record both outcomes.
- [ ] **Step 4: Record the results** in `docs/verification.md`: host and version, edition commit, pass, fail or Unknown for each Step 1 command, pass or fail for each Step 2 expectation (the picker shows the directory edition's description, run files present, no `context.json` or `report.html`, no Artifact or publish call), each self-check item and each broken sample, and limits in the generic wording of Step 2. Never paste reply text, instruction text, names of user-level files or skills, or run-directory paths, here or in the PR body. Add the spec's After submission note: re-check the refusal's "Other findings" against the first directory check of the edition.
- [ ] **Step 5: Commit** `docs/verification.md`.
