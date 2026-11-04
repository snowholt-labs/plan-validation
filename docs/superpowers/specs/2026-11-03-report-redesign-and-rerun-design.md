# Report redesign, opt-in publishing and the re-run suggestion

Date: 2026-11-03
Status: draft for maintainer approval

## Intent

The validation report is the maintainer's main working surface after a validation run. In practice the maintainer reads, in this order: the header, the scores and the confidence rate, the decisions that need an answer, and then the phases, tasks and launch prompts for the next session. Today all of this sits on one long page. The "Feature at a glance" block shows bullet text in cards. It does not show architecture, blocks or what the design will do.

This work has three parts, each its own delivery phase:

1. **Report redesign.** A tabbed report with a short Summary, real block and flow diagrams, a light blue professional style, and, in Claude Code, an opt-in private artifact link.
2. **"Run validation again?" suggestion.** Each report says whether another validation run is worth it, why, and how many runs are left (at most 3 runs in total).
3. **Docs-PR review rule.** Review rounds on a validated spec and plan stop fixing design gaps in the PR and send them back to validation.

## Background: why docs PRs ran long review loops

The maintainer reported docs PRs (spec and plan only) where `/code-review` ran 20–50 rounds and found gaps that validation could have fixed. On 3 Nov 2026 we sampled 12 docs PRs from the maintainer's repositories. Most are private, so this public spec gives counts only.

| # | Finding | Label |
|---|---|---|
| F1 | 10 of the 12 PRs were validated before the PR opened. The longest loop was 34 rounds. The starting assumption ("validation was skipped") is mostly wrong. | Verified |
| F2 | Review fixes changed the spec and plan after validation, and nobody re-validated. One PR reported that 11 of 13 files no longer matched their validation hashes. Another changed its plan by +64/−56 lines after the validation commit. | Verified |
| F3 | Rounds that review the latest fix create chains. Later rounds mostly found problems in text that earlier fix rounds had added. About 25 of roughly 80 sampled findings were of this kind. | Verified |
| F4 | Review did design work that belongs to validation. One unvalidated PR grew from +30 to +129/−30 lines during review. Another added two new decisions. Others deferred design gaps as review notes. | Verified |
| F5 | Low findings were often fixed anyway. That made each fix larger and gave the next round more to find. | Verified |
| F6 | The global review rule limits rounds only when Low findings alone remain. A High or Medium finding keeps the loop going with no limit. A docs-only severity rule was added on 3 Nov 2026, after most of the sampled rounds. | Verified (rule text). Its effect is an Assumption. |
| F7 | Plans written down to function and test names get reviewed like code, at high review effort. | Assumption |
| F8 | When the round cap was first added, and whether running sessions reloaded the rule change. | Unknown |

**Conclusion.** A re-run suggestion is good practice only when it has a limit and fixed triggers; without them it becomes the same loop. It does not remove the main cause on its own. The loops came from editing documents after validation. Part 2 makes the report say when to re-run. Part 3 changes the review rule so review stops fixing design gaps and sends them back to validation.

## Goals

- G1. A tabbed report: **Summary**, **Needs your answer (n)**, **Watch list (n)** and **Full report**.
- G2. The Summary fits the maintainer's reading order and stays short however long the report is.
- G3. Real diagrams made of shapes: zones, rounded boxes, arrows, numbered flow steps and side branches. They show the design's architecture and flow, not the validation process.
- G4. A neutral, professional light blue style with light and dark modes. No rose or plum.
- G5. A header with a small uppercase kicker (project · audience · evidence date), a large title with one accent-coloured word, a short summary, status pills and our own SVG icon.
- G6. Claude Code users can opt in to have each new report published as a **private** artifact. The local `report.html` is always written. Other hosts get only the local file.
- G7. Each report states "Run validation again: yes / no / stop", with the reasons, the run number and at most 3 runs.
- G8. Docs-PR review on a validated spec and plan has a hard round limit and a clear line between what review fixes and what goes back to validation.

## Non-goals

