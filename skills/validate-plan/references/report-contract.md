# Scoring and report contract


Score the original and revised versions separately, with the revised score taken after the final review and approved corrections.

- Use five equally weighted dimensions per document. Score **each dimension out of 10** and calculate the document's **Average /10 = sum of its five scores / 5**, rounded once to one decimal. Do not use 0–2 rows, a summed Total /10, or combine PLAN and SPEC into a single score. If any row is Unknown, the average is Unknown; do not omit that row from the denominator.
  - **PLAN dimensions:**
    - correctness and spec fit
    - security and privacy
    - performance
    - maintainability and complexity
    - execution and verification readiness
  - **SPEC dimensions:**
    - clarity and testability
    - correctness against the code
    - security and privacy
    - scope and simplicity
    - rollout, rollback and measurement
  - **Anchors** (the worst unresolved issue controls the dimension; scores describe document quality, not probability):
    - 10: no material issue in the reviewed scope, with adequate evidence.
    - 8: minor issues only.
    - 5: a material issue that would cause rework.
    - 2: several material rework issues, or one serious issue.
    - 0: a **blocker** preventing safe implementation, including a security or data-loss bug.
  - Use whole-number dimension scores. An intermediate score needs an evidence-based reason; do not manufacture precision or chase 10/10. Give no credit for a fix still awaiting approval. A material Unknown cannot receive 10 and becomes a blocker when it prevents safe implementation.
  - Calculate the averages; do not estimate them. For example, 10, 8, 10, 8, 9 gives **9.0/10**. Re-expressing old 0–2 scores on a 0–10 scale does not improve the underlying evidence.
- **Confidence** is separate from quality. Give a percentage for each material decision (what gets built, its security or rollout) and for the verdict. Label these **subjective evidence-confidence estimates, not measured probabilities**. Use steps of 5 percentage points and give evidence and uncertainty for every row.
  - 90–95%: directly exercised for the stated claim, with relevant limits identified.
  - 70–85%: supported by current code or primary documentation, but not exercised in the relevant environment.
  - 50–65%: depends on an explicitly labeled Assumption.
  - Below 50%: important evidence is Unknown. Use `Unknown` instead of a number when no defensible estimate is possible.
  - The verdict's confidence is no higher than the weakest decision it depends on.
  - A primary source verifies what it actually documents; it does not prove this repository's runtime behavior. A future production approval gate alone does not lower confidence in starting the approved implementation.
- **Verdict:**
  - **Not ready:** any blocker remains in either document, whatever the score.
  - **Ready after approvals:** no blocker remains, and the open items are only non-blocking user approvals, at least one of which holds back dependent work in the named scope. Each phase with such work waits, and a waiting phase names each such decision ID in `waits_for`. An approval that holds back nothing leaves the verdict Ready.
  - **Ready:** no blocker, and no unresolved approval that holds back work in the named implementation scope. Recorded limitations and separately scoped follow-ups are not automatically blockers.
  - Approval gates that PLAN already has for production, rollout, secrets or infrastructure do not lower the verdict. The handoff stops before them.

Dependency and alternatives decisions use **High/Medium/Low decision confidence** with dated primary evidence, reasons and explicit unknowns, as defined in [dependencies and alternatives](dependencies-and-alternatives.md). This is separate from the existing subjective readiness percentages and PLAN/SPEC quality scores; never produce a numeric package trust score. Preserve Verified/Assumption/Unknown labels for the underlying claims.

## Required report

Keep the eight evidence sections below in this order. Add the unnumbered **Summary diagrams, decisions and watch list** above them (supplied through `context.json`) and **Decisions made without your reply** at the end. Keep the report self-contained; do not print the full PLAN or SPEC or repeat the evidence inside the launch prompt.

### Write for a quick human read

