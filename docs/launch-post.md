# Launch post draft

I published Plan Validation, a small open-source plugin for Claude Code and a pair of Codex skills.

It is for the moment when you have an approved spec and an implementation plan, but want to check that the plan matches the code and can actually be followed before another agent session starts building.

It checks requirement coverage, rehearses the selected scope in a disposable worktree, tracks scope changes and saves an HTML evidence report with a complete handoff. A second skill prepares the correct plan/spec paths and review focus. A third critiques and revises prompts without executing them. Version 0.2.0 adds focused dependency/alternative review with approval before each external lookup and recorded decisions in the complete report.

This is an early pilot. The renderer and packaging have deterministic checks; I am still evaluating end-to-end usefulness and the extra time it takes. The included example is a reproducible fixture, not a performance benchmark.

I would appreciate a small redacted example of something it catches, misses or makes unnecessarily difficult. If it helps your workflow, a GitHub star helps others find it.

[Source, installation and example](https://github.com/snowholt/plan-validation)

---

Maintainer note: adapt this draft to the community and verify the current release status before posting. This file does not indicate that the post has been sent anywhere.