- No change to the eight evidence sections, the scoring rubric, the verdict rules or the phase-grouping rules.
- No migration of saved reports. Versions 1–3 keep rendering exactly as today.
- No automatic re-run. The maintainer starts any re-run in a fresh session.
- No change to the plugin's brand icons or the report favicon (Q1).
- No sharing, pinning or public links for published reports.

## Anti-goals (a failure even if it works)

- The Summary turns into a long list again. Counts belong on the Summary; lists belong in their own tabs.
- Diagrams that are bullet text in boxes. A diagram must show parts and how they connect, or steps and how they branch.
- A report that loads anything from the network, or a renderer that needs a non-stdlib package.
- A report that is uploaded anywhere without the user turning publishing on.
- A re-run loop with no end, or a re-run suggestion that never triggers.

## Constraints

- The renderer stays Python 3.10+ standard library only. `report.css` and `report.js` stay inlined. The CSP meta stays strict (`default-src 'none'`, a hashed script, `img-src data:`). No web fonts: use system font stacks.
- The renderer rejects bad input; it never repairs it. Raw HTML in agent text stays escaped.
- `validate-plan` stays explicit-only (`disable-model-invocation: true`, `allow_implicit_invocation: false`).
- No new runtime dependency. The diagrams are built by us (see Build vs adopt).
- The skill does not commit, push or publish anything except the opt-in private artifact described here.
- This spec and the docs are public. Use placeholders such as `<skill-directory>` and no home paths.

## Part 1: report redesign (format version 4)

### 1.1 Format version 4

- New reports (`kind: new`) use `format_version: 4`. Versions 1, 2 and 3 render saved reports only, and their output stays byte-for-byte the same as today, apart from the generation timestamp.
- Version 4 keeps everything version 3 checks: the sections, scores, confidence, phases, prompts, hashes and `decisions_without_reply`.
- Version 4 drops `feature` ("Feature at a glance"). Diagrams replace it (1.4).
- The source `report.md` contract does not change: the same eight headings and the same `### Technical details` rule.

### 1.2 Page layout

From top to bottom:

1. **Header card.**
   - **Kicker:** the context fields `project` and `audience` and the validation date, for example `PLAN-VALIDATION · PLAN REVIEW FOR THE MAINTAINER · EVIDENCE AS OF 3 NOV 2026`.
   - **Title:** `title`, with `title_accent` (a word or phrase that appears exactly once in `title`) in the accent colour.
   - **Summary:** `summary`, one to three short sentences.
   - **Status pills:**
     - the verdict;
     - `<n> phases · <m> tasks`;
     - the re-run state (Part 2);
     - "Historical", when the handoff is not current.
   - **Icon:** our own decorative SVG.

   Each pill uses colour, a shape and a word, never colour alone.
2. **Score strip.** Three tiles: PLAN average original → revised, SPEC average original → revised, and evidence confidence with "Subjective estimate, not a measured probability".
3. **Tab bar**, using the WAI-ARIA tabs pattern: Summary · Needs your answer `(n)` · Watch list `(n)` · Full report. A tab whose count is 0 is left out. Its Summary count card then says "None".
4. **Tab panels** (1.3).
5. **Footer.** As today: a local report, with no external requests.

### 1.3 Tab contents

**Summary.** This tab never lists open decisions or watch-list items. It shows:

1. **Diagrams:** 1–3 diagrams in a responsive grid (1.4).
2. **Count cards:** two clickable cards in one row.
   - "**n** need your answer" has a one-line hint, for example "D1 holds back Phase 2 · each has a recommendation".
   - "**n** gaps on the watch list" has a one-line hint, for example "1 fixed in the plan · 2 limits to know".
   - Clicking a card opens its tab.
3. **Next session:** a full-row card.
   - Phase cards: ID, tasks, title, and Ready or "Waits for <x>". Docs-only and security flags appear as small pills.
   - The first ready phase's prompt, with a copy button. When the handoff is not current, the copy button is replaced by the same historical warning as in section 8.
   - A link: "All prompts: Full report, section 8".
   - If no phase is ready, the remediation prompt instead.
