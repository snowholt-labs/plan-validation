# One review workflow for validated plans: design

Date: 2026-11-11. Status: approved by the maintainer on 2026-11-11. Supersedes the round-cap notes in `2026-11-05-review-loops-without-revalidation-design.md`.

Scope: this document covers the plan-validation plugin and this repository's own rules. Matching changes to the maintainer's private configuration and private repositories are tracked outside this repository.

Evidence labels: **Verified** (file:line), **Assumption**, **Unknown**. Decision owners: **Maintainer** (decided in the brainstorm) or **Proposed** (a default the maintainer approved with the design).

## 1. Intent and why

One review workflow, followed the same way by the plugin, this repository's rules and the plans the plugin writes, for both planning and implementation. Every review step runs once on any given text. Confidence that the work is right comes from how each finding is closed, not from repeating full reviews.

Why now (field use in private projects, anonymized):

- One phase ran 26 `/code-review` rounds, which took most of its active time.
- In another phase, a one-line CI test fix after the PR opened triggered a full re-review under a rule that any later commit needs both reviews again. That review found 5 new Medium findings in code the first round had passed. Four more rounds followed, changing 14 files (+587/−89).
- Validation loops churn too: one run took 14 review rounds before the end-of-run answers and 18 after.
- Naming a skill is not invoking it. Across 17 audited phases, `receiving-code-review` was invoked in none and `systematic-debugging` in one.

Maintainer's principle: one good process, even if it looks expensive, costs less than repeated failed loops or work that has to be patched again.

## 2. Goals, non-goals, anti-goals

Goals:
- One pipeline (section 3) for two units: the plan and spec during `/validate-plan`, and one plan phase during implementation.
- `/code-review` and `/security-review` each run at least once per unit, and never twice on unchanged text.
- Unit tests for every task, and integration tests where a task crosses a boundary. Coverage grows phase by phase.
- No pause to ask the maintainer except for the four stop reasons (D6).
- Each rule has one home. Other files point to it rather than copying it.

Non-goals:
- Editing Superpowers (a third-party plugin; updates would overwrite edits). Overrides live in the plan's Phase workflow.
- A report format bump, new `context.json` fields or renderer changes.
- Migrating saved reports.

Anti-goals (a failure even if it technically works):
- Full `/code-review` or `/security-review` runs repeated on unchanged code.
- A session that stops to ask "continue?" or presents a menu and waits.
- A round cap that lets a confirmed High or Medium bug ship.
- A confirmed, in-design bug left unfixed.

## 3. The pipeline

The same ten steps for both units.

| Step | Implementation unit (one phase) | Planning unit (plan + spec in `/validate-plan`) |
|---|---|---|
| 1 Scope | The phase's tasks and its done-check (report section 8) | The plan and spec scope (SKILL.md step 1) |
| 2 Failing tests | A unit test, plus an integration test when the task crosses a boundary (database, API, authentication, another service); each fails for the expected reason | A rehearsal command or coverage check that fails on the original plan (Assumption: the existing rehearsal, SKILL.md:40) |
| 3 Pass | Minimal code until green, all tests green, then refactor; repeat 2–3 per task | Plan or spec repair until the rehearsal passes |
| 4 Request review | Fresh reviewer, `superpowers:requesting-code-review` | Fresh reviewer, `references/plan-reviewer.md` brief |
| 5 Receive review | `superpowers:receiving-code-review`; close each finding (D5) | Same triage (SKILL.md:41) |
| 6 Critical or Important left? | Yes → step 7; no → step 8 | Same, with Medium/High |
| 7 Root cause, then fix | `superpowers:systematic-debugging`, then back to step 2 | Same |
| 8 Ready? | `superpowers:verification-before-completion`: done-check plus full unit and integration suites pass | Every claim rests on a command or review that ran (SKILL.md:43) |
| 9a / 9b | `/code-review`, then `/security-review`, once each on the final head | The same two, once each, inside the validation run (D10) |
| 10 Deliver | Open the PR; later commits follow D11 | The docs PR reuses 9a/9b when the text is unchanged (D10) |

Where each skill runs (Verified): `requesting-code-review` dispatches a fresh reviewer subagent (its SKILL.md:8, :32). The other skills run in whichever session does that work. Under subagent-driven development that is the fresh implementer subagent for each task (SDD SKILL.md:8), so that subagent loads `test-driven-development` and `systematic-debugging` itself, and its brief says so.

