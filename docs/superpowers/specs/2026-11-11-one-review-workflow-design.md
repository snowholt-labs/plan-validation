# One review workflow for validated plans: design

Date: 2026-11-11. Status: approved by the maintainer on 2026-11-11. On 2026-11-12 the exact wording of each change moved to the implementation plan (O6). Supersedes the round-cap notes in `2026-11-05-review-loops-without-revalidation-design.md`.

Scope: this document covers the plan-validation plugin and this repository's own rules. Matching changes to the maintainer's private configuration and private repositories are tracked outside this repository.

Evidence labels: **Verified** (file:line), **Assumption**, **Unknown**. Decision owners: **Maintainer** (decided by the maintainer) or **Proposed** (a default set while writing the design; the maintainer approved those in the 2026-11-11 design, and later ones stay open to change in the plan).

## 1. Intent and why

One review workflow, followed the same way by the plugin, this repository's rules and the plans the plugin writes, for both planning and implementation. Every review step runs once on any given text. Confidence that the work is right comes from how each finding is closed, not from repeating full reviews.

Why now (field use in private projects, anonymized):

- One phase ran 26 `/code-review` rounds, which took most of its active time.
- In another phase, a one-line CI test fix after the PR opened triggered a full re-review under a rule like this repository's `AGENTS.md:53` ("A new push needs both reviews again"). That review found 5 new Medium findings in code the first round had passed. Four more rounds followed, changing 14 files (+587/−89).
- Validation loops churn too: one run took 14 review rounds before the end-of-run answers and 18 after.
- Naming a skill is not invoking it. Across 17 audited phases, `receiving-code-review` was invoked in none and `systematic-debugging` in one.

Maintainer's principle: one good process, even if it looks expensive, costs less than repeated failed loops or work that has to be patched again.

## 2. Goals, non-goals, anti-goals

Goals:
- One pipeline (section 3) for two units: the plan and spec during `/validate-plan`, and one plan phase during implementation.
- `/code-review` and `/security-review` each run at least once per code unit, and never twice on unchanged text within a unit. A docs-only unit gets the reviews the repository's rules require. The plan-to-main PR's full review and the full re-review after a push to a PR into `main` (D9, D11) are deliberate exceptions.
- Unit tests for every task with observable behavior, and integration tests where a task crosses a boundary. Coverage grows phase by phase.
- No pause to ask the maintainer except for the four stop reasons (D6).
- Each rule has one home. Other files point to it rather than copying it.

Non-goals:
- Editing Superpowers (a third-party plugin; updates would overwrite edits). Overrides live in the plan's Phase workflow.
- A report format bump, new `context.json` fields or renderer changes.
- Migrating saved reports.

Anti-goals (a failure even if it technically works):
- Full `/code-review` or `/security-review` runs repeated on unchanged code within a phase or a validation run.
- A session that stops to ask "continue?" or presents a menu and waits.
- A round cap that lets a confirmed High or Medium bug ship.
- A confirmed, in-design bug left unfixed.

## 3. The pipeline

The same ten steps for both units.