4. **Run validation again:** a full-row card (Part 2).

**Needs your answer.** A compact table built from `open_decisions`: ID, question, recommendation, confidence (High/Medium/Low) and what it holds back. Each row links to section 6 in Full report, which keeps the full option menus.

**Watch list.** Cards built from `watch_list`. Each card has a kind (`gap`, `limit`, `risk` or `fixed`), shown by shape, colour and a word; a title; and one or two sentences.

**Full report.**
- All eight sections, restyled with card sections, rounded tables, section icons and pills. "Technical details" stays expandable.
- The scope table stays at the start of section 5. The section 8 phase table and the per-phase prompts with their copy buttons stay as they are.
- After the sections: "Decisions made without your reply", then document identity and provenance.

**Behaviour.**
- **In-page links:** a link to `#section-6`, `#scope` or a similar section opens the Full report tab and scrolls there. A URL hash on load does the same.
- **Arrow keys:** they move between tabs. Home and End jump to the first and last tab.
- **Without JavaScript:** if JavaScript is off or blocked, all panels are visible in order and the tab bar is hidden. The CSS keeps `[hidden]` elements hidden even when another rule sets their `display`.
- **Print:** print shows every panel in order and expands all details, as print does today.
- **Prompt sources:** each prompt has one source string. The Summary copy and the section 8 copy use different DOM IDs. `handoff.txt` and `handoff-phase-<id>.txt` are written exactly as today.

### 1.4 Diagrams

The agent describes diagrams as data in `context.json`. The renderer draws them as inline SVG. The agent never writes SVG or HTML.

```json
"diagrams": [
  {
    "kind": "zones",
    "eyebrow": "Architecture · planned",
    "title": "Who talks to whom",
    "description": "One sentence stating the whole diagram, for screen readers.",
    "caption": "One or two plain sentences shown under the diagram.",
    "zones": [
      {"label": "Your app", "nodes": [
        {"id": "caller", "title": "Caller", "sub": "asks for a request"},
        {"id": "helper", "title": "Retry helper", "sub": "waits, then tries again"}
      ], "chain": true},
      {"label": "Remote service", "nodes": [
        {"id": "api", "title": "API endpoint", "sub": "may answer 503"}
      ]}
    ],
    "links": [
      {"from": "helper", "to": "api", "label": "request", "sub": "HTTPS"},
      {"from": "api", "to": "helper", "label": "result"}
    ]
  },
  {
    "kind": "flow",
    "eyebrow": "Flow · planned",
    "title": "One request, start to finish",
    "description": "…",
    "caption": "…",
    "steps": [
      {"title": "Send the request", "sub": "first try, no wait"},
      {"title": "It fails", "sub": "timeout or 5xx answer"}
    ],
    "branches": [
      {"from_step": 2, "title": "Retry", "sub": "up to 5 tries", "tone": "retry", "returns_to": 1},
      {"from_step": 2, "title": "Give up", "sub": "report the error", "tone": "stop"}
    ]
  }
]
```

- **Kinds:**
  - **`zones`:** 1–3 zones side by side, with 1–5 nodes each, stacked as rounded pills (a title line and a muted sub line).
    - `chain: true` draws arrows between consecutive nodes in a zone.
    - `links` join nodes in neighbouring zones. Each link has a bold label above the line and a muted sub-label below it, with one colour per direction.
    - Links between zones that are not neighbours are rejected, and so are links within one zone (use `chain`).
  - **`flow`:** 2–7 numbered steps going down.
    - Up to 2 side `branches` in total. Two branches may come from the same step; they then sit side by side, and only the first may have `returns_to`.
    - `tone` is one of `retry`, `stop` or `note`, and controls the shape and colour.
    - `returns_to` draws a dashed arrow back to an earlier step.
