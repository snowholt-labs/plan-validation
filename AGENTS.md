# AGENTS.md

Repository workflow rules for coding agents (Codex, Claude Code and others).

## Git workflow

- Never push directly to `main`. Every change goes through a branch and a pull request.
- Ask the maintainer before any merge.

### Plan work

1. Create a plan branch from `main`, for example `plan/<topic>`.
2. Implement each phase on its own branch from the plan branch and open a PR into the plan branch.
3. Squash merge the phase PR only after CI passes and `/code-review` and `/security-review` report no unresolved findings.
4. When all phases are merged, open a PR from the plan branch into `main`. Run `/code-review` and `/security-review` on the full diff to catch cross-phase issues. After CI passes, merge with a merge commit (not squash), so each phase stays visible in history.

### Other changes

Use a short-lived branch and a PR into `main`. Squash merge after CI, `/code-review` and `/security-review` pass.

### Releases

1. Open a dedicated release PR, for example from `release/vX.Y.Z`. It contains only the version bump in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and `.codex-plugin/plugin.json`, plus the `CHANGELOG.md` entry.
2. Merge after CI passes.
3. Tag `vX.Y.Z` on the merged `main` commit, then publish the GitHub release.
