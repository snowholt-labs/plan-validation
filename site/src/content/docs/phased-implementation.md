---
title: Phased implementation
description: Run a validated plan one small phase per fresh session.
---

A validated plan can be built in one long session, but long sessions are expensive. Every message re-reads the whole conversation, so each new step costs more than the last, and finished work keeps taking up space the next task does not need. Running each small phase in its own fresh session keeps every session short.

## How the report helps

The validator groups the plan's existing tasks into small phases. The grouping does not change the plan: it lives only in the report and its `context.json`.

- Every validated task is in exactly one phase, in plan order. No task is split or moved.
- A phase never crosses a phase boundary the plan already defines. A large plan phase is split into consecutive sub-phases, aiming for 3–5 tasks each.
- Section 8 of the report shows a phase table: each phase's tasks, whether it is docs-only, whether it is security-sensitive and why (the "Security review" column marks where to look hardest; on the current Phase workflow it does not decide whether a security review runs), and whether it can start or waits for an approval.
- Each ready phase gets its own launch prompt with a copy button, saved as `handoff-phase-<id>.txt` beside the report.
- Each prompt names one phase, tells the session to follow the plan's Phase workflow, and includes a stop: `Stop at the end of Phase 1 and print the Phase 2 prompt; do not start it.` The last phase's prompt says it is the last phase.

Phases run in order. A phase that waits for an approval holds back every phase after it, and it gets a prompt only after the approval is recorded and the report is rendered again. Once earlier phases have merged, ask the validator to validate the remaining phases instead; the new report covers only the phases still to build and keeps their phase IDs.

## Recommended per-phase workflow

Each phase follows the plan's **Phase workflow** section: a short list of steps that every phase session runs. Validation adds the [Phase workflow block](https://github.com/snowholt-labs/plan-validation/blob/main/skills/validate-plan/references/phase-workflow.md) near the top of a plan that has no `## Phase workflow` heading, and leaves an existing one as it is. Apart from the worktree consent in its first step, the block grants no permission: pushing, opening a PR and merging still follow your repository's rules and the maintainer. In short, each phase session:

1. Works in a git worktree on its own phase branch, reads the phase's done-check from the report, and checks that no parked finding from an earlier phase still waits for a design update.
2. Builds each task test-first: a unit test, plus an integration test where the task crosses a boundary such as a database, an API or another service. Wording, configuration and version tasks skip this.
3. Reviews the phase with a fresh reviewer, checks each finding against the code before acting, and finds the cause of any failure before fixing it. Later rounds review only the latest fix.
4. Repeats the review until no Medium or High finding remains, with no round cap. When a problem keeps coming back, the session questions the design instead of patching again, and may park the finding with a recorded decision (the block's step 6 says when). A security finding is never parked, and never skipped as Low. Low findings are listed for the maintainer to fix or skip.
5. Proves the phase is ready by running the done-check and the full test suites.
6. Runs the code review and the security review once each on the final version and fixes every confirmed finding; each fix gets a fresh review of the fix and a security review of the fix; the code review does not run again. Then it delivers the branch as your repository defines, for example a PR into the plan branch.
7. Stops, and prints the next phase's prompt from the report, after a design-update prompt when a finding was parked. In that design update, you fix each parked finding in a new phase or accept it with a reason. The maintainer merges the phase PR, then starts the next phase in a fresh session.

The steps name Superpowers skills (`using-git-worktrees`, `test-driven-development`, `requesting-code-review` and others), and the session loads each one at its step. Without Superpowers, it follows the same steps as written. A docs-only phase skips the test-first rule, and its final reviews are the ones your repository requires for docs-only changes. The session asks you only when the next step is destructive, is a security-sensitive action, needs an approval it does not have, or the plan is too broken to follow.

Other rules:

- **Docs-only PRs** follow your repository's review rules. A plan's docs PR can reuse the code and security reviews from the validation run when it changes only the plan and spec (see below).
- **The final plan-to-main PR** gets a full code review and a full security review of the whole diff. That review also clears the saved action points and checks that every parked finding was fixed or accepted with a reason.
- **One phase at a time.** A phase starts only after the previous phase is merged into the plan branch. The session checks this first and stops if it is not.
- **After a phase PR opens,** a later commit, such as a CI fix, gets a review of that change and a security review of that change, not both full reviews, unless the PR targets your default branch or your repository's rules require both full reviews again (the block's step 10). A plan's docs PR into a branch other than your default branch reviews only what changed after a push (see below); every other PR gets both full reviews again.
- **Saved `/code-review` settings.** In Claude Code, validation's final review, phase sessions and docs-PR reviews that follow this page type `/code-review high --max-findings all`. The command keeps a typed level and finding limit as your saved choice, so type your own level and `--max-findings default` on your next manual run.
- **Plans already in progress.** A plan written before this workflow keeps its older Phase workflow, and its prompts keep the older pause sentence. To move it over, open a small docs PR that replaces its `## Phase workflow` section with the current block and adds `Replaced on <date>: workflow steps only, no scope change.` under the heading. Under it, add a `Boundary tasks:` line with your choice for each task that crosses a boundary without integration test infrastructure: approved without integration tests, or deferred. After the swap, the block's stop reasons govern even where a saved prompt has the older pause sentence. A plan that already has the `<!-- phase-workflow: 2 -->` marker keeps its copy and needs no swap, unless you accept a parked finding and its copy's step 1 has no `Accepted:` rule: then swap in the current block in the same docs PR. Give every swap PR a code review and a security review before it merges, because the next phase trusts its Phase workflow section. A plan swapped under validate-plan 0.7.0 compares that section with the installed block, so after you upgrade the plugin its next phase stops at step 1: swap in the current block again, in a docs PR that gets both reviews.

