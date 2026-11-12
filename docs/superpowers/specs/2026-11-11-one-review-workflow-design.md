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
- **D3 Done-check.** Validation writes one done-check per report phase in report section 8, on its own unfenced line before the phase prompts (report-contract.md:64 changes to match), as commands to run later (section 7 holds only results from this run: SKILL.md:43, report-contract.md:63): the exact test commands, plus the integration test that proves the phase when it has a boundary-crossing task. It is not written into the plan, because the phase grouping lives only in the report (Verified, SKILL.md:70). It names only tests that exist once the phase is done, never one a later phase adds, and is built from the task test commands step 5 rehearsed or reviewed. A phase with no done-check (an older report) runs the full suites at step 8. Assumption: the renderer accepts these lines in section 8, as it does the between-phases note (handoff-template.md:34); confirm with a render. Maintainer.
- **D3a What validation may add.** A missing test or assertion inside an existing task is an in-task repair (SKILL.md:39). New test infrastructure (a service, container, dependency or CI job) changes scope and becomes a pending approval (SKILL.md:25). Proposed.
- **D4 Who reviews, who rates, what range.** A fresh subagent each round: `code-reviewer.md` in a phase, which assigns Critical/Important/Minor (Verified, `code-reviewer.md:97-119`), and `plan-reviewer.md` in validation. The fixing session never re-rates. Round 1 reviews the whole unit; later rounds review only the latest fix and the code it touches (as SDD SKILL.md:395-403 does). Subagent-driven development's final review (SDD SKILL.md:445-469) counts as round 1. Proposed.
- **D5 How a finding closes.** Exactly one of: a real bug gets a failing test, a root-cause fix and a passing test; a wrong finding is rejected with evidence; a finding whose fix would change the design gets the smallest fix inside the design, or a recorded decision (what, why, cost if wrong, as in SDD SKILL.md:19-24), parked and listed in the end report. Minor findings from steps 4–6 are listed, not looped on. Proposed.
- **D6 No round cap; a stuck rule and four stop reasons.** If the same problem returns after a fix, or three fixes for one problem fail, the session stops patching and questions the design (systematic-debugging SKILL.md:195-210), records a decision and continues, rather than discussing first as :210 says. A finding the design causes is parked (D5, D16); any other stays open until its root cause is fixed, so no confirmed bug is waved through. It asks the maintainer only when the next step is destructive, is security-sensitive, needs an approval or authorization not already given (an approval gate from the repository rules or the report, or an outside effect), or the plan is too broken to follow (SDD SKILL.md:27-31). Maintainer.
- **D7 Readiness and debugging tools.** Step 8 is `superpowers:verification-before-completion`; a not-ready result goes to `superpowers:systematic-debugging`, then step 2. `superpowers:diagnosing-superpowers` asks the human questions and only reports (Verified, its SKILL.md:11-12, :23-24), so it is only for a post-mortem after a phase. Proposed.
- **D8 9a and 9b run once; every confirmed finding goes back.** `/code-review` and `/security-review` run once each on the final head. Every confirmed finding, Low included, goes back to step 2; `/code-review` gives no severity, so nobody has to rate its findings. Rejecting one needs evidence in the comment review. Maintainer.
- **D9 Fixes after 9a/9b.** A fix goes through steps 2–8; steps 4–6 review only the fix, and `/security-review` runs on the fix diff only. `/code-review` does not run again. The plan-to-main PR's full review is the backstop. Each comment review names the current head in `Head:` and lists what each review saw in `Scope:` lines (`/code-review` at its head; each fix range and its reviewer). Maintainer (posting Proposed).
- **D10 The planning unit's 9a/9b.** They run inside `/validate-plan`, read-only, once each before the step 8 render, on copies of the final plan and spec text (W-P4); fixes follow D9. If end-of-run answers change the plan or spec, the post-answer review already covers the whole revised documents (SKILL.md:51, :53), and `/security-review` runs once more on the answer edits only. Section 7 records the hash each review saw; `context.json` `documents` records the final hashes. The docs PR reuses both results only when it changes only the plan and spec, they hash to those final values, and section 7 records the exact input each review read and the security review's brief (W-P4); otherwise it gets a fresh, briefed review; it still posts both comment reviews on its head, each with a `Reused:` line naming the hash each review saw and the final hash, and sets both statuses. Otherwise both reviews run once on the changed lines and any other changed files. Unknown: whether both commands can target uncommitted or untracked files; the fallback is a saved diff file. In other hosts, "an equivalent independent review", as phase-workflow.md:17 says today. Maintainer (mechanics Proposed).
- **D11 After the PR opens.** A later commit, base change or conflict fix goes through steps 2–8 on that change only. The new head gets `## Code review` with `Scope: <old-head>..<new-head>` and the full review's URL, plus `## Security review` from `/security-review` on that change, and both statuses. This meets this repository's merge checks (`AGENTS.md:50, :53`) without a full re-review. Proposed.
- **D12 No `superpowers:finishing-a-development-branch`.** It ends in a menu and waits (Verified, its SKILL.md:53-80, :217); step 8 takes over its readiness role. Maintainer.
- **D13 In-flight plans.** One small docs PR per in-flight plan swaps in the new `## Phase workflow` section and adds one line under it: "Replaced on <date>: workflow steps only, no scope change." The next phase session reconciles that diff from the line (handoff-template.md:32-36), with no re-validation. Validation still adds the block only when a plan has none (phase-workflow.md:3, unchanged). In this repository the swap lands before the plan's next phase (W-A3). Maintainer (timing Proposed).
- **D14 Validation's own loop follows the same pattern.** No cap, plus the stuck rule. After round 1, each fresh reviewer gets the changes since the last round as `Review focus`, with earlier findings under `Findings already dispositioned`. Proposed.
- **D15 Skills are invoked, not just named.** When Superpowers is installed, each step loads its skill with the Skill tool, and a subagent that does a step loads that step's skill itself. Where a loaded skill says to stop and ask, the block's stop rule decides (S5). Proposed.
- **D16 A parked finding that needs a spec or plan change.** The phase PR still merges into the plan branch. The finding is listed as parked and tracked the way the repository's rules track review findings (an issue where they allow one; in this repository, which allows no extra labels or issues, AGENTS.md:46, :79, the code comment review and the end-of-phase report), and both statuses can pass (W-A6). Right after the merge, the end-of-phase report prints a design-update prompt before the next phase's prompt, which it marks as waiting for the new report (so the launch prompt's print instruction still holds): brainstorm the change with the maintainer, update the spec and plan with a fixing phase, then validate the remaining phases as a phase-only validation (Verified that path exists, handoff-template.md:36). The revised documents land through a docs PR into the same plan branch, and work continues from the new report. Nothing waits for the end of the plan, because later work built on a flaw costs more to fix. A security finding is never parked; one whose fix would change the design is a stop reason. Maintainer.

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
- **This repository's rules (`AGENTS.md`):** they point to the plan's Phase workflow (rows A0–A6).
- **A user's own repository rules:** they set which findings are required (the block's default is every confirmed finding, Low included) and how reviews are posted; the plugin text keeps deferring to them ("as this repository's rules require").
- **Superpowers:** unchanged. The plan's Phase workflow overrides it where they differ; user instructions take precedence over skills (Verified, using-superpowers SKILL.md:63).