- Lead with what the feature does, what changed, what was checked, and what needs attention. Use short sentences and familiar words. Explain an unavoidable technical term once; put file paths, hashes, command output and detailed reasoning in technical details.
- Target one to three short summary sentences per section and one sentence per table reason. These are writing targets, not permission to omit a material risk, uncertainty or scope change. Avoid repeating the same warning or evidence in several places.
- Keep both complete score tables and their averages visible. Keep blockers, pending approvals, important verification limits and next actions visible. In sections 1, 4, 5 and 7, place supporting evidence after `### Technical details` to make it expandable. Never use that marker to hide sections 2, 3, 6 or 8. Section 7 should normally have a short visible results/limits summary followed by expandable commands and output.
- **Summary diagrams, decisions and watch list:** the Summary tab shows what the feature is and what needs attention, without repeating the evidence.
  - **Diagrams:** 1–3 diagrams of the intended design, not the validation workflow. Use `zones` for parts and who talks to whom, and `flow` only for a genuine sequence of steps. The eyebrow says whether the diagram shows planned, existing or changing parts, and a node's sub-line can mark a single part that differs; do not imply proposed behavior is already shipped. Draw only connections the spec describes. The renderer draws the SVG from data; it rejects a label that does not fit rather than cutting it.
  - **Open decisions:** `open_decisions` mirrors section 6's pending approvals, one item per decision ID, each with its question, recommendation, High/Medium/Low confidence and what it holds back (`Nothing` or `None` when it holds back no work). Each ID also appears in section 6, which keeps the full option menu. Recorded defaults are not open decisions. When no blocker remains, a pending approval that holds back work in the validated scope makes the verdict Ready after approvals; in a phase-only validation, one that holds back only unselected phases is a separately scoped follow-up in section 6, not an open decision.
  - **Watch list:** `watch_list` names the gaps, limits, risks and items fixed in the plan that a reader should keep in mind, each in a short title and one or two sentences. Keep blockers and pending approvals in section 6 as well; the watch list does not replace it.
- **Decisions made without your reply:** list each unanswered routine question, the recommendation used, and why. Use an empty list when none. These are recorded defaults, not user approvals; required approvals stay in Open items. Supply the record through `context.json` so it appears once at the end.

