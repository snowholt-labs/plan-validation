---
title: Features
description: What the three skills do, what each one changes, and why checking a plan before implementation helps.
---

A plan can read well and still point to a file that does not exist, leave out an acceptance criterion or tell you to run a command that fails. Plan Validation checks those things before another agent session starts building from the plan.

## Why use it

- **Both directions of coverage.** Every requirement should have a task and a test, and every task should serve a requirement that was approved.
- **Exercise the instructions.** The selected scope is rehearsed against a recorded Git base, using focused checks you approve.
- **Visible scope changes.** Phases, numbered tasks, supporting work and dependencies are compared before and after revision, so nothing shifts quietly.
- **Evidence that outlasts the session.** The original and revised documents, fingerprints, real results, review findings and a complete handoff are saved.

It works with ordinary Markdown plans. [Superpowers](https://github.com/obra/superpowers) is optional.

## The three skills

### validation-args

Finds the right plan and specification copies and prepares a complete `validate-plan` command, including your review focus and worktree context. It only reads. It changes nothing.

### validate-plan

Reviews and revises the selected plan and specification, rehearses them, and has fresh independent reviewers check the revisions within the same run (without one, the report stays Not ready): verified Medium and High findings are fixed and reviewed again, and a finding that would change requirements, architecture, security boundaries or scope becomes a question for you. It then delivers an HTML report and asks one round of questions at the end, the approvals it needs and the Low findings to fix or skip; a host that cannot ask lists them in the report instead. Your answers are applied and the report re-renders in the same run; see [Known issues](/plan-validation/safety-and-limitations/#known-issues) for answers that edit the plan or spec. When the plan has no `## Phase workflow` section and the run is not read-only, it adds one that every phase session follows. It changes the selected planning documents, disposable rehearsal files and local report files. In Claude Code, an off-by-default setting also publishes each new report to your claude.ai account as a private artifact. It leaves the planning documents uncommitted and does not ship the feature.

### revise-prompt

Scores a prompt, imagines how it would fail and fixes those causes, waits only for questions that block the revision, uses defaults it tells you about, and returns a revision you can copy with a test you can run. Give it the output of a failed run and it finds the root cause and makes a minimal fix. It changes nothing but the conversation and never runs the prompt you give it.

For setup, see [Get started](/plan-validation/get-started/). For what a report contains, see [Reports and handoffs](/plan-validation/reports-and-handoffs/).
