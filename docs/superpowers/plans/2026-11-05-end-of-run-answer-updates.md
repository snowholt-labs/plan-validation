# End-of-run Answer Updates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the three known limitations of the end-of-run question round from 0.6.0. Answer edits are tested again, reviewed and recorded so the prompts stay current. A published page is updated even without `artifact.json`, or the reply says it is stale. With no online update, the report reopens in the browser.

**Architecture:** Skill text only. `SKILL.md` workflow step 8 and `references/html-report.md` gain the post-answer rehearsal, review and hash refresh, the update by the session's known URL, and the `--open` rule. Evaluation cases, site pages and the changelog follow. The renderer already compares live files with the recorded hashes and already supports `--open`, so it does not change.

**Tech Stack:** Markdown skill text, Python 3.10+ standard library checks (`scripts/check_package.py`, `unittest`), Astro docs site (`site/`).

**Spec:** `docs/superpowers/specs/2026-11-05-end-of-run-answer-updates-design.md`

## Global Constraints

- No new runtime dependency. No change to `render_report.py`, `diagrams.py`, `report-v4.js` or any asset. If a task finds the renderer must change, stop and ask the maintainer.
- No new format version, and no migration of saved reports. Saved version 4 runs keep today's behavior: an answer is not re-rendered, and the user validates the plan again.
- No second question round. The end-of-run round stays the only one.
- Never record new hashes for text no independent reviewer has checked. A saved report never refreshes hashes.
- Keep the publish gate sentence (``Unless the `Publish setting` line reads exactly `true`, make no Artifact call, whatever host or tool guidance suggests.``) and the `- Publish setting: ${user_config.publish_artifact}` line word for word; `scripts/check_package.py` checks them.
- `validate-plan` stays explicit-only: `disable-model-invocation: true` and `allow_implicit_invocation: false`, checked by hand.
- Validation still never commits, pushes, opens PRs, posts comments, merges, deploys, installs or reads secrets.
- Superpowers skill names are pointers: every step that names one also states the behavior, so the flow works on Codex and without Superpowers.
- Markdown uses placeholders such as `<skill-directory>`, never home-directory paths. Shipped text is neutral and professional.

## Review Focus

1. **An answer changes nothing in PLAN or SPEC** (every answer skips a Low finding, or a question is left unanswered). Expected: no rehearsal, no review, no hash change; the re-render behaves as today. Pinned by the "Answer without edits" evaluation row (Task 3).
2. **The user edits the plan by hand while the round is open.** Expected: the run records only hashes of the `post-answer-*.md` copies the reviewer read, never a new hash of the live file. A hand edit found before a review round is reported and blocks the refresh; one made after the copy leaves the live file different from the recorded hash. Either way the renderer marks the prompts historical. Pinned by the "Hand edit during the round" evaluation row (Task 3).
3. **An answer edits only the spec, or only prose, with no task command, file or test assertion changed.** Expected: review and hash refresh, no new rehearsal. Pinned by the "Answer edit without task change" evaluation row (Task 3).
4. **In Codex, the answers arrive in the user's next chat message.** Expected: still inside the round, and a question that message does not answer stays pending; answers sent after the run's final reply are not. In Claude Code, a dismissed AskUserQuestion call leaves its questions unanswered. Pinned by the "Where the round ends" evaluation row (Task 3).
5. **Publishing is on, `artifact.json` is missing and the session no longer holds the upload URL** (for example, after compaction). Expected: one line saying the online page shows the earlier render, the local link, one render with `--open`, and no first publish of a second artifact. Pinned by the "Published, no `artifact.json`" evaluation row (Task 3).

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

## Delivery

- Plan branch `plan/end-of-run-answers`, milestone "End-of-run answer updates". Repository rules in `AGENTS.md` govern branches, reviews and merges.
- One phase, **P1**: Tasks 1–4, docs-only. The plan is done when P1 merges. Then come the plan-to-`main` PR and the release.
- Docs-only: the plan's docs PR and P1 use the full-plan review (AGENTS.md, "Git workflow") as the code review, and `/security-review` once.
- Every `git commit` runs in the same command as `git branch --show-current`, and stops if the branch is not the phase branch. Task commit messages end with `Plan: docs/superpowers/plans/2026-11-05-end-of-run-answer-updates.md`, `Phase: P1`, `Task: <n>`, then `Co-Authored-By:`, with no blank line between them. The commit blocks below show only the subject.
- Do not edit `docs/verification.md`: only a release PR changes release checks (AGENTS.md "Releases").
- Check commands used below: **UNIT** is `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py'`; **PKG** is `python3 scripts/check_package.py`.

