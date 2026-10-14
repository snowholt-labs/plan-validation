# Fresh-session handoff

Fill every field from verified evidence and remove inapplicable lines. Do not leave placeholders. Pasting this prompt requests implementation of the named scope; it does not silently authorize additional external actions. Preserve explicit earlier permissions exactly.

```text
Implement the approved [phase/task scope] now.

Repository and source worktree: [absolute paths]
PLAN and SPEC: [absolute paths and relevant sections]
Validated document hashes: [PLAN and SPEC SHA-256]
Validated base and source state: [base SHA, branch/HEAD, document status]
Validation report and evidence: [absolute report directory]
Checks actually run: [commands, outcomes, tested SHA]
Independent review: [completion evidence and findings disposition]
Accepted limitations: [specific limits]
Dependency and alternative decisions: [decision IDs, exact names/versions, selected/original/pending/deferred state, reasons, High/Medium/Low confidence and dated evidence, or None with reason]
Research permissions and limits: [local ledger, completed/denied/unavailable lookups and remaining evidence gaps; completed lookup approvals cannot be reused]
Pending approvals and blocked tasks: [actual decisions, or None]
Independent work that can proceed: [exact tasks/checks within authorization]
Authorized actions: [actual user/repository authorization; no inferred permissions]

1. Read repository instructions, the full validation report, PLAN and SPEC. Recheck document hashes, source worktree, base and Git state. Reconcile changed state before relying on old execution evidence. Preserve unrelated work.
2. Implement only the named approved scope, using the repository's branch and review conventions. Follow its instructions on isolated worktrees and delegation. Do not repeat a start confirmation that the user already provided.
3. Run the approved focused checks. Report actual results and failures; distinguish inspected checks from executed checks. Stop dependent work for a material unexplained mismatch.
   Inspect commands and wrappers first. Do not download, install, execute or replace dependencies, change manifests/lockfiles, or enable services/plugins without the required separate authorization. Research and adopting an approach do not supply execution permission. Request approval before each new external lookup, including web and Context7; send only the approved public query/URL, never private code, plans, paths, personal data or secrets. Continue independent work when approval or access is unavailable.
4. Complete the repository's required code/security reviews, fix confirmed findings, and rerun affected checks. Identify the exact reviewed revision and limits. Never label a skipped review as passed.
5. Perform commits, pushes, PR creation, external comments, merges or deployment only when expressly authorized in the recorded permissions or the current request. Apply current checks and repository protections to the exact revision. Do not manufacture a branch strategy, bypass protection or expand scope.
6. Report what was implemented, verified and left unresolved, with links to relevant evidence. Keep production and later phases outside scope unless explicitly authorized.
```

For **Ready after approvals**, begin `Implement only the approved independent portion of [scope] now.` Identify precisely which work must wait.

For **Not ready**, replace the entire prompt with a remediation request naming the documents, current evidence, blockers and required checks. Preserve the dependency decisions, research limits, approvals and independent tasks above. Include `Do not start dependent implementation.` Do not begin with `Implement`.