| Step | Implementation unit (one phase) | Planning unit (plan + spec in `/validate-plan`) |
|---|---|---|
| 1 Scope | The phase's tasks and its done-check (report section 8) | The plan and spec scope (SKILL.md step 1) |
| 2 Failing tests | A unit test, plus an integration test when the task crosses a boundary (database, API, authentication, another service); each fails for the expected reason | A rehearsal command or coverage check that fails on the original plan (Assumption: the existing rehearsal, SKILL.md:40) |
| 3 Pass | Minimal code until green, all tests green, then refactor; repeat 2–3 per task | Plan or spec repair for a plan defect until the rehearsal passes; an environment cause is recorded as a limitation (SKILL.md:40) |
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
- **D2 Tests.** Each task with observable behavior writes a failing unit test first; a task that crosses a boundary also writes a failing integration test first. Wording-only, configuration, version and changelog tasks, and fixes of that kind, skip the test-first rule, like a docs-only phase, so repository rules such as `AGENTS.md:40` ("Do not test wording for its own sake") still hold. Step 8 runs the full unit and integration suites, so later phases re-run earlier phases' tests. No coverage-percentage gate. Maintainer (exemption Proposed).
- **D3 Done-check.** Validation writes one done-check per report phase in report section 8, before the phase prompts, as commands to run later (section 7 holds only results from this run: SKILL.md:43, report-contract.md:63): the phase's test commands, the integration test that proves a boundary-crossing task, and the full suites. It is not written into the plan, because the phase grouping lives only in the report (Verified, SKILL.md:70). It names only tests that exist once the phase is done, never one a later phase adds, and is built from the task test commands that validation rehearsed or reviewed. A phase with no done-check (an older report) runs the full suites at step 8. Assumption: the renderer accepts these lines in section 8, as it does the between-phases note (handoff-template.md:34), provided they are not fenced (render_report.py counts each fenced block as a prompt); confirm with a render. Maintainer.
- **D3a What validation may add.** A missing test or assertion inside an existing task is an in-task repair (SKILL.md:39). New test infrastructure (a service, container, dependency or CI job) changes scope and becomes a pending approval (SKILL.md:25). Proposed.
- **D4 Who reviews, who rates, what range.** A fresh subagent each round: `code-reviewer.md` in a phase, which assigns Critical/Important/Minor (Verified, `code-reviewer.md:97-119`; Critical counts as High, Important as Medium, Minor as Low, as phase-workflow.md:15 says today), and `plan-reviewer.md` in validation, whose brief replaces `requesting-code-review`'s template and commit range because the documents are uncommitted (SKILL.md:41). The fixing session never re-rates. In a phase, round 1 reviews the whole unit and later rounds review only the latest fix and the code it touches (as SDD SKILL.md:395-403 does). In validation, every round gets the current documents with the changes as `Review focus` (D14, plan-reviewer.md:3), and the post-answer review covers the whole revised documents. Subagent-driven development's final review (SDD SKILL.md:445-469) counts as round 1. Proposed.
- **D5 How a finding closes.** Each Medium or High finding closes exactly one way: a real bug gets a failing test, a root-cause fix and a passing test; a wrong finding is rejected with evidence; a finding whose fix would change the design gets the smallest fix inside the design, or a recorded decision (what, why, cost if wrong, as in SDD SKILL.md:19-24), parked and listed in the end report. Low findings from steps 4–6 are listed, not looped on; the end-of-phase report asks the maintainer to fix or skip each. A security finding is never parked: if its fix would change the design, or it stays stuck under D6, that is a stop reason. Proposed.
- **D6 No round cap; a stuck rule and four stop reasons.** No round cap applies, including subagent-driven-development's per-task breaker (S6). If the same problem returns after a fix, or three fixes for one problem fail, the session stops patching and questions the design (systematic-debugging SKILL.md:195-210), rather than discussing first as :210 says. If the design is the cause, or the root cause still cannot be fixed, the finding is parked with a recorded decision and fixed in a fixing phase right after the merge (D16, O4); a security finding is never parked, and for a stuck one any further fix is a security-sensitive action, so the session stops and asks. The session asks the maintainer only when the next step is destructive, is a security-sensitive action (SDD's wording, SDD SKILL.md:27-31; not every step of a security-sensitive phase), needs an approval or authorization not already given (an approval gate from the repository rules or the report, or an outside effect such as a merge or an install), or the plan is too broken to follow, including an environment that cannot run a required check. Maintainer.
- **D7 Readiness and debugging tools.** Step 8 is `superpowers:verification-before-completion`; a not-ready result goes to `superpowers:systematic-debugging`, then step 2. `superpowers:diagnosing-superpowers` asks the human questions and only reports (Verified, its SKILL.md:11-12, :23-24), so it is only for a post-mortem after a phase. Proposed.
- **D8 9a and 9b run once; every confirmed finding goes back.** `/code-review` and `/security-review` run once each on the final head, at a fixed local level with no cap on the number of findings. Every confirmed finding, Low included, goes back to step 2 or is rejected with evidence in the comment review; `/code-review` gives no severity, so nobody rates its findings and none is skipped as Low. The report's per-phase `security_review` flag (SKILL.md:76; render_report.py:471 rejects it on a docs-only phase) keeps marking security-sensitive phases for review focus; it no longer decides whether `/security-review` runs. Maintainer (level and flag note Proposed).
- **D9 Fixes after 9a/9b.** A fix goes through steps 2–8; in a phase, steps 4–6 review only the fix (in validation, the next round reads the current documents with the fix as `Review focus`, D4), and `/security-review` runs on the fix diff only. `/code-review` does not run again. The plan-to-main PR's full review is the backstop. Each comment review names the current head in `Head:` and lists what each review saw in `Scope:` lines (`/code-review` at its head; each fix range and its reviewer). Maintainer (posting Proposed).
- **D10 The planning unit's 9a/9b.** They run inside `/validate-plan`, read-only, once each before the step 8 render, on saved copies of the final plan and spec text; fixes follow D9, and a fix that changes a rehearsed task's commands, files or test assertions is rehearsed again. If end-of-run answers change the plan or spec, the post-answer review already covers the whole revised documents (SKILL.md:51, :53), and `/security-review` runs once more on the answer edits only. Section 7 records the exact input each review read and the hash it saw; `context.json` `documents` records the final hashes. How a review that cannot run is recorded is left to the plan (section 8), within the non-goals. The docs PR reuses both results only when it changes only the plan and spec, they hash to the final values, and section 7 records what each review read. It then still posts both comment reviews on its head, each with a `Reused:` line naming the hash each review saw and the final hash, plus a `Scope:` line naming what covered any answer edits (the post-answer review for the code review, the second `/security-review` run for the security review; D9), and sets both statuses. Otherwise each review runs once: on what differs from the text it read, when section 7 records where that text can still be read and it still matches the recorded hash, or on the full plan and spec when it cannot; either way plus any other changed files, so no status passes on text no review read. Unknown: whether either command can target uncommitted plan and spec text; `/security-review` reads only a branch's committed diff and skips documentation files, so it likely needs its procedure run in a briefed subagent on a saved diff. In other hosts, "an equivalent independent review", as `AGENTS.md:51` says. Maintainer (mechanics Proposed).
- **D11 After a phase PR opens.** A later commit, base change or conflict fix on a phase PR goes through steps 2–8 on that change only. The new head gets `## Code review` with a `Scope:` line for the change and the full review's URL, plus `## Security review` from `/security-review` on that change, and both statuses. This meets this repository's merge checks (`AGENTS.md:50, :53`) without a full re-review. Other PRs, including every PR into `main` and the plan-to-main PR, get both full reviews again after a push (O5). Maintainer.
- **D12 No `superpowers:finishing-a-development-branch`.** It ends in a menu and waits (Verified, its SKILL.md:53-80, :217); step 8 takes over its readiness role. The new block keeps the old guards: never merge locally into a protected or plan branch, and without authorization to push, stop and report that the branch is ready (phase-workflow.md:16, :18). Maintainer.
- **D13 In-flight plans.** One small docs PR per in-flight plan swaps in the new `## Phase workflow` section and adds one line under it: "Replaced on <date>: workflow steps only, no scope change." The next phase session reconciles that diff from the line (handoff-template.md:32-36), with no re-validation. The swap PR lists any boundary-crossing task that has no integration test infrastructure, as a D3a approval the maintainer settles on that PR. Validation still adds the block only when a plan has none (phase-workflow.md:3, unchanged). The new block carries a marker that tells it apart from the older block, so validation and repository rules can pick the right pause sentence and step numbers. In this repository the swap lands before the plan's next phase. Maintainer (listing and timing Proposed).
- **D14 Validation's own loop follows the same pattern.** No cap, plus the stuck rule. A finding still open under the stuck rule becomes an implementation blocker in section 6 (the verdict is Not ready), never a `decisions_without_reply` entry; one whose fix would change requirements, architecture, security boundaries or scope stays a pending approval, as today (SKILL.md:41, :52). The run still finishes without pausing. After round 1, each fresh reviewer gets the changes since the last round as `Review focus`, with earlier findings under `Findings already dispositioned`. Proposed.
- **D15 Skills are invoked, not just named.** When Superpowers is installed, each step loads its skill with the Skill tool, and a subagent that does a step loads that step's skill itself. Where a loaded skill says to stop and ask, ask for consent or wait for the human partner, the block's stop rule decides instead (S5). Proposed.
- **D16 A parked finding.** The phase PR still merges into the plan branch. The finding is listed first in the code comment review, and both statuses can pass. It is tracked as the repository's rules allow: an issue where they allow one; in this repository, which opens no extra issues (`AGENTS.md:46, :78`), the merged phase PR's code comment review. The end-of-phase report, printed when the phase session stops, puts a design-update prompt before the next phase's prompt and marks that prompt as waiting for the new report, so the launch prompt's instruction to print it still holds. The maintainer runs it right after the merge: brainstorm the change, update the spec and plan with a fixing phase, then validate the remaining phases as a phase-only validation (Verified that path exists, handoff-template.md:36). The revised documents land through a docs PR into the same plan branch, and work continues from the new report. Every phase also writes each parked finding to a durable record, and the block's step 1 makes each phase session read the previous phase's record and not start while it lists an unfixed finding and no newer report exists, so a saved prompt cannot skip the redesign. The record's form is left to the plan (section 8). The plan-to-main review checks that every parked finding is fixed. Nothing waits for the end of the plan, because later work built on a flaw costs more to fix. Maintainer.