---

### Task 1: Rehearse, review and record answer edits

**Files:**
- Modify: `skills/validate-plan/SKILL.md` (workflow step 7's "When the user answers ..." sentence; workflow step 8's second paragraph, including its sentence "For Not ready, the remediation prompt stays as it is", which gains "unless step 8's answer-edit steps add a blocker; the one remediation prompt then names every remaining blocker"; the "Resume or repeat" sentence "Do not replace recorded hashes to make stale evidence appear current.")
- Modify: `skills/validate-plan/references/html-report.md` (the saved-report paragraph ending "Never replace the recorded hashes just to make an old report appear current.")
- Modify: `skills/validate-plan/references/report-contract.md` (the "Drift warning" paragraph)

**Interfaces:**
- Produces: the term **end-of-run round**, defined once in step 8 and used unchanged by Tasks 2–4: the questions this run asked in step 8 and the user's reply to them (in Claude Code the AskUserQuestion results, where one call holds at most four questions, so a round can take several calls, and a dismissed or failed call leaves its questions unanswered; in Codex the user's next chat message after the questions), ending when the run delivers its final reply after handling that reply. A question the reply does not answer stays pending.
- Produces: the run-directory files `post-answer-plan.md` and `post-answer-spec.md`, the copies a post-answer review round reads, and `last-write.json`, the SHA-256 of each document, seeded from `revised-*.md` before any answer edit and updated right after each of the run's own writes.
- Consumes: the existing `references/plan-reviewer.md` fields `Review focus` and `Findings already dispositioned`. No field is added.

