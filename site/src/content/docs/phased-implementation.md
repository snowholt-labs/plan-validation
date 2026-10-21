---
title: Phased implementation
description: Run a validated plan one small phase per fresh session.
---

A validated plan can be built in one long session, but long sessions are expensive. Every message re-reads the whole conversation, so each new step costs more than the last, and finished work keeps taking up space the next task does not need. Running each small phase in its own fresh session keeps every session short.

## How the report helps

The validator groups the plan's existing tasks into small phases. It does not change the plan: the grouping lives only in the report and its `context.json`.

- Every validated task is in exactly one phase, in plan order. No task is split or moved.
- A phase never crosses a phase boundary the plan already defines. A large plan phase is split into consecutive sub-phases, aiming for 3–5 tasks each.
- Section 8 of the report shows a phase table: each phase's tasks, whether it is docs-only, whether it needs a security review and why, and whether it can start or waits for an approval.
- Each ready phase gets its own launch prompt with a copy button, saved as `handoff-phase-<id>.txt` beside the report.
- Each prompt names one phase and includes a stop: `Stop at the end of Phase 1 and print the Phase 2 prompt from the report; do not start it.` The last phase's prompt says it is the last phase.

Phases run in order. A phase that waits for an approval holds back every phase after it, and it gets a prompt only after the approval is recorded and the report is rendered again.

## Recommended per-phase workflow

This is repository workflow, so it belongs in each repository's own instructions (for example `AGENTS.md`), not in the launch prompt. A suggested version:

1. A fresh session reads the plan, spec, report, context and the progress file, if the workflow keeps one.
2. Helper agents build the phase's tasks. The main session coordinates and keeps only short results.
3. A helper agent runs a code review on the branch, and the findings get fixed. Repeat by severity, not by round count: keep going while a round finds bugs, security issues or failing tests, and stop when a round finds only minor items such as style, naming or nitpicks. Save those minor items as action points for the final review. As a safety limit, stop after 5 rounds: if real problems remain, do not open the PR, and ask the maintainer.
4. A helper agent runs a security review only when the phase is flagged as security-sensitive (authentication, user input, secrets, dependencies or CI workflows). It reviews the branch, so it runs before the PR is opened.
5. Open the PR into the plan branch and wait for CI to pass. Because both reviews already ran, CI usually runs once per PR.
6. Post a short review summary as a PR comment, and record the action points in the progress file.
7. Stop, and print the next phase's prompt from the report. The maintainer merges the phase PR, then starts the next phase in a fresh session.

Other rules:

- **Docs-only PRs** (for example, fixing a reference in a plan or spec) need CI only, with no code or security review.
- **The final plan-to-main PR** gets a full code review and a full security review of the whole diff. That review also clears the saved action points.
- **One phase at a time.** A phase starts only after the previous phase is merged into the plan branch. The session checks this first and stops if it is not.

Between phases, the plan branch moves on purpose: earlier phases are merged and their task checkboxes are ticked. That is expected. Any other change to the plan, spec or approvals means the session reconciles it with the report before building.

## Text for your repository instructions

Paste this into your repository's `AGENTS.md` (or equivalent) and adjust it to your rules:

```markdown
### Phased implementation

- Run one validated phase per fresh session. Start a phase only after the previous phase is merged into the plan branch.
- Build the phase's tasks with helper agents; keep only short results in the main session.
- Review the branch and fix findings. Repeat while a round finds bugs, security issues or failing tests; stop when only minor items remain and save them as action points. After 5 rounds with real problems left, do not open the PR; ask the maintainer.
- Run a security review before opening the PR only when the phase is flagged security-sensitive (authentication, user input, secrets, dependencies, CI workflows).
- Open the PR into the plan branch, wait for CI, post a short review summary as a PR comment and record action points in the progress file.
- Stop at the end of the phase and print the next phase's prompt from the report. The maintainer merges and starts the next session.
- Between phases, merged earlier phases and ticked task checkboxes are expected. Reconcile any other change to the plan, spec or approvals with the validation report before building.
- Docs-only PRs need CI only. The final plan-to-main PR gets a full code review and a full security review, which also clears the saved action points.
```
