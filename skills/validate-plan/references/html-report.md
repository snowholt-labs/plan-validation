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
  section 6 and research/execution limits in section 7; section 8 points back to
  those records instead of repeating them. Use the exact source headings above;
  versions 2 and 3 render friendlier display labels without changing section anchors.
  In sections 1, 4, 5 and 7, `### Technical details` starts expandable evidence
  through the end of that section. Put a concise results/limits summary before
  it. The marker is forbidden in sections 2, 3, 6 and 8 so score tables, blockers
  and the prompt stay visible. Markers inside fenced examples are literal text.
- `context.json`: the small context record below. Use verified facts; use
  `Unknown` for unrecovered counts. Full document hashes identify the revisions
  that were actually validated, not whatever file happens to exist later.
  New reports (`kind: new`) must use `format_version: 3`, a feature overview, an explicit
  `decisions_without_reply` list (empty when no routine defaults were used), and the
  phase grouping in `task_inventory` and `phases` (rules below).
- `revised-plan.md` and `revised-spec.md`: copies of the validated revisions.
- A local research ledger and source evidence when research ran or was declined,
  including sent, declined or unavailable lookups. Record only public query text;
  preserve dates and evidence limits. No research requires no empty ledger.

Run the helper from **this skill's** directory (substitute absolute paths):

```bash
python3 <skill-directory>/scripts/render_report.py --report <run-directory>/report.md --context <run-directory>/context.json --output <run-directory>/report.html --open
```

Leave out `--open` when re-rendering a saved report unless the user asked to see it again.

The helper uses only Python's standard library. Versions 2 and 3 add a local HTML/CSS
block diagram above the eight evidence sections, optional expandable technical
details, and the routine-default record at the end. It requires 3–7 feature
steps, each with a nonempty title and description, and rejects handoffs longer
than 80 whitespace-separated words; a backtick-quoted absolute path counts as one word. Target 50–80 words; do not add filler to
meet a minimum. Print/PDF expands details and restores their state afterward.
Use `feature.layout: flow` (the default) for a genuine sequence with arrows, or
`blocks` for independent parts displayed without ordering or arrows. The
`steps` array supplies the block text in either layout.
It renders the full report and
writes `handoff.txt` from section 8 exactly when the handoff is current. It rejects missing sections, incorrect
averages and Ready reports with an incomplete cold read. It checks the two live
document fingerprints; a mismatch labels the result historical and removes the
copy button and prompt download, and prefixes the exported text with a warning.
Set `handoff_status` to `historical` if Git state or approvals have drifted even
when the document hashes match. A Not ready prompt must explicitly say
`Do not start dependent implementation.` and must not begin `Implement ...`.
These are structural checks, not a substitute for reviewing the
evidence, approvals, Git state or the generated report.

Version 3 adds the phase grouping. The renderer also checks that:

- the phases cover `task_inventory` exactly once, in plan order, with no empty phase;
- phase IDs are unique ignoring case and safe as file names (1–16 letters, digits,
  dots or hyphens, starting with a letter or digit);
- the flags are consistent: `docs_only` and `security_review` are booleans and not
  both true, a security review has a `security_reason`, and a waiting phase names
  what it `waits_for`;
- once a phase waits, every later phase waits, and a `Ready` verdict has no waiting phase;
- section 8 has one fenced prompt per ready phase, in order, each within 80 words and
  saying `Stop at the end of Phase <id>` for its own phase only, never negated;
- a Not ready report, or one whose first phase waits, has exactly one prompt that
  says `Do not start dependent implementation.` and has no `Implement` instruction.

Section 8 shows the phase table above the prompts, and each phase prompt has its
own copy button. Besides `handoff.txt` (the first prompt), the renderer writes
`handoff-phase-<id>.txt` for each ready phase, with the historical warning when the
handoff is not current. A re-render first deletes every `handoff-phase-*.txt` in the
run directory, so an earlier phase prompt never survives a changed verdict.

Example context shape (replace every example value; do not invent a review):

```json
{
  "format_version": 3,
  "title": "Feature name",
  "validation_date": "2026-10-14",
  "kind": "new",
  "review_status": "complete",
  "handoff_status": "current",
  "summary": "What is ready, the important fixes, and the main limitation.",
  "freshness": "Checked at <UTC time>: branch, head, base, approvals and PR state. Tests were run at the recorded SHA.",
  "provenance": "Validation session identifier and source evidence paths.",
  "feature": {
    "layout": "flow",
    "summary": "The proposed feature lets a reader open a document they can access.",
    "steps": [
      {"title": "Choose a document", "description": "The reader selects a saved document."},
      {"title": "Check access", "description": "The application checks permission to open it."},
      {"title": "Show the result", "description": "The document opens, or an explanation appears."}
    ]
  },
  "decisions_without_reply": [],
  "task_inventory": ["1", "2", "3"],
  "phases": [
    {"id": "1", "title": "Renderer", "tasks": ["1", "2"], "docs_only": false,
     "security_review": true, "security_reason": "Renders untrusted text into HTML.", "status": "ready"},
    {"id": "2", "title": "Docs", "tasks": ["3"], "docs_only": true,
     "security_review": false, "status": "waiting", "waits_for": "D1 approval"}
  ],
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

`task_inventory` lists every validated task ID as a string, in plan order
(`"5b"` and `"5"` are different tasks). Each phase has an `id`, a `title`, its
`tasks`, the booleans `docs_only` and `security_review` (with `security_reason`
when true), and `status` `ready` or `waiting` (with `waits_for` when waiting).
A phase-only validation lists only the selected tasks.

Each routine-default entry, when applicable, has `question`, `decision` and
`reason` strings. Do not invent defaults for a demonstration or record a required
approval as a routine choice. The final HTML displays this list; the launch
prompt references context.json so the next agent can recover it.

Existing contexts without `format_version` are treated as version 1, preserving
their original long prompt and eight-section layout when explicitly rendered.
Do not modify existing reports, plans or specs to migrate the format. New
validation runs use version 3; version 2 renders saved reports only, and legacy support is for recovery, not a way around
the new writing requirements. Unsupported versions are rejected.

For a recovered report set `kind` to `saved`, keep its original date, scores,
test results and exact handoff, and state that it is being rendered rather than
revalidated. Check current documents and Git state first. If approvals or Git
state changed, mark the old prompt historical in the report and provide a
remediation/resume prompt; unchanged file hashes alone do not establish readiness.
Never replace the recorded hashes just to make an old report appear current.

## Delivery

Open or inspect the generated page. For new reports, confirm the feature
diagram, the phase table, one short prompt per ready phase, visible blockers/limits, expandable evidence and final
defaults record. Confirm both five-row tables and averages,
confidence/evidence, scope comparison, limits and the entire prompt are present.
Confirm applicable dependency/alternative tables and recorded choices are inside
the report, and that the copied prompt references their complete saved record.
Check that each copied prompt matches `handoff.txt` or its `handoff-phase-<id>.txt`. Provide a clickable absolute link
to `report.html`; a short local preview URL may accompany it. If serving locally,
bind to `127.0.0.1`, serve only this report directory, and keep that preview alive.
No dependency install or external hosting is needed. Render new reports with `--open`;
keep the clickable absolute link to `report.html` either way, and when the renderer
prints `"opened": false`, do not say the report was opened.

The final response and any later completed-run reminder must contain the actual
report link. A path to a Markdown scratchpad or "see my earlier prompt" is not
delivery. On a renderer failure, fix it before declaring report delivery complete;
if blocked, provide the full Markdown report and exact failure without losing
the evidence. Record this durable directory in the compaction checkpoint.
