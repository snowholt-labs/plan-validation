# Phased Implementation Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The validator groups a validated plan's existing tasks into small phases, and the report gives one launch prompt per phase that stops at the phase end.

**Architecture:** A new report format version 3 adds a task inventory and a phase list to `context.json`. The renderer validates the grouping, requires one prompt per startable phase in section 8, shows a phase table with one copy button per prompt, and writes one text file per phase prompt. The skill text tells the validator how to group tasks and word each prompt; a new documentation page publishes the recommended per-phase workflow for repositories.

**Tech Stack:** Python 3.10+ standard library (`render_report.py`, `unittest`), vanilla JavaScript (`report.js`), Markdown skill files, Astro Starlight site (`site/`).

**Spec:** `docs/superpowers/specs/2026-10-20-phased-handoff-design.md`

## Global Constraints

- Python standard library only; no new dependencies (Python, npm or otherwise).
- Claude Code and Codex share the same skill text.
- `validate-plan` stays explicit-only: `disable-model-invocation: true` in `SKILL.md`, `allow_implicit_invocation: false` in `agents/openai.yaml`. Do not touch either.
- Each launch prompt targets 50–80 words with an 80-word maximum; a backtick-quoted absolute path counts as one word.
- New reports (`kind: new`) use `format_version: 3`. Versions 1 and 2 render saved reports unchanged. Existing reports are not migrated.
- The renderer does not enforce phase size; the 3–5-task target is guidance in skill text only.
- A Not ready report keeps exactly one remediation prompt containing `Do not start dependent implementation.` and no `Implement` instruction.
- No prompt grants commit, PR, comment, merge, dependency or service permissions.
- The plan file is not edited to add phase grouping; the grouping lives only in the report and `context.json`.

## Review Focus

1. Task IDs that are not plain numbers (`5b`, `A1`) must match exactly as strings, so a plan with Task 5b groups correctly. (Task 1)
2. A phase ID that could escape the run directory (`../x`, `a/b`) must be rejected before it becomes a file name. (Task 1)
3. Phase `1`'s prompt saying "Stop at the end of Phase 12" must not pass as stopping at Phase 1. (Task 2)
4. A historical report must offer no copy button for any phase, and every phase prompt file must carry the historical warning. (Tasks 2 and 3)
5. A phase prompt containing its own inner code fence must still count as one prompt. (Task 2)

## Delivery

Follow `AGENTS.md` plan work. First, the spec and this plan go in through a PR from `docs/phased-handoff-spec` into `main`, reviewed and merged under the current `AGENTS.md` "Other changes" rule (the "docs-only PRs: CI only" rule is a follow-up and does not apply yet). After it merges, create `plan/phased-handoff` from `main` and a milestone named "Phased handoff". Phase 1 is Tasks 1–3 (renderer); Phase 2 is Tasks 4–5 (skill text and site). Each phase is one PR into the plan branch, squash merged after CI and review; then one plan-to-`main` PR with a merge commit.

---

### Task 1: Format version 3 and phase validation

**Files:**
- Modify: `skills/validate-plan/scripts/render_report.py` (`render()` version checks near lines 321–330; new helper)
- Modify: `skills/validate-plan/scripts/test_render_report.py` (`REPORT` fixture, `modern_context()`, new tests)
- Modify: `scripts/demo.py` (context near lines 109–133)

**Interfaces:**
- Produces: `PHASE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]{0,15}\Z")`
- Produces: `phase_plan(context: dict, verdict: str) -> list[dict]` — returns `context["phases"]` after validation; raises `ValueError` whose message contains `Phase`.
- Produces context shape (version 3 only):

```json
"task_inventory": ["1", "2", "3"],
"phases": [
  {"id": "1", "title": "Renderer", "tasks": ["1", "2"], "docs_only": false,
   "security_review": true, "security_reason": "Renders untrusted text into HTML.", "status": "ready"},
  {"id": "2", "title": "Docs", "tasks": ["3"], "docs_only": true,
   "security_review": false, "status": "waiting", "waits_for": "D1 approval"}
]
```

- [ ] **Step 1: Update the shared fixtures**