## 7. Conflict table

| ID | Home | file:line | Conflict | Proposed change |
|---|---|---|---|---|
| P1 | plan-validation | `skills/validate-plan/references/phase-workflow.md:6-20` | Old 9 steps: step 6 has no stuck rule, step 7 runs finishing, step 8 defers to repository rules that may loop; no integration tests or done-check | Replace with W-P1 |
| P2 | plan-validation | `skills/validate-plan/SKILL.md:70`; `references/report-contract.md:64` | Nothing writes a done-check; section 8's contract has no place for one | Add W-P2 |
| P3 | plan-validation | `SKILL.md:41` | "There is no round cap" with no stuck rule; every round reviews everything; skills are named, not loaded | W-P3 |
| P4 | plan-validation | `SKILL.md:43` | No `/code-review` or `/security-review` in validation | Add W-P4 |
| P5 | plan-validation | `SKILL.md:26` | "Do not … post comments …" could read as forbidding the read-only review commands | Add W-P5 |
| P6 | plan-validation | `SKILL.md:51` | Post-answer loop "There is no round cap" with no stuck rule | W-P6 |
| P7 | plan-validation | `site/src/content/docs/phased-implementation.md:24-30, :36, :44-52, :63-68`; `docs/evaluation.md:49` | Old steps; security review only when flagged (:29, :63); docs-only PRs need CI only or a looping full-plan review (:36, :44-52, :68) | W-P7 |
| P8 | plan-validation | `skills/validate-plan/handoff-template.md:12, :22, :26`; `docs/evaluation.md:61` | "Pause only for required approvals or unfixable failures" is vaguer than the stop reasons; :26 and the evaluation row explain the old sentence | W-P8 (same length; plans with an older block or none keep the old sentence) |
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
| S5 | superpowers | receiving-code-review `SKILL.md:44-45, :82-83`; test-driven-development `SKILL.md:24-27`; using-git-worktrees `SKILL.md:41, :130` | Stop and ask, ask for consent, or ask whether to proceed | No edit; overridden by W-P1's stop rule (step 1 gives the worktree consent) |

