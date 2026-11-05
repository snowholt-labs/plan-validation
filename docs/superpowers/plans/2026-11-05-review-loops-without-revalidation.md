# Review Loops Without Re-validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove re-validation (run counting, the 3-run limit, `rerun`, held prompts) from new reports. Validation reviews the plan with a full-plan review loop, asks the maintainer once at the end, and writes a fixed Phase workflow into each new plan. Docs PRs swap `/code-review` for a full-plan review.

**Architecture:** The renderer gains format version 5: version 4 without `validation_run`, `rerun`, `rerun.txt` or held prompts, with drift advice that names no run. New reports must use version 5, and version 4 keeps rendering saved reports byte for byte. The skill text, references, evaluation cases, site docs, `AGENTS.md` and the maintainer's global rules then describe the new flow.

**Tech Stack:** Python 3.10+ standard library (`unittest`), Markdown skill text, Astro docs site (`site/`).

**Spec:** `docs/superpowers/specs/2026-11-05-review-loops-without-revalidation-design.md`

## Global Constraints

- Python 3.10+, standard library only. No new runtime dependency. Superpowers is never bundled or required.
- Superpowers skill names are pointers: every step that names one also states the behavior, so the flow works on Codex and without Superpowers.
- Versions 1–3 output stays frozen by `test_legacy_output_is_frozen`. Its digests are never re-pinned. Version 4 saved output is pinned the same way in Task 1 and never re-pinned.
- Only new plans change. Do not migrate or rewrite existing reports, plans or specs.
- Phase prompts stay at most 80 words, a backtick-quoted absolute path counting as one word.
- Validation still never commits, pushes, opens PRs, posts comments, merges, deploys, installs or reads secrets.
- `validate-plan` stays explicit-only: `disable-model-invocation: true` and `allow_implicit_invocation: false`, checked by hand.
- Markdown uses placeholders such as `<skill-directory>`, never home-directory paths.
- Shipped text is neutral and professional.

## Review Focus

1. **An existing saved version 4 report re-renders.** Expected: the page, `handoff.txt`, the phase prompts and the kept `rerun.txt` are unchanged. `test_v4_saved_output_is_frozen` (Task 1) covers the page, handoff, prefix and phase prompts. `test_saved_rerender_keeps_the_latest_rerun_file`, rewritten in Task 2, covers the kept `rerun.txt` through `main`.
2. **A new report still carries `validation_run` or `rerun`,** from an agent following old habits. Expected: rejected with a message saying re-validation was removed. Covered by `test_v5_rejects_run_fields` (Task 1).
3. **A version 5 section 8 still says "Run validation again first".** Expected: rejected. Covered by `test_v5_rejects_run_first_line` (Task 1).
4. **The plan or spec changed after a version 5 review.** Expected: the warning tells the reader to reconcile the change or validate again, and names no run number, no limit and no review rounds. Covered by `test_v5_drift_warning_names_no_run` (Task 1).
5. **A new version 5 render goes into a run directory that has an old `rerun.txt`.** Expected: the stale file is deleted, and the JSON says `"rerun": null` and `"handoff_held": false`. Covered by `test_v5_main_writes_no_rerun_file` (Task 1).

## Phase workflow

Every phase follows these steps, in a fresh session, on its own phase branch.