In `test_render_report.py`, append this line inside the `REPORT` handoff fence, after the "Squash into the plan branch..." line: `Stop at the end of Phase 1; it is the last phase.` Change `modern_context()` to set `"format_version": 3`, `"task_inventory": ["1"]` and `"phases": [{"id": "1", "title": "Example", "tasks": ["1"], "docs_only": False, "security_review": False, "status": "ready"}]`.

- [ ] **Step 2: Write the failing tests**

```python
def test_phases_must_cover_the_task_inventory_once_in_order(self):
    for inventory, tasks in ((["1", "2", "3"], [["1"], ["3"]]), (["1", "2", "3"], [["1", "2"], ["2", "3"]]),
                             (["1", "2", "3"], [["2", "1"], ["3"]]), (["1", "2"], [["1", "2"], []])):
        with self.subTest(tasks=tasks):
            context = self.modern_context()
            context["task_inventory"] = inventory
            context["phases"] = [dict(context["phases"][0], id=str(i + 1), tasks=t) for i, t in enumerate(tasks)]
            with self.assertRaisesRegex(ValueError, "Phase"):
                phase_plan(context, "Ready")

def test_letter_task_ids_match_exactly(self):
    context = self.modern_context()
    context["task_inventory"] = ["5", "5b", "6"]
    context["phases"][0]["tasks"] = ["5", "5b", "6"]
    self.assertEqual(phase_plan(context, "Ready")[0]["tasks"], ["5", "5b", "6"])

def test_phase_ids_cannot_become_paths(self):
    for bad in ("../x", "a/b", "", ".hidden", "x" * 17):
        with self.subTest(bad=bad):
            context = self.modern_context()
            context["phases"][0]["id"] = bad
            with self.assertRaisesRegex(ValueError, "Phase"):
                phase_plan(context, "Ready")
    context = self.modern_context()
    context["task_inventory"] = ["1", "2"]
    context["phases"] = [dict(context["phases"][0], id="A", tasks=["1"]), dict(context["phases"][0], id="a", tasks=["2"])]
    with self.assertRaisesRegex(ValueError, "Phase"):
        phase_plan(context, "Ready")

def test_waiting_phase_holds_back_later_phases_and_blocks_ready(self):
    context = self.modern_context()
    context["task_inventory"] = ["1", "2"]
    first = dict(context["phases"][0], tasks=["1"], status="waiting", waits_for="D1")
    second = dict(context["phases"][0], id="2", tasks=["2"], status="ready")
    context["phases"] = [first, second]
    with self.assertRaisesRegex(ValueError, "Phase"):
        phase_plan(context, "Ready after approvals")
    context["phases"][1]["status"], context["phases"][1]["waits_for"] = "waiting", "D1"
    with self.assertRaisesRegex(ValueError, "Phase"):
        phase_plan(context, "Ready")
    self.assertEqual(len(phase_plan(context, "Not ready")), 2)

def test_phase_flags_must_be_consistent(self):
    for change in ({"docs_only": True, "security_review": True, "security_reason": "x"},
                   {"security_review": True}, {"status": "waiting"}, {"status": "later"}, {"docs_only": "no"}):
        with self.subTest(change=change):
            context = self.modern_context()
            context["phases"][0].update(change)
            with self.assertRaisesRegex(ValueError, "Phase"):
                phase_plan(context, "Not ready")

def test_new_reports_require_version_three(self):
    context = self.modern_context()
    context["format_version"] = 2
    with self.assertRaisesRegex(ValueError, "format_version"):
        render(REPORT, context)
    context["kind"] = "saved"
    render(REPORT, context)
```

Import `phase_plan` alongside `render`. Update `test_new_report_cannot_fall_back_to_legacy_format` and `test_unknown_report_format_is_rejected` only where their messages name version 2.

- [ ] **Step 3: Run the tests to verify they fail**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py'`
Expected: ERROR — the test module fails to import (`phase_plan` is missing), so no test runs.

- [ ] **Step 4: Implement**

