# One Review Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship one review workflow for validated plans: a ten-step Phase workflow block with no round cap, a stuck rule and four stop reasons; validation's own final `/code-review` and `/security-review`; a done-check per phase; parked findings; and the matching evaluation cases, site pages and repository rules.

**Architecture:** Almost all of the change is skill text. The Phase workflow block in `references/phase-workflow.md` becomes the one home for a phase's steps, and a new `references/validation-reviews.md` becomes the one home for validation's final reviews. `SKILL.md`, the report contract, the handoff template, the site and `AGENTS.md` point to them. The renderer does not change: one new test pins that it already accepts unfenced done-check lines in section 8.

**Tech Stack:** Markdown skill text, Python 3.10+ standard library (`unittest`), Astro docs site (`site/`).

**Spec:** `docs/superpowers/specs/2026-11-11-one-review-workflow-design.md`

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

## Global Constraints

- No report format bump, no new `context.json` fields and no renderer changes (spec section 2, non-goals). Versions 1–4 output stays frozen by `test_legacy_output_is_frozen` and `test_v4_saved_output_is_frozen`; never re-pin their digests.
- Do not migrate saved reports or rewrite existing plans and specs, except the one-line note in Task 7.
- Superpowers is never edited, bundled or required. Every step that names a Superpowers skill also states the behavior, so it works without Superpowers and on Codex.
- Phase prompts stay at most 80 words. The new pause sentence has the same 8 words as the old one.
- Validation still never commits, pushes, opens PRs, posts comments, merges, deploys, installs or reads secrets. Running `/code-review` and `/security-review` read-only is the only new action, and only as Task 3 words it. `/code-review` keeps the level and finding limit it types as the user's saved choice (PD6); Task 6 discloses that in `README.md` and the safety page.
- `validate-plan` stays explicit-only: `disable-model-invocation: true` and `allow_implicit_invocation: false`, checked by hand.
- Wording, configuration, version and changelog tasks skip the test-first rule (spec D2); `AGENTS.md` says "Do not test wording for its own sake".
- Markdown uses placeholders such as `<skill-directory>`, never home-directory paths. Shipped text is neutral and professional.
- Cite each edit by quoted text, not line numbers: each edit shifts the lines below it.
- Shared names that several tasks use, spelled exactly:
  - Block marker line: `<!-- phase-workflow: 2 -->`
  - Parked-finding section heading in a plan: `## Parked findings`
  - Done-check line prefix: `Done-check, Phase <id>:`
  - New reference file: `skills/validate-plan/references/validation-reviews.md`
  - New pause sentence: `Pause only for the Phase workflow's stop reasons.`
  - Old pause sentence, kept for older blocks: `Pause only for required approvals or unfixable failures.`
  - Code review command: `/code-review high --max-findings all`

## Review Focus

