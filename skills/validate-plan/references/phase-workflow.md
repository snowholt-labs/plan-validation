# Phase workflow block

Validation copies the block below into the plan once, near the top, only when the plan has no `## Phase workflow` heading. Copy it from `## Phase workflow` to the docs-only sentence, unchanged.

```markdown
## Phase workflow

Every phase follows these steps, in a fresh session, on its own phase branch.

1. Work in a git worktree for the phase branch (`superpowers:using-git-worktrees`).
2. For each task: write the failing test first and watch it fail (`superpowers:test-driven-development`), write the code, then prove it works by running the tests (`superpowers:verification-before-completion`).
3. Review the phase against the plan, spec and validation report (`superpowers:requesting-code-review`, with the plan and spec paths, the report path named in the phase prompt and the phase's base..head range).
4. Check each finding before fixing it, and push back on wrong ones (`superpowers:receiving-code-review`).
5. For any failing test or unexpected behavior, find the cause before fixing it (`superpowers:systematic-debugging`).
6. Repeat steps 3–5 until no Medium or High finding remains (Critical counts as High, Important as Medium, Minor as Low). Do not loop on wording-level findings: list them, and ask the maintainer to fix or skip each one in the end-of-phase report.
7. Run `superpowers:finishing-a-development-branch` as the readiness check: tests pass on the branch. Do not push, open a PR or merge at this step, and never merge locally into a protected or plan branch.
8. Run the code and security reviews this repository's rules require (in Claude Code, `/code-review` and `/security-review`), and fix required findings.
9. Deliver the branch as the repository's rules define (for a plan branch, a PR into that branch). Push and open a PR only when the repository's rules or the maintainer authorize it. Otherwise stop and report that the branch is ready.

A docs-only phase skips step 2's test-first rule. Its step 8 runs the reviews the repository's rules require for docs-only changes.
```