Between phases, the plan branch moves on purpose: earlier phases are merged and their task checkboxes are ticked. That is expected, and so are a swapped Phase workflow section and parked findings you accepted. Any other change to the plan, spec or approvals means the session reconciles it with the report before building.

## Reviewing a plan's docs PRs

Some repositories review docs PRs. The plan-validation repository is one: its own `AGENTS.md` asks for a code review and a security review on every PR into `main` or a plan branch, docs-only PRs included. Validation runs both reviews on the final plan and spec when it can, and the report records what each read and its hash. A plan's docs PR can reuse them:

- **Reuse when nothing changed.** If the PR changes only the plan and spec, both match the hashes in the report and the report records what each review read and marks none of the final text as uncovered, post the recorded results as the code and security reviews, each with a `Reused:` line naming the hash it read and the final hash, and `Scope:` lines naming what covered any difference: each validation fix and any end-of-run answer edits, with the reviews that covered them.
- **Otherwise review the difference once.** Each review runs once on what differs from the text it read, or on the whole plan and spec when that text is gone, plus any other changed files. After a new push, each review covers only what changed since the head its own last posted review named (counting only reviews the reviewing account posted; the whole plan and spec, plus any other changed files, when that head is not an ancestor of the PR head), unless the PR targets your default branch, which gets both full reviews again. [Validation reviews](https://github.com/snowholt-labs/plan-validation/blob/main/skills/validate-plan/references/validation-reviews.md) gives the targets and saved diffs; your repository's rules win when they ask for more. In Claude Code, type the code review as `/code-review high --max-findings all`, and run the security review as `/security-review`'s procedure in a subagent on a saved diff, because the command skips documentation files.
- **Some findings go to the maintainer.** A finding whose fix would change a security or privacy boundary, a permission or an external action is asked, not fixed, and stays open in the posted review until the maintainer settles it. A finding that only disagrees with a decision the maintainer recorded is rejected with that decision as evidence.

In the plan-validation repository, a docs-only phase PR gets the code review and the security review once each on its final head, typed and targeted as step 9 of the current Phase workflow block types and targets them for a code phase.

## Text for your repository instructions

Paste this into your repository's `AGENTS.md` (or equivalent) and adjust it to your rules:

```markdown
### Phased implementation

- Run one validated phase per fresh session. Start a phase only after the previous phase is merged into the plan branch.
- Build the phase's tasks with helper agents; keep only short results in the main session.
- Follow the plan's Phase workflow section: worktree, test-first tasks with unit tests and, across boundaries, integration tests, review until no Medium or High finding remains with no round cap, a readiness check with the done-check and full suites, then the code and security reviews once each on the final head, with the code review typed as `/code-review high --max-findings all` in Claude Code.
- List wording-level findings and ask the maintainer to fix or skip each one in the end-of-phase report; save skipped or unanswered ones as action points.
- Open the PR into the plan branch, wait for CI and post a short review summary as a PR comment. A later commit gets a review of that change and a security review of that change, not both full reviews.
- Stop at the end of the phase and print the next phase's prompt from the report, after the design-update prompt when a finding was parked. The maintainer merges and starts the next session.
- Between phases, merged earlier phases, ticked task checkboxes, a `Replaced on <date>` swap that changes only the Phase workflow section and leaves it carrying the `<!-- phase-workflow: 2 -->` marker, and parked findings added with an `Accepted:` line, with no other change to the Parked findings section, are expected. Reconcile any other change to the plan, spec or approvals with the validation report before building.
- When the repository requires reviews on a plan's docs PR, it can reuse validation's `/code-review` and `/security-review` results when it changes only the plan and spec, their hashes match the report and the report records what each review read and marks none of the final text as uncovered. When any of these does not hold, review once what differs, plus any other changed files, and after a new push each review covers only what changed since the head its own last posted review named (counting only reviews the reviewing account posted; the full plan and spec, plus any other changed files, when that head is not an ancestor of the PR head; both full reviews again when the PR targets the default branch); in Claude Code, type `/code-review high --max-findings all` and run `/security-review`'s procedure in a subagent on a saved diff so it reads Markdown. Post reused results with a `Reused:` line naming the hash each review read and the final hash, and `Scope:` lines naming what covered any difference. Ask the maintainer about a finding whose fix would change a security or privacy boundary, a permission or an external action; it stays open in the posted review until the maintainer settles it. Reject a finding that only disagrees with a recorded decision, citing that decision.
- The final plan-to-main PR gets a full code review and a full security review, which also clears the saved action points and checks that every parked finding was fixed or accepted with a reason.
```
