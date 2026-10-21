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
  - **Ready after approvals:** no blocker remains, and the open items are only non-blocking user approvals.
  - **Ready:** no blocker or unresolved approval for the named implementation scope. Recorded limitations and separately scoped follow-ups are not automatically blockers.
  - Approval gates that PLAN already has for production, rollout, secrets or infrastructure do not lower the verdict. The handoff stops before them.

Dependency and alternatives decisions use **High/Medium/Low decision confidence** with dated primary evidence, reasons and explicit unknowns, as defined in [dependencies and alternatives](dependencies-and-alternatives.md). This is separate from the existing subjective readiness percentages and PLAN/SPEC quality scores; never produce a numeric package trust score. Preserve Verified/Assumption/Unknown labels for the underlying claims.

## Required report

Keep the eight evidence sections below in this order. Add an unnumbered **Feature at a glance** section above them and **Decisions made without your reply** at the end. Keep the report self-contained; do not print the full PLAN or SPEC or repeat the evidence inside the launch prompt.

### Write for a quick human read

- Lead with what the feature does, what changed, what was checked, and what needs attention. Use short sentences and familiar words. Explain an unavoidable technical term once; put file paths, hashes, command output and detailed reasoning in technical details.
- Target one to three short summary sentences per section and one sentence per table reason. These are writing targets, not permission to omit a material risk, uncertainty or scope change. Avoid repeating the same warning or evidence in several places.
- Keep both complete score tables and their averages visible. Keep blockers, pending approvals, important verification limits and next actions visible. In sections 1, 4, 5 and 7, place supporting evidence after `### Technical details` to make it expandable. Never use that marker to hide sections 2, 3, 6 or 8. Section 7 should normally have a short visible results/limits summary followed by expandable commands and output.
- **Feature at a glance:** show the feature's main user flow or parts in 3–7 blocks with short labels and one-sentence descriptions, supplied through `context.json`. Use `layout: flow` only for a genuine sequence; use `layout: blocks` for independent/parallel parts without arrows. Describe the intended behavior, not the validation workflow. Summarize important branches in the relevant block; do not invent sequential relationships or imply proposed behavior is already shipped. State what is new or changed in the overview summary. Text remains available to screen readers; no external diagram service or new dependency is needed.
- **Decisions made without your reply:** list each unanswered routine question, the recommendation used, and why. Use an empty list when none. These are recorded defaults, not user approvals; required approvals stay in Open items. Supply the record through `context.json` so it appears once at the end.

1. **Verdict:** `Ready / Ready after approvals / Not ready`, confidence with its main limitation, PLAN original average → revised average /10, SPEC original average → revised average /10. Include the reviewed paths, branch/worktree and base SHA.
2. **PLAN comparison:** all five dimensions in `Dimension | Original /10 | Revised /10 | Reason / evidence`, followed by **Average /10**. Show unchanged dimensions too.
3. **SPEC comparison:** the same columns and average, using all five SPEC dimensions.
4. **Decision confidence:** `Decision | Confidence | Evidence | Remaining uncertainty`. Include the verdict's material dependencies, and label the percentages as subjective estimates. Do not omit the table when there are no new decisions; report the readiness decision and its evidence.
5. **Changes:** begin with a scope/complexity comparison: `Measure | Original | Revised | Reason / evidence`. Include delivery phases, unique numbered tasks, implementation/supporting tasks and dependencies/services; add PR count or repeated checks when they change. Explain task mappings, real added work versus regrouping, and the precise approval basis. Then give short groups for bugs fixed, PLAN changes, and SPEC changes with section and reason. Write `None` for an empty group; use `Unknown` for an unrecovered baseline.
6. **Open items:** distinguish implementation blockers, pending approvals, accepted limitations and separately scoped follow-ups. Record actual authorized actions and remaining research limits, installation, service and external-action gates here, with their approval basis or repository instruction reference. State `None` when appropriate; do not call the same unresolved item both blocking and ready. Never infer permissions from a recommendation or an unanswered question.
7. **Verification and checkout:** actual dry-run commands/results, reviewed versus executed checks, checks not run, tested SHA, changed files, commit status and worktree cleanup. Never replace an actual test count with an inferred new total.
8. **Fresh-session handoff:** a one-line suggested effort covering all phases, then one fenced launch prompt per ready phase, in phase order, following `../handoff-template.md`. The renderer adds the phase table from `context.json` above the prompts. Each prompt targets 50–80 words with an 80-word maximum, names one phase and its tasks, and says `Stop at the end of Phase <id>` for its own phase. Reference verified plan/spec/report/context paths; keep full decisions, permissions and evidence in those sources. For **Ready after approvals**, give prompts only for ready phases before the first waiting phase and name the waiting decision; if the first phase waits, give one prompt that names what to resolve and says `Do not start dependent implementation.` For **Not ready**, use one short remediation prompt naming the blocker and explicitly prohibiting dependent implementation; no phase prompts.

## Dependency evidence within the eight sections

Keep both complete PLAN/SPEC tables, scope changes, confidence/evidence, verification limits and the full copyable handoff. Do not substitute a dependency summary or decision menu for this contract.

- **Section 4:** add material dependency/alternative decisions to the existing four-column confidence table, using High/Medium/Low, dated evidence and uncertainty. Keep the readiness row and its existing convention.
- **Section 5:** after the scope comparison, include applicable dependency assessments and the original-versus-alternatives comparison, with at most two alternatives. Record exact identities/versions, rationale, approval basis and decision IDs. No applicable concern needs only a brief evidence-backed statement, not an empty table.
- **Section 6:** record actionable unresolved choices and their pending, selected or deferred status. Name blocked tasks, independent work, and each required approval. Record actual answers without assuming silence means approval. Routine recommendations used without a reply belong in the final defaults record, not the pending-approval list.
- **Section 7:** identify local evidence, the public research ledger, declined/unavailable lookups, inspected versus executed commands and resulting limits. No external research is not the same as no local validation.
- **Section 8:** give a concrete launch instruction per ready phase with its phase, tasks and source paths, including for Not ready remediation. Refer to the full decision and permission record in the report/context instead of copying it. A bare link without an instruction and scope is not a handoff.