- **Count:** 1–3 diagrams per report.
- **Fit:** every label must fit its shape, and nothing may overlap. The renderer rejects text over the length limits rather than cutting it. The spec's starting limits (node or step title 28 characters, sub-line 42, zone label 34, link label 18, link sub-label 28) did not fit 170-unit zones with 48-unit gaps, so the plan tunes them: node or step title 24, sub-line 30, zone label 28, link label 14, link sub-label 18, branch title 14, branch sub-line 18. The fit rule is about 7 units per character for 13 px text and 6 for 11 px sub-lines, plus 10 units of padding on each side. A test checks worst-case diagrams for overlap, and the renderer runs the same overlap check on each real diagram and rejects one that collides. Very wide letters (such as `W`) can still exceed the average; the manual check uses them.
- **Text:** `id`s are unique within a diagram, use only lowercase letters, digits and hyphens (at most 24 characters), and links must name existing nodes. An `id` only resolves links; it is never written into the page as a DOM `id`. All text is escaped.
- **Markers:** each SVG holds its own arrow markers, with IDs prefixed by the diagram number. A marker defined inside an SVG hidden with `display: none` does not render in Chromium (checked during validation).
- **Accessibility:** each SVG has `role="img"`, a `<title>` and a `<desc>` (from `description`), and each diagram card has a heading.
- **Colours:** only from CSS tokens, so both colour modes work.
- **Phone width:** the diagram card scrolls sideways (`min-width` on the SVG, `overflow-x: auto` on the wrapper, and `min-width: 0` on the grid item, without which a one-column grid grew to 660 px at a 360 px viewport during validation). The page itself never scrolls sideways.
- **Content rule (skill text):** diagrams describe the intended design, not the validation workflow. The eyebrow says whether a part is planned, existing or changing. Do not invent connections the spec does not describe.

### 1.5 Style

- **Tokens:** light blue, in the spirit of the reference artifact. For example: background `#f3f7fc`, surface `#fff`, ink `#12243a`, muted `#4d6178`, line `#d2dfed`, blue `#2463ad`, blue-soft `#dbe8f8`, indigo `#3e4fa6`. Mint, amber, red and slate are for status only.
- **Dark mode:** a token set under `@media (prefers-color-scheme: dark)`, guarded by `:root:not([data-theme="light"])`, and repeated under `:root[data-theme="dark"]`. `body` has an explicit background.
- **Fonts:** system stacks. A serif display stack (`Georgia`, `"Times New Roman"`, serif) for section headings, and the system sans for body text. Monospace for code and prompts.
- **Shapes:** rounded cards (14–24 px), pill chips, and small decorative section marks (circle, diamond, triangle, rounded square) as inline SVG.
- **Layout:** works at 360 px width with a 16 px side gutter.
- **Hero icon (my call):** a new decorative SVG designed for the report: a document with lines, a check badge and a small flow motif, in the blue tokens. It ships as `skills/validate-plan/assets/report-icon.svg` and is inlined as markup. It is marked `aria-hidden` and has no script or links (`check_package.py` already checks shipped SVGs). The favicon stays the unchanged brand icon (Q1).
- **Page title:** `<title>` is the context `title` alone. That keeps it short, which the artifact gallery needs too.

### 1.6 New `context.json` fields (version 4)

| Field | Rule |
|---|---|
| `project` | Nonempty, at most 40 characters. Usually the repository name. |
| `audience` | Nonempty, at most 60 characters, for example "plan review for the maintainer". |
| `title_accent` | A substring that appears exactly once in `title`. |
| `diagrams` | 1–3 items, as in 1.4. |
| `open_decisions` | A list, possibly empty. Each item has `id`, `question`, `recommendation`, `confidence` (`High`, `Medium` or `Low`) and `holds_back` (text, or `"Nothing"`). Each `id` must also appear in section 6. The list must match section 6's pending approvals: the skill text requires it, and the renderer checks the IDs. A `Ready after approvals` verdict with an empty list is rejected. |
| `watch_list` | A list, possibly empty. Each item has `kind` (`gap`, `limit`, `risk` or `fixed`), a `title` of at most 60 characters, and a `body`. |
| `feature` | Rejected in version 4. |