In `render_report.py`: accept `format_version` 1, 2 or 3; `kind: new` requires 3 (message: "New reports require format_version 3; ..."). Change every `version == 2` branch to `version >= 2`. Add `PHASE_ID` and `phase_plan()` enforcing: `task_inventory` is a nonempty list of unique nonempty strings; `phases` is a nonempty list of objects; each `id` is a string that matches `PHASE_ID` and is unique ignoring case (phase files would collide on case-insensitive file systems); `title` nonempty; `tasks` a nonempty list of strings; the concatenated `tasks` equal `task_inventory`; `docs_only` and `security_review` are booleans and not both true; `security_review: true` needs a nonempty `security_reason`; `status` is `ready` or `waiting`; `waiting` needs a nonempty `waits_for`; once a phase waits, every later phase waits; verdict `Ready` (compared case-insensitively) allows no waiting phase. Type errors must surface as `ValueError`, because `main()` catches only `ValueError`, `KeyError`, `OSError` and `ArithmeticError`. In `render()`, call `phase_plan(context, verdict)` for version 3 after the verdict is parsed.

In `scripts/demo.py`, set `"format_version": 3`, `"task_inventory": ["1"]` and one phase: `{"id": "1", "title": "Retry delay cap", "tasks": ["1"], "docs_only": False, "security_review": False, "status": "waiting", "waits_for": "Remediation of the missing delay cap"}`.

- [ ] **Step 5: Run all checks**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py' && python3 scripts/demo.py --output "$(mktemp -d)/demo"`
Expected: all tests OK; demo exits 0.

- [ ] **Step 6: Commit**

```bash
git add skills/validate-plan/scripts/render_report.py skills/validate-plan/scripts/test_render_report.py scripts/demo.py
git commit -m "Add report format version 3 with validated phase grouping"
```

### Task 2: One prompt per startable phase

**Files:**
- Modify: `skills/validate-plan/scripts/render_report.py` (section 8 prompt extraction near lines 357–371; `main()`)
- Modify: `skills/validate-plan/scripts/test_render_report.py`

**Interfaces:**
- Consumes: `phase_plan(context, verdict)` from Task 1.
- Produces: `HISTORICAL_PREFIX: str` — the existing "HISTORICAL PROMPT — DO NOT EXECUTE..." text, moved to a constant.
- Produces: `phase_handoffs(source: str, context: dict) -> list[tuple[str, str]]` — `(phase_id, prompt)` for each ready phase of a version-3 Ready / Ready after approvals report, in order; `[]` for Not ready, for a report with no ready phase and for versions 1–2.
- Produces files from `main()`: `handoff-phase-<id>.txt` beside `report.html`, one per entry of `phase_handoffs`, prefixed with `HISTORICAL_PREFIX` when the handoff is not current. Before writing them, `main()` deletes every existing `handoff-phase-*.txt` in the output directory, so a re-render (for example after an answer turns the report Not ready) never leaves an earlier, unmarked phase prompt behind. `handoff.txt` stays: the first ready phase's prompt (or the remediation prompt). The printed JSON gains `"phase_handoffs": [<absolute paths>]`.
- `render()` keeps returning `(page, handoff, current)`.

- [ ] **Step 1: Write the failing tests**

Add a helper `two_phase(self)` returning `(source, context)`: `task_inventory` `["1", "2"]`, phases `1` (tasks `["1"]`) and `2` (tasks `["2"]`), both ready; section 8 replaced with two ```` ```text ```` blocks whose texts are `Implement Phase 1. Stop at the end of Phase 1 and print the Phase 2 prompt from the report; do not start it.` and `Implement Phase 2. Stop at the end of Phase 2; it is the last phase.`

```python
def test_each_ready_phase_gets_its_own_prompt(self):
    source, context = self.two_phase()
    _, prompt, _ = render(source, context)
    self.assertTrue(prompt.startswith("Implement Phase 1."))
    self.assertEqual([pid for pid, _ in phase_handoffs(source, context)], ["1", "2"])

def test_prompt_count_must_match_ready_phases(self):
    source, context = self.two_phase()
    source = source.replace("**Ready.**", "**Ready after approvals.**")
    context["phases"][1].update(status="waiting", waits_for="D1")
    with self.assertRaisesRegex(ValueError, "prompt"):
        render(source, context)

def test_prompt_must_stop_at_its_own_phase(self):
    source, context = self.two_phase()
    for other in ("12", "1.2", "1-b", "1b"):
        with self.subTest(other=other):
            bad = source.replace("Stop at the end of Phase 1 and", f"Stop at the end of Phase {other} and")
            with self.assertRaisesRegex(ValueError, "Phase 1"):
                render(bad, context)
    render(source.replace("Stop at the end of Phase 2;", "Stop at the end of Phase 2."), context)

