# One Review Workflow Follow-up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close every open action point from the one review workflow: build the decisions in the follow-up design, give each repeated rule one home, and align the copies that must stay complete.

**Architecture:** All changes are Markdown text. The Phase workflow block (`references/phase-workflow.md`) and `references/validation-reviews.md` stay the homes of their rules and change first. `SKILL.md`, the handoff template, the report contract, the evaluation rows, the site pages and `AGENTS.md` then point to them or align their full copies. No renderer, report format or `context.json` change.

**Tech Stack:** Markdown skill text; Python 3.10+ standard library checks; Astro docs site (`site/`).

**Spec:** `docs/superpowers/specs/2026-11-13-one-review-followup-design.md` (decisions M1–M5 and P1–P16). Its appendix `docs/superpowers/specs/2026-11-13-one-review-followup-triage.md` holds every row's current text.

## Phase workflow

<!-- phase-workflow: 2 -->

Every phase follows these steps, in a fresh session, on its own phase branch. When Superpowers is installed, load each named skill with the Skill tool at its step. A subagent that does a step loads that step's skill itself, and its brief says so: under `superpowers:subagent-driven-development`, each implementer subagent loads `superpowers:test-driven-development` and `superpowers:systematic-debugging`. Where a loaded skill says to stop and ask, to ask for consent or to wait for the human partner, the stop reasons below decide instead. Without Superpowers, follow each step as written.

1. Work in a git worktree for the phase branch (`superpowers:using-git-worktrees`); this step gives that skill's consent. Read the phase's done-check in section 8 of the validation report, when it has one. If the plan has a `## Parked findings` section that lists a finding from an earlier phase missing from `revised-plan.md` in the report's run directory, the design update (step 10) has not run: stop and say so. A `Replaced on <date>` line under the `## Phase workflow` heading marks a swapped block; that swap is an expected difference from `revised-plan.md` only when the section, apart from that line, matches the block in validate-plan's `references/phase-workflow.md`, marker included. Any other change to that section, or a swap the session cannot compare, needs reconciliation.
2. For each task with observable behavior, write the failing tests first and watch each fail for the expected reason (`superpowers:test-driven-development`): a unit test, plus an integration test when the task crosses a boundary (database, API, authentication, another service). Wording-only, configuration, version and changelog tasks, and fixes of that kind, skip the test-first rule.
3. Write the minimal code that makes the tests pass, keep all tests green, then refactor. Repeat steps 2–3 for each task.
4. Review the phase with a fresh reviewer (`superpowers:requesting-code-review`), given the plan and spec paths and the report path named in the phase prompt. Round 1 reviews the phase's base..head range; when `superpowers:subagent-driven-development` ran the tasks, its final review is round 1. Later rounds review only the latest fix and the code it touches. The reviewer sets each finding's severity (Critical counts as High, Important as Medium, Minor as Low); the fixing session never re-rates.
5. Check each finding against the code before acting (`superpowers:receiving-code-review`). Close each Medium or High finding exactly one way: a real bug gets a failing test, a root-cause fix and a passing test; a wrong finding is rejected with evidence; a finding whose fix would change the design gets the smallest fix inside the design, or is parked. To park a finding, add a line under `## Parked findings` at the end of the plan (create the section if needed): `- Phase <id>: <finding>, <file:line>. Decision: <what>; why: <why>; cost if wrong: <cost>.` A security finding is never parked: when its fix would change the design, that is a stop reason.
6. Repeat steps 4–5 until no Medium or High finding remains. There is no round cap, including subagent-driven-development's per-task limit. If the same problem returns after a fix, or three fixes for one problem fail, stop patching and question the design (`superpowers:systematic-debugging`) without first waiting to discuss it. If the design is the cause, or the root cause still cannot be fixed, park the finding as step 5 does; a fixing phase fixes it right after this phase merges. A stuck security finding is a stop reason. List Low findings without looping on them; the end-of-phase report asks the maintainer to fix or skip each one.
7. For any failing test or unexpected behavior, find the root cause before fixing it (`superpowers:systematic-debugging`), then return to step 2.
8. Prove the phase is ready (`superpowers:verification-before-completion`): run the done-check, if any, and the full unit and integration suites, read the output, and claim only what it shows. If anything fails, go to step 7.
9. Run the code review and the security review once each on the final head, on the phase's base..head range only (in Claude Code, `/code-review high --max-findings all` and `/security-review`; in other hosts, an equivalent independent review). Name the range as each review's target; when a review cannot take it, would skip files in it (such as documentation that `/security-review` skips), or returns a result that cites nothing from it, run its procedure in a fresh read-only subagent on a saved diff of the range, with every changed file in scope. Wait for each result. Close every confirmed finding as step 5 does, Low included, and every security finding at any severity. A fix, including a line added under `## Parked findings`, is a commit that goes through steps 2–8: step 4 reviews only that commit, and the security review runs again on its diff only; the code review does not run again. Record what each review saw: the head it read, and each fix range with its reviewer.
10. Deliver the branch as the repository's rules define (for a plan branch, a PR into that branch). Never merge locally into a protected or plan branch. Push and open a PR only when the repository's rules or the maintainer authorize it; otherwise stop and report that the branch is ready. List parked findings first in the code review comment, and track each as the repository's rules allow. A later commit, base change or conflict fix goes through steps 2–8 on that change only, and the security review runs on that change only (targeted as step 9 says), unless the PR targets the default branch or the repository's rules require both full reviews again; after a rebase, the change is what `git range-diff` shows, and after a base merge, what `git show --remerge-diff` shows; save that output and give each review the saved copy as its target. Do not run `superpowers:finishing-a-development-branch`. When a finding was parked, print this design-update prompt before the next phase's prompt (or alone, after the last phase), and mark the next phase's prompt as waiting for the new report: "Design update after Phase <id>: brainstorm the parked findings in the plan's `## Parked findings` with the maintainer, update the spec and plan with a fixing phase and add `Fixing task: Task <n>.` to each entry, validate the remaining phases as a phase-only validation, then land the revised plan and spec as the repository's rules define (for a plan branch, a docs PR into that branch). Do not start the next phase."

Stop reasons: ask the maintainer only when the next step is destructive, is a security-sensitive action (such as changing access rules or secret handling; not every step of a security-sensitive phase), needs an approval or authorization not already given (such as a merge, an install or another outside effect), or the plan is too broken to follow (including an environment that cannot run a required check). The stops in steps 1, 5 and 6 are cases of these: a design update, or a design change for a security finding, needs the maintainer's approval, and any further fix of a stuck security finding is a security-sensitive action. Otherwise decide, record the decision and continue.

A docs-only phase skips step 2's test-first rule. Its step 9 runs the reviews the repository's rules require for docs-only changes.

## Global Constraints