1. **Section 8 gains unfenced done-check lines.** Expected: the renderer still finds exactly one prompt per ready phase, does not count the lines toward any prompt and shows them above the phase table. Covered by `test_v5_section8_accepts_done_check_lines` (Task 1).
2. **A plan still on the older nine-step block gets a new report.** Expected: its prompts keep the old pause sentence, because the older block has no stop reasons. Covered by the handoff-template variant (Task 4) and the `Older Phase workflow` evaluation row (Task 5).
3. **The maintainer runs a saved phase prompt after a finding was parked.** Expected: step 1 sees a `## Parked findings` entry that the report's `revised-plan.md` lacks and stops, so the redesign cannot be skipped, and a validation run reports an entry without `Fixing task:` as a blocker. Covered by block step 1 (Task 2), Task 3 edit 8 and the `Parked finding` evaluation row (Task 5).
4. **Validation reviews the live plan while the maintainer edits it.** Expected: both final reviews read saved copies with recorded hashes, never the live files. Covered by `validation-reviews.md` (Task 3) and the `Validation's final reviews` evaluation row (Task 5).
5. **`/code-review` typed with no level** reuses the last level typed, which can be `max` or `ultra`. Expected: the places that type it (block step 9, `validation-reviews.md` and the site's text to paste) type `high`, and `AGENTS.md` points to step 9 instead of naming the bare command. Covered by the `/code-review(?! high)` check in Task 7 step 4 for the instruction files; Task 6 step 1 writes the site text.

## Decisions in this plan

The spec leaves these to the plan (section 8). Each is Proposed unless marked otherwise. The maintainer approved PD5 and PD6 on 2026-11-12.

- **PD1 Parked-finding record:** the plan's own `## Parked findings` section, one line per finding, written by the phase that parks it. It survives a fresh session, a squash merge and a PR the maintainer opens. It is committed with the phase's work before step 9, or as a fix that goes through steps 2–8 after it, so no commit follows the reviewed head. The next phase's step 1 compares it with the report's `revised-plan.md`. The design update adds `Fixing task: Task <n>.` to each entry, and the plan-to-`main` review checks that each named task is done. Cost if wrong: plan files gain a section, and in a public repository the finding text is public (it is already public in the PR's comment review).
- **PD2 Block marker:** the HTML comment `<!-- phase-workflow: 2 -->` right under the block's heading. It is invisible when rendered and easy to grep. Cost if wrong: a tool that strips comments makes a new block look older, and the plan gets the old pause sentence, which is the safe fallback.
- **PD3 Validation review targets:** saved copies of the final plan and spec, plus `final-review.diff` that holds both copies as added text. `/security-review` always runs as a briefed subagent on that diff, because it reads only a branch's committed diff and skips documentation files. `/code-review` gets the diff as its target, with the same subagent fallback. Unknown: whether `/code-review` accepts a diff file as a target; the fallback covers both answers.
- **PD4 Review gap:** a final review that cannot run at all is recorded in section 7 and the watch list. It does not make the run Not ready by itself, because step 6's independent review still decides `review_status`. The docs PR then runs that review itself instead of reusing it.
- **PD5 Security column (approved 2026-11-12: explain only):** explain the per-phase `security_review` flag in the docs instead of relabeling the report's "Security review" column. A relabel is a renderer change against the non-goals and would need gating to version 5 output.
- **PD6 Saved `/code-review` settings (approved 2026-11-12: accept and disclose):** typing `/code-review high --max-findings all`, in a phase session or in validation's final review, stores `high` and `all` as the user's saved choice for later manual runs, replacing any level and finding limit saved earlier. Accept it, and tell users on the site page to type their own level and `--max-findings default` on their next manual run. Typing `--max-findings default` instead would still store `high` and would cap findings, against D8's "no cap on the number of findings".
- **PD7 Change range after a rebase or base merge:** the change to review is what `git range-diff <old-base>..<old-head> <new-base>..<new-head>` shows for a rebase, or `git show --remerge-diff <merge-commit>` for a base merge (Git 2.36 or later), not `<old-head>..<new-head>`.
- **PD8 Codex wording:** in other hosts, "an equivalent independent review" is two fresh read-only subagents with the brief in `validation-reviews.md`, one asked for correctness findings and one for security findings.
- **PD9 One home for validation's final reviews:** a new reference file, `validation-reviews.md`, read at step 8, so `SKILL.md` gains pointers, not a long paragraph.
- **PD10 Answer edits:** before end-of-run item 8 copies the reviewed copies over `revised-*.md`, validation writes `answer-edits.diff` and runs the security review once on it.
- **PD11 Release:** minor release 0.7.0, in a separate release PR after the plan-to-`main` merge, as `AGENTS.md` "Releases" requires.

## Coverage

Spec section 7 rows:

| Row | Task |
|---|---|
| P1 block | Task 2 |
| P2 done-check | Task 3 (`SKILL.md` phase grouping), Task 4 (report contract) |
| P3 step 6, P4 step 8, P5 research rules, P6 post-answer loop | Task 3 |
| P7 site page and Docs-PR evaluation row | Task 5, Task 6 |
| P8 handoff template and Implementation handoff row | Task 4, Task 5 |
| P9 superseded note | Task 7 |
| P10 release entry and new evaluation rows | Release follow-up, Task 5 |
| P11 security flag | Task 3, Task 4, Task 6; renderer unchanged (PD5) |
| P12 other site pages | Task 6 |
| A0–A6 `AGENTS.md` | Task 7 |
| A7 | No change: D2 exempts wording tasks |
| S1–S6 Superpowers | No change: the block overrides them |

Spec section 8 items:

| Item | Where |
|---|---|
| Review targets | Task 2 steps 9–10, Task 3, PD3, PD7 |
| Review settings | Task 2 step 9, Task 3, PD6 |
| Review gaps | Task 3, PD4 |
| Delegated briefs | Task 3 |
| Done-check format | Task 1, Task 3, Task 4 |
| Handoff limits | Task 4 |
| Block marker and step 1 check | Task 2, Task 4, Task 7, PD1, PD2 |
| Parked-finding record | Task 2, Task 3, PD1 |
| Security column | PD5 |
| Line references | Global Constraints |
| Release mechanics | Delivery, Release follow-up, PD11 |
| Codex wording | Task 3, PD8 |
| In-flight plans | Delivery, Task 6, Task 7 |
| Evaluation rows | Task 5 |

## Delivery

- Plan branch `plan/one-review-workflow`, milestone "One review workflow". Repository rules in `AGENTS.md` govern branches, reviews and merges.
- Phases: **P1** Tasks 1–4 (test and skill text), **P2** Tasks 5–6 (evaluation and site, docs-only), **P3** Task 7 (repository rules, docs-only). The plan is done when P3 merges. Then come the plan-to-`main` PR and the release.
- **This plan runs under the rules in force today** (Proposed). Its docs PR and phases follow the current `AGENTS.md` and the older Phase workflow block that the installed `validate-plan` (0.6.1) adds. Task 7 changes `AGENTS.md` last, so no phase runs under half-changed rules. Every phase and PR of this plan follows `AGENTS.md` and `site/src/content/docs/phased-implementation.md` as they are on `main` at `2c996d9`, and this plan's own Phase workflow section above, even after P2 changes the site page and P3 changes `AGENTS.md` on the plan branch. Read those rules with `git show 2c996d9:AGENTS.md` and `git show 2c996d9:site/src/content/docs/phased-implementation.md`, not the working copies, which a host may load on its own (`CLAUDE.md` imports `AGENTS.md`), and say so in every subagent brief. The plan-to-`main` PR gets both full reviews under the old and the new rules alike.
- **Security reviews of this plan's own PRs** (docs, phase and plan-to-`main`) run the `/security-review` procedure in a fresh read-only subagent on a saved diff of the PR range, with every changed file in scope, skill and rules Markdown included as a behavioral contract, because the command itself skips documentation files.
- **No in-flight plans in this repository.** `git ls-remote --heads origin 'plan/*'` returned no branch on 2026-11-12, so no plan needs its block swapped (D13). Users' in-flight plans get the swap instructions on the site page (Task 6).
- **The `## Phase workflow` line inside Task 2's code fence is file content, not a section of this plan.** This plan's own Phase workflow section, near the top, is the older nine-step block that validation (0.6.1) added; every phase of this plan follows it.
- Every `git commit` runs in the same command as `git branch --show-current`, and stops if the branch is not the expected phase branch. Task commit messages end with `Plan: docs/superpowers/plans/2026-11-12-one-review-workflow.md`, `Phase: <P1–P3>`, `Task: <n>`, then `Co-Authored-By:`, with no blank line between them. The commit blocks below show only the subject.
- Commands used below:
  - **UNIT:** `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py'` (append `-k <name>` for one test)
  - **PACKAGE:** `python3 scripts/check_package.py`
  - **DEMO:** `python3 scripts/demo.py --output "$(mktemp -d)/demo"`
  - **SITE:** `cd site && npm ci && npm test && npm run build`
- Matching changes to the maintainer's private configuration and private repositories are tracked outside this repository.

---

### Task 1: Pin that section 8 accepts done-check lines

**Files:**
- Test: `skills/validate-plan/scripts/test_render_report.py` (add one method to `ReportTests`, after `test_v5_main_writes_no_rerun_file`)

**Interfaces:**
- Consumes: `render`, `REPORT`, `self.v5_context()` and `self.two_phase(context)` from the existing test module.
- Produces: proof that the line format `Done-check, Phase <id>:` (Tasks 3 and 4) renders without a renderer change.

- [ ] **Step 1: Write the test**

```python
def test_v5_section8_accepts_done_check_lines(self):
    source, context = self.two_phase(self.v5_context())
    lines = ("Done-check, Phase 1: `python3 -m unittest discover -s tests -k one`, then the full unit and integration suites.",
             "Done-check, Phase 2: `python3 -m unittest discover -s tests`, then the full unit and integration suites.")
    source = source.replace("## 8. Fresh-session handoff\n",
                            "## 8. Fresh-session handoff\n" + "\n\n".join(lines) + "\n\n", 1)
    rendered = render(source, context)
    page, handoff, _, _ = rendered
    self.assertEqual([pid for pid, _ in rendered.pairs], ["1", "2"])
    self.assertFalse(any("Done-check" in prompt for _, prompt in rendered.pairs))
    for line in ("Done-check, Phase 1:", "Done-check, Phase 2:"):
        self.assertIn(line, page)
        self.assertLess(page.index(line), page.index('aria-label="Phase plan"'))
    self.assertNotIn("Done-check", handoff)
```

- [ ] **Step 2: Run it**

Run: UNIT `-k test_v5_section8_accepts_done_check_lines`
Expected: PASS on the first run (checked on 2026-11-12 against a scratch copy of the current renderer). This test pins behavior the skill text starts relying on; it is not a new feature. If it fails, do not change the renderer: a renderer change is a spec non-goal, so stop and ask the maintainer (the plan is too broken to follow).

- [ ] **Step 3: Run the full suite**

Run: UNIT
Expected: all tests pass; the frozen-output tests are unchanged.

- [ ] **Step 4: Commit**

```bash
git add skills/validate-plan/scripts/test_render_report.py
git commit -m "Pin that section 8 accepts done-check lines"
```

### Task 2: The new Phase workflow block

**Files:**
- Modify: `skills/validate-plan/references/phase-workflow.md` (replace the whole file)

**Interfaces:**
- Consumes: the shared names in Global Constraints.
- Produces: the marker line, the `## Parked findings` line format, the design-update prompt and the four stop reasons that Tasks 4–7 point to.

- [ ] **Step 1: Replace the whole file with this text**

````markdown
# Phase workflow block

Validation copies the block below into the plan once, near the top, only when the plan has no `## Phase workflow` heading. Copy it from `## Phase workflow` to the docs-only sentence, unchanged. The marker line `<!-- phase-workflow: 2 -->` tells this block from the older nine-step block, which has no marker. A plan on the older block keeps it, and its phase prompts keep the older pause sentence.

```markdown
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
```
````

- [ ] **Step 2: Check the shared names and the old text**

Run: `grep -c -F -e '<!-- phase-workflow: 2 -->' -e '## Parked findings' -e '/code-review high --max-findings all' skills/validate-plan/references/phase-workflow.md`
Expected: a count of at least 4 (the marker twice, the section name, the command).
Run: `grep -n -E 'finishing-a-development-branch' skills/validate-plan/references/phase-workflow.md`
Expected: one line only, step 10's "Do not run".

- [ ] **Step 3: Run PACKAGE**

Expected: passes.

- [ ] **Step 4: Commit**

```bash
git add skills/validate-plan/references/phase-workflow.md
git commit -m "Replace the Phase workflow block with the ten-step workflow"
```

### Task 3: Validation text and its final reviews

**Files:**
- Create: `skills/validate-plan/references/validation-reviews.md`
- Modify: `skills/validate-plan/SKILL.md`
- Modify: `skills/validate-plan/references/plan-reviewer.md`

**Interfaces:**
- Consumes: the shared names in Global Constraints.
- Produces: `validation-reviews.md` with the headings "Inputs", "Commands", "Closing findings", "Record", "When a review cannot run", "After end-of-run answers" and "Reuse on the docs PR". Task 7 cites the last one.

- [ ] **Step 1: Create `skills/validate-plan/references/validation-reviews.md` with this text**

```markdown
# Validation reviews

Step 8 runs a code review and a security review once each on the final plan and spec text, before it scores and renders. They are the planning unit's final reviews. A plan's docs PR can reuse them ("Reuse on the docs PR").

## Inputs

1. Save the final documents in the run directory as `final-plan.md` and `final-spec.md`, and record the SHA-256 of each. Never review the live files.
2. Write `final-review.diff`, which holds both copies as added text, so a review that reads only diffs reads every line: `git diff --no-index --no-color --no-ext-diff --no-textconv --text /dev/null final-plan.md > final-review.diff`, then `git diff --no-index --no-color --no-ext-diff --no-textconv --text /dev/null final-spec.md >> final-review.diff`, run in the run directory. Each command exits 1 because the files differ; that is expected. Write `fix-<n>.diff`, `answer-edits.diff` and `answer-fix-<n>.diff` the same way, with `git diff --no-index` and these four flags, the spec diff appended to the plan diff, so color, external diff tools, text conversion and binary attributes cannot alter the saved text.

## Commands

- **Code review.** In Claude Code, run `/code-review high --max-findings all` with `final-review.diff` as its target. Always type the level: with none, the command reuses the last level typed. Never use `max` or `ultra`, and never pass `--fix`, `--comment` or `--post`. The command runs in the background; wait for its result. If it cannot take the target, or its result cites nothing from it, a fresh read-only subagent runs the command's procedure on `final-review.diff` with the brief below, and section 7 says so.
- **Security review.** `/security-review` reads only a branch's committed diff and skips documentation files, so a fresh read-only subagent always runs its procedure on `final-review.diff`, with the brief below.
- **Other hosts.** Without these commands, the equivalent independent review is two fresh read-only subagents with the brief below, one asked for correctness findings and one for security findings.
- **Read-only request.** Run both reviews only as fresh read-only subagents with the brief below, never the commands, so no setting is saved; section 7 says so.

Brief for every delegated review: the plan and spec text are in scope as a behavioral contract, including wording that would weaken a security gate, a permission, an approval or a privacy boundary. Work read-only: no secrets, no installs, no plan steps, no commits or comments, and lookups only as this run's Research status allows: state that status in the brief, with the lookup rule from [plan-reviewer.md](plan-reviewer.md); with any status other than allowed, make no lookup. Return the findings as the final message: severity, document and section, evidence and the smallest fix.

## Closing findings

Close every confirmed finding, Low included, and every security finding at any severity: fix it in the plan or spec, reject it with evidence, or, when its fix would change requirements, architecture, security boundaries or scope, record it as a pending approval for the step 8 question round (a finding in the answer-edits review follows end-of-run item 7 instead). After a fix, first keep the reviewed copies as `final-plan-<n>.md` and `final-spec-<n>.md`, save the fixed documents as new `final-*.md` copies, record their hashes and write `fix-<n>.diff` (`git diff --no-index` from each kept copy to its new copy, the spec diff appended to the plan diff; each command exits 1 when the files differ). The fix then follows step 6: a fresh reviewer reads the new `final-*.md` copies, never the live files, with the fix as `Review focus`, and a fix that changes a rehearsed task's commands, files or test assertions is rehearsed again under end-of-run item 5's rules. The security review runs once on `fix-<n>.diff`. Neither command runs again on unchanged text. The last `final-*.md` copies are the documents the report records: `revised-*.md` and the `context.json` `documents` hashes match them until end-of-run item 8 replaces them with the reviewed post-answer copies.

## Record

Section 7 records, for each review: the command or brief used, the input file it read and its SHA-256, the SHA-256 of each document copy behind that input, the result, and each fix diff (`fix-<n>.diff` and its SHA-256) with the security review that read it and the step-6 review round that read the fixed copies, and each `answer-fix-<n>.diff` with its SHA-256, its security review and its post-answer round. `context.json` `documents` keeps the final hashes, as before.

## When a review cannot run

If a review cannot run at all (no command and no delegation), record the gap in section 7 and in the watch list, and continue. Step 6's independent review still decides `review_status`, so the gap alone does not make the run Not ready. The docs PR then runs that review itself on the full plan and spec instead of reusing it, plus any other changed files; the security review runs its procedure in a fresh read-only subagent, with every changed file in scope, on a saved diff that holds the PR head's plan and spec as added text, written with Inputs item 2's flags, plus the PR's base..head diff of its other changed files.

## After end-of-run answers

When answers change PLAN or SPEC, the post-answer review (end-of-run item 6) covers the whole revised documents. Each time a post-answer round leaves no Medium or High finding to fix, and before end-of-run item 8 copies the reviewed copies over `revised-*.md`, run the security review once, as above, on the answer edits it has not read: the first time on `answer-edits.diff`, written from `revised-*.md` to the `post-answer-*.md` copies; later on `answer-fix-<n>.diff`, written with `git diff --no-index` from the copies the last security review read to this round's copies, the spec diff appended to the plan diff. Before end-of-run item 8 makes the next round's copies, keep the copies each security review read as `post-answer-plan-<n>.md` and `post-answer-spec-<n>.md`. A fix it needs is another edit and needs another post-answer round.

## Reuse on the docs PR

A plan's docs PR reuses both results only when it changes only the plan and spec, both hash to the final values in `context.json`, and section 7 records what each review read. It still posts both reviews on its head as the repository's rules require, each naming the hash its review read and the final hash, and what covered the difference: for each fix, the step-6 round that reviewed the fixed copies for the code review and the security review of `fix-<n>.diff` for the security review, and, for any answer edits, the post-answer review for the code review and the security reviews of `answer-edits.diff` and each `answer-fix-<n>.diff` for the security review. Otherwise each review runs once: on what differs from the text it read, when its saved copy still matches the recorded hash, or on the full plan and spec when it does not; either way plus any other changed files, with every changed file in scope, and the security review runs its procedure in a fresh read-only subagent on a saved diff that holds what it reviews: the differing text, or the PR head's plan and spec as added text, written with Inputs item 2's flags, plus the PR's base..head diff of the other changed files. A finding left as a pending approval stays open in the posted review until the maintainer settles it.
```

- [ ] **Step 2: Edit `SKILL.md`**

1. After the line `Do not read secrets, install dependencies, commit, push, open PRs, post comments, merge or deploy during validation. Printing a handoff does not execute it or grant these permissions.`, append to the same bullet, after a space:

   ```text
   Running `/code-review` at the typed level `high`, without `--fix`, `--comment` or `--post`, and `/security-review`, as [validation reviews](references/validation-reviews.md) describes, is allowed: both only report findings, and `/code-review` keeps the level and finding limit it types as the user's saved choice for later runs.
   ```

2. Directly under the `## Workflow` heading, before `1. **Establish the baseline.**`, add this paragraph:

   ```text
   When Superpowers is installed, load each skill a step names with the Skill tool at that step; a subagent that does a step loads that step's skill itself. Where a loaded skill says to stop and ask, this skill's rules decide instead: mid-run work never pauses.
   ```

3. In step 6, replace `Fix verified Medium and High findings in the plan or spec, then review again with a fresh agent, until none remain; there is no round cap.` with:

   ```text
   Fix verified Medium and High findings in the plan or spec, then review again with a fresh agent, until none remain. There is no round cap. After the first round, give each new reviewer the current documents, add the changes since the last round to `Review focus` after the user's focus, and list the earlier findings under `Findings already dispositioned`. If the same finding returns after a fix, or three fixes for one problem fail, stop editing that part and question the approach (`superpowers:systematic-debugging`): record the finding in section 6 as an implementation blocker, so the verdict is Not ready, never in `decisions_without_reply`. The loop continues for the other findings, and the run finishes without pausing.
   ```

4. In step 8, before `Before scoring, check that every claim`, add this sentence:

   ```text
   Then run the final code and security reviews once each, as [validation reviews](references/validation-reviews.md) describes.
   ```

5. In end-of-run item 6 (**Post-answer review.**), replace `the reviewer may still report a defect in how an answer was applied. There is no round cap.` with `the reviewer may still report a defect in how an answer was applied. There is no round cap; step 6's stuck rule applies.` (after item 3, `There is no round cap.` alone also matches step 6).
6. In end-of-run item 8 (**Hash only reviewed text.**), replace `When a round leaves no Medium or High finding to fix, set each document's` with:

   ```text
   When a round leaves no Medium or High finding to fix, and the security review of the answer edits that read this round's copies ([validation reviews](references/validation-reviews.md)) leaves no finding to fix at any severity, set each document's
   ```

7. Under `### Phase grouping`, replace the bullet `- Record for each phase whether it is docs-only, whether it needs a security review and why (auth, user input, secrets, dependencies, CI workflows), and whether it is ready or waits, naming what it waits for.` with these two bullets:

   ```text
   - Record for each phase whether it is docs-only, whether it is security-sensitive and why (auth, user input, secrets, dependencies, CI workflows), and whether it is ready or waits, naming what it waits for. The `security_review` flag marks where review should look hardest. On the current Phase workflow it does not decide whether a security review runs: a code phase gets one at step 9. On an older block, or with none, a code phase gets one when flagged or when the repository's rules require one. A docs-only phase, on any block or none, gets the reviews the repository's rules require.
   - Write one done-check line per phase in section 8, before the between-phases note and the prompts: `Done-check, Phase <id>: <commands>`, unfenced, because a fenced block counts as a prompt. It lists commands to run later, not results: the phase's task test commands, the integration test that proves a task crossing a boundary, and the full unit and integration suites. Name only tests that exist once the phase is done, never one a later phase adds, and build it from the task test commands that step 5 rehearsed or step 6 reviewed. A missing test or assertion inside a task is an in-task repair (step 4); new test infrastructure, such as a service, container, dependency or CI job, is a pending approval.
   ```

8. In step 3, after `map every task back to a requirement.`, add, after a space:

   ```text
   If the plan has a `## Parked findings` section, each entry must name its fixing task (`Fixing task: Task <n>.`), and that task must exist in the plan; an entry without one is an implementation blocker in section 6, so the verdict is Not ready, because the design update (Phase workflow step 10) has not run.
   ```

- [ ] **Step 3: Edit `plan-reviewer.md`**

Replace `A round after fixes also gets the list of findings already dispositioned, so it does not re-raise them.` with `` A round after fixes also names the changes since the last round in `Review focus` and gets the list of findings already dispositioned, so it does not re-raise them. ``

- [ ] **Step 4: Check**

Run: `grep -n -i 'no round cap' skills/validate-plan/SKILL.md`
Expected: two lines, step 6 (`There is no round cap.`) and item 6 (`There is no round cap; step 6's stuck rule applies.`).
Run: `grep -n 'needs a security review' skills/validate-plan/SKILL.md`
Expected: no output.
Run: PACKAGE, then UNIT.
Expected: both pass; PACKAGE checks the two new relative links.

- [ ] **Step 5: Commit**

```bash
git add skills/validate-plan/references/validation-reviews.md skills/validate-plan/SKILL.md skills/validate-plan/references/plan-reviewer.md
git commit -m "Add validation's final reviews, the stuck rule and done-checks"
```

### Task 4: Report contract, handoff template and the security flag

**Files:**
- Modify: `skills/validate-plan/references/report-contract.md`
- Modify: `skills/validate-plan/handoff-template.md`
- Modify: `skills/validate-plan/references/html-report.md`

**Interfaces:**
- Consumes: the marker and both pause sentences (Global Constraints); the done-check line (Task 3).
- Produces: the section 8 order: effort line, done-check lines, between-phases note, fenced prompts.

- [ ] **Step 1: Edit `report-contract.md`**

1. In item 7 (**Verification and checkout**), after `Never replace an actual test count with an inferred new total.`, add, after a space:

   ```text
   Include the final code and security reviews: the command or brief, the input each read and its hash, the results and each fix diff ([validation reviews](validation-reviews.md)).
   ```

2. In item 8, replace `a one-line suggested effort covering all phases, then one fenced launch prompt per ready phase` with `a one-line suggested effort covering all phases, one unfenced done-check line per phase (SKILL.md, Phase grouping), then one fenced launch prompt per ready phase`.
3. In item 8, replace `so write only the effort line, the between-phases note and the fenced prompts` with `so write only the effort line, the done-check lines, the between-phases note and the fenced prompts`.
4. Replace `A same-run answer edit that passed the post-answer review (SKILL.md step 8) is not drift` with `A same-run answer edit that passed the post-answer review and the security review of the answer edits (SKILL.md step 8) is not drift`.

- [ ] **Step 2: Edit `handoff-template.md`**

1. In the fenced template, replace `Pause only for required approvals or unfixable failures.` with `Pause only for the Phase workflow's stop reasons.`
2. Replace `Variants, each replacing the stop sentence, the merge check or the Phase workflow sentence:` with `Variants, each replacing the stop sentence, the merge check, the Phase workflow sentence or the pause sentence:`
3. Replace the bullet that starts `- **Plan with no Phase workflow section**` with these two bullets:

   ```text
   - **Plan with no Phase workflow section** (a read-only validation, which adds no block to the plan): "Follow recorded decisions, permissions and reviews; preserve unrelated work." instead of the Phase workflow sentence, and "Pause only for required approvals or unfixable failures." instead of the pause sentence.
   - **Plan whose Phase workflow has no `<!-- phase-workflow: 2 -->` marker** (an older block): "Pause only for required approvals or unfixable failures." instead of the pause sentence, because the older block has no stop reasons.
   ```

4. Replace `while keeping approval gates from repository rules and the report, such as a merge that needs the maintainer, inside the prompt itself.` with `while keeping approval gates from repository rules and the report, such as a merge that needs the maintainer: the Phase workflow's stop reasons include any approval or authorization not already given, and the older pause sentence names required approvals directly.`
5. Replace ``treat only `- [ ]` to `- [x]` changes as expected.`` with ``treat only `- [ ]` to `- [x]` changes, and a Phase workflow section that, apart from a `Replaced on <date>` line under its heading, matches the block in validate-plan's `references/phase-workflow.md`, as expected.``
6. In the one-line note, replace `earlier phases merged into the plan branch and ticked task checkboxes are expected;` with `earlier phases merged into the plan branch, ticked task checkboxes and a Replaced on <date> swap that matches the block in validate-plan's references/phase-workflow.md are expected;`

- [ ] **Step 3: Edit `html-report.md`**

Replace `` `tasks`, the booleans `docs_only` and `security_review` (with `security_reason`
when true), `` with `` `tasks`, the booleans `docs_only` and `security_review` (with `security_reason`
when true; `security_review` marks a security-sensitive phase for review focus, and on an
older Phase workflow block, or with none, a flagged code phase gets a security review too,
as SKILL.md "Phase grouping" says), ``. Keep the line breaks of the surrounding paragraph.

In the same file, replace `post-answer review passes (SKILL.md step 8)` with `post-answer review and the security review of the answer edits pass (SKILL.md step 8)`.

- [ ] **Step 4: Check**

Run: `grep -c "Pause only for required approvals or unfixable failures." skills/validate-plan/handoff-template.md`
Expected: `2` (the two variants), and none inside the fenced template.
Run: PACKAGE, UNIT, DEMO.
Expected: all pass; DEMO exits 0 and prints `Fixture: 3 tests, 1 expected failure. Corrected control: 3 passed.` (it checks the `64 != 30` failure on `uncapped.py` itself).

- [ ] **Step 5: Commit**

```bash
git add skills/validate-plan/references/report-contract.md skills/validate-plan/handoff-template.md skills/validate-plan/references/html-report.md
git commit -m "Add done-check lines and the stop-reasons pause sentence"
```

### Task 5: Evaluation cases

**Files:**
- Modify: `docs/evaluation.md` (the `Starter cases` table)

**Interfaces:**
- Consumes: Tasks 2–4 wording.
- Produces: none.

- [ ] **Step 1: Edit existing rows**

1. **Phase workflow added:** append `` ; the added block carries the `<!-- phase-workflow: 2 -->` marker `` to its outcome.
2. **Docs-PR review:** replace its outcome with: `` A plan's docs PR reuses the validation run's code and security reviews, each posted with a `Reused:` line naming the hash its review read and the final hash and `Scope:` lines naming what covered any difference, only when it changes only the plan and spec, both hash to the report's final values and section 7 records what each review read; otherwise each review runs once on what differs from the text it read, or on the full plan and spec, plus any other changed files, the security review as its procedure in a read-only subagent on a saved diff; a finding whose fix would change a security or privacy boundary, a permission or an external action goes to the maintainer and stays open in the posted review. A docs-only phase PR gets the reviews the repository's rules require (in this repository, the code and security reviews once each on its final head, typed and targeted as Phase workflow step 9 types and targets them) ``
3. **Implementation handoff:** replace `it pauses only at a required approval or an unfixable failure` with `it pauses only for the Phase workflow's stop reasons (a destructive step, a security-sensitive action, an approval or authorization not already given, or a plan too broken to follow; with an older block or none, a required approval or an unfixable failure)`.

- [ ] **Step 2: Add these rows after the `Implementation handoff` row**

```text
| Stuck finding in validation | A finding that returns after a fix, or survives three fixes, stops being edited and becomes an implementation blocker in section 6 (verdict Not ready), never a `decisions_without_reply` entry; the run still finishes without pausing |
| Validation's final reviews | `/code-review high --max-findings all` and `/security-review` (or briefed subagents running their procedures) run once each on saved copies of the final plan and spec, never the live files; every confirmed finding is fixed, rejected with evidence or made a pending approval; section 7 records what each read and its hash; a review that cannot run is a recorded gap, not a Not ready verdict by itself |
| Done-check | Section 8 has one unfenced `Done-check, Phase <id>:` line per phase before the prompts, naming only tests that exist once that phase is done, plus the full suites; it is never counted as a prompt |
| Parked finding | A non-security finding whose fix would change the design, or that stays stuck, is recorded under the plan's `## Parked findings`, listed first in the code review comment, and followed by a design-update prompt before the next phase's prompt; the next phase session stops while the plan lists an entry the report's `revised-plan.md` lacks; a security finding is never parked; validation reports an entry without `Fixing task: Task <n>.` as an implementation blocker (Not ready) |
| Older Phase workflow | A plan whose block has no `<!-- phase-workflow: 2 -->` marker keeps its block, and its phase prompts keep "Pause only for required approvals or unfixable failures." |
| Change after a phase PR opens | A later commit, base change or conflict fix on a phase PR is reviewed as that change only (steps 2–8, then a security review of the change, targeted as step 9 says), with a `Scope:` line naming it, unless the PR targets the default branch; that PR and every other PR get both full reviews again |
```

- [ ] **Step 3: Run PACKAGE**

Expected: passes.

- [ ] **Step 4: Commit**

```bash
git add docs/evaluation.md
git commit -m "Add evaluation cases for the one review workflow"
```

### Task 6: Site pages

**Files:**
- Modify: `site/src/content/docs/phased-implementation.md`
- Modify: `site/src/content/docs/reports-and-handoffs.md`
- Modify: `site/src/content/docs/first-run.md`
- Modify: `site/src/content/docs/features.md`
- Modify: `site/src/content/docs/safety-and-limitations.md`
- Modify: `README.md` (the `validate-plan` row of the skills table)

**Interfaces:**
- Consumes: Tasks 2–4 wording; PD6 (approved) for the saved-settings bullet.
- Produces: none.

- [ ] **Step 1: Edit `phased-implementation.md`**

1. Replace `whether it is docs-only, whether it needs a security review and why,` with `whether it is docs-only, whether it is security-sensitive and why (the flag marks where to look hardest; on the current Phase workflow it does not decide whether a security review runs),`.
2. Replace the numbered list under "Recommended per-phase workflow" (from `1. Works in a git worktree on its own phase branch.` to item 7) with:

   ```text
   1. Works in a git worktree on its own phase branch, reads the phase's done-check from the report, and checks that no parked finding from an earlier phase still waits for a design update.
   2. Builds each task test-first: a unit test, plus an integration test where the task crosses a boundary such as a database, an API or another service. Wording, configuration and version tasks skip this.
   3. Reviews the phase with a fresh reviewer, checks each finding against the code before acting, and finds the cause of any failure before fixing it. Later rounds review only the latest fix.
   4. Repeats the review until no Medium or High finding remains, with no round cap. When a problem keeps coming back, the session questions the design and parks the finding with a recorded decision instead of patching again; a security finding is never parked. Low findings are listed for the maintainer to fix or skip.
   5. Proves the phase is ready by running the done-check and the full test suites.
   6. Runs the code review and the security review once each on the final version and fixes every confirmed finding; each fix gets a review of the fix only. Then it delivers the branch as your repository defines, for example a PR into the plan branch.
   7. Stops, and prints the next phase's prompt from the report, after a design-update prompt when a finding was parked. The maintainer merges the phase PR, then starts the next phase in a fresh session.
   ```

3. Replace `` The steps name Superpowers skills (`using-git-worktrees`, `test-driven-development`, `requesting-code-review` and others). Without Superpowers, the session follows the same steps as written. A docs-only phase skips the test-first rule. `` with `` The steps name Superpowers skills (`using-git-worktrees`, `test-driven-development`, `requesting-code-review` and others), and the session loads each one at its step. Without Superpowers, it follows the same steps as written. A docs-only phase skips the test-first rule, and its final reviews are the ones your repository requires for docs-only changes. The session asks you only when the next step is destructive, is a security-sensitive action, needs an approval it does not have, or the plan is too broken to follow. ``
4. Under "Other rules", replace the `**Docs-only PRs**` bullet with `- **Docs-only PRs** follow your repository's review rules. A plan's docs PR can reuse the code and security reviews from the validation run when it changes only the plan and spec (see below).`
5. In the `**The final plan-to-main PR**` bullet, replace `That review also clears the saved action points.` with `That review also clears the saved action points and checks that every parked finding was fixed.`
6. After the `**One phase at a time.**` bullet, add:

   ```text
   - **After a phase PR opens,** a later commit, such as a CI fix, gets a review of that change only, unless the PR targets your default branch. That PR and every other PR get both full reviews again.
   - **Saved `/code-review` settings.** Phase sessions and docs-PR reviews that follow this page type `/code-review high --max-findings all`. The command keeps a typed level and finding limit as your saved choice, so type your own level and `--max-findings default` on your next manual run.
   - **Plans already in progress.** A plan written before this workflow keeps its older Phase workflow, and its prompts keep the older pause sentence. To move it over, open a small docs PR that replaces its `## Phase workflow` section with the current block and adds `Replaced on <date>: workflow steps only, no scope change.` under the heading. List any task that crosses a boundary without integration test infrastructure, for the maintainer to approve.
   ```

7. Under "Reviewing a plan's docs PRs", replace everything from `The workflow above needs only CI for docs-only PRs.` to `` Other docs-only PRs, such as a README fix, have no plan to review against and keep `/code-review`. `` with:

   ```text
   Some repositories review docs PRs. The plan-validation repository is one: its own `AGENTS.md` asks for a code review and a security review on every PR into `main` or a plan branch, docs-only PRs included. Validation runs both reviews on the final plan and spec when it can, and the report records what each read and its hash. A plan's docs PR can reuse them:

   - **Reuse when nothing changed.** If the PR changes only the plan and spec, both match the hashes in the report and the report records what each review read, post the recorded results as the code and security reviews, each with a `Reused:` line naming the hash it read and the final hash, and `Scope:` lines naming what covered any difference: each validation fix and any end-of-run answer edits, with the reviews that covered them.
   - **Otherwise review the difference once.** Each review runs once on what differs from the text it read, or on the whole plan and spec when that text is gone, plus any other changed files. In Claude Code, type the code review as `/code-review high --max-findings all`, and run the security review as `/security-review`'s procedure in a subagent on a saved diff, because the command skips documentation files.
   - **Some findings go to the maintainer.** A finding whose fix would change a security or privacy boundary, a permission or an external action is asked, not fixed, and stays open in the posted review until the maintainer settles it. A finding that only disagrees with a decision the maintainer recorded is rejected with that decision as evidence.

   In the plan-validation repository, a docs-only phase PR gets the code review and the security review once each on its final head, typed and targeted as Phase workflow step 9 types and targets them for a code phase.
   ```

8. In the text to paste, replace these lines:
   - The line starting `- Follow the plan's Phase workflow section:` with `` - Follow the plan's Phase workflow section: worktree, test-first tasks with unit tests and, across boundaries, integration tests, review until no Medium or High finding remains with no round cap, a readiness check with the done-check and full suites, then the code and security reviews once each on the final head, with the code review typed as `/code-review high --max-findings all` in Claude Code. ``
   - `- Open the PR into the plan branch, wait for CI and post a short review summary as a PR comment.` with `- Open the PR into the plan branch, wait for CI and post a short review summary as a PR comment. A later commit gets a review of that change only.`
   - `- Stop at the end of the phase and print the next phase's prompt from the report. The maintainer merges and starts the next session.` with `- Stop at the end of the phase and print the next phase's prompt from the report, after the design-update prompt when a finding was parked. The maintainer merges and starts the next session.`
   - The line starting `- Docs-only PRs need CI only.` with `` - Docs-only PRs follow your review rules. A plan's docs PR can reuse validation's `/code-review` and `/security-review` results when it changes only the plan and spec, their hashes match the report and the report records what each review read; otherwise review once what differs, plus any other changed files, typing `/code-review high --max-findings all` in Claude Code and running `/security-review`'s procedure in a subagent on a saved diff so it reads Markdown. Post reused results with a `Reused:` line naming the hash each review read and the final hash, and `Scope:` lines naming what covered any difference. Ask the maintainer about a finding whose fix would change a security or privacy boundary, a permission or an external action; it stays open in the posted review until the maintainer settles it. ``
   - `- The final plan-to-main PR gets a full code review and a full security review, which also clears the saved action points.` with `- The final plan-to-main PR gets a full code review and a full security review, which also clears the saved action points and checks that every parked finding was fixed.`

- [ ] **Step 2: Edit the other three pages**

1. `reports-and-handoffs.md`:
   - Replace `the agent fixes verified Medium and High findings, and review runs again until none remain.` with `` the agent fixes verified Medium and High findings, and review runs again until none remain. A finding that keeps coming back after fixes becomes a blocker instead of another loop. Then `/code-review` and `/security-review` run once each on saved copies of the final plan and spec, and the report records what each read, so a plan's docs PR can reuse them. ``
   - Replace `whether it needs a security review,` with `whether it is security-sensitive (where review should look hardest),`.
   - Replace `naming that phase and its tasks with absolute plan/spec/report paths.` with `naming that phase and its tasks with absolute plan/spec/report paths. Above the prompts, a done-check line per phase lists the commands that prove it is ready.`
   - Replace `to stop only for a required approval or a failure it cannot fix,` with `to stop only for the Phase workflow's stop reasons (a destructive step, a security-sensitive action, an approval it does not have, or a plan too broken to follow),`.
2. `first-run.md`: in item 4, after `turns any finding that would change requirements, architecture, security boundaries or scope into a pending approval.`, add, after a space: `` A finding that keeps coming back becomes a blocker instead of another loop. Then it runs `/code-review` and `/security-review` once each on the final plan and spec. ``
3. `features.md`: after `becomes a question for you.`, add, after a space: `` A finding that keeps coming back becomes a blocker instead of another loop, and `/code-review` and `/security-review` run once each on the final plan and spec. ``
4. `safety-and-limitations.md`: after `It can create local evidence and a disposable rehearsal worktree.`, add, after a space: `` In Claude Code, its final `/code-review` run keeps the level and finding limit it types as your saved choice for later manual runs. ``
5. `README.md`: in the `validate-plan` row, replace `local report artifacts; with the Claude Code` with `` local report artifacts; in Claude Code, the `/code-review` level and finding limit it types, which the command keeps as your saved choice; with the Claude Code ``.

- [ ] **Step 3: Run SITE and PACKAGE**

Expected: the site tests pass and the build succeeds; PACKAGE passes (it checks home-directory paths in the site pages).

- [ ] **Step 4: Commit**

```bash
git add site/src/content/docs/phased-implementation.md site/src/content/docs/reports-and-handoffs.md site/src/content/docs/first-run.md site/src/content/docs/features.md site/src/content/docs/safety-and-limitations.md README.md
git commit -m "Describe the one review workflow on the site"
```

### Task 7: Repository rules and the superseded note

**Files:**
- Modify: `AGENTS.md` (sections "Git workflow" and "Plan work")
- Modify: `docs/superpowers/specs/2026-11-05-review-loops-without-revalidation-design.md` (one note under the header)

**Interfaces:**
- Consumes: the marker, `## Parked findings`, `validation-reviews.md` "Reuse on the docs PR" and the block's step numbers (Tasks 2–3).
- Produces: none.

- [ ] **Step 1: Edit `AGENTS.md` "Git workflow"**

1. Replace the bullet that starts `- Code and security review means` with:

   ```text
   - Code and security review means a code review and a security review of the PR diff, with findings fixed, explicitly accepted or parked as the plan's Phase workflow allows (in Claude Code, `/code-review`, always typed with the level that step 9 of the current Phase workflow block in `skills/validate-plan/references/phase-workflow.md` types, for every PR, including PRs outside a plan and phases of plans on an older block, and `/security-review`; in other hosts, an equivalent independent review). A plan's docs PR may reuse the validation run's reviews, and later pushes to a phase PR get change-only reviews (see below).
   ```

2. In the next bullet, replace everything from `On a plan's docs PR or a docs-only phase PR, the code review is the full-plan review` to `` Other docs-only PRs keep `/code-review`. `` with:

   ```text
   A plan's docs PR reuses the validation run's code and security reviews when it changes only the plan and spec, both hash to the final values in the report's `context.json`, and section 7 records what each review read ("Reuse on the docs PR" in `skills/validate-plan/references/validation-reviews.md`). Each comment review then adds a `Reused:` line with the hash its review read and the final hash, and `Scope:` lines naming what covered the difference: each validation fix and any end-of-run answer edits, with the reviews that covered them. Otherwise each review runs once, typed and targeted as Phase workflow step 9 types and targets them, on what differs from the text it read or on the full plan and spec, plus any other changed files. A docs-only phase PR gets the code review and the security review once each on its final head, typed and targeted as Phase workflow step 9 types and targets them for a code phase. A finding whose fix would change a security or privacy boundary, a permission or an external action goes to the maintainer; one that only disagrees with a decision the maintainer recorded is rejected with that decision as evidence.
   ```

3. In the bullet that starts `- Post each review's result`, replace `` `success` only when every finding is fixed or explicitly accepted. A new push needs both reviews again. `` with:

   ```text
   `success` only when every finding is fixed, explicitly accepted, or parked under the plan's Phase workflow and listed first in the code comment review (a security finding is never parked). Each comment review names the current head in `Head:` and lists in `Scope:` lines what each review saw: the full review's head, and each later fix or change range with its reviewer. After a new push to a phase PR (a fix, base change or conflict fix), the change goes through the Phase workflow's steps 2–8, and the new head gets a `## Code review` whose `Scope:` names that change and links the full review, a `## Security review` of that change only, targeted as Phase workflow step 9 says, and both statuses. Every other PR, including every PR into `main`, needs both full reviews again after a new push.
   ```

- [ ] **Step 2: Edit `AGENTS.md` "Plan work"**

1. Replace the paragraph that starts `This repo follows the per-phase workflow published in` with:

   ```text
   This repo follows the per-phase workflow published in `site/src/content/docs/phased-implementation.md`, and every docs-only PR also gets both reviews. Each phase follows the plan's Phase workflow section; the bullets below add this repository's specifics to its review and delivery steps, not extra review rounds. A plan whose Phase workflow lacks the `<!-- phase-workflow: 2 -->` marker gets a docs PR that swaps in the current block before its next phase starts, with `Replaced on <date>: workflow steps only, no scope change.` under the heading; that PR lists any task that crosses a boundary without integration test infrastructure, for the maintainer to approve or defer.
   ```

2. Replace the bullet that starts `- Phase review, before opening the PR:` with:

   ```text
   - Phase review, before opening the PR: the Phase workflow's review loop and readiness check (steps 4–8), with no round cap; a problem that keeps returning follows its stuck rule. List minor items in the code comment review; the end-of-phase report asks the maintainer to fix or skip each, and skipped or unanswered ones are saved as action points for the plan-to-`main` review.
   ```

3. Replace `- Run a security review on every phase, after the code review rounds, whether or not the validation report flags it as security-sensitive.` with `- Run the code review and the security review once each on every phase's final head, typed and targeted as Phase workflow step 9 types and targets them, whether or not the validation report flags it as security-sensitive.`
4. Replace `then stop and print the next phase's prompt from the report.` with `then stop and print the next phase's prompt from the report, after the design-update prompt when a finding was parked (Phase workflow step 10).`
5. Replace `` - The plan-to-`main` PR gets a full code and security review of the whole diff, which also resolves the saved action points. `` with `` - The plan-to-`main` PR gets a full code and security review of the whole diff, which also resolves the saved action points and checks that every entry under the plan's `## Parked findings` names a fixing task that is done. ``

- [ ] **Step 3: Add the superseded note**

In `docs/superpowers/specs/2026-11-05-review-loops-without-revalidation-design.md`, after the line `**Status:** Draft for maintainer review`, add a blank line and:

```text
**Note (2026-11-12):** the remark that existing `/code-review` round limits on code PRs stay is superseded by `2026-11-11-one-review-workflow-design.md`, which has no round cap.
```

- [ ] **Step 4: Check the whole plan's changes**

Run: `git grep -n -i -E 'no round cap|Pause only for required approvals|finishing-a-development-branch|steps 8 and 9|5 rounds|5-round|need(s)? CI only|unfixable failure|needs a security review|full-plan review|stop only for a required approval' -- ':!docs/superpowers/' ':!CHANGELOG.md'`
Expected: every hit states a new rule or the older-block fallback, and none describes the old rules: "no round cap" in `SKILL.md` (step 6 and item 6), `phase-workflow.md` step 6, the `AGENTS.md` phase-review bullet and the site page; `Do not run` `superpowers:finishing-a-development-branch` in `phase-workflow.md` step 10; the old pause sentence in the two older-block variants of `handoff-template.md` and in two `docs/evaluation.md` rows.
Run: `git grep -n -P '/code-review(?! high)' -- AGENTS.md skills/validate-plan/references/phase-workflow.md skills/validate-plan/references/validation-reviews.md`
Expected: one line, the `AGENTS.md` definition bullet (`/code-review`, always typed with the level that step 9 of the current Phase workflow block types): every other mention in these instruction files types `high`, and `AGENTS.md` points to step 9 instead of naming the bare command (the test fixtures are frozen and not checked).
Run: UNIT, PACKAGE, DEMO, SITE.
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add AGENTS.md docs/superpowers/specs/2026-11-05-review-loops-without-revalidation-design.md
git commit -m "Point the repository rules at the one review workflow"
```

## Release follow-up (after the plan-to-main merge, not a plan phase)

A dedicated release PR from `release/v0.7.0`, as `AGENTS.md` "Releases" describes: version `0.7.0` in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and `.codex-plugin/plugin.json`; the release tag in `site/src/content/docs/get-started.md`; the release checks in `docs/verification.md`; and this `CHANGELOG.md` entry:

```text
## 0.7.0 — <release date>

- New plans get a ten-step Phase workflow (marked `<!-- phase-workflow: 2 -->`): test-first tasks with integration tests across boundaries, a fresh-reviewer loop with no round cap, a stuck rule that questions the design instead of patching again, a readiness check with the phase's done-check and the full suites, then `/code-review` and `/security-review` once each on the final head. A fix after them, or a later push to a phase PR that does not target the default branch, gets a review of that change only. The session asks only for four stop reasons: a destructive step, a security-sensitive action, an approval not already given, or a plan too broken to follow.
- A finding whose fix would change the design, or that stays stuck, is parked in the plan's `## Parked findings` section; the phase PR still merges, a design-update prompt comes before the next phase's prompt, and the next phase does not start until the design update has run. A security finding is never parked.
- Validation runs `/code-review` and `/security-review` once each on saved copies of the final plan and spec, and records what each read, so a plan's docs PR can reuse them. A finding that keeps returning in validation becomes a blocker instead of another loop.
- Section 8 of new reports lists a done-check line per phase. Phase prompts say "Pause only for the Phase workflow's stop reasons."; plans on the older block keep the older sentence.
```

The release lands after the plan-to-`main` merge, so the older-block rules (Tasks 4 and 7) ship no later than the release.
