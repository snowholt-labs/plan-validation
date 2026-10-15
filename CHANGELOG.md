# Changelog

## Unreleased

- Shorten new fresh-session handoffs to a 50–80-word target, with explicit phase/validated-plan scope and links to the complete evidence and permission record.
- Add a local, accessible “Feature at a glance” block diagram, plain-language summaries and expandable technical evidence. Keep both complete score tables, blockers and required approvals visible.
- Use and disclose recommended defaults for unanswered routine clarifications, including prompt revision; keep required facts and approvals pending.
- Add report format version 2 while retaining legacy rendering. Existing reports and planning documents are not migrated.

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
