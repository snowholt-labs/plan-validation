#!/usr/bin/env python3
"""Execute the authored fixture and render a clearly labeled example report."""

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error("Output already exists; choose a new directory to preserve existing files")

    evidence = []
    for name, expected_exit in (("uncapped", 1), ("corrected", 0)):
        command = [sys.executable, "examples/retry/checks.py", name]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30)
        captured = (result.stdout + result.stderr).replace(str(ROOT), "<repository>")
        if result.returncode != expected_exit or "Ran 3 tests" not in captured:
            raise SystemExit(f"Unexpected {name} fixture outcome: {captured}")
        if name == "uncapped" and ("64 != 30" not in captured or "failures=1" not in captured):
            raise SystemExit("The expected boundary failure was not reproduced")
        evidence.append({"command": "python3 examples/retry/checks.py " + name,
                         "exit_code": result.returncode, "output": captured})

    output.mkdir(parents=True, mode=0o700)
    try:
        render(output, evidence)
    except BaseException:
        # Remove the output directory this run created; parent directories stay.
        shutil.rmtree(output)
        raise
    print("Fixture: 3 tests, 1 expected failure. Corrected control: 3 passed.")
    print(f"Example report: {output / 'report.html'}")


def render(output, evidence):
    documents = []
    for label in ("PLAN", "SPEC"):
        path = output / (label.lower() + ".md")
        path.write_bytes((ROOT / "examples/retry" / path.name).read_bytes())
        documents.append({"label": label, "path": str(path),
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    dimensions = [
        ["Correctness and spec fit", "Security and privacy", "Performance", "Maintainability and complexity", "Execution and verification readiness"],
        ["Clarity and testability", "Correctness against the code", "Security and privacy", "Scope and simplicity", "Rollout, rollback and measurement"],
    ]
    tables = []
    for names in dimensions:
        tables.append("| Dimension | Original /10 | Revised /10 | Reason / evidence |\n"
                      "| --- | --- | --- | --- |\n" +
                      "\n".join(f"| {name} | Unknown | Unknown | Authored demonstration; no document-quality evaluation. |" for name in names) +
                      "\n| Average /10 | Unknown | Unknown | No invented scores. |")
    report = f'''# Retry delay: a missing boundary

## 1. Verdict
**Not ready.** Confidence: Unknown.
Authored demonstration, not a completed agent validation. The uncapped fixture violates R3. A corrected control passes the same checks, but no independent reviewer has assessed a revised implementation plan.

## 2. PLAN comparison
{tables[0]}

## 3. SPEC comparison
{tables[1]}

## 4. Decision confidence
No subjective probability has been assigned to this demonstration.
| Decision | Confidence | Evidence | Remaining uncertainty |
| --- | --- | --- | --- |
| Original instruction omits the cap | Verified | PLAN Task 1 says 2 ** attempt; SPEC R3 requires at most 30. | No claim about how often an agent finds this. |
| Boundary failure is reproducible | Verified | Uncapped fixture: 3 tests, 1 failure, 64 != 30; corrected control: 3 passing tests. | This tiny fixture is not a general benchmark. |
| Implementation readiness | Unknown | No independent review occurred. | Real plan revision, review and handoff still needed. |

## 5. Changes
The original documents are preserved. The separate corrected control demonstrates a minimal implementation correction. No validated plan revision or added product requirement is claimed.

## 6. Open items
Blocker: revise Task 1 to include R3 and its boundary assertion, then obtain an independent cold read. This report does not authorize real implementation or external actions.

## 7. Verification and checkout
The original example failed the delay-limit check; the corrected version passed all three checks. No independent review or production test was run.

### Technical details
Executed `python3 examples/retry/checks.py uncapped`: exit 1, 3 tests, 1 failure.
Executed `python3 examples/retry/checks.py corrected`: exit 0, 3 tests passed.
Actual captured outputs are saved in evidence.json. No agent evaluation, Git rehearsal worktree, production test, model-cost measurement or independent review was performed. The script rendered fixture copies; it did not alter the original documents.

## 8. Fresh-session handoff
```text
Work in `{ROOT}`. Resume validation of the retry-delay fixture using `{output / 'plan.md'}` and `{output / 'spec.md'}`.

Read `{output / 'report.md'}`, its context.json, and repository instructions first. Confirm the saved evidence still applies. Resolve the missing delay cap and independent review within recorded permissions; rerun the three acceptance checks.

Do not start dependent implementation. Report results and any defaults chosen, then stop.
```
'''
    context = {
        "format_version": 3,
        "task_inventory": ["1"],
        "phases": [{"id": "1", "title": "Retry delay cap", "tasks": ["1"], "docs_only": False, "security_review": False,
                    "status": "waiting", "waits_for": "Remediation of the missing delay cap"}],
        "title": "Retry delay: a missing boundary",
        "validation_date": datetime.now(timezone.utc).date().isoformat(),
        "kind": "new", "review_status": "not_run", "handoff_status": "current",
        "summary": "The proposed retry feature should never wait more than 30 seconds. The plan missed that limit; the example below shows the failure and the correction.",
        "freshness": "Fixture copies checked at rendering. No repository or implementation approval is represented.",
        "provenance": "scripts/demo.py; authored public fixture, not an agent benchmark.",
        "documents": documents,
        "feature": {
            "summary": "Proposed behavior: retry an unsuccessful action with a longer wait each time, capped at 30 seconds.",
            "steps": [
                {"title": "Try the action", "description": "An unsuccessful attempt may need another try."},
                {"title": "Choose the wait", "description": "Later attempts wait longer."},
                {"title": "Apply the limit", "description": "The wait never exceeds 30 seconds. This is the missing rule."},
                {"title": "Retry", "description": "Try again after the limited wait."},
            ],
        },
        "decisions_without_reply": [],
        "scope": {"explanation": "The same one-task fixture is retained; the corrected control adds no requirement.",
                  "approval": "Teaching example only. No real implementation or external-action authorization.",
                  "rows": [{"metric": metric, "original": count, "revised": count, "reason": "Same fixture scope; no plan revision claimed."}
                           for metric, count in (("Delivery phases", "1"), ("Implementation tasks", "1"),
                                                 ("Supporting tasks", "0"), ("Numbered tasks", "1"),
                                                 ("Dependencies / services", "0"))]},
        "notes": [{"title": "Demonstration, not a benchmark", "body": "A deliberately planted defect and reference correction exercise the report. Agent effectiveness remains unmeasured."}],
    }
    module_path = ROOT / "skills/validate-plan/scripts/render_report.py"
    spec = importlib.util.spec_from_file_location("renderer", module_path)
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    page, prompt, current = renderer.render(report, context)
    if not current:
        raise SystemExit("Demo document identity check failed")
    for name, content in (("report.md", report), ("report.html", page), ("handoff.txt", prompt + "\n"),
                          ("context.json", json.dumps(context, indent=2) + "\n"),
                          ("evidence.json", json.dumps(evidence, indent=2) + "\n")):
        (output / name).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