## 8. Proposed wording

### W-P1: `references/phase-workflow.md`, the block from `## Phase workflow` to the docs-only sentence

```markdown
## Phase workflow

Every phase follows these steps, in a fresh session, on its own phase branch. When Superpowers is installed, load each named skill with the Skill tool at its step; a subagent that does a step loads that step's skill itself, and its brief says so. Where a loaded skill says to stop and ask, to ask for consent or to wait for the human partner, this block's stop rule (below) decides instead. Without Superpowers, follow the step as written.

1. Work in a git worktree for the phase branch (`superpowers:using-git-worktrees`). Read the phase's done-check in section 8 of the validation report, when it has one.
2. For each task, write the failing tests first and watch them fail for the expected reason, the feature missing and not a typo (`superpowers:test-driven-development`): a unit test, plus an integration test when the task crosses a boundary (database, API, authentication, another service).
3. Write the minimal code that makes the tests pass, keep all tests green, then refactor. Repeat steps 2–3 for each task.
4. Review the phase with a fresh reviewer (`superpowers:requesting-code-review`), given the plan and spec paths and the report path named in the phase prompt. Round 1 reviews the phase's base..head range; later rounds review only the latest fix and the code it touches. When `superpowers:subagent-driven-development` ran the tasks, its final review is round 1. The reviewer sets each finding's severity (Critical counts as High, Important as Medium, Minor as Low).
5. Check each finding against the code before acting (`superpowers:receiving-code-review`) and close it one way: a real bug gets a failing test, a root-cause fix and a passing test; a wrong finding is rejected with evidence; a finding whose fix would change the design gets the smallest fix inside the design, or a recorded decision (what, why, cost if wrong) listed in the end-of-phase report. A security finding is never parked: if its fix would change the design, ask the maintainer.
6. Repeat steps 4–5 until no Medium or High finding remains. There is no round cap. If the same problem returns after a fix, or three fixes for one problem fail, stop patching and question the design (step 7). If the design is the cause, park the finding as step 5 does and continue; otherwise fix the root cause. The finding stays open until it is fixed, rejected with evidence or parked. List Low findings without looping on them; the end-of-phase report asks the maintainer to fix or skip each one.
7. For any failing test or unexpected behavior, find the cause before fixing it (`superpowers:systematic-debugging`), then return to step 2.
8. Prove the phase is ready (`superpowers:verification-before-completion`): run the done-check commands, if any, and the full unit and integration suites, read the output, and claim only what it shows. If anything fails, go to step 7.
9. Run the code review and the security review once each on the final head, as this repository's rules require (in Claude Code, `/code-review` and `/security-review`; in other hosts, an equivalent independent review). Close every confirmed finding as step 5 does, Low included unless the repository's rules make Low findings optional (then list them), with any fix going through steps 2–8; step 4 reviews only the fix, and the security review runs again on the fix only. Never repeat either review on unchanged code unless the repository's rules require it.
10. Deliver the branch as the repository's rules define (for a plan branch, a PR into that branch), and never merge locally into a protected or plan branch. Push and open a PR only when the repository's rules or the maintainer authorize it; otherwise stop and report that the branch is ready. A later commit, such as a CI fix, goes through steps 2–8 on that change only, and the security review runs on that change only, unless the repository's rules require both reviews again on the new head. Do not run `superpowers:finishing-a-development-branch`. If a parked finding needs a spec or plan change, print a design-update prompt before the next phase's prompt, and mark that prompt as waiting for the new report: brainstorm the change with the maintainer, update the spec and plan with a fixing phase, and validate the remaining phases.

Ask the maintainer only when the next step is destructive, is security-sensitive, needs an approval or authorization not already given (such as a merge, an install or another outside effect), or the plan is too broken to follow. Otherwise decide, record the decision and continue.

A docs-only phase skips step 2's test-first rule. Its step 9 runs the reviews the repository's rules require for docs-only changes.
```

### W-P2: SKILL.md:70 (phase grouping), append; `references/report-contract.md:64`

