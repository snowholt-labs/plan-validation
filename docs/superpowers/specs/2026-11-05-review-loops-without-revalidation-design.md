# Review loops without re-validation

**Date:** 2026-11-05
**Status:** Draft for maintainer review

## Why

Release 0.5.0 added a "run validation again" feature (run counting, a 3-run limit, `rerun.txt`, held phase prompts). It was meant to stop the endless `/code-review` loop on docs PRs. It moved the loop instead.

What happened in a real run (a private project, 2026-11-05):

1. Validation deferred an open decision. Answering it later meant a re-render.
2. Round 1 of `/code-review` on the docs PR found a design gap: a lost reply from an external API could cause a duplicate post.
3. The global rule says a design gap in a validated docs PR is not fixed in the PR. The session stopped and asked the maintainer to run `/validate-plan` again, the last of 3 runs.
4. The maintainer had the gap fixed in place anyway, then `/code-review` started another round.

Root cause, as the maintainer sees it: `/code-review` reviews a diff. It does not read the whole plan and spec, so it cannot check the docs against them. It finds partial issues, rewords text and sometimes changes meaning. The Superpowers review skills take the plan and spec as input and check the work against them. `/code-review` is the right tool later, once code exists, to find code bugs.

## Goals

- Drop re-validation entirely: no run counting, no run limit, no "run validation again" recommendation, no held prompts.
- During validation, use Superpowers review, debugging and verification skills to check the plan, and ask the maintainer to answer pending open questions or approve recommendations in the same session.
- Validation adds a fixed per-phase workflow to every new plan that lacks it.
- On docs PRs, replace `/code-review` with a Superpowers review against the full plan, spec and validation report.
- Keep `/code-review` and `/security-review` before every code PR, after the per-phase loop has already caught most issues.

## Non-goals

- No migration of existing plans or saved reports. The maintainer re-runs `/validate-plan` on existing plans to get the new flow.
- No change to scoring, the eight report sections, the phase grouping rules or the verdict rules, except where named below.
- No new runtime dependency. Superpowers is not bundled or required.

## Anti-goals

- A new loop that costs as much as the old one.
- Reviews that reword correct text or change meaning without a real defect.
- A plugin that stops working on Codex or without Superpowers installed.

## Decided by the maintainer

- Re-validation is dropped entirely.
- Each plan uses git worktrees (`superpowers:using-git-worktrees`).
- Validation uses `requesting-code-review`, `receiving-code-review`, `systematic-debugging` and `verification-before-completion`, and asks the maintainer to answer pending open questions or approve recommendations.
- Each phase loops: write the test first, code, prove it works, review against the plan, check each finding before fixing, find the cause of any failure before fixing. Repeat until the review is clean.
- Then `finishing-a-development-branch` says the branch is ready. Only then `/code-review` and `/security-review` run, before the PR.
- Review loops have no round cap while Medium or High findings remain. When only wording-level (Low) findings remain, the loop stops. The session does not block: it opens the PR, lists those findings in the code review, and asks the maintainer to fix or skip each one in its end report.
- The Phase workflow block goes into every user's new plan, adapted: its last step follows that repository's own review and PR rules, so it fits repos without plan branches or Claude Code.
- Docs PRs do not run `/code-review`. The Superpowers review is posted as the docs PR's code review. `/security-review` still runs once on docs PRs.
- Design gaps found in a docs PR are fixed in the PR, and review runs again, until no Medium or High finding remains. A finding whose fix would change a security or privacy boundary, a permission or an external action goes to the maintainer instead (maintainer decision, 2026-11-05).
- Only new plans change. The global `<home>/.claude/rules/git-workflow.md` is updated too.

## Design

### 1. Validation (`/validate-plan`)

Changes to `skills/validate-plan/SKILL.md` and its references:

- **Review loop (workflow step 6).** The independent reviewer gets the full plan, spec and relevant code paths, plus the original snapshots to compare against. Validation leaves its edits uncommitted, so there is no commit range to review. Dispatch the reviewer the way `superpowers:requesting-code-review` does: a fresh reviewer subagent that returns only its findings. Use the `references/plan-reviewer.md` brief, which reviews documents rather than a diff. Triage findings with `superpowers:receiving-code-review` behavior: verify each against the code and documents, push back on wrong ones, never reword correct text. Fix verified Medium and High findings in the plan or spec and review again. Repeat until none remain. A finding whose fix would change requirements, architecture, security boundaries or scope is not fixed: it becomes a pending approval, is asked at the end of the run, and leaves the loop. Low findings are listed, not fixed.
- **Rehearsal failures (step 5).** A failing dry-run command is investigated with `superpowers:systematic-debugging` behavior before the plan is changed: find the cause, then fix the plan.
- **Before the verdict (step 8).** Apply `superpowers:verification-before-completion` behavior: every claim in the verdict and section 7 is backed by a command or review that actually ran in this run.
- **Ask the maintainer once, at the end (end of step 8, after the first render).** Validation still finishes all independent work first without pausing, and renders the report. It then asks one round of questions: each pending approval with its recommendation, and any wording-only findings left by the review loop. Claude Code uses AskUserQuestion; Codex asks in chat. Answers are applied and rechecked, then the same run re-renders. If this run published its report as a private artifact, the re-render updates that same artifact without being asked (maintainer decision, 2026-11-05). A question left unanswered stays a pending approval in the already-rendered report. Where the host cannot ask, the report's open items are the questions. Routine defaults are still recorded without asking.
- **Add the phase workflow to the plan.** When the plan lacks it, validation adds the "Phase workflow" block (section 2) to the plan, once, near the top. This is a new allowed edit and replaces the rule that validation must not invent review conventions for this one block. It is recorded in section 5 of the report as a plan change, with the validate-plan skill's Phase workflow rule as its approval basis. The block grants no permission: its PR and review steps follow the repository's own rules.
- **Phase prompts.** Each phase prompt tells the session to follow the plan's Phase workflow, folded into the existing "Follow recorded decisions…" sentence so the 80-word limit holds. The exact template is in the plan.
- **Drop re-validation.** Remove run counting (`validation_run`, `plan_key`, the 3-run limit and the reset), the `rerun` recommendation, `rerun.txt`, held phase prompts (`handoff_held`) and the run-again-first note. The maintainer can still run `/validate-plan` again by choice; nothing recommends or counts it.
- **Drift warning.** When the plan or spec changed after review, the saved report's historical warning says the documents changed and to reconcile the change or validate again. It names no run number and no limit.
- **Not ready.** The remediation prompt fixes the blocker. The final reply tells the maintainer that validating the fixed plan, by choice, is how to get phase prompts. Nothing counts that run, and the remediation prompt itself never asks for it.
- **Version 4 runs.** An answer recorded for a version 4 run is not re-rendered as a new report, and its context is not migrated. Validate the plan again; the new run uses version 5.

### 2. The per-phase workflow block

Validation writes this block into the plan (wording may be tightened; the steps and order are fixed):

```markdown
## Phase workflow

Every phase follows these steps, in a fresh session, on its own phase branch.

1. Work in a git worktree for the phase branch (`superpowers:using-git-worktrees`).
2. For each task: write the failing test first and watch it fail (`superpowers:test-driven-development`), write the code, then prove it works by running the tests (`superpowers:verification-before-completion`).
3. Review the phase against the plan, spec and validation report (`superpowers:requesting-code-review`, with the plan and spec paths, the report path named in the phase prompt and the phase's base..head range).
4. Check each finding before fixing it, and push back on wrong ones (`superpowers:receiving-code-review`).
5. For any failing test or unexpected behavior, find the cause before fixing it (`superpowers:systematic-debugging`).
6. Repeat steps 3–5 until no Medium or High finding remains (Critical counts as High, Important as Medium, Minor as Low). Do not loop on wording-level findings: list them, and ask the maintainer to fix or skip each one in the end-of-phase report.
7. Run `superpowers:finishing-a-development-branch` as the readiness check: tests pass on the branch. Do not push, open a PR or merge at this step, and never merge locally into a protected or plan branch.
8. Run the code and security reviews this repository's rules require (in Claude Code, `/code-review` and `/security-review`), and fix required findings.
9. Deliver the branch as the repository's rules define (for a plan branch, a PR into that branch). Push and open a PR only when the repository's rules or the maintainer authorize it. Otherwise stop and report that the branch is ready.

A docs-only phase skips step 2's test-first rule. Its step 8 runs the reviews the repository's rules require for docs-only changes.
```

When Superpowers is not installed (or on Codex), each step's behavior stands on its own; the skill names are pointers, not requirements.

### 3. Docs PRs

Applies only to a plan's docs PR and to docs-only phase PRs. Other docs-only PRs (a README fix, a site page) have no plan to review against, so they keep `/code-review`.