## 5. Answers to the seven design questions

1. **Exit if the loop keeps finding issues:** no cap; the stuck rule and the four stop reasons (D6).
2. **Who sets severity:** the fresh steps 4–6 reviewer, never the fixer (D4). `/code-review` findings need no rating, because every confirmed one is fixed or rejected with evidence (D8).
3. **Review range per round:** in a phase, round 1 covers the whole unit and later rounds the latest fix, while every validation round reads the current documents with the changes as focus (D4); 9a/9b cover the whole unit once (D8); after a phase PR opens, only the change (D11).
4. **SDD's final review:** round 1 of steps 4–6 (D4); its one-fix-wave limit and its per-task breaker are replaced by the step 6 loop (D6).
5. **Step 7 and the menu:** finishing is dropped (D12); the handoff keeps "do not ask", and its pause sentence points to the stop reasons (D6).
6. **Old notes that point away from the built-in reviews:** delete them once the rules change (tracked privately).
7. **plan-validation's no-cap loop:** same pattern (D14).

## 6. Where each part lives

- **The pipeline:** this plugin. A phase's steps live in `references/phase-workflow.md`, copied into each plan; the planning unit's steps live in `skills/validate-plan/SKILL.md`.
- **This repository's rules (`AGENTS.md`):** they point to the plan's Phase workflow (rows A0–A7).
- **A user's own repository rules:** they set how reviews are posted and may require more reviews; the plugin text keeps deferring to them ("as this repository's rules require").
- **Superpowers:** unchanged. The plan's Phase workflow overrides it where they differ; user instructions take precedence over skills (Verified, using-superpowers SKILL.md:63).