def test_first_phase_waiting_needs_a_non_implementation_prompt(self):
    source, context = self.two_phase()
    for phase in context["phases"]:
        phase.update(status="waiting", waits_for="D1")
    source = source.replace("**Ready.**", "**Ready after approvals.**")
    with self.assertRaisesRegex(ValueError, "one"):
        render(source, context)
    waiting = source.split("## 8.")[0] + "## 8. Fresh-session handoff\n```text\nRecord D1, then re-render the report. Do not start dependent implementation.\n```\n"
    _, prompt, _ = render(waiting, context)
    self.assertIn("Do not start dependent implementation.", prompt)
    self.assertEqual(phase_handoffs(waiting, context), [])

def test_every_phase_prompt_has_the_word_limit(self):
    source, context = self.two_phase()
    with self.assertRaisesRegex(ValueError, "80 words"):
        render(source.replace("Implement Phase 2.", "Implement Phase 2. " + "detail " * 80), context)

def test_inner_fence_in_a_phase_prompt_counts_once(self):
    source, context = self.two_phase()
    source = source.replace("```text\nImplement Phase 2.", "````text\nImplement Phase 2.\n```\nexample\n```").replace(
        "it is the last phase.\n```", "it is the last phase.\n````")
    self.assertEqual(len(phase_handoffs(source, context)), 2)

def test_not_ready_keeps_one_remediation_prompt(self):
    source, context = self.two_phase()
    context["phases"][0].update(status="waiting", waits_for="Blocker")
    context["phases"][1].update(status="waiting", waits_for="Blocker")
    source = source.replace("**Ready.**", "**Not ready.**")
    with self.assertRaisesRegex(ValueError, "one"):
        render(source, context)
    remediation = REPORT.replace("**Ready.**", "**Not ready.**").replace(
        "Implement the approved scope now.", "Resume validation. Do not start dependent implementation.")
    self.assertEqual(phase_handoffs(remediation, context), [])

def test_main_writes_one_file_per_phase_and_marks_historical_files(self):
    # Write source and context into the temporary directory, run
    # `python3 render_report.py --report ... --context ... --output <dir>/report.html` with subprocess,
    # then assert handoff-phase-1.txt and handoff-phase-2.txt exist with the exact prompts and that the
    # printed JSON lists both under "phase_handoffs".
    # Set context["handoff_status"] = "historical", rerun into a fresh directory, and assert
    # both phase files start with HISTORICAL_PREFIX.
    # Finally re-render a valid Not ready remediation report into the first directory and assert
    # no handoff-phase-*.txt file remains there.
    ...
```

Write the last test's body as its comments describe; resolve the script path from `Path(__file__).with_name("render_report.py")` and run it with `sys.executable`. Import `HISTORICAL_PREFIX` and `phase_handoffs` alongside `render`; add `json`, `subprocess` and `sys` to the test imports.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py' -k phase -k prompt -k remediation`
Expected: FAIL / ERROR (`phase_handoffs` missing; version 3 still requires exactly one fence).

- [ ] **Step 3: Implement**

For version 3: a Not ready report, and a Ready after approvals report whose first phase waits (so no phase can start; approved as VD1), needs exactly one fenced prompt (message contains "one"), checked by the existing remediation rules: it must contain `Do not start dependent implementation.` and no `Implement` instruction. Otherwise Ready / Ready after approvals needs exactly as many fenced prompts as ready phases (message contains "prompt"); prompt *i* belongs to ready phase *i*. Every prompt is checked against the 80-word limit (message contains "80 words"). Each ready-phase prompt (not a remediation prompt) must match `rf"\bstop at the end of phase {re.escape(phase_id)}(?![A-Za-z0-9-]|\.[A-Za-z0-9])"` case-insensitively, so "Phase 1.2", "Phase 1-b" and "Phase 12" do not pass for Phase 1 while a sentence-ending period does; otherwise raise a `ValueError` naming `Phase <id>`. `handoff` (returned and written to `handoff.txt`) is the first prompt. Implement `phase_handoffs()` by reusing the same section split, verdict parse and prompt extraction as `render()`; do not duplicate the validation rules. Versions 1–2 keep the existing single-fence behavior, and their remediation rule still applies only to Not ready.

- [ ] **Step 4: Run all checks**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py' && python3 scripts/demo.py --output "$(mktemp -d)/demo"`
Expected: all tests OK; demo exits 0.