### 1.7 Opt-in private artifact (Claude Code only)

- **Setting.** `.claude-plugin/plugin.json` gains `userConfig.publish_artifact`. Its properties: `type: boolean`, `default: false`, a `title`, and a `description` saying it uploads each new report, with its local paths, to the user's claude.ai account as a private artifact. Claude Code asks for it when the plugin is enabled.
  - Evidence: the Claude Code plugin docs (manifest reference, "User configuration"), read 3 Nov 2026. Verified as documentation; runtime behaviour is Unknown until Phase 1 checks it.
- **Reading the setting.** `SKILL.md` reads `${user_config.publish_artifact}`. Only the exact value `true` turns publishing on. Anything else is off: a missing setting, an older Claude Code that leaves the placeholder as literal text, a standalone skill install, or Codex. The manifest reference (read 4 Nov 2026) documents substitution of non-sensitive `${user_config.KEY}` values in skill content, and says an unrecognized top-level manifest field is stripped while the plugin still loads; the setting is therefore not `sensitive`.
- **When it is off,** the skill does not publish the report, even when the host's own guidance suggests publishing finished work.
- **When it is on, after a successful local render of a `kind: new` report:**
  1. Read the whole `report.html`, as the Artifact tool requires.
  2. Copy `report.html`, `report.md`, `handoff.txt` and each `handoff-phase-<id>.txt` into a new folder in the session scratchpad. The Artifact tool accepts supporting `files` only from the working directory or the scratchpad (its tool description, 4 Nov 2026), and the run directory is in neither. The run directory stays the durable record.
  3. Run the Artifact quickstart (`intent: "other"`), then publish the scratchpad `report.html` as-is, with `root` set to that folder.
     - Publish `report.md`, `handoff.txt` and each `handoff-phase-<id>.txt` as supporting `files`, so the page's links work.
     - Use a one-sentence `description` and the icon `checklist`. Never pass `pin`.
  4. Save `artifact.json` in the run directory, holding `url`, `published_at` and the SHA-256 of the published `report.html`. A later re-render of the same run, when the user asks for one, updates that URL; in a later session it first reads the artifact, because the Artifact tool refuses an update to an artifact the session has not read. A new validation run creates a new artifact.
  5. The reply gives the artifact link first and the local `report.html` link second.
- **Private by default.** A new artifact is visible only to its owner (Claude Code artifacts docs, read 3 Nov 2026: Verified). Repository visibility does not change this; the docs describe no link between them. The skill never shares, pins or changes visibility; sharing stays the user's own manual step.
- **Failure.** If publishing fails, the skill says so in one line, gives the local link and does not retry the same call.
- **Saved reports.** A saved report (`kind: saved`) is published only when the user asks.
- **Local opening (my call).** When publishing is on and succeeds, the skill does not pass `--open`. When it is off or fails, it keeps today's `--open` behaviour.
- **Docs that change.**
  - `references/html-report.md`: replace "Do not publish it."
  - `SKILL.md`, "Authority and boundaries": allow the opt-in artifact as the only external publish.
  - `site/src/content/docs/reports-and-handoffs.md`: replace "Do not publish a report merely…".
  - `get-started.md`: document the setting.
  - `SECURITY.md`: add a privacy note if it covers data handling.
  - `README.md` ("Reports stay under…", "Local retention", "Reports are local by default") and `site/src/content/docs/safety-and-limitations.md` (data handling): name the opt-in exception, because both say reports stay local.
- **Unknown: is `${user_config.publish_artifact}` substituted inside `SKILL.md` at runtime?** Publishing is the last sub-phase of Phase 1, and its first task checks this with a test install. If substitution does not work, stop that sub-phase and ask the maintainer. Do not invent another opt-in mechanism. The renderer work does not depend on it and can merge without it.
- **Unknown: does the artifact host honour the report's CSP meta and inline hashed script?** Phase 1 includes a check: publish the demo report privately and confirm that tabs, copy buttons, dark mode, phone width and print work. If the host breaks the page, stop and bring the finding to the maintainer. Do not weaken the local CSP.