1. Work in a git worktree for the phase branch (`superpowers:using-git-worktrees`).
2. For each task: write the failing test first and watch it fail (`superpowers:test-driven-development`), write the code, then prove it works by running the tests (`superpowers:verification-before-completion`).
3. Review the phase against the plan, spec and validation report (`superpowers:requesting-code-review`, with the plan and spec paths, the report path named in the phase prompt and the phase's base..head range).
4. Check each finding before fixing it, and push back on wrong ones (`superpowers:receiving-code-review`).
5. For any failing test or unexpected behavior, find the cause before fixing it (`superpowers:systematic-debugging`).
6. Repeat steps 3–5 until no Medium or High finding remains (Critical counts as High, Important as Medium, Minor as Low). Do not loop on wording-level findings: list them, and ask the maintainer to fix or skip each one in the end-of-phase report.
7. Run `superpowers:finishing-a-development-branch` as the readiness check: tests pass on the branch. Do not push, open a PR or merge at this step, and never merge locally into a protected or plan branch.
8. Run the code and security reviews this repository's rules require (in Claude Code, `/code-review` and `/security-review`), and fix required findings.
9. Deliver the branch as the repository's rules define (for a plan branch, a PR into that branch). Push and open a PR only when the repository's rules or the maintainer authorize it. Otherwise stop and report that the branch is ready.

A docs-only phase skips step 2's test-first rule. Its step 8 runs the reviews the repository's rules require for docs-only changes.

## Delivery

- Plan branch `plan/review-loops`, milestone "Review loops without re-validation". Repository rules in `AGENTS.md` govern branches, reviews and merges.
- Phases: **P1** Tasks 1–2 (renderer), **P2** Tasks 3–5 (skill text and evaluation, docs-only), **P3** Tasks 6–7 (site docs and `AGENTS.md`, docs-only). The plan is done when P3 merges. Then come the plan-to-`main` PR and the release.
- **Follow-up after the release:** Task 8. It is not a plan phase and has no branch or PR. It starts only after the release that ships P1–P3 is tagged, and only on the maintainer's go-ahead.
- Every `git commit` runs in the same command as `git branch --show-current`, and stops if the branch is not the expected phase branch. Task commit messages end with `Plan: docs/superpowers/plans/2026-11-05-review-loops-without-revalidation.md`, `Phase: <P1–P3>`, `Task: <n>`, then `Co-Authored-By:`, with no blank line between them. The commit blocks below show only the subject.
- **This plan's own docs PRs already use the new review.** On 2026-11-05 the maintainer decided that the docs PR and the docs-only phases P2–P3 use the full-plan review (spec section 3) instead of `/code-review`, posted as `## Code review` with `review/code`, and `/security-review` once. The code phase P1 follows today's rules: the Phase workflow, then `/code-review` and `/security-review`.
- **`assets/report-v4.css` and `report-v4.js` are not changed.** Saved version 4 reports still draw the rerun card with them.
- Test command used below: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py'` (abbreviated **UNIT**; append `-k <name>` for one test).

---

### Task 1: Format version 5 in the renderer

**Files:**
- Modify: `skills/validate-plan/scripts/render_report.py` (`render`, `waits_for_rerun`, `page_v4`, a new `historical_warning_v5`, new constants)
- Test: `skills/validate-plan/scripts/test_render_report.py`

**Interfaces:**
- Produces: `render()` accepts `format_version` 1–5. In this task, new reports may use 4 or 5. Task 2 narrows that to 5.
- Produces: the constant `V5_DRIFT_TEXT = "The plan or spec changed or could not be read after this validation. Reconcile the change before building, or validate the changed scope again."`
- Produces: `historical_warning_v5(fingerprints_match: bool) -> str`, which, when the fingerprints match (only Git state or approvals drifted), returns `<p class="warning">This is a historical prompt. Git state or approvals changed after this validation. Reconcile the change before building, or validate the changed scope again.</p>`, so the page never mixes "Revalidate" and "Reconcile". Otherwise it returns `<p class="warning">This is a historical prompt. {V5_DRIFT_TEXT}</p>`, without `HISTORICAL_TEXT`, whose "Revalidate the changed scope" would contradict it. `HISTORICAL_PREFIX` stays for versions 1–4, because the digests cover it. Version 5 uses `V5_HISTORICAL_PREFIX = "HISTORICAL PROMPT — DO NOT EXECUTE.\nDocument identity, Git state or approvals changed. Reconcile the change before building, or validate the changed scope again.\n\n"`.
- Produces: `phase_status(phase, verdict, current, rerun_first=False, version=4)`. At version 5 it returns `Reconcile before starting` where earlier versions return `Revalidate before starting`.
- Produces test helpers in `ReportTests`:
  - `v4_context(self, kind="saved") -> dict`: an explicit copy of today's `modern_context()` body, with `format_version` 4, `validation_run`, `rerun` and the given `kind`. It must not call `modern_context()`, so Task 2 can change that helper without touching it.
  - `v5_context(self) -> dict`: built from `self.v4_context("new")` by deleting `validation_run` and `rerun` and setting `format_version` to 5. Never build it from `modern_context()`: Task 2 makes `modern_context()` return `v5_context()`, which would then recurse.

- [ ] **Step 1: Pin version 4 saved output on the unchanged renderer**

  Add `V4_SAVED_DIGESTS` (a dict) and `v4_saved_cases(self) -> dict[str, tuple[str, dict]]`. Like the legacy cases ("The fixtures are literal on purpose"), the cases use literal module-level copies beside the digests: `V4_FROZEN_REPORT`, `V4_FROZEN_RERUN_PROMPT` and a literal v4 context dict. Only its `documents` come from `setUp` at runtime, as `legacy_cases` does with `legacy_documents()`, because the document paths are temporary files. Every case's context has `"kind": "saved"`, so Task 2's rejection of new v4 reports leaves the digests valid. They never use the shared `REPORT`, `run_first`, `rerun_yes`, `stop_rerun` or `ZONES_DIAGRAM`, so later edits to those cannot break the digests. Four keys:
  - `"v4-no"`: `V4_FROZEN_REPORT` with a deep copy of the literal context, which has `rerun` `{"recommendation": "no", ...}`.
  - `"v4-yes-held"`: `V4_FROZEN_REPORT` with the run-first line written into its section 8 literally, and a context whose `rerun` is a literal yes object carrying `V4_FROZEN_RERUN_PROMPT`. Copy today's passing values once; don't call `run_first` or `rerun_yes`.
  - `"v4-stop-historical"`: `V4_FROZEN_REPORT` with a context whose `rerun` is a literal stop object and whose `handoff_status` is `"historical"`.
  - `"v4-drift"`: `V4_FROZEN_REPORT` with the literal context whose PLAN document points to its own file, `<temp dir>/drift/PLAN.md`, written with the text `Changed`, while the recorded `sha256` is still that of `PLAN`. The file name stays `PLAN.md` so that `validation_run.plan_key` (`PLAN.md`) still ends the PLAN path. Never rewrite the shared `PLAN.md`: the other cases must render as current.

  Add a test that compares them. Each digest covers the page, the handoff, the prefix and every phase prompt:

  ```python
  def test_v4_saved_output_is_frozen(self):
      actual = {}
      for key, (source, context) in self.v4_saved_cases().items():
          rendered = render(source, context)
          blob = "\0".join((normalized(rendered[0], self.directory.name), rendered[1], rendered.prefix,
                             *(f"{phase}:{prompt}" for phase, prompt in rendered.pairs)))
          actual[key] = hashlib.sha256(blob.encode()).hexdigest()
      self.assertEqual(actual, V4_SAVED_DIGESTS)
  ```

  Fill `V4_SAVED_DIGESTS` with the digests the current code prints. Get them by temporarily printing `actual` in the test, running it, then removing the print. Run **UNIT** `-k test_v4_saved_output_is_frozen`. Expected: PASS before any renderer change.

- [ ] **Step 2: Add the `v4_context` and `v5_context` helpers (Interfaces above), then write the failing version 5 tests**

  ```python
  def test_v5_renders_without_run_fields(self):
      page, handoff, current, rerun_prompt = render(REPORT, self.v5_context())
      self.assertTrue(current)
      self.assertIsNone(rerun_prompt)
      self.assertNotIn('id="rerun"', page)
      self.assertNotIn("Run validation again", page)
      self.assertNotIn("of at most 3", page)
      self.assertFalse(handoff.startswith("HELD PROMPT"))

  def test_v5_rejects_run_fields(self):
      for field, value in (("validation_run", {"number": 1, "plan_key": "PLAN.md", "scope": "full"}),
                           ("rerun", {"recommendation": "no", "reasons": ["x"]})):
          with self.subTest(field=field):
              context = self.v5_context()
              context[field] = value
              with self.assertRaisesRegex(ValueError, "no validation_run or rerun"):
                  render(REPORT, context)

  def test_v5_rejects_run_first_line(self):
      with self.assertRaisesRegex(ValueError, "run validation again first"):
          render(run_first(REPORT), self.v5_context())

  def test_v5_drift_warning_names_no_run(self):
      context = self.v5_context()
      plan = Path(context["documents"][0]["path"])
      plan.write_text("Changed")
      self.addCleanup(plan.write_text, "PLAN")
      page, handoff, current, _ = render(REPORT, context)
      self.assertFalse(current)
      self.assertTrue(handoff.startswith(render_report.V5_HISTORICAL_PREFIX))
      self.assertIn(render_report.V5_DRIFT_TEXT, page)
      self.assertIn("Reconcile before starting", page)
      for text in ("run 2 of 3", "3-run limit", "review rounds", "run limit", "Revalidate the changed scope", "Revalidate before starting"):
          self.assertNotIn(text, page)

  def test_v5_main_writes_no_rerun_file(self):
      out = Path(self.directory.name) / "v5"
      out.mkdir()
      (out / "rerun.txt").write_text("old\n")
      result = self.run_renderer(out, REPORT, self.v5_context())
      self.assertEqual(result.returncode, 0, result.stderr)
      output = json.loads(result.stdout)
      self.assertIsNone(output["rerun"])
      self.assertFalse(output["handoff_held"])
      self.assertFalse((out / "rerun.txt").exists())
  ```

- [ ] **Step 3: Run them to verify they fail**

  Run **UNIT** `-k test_v5_`. Expected: FAIL. `format_version must be 1 (legacy), 2, 3 or 4` is raised for every test.

- [ ] **Step 4: Implement version 5 in `render_report.py`**
  - `render()`: allow versions `(1, 2, 3, 4, 5)`. The error becomes `format_version must be 1 (legacy), 2, 3, 4 or 5`. New reports need `version in (4, 5)`, with the message `New reports require format_version 4 or 5; earlier versions render saved reports only`. Task 2 narrows it to 5. Change the `test_new_reports_require_version_4` regex from `format_version 4` to `format_version 4 or 5`.
  - `run_first_note()`: at version 5, the stray-line error reads `Section 8 says to run validation again first, but new reports have no re-run; remove that line`. Version 4 keeps its message.
  - In the `version >= 4` block, at version 5: raise `ValueError("Version 5 reports have no validation_run or rerun; re-validation was removed")` when either key is present. Then set `fields["rerun"] = None` and skip `rerun_check`. Version 4 keeps calling `rerun_check`.
  - `waits_for_rerun()`: true only for `version == 4`. Version 5 then reaches the existing branch in `run_first_note` that rejects a "run validation again first" line. The held prefix and `phases_held` stay false.
  - `prompt_prefix()`: return `V5_HISTORICAL_PREFIX` at version 5 when not current. Pass the version to every `phase_status` call: through `phase_table` and `report_sections`, and in `page_v4`'s own Summary phase cards, and make `page_v4` pass the context's real version to `report_sections` instead of the hard-coded 4. The Files list covers these as part of `render_report.py`.
  - `page_v4()`: when `fields["rerun"]` is `None`, add no rerun pill and no `rerun_card`, and use `historical_warning_v5(fingerprints_match)`.
  - `render()` return: pass `None` as the re-run prompt when `fields["rerun"]` is `None`. `main()` already deletes `rerun.txt` for a non-saved kind and writes none for `None`.
  - In `test_new_reports_require_version_4`, change the "unknown version" assertion from `format_version` 5 to 6, since 5 is now valid. Task 2 rewrites the rest of the test.

- [ ] **Step 5: Run all tests**

  Run **UNIT**. Expected: PASS, with `test_v4_saved_output_is_frozen` and `test_legacy_output_is_frozen` unchanged.

- [ ] **Step 6: Commit**

  ```bash
  git add skills/validate-plan/scripts/render_report.py skills/validate-plan/scripts/test_render_report.py
  git commit -m "Add report format version 5 without re-run fields"
  ```

### Task 2: New reports require version 5

**Files:**
- Modify: `skills/validate-plan/scripts/render_report.py` (`render`)
- Modify: `skills/validate-plan/scripts/test_render_report.py`
- Modify: `scripts/demo.py`

**Interfaces:**
- Consumes: `v4_context(kind)` and `v5_context()` from Task 1.
- Produces: a `kind: "new"` context with `format_version` other than 5 raises `New reports require format_version 5; earlier versions render saved reports only`.

- [ ] **Step 1: Write the failing test**

  Rename `test_new_reports_require_version_4` to `test_new_reports_require_version_5`, with these assertions:
  - `format_version` 3, then 4, on a new context: `assertRaisesRegex(ValueError, "format_version 5")`.
  - `format_version` 6: `assertRaisesRegex(ValueError, "format_version")`.
  - `render(REPORT, self.v4_context())` (saved) still renders.
  - `render(REPORT, self.v5_context())` renders.

- [ ] **Step 2: Run it to verify it fails**

  Run **UNIT** `-k test_new_reports_require_version_5`. Expected: FAIL, because version 4 new is still accepted.

- [ ] **Step 3: Require version 5 for new reports**

  In `render()`, change the check to `version != 5` with the message above. Make `modern_context()` return `v5_context()`, so the shared page tests now cover version 5.

- [ ] **Step 4: Move the v4 re-run tests to saved reports**

  Run **UNIT** and sort each failing test by this rule:
  1. **It checks a v4 behavior that a saved report still shows** (the rerun card and pill, held prompts and their files, the saved drift warning, a kept `rerun.txt`). Switch it to `self.v4_context()`, which is kind `"saved"`.
  2. **It checks only what a new v4 report did** (writing `rerun.txt`, the `rerun.txt` path check in `main`, `run_first_note` *requiring* the run-first line, the run-counting rules that `rerun_check` applies to a new run's prompt). Tests of `run_first_note` *rejecting* a stray or reworded run-first line, and of accepting a negated one ("You do not need to run validation again first."), are still v5 behavior and follow rule 3. Version 5 is the only new format now, so delete it. Keep a test when its `rerun_check` errors also fire for a saved v4 report. In that case switch it to `v4_context()`.
  3. **It uses `stop_rerun` or `rerun_yes` only to fill v4's required fields,** and checks something else: Not ready remediation prompts, merge sentences, failed-write cleanup and so on. Keep it on `modern_context()` (version 5) and drop the `stop_rerun`/`rerun_yes` call, so the new-report checks keep running. `test_failed_write_never_leaves_an_old_rerun_prompt` becomes a v5 test: an earlier `rerun.txt` is gone after a failed write.

  4. **Its expected wording changes at version 5,** for example `test_historical_phase_table_offers_no_start` ("Revalidate before starting") and `test_main_writes_one_file_per_phase_and_marks_historical_files` (`HISTORICAL_PREFIX`). Keep it on `modern_context()` and expect "Reconcile before starting" and `V5_HISTORICAL_PREFIX`.

  `test_saved_rerender_keeps_the_latest_rerun_file` is not deleted. Rewrite it to write the `rerun.txt` file directly, then run `main` on `self.v4_context()`. Its assertions stay the same.

  List every deleted test in the commit message body.

- [ ] **Step 5: Update the demo** (`test_demo_runs_into_a_folder_with_spaces` fails from Step 3 until this step; do not sort, delete or rewrite it in Step 4)

  In `scripts/demo.py`:
  - set `format_version` to 5;
  - remove `validation_run`, `rerun` and the `rerun.txt` write;
  - take the third value of `render(...)` as before, and ignore the fourth (now always `None`);
  - in the remediation prompt, replace `Do not edit the implementation files or validate again; the re-run prompt does that.` with `Do not edit the implementation files.` Recheck that the prompt stays within 80 words and has no unnegated `implement` form.

- [ ] **Step 6: Run all checks**

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py'
  python3 scripts/check_package.py
  python3 scripts/demo.py --output "$(mktemp -d)/demo"
  ```

  Expected:
  - The unit tests PASS. Both frozen-digest tests are unchanged.
  - `check_package.py` passes.
  - The demo reports `64 != 30` for `uncapped.py`, passes `corrected.py`, and renders. Its output folder has no `rerun.txt`.

- [ ] **Step 7: Commit**

  ```bash
  git add skills/validate-plan/scripts/render_report.py skills/validate-plan/scripts/test_render_report.py scripts/demo.py
  git commit -m "Require format version 5 for new reports"
  ```

### Task 3: Validation workflow text

**Files:**
- Create: `skills/validate-plan/references/phase-workflow.md` (the exact block validation copies into a plan)
- Modify: `skills/validate-plan/SKILL.md` (Authority and boundaries, workflow steps 1 and 4–8, Report and handoff, Resume or repeat)
- Modify: `skills/validate-plan/references/plan-reviewer.md`

**Interfaces:**
- Produces: `references/phase-workflow.md`, which holds this plan's "Phase workflow" section verbatim, from `## Phase workflow` to the docs-only sentence. It adds one line above the block: validation copies the block into the plan once, near the top, only when the plan has no `## Phase workflow` heading.

- [ ] **Step 1: Write `references/phase-workflow.md`**, with the content above.

- [ ] **Step 2: Edit `SKILL.md`**
  - **Authority and boundaries:** the "Do not stop to ask routine questions… Ask only for a missing required path or an ambiguous document pairing" bullet, and "keep working instead of stopping to ask", now allow one more ask. That is the single end-of-run question round at the end of step 8, after independent work. Mid-run work still never pauses.
  - **Step 1:** remove the run counting and the run-limit stop.
  - **Step 4:** keep "do not invent other conventions". Add the one exception: when the plan has no `## Phase workflow` heading, add the block from `references/phase-workflow.md` (linked from SKILL.md as a relative Markdown link). Record it in section 5 with this skill rule as its approval basis. The block grants no permission. A read-only request adds nothing.
  - **Step 5:** before changing the plan for a failing rehearsal command, find its cause (`superpowers:systematic-debugging` when installed). Write the behavior out in words.
  - **Step 6:** dispatch the reviewer the way `superpowers:requesting-code-review` does, as a fresh subagent that returns only findings. Always use the `plan-reviewer.md` brief: the documents are uncommitted, so there is no commit range for that skill's diff template. The brief gives the reviewer the revised documents and the original snapshots. Triage each finding against the code and documents (`superpowers:receiving-code-review` behavior): push back on wrong ones and never reword correct text. Fix verified Medium and High findings, then review again until none remain.
    - A finding whose fix changes requirements, architecture, security boundaries or scope is not fixed. It becomes a pending approval and leaves the loop.
    - Low findings are listed, not fixed. There is no round cap.
  - **Step 7:** independent work still never pauses. Record the questions here; they are asked in step 8, after the first render. In step 7's text, remove the "update `rerun` … (the run number stays)" clause and the "add or remove the section 8 run-again-first note to match" clause from the re-render sentence. Change "the user can answer later" and "do not stop to ask" so they point to the step 8 question round.
  - **Step 8, at its end, after cleanup, verification and the first render:** ask one round of questions: each pending approval with its recommendation, and any wording-only findings to fix or skip. Use AskUserQuestion in Claude Code, and chat in Codex.
    - Apply and recheck each answer, then re-render in the same run. If this run published an artifact (`artifact.json` in the run directory), update that same artifact after the re-render, without being asked, using the existing update steps in html-report.md (`url` from `artifact.json`, no quickstart, stale phase files set to `null`, `artifact.json` rewritten). Qualify "update that artifact … only when the user asks" in "Resume or repeat", and the "A re-render after a recorded answer is a re-render, as in Resume or repeat below" sentence in "Report and handoff", to allow this one case. An unanswered question stays pending in the rendered report. Where the host cannot ask, the report's open items are the questions.
    - An answer for a version 4 run is not re-rendered or migrated. Tell the maintainer to validate the plan again; the new run uses version 5.
    - Not ready: the remediation prompt stays as it is. The final reply, not the prompt, tells the maintainer that validating the fixed plan is how to get phase prompts.
  - **Step 8, before scoring:** every claim in the verdict and section 7 must rest on a command or review that ran in this run (`superpowers:verification-before-completion` behavior).
  - **Report and handoff:** new reports use format version 5. That is version 4 without `validation_run` and `rerun`. Version 4 renders saved reports only.
    - Remove the `rerun.txt`, `handoff_held` and run-again parts of the delivery reply, and the `"handoff_held": true` sentence in the paragraph about inspecting the renderer output.
    - Each phase prompt follows the plan's Phase workflow (Task 4 has the template).
  - **Resume or repeat:** remove "keep the `validation_run`". A re-render still is not a new run.

- [ ] **Step 3: Edit `plan-reviewer.md`**
  - Add a `Validation report: <absolute path, or None for a first validation>` input line.
  - Ask for severity as High, Medium or Low, defined as: High blocks safe implementation; Medium would cause rework or a wrong build; Low is wording, style or optional detail. The loop's exit rule uses this scale.
  - Add one sentence: each review round gets the current documents. A round after fixes also gets the list of findings already dispositioned, so it does not re-raise them.

- [ ] **Step 4: Verify**

  ```bash
  python3 scripts/check_package.py
  grep -n -i -E "run count|3-run|run limit|rerun|re-run|run-again|run validation again|validation_run|handoff_held|held" skills/validate-plan/SKILL.md
  ```

  Expected:
  - `check_package.py` passes. This also checks the new relative link, the `Publish setting` line and the publish gate sentence.
  - The `grep` prints only lines that mention version 4 saved reports.
  - By hand: `disable-model-invocation: true` is still in the frontmatter.

- [ ] **Step 5: Commit**

  ```bash
  git add skills/validate-plan/SKILL.md skills/validate-plan/references/phase-workflow.md skills/validate-plan/references/plan-reviewer.md
  git commit -m "Replace re-validation with a review loop and end-of-run questions"
  ```

### Task 4: Report contract and handoff template

**Files:**
- Modify: `skills/validate-plan/references/report-contract.md` (remove "Run validation again"; section 8 and drift text)
- Modify: `skills/validate-plan/references/html-report.md` (remove "Run counting" and the `validation_run`/`rerun` fields from the version 5 shape; one line saying version 4 saved contexts keep them)
- Modify: `skills/validate-plan/handoff-template.md`

**Interfaces:**
- Consumes: `V5_DRIFT_TEXT` wording from Task 1 (the docs say the same thing in prose).
- Produces: this phase prompt template, 79 words with sample paths. It keeps "its context.json" and "reviews", and shortens the stop sentence:

  ```text
  Work in `[repository path]`. Implement Phase [N] (Tasks [first]–[last]) from `[PLAN path]`.

  Read `[SPEC path]`, `[report.md path]`, its context.json and repository instructions. Confirm Phase [previous] is merged and the scope is still valid. Follow the plan's Phase workflow and recorded decisions, permissions and reviews; preserve unrelated work.

  Do not ask to continue between steps. Pause only for required approvals or unfixable failures. Stop at the end of Phase [N] and print the Phase [next] prompt; do not start it. Report results and defaults.
  ```

- Produces: a variant for a plan with no `## Phase workflow` section (a read-only validation): use `Follow recorded decisions, permissions and reviews; preserve unrelated work.` instead, without the Phase workflow words.
- Produces: the shortened waiting variant `Stop at the end of Phase [N]; Phase [next] waits for [decision IDs].`, for example `D1, D2 and D3`. The renderer requires only `Stop at the end of Phase <id>`.

- [ ] **Step 1: Edit `report-contract.md`**
  - Delete the "Run validation again" section.
  - Section 8: drop the "run-again-first note".
  - Move the drift sentence out of the deleted section into a short "Drift warning" paragraph after section 8. For version 5, the historical warning says the documents changed, and to reconcile or validate the changed scope again. It names no run and no limit. Version 4 saved reports keep the warning their renderer draws (run number, 3-run limit, reset).
  - Section 6: drop "a user's explicit reset of the run count".

- [ ] **Step 2: Edit `html-report.md`**
  - Show the version 5 context example without `validation_run` and `rerun`, and delete "Run counting".
  - Rewrite the renderer-check bullets about the run-first line, the section 8 paragraph on held prompts and the `rerun.txt` paragraph, currently near lines 118–146 and 370–380, so that they apply only to version 4 saved reports. A saved report keeps its section 8, held note and `rerun.txt`. A new version 5 report has none of them.
  - Delivery checks: drop "while phase prompts are held" and the Run validation again card check for new reports.
  - Add one line: version 4 saved contexts keep those fields, and the renderer still checks them.
  - In "Private artifact (Claude Code, opt-in)", qualify the whole sentence "Update an existing artifact only when the user asks to publish or update it, … stays local" (currently lines 442–444). The end-of-run re-render in the same run, after the maintainer's answers, updates the run's own artifact through the existing update steps, without being asked. Every other re-render still updates it only on request. Leave the `--open` sentence ("or the same run after a recorded answer") unchanged.
  - Change "New reports (`kind: new`) must use `format_version: 4` … and the run fields `validation_run` and `rerun`" (currently line 44) and "New validation runs use version 4" (currently line 325) to version 5 without the run fields. Drop "the re-run recommendation (run number, answer, reasons and any re-run prompt)" from the full-chat-report list (currently line 8).
  - Update the JSON output description: `rerun` is `null` and `handoff_held` is `false` for version 5.

- [ ] **Step 3: Edit `handoff-template.md`**
  - Replace the prompt block with the template above, and the "Phase before a waiting phase" variant with the shortened one.
  - Delete the run-again-first paragraph.
  - Where it says "in a version 4 report, only a path with no spaces…", say "in a version 4 or later report".
  - Keep the variants, the between-phases note, Ready after approvals, Not ready and Suggested effort.

- [ ] **Step 4: Verify the prompt fits and the package checks pass**

  ```bash
  python3 - <<'E'
  t = open("skills/validate-plan/handoff-template.md").read().split("```text\n")[1].split("\n```")[0]
  t = t.replace("[repository path]", "R").replace("[PLAN path]", "P").replace("[SPEC path]", "S").replace("[report.md path]", "M")
  stop = "Stop at the end of Phase [N] and print the Phase [next] prompt; do not start it."
  print(len(t.split()), len(t.replace(stop, "Stop at the end of Phase [N]; Phase [next] waits for D1, D2 and D3.").split()))
  E
  python3 scripts/check_package.py
  grep -rn -i -E "run validation again|3-run|run [0-9] of|rerun|re-run|format_version: 4|use version 4" skills/validate-plan/references skills/validate-plan/handoff-template.md
  ```

  Expected:
  - Both word counts are at most 80.
  - `check_package.py` passes.
  - Read each `grep` hit. None may describe a re-run, `rerun.txt` or held prompts for a new report. Version 5 lines such as "`rerun` is `null`" are fine.

- [ ] **Step 5: Commit**

  ```bash
  git add skills/validate-plan/references/report-contract.md skills/validate-plan/references/html-report.md skills/validate-plan/handoff-template.md
  git commit -m "Drop the re-run contract and point phase prompts at the Phase workflow"
  ```

### Task 5: Evaluation cases

**Files:**
- Modify: `docs/evaluation.md`

- [ ] **Step 1: Edit the starter cases**
  - Delete the rows "Re-run yes", "Re-run no", "Run 3 stop", "Re-render does not count" and "Phase-only run counts separately".
  - Rewrite "Drift after review": the warning says to reconcile or validate the changed scope again, and names no run, limit or review rounds.
  - In "Fresh-session handoff", add that each prompt follows the plan's Phase workflow, except the read-only variant for a plan with no Phase workflow section.
  - Add these rows:
    - **End-of-run questions:** the report is rendered first. Then pending approvals and wording-only findings are asked once, the answers are applied and rechecked, and the same run re-renders. An unanswered question stays pending in the rendered report, never approved.
    - **Approval-needing finding:** a review finding whose fix would change requirements or boundaries becomes a pending approval and leaves the loop. It is not fixed in the plan.
    - **Phase workflow added:** a plan with no `## Phase workflow` heading gets the block once, recorded in section 5. A plan that has one is not changed. A read-only request adds nothing.
    - **Phase prompt:** says `Follow the plan's Phase workflow` (or, in the read-only variant for a plan without the section, leaves it out) and stays within 80 words.
    - **Answers update the artifact:** with publishing on, the re-render after end-of-run answers updates the same artifact URL. No new artifact is made. Any later re-render, including one after answers given later, stays local unless the user asks.
    - **Docs-PR review:** on a plan's docs PR or a docs-only phase PR, the code review is a full-plan review. The reviewer gets the plan, spec and report. Verified Medium and High findings, design gaps included, are fixed in the PR until none remain. A finding that contradicts a recorded decision, or whose fix would change a security or privacy boundary, a permission or an external action, goes to the maintainer. Wording findings are listed, and fix-or-skip is asked. The result is posted as `## Code review` with `review/code`. `/security-review` runs once. Other docs-only PRs keep `/code-review`.
    - **Without Superpowers:** the review loop, debugging and verification steps still run as written behavior, with the same bundled reviewer brief.
  - Do not edit `docs/verification.md`: it records the dated 0.5.0 release checks, and only a release PR changes release checks (AGENTS.md "Releases").

- [ ] **Step 2: Verify**

  Run `python3 scripts/check_package.py`. Expected: PASS.

- [ ] **Step 3: Commit**

  ```bash
  git add docs/evaluation.md
  git commit -m "Update evaluation cases for the review loop"
  ```

### Task 6: Site docs and changelog

**Files:**
- Modify: `site/src/content/docs/phased-implementation.md` (recommended per-phase workflow, "Reviewing a validated spec and plan", the pasteable block)
- Modify: `site/src/content/docs/reports-and-handoffs.md` (delete "Run validation again"; drop held-prompt wording in "Starting implementation"; version 5 in the format paragraph and drift paragraph)
- Modify: `site/src/content/docs/troubleshooting.md` (historical handoff: reconcile or validate the changed scope again)
- Modify: `CHANGELOG.md` (root; synced into the site at build)

- [ ] **Step 1: Edit `phased-implementation.md`**
  - **"How the report helps":** drop the held-note bullet, "When the report says to run validation again first…" (currently line 15), and "or waits for another validation run".
  - **Stop example (currently line 16):** change it to the new stop sentence, `Stop at the end of Phase 1 and print the Phase 2 prompt; do not start it.`
  - **Per-phase workflow:** replace it with the Phase workflow steps, linking `skills/validate-plan/references/phase-workflow.md` on GitHub. Say that validation adds it to new plans.
  - **Docs PRs:** keep "Docs-only PRs need CI only" as the default. Replace "Reviewing a validated spec and plan" with spec section 3, still framed as "if your repository reviews docs PRs":
    - a full-plan review instead of `/code-review`, given the plan, spec and report;
    - verified Medium and High findings, design gaps included, are fixed in the PR, and review runs again until none remain;
    - a finding that contradicts a recorded decision, or whose fix would change a security or privacy boundary, a permission or an external action, goes to the maintainer;
    - wording findings are listed with fix-or-skip asked at the end, and do not block;
    - the result is posted as the code review; `/security-review` runs once;
    - reviewer severities map Critical to High, Important to Medium, Minor to Low.
  - **Pasteable block:** update it to match.

- [ ] **Step 2: Edit `reports-and-handoffs.md` and `troubleshooting.md`**, as listed under Files.

  Then edit every other mention on `reports-and-handoffs.md` of a re-run, `rerun.txt`, held prompts or run counting. Today these are lines 10, 12, 44, 50, 70 and 84. Each one must either describe only saved version 4 reports or be removed. Also say that after a Not ready remediation, the maintainer validates the fixed plan to get phase prompts.

  Check with `grep -n -i -E "re-run|rerun|run validation again|held|run [0-9] of" site/src/content/docs/*.md` and read each hit. Expected: no hit describes a re-run, `rerun.txt` or held prompts for a new report. Unrelated hits are fine, such as line 46's "rerun tests" and the changelog.

- [ ] **Step 3: Add a changelog entry**

  Add an `## Unreleased` entry at the top of `CHANGELOG.md`. Its bullets:
  - version 5 for new reports, with no re-run, run count or held prompts, while version 4 renders saved reports unchanged;
  - the validation review loop and end-of-run questions;
  - the Phase workflow block;
  - the docs-PR review recommendation.

- [ ] **Step 4: Verify**

  ```bash
  python3 scripts/check_package.py
  cd site && npm ci && npm test && npm run build
  ```

  Expected: both pass.

- [ ] **Step 5: Commit**

  ```bash
  git add site/src/content/docs/phased-implementation.md site/src/content/docs/reports-and-handoffs.md site/src/content/docs/troubleshooting.md CHANGELOG.md
  git commit -m "Document the review loop and drop re-validation from the site"
  ```

### Task 7: Repository instructions

**Files:**
- Modify: `AGENTS.md` ("Report pipeline", "Format versions", "Git workflow", "Plan work")

- [ ] **Step 1: Edit `AGENTS.md`**
  - **Report pipeline and Format versions:** version 5 is current, and version 4 renders saved reports only. Move the `validation_run`/`rerun`/`rerun.txt`/held text under version 4. Name `test_v4_saved_output_is_frozen` beside `test_legacy_output_is_frozen`: its digests are never re-pinned either.
  - **Git workflow:** "Every PR into `main` or `plan/**` gets both reviews, docs-only PRs included" stays. Add that on a plan's docs PR or a docs-only phase PR, the code review is the full-plan review (section 3 of `docs/superpowers/specs/2026-11-05-review-loops-without-revalidation-design.md`) instead of `/code-review`, posted as `## Code review` with `review/code`. Other docs-only PRs keep `/code-review`. The "Code and security review means … (in Claude Code, `/code-review` and `/security-review` …)" definition gains the same exception.
  - **Plan work:** each phase follows the plan's Phase workflow. Its steps 8 and 9 are this repository's existing phase review and PR steps (review rounds, security review, PR, CI, comment reviews and statuses), which stay as written for code phases. They are not a second round after step 9. On a docs-only phase PR, the 5-round cap does not apply to the full-plan review: it loops until no Medium or High finding remains (spec section 3).
  - **Minor items:** in "Phase review", say that the end-of-phase report asks the maintainer to fix or skip each wording-level item. Items left unanswered or skipped are saved as action points for the plan-to-`main` review, as today. That is one disposition, not two.

- [ ] **Step 2: Verify**

  Run `python3 scripts/check_package.py`. Expected: PASS.

- [ ] **Step 3: Commit**

  ```bash
  git add AGENTS.md
  git commit -m "Describe version 5 and the docs-PR review in AGENTS.md"
  ```

### Task 8: Global rules (follow-up after the release, outside the repository)

Runs after the release that ships P1–P3 is tagged. It is not part of any phase. It edits `<home>/.claude/rules/git-workflow.md`, which is not in the repository. There is no branch, commit or PR. Confirm with the maintainer before writing, because the global rules require approval for writes outside the repository.

**Files:**
- Modify: `<home>/.claude/rules/git-workflow.md` ("Reviews Before Every PR")

- [ ] **Step 1: Edit "Reviews Before Every PR"**
  - **Validated docs-PR bullet** ("In a docs PR of a spec and plan that has a `/validate-plan` report…"): replace it with the docs-PR rule from spec section 3. There is no re-validation and no 3-run limit. Design gaps are fixed in the PR until no Medium or High finding remains, except a fix that would change a security or privacy boundary, a permission or an external action, which goes to the maintainer. Wording findings are listed and fix-or-skip is asked at the end.
  - **First bullet:** add that on a plan's docs PR or a docs-only phase PR, the code review is the full-plan review instead of `/code-review`, posted as `## Code review` with the `review/code` status. Other docs-only PRs keep `/code-review`, and "Review docs-only and previously reviewed changes fully" stays for them.
  - **Docs-only severity bullet** ("In a docs-only PR … a `/code-review` finding is High or Medium only when…"): make it apply to the findings of whichever code review the PR runs, the full-plan review included.
  - **"Internal reviews from subagent-driven development do not replace these two reviews":** append "except the docs-PR full-plan review above".
  - **Timing bullet:** delete "(3 rounds for a validated spec and plan, above)".

- [ ] **Step 2: Rebuild the Codex copy**

  Run `<home>/.claude/codex/build-agents-md.sh`. Expected: exit 0.

- [ ] **Step 3: Verify**

  Run `grep -n -E "validate-plan. again|3-run|3 rounds for a validated" <home>/.claude/rules/git-workflow.md`. Expected: no output.