## 4. Decisions

- **D1 One pipeline, both units.** Maintainer.
- **D2 Tests.** Each task writes a failing unit test first; a task that crosses a boundary also writes a failing integration test first. Step 8 runs the full unit and integration suites, so later phases re-run earlier phases' tests. No coverage-percentage gate. Maintainer.
- **D3 Done-check.** Validation writes one done-check per report phase in report section 8, on its own line before the phase prompts, as commands to run later (section 7 holds only results from this run: SKILL.md:43, report-contract.md:63): the exact test commands, plus the integration test that proves the phase when it has a boundary-crossing task. It is not written into the plan, because the phase grouping lives only in the report (Verified, SKILL.md:70). It uses only tests for its own and earlier phases' tasks, and is rehearsed in step 5 when authorized. A phase with no done-check (an older report) runs the full suites at step 8. Assumption: the renderer accepts these lines in section 8, as it does the between-phases note (handoff-template.md:34); confirm with a render. Maintainer.
- **D3a What validation may add.** A missing test or assertion inside an existing task is an in-task repair (SKILL.md:39). New test infrastructure (a service, container, dependency or CI job) changes scope and becomes a pending approval (SKILL.md:25). Proposed.
- **D4 Who reviews, who rates, what range.** A fresh subagent each round: `code-reviewer.md` in a phase, which assigns Critical/Important/Minor (Verified, `code-reviewer.md:97-119`), and `plan-reviewer.md` in validation. The fixing session never re-rates. Round 1 reviews the whole unit; later rounds review only the latest fix and the code it touches (as SDD SKILL.md:395-403 does). Subagent-driven development's final review (SDD SKILL.md:445-469) counts as round 1. Proposed.
- **D5 How a finding closes.** Exactly one of: a real bug gets a failing test, a root-cause fix and a passing test; a wrong finding is rejected with evidence; a finding whose fix would change the design gets the smallest fix inside the design, or a recorded decision (what, why, cost if wrong, as in SDD SKILL.md:19-24), parked and listed in the end report. Minor findings from steps 4–6 are listed, not looped on. Proposed.
- **D6 No round cap; a stuck rule and four stop reasons.** If the same problem returns after a fix, or three fixes for one problem fail, the session stops patching and questions the design (systematic-debugging SKILL.md:195-210), records a decision and continues, rather than discussing first as :210 says. It asks the maintainer only when the next step is destructive, security-sensitive, has an outside effect not already authorized, or the plan is too broken to follow (SDD SKILL.md:27-31). Maintainer.
- **D7 Readiness and debugging tools.** Step 8 is `superpowers:verification-before-completion`; a not-ready result goes to `superpowers:systematic-debugging`, then step 2. `superpowers:diagnosing-superpowers` asks the human questions and only reports (Verified, its SKILL.md:11-12, :23-24), so it is only for a post-mortem after a phase. Proposed.
- **D8 9a and 9b run once; every confirmed finding goes back.** `/code-review` and `/security-review` run once each on the final head. Every confirmed finding, Low included, goes back to step 2; `/code-review` gives no severity, so nobody has to rate its findings. Rejecting one needs evidence in the comment review. Maintainer.
- **D9 Fixes after 9a/9b.** A fix goes through steps 2–8; steps 4–6 review only the fix, and `/security-review` runs on the fix diff only. `/code-review` does not run again. The plan-to-main PR's full review is the backstop. Maintainer.
- **D10 The planning unit's 9a/9b.** They run inside `/validate-plan` on the plan and spec text whose hashes `context.json` `documents` records: as the run's last review step: before the step 8 render when no question is pending, otherwise after the end-of-run round and any post-answer loop (SKILL.md:51-53). Results go in section 7. The docs PR reuses them when the committed plan and spec hash to those values; it still posts both comment reviews on its head, each with a `Reused:` line naming the hash each review saw and the final hash, and sets both statuses. If the text differs, both reviews run once on the changed lines only. Unknown: whether both commands can target uncommitted or untracked files; the fallback is a saved diff file. In other hosts, "an equivalent independent review", as phase-workflow.md:17 says today. Maintainer (mechanics Proposed).
- **D11 After the PR opens.** A later commit, base change or conflict fix goes through steps 2–8 on that change only. The new head gets `## Code review` with `Scope: <old-head>..<new-head>` and the full review's URL, plus `## Security review` from `/security-review` on that change, and both statuses. This meets this repository's merge checks (`AGENTS.md:50, :53`) without a full re-review. Proposed.
- **D12 No `superpowers:finishing-a-development-branch`.** It ends in a menu and waits (Verified, its SKILL.md:53-80, :217); step 8 takes over its readiness role. Maintainer.
- **D13 In-flight plans.** One small docs PR per in-flight plan swaps in the new `## Phase workflow` section and adds one line under it: "Replaced on <date>: workflow steps only, no scope change." The next phase session reconciles that diff from the line (handoff-template.md:32-36), with no re-validation. Validation still adds the block only when a plan has none (phase-workflow.md:3, unchanged). Maintainer.
- **D14 Validation's own loop follows the same pattern.** No cap, plus the stuck rule. After round 1, each fresh reviewer gets the changes since the last round as `Review focus`, with earlier findings under `Findings already dispositioned`. Proposed.
- **D15 Skills are invoked, not just named.** When Superpowers is installed, each step loads its skill with the Skill tool, and a subagent that does a step loads that step's skill itself. Proposed.
- **D16 A parked finding that needs a spec or plan change.** The phase PR still merges into the plan branch. The finding is listed as parked and tracked the way the repository's rules track review findings (an issue where they allow one; in this repository, which allows no extra labels or issues, AGENTS.md:46, :79, the code comment review and the end-of-phase report), and both statuses can pass (W-A6). Right after the merge, the end-of-phase report prints a design-update prompt instead of the next phase's prompt: brainstorm the change with the maintainer, update the spec and plan with a fixing phase, then validate the remaining phases as a phase-only validation (Verified that path exists, handoff-template.md:36). The revised documents land through a docs PR into the same plan branch, and work continues from the new report. Nothing waits for the end of the plan, because later work built on a flaw costs more to fix. A security-sensitive finding is still a stop reason. Maintainer.