- No renderer, report format or `context.json` change (spec M4, non-goals). `test_legacy_output_is_frozen` and `test_v4_saved_output_is_frozen` digests are never re-pinned.
- Do not edit merged plans and specs (`2026-11-12-one-review-workflow.md`, `2026-11-11-one-review-workflow-design.md`, `2026-11-05-review-loops-without-revalidation-design.md`) or the released 0.7.0 `CHANGELOG.md` entry.
- The block marker stays exactly `<!-- phase-workflow: 2 -->` (spec M1).
- Every task here is wording-only, so each skips the test-first rule (one review spec D2; `AGENTS.md`: "Do not test wording for its own sake"). Each task's check is the grep and the repository commands below.
- Full copies keep every condition of the rules they already carry and do not grow to carry the whole home; pointers name the home and the rule and do not restate its conditions (spec section 5).
- Cite edits by quoted text, not line numbers.
- Markdown uses placeholders, never home-directory paths. Shipped text is neutral and professional. No private repository names or private rules.
- `validate-plan` stays explicit-only: `disable-model-invocation: true` and `allow_implicit_invocation: false`, checked by hand.
- Shared strings, spelled exactly:
  - Accepted line: `Accepted: <reason> (maintainer, <date>).`
  - Fixing-task line: `Fixing task: Task <n>.`
  - Boundary line: `Boundary tasks: Task <n> approved without integration tests; Task <m> deferred (maintainer, <date>).`
  - Swap line: `Replaced on <date>: workflow steps only, no scope change.`
  - Code review command: `/code-review high --max-findings all`
  - Saved range diff: `git diff --no-color --no-ext-diff --no-textconv --text <base>..<head>`
  - Rebase change: `git diff --no-color --no-ext-diff --no-textconv --text <old-base>..<old-head>`, then the same command for `<new-base>..<new-head>` appended to the same file; `<old-base>` is `git merge-base <old-head> <new-base>`
  - Base-merge change: `git show --remerge-diff --no-color --no-ext-diff --no-textconv --text`

## Review Focus

1. **A plan validated before this change (block marker 2, older wording) runs its next phase.** Expected: it follows its own copy of the block; no swap PR is asked for, and `AGENTS.md`'s marker check passes. Covered by Task 1 step 1 (intro), Task 6 step 3 and the `Older Phase workflow` row (Task 4).
2. **The maintainer accepts every parked finding, so no new report exists.** Expected: the next phase's step 1 lets the accepted entries through, and validation counts them as settled. Covered by Task 1 (steps 3 and 6: block steps 1 and 10), Task 3 (`SKILL.md` coverage and template note) and the `Parked finding` row (Task 4).
3. **Two fixes during validation's final reviews, or an answer edit after a fix.** Expected: each security review reads only text no earlier security review read, from the last kept copies. Covered by Task 2 (Inputs item 3) and the `Second fix in validation's final reviews` row (Task 4).
4. **A docs PR gets a second push after its reviews were posted.** Expected: each review covers only what changed since the `Head:` its last posted review named, in any file; a PR into `main` still gets both full reviews. Covered by Task 2 ("Reuse on the docs PR"), Task 6 step 1 and the `Docs-PR review` row (Task 4).
5. **The text to paste, once pasted into a user's `AGENTS.md`.** Expected: no sentence points back at the rules it sits in, and no docs-only default is claimed. Covered by Task 5 step 3 and its grep.

## Coverage

| Spec decision | Task |
|---|---|
| M1 marker and swap check | Task 1 (steps 1 and 3), Task 3 (template), Task 4, Task 5, Task 6 |
| M2 push to a docs PR | Task 2, Task 4, Task 5, Task 6 |
| M3 accepted parked finding | Task 1 (steps 3, 4 and 6), Task 3, Task 4, Task 5, Task 6 |
| M4 no renderer change, explain the column | Task 5 |
| M5 validation answers (D1–D4) | Task 1 (steps 3, 4 and 6), Task 2 (step 4), Task 3 (step 1), Task 4, Task 5 (step 1) |
| P1 one home | Tasks 3, 5 and 6 (pointers), Task 4 and Task 5 step 3 (aligned copies) |
| P2 hand-offs, P3 older pause sentence, P5 step 9 Low, P6 security Low, P7 saved diffs | Task 1, Task 4 |
| P4 swap-PR approvals | Task 1 (step 3), Task 4, Task 5, Task 6 |
| P8 last reviewed copy, P9 review gaps, P12 repository rules win | Task 2, Task 3 (`SKILL.md` item 8), Task 4 |
| P10 stuck post-answer finding | Task 3, Task 4 |
| P11 done-check lines | Task 3, Task 4, Task 5 |
| P13 Markdown in security reviews, P14 `/code-review` settings, P15 marker check | Task 6 |
| P16 text to paste | Task 5 |
| Section 6 wording fixes | 65-L1, 65-L5, 65-L6: Task 2; 65-L3, PA3-L5: Task 3; 65-D16: Task 4; 66-13 to 66-15, 66-19, 66-20: Task 5; 67-2: Task 6 |

## Delivery

- Plan branch `plan/one-review-followup`, milestone "One review workflow follow-up". `AGENTS.md` governs branches, reviews and merges.
- Proposed phases (validation sets the final grouping): **P1** Tasks 1–3 (skill text), **P2** Tasks 4–5 (evaluation and site), **P3** Task 6 (repository rules). All three are docs-only.
- **This plan runs under the rules in force at `main` 100f4ab.** Task 6 changes `AGENTS.md` last, so no phase runs under half-changed rules. Each phase follows this plan's own Phase workflow section, which Task 1 does not change (a plan keeps the copy it has, spec M1).
- **Security reviews of this plan's own PRs** run the `/security-review` procedure in a fresh read-only subagent on a saved diff of the PR range, with every changed file in scope, Markdown included.
- **Validated with `validate-plan` 0.7.0,** which added the marker-2 block above. An older version would have added the nine-step block, and `AGENTS.md` would then require a swap PR before P1. This plan's block has no `Accepted:` rule: if the maintainer accepts a parked finding during this plan, the design-update docs PR swaps in the block from the plan branch's `references/phase-workflow.md` (spec M1). Until P3 lands, that docs PR, once merged with both reviews passed, is the reconciliation for the swapped block and the `Accepted:` entries it adds only; any other plan, spec or approval change in it still needs reconciliation.
- **The triage appendix is a record of inputs, not a rule.** On the docs PR it is an other changed file: a review finding on its wording is closed as history, not fixed; only a wrong current-text quote that a task relies on is fixed.
- **No in-flight plans in this repository:** `git ls-remote --heads origin 'plan/*'` returned only `plan/one-review-workflow`, which is merged into `main`.
- Text inside a fenced block below is file content. A `## Phase workflow` line inside a fence is not a section of this plan.
- Every `git commit` runs in the same command as `git branch --show-current`, and stops if the branch is not the expected phase branch. Task commit messages end with `Plan: docs/superpowers/plans/2026-11-13-one-review-followup.md`, `Phase: <P1–P3>`, `Task: <n>`, then `Co-Authored-By:`, with no blank line between them. The commit blocks below show only the subject.
- Commands:
  - **UNIT:** `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py'`
  - **PACKAGE:** `python3 scripts/check_package.py`
  - **DEMO:** `python3 scripts/demo.py --output "$(mktemp -d)/demo"`
  - **SITE:** `cd site && npm ci && npm test && npm run build`
