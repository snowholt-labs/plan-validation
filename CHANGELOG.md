# Changelog

## Unreleased

- Reject a new report whose later phase prompt does not say `Confirm Phase <previous> is merged`, and stop treating a split plan phase as one PR, so a plan run in several sessions cannot end each session without a merge. The skill follows repository branch conventions first, then the user's, and raises a one-PR delivery across phases as an approval when neither defines per-phase delivery.

## 0.3.0 — 2026-10-20

- Group a validated plan's tasks into small phases and give one launch prompt per ready phase, so each phase runs in its own fresh session and stops at the phase end. Phases keep plan order and plan phase boundaries, target 3–5 tasks, and flag docs-only phases and phases that need a security review.
- Add report format version 3 for new reports: a validated task inventory and phase list, one prompt of at most 80 words per ready phase with a checked `Stop at the end of Phase <id>` sentence, `handoff-phase-<id>.txt` files, a phase table and one copy button per phase prompt. Not ready reports, and reports whose first phase waits for an approval, keep one remediation prompt.
- After earlier phases merge, validate the remaining phases as a phase-only validation instead of re-rendering the old report. Historical phase tables show "Revalidate before starting".
- Add a "Phased implementation" documentation page with the recommended per-phase workflow: one fresh session per phase after the previous phase merges, a severity-based review loop, a security review only for flagged phases, and full code and security review on the plan-to-main PR. The repository's own `AGENTS.md` adopts this workflow, and the evaluation cases cover phase grouping, waiting phases and between-phase changes.
- Relicense the project from MIT to the Apache License 2.0 and add a NOTICE file that credits the original project and its creator. Versions up to 0.2.0 remain available under the MIT License.
- Add plugin icons: light, dark and composer icons for Codex, and a directory icon for Anthropic's plugin directory. Generated HTML reports show an inline favicon.
- Shorten new fresh-session handoffs to a 50–80-word target, with explicit phase/validated-plan scope and links to the complete evidence and permission record.
- Add a local, accessible “Feature at a glance” block diagram, plain-language summaries and expandable technical evidence. Keep both complete score tables, blockers and required approvals visible.
- Use and disclose recommended defaults for unanswered routine clarifications, including prompt revision; keep required facts and approvals pending.
- Run public research by default instead of asking before each lookup; host permission settings still apply. Queries stay public-only, every lookup is listed in the report, and users can decline research for a run.
- Stop asking routine questions during validation. Apply the recommended best practice and disclose it; record choices that need approval as a menu with a recommendation in the report, without pausing independent work.
- Tell the implementing agent to continue through passing steps and reviews without asking to continue, stopping only for a required approval, an unfixable failure or the scope end.
- Suggest a reasoning effort for the validation and next sessions; never set or require one.
- Report format version 2 (the "Feature at a glance" diagram and "Decisions made without your reply") was added during this release's development and is superseded by version 3, which keeps both. The renderer still reads saved version 1 and 2 reports. Existing reports and planning documents are not migrated.

## 0.2.0 — 2026-10-14

- Add focused review of proposed/changed dependencies and relevant existing security-critical components, with dated primary evidence and High/Medium/Low decision confidence.
- Compare the original approach with at most two suitable alternatives, including the existing implementation or no dependency; verify plugin ownership, availability and fit.
- Require approval before each external lookup, including web and Context7; exclude confidential queries and continue independent checks when permission/access is unavailable.
- Preserve installation/execution/service boundaries, inspect planned commands before rehearsal, and record actionable decisions in the report and handoff.
- Add portable `revise-prompt`: critique, score, clarify, wait for complete answers or explicit defaults, then produce a copy-ready revision without executing the prompt. The personal source skill remains unchanged.
- Preserve the eight-section HTML contract, both PLAN/SPEC score tables, scope changes and full handoff; add dependency comparison and no-concern renderer regressions.
- Update manifests, documentation, privacy disclosures, examples and wiki. No runtime dependencies or telemetry added.

Verification evidence and limitations are recorded in [docs/verification.md](docs/verification.md). Directory scanning, reviewer approval and live listing remain separate from GitHub release publication.

## 0.1.0 — 2026-10-14

Initial public pilot.

- Bundle `validate-plan` and `validation-args` as a Claude Code plugin and installable Codex skills.
- Preserve the existing HTML renderer, report assets and regression tests.
- Adapt private host-specific instructions into a shared workflow with explicit invocation, repository-defined permissions and no mandatory external planning plugin.
- Include a local reviewer brief, evidence/report contract and permission-preserving implementation handoff.
- Document installation, first use, updates, removal, privacy and verification limits.
- Add a deterministic demonstration, package checks and CI.

The release does not establish end-to-end agent reliability, cross-platform behavior or comparative time/cost improvements.