## 5. Answers to the seven design questions

1. **Exit if the loop keeps finding issues:** no cap; the stuck rule and the four stop reasons (D6).
2. **Who sets severity:** the fresh steps 4–6 reviewer, never the fixer (D4). `/code-review` findings need no rating, because every confirmed one is fixed (D8).
3. **Review range per round:** round 1 covers the whole unit, later rounds the latest fix (D4); 9a/9b cover the whole unit once (D8); after the PR opens, only the change (D11).
4. **SDD's final review:** round 1 of steps 4–6 (D4); its one-fix-wave limit is replaced by the step 6 loop.
5. **Step 7 and the menu:** finishing is dropped (D12); the handoff keeps "do not ask", and its pause sentence points to the stop reasons (W-P8).
6. **Old notes that point away from the built-in reviews:** delete them once the rules change (tracked privately).
7. **plan-validation's no-cap loop:** same pattern (D14).

## 6. Where each part lives

- **The pipeline:** this plugin. A phase's steps live in `references/phase-workflow.md`, copied into each plan; the planning unit's steps live in `skills/validate-plan/SKILL.md`.
- **This repository's rules (`AGENTS.md`):** they point to the plan's Phase workflow (rows A1–A5).
- **A user's own repository rules:** they set which findings are required and how reviews are posted; the plugin text keeps deferring to them ("as this repository's rules require").
- **Superpowers:** unchanged. The plan's Phase workflow overrides it where they differ; user instructions take precedence over skills (Verified, using-superpowers SKILL.md:63).

## 7. Conflict table