- Release: a separate release PR after the plan-to-`main` merge, as `AGENTS.md` "Releases" says. The version number is the maintainer's call then.

---

### Task 1: The Phase workflow block

**Files:**
- Modify: `skills/validate-plan/references/phase-workflow.md`

**Interfaces:**
- Consumes: none.
- Produces: the block's step 1 swap and accepted-entry checks, step 2's `Boundary tasks:` sentence, step 9 and step 10 wording, and the stop-reasons sentence that Tasks 3–6 point to or copy.

- [ ] **Step 1: Replace the intro paragraph**

Replace the paragraph that starts `Validation copies the block below into the plan once` with:

```text
Validation copies the block below into the plan once, near the top, only when the plan has no `## Phase workflow` heading. Copy it from `## Phase workflow` to the docs-only sentence, unchanged. The marker line `<!-- phase-workflow: 2 -->`, under the block's heading, tells this block from the older nine-step block, which has no marker. The marker number changes only when a step or a stop reason is added, removed or renumbered; any other change keeps it, and a plan keeps the copy of the block it has. A plan on the older block keeps it, and its phase prompts keep the older pause sentence.
```

- [ ] **Step 2: Add the hand-off sentence (P2)**

In the block's opening paragraph, after the sentence that ends `` each implementer subagent loads `superpowers:test-driven-development` and `superpowers:systematic-debugging`. ``, insert:

```text
Where a loaded skill hands off to branch finishing, do not follow that hand-off; continue with the next step of this workflow.
```

- [ ] **Step 3: Replace step 1's parked-finding and swap sentences (M1, M3, P4)**

In step 1, replace everything from `If the plan has a `## Parked findings` section` to the end of the step (`needs reconciliation.`) with:

```text
If the plan has a `## Parked findings` section that lists a finding from an earlier phase missing from `revised-plan.md` in the report's run directory, and the entry has no `Accepted:` line, the design update (step 10) has not run: stop and say so. Compared with `revised-plan.md` and `revised-spec.md`, these differences are expected: earlier phases merged into the plan branch, ticked task checkboxes (`- [ ]` to `- [x]`), entries added under `## Parked findings` (and its heading, if new), each with an `Accepted: <reason> (maintainer, <date>).` line, with no other change to that section, and a swapped block. A `Replaced on <date>` line under the `## Phase workflow` heading marks a swapped block; that swap is expected when it changes nothing outside that section and the section carries the marker. Lines under `Replaced on <date>`, such as a `Boundary tasks:` line, are part of the swap. Any other change, or a swap without the marker, needs reconciliation.
```

Then at the end of step 2, after `skip the test-first rule.`, insert (R1-9):

```text
A task that the `Boundary tasks:` line approves without integration tests skips the integration test; a task it defers is not built until the maintainer schedules it.
```

- [ ] **Step 4: Edit steps 5 and 6 (P6, M3)**

1. In step 5, after `A security finding is never parked: when its fix would change the design, that is a stop reason.`, insert: ``Only the design update (step 10) adds an `Accepted:` line to a parked entry, on the maintainer's choice, and never to a security finding.``
2. In step 6, replace `park the finding as step 5 does; a fixing phase fixes it right after this phase merges.` with `park the finding as step 5 does; the design update (step 10) then fixes it in a fixing phase or records the maintainer's acceptance.`
3. In step 6, after `the end-of-phase report asks the maintainer to fix or skip each one.`, insert:

```text
A security finding is closed at any severity, Low included, and never listed for fix or skip.
```

- [ ] **Step 5: Edit step 9 (P5, P7)**

1. Replace `run its procedure in a fresh read-only subagent on a saved diff of the range, with every changed file in scope.` with `` run its procedure in a fresh read-only subagent on a saved diff of the range (`git diff --no-color --no-ext-diff --no-textconv --text <base>..<head>`), with every changed file in scope. ``
2. Replace `Close every confirmed finding as step 5 does, Low included, and every security finding at any severity.` with `Close every confirmed finding as step 5 does, Low included, and every security finding at any severity; a non-security Low finding whose fix would change the design is not parked but listed for the maintainer to fix or skip, as step 6 lists Lows.`

- [ ] **Step 6: Edit step 10 (P7, M3)**

1. Replace ``after a rebase, the change is what `git range-diff` shows, and after a base merge, what `git show --remerge-diff` shows;`` with ``after a rebase, the change is what two saved diffs show together, `git diff --no-color --no-ext-diff --no-textconv --text <old-base>..<old-head>` and then the same command for `<new-base>..<new-head>` appended to the same file, where `<old-base>` is `git merge-base <old-head> <new-base>` (`git range-diff` can show changed Markdown as unchanged); and after a base merge, what `git show --remerge-diff --no-color --no-ext-diff --no-textconv --text` shows;`` (D4)
2. Replace `and mark the next phase's prompt as waiting for the new report:` with `and mark the next phase's prompt as waiting for the design update, and for the new report's prompts when a finding gets a fixing phase:`
3. Replace the quoted design-update prompt, from `"Design update after Phase <id>:` to `Do not start the next phase."`, with:

