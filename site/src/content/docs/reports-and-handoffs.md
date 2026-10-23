---
title: Reports and handoffs
description: What the eight report sections, scores and evidence mean, and how the handoff works.
---

The report is a durable record of one validation, not a live monitor. It lives under `~/.local/share/plan-validation/<repository>/<run>/` with original/revised document copies, Markdown, context metadata and the exact handoff text.

## A quick overview, then eight evidence sections

New reports begin with **Feature at a glance**: 3–7 plain-language blocks showing the proposed feature's main behavior. The diagram describes the feature, not the validation process, and stays readable without external scripts, fonts or services.

| Section | Purpose |
| --- | --- |
| Verdict | Ready, Ready after approvals or Not ready for the named scope |
| PLAN comparison | Five original/revised dimensions and the arithmetic average |
| SPEC comparison | Five separate dimensions and average |
| Decision confidence | Evidence, subjective confidence and remaining uncertainty |
| Changes | Phase/task/dependency counts, mappings, reasons, dependency/alternative comparisons and approval basis |
| Open items | Decision IDs/answers, blockers, pending approvals, accepted limits and separate follow-ups |
| Verification and checkout | Actual commands/results, tested revision and worktree cleanup |
| Fresh-session handoff | A phase table, then one 50–80-word launch prompt per ready phase referencing the complete saved evidence |

Short summaries explain what changed and why it matters. Both full score tables, blockers, pending approvals and important limits stay visible. Supporting commands, hashes and detailed reasoning can sit under **Technical details**. Print/PDF includes the expanded evidence.

The final **Decisions made without your reply** record lists each unanswered routine question, the recommendation used and its reason, or None. A default is not approval for a dependency, service, security change or external action.

## Scores and evidence

Each dimension is scored out of ten. The five dimensions have equal weight. An Unknown dimension makes that document's average Unknown. A higher score is not a success probability or a calibrated security assessment.

Dependency and alternatives decisions use High/Medium/Low confidence with dated primary-source evidence, reasons, and Verified/Assumption/Unknown claims. These are not package trust scores. Applicable comparisons stay in section 5; choices and lookup limits stay in sections 6–7. The short handoff points to those records instead of repeating them.

Existing readiness confidence estimates, when used, are subjective and supported by evidence and uncertainty. `Unknown` is preferable to invented precision. An official source establishes what that source documents; it does not prove your repository ran successfully.

## What the renderer checks

The renderer rejects missing sections, malformed score tables, incorrect averages, a Ready report without completed-review metadata, missing scope records and invalid remediation prompts. New reports use format version 3. They also require the feature overview, a default-decision record, and a phase grouping that covers every validated task once, in plan order. Section 8 needs one prompt of at most 80 words per ready phase, and each prompt must say `Stop at the end of Phase <id>` for its own phase. It compares the recorded SHA-256 values with both document files at render time.

These checks validate the report contract. They do not verify the truth of an agent's recorded review, reconstruct Git approvals or rerun tests. A JSON field saying the review is complete is an assertion that must be backed by saved evidence.

## Freshness

Changed or unavailable documents disable the current prompt controls. The agent must also mark Git or approval drift as historical even if document hashes match. The static HTML does not refresh itself when you edit files afterward.

On resumption, the skill rechecks the saved report, current paths, hashes, branch/base and approvals. It can regenerate missing HTML from saved evidence, clearly labeling this as recovery rather than a new validation.

Older contexts without a format version still render through the legacy format. Updating the plugin does not rewrite existing reports, plans or specs. New runs use version 3; version 2 still renders saved reports.

## Starting implementation

The report groups the validated tasks into small phases and shows them in a table: tasks, whether the phase is docs-only, whether it needs a security review, and whether it can start or waits for an approval. Each ready phase gets its own prompt with a copy button, naming that phase and its tasks with absolute plan/spec/report paths. The next agent reads the report and context.json to recover detailed evidence, decisions and permissions before starting. A phase review never authorizes other phases. The prompt tells the agent to continue through passing steps and reviews without asking, to stop only for a required approval or a failure it cannot fix, and to stop at the end of its phase and print the next phase's prompt without starting it. See [Phased implementation](/plan-validation/phased-implementation/) for the recommended workflow. A line above the prompt suggests a reasoning effort with a reason; you choose the actual level in your host. Not ready reports, and reports whose first phase waits for an approval, supply one short prompt that resolves the blocker instead.

## Rendering manually

Use the exact schema and headings in the bundled [HTML report reference](https://github.com/snowholt-labs/plan-validation/blob/main/skills/validate-plan/references/html-report.md):

```bash
python3 /path/to/validate-plan/scripts/render_report.py \
  --report /path/to/run/report.md \
  --context /path/to/run/context.json \
  --output /path/to/run/report.html \
  --open
```

Substitute real absolute paths. Use a dedicated private run directory. The helper writes `report.html`, its Markdown source, `handoff.txt` (the first prompt) and a `handoff-phase-<id>.txt` for each ready phase. A re-render deletes earlier phase files first. No hosting or network service is needed. With `--open`, the helper also opens the report in your default browser when a desktop is available; otherwise use the `report.html` link. Do not publish a report merely because the renderer accepted it.