- [ ] **Step 5: Commit**

```bash
git add skills/validate-plan/scripts/render_report.py skills/validate-plan/scripts/test_render_report.py
git commit -m "Require one stopping prompt per ready phase and save each one"
```

### Task 3: Phase table and per-prompt copy buttons

**Files:**
- Modify: `skills/validate-plan/scripts/render_report.py` (section 8 HTML near lines 392–403)
- Modify: `skills/validate-plan/assets/report.js`
- Modify: `skills/validate-plan/assets/report.css` (only if the new markup needs spacing)
- Modify: `skills/validate-plan/scripts/test_render_report.py`

**Interfaces:**
- Consumes: `phase_plan()` (Task 1); the prompt-to-phase pairing (Task 2).
- Produces markup (version 3): a table in `<div class="table-scroll" role="region" aria-label="Phase plan" tabindex="0">` with columns `Phase | Tasks | Kind | Security review | Status`, showing every phase (Kind: `Code` or `Docs only`; Security review: `Yes — <reason>` or `No`; Status: `Waits for <waits_for>` for a waiting phase; otherwise `Can start`, or `Waits for remediation` in a Not ready report, so a remediation-only report never shows a phase as startable). Then, per ready phase, `<h3>Phase <id>: <title></h3>`, a toolbar with `<button class="copy-prompt" type="button" data-copy-target="handoff-<id>">Copy Phase <id> prompt</button><span class="copy-status" role="status" aria-live="polite"></span>`, and `<pre id="handoff-<id>" tabindex="0">`. A version-3 Not ready report, or one with no ready phase, shows the table and the existing single remediation prompt markup.
- Version 1 and 2 markup (one shared code path) keeps `id="copy-prompt"` and `id="handoff"` and adds `class="copy-prompt" data-copy-target="handoff"` to the button, so saved reports keep a working copy button.
- `report.js` binds every `button[data-copy-target]` and finds the prompt with `document.getElementById(button.dataset.copyTarget)` (not a CSS selector, because phase IDs may contain dots); the status element is the button's next sibling.

- [ ] **Step 1: Write the failing tests**

```python
def test_phase_table_lists_every_phase_with_its_flags(self):
    source, context = self.two_phase()
    context["phases"][1].update(docs_only=True)
    page, _, _ = render(source, context)
    table = page[page.index('aria-label="Phase plan"'):]
    for text in ("Phase", "Tasks", "Kind", "Security review", "Status", "Docs only", "Can start"):
        self.assertIn(text, table)

def test_every_copy_button_targets_an_existing_prompt(self):
    source, context = self.two_phase()
    page, _, _ = render(source, context)
    targets = re.findall(r'data-copy-target="([^"]+)"', page)
    self.assertEqual(targets, ["handoff-1", "handoff-2"])
    for target in targets:
        self.assertIn(f'<pre id="{target}"', page)

def test_historical_phase_report_offers_no_copy_button(self):
    source, context = self.two_phase()
    context["handoff_status"] = "historical"
    page, _, _ = render(source, context)
    # report.js is inlined and names the attribute, so look for markup only.
    self.assertNotIn('data-copy-target="', page)
    self.assertNotIn('href="handoff.txt"', page)

def test_not_ready_phase_table_offers_no_start(self):
    source = REPORT.replace("**Ready.**", "**Not ready.**").replace(
        "Implement the approved scope now.", "Resume validation. Do not start dependent implementation.")
    page, _, _ = render(source, self.modern_context())
    self.assertIn("Waits for remediation", page)
    self.assertNotIn("Can start", page)

def test_saved_reports_keep_a_working_copy_button(self):
    page, _, _ = render(REPORT, self.context)
    self.assertIn('data-copy-target="handoff"', page)
    self.assertIn('<pre id="handoff"', page)

def test_phase_titles_cannot_inject_markup(self):
    source, context = self.two_phase()
    context["phases"][0]["title"] = "<img src=x onerror=alert(1)>"
    page, _, _ = render(source, context)
    self.assertNotIn("<img src=x", page)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py' -k phase -k copy`
Expected: FAIL (no phase table or `data-copy-target` yet).

- [ ] **Step 3: Implement**

