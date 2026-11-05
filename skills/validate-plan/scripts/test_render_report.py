"""Contract, arithmetic, provenance and injection regressions for HTML delivery."""

import base64
import contextlib
import copy
import hashlib
import html
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import urllib.request  # noqa: F401  Path.as_uri imports it lazily; keep platform patches from breaking that import.
import webbrowser
from pathlib import Path
from unittest import mock

import render_report
from render_report import ASSETS, HISTORICAL_PREFIX, cells, open_report, phase_plan, render


REPORT = """# Example validation

## 1. Verdict
**Ready.** Confidence: 75% (subjective, not a measured probability).

## 2. PLAN comparison
| Dimension | Original /10 | Revised /10 | Reason / evidence |
|---|---|---|---|
| Correctness and spec fit | 4 | 9 | Corrected interface. |
| Security and privacy | 8 | 9 | Checked access boundary. |
| Performance | 9 | 9 | Unchanged. |
| Maintainability and complexity | 8 | 9 | Kept existing components. |
| Execution and verification readiness | 2 | 9 | Fixed command. |
| **Average /10** | **6.2** | **9.0** | |

## 3. SPEC comparison
| Dimension | Original /10 | Revised /10 | Reason / evidence |
|---|---|---|---|
| Clarity and testability | 7 | 9 | Clarified error. |
| Correctness against the code | 8 | 9 | Verified reference. |
| Security and privacy | 9 | 9 | Unchanged. |
| Scope and simplicity | 9 | 9 | Unchanged. |
| Rollout, rollback and measurement | 5 | 9 | Defined rollback. |
| **Average /10** | **7.6** | **9.0** | |

## 4. Decision confidence
Subjective estimates, not measured probabilities.
| Decision | Confidence | Evidence | Remaining uncertainty |
|---|---|---|---|
| Readiness | 75% | Recorded focused check | No browser check |

## 5. Changes
- A corrected assertion within Task 2.
  - No new requirement.

## 6. Open items
No blockers. Browser verification runs during implementation.

## 7. Verification and checkout
Recorded focused check; no production run.

## 8. Fresh-session handoff
```text
Implement the approved scope now.
Keep Persian text: «سلام» and literal <code> & "quotes".
Run /code-review and /security-review; fix confirmed findings before each PR.
Squash into the plan branch after green checks. Ask before the normal main merge.
Stop at the end of Phase 1; it is the last phase.
```
"""

# Version 1-3 output is frozen: these digests must never be re-pinned in a later task.
# A mismatch means legacy output changed and the renderer must be fixed instead.
# The fixtures are literal on purpose: later tasks edit REPORT and the shared helpers.
LEGACY_REPORT = """# Example validation

## 1. Verdict
**Ready.** Confidence: 75% (subjective, not a measured probability).

## 2. PLAN comparison
| Dimension | Original /10 | Revised /10 | Reason / evidence |
|---|---|---|---|
| Correctness and spec fit | 4 | 9 | Corrected interface. |
| Security and privacy | 8 | 9 | Checked access boundary. |
| Performance | 9 | 9 | Unchanged. |
| Maintainability and complexity | 8 | 9 | Kept existing components. |
| Execution and verification readiness | 2 | 9 | Fixed command. |
| **Average /10** | **6.2** | **9.0** | |

## 3. SPEC comparison
| Dimension | Original /10 | Revised /10 | Reason / evidence |
|---|---|---|---|
| Clarity and testability | 7 | 9 | Clarified error. |
| Correctness against the code | 8 | 9 | Verified reference. |
| Security and privacy | 9 | 9 | Unchanged. |
| Scope and simplicity | 9 | 9 | Unchanged. |
| Rollout, rollback and measurement | 5 | 9 | Defined rollback. |
| **Average /10** | **7.6** | **9.0** | |

## 4. Decision confidence
Subjective estimates, not measured probabilities.
| Decision | Confidence | Evidence | Remaining uncertainty |
|---|---|---|---|
| Readiness | 75% | Recorded focused check | No browser check |

## 5. Changes
- A corrected assertion within Task 2.
  - No new requirement.

## 6. Open items
No blockers. Browser verification runs during implementation.

## 7. Verification and checkout
Recorded focused check; no production run.

## 8. Fresh-session handoff
```text
Implement the approved scope now.
Keep Persian text: «سلام» and literal <code> & "quotes".
Run /code-review and /security-review; fix confirmed findings before each PR.
Squash into the plan branch after green checks. Ask before the normal main merge.
Stop at the end of Phase 1; it is the last phase.
```
"""

LEGACY_DIGESTS = {
    "v1": "2d5c728c940bc6303005eaabfe0413369738017739c4c8038b84bea861b278c8",
    "v2": "86d7e88a2693aac976f22ae5d4bcd60e636560ccb44fa5189a11611bdb460704",
    "v3": "0c49b2b29f35381d345767851b829088bcd88db9837c22397403538af9875831",
    "v3-two-phases": "e53737dd42ef4a46b72db044b176be6a1d3f3abcc2fdaf0658eff8fee43342c5",
    "v3-remediation": "98343b82185019953506ff7d0f33465ee2dd7d1e6d4ba41776b0f397dc7a8773",
    "v3-historical": "59722184cc8bf4408274819d760d3bece1eb94ddaf2ec99ffe4fbd809a6bc7f9",
}


ZONES_DIAGRAM = {
    "kind": "zones",
    "eyebrow": "Architecture · planned",
    "title": "Who talks to whom",
    "description": "The caller asks the retry helper, which sends requests to the remote API.",
    "caption": "The helper waits between tries.",
    "zones": [
        {"label": "Your app", "nodes": [
            {"id": "caller", "title": "Caller", "sub": "asks for a request"},
            {"id": "helper", "title": "Retry helper", "sub": "waits, then tries again"},
        ], "chain": True},
        {"label": "Remote service", "nodes": [
            {"id": "api", "title": "API endpoint", "sub": "may answer 503"},
        ]},
    ],
    "links": [
        {"from": "helper", "to": "api", "label": "request", "sub": "HTTPS"},
        {"from": "api", "to": "helper", "label": "result"},
    ],
}


# Version 4 saved output is frozen too: these digests are never re-pinned. Saved version 4 reports keep
# their rerun card, held prompts and run-counting drift warning after version 5 drops them for new reports.
# Like the legacy fixtures, these are literal copies, so later edits to REPORT, ZONES_DIAGRAM, run_first,
# rerun_yes or stop_rerun cannot change them.
V4_FROZEN_REPORT = """# Example validation

## 1. Verdict
**Ready.** Confidence: 75% (subjective, not a measured probability).

## 2. PLAN comparison
| Dimension | Original /10 | Revised /10 | Reason / evidence |
|---|---|---|---|
| Correctness and spec fit | 4 | 9 | Corrected interface. |
| Security and privacy | 8 | 9 | Checked access boundary. |
| Performance | 9 | 9 | Unchanged. |
| Maintainability and complexity | 8 | 9 | Kept existing components. |
| Execution and verification readiness | 2 | 9 | Fixed command. |
| **Average /10** | **6.2** | **9.0** | |

## 3. SPEC comparison
| Dimension | Original /10 | Revised /10 | Reason / evidence |
|---|---|---|---|
| Clarity and testability | 7 | 9 | Clarified error. |
| Correctness against the code | 8 | 9 | Verified reference. |
| Security and privacy | 9 | 9 | Unchanged. |
| Scope and simplicity | 9 | 9 | Unchanged. |
| Rollout, rollback and measurement | 5 | 9 | Defined rollback. |
| **Average /10** | **7.6** | **9.0** | |

## 4. Decision confidence
Subjective estimates, not measured probabilities.
| Decision | Confidence | Evidence | Remaining uncertainty |
|---|---|---|---|
| Readiness | 75% | Recorded focused check | No browser check |

## 5. Changes
- A corrected assertion within Task 2.
  - No new requirement.

## 6. Open items
No blockers. Browser verification runs during implementation.

## 7. Verification and checkout
Recorded focused check; no production run.

## 8. Fresh-session handoff
```text
Implement the approved scope now.
Keep Persian text: «سلام» and literal <code> & "quotes".
Run /code-review and /security-review; fix confirmed findings before each PR.
Squash into the plan branch after green checks. Ask before the normal main merge.
Stop at the end of Phase 1; it is the last phase.
```
"""

V4_FROZEN_RUN_FIRST_TEXT = "Run validation again first, with the re-run prompt in the Summary; start a phase only after that run."

V4_FROZEN_RERUN_PROMPT = ("/plan-validation:validate-plan PLAN: `/data/PLAN.md` SPEC: `/data/SPEC.md` FOCUS: Run validation again "
                          "(run 2 of 3). Previous report: `/data/run-1/report.md`. Run this before starting any phase. "
                          "Focus on the delay cap. Do not start dependent implementation.")

V4_FROZEN_DIAGRAM = {
    "kind": "zones",
    "eyebrow": "Architecture · planned",
    "title": "Who talks to whom",
    "description": "The caller asks the retry helper, which sends requests to the remote API.",
    "caption": "The helper waits between tries.",
    "zones": [
        {"label": "Your app", "nodes": [
            {"id": "caller", "title": "Caller", "sub": "asks for a request"},
            {"id": "helper", "title": "Retry helper", "sub": "waits, then tries again"},
        ], "chain": True},
        {"label": "Remote service", "nodes": [
            {"id": "api", "title": "API endpoint", "sub": "may answer 503"},
        ]},
    ],
    "links": [
        {"from": "helper", "to": "api", "label": "request", "sub": "HTTPS"},
        {"from": "api", "to": "helper", "label": "result"},
    ],
}

V4_FROZEN_CONTEXT = {
    "title": "Example", "validation_date": "2026-10-14", "kind": "saved",
    "review_status": "complete", "handoff_status": "current", "summary": "The approved scope is ready.",
    "freshness": "Branch and base checked; recorded tests were not repeated.",
    "scope": {"explanation": "Same scope.", "approval": "No expansion.", "rows": [
        {"metric": metric, "original": "1", "revised": "1", "reason": "Unchanged."}
        for metric in ("Delivery phases", "Implementation tasks", "Supporting tasks", "Numbered tasks", "Dependencies / services")
    ]},
    "format_version": 4,
    "project": "plan-validation", "audience": "plan review for the maintainer", "title_accent": "Example",
    "task_inventory": ["1"],
    "phases": [{"id": "1", "title": "Example", "tasks": ["1"], "docs_only": False, "security_review": False, "status": "ready"}],
    "diagrams": [V4_FROZEN_DIAGRAM],
    "open_decisions": [],
    "watch_list": [],
    "decisions_without_reply": [],
    "validation_run": {"number": 1, "plan_key": "PLAN.md", "scope": "full"},
    "rerun": {"recommendation": "no", "reasons": ["Nothing is left that validation can fix."]},
}

V4_SAVED_DIGESTS = {
    "v4-no": "fc27c4300559e6217d50b40359bf0729365987cc8c4ee6dcc560b70ed3115c4d",
    "v4-yes-held": "f881f1d391a5024893a42f8152ab55aeb821e462799067f285d79904db64f9e6",
    "v4-stop-historical": "90f9552dd75a324cf80d6ef6b4ee291113279d9a65385a8dd3624aee3322a437",
    "v4-drift": "e2acc92c58e2391e757540b8a347477e9a4c5cbe91dd87b3b483b8f69c08f23e",
}


def run_first(source):
    """Add the line section 8 says before its prompts while a rerun yes holds a Ready report's phases."""
    return source.replace("## 8. Fresh-session handoff\n", "## 8. Fresh-session handoff\n" + render_report.RUN_FIRST_TEXT + "\n\n", 1)