| ID | Home | file:line | Conflict | Proposed change |
|---|---|---|---|---|
| P1 | plan-validation | `skills/validate-plan/references/phase-workflow.md:6-20` | Old 9 steps: step 6 has no stuck rule, step 7 runs finishing, step 8 defers to repository rules that may loop; no integration tests or done-check | Replace with W-P1 |
| P2 | plan-validation | `skills/validate-plan/SKILL.md:70` | Nothing writes a done-check | Add W-P2 |
| P3 | plan-validation | `SKILL.md:41` | "There is no round cap" with no stuck rule; every round reviews everything; skills are named, not loaded | W-P3 |
| P4 | plan-validation | `SKILL.md:43` | No `/code-review` or `/security-review` in validation | Add W-P4 |
| P5 | plan-validation | `SKILL.md:26` | "Do not … post comments …" could read as forbidding the read-only review commands | Add W-P5 |
| P6 | plan-validation | `SKILL.md:51` | Post-answer loop "There is no round cap" with no stuck rule | W-P6 |
| P7 | plan-validation | `site/src/content/docs/phased-implementation.md:24-30, :29, :36, :44` | Old steps; security review only when flagged (:29); docs-only PRs need CI only (:36, :44) | W-P7 |
| P8 | plan-validation | `skills/validate-plan/handoff-template.md:12, :22` | "Pause only for required approvals or unfixable failures" is vaguer than the stop reasons | W-P8 (same length; plans with an older block or none keep the old sentence) |
| P9 | plan-validation | `docs/superpowers/specs/2026-11-05-review-loops-without-revalidation-design.md:136` | Says a global 6-round cap stays; that cap applies only to rounds with only Low findings left | W-P9 note; leave the history as written |
| P10 | plan-validation | `CHANGELOG.md`, three manifests | Behavior change in skill text | Minor release entry; check against `docs/evaluation.md` (AGENTS.md:39) |
| A0 | repo rule | `AGENTS.md:51` | Still makes the full-plan review the code review on docs PRs and docs-only phase PRs, and defines review as "of the PR diff" | W-A0 |
| A1 | repo rule | `AGENTS.md:52` | The docs PR runs a looping full-plan review instead of reusing the validation reviews | W-A1 |
| A2 | repo rule | `AGENTS.md:53` | "A new push needs both reviews again" | W-A2 |
| A3 | repo rule | `AGENTS.md:57` | Points to "steps 8 and 9" and "after step 9"; the new block uses steps 4–10, and older blocks stay in use | W-A3 |
| A4 | repo rule | `AGENTS.md:60` | A 5-round cap, then "ask the maintainer" | W-A4 |
| A5 | repo rule | `AGENTS.md:62` | Always prints the next phase's prompt, even when a parked finding needs a redesign | W-A5 |
| A6 | repo rule | `AGENTS.md:53` | `success` "only when every finding is fixed or explicitly accepted" blocks D16's merge | W-A6 |
| S1 | superpowers | SDD `SKILL.md:445-469` | Final review allows one fix wave | No edit; overridden by W-P1 steps 4–6 |
| S2 | superpowers | SDD `SKILL.md:487` | "Use superpowers:finishing-a-development-branch" | No edit; overridden by W-P1 step 10 |
| S3 | superpowers | systematic-debugging `SKILL.md:210` | "Discuss with your human partner before attempting more fixes" | No edit; overridden by W-P1 step 6 |
| S4 | superpowers | finishing `SKILL.md:217` | "Present the menu and wait." | Not used (D12) |

## 8. Proposed wording

### W-P1: `references/phase-workflow.md`, the block from `## Phase workflow` to the docs-only sentence

