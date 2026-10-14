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

## Required report

Use these sections in this order. Keep the report self-contained; do not print the full PLAN or SPEC.

1. **Verdict:** `Ready / Ready after approvals / Not ready`, confidence with its main limitation, PLAN original average → revised average /10, SPEC original average → revised average /10. Include the reviewed paths, branch/worktree and base SHA.
2. **PLAN comparison:** all five dimensions in `Dimension | Original /10 | Revised /10 | Reason / evidence`, followed by **Average /10**. Show unchanged dimensions too.
3. **SPEC comparison:** the same columns and average, using all five SPEC dimensions.
4. **Decision confidence:** `Decision | Confidence | Evidence | Remaining uncertainty`. Include the verdict's material dependencies, and label the percentages as subjective estimates. Do not omit the table when there are no new decisions; report the readiness decision and its evidence.
5. **Changes:** begin with a scope/complexity comparison: `Measure | Original | Revised | Reason / evidence`. Include delivery phases, unique numbered tasks, implementation/supporting tasks and dependencies/services; add PR count or repeated checks when they change. Explain task mappings, real added work versus regrouping, and the precise approval basis. Then give short groups for bugs fixed, PLAN changes, and SPEC changes with section and reason. Write `None` for an empty group; use `Unknown` for an unrecovered baseline.
6. **Open items:** distinguish implementation blockers, pending approvals, accepted limitations and separately scoped follow-ups. State `None` when appropriate; do not call the same unresolved item both blocking and ready.
7. **Verification and checkout:** actual dry-run commands/results, reviewed versus executed checks, checks not run, tested SHA, changed files, commit status and worktree cleanup. Never replace an actual test count with an inferred new total.
8. **Fresh-session handoff:** a complete fenced prompt following `../handoff-template.md`. For **Ready after approvals**, name each genuinely pending approval and continue only independent approved work. For **Not ready**, include a fenced remediation/resume prompt that names the blockers and explicitly does not authorize dependent implementation; never imply it is ready.
