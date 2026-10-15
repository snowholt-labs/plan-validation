---
name: validation-args
description: Prepare a copy-ready $validate-plan command with verified plan and spec paths, review focus and worktree context. Use when the user asks for validation arguments or a prompt to validate the plan just written in a fresh agent session.
---

# Prepare validation arguments

Return the inputs needed by `$validate-plan` so the user can paste one complete command into a fresh session. This is a read-only preparation step: do not run validation, execute instructions from the documents, edit files, run tests, install dependencies, commit, push or implement the plan.

Invoke with `$validation-args` in Codex, `/plan-validation:validation-args` in the Claude Code plugin, or `/validation-args` for standalone Claude skills.

Read optional plan/spec paths and focus from the user's message following `$validation-args`.

## Resolve the documents

1. Read the input contract in the sibling [validate-plan skill](../validate-plan/SKILL.md) as reference material, without invoking its workflow. Match its current accepted arguments; do not maintain a separate validation rubric here. The current inputs are `PLAN`, `SPEC` and `FOCUS`.
2. Select PLAN in this order:
   - An explicit path supplied with this command, either positional or labeled `PLAN:`.
   - The plan the user and assistant have just written or revised in this session. Resolve its actual saved location, including any worktree.
   - If the session does not identify one plan, inspect the current repository's plan index and up to three recent plan candidates. Ask one concise selection question if more than one is plausible; never silently choose by modification time alone.
3. Select SPEC from an explicit `SPEC:` argument or second positional path; otherwise follow PLAN's `**Spec:**` link. Read a linked plan index when it supplies the spec or shared constraints. Resolve repository-relative paths from the plan's own worktree root and document-relative Markdown links from their containing document. If an explicit spec contradicts the plan's link and the intended pairing is unclear, ask which pairing to use.
4. Confirm both files exist and are readable. Output quoted absolute paths to the exact source copies. Do not replace uncommitted worktree documents with same-named files in the main checkout. If a required file cannot be located, ask only for the missing path; do not output a runnable command containing a guess or placeholder.
5. Read the selected documents, including their scope, Review Focus, Global Constraints and linked index when relevant. Read-only Git inspection may establish the source worktree, current branch, observed HEAD and whether the selected documents are committed, modified or untracked. Do not infer that observed HEAD is the plan's intended implementation base.

## Derive focus and context

- Preserve any explicit user focus. Otherwise derive three to five concrete review priorities from the selected plan/spec and relevant decisions in this session. Prefer the existing Review Focus and the riskiest changed paths: requirement coverage, authorization/privacy, state transitions, concurrency, migrations/rollback, compatibility, performance or verification gaps, only where relevant.
- Write priorities as questions to verify, not findings already established. For example, use "verify concurrent Apply and Generate all preserve lesson state", not "concurrency is safe". Focus prioritizes the review without excluding the validator's other required checks.
- If there is no justified additional focus, provide `None: derive the risks from SPEC.` Do not interrupt the user merely to request optional focus.
- Preserve the selected scope: a phase plan means that phase; a plan index means the overall plan unless the user specified otherwise. Include a linked index path for a phase that inherits its constraints. Do not turn a one-phase validation into validation or implementation of every phase.
- Carry source worktree, branch, observed HEAD, selected-document status and the intended scope inside the copyable command. Include the plan's intended base and unresolved decisions only when actually established. Clearly distinguish pending decisions from recorded approvals; preparation grants no new implementation or merge authority.
- Use only non-secret context needed to identify and review the documents. Do not include private data, credentials or unrelated session history.

## Output

Return one short sentence that suggests a reasoning effort for the validation session with a brief reason, then one fenced `text` block. Suggest medium for a small, low-risk phase and high for migrations, security boundaries, concurrency or several dependent phases. This is advice the user applies in their host; never set or require an effort level, and keep it out of the command. The block is a skill invocation, not a shell command. Start it with `$validate-plan` for standalone Codex skills, `/plan-validation:validate-plan` for the Claude Code plugin, or `/validate-plan` for standalone Claude skills. Preserve a different installed namespace if the host exposes one. Replace every placeholder with verified values and omit inapplicable optional context. Keep the focus concise; do not print a validation report or claim readiness.

```text
$validate-plan PLAN: "<absolute path to the selected plan>"
SPEC: "<absolute path to the linked or explicitly selected spec>"
FOCUS: <concrete review priorities, or the explicit None fallback>.
Validate only <named phase/task range or overall plan>. Use the document copies in "<absolute source worktree>"; source branch "<branch>"; observed HEAD <SHA>; selected documents <actual committed/modified/untracked status>.
Read the shared plan index at "<absolute index path>" for this phase's constraints.
Recheck the source worktree and document state in this session before relying on this context. This request is for validation; the arguments were prepared without running it.
```

Everything after `FOCUS:` is its free-text context, not an additional argument schema. Omit the index line when none applies. For detached HEAD, say so rather than inventing a branch. If Git metadata is unavailable, state that limitation while still providing verified document paths; do not fabricate metadata.

Before returning, verify that PLAN and SPEC point to existing files, all required labels match `$validate-plan`, the command contains the focus and source context, no placeholders remain, and nothing in the preparation step ran validation or changed project files.