```text
"Design update after Phase <id>: brainstorm the parked findings in the plan's `## Parked findings` with the maintainer. For each one the maintainer accepts, add `Accepted: <reason> (maintainer, <date>).`; for the others, update the spec and plan with a fixing phase, add `Fixing task: Task <n>.` and validate the remaining phases as a phase-only validation. Land the changes as the repository's rules define (for a plan branch, a docs PR into that branch). Do not start the next phase until they land."
```

- [ ] **Step 7: Add the older-pause sentence to the stop reasons (P3)**

After the stop-reasons paragraph's last sentence, `Otherwise decide, record the decision and continue.`, insert in the same paragraph:

```text
When a phase prompt carries the older pause sentence, these stop reasons govern.
```

- [ ] **Step 8: Check**

Run: `grep -c 'phase-workflow: 2' skills/validate-plan/references/phase-workflow.md`
Expected: `2` (the intro and the marker line).
Run: `grep -n -E 'hands off to branch finishing|Accepted:|Boundary tasks:|never listed for fix or skip|--no-ext-diff|waiting for the design update|older pause sentence, these stop reasons' skills/validate-plan/references/phase-workflow.md`
Expected: the hand-off phrase in the opening paragraph; `Accepted:` in steps 1, 5 and 10; `Boundary tasks:` in steps 1 and 2; `never listed for fix or skip` in step 6; `--no-ext-diff` in step 9 and step 10; `waiting for the design update` in step 10; the older-pause sentence in the stop-reasons paragraph. No other line.
Run: UNIT, PACKAGE.
Expected: both pass.

- [ ] **Step 9: Commit**

```bash
git add skills/validate-plan/references/phase-workflow.md
git commit -m "Settle the open Phase workflow questions"
```

### Task 2: Validation reviews

**Files:**
- Modify: `skills/validate-plan/references/validation-reviews.md`

**Interfaces:**
- Consumes: none.
- Produces: Inputs item 3 ("Last reviewed copy"), the review-gap rule and the docs-PR push rule that Tasks 3–6 point to.

- [ ] **Step 1: Edit Inputs item 2 and add item 3 (P8, 65-L1)**

1. Replace `Each command exits 1 because the files differ; that is expected. Write `fix-<n>.diff`, `answer-edits.diff` and `answer-fix-<n>.diff` the same way, with `git diff --no-index` and these four flags, the spec diff appended to the plan diff, so color, external diff tools, text conversion and binary attributes cannot alter the saved text.` with:

```text
Run the two commands separately, not joined with `&&`: each exits 1 because the files differ, which is expected, and `&&` would skip the spec. Write every other saved diff in this file with these four flags, using `git diff --no-index` when it compares two files and appending the spec diff to the plan diff, so color, external diff tools, text conversion and binary attributes cannot alter the saved text.
```

2. After item 2, add:

```text
3. **Last reviewed copy.** Each time the security review reads text, keep the copies it read; the next security review reads only the diff from those kept copies to the current copies, written as item 2 says. Final-review fixes keep `final-plan-<n>.md` and `final-spec-<n>.md` and write `fix-<n>.diff`. Answer edits keep `post-answer-plan-<n>.md` and `post-answer-spec-<n>.md` and write `answer-edits.diff`, then `answer-fix-<n>.diff`. `<n>` counts up from 1 in each family, and every later fix, including a second fix found while reviewing a fix, takes the next number. The unnumbered names, such as `final-plan.md` and `post-answer-plan.md`, always mean the current copy. When a second fix comes before the security review of the first, keep each fix's copies as it is made; the next security review still reads the diff from the copies the last security review read, so it covers both fixes.
```

- [ ] **Step 2: Add a Limits line to the brief (65-L5)**

Replace `Return the findings as the final message: severity, document and section, evidence and the smallest fix.` with `` Return the findings as the final message: severity, document and section, evidence and the smallest fix, then a `Limits:` line naming each lookup made or skipped and anything not read. ``

- [ ] **Step 3: Point "Closing findings" at item 3 (P8)**

Replace `After a fix, first keep the reviewed copies as `final-plan-<n>.md` and `final-spec-<n>.md`, save the fixed documents as new `final-*.md` copies, record their hashes and write `fix-<n>.diff` (`git diff --no-index` from each kept copy to its new copy, the spec diff appended to the plan diff; each command exits 1 when the files differ).` with:

```text
After a fix, keep the reviewed copies, save the fixed documents as the new `final-plan.md` and `final-spec.md`, record their hashes and write `fix-<n>.diff`, as Inputs item 3 says. A finding raised while a fix is reviewed is closed the same way, with the next number.
```

Then replace `a fresh reviewer reads the new `final-*.md` copies, never the live files,` with `a fresh reviewer reads the new `final-plan.md` and `final-spec.md`, never the live files,`, and `The last `final-*.md` copies are the documents the report records:` with `The last `final-plan.md` and `final-spec.md` are the documents the report records:`.

- [ ] **Step 4: Replace "When a review cannot run" (P9)**

Replace that section's paragraph with:

```text
If a review cannot run at all (no command and no delegation), whether one of the final reviews or a security review of the answer edits, record the gap in section 7 and in the watch list, mark in section 7 which text that review did not cover, and continue. Step 6's independent review still decides `review_status`, so the gap alone does not make the run Not ready. A security review of the answer edits that could not run is not a pass, so end-of-run item 8 leaves the hashes unrefreshed and the report's prompts stay historical. After a gap in the final reviews, the docs PR runs only the missing review itself, on the full plan and spec plus any other changed files, as "Reuse on the docs PR" says; the other review is reused when its own conditions there hold.
```

- [ ] **Step 5: Point "After end-of-run answers" at item 3 (P8)**

Replace everything from `run the security review once, as above, on the answer edits it has not read:` to the end of the sentence that ends `` as `post-answer-plan-<n>.md` and `post-answer-spec-<n>.md`. `` with:

```text
run the security review once on the answer edits it has not read, as Inputs item 3 says: the first time on `answer-edits.diff`, written from `revised-plan.md` and `revised-spec.md` to `post-answer-plan.md` and `post-answer-spec.md`; later on `answer-fix-<n>.diff`, written from the last kept copies to this round's copies. Keep the copies each security review read before end-of-run item 8 makes the next round's copies.
```

- [ ] **Step 6: Edit "Reuse on the docs PR" (M2, P9, P12, 65-L6)**

First replace `A plan's docs PR reuses both results only when it changes only the plan and spec, both hash to the final values in `context.json`, and section 7 records what each review read. It still posts` with ``A plan's docs PR reuses a review's result only when it changes only the plan and spec, both hash to the final values in `context.json`, and section 7 records what that review read and marks none of the final text as uncovered by it. It still posts``, so a review that missed the answer edits is never reused while the other review still can be. Then replace from `Otherwise each review runs once:` to the end of the section with:

```text
A review that is not reused runs once: on what differs from the text it read, when its saved copy still matches the recorded hash, or on the full plan and spec when it does not or when section 7 records a gap for that review; either way plus any other changed files, with every changed file in scope. After a new push to a docs PR that does not target the default branch, each review runs once on what changed since the head that its last posted review named in `Head:`, in the plan, the spec and any other file. Count only a review posted by the account that runs and records these reviews, never a comment from anyone else. When that head is not an ancestor of the PR head, as after a rebase or force push, each review runs once on the full plan and spec, plus any other changed files. A docs PR into the default branch gets both full reviews again. The security review runs its procedure in a fresh read-only subagent on a saved diff that holds what it reviews: the differing text or the PR head's plan and spec as added text, plus the PR's base..head diff of the other changed files; or, after a new push whose named head is an ancestor of the PR head, the diff from that head to the PR head; all written with Inputs item 2's flags. These rules are the minimum: when the repository's rules require more, such as a full-plan review on every docs PR, the repository's rules win. A finding left as a pending approval stays open in the posted review until the maintainer settles it.
```