## 7. Conflict table

Each row names a file that conflicts with the design and the decisions its change follows. The exact wording is left to the implementation plan (section 8).

| ID | Home | File | Conflict | Change follows |
|---|---|---|---|---|
| P1 | plan-validation | `skills/validate-plan/references/phase-workflow.md` (the block) | Old 9 steps: step 6 has no stuck rule, step 7 runs finishing, step 8 defers to repository rules that may loop; no integration tests or done-check | New ten-step block: D1, D2, D4–D9, D12, D15, D16 |
| P2 | plan-validation | `skills/validate-plan/SKILL.md` (phase grouping); `references/report-contract.md` (section 8) | Nothing writes a done-check; section 8 holds only the effort line, the between-phases note and the prompts | D3 |
| P3 | plan-validation | `SKILL.md` step 6 | "There is no round cap" with no stuck rule; every round reviews everything; skills are named, not loaded | D4, D14, D15 |
| P4 | plan-validation | `SKILL.md` step 8 | No `/code-review` or `/security-review` in validation | D10 |
| P5 | plan-validation | `SKILL.md` research and approval rules | "Do not … post comments …" could read as forbidding the read-only review commands; no rule keeps `/code-review` at a local level | D8, D10 |
| P6 | plan-validation | `SKILL.md` end-of-run post-answer review | "There is no round cap" with no stuck rule | D14 |
| P7 | plan-validation | `site/src/content/docs/phased-implementation.md` (the step list, "Other rules", "Reviewing a plan's docs PRs" and the text to paste); `docs/evaluation.md` (Docs-PR review row) | Old steps; security review only when flagged; docs-only PRs need CI only, or a looping full-plan review | D1–D12, D16 |
| P8 | plan-validation | `skills/validate-plan/handoff-template.md` (pause sentence, variants, explanation); `docs/evaluation.md` (Implementation handoff row) | "Pause only for required approvals or unfixable failures" is vaguer than the stop reasons | D6; plans on an older block, or with none, keep the old sentence |
| P9 | plan-validation | `docs/superpowers/specs/2026-11-05-review-loops-without-revalidation-design.md` (its round-cap remark) | Conflicts with the no-cap design | A one-line superseded note; the history stays as written |
| P10 | plan-validation | `CHANGELOG.md`, three manifests | Behavior change in skill text | Minor release entry; new `docs/evaluation.md` rows (AGENTS.md:39) |
| P11 | plan-validation | `SKILL.md:76`; `references/html-report.md` (the flag); `render_report.py` (the phase table's "Security review" column); site `phased-implementation.md`, `reports-and-handoffs.md` | The per-phase flag reads as whether a security review runs | D8 |
| P12 | plan-validation | site `reports-and-handoffs.md`, `first-run.md`, `features.md` | Describe the old validation loop and pause sentence | D6, D10, D14 |
| A0 | repo rule | `AGENTS.md:51` | Makes the full-plan review the code review on docs PRs and docs-only phase PRs; defines the code review as `/code-review` of the PR diff | D9, D10 |
| A1 | repo rule | `AGENTS.md:52` | The docs PR runs a looping full-plan review instead of reusing the validation reviews | D10 |
| A2 | repo rule | `AGENTS.md:53` | "A new push needs both reviews again" applies to phase PRs too | D9, D11 (phase PRs only, O5) |
| A3 | repo rule | `AGENTS.md:57` | Points to "steps 8 and 9" and "after step 9"; the new block uses steps 4–10 | D13 (swap older blocks before the next phase) |
| A4 | repo rule | `AGENTS.md:60` | A 5-round cap, then "ask the maintainer" | D6 |
| A5 | repo rule | `AGENTS.md:62` | Always prints the next phase's prompt, even when a parked finding needs a redesign | D16 |
| A6 | repo rule | `AGENTS.md:53` | `success` "only when every finding is fixed or explicitly accepted" blocks a parked finding's merge | D16 |
| A7 | repo rule | `AGENTS.md:40` | Test-first for every task would force wording tests | None needed: D2 exempts wording, configuration and version tasks |
| S1 | superpowers | SDD `SKILL.md:445-469` | Final review allows one fix wave | No edit; overridden by the block's steps 4–6 |
| S2 | superpowers | SDD `SKILL.md:487` | "Use superpowers:finishing-a-development-branch" | No edit; overridden by the block's step 10 (D12) |
| S3 | superpowers | systematic-debugging `SKILL.md:210` | "Discuss with your human partner before attempting more fixes" | No edit; overridden by the block's step 6 (D6) |
| S4 | superpowers | finishing `SKILL.md:217` | "Present the menu and wait." | Not used (D12) |
| S5 | superpowers | receiving-code-review `SKILL.md:44-45, :82-83`; test-driven-development `SKILL.md:24-27`; using-git-worktrees `SKILL.md:41, :130` | Stop and ask, ask for consent, or ask whether to proceed | No edit; overridden by the block's stop rule (D15); step 1 gives the worktree consent |
| S6 | superpowers | SDD `SKILL.md:411-429` | Per-task breaker: after 5 review rounds, open findings are parked, real ones included | No edit; overridden by the block's step 6 (D6) |

## 8. Left to the implementation plan

The plan writes the exact wording for each row in section 7, and `/validate-plan` reviews it. A wording draft from the design reviews exists outside the repository; the plan may start from it. Five code-review rounds on that draft raised these points, which the wording must settle:

- **Review targets.** Aim step 9's `/code-review` at the phase's base..head range, and `/security-review` at a fix-only or change-only diff; by default both read the branch against its upstream or the default branch. Target uncommitted plan and spec copies in validation (D10, Unknown), with a briefed subagent running the command's procedure on a saved diff as the fallback. Set the `Scope:` range after a rebase or base merge, where `<old-head>..<new-head>` holds other commits.
- **Review settings.** Run `/code-review` at a fixed local level (never `max` or `ultra`, never with no level, which reuses the last level typed), with no cap on findings, and never with `--fix`, `--comment` or `--post`. An explicit level and finding limit persist as the user's saved choice, so the plan says whether that lasting change is acceptable or how to avoid it. Wait for its background result before scoring.
- **Review gaps.** What validation records when a review cannot run, without making every run Not ready while targeting is unsolved.
- **Delegated briefs.** Validation's review subagents carry `plan-reviewer.md`'s limits (no secrets, no installs, no plan steps, lookups only as research status allows), and the security brief puts plan and spec text in scope, since `/security-review` skips documentation files by default.
- **Done-check format.** An unfenced line per phase in section 8, and matching wording in `report-contract.md` section 8, which today allows only the effort line, the between-phases note and the prompts.
- **Handoff limits.** Keep every phase prompt within 80 words; give plans on an older block, or with none, the old pause sentence.
- **Block marker.** The marker that tells the new block from the older one (D13), and the step 1 check of the previous phase's parked-finding record (D16).
- **Parked-finding record.** A form every phase writes and the next phase's step 1 reads (D16): it survives a fresh session, a squash merge and a PR opened by the maintainer, and needs no commit after the reviewed head.
- **The security column (P11).** Relabel or explain the report's "Security review" column. A relabel is a renderer change: it needs the maintainer's approval against the non-goal, and gating to version 5 output, because versions 1–4 output is frozen (`test_legacy_output_is_frozen`, `test_v4_saved_output_is_frozen`).
- **Line references.** Cite edits by quoted text, not line numbers, because each edit shifts the lines below it.
- **Release mechanics.** The PR split, the order (land the older-block clause no later than the release), the version number and the CHANGELOG entry.
- **Codex wording.** The exact wording for "an equivalent independent review" in the planning unit.
- **In-flight plans.** Finding them (D13).
- **Evaluation.** New `docs/evaluation.md` rows for the stuck rule, the done-check and validation's two reviews (AGENTS.md:39).

## 9. Questions answered by the maintainer

- **O1:** a fix after 9a/9b, or a post-PR commit, also gets `/security-review` on that change only.
- **O2:** confirmed Low `/code-review` findings go back to step 2 too.
- **O3:** a parked design finding merges and is tracked, and the redesign happens right after the merge, before the next phase (D16).
- **O4 (2026-11-12):** a finding that keeps returning when the design is not the cause is also parked and fixed in a fixing phase right after the merge, before the plan reaches `main` (D6).
- **O5 (2026-11-12):** the change-only review after a push applies to phase PRs only; other PRs, including those into `main`, get both full reviews again (D11).
- **O6 (2026-11-12):** the exact wording moves from this design to the implementation plan, after five review rounds on the wording draft found 10, 10, 15, 15 and 15 points without converging.

## 10. Builder check

A fresh builder read the design on 2026-11-11. Its questions were settled as follows:
- Done-check location for report-only phases: report section 8, not the plan (D3).
- Whether validation may add tests: in-task tests yes; new test infrastructure needs approval (D3a).
- Drift from the in-flight docs PRs: a one-line note under the new section; no re-validation (D13).
- Rating `/code-review` findings: no longer needed (O2).
- Parked findings at merge: became O3.