> For each phase, write one done-check in section 8 on its own unfenced line before the phase prompts (`Done-check, Phase <id>: …`; a fenced block would count as a prompt). It lists commands to run later, not results: the phase's unit and integration test commands, the integration test that proves a task crossing a boundary, and the full unit and integration suites. Name only tests that exist once the phase is done (existing tests and those of that phase's and earlier phases' tasks), never one a later phase adds. Build it from the task test commands step 5 rehearsed or reviewed; do not run it again for the report. Adding a missing test or assertion inside a task is an in-task repair; new test infrastructure needs approval.

In `references/report-contract.md:64` (section 8), replace "a one-line suggested effort covering all phases, then one fenced launch prompt per ready phase" with "a one-line suggested effort covering all phases, one unfenced done-check line per phase (SKILL.md, Phase grouping), then one fenced launch prompt per ready phase", and "so write only the effort line, the between-phases note and the fenced prompts" with "so write only the effort line, the done-check lines, the between-phases note and the fenced prompts".

### W-P3: SKILL.md step 6, replace "Fix verified Medium and High findings in the plan or spec, then review again with a fresh agent, until none remain; there is no round cap."

> When Superpowers is installed, load `superpowers:requesting-code-review` and `superpowers:receiving-code-review` with the Skill tool before the first round; the bundled `plan-reviewer.md` brief replaces that skill's template and commit range, because the documents are uncommitted. Fix verified Medium and High findings in the plan or spec, then review again with a fresh agent, until none remain. After the first round, give each new reviewer the changes since the last round as `Review focus` and the earlier findings under `Findings already dispositioned`. There is no round cap. If the same finding returns after a fix, or three fixes for one problem fail, stop editing that part: question the approach (`superpowers:systematic-debugging` when installed), and record the open finding as a pending approval in section 6 and `open_decisions`, as end-of-run item 7 does, never in `decisions_without_reply`; its phases wait, and the loop continues for the rest.

### W-P4: SKILL.md step 8, add before "Before scoring, check that every claim"

> Run `/code-review high` and `/security-review` once each, read-only (in other hosts, an equivalent independent review), on copies of the final PLAN and SPEC saved in the run directory, never the live files. Target the copies as a path or a saved diff of the whole documents. `/security-review` reads only a branch's committed diff and skips documentation files, so run its procedure in a fresh subagent on the saved diff, with a brief that puts the plan and spec text in scope as a behavioral contract; do the same for `/code-review` when it cannot take the target. Record in section 7 the exact input each review read and, for the security review, its brief. If neither can run, disclose the gap and set `review_status` to a value other than `complete`, as end-of-run item 9 does. Close every confirmed finding, Low included: fix it in the plan or spec, reject it with evidence, or, when its fix would change requirements, architecture, security boundaries or scope, record it as a pending approval as end-of-run item 7 does. A fresh step 6 reviewer and `/security-review` check only each fix; neither command runs again on unchanged text. A fix that changes a rehearsed task's commands, files or test assertions is rehearsed again under end-of-run item 5's rules. Record in section 7 the commands, targets, results and the hash each review saw; `context.json` `documents` records the final hashes. If end-of-run answers later change PLAN or SPEC, the post-answer review (item 6) covers the whole revised documents, and `/security-review` runs once more on the answer edits only, before the re-render; a fix it needs follows item 8.

### W-P5: SKILL.md:26, append

> Running `/code-review` with an explicit local level (`high`; never `max`, `ultra` or no level, which reuses the last level typed) and without `--fix`, `--comment` or `--post`, and running `/security-review`, is allowed: both only report.

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

Replace :44-52 with:

> Docs-only PRs get the reviews your repository requires. The plan-validation repository, for example, asks for a code review and a security review on every PR into `main` or a plan branch. A plan's docs PR can reuse the reviews validation already ran: validation runs `/code-review` and `/security-review` once each on the final plan and spec and records their hashes in the report. When the docs PR changes only that plan and spec and their hashes match, post those results with a `Reused:` line; otherwise review the changed lines once. A docs-only phase PR gets both reviews once on its final head.

In the text to paste:

- :63: replace with "- Follow the plan's Phase workflow section: worktree, test-first tasks with unit tests and, across boundaries, integration tests, review until no Medium or High finding remains, readiness check with the done-check and full suites, then the code review and the security review once each on the final head."
- :65: append "A later commit gets a review of that change only."
- :66: after "print the next phase's prompt from the report", add ", after the design-update prompt when a parked finding needs a spec or plan change".
- :68: replace with "- Docs-only PRs get the reviews your repository requires. A plan's docs PR can reuse validation's `/code-review` and `/security-review` results when it changes only the plan and spec and their hashes match the report; otherwise review the changed lines once."

