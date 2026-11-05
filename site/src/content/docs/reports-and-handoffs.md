---
title: Reports and handoffs
description: What the eight report sections, scores and evidence mean, and how the handoff works.
---

The report is a durable record of one validation, not a live monitor. It lives under `~/.local/share/plan-validation/<repository>/<run>/` with original/revised document copies, Markdown, context metadata and the exact handoff text.

## A summary, then eight evidence sections

New reports open with a header card (the verdict, phase and task counts, whether to run validation again, and a Historical label when the handoff is out of date) and a score strip with both averages and the confidence estimate. Below them are four tabs:

- **Summary:** 1–3 diagrams of the planned design, a count of decisions that need your answer and of watch-list items, the next session's phases with the first prompt and its copy button (or the historical warning when the handoff is out of date), and a "Run validation again" card. When that card says yes in a Ready or Ready after approvals report, run validation again before any phase. In a current report, ready phases then show "Run validation again first", the card comes first and the phase prompts have no copy button.
- **Needs your answer:** each pending decision with its recommendation, confidence and what it holds back, linked to the full option menu in Open items.
- **Watch list:** gaps, limits, risks and items fixed in the plan, each labelled with a word, not only a colour.
- **Full report:** the eight evidence sections below, then the defaults record and the document identity.

A tab with nothing in it is left out. The diagrams describe the feature, not the validation process. The renderer draws them from data, so labels are checked to fit and never overlap. The page stays readable without external scripts, fonts or services; without JavaScript every tab shows in order. A link to a section, such as Open items, opens the Full report tab.

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

The renderer rejects missing sections, malformed score tables, incorrect averages, a Ready report without completed-review metadata, missing scope records and invalid remediation prompts. New reports use format version 4. They also require 1–3 diagrams, the pending-decision and watch lists (which may be empty), a default-decision record, and a phase grouping that covers every validated task once, in plan order. Section 8 needs one prompt of at most 80 words per ready phase, and each prompt must say `Stop at the end of Phase <id>` for its own phase. Each prompt after the first must also say `Confirm Phase <previous> is merged`. Version 4 also requires the header fields (`project`, `audience`, and a `title_accent` found exactly once in the title) and rejects the old `feature` overview. Each pending decision's ID must also appear in Open items. A Ready after approvals verdict needs at least one decision that holds back work, each named in a waiting phase's `waits_for`; a Ready verdict must have none. The run number and the re-run recommendation must follow the rules below. It compares the recorded SHA-256 values with both document files at render time.

These checks validate the report contract. They do not verify the truth of an agent's recorded review, reconstruct Git approvals or rerun tests. A JSON field saying the review is complete is an assertion that must be backed by saved evidence.

## Freshness

Changed or unavailable documents disable the launch prompt controls. A new report keeps its re-run prompt copyable, because running validation again is the advice for changed documents. The agent must also mark Git or approval drift as historical even if document hashes match. The static HTML does not refresh itself when you edit files afterward.

On resumption, the skill rechecks the saved report, current paths, hashes, branch/base and approvals. It can regenerate missing HTML from saved evidence, clearly labeling this as recovery rather than a new validation.

Older contexts without a format version still render through the legacy format. Updating the plugin does not rewrite existing reports, plans or specs. New runs use version 4; versions 2 and 3 still render saved reports, with their Feature at a glance page, exactly as before.

## Run validation again

Each new report says whether to run validation again: **yes** (another run is likely to fix something), **no** (nothing is left that validation can fix) or **stop** (do not run again; you decide the next step). It gives one to four reasons and shows "Run <n> of at most 3".

- The renderer requires yes or stop, never no, when the confidence is below 70% or Unknown, a revised PLAN or SPEC average is below 8.0 or Unknown, or the verdict is Not ready.
- Run 3 never says yes. A pending approval is never a reason to run again: recording your answer re-renders the same report, or, once earlier phases have merged, starts a phase-only validation of the remaining phases.
- With a yes in a Ready or Ready after approvals report, run validation again before starting any phase.
- In a Not ready report, use the remediation prompt first. A remediation session is not a validation run; the re-run prompt then validates the fix as the next counted run.
- A yes comes with a copyable re-run prompt of at most 80 words, saved as `rerun.txt` beside the report. A report re-rendered from saved evidence shows the prompt without a copy button and leaves `rerun.txt` as its run wrote it. It invokes the skill with the plan, the spec and the previous report, says which run it starts, keeps a phase-only run's scope, and never starts implementation.
- Runs are counted per plan path (relative to the repository) and scope, across all worktrees of the repository. A re-render is not a new run. A phase-only validation after merges starts its own count. A fourth run needs your explicit reset.
- If the plan or spec changes after review, the historical warning says to run validation again, naming the next run, instead of more review rounds. After a recorded stop, it says to decide the next step yourself instead.

## Starting implementation

The report groups the validated tasks into small phases and shows them in a table: tasks, whether the phase is docs-only, whether it needs a security review, and whether it can start, waits for an approval or waits for another validation run. Each ready phase gets its own prompt with a copy button (held back while a re-run `yes` comes first), naming that phase and its tasks with absolute plan/spec/report paths. The next agent reads the report and context.json to recover detailed evidence, decisions and permissions before starting. A phase review never authorizes other phases. The prompt tells the agent to continue through passing steps and reviews without asking, to stop only for a required approval or a failure it cannot fix, and to stop at the end of its phase and print the next phase's prompt without starting it. See [Phased implementation](/plan-validation/phased-implementation/) for the recommended workflow. A line above the prompt suggests a reasoning effort with a reason; you choose the actual level in your host. Not ready reports, and reports whose first phase waits for an approval, supply one short prompt that resolves the blocker instead.

## Rendering manually

Use the exact schema and headings in the bundled [HTML report reference](https://github.com/snowholt-labs/plan-validation/blob/main/skills/validate-plan/references/html-report.md):

```bash
python3 /path/to/validate-plan/scripts/render_report.py \
  --report /path/to/run/report.md \
  --context /path/to/run/context.json \
  --output /path/to/run/report.html \
  --open
```

Substitute real absolute paths. Use a dedicated private run directory. The helper writes `report.html`, its Markdown source, `handoff.txt` (the first prompt), a `handoff-phase-<id>.txt` for each ready phase, and `rerun.txt` when the report recommends running validation again. A re-render deletes earlier phase files first, and earlier re-run files too, except when it re-renders a report from saved evidence. No hosting or network service is needed. With `--open`, the helper also opens the report in your default browser when a desktop is available; otherwise use the `report.html` link.

Reports stay local unless you turn on the Claude Code setting **Publish validation reports as private artifacts** (`publish_artifact`, off by default). With it on, the skill renders each new report without `--open`, publishes it to your claude.ai account as a private artifact, saves the link in `artifact.json` beside the report and gives the artifact link before the local one. The upload includes the report's local paths and project details. The skill never shares, pins or changes the visibility of the artifact. Publishing needs a Claude Code session that offers the Artifact tool and a scratchpad folder. If either is missing, or publishing fails before the upload finishes, the skill says so in one line and opens the local report instead. If the upload worked but a later step failed, it still gives the artifact link and names the failed step. In the artifact viewer, tabs, links within the page and copy buttons work, but the **Print / PDF** button and the download links do not; use the local `report.html` to print or download. Recording an answer re-renders the report locally; the artifact keeps the earlier version until you ask the skill to update it. With the setting off, in Codex or in a standalone skill install, the skill makes no publish call, even when the host suggests publishing finished work.
