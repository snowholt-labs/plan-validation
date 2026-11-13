---
title: Reports and handoffs
description: What the eight report sections, scores and evidence mean, and how the handoff works.
---

The report is a durable record of one validation, not a live monitor. It lives under `~/.local/share/plan-validation/<repository>/<run>/` with original/revised document copies, Markdown, context metadata and the exact handoff text.

## A summary, then eight evidence sections

New reports open with a header card (the verdict, phase and task counts, and a Historical label when the handoff is out of date) and a score strip with both averages and the confidence estimate. Below them are four tabs:

- **Summary:** 1–3 diagrams of the planned design, a count of decisions that need your answer and of watch-list items, the next session's phases with the first prompt and its copy button (or the historical warning when the handoff is out of date). A report saved by an earlier version 4 run also shows its "Run validation again" card, as that run recorded it.
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

The renderer rejects missing sections, malformed score tables, incorrect averages, a Ready report without completed-review metadata, missing scope records and invalid remediation prompts. New reports use format version 5. They also require 1–3 diagrams, the pending-decision and watch lists (which may be empty), a default-decision record, and a phase grouping that covers every validated task once, in plan order. Section 8 needs one prompt of at most 80 words per ready phase, and each prompt must say `Stop at the end of Phase <id>` for its own phase. Each prompt after the first must also say `Confirm Phase <previous> is merged`. Versions 4 and 5 also require the header fields (`project`, `audience`, and a `title_accent` found exactly once in the title) and reject the old `feature` overview. Each pending decision's ID must also appear in Open items. A Ready after approvals verdict needs at least one decision that holds back work, each named in a waiting phase's `waits_for`; a Ready verdict must have none. It compares the recorded SHA-256 values with both document files at render time.

These checks validate the report contract. They do not verify the truth of an agent's recorded review, reconstruct Git approvals or rerun tests. A JSON field saying the review is complete is an assertion that must be backed by saved evidence.

## Freshness

Changed or unavailable documents disable the launch prompt controls. In a version 5 report, the historical warning says what changed and to reconcile the change before building, or validate the changed scope again. It names no run number and no limit. The agent must also mark Git or approval drift as historical even if document hashes match. The static HTML does not refresh itself when you edit files afterward.

On resumption, the skill rechecks the saved report, current paths, hashes, branch/base and approvals. It can regenerate missing HTML from saved evidence, clearly labeling this as recovery rather than a new validation.

Older contexts without a format version still render through the legacy format. Updating the plugin does not rewrite existing reports, plans or specs. New runs use version 5, which is version 4 without the re-run recommendation, run count and held prompts. Versions 2–4 still render saved reports exactly as before: versions 2 and 3 with their Feature at a glance page, and version 4 with its re-run card, run number and held prompts.

## Review and questions in one run

Validation does not ask you to run it again. Within one run, an independent reviewer checks the revised plan and spec, the agent fixes verified Medium and High findings, and review runs again until none remain. A finding that keeps coming back after fixes becomes a blocker instead of another loop. Then `/code-review` and `/security-review` run once each on saved copies of the final plan and spec, and the report records what each read, so a plan's docs PR can reuse them. A finding whose fix would change requirements, architecture, security boundaries or scope is not fixed; it becomes a pending approval. Low findings are listed.

At the end, the agent asks one round of questions: each pending approval with its recommendation, and the Low findings to fix or skip. It applies your answers and re-renders the report in the same run. An answer that changes the plan or spec is tested again where it changed a rehearsed task, checked by a fresh reviewer and recorded, so the phase prompts stay current. A reviewer finding that needs your approval stays open in the report; there is no second round of questions. With publishing off, the updated report opens in the browser after your answers. An unanswered question stays pending in the report, never approved.

- After a Not ready report, use the remediation prompt first, then validate the fixed plan to get phase prompts.
- An answer given after the run's final reply still re-renders the same report locally; validate the revised plan to get current prompts. Once earlier phases have merged, it starts a phase-only validation of the remaining phases instead.
- A report saved by an earlier version 4 run keeps its re-run card, run number and `rerun.txt`. An answer to such a report is not re-rendered or migrated: validate the plan again, and the new run uses version 5.

## Starting implementation

The report groups the validated tasks into small phases and shows them in a table: tasks, whether the phase is docs-only, whether it is security-sensitive (where review should look hardest), and whether it can start or waits for an approval. Each ready phase gets its own prompt with a copy button, naming that phase and its tasks with absolute plan/spec/report paths. Above the prompts, a done-check line per phase lists the commands that prove it is ready. The next agent reads the report and context.json to recover detailed evidence, decisions and permissions before starting. A phase review never authorizes other phases. The prompt tells the agent to follow the plan's Phase workflow, to continue through passing steps and reviews without asking, to stop only for the Phase workflow's stop reasons (a destructive step, a security-sensitive action, an approval it does not have, or a plan too broken to follow), and to stop at the end of its phase and print the next phase's prompt without starting it. See [Phased implementation](/plan-validation/phased-implementation/) for the recommended workflow. A line above the prompt suggests a reasoning effort with a reason; you choose the actual level in your host. Not ready reports, and reports whose first phase waits for an approval, supply one short prompt that resolves the blocker instead.

## Rendering manually

Use the exact schema and headings in the bundled [HTML report reference](https://github.com/snowholt-labs/plan-validation/blob/main/skills/validate-plan/references/html-report.md):

```bash
python3 /path/to/validate-plan/scripts/render_report.py \
  --report /path/to/run/report.md \
  --context /path/to/run/context.json \
  --output /path/to/run/report.html \
  --open
```

Substitute real absolute paths. Use a dedicated private run directory. The helper writes `report.html`, its Markdown source, `handoff.txt` (the first prompt) and a `handoff-phase-<id>.txt` for each ready phase. Before writing, a render deletes the earlier `handoff.txt` and phase files, and any `rerun.txt`. A report saved by an earlier version 4 run that re-renders from saved evidence keeps its `rerun.txt` and held notes. No hosting or network service is needed. With `--open`, the helper also opens the report in your default browser when a desktop is available; otherwise use the `report.html` link.

Reports stay local unless you turn on the Claude Code setting **Publish validation reports as private artifacts** (`publish_artifact`, off by default). With it on, the skill renders each new report without `--open`, publishes it to your claude.ai account as a private artifact, saves the link in `artifact.json` beside the report and gives the artifact link before the local one. The upload includes the report's local paths and project details. The skill never shares, pins or changes the visibility of the artifact. Publishing needs a Claude Code session that offers the Artifact tool and a scratchpad folder. If either is missing, or publishing fails before the upload finishes, the skill says so in one line and opens the local report instead. If the upload worked but a later step failed, it still gives the artifact link and names the failed step. In the artifact viewer, tabs, links within the page and copy buttons work, but the **Print / PDF** button and the download links do not; use the local `report.html` to print or download. The answers to the end-of-run questions update that same artifact in the same run, even when `artifact.json` is missing, as long as the session still holds the link it published. If the page cannot be updated, the reply says in one line that the online page shows an earlier render whose prompts may be out of date, and the local report opens instead. An answer given after the run's final reply re-renders the report locally; the artifact keeps the earlier version until you ask the skill to update it. With the setting off, in Codex or in a standalone skill install, the skill makes no publish call, even when the host suggests publishing finished work.
