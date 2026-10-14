---
name: validate-plan
description: Review, rehearse and revise an implementation plan against its approved specification when explicitly asked to validate a plan. Produce a complete HTML evidence report, scope comparison and fresh-session handoff.
disable-model-invocation: true
---

# Validate an implementation plan

Review the plan against the approved specification and current repository, rehearse its implementation where authorized, and preserve what actually happened. This is a validation workflow, not delivery of the feature.

## Host and inputs

- Codex standalone skills: `$validate-plan`; `$validation-args` prepares the inputs.
- Claude Code plugin: `/plan-validation:validate-plan`; `/plan-validation:validation-args` prepares the inputs. Standalone Claude skills use `/validate-plan` and `/validation-args`.
- Read arguments from the invoking message. Accept positional PLAN, SPEC, then free-text FOCUS, or labeled `PLAN:`, `SPEC:`, `FOCUS:`. Quote paths that contain spaces. This is a skill invocation, not a shell command.
- Resolve repository-relative paths from the selected worktree root and Markdown links from their containing document. Follow the plan's `**Spec:**` link when SPEC is omitted. Preserve uncommitted worktree copies.
- Ask for missing required paths or a genuinely ambiguous pairing. Inspect at most three plausible plan candidates; never select solely by modification time. Omitted FOCUS means derive risks from SPEC; no question is needed.
- Support ordinary Markdown plans as well as Superpowers plans. Use an installed planning skill's conventions when relevant, but do not require, install, upgrade or read private internal templates from another plugin.

## Authority and boundaries

- Read repository instructions and honor the user's selected phase, task range, permissions and verification restrictions.
- Within the repository, edit only the selected PLAN and SPEC, leaving them uncommitted. Save report artifacts outside the repository. Preserve all unrelated changes.
- Correct stale paths, contradictions, invalid commands and missing details that preserve approved requirements. Ask before changing requirements, architecture, user-visible behavior, security/privacy boundaries, dependencies, services, cost or delivery scope. If a correction also changes a boundary, it requires approval.
- Do not read secrets, install dependencies, commit, push, open PRs, post comments, merge or deploy during validation. Printing a handoff does not execute it or grant these permissions.
- A detached Git worktree isolates working files; it is not a security sandbox. Inspect planned commands before executing them. Do not run commands that touch production, shared databases, external services, credentials, unapproved networks or destructive operations without explicit authorization. Record the blocked check and continue independent work.
- A read-only request overrides document edits and execution: inspect only, report that rehearsal was not run, and do not imply that text review proves runtime behavior.

## Workflow

1. **Establish the baseline.** Read PLAN, SPEC and the relevant code, tests, configuration and locked dependency versions. Record source worktree, branch or detached HEAD, `git status --porcelain -uall`, worktrees, intended base SHA and the exact scope. Distinguish observed HEAD from the intended implementation base. If the scope is already implemented, clarify whether to review remaining tasks or stop.
2. **Preserve original evidence.** Read [references/html-report.md](references/html-report.md). Create its private run directory; copy untouched PLAN and SPEC there before edits. Record document hashes, requirement IDs, phases, unique numbered tasks, implementation/supporting tasks and dependencies/services. Use Unknown for an unrecoverable baseline.
3. **Review coverage and risks.** Map every scoped SPEC requirement to a PLAN task and a meaningful test; map every task back to a requirement. Check current interfaces, exact files, assertions, error paths, sequencing, security/privacy, performance where relevant, and rollout/rollback. Verify external technical claims using available Context7 tools or current official documentation. Label findings Verified, Assumption or Unknown and cite evidence.
4. **Revise with scope control.** Repair defects inside existing tasks where practical. Require precise interfaces, fixed values, test assertions and commands; do not demand complete routine implementation bodies. Keep existing document structure and decision IDs. Explain every task split/addition/removal and repeated check. Preserve the repository's own branch and review conventions; do not introduce a plan branch or merge policy. Collect material approval questions; leave affected requirements unchanged until answered.
5. **Rehearse the authorized scope.** Create a new detached worktree at the confirmed implementation base. Use a gitignored `.worktrees/plan-dryrun-<topic>` path or a session temporary directory. Implement enough of each scoped task to exercise its instructions and assertions; skip commit, push, PR and deployment steps. Run only approved focused commands whose dependencies already exist. Record exact commands, exit codes, outputs and relevant counts. A blocked environment is a recorded limitation, not a passing check. Repair the plan when an actual mismatch exposes a defect.
6. **Obtain an independent cold read.** This skill explicitly requests one fresh review agent when delegation is available and permitted. Use [references/plan-reviewer.md](references/plan-reviewer.md), original scope snapshots and current documents. Reviewers are read-only and return findings as their final response. Wait for the completed response, verify findings and record their disposition. If an independent reviewer is unavailable, disclose that gap and use Not ready until a separate review is supplied; never present self-review as independent. Recheck material later edits.
7. **Resolve decisions.** Ask only for unresolved consequential decisions, grouping at most three at a time. Do not repeat existing approvals. Continue independent authorized work while decisions are pending. Recheck affected sections after an approved change without chasing a perfect score.
8. **Clean up and deliver.** Inspect the exact worktree created by this run, preserve evidence, then remove only that disposable worktree. Force removal is allowed only for its known rehearsal edits; never remove another checkout or unknown work. Compare final branch, status and worktree inventory with the baseline. Report concurrent changes without reverting or switching them. Score and render the complete report below.

## Report and handoff

Read [references/report-contract.md](references/report-contract.md) for the rubric and eight required sections. Deliver both five-dimension comparison tables and their calculated averages, decision confidence with evidence, scope comparison, actual checks and limits, and the complete handoff. Scores describe reviewed document quality; confidence estimates are subjective, not calibrated probabilities.

- **Ready:** no material blocker or unresolved approval for the named implementation scope, with the independent review completed.
- **Ready after approvals:** only identified non-blocking approvals remain; dependent work waits.
- **Not ready:** a blocker remains or required independent review/evidence is missing. Include a remediation prompt stating `Do not start dependent implementation.`

Instantiate [handoff-template.md](handoff-template.md) from verified paths, revisions, checks and permissions. Carry the user's actual authorization; never add commit, PR, comment, merge, deployment, dependency or service permissions. An optional repository-specific workflow belongs in that repository's instructions, not in this skill's universal defaults.

Use `scripts/render_report.py` with the files described in [references/html-report.md](references/html-report.md). Inspect the output and exact `handoff.txt`. The renderer checks structure, arithmetic and document fingerprints; it does not prove that an agent review or command actually occurred.

Return a brief verdict, a clickable absolute link to `report.html`, and any immediate blocker. The HTML must contain the full report even when chat is concise. If the user asks for the full report in chat, include all eight sections as well.

## Resume or repeat

Keep the original/revised snapshots, hashes, commands/results, reviewer response, tested SHA, scope, approvals, report and handoff in the durable run directory. Read that record after compaction; never reconstruct counts or approvals from a vague recap.

When asked to repeat results, verify current document hashes, worktree, base and approvals, then link the saved complete report. Regenerate missing HTML from saved evidence without claiming a new validation. Mark changed or unverifiable state historical; retain the historical prompt and provide a current remediation prompt when needed. Do not replace recorded hashes to make stale evidence appear current. Static HTML only reflects checks made when rendered.