```markdown
## Phase workflow

Every phase follows these steps, in a fresh session, on its own phase branch. When Superpowers is installed, load each named skill with the Skill tool at its step; a subagent that does a step loads that step's skill itself, and its brief says so. Without Superpowers, follow the step as written.

1. Work in a git worktree for the phase branch (`superpowers:using-git-worktrees`). Read the phase's done-check in section 8 of the validation report, when it has one.
2. For each task, write the failing tests first and watch them fail for the expected reason, the feature missing and not a typo (`superpowers:test-driven-development`): a unit test, plus an integration test when the task crosses a boundary (database, API, authentication, another service).
3. Write the minimal code that makes the tests pass, keep all tests green, then refactor. Repeat steps 2–3 for each task.
4. Review the phase with a fresh reviewer (`superpowers:requesting-code-review`), given the plan and spec paths and the report path named in the phase prompt. Round 1 reviews the phase's base..head range; later rounds review only the latest fix and the code it touches. When `superpowers:subagent-driven-development` ran the tasks, its final review is round 1. The reviewer sets each finding's severity (Critical counts as High, Important as Medium, Minor as Low).
5. Check each finding against the code before acting (`superpowers:receiving-code-review`) and close it one way: a real bug gets a failing test, a root-cause fix and a passing test; a wrong finding is rejected with evidence; a finding whose fix would change the design gets the smallest fix inside the design, or a recorded decision (what, why, cost if wrong) listed in the end-of-phase report.
6. Repeat steps 4–5 until no Medium or High finding remains. There is no round cap. If the same problem returns after a fix, or three fixes for one problem fail, stop patching: question the design, record a decision and continue. List Low findings without looping on them; the end-of-phase report asks the maintainer to fix or skip each one.
7. For any failing test or unexpected behavior, find the cause before fixing it (`superpowers:systematic-debugging`), then return to step 2.
8. Prove the phase is ready (`superpowers:verification-before-completion`): run the done-check commands, if any, and the full unit and integration suites, read the output, and claim only what it shows. If anything fails, go to step 7.
9. Run the code review and the security review once each on the final head, as this repository's rules require (in Claude Code, `/code-review` and `/security-review`; in other hosts, an equivalent independent review). Fix every confirmed finding, Low included, through steps 2–8, or reject it with evidence; step 4 reviews only the fix, and the security review runs again on the fix only. Never repeat either review on unchanged code.
10. Deliver the branch as the repository's rules define (for a plan branch, a PR into that branch). Push and open a PR only when the repository's rules or the maintainer authorize it. A later commit, such as a CI fix, goes through steps 2–8 on that change only, and the security review runs on that change only. Do not run `superpowers:finishing-a-development-branch`. If a parked finding needs a spec or plan change, end the phase report with a design-update prompt instead of the next phase's prompt: brainstorm the change with the maintainer, update the spec and plan with a fixing phase, and validate the remaining phases.

Ask the maintainer only when the next step is destructive, security-sensitive, has an outside effect not already authorized, or the plan is too broken to follow. Otherwise decide, record the decision and continue.

A docs-only phase skips step 2's test-first rule. Its step 9 runs the reviews the repository's rules require for docs-only changes.
```

### W-P2: SKILL.md:70 (phase grouping), append

> For each phase, write one done-check in section 8, on its own line before the phase prompts (`Done-check, Phase <id>: …`), as commands to run later rather than results: the exact commands that prove the phase (its unit and integration tests and the full suites), and the integration test that proves it when a task crosses a boundary. Use only tests for that phase's and earlier phases' tasks. Adding a missing test or assertion inside a task is an in-task repair; new test infrastructure needs approval.

### W-P3: SKILL.md step 6, replace "Fix verified Medium and High findings in the plan or spec, then review again with a fresh agent, until none remain; there is no round cap."

> When Superpowers is installed, load `superpowers:requesting-code-review` and `superpowers:receiving-code-review` with the Skill tool before the first round. Fix verified Medium and High findings in the plan or spec, then review again with a fresh agent, until none remain. After the first round, give each new reviewer the changes since the last round as `Review focus` and the earlier findings under `Findings already dispositioned`. There is no round cap. If the same finding returns after a fix, or three fixes for one problem fail, stop editing that part: question the approach (`superpowers:systematic-debugging` when installed), record a decision in `decisions_without_reply` or as a pending approval, and continue.

### W-P4: SKILL.md step 8, add before "Score and render"

> Run `/code-review` and `/security-review` once each, read-only, as the run's last review step on the final plan and spec text (in other hosts, an equivalent independent review): before the step 8 render when no question is pending, otherwise after the end-of-run round and any post-answer loop, before the re-render. Fix confirmed findings under step 6's rules, where the next reviewer and `/security-review` check only the fix; never run either again on unchanged text. Record in section 7 the commands, targets and results, the hash each review saw, and the final hash written to `context.json` `documents`.

### W-P5: SKILL.md:26, append

> Running `/code-review` and `/security-review` without `--fix` or `--comment` is allowed.

### W-P6: SKILL.md:51, replace "There is no round cap."

> There is no round cap; step 6's stuck rule applies.

### W-P7: site `phased-implementation.md`

Replace the list at :24-30 with:

1. Works in a git worktree on its own phase branch and reads the phase's done-check.
2. Builds each task test-first, with a unit test and, where the task crosses a boundary, an integration test.
3. Reviews the phase with a fresh reviewer, checks each finding before fixing it, and finds the cause of any failure first. Later rounds review only the latest fix.
4. Repeats the review until no Medium or High finding remains, with no round cap. If a problem keeps coming back, the session rethinks the design, records a decision and continues.
5. Proves the phase is ready by running the done-check and the full test suites.
6. Runs the code review and the security review once each on the final version, fixes what they find and has the fix reviewed, then delivers the branch as your repository defines.
7. Stops, and prints the next phase's prompt from the report. The maintainer merges the phase PR, then starts the next phase in a fresh session.

