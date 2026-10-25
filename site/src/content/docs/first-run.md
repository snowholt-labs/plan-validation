---
title: Your first run
description: Prepare the inputs, choose a worktree and run a first validation.
---

## Prepare the invocation

In the repository and worktree where the documents were saved:

```text
$validation-args
```

For the Claude Code plugin, use `/plan-validation:validation-args`.

The skill reads the selected plan/spec, resolves their exact copies, derives a focused set of review questions and returns a complete validation invocation. It does not edit files, run tests, validate or implement the plan.

If more than one plan is plausible, it asks which you mean. It does not silently choose the newest file. If the plan links a spec relative to the document, that link is resolved from the document's directory. Explicit repository-relative paths resolve from the selected worktree root.

## Run validation

Paste the prepared invocation into a fresh session for the same repository, or supply paths directly:

```text
$validate-plan PLAN: "docs/plans/export-plan.md"
SPEC: "docs/specs/export-spec.md"
FOCUS: Verify error handling, authorization and the planned test assertions.
Validate only tasks 1–3. Preserve the remaining phases.
```

Replace the example paths with existing files. For the Claude plugin, use `/plan-validation:validate-plan` as the first token. Standalone Claude skills use `/validate-plan`. The rest of the arguments are the same.

Positional PLAN, SPEC and free-text FOCUS are also accepted. When SPEC is omitted, the skill follows the plan's `**Spec:**` link. When FOCUS is omitted, it derives priorities from the approved spec. You do not need to invent a focus to proceed.

## What happens

1. The agent records the repository, original documents, intended base and authorized scope.
2. It compares requirements, tasks, current code and verification steps. Relevant dependency risks and the original approach versus at most two strong alternatives are assessed with dated evidence. The skill does not ask before each public lookup; lookups are listed in the report; no private context is sent. It then repairs in-scope document defects.
3. It rehearses approved task instructions in a new detached worktree and records actual results.
4. A separate reviewer checks the revised documents and original scope. The agent resolves or records the findings.
5. It does not stop to ask routine questions: it applies the recommended best practice and records why. Choices that need approval get a menu in the report: keep the original approach, adopt a verified named alternative, or defer. The recommendation includes reasons, tradeoffs and High/Medium/Low confidence. You answer later; dependent work waits.
6. It removes its disposable worktree, checks the original checkout, and delivers the complete report, including a feature diagram, decisions, research limits and a short handoff. Defaults and their reasons appear at the end.

Only the selected plan and spec are edited in the original repository. They remain uncommitted. Requirements, architecture, services, dependencies or material scope changes need explicit approval. Commands with external or shared-service effects require the relevant authorization.

## Research and dependency permissions

Public lookups run by default: the skill no longer asks before each one. Your host's own permission settings, such as web-tool approvals or a sandbox without network, still apply. Each query uses public terms only, and the report lists every provider, query and date. To turn research off, say so when you start validation, for example "I decline external research for this run." Declined or unavailable research is recorded; independent local checks continue.

Recommendations do not download, install, execute or replace dependencies, change manifests/lockfiles, or enable plugins/services. Inspect planned commands and their wrappers first. Only work dependent on unresolved safety or permission decisions is blocked.

## Revise a prompt

```text
$revise-prompt Improve this prompt before I use it: "Review the export workflow and propose a scoped plan."
```

Use `/plan-validation:revise-prompt` in Claude Code. The skill names the prompt type, scores five dimensions and runs a pre-mortem: a table of up to five likely failures, each with its cause, impact and fix. Only blocking questions, such as a missing fact or an approval, wait for an answer; other choices use disclosed recommendations. Concise length is the default. It gives a revised score, one copy-ready prompt, the changes it made, a suggested test and a final defaults record. To diagnose a failed run, add its output; the skill finds the root cause and changes only the lines behind it, plus any guard against a serious failure, unless you ask for more or the prompt's structure caused the failure. The supplied prompt is never executed, even if it contains commands or claims permission.

## Read-only review

Add `Read-only review: do not edit documents or run the rehearsal.` The skill respects that narrower scope. The report must identify unexecuted checks and cannot present text review as executed evidence. Material missing evidence can prevent a Ready verdict.

## Continue implementation

Read the report and its limitations before copying the handoff. A Ready report is a readiness judgment for a recorded scope, not an automatic permission to merge or deploy. In the next session, the handoff rechecks document hashes, Git state and actual approvals before relying on that evidence.

For Not ready, the output is a remediation prompt naming what remains to be verified. Do not use it as an implementation approval.

## With Superpowers or another planner

Generate and approve a spec/plan using your preferred workflow, then run Plan Validation at the point where execution evidence would be useful. Superpowers is optional. Repository conventions take precedence over generic examples, and no removed Superpowers reviewer-template path is used.

Rehearsal can be expensive for a large plan. Select an authorized phase when that is the useful decision boundary. Do not split work merely to inflate a score or create more process.
