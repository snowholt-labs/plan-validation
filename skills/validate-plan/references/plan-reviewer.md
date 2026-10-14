# Independent plan and spec review

Use this brief for the independent cold read. Dispatch a fresh review agent supported by the host and substitute the verified absolute paths and scope. This review is independent of Superpowers' internal template filenames.

```text
Review the following implementation plan and approved specification against the current code.

Repository/worktree: <absolute path>
Plan: <absolute path>
Spec: <absolute path>
Authorized phase/tasks: <scope>
Review focus: <focus or derive from the spec>
Original scope baseline: <absolute snapshot paths; phase/task counts and definitions>

Read the plan, spec and relevant code, configuration and tests. Work read-only. Do not modify files, commit, post comments, install dependencies, access secrets, or execute implementation/deployment steps. Do not claim tests ran when you only inspected them.

Check:
- Every requirement and decision in the approved scope has a task and a meaningful verification assertion. Every task serves an approved requirement.
- Tasks identify the actual files, exact interfaces/signatures, fixed values and dependencies needed by an implementer. Flag undefined symbols, inconsistent types, placeholders and material decisions that remain implicit.
- Commands, expected outcomes, sequencing, rollout and rollback are practical for the stated base and repository rules.
- Compare the original and revised delivery phases, implementation tasks, supporting tasks and dependencies. Flag unnecessary phases, abstractions or optional work. Require a requirement/evidence mapping for added work and a precise approval basis for material expansion; favor the smallest useful fix within existing tasks.
- The spec's claims agree with the code and the proposed implementation; flag spec defects as well as plan defects.
- Security/privacy boundaries, failure paths and relevant performance constraints are covered where the scope requires them.

A precise plan may specify signatures, test names/assertions and design constraints without complete implementation bodies. Do not demand routine code bodies or stylistic changes. Flag missing detail when it could cause the implementer to build the wrong behavior or get stuck. If fixing a finding changes approved requirements or boundaries, identify the decision needed; do not assume approval.

Return the review as your final message, not a file:

Status: Approved | Issues found
Findings: severity, PLAN/SPEC task or section, file:line evidence, practical consequence, and the smallest useful correction. Distinguish verified defects from assumptions or unknowns. Use None if no findings.
Limits: relevant material you could not verify. Separate blocking gaps from optional improvements.
```