### 1.8 Build vs adopt (diagrams only)

| Option | Fit | Self-contained and stdlib | Security | Verdict |
|---|---|---|---|---|
| Our SVG templates from constrained data | Exactly the shapes we want (zones, pills, flow, branches) | Yes | All text escaped; no agent SVG | **Chosen** |
| Mermaid (JS, renders in the browser) | Generic flowcharts; little control over the look | No: a large script must be inlined or fetched, and the CSP must allow it (Assumption: well over 1 MB) | Runs third-party script in the report | Rejected |
| Graphviz / D2 (external binaries) | Good automatic layout | No: needs an installed binary, so not stdlib | Runs an external tool on agent text | Rejected |
| Agent-written raw SVG | Anything | Yes | SVG can carry script and links; safe cleaning is hard in stdlib | Rejected |

Decision confidence: **High**. The self-contained, stdlib-only and no-agent-markup constraints rule out the alternatives whatever their size. The Mermaid size is an Assumption; no lookup was made.

Publishing uses Claude Code's own Artifact tool, so it needs no build-vs-adopt comparison.

## Part 2: "Run validation again?"

### 2.1 Behaviour

Every new version 4 report states one of these:

- **yes:** another run is likely to fix something. The reasons are listed, and a copyable re-run prompt is shown.
- **no:** nothing left that validation can fix. The reasons are listed.
- **stop:** do not re-run. The maintainer decides what to do next. The reasons say what remains. This is always the answer at run 3 when another run would otherwise be suggested.

It appears as a header pill and as the full-row "Run validation again" card on the Summary, showing "Run <n> of at most 3".

### 2.2 Triggers (thresholds are my call)

The renderer computes mechanical triggers:

- confidence is `Unknown` or below 70%;
- a revised PLAN or SPEC average is below 8.0 or `Unknown`;
- the verdict is Not ready.

Rules:

- **Runs 1–2:** if any mechanical trigger fires, the recommendation must be `yes` or `stop`, never `no`.
- **Stop before run 3:** `stop` is allowed before run 3 when a re-run cannot help, for example when the blocker needs the maintainer's decision. Its reasons must say what to decide.
- **Agent reasons:** the agent may say `yes` without a mechanical trigger. An example is gaps that validation could fix but did not reach. It must give the reasons.
- **Run 3:** `yes` is rejected. The answer is `stop`, or `no` when no trigger fires.
- **Pending approvals:** they are not a re-run trigger. Recording an answer stays the existing same-run re-render, or a phase-only validation after merges.

### 2.3 Run counting

- `context.json` gains `validation_run`. It holds:
  - `number` (1–3);
  - `plan_key`, the plan's path relative to the repository root, so other worktrees and checkouts match; the PLAN document's path must end with it;
  - `scope`, which is `full` or `phases:<first>-<last>` for a phase-only validation, where `<first>` and `<last>` are the first and last phase IDs in the context's `phases` (the renderer compares the whole string, because phase IDs may contain hyphens);
  - `previous_report`, an absolute path, required when `number` > 1.
- **What counts as a run (my call):**
  - A run is a new validation in a fresh session.
  - A same-run re-render, such as after recording an answer or repeating a report, never counts.
  - A phase-only validation after merges starts its own count, because its scope differs. A plan with many phases is therefore never blocked by the limit in normal use.
  - A changed spec path does not reset the count.
- The skill finds earlier runs in `~/.local/share/plan-validation/<repo-name>/` whose `context.json` has the same `plan_key` and `scope`. The new number is the highest earlier number plus one.
  - `<repo-name>` is the folder name of the repository's main worktree, so linked worktrees share it.
  - Only version 4 contexts with a `validation_run` count; the count starts at 1 with the first version 4 report.
  - The current run directory is skipped. A re-render keeps the number already recorded in its own `context.json`.
  - An earlier `context.json` that cannot be read is named in section 7, not guessed.
