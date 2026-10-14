# Reports and handoffs

The report is a durable record of one validation, not a live monitor. It lives under `~/.local/share/plan-validation/<repository>/<run>/` with original/revised document copies, Markdown, context metadata and the exact handoff text.

## Eight sections

| Section | Purpose |
| --- | --- |
| Verdict | Ready, Ready after approvals or Not ready for the named scope |
| PLAN comparison | Five original/revised dimensions and the arithmetic average |
| SPEC comparison | Five separate dimensions and average |
| Decision confidence | Evidence, subjective confidence and remaining uncertainty |
| Changes | Phase/task/dependency counts, mappings, reasons and approval basis |
| Open items | Blockers, pending approvals, accepted limits and separate follow-ups |
| Verification and checkout | Actual commands/results, tested revision and worktree cleanup |
| Fresh-session handoff | Complete implementation or remediation prompt |

## Scores and evidence

Each dimension is scored out of ten. The five dimensions have equal weight. An Unknown dimension makes that document's average Unknown. A higher score is not a success probability or a calibrated security assessment.

Confidence estimates, when used, are subjective and supported by evidence and uncertainty. `Unknown` is preferable to invented precision. An official source establishes what that source documents; it does not prove your repository ran successfully.

## What the renderer checks

The renderer rejects missing sections, malformed score tables, incorrect averages, a Ready report without completed-review metadata, missing scope records and invalid remediation prompts. It compares the recorded SHA-256 values with both document files at render time.

These checks validate the report contract. They do not verify the truth of an agent's recorded review, reconstruct Git approvals or rerun tests. A JSON field saying the review is complete is an assertion that must be backed by saved evidence.

## Freshness

Changed or unavailable documents disable the current prompt controls. The agent must also mark Git or approval drift as historical even if document hashes match. The static HTML does not refresh itself when you edit files afterward.

On resumption, the skill rechecks the saved report, current paths, hashes, branch/base and approvals. It can regenerate missing HTML from saved evidence, clearly labeling this as recovery rather than a new validation.

## Rendering manually

Use the exact schema and headings in the bundled [HTML report reference](https://github.com/snowholt/plan-validation/blob/main/skills/validate-plan/references/html-report.md):

```bash
python3 /path/to/validate-plan/scripts/render_report.py \
  --report /path/to/run/report.md \
  --context /path/to/run/context.json \
  --output /path/to/run/report.html
```

Substitute real absolute paths. Use a dedicated private run directory. The helper writes `report.html`, its Markdown source and `handoff.txt`. No hosting or network service is needed. Do not publish a report merely because the renderer accepted it.