def normalized(page, root):
    return re.sub(r"HTML generated \S+\.", "HTML generated X.", page.replace(root, "ROOT"))


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        documents = []
        for label in ("PLAN", "SPEC"):
            path = root / f"{label}.md"
            path.write_text(label)
            documents.append({"label": label, "path": str(path), "sha256": hashlib.sha256(label.encode()).hexdigest()})
        self.context = {
            "title": "Example", "validation_date": "2026-10-14", "kind": "saved",
            "review_status": "complete", "handoff_status": "current", "summary": "The approved scope is ready.",
            "freshness": "Branch and base checked; recorded tests were not repeated.",
            "documents": documents,
            "scope": {"explanation": "Same scope.", "approval": "No expansion.", "rows": [
                {"metric": metric, "original": "1", "revised": "1", "reason": "Unchanged."}
                for metric in ("Delivery phases", "Implementation tasks", "Supporting tasks", "Numbered tasks", "Dependencies / services")
            ]},
        }

    def modern_context(self):
        """The current new-report context: version 5."""
        return self.v5_context()

    def v4_context(self, kind="saved"):
        """A version 4 context with its run fields. An explicit copy, so modern_context() can change."""
        context = copy.deepcopy(self.context)
        context.update({
            "format_version": 4, "kind": kind,
            "project": "plan-validation", "audience": "plan review for the maintainer", "title_accent": "Example",
            "task_inventory": ["1"],
            "phases": [{"id": "1", "title": "Example", "tasks": ["1"], "docs_only": False, "security_review": False, "status": "ready"}],
            "diagrams": [copy.deepcopy(ZONES_DIAGRAM)],
            "open_decisions": [],
            "watch_list": [],
            "decisions_without_reply": [],
            "validation_run": {"number": 1, "plan_key": "PLAN.md", "scope": "full"},
            "rerun": {"recommendation": "no", "reasons": ["Nothing is left that validation can fix."]},
        })
        return context

    def v5_context(self):
        """A new version 5 context: version 4 without the run fields. Never built from modern_context()."""
        context = self.v4_context("new")
        del context["validation_run"], context["rerun"]
        context["format_version"] = 5
        return context

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

    def stop_rerun(self, context):
        """A Not ready report fires a re-run trigger, so it cannot recommend no."""
        context["rerun"] = {"recommendation": "stop", "reasons": ["The blocker needs the maintainer's decision."]}
        return context

    def pending_d1(self, source, context):
        """Name one pending decision, D1, in section 6 and the context."""
        context["open_decisions"] = [{"id": "D1", "question": "Approve the paid service?", "recommendation": "Approve it.",
                                      "confidence": "High", "holds_back": "Phase 1"}]
        return source.replace("No blockers.", "Pending approval D1: adding a paid service."), context

    def phase_1_waits(self, source, context, decision="D1"):
        """Make the only phase wait for a decision; section 8 then holds one prompt that starts nothing."""
        context["phases"][0].update(status="waiting", waits_for=decision)
        return source.split("## 8.")[0] + (
            f"## 8. Fresh-session handoff\n```text\nRecord {decision}, then re-render the report. "
            "Do not start dependent implementation.\n```\n"), context

    def test_feature_diagram_precedes_scores_without_replacing_evidence(self):
        page, prompt, current, _ = render(REPORT, self.v3_saved_context())
        self.assertTrue(current)
        self.assertIn('aria-labelledby="feature-heading"', page)
        self.assertIn("Feature at a glance", page)
        self.assertIn('<ol class="feature-flow" role="list">', page)
        self.assertLess(page.index('id="feature-overview"'), page.index('id="section-1"'))
        for title in ("Choose a document", "Check access", "Show the result"):
            self.assertIn(title, page)
        self.assertEqual(page.count('aria-labelledby="heading-'), 8)
        self.assertEqual(page.count("<strong>Average /10</strong>"), 2)
        self.assertEqual(prompt, REPORT.split("```text\n")[1].split("\n```")[0])

    def test_modern_report_requires_a_complete_three_to_seven_block_diagram(self):
        for feature in (None, {}, {"summary": "Flow", "steps": []},
                        {"summary": "Flow", "steps": [{"title": "A", "description": "B"}] * 8},
                        {"summary": "Flow", "steps": [{"title": "A"}] * 3},
                        {"summary": "", "steps": [{"title": "A", "description": "B"}] * 3}):
            with self.subTest(feature=feature):
                context = self.v3_saved_context()
                context["feature"] = feature
                with self.assertRaisesRegex(ValueError, "Feature"):
                    render(REPORT, context)

    def test_independent_feature_blocks_do_not_imply_a_sequence(self):
        context = self.v3_saved_context()
        context["feature"]["layout"] = "blocks"
        page, _, _, _ = render(REPORT, context)
        overview = page[page.index('<section id="feature-overview"'):page.index('<section id="section-1"')]
        self.assertIn('<ul class="feature-blocks" role="list">', overview)
        self.assertNotIn('<ol', overview)
        self.assertNotIn('class="step-arrow"', overview)
        self.assertIn("Check access", overview)

    def test_unknown_feature_layout_is_rejected(self):
        context = self.v3_saved_context()
        context["feature"]["layout"] = "unknown"
        with self.assertRaisesRegex(ValueError, "layout"):
            render(REPORT, context)

    def test_technical_details_collapse_but_summary_and_blockers_stay_visible(self):
        source = REPORT.replace("Recorded focused check; no production run.",
                                "Two local checks passed. No production run.\n\n### Technical details\n"
                                "```bash\npython3 checks.py\n```\nExit 0; two checks passed.")
        page, _, _, _ = render(source, self.modern_context())
        details = re.search(r'<details class="technical-details">(.*?)</details>', page, re.S)
        self.assertIsNotNone(details)
        self.assertIn("python3 checks.py", details[1])
        self.assertNotIn("Two local checks passed.", details[1])
        self.assertNotIn("No blockers.", details[1])
        self.assertIn("Two local checks passed.", page)

    def test_score_tables_open_items_and_handoff_cannot_be_collapsed(self):
        for heading in ("PLAN comparison", "SPEC comparison", "Open items", "Fresh-session handoff"):
            with self.subTest(heading=heading):
                source = REPORT.replace(heading + "\n", heading + "\nSummary.\n\n### Technical details\n")
                with self.assertRaisesRegex(ValueError, "Technical details"):
                    render(source, self.modern_context())

    def test_detail_marker_in_a_code_block_is_not_a_disclosure(self):
        source = REPORT.replace("Recorded focused check; no production run.",
                                "A literal example:\n```text\n### Technical details\n```\n")
        page, _, _, _ = render(source, self.modern_context())
        self.assertNotIn('<details class="technical-details">', page)
        self.assertIn("### Technical details", page)

    def test_details_require_a_visible_summary(self):
        source = REPORT.replace("Recorded focused check; no production run.",
                                "### Technical details\nOnly hidden evidence.")
        with self.assertRaisesRegex(ValueError, "visible summary"):
            render(source, self.modern_context())

    def test_defaulted_choices_end_the_report_without_claiming_approval(self):
        context = self.modern_context()
        context["decisions_without_reply"] = [{
            "question": "How much detail?", "decision": "Use a concise summary.",
            "reason": "The user requested a quick overview.",
        }]
        source = REPORT.replace("No blockers.", "Approval pending: adding a paid service. No blockers.")
        page, _, _, _ = render(source, context)
        self.assertIn("Decisions made without your reply", page)
        self.assertIn("Use a concise summary.", page)
        self.assertIn("The user requested a quick overview.", page)
        self.assertIn("not user approval", page)
        self.assertLess(page.index('id="section-8"'), page.index('id="defaulted-decisions"'))
        self.assertIn("Approval pending: adding a paid service.", page)

    def test_missing_or_incomplete_default_decisions_are_rejected(self):
        for decisions in (None, "None", [{"question": "Q", "decision": "D"}],
                          [{"question": "Q", "decision": "D", "reason": ""}]):
            context = self.modern_context()
            context["decisions_without_reply"] = decisions
            with self.subTest(decisions=decisions), self.assertRaisesRegex(ValueError, "Decisions"):
                render(REPORT, context)

    def test_feature_and_decision_text_cannot_inject_markup(self):
        context = self.v3_saved_context()
        payload = '<img src=x onerror="alert(1)"><script>alert(2)</script>'
        context["feature"]["summary"] = payload
        context["feature"]["steps"][0]["title"] = payload
        context["feature"]["steps"][0]["description"] = payload
        context["decisions_without_reply"] = [{"question": payload, "decision": payload, "reason": payload}]
        page, _, _, _ = render(REPORT, context)
        self.assertNotIn("<img src=x", page)
        self.assertNotIn("<script>alert", page)
        self.assertIn("&lt;img", page)
        self.assertEqual(page.count("<script>"), 1)

    def test_new_handoffs_are_short_while_legacy_handoffs_remain_readable(self):
        source = REPORT.replace("Implement the approved scope now.", "Implement " + "detail " * 81)
        with self.assertRaisesRegex(ValueError, "80 words"):
            render(source, self.modern_context())
        self.context["kind"] = "saved"
        _, prompt, _, _ = render(source, self.context)
        self.assertIn("detail " * 81, prompt)

    def test_unknown_report_format_is_rejected(self):
        context = self.modern_context()
        context["format_version"] = 99
        with self.assertRaisesRegex(ValueError, "format_version"):
            render(REPORT, context)

    def test_new_report_cannot_fall_back_to_legacy_format(self):
        context = self.modern_context()
        del context["format_version"]
        with self.assertRaisesRegex(ValueError, "format_version"):
            render(REPORT, context)
        context["format_version"] = 1
        with self.assertRaisesRegex(ValueError, "format_version"):
            render(REPORT, context)

    def test_not_ready_rejects_an_implementation_instruction_anywhere(self):
        source = REPORT.replace("**Ready.**", "**Not ready.**").replace(
            "Implement the approved scope now.",
            "Work in /repo. Implement all validated phases. Do not start dependent implementation.")
        with self.assertRaisesRegex(ValueError, "remediation prompt"):
            render(source, self.modern_context())

    def test_not_ready_rejects_line_and_list_implementation_instructions(self):
        for instruction in ("Fix the cap.\nImplement Task 2.", "- Implement Task 2.", "Then implement Task 2."):
            source = REPORT.replace("**Ready.**", "**Not ready.**").replace(
                "Implement the approved scope now.", instruction + "\nDo not start dependent implementation.")
            with self.subTest(instruction=instruction), self.assertRaisesRegex(ValueError, "remediation prompt"):
                render(source, self.modern_context())
        source = REPORT.replace("**Ready.**", "**Not ready.**").replace(
            "Implement the approved scope now.", "Do not implement Task 2. Do not start dependent implementation.")
        self.assertIn("Copy remediation prompt", render(source, self.modern_context())[0])

    def test_v4_remediation_prompt_rejects_every_implement_form(self):
        not_ready = REPORT.replace("**Ready.**", "**Not ready.**")
        for instruction in ("Start implementing Phase 1.", "The fix implements Task 2.",
                            "Fix `/repo/a\nStart implementing Phase 1 now.md`.", "Keep D1 or not\nImplement Phase 1.",
                            "Reimplement Phase 1.", "Keep D1 or not\u2028Implement Phase 1.", "Keep D1 or not\rImplement Phase 1.",
                            "Run `/feature-dev:implement` for Phase 1.", "Run `/implement` now.", "Run `/x:implement/` now.",
                            "Run `/implement/` now.", "Run `/feature-dev:implement.md` now.", "Fix `/repo/x Implement Phase 1 now`.",
                            "Run `/implement /home/u/plan.md` now.", "Run `/implement docs/plan.md` now.",
                            "Fix `/repo/ Implement Phase 1 now.md`.", "Read `/repo/plan.md`implement it.",
                            "Fix `/home/u/My Repo/x implement now.md`.", "Read `/x/y not` Implement Phase 1.",
                            "Read `/repo/plan.md then implement.`", "Use `/implement/ /repo/plan.md` now."):
            source = not_ready.replace("Implement the approved scope now.", instruction + " Do not start dependent implementation.")
            with self.subTest(instruction=instruction), self.assertRaisesRegex(ValueError, "remediation prompt"):
                render(source, self.modern_context())
        # A quoted path, a curly or tabbed negation and a wrapped sentence are not instructions,
        # and a saved re-render accepts and rejects exactly what the new report did.
        source = not_ready.replace("Implement the approved scope now.",
                                   "Fix `/repo/implementing/plan.md`. Don’t implement Task 2. Do not\timplement Task 3. "
                                   "Do not\u00a0reimplement Task 4. Never re-implement Task 5. Do not start dependent\n  implementation.")
        saved = self.modern_context()
        saved["kind"] = "saved"
        for context in (self.modern_context(), saved):
            self.assertIn("Copy remediation prompt", render(source, context)[0])
        with self.assertRaisesRegex(ValueError, "remediation prompt"):
            render(not_ready.replace("Implement the approved scope now.", "Start implementing Phase 1. Do not start dependent implementation."), saved)

    def test_quoted_absolute_paths_are_names_not_instructions(self):
        not_ready = REPORT.replace("**Ready.**", "**Not ready.**")
        for path in ("`/implement.md`", "`/repo/implement`", "`~/implement`", "`C:\\implement\\plan.md`", "`/repo/docs/`"):
            source = not_ready.replace("Implement the approved scope now.", f"Read {path}. Do not start dependent implementation.")
            with self.subTest(path=path):
                render(source, self.modern_context())
        # A quoted span with spaces is text, except a document path the report records exactly.
        context = self.modern_context()
        plan = Path(self.directory.name) / "My Repo" / "implement-retry.md"
        plan.parent.mkdir()
        plan.write_text("PLAN")
        context["documents"][0]["path"] = str(plan)
        render(not_ready.replace("Implement the approved scope now.", f"Read `{plan}`. Do not start dependent implementation."), context)
        for other in ("`/home/u/My Repo/docs/plans/implement-retry.md`", f"`{plan}.bak`"):
            source = not_ready.replace("Implement the approved scope now.", f"Read {other}. Do not start dependent implementation.")
            with self.subTest(other=other), self.assertRaisesRegex(ValueError, "remediation prompt"):
                render(source, context)

    def test_quoted_path_with_spaces_counts_each_word(self):
        # Version 4 counts a quoted span with spaces as text, unless it is a recorded document path.
        self.assertEqual(render_report.word_count("Work in `/Users/Jane Doe/my repo`."), 5)
        self.assertEqual(render_report.word_count("Work in `/Users/Jane Doe/my repo`.", 4, {"/Users/Jane Doe/my repo"}), 3)
        self.assertEqual(render_report.word_count("`/a/b " + "w/ " * 100 + "c/d`"), 102)
        self.assertEqual(render_report.word_count("`/repo/plan.md and then do whatever you want`"), 7)
        # Saved version 1-3 reports keep their rule: any quoted absolute path is one word.
        self.assertEqual(render_report.word_count("Work in `/Users/Jane Doe/my repo`.", 3), 3)
        source = REPORT.replace("Implement the approved scope now.", "Run `/a/b " + "detail " * 80 + "z.md` now.")
        with self.assertRaisesRegex(ValueError, "80 words"):
            render(source, self.modern_context())

    def test_quoted_slash_command_counts_every_word(self):
        # Version 4 counts a quoted command's words; only a quoted path counts as one word.
        command = "`/feature-dev:implement " + "detail " * 80 + "`"
        source = REPORT.replace("Implement the approved scope now.", f"Run {command} now.")
        with self.assertRaisesRegex(ValueError, "80 words"):
            render(source, self.modern_context())

    def test_backticks_around_prose_do_not_bypass_the_word_limit(self):
        source = REPORT.replace("Implement the approved scope now.", "`" + "detail " * 81 + "` now.")
        with self.assertRaisesRegex(ValueError, "80 words"):
            render(source, self.modern_context())

    def test_backtick_quoted_paths_count_as_one_word(self):
        path = "`/Users/x/My-Projects/" + "deep-folder/" * 40 + "plan.md`"
        source = REPORT.replace("Implement the approved scope now.", f"Implement the plan in {path} now.")
        _, prompt, _, _ = render(source, self.modern_context())
        self.assertIn(path, prompt)

    def test_hidden_section_four_tables_do_not_replace_the_visible_confidence_table(self):
        extra = "\n\n### Technical details\n| Command | Exit |\n|---|---|\n| checks.py | 0 |\n"
        source = REPORT.replace("| Readiness | 75% | Recorded focused check | No browser check |",
                                "| Readiness | 75% | Recorded focused check | No browser check |" + extra)
        page, _, _, _ = render(source, self.modern_context())
        self.assertIn("checks.py", page)
        table = "| Decision | Confidence | Evidence | Remaining uncertainty |\n|---|---|---|---|\n| Readiness | 75% | Recorded focused check | No browser check |"
        hidden = REPORT.replace(table, "### Technical details\n" + table)
        with self.assertRaisesRegex(ValueError, "Decision confidence"):
            render(hidden, self.modern_context())

    def test_confidence_table_is_found_after_other_tables_and_code(self):
        prefix = "| Summary | Value |\n|---|---|\n| Checks | 2 |\n\n```text\n| not | a | table |\n```\n\n"
        source = REPORT.replace("| Decision | Confidence |", prefix + "| Decision | Confidence |")
        page, _, _, _ = render(source, self.modern_context())
        self.assertIn("Recorded focused check", page)

    def test_legacy_confidence_table_validation_is_unchanged(self):
        source = REPORT.replace("| Readiness | 75% | Recorded focused check | No browser check |",
                                "| Readiness | 75% | Recorded focused check | No browser check |\n\n| Extra | Table |\n|---|---|")
        with self.assertRaisesRegex(ValueError, "Decision confidence"):
            render(source, self.context)

    def test_verdict_confidence_must_be_visible(self):
        source = REPORT.replace("**Ready.** Confidence: 75% (subjective, not a measured probability).",
                                "**Ready.** Main limit: no browser check.\n\n### Technical details\nConfidence: 75%.")
        with self.assertRaisesRegex(ValueError, "Confidence"):
            render(source, self.modern_context())

    def test_long_feature_flow_stacks_vertically(self):
        context = self.v3_saved_context()
        context["feature"]["steps"] = [{"title": f"Step {n}", "description": "Does one thing."} for n in range(7)]
        page, _, _, _ = render(REPORT, context)
        self.assertIn('<ol class="feature-flow vertical" role="list">', page)

    def test_modern_report_requires_the_contract_section_headings(self):
        source = REPORT.replace("## 2. PLAN comparison", "## 2. SPEC comparison", 1)
        with self.assertRaisesRegex(ValueError, "heading"):
            render(source, self.modern_context())

    def test_detail_marker_tolerates_crlf_and_casing(self):
        for marker in ("### Technical details", "### technical Details"):
            source = REPORT.replace("Recorded focused check; no production run.",
                                    f"Summary.\n\n{marker}\nExit 0.").replace("\n", "\r\n")
            with self.subTest(marker=marker):
                page, _, _, _ = render(source, self.modern_context())
                self.assertIn('<details class="technical-details">', page)
        source = REPORT.replace("No blockers.", "Summary.\r\n\r\n### technical details\r\nHidden blocker.")
        with self.assertRaisesRegex(ValueError, "Technical details"):
            render(source, self.modern_context())

    def test_modern_historical_handoff_is_called_historical(self):
        context = self.modern_context()
        context["handoff_status"] = "historical"
        page, _, _, _ = render(REPORT, context)
        pills = page[page.index('<ul class="pills"'):page.index('</ul>', page.index('<ul class="pills"'))]
        self.assertIn("Historical", pills)

    def test_complete_report_preserves_prompt_and_both_tables(self):
        page, prompt, current, _ = render(REPORT, self.context)
        self.assertTrue(current)
        self.assertEqual(prompt, REPORT.split("```text\n")[1].split("\n```")[0])
        for number in range(1, 9):
            self.assertIn(f'id="section-{number}"', page)
        self.assertEqual(page.count("<strong>Average /10</strong>"), 2)
        self.assertIn('id="copy-prompt"', page)
        self.assertIn("6.2 <i>→</i> 9.0", page)
        self.assertIn("7.6 <i>→</i> 9.0", page)

    def test_report_embeds_the_favicon_as_an_inline_image(self):
        page, _, _, _ = render(REPORT, self.context)
        href = re.search(r'<link rel="icon" type="image/svg\+xml" href="data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)">', page)
        self.assertIsNotNone(href)
        self.assertEqual(base64.b64decode(href.group(1)), (ASSETS / "favicon.svg").read_bytes())
        self.assertIn("img-src data:", page)

    def test_incorrect_average_cannot_be_delivered(self):
        with self.assertRaisesRegex(ValueError, "average"):
            render(REPORT.replace("**6.2**", "**8.0**"), self.context)

    def test_missing_score_row_and_missing_section_are_errors(self):
        for source in (REPORT.replace("| Performance | 9 | 9 | Unchanged. |\n", ""),
                       REPORT.replace("## 7. Verification and checkout", "### 7. Verification and checkout")):
            with self.assertRaises(ValueError):
                render(source, self.context)

    def test_unknown_score_keeps_unknown_average(self):
        source = REPORT.replace("| Performance | 9 | 9 |", "| Performance | Unknown | 9 |")
        with self.assertRaisesRegex(ValueError, "average"):
            render(source, self.context)
        page, _, _, _ = render(source.replace("**6.2**", "**Unknown**"), self.context)
        self.assertIn("Unknown <i>→</i> 9.0", page)

    def test_ready_cannot_precede_reviewer_completion(self):
        for status in ("running", "not_run", None):
            self.context["review_status"] = status
            with self.assertRaisesRegex(ValueError, "cold read"):
                render(REPORT, self.context)

    def test_changed_or_missing_document_disables_start_button(self):
        plan = Path(self.context["documents"][0]["path"])
        plan.write_text("Revised after validation")
        page, prompt, current, _ = render(REPORT, self.context)
        self.assertFalse(current)
        self.assertNotIn('id="copy-prompt"', page)
        self.assertNotIn('href="handoff.txt"', page)
        self.assertTrue(prompt.startswith("HISTORICAL PROMPT — DO NOT EXECUTE."))
        self.assertIn("historical prompt", page)
        plan.unlink()
        self.assertFalse(render(REPORT, self.context)[2])

    def test_saved_report_is_labeled_recorded(self):
        self.context["kind"] = "saved"
        page, _, _, _ = render(REPORT, self.context)
        self.assertIn("Saved validation", page)
        self.assertIn("Recorded: Ready", page)

    def test_git_or_approval_drift_can_disable_handoff_with_matching_files(self):
        self.context["handoff_status"] = "historical"
        page, prompt, current, _ = render(REPORT, self.context)
        self.assertFalse(current)
        self.assertIn("Document fingerprints match", page)
        self.assertNotIn('href="handoff.txt"', page)
        self.assertNotIn('id="copy-prompt"', page)
        self.assertTrue(prompt.startswith("HISTORICAL PROMPT"))

    def test_numbered_headings_and_code_fences_inside_prompt_are_content(self):
        source = REPORT.replace("```text\n", "````text\n## 1. Follow these steps\n```bash\nprintf hello\n```\n")
        source = source.rsplit("```", 1)[0] + "````\n"
        page, prompt, _, _ = render(source, self.context)
        self.assertIn("## 1. Follow these steps", prompt)
        self.assertIn("```bash", prompt)
        self.assertEqual(page.count('aria-labelledby="heading-'), 8)

    def test_missing_outer_fence_never_truncates_handoff_at_inner_fence(self):
        source = REPORT.replace("```text\n", "````text\n```bash\nprintf hello\n```\n")
        source = source.rsplit("```", 1)[0]
        with self.assertRaisesRegex(ValueError, "Unclosed fenced"):
            render(source, self.context)

    def test_report_content_cannot_inject_active_html_or_script(self):
        payload = '<img src=x onerror="alert(1)"><script>alert(2)</script>'
        self.context["title"] = payload
        self.context["scope"]["rows"][0]["reason"] = payload
        source = REPORT.replace("No blockers.", payload + ' [unsafe](javascript:alert) [safe](https://example.org/docs) No blockers.')
        source = source.replace("Keep Persian text:", '</pre></script><script>alert(3)</script> Keep Persian text:')
        page, prompt, _, _ = render(source, self.context)
        self.assertNotIn("<img src=x", page)
        self.assertNotIn("<script>alert", page)
        self.assertNotIn('href="javascript:', page)
        self.assertIn('href="https://example.org/docs"', page)
        self.assertIn("&lt;img", page)
        self.assertIn("</pre></script>", prompt)
        self.assertEqual(page.count("<script>"), 1)

    def test_scope_counts_are_required_but_unknown_is_honest(self):
        context = copy.deepcopy(self.context)
        context["scope"]["rows"].pop()
        with self.assertRaisesRegex(ValueError, "Scope comparison"):
            render(REPORT, context)
        self.context["scope"]["rows"][0]["original"] = "Unknown"
        self.assertIn("Unknown", render(REPORT, self.context)[0])

    def test_table_pipes_inside_code_do_not_split_cells(self):
        self.assertEqual(cells(r"| `A | B` | 9 | a \| b |"), ["`A | B`", "9", "a | b"])

    def test_remediation_report_does_not_require_successful_review(self):
        self.context["review_status"] = "blocked"
        source = REPORT.replace("**Ready.**", "**Not ready.**")
        with self.assertRaisesRegex(ValueError, "remediation prompt"):
            render(source, self.context)
        source = source.replace("Implement the approved scope now.", "Resume validation. Do not start dependent implementation.")
        page, _, _, _ = render(source, self.context)
        self.assertIn("Copy remediation prompt", page)

    def test_dependency_comparison_preserves_full_report_and_decision_handoff(self):
        comparison = """### Dependency and alternatives
| Approach | Identity/version | Benefit and risk | Evidence and effort |
|---|---|---|---|
| Original | Fixture helper 1.0 | Unknown publisher; do not execute | Local fixture, 2026-10-14; external research denied |
| Keep existing | Standard library | No new package; existing tests cover the requirement | Local fixture, 2026-10-14; no migration |

D1: Pending. Recommendation: keep existing. Decision confidence: Medium.
"""
        decision = "D1 pending; dependent Task 2 waits. Task 1 may continue. Research denied; no lookup, installation or service enablement authorized."
        source = REPORT.replace("**Ready.**", "**Not ready.**")
        source = source.replace("| Readiness | 75% | Recorded focused check | No browser check |",
                                "| Readiness | Unknown | Fixture evidence only | D1 unresolved |\n"
                                "| D1 | Medium | Verified local fixture, 2026-10-14 | Unknown upstream identity; lookup denied |")
        source = source.replace("## 6. Open items", comparison + "\n## 6. Open items")
        source = source.replace("No blockers. Browser verification runs during implementation.", decision)
        source = source.replace("Implement the approved scope now.",
                                "Resume validation. Do not start dependent implementation.\n" + decision)
        page, prompt, current, _ = render(source, self.context)
        self.assertTrue(current)
        self.assertEqual(page.count('aria-labelledby="heading-'), 8)
        self.assertEqual(page.count("<strong>Average /10</strong>"), 2)
        self.assertIn('aria-label="Scope comparison"', page)
        self.assertIn("Fixture helper 1.0", page)
        self.assertIn("Keep existing", page)
        self.assertIn("Decision confidence: Medium", page)
        self.assertIn(decision, prompt)
        self.assertEqual(prompt, source.split("```text\n")[1].split("\n```")[0])

    def test_no_dependency_concern_needs_no_menu_or_extra_schema(self):
        source = REPORT.replace("- A corrected assertion within Task 2.",
                                "No dependency change or unresolved choice in the reviewed scope.\n- A corrected assertion within Task 2.")
        page, prompt, current, _ = render(source, self.context)
        self.assertTrue(current)
        self.assertIn("No dependency change or unresolved choice", page)
        self.assertEqual(prompt, REPORT.split("```text\n")[1].split("\n```")[0])


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

    def test_malformed_phase_fields_are_value_errors(self):
        for change in ({"task_inventory": [["1"]]}, {"task_inventory": "1"}, {"phases": [["1"]]},
                       {"phases": [{"id": 1, "title": "x", "tasks": ["1"]}]}, {"phases": "1"}):
            with self.subTest(change=change):
                context = self.modern_context()
                context.update(change)
                with self.assertRaisesRegex(ValueError, "Phase"):
                    phase_plan(context, "Ready")

    def test_new_reports_require_version_5(self):
        for version in (3, 4):
            with self.subTest(version=version):
                context = self.v5_context()
                context["format_version"] = version
                with self.assertRaisesRegex(ValueError, "format_version 5"):
                    render(REPORT, context)
        context = self.v5_context()
        context["format_version"] = 6
        with self.assertRaisesRegex(ValueError, "format_version"):
            render(REPORT, context)
        render(REPORT, self.v4_context())
        render(REPORT, self.v5_context())
        render(REPORT, self.v3_saved_context())

    def test_v4_rejects_feature(self):
        context = self.modern_context()
        context["feature"] = self.v3_saved_context()["feature"]
        with self.assertRaisesRegex(ValueError, "feature"):
            render(REPORT, context)

    def test_v4_header_fields(self):
        for field, limit in (("project", 40), ("audience", 60)):
            for value in (None, 7, "", "   ", "x" * (limit + 1)):
                with self.subTest(field=field, value=value):
                    context = self.modern_context()
                    context[field] = value
                    with self.assertRaisesRegex(ValueError, field):
                        render(REPORT, context)
            context = self.modern_context()
            context[field] = "x" * limit
            render(REPORT, context)
        for title, accent in (("Example", "Missing"), ("Example Example", "Example"), ("Example", ""), ("Example", None),
                              ("Fish & chips", "amp"), ("Fish camp", " ")):
            with self.subTest(title=title, accent=accent):
                context = self.modern_context()
                context.update(title=title, title_accent=accent)
                with self.assertRaisesRegex(ValueError, "title_accent"):
                    render(REPORT, context)

    def test_v4_open_decisions(self):
        decision = {"id": "D1", "question": "Approve the paid service?", "recommendation": "Approve it.",
                    "confidence": "High", "holds_back": "Nothing"}
        source = REPORT.replace("No blockers.", "Pending approval **D1**: adding a paid service.")
        bad = [dict(decision, question="")] + [{k: v for k, v in decision.items() if k != key} for key in decision]
        bad += [dict(decision, confidence="Very high"), dict(decision, id="D9"), dict(decision, id="D(1"), dict(decision, id=1), "D1"]
        for item in bad:
            with self.subTest(item=item):
                context = self.modern_context()
                context["open_decisions"] = [item]
                with self.assertRaisesRegex(ValueError, "decision"):
                    render(source, context)
        context = self.modern_context()
        context["open_decisions"] = [decision]
        with self.assertRaisesRegex(ValueError, "D1"):
            render(source.replace("**D1**", "D10"), context)
        context["open_decisions"] = "None"
        with self.assertRaisesRegex(ValueError, "open_decisions"):
            render(source, context)
        context["open_decisions"] = [decision]
        render(source, context)

    def test_v4_ready_cannot_hold_back_work(self):
        source, context = self.pending_d1(REPORT, self.modern_context())
        with self.assertRaisesRegex(ValueError, "Ready verdict"):
            render(source, context)
        for nothing in (" nothing ", "Nothing.", "**Nothing**", "None", "`none`", "_Nothing_!"):
            with self.subTest(holds_back=nothing):
                context["open_decisions"][0]["holds_back"] = nothing
                render(source, context)
        for blocking in ("Nothing yet", "Phase 1", "None of phase 2 can start"):
            with self.subTest(holds_back=blocking):
                context["open_decisions"][0]["holds_back"] = blocking
                with self.assertRaisesRegex(ValueError, "Ready verdict"):
                    render(source, context)
        render(*self.phase_1_waits(source.replace("**Ready.**", "**Ready after approvals.**"),
                                   self.pending_d1(REPORT, self.modern_context())[1]))

    def test_v4_held_back_work_waits_for_its_decision(self):
        # A decision that holds back Phase 1 while Phase 1 is ready would hand out its implementation prompt.
        source, context = self.pending_d1(REPORT.replace("**Ready.**", "**Ready after approvals.**"), self.modern_context())
        with self.assertRaisesRegex(ValueError, "D1 holds back work"):
            render(source, context)
        # Phase 1 is ready and Phase 2 waits for something else: Phase 1 would still get a prompt.
        two_source, two = self.two_phase()
        two_source, two = self.pending_d1(two_source.replace("**Ready.**", "**Ready after approvals.**"), two)
        two["phases"][1].update(status="waiting", waits_for="D10 and the CI fix")
        two_source = two_source.split("```text\nImplement Phase 2.")[0]
        with self.assertRaisesRegex(ValueError, "D1 holds back work"):
            render(two_source, two)
        two["phases"][1]["waits_for"] = "D1"
        render(two_source, two)
        page, prompt, _, _ = render(*self.phase_1_waits(source, context))
        self.assertIn("Do not start dependent implementation.", prompt)
        self.assertNotIn("Copy Phase 1 prompt", page)

    def test_v4_decision_ids_are_unique(self):
        source = REPORT.replace("No blockers.", "Pending approvals D1 and d1.")
        decision = {"question": "Approve?", "recommendation": "Approve it.", "confidence": "High", "holds_back": "Nothing"}
        for second in ("D1", "d1"):
            with self.subTest(second=second):
                context = self.modern_context()
                context["open_decisions"] = [dict(decision, id="D1"), dict(decision, id=second)]
                with self.assertRaisesRegex(ValueError, "unique"):
                    render(source, context)

    def test_v4_pending_approvals_must_hold_back_work(self):
        # Ready after approvals says something waits; a list where nothing waits contradicts it.
        source, context = self.pending_d1(REPORT.replace("**Ready.**", "**Ready after approvals.**"), self.modern_context())
        context["open_decisions"][0]["holds_back"] = "Nothing."
        with self.assertRaisesRegex(ValueError, "holds back work"):
            render(source, context)

    def test_v4_answer_hint_counts_the_rest(self):
        source = REPORT.replace("No blockers.", "Pending approvals D1, D2 and D3.").replace("**Ready.**", "**Ready after approvals.**")
        decision = {"question": "Approve?", "recommendation": "Approve it.", "confidence": "High"}
        for count, tail in ((2, "· 1 more holds back work"), (3, "· 2 more hold back work")):
            with self.subTest(count=count):
                context = self.modern_context()
                context["open_decisions"] = [dict(decision, id=f"D{n}", holds_back=f"Phase {n}") for n in range(1, count + 1)]
                page, _, _, _ = render(*self.phase_1_waits(source, context, " and ".join(f"D{n}" for n in range(1, count + 1))))
                button = re.search(r'<a class="count" href="#panel-answer" data-open-tab="answer">.*?</a>', page, re.S).group(0)
                self.assertIn("D1 holds back Phase 1 " + tail + " ·", button)

    def test_v4_answer_hint_holds_no_link(self):
        # The count card is a link, and a link inside a link is invalid; the table keeps the link.
        source, context = self.pending_d1(REPORT.replace("**Ready.**", "**Ready after approvals.**"), self.modern_context())
        context["open_decisions"][0]["holds_back"] = "[Phase 1](https://example.com/p1) and **tests**"
        page, _, _, _ = render(*self.phase_1_waits(source, context))
        button = re.search(r'<a class="count" href="#panel-answer" data-open-tab="answer">.*?</a>', page, re.S).group(0)
        self.assertEqual(button.count("<a"), 1)
        self.assertIn("D1 holds back Phase 1 and tests", button)
        self.assertIn('<a href="https://example.com/p1"', self.panel(page, "answer"))

    def test_renderer_runs_with_isolated_python(self):
        # -I drops the script folder from sys.path, so the sibling diagrams module must load by path.
        script = Path(render_report.__file__).resolve()
        result = subprocess.run([sys.executable, "-I", "-B", str(script), "--help"], capture_output=True, text=True,
                                cwd=tempfile.gettempdir(), timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--report", result.stdout)

    def test_v4_watch_list(self):
        item = {"kind": "gap", "title": "No browser check", "body": "The page was not opened in a browser."}
        for bad in ("None", [dict(item, kind="bug")], [dict(item, title="x" * 61)], [dict(item, title="")],
                    [dict(item, body="")], [{"kind": "gap", "title": "No body"}], ["gap"]):
            with self.subTest(bad=bad):
                context = self.modern_context()
                context["watch_list"] = bad
                with self.assertRaisesRegex(ValueError, "watch_list"):
                    render(REPORT, context)
        context = self.modern_context()
        context["watch_list"] = [dict(item, kind=kind, title="x" * 60) for kind in ("gap", "limit", "risk", "fixed")]
        render(REPORT, context)

    def test_v4_pending_approvals_need_decisions(self):
        source = REPORT.replace("**Ready.**", "**Ready after approvals.**")
        with self.assertRaisesRegex(ValueError, "open_decisions"):
            render(source, self.modern_context())
        render(*self.phase_1_waits(*self.pending_d1(source, self.modern_context())))

    def test_v4_text_fields_cannot_inject_markup(self):
        probe = '<script>x</script>"&amp'
        context = self.modern_context()
        context.update(project=probe, audience=probe, title=probe, title_accent="x")
        context["watch_list"] = [{"kind": "risk", "title": probe, "body": probe}]
        source, context = self.pending_d1(REPORT.replace("**Ready.**", "**Ready after approvals.**"), context)
        context["open_decisions"][0].update(question=probe, recommendation=probe, holds_back=probe)
        page, _, _, _ = render(*self.phase_1_waits(source, context))
        self.assertNotIn("<script>x", page)
        self.assertNotIn('"&amp<', page)
        self.assertEqual(page.count("<script>"), 1)
        escaped = "&lt;script&gt;x&lt;/script&gt;&quot;&amp;amp"
        self.assertIn(f'<p class="kicker">{escaped} · {escaped} · Evidence as of 2026-10-14</p>', page)
        self.assertIn(f"<h1>&lt;script&gt;<em>x</em>&lt;/script&gt;&quot;&amp;amp</h1>", page)
        answer = page[page.index('id="panel-answer"'):page.index('</section>', page.index('id="panel-answer"'))]
        self.assertEqual(answer.count(f"<td>{escaped}</td>"), 3)
        watch = page[page.index('id="panel-watch"'):page.index('</section>', page.index('id="panel-watch"'))]
        self.assertIn(f"<h3>{escaped}</h3><p>{escaped}</p>", watch)
        # The accent is split from the raw title, so an entity can never be cut in two.
        context = self.modern_context()
        context.update(title="Fish & camp", title_accent="amp")
        page, _, _, _ = render(REPORT, context)
        self.assertIn("<h1>Fish &amp; c<em>amp</em></h1>", page)
        self.assertNotIn("&<", page)

    def test_v4_phase_prompts_still_checked(self):
        source, context = self.two_phase()
        self.assertEqual(context["format_version"], 5)
        self.assertEqual([pid for pid, _ in render(source, context).pairs], ["1", "2"])
        with self.assertRaisesRegex(ValueError, "Confirm Phase 1 is merged"):
            render(source.replace("Confirm Phase 1 is merged.", ""), context)

    @property
    def RERUN_PROMPT(self):
        plan, spec = (doc["path"] for doc in self.context["documents"])
        return (f"/plan-validation:validate-plan PLAN: `{plan}` SPEC: `{spec}` FOCUS: Run validation again (run 2 of 3). "
                "Previous report: `/data/run-1/report.md`. Run this before starting any phase. Focus on the delay cap. "
                "Do not start dependent implementation.")

    def rerun_prompt_for(self, out):
        """The re-run prompt naming the report.md that main() writes into out."""
        return self.RERUN_PROMPT.replace("/data/run-1/report.md", str((out / "report.md").resolve()))

    def rerun_yes(self, context, prompt=None):
        context["rerun"] = {"recommendation": "yes", "reasons": ["The delay cap is still open."],
                            "prompt": self.RERUN_PROMPT if prompt is None else prompt}
        return context

    def test_saved_v4_rerun_prompt_stays_as_written(self):
        # The checks that only a new version 4 run applied never reject a saved report.
        plan, spec = (doc["path"] for doc in self.context["documents"])
        for name, prompt in {
            "invocation": self.RERUN_PROMPT.replace("/plan-validation:validate-plan ", ""),
            "other command": self.RERUN_PROMPT.replace("/plan-validation:validate-plan", "/plan-validation:validate-planner"),
            "PLAN path": self.RERUN_PROMPT.replace(f"`{plan}`", "the plan"),
            "PLAN path .bak": self.RERUN_PROMPT.replace(f"`{plan}`", f"`{plan}.bak`"),
            "SPEC path": self.RERUN_PROMPT.replace(f"`{spec}`", "the spec"),
            "no previous report": self.RERUN_PROMPT.replace("Previous report: `/data/run-1/report.md`.", "Read the last report."),
            "relative previous report": self.RERUN_PROMPT.replace("`/data/run-1/report.md`", "`run-1/report.md`"),
            "other file": self.RERUN_PROMPT.replace("`/data/run-1/report.md`", "`/data/run-1/report.html`"),
            "no order": self.RERUN_PROMPT.replace(" Run this before starting any phase.", ""),
        }.items():
            with self.subTest(name=name):
                render(run_first(REPORT), self.rerun_yes(self.v4_context(), prompt))
        # A run-2 prompt that names the earlier run's report.
        second = self.rerun_yes(self.v4_context(), self.RERUN_PROMPT.replace("run 2 of 3", "run 3 of 3"))
        second["validation_run"].update(number=2, previous_report="/data/run-1/report.md")
        render(run_first(REPORT), second)
        # A phase-only run without its scope sentence.
        source, two = self.two_phase(self.v4_context())
        two["validation_run"]["scope"] = "phases:1-2"
        render(run_first(source), self.rerun_yes(two))
        # A recorded plan path with spaces may hold the verb in its file name.
        spaced_plan = self.v4_context()
        path = Path(self.directory.name) / "My Repo" / "implement-retry.md"
        path.parent.mkdir()
        path.write_text("PLAN")
        spaced_plan["documents"][0]["path"] = str(path)
        spaced_plan["validation_run"]["plan_key"] = "implement-retry.md"
        render(run_first(REPORT), self.rerun_yes(spaced_plan, self.RERUN_PROMPT.replace(plan, str(path))))
        # The prompt rules that also bind a saved report still apply: a ".." detour through words with spaces
        # is neither a name nor exempt from the word limit or the Implement check.
        detour = self.RERUN_PROMPT.replace("/data/run-1/report.md", "/implement every task now/../data/report.md")
        with self.assertRaisesRegex(ValueError, "Implement"):
            render(run_first(REPORT), self.rerun_yes(self.v4_context(), detour))
        padded = self.RERUN_PROMPT.replace("/data/run-1/report.md", "/x " + "word " * 80 + "/../data/report.md")
        with self.assertRaisesRegex(ValueError, "80 words"):
            render(run_first(REPORT), self.rerun_yes(self.v4_context(), padded))

    def test_v4_requires_run_fields(self):
        for key in ("validation_run", "rerun"):
            with self.subTest(key=key):
                context = self.v4_context()
                del context[key]
                with self.assertRaisesRegex(ValueError, key):
                    render(REPORT, context)
                context[key] = "full"
                with self.assertRaisesRegex(ValueError, key):
                    render(REPORT, context)

    def test_run_fields(self):
        def run(**changes):
            context = self.v4_context()
            context["validation_run"].update(changes)
            return context
        source, two = self.two_phase(self.v4_context())
        cases = [
            ("number", run(number=0)), ("number", run(number=4)), ("number", run(number=True)), ("number", run(number="1")),
            ("previous_report", run(number=2)),
            ("previous_report", run(number=2, previous_report="run-1/report.md")),
            ("scope", run(scope="phases")), ("scope", run(scope="phases:1-2")), ("scope", run(scope="")),
            ("plan_key", run(plan_key=" ")), ("plan_key", run(plan_key="/PLAN.md")), ("plan_key", run(plan_key="../PLAN.md")),
            ("plan_key", run(plan_key="docs/../PLAN.md")), ("plan_key", run(plan_key="LAN.md")), ("plan_key", run(plan_key="docs/PLAN.md")),
        ]
        for name, context in cases:
            with self.subTest(name=name, run=context["validation_run"]):
                with self.assertRaisesRegex(ValueError, name):
                    render(REPORT, context)
        render(REPORT, run(number=2, previous_report="/data/run-1/report.md"))
        render(REPORT, run(scope="phases:1-1"))
        # Phase IDs may hold hyphens, so the scope is compared whole, never split.
        two["phases"][0]["id"], two["phases"][1]["id"] = "1-a", "2-b"
        source = source.replace("Phase 1", "Phase 1-a").replace("Phase 2", "Phase 2-b")
        two["validation_run"]["scope"] = "phases:1-a-2-b"
        render(source, two)
        two["validation_run"]["scope"] = "phases:1-a-2"
        with self.assertRaisesRegex(ValueError, "scope"):
            render(source, two)

    def test_triggers_forbid_no(self):
        remediation = REPORT.replace("**Ready.**", "**Not ready.**").replace(
            "Implement the approved scope now.", "Resume validation. Do not start dependent implementation.")
        # One revised PLAN cell 9 -> 3 makes the revised average 7.8.
        low_plan = REPORT.replace("| Performance | 9 | 9 | Unchanged. |", "| Performance | 9 | 3 | Unchanged. |").replace(
            "| **Average /10** | **6.2** | **9.0** | |", "| **Average /10** | **6.2** | **7.8** | |")
        cases = {
            "confidence 65%": REPORT.replace("Confidence: 75%", "Confidence: 65%"),
            "confidence Unknown": REPORT.replace("Confidence: 75%", "Confidence: Unknown"),
            "PLAN average 7.8": low_plan,
            "Not ready": remediation,
        }
        for name, source in cases.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "Run validation again"):
                    render(source, self.v4_context())
                render(source, self.stop_rerun(self.v4_context()))
                render(source, self.rerun_yes(self.v4_context()))
        # A saved Ready report's phase prompts still wait for the re-run its yes asked for.
        low = REPORT.replace("Confidence: 75%", "Confidence: 65%")
        page = render(run_first(low), self.rerun_yes(self.v4_context()))[0]
        summary = self.panel(page, "summary")
        self.assertIn("Run validation again first", summary)
        self.assertNotIn("Can start", page)
        # No phase prompt can be copied before the re-run, and the re-run card comes before the next session.
        self.assertNotIn("Copy Phase", page)
        self.assertNotIn('href="handoff.txt"', page)
        self.assertLess(summary.index('id="rerun"'), summary.index("Next session"))
        self.assertIn(render_report.RUN_FIRST_NOTE, self.panel(page, "full"))
        # Without the yes, the phase prompts keep their copy buttons.
        page = render(low, self.stop_rerun(self.v4_context()))[0]
        self.assertIn("Copy Phase 1 prompt", page)
        self.assertIn('href="handoff.txt"', page)
        # 70% and an average of exactly 8.0 are not below the thresholds.
        render(REPORT.replace("Confidence: 75%", "Confidence: 70%"), self.v4_context())

    def test_run_three_never_yes(self):
        context = self.rerun_yes(self.v4_context(), self.RERUN_PROMPT.replace("run 2 of 3", "run 4 of 3"))
        context["validation_run"].update(number=3, previous_report="/data/run-2/report.md")
        with self.assertRaisesRegex(ValueError, "run 3"):
            render(REPORT, context)
        self.stop_rerun(context)
        self.assertIsNone(render(REPORT, context)[3])
        context["rerun"] = {"recommendation": "no", "reasons": ["Nothing is left that validation can fix."]}
        render(REPORT, context)
        with self.assertRaisesRegex(ValueError, "Run validation again"):
            render(REPORT.replace("Confidence: 75%", "Confidence: 65%"), context)

    def test_no_trigger_allows_every_answer_before_run_3(self):
        for recommendation in ("no", "stop"):
            context = self.v4_context()
            context["rerun"]["recommendation"] = recommendation
            render(REPORT, context)
        render(run_first(REPORT), self.rerun_yes(self.v4_context()))
        # A pending approval alone is not a re-run trigger.
        render(*self.phase_1_waits(*self.pending_d1(REPORT.replace("**Ready.**", "**Ready after approvals.**"), self.v4_context())))

    def test_rerun_prompt_rules(self):
        cases = {
            "prompt": None,
            "80 words": self.RERUN_PROMPT + " detail" * 80,
            "run 2 of 3": self.RERUN_PROMPT.replace("run 2 of 3", "run 3 of 3"),
            "Implement": self.RERUN_PROMPT + " Implement Phase 1.",
            "implementing": self.RERUN_PROMPT + " Then start implementing Phase 1.",
            "quoted instruction": self.RERUN_PROMPT + " Then `/x Implement Phase 1 now` please.",
            "split quote": self.RERUN_PROMPT + " Fix `/repo/a\nStart implementing Phase 1 now.md`.",
            "slash command": self.RERUN_PROMPT + " Then run `/feature-dev:implement` for Phase 1.",
            "Do not start dependent implementation": self.RERUN_PROMPT.replace(" Do not start dependent implementation.", ""),
        }
        for name, prompt in cases.items():
            with self.subTest(name=name):
                context = self.rerun_yes(self.v4_context())
                if prompt is None:
                    del context["rerun"]["prompt"]
                else:
                    context["rerun"]["prompt"] = prompt
                with self.assertRaisesRegex(ValueError, "Implement" if name in ("implementing", "quoted instruction", "split quote", "slash command") else name):
                    render(REPORT, context)
        # A negated mention, with a typographic apostrophe too, is not an instruction.
        render(run_first(REPORT), self.rerun_yes(self.v4_context(), self.RERUN_PROMPT + " Don’t implement anything."))
        # Every sentence check reads a wrapped prompt as one line.
        wrapped = self.RERUN_PROMPT.replace("run 2 of 3", "run 2\n  of 3").replace("dependent implementation", "dependent\n  implementation")
        render(run_first(REPORT), self.rerun_yes(self.v4_context(), wrapped))
        # A "not" closing one line does not excuse an instruction on the next.
        with self.assertRaisesRegex(ValueError, "Implement"):
            render(run_first(REPORT), self.rerun_yes(self.v4_context(), self.RERUN_PROMPT + " Keep D1 or not\nImplement Phase 1."))
        # A raw CR from context.json ends a line too, and a word that only ends in "not" is no negation.
        for tail in (" Keep D1 or not\rImplement Phase 1.", " Call isNot implement Phase 1.", " Do n’t implement Phase 1."):
            with self.subTest(tail=tail), self.assertRaisesRegex(ValueError, "Implement"):
                render(run_first(REPORT), self.rerun_yes(self.v4_context(), self.RERUN_PROMPT + tail))
        # Paths are names, not instructions, even when they contain the word.
        render(run_first(REPORT), self.rerun_yes(self.v4_context(), self.RERUN_PROMPT.replace(
            "`/repo/PLAN.md`", "`/repo/docs/implementation plan.md`").replace(
            "`/data/run-1/report.md`", "`/data/20261104T0000Z-implement-retry/report.md`")))
        # Describing implementation is not an instruction to implement.
        render(run_first(REPORT), self.rerun_yes(self.v4_context(), self.RERUN_PROMPT.replace(
            "Focus on the delay cap.", "Check whether Task 3 is implemented correctly and the implementation order.")))
        # Only yes carries a prompt, so rerun.txt exists only for yes.
        context = self.v4_context()
        context["rerun"]["prompt"] = self.RERUN_PROMPT
        with self.assertRaisesRegex(ValueError, "prompt"):
            render(REPORT, context)

    def test_v5_prompt_cannot_say_run_first(self):
        # A prompt that sends the next session to a re-run points at a rerun.txt version 5 never writes.
        prompt = "Run validation again first, with the re-run prompt in rerun.txt. Implement the approved scope now."
        with self.assertRaisesRegex(ValueError, "remove that line"):
            render(REPORT.replace("Implement the approved scope now.", prompt), self.modern_context())
        for conditional in ("If you do not run validation again first, Phase 1 builds on a stale plan.",
                            "Agents that never run validation again first build on stale plans.",
                            "If you don't run validation again first, stop."):
            with self.subTest(conditional=conditional), self.assertRaisesRegex(ValueError, "remove that line"):
                render(REPORT.replace("Implement the approved scope now.", conditional + " Implement the approved scope now."),
                       self.modern_context())
        for negated in ("You do not need to run validation again first.", "Do not run validation again first.",
                        "Don’t run validation again first.", "Never run validation again first.",
                        "You need not run validation again first.", "- Do not run validation again first."):
            with self.subTest(negated=negated):
                render(REPORT.replace("Implement the approved scope now.", negated + " Implement the approved scope now."),
                       self.modern_context())

    def test_section_8_never_says_run_first(self):
        # A new report has no re-run, so any run-first line contradicts the page.
        context = self.modern_context()
        with self.assertRaisesRegex(ValueError, "remove that line"):
            render(run_first(REPORT), context)
        # Other wording that mentions running validation again is free text.
        for line in ("You do not need to run validation again first.", "There is no need to run validation again first."):
            render(REPORT.replace("## 8. Fresh-session handoff\n", f"## 8. Fresh-session handoff\n{line}\n\n", 1), context)
        # A reworded run-first line still tells the reader to hold the phases, and a negation in
        # another clause of the sentence does not excuse it.
        for line in ("Run validation again first, then start Phase 1.",
                     "There are no open decisions, so run validation again first.",
                     "Not ready means run validation again first."):
            with self.subTest(line=line), self.assertRaisesRegex(ValueError, "remove that line"):
                render(REPORT.replace("## 8. Fresh-session handoff\n", f"## 8. Fresh-session handoff\n{line}\n\n", 1), context)
        not_ready = REPORT.replace("**Ready.**", "**Not ready.**").replace(
            "Implement the approved scope now.", "Fix Task 1. Do not start dependent implementation.")
        render(not_ready, context)
        with self.assertRaisesRegex(ValueError, "remove that line"):
            render(run_first(not_ready), context)
        historical = self.modern_context()
        historical["handoff_status"] = "historical"
        with self.assertRaisesRegex(ValueError, "remove that line"):
            render(run_first(REPORT), historical)
        source, waiting = self.phase_1_waits(*self.pending_d1(REPORT.replace("**Ready.**", "**Ready after approvals.**"),
                                                              self.modern_context()))
        render(source, waiting)
        with self.assertRaisesRegex(ValueError, "remove that line"):
            render(run_first(source), waiting)
        # A saved report keeps section 8 as its run wrote it.
        saved = self.rerun_yes(self.v4_context())
        render(REPORT, saved)
        render(run_first(REPORT), self.v4_context())

    def test_held_phase_prompt_files_say_run_first(self):
        out = Path(self.directory.name) / "held"
        out.mkdir()
        code, stdout, err = self.run_main(out, run_first(REPORT), self.rerun_yes(self.v4_context()))
        self.assertEqual(code, 0, err)
        result = json.loads(stdout)
        self.assertTrue(result["handoff_current"])
        self.assertTrue(result["handoff_held"])
        # Every prompt file a session or a publish could pick up starts with the held note.
        for name in ("handoff.txt", "handoff-phase-1.txt"):
            text = (out / name).read_text(encoding="utf-8")
            self.assertTrue(text.startswith(render_report.HELD_PREFIX), name)
            self.assertIn("Implement the approved scope now.", text)
        # Without the yes the files start the phase; a historical handoff keeps its own warning.
        code, stdout, err = self.run_main(out, REPORT, self.modern_context())
        self.assertEqual(code, 0, err)
        self.assertFalse(json.loads(stdout)["handoff_held"])
        self.assertTrue((out / "handoff-phase-1.txt").read_text(encoding="utf-8").startswith("Implement the approved scope now."))
        historical = self.rerun_yes(self.v4_context())
        historical["handoff_status"] = "historical"
        code, stdout, err = self.run_main(out, run_first(REPORT), historical)
        self.assertEqual(code, 0, err)
        self.assertFalse(json.loads(stdout)["handoff_held"])
        for name in ("handoff.txt", "handoff-phase-1.txt"):
            self.assertTrue((out / name).read_text(encoding="utf-8").startswith(HISTORICAL_PREFIX), name)

    def test_rerun_reasons(self):
        for reasons in ([], ["One.", "Two.", "Three.", "Four.", "Five."], ["One.", " "], "One.", [1]):
            with self.subTest(reasons=reasons):
                context = self.v4_context()
                context["rerun"]["reasons"] = reasons
                with self.assertRaisesRegex(ValueError, "reasons"):
                    render(REPORT, context)
        context = self.v4_context()
        context["rerun"]["recommendation"] = "maybe"
        with self.assertRaisesRegex(ValueError, "recommendation"):
            render(REPORT, context)

    def test_rerun_rendered(self):
        # A saved version 4 report shows its re-run advice as recorded, like its verdict.
        page, _, _, prompt = render(run_first(REPORT), self.rerun_yes(self.v4_context()))
        pills = page[page.index('<ul class="pills"'):page.index('</ul>', page.index('<ul class="pills"'))]
        self.assertIn("<span>Recorded: run validation again: yes</span>", pills)
        summary = self.panel(page, "summary")
        self.assertIn("Run 1 of at most 3", summary)
        self.assertIn("The delay cap is still open.", summary)
        match = re.search(r'<pre id="rerun-prompt"[^>]*>(.*?)</pre>', summary, re.S)
        self.assertEqual(html.unescape(match.group(1)), self.RERUN_PROMPT)
        # A saved report's run label may be stale, so it gets no copy button and no rerun.txt.
        self.assertIsNone(prompt)
        self.assertNotIn('data-copy-target="rerun-prompt"', page)
        for recommendation in ("no", "stop"):
            with self.subTest(recommendation=recommendation):
                context = self.v4_context()
                context["rerun"]["recommendation"] = recommendation
                page, _, _, _ = render(REPORT, context)
                self.assertIn(f"<span>Recorded: run validation again: {recommendation}</span>", page)
                self.assertIn("Nothing is left that validation can fix.", self.panel(page, "summary"))
                self.assertNotIn('id="rerun-prompt"', page)
        context = self.rerun_yes(self.v4_context())
        context["handoff_status"] = "historical"
        page, _, current, _ = render(run_first(REPORT), context)
        self.assertFalse(current)
        self.assertEqual(re.findall(r'data-copy-target="([^"]+)"', self.panel(page, "summary")), [])
        self.assertIn('<pre id="rerun-prompt"', page)

    def test_rerun_text_cannot_inject_markup(self):
        probe = '<script>x</script>"&amp'
        context = self.rerun_yes(self.v4_context(), self.RERUN_PROMPT + " " + probe)
        context["rerun"]["reasons"] = [probe]
        page, _, _, _ = render(run_first(REPORT), context)
        self.assertEqual(page.count("<script>"), 1)
        self.assertNotIn("<script>x", page)
        summary = self.panel(page, "summary")
        self.assertEqual(summary.count("&lt;script&gt;x&lt;/script&gt;&quot;&amp;amp"), 2)

    def test_saved_rerender_keeps_the_latest_rerun_file(self):
        out = Path(self.directory.name) / "rerun-saved"
        out.mkdir()
        # The file a version 4 run wrote; a saved re-render never writes or deletes it.
        (out / "rerun.txt").write_text(self.rerun_prompt_for(out) + "\n", encoding="utf-8")
        code, stdout, err = self.run_main(out, run_first(REPORT), self.rerun_yes(self.v4_context(), self.rerun_prompt_for(out)))
        self.assertEqual(code, 0, err)
        # The JSON names the kept file, so the reply can still give its path.
        self.assertEqual(json.loads(stdout)["rerun"], str((out / "rerun.txt").resolve()))
        self.assertEqual((out / "rerun.txt").read_text(encoding="utf-8"), self.rerun_prompt_for(out) + "\n")

    def test_saved_drift_warning_names_no_run_number(self):
        context = self.v4_context()
        plan = Path(context["documents"][0]["path"])
        plan.write_text("Changed")
        self.addCleanup(plan.write_text, "PLAN")
        page, _, _, _ = render(REPORT, context)
        self.assertNotIn("(run 2 of 3)", page)
        self.assertIn("Run validation again instead of more review rounds", page)

    def test_failed_write_never_leaves_an_old_rerun_prompt(self):
        out = Path(self.directory.name) / "rerun-fail"
        out.mkdir()
        # An earlier version 4 run left its re-run prompt in the run directory.
        (out / "rerun.txt").write_text(self.rerun_prompt_for(out) + "\n", encoding="utf-8")
        # A new version 5 write fails after report.html is written; the old yes prompt must already be gone.
        write_text = Path.write_text

        def failing(path, *args, **kwargs):
            if path.name == "handoff.txt":
                raise OSError("disk full")
            return write_text(path, *args, **kwargs)
        with mock.patch.object(Path, "write_text", failing):
            code, _, err = self.run_main(out, REPORT, self.modern_context())
        self.assertEqual(code, 1)
        self.assertIn("disk full", err)
        self.assertFalse((out / "rerun.txt").exists())

    def test_failed_write_never_leaves_an_unheld_prompt(self):
        out = Path(self.directory.name) / "held-fail"
        out.mkdir()
        code, _, err = self.run_main(out, REPORT, self.modern_context())
        self.assertEqual(code, 0, err)
        self.assertTrue((out / "handoff-phase-1.txt").exists())
        # A saved version 4 yes render fails after report.html is written; no earlier, unheld prompt may stay beside it.
        write_text = Path.write_text

        def failing(path, *args, **kwargs):
            if path.name == "handoff.txt":
                raise OSError("disk full")
            return write_text(path, *args, **kwargs)
        with mock.patch.object(Path, "write_text", failing):
            code, _, err = self.run_main(out, run_first(REPORT), self.rerun_yes(self.v4_context()))
        self.assertEqual(code, 1)
        self.assertIn("disk full", err)
        self.assertFalse((out / "handoff.txt").exists())
        self.assertEqual(list(out.glob("handoff-phase-*.txt")), [])

    def test_prompts_may_quote_this_runs_files_with_spaces(self):
        # A run directory under a home or repository folder with spaces is common on Windows and macOS.
        out = Path(self.directory.name) / "Jane Doe" / "my repo" / "run 1"
        out.mkdir(parents=True)
        report, context_file = out / "report.md", out / "context.json"
        prompt = f"Implement the approved scope now. Read `{report}` and `{context_file}` first."
        block = REPORT.split("```text\n", 1)[1].split("\n```", 1)[0].replace("Implement the approved scope now.", prompt)
        filler = 80 - render_report.word_count(block, 4, {str(report), str(context_file)}) - 1
        self.assertGreater(filler, 0)
        source = REPORT.replace("Implement the approved scope now.", prompt + " Then" + " check" * filler + ".")
        # Without the run's own paths every word inside them counts, so the prompt is over the limit.
        with self.assertRaisesRegex(ValueError, "80 words"):
            render(source, self.modern_context())
        (out / "context.json").write_text(json.dumps(self.modern_context()), encoding="utf-8")
        (out / "in.md").write_text(source, encoding="utf-8")
        argv = ["render_report.py", "--report", str(out / "in.md"), "--context", str(context_file), "--output", str(out / "report.html")]
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            render_report.main()
        self.assertIn(str(report), (out / "handoff-phase-1.txt").read_text(encoding="utf-8"))

    def test_demo_runs_into_a_folder_with_spaces(self):
        # The demo's prompts quote its own report.md, so a spaced output folder must still render.
        script = Path(__file__).resolve().parents[3] / "scripts" / "demo.py"
        output = Path(self.directory.name) / "My demo" / "please implement it"
        result = subprocess.run([sys.executable, "-B", str(script), "--output", str(output)], capture_output=True, text=True,
                                timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((output / "report.html").exists())

    def test_run_three_error_names_only_stop(self):
        context = self.v4_context()
        context["validation_run"].update(number=3, previous_report="/data/run-2/report.md")
        with self.assertRaises(ValueError) as caught:
            render(REPORT.replace("Confidence: 75%", "Confidence: 65%"), context)
        self.assertIn("recommend stop", str(caught.exception))
        self.assertNotIn("yes", str(caught.exception))

    def test_reset_run_is_run_one(self):
        context = self.v4_context()
        context["validation_run"]["reset"] = True
        render(REPORT, context)
        for change in ({"reset": "true"}, {"reset": True, "number": 2, "previous_report": "/data/run-1/report.md"}):
            with self.subTest(change=change):
                context = self.v4_context()
                context["validation_run"].update(change)
                with self.assertRaisesRegex(ValueError, "reset"):
                    render(REPORT, context)

    def test_malformed_documents_get_a_message(self):
        # A malformed context is rejected with a message that names the field, never a traceback.
        cases = {"v5": (REPORT, self.modern_context()), "v4": (REPORT, self.v4_context()), **self.legacy_cases()}
        for version, (source, base) in cases.items():
            plan, spec = base["documents"]
            fields = [[plan, {key: value for key, value in spec.items() if key != "path"}],
                      [plan, dict(spec, sha256=5)], [plan, dict(spec, label=["SPEC"])], [plan, dict(spec, path=7)]]
            for documents in [None, "PLAN", {"label": "PLAN"}, base["documents"] + [42], [plan, None]] + fields:
                with self.subTest(version=version, documents=documents):
                    context = copy.deepcopy(base)
                    context["documents"] = documents
                    with self.assertRaisesRegex(ValueError, "documents must be a list of objects"):
                        render(source, context)
            # A relative path is named as such, not blamed on plan_key, which reads it.
            with self.subTest(version=version, documents="relative"):
                context = copy.deepcopy(base)
                context["documents"][0]["path"] = "PLAN.md"
                with self.assertRaisesRegex(ValueError, "Document paths must be absolute"):
                    render(source, context)
            # A path that is not a valid file name is rejected by name, not with an encoding traceback.
            for surrogate in ("\ud800", "\udc80"):
                with self.subTest(version=version, documents=f"surrogate {surrogate!a}"):
                    context = copy.deepcopy(base)
                    context["documents"][1]["path"] += surrogate
                    with self.assertRaisesRegex(ValueError, "valid UTF-8"):
                        render(source, context)
            # A path with a NUL character is rejected by name, for either document, never written into the page.
            for index in (0, 1):
                with self.subTest(version=version, documents=f"nul {index}"):
                    context = copy.deepcopy(base)
                    context["documents"][index]["path"] += "\0"
                    with self.assertRaisesRegex(ValueError, "cannot contain a NUL character"):
                        render(source, context)
            # A missing documents field names the documents, not a field that reads them.
            with self.subTest(version=version, documents="missing"):
                context = copy.deepcopy(base)
                del context["documents"]
                with self.assertRaisesRegex(ValueError, "exactly PLAN and SPEC"):
                    render(source, context)

    def test_v4_historical_says_rerun(self):
        # A saved version 4 report keeps its run-counting drift warning, without a run number.
        context = self.v4_context()
        plan = Path(context["documents"][0]["path"])
        plan.write_text("Changed")
        self.addCleanup(plan.write_text, "PLAN")
        page, _, _, _ = render(REPORT, context)
        advice = "Run validation again instead of more review rounds, if the 3-run limit allows."
        self.assertIn(advice, self.panel(page, "summary"))
        self.assertIn(advice, self.panel(page, "full"))
        self.assertIn("changed or could not be read", page)
        # The recorded no came before the change, so the page says so instead of contradicting the warning.
        self.assertIn("<span>Recorded: run validation again: no</span>", page)
        self.assertNotIn("<span>Run validation again: no</span>", page)
        # An earlier recorded stop is not overridden either: the page never offers the next run.
        context["rerun"] = {"recommendation": "stop", "reasons": ["D1 needs the user's decision first."]}
        # A firing trigger (confidence below 70%) does not override the recorded stop either.
        page, _, _, _ = render(REPORT.replace("Confidence: 75%", "Confidence: 60%"), context)
        self.assertIn("confidence below 70%", page)
        self.assertIn("The recorded answer is stop", page)
        self.assertNotIn("Run validation again (run", page)
        self.assertNotIn("Run validation again instead", page)
        self.assertNotIn("run limit is reached", page)
        # At run 3 a saved page states the limit whatever it recorded, and never invites a fourth run.
        context["validation_run"].update(number=3, previous_report="/data/run-2/report.md")
        for recommendation in ("stop", "no"):
            with self.subTest(recommendation=recommendation):
                context["rerun"] = {"recommendation": recommendation, "reasons": ["The run limit is reached."]}
                page, _, _, _ = render(REPORT, context)
                self.assertNotIn("run 4 of 3", page)
                self.assertIn("The run limit is reached for this scope, so revalidating it needs your explicit reset", page)
                self.assertNotIn("Run validation again instead", page)
        # Git or approval drift alone does not claim the documents changed.
        plan.write_text("PLAN")
        context = self.v4_context()
        context["handoff_status"] = "historical"
        page, _, _, _ = render(REPORT, context)
        self.assertIn("This is a historical prompt.", page)
        self.assertNotIn("The plan or spec changed", page)
        self.assertNotIn("Run validation again (run", page)
        self.assertNotIn("run limit is reached", page)
        # With Git or approval drift alone, the run limit and a recorded stop still say what revalidating takes.
        for number, recommendation, advice in ((3, "no", "The run limit is reached"), (3, "stop", "The run limit is reached"),
                                               (1, "stop", "The recorded answer is stop")):
            with self.subTest(number=number, recommendation=recommendation):
                context = self.v4_context()
                context["handoff_status"] = "historical"
                context["validation_run"].update(number=number, previous_report=f"/data/run-{number - 1}/report.md" if number > 1 else None)
                context["rerun"] = {"recommendation": recommendation, "reasons": ["Recorded reason."]}
                page, _, _, _ = render(REPORT, context)
                self.assertIn(advice, page)
                self.assertNotIn("The plan or spec changed", page)

    def two_phase(self, context=None):
        context = self.modern_context() if context is None else context
        context["task_inventory"] = ["1", "2"]
        context["phases"] = [dict(context["phases"][0], tasks=["1"]), dict(context["phases"][0], id="2", tasks=["2"])]
        prompts = ("Implement Phase 1. Stop at the end of Phase 1 and print the Phase 2 prompt from the report; do not start it.",
                   "Implement Phase 2. Confirm Phase 1 is merged. Stop at the end of Phase 2; it is the last phase.")
        source = REPORT.split("## 8. Fresh-session handoff")[0] + "## 8. Fresh-session handoff\n" + "".join(
            f"```text\n{prompt}\n```\n" for prompt in prompts)
        return source, context

    def test_each_ready_phase_gets_its_own_prompt(self):
        source, context = self.two_phase()
        _, prompt, _, _ = render(source, context)
        self.assertTrue(prompt.startswith("Implement Phase 1."))
        self.assertEqual([pid for pid, _ in render(source, context).pairs], ["1", "2"])

    def test_prompt_count_must_match_ready_phases(self):
        source, context = self.two_phase()
        source = source.replace("**Ready.**", "**Ready after approvals.**")
        source, context = self.pending_d1(source, context)
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
        render(source.replace("Stop at the end of Phase 1 and", "Stop at the end of\nPhase 1 and"), context)
        # A curly apostrophe negates like a straight one.
        with self.assertRaisesRegex(ValueError, "Stop at the end of Phase 1"):
            render(source.replace("Stop at the end of Phase 1 and", "Don’t stop at the end of Phase 1 and"), context)
        with self.assertRaisesRegex(ValueError, "Stop at the end of Phase 1"):
            render(source.replace("Stop at the end of Phase 1 and", "You cannot stop at the end of Phase 1 and"), context)

    def test_saved_v3_keeps_its_negation_rule(self):
        # The wider version 4 negation set must not reject a saved version 3 report that rendered before.
        source, context = self.legacy_cases()["v3-two-phases"]
        for negated in ("Don’t stop at the end of Phase 1 and", "You cannot stop at the end of Phase 1 and"):
            with self.subTest(negated=negated):
                render(source.replace("Stop at the end of Phase 1 and", "Stop at the end of Phase 1. " + negated), context)

    def test_later_prompt_must_confirm_the_previous_phase_is_merged(self):
        source, context = self.two_phase()
        for bad in ("Confirm Phase 1 is committed.", "Confirm Phase 12 is merged.", "Confirm Phase 1.2 is merged.",
                    "Confirm Phase 1-b is merged.", "Do not confirm Phase 1 is merged.", "Never confirm Phase 1 is merged.",
                    "Don’t confirm Phase 1 is merged.", ""):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "Confirm Phase 1 is merged"):
                    render(source.replace("Confirm Phase 1 is merged.", bad), context)
        render(source.replace("Confirm Phase 1 is merged.", "Confirm Phase 1 is merged; stop if you can't confirm Phase 1 is merged."), context)
        context["kind"] = "saved"
        render(source.replace("Confirm Phase 1 is merged.", "Confirm Phase 1 is committed."), context)

    def test_merge_check_names_the_ready_phase_just_before(self):
        source, context = self.two_phase()
        context["task_inventory"] = ["1", "2", "3"]
        context["phases"].append(dict(context["phases"][1], id="3", tasks=["3"]))
        source = source.replace("Stop at the end of Phase 2; it is the last phase.",
                                "Stop at the end of Phase 2 and print the Phase 3 prompt from the report; do not start it.")
        source += "```text\nImplement Phase 3. {} Stop at the end of Phase 3; it is the last phase.\n```\n"
        render(source.format("Confirm Phase 2 is merged."), context)
        with self.assertRaisesRegex(ValueError, "Confirm Phase 2 is merged"):
            render(source.format("Confirm Phase 1 is merged."), context)

    def test_first_phase_waiting_needs_a_non_implementation_prompt(self):
        source, context = self.two_phase()
        for phase in context["phases"]:
            phase.update(status="waiting", waits_for="D1")
        source = source.replace("**Ready.**", "**Ready after approvals.**")
        source, context = self.pending_d1(source, context)
        with self.assertRaisesRegex(ValueError, "one"):
            render(source, context)
        waiting = source.split("## 8.")[0] + "## 8. Fresh-session handoff\n```text\nRecord D1, then re-render the report. Do not start dependent implementation.\n```\n"
        _, prompt, _, _ = render(waiting, context)
        self.assertIn("Do not start dependent implementation.", prompt)
        self.assertEqual(render(waiting, context).pairs, [])
        with self.assertRaisesRegex(ValueError, "cannot contain an Implement instruction"):
            render(waiting.replace("Record D1, then", "Implement Phase 1, then"), context)

    def test_every_phase_prompt_has_the_word_limit(self):
        source, context = self.two_phase()
        with self.assertRaisesRegex(ValueError, "80 words"):
            render(source.replace("Implement Phase 2.", "Implement Phase 2. " + "detail " * 80), context)

    def test_inner_fence_in_a_phase_prompt_counts_once(self):
        source, context = self.two_phase()
        source = source.replace("```text\nImplement Phase 2.", "````text\nImplement Phase 2.\n```\nexample\n```\n").replace(
            "it is the last phase.\n```", "it is the last phase.\n````")
        self.assertEqual(len(render(source, context).pairs), 2)
        self.assertIn("example", render(source, context).pairs[1][1])

    def test_not_ready_keeps_one_remediation_prompt(self):
        source, context = self.two_phase()
        context["phases"][0].update(status="waiting", waits_for="Blocker")
        context["phases"][1].update(status="waiting", waits_for="Blocker")
        source = source.replace("**Ready.**", "**Not ready.**")
        with self.assertRaisesRegex(ValueError, "one"):
            render(source, context)
        remediation = REPORT.replace("**Ready.**", "**Not ready.**").replace(
            "Implement the approved scope now.", "Resume validation. Do not start dependent implementation.")
        self.assertEqual(render(remediation, context).pairs, [])

    def run_renderer(self, directory, source, context):
        (directory / "in.md").write_text(source, encoding="utf-8")
        (directory / "in.json").write_text(json.dumps(context), encoding="utf-8")
        script = Path(__file__).with_name("render_report.py")
        return subprocess.run([sys.executable, str(script), "--report", str(directory / "in.md"), "--context", str(directory / "in.json"),
                               "--output", str(directory / "report.html")], capture_output=True, text=True)

    def test_main_writes_one_file_per_phase_and_marks_historical_files(self):
        source, context = self.two_phase()
        root = Path(self.directory.name)
        for status in ("current", "historical"):
            context["handoff_status"] = status
            out = root / status
            out.mkdir()
            result = self.run_renderer(out, source, context)
            self.assertEqual(result.returncode, 0, result.stderr)
            files = json.loads(result.stdout)["phase_handoffs"]
            self.assertEqual(files, [str((out / f"handoff-phase-{pid}.txt").resolve()) for pid in ("1", "2")])
            for pid, prompt in render(source, context).pairs:
                text = (out / f"handoff-phase-{pid}.txt").read_text(encoding="utf-8")
                self.assertEqual(text, (render_report.V5_HISTORICAL_PREFIX if status == "historical" else "") + prompt + "\n")
        out = root / "current"
        for phase in context["phases"]:
            phase.update(status="waiting", waits_for="Blocker")
        context["handoff_status"] = "current"
        remediation = source.split("## 8.")[0].replace("**Ready.**", "**Not ready.**") + (
            "## 8. Fresh-session handoff\n```text\nResume validation. Do not start dependent implementation.\n```\n")
        result = self.run_renderer(out, remediation, context)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(out.glob("handoff-phase-*.txt")), [])

    def test_phase_table_lists_every_phase_with_its_flags(self):
        source, context = self.two_phase()
        context["phases"][1].update(docs_only=True)
        context["phases"][0].update(security_review=True, security_reason="Renders untrusted text.")
        page, _, _, _ = render(source, context)
        start = page.index('aria-label="Phase plan"')
        table = page[start:page.index("</table>", start)]
        for text in ("Tasks", "Kind", "Security review", "Status", "Docs only", "Code", "Yes — Renders untrusted text.", "Can start"):
            self.assertIn(text, table)
        self.assertEqual(table.count("<tr>"), 3)

    def test_every_copy_button_targets_an_existing_prompt(self):
        source, context = self.two_phase()
        page, _, _, _ = render(source, context)
        targets = re.findall(r'data-copy-target="([^"]+)"', page)
        self.assertEqual(targets, ["summary-handoff-1", "handoff-1", "handoff-2"])
        for target in targets:
            self.assertIn(f'<pre id="{target}"', page)
        self.assertIn("Copy Phase 2 prompt", page)
        self.assertNotIn("```text", page)

    def test_historical_phase_report_offers_no_copy_button(self):
        source, context = self.two_phase()
        context["handoff_status"] = "historical"
        page, _, _, _ = render(source, context)
        # report.js is inlined and names the attribute, so look for markup only.
        self.assertNotIn('data-copy-target="', page)
        self.assertNotIn('href="handoff.txt"', page)
        self.assertEqual(page.count("This is a historical prompt."), 3)

    def test_not_ready_phase_table_offers_no_start(self):
        source = REPORT.replace("**Ready.**", "**Not ready.**").replace(
            "Implement the approved scope now.", "Resume validation. Do not start dependent implementation.")
        page, _, _, _ = render(source, self.modern_context())
        self.assertIn("Waits for remediation", page)
        self.assertNotIn("Can start", page)
        self.assertIn("Copy remediation prompt", page)

    def test_saved_reports_keep_a_working_copy_button(self):
        page, _, _, _ = render(REPORT, self.context)
        self.assertIn('data-copy-target="handoff"', page)
        self.assertIn('<pre id="handoff"', page)

    def test_phase_titles_cannot_inject_markup(self):
        source, context = self.two_phase()
        context["phases"][0]["title"] = "<img src=x onerror=alert(1)>"
        context["phases"][1].update(status="waiting", waits_for="D1 <script>alert(2)</script>")
        source = source.replace("**Ready.**", "**Ready after approvals.**").split("```text\nImplement Phase 2.")[0]
        source, context = self.pending_d1(source, context)
        context["open_decisions"][0]["holds_back"] = "Phase 2"
        page, _, _, _ = render(source, context)
        self.assertNotIn("<img src=x", page)
        self.assertNotIn("<script>alert", page)
        self.assertIn("&lt;img src=x", page)

    def test_first_phase_waiting_offers_a_remediation_copy_button(self):
        source, context = self.two_phase()
        for phase in context["phases"]:
            phase.update(status="waiting", waits_for="D1")
        source = source.split("## 8.")[0].replace("**Ready.**", "**Ready after approvals.**") + (
            "## 8. Fresh-session handoff\n```text\nRecord D1, then re-render the report. Do not start dependent implementation.\n```\n")
        source, context = self.pending_d1(source, context)
        page, _, _, _ = render(source, context)
        self.assertIn("Copy remediation prompt", page)
        self.assertNotIn("Copy implementation prompt", page)

    def test_mismatched_inner_fence_cannot_split_phase_prompts(self):
        source, context = self.two_phase()
        source = source.replace("do not start it.\n```", "do not start it.\n```bash\nnpm test\n```\nThen report results.\n```")
        with self.assertRaisesRegex(ValueError, "fence"):
            render(source, context)

    def test_prompt_cannot_negate_or_move_its_stop(self):
        source, context = self.two_phase()
        for bad in ("Do not stop at the end of Phase 1 and", "Stop at the end of Phase 2. Stop at the end of Phase 1 and"):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "Phase 1"):
                    render(source.replace("Stop at the end of Phase 1 and", bad), context)

    def test_historical_phase_table_offers_no_start(self):
        source, context = self.two_phase()
        context["handoff_status"] = "historical"
        page, _, _, _ = render(source, context)
        self.assertNotIn("Can start", page)
        self.assertIn("Reconcile before starting", page)

    def test_unclosed_inner_fence_with_even_fence_lines_is_rejected(self):
        source, context = self.two_phase()
        for opener, closer in (("````bash", "```"), ("```bash", "```bash")):
            with self.subTest(opener=opener):
                bad = source.replace("```text\nImplement Phase 2.", f"`````text\nImplement Phase 2.\n{opener}\nnpm test\n{closer}").replace(
                    "it is the last phase.\n```", "it is the last phase.\n`````")
                with self.assertRaisesRegex(ValueError, "fence"):
                    render(bad, context)

    def test_changed_plan_phase_table_offers_no_start(self):
        source, context = self.two_phase()
        Path(context["documents"][0]["path"]).write_text("Changed")
        self.assertNotIn("Can start", render(source, context)[0])

    def test_inline_code_at_line_start_is_not_a_fence(self):
        source, context = self.two_phase()
        source = source.replace("Implement Phase 2.", "Implement Phase 2.\n```npm test``` must pass.")
        self.assertEqual(len(render(source, context).pairs), 2)

    def run_main(self, directory, source, context, *extra):
        (directory / "in.md").write_text(source, encoding="utf-8")
        (directory / "in.json").write_text(json.dumps(context), encoding="utf-8")
        argv = ["render_report.py", "--report", str(directory / "in.md"), "--context", str(directory / "in.json"),
                "--output", str(directory / "report.html"), *extra]
        out, err, code = io.StringIO(), io.StringIO(), 0
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                render_report.main()
            except SystemExit as exit_:
                code = exit_.code or 0
        return code, out.getvalue(), err.getvalue()

    def test_open_launches_browser_after_report_is_written(self):
        out = Path(self.directory.name) / "run dir"
        out.mkdir()
        calls = []
        def fake_open(path):
            calls.append(path)
            self.assertTrue((out / "report.html").is_file())
            return True, ""
        with mock.patch.object(render_report, "open_report", fake_open):
            code, stdout, _ = self.run_main(out, *self.two_phase(), "--open")
        self.assertEqual(code, 0)
        self.assertEqual(calls, [(out / "report.html").resolve()])
        self.assertIs(json.loads(stdout)["opened"], True)

    def test_open_failure_still_renders(self):
        for outcome in ((False, "no display"), IndexError("list index out of range")):
            out = Path(self.directory.name) / type(outcome).__name__
            out.mkdir()
            if isinstance(outcome, tuple):
                patch = mock.patch.object(render_report, "open_report", return_value=outcome)
            else:  # webbrowser.get() itself raises for a malformed $BROWSER
                patch = mock.patch("webbrowser.get", side_effect=outcome)
            with patch, mock.patch.object(sys, "platform", "linux"), mock.patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True):
                code, stdout, stderr = self.run_main(out, *self.two_phase(), "--open")
            self.assertEqual(code, 0)
            self.assertIs(json.loads(stdout)["opened"], False)
            self.assertEqual(len(stderr.strip().splitlines()), 1)
            self.assertIn("Browser not opened", stderr)

    def test_without_open_flag_no_browser_and_no_opened_key(self):
        with mock.patch.object(render_report, "open_report") as opener:
            code, stdout, _ = self.run_main(Path(self.directory.name), *self.two_phase())
        self.assertEqual(code, 0)
        opener.assert_not_called()
        self.assertNotIn("opened", json.loads(stdout))

    def test_rejected_report_with_open_calls_no_browser(self):
        source, context = self.two_phase()
        with mock.patch.object(render_report, "open_report") as opener:
            code, _, _ = self.run_main(Path(self.directory.name), source.replace("**Ready.**", "**Maybe.**"), context, "--open")
        self.assertEqual(code, 1)
        opener.assert_not_called()

    def test_open_report_skips_without_display(self):
        with mock.patch.object(sys, "platform", "linux"), mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch("webbrowser.get") as get:
            self.assertEqual(open_report(Path("/tmp/x/report.html"))[0], False)
        get.assert_not_called()

    def test_open_report_refuses_console_browser(self):
        for platform in ("linux", "darwin", "win32"):
            for browser in (webbrowser.GenericBrowser("lynx"), webbrowser.Elinks("elinks")):
                with mock.patch.object(sys, "platform", platform), mock.patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True), \
                     mock.patch("webbrowser.get", return_value=browser), mock.patch.object(browser, "open") as launch:
                    self.assertEqual(open_report(Path("/tmp/x/report.html")), (False, "no graphical browser"))
                launch.assert_not_called()

    def test_open_report_uses_percent_encoded_file_uri(self):
        browser = mock.Mock(spec=webbrowser.BackgroundBrowser)
        browser.open.return_value = True
        path = Path(self.directory.name).resolve() / "run dir" / "report.html"
        with mock.patch.object(sys, "platform", "linux"), mock.patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True), \
             mock.patch("webbrowser.get", return_value=browser):
            self.assertEqual(open_report(path), (True, ""))
        browser.open.assert_called_once_with(path.as_uri(), new=2)
        self.assertTrue(path.as_uri().startswith("file:///"))
        self.assertTrue(path.as_uri().endswith("/run%20dir/report.html"))

    def test_open_report_returns_false_when_browser_raises(self):
        browser = mock.Mock(spec=webbrowser.BackgroundBrowser)
        browser.open.side_effect = webbrowser.Error("boom")
        for get in (mock.patch("webbrowser.get", return_value=browser), mock.patch("webbrowser.get", side_effect=ValueError("No closing quotation")),
                    mock.patch("webbrowser.get", side_effect=IndexError("list index out of range"))):
            with mock.patch.object(sys, "platform", "linux"), mock.patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True), get:
                opened, reason = open_report(Path(self.directory.name).resolve() / "report.html")
            self.assertIs(opened, False)
            self.assertTrue(reason)
        self.assertEqual(browser.open.call_count, 1)

    def test_open_report_hides_output_from_the_browser(self):
        devnull = os.stat(os.devnull)
        before = os.fstat(1)
        seen = []
        browser = mock.Mock(spec=webbrowser.BackgroundBrowser)
        browser.open.side_effect = lambda *args, **kwargs: seen.append([os.path.samestat(os.fstat(fd), devnull) for fd in (0, 1, 2)]) or True
        with mock.patch.object(sys, "platform", "linux"), mock.patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True), \
             mock.patch("webbrowser.get", return_value=browser):
            self.assertEqual(open_report(Path(self.directory.name).resolve() / "report.html"), (True, ""))
        self.assertEqual(seen, [[True, True, True]])
        self.assertTrue(os.path.samestat(os.fstat(1), before))

    @unittest.skipIf(sys.platform == "win32", "uses a POSIX shell as the stand-in browser")
    def test_open_does_not_keep_a_capturing_caller_waiting(self):
        # A background "browser" that outlives the renderer must not hold its output pipes open.
        directory = Path(self.directory.name)
        source, context = self.two_phase()
        (directory / "in.md").write_text(source, encoding="utf-8")
        (directory / "in.json").write_text(json.dumps(context), encoding="utf-8")
        # The stand-in replaces webbrowser.get() inside the child, so no real browser can start.
        child = (f"import sys, webbrowser; sys.path.insert(0, {str(Path(__file__).parent)!r}); import render_report; "
                 "webbrowser.get = lambda: webbrowser.BackgroundBrowser(['sh', '-c', 'sleep 10', '%s']); "
                 "render_report.main()")
        argv = ["--report", str(directory / "in.md"), "--context", str(directory / "in.json"), "--output", str(directory / "report.html"), "--open"]
        result = subprocess.run([sys.executable, "-c", child, *argv], capture_output=True, text=True,
                                env=dict(os.environ, DISPLAY=":0"), timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIs(json.loads(result.stdout)["opened"], True)


    def panel(self, page, name):
        """Return one tab panel's markup, up to the next panel or the end of main."""
        start = page.index(f'<section id="panel-{name}"')
        ends = [page.find(marker, start + 1) for marker in ('<section id="panel-', '</main>')]
        return page[start:min(end for end in ends if end != -1)]

    def test_v4_layout_order(self):
        for context in (self.modern_context(), self.v4_context()):
            with self.subTest(version=context["format_version"]):
                context["decisions_without_reply"] = [{"question": "Q?", "decision": "D.", "reason": "R."}]
                self.check_v4_layout(render(REPORT, context)[0], context["format_version"] == 4)

    def check_v4_layout(self, page, rerun):
        markers = ('<header class="hero"', '<p class="kicker">plan-validation · plan review for the maintainer · Evidence as of 2026-10-14</p>',
                   '<h1><em>Example</em></h1>', '<div class="scores"', '<div role="tablist" class="tabs" hidden',
                   '<section id="panel-summary"', '<section id="panel-full"')
        positions = [page.index(marker) for marker in markers]
        self.assertEqual(positions, sorted(positions))
        full = self.panel(page, "full")
        for number, heading in enumerate(render_report.READABLE_HEADINGS, 1):
            self.assertIn(f'<h2 id="heading-{number}">{heading}</h2>', full)
        self.assertLess(full.index('id="section-8"'), full.index('id="defaulted-decisions"'))
        self.assertLess(full.index('id="defaulted-decisions"'), full.index('class="identity"'))
        summary = self.panel(page, "summary")
        if rerun:
            self.assertLess(summary.index('class="card next"'), summary.index('<div id="rerun" class="card rerun">'))
        else:
            self.assertNotIn('id="rerun"', summary)

    def test_v4_status_pills(self):
        page, _, _, _ = render(REPORT, self.modern_context())
        pills = page[page.index('<ul class="pills"'):page.index('</ul>', page.index('<ul class="pills"'))]
        self.assertIn('<span>Ready</span>', pills)
        self.assertIn("1 phase · 1 task", pills)
        self.assertNotIn("Historical", pills)
        source, context = self.two_phase()
        context["handoff_status"] = "historical"
        page, _, _, _ = render(source, context)
        pills = page[page.index('<ul class="pills"'):page.index('</ul>', page.index('<ul class="pills"'))]
        self.assertIn("2 phases · 2 tasks", pills)
        self.assertIn("<span>Historical</span>", pills)

    def test_v4_optional_tabs(self):
        page, _, _, _ = render(REPORT, self.modern_context())
        for name in ("answer", "watch"):
            self.assertNotIn(f'id="panel-{name}"', page)
            self.assertNotIn(f'id="tab-{name}"', page)
        self.assertNotIn('data-open-tab="', page)
        summary = self.panel(page, "summary")
        self.assertEqual(summary.count('<div class="count count-none"><strong>None</strong>'), 2)
        self.assertNotIn('<a class="count"', summary)

        # D2 holds back work, which only a Ready after approvals verdict allows.
        source = REPORT.replace("No blockers.", "Pending approvals D1 and D2.").replace("**Ready.**", "**Ready after approvals.**")
        context = self.modern_context()
        decision = {"question": "Approve?", "recommendation": "Approve it.", "confidence": "High", "holds_back": "Nothing"}
        context["open_decisions"] = [dict(decision, id="D1"), dict(decision, id="D2", holds_back="Phase 2")]
        context["watch_list"] = [{"kind": kind, "title": f"{kind} item", "body": "Body."} for kind in ("gap", "limit", "risk", "fixed")]
        page, _, _, _ = render(*self.phase_1_waits(source, context, "D2"))
        tab = page[page.index('id="tab-answer"'):page.index('</button>', page.index('id="tab-answer"'))]
        self.assertIn("Needs your answer", tab)
        self.assertIn('<span class="badge">2</span>', tab)
        answer = self.panel(page, "answer")
        rows = re.findall(r"<tr>.*?</tr>", answer[answer.index("<tbody>"):])
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertIn('href="#section-6"', row)
        summary = self.panel(page, "summary")
        # Count cards are links to their panels, so they work without JavaScript too.
        self.assertIn('<a class="count" href="#panel-answer" data-open-tab="answer"><strong>2</strong>', summary)
        self.assertIn('<a class="count" href="#panel-watch" data-open-tab="watch"><strong>4</strong><span>items on the watch list</span>', summary)
        self.assertIn('id="panel-answer"', page)
        self.assertIn('id="panel-watch"', page)
        self.assertNotIn("Approve it.", summary)
        cards = re.findall(r'<article class="watch watch-(\w+)">(.*?)</article>', self.panel(page, "watch"), re.S)
        self.assertEqual([kind for kind, _ in cards], ["gap", "limit", "risk", "fixed"])
        for kind, card in cards:
            self.assertIn(f"<span>{kind.capitalize()}</span>", card)

    def test_v4_prompt_ids_are_unique_and_match_handoff(self):
        source, context = self.two_phase()
        source = source.replace("Phase 1", "Phase 1.2")
        context["phases"][0]["id"] = "1.2"
        context["diagrams"] = [copy.deepcopy(ZONES_DIAGRAM), copy.deepcopy(ZONES_DIAGRAM)]
        out = Path(self.directory.name) / "ids"
        out.mkdir()
        result = self.run_renderer(out, source, context)
        self.assertEqual(result.returncode, 0, result.stderr)
        page = (out / "report.html").read_text(encoding="utf-8")
        ids = re.findall(r'\sid="([^"]+)"', page)
        self.assertEqual(len(ids), len(set(ids)))
        texts = {}
        for name in ("summary-handoff-1.2", "handoff-1.2"):
            match = re.search(rf'<pre id="{re.escape(name)}"[^>]*>(.*?)</pre>', page, re.S)
            texts[name] = html.unescape(match.group(1))
        self.assertEqual(texts["summary-handoff-1.2"], texts["handoff-1.2"])
        self.assertEqual(texts["handoff-1.2"] + "\n", (out / "handoff.txt").read_text(encoding="utf-8"))
        targets = re.findall(r'data-copy-target="([^"]+)"', page)
        self.assertEqual(targets, ["summary-handoff-1.2", "handoff-1.2", "handoff-2"])
        self.assertTrue(set(targets) <= set(ids))

    def test_v4_historical_summary_has_no_copy_button(self):
        for change in ("status", "document"):
            with self.subTest(change=change):
                context = self.modern_context()
                if change == "status":
                    context["handoff_status"] = "historical"
                else:
                    plan = Path(context["documents"][0]["path"])
                    plan.write_text("Changed")
                    self.addCleanup(plan.write_text, "PLAN")
                page, _, current, _ = render(REPORT, context)
                self.assertFalse(current)
                summary = self.panel(page, "summary")
                self.assertNotIn('data-copy-target="summary-handoff', summary)
                self.assertIn("This is a historical prompt.", summary)
                self.assertEqual(change == "document", render_report.V5_DRIFT_TEXT in summary)
                self.assertEqual(change == "status", "Git state or approvals changed after this validation." in summary)
                self.assertNotIn("Revalidate", page)
                self.assertNotIn("Run validation again", summary)
                self.assertIn('<pre id="summary-handoff-1"', summary)
                self.assertNotIn('href="handoff.txt"', page)

    def test_v4_summary_shows_remediation_prompt_when_no_phase_is_ready(self):
        source = REPORT.replace("**Ready.**", "**Not ready.**").replace(
            "Implement the approved scope now.", "Resume validation. Do not start dependent implementation.")
        page, _, _, _ = render(source, self.modern_context())
        summary = self.panel(page, "summary")
        self.assertIn('data-copy-target="summary-handoff"', summary)
        self.assertIn('<pre id="summary-handoff"', summary)
        self.assertIn("Resume validation.", summary)
        self.assertIn("Waits for remediation", summary)
        self.assertNotIn("Can start", page)

    def test_v4_page_contract(self):
        page, _, _, _ = render(REPORT, self.modern_context())
        self.assertIn("<title>Example</title>", page)
        js = (ASSETS / "report-v4.js").read_text()
        digest = base64.b64encode(hashlib.sha256(js.encode()).digest()).decode()
        self.assertIn(f"script-src 'sha256-{digest}'", page)
        self.assertIn(f"<script>{js}</script>", page)
        self.assertEqual(page.count("<script>"), 1)
        self.assertNotRegex(page.replace("http://www.w3.org/2000/svg", ""), r"https?://")
        icon = (ASSETS / "report-icon.svg").read_text().strip()
        inner = icon[icon.index(">") + 1:]
        self.assertIn(inner, page)
        tag = page[page.rindex("<svg", 0, page.index(inner)):page.index(inner)]
        self.assertIn('aria-hidden="true"', tag)
        self.assertLessEqual(set(re.findall(r"<([a-z]+)", icon)), {"svg", "rect", "path", "circle"})
        self.assertNotRegex(icon.lower(), r"href|url\(|script|style|\sid=")

    def test_v4_js_routes_hash_to_full_report(self):
        js = (ASSETS / "report-v4.js").read_text()
        for text in ("hashchange", "aria-selected", "ArrowRight", "ArrowLeft", '"Home"', '"End"', "beforeprint", "afterprint",
                     # A modified or non-primary click opens a new tab, so it must not switch this page's panel.
                     "event.button !== 0", "event.ctrlKey", "event.metaKey", "event.shiftKey", "event.altKey"):
            self.assertIn(text, js)
        # A count card is a link: a plain click chooses its tab without following the link, and a
        # modified click is left to the browser, like every other link on the page.
        handler = re.search(r'querySelectorAll\("\[data-open-tab\]"\).*?\n  \}\);', js, re.S).group(0)
        self.assertLess(handler.index("plainClick(event)"), handler.index("event.preventDefault()"))
        self.assertLess(handler.index("event.preventDefault()"), handler.index("choose(tab)"))
        self.assertIn("if (!plainClick(event)) return;", js)

    def test_v4_icon_follows_colour_tokens(self):
        icon = (ASSETS / "report-icon.svg").read_text()
        css = (ASSETS / "report-v4.css").read_text()
        shapes = re.findall(r"<(?:rect|path|circle)\b[^>]*>", icon)
        self.assertTrue(shapes)
        for shape in shapes:
            name = re.search(r'class="(ri-[a-z]+)"', shape)
            self.assertIsNotNone(name, shape)
            self.assertRegex(css, rf"\.hero-icon \.{name.group(1)}\{{[^}}]*var\(--")

    def test_v4_no_js_shows_everything(self):
        source = REPORT.replace("No blockers.", "Pending approvals D1.")
        context = self.modern_context()
        context["open_decisions"] = [{"id": "D1", "question": "Approve?", "recommendation": "Approve it.",
                                      "confidence": "High", "holds_back": "Nothing"}]
        context["watch_list"] = [{"kind": "gap", "title": "Gap item", "body": "Body."}]
        page, _, _, _ = render(source, context)
        panels = re.findall(r'<section [^>]*role="tabpanel"[^>]*>', page)
        self.assertEqual(len(panels), 4)
        for tag in panels:
            self.assertNotRegex(tag, r"\shidden(?:[\s=>])")
        tablist = re.search(r'<div role="tablist"[^>]*>', page).group(0)
        self.assertRegex(tablist, r"\shidden(?:[\s=>])")

    def test_v4_css_scrolls_diagrams_not_page(self):
        css = (ASSETS / "report-v4.css").read_text()
        for text in (".dg-wrap{overflow-x:auto", ".fig{min-width:0", "[hidden]{display:none!important}",
                     ".fig:has(.dg-w3){grid-column:1/-1}", "prefers-color-scheme: dark",
                     ':root[data-theme="dark"]', ':root:not([data-theme="light"])'):
            self.assertIn(text, css)
        for name, width in (("dg-w1", 232), ("dg-w2", 584), ("dg-w3", 936), ("dg-flow", 608)):
            self.assertRegex(css, rf"\.{name}\{{[^}}]*min-width:{width}px")
        self.assertRegex(css, r"(?<![\w.-])pre\{[^}]*white-space:pre-wrap[^}]*overflow-wrap:anywhere")
        self.assertRegex(css, r"(?<![\w.-])code\{[^}]*overflow-wrap:anywhere")
        self.assertRegex(css, r"\.identity small\{[^}]*overflow-wrap:anywhere")
        # Count-card hints and status chips hold agent text such as a long holds_back path.
        self.assertRegex(css, r"\.count\{[^}]*overflow-wrap:anywhere")
        self.assertRegex(css, r"\.chip\{[^}]*overflow-wrap:anywhere")
        self.assertRegex(css, r"(?<![\w.-])body\{[^}]*background:")
        # Diagram text sizes match the geometry in diagrams.py; marker heads are never dashed.
        self.assertRegex(css, r"\.t,\.zl,\.lb,\.numt\{[^}]*font-size:13px")
        self.assertRegex(css, r"\.s,\.ls\{[^}]*font-size:11px")
        self.assertIn("marker path{stroke:none", css)
        self.assertNotRegex(css, r"(?<![\]\w-])\.ar-dash\{[^}]*dasharray")
        # In print a wide diagram scales down to the page width instead of being clipped.
        print_css = css[css.index("@media print"):]
        self.assertRegex(print_css, r"\.dg-wrap svg\{[^}]*min-width:0[^}]*max-width:100%")

    def legacy_documents(self):
        root = Path(self.directory.name)
        documents = []
        for label in ("PLAN", "SPEC"):
            path = root / f"{label}.md"
            path.write_text(label)
            documents.append({"label": label, "path": str(path), "sha256": hashlib.sha256(label.encode()).hexdigest()})
        return documents

    def v3_saved_context(self):
        return {
            "title": "Example", "validation_date": "2026-10-14", "kind": "saved",
            "review_status": "complete", "handoff_status": "current", "summary": "The approved scope is ready.",
            "freshness": "Branch and base checked; recorded tests were not repeated.",
            "documents": self.legacy_documents(),
            "scope": {"explanation": "Same scope.", "approval": "No expansion.", "rows": [
                {"metric": "Delivery phases", "original": "1", "revised": "1", "reason": "Unchanged."},
                {"metric": "Implementation tasks", "original": "1", "revised": "1", "reason": "Unchanged."},
                {"metric": "Supporting tasks", "original": "1", "revised": "1", "reason": "Unchanged."},
                {"metric": "Numbered tasks", "original": "1", "revised": "1", "reason": "Unchanged."},
                {"metric": "Dependencies / services", "original": "1", "revised": "1", "reason": "Unchanged."},
            ]},
            "format_version": 3,
            "task_inventory": ["1"],
            "phases": [{"id": "1", "title": "Example", "tasks": ["1"], "docs_only": False, "security_review": False, "status": "ready"}],
            "feature": {
                "summary": "A reader requests a document and sees the result.",
                "steps": [
                    {"title": "Choose a document", "description": "The reader selects a saved document."},
                    {"title": "Check access", "description": "The application checks the reader's permission."},
                    {"title": "Show the result", "description": "The document opens, or an explanation appears."},
                ],
            },
            "decisions_without_reply": [],
        }

    def legacy_cases(self):
        v1 = self.v3_saved_context()
        for key in ("format_version", "task_inventory", "phases", "feature", "decisions_without_reply"):
            del v1[key]
        v2 = self.v3_saved_context()
        v2["format_version"] = 2
        del v2["task_inventory"], v2["phases"]
        two_phases = self.v3_saved_context()
        two_phases["task_inventory"] = ["1", "2"]
        two_phases["phases"] = [
            {"id": "1", "title": "Example", "tasks": ["1"], "docs_only": False, "security_review": False, "status": "ready"},
            {"id": "2", "title": "Example", "tasks": ["2"], "docs_only": False, "security_review": False, "status": "ready"},
        ]
        two_source = LEGACY_REPORT.split("## 8. Fresh-session handoff")[0] + "## 8. Fresh-session handoff\n" + (
            "```text\nImplement Phase 1. Stop at the end of Phase 1 and print the Phase 2 prompt from the report; do not start it.\n```\n"
            "```text\nImplement Phase 2. Confirm Phase 1 is merged. Stop at the end of Phase 2; it is the last phase.\n```\n")
        remediation = self.v3_saved_context()
        remediation["task_inventory"] = ["1", "2"]
        remediation["phases"] = [
            {"id": "1", "title": "Example", "tasks": ["1"], "docs_only": False, "security_review": False, "status": "waiting", "waits_for": "D1"},
            {"id": "2", "title": "Example", "tasks": ["2"], "docs_only": False, "security_review": False, "status": "waiting", "waits_for": "D1"},
        ]
        remediation_source = LEGACY_REPORT.split("## 8.")[0].replace("**Ready.**", "**Ready after approvals.**") + (
            "## 8. Fresh-session handoff\n```text\nRecord D1, then re-render the report. Do not start dependent implementation.\n```\n")
        historical = self.v3_saved_context()
        historical["handoff_status"] = "historical"
        return {
            "v1": (LEGACY_REPORT, v1),
            "v2": (LEGACY_REPORT, v2),
            "v3": (LEGACY_REPORT, self.v3_saved_context()),
            "v3-two-phases": (two_source, two_phases),
            "v3-remediation": (remediation_source, remediation),
            "v3-historical": (LEGACY_REPORT, historical),
        }

    def test_legacy_output_is_frozen(self):
        actual = {
            key: hashlib.sha256(normalized(render(source, context)[0], self.directory.name).encode()).hexdigest()
            for key, (source, context) in self.legacy_cases().items()
        }
        self.assertEqual(actual, LEGACY_DIGESTS)


    def v4_saved_cases(self):
        """Saved version 4 renders: a no, a held yes, a historical stop and a changed plan."""
        documents = self.legacy_documents()

        def context(**changes):
            result = copy.deepcopy(V4_FROZEN_CONTEXT)
            result["documents"] = copy.deepcopy(documents)
            result.update(changes)
            return result

        held_source = V4_FROZEN_REPORT.replace("## 8. Fresh-session handoff\n",
                                               "## 8. Fresh-session handoff\n" + V4_FROZEN_RUN_FIRST_TEXT + "\n\n", 1)
        yes = {"recommendation": "yes", "reasons": ["The delay cap is still open."], "prompt": V4_FROZEN_RERUN_PROMPT}
        stop = {"recommendation": "stop", "reasons": ["The blocker needs the maintainer's decision."]}
        # The changed plan keeps the name PLAN.md, so validation_run.plan_key still ends its path,
        # and lives in its own folder, so the other cases still render as current.
        drift = context()
        changed = Path(self.directory.name) / "drift" / "PLAN.md"
        changed.parent.mkdir(exist_ok=True)
        changed.write_text("Changed")
        drift["documents"][0]["path"] = str(changed)
        return {
            "v4-no": (V4_FROZEN_REPORT, context()),
            "v4-yes-held": (held_source, context(rerun=yes)),
            "v4-stop-historical": (V4_FROZEN_REPORT, context(rerun=stop, handoff_status="historical")),
            "v4-drift": (V4_FROZEN_REPORT, drift),
        }

    def test_v4_saved_output_is_frozen(self):
        actual = {}
        for key, (source, context) in self.v4_saved_cases().items():
            rendered = render(source, context)
            blob = "\0".join((normalized(rendered[0], self.directory.name), rendered[1], rendered.prefix,
                               *(f"{phase}:{prompt}" for phase, prompt in rendered.pairs)))
            actual[key] = hashlib.sha256(blob.encode()).hexdigest()
            # Each case still shows what it pins: held prompts, a historical stop, a changed plan.
            self.assertEqual(rendered.held, key == "v4-yes-held", key)
            self.assertEqual(rendered[2], key in ("v4-no", "v4-yes-held"), key)
        self.assertEqual(actual, V4_SAVED_DIGESTS)


if __name__ == "__main__":
    unittest.main()
