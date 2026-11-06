# End-of-run answer updates

**Date:** 2026-11-05
**Status:** Draft for maintainer review

## Why

Release 0.6.0 moved every validation question to one round at the end of the run (`skills/validate-plan/SKILL.md` workflow step 8). The release notes list three known limitations of that round. The maintainer wants all three fixed:

1. **Answer edits leave the prompts out of date.** When an answer changes the plan or spec, the run applies the change, but `context.json` keeps the hashes recorded before the answer, and no reviewer checks the change. The renderer compares the live files with those hashes (`render_report.py`, `freshness_state`). The two no longer match, so it marks the phase prompts historical and removes their copy buttons. Today the user has to validate the revised plan again to get current prompts.
2. **A published report can go stale with no warning.** If the upload succeeded but writing `artifact.json` failed (`references/html-report.md`, "Private artifact"), the end-of-run re-render does not update the published page, and the reply does not say so.
3. **The browser does not reopen.** With publishing off, the end-of-run re-render runs without `--open` (html-report.md: "Leave out `--open` when re-rendering a report (a saved report, or the same run after a recorded answer)"). The updated report only appears if the user clicks the `report.html` link.

## Goals

- An answer that edits the plan or spec gets an independent review of the change in the same run. When that review passes, the run records the new revisions and hashes, and the re-rendered prompts are current.
- A run that published a report always either updates that page after the answers, or says in one line that the page is out of date.
- With publishing off, or when the online page is not updated, the updated report opens in the browser after the answers.

## Non-goals

- No second question round. The end-of-run round stays the only one.
- No new report format version, and no migration of saved reports. Saved version 4 runs keep their current behavior: an answer is not re-rendered, and the user validates the plan again.
- No change to scoring, the eight report sections, the verdict rules or the phase grouping rules, except where named below.
- No new runtime dependency.

## Anti-goals

- New hashes recorded for text no independent reviewer has checked. That would make unreviewed edits look current, which the existing rule "Never replace the recorded hashes just to make an old report appear current" exists to prevent.
- A review of an answer edit that grows into a new open-ended loop of questions to the user.
- Opening a local browser tab when the online page was updated. The artifact link replaces the local page in that case.

## Decided by the maintainer

- Fix all three limitations in one plan.
- Answer edits: save the new copy and its hash, have a fresh reviewer check the changed parts, and count the prompts as current only once that review passes. A finding that needs the user's approval stays open in the report. No second question round.
- Missing `artifact.json`: the run uses the link it just published to update the page, then writes `artifact.json`. If that fails, the reply says in one line that the online page is out of date and gives the local link.
- Browser: with publishing off, the updated report opens in the browser again after the answers.
- Retest: when an answer changes a task's commands, files or test assertions, the run tests that task again in a fresh practice worktree before the prompts count as current.

## Design

### 1. Review and record answer edits

This applies to the end-of-run question round of a new (`kind: new`, version 5) run, after the answers arrive (SKILL.md workflow step 8).

**Where the round ends.** The round is the questions this run asked in step 8. The user's reply to them is part of the round: in Claude Code the AskUserQuestion results (one call holds at most four questions, so a round can take several calls; a dismissed or failed call leaves its questions unanswered), in Codex the user's next chat message after the questions. A question that reply does not answer stays pending. The round ends when the run delivers its final reply after handling that reply. Answers given after that, in a later message or a later session, keep today's behavior: a re-render stays local, no hashes are refreshed, and the user validates the revised plan to get current prompts (the `docs/evaluation.md` row "Answers update the artifact" already says a later re-render stays local).

