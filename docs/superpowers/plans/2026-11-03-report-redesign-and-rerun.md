# Report Redesign and Re-run Suggestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship report format version 4: a tabbed, light blue report with real SVG diagrams, opt-in private artifact publishing in Claude Code, and a bounded "Run validation again" recommendation. Also add a docs-PR review rule that sends design gaps back to validation.

**Architecture:**
- The stdlib renderer `render_report.py` keeps the shared parsing and checks. It adds a version 4 page builder with its own CSS and JS assets, so the version 1–3 output stays byte-identical.
- Diagrams are drawn as SVG by a new stdlib module, `diagrams.py`, from data the agent writes in `context.json`.
- Publishing and run counting are agent behaviour, so they live in the skill text. The renderer only checks the data.

**Tech Stack:** Python 3.10+ standard library, `unittest`, inline CSS and JS, Markdown skill text, the Astro docs site (`site/`).

**Spec:** `docs/superpowers/specs/2026-11-03-report-redesign-and-rerun-design.md`

## Global Constraints

- The renderer uses the Python 3.10+ standard library only. No new runtime dependency.
- The report stays self-contained. CSS and JS are inlined. The CSP stays `default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-…'; img-src data:; base-uri 'none'; form-action 'none'`. No web fonts.
- The renderer rejects bad input and never repairs it. All agent text is escaped. The agent never supplies SVG or HTML.
- Versions 1–3 render byte-for-byte as before, apart from the `HTML generated <timestamp>.` text. New reports (`kind: new`) must use `format_version: 4`.
- The brand icons and `skills/validate-plan/assets/favicon.svg` stay unchanged. The new hero icon is `skills/validate-plan/assets/report-icon.svg`.
- `validate-plan` stays explicit-only: `disable-model-invocation: true` and `allow_implicit_invocation: false`.
- Publishing is on only when `${user_config.publish_artifact}` is exactly `true`, the host is Claude Code and the Artifact tool exists. Artifacts are never shared, pinned or made public.
- Re-run limits: at most 3 runs per `plan_key` and `scope`. The mechanical triggers are confidence `Unknown` or below 70%, a revised PLAN or SPEC average below 8.0 or `Unknown`, or the verdict Not ready.
- Public repo: no home paths and no private repository names in docs. Use `<skill-directory>`-style placeholders.
- Delivery follows `AGENTS.md`, "Plan work":
  - Use the plan branch `plan/report-redesign` and the milestone "Report redesign and re-run".
  - Before Phase 1a, create `plan/report-redesign` from the current `origin/main` and land this spec and plan in a `docs/report-redesign` PR into it. That PR is docs-only (CI only) and lands both files exactly as validated, so their hashes still match the validation report. The maintainer's merge of it is the spec's approval record.
  - Each phase gets its own branch and a PR into the plan branch, squash-merged.
  - The plan-to-`main` PR uses a merge commit.
  - Every commit for a task ends with `Plan: docs/superpowers/plans/2026-11-03-report-redesign-and-rerun.md`, `Phase: <id>` and `Task: <n>` trailers.
- Each phase PR must pass CI on its own. CI runs the unit tests, `python3 scripts/check_package.py` and `python3 scripts/demo.py` on every pull request, including PRs into the plan branch. A task that changes what the renderer accepts also updates `scripts/demo.py` in the same task.
- Test command, used throughout:
  - All tests: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py'`
  - One test: add `-k <name>`.

## Review Focus

1. **Hostile text in diagram fields.** Text such as `</text><script>`, `"` or `&` in a node title must appear as literal text in the SVG and never become markup. Test: `test_diagram_text_is_escaped` (Task 2).
2. **Phone width with a 3-zone diagram.** The page must never scroll sideways; only the diagram card may. No label may overflow its shape or overlap another shape, label or line. Tests: `test_layout_fits_and_never_overlaps` (Task 2), `test_v4_css_scrolls_diagrams_not_page` (Task 4), plus the manual 360 px check (Task 5).
3. **A link to a section on another tab.** A `#section-6` link from the Needs-your-answer table, or a pasted URL with that hash, must show the Full report tab and scroll there. Test: `test_v4_js_routes_hash_to_full_report` (Task 5), plus the manual check.
4. **Phase IDs with dots, such as `1.2`, in the Summary prompt copy button.** The button must copy the right prompt. The Summary and section 8 elements must have different IDs. Test: `test_v4_prompt_ids_are_unique_and_match_handoff` (Task 4).
5. **A saved version 3 report rendered after the upgrade.** It must look exactly as before and must not need the new fields. Test: `test_legacy_output_is_frozen` (Task 1), which covers one-phase, two-phase, remediation and historical version 3 pages.

---

## Phase 1a: Version 4 renderer (Tasks 1–5)

### Task 1: Freeze legacy output

**Files:**
- Modify: `skills/validate-plan/scripts/test_render_report.py`