- [ ] **Step 7: Check**

Run: `grep -n -E 'final-\*\.md|post-answer-\*\.md' skills/validate-plan/references/validation-reviews.md`
Expected: no output.
Run: `grep -c 'Inputs item 3' skills/validate-plan/references/validation-reviews.md`
Expected: `2` or more.
Run: UNIT, PACKAGE.
Expected: both pass.

- [ ] **Step 8: Commit**

```bash
git add skills/validate-plan/references/validation-reviews.md
git commit -m "Give validation reviews one copy rule and a push rule"
```

### Task 3: SKILL.md, the handoff template and the report contract

**Files:**
- Modify: `skills/validate-plan/SKILL.md`
- Modify: `skills/validate-plan/handoff-template.md`
- Modify: `skills/validate-plan/references/report-contract.md`
- Modify: `skills/validate-plan/references/html-report.md`

**Interfaces:**
- Consumes: Task 1 step 3 (accepted entries, swap check); Task 2 (review gaps, item 3).
- Produces: none.

- [ ] **Step 1: Edit `SKILL.md`**

1. Permission line (69-9): in the sentence that starts ``Running `/code-review` at the typed level `high` ``, replace ``and `/security-review`, as`` with ``and running `/security-review`'s procedure in a fresh read-only subagent, as``. The link after it stays.
2. Coverage (M3): replace ``each entry must name its fixing task (`Fixing task: Task <n>.`), and that task must exist in the plan; an entry without one is an implementation blocker`` with ``each entry must name its fixing task (`Fixing task: Task <n>.`), and that task must exist in the plan, or carry the maintainer's acceptance (`Accepted: <reason> (maintainer, <date>).`); an entry with neither is an implementation blocker``
3. Revise (PA1-L7): replace `The block grants no permission: its review and delivery steps follow the repository's own rules.` with `Apart from step 1's worktree consent, the block grants no permission: it types its own reviews for code phases (step 9), and pushing, opening a PR and merging follow the repository's rules (step 10).`
4. End-of-run item 8 (P9, P10, PA3-L5, M5): replace `and the security review of the answer edits that read this round's copies (` with `and the security review that read this round's answer edits (`, keeping the link that follows. Then, after `Any PLAN or SPEC edit after that round needs another round.`, insert `A finding still open under step 6's stuck rule is a finding left to fix, and a security review of the answer edits that could not run is not a pass; in either case the hashes are not refreshed.`
5. Done-check (P11): replace `Write one done-check line per phase in section 8,` with `Write one done-check line in section 8 for each phase that gets a phase prompt (none in a Not ready report, and none for a waiting phase),`
6. Post-answer review (P8): replace ``reading the `post-answer-*.md` copies made and checked under item 8`` with ``reading `post-answer-plan.md` and `post-answer-spec.md`, made and checked under item 8``

- [ ] **Step 2: Edit `handoff-template.md` (M1, M3, 65-L3)**

1. Replace ``- **Plan whose Phase workflow has no `<!-- phase-workflow: 2 -->` marker** (an older block):`` with ``- **Plan whose Phase workflow has no `<!-- phase-workflow: 2 -->` marker line under its heading** (an older block):``
2. In "Expected changes between phases", replace ``and treat only `- [ ]` to `- [x]` changes, and a Phase workflow section that, apart from a `Replaced on <date>` line under its heading, matches the block in validate-plan's `references/phase-workflow.md`, as expected.`` with:

```text
and treat only these as expected: `- [ ]` to `- [x]` changes; a `Replaced on <date>` swap that changes nothing outside the `## Phase workflow` section and keeps the `<!-- phase-workflow: 2 -->` marker; and entries added under `## Parked findings` (and its heading, if new), each with an `Accepted:` line, with no other change to that section.
```

3. Replace the quoted note, from `` `Between phases, earlier phases merged`` to its closing backtick, with:

```text
`Between phases, earlier phases merged into the plan branch, ticked task checkboxes, a Replaced on <date> swap that changes only the Phase workflow section and keeps its marker, and accepted parked findings are expected; compare the plan and spec with revised-plan.md and revised-spec.md in this run directory and reconcile any other change first.`
```

- [ ] **Step 3: Edit `report-contract.md` (P11) and `html-report.md` (P8)**

Replace `one unfenced done-check line per phase (SKILL.md, Phase grouping)` with `one unfenced done-check line for each phase that gets a phase prompt (SKILL.md, Phase grouping)`.

In `html-report.md`, replace ``documents, the `post-answer-*.md` copies, replace the earlier ones.`` with ``documents, `post-answer-plan.md` and `post-answer-spec.md`, replace the earlier ones.``

Then in `html-report.md` replace these three lines (R1-11), which wrap as shown:

```text
when true; `security_review` marks a security-sensitive phase for review focus, and on an
older Phase workflow block, or with none, a flagged code phase gets a security review too,
as SKILL.md "Phase grouping" says), and `status` `ready` or `waiting` (with `waits_for` when waiting).
```

with:

```text
when true; `security_review` marks a security-sensitive phase for review focus, and SKILL.md
"Phase grouping" says when a phase gets a security review), and `status` `ready` or `waiting`
(with `waits_for` when waiting).
```

- [ ] **Step 4: Check**

Run: `grep -rn -E 'matches the block in validate-plan|done-check line per phase|final-\*\.md|post-answer-\*\.md|flagged code phase gets a security review' skills/`
Expected: no output.
Run: UNIT, PACKAGE, DEMO.
Expected: all pass (`test_v5_section8_accepts_done_check_lines` unchanged).

- [ ] **Step 5: Commit**

```bash
git add skills/validate-plan/SKILL.md skills/validate-plan/handoff-template.md skills/validate-plan/references/report-contract.md skills/validate-plan/references/html-report.md
git commit -m "Point validation text at the settled review rules"
```

### Task 4: Evaluation rows

**Files:**
- Modify: `docs/evaluation.md`

**Interfaces:**
- Consumes: Tasks 1–3 text.
- Produces: none. Each row states expected behavior in full; it never points at the file it checks.

- [ ] **Step 1: Replace these rows' expected-behavior cells**