1. If no answer changed PLAN or SPEC (for example, every answer skipped a Low finding or left a question unanswered), nothing below runs. The recorded hashes stay; sections 2 and 3 still apply to the re-render.
2. If an answer changed PLAN or SPEC, the run first checks for hand edits: before applying any answer edit, it compares the live PLAN and SPEC with `revised-plan.md` and `revised-spec.md` (any difference is a hand edit) and, when they match, seeds `last-write.json` in the run directory with both documents' hashes. Before each of its own writes to PLAN or SPEC, the live file's hash must equal that record; right after each own write, the run records the new hash. Then the edits the answers require are applied in full, including the rechecks of affected sections that step 7 already asks for. A failed check means a hand edit: it is reported in the reply and section 7, the remaining answer edits are applied without overwriting the user's change, items 3–6 are skipped, and no hash is refreshed, so the prompts stay historical and the reply says to validate the revised plan for current prompts.
3. If an answer changed the commands, files or test assertions of a task that step 5 rehearsed, the run rehearses that task again under workflow step 5's rules: a new detached worktree at a path the run has not used before (not the step 5 path), at the same recorded implementation base SHA, with the edits of earlier tasks that a changed task builds on applied as setup only, only the approved focused commands for the changed tasks, exact commands, exit codes and outputs recorded, and only that worktree removed afterwards, as step 8's cleanup describes, followed by the same worktree inventory comparison with the baseline. A failing command is traced to its cause before the plan changes, as step 5 requires. Tasks the answers did not change are not rehearsed again, and section 7 keeps their earlier results. A changed task that step 5 did not rehearse (outside the authorized rehearsal scope, or with no approved focused command) keeps its recorded step 5 limit, and the verdict follows the existing rules. If the rehearsal cannot run (for example, the environment blocks it), section 7 records that limit, and the changed tasks' phases cannot be Ready. Because a waiting phase under Ready after approvals must name a pending approval, and SKILL.md makes missing required evidence Not ready, the verdict becomes Not ready, with one remediation prompt that names the blocked rehearsal and every other remaining blocker and says `Do not start dependent implementation.`
4. A fresh independent reviewer then checks the revised documents, following workflow step 6: a new subagent with the `references/plan-reviewer.md` brief, the revised documents (the `post-answer-*.md` copies made and checked under item 6 before each round, never the live files) and the original scope snapshots, plus the user's answers and a list of the changed sections as the review focus, and the new rehearsal results. Each answer goes in the brief's "Findings already dispositioned" field as settled by the user, so the reviewer does not re-argue the chosen option; it may still report a defect in how the answer was applied. The same loop rules apply: verify each finding, fix verified Medium and High findings, review again with a fresh agent until none remain, list Low findings without fixing them.
5. A finding whose fix would change requirements, architecture, security boundaries or scope is not fixed and not asked. It is added to section 6 and `open_decisions` as a pending approval, and the phases it affects wait, under the existing verdict rules. The final reply names it in one line.
6. The hashes are taken from the exact text the reviewer read. Before each post-answer review round, the run copies the live documents to `post-answer-plan.md` and `post-answer-spec.md` in the run directory, checks that each copy's hash equals `last-write.json` (a mismatch is a hand edit, item 2), and gives the reviewer those copies. When a round leaves no Medium or High finding to fix (an approval-needing finding has left the loop under item 5), the run sets each document's `sha256` in `context.json` `documents` to the hash of its post-answer copy, never a new hash of the live file, then copies those copies over `revised-plan.md` and `revised-spec.md`. Any PLAN or SPEC edit after that round needs another round. A live file that changed after its copy was made then differs from the recorded hash, so the renderer marks the prompts historical. Section 5 records the answer edits, and section 7 records the new rehearsal runs and the post-answer review rounds with their outcome.
7. The run then re-renders as today. Because the live files now match the recorded hashes, the prompts are current, unless Git state or approvals drifted for another reason, in which case `handoff_status` stays `historical` as today.

If no independent reviewer is available, the existing step 6 rule applies: disclose the gap, and the verdict is Not ready until a separate review is supplied. `review_status` is no longer `complete`, and section 8 becomes one remediation prompt that names the missing review and every other remaining blocker and says `Do not start dependent implementation.`, as the renderer requires for Not ready. The hashes and `revised-*.md` are not refreshed, so the prompts stay historical.

The rule "Never replace the recorded hashes just to make an old report appear current" stays. Its wording gains the one exception above: in the same run, after the post-answer review passes, the hashes of the reviewed final documents replace the earlier ones. A saved report never refreshes hashes. Step 8's sentence "For Not ready, the remediation prompt stays as it is" gains the matching exception: when these steps add a blocker, the one remediation prompt names every remaining blocker.

### 2. Update the published page without `artifact.json`

This applies to the end-of-run re-render of a run that published an artifact in the same session.

