# Directory edition design

Date: 2026-11-15
Status: draft for maintainer review

## Intent

Anthropic's plugin directory refused plan-validation v0.7.0 (commit `7c1dc68`) through an automatic policy check. Organizations that Anthropic has not verified may ship only Markdown, text, JSON, YAML and PNG, JPEG, GIF, WebP or ICO images. A file may not start with `#!`, and a manifest field may not fall outside the allowed lists. The full plugin depends on a Python renderer, inline JavaScript and CSS, and SVG assets, so it cannot pass. No rearrangement of files fixes that.

The goal is discovery. The directory edition is a way in for people browsing the directory. The full plugin stays on this repository's own marketplace and remains the recommended install. A smaller edition is acceptable.

## Goals

- A directory edition in its own subfolder that passes every rule in the refusal text.
- Generated from the full plugin's skill sources, so the two editions cannot drift apart unnoticed.
- `revise-prompt` and `validation-args` ship with the same behavior as the full plugin.
- `validate-plan` keeps the full validation workflow and the eight-section report contract, and writes the report as Markdown.
- The edition's README states plainly that its report checks are done by the agent, not by code, and points to the full plugin.

## Non-goals

- Changing the full plugin's behavior, renderer, report format versions or frozen outputs.
- A Codex build of the directory edition. The directory is for Claude Code only.
- An HTML report, written by the agent or otherwise, in the directory edition.
- Becoming a Verified organization.

## Anti-goals

- A directory edition that is weaker on safety than its README admits. A `Ready` verdict without completed reviews, or a `Not ready` handoff that tells the next session to implement, is a failure even if the listing is accepted.
- A second copy of the skill text that someone has to keep in sync by hand.
- Any change that makes the full edition's install or behavior worse.

## Constraints

- The refusal text is the primary source for the policy. The list below restates its rules; the plan's checker task maps each one to a named check and a test. A generated edition must pass:
  - only allowed file types (judged by content, not name);
  - no file starting with `#!`;
  - UTF-8 with no NUL bytes;
  - no package manager configuration and no `package.json`;
  - no `.claude/skills` folder;
  - `.claude-plugin/` holds only `plugin.json` and the icon image;
  - only manifest and frontmatter fields that Claude Code reads.
- Claude Code's documented `plugin.json` fields (manifest reference at code.claude.com, checked 2026-11-15) cover every field the edition uses. The directory also reads `icon` for the listing.
- The repository is public. No private paths, rule files or session details go into the edition or this spec.
- Skill text is behavioral contract. Changes to it are checked against `docs/evaluation.md`.
- Standard library Python only for the repository tooling (generator, checker, tests). This tooling lives outside the submitted folder.

## Approaches

| Approach | Trade-off | Decision |
|---|---|---|
| A. Generated subfolder: a script builds the edition from `skills/`, swapping renderer-dependent files for Markdown-report versions, and CI fails if the committed output is out of date | One source of truth; needs a generator, a checker and a sync check | **Chosen by the maintainer** |
| B. Hand-copied subfolder | Fastest start; two copies drift | Rejected: drift is an anti-goal |
| C. Separate repository | Cleanest submission; most upkeep, and drift across repositories | Rejected: highest maintenance |

## Design

### Layout

- `editions/directory/` holds the edition's own sources: the plugin manifest, README, overrides and the override record. (The plugin name is settled; see Open questions.)
- `directory-edition/` is the generated output, committed, and is the folder submitted to the directory. Its contents are `.claude-plugin/plugin.json`, `.claude-plugin/icon.png`, `README.md`, `LICENSE`, `NOTICE.txt` (the root `NOTICE`, which the Apache-2.0 license asks redistributions to carry), and `skills/` with the three skills.
- `scripts/build_directory_edition.py` generates the output. `scripts/check_directory_edition.py` checks it against the policy. Neither ships in the edition.

### What the generator does