- No `/code-review`. The code review is a Superpowers review (`requesting-code-review`) that gets the plan, spec, validation report and relevant code paths, then `receiving-code-review` triage.
- The reviewer checks the docs against each other, the code and the report's recorded decisions. A finding that contradicts a recorded maintainer decision is not fixed; it goes to the maintainer as a question.
- Verified Medium and High findings, design gaps included, are fixed in the PR. Review runs again until none remain. A finding whose fix would change a security or privacy boundary, a permission or an external action is not fixed in the PR; it goes to the maintainer as a question. Wording-only findings are listed in the code review, and the maintainer is asked to fix or skip each one in the end report; they do not block.
- The result is posted as the `## Code review` comment review with the `review/code` status, in the same format as today, so the `Required reviews` ruleset still works.
- `/security-review` runs once on the final head.

### 4. Code PRs

Unchanged except that the per-phase loop (section 2) runs first. `/code-review` rounds and `/security-review` follow the existing repository and global rules, including their round limits.

## What changes

**Global rules, `<home>/.claude/rules/git-workflow.md`** (outside this repo; then run `<home>/.claude/codex/build-agents-md.sh`):

- Line 44: replace "design gaps go back to `/validate-plan` … 3-run limit … at most 3 `/code-review` rounds" with the docs-PR rule in section 3.
- "Reviews Before Every PR": add the docs-PR exception (Superpowers review posted as `## Code review` and `review/code`).
- "Internal reviews from subagent-driven development do not replace these two reviews": keep for code PRs; note the docs-PR exception.
- "Timing": drop the "3 rounds for a validated spec and plan" cap.

**This repo, `AGENTS.md`:** the "Plan work" section and "Every PR into `main` or `plan/**` gets both reviews, docs-only PRs included", to match sections 2–3.

**Skill text:** `skills/validate-plan/SKILL.md` (steps 1, 5, 6, 7, 8 and "Report and handoff"), `references/report-contract.md` (remove "Run validation again"; update the drift text), `references/html-report.md` (remove "Run counting" and the rerun fields), `references/plan-reviewer.md` (report path input, already-dispositioned findings), `handoff-template.md` (remove the run-again and held notes; add the Phase workflow sentence).

**Renderer:** `scripts/render_report.py` and its tests. `assets/report-v4.css` and `report-v4.js` do not change, because saved version 4 reports still draw the rerun card with them. Add format version 5 for new reports: version 4 without `validation_run`, `rerun`, `rerun.txt` and held prompts, with the new drift wording. Version 4 renders saved reports only. Frozen digests are not re-pinned.

**Docs and evaluation:** `docs/evaluation.md` (remove re-run, run-limit and run-count rows; add rows for the end-of-validation questions, the Phase workflow block and the docs-PR review), `site/src/content/docs/phased-implementation.md` (including its pasteable block), `reports-and-handoffs.md`, `troubleshooting.md`, root `CHANGELOG.md`.

## Builder's calls (marked as mine, not the maintainer's)

- **Format version 5** instead of changing version 4, so existing saved reports still re-render.
- **Superpowers optional:** skills are named when installed; their behavior is written out so the flow works without them, keeping the plugin dual-host with no required plugin.
- **One plan-level Phase workflow block**, pointed to from each phase prompt, instead of repeating the loop in every phase.
- **Worktree per phase branch**, since phases run one after another. The validation dry-run worktree is unchanged.
- **finishing-a-development-branch** used only as the readiness check (tests pass). It does not push, open a PR or merge; reviews run next, and delivery follows the repository's rules.
- **Questions asked once at the end** of validation, so independent work never waits on the maintainer.
- **The docs-PR reviewer gets the validation report**, so it checks against recorded decisions instead of redesigning from scratch.
- **Report path:** phase prompts already name the saved `report.md`; the phase session, and the docs-PR session, pass that path to the reviewer. The committed plan holds no local path.
- **Rollout:** the global `git-workflow.md` edit is a follow-up after the plugin release, not a plan phase, and then applies to all plans. The maintainer decided on 2026-11-05 that this plan's own docs PR and its docs-only phases already use the full-plan review of section 3. Its code phase follows the rules in force.
- **Docs-PR design gaps** that do not contradict a recorded maintainer decision, and do not change a security or privacy boundary, a permission or an external action, are fixed without asking, as the maintainer decided.
- **Existing `/code-review` round limits on code PRs stay** (6 rounds global, 5 in this repo's AGENTS.md); the no-cap rule applies to the Superpowers loops.

## Left to the builder

- Exact wording of skill text, the Phase workflow block and the drift warning.
- Renderer structure for version 5 and test layout.
- Which site pages need more than a sentence change.

## Success looks like

- A validated plan's docs PR settles without any `/validate-plan` re-run.
- Validation ends with the maintainer's answers recorded, so fewer decisions are deferred to later phases.
- New plans contain the Phase workflow block, and phase sessions follow it.
- `/code-review` on code PRs finds fewer High and Medium findings than before (observed, not measured).