Replace :36 with:

> **Docs-only PRs** follow your repository's review rules. A plan's docs PR can reuse the reviews from the validation run when the plan and spec are unchanged.

At :44, replace "The workflow above needs only CI for docs-only PRs." with "Docs-only PRs get the reviews your repository requires."

### W-P8: handoff-template.md:12, replace the pause sentence

> Pause only for the Phase workflow's stop reasons.

And add to the variants (:17-22): "**Plan whose Phase workflow has no stop-reasons sentence** (an older block, or no section): keep 'Pause only for required approvals or unfixable failures.'"

### W-P9: top of the 2026-11-05 spec

> Note (2026-11-11): line 136 misreads the global rule, which caps only rounds with Low findings left. Superseded by `2026-11-11-one-review-workflow-design.md`.

### W-A0: `AGENTS.md:51`, replace "On a plan's docs PR or a docs-only phase PR, the code review is the full-plan review instead of `/code-review` (see below)."

> After a new push, the review covers the pushed change only. On a plan's docs PR, the validation run's reviews may be reused (see below).

### W-A1: plan-validation `AGENTS.md:52`, replace from "On a plan's docs PR or a docs-only phase PR" to "Other docs-only PRs keep `/code-review`."

> On a plan's docs PR, reuse the validation run's recorded code and security reviews when the plan and spec hashes match the report, posting them with a `Reused:` line; otherwise review the changed lines once. A docs-only phase PR gets `/code-review` and `/security-review` once each on its final head, like other docs-only PRs. Findings that contradict a recorded decision, or would change a security or privacy boundary, a permission or an external action, go to the maintainer.

### W-A2: `AGENTS.md:53`, replace "A new push needs both reviews again."

> A new push gets a review of the pushed change only, posted with a `Scope:` line; for a plan phase, as its Phase workflow's step 10 describes.

### W-A3: `AGENTS.md:57`, replace from "Each phase follows" to "a second round after step 9."

> Each phase follows the plan's Phase workflow section. The bullets below add this repository's specifics to its review and delivery steps (steps 4–10 of the current block, 3–9 of an older one); they are not extra review rounds.

### W-A4: `AGENTS.md:60`, replace the whole bullet

> Phase review, before opening the PR: follow the plan's Phase workflow, steps 4–8. List minor items in the code comment review; the end-of-phase report asks the maintainer to fix or skip each, and skipped or unanswered ones are saved as action points for the plan-to-`main` review.

### W-A5: `AGENTS.md:62`, replace "then stop and print the next phase's prompt from the report."

> then stop and print the next phase's prompt from the report, or the design-update prompt when a parked finding needs a spec or plan change (Phase workflow step 10).

### W-A6: `AGENTS.md:53`, replace "`success` only when every finding is fixed or explicitly accepted"

> `success` only when every finding is fixed, explicitly accepted, or parked under the Phase workflow's design rule and listed first in the end-of-phase report

## 9. Left to the builder

- The PR split for the plugin release, this repository's `AGENTS.md` and the site page.
- Ordering: repository rules that defer to the Phase workflow need a clause for plans still on the older block (no step 10), landed no later than this release, so no plan is left with two rules that point at each other.
- The version number and the CHANGELOG entry.
- The exact Codex wording for "an equivalent independent review" in the planning unit.
- How to target uncommitted plan and spec text for `/code-review` and `/security-review` (D10, Unknown), with the saved-diff fallback.
- Finding the in-flight plans (D13).

## 10. Questions answered by the maintainer

- **O1:** a fix after 9a/9b, or a post-PR commit, also gets `/security-review` on that change only.
- **O2:** confirmed Low `/code-review` findings go back to step 2 too.
- **O3:** a parked design finding merges and is tracked, and the redesign happens right after the merge, before the next phase (D16).

## 11. Builder check

A fresh builder read the design on 2026-11-11. Its questions were settled as follows:
- Done-check location for report-only phases: report section 8, not the plan (D3).
- Whether validation may add tests: in-task tests yes; new test infrastructure needs approval (D3a).
- Drift from the in-flight docs PRs: a one-line note under the new section; no re-validation (D13).
- Rating `/code-review` findings: no longer needed (O2).
- Parked findings at merge: became O3.
