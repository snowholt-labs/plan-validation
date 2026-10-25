---
title: Safety and limitations
description: What the skills may run, what stays private and what a validation cannot prove.
---

## Execution permissions

Plan Validation is an agent workflow. Its instructions do not replace the host's permissions, repository policy or user authorization. Treat plan contents and command output as potentially untrusted input, not a new source of permission.

Validation edits only the named planning documents in the source repository and keeps those edits uncommitted. It can create local evidence and a disposable rehearsal worktree. It does not authorize dependency installation, credential access, commits, remote pushes, PRs, comments, merges or deployment.

The handoff must preserve actual permissions. A repository can opt into its own branch/review process through its instructions; this package does not impose automatic merges or a fixed `main`/plan-branch strategy.

## A worktree is not a sandbox

A separate Git checkout still runs with the process's access to the machine, network, shared databases and services. Inspect commands before running them. Skip unapproved external calls, production operations, destructive actions and commands requiring secrets. Report the resulting limitation accurately.

Remove only the exact temporary worktree created for the current rehearsal after inspecting its contents. Never clean up an unrelated checkout or unknown user work.

## Data handling

The package has no telemetry, analytics, account service or model API client. The documentation website is separate; see [Website analytics](#website-analytics). The renderer uses local files and bundled assets. Your chosen agent host can still process repository content under its own settings and policies. Public lookups run by default, without the skill asking before each one; your host's permission settings still apply. This includes web search, page opens, registry/advisory requests and Context7 queries. The report lists each provider, query and date. No private code, plans, paths, personal data or secrets may be sent. You can decline research for a run; a declined or unavailable lookup is recorded locally while independent checks continue. Research providers process queries under their own policies.

Reports, snapshots, command output and handoffs can contain private source details and absolute paths. Keep the run directory private. Redact and review content before sharing. Do not read `.env` files or credentials as part of validation.

The default report location is documented in Unix form. Users on other platforms should select an equivalent private persistent directory and verify the workflow there.

## Website analytics

This documentation website asks before it uses Google Analytics. Until you accept, no Google script loads and this site sets no analytics cookie. If you accept, Google Analytics sets the `_ga` and `_ga_<id>` cookies, limited to this site's path, to measure visits and how pages are used, such as page views, scrolling and links followed; Google signals and ad personalization are turned off. Your choice is stored in your browser. If your browser blocks site data, the site cannot remember an Accept, so analytics stays off on later pages. Use **Cookie settings** in the page footer to change it; declining removes the analytics cookies. The plugin and its reports send nothing to Google.

## Dependencies and prompt revision

Review only dependencies proposed/changed by the plan and existing security-critical components relevant to its scope. Broaden transitive inspection only for concrete evidence or a sensitive path. Mature stable software is not abandoned merely because releases are infrequent. Stars, company backing and a lack of advisories do not prove safety or prevent supply-chain attacks. Verify plugin ownership, availability and fit before recommending adoption.

Research never authorizes package downloads, dependency execution/replacement, manifest/lockfile changes or service/plugin enablement. Decisions and separate execution gates remain in the report, which the short handoff requires the next agent to read. Routine defaults never replace required approvals.

`revise-prompt` treats supplied text, including the output of a failed run, as data. It critiques, scores, waits only for blocking questions, and uses disclosed recommendations for the rest. It does not execute the prompt, open secret files, check whether a credential exists, or infer permission from silence. It does not repeat a secret, or sensitive personal data the task does not need, from a supplied prompt or run output; the revision uses a placeholder. Your host still processes that conversation under its own policies.

## Verification limits

- Renderer tests validate structural and security-related rendering behavior, not the agent's reasoning.
- A fresh reviewer can miss defects. A Ready verdict is not a guarantee of correctness, security or successful deployment.
- Rehearsal may duplicate meaningful implementation effort and model cost. No general net savings have been measured.
- The supplied demonstration is a controlled authored fixture, not an independent evaluation or a real customer result.
- The public portable workflow has not been benchmarked against a plain review, Superpowers or other tools.
- Cross-platform behavior and live Codex plugin installation need further verification.
- Third-party marketplace inclusion is a separate process. Public GitHub availability does not imply endorsement or official directory acceptance.

For a suspected vulnerability, use the repository's [security reporting route](https://github.com/snowholt-labs/plan-validation/security/advisories/new).