- A new number above 3 is not allowed. The skill tells the maintainer the limit is reached and does not validate again unless the maintainer explicitly resets the count. A reset is recorded in `decisions_without_reply`, never assumed.
- `context.json` also gains `rerun`, with `recommendation` (`yes`, `no` or `stop`), `reasons` (1–4 short strings) and `prompt` (required only for `yes`).
- **The prompt:**
  - at most 80 words;
  - says "run <n+1> of 3";
  - names the plan, the spec and the previous report;
  - names what the run should focus on;
  - contains no "Implement" instruction;
  - says `Do not start dependent implementation.`
- **Where the prompt goes:** the prompt lives only in `context.json`, not in section 8's fences, so phase-prompt counting does not change. The renderer writes it to `rerun.txt`. A re-render deletes any old `rerun.txt` first.

### 2.4 After review changes the documents

A static report only knows the state at render time. Drift after the report is handled in two ways.

- **Hash check.** The existing hash check already marks the handoff historical when the plan or spec changes. In version 4 the historical warning also says: "The plan or spec changed after this validation. Run validation again (run <n+1> of 3) instead of more review rounds."
- **Review rule.** Part 3 changes the review rule so docs-PR review sends design gaps back to validation.

### 2.5 Renderer checks (Part 2)

- `validation_run` and `rerun` are present and well formed.
- The trigger rules in 2.2 hold.
- The run 3 rule holds.
- The prompt rules hold (word count, run label, no Implement).
- `rerun.txt` is written only for `yes`.

## Part 3: docs-PR review rule

### 3.1 Rule (applies to a docs PR of a spec and plan that has a validation report)

- **What review fixes:** small, local defects only. Examples: a wrong path or command, a contradiction between two sections or with the code, or wrong wording.
- **What goes back to validation:** a finding that would add or change requirements, design, phases, tasks or scope is a gap.
  - It is not fixed in the PR.
  - Review stops, and the maintainer re-runs validation in a fresh session. This counts toward the 3-run limit.
  - Review then restarts on the new head.
- **Round limit:** at most 3 `/code-review` rounds on such a PR. If High or Medium findings remain after round 3, stop: re-validate, or ask the maintainer.
- **Low findings:** they are listed, not fixed, unless a High or Medium fix touches the same line.
- **Other PRs:** non-docs PRs keep their current round rules.

### 3.2 Where it goes

- **The maintainer's global git-workflow rule.** This file is outside the repository: it is local, not in git, and not public (checked 3 Nov 2026).
  - The edit replaces the docs-PR part of "Reviews Before Every PR": the docs-only severity paragraph and the docs-PR use of the 6-round "Timing" bullet. It does not change the rules for other PRs.
  - It needs the maintainer's explicit OK at the time of the edit. There is no PR.
  - Afterwards, run the maintainer's Codex rules rebuild script.
- **This repo's published workflow page.** Add the same guidance to `site/src/content/docs/phased-implementation.md` as a recommendation for repositories that review docs PRs. This repo's own `AGENTS.md` exempts docs PRs from code review, so the rule targets other repositories. `AGENTS.md` does not change.

## Phases

| Phase | Scope | Depends on | Docs-only | Security review |
|---|---|---|---|---|
| 1 | Version 4 renderer, CSS, JS, icon, diagrams, tabs, the new context fields, the demo moved to version 4, the opt-in artifact (`userConfig`, skill text, docs) and the artifact host check | none | no | yes: renders untrusted agent text into HTML and SVG, and adds an external publish path |
| 2 | Re-run suggestion: context fields, renderer checks, `rerun.txt`, the historical warning text, run counting in skill text, docs and evaluation cases | Phase 1 merged | no | yes: renders untrusted text and adds a new written file |
| 3 | Docs-PR review rule: the site workflow page, plus the global rule edit outside the repo | none (can run any time) | yes (repo part) | no |

