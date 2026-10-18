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

Reviews and revises the selected plan and specification, rehearses them, has them independently reviewed, and delivers an HTML report. It changes the selected planning documents, disposable rehearsal files and local report files. It leaves the planning documents uncommitted and does not ship the feature.

### revise-prompt

Critiques and scores a prompt, asks only the questions that matter, uses routine defaults it tells you about, and returns a revision you can copy. It changes nothing but the conversation and never runs the prompt you give it.

For setup, see [Get started](/plan-validation/get-started/). For what a report contains, see [Reports and handoffs](/plan-validation/reports-and-handoffs/).