Render the markup above with `escape()`/`inline()` on every context string. For version 3, the section 8 intro is the section text with all fenced prompts removed. Keep the existing historical warning in place of every toolbar. Rewrite the copy block in `report.js` as one loop over `document.querySelectorAll("button[data-copy-target]")`, keeping the current clipboard call, selection fallback and status messages.

- [ ] **Step 4: Run all checks and inspect the output**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py' && python3 scripts/check_package.py && python3 scripts/demo.py --output "$(mktemp -d)/demo"`
Expected: all OK. Render a two-phase report into a temporary directory and open it in a browser: both copy buttons copy their own prompt.

- [ ] **Step 5: Commit**

```bash
git add skills/validate-plan/scripts/render_report.py skills/validate-plan/scripts/test_render_report.py skills/validate-plan/assets/report.js skills/validate-plan/assets/report.css
git commit -m "Show the phase plan and a copy button for each phase prompt"
```

### Task 4: Skill text for phase grouping and phase prompts

**Files:**
- Modify: `skills/validate-plan/SKILL.md` ("Report and handoff", lines 45–55)
- Modify: `skills/validate-plan/handoff-template.md`
- Modify: `skills/validate-plan/references/report-contract.md` (section 8 rules)
- Modify: `skills/validate-plan/references/html-report.md` (format version, checks, example context, files)
- Modify: `AGENTS.md` ("Format versions" bullet)

**Interfaces:**
- Consumes: the version-3 context fields and renderer checks from Tasks 1–3, exactly as named there.

- [ ] **Step 1: `SKILL.md`**

Switch new reports to format version 3. Add the grouping rules from the spec's "Validator and report changes" section: every validated task in exactly one phase, in plan order, none split or moved; never cross a plan-defined phase or part; split a plan phase larger than about 5 tasks into consecutive sub-phases; keep small plan phases; a phase-less plan of 5 or fewer tasks is one phase; target 3–5 tasks; end where tests pass and the PR is reviewable alone; record docs-only, security review with reason, and ready/waiting with what it waits for; phases run in order and a waiting phase holds back later ones; partial approval makes the whole phase wait; if the first phase waits, section 8 holds one prompt that names what to resolve and says `Do not start dependent implementation.`; a phase-only validation groups only the selected scope. State that the grouping lives only in the report and context, never in the plan file. Replace "the selected phase or whole validated scope" with one prompt per ready phase. Keep "Repository-specific workflow belongs in repository instructions" and add a pointer to the "Phased implementation" documentation page for the recommended workflow, as the absolute URL `https://snowholt-labs.github.io/plan-validation/phased-implementation/` (a relative link would leave the shipped skill directory).

- [ ] **Step 2: `handoff-template.md`**

Replace the template block with this text (about 70 words with filled paths):

```text
Work in `[repository path]`. Implement Phase [N] (Tasks [list]) from `[PLAN path]`.

Read `[SPEC path]`, `[report.md path]`, its context.json and repository instructions. Confirm Phase [N-1] is merged and the scope is still valid. Follow recorded decisions, permissions and reviews; preserve unrelated work.

Do not ask to continue between steps. Stop only for required approvals or unfixable failures. Stop at the end of Phase [N] and print the Phase [N+1] prompt from the report; do not start it.
```

Also replace the "For **Ready after approvals**" paragraph: phases run in order, so name the ready phases and the first waiting phase with its decision ID; when the first phase waits, section 8 holds one prompt with `Do not start dependent implementation.` Add the variants: Phase 1 drops "Phase [N-1] is merged and"; the last phase ends "Stop at the end of Phase [N]; it is the last phase."; the phase before a waiting phase ends "Stop at the end of Phase [N]. Phase [N+1] waits for [decision]; there is no prompt for it yet." Name only the decision ID there (for example `D1`), because a descriptive decision pushes this variant past 80 words. Define expected changes between phases: earlier phases merged into the plan branch and ticked task checkboxes are not drift; any other plan, spec or approval change needs reconciliation first. Tell the session how to check this: compare the plan and spec with `revised-plan.md` and `revised-spec.md` in the report's run directory (for example `diff`), and treat only `- [ ]` to `- [x]` changes as expected. Keep the Not ready and suggested-effort sections; one suggested-effort line covers all phases.

- [ ] **Step 3: `report-contract.md` and `html-report.md`**