**Interfaces:**
- Produces:
  - `LEGACY_DIGESTS: dict[str, str]`, for the keys `"v1"`, `"v2"`, `"v3"`, `"v3-two-phases"`, `"v3-remediation"` and `"v3-historical"`.
  - `normalized(page: str, root: str) -> str`: `re.sub(r"HTML generated \S+\.", "HTML generated X.", page.replace(root, "ROOT"))`.
  - `ReportTests.v3_saved_context()`: a version 3, `kind: "saved"` context written out literally (today's `modern_context()` values: one ready phase, the three-step `feature`, `decisions_without_reply: []`). It must not call `modern_context()`, because Task 3 turns that helper into version 4 and removes `feature`.

- [ ] **Step 1: Write the freeze test.** Add `test_legacy_output_is_frozen` as a method of `ReportTests` (not a subclass, which would run every test twice). It renders and hashes these cases:
  - `"v1"`: `REPORT` with `self.context` (no `format_version`, `kind: saved`);
  - `"v2"`: `REPORT` with `v3_saved_context()` set to `format_version: 2`, without `task_inventory` and `phases`;
  - `"v3"`: `REPORT` with `v3_saved_context()`;
  - `"v3-two-phases"`: `v3_saved_context()` with phases `1` and `2` (one task each) and a source whose section 8 holds the two prompts `two_phase()` uses today;
  - `"v3-remediation"`: the same two phases, both waiting for `D1`, a `Ready after approvals` verdict and the single prompt `Record D1, then re-render the report. Do not start dependent implementation.`;
  - `"v3-historical"`: `v3_saved_context()` with `handoff_status: "historical"`.

  Write these sources and contexts out literally in a `legacy_cases()` helper used only by this test. Do not call `two_phase()` or copy from other tests at run time: later tasks edit those fixtures, and any edit would change a frozen digest.

  It asserts that the dict of `hashlib.sha256(normalized(render(source, context)[0], self.directory.name).encode()).hexdigest()` values equals `LEGACY_DIGESTS`. Use `render(...)[0]` so the test survives Task 10's 4-tuple.
- [ ] **Step 2: Pin the digests.** Run the test on the current `main` code with placeholder digests, copy the six actual digests from the failure output into `LEGACY_DIGESTS`, and run it again. Then run it once more with a different `TMPDIR` to prove the path masking works.

  Expected: PASS both times. A one-byte change to `report.css` or to a version 3 label must make it fail. Never re-pin these digests in a later task: a mismatch means legacy output changed and must be fixed.
- [ ] **Step 3: Commit.** `test: freeze version 1–3 report output`

### Task 2: Diagram module

**Files:**
- Create: `skills/validate-plan/scripts/diagrams.py`
- Create: `skills/validate-plan/scripts/test_diagrams.py`

**Interfaces:**
- Produces:
  - `LIMITS: dict[str, int]` (tuned from the spec's starting limits so that every label fits; spec 1.4 "Fit"). Node limits also apply to flow steps:
    ```python
    {"eyebrow": 40, "title": 60, "node_title": 24, "node_sub": 30, "zone_label": 28,
     "link_label": 14, "link_sub": 18, "branch_title": 14, "branch_sub": 18}
    ```
  - `CHAR_WIDTH = {"t": 7, "s": 6}` (SVG units per character: titles and labels at 13 px, sub-lines at 11 px) and `PAD = 10` (inner padding on each side of a shape). The keys `node_sub`, `link_sub` and `branch_sub` use `"s"`; every other SVG key uses `"t"`.
  - Geometry constants:
    - Zones: `ZONE_W = 220`, `GAP = 132`, `PILL_H = 48`, `PILL_GAP = 22`, `LABEL_H = 34`. The `viewBox` width is `zones * 220 + (zones - 1) * 132 + 12` (232, 584 or 936).
    - Flow: `STEP_W = 260`, `STEP_H = 48`, `STEP_GAP = 22`, a numbered circle of radius 12 inside the step's left edge, `BRANCH_W = 130`, `BRANCH_GAP = 40` (step to first branch) and 24 between two branches. The `viewBox` width is 608.
  - `validate_diagrams(value: object) -> list[dict]`. It raises `ValueError` with messages that start with `Diagram`.
    - Text length counts a character whose `unicodedata.east_asian_width` is `W` or `F` as 2, so wide scripts cannot overflow a shape.
    - A node `id` must match `[a-z][a-z0-9-]{0,23}`. It is only used to resolve links and is never written into the page as a DOM `id`.
    - Two branches may leave the same step. They then sit side by side, and only the first may have `returns_to`.
    - After the field checks, it runs the same overlap check as `test_layout_fits_and_never_overlaps` on `layout_boxes(diagram)` for the real input and raises `Diagram <n> overlaps: …` when any text or shape collides. This catches link sets the worst cases do not cover, such as two links from one pill into the same gap. The renderer rejects; it never moves text.
  - `render_diagram(diagram: dict, index: int) -> str`. It returns one `<section class="fig" aria-labelledby="dg-<index>-h">…</section>` that holds an eyebrow, an `<h3>`, a `<div class="dg-wrap">` with the `<svg>`, and a caption. The `<svg>` has the class `dg-w<zones>` (zones) or `dg-flow`, which Task 4's CSS uses for `min-width`.
  - Arrow markers live in each diagram's own `<defs>`, with IDs prefixed `dg-<index>-` (for example `dg-1-m-fwd`). There is no shared hidden marker `<svg>`: in Chromium, a marker defined inside a `display: none` SVG does not render (checked during validation), and tab panels are hidden with `display: none`.
  - `layout_boxes(diagram: dict) -> list[tuple[str, float, float, float, float]]`: the `(kind, x, y, width, height)` of every shape, text line and line segment, for the overlap test. `render_diagram` draws from the same boxes.
  - SVG classes, which Task 4's CSS styles: `z-a z-b z-c pill pill-retry pill-stop pill-note t s zl ar ar-fwd ar-back ar-dash lb ls num`.

- [ ] **Step 1: Write the failing tests** in `test_diagrams.py`:
  - **`test_valid_zones_and_flow_render`:** the spec's 1.4 example (zones plus flow) gives 2 sections. Each section has one `role="img"`, `<title>` and `<desc>`, with `<desc>` equal to `description`.
  - **`test_diagram_count_and_kind`:**
    - `[]`, 4 items, `kind: "tree"` and a non-list each raise `Diagram`.
  - **`test_zone_and_node_limits`:**
    - 0 or 4 zones, or 0 or 6 nodes in a zone, raise an error.
    - A node title of 25 characters raises an error that names `node_title`.
    - Exactly 24 characters passes.
  - **`test_links_name_existing_neighbouring_nodes`:**
    - A link to an unknown ID raises an error.
    - A link from zone 1 to zone 3 raises an error, and so does a link between two nodes of the same zone (use `chain`).
    - Duplicate IDs in one diagram raise an error.
    - An ID such as `Caller`, `a b` or `section-6"` raises an error.
  - **`test_flow_steps_and_branches`:**
    - 1 or 8 steps raise an error, and so do 3 branches.
    - `from_step` 0 or above the step count raises an error.
    - `returns_to` must be at least 1 and less than `from_step`.
    - Two branches from one step where the second has `returns_to` raise an error.
    - `tone` must be `retry`, `stop` or `note`.
  - **`test_diagram_text_is_escaped`:** put the probe `</text><script>x</script>"'&` in every text field (eyebrow, title, description, caption, zone label, node title and sub, link label and sub, step title and sub, branch title and sub; shorten it to the field's limit where needed). The output has no `<script`, contains `&lt;/text&gt;` and `&quot;`, and no probe text appears inside an attribute other than as escaped text.
  - **`test_required_text_fields`:** a missing or blank `eyebrow`, `title`, `description` or `caption` raises an error.
  - **`test_limits_fit_shapes`:** for each limit, `limit * CHAR_WIDTH[font] + 2 * PAD` is at most the width of the shape or gap that holds it (node and step text in `ZONE_W` or `STEP_W` minus the number circle, zone label in `ZONE_W`, link text in `GAP`, branch text in `BRANCH_W`).
  - **`test_layout_fits_and_never_overlaps`:** for two worst cases, check `layout_boxes`: no two shapes intersect; no text box (`len(text) * CHAR_WIDTH`) leaves its shape or intersects another text box or a line it does not label; every box lies inside the `viewBox`. Worst case A: 3 zones of 5 nodes, every label at its limit using `W`, both directions of links between each neighbouring pair, and links that need elbows. Worst case B: 7 steps at their limits, two branches from step 4 (the first returning to step 1) — and, separately, one branch each from steps 2 and 6.
- [ ] **Step 2: Run them to see them fail.**

  Command: `… -k diagram`

  Expected: FAIL with `ModuleNotFoundError: diagrams`.
- [ ] **Step 3: Implement `validate_diagrams`, `layout_boxes` and `render_diagram`.** Escape every text value with `html.escape(value, quote=True)`, in text nodes and attributes alike.
  - **Zones layout:**
    - Zones sit side by side with the geometry constants above. Pills are `ZONE_W` wide, 48 tall and 22 apart, stacked under a 34-unit zone label.
    - A link draws a horizontal arrow at the source pill's centre line. When the target sits on another row, the arrow becomes an elbow whose vertical part runs at a fixed lane in the gap, chosen so that it does not cross another link's label.
    - Forward links (left to right) use `ar-fwd`, and backward links use `ar-back`. The label sits 8 units above the line and the sub-label 14 units below.
  - **Flow layout:**
    - Steps use the flow constants above, with 22-unit arrows between them.
    - Branch boxes sit to the right at their `from_step` row. A second branch from the same step sits 24 units to the right of the first.
    - `returns_to` draws a dashed `ar-dash` path from the branch box back to that step's right edge, in a lane that crosses no other box.
  - **Markers:** each SVG's `<defs>` holds its markers, referenced as `url(#dg-<index>-m-fwd)`.
  - **Phone width:** set the SVG `min-width` in CSS by class (`dg-w1`, `dg-w2`, `dg-w3`, `dg-flow`), not inline.
  - If the worst cases in `test_layout_fits_and_never_overlaps` cannot fit, lower a limit in `LIMITS` rather than shrinking text. The spec lets the builder tune the limits.
- [ ] **Step 4: Run the tests.** Expected: PASS.
- [ ] **Step 5: Commit.** `feat: draw zone and flow diagrams from report data`

### Task 3: Version 4 context checks and version dispatch

**Files:**
- Modify: `skills/validate-plan/scripts/render_report.py` (`render`, `handoff_prompts`, `phase_handoffs`, and a new `v4_fields`)
- Modify: `skills/validate-plan/scripts/test_render_report.py`
- Modify: `scripts/demo.py` (the smallest valid version 4 context, so CI stays green)

**Interfaces:**
- Consumes: `diagrams.validate_diagrams`.
- Produces:
  - `v4_fields(context: dict, open_items: str) -> dict`. It returns `{"diagrams": list, "decisions": list, "watch": list}`, already checked.
  - `render` accepts `format_version` 1–4.
  - `kind: new` requires version 4. Version 3 is allowed only with `kind: saved`.
  - `handoff_prompts`, `phase_handoffs` and `render` treat `version >= 3` as today's version 3. Every current `version == 3` test in `render_report.py` becomes `version >= 3`: the ready-phase list, the inner-fence check and the remediation rule in `handoff_prompts`, the `phase_plan` call in `render`, and the section 8 `phase_table`. `phase_handoffs` returns pairs for versions 3 and 4. The `version < 3` prompt label stays as it is.
  - `feature_overview` runs only for versions 2 and 3 (`version in (2, 3)`).
  - `render_report.py` imports `diagrams` at module level. The CLI and the tests already have the scripts directory on `sys.path`; `scripts/demo.py` does not, so it inserts it before loading the renderer.

- [ ] **Step 1: Update the test helpers.**
  - `modern_context()` now returns version 4. It adds `project: "plan-validation"`, `audience: "plan review for the maintainer"`, `title_accent: "Example"` and one valid `zones` diagram. It sets `open_decisions: []` and `watch_list: []`, and removes `feature`.
  - Reuse Task 1's `v3_saved_context()`; do not change it, because `test_legacy_output_is_frozen` depends on it.
  - Move the existing Feature-at-a-glance tests to `v3_saved_context()`.
  - Replace `test_new_reports_require_version_three`, which renders `kind: new` with version 3 and a saved version 2 report without `feature`, with `test_new_reports_require_version_4` below. Keep `test_new_report_cannot_fall_back_to_legacy_format`; its errors still apply.
  - The new `Ready after approvals` rule affects four existing tests that use `two_phase()` with that verdict: `test_first_phase_waiting_needs_a_non_implementation_prompt`, `test_phase_titles_cannot_inject_markup`, `test_first_phase_waiting_offers_a_remediation_copy_button` and `test_prompt_count_must_match_ready_phases`. In each test's own source and context (not in `two_phase()`), add `open_decisions` with one `D1` item and make section 6 name `D1`.
- [ ] **Step 2: Write the failing tests:**
  - **`test_new_reports_require_version_4`:** `kind: new` with version 3 raises `format_version 4`, and version 5 raises an error. A saved version 3 context still renders.
  - **`test_v4_rejects_feature`:** a `feature` key raises an error.
  - **`test_v4_header_fields`:**
    - A blank `project`, or one over 40 characters, raises an error.
    - A blank `audience`, or one over 60 characters, raises an error.
    - `title_accent` missing from `title`, or appearing twice, raises an error.
  - **`test_v4_open_decisions`:**
    - Missing fields raise an error.
    - `confidence: "Very high"` raises an error.
    - An ID such as `D9` that does not appear in section 6 raises an error. So does `D1` when section 6 contains only `D10`.
    - An ID that does not match `[A-Za-z0-9][A-Za-z0-9.-]{0,15}` (for example `D(1`) raises an error.
    - `{"id": "D1", …}` passes when section 6 contains `D1`.
  - **`test_v4_watch_list`:** `kind: "bug"` raises an error, and a title over 60 characters raises an error.
  - **`test_v4_pending_approvals_need_decisions`:** a `Ready after approvals` verdict with an empty `open_decisions` raises an error, so the Summary never says "None" while approvals are pending.
  - **`test_v4_text_fields_cannot_inject_markup`:** the probe `<script>x</script>"&amp` in `project`, `audience`, `title`, `open_decisions` and `watch_list` text renders as escaped text. With `title: "Fish & chips"` and `title_accent: "amp"`, the page keeps `&amp;` intact: split `title` around the accent first, then escape each part.
  - **`test_v4_phase_prompts_still_checked`:** a version 4 report with two ready phases and a missing `Confirm Phase 1 is merged` raises the same error as version 3.
- [ ] **Step 3: Run them to see them fail.** Expected: FAIL.
- [ ] **Step 4: Implement `v4_fields` and the version switch.**
  - `render` calls `v4_fields` after `handoff_prompts`, so existing prompt errors keep their messages and order.
  - Decision IDs are matched in section 6's plain text with `rf"(?<![A-Za-z0-9.-]){re.escape(id)}(?![A-Za-z0-9-]|\.[A-Za-z0-9])"`, the same boundary rule `handoff_prompts` uses for phase IDs.
  - `watch_list` kinds are `gap`, `limit`, `risk` and `fixed`. Decision `confidence` is `High`, `Medium` or `Low`.
  - Until Task 4, version 4 uses the version 3 page without the feature overview.
- [ ] **Step 5: Update the demo.** In `scripts/demo.py`, insert `ROOT / "skills/validate-plan/scripts"` into `sys.path` before loading the renderer, set `format_version: 4`, add `project`, `audience` and `title_accent`, replace `feature` with one valid `zones` diagram, and add `open_decisions: []` and `watch_list: []`. Task 6 replaces these with the final demo content. Without this step the demo, and so CI, fails from this task on: validation reproduced `ModuleNotFoundError: No module named 'diagrams'`, then `New reports require format_version 3`.
- [ ] **Step 6: Run all tests and the demo.** Expected: PASS, including `test_legacy_output_is_frozen`; `python3 scripts/demo.py --output "$(mktemp -d)/demo"` exits 0.
- [ ] **Step 7: Commit.** `feat: accept format version 4 report data`

### Task 4: Version 4 page, style and hero icon

**Files:**
- Modify: `skills/validate-plan/scripts/render_report.py` (new `page_v4(...)`, called from `render` for version 4)
- Create: `skills/validate-plan/assets/report-v4.css`
- Create: `skills/validate-plan/assets/report-icon.svg`
- Create: `skills/validate-plan/assets/report-v4.js` as a stub holding only `"use strict";`, so the CSP hash test has a script to hash. Task 5 fills it.
- Modify: `skills/validate-plan/scripts/test_render_report.py`

**Interfaces:**
- Consumes:
  - `v4_fields` and `diagrams.render_diagram`;
  - the existing `scores`, `phase_table`, `section_content` and `defaulted_decisions`;
  - Task 5's JS hooks, listed under Produces.
- Produces the DOM contract that Task 5's JS relies on:
  - The tab list is `<div role="tablist" class="tabs" hidden>`. JS removes `hidden`.
  - Each tab is a button `id="tab-<name>"` with `role="tab"`, `aria-controls="panel-<name>"`, `aria-selected` and `tabindex`.
  - Each panel is `<section id="panel-<name>" role="tabpanel" aria-labelledby="tab-<name>" tabindex="0">`.
  - `<name>` is `summary`, `answer`, `watch` or `full`. `answer` and `watch` are left out when their lists are empty.
  - Count cards are `<button class="count" data-open-tab="answer|watch">`.
  - Copy buttons use `data-copy-target`.
  - Summary prompts use `id="summary-handoff-<phase-id>"` (or `summary-handoff`). Section 8 keeps `handoff-<phase-id>` (or `handoff`).
  - The re-run slot is an empty `<div id="rerun-slot"></div>`, filled in Phase 2.

- [ ] **Step 1: Write the failing tests:**
  - **`test_v4_layout_order`:** these appear in order: hero, kicker (uppercase via CSS; the source text is `project · audience · Evidence as of <date>`), `<h1>` with `<em>Example</em>`, score strip, tablist, `panel-summary`, `panel-full`. `panel-full` contains the 8 section headings, and the defaults record comes after section 8.
  - **`test_v4_status_pills`:** the verdict pill and `1 phase · 1 task` are present. `Historical` appears only when the handoff is not current.
  - **`test_v4_optional_tabs`:**
    - Empty lists give no `panel-answer` or `panel-watch`, and the count cards say `None`.
    - Two decisions give `Needs your answer` with `2` in a badge and a table with one row per decision. Each row links to `#section-6`.
    - Each watch-list card shows its kind as a word (`Gap`, `Limit`, `Risk` or `Fixed`), not only as a colour.
  - **`test_v4_prompt_ids_are_unique_and_match_handoff`:** with phase IDs `1.2` and `2`:
    - every `id=` value in the page is unique, including with two diagrams whose nodes share IDs such as `api`;
    - the text of `summary-handoff-1.2` equals the `handoff-1.2` text and the `handoff.txt` content;
    - the `data-copy-target` values all name existing IDs.
  - **`test_v4_historical_summary_has_no_copy_button`:** with `handoff_status: "historical"` (or a changed document), the Summary prompt has no copy button and shows the same historical warning as section 8, as version 3 does.
  - **`test_v4_page_contract`:**
    - `<title>` equals the context title.
    - The CSP meta is present, with a hash that matches the inlined `report-v4.js`.
    - After removing every `http://www.w3.org/2000/svg`, the page contains no `http://` or `https://`.
    - `report-icon.svg` is inlined with `aria-hidden="true"`.
  - **`test_v4_css_scrolls_diagrams_not_page`:**
    - `report-v4.css` contains `.dg-wrap{overflow-x:auto`.
    - It contains `.fig{min-width:0` (or the diagram grid uses `minmax(0,1fr)`). Validation measured a 360 px page with a one-column `1fr` grid: without it the page scrolled to 660 px; with it, 360 px.
    - It contains `[hidden]{display:none!important}`. Validation confirmed that a `display:flex` rule on `.tabs` otherwise overrides the `hidden` attribute, so the no-JS tab bar would show.
    - It sets a `min-width` for `.dg-w1`, `.dg-w2`, `.dg-w3` and `.dg-flow` equal to their `viewBox` widths, and a 3-zone diagram card spans the full grid row.
    - `pre` blocks wrap (`white-space:pre-wrap` with `overflow-wrap:anywhere`), and `code` and the identity block's `small` use `overflow-wrap:anywhere`, so long paths and 64-character SHA256 values cannot widen the page.
    - It contains `prefers-color-scheme: dark`, `:root[data-theme="dark"]` and `:root:not([data-theme="light"])`.
    - `body` has a `background` declaration.
  - **Existing tests:** after this task, `modern_context()` renders the version 4 page. A test that checks version 3 page markup (the old hero, nav or feature overview) moves to `v3_saved_context()`. A test of shared checks (scores, prompts, phases, section 8 copy buttons, favicon, CSP) stays on `modern_context()`. Update these exact assertions for the version 4 Summary instead of bending `page_v4` to them:
    - `test_every_copy_button_targets_an_existing_prompt`: the expected targets become `["summary-handoff-1", "handoff-1", "handoff-2"]` (in page order).
    - `test_historical_phase_report_offers_no_copy_button`: the historical-warning count becomes 3 (Summary plus two section 8 prompts).
    - `test_modern_historical_handoff_is_called_historical`: check the header's `Historical` pill instead of `class="freshness"`.
- [ ] **Step 2: Run them to see them fail.** Expected: FAIL.
- [ ] **Step 3: Implement `page_v4`.**

  Signature: `page_v4(context: dict, fields: dict, parts: list, verdict: str, confidence: str, plan: list, spec: list, prompts: list, pairs: list, current: bool, checks: list) -> str`

  - **Content:** follow spec 1.2–1.3 for content and order. Summary shows the first ready phase's prompt, or the single remediation prompt. When the handoff is not current, it shows the historical warning instead of a copy button, exactly as section 8 does.
  - **Shared parts:** keep the favicon link, the CSP meta, the section 8 markup and the document identity block from the version 3 page, and the header actions: "Source Markdown" (`report.md`), "Prompt .txt" (`handoff.txt`, only when current) and the `#print-report` button.
  - **Kicker:** `project · audience · Evidence as of <validation_date>` with the ISO date as given; CSS makes it uppercase.
  - **Tokens:** copy the token values from spec 1.5. Use system font stacks, with `Georgia,"Times New Roman",serif` for `h2` and `h3`.
  - **Hero icon:** draw `report-icon.svg` with `<rect>`, `<path>` and `<circle>` only, using blue tokens as literal hex, with no `href`, `url(` or script. The current `check_package.py` SVG rule checks it.
  - **Assets:** keep `report.css` and `report.js` untouched.
- [ ] **Step 4: Run all tests.** Expected: PASS, with the frozen digests unchanged.
- [ ] **Step 5: Commit.** `feat: render version 4 report with summary tabs and diagrams`

### Task 5: Tabs, routing, print and copy script

**Files:**
- Modify: `skills/validate-plan/assets/report-v4.js` (the Task 4 stub)
- Modify: `skills/validate-plan/scripts/test_render_report.py`

**Interfaces:**
- Consumes: the DOM contract from Task 4.
- Produces:
  - **Tab behaviour:** clicking a tab or a `[data-open-tab]` card activates that tab. Left/Right move between tabs; Home/End go to the first/last tab.
  - **Hash routing:** a `#section-N`, `#scope` or `#defaulted-decisions` hash, on load or on `hashchange`, activates `full` and scrolls to the target.
  - **Print:** `beforeprint` shows all panels and opens all `<details>`; `afterprint` restores them.
  - **Copy buttons:** they behave like today's `report.js`.

- [ ] **Step 1: Write the failing tests.** These are static checks; behaviour is checked by hand in Step 4.
  - **`test_v4_js_routes_hash_to_full_report`:** `report-v4.js` contains `hashchange`, `aria-selected`, `ArrowRight`, `ArrowLeft`, `Home`, `End`, `beforeprint` and `afterprint`.
  - **`test_v4_no_js_shows_everything`:** in the rendered page, no `role="tabpanel"` element has `hidden`, and the tablist has `hidden`. JS hides panels at runtime.
- [ ] **Step 2: Implement `report-v4.js`.** Use `"use strict"` and no external calls. Use `getElementById` for IDs that may contain dots.
- [ ] **Step 3: Run all tests.** Expected: PASS.
- [ ] **Step 4: Manual check.** Render `REPORT` with a version 4 context to a scratch directory and open it in a browser. Check each item in light and dark mode, at 360 px and 1280 px, and with JS on and off:
  - tabs, keyboard, the count cards and `#section-6` links;
  - both copy buttons;
  - print preview showing every panel;
  - at 360 px, `document.documentElement.scrollWidth` is 360 with a 3-zone diagram, a long backticked path in a prompt and the SHA256 identity block, and the diagram card scrolls on its own;
  - arrowheads show on every link, including after switching tabs;
  - a diagram whose labels are at their limits and made of wide letters (`W`, `M`) stays inside its shapes, or the limit in `LIMITS` is lowered.

  Record what you checked in the PR body under Verification.
- [ ] **Step 5: Commit.** `feat: add tab, routing and print behaviour to version 4 reports`

## Phase 1b: Demo, contract and docs for version 4 (Tasks 6–7)

### Task 6: Demo on version 4

**Files:**
- Modify: `scripts/demo.py`

**Interfaces:**
- Consumes: the version 4 context fields from Task 3.

- [ ] **Step 1: Update the demo context.** Task 3 already made it a minimal version 4 context and added the scripts directory to `sys.path`; keep both.
  - Set `project: "plan-validation"`, `audience: "example report"` and `title_accent: "missing boundary"`.
  - Replace Task 3's placeholder diagram with two diagrams, every label within `LIMITS`:
    - a `flow`: try, fail, wait the next delay (capped at 30 s), and try again, with branches `Retry` (returns to step 1) and `Give up`;
    - a `zones`: a caller and a retry helper in "Your app", an API endpoint in "Remote service".
  - Add one `watch_list` `gap` item, "No delay cap", and keep `open_decisions: []`.
- [ ] **Step 2: Run the demo.**

  Command: `python3 scripts/demo.py --output "$(mktemp -d)/demo"`

  Expected: exit 0. The output still shows the `64 != 30` failure and the corrected pass, and `report.html` contains `role="tablist"`.
- [ ] **Step 3: Commit.** `chore: render the demo as a version 4 report`

### Task 7: Skill text, contract and docs for version 4

**Files:**
- Modify: `skills/validate-plan/SKILL.md` (the "Report and handoff" paragraph on format version 3)
- Modify: `skills/validate-plan/references/report-contract.md` (replace "Feature at a glance" with "Summary diagrams, decisions and watch list")
- Modify: `skills/validate-plan/references/html-report.md` (the context example becomes version 4; the field rules from spec 1.6; the version paragraph)
- Modify: `site/src/content/docs/reports-and-handoffs.md`
- Modify: `AGENTS.md` (the "Format versions" bullet, and the "Report pipeline" bullet: `diagrams.py`, `report-v4.css`, `report-v4.js` and `report-icon.svg`)
- Modify: `docs/evaluation.md`
- Modify: `CHANGELOG.md` (the Unreleased section)

- [ ] **Step 1: Update the skill text.**
  - New reports use version 4, with 1–3 diagrams that describe the intended design (spec 1.4, content rule).
  - `open_decisions` mirrors section 6's pending approvals.
  - `watch_list` holds gaps, limits, risks and fixed items.
  - The other rules stay unchanged.
- [ ] **Step 2: Update the evaluation cases.** Replace the "Feature overview and readable report" case with "Summary tab". Its observable outcome:
  - 1–3 design diagrams, and no validation-workflow diagram;
  - decision and watch-list counts that open their tabs;
  - a full-row next-session card;
  - full evidence in Full report.
- [ ] **Step 3: Run the checks.**
  - `python3 scripts/check_package.py`: exit 0.
  - `cd site && npm ci && npm test && npm run build`: exit 0.
- [ ] **Step 4: Commit.** `docs: describe format version 4 reports`

## Phase 1c: Opt-in private artifact (Tasks 8–9)

### Task 8: Plugin setting and runtime gate

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `scripts/check_package.py`
- Modify: `skills/validate-plan/SKILL.md` (one line that reads the setting)

**Interfaces:**
- Produces:
  - `plugin.json` `userConfig.publish_artifact`:
    ```json
    {"type": "boolean", "default": false, "title": "Publish validation reports as private artifacts",
     "description": "Uploads each new report, including local file paths, to your claude.ai account as a private artifact. Off by default."}
    ```
  - A `SKILL.md` line: `Publish setting: ${user_config.publish_artifact}`. Only the exact value `true` turns publishing on.

- [ ] **Step 1: Write the failing check.** `check_package.py` reports an error unless `userConfig.publish_artifact` has `type: "boolean"`, `default: false`, a nonempty `title` and `description` (both required by Claude Code), and no `sensitive: true` (a sensitive value is not substituted into skill content).

  Command: `python3 scripts/check_package.py`

  Expected: FAIL, naming `publish_artifact`.
- [ ] **Step 2: Add the setting to `plugin.json` and the line to `SKILL.md`.** Run the check again. Expected: PASS.
- [ ] **Step 3: Validate the plugin.** Run `claude plugin validate .` and `claude plugin validate .claude-plugin/plugin.json`. Expected: both pass. If `userConfig` is rejected, stop and ask the maintainer.
- [ ] **Step 4: Runtime gate (maintainer step).** Installing or reconfiguring a plugin changes the maintainer's own Claude Code settings, so the implementing agent prints these steps and waits for her results; it does not install the plugin itself.
  1. Load the branch as a local plugin in Claude Code.
  2. Leave the option unset, start a session and invoke `/plan-validation:validate-plan` with a missing path, so it stops early. Ask the agent to quote its `Publish setting:` line.
  3. Repeat with the option on, then with it off.

  Expected: `false` (or anything other than `true`) when unset or off, and exactly `true` when on. The Claude Code manifest reference (read 4 Nov 2026) documents `${user_config.KEY}` substitution in skill content for non-sensitive values, so the option must not be `sensitive`. If the on case shows the raw `${user_config.publish_artifact}` or another value, stop Phase 1c and report it to the maintainer (spec 1.7). Do not invent another mechanism. Phases 2 and 3 cannot start until 1c merges, so the report's decision D1 records the recommended way out: abandon the 1c branch (closing its PR if one is open), then validate Phases 2–3 as a phase-only validation that follows Phase 1b. A literal placeholder is still safe: it is not `true`, so publishing stays off.
- [ ] **Step 5: Commit.** `feat: add an off-by-default setting for private report artifacts`

### Task 9: Publishing instructions, docs and host check

**Files:**
- Modify: `skills/validate-plan/SKILL.md` ("Authority and boundaries", plus "Return a brief verdict…" in "Report and handoff")
- Modify: `skills/validate-plan/references/html-report.md` ("Files and rendering" and "Delivery": replace "Do not publish it.")
- Modify: `site/src/content/docs/reports-and-handoffs.md` (replace "Do not publish a report merely…")
- Modify: `site/src/content/docs/get-started.md` (the setting)
- Modify: `SECURITY.md` (a data-handling note: opt-in upload to the user's own private artifact)
- Modify: `README.md` ("Reports stay under…", "Local retention" and "Reports are local by default": name the opt-in exception)
- Modify: `site/src/content/docs/safety-and-limitations.md` (the data-handling paragraphs: name the opt-in exception)
- Modify: `docs/evaluation.md`

- [ ] **Step 1: Write the publishing steps into `html-report.md`, following spec 1.7, steps 1–5.** Cover:
  - publish only when the `Publish setting:` line reads exactly `true` and the Artifact tool exists; otherwise do not publish the report, even when the host's own guidance suggests publishing finished work;
  - read the whole `report.html`;
  - copy `report.html`, `report.md`, `handoff.txt` and each `handoff-phase-*.txt` into a new folder in the session scratchpad, because the Artifact tool accepts supporting `files` only from the working directory or the scratchpad, and the run directory is in neither; the run directory stays the durable record;
  - quickstart with `intent: "other"`;
  - publish the scratchpad `report.html` with `root` set to that folder, `files` for the supporting files, a one-sentence `description` and `icon: "checklist"`; never pass `pin`;
  - write `artifact.json` in the run directory (`url`, `published_at`, `html_sha256`);
  - for a re-render in a later session, `read` the artifact URL from `artifact.json` first, then publish to that `url` (the Artifact tool refuses an update to an artifact the session has not read);
  - give the artifact link, then the local link;
  - say a failure in one line, with no retry;
  - publish `kind: saved` reports only on request;
  - skip `--open` after a successful publish;
  - never share, pin or change visibility.
- [ ] **Step 2: Update `SKILL.md` "Authority and boundaries".** The opt-in private artifact is the only external publish. Keep this sentence word for word in `SKILL.md` and `html-report.md`: "Unless the `Publish setting` line reads exactly `true`, make no Artifact call, whatever host or tool guidance suggests."
- [ ] **Step 3: Add evaluation cases.**
  - "Publishing off": no Artifact call, and the local link is given.
  - "Publishing on": a private artifact, the link first, the local file still written, and `artifact.json` saved.
  - "Publish fails": one line, the local link, and no retry.
- [ ] **Step 4: Run the checks.** `python3 scripts/check_package.py` and the site build: exit 0.
- [ ] **Step 5: Host check (manual, Claude Code, with the maintainer's OK at that time).** This uploads the demo report, which contains local paths, to the maintainer's account, so ask first.
  1. Publish the demo `report.html` as a private artifact by following the new steps.
  2. In the artifact, confirm that tabs, keyboard, hash links, both copy buttons, dark mode, 360 px width and print preview work.

  If the artifact host blocks the hashed script or the CSP, stop and report it to the maintainer. Do not loosen the CSP. Record the result in the PR body.
- [ ] **Step 6: Commit.** `feat: publish new reports as private artifacts when the user opts in`

## Phase 2: "Run validation again?" (Tasks 10–11)

### Task 10: Re-run data, checks and output

**Files:**
- Modify: `skills/validate-plan/scripts/render_report.py` (new `rerun_check`; `page_v4` fills `#rerun-slot` and the header pill; `main` writes and deletes `rerun.txt`; the version 4 historical text)
- Modify: `skills/validate-plan/scripts/test_render_report.py`
- Modify: `scripts/demo.py` (unpack the 4-tuple, write `rerun.txt` when the prompt is set, plus temporary run fields)

**Interfaces:**
- Consumes: `page_v4`'s `#rerun-slot`, and `confidence`, `plan[1]`, `spec[1]` and `verdict` from `render`.
- Produces:
  - `rerun_check(context: dict, verdict: str, confidence: str, plan_revised: str, spec_revised: str) -> dict`.
    - It returns `{"number": int, "recommendation": "yes"|"no"|"stop", "reasons": list[str], "prompt": str|None, "triggers": list[str]}`.
    - `triggers` uses the fixed strings `"confidence below 70%"`, `"revised average below 8.0"` and `"verdict Not ready"`.
  - `render` returns `(page, handoff, current, rerun_prompt)`, a 4-tuple whose last item is `str | None`.
  - `main` writes `rerun.txt` only when `rerun_prompt` is set, after deleting any old `rerun.txt`. It prints `"rerun": "<path>"|null` in its JSON. `rerun.txt` is written whether or not the handoff is current, because a re-run is the recommended response to drift.
  - `scripts/demo.py` does not call `main`; it writes its files itself, so it also writes `rerun.txt` when `rerun_prompt` is set.
  - The callers to update are the 34 tuple-unpacking `render(...)` calls in `test_render_report.py` (the `render(...)[0]` calls and Task 1's freeze test need no change), `main` and `scripts/demo.py`. After this task, `grep -nE '= render\(|renderer\.render\(' -r scripts skills` shows only 4-name unpacking.

- [ ] **Step 1: Write the failing tests:**
  - **`test_v4_requires_run_fields`:** a missing `validation_run` or `rerun` raises an error.
  - **`test_run_fields`:**
    - `number` 0 or 4 raises an error.
    - `number` 2 without `previous_report` raises an error.
    - `scope` must be `full` or exactly `phases:<first>-<last>`, where `<first>` and `<last>` are the first and last `id` in the context's `phases`. Phase IDs may contain hyphens, so the scope is compared with that string, not split.
    - `plan_key` must not be blank, must not start with `/` and must not contain a `..` segment.
    - `previous_report`, when present, must be an absolute path.
    - The PLAN document's `path` must end with `/` + `plan_key`.
  - **`test_triggers_forbid_no`:** each of these, with `recommendation: "no"` at run 1, raises `Run validation again`:
    - confidence `65%`;
    - confidence `Unknown`;
    - a revised PLAN average of `7.8`;
    - a Not ready verdict.
  - **`test_run_three_never_yes`:** `yes` at run 3 raises an error. `stop` with reasons passes. `no` without triggers passes. `no` with a trigger at run 3 raises an error.
  - **`test_no_trigger_allows_every_answer_before_run_3`:** with no trigger at run 1, `no`, `stop` and `yes` (with a valid prompt) all pass, and a `Ready after approvals` verdict alone is not a trigger.
  - **`test_rerun_prompt_rules`:**
    - `yes` without a prompt raises an error.
    - A prompt over 80 words raises an error.
    - A prompt without `run 2 of 3` (for run 1) raises an error.
    - A prompt with `Implement Phase 1` raises an error.
    - A prompt without `Do not start dependent implementation.` raises an error.
  - **`test_rerun_reasons`:** 0 or 5 reasons raise an error, and so does a blank reason.
  - **`test_rerun_rendered`:**
    - The pill reads `Run validation again: yes`.
    - The Summary card shows `Run 1 of at most 3`, the reasons and a copy button whose target text equals the returned `rerun_prompt`.
    - For `no` and `stop` there is no copy button.
  - **`test_rerun_file_lifecycle`:** run `main()` through `subprocess`. A `yes` render writes `rerun.txt`. A following `no` render of the same directory deletes it.
  - **`test_v4_historical_says_rerun`:** a fingerprint mismatch shows `Run validation again (run 2 of 3) instead of more review rounds`.
  - Update every caller of `render` to unpack the 4-tuple (see Interfaces). Add valid `validation_run` (`{"number": 1, "plan_key": "PLAN.md", "scope": "full"}`, matching the test document path) and `rerun` (`no`, one reason) to `modern_context()`, so the existing version 4 tests keep passing. Tests with a Not ready verdict set `rerun` to `stop` with one reason. `render` calls `rerun_check` after `handoff_prompts`, so the existing remediation-prompt errors keep their messages. The demo also needs temporary `validation_run` and `rerun` values so it keeps passing until Task 11.
- [ ] **Step 2: Run them to see them fail.** Expected: FAIL.
- [ ] **Step 3: Implement `rerun_check`.**
  - It follows spec 2.2–2.3 exactly.
  - `Unknown` averages count as below 8.0.
  - The prompt is checked with `word_count`.
  - The Implement check reuses the regex from `handoff_prompts`.
  - In the historical text at run 3, `run 4 of 3` is replaced by `the run limit is reached; decide the next step yourself`.
- [ ] **Step 4: Run all tests.** Expected: PASS, with the frozen digests unchanged.
- [ ] **Step 5: Commit.** `feat: recommend whether to run validation again, at most three runs`

### Task 11: Run counting in skill text, demo and docs

**Files:**
- Modify: `skills/validate-plan/SKILL.md` (Workflow step 1, plus "Resume or repeat")
- Modify: `skills/validate-plan/references/report-contract.md` (a new "Run validation again" subsection)
- Modify: `skills/validate-plan/references/html-report.md` (the `validation_run` and `rerun` fields; `rerun.txt`)
- Modify: `scripts/demo.py` (`validation_run` `{number: 1, plan_key: "plan.md", scope: "full"}`, because the demo's PLAN copy is `<output>/plan.md`, plus `rerun` `yes`, with the trigger "verdict Not ready" and a valid prompt)
- Modify: `site/src/content/docs/reports-and-handoffs.md`
- Modify: `docs/evaluation.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Write the skill text, following spec 2.3.**
  - **How to find earlier runs:** look in `~/.local/share/plan-validation/<repo-name>/*/context.json` for the same `plan_key` and `scope`. The new number is the highest earlier number plus one.
    - `<repo-name>` is the folder name of the repository's main worktree (the parent of `git rev-parse --path-format=absolute --git-common-dir`), so a linked worktree or a `.worktrees/…` checkout uses the same folder. Define this in `html-report.md` "Files and rendering" too, where the run directory is created.
    - Only contexts with `format_version` 4 and a `validation_run` count. Version 1–3 reports have no run number, so the count starts at 1 with the first version 4 report.
    - Skip the current run directory. If an earlier `context.json` cannot be read or parsed, do not guess its number: name it in section 7 and count the rest.
  - **What counts as a run:**
    - Re-renders never count. A re-render keeps the `validation_run` already recorded in that run directory's `context.json` and does not search again.
    - Phase-only validations count separately. They keep the earlier report's phase IDs (an existing handoff rule), so the `scope` string stays the same across their runs.
    - When the new number would pass 3, stop before validating and tell the maintainer.
    - A reset needs the maintainer's explicit words, and is recorded in `decisions_without_reply`.
  - **Pending approvals:** they are never a re-run trigger.
- [ ] **Step 2: Add evaluation cases.**
  - "Re-run yes", with its trigger and prompt.
  - "Re-run no", with its reason.
  - "Run 3 stop".
  - "Re-render does not count".
  - "Phase-only run counts separately".
  - "Drift after review": the historical warning names the re-run.
- [ ] **Step 3: Run the checks.**
  - The demo command: exit 0, and `rerun.txt` exists in its output directory (written by `demo.py` itself, Task 10).
  - `python3 scripts/check_package.py`: exit 0.
  - The site build: exit 0.
  - All unit tests: PASS.
- [ ] **Step 4: Commit.** `docs: count validation runs and document the re-run suggestion`

## Phase 3: Docs-PR review rule (Tasks 12–13)

### Task 12: Published workflow guidance

**Files:**
- Modify: `site/src/content/docs/phased-implementation.md` (a new section "Reviewing a validated spec and plan")

- [ ] **Step 1: Add the rule from spec 3.1 as a recommendation for repositories that review docs PRs.**
  - Review fixes only local defects: a wrong path or command, a contradiction, or wording.
  - A finding that adds or changes requirements, design, phases, tasks or scope stops the review, and validation runs again in a fresh session. It counts toward the 3-run limit.
  - Review allows at most 3 rounds. High or Medium findings left after round 3 mean re-validate or ask the maintainer.
  - Low findings are listed, not fixed.

  Say that this repository's own `AGENTS.md` exempts docs PRs from code review.
- [ ] **Step 2: Build the site.** `cd site && npm ci && npm test && npm run build`: exit 0.
- [ ] **Step 3: Commit.** `docs: recommend a review rule for validated specs and plans`

### Task 13: Maintainer's global rule (outside the repository)

**Files:**
- Modify, outside the repo and only with the maintainer's explicit OK at that time: the maintainer's global git-workflow rule file, section "Reviews Before Every PR".

- [ ] **Step 1: Show the maintainer the exact before and after text, and wait for an explicit yes.**
  - **Replace:** the docs-only severity bullet, and the docs-PR use of the 6-round "Timing" bullet.
  - **With:** the spec 3.1 rule for a docs PR of a spec and plan that has a validation report.
  - **Keep:** the round rules for all other PRs.
- [ ] **Step 2: Apply the edit and rebuild.** Run the maintainer's Codex rules rebuild script, named in their global instructions. Expected: exit 0.
- [ ] **Step 3: No commit and no PR.** The file is not in a repository. Report the change in the phase summary.
