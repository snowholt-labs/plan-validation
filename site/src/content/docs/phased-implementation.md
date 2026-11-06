---
title: Phased implementation
description: Run a validated plan one small phase per fresh session.
---

A validated plan can be built in one long session, but long sessions are expensive. Every message re-reads the whole conversation, so each new step costs more than the last, and finished work keeps taking up space the next task does not need. Running each small phase in its own fresh session keeps every session short.

## How the report helps

The validator groups the plan's existing tasks into small phases. The grouping does not change the plan: it lives only in the report and its `context.json`.

- Every validated task is in exactly one phase, in plan order. No task is split or moved.
- A phase never crosses a phase boundary the plan already defines. A large plan phase is split into consecutive sub-phases, aiming for 3–5 tasks each.
- Section 8 of the report shows a phase table: each phase's tasks, whether it is docs-only, whether it needs a security review and why, and whether it can start or waits for an approval.
- Each ready phase gets its own launch prompt with a copy button, saved as `handoff-phase-<id>.txt` beside the report.
- Each prompt names one phase, tells the session to follow the plan's Phase workflow, and includes a stop: `Stop at the end of Phase 1 and print the Phase 2 prompt; do not start it.` The last phase's prompt says it is the last phase.

Phases run in order. A phase that waits for an approval holds back every phase after it, and it gets a prompt only after the approval is recorded and the report is rendered again. Once earlier phases have merged, ask the validator to validate the remaining phases instead; the new report covers only the phases still to build and keeps their phase IDs.

## Recommended per-phase workflow

Each phase follows the plan's **Phase workflow** section: a short list of steps that every phase session runs. Validation adds the [Phase workflow block](https://github.com/snowholt-labs/plan-validation/blob/main/skills/validate-plan/references/phase-workflow.md) near the top of a plan that has no `## Phase workflow` heading, and leaves an existing one as it is. The block grants no permission: pushing, opening a PR and merging still follow your repository's rules and the maintainer. In short, each phase session:

1. Works in a git worktree on its own phase branch.
2. Builds each task test-first and proves it works by running the tests.
3. Reviews the phase against the plan, spec and validation report, checks each finding before fixing it, and finds the cause of any failure before fixing it.
4. Repeats the review until no Medium or High finding remains. Wording-level findings are listed, and the maintainer is asked to fix or skip each one in the end-of-phase report; skipped or unanswered ones are saved as action points.
5. Checks that the branch is ready (tests pass), without pushing, opening a PR or merging yet.
6. Runs the code review, and a security review when the report flags the phase security-sensitive (authentication, user input, secrets, dependencies or CI workflows) or your repository requires one, then delivers the branch as your repository defines, for example a PR into the plan branch.
7. Stops, and prints the next phase's prompt from the report. The maintainer merges the phase PR, then starts the next phase in a fresh session.

The steps name Superpowers skills (`using-git-worktrees`, `test-driven-development`, `requesting-code-review` and others). Without Superpowers, the session follows the same steps as written. A docs-only phase skips the test-first rule.

Other rules:

- **Docs-only PRs** (for example, fixing a reference in a plan or spec) need CI only, with no code or security review.
- **The final plan-to-main PR** gets a full code review and a full security review of the whole diff. That review also clears the saved action points.
- **One phase at a time.** A phase starts only after the previous phase is merged into the plan branch. The session checks this first and stops if it is not.

Between phases, the plan branch moves on purpose: earlier phases are merged and their task checkboxes are ticked. That is expected. Any other change to the plan, spec or approvals means the session reconciles it with the report before building.

## Reviewing a plan's docs PRs

The workflow above needs only CI for docs-only PRs. Some repositories also review docs PRs. The plan-validation repository is one: its own `AGENTS.md` asks for a code review and a security review on every PR into `main` or a plan branch, docs-only PRs included. If your repository reviews a plan's docs PR, or a docs-only phase PR, this review is recommended:

- **A full-plan review instead of `/code-review`.** The reviewer gets the plan, spec and validation report, and checks the docs against each other, the code and the report's recorded decisions.
- **Verified Medium and High findings are fixed in the PR**, design gaps included, and the review runs again until none remain. Reviewer severities map Critical to High, Important to Medium and Minor to Low.
- **Some findings go to the maintainer instead.** A finding that contradicts a recorded decision, or whose fix would change a security or privacy boundary, a permission or an external action, is asked as a question, not fixed.
- **Wording findings do not block.** They are listed, and the maintainer is asked to fix or skip each one at the end.
- **The result is posted as the code review.** `/security-review` runs once, on the final head.

Other docs-only PRs, such as a README fix, have no plan to review against and keep `/code-review`.

## Text for your repository instructions

Paste this into your repository's `AGENTS.md` (or equivalent) and adjust it to your rules:

```markdown
### Phased implementation

- Run one validated phase per fresh session. Start a phase only after the previous phase is merged into the plan branch.
- Build the phase's tasks with helper agents; keep only short results in the main session.
- Follow the plan's Phase workflow section: worktree, test-first tasks, review against the plan, spec and report until no Medium or High finding remains, readiness check, then the code review. Run a security review before opening the PR when the phase is flagged security-sensitive (authentication, user input, secrets, dependencies, CI workflows).
- List wording-level findings and ask the maintainer to fix or skip each one in the end-of-phase report; save skipped or unanswered ones as action points.
- Open the PR into the plan branch, wait for CI and post a short review summary as a PR comment.
- Stop at the end of the phase and print the next phase's prompt from the report. The maintainer merges and starts the next session.
- Between phases, merged earlier phases and ticked task checkboxes are expected. Reconcile any other change to the plan, spec or approvals with the validation report before building.
- Docs-only PRs need CI only. If you review docs PRs, a plan's docs PR and docs-only phase PRs get a full-plan review (plan, spec and report) instead of `/code-review`: fix verified Medium and High findings, design gaps included, until none remain; ask the maintainer about findings that contradict a recorded decision or would change a security or privacy boundary, a permission or an external action; list wording findings for fix-or-skip. Post it as the code review; reviewer severities map Critical to High, Important to Medium and Minor to Low. Run `/security-review` once.
- The final plan-to-main PR gets a full code review and a full security review, which also clears the saved action points.
```