1. Copies every file under `skills/` that is Markdown and that no rule excludes.
2. Drops what the directory edition does not use: `scripts/`, `assets/`, every `agents/openai.yaml` (Codex metadata) and `references/html-report.md`.
3. Replaces each overridden file with its version from `editions/directory/overrides/`. Overrides replace whole files (my call). Markers inside the full skill text were rejected because they would put extra HTML comments into the full skill's model context.
4. Records, for each override, the SHA-256 of the full-edition file it replaces, and of any other full-edition file it was written from (for `markdown-report.md`: `html-report.md` and `render_report.py`, whose checks the self-check restates). The generator fails when any of these sources changes without its override being reviewed and its recorded hash updated. That makes drift a CI failure instead of a silent gap.
5. Writes the manifest with the name, version, author, homepage, repository, license, keywords (without `codex`) and icon read from `.claude-plugin/plugin.json`, the description from `editions/directory/`, and no `userConfig`.
6. Rewrites or rejects relative links that point at dropped files, so the link check passes.

The output is deterministic: running the generator twice gives byte-identical files.

### Overrides

The files that reference the renderer or `context.json` today are `skills/validate-plan/SKILL.md`, `references/html-report.md`, `references/report-contract.md`, `references/validation-reviews.md` and `handoff-template.md`; `references/research-permissions.md` names one `context.json` field. Each gets an override, or the generator drops it where nothing else needs it:

- **`SKILL.md`** is the same workflow, with these changes:
  - no `Publish setting` line and no Artifact publishing;
  - writes the report as Markdown instead of rendering it;
  - runs the self-check below;
  - links to the saved `report.md`.
- **`references/markdown-report.md`** (new; replaces `html-report.md`) covers:
  - the run directory and file names: `report.md`, `handoff.txt`, and one `handoff-phase-<id>.txt` per ready phase, outside the repository as today;
  - how to record document hashes with `shasum -a 256` or `sha256sum`, whichever is present;
  - the self-check list.
- **`report-contract.md`** and **`handoff-template.md`**: the same contract, minus renderer and `context.json` references.
- **`references/research-permissions.md`**: the same rules; its one `context.json` field name (`decisions_without_reply`) becomes the report's `## Decisions made without your reply`.
- **`references/validation-reviews.md`**: the same rules. "Reuse on the docs PR" keeps working, but it compares the plan and spec with the final hashes in the report's run record, not with `context.json`.

### Report data without `context.json` (builder's question, settled as my call)

The edition writes no sidecar file. Everything `context.json` holds today goes into `report.md`, so the agent checks one file:

- **Above the eight sections:** an unnumbered `## Summary`. It holds a plain-language summary of the feature, the open decisions (ID, question, recommendation, High/Medium/Low confidence, what it holds back) and the watch list. The diagrams become one or two short text descriptions; no images are drawn.
- **After section 8:** the unnumbered `## Decisions made without your reply`, as today.
- **Last:** an unnumbered `## Run record` with fixed tables:
  - documents: label, absolute path and full SHA-256;
  - review status (`complete` or not);
  - handoff status (`current` or `historical`);
  - the task inventory;
  - one phase row per phase: ID, title, tasks, status, what it waits for, docs-only, security review and its reason.

The eight numbered sections and their exact headings do not change. The self-check reads the run record for phase and review checks.

### Agent self-check

The renderer's validators become an explicit checklist that the agent runs before it reports. A failed item is fixed and rechecked, never reported as passed. The plan takes the list from `render_report.py`'s actual version 5 checks, not from summaries. At minimum it covers:

- **Verdict:**
  - section 1 starts with `Ready`, `Ready after approvals` or `Not ready`;
  - `Ready` or `Ready after approvals` only after the cold read is complete and its findings are dispositioned;
  - no open decision holds work back under `Ready`; under `Ready after approvals`, at least one does, and a waiting phase names each such decision ID.
- **Confidence and scores:**
  - confidence is `Unknown` or a multiple of 5%;
  - scores are 0–10 or Unknown, and the declared average matches the five dimension scores.
- **Structure:**
  - exactly eight numbered level-two sections with the exact headings;
  - every section holds evidence or an explicit Unknown or None;
  - no unclosed code fence.
