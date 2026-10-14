# Durable HTML report

Read this when creating the baseline or publishing/repeating a validation result.
The HTML is the full report, not an abridged alternative. The chat response gives
the verdict, the report link and any immediate blocker in at most three bullets.
If the user explicitly asks for the full report in chat, print all eight sections too.

## Files and rendering

Use a new, private local run directory under
`~/.local/share/plan-validation/<repo-name>/<UTC-timestamp>-<topic>/`.
Do not put the only copy in `/tmp`, a session scratchpad, personal memory or a
throwaway worktree. Do not publish it or commit it to the project.

During baseline collection, copy the untouched documents to `original-plan.md` and
`original-spec.md` in this directory. Record baseline counts and their definitions.
After validation, save:

- `report.md`: the source prose for all eight report sections; numbered headings exactly
  `## 1. Verdict` through `## 8. Fresh-session handoff`. Both score tables have
  five dimension rows and an `Average /10` row. Section 1 begins with the verdict
  and contains `Confidence: 75%` (use the actual estimate, or `Unknown`). Store the
  structured scope table in context.json only; the renderer places it at the
  beginning of section 5. Do not duplicate that table in report.md.
  Put applicable dependency and alternatives tables in section 5 after that scope
  table. Keep section 4's four-column table, using High/Medium/Low for dependency
  decisions and the existing convention for readiness. Put decision states in
  section 6 and research/execution limits in section 7; retain them in section 8.
- `context.json`: the small context record below. Use verified facts; use
  `Unknown` for unrecovered counts. Full document hashes identify the revisions
  that were actually validated, not whatever file happens to exist later.
- `revised-plan.md` and `revised-spec.md`: copies of the validated revisions.
- A local research ledger and source evidence when research was proposed, including
  approved, denied, pending or unavailable lookups. Record only public query text;
  preserve dates and evidence limits. No research requires no empty ledger.

Run the helper from **this skill's** directory (substitute absolute paths):

```bash
python3 <skill-directory>/scripts/render_report.py --report <run-directory>/report.md --context <run-directory>/context.json --output <run-directory>/report.html
```

The helper uses only Python's standard library. It renders the full report and
writes `handoff.txt` from section 8 exactly when the handoff is current. It rejects missing sections, incorrect
averages and Ready reports with an incomplete cold read. It checks the two live
document fingerprints; a mismatch labels the result historical and removes the
copy button and prompt download, and prefixes the exported text with a warning.
Set `handoff_status` to `historical` if Git state or approvals have drifted even
when the document hashes match. A Not ready prompt must explicitly say
`Do not start dependent implementation.` and must not begin `Implement ...`.
These are structural checks, not a substitute for reviewing the
evidence, approvals, Git state or the generated report.

Example context shape (replace every example value; do not invent a review):

```json
{
  "title": "Feature name",
  "validation_date": "2026-10-14",
  "kind": "new",
  "review_status": "complete",
  "handoff_status": "current",
  "summary": "What is ready, the important fixes, and the main limitation.",
  "freshness": "Checked at <UTC time>: branch, head, base, approvals and PR state. Tests were run at the recorded SHA.",
  "provenance": "Validation session identifier and source evidence paths.",
  "documents": [
    {"label": "PLAN", "path": "/absolute/plan.md", "sha256": "<64 lowercase hex characters>"},
    {"label": "SPEC", "path": "/absolute/spec.md", "sha256": "<64 lowercase hex characters>"}
  ],
  "scope": {
    "explanation": "Requirements stayed the same; one test was added within an existing task.",
    "approval": "No scope change. Cite any existing authorization or newly approved change precisely.",
    "rows": [
      {"metric": "Delivery phases", "original": "1", "revised": "1", "reason": "Same delivery boundary; original/revised section evidence."},
      {"metric": "Implementation tasks", "original": "5", "revised": "5", "reason": "Map original task IDs to revised task IDs."},
      {"metric": "Supporting tasks", "original": "2", "revised": "2", "reason": "Setup and release tasks; state repeated runs separately."},
      {"metric": "Numbered tasks", "original": "7", "revised": "7", "reason": "Count unique tasks, not checkboxes or test cases."},
      {"metric": "Dependencies / services", "original": "No additions", "revised": "No additions", "reason": "Manifest and plan evidence."}
    ]
  },
  "notes": [{"title": "Verification limit", "body": "Which checks were inspected, executed or not run."}]
}
```

For a recovered report set `kind` to `saved`, keep its original date, scores,
test results and exact handoff, and state that it is being rendered rather than
revalidated. Check current documents and Git state first. If approvals or Git
state changed, mark the old prompt historical in the report and provide a
remediation/resume prompt; unchanged file hashes alone do not establish readiness.
Never replace the recorded hashes just to make an old report appear current.

## Delivery

Open or inspect the generated page. Confirm both five-row tables and averages,
confidence/evidence, scope comparison, limits and the entire prompt are present.
Confirm applicable dependency/alternative tables and recorded choices are inside
the report, and that pending/deferred choices and lookup limits survive copying.
Check that copied text matches `handoff.txt`. Provide a clickable absolute link
to `report.html`; a short local preview URL may accompany it. If serving locally,
bind to `127.0.0.1`, serve only this report directory, and keep that preview alive.
No dependency install or external hosting is needed.

The final response and any later completed-run reminder must contain the actual
report link. A path to a Markdown scratchpad or "see my earlier prompt" is not
delivery. On a renderer failure, fix it before declaring report delivery complete;
if blocked, provide the full Markdown report and exact failure without losing
the evidence. Record this durable directory in the compaction checkpoint.
