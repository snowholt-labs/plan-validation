"""Contract, arithmetic, provenance and injection regressions for HTML delivery."""

import base64
import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from render_report import ASSETS, HISTORICAL_PREFIX, cells, phase_handoffs, phase_plan, render


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
        context = copy.deepcopy(self.context)
        context.update({
            "format_version": 3, "kind": "new",
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
        })
        return context

    def test_feature_diagram_precedes_scores_without_replacing_evidence(self):
        page, prompt, current = render(REPORT, self.modern_context())
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
                context = self.modern_context()
                context["feature"] = feature
                with self.assertRaisesRegex(ValueError, "Feature"):
                    render(REPORT, context)

    def test_independent_feature_blocks_do_not_imply_a_sequence(self):
        context = self.modern_context()
        context["feature"]["layout"] = "blocks"
        page, _, _ = render(REPORT, context)
        overview = page[page.index('<section id="feature-overview"'):page.index('<section id="section-1"')]
        self.assertIn('<ul class="feature-blocks" role="list">', overview)
        self.assertNotIn('<ol', overview)
        self.assertNotIn('class="step-arrow"', overview)
        self.assertIn("Check access", overview)

    def test_unknown_feature_layout_is_rejected(self):
        context = self.modern_context()
        context["feature"]["layout"] = "unknown"
        with self.assertRaisesRegex(ValueError, "layout"):
            render(REPORT, context)

    def test_technical_details_collapse_but_summary_and_blockers_stay_visible(self):
        source = REPORT.replace("Recorded focused check; no production run.",
                                "Two local checks passed. No production run.\n\n### Technical details\n"
                                "```bash\npython3 checks.py\n```\nExit 0; two checks passed.")
        page, _, _ = render(source, self.modern_context())
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
        page, _, _ = render(source, self.modern_context())
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
        page, _, _ = render(source, context)
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
        context = self.modern_context()
        payload = '<img src=x onerror="alert(1)"><script>alert(2)</script>'
        context["feature"]["summary"] = payload
        context["feature"]["steps"][0]["title"] = payload
        context["feature"]["steps"][0]["description"] = payload
        context["decisions_without_reply"] = [{"question": payload, "decision": payload, "reason": payload}]
        page, _, _ = render(REPORT, context)
        self.assertNotIn("<img src=x", page)
        self.assertNotIn("<script>alert", page)
        self.assertIn("&lt;img", page)
        self.assertEqual(page.count("<script>"), 1)

    def test_new_handoffs_are_short_while_legacy_handoffs_remain_readable(self):
        source = REPORT.replace("Implement the approved scope now.", "Implement " + "detail " * 81)
        with self.assertRaisesRegex(ValueError, "80 words"):
            render(source, self.modern_context())
        self.context["kind"] = "saved"
        _, prompt, _ = render(source, self.context)
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

    def test_backticks_around_prose_do_not_bypass_the_word_limit(self):
        source = REPORT.replace("Implement the approved scope now.", "`" + "detail " * 81 + "` now.")
        with self.assertRaisesRegex(ValueError, "80 words"):
            render(source, self.modern_context())

    def test_backtick_quoted_paths_count_as_one_word(self):
        path = "`/Users/x/My Projects/" + "deep folder " * 40 + "plan.md`"
        source = REPORT.replace("Implement the approved scope now.", f"Implement the plan in {path} now.")
        _, prompt, _ = render(source, self.modern_context())
        self.assertIn(path, prompt)

    def test_hidden_section_four_tables_do_not_replace_the_visible_confidence_table(self):
        extra = "\n\n### Technical details\n| Command | Exit |\n|---|---|\n| checks.py | 0 |\n"
        source = REPORT.replace("| Readiness | 75% | Recorded focused check | No browser check |",
                                "| Readiness | 75% | Recorded focused check | No browser check |" + extra)
        page, _, _ = render(source, self.modern_context())
        self.assertIn("checks.py", page)
        table = "| Decision | Confidence | Evidence | Remaining uncertainty |\n|---|---|---|---|\n| Readiness | 75% | Recorded focused check | No browser check |"
        hidden = REPORT.replace(table, "### Technical details\n" + table)
        with self.assertRaisesRegex(ValueError, "Decision confidence"):
            render(hidden, self.modern_context())

    def test_confidence_table_is_found_after_other_tables_and_code(self):
        prefix = "| Summary | Value |\n|---|---|\n| Checks | 2 |\n\n```text\n| not | a | table |\n```\n\n"
        source = REPORT.replace("| Decision | Confidence |", prefix + "| Decision | Confidence |")
        page, _, _ = render(source, self.modern_context())
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
        context = self.modern_context()
        context["feature"]["steps"] = [{"title": f"Step {n}", "description": "Does one thing."} for n in range(7)]
        page, _, _ = render(REPORT, context)
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
                page, _, _ = render(source, self.modern_context())
                self.assertIn('<details class="technical-details">', page)
        source = REPORT.replace("No blockers.", "Summary.\r\n\r\n### technical details\r\nHidden blocker.")
        with self.assertRaisesRegex(ValueError, "Technical details"):
            render(source, self.modern_context())

    def test_modern_historical_handoff_is_called_historical(self):
        context = self.modern_context()
        context["handoff_status"] = "historical"
        page, _, _ = render(REPORT, context)
        hero = page[page.index('class="freshness"'):page.index('</p>', page.index('class="freshness"'))]
        self.assertIn("historical", hero)

    def test_complete_report_preserves_prompt_and_both_tables(self):
        page, prompt, current = render(REPORT, self.context)
        self.assertTrue(current)
        self.assertEqual(prompt, REPORT.split("```text\n")[1].split("\n```")[0])
        for number in range(1, 9):
            self.assertIn(f'id="section-{number}"', page)
        self.assertEqual(page.count("<strong>Average /10</strong>"), 2)
        self.assertIn('id="copy-prompt"', page)
        self.assertIn("6.2 <i>→</i> 9.0", page)
        self.assertIn("7.6 <i>→</i> 9.0", page)

    def test_report_embeds_the_favicon_as_an_inline_image(self):
        page, _, _ = render(REPORT, self.context)
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
        page, _, _ = render(source.replace("**6.2**", "**Unknown**"), self.context)
        self.assertIn("Unknown <i>→</i> 9.0", page)

    def test_ready_cannot_precede_reviewer_completion(self):
        for status in ("running", "not_run", None):
            self.context["review_status"] = status
            with self.assertRaisesRegex(ValueError, "cold read"):
                render(REPORT, self.context)

    def test_changed_or_missing_document_disables_start_button(self):
        plan = Path(self.context["documents"][0]["path"])
        plan.write_text("Revised after validation")
        page, prompt, current = render(REPORT, self.context)
        self.assertFalse(current)
        self.assertNotIn('id="copy-prompt"', page)
        self.assertNotIn('href="handoff.txt"', page)
        self.assertTrue(prompt.startswith("HISTORICAL PROMPT — DO NOT EXECUTE."))
        self.assertIn("historical prompt", page)
        plan.unlink()
        self.assertFalse(render(REPORT, self.context)[2])

    def test_saved_report_is_labeled_recorded(self):
        self.context["kind"] = "saved"
        page, _, _ = render(REPORT, self.context)
        self.assertIn("Saved validation", page)
        self.assertIn("Recorded: Ready", page)

    def test_git_or_approval_drift_can_disable_handoff_with_matching_files(self):
        self.context["handoff_status"] = "historical"
        page, prompt, current = render(REPORT, self.context)
        self.assertFalse(current)
        self.assertIn("Document fingerprints match", page)
        self.assertNotIn('href="handoff.txt"', page)
        self.assertNotIn('id="copy-prompt"', page)
        self.assertTrue(prompt.startswith("HISTORICAL PROMPT"))

    def test_numbered_headings_and_code_fences_inside_prompt_are_content(self):
        source = REPORT.replace("```text\n", "````text\n## 1. Follow these steps\n```bash\nprintf hello\n```\n")
        source = source.rsplit("```", 1)[0] + "````\n"
        page, prompt, _ = render(source, self.context)
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
        page, prompt, _ = render(source, self.context)
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
        page, _, _ = render(source, self.context)
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
        page, prompt, current = render(source, self.context)
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
        page, prompt, current = render(source, self.context)
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

    def test_new_reports_require_version_three(self):
        context = self.modern_context()
        context["format_version"] = 2
        with self.assertRaisesRegex(ValueError, "format_version"):
            render(REPORT, context)
        context["kind"] = "saved"
        render(REPORT, context)

    def two_phase(self):
        context = self.modern_context()
        context["task_inventory"] = ["1", "2"]
        context["phases"] = [dict(context["phases"][0], tasks=["1"]), dict(context["phases"][0], id="2", tasks=["2"])]
        prompts = ("Implement Phase 1. Stop at the end of Phase 1 and print the Phase 2 prompt from the report; do not start it.",
                   "Implement Phase 2. Stop at the end of Phase 2; it is the last phase.")
        source = REPORT.split("## 8. Fresh-session handoff")[0] + "## 8. Fresh-session handoff\n" + "".join(
            f"```text\n{prompt}\n```\n" for prompt in prompts)
        return source, context

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
        render(source.replace("Stop at the end of Phase 1 and", "Stop at the end of\nPhase 1 and"), context)

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
        with self.assertRaisesRegex(ValueError, "Do not start dependent implementation"):
            render(waiting.replace("Record D1, then", "Implement Phase 1, then"), context)

    def test_every_phase_prompt_has_the_word_limit(self):
        source, context = self.two_phase()
        with self.assertRaisesRegex(ValueError, "80 words"):
            render(source.replace("Implement Phase 2.", "Implement Phase 2. " + "detail " * 80), context)

    def test_inner_fence_in_a_phase_prompt_counts_once(self):
        source, context = self.two_phase()
        source = source.replace("```text\nImplement Phase 2.", "````text\nImplement Phase 2.\n```\nexample\n```\n").replace(
            "it is the last phase.\n```", "it is the last phase.\n````")
        self.assertEqual(len(phase_handoffs(source, context)), 2)
        self.assertIn("example", phase_handoffs(source, context)[1][1])

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
            for pid, prompt in phase_handoffs(source, context):
                text = (out / f"handoff-phase-{pid}.txt").read_text(encoding="utf-8")
                self.assertEqual(text, (HISTORICAL_PREFIX if status == "historical" else "") + prompt + "\n")
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
        page, _, _ = render(source, context)
        start = page.index('aria-label="Phase plan"')
        table = page[start:page.index("</table>", start)]
        for text in ("Tasks", "Kind", "Security review", "Status", "Docs only", "Code", "Yes — Renders untrusted text.", "Can start"):
            self.assertIn(text, table)
        self.assertEqual(table.count("<tr>"), 3)

    def test_every_copy_button_targets_an_existing_prompt(self):
        source, context = self.two_phase()
        page, _, _ = render(source, context)
        targets = re.findall(r'data-copy-target="([^"]+)"', page)
        self.assertEqual(targets, ["handoff-1", "handoff-2"])
        for target in targets:
            self.assertIn(f'<pre id="{target}"', page)
        self.assertIn("Copy Phase 2 prompt", page)
        self.assertNotIn("```text", page)

    def test_historical_phase_report_offers_no_copy_button(self):
        source, context = self.two_phase()
        context["handoff_status"] = "historical"
        page, _, _ = render(source, context)
        # report.js is inlined and names the attribute, so look for markup only.
        self.assertNotIn('data-copy-target="', page)
        self.assertNotIn('href="handoff.txt"', page)
        self.assertEqual(page.count("This is a historical prompt."), 2)

    def test_not_ready_phase_table_offers_no_start(self):
        source = REPORT.replace("**Ready.**", "**Not ready.**").replace(
            "Implement the approved scope now.", "Resume validation. Do not start dependent implementation.")
        page, _, _ = render(source, self.modern_context())
        self.assertIn("Waits for remediation", page)
        self.assertNotIn("Can start", page)
        self.assertIn("Copy remediation prompt", page)

    def test_saved_reports_keep_a_working_copy_button(self):
        page, _, _ = render(REPORT, self.context)
        self.assertIn('data-copy-target="handoff"', page)
        self.assertIn('<pre id="handoff"', page)

    def test_phase_titles_cannot_inject_markup(self):
        source, context = self.two_phase()
        context["phases"][0]["title"] = "<img src=x onerror=alert(1)>"
        context["phases"][1].update(status="waiting", waits_for="<script>alert(2)</script>")
        source = source.replace("**Ready.**", "**Ready after approvals.**").split("```text\nImplement Phase 2.")[0]
        page, _, _ = render(source, context)
        self.assertNotIn("<img src=x", page)
        self.assertNotIn("<script>alert", page)
        self.assertIn("&lt;img src=x", page)

    def test_first_phase_waiting_offers_a_remediation_copy_button(self):
        source, context = self.two_phase()
        for phase in context["phases"]:
            phase.update(status="waiting", waits_for="D1")
        source = source.split("## 8.")[0].replace("**Ready.**", "**Ready after approvals.**") + (
            "## 8. Fresh-session handoff\n```text\nRecord D1, then re-render the report. Do not start dependent implementation.\n```\n")
        page, _, _ = render(source, context)
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
        page, _, _ = render(source, context)
        self.assertNotIn("Can start", page)
        self.assertIn("Revalidate before starting", page)

    def test_inline_code_at_line_start_is_not_a_fence(self):
        source, context = self.two_phase()
        source = source.replace("Implement Phase 2.", "Implement Phase 2.\n```npm test``` must pass.")
        self.assertEqual(len(phase_handoffs(source, context)), 2)


if __name__ == "__main__":
    unittest.main()