- [ ] **Step 1: Edit `SKILL.md` step 8.** Replace "Apply and recheck each answer" in "Apply and recheck each answer and re-render in the same run." with the numbered sub-list below, so it sits between receiving the answers and "re-render in the same run" (item 4 applies the answers), in the order it runs, applying only to a `kind: new` version 5 run:
  1. Define the end-of-run round (Interfaces above). Answers after it keep today's behavior: a local re-render, no hash refresh, and validate the revised plan to get current prompts.
  2. No answer changed PLAN or SPEC: nothing below runs; the hashes stay (Task 2's artifact and `--open` rules still apply).
  3. Before applying any answer edit, compare the live PLAN and SPEC with `revised-plan.md` and `revised-spec.md`; any difference is a hand edit. When they match, seed `last-write.json` in the run directory with both documents' hashes. Before each of the run's own writes to PLAN or SPEC, the live file's hash must equal that record; right after each own write, record the new hash. A failed check means a hand edit: report it in the reply and section 7, apply the remaining answer edits without overwriting the user's change, skip items 5–8, and refresh no hash, so the prompts stay historical and the reply says to validate the revised plan for current prompts.
  4. Apply the edits the answers require in full, with step 7's rechecks of affected sections.
  5. An answer changed the commands, files or test assertions of a task that step 5 rehearsed: rehearse only those tasks again under step 5's rules (a new detached worktree at a path this run has not used, not the step 5 path, at the same recorded implementation base SHA; the edits of earlier tasks a changed task builds on applied as setup only, not recorded as new results; approved focused commands only; exact commands, exit codes and outputs recorded; a failing command traced to its cause before the plan changes). Then inspect and remove only that worktree under step 8's cleanup rules, and compare the worktree inventory with the baseline again. A changed task that step 5 did not rehearse keeps its recorded step 5 limit, and the verdict follows the existing rules. If the rehearsal cannot run, record the limit in section 7; the changed tasks' phases cannot be Ready, and because a waiting phase under Ready after approvals must name a pending approval and missing required evidence is Not ready (SKILL.md "Report and handoff"), the verdict becomes Not ready, with one remediation prompt that names the blocked rehearsal and every other remaining blocker and says `Do not start dependent implementation.`
  6. A fresh independent reviewer then reviews the whole revised documents, reading the `post-answer-*.md` copies made and checked under item 8 before each round (never the live files), under step 6's loop rules. `Review focus` names the changed sections and the new rehearsal results. `Findings already dispositioned` lists each answer as settled by the user; the reviewer may still report a defect in how an answer was applied. No round cap.
  7. A finding whose fix would change requirements, architecture, security boundaries or scope goes to section 6 and `open_decisions` as a pending approval, is not asked, leaves the loop, and its phases wait. The final reply names it in one line.
  8. Hash only reviewed text. Before each post-answer review round, copy the live documents to `post-answer-plan.md` and `post-answer-spec.md` in the run directory, check that each copy's hash equals `last-write.json` (a mismatch is a hand edit, item 3), and give the reviewer those copies. When a round leaves no Medium or High finding to fix, set each document's `sha256` in `context.json` `documents` to the hash of its post-answer copy, never a new hash of the live file, then copy those copies over `revised-plan.md` and `revised-spec.md`. Any PLAN or SPEC edit after that round needs another round. Record the answer edits in section 5, and the new rehearsal runs and post-answer review rounds in section 7. If Git state or approvals drifted for another reason, `handoff_status` stays `historical`, as today.
  9. Without an independent reviewer: disclose it; set `review_status` to a value other than `complete` (for example `incomplete`); the verdict is Not ready until a separate review is supplied, with section 8 holding one remediation prompt that names the missing review and every other remaining blocker and says `Do not start dependent implementation.`; `revised-*.md` and the hashes stay unchanged.

- [ ] **Step 2: Edit `SKILL.md` step 7.** In "When the user answers, record it in sections 5–6, apply and recheck the affected changes, then re-render the report, context and handoff.", add that an answer that edits PLAN or SPEC follows step 8's answer-edit steps before the re-render.

- [ ] **Step 3: Edit `html-report.md`.** Keep "Never replace the recorded hashes just to make an old report appear current." and add the single exception after it: in the same run, after the post-answer review passes (SKILL.md step 8), the hashes of the reviewed final documents replace the earlier ones. A saved report never refreshes hashes.

- [ ] **Step 4: Edit `report-contract.md`.** In "Drift warning", say that a same-run answer edit that passed the post-answer review is not drift, because its hashes were refreshed; any other change after review still is.

- [ ] **Step 5: Edit `SKILL.md` "Resume or repeat".** After "Do not replace recorded hashes to make stale evidence appear current.", add that the only exception is step 8's post-answer review in the same run.

- [ ] **Step 6: Verify.**
  Run **PKG** and **UNIT**. Expected: both pass, with the same test count as before (168 at base `80794b8`; the renderer is unchanged).
  Run `git diff --stat -- skills/validate-plan/scripts skills/validate-plan/assets`. Expected: no output.
  Run `grep -n "Never replace the recorded hashes" skills/validate-plan/references/html-report.md`. Expected: one hit, followed in the same paragraph by the exception.
  Run `grep -n "post-answer" skills/validate-plan/SKILL.md skills/validate-plan/references/html-report.md skills/validate-plan/references/report-contract.md` and read each hit. Expected: every hash refresh names the reviewed `post-answer-*.md` copies, and none hashes the live file.

- [ ] **Step 7: Commit**

  ```bash
  git add skills/validate-plan/SKILL.md skills/validate-plan/references/html-report.md skills/validate-plan/references/report-contract.md
  git commit -m "Rehearse, review and record end-of-run answer edits"
  ```

### Task 2: Update the published page and reopen the browser

**Files:**
- Modify: `skills/validate-plan/SKILL.md` (workflow step 8's artifact sentence "If this run published an artifact (`artifact.json` in the run directory) ..."; the "Report and handoff" delivery paragraph's sentence "A re-render after a recorded answer is a re-render ..."; the "Resume or repeat" sentence "pass `--open` on a re-render only when the user asked to see the report again")
- Modify: `skills/validate-plan/references/html-report.md` (the `--open` paragraph after the render command; the Delivery paragraph "Render a new run's report with `--open`, except when it is published (below); a re-render opens only when the user asked"; the paragraph "The one exception is the end-of-run re-render in the same run ...", including its sentence "If the run has no `artifact.json` and the user gives no artifact URL, follow steps 1–7 as a first publish instead."; the "publishing is unavailable" sentence "with `--open` for a new run, and for an update or a publish on request only when the user asked to see it"; the sentence "If the stored URL can no longer be read, say so in one line, leave `artifact.json` unchanged and deliver the report locally"; the failure paragraph "If a step before the upload, or the upload itself, fails ...")

**Interfaces:**
- Consumes: the term **end-of-run round** from Task 1.
- Produces: the **end-of-run re-render** rules that Tasks 3–4 describe: update by `artifact.json` or by the session's known upload URL; otherwise one stale-page line; `--open` whenever the online page is not updated.

- [ ] **Step 1: Edit the artifact rule.** In step 8 and in html-report.md's "The one exception ..." paragraph, add the spec's section 2:
  - The publish gate still applies: before the re-render, check as for any update that the `Publish setting` line reads exactly `true` and the Artifact tool and a session scratchpad are available. A failed check means the online page is not updated (the out-of-date line below).
  - `artifact.json` exists: today's update steps.
  - `artifact.json` missing, and this session holds the URL from this run's successful upload (the `url` the Artifact tool returned to this run's own publish call, never one found by listing artifacts or rebuilt from memory): the same update steps with that URL (read it first if the Artifact tool requires), then write `artifact.json` with that `url` and the new `published_at` and `html_sha256`.
  - No URL known, a failed gate check, or the update fails: one line saying the online page shows the earlier render and its prompts may be out of date, the artifact link when known, and the local `report.html` link.
  - The end-of-run re-render never publishes a first artifact (no quickstart, no publish without `url`). Scope the sentence "If the run has no `artifact.json` and the user gives no artifact URL, follow steps 1–7 as a first publish instead." to a user's request to publish.
  - This run did not publish: nothing applies.