1. **Verdict:** `Ready / Ready after approvals / Not ready`, confidence with its main limitation, PLAN original average → revised average /10, SPEC original average → revised average /10. Include the reviewed paths, branch/worktree and base SHA.
2. **PLAN comparison:** all five dimensions in `Dimension | Original /10 | Revised /10 | Reason / evidence`, followed by **Average /10**. Show unchanged dimensions too.
3. **SPEC comparison:** the same columns and average, using all five SPEC dimensions.
4. **Decision confidence:** `Decision | Confidence | Evidence | Remaining uncertainty`. Include the verdict's material dependencies, and label the percentages as subjective estimates. Do not omit the table when there are no new decisions; report the readiness decision and its evidence.
5. **Changes:** begin with a scope/complexity comparison: `Measure | Original | Revised | Reason / evidence`. Include delivery phases, unique numbered tasks, implementation/supporting tasks and dependencies/services; add PR count or repeated checks when they change. Explain task mappings, real added work versus regrouping, and the precise approval basis. Then give short groups for bugs fixed, PLAN changes, and SPEC changes with section and reason. Write `None` for an empty group; use `Unknown` for an unrecovered baseline.
6. **Open items:** distinguish implementation blockers, pending approvals, accepted limitations and separately scoped follow-ups. Record actual authorized actions (including a user's explicit reset of the run count) and remaining research limits, installation, service and external-action gates here, with their approval basis or repository instruction reference. State `None` when appropriate; do not call the same unresolved item both blocking and ready. Never infer permissions from a recommendation or an unanswered question.
7. **Verification and checkout:** actual dry-run commands/results, reviewed versus executed checks, checks not run, tested SHA, changed files, commit status and worktree cleanup. Never replace an actual test count with an inferred new total.
8. **Fresh-session handoff:** a one-line suggested effort covering all phases, then one fenced launch prompt per ready phase, in phase order, following `../handoff-template.md`. The renderer adds the phase table from `context.json` above the prompts and a heading for each prompt, and shows all other section 8 text above the table, so write only the effort line, the between-phases note and, for a Ready or Ready after approvals `yes`, the run-again-first note from the template and the fenced prompts. Each prompt targets 50–80 words with an 80-word maximum, names one phase and its tasks, and says `Stop at the end of Phase <id>` for its own phase. Reference verified plan/spec/report/context paths; keep full decisions, permissions and evidence in those sources. For **Ready after approvals**, give prompts only for ready phases before the first waiting phase and name the waiting decision; if the first phase waits, give one prompt that names what to resolve and says `Do not start dependent implementation.` For **Not ready**, use one short remediation prompt naming the blocker and explicitly prohibiting dependent implementation; no phase prompts. Both kinds of remediation prompt follow the template's rule on the word `implement`.

## Run validation again

Every new report says whether to run validation again, in `context.json` `rerun`
(fields and run counting in [html-report.md](html-report.md)). It is not one of the
eight sections; the page shows it as a header pill and a Summary card with
"Run <n> of at most 3".

- **yes:** another run is likely to fix something. The reasons say what.
- **no:** nothing is left that validation can fix. The reasons say why.
- **stop:** do not run again; the user decides the next step. The reasons say what
  remains, or what to decide.

Give 1–4 short reasons. The renderer computes these mechanical triggers:

- confidence `Unknown` or below 70%;
- a revised PLAN or SPEC average below 8.0, or `Unknown`;
- the verdict Not ready.

Rules:

- **Runs 1 and 2:** when a trigger fires, answer `yes` or `stop`, never `no`. Use
  `stop` when another run cannot help, for example when the blocker needs the user's
  decision; its reasons name what to decide. `yes` without a trigger is allowed when
  validation could fix gaps it did not reach; its reasons name them.
- **Run 3:** never `yes`. Answer `stop`, or `no` when no trigger fires.
- **Pending approvals** are never a trigger. Recording an answer stays the same-run
  re-render, or a phase-only validation after merges.

In a Not ready report with `yes`, the section 8 remediation prompt comes first: it fixes
the blocker, and a remediation session is not a validation run. The re-run prompt then
validates the result as the next counted run, and it says so:
`Run this after the remediation session.`
In a Ready or Ready after approvals report with `yes`, run validation again before
starting any phase: another run is likely to change the plan the phase prompts build.
The re-run prompt says so: `Run this before starting any phase.`

Only `yes` has a `prompt`. It lives only in `context.json`, never in section 8, and
the renderer writes it to `rerun.txt`. The prompt:

- has at most 80 words; a backtick-quoted absolute path counts as one word (only a path with no spaces, or the PLAN or SPEC path quoted exactly; a quoted slash command counts every word);
- starts with the invocation this run used (such as `/plan-validation:validate-plan`
  or `$validate-plan`), because the skill runs only when invoked explicitly;
- names the PLAN, the SPEC and this run's `report.md` as the previous report;
- says `run <n+1> of 3`, where `<n>` is this run's number;
- for a phase-only validation, keeps this run's scope with `Validate only Phases
  <first>-<last>.` (hyphen or en dash; `Validate only Phase <id>.` for one phase), so the next run
  counts under the same scope;
- names what the run should focus on;
- in a Not ready report, says `Run this after the remediation session.`; otherwise
  says `Run this before starting any phase.`;
- has no `implement`, `implements` or `implementing` (also with a `re` or `re-` prefix), except right after `not`, `cannot`, `n't` (straight or curly apostrophe) or `never` on the same line (such as `Do not implement`), or inside a backtick-quoted absolute path with no spaces (a path that starts with `/` needs a first segment without a colon and, without a file extension, a second segment, so a quoted slash command such as `/feature-dev:implement` or `/implement/` is not a path; a quoted span with spaces is text, except a PLAN or SPEC path quoted exactly), and says `Do not start dependent implementation.`

```text
/plan-validation:validate-plan PLAN: `[PLAN path]` SPEC: `[SPEC path]` FOCUS: Run validation again (run [n+1] of 3). Previous report: `[report.md path]`; read it and its context.json first. [Run this after the remediation session. (Not ready) or Run this before starting any phase.] Focus on [what to fix]. [For a phase-only run: Validate only Phases [first]-[last].] Do not start dependent implementation.
```

When the plan or spec changes after review, the historical warning says to run
validation again, naming the next run (below run 3 and without a recorded stop, a saved
re-render names none and adds "if the 3-run limit allows"), instead of more review
rounds. At run 3 it says the run limit is reached and that revalidating the same scope
needs the user's explicit reset (once another phase has merged, a phase-only validation
of the phases still to build counts separately), and after a recorded `stop` it names
no run and says to decide the next step before revalidating; these two also appear when
only Git state or approvals drifted.

## Dependency evidence within the eight sections

Keep both complete PLAN/SPEC tables, scope changes, confidence/evidence, verification limits and the full copyable handoff. Do not substitute a dependency summary or decision menu for this contract.

- **Section 4:** add material dependency/alternative decisions to the existing four-column confidence table, using High/Medium/Low, dated evidence and uncertainty. Keep the readiness row and its existing convention.
- **Section 5:** after the scope comparison, include applicable dependency assessments and the original-versus-alternatives comparison, with at most two alternatives. Record exact identities/versions, rationale, approval basis and decision IDs. No applicable concern needs only a brief evidence-backed statement, not an empty table.
- **Section 6:** record actionable unresolved choices and their pending, selected or deferred status. Name blocked tasks, independent work, and each required approval. Record actual answers without assuming silence means approval. Routine recommendations used without a reply belong in the final defaults record, not the pending-approval list.
- **Section 7:** identify local evidence, the public research ledger, declined/unavailable lookups, inspected versus executed commands and resulting limits. No external research is not the same as no local validation.
- **Section 8:** give a concrete launch instruction per ready phase with its phase, tasks and source paths, including for Not ready remediation. Refer to the full decision and permission record in the report/context instead of copying it. A bare link without an instruction and scope is not a handoff.
