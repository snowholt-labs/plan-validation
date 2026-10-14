# Troubleshooting

## The skill does not appear

For Claude Code, run `claude plugin list` and `claude plugin details plan-validation`. Confirm the plugin is enabled and the inventory contains `validate-plan`, `validation-args` and `revise-prompt`. Use the plugin-prefixed command `/plan-validation:validate-plan`, then restart the session if needed.

For standalone Codex installation, inspect the exact installed directory and its `SKILL.md`. The three skills must be separate sibling folders. Restart Codex if discovery has not refreshed. Avoid simultaneous copies with the same skill name in several discovery locations.

## An install destination already exists

Inspect it first. It may be a customized version or another installation. Preserve changes and decide which copy to keep; the manual installation guide intentionally refuses to overwrite existing paths.

## PLAN or SPEC cannot be found

Use absolute quoted paths to the exact worktree copies. A document in another worktree may contain uncommitted changes that are absent from the main checkout. Correct the plan's linked `**Spec:**` path if it is stale; do not substitute a same-named file without verifying it.

## Rehearsal cannot run

The workflow does not install dependencies or fetch credentials. Missing prerequisites, forbidden local suites or commands with unauthorized external side effects are reported as execution limits. Resolve the specific prerequisite or request an explicitly read-only review; do not relabel an unexecuted check as passing.

## No independent reviewer is available

The report stays Not ready and identifies the missing cold read. Use a host with permitted fresh-agent review or supply a separate completed review. Self-review is useful but is not independent review.

## The report says the handoff is historical

Documents, Git state or approvals changed or could not be checked. Revalidate the changed scope. Do not edit hashes or status fields merely to enable the copy button.

## The renderer rejects the report

Use the [bundled report contract](https://github.com/snowholt/plan-validation/blob/main/skills/validate-plan/references/report-contract.md). Confirm eight numbered sections, five dimensions plus an average in each score table, complete scope metadata and a suitable handoff. Keep the error and original evidence until repaired.

## The browser cannot copy the prompt

Clipboard permissions vary, especially for `file://` pages. Select the complete prompt or open the generated `handoff.txt`. A historical report deliberately does not offer a current implementation prompt.

## Report a reproducible failure

Include release, host/version, OS, the exact relevant command and error lines, plus a minimal redacted example. [Open an issue](https://github.com/snowholt/plan-validation/issues/new/choose). Do not include credentials or private project documents.
