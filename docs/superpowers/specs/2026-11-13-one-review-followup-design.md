# One review workflow follow-up: design

Date: 2026-11-13. Status: approved by the maintainer on 2026-11-14. Follows `2026-11-11-one-review-workflow-design.md` (the "one review spec" below), released in 0.7.0. Where they differ, this design wins; the one review spec and its plan stay as written history.

Scope: this document covers the plan-validation plugin and this repository's own rules. Matching changes to the maintainer's private configuration are tracked outside this repository.

Evidence labels: **Verified** (file:line at `main` 100f4ab), **Assumption**, **Unknown**. Decision owners: **Maintainer** (decided by the maintainer on 2026-11-13) or **Proposed** (a default set while writing this design, open to change before the plan is validated).

## 1. Intent and why

The one review workflow shipped with a pile of unfixed review action points. The phase PRs (#65, #66, #67) saved them for the plan-to-`main` review, and that review (#69) accepted 11 more. A small fix PR for three of them (#68) ran four `/code-review` rounds that found 6, 8, 10 and 8 items, mostly new wording problems in the fix text itself, and was closed unmerged.

Two causes stand out:

- **Decisions were missing.** Many items ask a behavior question the one review spec did not answer. Fixing them in wording only moves the question to the next sentence.
- **Rules were copied.** The same rule is written out in up to seven files (the block, `validation-reviews.md`, `SKILL.md`, `AGENTS.md`, the site pages, the text to paste and `docs/evaluation.md`), and each copy drifts a little. Every drift is a new finding.

So this revision decides the open behavior questions here, gives each rule one home, and closes pure-wording items with a recorded reason instead of a fix loop. The maintainer chose this approach (option B) over fixing every item one by one.

## 2. Goals, non-goals, anti-goals

Goals:
- Every open action point closes one way: decided here and built by the plan, merged into a one-home rule, fixed as wording because it could mislead an implementer, or closed with a reason (section 7).
- Each rule has one home (section 5). Other prose points to it; the copies that must stay complete say the same thing.
- Plans already written keep working without a swap PR (M1).

Non-goals:
- Renderer, report format or `context.json` changes (M4).
- Editing merged plans and specs (`2026-11-12-one-review-workflow.md`, the one review spec, the 2026-11-05 spec) or the released 0.7.0 `CHANGELOG.md` entry. This design records where they are superseded.
- Recovering the unrecorded round-4 findings of #68 by running reviews again.

Anti-goals:
- A fix loop on wording: a phase that keeps re-reviewing its own wording fixes.
- A pointer in text that is pasted or copied elsewhere (the block, the text to paste, the report's between-phases note), which would point at nothing once copied.
- An evaluation row that points at the file it checks instead of stating the expected behavior.

## 3. Inputs

- PR #69's `## Code review` comment review: 11 accepted action points (69-1 to 69-11). Its 4 rejected items stay rejected.
- Saved items from the phase reviews: #65 (6 Low, 17 deferred design items, 2 security notes), #66 (22 Low), #67 (4 Low and 1 security note).
- The validation report's post-answer Low items PA1-L7, PA1-L8 and PA3-L1 to PA3-L5.
- Closed branch `fix/final-review-wording` (#68): its three fixes and the constraints its commit messages show (68-1 to 68-12, inferred). Round 4's 8 findings were never recorded: **Unknown**.

After merging duplicates: 57 rows (21 design, 16 duplication, 16 wording, 3 obsolete, 1 rejected). Section 7 lists every row's outcome.

## 4. Decisions

### Decided by the maintainer

- **M1 Block marker and the swap check.** The marker stays `<!-- phase-workflow: 2 -->`. It changes only when the block's step numbers or stop reasons change, so the wording fixes in this design keep marker 2. Step 1's swap check no longer compares the swapped section with the installed `references/phase-workflow.md`, which can be a newer version (69-11, 65-D10). A `Replaced on <date>` swap is an expected difference when it changes nothing outside the `## Phase workflow` section and the section carries the marker. A plan already on marker 2 keeps its own copy of the block; no swap PR is needed. The swap PR itself gets both reviews before it merges, which is what makes trusting its content safe. Marker-2 copies written before this design lack M3 and P2–P7 and keep working as written; a maintainer who accepts a finding (M3) in such a plan swaps in the current block in the same docs PR (a call made while writing this design).
- **M2 A new push to a plan's docs PR.** Each review runs once on what changed since the head that the last posted review of that kind read, plus any other changed files, typed and targeted like the first docs-PR review. This is a narrow exception to O5 ("other PRs get both full reviews again") for a plan's docs PR only; every PR into `main` keeps both full reviews after a push. Settles 69-1 and the from-side of "what differs" (65-D13).
- **M3 An accepted parked finding.** During the design update, the maintainer may accept a parked non-security finding instead of fixing it: its entry gets `Accepted: <reason> (maintainer, <date>).` instead of `Fixing task: Task <n>.` Validation treats an accepted entry like one with a fixing task. The next phase's step 1 lets an accepted entry through without a new report, and when every new entry is accepted, the design update needs no phase-only validation: the accepted entries land through a docs PR into the plan branch, and the next phase's saved prompt may then start (the waiting mark is only in the end-of-phase output, so nothing needs clearing). Every list of expected between-phase changes (block step 1, the handoff template's check and between-phases note, `AGENTS.md`'s phase-start check, the text to paste) adds `Accepted:` lines under `## Parked findings`. The plan-to-`main` review checks that every entry has a done fixing task or an `Accepted:` line. A security finding is never parked, so it is never accepted. Settles 65-D2.
- **M4 No renderer change.** The renderer keeps rejecting `docs_only` together with `security_review`, and the "Security review" column keeps its title. The site pages say the column marks phases that need security focus; it does not decide whether the security review runs. Settles 65-D9 and 66-8.
- **M5 Validation answers (2026-11-14).** The maintainer settled four questions the validation raised. D1: a plan swapped under 0.7.0 compares its Phase workflow section with the installed block, so after an upgrade its next phase stops at step 1; the site tells such a plan to swap in the current block again in a docs PR. D2: when the security review of the answer edits cannot run, the hashes are not refreshed (P9). D3: step 1 trusts a swapped section without checking the swap PR's reviews; M1 stands. D4: after a rebase, step 10 saves two `git diff --text` outputs, old base..old head and new base..new head, instead of `git range-diff`, which can show changed Markdown as unchanged under a `-diff` attribute (P7).

### Proposed

- **P1 One home per rule.** Section 5.
- **P2 Branch-finishing hand-offs (69-6).** The block's opening paragraph says: where a loaded skill hands off to branch finishing, do not follow that hand-off; continue with the next step of this workflow. It is its own sentence, not part of the implementer brief, covers every skill that hands off (subagent-driven development and executing-plans), and never sends the session past steps 8 and 9 (constraints 68-1, 68-7, 68-9). #68's last wording is the starting point.
- **P3 Prompts after a swap (69-7, 66-22).** The block's stop reasons say that they also govern a phase prompt that carries the older pause sentence. A swapped plan therefore follows the stop reasons, and its saved prompts need no re-validation.
- **P4 Swap-PR approvals (69-4).** The swap PR records the maintainer's choice for each boundary-crossing task without integration test infrastructure on a line under `Replaced on <date>`: `Boundary tasks: Task <n> approved without integration tests; Task <m> deferred (maintainer, <date>).` It sits inside the Phase workflow section, so M1's swap check accepts it, and the phase session reads it.
- **P5 Step 9 Low that would change the design (65-D3).** A non-security one is listed for the maintainer to fix or skip, like a step 4–6 Low, and is not parked; a security one is closed as P6 says. Parking stays for Medium and High findings and stuck findings.
- **P6 Security Lows in the step 4–6 loop (67-S1).** A security finding from steps 4–6 is closed at any severity (fixed or rejected with evidence), never listed for fix or skip. When its fix would change the design, that is a stop reason, as block step 5 says.
- **P7 Saved diffs in the block (65-D7).** Every diff or range output the block saves for a review (step 9's fallback diff, step 10's rebase diffs and `git show --remerge-diff` output; after a rebase, two `git diff --text` outputs replace `git range-diff`, M5) is written with flags that stop color, external diff tools and text conversion from changing it, as validation's saved diffs are. The plan names the flags each command accepts, checked by running it.
- **P8 One "last reviewed copy" rule in validation (65-D1, 65-D6, 65-D17, 65-L6).** `validation-reviews.md` defines once: each time the security review reads text, that text is kept as the next numbered copy, and the next security review reads the diff from the last kept copy to the current text, written with Inputs item 2's flags. The final-review fixes, a second fix during the final reviews, and the answer edits all follow it. Existing file names stay; globs name only the unnumbered copies.
- **P9 Review gaps (65-D11, 65-D12).** When one review cannot run (the final reviews or the answer-edits security review), section 7 and the watch list record the gap, the run continues, and section 7 marks that review as not covering the text. When the missing review is the answer-edits security review, the hash refresh does not run, so the report's prompts stay historical (M5). After a final-review gap, the docs PR runs only the missing review itself, on the full plan and spec plus other changed files; the other review is reused when its own conditions hold.
- **P10 Stuck post-answer finding (65-D5).** A stuck finding counts as a finding left to fix: no hash refresh, and under D14 it is an implementation blocker, so the verdict is Not ready.
- **P11 Done-check lines (65-D8).** Written only for phases that get a prompt. A Not ready report and waiting phases have none.
- **P12 Repository rules that require more (65-D14).** When a repository's rules require a full-plan review on every docs PR, they win; the difference review in `validation-reviews.md` is the minimum.
- **P13 This repository's security review covers Markdown (69-3).** In `AGENTS.md`, every security review covers documentation, because this repository ships Markdown as a behavioral contract: when `/security-review` would skip a changed file, its procedure runs in a fresh read-only subagent on a saved diff of the range that review targets, for every PR, including PRs outside a plan. It keeps all three of step 9's triggers, names the current block's step 9, does not fix the target to base..head (change-only and docs-PR reviews choose their own), and its brief lifts the documentation exclusion (constraints 68-3 to 68-6, 68-10, 68-11).
- **P14 `/code-review` settings outside a plan (69-10).** `AGENTS.md` types `/code-review high --max-findings all` for every PR in this repository.
- **P15 Marker check at phase start (69-8, 66-11, 67-1).** `AGENTS.md`'s phase-start check also confirms that the plan's Phase workflow has the marker, and stops when it does not (a swap PR comes first). Its step numbers then always mean the current block.
- **P16 The text to paste and docs-only PRs (69-2).** The text to paste drops "Docs-only PRs follow your review rules", which points at itself once pasted. It keeps the docs-PR reuse rule, starting from the case where the repository reviews a plan's docs PR, so it claims no default for other docs-only PRs (constraints 68-2, 68-8, 68-12).

## 5. One home per rule

| Rule | Home | Full copies that stay (aligned to the home) | Becomes a pointer |
|---|---|---|---|
| Phase steps, stop reasons, parking, fix after the final reviews, change after a PR opens, expected between-phase changes | the block (`references/phase-workflow.md`) | the text to paste; the report's between-phases note (`handoff-template.md`); `docs/evaluation.md` rows | site prose in `phased-implementation.md`, `reports-and-handoffs.md`; `SKILL.md` step 4; `AGENTS.md` lists of step contents |
| Validation's final reviews, review gaps, docs-PR reuse and difference review, saved diffs and copies | `references/validation-reviews.md` (each rule once inside it) | the text to paste; `docs/evaluation.md` rows | `SKILL.md`; `AGENTS.md`; site prose; `features.md`, `first-run.md` |
| The `security_review` flag marks focus only | `SKILL.md` phase grouping | none | `html-report.md`, site pages |
| This repository's review typing, statuses, push rules and swap PRs | `AGENTS.md` | none | site prose that describes this repository |

Rules for the copies:
- A pointer names the home and the rule, for example "as the Phase workflow's step 10 says", and does not restate its conditions.
- A full copy keeps every condition of the rules it already carries, aligned to the home's wording. It does not grow to carry the whole home: the text to paste stays a short list.
- Site prose that becomes a pointer keeps a short summary without conditions and links to the home; the step list in `phased-implementation.md` stays as that summary.
- `docs/evaluation.md` rows state expected behavior in full, because they are the oracle the skill text is checked against.

## 6. Wording fixes kept

Fixed because each could make an implementer or agent do the wrong thing, or because the file is edited anyway: 65-L1 (warn that the two `git diff` commands run separately, not with `&&`, which would drop the spec), 65-L3 (where the marker sits), 65-L5 (a Limits line in the delegated brief's return shape), 65-L6 and 65-S1 (the flags cover the base..head diff too), 65-D16 (an evaluation row for the docs-PR gap case), 66-13, 66-14, 66-15 ("In Claude Code" and validation's own saved setting), 66-19 and 66-20 (say which review is limited to the change), 67-2 ("steps 9 and 10"), PA3-L5 (who reads the copies).

## 7. Every row's outcome

The IDs are those of the source reviews. The appendix `2026-11-13-one-review-followup-triage.md` maps each one to its merged row (R01–R57), with its current text and file:line. #65's design items 65-D1 to 65-D17 are the numbered list under "Action points for a follow-up plan revision" in #65's code comment review.

| Outcome | Rows |
|---|---|
| Decided (section 4) | 69-1 (M2), 69-2 (P16), 69-3 (P13), 69-4 (P4), 69-6 (P2), 69-7 and 66-22 (P3), 69-8, 66-11, 67-1 (P15), 69-10 and PA1-L8a (P14), 69-11 and 65-D10 (M1), 65-D1, 65-D6, 65-D17 (P8), 65-D2 (M3), 65-D3 (P5), 65-D5 (P10), 65-D7 (P7), 65-D8 (P11), 65-D9 and 66-8 (M4), 65-D11, 65-D12 (P9), 65-D13 (M2), 65-D14 (P12), 67-S1 (P6) |
| One home (section 5) | 69-5, 65-D15, 66-22 second half, 69-9, 66-10, 65-L2, 66-1, 66-2, 66-3, PA3-L1, 66-4, PA3-L3, 66-6, 66-7, 66-9, 66-12, 66-17, 66-18, 67-3, PA1-L7 |
| Wording fix (section 6) | 65-L1, 65-L3, 65-L5, 65-L6, 65-S1, 65-D16, 66-13, 66-14, 66-15, 66-19, 66-20, 67-2, PA3-L5 |
| Closed: obsolete | 66-5 (restored by #66's security fixes), 66-21 (the shipped 0.7.0 entry was reworded), PA1-L8b (the plan is complete) |
| Closed: rejected | 65-D4: one review spec D8 decides that every confirmed final-review finding, Low included, is closed, while steps 4–6 list Lows |
| Closed: history or format | 65-L4 (line wrapping only); 66-16, 67-4, PA3-L2, PA3-L4 (merged plan and specs; superseded here: the answer edits get one security review per clean post-answer round, on text no security review read, per P8) |
| Unknown | #68 round 4 (8 findings, never recorded) |

## 8. Left to the implementation plan

- The exact wording of every change, cited by quoted text, not line numbers.
- Phases: skill text first (the block, `validation-reviews.md`, `SKILL.md`, `handoff-template.md`), then the site pages and `docs/evaluation.md`, then `AGENTS.md`. Each later phase aligns its copies with text an earlier phase merged.
- New or changed `docs/evaluation.md` rows for M1, M2, M3, P2, P3, P4, P5, P6, P9, P10 and P11.
- The flags for P7, checked by running each command.
- Release mechanics: a release PR after the plan reaches `main`, as `AGENTS.md` "Releases" says; the version number is the maintainer's call then.
- Any copies of these rules this design did not find: the plan's tasks grep for them.