- The publish gate still applies: before the re-render, the run checks, as for any update, that the `Publish setting` line reads exactly `true` and that the Artifact tool and a session scratchpad are available. If any check fails, the online page is not updated (the out-of-date line below).
- If `artifact.json` exists, nothing changes: the run follows html-report.md's update steps as today.
- If `artifact.json` is missing but this session holds the URL from this run's successful upload (the `url` the Artifact tool returned to this run's own publish call, never a URL found by listing artifacts or rebuilt from memory), the run follows the same update steps with that URL, then writes `artifact.json` with that `url` and the new `published_at` and `html_sha256`.
- If no URL is known, the gate checks fail, or the update fails, the reply says in one line that the online page shows the earlier render and its prompts may be out of date, and gives the artifact link when known and the local `report.html` link. The report then opens locally, as section 3 describes.
- The end-of-run re-render never publishes a first artifact: no quickstart and no publish without `url`. html-report.md's rule "If the run has no `artifact.json` and the user gives no artifact URL, follow steps 1–7 as a first publish instead" applies only when the user asks to publish.
- If this run did not publish (publishing off, unavailable, or the upload failed), nothing here applies.
- "The update fails" includes the existing case "If the stored URL can no longer be read": that sentence also leads to the local `--open` render in section 3.

### 3. Reopen the browser after the answers

The end-of-run re-render adds `--open` whenever the online page is not updated by it: publishing is off or unavailable, the run did not publish, or the update in section 2 failed. When the online page is updated, the re-render stays without `--open` and the reply gives the artifact link first, as today. The run decides before rendering whether an update will be tried: the gate checks pass and `artifact.json` or a URL this session's own publish returned is known. If not, it renders once with `--open`. If it will be tried, it renders without `--open`, because the upload needs the rendered files; only when that update then fails does it run the same render command again with `--open`, as the existing failure path does for a new run.

This covers only the end-of-run re-render in the same run. Other re-renders keep the current rule: leave out `--open` unless the user asked to see the report.

## What changes

- `skills/validate-plan/SKILL.md`: workflow step 8 (the answer review and hash refresh, the update without `artifact.json`, the `--open` rule), and the "Resume or repeat" sentences on hashes and on `--open`, which gain a pointer to the step 8 exception.
- `skills/validate-plan/references/html-report.md`: the `--open` rule after the render command, the hash rule ("Never replace the recorded hashes ...", in the saved-report paragraph), the artifact update text ("The one exception is the end-of-run re-render ...", and the first-publish fallback after it), and the `--open` wording for an update in the "publishing unavailable" sentence and in the failure paragraph.
- `skills/validate-plan/references/report-contract.md`: the drift warning paragraph, if its wording conflicts with the refresh.
- `docs/evaluation.md`: behavior cases for an answer edit (a changed task rehearsed again, review passes, review finds a Medium, review finds an approval-needing finding, no reviewer available), a missing `artifact.json` with a known URL and with an unknown one, and the browser reopen with publishing off; and the existing rows whose `--open` or drift wording the change affects.
- `CHANGELOG.md` (an Unreleased entry) and the site pages that describe the end-of-run round (`site/src/content/docs/features.md` and any page the builder finds that describes it).
- `scripts/check_package.py` keeps its publish gate sentence checks passing; any sentence it checks must not be reworded.

The renderer (`render_report.py`, `diagrams.py`, `report-v4.js`) is expected not to change, because the refresh is a change to the agent's `context.json`, and `--open` already exists.

## Builder's calls (marked as mine, not the maintainer's)

- Any answer edit triggers the review, including a Low finding the user chose to fix, because any edit can introduce a defect.
- The reviewer gets the whole revised documents, with the changed sections named as the focus, rather than only the changed sections, so it can catch a contradiction the change creates elsewhere.
- When the section 2 update fails, the report opens locally, so the user sees the current report somewhere.
- The post-answer review has no round cap, matching step 6.
- Where the round ends (section 1): the run's final reply after handling the user's reply to the step 8 questions.
- Each answer is passed to the reviewer as already dispositioned, so the reviewer cannot overturn the user's choice but can still find defects in how it was applied.
- If the rehearsal of a changed task cannot run, that task's phases are not Ready, because their prompts would rest on untested text.

## Left to the builder

- Exact wording of the new SKILL.md and html-report.md text, within the decisions above.
- How the evaluation cases are phrased in `docs/evaluation.md`.
- Whether a renderer test is useful. If the renderer turns out to need a change, add a regression test for the observable failure, as AGENTS.md requires.

## Success looks like

- After the user answers an end-of-run question that edits the plan, the re-rendered report shows current phase prompts with copy buttons, and section 7 shows the new rehearsal of changed tasks and the post-answer review.
- A run that published never leaves a stale online page without saying so.
- With publishing off, the updated report is in front of the user after the answers without clicking a link.
