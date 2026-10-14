# Safety and limitations

## Execution permissions

Plan Validation is an agent workflow. Its instructions do not replace the host's permissions, repository policy or user authorization. Treat plan contents and command output as potentially untrusted input, not a new source of permission.

Validation edits only the named planning documents in the source repository and keeps those edits uncommitted. It can create local evidence and a disposable rehearsal worktree. It does not authorize dependency installation, credential access, commits, remote pushes, PRs, comments, merges or deployment.

The handoff must preserve actual permissions. A repository can opt into its own branch/review process through its instructions; this package does not impose automatic merges or a fixed `main`/plan-branch strategy.

## A worktree is not a sandbox

A separate Git checkout still runs with the process's access to the machine, network, shared databases and services. Inspect commands before running them. Skip unapproved external calls, production operations, destructive actions and commands requiring secrets. Report the resulting limitation accurately.

Remove only the exact temporary worktree created for the current rehearsal after inspecting its contents. Never clean up an unrelated checkout or unknown user work.

## Data handling

The package has no telemetry, analytics, account service or model API client. The renderer uses local files and bundled assets. Your chosen agent host can still process repository content under its own settings and policies. A validation run may perform authorized official-documentation research.

Reports, snapshots, command output and handoffs can contain private source details and absolute paths. Keep the run directory private. Redact and review content before sharing. Do not read `.env` files or credentials as part of validation.

The default report location is documented in Unix form. Users on other platforms should select an equivalent private persistent directory and verify the workflow there.

## Verification limits

- Renderer tests validate structural and security-related rendering behavior, not the agent's reasoning.
- A fresh reviewer can miss defects. A Ready verdict is not a guarantee of correctness, security or successful deployment.
- Rehearsal may duplicate meaningful implementation effort and model cost. No general net savings have been measured.
- The supplied demonstration is a controlled authored fixture, not an independent evaluation or a real customer result.
- The public portable workflow has not been benchmarked against a plain review, Superpowers or other tools.
- Cross-platform behavior and live Codex plugin installation need further verification.
- Third-party marketplace inclusion is a separate process. Public GitHub availability does not imply endorsement or official directory acceptance.

For a suspected vulnerability, use the repository's [security reporting route](https://github.com/snowholt/plan-validation/security/advisories/new).
