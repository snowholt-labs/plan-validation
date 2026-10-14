"""Contract, arithmetic, provenance and injection regressions for HTML delivery."""

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from render_report import cells, render


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
            "title": "Example", "validation_date": "2026-10-14", "kind": "new",
            "review_status": "complete", "handoff_status": "current", "summary": "The approved scope is ready.",
            "freshness": "Branch and base checked; recorded tests were not repeated.",
            "documents": documents,
            "scope": {"explanation": "Same scope.", "approval": "No expansion.", "rows": [
                {"metric": metric, "original": "1", "revised": "1", "reason": "Unchanged."}
                for metric in ("Delivery phases", "Implementation tasks", "Supporting tasks", "Numbered tasks", "Dependencies / services")
            ]},
        }

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


if __name__ == "__main__":
    unittest.main()