- [ ] **Step 2: Edit the `--open` rule.** In html-report.md's paragraph after the render command, its Delivery paragraph, its "publishing is unavailable" sentence, its sentence "If the stored URL can no longer be read, say so in one line, leave `artifact.json` unchanged and deliver the report locally" and its failure paragraph, and in SKILL.md's delivery paragraph and "Resume or repeat" sentence, add: the end-of-run re-render adds `--open` whenever the online page is not updated by it (publishing off or unavailable, the run did not publish, or the Step 1 update was not made or failed). Decide before rendering whether an update will be tried: the gate checks pass and `artifact.json` or a URL this session's own publish returned is known. If not, render once with `--open`. If it will be tried, render without `--open`, because the upload needs the rendered files; only when that update then fails, run the same render command again with `--open`. When the online page is updated, it stays without `--open` and the reply gives the artifact link first. Every other re-render keeps "only when the user asked".

- [ ] **Step 3: Check for contradictions.** Run `grep -n -i -e '--open' skills/validate-plan/SKILL.md skills/validate-plan/references/html-report.md` and read each hit; then run `grep -n "first publish" skills/validate-plan/SKILL.md skills/validate-plan/references/html-report.md`. Expected: every `--open` hit agrees with Step 2, and none says the end-of-run re-render, or an update after a failed end-of-run update, opens only when the user asked; every "first publish" hit applies only to a user's request, never to the end-of-run re-render.

- [ ] **Step 4: Verify.** Run **PKG** and **UNIT**. Expected: both pass; PKG still finds the publish gate sentence and the `Publish setting` line.

- [ ] **Step 5: Commit**

  ```bash
  git add skills/validate-plan/SKILL.md skills/validate-plan/references/html-report.md
  git commit -m "Update the published page and reopen the report after end-of-run answers"
  ```

### Task 3: Evaluation cases

**Files:**
- Modify: `docs/evaluation.md` (the "Starter cases" table)

**Interfaces:**
- Consumes: the end-of-run round (Task 1) and the end-of-run re-render rules (Task 2).

- [ ] **Step 1: Edit existing rows.**
  - **Report delivery:** add the end-of-run re-render exception: it opens with `--open` whenever the online page is not updated.
  - **Answers update the artifact:** add that a missing `artifact.json` with a URL this session holds still updates that URL and writes `artifact.json`.
  - **End-of-run questions:** add that an answer edit is rehearsed (changed tasks only), reviewed and recorded before the re-render.
  - **Publish fails:** add that a failed end-of-run update renders the report again with `--open`.
  - **Publishing unavailable:** add that the end-of-run re-render is the one render, with `--open`.
  - **Re-render of a published run:** add that the step 8 re-render without `artifact.json` uses the URL this session's own publish returned and never makes a new artifact.
  - **Drift after review:** add that a same-run answer edit that passed the post-answer review is not drift.