| Row | New expected behavior |
|---|---|
| Drift after review | `When the plan or spec changes after the report, or Git state or approvals change, the historical warning says to reconcile the change before building or validate the changed scope again; it names no run number, run limit or review rounds; a same-run answer edit that passed the post-answer review and the security review of the answer edits is not drift; a security review of the answer edits that could not run leaves the prompts historical` |
| Answer edit reviewed | ``The changed tasks rehearsed again in a new worktree, at a path not used before in the run, that is then removed with no other worktree touched; a fresh reviewer given `post-answer-plan.md` and `post-answer-spec.md` and the answers as settled; `revised-*.md` and the changed `sha256` replaced from those copies only after the security review of the answer edits leaves no finding to fix (a security review that could not run leaves them unchanged and the prompts historical); current prompts with copy buttons; section 7 shows the rehearsal and the review`` |
| Docs-PR review | ``A plan's docs PR reuses the validation run's code and security reviews, each posted with a `Reused:` line naming the hash its review read and the final hash and `Scope:` lines naming what covered any difference, only when it changes only the plan and spec, both hash to the report's final values and section 7 records what each review read and marks none of the final text as uncovered by it; a review that could not run in validation is run on the docs PR on the full plan and spec, and the other is still reused when its conditions hold; otherwise each review runs once on what differs from the text it read, or on the full plan and spec, plus any other changed files; after a new push to a docs PR that does not target the default branch, each review covers only what changed since the `Head:` its last posted review named, in any file (a review the reviewing account posted; the full plan and spec, plus any other changed files, when that head is not an ancestor of the PR head), while a docs PR into the default branch gets both full reviews again; the security review runs as its procedure in a read-only subagent on a saved diff; repository rules that require more win; a finding whose fix would change a security or privacy boundary, a permission or an external action goes to the maintainer and stays open in the posted review until the maintainer settles it; a finding that only disagrees with a recorded decision is rejected with that decision as evidence. A docs-only phase PR gets the reviews the repository's rules require (in this repository, the code and security reviews once each on its final head, typed and targeted as step 9 of the current Phase workflow block types and targets them for a code phase)`` |
| Implementation handoff | `The implementing agent continues through passing steps and reviews without asking to continue; it pauses only for the Phase workflow's stop reasons (a destructive step, a security-sensitive action, an approval or authorization not already given, or a plan too broken to follow; with an older block or none, a required approval or an unfixable failure; after a block swap, the stop reasons govern a prompt that carries the older pause sentence), stops at the end of its phase, prints the next phase's prompt when the report has one, and does not start it` |
| Done-check | ``Section 8 has one unfenced `Done-check, Phase <id>:` line for each phase that gets a phase prompt, before the prompts, naming only tests that exist once that phase is done, plus the full suites; a Not ready report and a waiting phase have none; it is never counted as a prompt`` |
| Parked finding | ``A non-security Medium or High finding whose fix would change the design, or that stays stuck, is recorded under the plan's `## Parked findings`, listed first in the code review comment, and followed by a design-update prompt before the next phase's prompt; the next phase session stops while the plan lists an entry the report's `revised-plan.md` lacks and that has no `Accepted:` line; an entry the maintainer accepted (`Accepted: <reason> (maintainer, <date>).`) lets the next phase start without a new report; a security finding is never parked or accepted; validation reports an entry with neither `Fixing task: Task <n>.` nor `Accepted:` as an implementation blocker (Not ready)`` |
| Older Phase workflow | ``A plan whose block has no `<!-- phase-workflow: 2 -->` marker keeps its block, and its phase prompts keep "Pause only for required approvals or unfixable failures."; a plan with the marker keeps its own copy of the block, whatever wording the installed block has, and needs no swap unless its step 1 has no `Accepted:` rule and a parked finding is accepted: then the docs PR that adds the `Accepted:` line swaps in the current block; a plan swapped under validate-plan 0.7.0 compares its Phase workflow section with the installed block, so after an upgrade its next phase stops at step 1 until a docs PR swaps in the current block again`` |
| Change after a phase PR opens | ``A later commit, base change or conflict fix on a phase PR gets a review of that change and a security review of that change, not both full reviews (steps 2–8, then the security review targeted as step 9 says, after a rebase saved as two `git diff --text` outputs, old base..old head and new base..new head, in one file, and after a base merge as `git show --remerge-diff` output, with color, external diff tools and text conversion turned off), with a `Scope:` line naming it, unless the PR targets the default branch or the repository's rules require both full reviews again; a PR into the default branch gets both full reviews again`` |
| Between-phase changes | ``The next phase session confirms the previous phase is merged, accepts merged phases, ticked checkboxes, a `Replaced on <date>` swap that changes only the Phase workflow section and keeps the marker (with its `Boundary tasks:` line), and parked entries with an `Accepted:` line, and reconciles any other plan, spec or approval change first; an approval recorded after merges leads to a phase-only validation of the remaining phases that keeps their IDs, not a re-render of the old report`` |

In the `Hand edit during the round` row, replace ``Only the reviewed `post-answer-*.md` copy is hashed`` with ``Only the reviewed `post-answer-plan.md` or `post-answer-spec.md` copy is hashed``.

- [ ] **Step 2: Add rows after "Between-phase changes"**

```text
| Branch-finishing hand-off | Under `superpowers:subagent-driven-development` or `superpowers:executing-plans`, the session does not follow the skill's hand-off to `finishing-a-development-branch`; it continues with the next Phase workflow step and still runs steps 8 and 9 |
| Step 9 Low that would change the design | A non-security Low final-review finding whose fix would change the design is listed for the maintainer to fix or skip, not parked; no design-update prompt follows |
| Security Low in the review loop | A Low security finding from steps 4–6 is fixed or rejected with evidence, never listed for fix or skip |
| Stuck post-answer finding | A post-answer finding still open under the stuck rule leaves `revised-*.md` and the hashes unchanged and is an implementation blocker (Not ready) |
| Second fix in validation's final reviews | A finding raised while a final-review fix is reviewed is closed the same way, with the next numbered copies and fix diff; each security review reads only text no earlier security review read |
```

- [ ] **Step 3: Check**

Run: `grep -rn -E 'final-\*\.md|post-answer-\*\.md' skills docs/evaluation.md`
Expected: no output.
Run: `grep -c '^| ' docs/evaluation.md`
Expected: `71` (66 table lines at `main` 100f4ab, plus the five new rows).
Run: PACKAGE, SITE.
Expected: both pass.

- [ ] **Step 4: Commit**

```bash
git add docs/evaluation.md
git commit -m "Align the evaluation rows with the settled review rules"
```

### Task 5: Site pages

**Files:**
- Modify: `site/src/content/docs/phased-implementation.md`
- Modify: `site/src/content/docs/reports-and-handoffs.md`
- Modify: `site/src/content/docs/features.md`
- Modify: `site/src/content/docs/first-run.md`

**Interfaces:**
- Consumes: Tasks 1–3 text.
- Produces: none.

- [ ] **Step 1: Edit `phased-implementation.md` prose**

