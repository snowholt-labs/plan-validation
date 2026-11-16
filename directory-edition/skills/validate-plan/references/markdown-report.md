# Durable Markdown report

Read this when creating the baseline or repeating a validation result.
`report.md` is the full report, not an abridged alternative. The chat response gives
the verdict, the report link and any immediate blocker in at most three bullets.
If the user explicitly asks for the full report in chat, print all eight sections too,
with the Summary's design descriptions, open decisions, watch list and defaulted decisions.

## Files

Use a new, private local run directory under
`~/.local/share/plan-validation/<repo-name>/<UTC-timestamp>-<topic>/`.
`<repo-name>` is the folder name of the repository's main worktree: the first
`worktree` entry of `git worktree list --porcelain`. A linked worktree or a
`.worktrees/…` checkout therefore uses the same folder as the main checkout.
Do not put the only copy in `/tmp`, a session scratchpad, personal memory or a
throwaway worktree. Do not commit it to the project.

During baseline collection, copy the untouched documents to `original-plan.md` and
`original-spec.md` in this directory, and record their hashes (below). Record baseline
counts and their definitions. Use verified facts; use `Unknown` for unrecovered counts.
Full document hashes identify the revisions that were actually validated, not whatever
file happens to exist later. After validation, save:

- `report.md`: the complete report, in the layout below. It is the only report file;
  every record the report needs lives in it.
- `handoff.txt` and one `handoff-phase-<id>.txt` per ready phase (Handoff files below).
- `revised-plan.md` and `revised-spec.md`: copies of the validated revisions.
- A local research ledger and source evidence when research ran or was declined,
  including sent, declined or unavailable lookups. Record only public query text;
  preserve dates and evidence limits. No research requires no empty ledger.

## Hashes

Compute document hashes with `shasum -a 256` or `sha256sum`, whichever is present.
Record the full hex digest: 64 lowercase hexadecimal characters, never a shortened one.

## Report layout

Start `report.md` with a level-one title naming the feature, for example
`# Feature name: plan validation`, and the validation date. Then write these
level-two sections in this order:

1. `## Summary` (unnumbered), which shows what the feature is and what needs attention,
   without repeating the evidence:
   - a plain summary: what is ready, the important fixes and the main limitation, and
     when the branch, head, base, approvals and PR state were checked;
   - one or two short text descriptions of the intended design, not the validation
     workflow. Each says whether it describes planned, existing or changing parts, does
     not imply proposed behavior is already shipped, and names only connections the spec
     describes. Draw no images or diagrams;
   - **Open decisions**: a table `ID | Question | Recommendation | Confidence | Holds back`,
     or `None.` when there are none (rules below);
   - **Watch list**: a table `Kind | Title | Body`, or `None.` when there are none
     (rules below).
2. The eight numbered sections, with the exact headings `## 1. Verdict`,
   `## 2. PLAN comparison`, `## 3. SPEC comparison`, `## 4. Decision confidence`,
   `## 5. Changes`, `## 6. Open items`, `## 7. Verification and checkout` and
   `## 8. Fresh-session handoff`, as [report-contract.md](report-contract.md) defines them.
3. `## Decisions made without your reply` (unnumbered).
4. `## Run record` (unnumbered), last (tables below).

Within the eight sections:

- Both score tables have five dimension rows and an `Average /10` row. Section 1 begins
  with the verdict and contains `Confidence: 75%` (use the actual estimate, or `Unknown`).
- Section 5 begins with the scope comparison table, `Measure | Original | Revised | Reason / evidence`,
  with the rows `Delivery phases`, `Implementation tasks`, `Supporting tasks`,
  `Numbered tasks` and `Dependencies / services`. Follow it with its explanation and
  its approval basis (or `Unknown`), written in `report.md` itself. Put applicable
  dependency and alternatives tables in section 5 after that explanation.
- Keep section 4's four-column table, using High/Medium/Low for dependency decisions and
  the existing convention for readiness. Put decision states in section 6 and
  research/execution limits in section 7; section 8 points back to those records instead
  of repeating them.
- In sections 1, 4, 5 and 7, `### Technical details` starts the supporting evidence,
  which runs to the end of that section. Put a concise results/limits summary before it.
  The heading is forbidden in sections 2, 3, 6 and 8, so score tables, blockers and the
  prompts stay in the main text. Headings inside fenced examples are literal text.

### Open decisions

The open decisions mirror section 6's pending approvals for the validated scope, one row
per decision ID. Recorded defaults are not open decisions.

- **ID:** 1–16 letters, digits, dots or hyphens, starting with a letter or digit, unique
  ignoring case, and present in section 6 with the same case, as a whole word (`D1` does
  not match `D10`).
- **Question**, **Recommendation**, and **Confidence** of `High`, `Medium` or `Low`.
- **Holds back:** the phases or tasks it holds back, or `Nothing` or `None`, in any case,
  when it holds back no work. Any other text counts as holding back work.
