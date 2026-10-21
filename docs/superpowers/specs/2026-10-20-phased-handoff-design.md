# Phased implementation handoff design

Date: 2026-10-20. Status: draft for maintainer review.

## Intent

Today a validated plan is built in one long session. The handoff tells the implementing agent to "Implement all validated phases" and "Do not ask to continue between steps", so one session runs every task, review, PR and merge until the plan ends.

That session is where most of the cost goes. Across 16 plans that were validated and built in Claude Code, validation was about 24% of the API-equivalent cost and implementation about 76%. Inside an implementation session every message re-reads the whole conversation, so cost grows faster than the work:

- CI suite speedups (e2ba): the main context grew from 74k to 435k tokens over 352 messages, with 236 shell commands and 31 skill runs (including reviews) kept in that context. Claude Code reported $127 for the session.
- Mail-hub: the maintainer stopped the session by hand after Task 11, at 385k tokens of context.

Auto-compaction does not fix this: it keeps a summary of finished work that the next task does not need.

The change: the validator groups the plan's existing tasks into small phases, and each phase runs in its own fresh session that stops at the phase end and hands over the prompt for the next phase. The plan's tasks and structure stay exactly as written.

## Goals

1. **Phase grouping.** The validator groups the validated plan's tasks into implementation phases, each small enough for one fresh session. Target 3–5 tasks per phase. End each phase where the tests pass and the PR can be reviewed on its own.
2. **Plan file untouched by grouping.** The grouping lives only in the report and its context. The validator does not add, rename or reorder phase headings or tasks in the plan for this purpose. Its existing defect repairs inside tasks are unchanged.
3. **One phase per session.** Each handoff prompt names exactly one phase and tells the agent to stop at the end of that phase and print the next phase's prompt. The agent does not start the next phase.
4. **A ready prompt for every phase.** The report holds one copyable launch prompt per phase, so the next prompt is exact, not improvised.
5. **Recommended per-phase workflow for repositories.** The plugin documents a per-phase workflow that repositories can adopt in their own instructions (below). This change publishes it as a page on the documentation site (`site/src/content/docs/`).

## Recommended per-phase workflow

This is repository workflow, so it belongs in each repository's instructions (for example `AGENTS.md`), not in the universal launch prompt. The plugin publishes it as recommended text in the documentation. Decided with the maintainer on 2026-10-20:

1. A fresh session reads the plan, spec, report, context and the progress file.
2. Helper agents build the phase's tasks; the main session coordinates and keeps only short results.
3. A helper agent runs code review on the branch; the findings get fixed; repeat. **Stop by severity, not round count:** keep looping while a round finds bugs, security issues or failing tests; stop when a round finds only minor items (style, naming, nitpicks) and save those as action points for the final plan-branch review. **Safety limit: 5 rounds.** If real problems remain at round 5, stop, do not open the PR, and ask the maintainer.
4. A helper agent runs a security review only when the phase is flagged security-sensitive (auth, user input, secrets, dependencies, CI workflows). It reviews the branch, so it runs before the PR is opened.
5. Open the PR into the plan branch and wait for CI to pass. Because both reviews ran first, CI usually runs once per PR.
6. Post a short review summary as a PR comment (comments do not trigger CI in the repositories checked) and record action points in the progress file.
7. Stop. Print the next phase's prompt from the report. The maintainer merges the phase PR, then starts the next phase in a fresh session.

Other rules:

- **Docs-only PRs** (for example, plan or spec reference fixes): CI only, no code or security review.
- **Final plan-to-main PR:** a full code review and a full security review of the whole diff, which also clears the saved action points.
- A phase starts only after the previous phase is merged into the plan branch; the session confirms this first and stops if it is not.

## Validator and report changes

These are the plugin changes.