1. Phase table (M4): replace `whether it is security-sensitive and why (the flag marks where to look hardest; on the current Phase workflow it does not decide whether a security review runs),` with `whether it is security-sensitive and why (the "Security review" column marks where to look hardest; on the current Phase workflow it does not decide whether a security review runs),`
2. Permission (66-7): replace `The block grants no permission: pushing, opening a PR and merging still follow your repository's rules and the maintainer.` with `Apart from the worktree consent in its first step, the block grants no permission: pushing, opening a PR and merging still follow your repository's rules and the maintainer.`
3. Step list item 4 (66-9, P6): replace `When a problem keeps coming back, the session questions the design and parks the finding with a recorded decision instead of patching again; a security finding is never parked.` with `When a problem keeps coming back, the session questions the design instead of patching again, and may park the finding with a recorded decision (the block's step 6 says when). A security finding is never parked, and never skipped as Low.`
4. Step list item 6 (66-20): replace `each fix gets a fresh review and a security review of the fix only.` with `each fix gets a fresh review of the fix and a security review of the fix; the code review does not run again.`
5. Step list item 7 (M3): replace `after a design-update prompt when a finding was parked.` with `after a design-update prompt when a finding was parked. In that design update, you fix each parked finding in a new phase or accept it with a reason.`
6. "After a phase PR opens" (66-2, 66-19): replace the bullet with `` - **After a phase PR opens,** a later commit, such as a CI fix, gets a review of that change and a security review of that change, not both full reviews, unless the PR targets your default branch or your repository's rules require both full reviews again (the block's step 10). A plan's docs PR into a branch other than your default branch reviews only what changed after a push (see below); every other PR gets both full reviews again. ``
7. Saved settings (66-13, 66-14): replace `Phase sessions and docs-PR reviews that follow this page type` with `In Claude Code, validation's final review, phase sessions and docs-PR reviews that follow this page type`
8. Plans already in progress (P3, P4, M1): replace `List any task that crosses a boundary without integration test infrastructure, for the maintainer to approve.` with ``Under it, add a `Boundary tasks:` line with your choice for each task that crosses a boundary without integration test infrastructure: approved without integration tests, or deferred. After the swap, the block's stop reasons govern even where a saved prompt has the older pause sentence. A plan that already has the `<!-- phase-workflow: 2 -->` marker keeps its copy and needs no swap, unless you accept a parked finding and its copy's step 1 has no `Accepted:` rule: then swap in the current block in the same docs PR. Give every swap PR a code review and a security review before it merges, because the next phase trusts its Phase workflow section. A plan swapped under validate-plan 0.7.0 compares that section with the installed block, so after you upgrade the plugin its next phase stops at step 1: swap in the current block again, in a docs PR that gets both reviews.``
9. Between phases (66-6, M3): replace `earlier phases are merged and their task checkboxes are ticked. That is expected.` with `earlier phases are merged and their task checkboxes are ticked. That is expected, and so are a swapped Phase workflow section and parked findings you accepted.`
10. Docs-PR bullet "Otherwise review the difference once" (M2, 66-12, P12): replace the sentence `Each review runs once on what differs from the text it read, or on the whole plan and spec when that text is gone, plus any other changed files.` with `Each review runs once on what differs from the text it read, or on the whole plan and spec when that text is gone, plus any other changed files. After a new push, each review covers only what changed since the head its own last posted review named (counting only reviews the reviewing account posted; the whole plan and spec, plus any other changed files, when that head is not an ancestor of the PR head), unless the PR targets your default branch, which gets both full reviews again. [Validation reviews](https://github.com/snowholt-labs/plan-validation/blob/main/skills/validate-plan/references/validation-reviews.md) gives the targets and saved diffs; your repository's rules win when they ask for more.`
11. Docs-only phase line (66-11): replace `typed and targeted as Phase workflow step 9 types and targets them for a code phase.` with `typed and targeted as step 9 of the current Phase workflow block types and targets them for a code phase.`
12. "Reuse when nothing changed" (P9): replace `both match the hashes in the report and the report records what each review read,` with `both match the hashes in the report and the report records what each review read and marks none of the final text as uncovered,`
13. Final plan-to-main PR bullet (M3): replace `That review also clears the saved action points and checks that every parked finding was fixed.` with `That review also clears the saved action points and checks that every parked finding was fixed or accepted with a reason.`

- [ ] **Step 2: Check `phased-implementation.md` prose**

Run: `grep -n -E 'for the maintainer to approve\.|fix only\.|parks the finding with|parked finding was fixed\.' site/src/content/docs/phased-implementation.md`
Expected: no output.

- [ ] **Step 3: Edit the text to paste (P16, 66-15, 66-18, 66-19, M2, M3)**

Inside the fenced block under "Text for your repository instructions":

1. Replace `A later commit gets a code review and a security review of that change only.` with `A later commit gets a review of that change and a security review of that change, not both full reviews.`
2. Replace `- Between phases, merged earlier phases and ticked task checkboxes are expected.` with ``- Between phases, merged earlier phases, ticked task checkboxes, a `Replaced on <date>` swap that changes only the Phase workflow section and keeps the `<!-- phase-workflow: 2 -->` marker, and parked findings with an `Accepted:` line are expected.``
3. Replace the whole bullet that starts `- Docs-only PRs follow your review rules.` with:

```text
- When the repository requires reviews on a plan's docs PR, it can reuse validation's `/code-review` and `/security-review` results when it changes only the plan and spec, their hashes match the report and the report records what each review read and marks none of the final text as uncovered. When any of these does not hold, review once what differs, plus any other changed files, and after a new push each review covers only what changed since the head its own last posted review named (counting only reviews the reviewing account posted; the full plan and spec, plus any other changed files, when that head is not an ancestor of the PR head; both full reviews again when the PR targets the default branch); in Claude Code, type `/code-review high --max-findings all` and run `/security-review`'s procedure in a subagent on a saved diff so it reads Markdown. Post reused results with a `Reused:` line naming the hash each review read and the final hash, and `Scope:` lines naming what covered any difference. Ask the maintainer about a finding whose fix would change a security or privacy boundary, a permission or an external action; it stays open in the posted review until the maintainer settles it. Reject a finding that only disagrees with a recorded decision, citing that decision.
```

4. Replace `which also clears the saved action points and checks that every parked finding was fixed.` with `which also clears the saved action points and checks that every parked finding was fixed or accepted with a reason.`

Run: `grep -n -E 'follow your review rules|your rules|these rules' site/src/content/docs/phased-implementation.md`
Expected: one hit, the line above the fence that ends `adjust it to your rules:`; no hit inside the text to paste.

- [ ] **Step 4: Edit the other pages (69-9, 66-1, 66-8, P11)**