- A `Ready after approvals` verdict needs at least one decision that holds back work, and
  the Waits for column of a waiting phase must name each such decision by its exact ID
  (list each ID, never a range such as `D1-D3`). A `Ready` verdict must have none that does.
- In a phase-only validation, an approval that holds back only phases outside the selected
  scope is a separately scoped follow-up in section 6 and stays out of the open decisions.

### Watch list

Each item has a **Kind** of `gap`, `limit`, `risk` or `fixed`, a **Title** of at most
60 characters and a one- or two-sentence **Body**. The watch list names the gaps, limits,
risks and items fixed in the plan that a reader should keep in mind. Keep blockers and
pending approvals in section 6 as well; the watch list does not replace it.

### Decisions made without your reply

List each unanswered routine question with its **Question**, **Decision** and **Reason**,
or write `None. No unanswered routine questions were defaulted.` These are recorded
defaults, not user approvals; required approvals stay in Open items. Do not invent
defaults for a demonstration or record a required approval as a routine choice. The
launch prompt references `report.md`, so the next agent can recover this record.

### Run record

- **Documents:** a table `Label | Path | SHA-256` with exactly two rows, `PLAN` and `SPEC`.
  Each path is absolute, holds no NUL character, and each hash is the full 64-character
  SHA-256 (Hashes above).
- `Review status: complete` or `Review status: incomplete`, on its own line. It is
  `complete` only after the independent review ran and its findings were dispositioned.
- `Handoff status: current` or `Handoff status: historical`, on its own line. Before
  writing it, recompute both live document hashes. Set `historical` when either differs
  from the Documents table, or when Git state or approvals drifted, even when the hashes
  match.
- **Task inventory:** a one-column table `Task` listing every validated task ID in plan
  order, each once. Task IDs are text, so `5b` and `5` are different tasks. A phase-only
  validation lists only the selected tasks.
- **Phases:** a table `ID | Title | Tasks | Status | Waits for | Docs only | Security review | Security reason`,
  one row per phase in order. Tasks are the phase's task IDs, comma separated. Status is
  `ready` or `waiting`; Waits for names what a waiting phase waits for and is `None` for a
  ready phase. Docs only and Security review are `yes` or `no`. Security reason gives the
  reason when Security review is `yes`, and `None` otherwise. The Security review column
  marks a security-sensitive phase for review focus; SKILL.md "Phase grouping" says when
  a phase gets a security review.

## Handoff files

Before writing any handoff file, delete `handoff.txt` and every earlier
`handoff-phase-*.txt` in the run directory, so an earlier prompt never survives a
changed verdict or a failed write. Then write:

- `handoff.txt`: the first fenced prompt of section 8 (the first ready phase's prompt, or
  the single remediation prompt), exactly as written there;
- `handoff-phase-<id>.txt` for each ready phase: that phase's prompt, exactly as written
  in section 8.

When Handoff status is `historical`, every one of these files starts with these two lines,
and section 8 of `report.md` starts with the same two lines, unfenced, above every prompt:

```text
HISTORICAL PROMPT — DO NOT EXECUTE.
Document identity, Git state or approvals changed or could not be checked. Reconcile the change before building, or validate the changed scope again.
```

Each prompt targets 50–80 words; do not add filler to meet a minimum.

## Saved reports

For a recovered report, say in the Summary that it is a saved report, keep its original
date, scores, test results and exact handoff, and state that it is being rewritten rather
than revalidated. Check current documents and Git state first. If approvals or Git state
changed, mark the old prompt historical in the report and provide a remediation/resume
prompt; unchanged file hashes alone do not establish readiness. A saved report keeps
section 8 as its run wrote it. Never replace the recorded hashes just to make an old
report appear current. The single exception is the same run's end-of-run answers: after
the post-answer review and the security review of the answer edits pass (SKILL.md step 8),
the hashes of the reviewed final documents, `post-answer-plan.md` and
`post-answer-spec.md`, replace the earlier ones. A saved report never refreshes hashes.
Do not modify existing reports, plans or specs to migrate their format.

## Self-check

Run this checklist on the written `report.md` and handoff files before replying. Mark
each item pass or fail in the reply's self-check result. Fix every failed item, then
check it again; never report a failed item as passed. These are structural checks made
by the agent, not by code, and they are not a substitute for reviewing the evidence,
approvals, Git state or the report itself.

1. Exactly eight numbered level-two sections with the exact headings, each running to the
   next level-two heading outside a code fence (headings inside fences, such as in a
   prompt, do not count), so section 8 ends at `## Decisions made without your reply`,
   and items 12–15 read only that span. Each section holds evidence or an explicit
   `Unknown` or `None`. No code fence is left unclosed. Every table row has its header's
   column count.
2. Section 1 starts with `Ready`, `Ready after approvals` or `Not ready`, and its visible
   text (before any `### Technical details`) has `Confidence:` with `Unknown` or a whole
   percentage from 0 to 100 in steps of 5.