- [ ] **Step 2: Add rows** (case name, then the observable outcome):
  - **Answer edit reviewed:** the changed tasks rehearsed again in a new worktree, at a path not used before in the run, that is then removed with no other worktree touched; a fresh reviewer given the `post-answer-*.md` copies and the answers as settled; `revised-*.md` and the changed `sha256` replaced from those copies; current prompts with copy buttons; section 7 shows the rehearsal and the review.
  - **Answer edit finds a Medium:** fixed and reviewed again by a fresh agent until none remain, then recorded.
  - **Answer edit needs approval:** a pending approval in section 6 and `open_decisions`, no second question, the affected phases wait, one line in the reply.
  - **Answer edit, no reviewer:** the gap disclosed, `review_status` not `complete`, Not ready with one remediation prompt, no hash refresh.
  - **Answer edit on an unrehearsed task:** a changed task that step 5 did not rehearse is not rehearsed now; it keeps its step 5 limit, and the verdict follows the existing rules.
  - **Answer edit, rehearsal blocked:** the limit in section 7; the changed tasks' phases are not Ready; Not ready with one remediation prompt naming the blocked rehearsal.
  - **Answer without edits:** no rehearsal, no review, no hash change.
  - **Answer edit without task change:** review and hash refresh, no rehearsal.
  - **Hand edit during the round:** only the reviewed `post-answer-*.md` copy is hashed, never the live file; a hand edit found before the answers are applied (live differs from `revised-*.md`) or before a review round (live hash differs from `last-write.json` before a write or a review round) is reported and blocks the refresh; the live file differs; the prompts are historical.
  - **Where the round ends:** a Codex answer in the next chat message is inside the round, and a question it does not answer stays pending; in Claude Code a dismissed AskUserQuestion call leaves its questions pending; an answer after the run's final reply gets a local re-render, no hash refresh, and the advice to validate the revised plan.
  - **Published, no `artifact.json`:** with the URL this session's own publish returned, that page updated and `artifact.json` written; with no known URL or an unavailable Artifact tool, one stale-page line, the local link, one render with `--open`; with a failed update, the same line and a second render with `--open`; never a second artifact.
  - **Browser after answers:** with publishing off, the end-of-run re-render opens the report; with the online page updated, it does not.

- [ ] **Step 3: Verify.** Run **PKG**. Expected: PASS.

- [ ] **Step 4: Commit**

  ```bash
  git add docs/evaluation.md
  git commit -m "Add evaluation cases for end-of-run answer updates"
  ```

### Task 4: Site docs and changelog

**Files:**
- Modify: `site/src/content/docs/reports-and-handoffs.md` (the paragraph starting "At the end, the agent asks one round of questions"; in the publishing paragraph, the sentences from "The answers to the end-of-run questions update that same artifact in the same run.")
- Modify: `site/src/content/docs/first-run.md` (step 6)
- Modify: `site/src/content/docs/features.md` (the validate-plan paragraph, only where it describes the end-of-run round)
- Modify: `CHANGELOG.md` (root; synced into the site at build)

**Interfaces:**
- Consumes: the end-of-run round (Task 1) and the end-of-run re-render rules (Task 2).

- [ ] **Step 1: Edit the site pages.** Say, in plain words:
  - an answer that changes the plan is tested again where it changed a task, reviewed, and recorded, so the prompts stay current;
  - a reviewer finding that needs your approval stays open in the report, with no second round of questions;
  - with publishing on, the same page is updated even when `artifact.json` is missing, or the reply says the online page is out of date;
  - with publishing off, the updated report opens in the browser after your answers;
  - answers given after the run's final reply still re-render locally, and validating the revised plan gives current prompts.

  Check with `grep -n -i "end-of-run\|one round of questions\|answer recorded later" site/src/content/docs/*.md` and read each hit. Expected: none contradicts the list above (the synced `changelog.md` copy is fine).

- [ ] **Step 2: Add a changelog entry.** Add `## Unreleased` at the top of `CHANGELOG.md`, with one bullet per spec section: answer edits rehearsed, reviewed and recorded so prompts stay current; the published page updated without `artifact.json` or flagged as out of date; the report reopened after the answers when no online page is updated.

- [ ] **Step 3: Verify.**

  ```bash
  python3 scripts/check_package.py
  (cd site && npm ci && npm test && npm run build)
  ```

  Expected: all pass. `npm ci` installs the locked site dependencies and changes no manifest or lockfile; `npm run build` regenerates the gitignored `site/src/content/docs/changelog.md` from `CHANGELOG.md`.

- [ ] **Step 4: Commit**

  ```bash
  git add site/src/content/docs/reports-and-handoffs.md site/src/content/docs/first-run.md site/src/content/docs/features.md CHANGELOG.md
  git commit -m "Document end-of-run answer updates"
  ```