- **Handoff:**
  - one fenced prompt per ready phase, or exactly one when no phase is ready, each of at most 80 words, counted as the renderer counts (a backtick-quoted path without spaces counts as one word);
  - a `Not ready` handoff, or one whose first phase waits, has no implement instruction and contains `Do not start dependent implementation`;
  - no "run validation again first" line, except right after the renderer's allowed negations (such as `do not need to`).
- **Phases:**
  - every task appears once, in plan order;
  - phase IDs are safe and unique;
  - flags are consistent, and waiting order holds;
  - one prompt per ready phase, which says `Stop at the end of Phase <id>` and, after the first, `Confirm Phase <previous> is merged`.

The final reply gives the verdict, a link to `report.md` and the self-check result. It says that the checks were made by the agent.

### Repository tooling and CI

- **`check_directory_edition.py`** encodes each rule in the refusal text as a separate, named check over `directory-edition/`, so a future refusal can be matched to a rule. It also rejects any mention of `render_report`, `context.json`, `report.html` or `html-report.md` in the output (my call), and, in the edition's skills, any `context.json` field name or renderer option (`open_decisions`, `waits_for`, `review_status`, `--open` and the like). That way an edit to a file copied unchanged cannot quietly ship a reference to a dropped part.
- **Submitting a subfolder:** the refusal text itself says to "put the plugin in a subfolder and submit that folder". The root's `site/package.json` and `marketplace.json` therefore stay out of the submission.
- **Sync check:** CI rebuilds the edition into a temporary folder and fails on any missing, extra or differing file (`build_directory_edition.py --check`), which covers what regenerating and running `git diff --exit-code directory-edition/` would, plus untracked extra files, without touching the committed folder.
- **`check_package.py`:**
  - scopes the full-edition-only checks (`agents/openai.yaml`, the `Publish setting` line, the publish gate sentence) to the full edition;
  - adds the edition manifest to the version-match check;
  - runs its other checks (links, leaked home paths, symlinks) over the edition too.
- **Tests** for the generator and checker live in `scripts/` and get their own CI step, since the current test step discovers only `skills/validate-plan/scripts`.
- **Releases:** the release checklist in `AGENTS.md` grows from three manifests to four (or the generator copies the version, and the release step regenerates). `docs/verification.md` gains the directory-edition checks.

### Documentation

- `directory-edition/README.md` covers:
  - what the edition is;
  - what it leaves out (the HTML report, renderer checks, Codex support, artifact publishing);
  - that its report checks are done by the agent;
  - how to install the full plugin from this repository's marketplace.
- A short "Editions" note in the documentation site's get-started page.

### Verification

- `claude plugin validate directory-edition --profile directory --strict` and `claude plugin validate directory-edition/.claude-plugin/plugin.json` pass, when Claude Code is installed. The directory profile runs part of the directory's own checks, such as the README length.
- The checker, sync check and existing CI pass.
- A manual run of the directory edition's `validate-plan` on a small sample plan produces a valid eight-section `report.md`, handoff files and a self-check result, recorded in `docs/verification.md`. Renderer tests do not stand in for this.
- A deliberately broken sample (a `Ready` verdict with an incomplete cold read) is caught by the self-check in that manual run.

### Left to the builder

- The exact override text, as long as it keeps the full workflow and the self-check above.
- The format of the override record (a JSON file beside the overrides is suggested).
- How links to dropped files are rewritten.
- The order of the plan's tasks.

## After submission

The refusal's "Other findings" (a value read from the machine, and a command the plugin runs) likely trace to the renderer's display-variable read and to documented commands, both absent from the edition. Re-check them against the first directory check of the edition rather than designing around guesses.

## Open questions

1. **Plugin name.** Decision: keep `plan-validation` (approved by the maintainer on 2026-11-15). The README tells users to install one edition only.
   - Keeping `plan-validation` leaves the skill text unchanged; `revise-prompt` and `validation-args` tell users to type `/plan-validation:<skill>`. It may also update the existing directory submission instead of starting a new one. The cost: someone who installs both editions gets clashing commands, and our own marketplace cannot list both.
   - A new name avoids the clash, but those two skills need text changes and the directory may treat it as a new submission.