3. `Ready` and `Ready after approvals` both need `Review status: complete`.
4. Sections 2 and 3 each hold exactly one four-column table: a header, a separator, five
   dimension rows and an `Average /10` row, with both score columns labeled `/10`, scores
   0–10 or `Unknown`, and each declared average equal to the five scores' mean rounded
   half up to one decimal (`Unknown` if any score is `Unknown`).
5. Section 4's visible text (before any `### Technical details`) has a four-column table
   whose first header is `Decision`, with at least one evidence row.
6. `### Technical details` appears at most once per section, only in sections 1, 4, 5
   and 7, with visible text before it and evidence after it.
7. Section 5's scope table has the rows Delivery phases, Implementation tasks, Supporting
   tasks, Numbered tasks and Dependencies / services, plus an explanation and an approval
   basis (or `Unknown`).
8. Documents table: exactly PLAN and SPEC, absolute paths, full 64-character SHA-256.
   Recompute both live hashes, and set Handoff status to `historical` when either differs
   or Git state or approvals drifted.
9. Phases: every task in the Task inventory once, in plan order, no empty phase. IDs are
   unique ignoring case, 1–16 letters, digits, dots or hyphens, starting with a letter or
   digit. Each phase has a title. Docs only and Security review are `yes` or `no` and not
   both `yes`; Security review `yes` has a reason. Status is `ready` or `waiting`, and a
   waiting phase says what it waits for. No ready phase comes after a waiting one, and a
   `Ready` verdict has no waiting phase.
10. Open decisions: each has an ID (same format, unique ignoring case), question,
    recommendation, confidence `High`, `Medium` or `Low`, and holds back. Each ID appears
    as a whole word in section 6, with the same case. `Ready after approvals` needs at
    least one that holds back work (anything but `Nothing` or `None`), each named by its
    exact ID in a waiting phase's Waits for; `Ready` has none that holds back work.
11. Each watch-list item has a kind of `gap`, `limit`, `risk` or `fixed`, a nonempty title
    of at most 60 characters and a nonempty body. Each default under
    `## Decisions made without your reply` has a question, a decision and a reason.
12. Section 8: one fenced prompt per ready phase, in order, or exactly one fenced prompt
    when no phase is ready. Each has at most 80 whitespace-separated words, counting a
    backtick-quoted span as one word only when it is the recorded PLAN or SPEC path or
    this run's `report.md` quoted exactly, or an absolute path with no spaces that starts
    with `~/`, a drive (`C:\` or `C:/`) or `/`, where a `/` path needs a first segment
    without a colon and, without a file extension, a second segment (so
    `/feature-dev:implement` and `/implement/` count as text). No prompt has an unclosed
    inner fence. Each ready prompt says `Stop at the end of Phase <id>`, not negated, and
    every `Stop at the end of Phase` sentence in it names that prompt's own phase and none
    is negated. Each ready prompt after the first says `Confirm Phase <previous> is merged`,
    not negated. Items 12–14 match words ignoring case, and a required sentence may wrap
    across lines.
13. A `Not ready` report, or one whose first phase waits, has exactly one prompt, even
    when Phases rows say `ready`, with `Do not start dependent implementation` (ignoring
    case) and no `implement`, `implements` or `implementing` (also with `re` or `re-`)
    except right after `not`, `cannot`, `n't` or `never` on the same line, or inside a
    backtick-quoted path as item 12 defines it (a quoted slash command such as
    `/feature-dev:implement` is text and is checked).
14. Neither section 8 nor its prompts say "run validation again first" unless `not`,
    `never` or `n't` followed by `need to` or `have to` (as in `do not need to`,
    `don't have to`), or `no need to`, comes right before it. `Do not run validation again
    first` fails, so reword it: a new report has no re-run.
15. When Handoff status is `historical`, section 8 and every handoff file start with the
    historical warning lines (Handoff files above).
16. The Task inventory is nonempty and lists each task ID once.
17. `Review status` is exactly `complete` or `incomplete`, and `Handoff status` is exactly
    `current` or `historical`.
18. `handoff.txt` and each `handoff-phase-<id>.txt` match their section 8 prompts exactly,
    and no handoff file remains for a phase that is no longer ready.

## Delivery

Read the written files back. For new reports, confirm the Summary's design descriptions,
open decisions and watch list, the Run record's Phases table, one short prompt per ready
phase, visible blockers/limits, the technical details and the final defaults record.
Confirm both five-row tables and averages, confidence/evidence, scope comparison, limits
and the entire prompts are present. Confirm applicable dependency/alternative tables and
recorded choices are inside the report, and that each prompt references their complete
saved record. Provide a clickable absolute link to `report.md`.

The final response and any later completed-run reminder must contain the actual report
link. A path to a Markdown scratchpad or "see my earlier prompt" is not delivery. When a
self-check item cannot be made to pass, say so with the failed item; if blocked, provide
the full Markdown report and the exact failure without losing the evidence. Record this
durable directory in the compaction checkpoint.