In `docs/evaluation.md:49` (Docs-PR review), replace the description with "A plan's docs PR reuses the validation run's `/code-review` and `/security-review` results, each posted with a `Reused:` line, when it changes only the plan and spec and their hashes match the report; otherwise both review the changed lines once. A docs-only phase PR gets both once on its final head."

### W-P8: handoff-template.md:12, replace the pause sentence

> Pause only for the Phase workflow's stop reasons.

And add to the variants (:17-22): "**Plan whose Phase workflow has no stop-reasons sentence** (an older block, or no section): keep 'Pause only for required approvals or unfixable failures.'"

At :26, replace "while keeping approval gates from repository rules and the report, such as a merge that needs the maintainer, inside the prompt itself" with "while keeping approval gates from repository rules and the report, such as a merge that needs the maintainer: the Phase workflow's stop reasons include any approval or authorization not already given, and the older pause sentence names required approvals directly".

In `docs/evaluation.md:61` (Implementation handoff), replace "it pauses only at a required approval or an unfixable failure" with "it pauses only for the stop reasons of the plan's Phase workflow (with an older block, a required approval or an unfixable failure)".

### W-P9: top of the 2026-11-05 spec

> Note (2026-11-11): line 136 misreads the global rule, which caps only rounds with Low findings left. Superseded by `2026-11-11-one-review-workflow-design.md`.

### W-A0: `AGENTS.md:51`, replace the whole bullet

> - Code and security review means a code review and a security review of the PR diff (after a new push, of the pushed change, as below), with findings fixed, explicitly accepted or parked as below (in Claude Code, `/code-review` and `/security-review` once on the PR diff, then the reviews of later changes described below; in other hosts, an equivalent independent review). On a plan's docs PR, the validation run's reviews may be reused (see below).

### W-A1: plan-validation `AGENTS.md:52`, replace from "On a plan's docs PR or a docs-only phase PR" to "Other docs-only PRs keep `/code-review`."

> On a plan's docs PR, reuse the validation run's recorded code and security reviews when the PR changes only the plan and spec, their hashes match the report, and its section 7 records the exact input each review read and the security review's brief, posting each with a `Reused:` line; otherwise review the changed lines once. A docs-only phase PR gets `/code-review` and `/security-review` once each on its final head, like other docs-only PRs. A finding whose fix would change a security or privacy boundary, a permission or an external action, or that shows a recorded decision causes a defect, is a stop reason and goes to the maintainer; a finding that only disagrees with a decision the maintainer recorded (not one the agent recorded itself, and never a security finding) is rejected with that decision as evidence and listed in the code comment review.

### W-A2: `AGENTS.md:53`, replace "A new push needs both reviews again."

> A fix after `/code-review`, before or after the PR opens, gets a fresh reviewer (`superpowers:requesting-code-review`) on that change and the code it touches, and `/security-review` on that change; `/code-review` does not run again. Each comment review names the current head in `Head:` and lists in `Scope:` lines what each review saw (`/code-review` at its head; each fix range and its reviewer). For a plan phase, as its Phase workflow's steps 9 and 10 describe.

### W-A3: `AGENTS.md:57`, replace from "Each phase follows" to "a second round after step 9."

> Each phase follows the plan's Phase workflow section. The bullets below add this repository's specifics to its review and delivery steps (steps 4–10); they are not extra review rounds. A plan still on the older block (no step 10) gets its block-swap docs PR (D13) before its next phase starts.

### W-A4: `AGENTS.md:60`, replace the whole bullet

> Phase review, before opening the PR: follow the plan's Phase workflow review loop and readiness check (steps 4–8). List minor items in the code comment review; the end-of-phase report asks the maintainer to fix or skip each, and skipped or unanswered ones are saved as action points for the plan-to-`main` review.

### W-A5: `AGENTS.md:62`, replace "then stop and print the next phase's prompt from the report."

> then stop and print the next phase's prompt from the report, after the design-update prompt when a parked finding needs a spec or plan change (Phase workflow step 10).

### W-A6: `AGENTS.md:53`, replace "`success` only when every finding is fixed or explicitly accepted"

> `success` only when every finding is fixed, explicitly accepted, or parked under the Phase workflow's design rule and listed first in the end-of-phase report (a security finding is never parked)

## 9. Left to the builder

- The PR split for the plugin release, this repository's `AGENTS.md` and the site page.
- Ordering: land W-A3's older-block clause no later than this release, so no plan is left with two rules that point at each other.
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