Section 8 contract: the phase table (rendered from context), then one fenced prompt per ready phase in order, each within the word limit and naming its own stop; Not ready keeps one remediation prompt. In `html-report.md`: new reports use `format_version: 3`; add `task_inventory` and `phases` to the example context with the field rules from Task 1; list the new renderer checks (coverage and order, phase IDs unique ignoring case, flag consistency, waiting order, prompt count, the single prompt when no phase can start, per-prompt stop sentence and word limit); list the `handoff-phase-<id>.txt` files and that a re-render replaces them. Keep the version 1 and 2 recovery text, stating that version 2 is now saved-report only.

- [ ] **Step 4: `AGENTS.md`**

Update the "Report pipeline" bullet (version 3 adds the phase checks and writes `handoff-phase-<id>.txt` files beside `handoff.txt`) and the "Format versions" bullet: 1 legacy, 2 saved-report only, 3 current (adds the task inventory, phase grouping and one prompt per ready phase); new reports must use version 3.

- [ ] **Step 5: Verify**

Run: `python3 scripts/check_package.py && grep -rnE 'format version 2|format_version.{0,3}2\b|all validated phases' skills/validate-plan/SKILL.md skills/validate-plan/handoff-template.md skills/validate-plan/references AGENTS.md`
Expected: check passes; the grep shows only lines describing version 2 as saved-report only (it covers `format_version: 2` and the JSON form `"format_version": 2`; the test file is excluded because its legacy fixtures keep version 2 on purpose). Then confirm by hand that `SKILL.md` frontmatter still has `disable-model-invocation: true` and `skills/validate-plan/agents/openai.yaml` is unchanged (`git diff --stat`). Check the changed skill text against `docs/evaluation.md` as `AGENTS.md` requires; its "Implementation handoff" case still expects a stop at "the scope end" and is updated in the spec's follow-up, so note that known gap in the PR body.

- [ ] **Step 6: Commit**

```bash
git add skills/validate-plan AGENTS.md
git commit -m "Teach the validator to group tasks into phases with one prompt each"
```

### Task 5: Documentation page for the per-phase workflow

**Files:**
- Create: `site/src/content/docs/phased-implementation.md`
- Modify: `site/scripts/content-map.mjs` (`SIDEBAR`, "Learn" items)
- Modify: `site/scripts/sync-content.test.mjs` (`the sidebar has four groups with the planned order` lists every slug)
- Modify: `site/src/content/docs/reports-and-handoffs.md` ("What the renderer checks", "Freshness", "Starting implementation")
- Modify: `README.md` (report item 8, which still says "naming one phase or the whole validated scope")

- [ ] **Step 1: Write the page**

Front matter `title: Phased implementation`, `description: Run a validated plan one small phase per fresh session.` Content, in plain words: why (each message re-reads the whole session, so long sessions cost more; cite no private numbers or paths), how the report groups tasks and gives one prompt per phase, and the spec's "Recommended per-phase workflow" steps 1–7 and "Other rules" (severity-based review loop with the 5-round safety limit; security review only for flagged phases, before the PR; docs-only PRs CI only; full reviews on the final plan-to-main PR; merge before the next phase). End with a short copyable block of repository-instruction text a maintainer can paste into `AGENTS.md`.

- [ ] **Step 2: Sidebar and cross-links**

Add `{ label: 'Phased implementation', slug: 'phased-implementation' }` after "Reports and handoffs" in the "Learn" group, and add `'phased-implementation'` after `'reports-and-handoffs'` in the expected slug list of `sync-content.test.mjs` (without it, `npm test` fails). In `reports-and-handoffs.md`: new runs use version 3; describe the phase table, one prompt per ready phase, the stop sentence and the `handoff-phase-<id>.txt` files; link to the new page from "Starting implementation". In `README.md`, change report item 8 to one prompt per ready phase that stops at the phase end.

- [ ] **Step 3: Verify**

Run: `python3 scripts/check_package.py && cd site && npm ci && npm test && npm run build`
Expected: all pass; the built site includes `phased-implementation/`.

- [ ] **Step 4: Commit**

```bash
git add site/src/content/docs/phased-implementation.md site/scripts/content-map.mjs site/scripts/sync-content.test.mjs site/src/content/docs/reports-and-handoffs.md README.md
git commit -m "Document the phased implementation workflow"
```