1. `reports-and-handoffs.md`, validation paragraph: replace `Then `/code-review` and `/security-review` run once each on saved copies of the final plan and spec,` with `` Then the code review (`/code-review` in Claude Code) and the security review (`/security-review`'s procedure, run in a subagent because the command skips documentation) run once each on saved copies of the final plan and spec, ``
2. `reports-and-handoffs.md`, handoff paragraph: replace `whether it is security-sensitive (where review should look hardest),` with `whether it is security-sensitive (the "Security review" column: where review should look hardest, not whether a security review runs),`; replace `a done-check line per phase lists` with `a done-check line for each phase with a prompt lists`; replace `or a plan too broken to follow),` with `or a plan too broken to follow; a plan on an older block, or with none, keeps the older pause sentence),`
3. `features.md`: replace `` and `/code-review` and `/security-review` run once each on the final plan and spec. `` with `` and the code review (`/code-review`) and the security review (`/security-review`'s procedure in a subagent) run once each on the final plan and spec. ``
4. `first-run.md`: replace `` Then it runs `/code-review` and `/security-review` once each on the final plan and spec. `` with `` Then it runs the code review (`/code-review`) and the security review (`/security-review`'s procedure in a subagent) once each on the final plan and spec. ``

- [ ] **Step 5: Check**

Run: PACKAGE, SITE.
Expected: both pass; the site's link check accepts the new link.

- [ ] **Step 6: Commit**

```bash
git add site/src/content/docs/phased-implementation.md site/src/content/docs/reports-and-handoffs.md site/src/content/docs/features.md site/src/content/docs/first-run.md
git commit -m "Point the site pages at the settled review rules"
```

### Task 6: Repository rules

**Files:**
- Modify: `AGENTS.md` (sections "Git workflow" and "Plan work")

**Interfaces:**
- Consumes: Task 1 (step numbers, swap check, accepted entries), Task 2 ("Reuse on the docs PR").
- Produces: none.

- [ ] **Step 1: Edit "Git workflow" (P13, P14, M2, 67-2, 67-3)**

1. In the bullet that starts `- Code and security review means`, replace the parenthesis that starts ``(in Claude Code, `/code-review`, always typed with the level`` and ends `an equivalent independent review)` with:

```text
(in Claude Code, for every PR, including PRs outside a plan and phases of plans on an older block: `/code-review high --max-findings all`, as step 9 of the current Phase workflow block in `skills/validate-plan/references/phase-workflow.md` types it, and `/security-review`; in other hosts, an equivalent independent review). Every security review in this repository covers Markdown, because the repository ships it as a behavioral contract: when `/security-review` cannot take its target, would skip a changed file such as Markdown, or returns a result that cites nothing from it, run its procedure in a fresh read-only subagent on a saved diff of the range that review targets, with every changed file in scope, documentation included, as step 9 of the current block says
```

The replacement ends without a period: the period that follows the old parenthesis ends its last sentence.

2. In the next bullet, replace the sentence that starts `A plan's docs PR reuses the validation run's code and security reviews when it changes only the plan and spec,` and ends `("Reuse on the docs PR" in `skills/validate-plan/references/validation-reviews.md`).` with `` A plan's docs PR reuses the validation run's code and security reviews under the conditions in "Reuse on the docs PR" in `skills/validate-plan/references/validation-reviews.md`, which also says what each review covers when it cannot reuse them and after a new push. `` Then replace `Otherwise each review runs once, typed and targeted as Phase workflow step 9 types and targets them, on what differs from the text it read or on the full plan and spec, plus any other changed files.` with `Each review it runs itself is typed as step 9 of the current Phase workflow block types it, on the target that "Reuse on the docs PR" names.`
3. In the bullet that starts `- Post each review's result`, replace from `After a new push to a phase PR (a fix, base change or conflict fix),` to the end of the bullet with:

```text
After a new push to a phase PR, the change is reviewed as steps 9 and 10 of the current Phase workflow block say, and the new head gets a `## Code review` whose `Scope:` names that change and links the full review, a `## Security review` of that change only, and both statuses. A plan's docs PR into a plan branch, after a new push, follows "Reuse on the docs PR". Every other PR, including every PR into `main`, needs both full reviews again after a new push.
```

4. Replace `with findings fixed, explicitly accepted or parked as the plan's Phase workflow allows` with `with findings fixed, explicitly accepted by the maintainer or parked as the plan's Phase workflow allows`, and `every finding is fixed, explicitly accepted, or parked under` with `every finding is fixed, explicitly accepted by the maintainer, or parked under`, so a review session never accepts a finding itself.

- [ ] **Step 2: Edit the "Plan work" paragraph (P4)**

Replace `that PR lists any task that crosses a boundary without integration test infrastructure, for the maintainer to approve or defer.` with ``that PR records the maintainer's choice for each task that crosses a boundary without integration test infrastructure on a `Boundary tasks:` line under the `Replaced on` line: approved without integration tests, or deferred. A plan with the marker whose Phase workflow step 1 has no `Accepted:` rule gets the same swap in the docs PR that adds an `Accepted:` line.``

- [ ] **Step 3: Edit the "Plan work" bullets (P15, M3)**

1. Replace `Start a phase only after the previous one is merged into the plan branch; confirm this first and stop if it is not. Merged earlier phases and ticked task checkboxes are expected; reconcile any other plan, spec or approval change with the validation report first.` with:

```text
Start a phase only after the previous one is merged into the plan branch, and only when the plan's Phase workflow has the `<!-- phase-workflow: 2 -->` marker (otherwise a docs PR that swaps in, or adds, the current block with a `Replaced on <date>` line comes first); confirm both first and stop if either fails. Merged earlier phases, ticked task checkboxes, a `Replaced on <date>` swap and accepted parked findings are expected, as step 1 of the current Phase workflow block says; reconcile any other plan, spec or approval change with the validation report first.
```

2. Replace `the Phase workflow's review loop and readiness check (steps 4–8),` with `the Phase workflow's review loop and readiness check (steps 4–8 of the current block),`
3. Replace `` names a fixing task that is done. `` with `` names a fixing task that is done or carries an `Accepted:` line. ``
4. Replace each remaining `Phase workflow step 9 types and targets them` with `step 9 of the current Phase workflow block types and targets them`: two places, the docs-only phase PR sentence in "Git workflow" and the bullet that starts `- Run the code review and the security review once each`.

- [ ] **Step 4: Check the whole plan's changes**

Run: `git grep -n -P '/code-review(?! high)' -- AGENTS.md skills/validate-plan/references/phase-workflow.md skills/validate-plan/references/validation-reviews.md`
Expected: no output.
Run: `git grep -n -E 'matches the block in validate-plan|for the maintainer to approve or defer|Phase workflow step 9 types|parked finding was fixed\.' -- AGENTS.md skills site docs/evaluation.md`
Expected: no output.
Run: UNIT, PACKAGE, DEMO, SITE; and `claude plugin validate .` and `claude plugin validate .claude-plugin/plugin.json` when Claude Code is installed.
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add AGENTS.md
git commit -m "Point the repository rules at the settled review rules"
```