The planner may split Phase 1 into consecutive sub-phases, with publishing last (see 1.7). Each phase or sub-phase PR must pass CI on its own, including `scripts/demo.py`, so a change to what the renderer accepts updates the demo in the same phase.

All phases merge into one plan branch and ship in one release. So in Phase 1, `validation_run` and `rerun` are optional, and the re-run pill and card are hidden when they are absent. Phase 2 makes them required for version 4. No version 5 is needed, because no version 4 report is released before Phase 2.

## Testing and verification

- **Renderer regressions** (AGENTS.md): one test per new rejection, each checking the observable failure, not wording:
  - an accent word missing or repeated;
  - diagram count and kind;
  - an over-long label;
  - an unknown link node;
  - a link between zones that are not neighbours;
  - a branch from a step that does not exist;
  - a decision ID missing from section 6;
  - `feature` present in version 4;
  - the re-run rules (a trigger with `no`; `yes` at run 3; a prompt over 80 words; a prompt with Implement; a missing `previous_report`).
- **Output tests:**
  - Versions 1–3 render unchanged: fixtures compared with the generation timestamp and temporary paths masked, covering one-phase, two-phase, remediation and historical version 3 pages.
  - Worst-case zones and flow diagrams have no overlapping shapes or labels, and every label fits its shape.
  - Version 4 output contains the tab roles, unique prompt IDs and an escaped diagram text probe.
  - `handoff*.txt` and `rerun.txt` are written and deleted as specified.
- **`check_package.py`:**
  - `userConfig.publish_artifact` exists with `default: false`;
  - the new SVG has no active content;
  - the new docs leak no home paths.
- **Demo:** `demo.py` renders a version 4 report and still checks `64 != 30` and the corrected pass.
- **Manual checks** (Phase 1), each in light and dark mode at 360 px and at desktop width, with JavaScript on and off:
  - tabs and keyboard use;
  - copy buttons;
  - print;
  - the private artifact check from 1.7.
- **`docs/evaluation.md`** cases:
  - Summary tab content and counts;
  - publishing off by default (no upload);
  - publishing on (private artifact, link given, local file still written);
  - a failed publish;
  - each re-run recommendation;
  - run 3 stop;
  - drift after review leads to a re-run, not more rounds.
- **CI:** CI as today, plus `cd site && npm ci && npm test && npm run build` for site changes.

## Rollout and rollback

- Ships in the next minor release. `CHANGELOG.md` names format version 4, the opt-in setting and the re-run suggestion.
- **Rollback:** revert the release. Saved version 4 reports would then fail to render on the older plugin, as any newer format does. Older reports are unaffected.
- Publishing is off unless each user turns it on.

## Calls made without the maintainer

- Tabs instead of an overlay for the count cards: they print well, need no focus trapping and match the Summary/Full report pattern. (The maintainer agreed to tabs.)
- A tab with a count of 0 is hidden, and its card says "None".
- The diagram data schema, the kinds (`zones`, `flow`), the limits and the "reject, don't truncate" rule.
- System fonts with a serif display stack.
- The design of the new hero icon.
- The re-run thresholds (below 70% confidence, a revised average below 8.0, Not ready), and `stop` allowed before run 3.
- Run counting by repository-relative plan path and scope. Re-renders never count, and phase-only validations count separately. A reset must be explicit and recorded.
- Publishing is the last sub-phase of Phase 1 and stops if the setting cannot be read at runtime.
- `validation_run` and `rerun` are optional in Phase 1 and required from Phase 2, all in one release.
- No `--open` when the artifact publish succeeds.
- Supporting files published with the artifact so its links work.

## Maintainer decisions

- **Q1 (answered 3 Nov 2026).** The brand icons and the report favicon stay as they are. Only the new hero icon is blue. Old reports stay exactly as they are.

## Left to the builder

- Exact token values, spacing and the SVG layout maths, within the limits above.
- How the tab script is structured inside `report.js`, keeping the hashed-inline CSP.
- How the renderer is split into helper functions, and how test fixtures are organised.