- **Phase grouping rules.** Every task in the validated scope appears in exactly one phase, in plan order; no task is split or moved. Phases never cross a boundary the plan already defines, because in these repositories a plan phase is also a PR boundary. If the plan's own phase or part is larger than about 5 tasks, it is split into consecutive sub-phases; small plan phases stay as they are, even with one task. A plan with no phases of its own and 5 or fewer tasks is one phase. *(Builder's call: never merging small plan phases can cost one session per tiny phase; that is accepted to keep PR boundaries intact.)* Each phase records: an ID and short title, its task IDs, whether it is docs-only, whether it needs a security review and why, and whether it can start now or waits for a named approval.
- **Approvals and order.** Phases run in plan order, so a phase that waits for an approval also holds back every phase after it. Approval is per phase: a phase whose tasks are only partly approved waits as a whole. The prompt for the phase just before a waiting phase ends with "Stop at the end of Phase N. Phase N+1 waits for <decision>; there is no prompt for it yet." *(Builder's call.)*
- **Expected changes between phases.** After Phase 1, the plan branch has moved and earlier phases are merged; that is expected and is not drift. The next session checks that the previous phase is merged into the plan branch, and that the plan and spec are unchanged apart from task checkboxes being ticked. Any other change to the plan, spec or approvals means the session reconciles first, as today. The renderer's fingerprint check still runs at render time only, so it is not affected. *(Builder's call.)*
- **Progress file.** The plugin does not create or own a progress file. Superpowers' execution workflow already keeps one (for example `.superpowers/sdd/<plan>/progress.md`); a fresh session uses it when it exists. Prompts do not name it. *(Builder's call.)*
- **Report.** The phase grouping appears as a visible table in section 8, above the prompts. Section 8 then holds one prompt per phase, in order. Each prompt follows the existing 50–80-word target and 80-word maximum and keeps the existing rules: absolute paths in backticks, reference to report and context, no added permissions.
- **Prompt wording.** The prompt names one phase and its tasks, and replaces "the scope end" with an explicit "Stop at the end of Phase N and print the Phase N+1 prompt from the report; do not start it." The last phase's prompt says to stop at the end of the plan.
- **Ready after approvals.** Phases that wait for an approval show what they wait for; they get a prompt only once the approval is recorded and the report is re-rendered, as today.
- **Not ready.** Unchanged: one remediation prompt with `Do not start dependent implementation.` and no per-phase prompts. The phase grouping table is still shown.
- **A phase-only validation** (the user validated one phase) groups only that selected scope.

## Renderer changes

- New reports use **format version 3**. Version 3 adds a required phase list in `context.json` and the per-phase prompts in section 8. Versions 1 and 2 still render saved reports unchanged; existing reports are not migrated.
- Version 3 also records the ordered list of validated task IDs, so the renderer can check that the phases cover that list exactly once and in order, and that no phase is empty.
- Each per-phase prompt is checked like today's handoff (word limit, Not ready rules). The renderer writes the first startable phase's prompt to `handoff.txt`, as today, and also saves each phase's prompt as its own text file. Each prompt in the HTML has its own copy button.
- The renderer does not enforce phase size; the 3–5 target is guidance in the skill text.
- Add regression tests for: a task missing from the phases, a task in two phases, out-of-order tasks, an empty phase, a phase prompt over 80 words, and a Not ready report with per-phase prompts.

## Constraints

- Python standard library only; no new dependencies.
- Both hosts (Claude Code and Codex) get the same skill text.
- `validate-plan` stays explicit-only (`disable-model-invocation: true`, `allow_implicit_invocation: false`).
- The demo (`scripts/demo.py`) and `scripts/check_package.py` keep passing; the demo moves to format version 3.

## Non-goals

- Starting sessions automatically. No hook or script launches the next phase; the maintainer starts each fresh session by hand.
- Merging automatically. Merge stays with the maintainer, under each repository's rules.
- Changing the plan's tasks, task order, task count or phase headings to fit the grouping.
- Choosing models for helper agents, or other host settings.

## Anti-goals

The change fails, even if it renders, if:

- A phase prompt lets the agent run past its phase into the next one.
- The grouping reorders, splits, drops or duplicates a task.
- A prompt grants commit, PR, comment, merge, dependency or service permissions that the repository rules or report do not already grant.
- An implementing session stops mid-phase for a routine question.
- Evidence or approvals are lost between sessions: each fresh session must be able to recover state from the plan, report, context and repository, plus a progress file when the workflow keeps one.

## Follow-ups outside this change

- Update repository instructions to the recommended workflow: this repository's `AGENTS.md` (docs-only PRs CI only; security review only on flagged phases; severity-based review loop) and e2ba's `AGENTS.md`. Separate PRs, one per repository.
- Update `docs/evaluation.md` cases for the phased handoff.
- Measure the next two plans built this way against the baseline above: peak context per implementation session and total implementation cost.

## Left to the builder

- `context.json` field names for the phase list and task inventory.
- File names for the per-phase prompt files.
- Exact HTML layout of the phase table and copy buttons, within the current report style.
- Exact wording of the skill and template text, within the rules above.
