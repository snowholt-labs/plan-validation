# Contributing

Start with a small, reproducible problem. This project prioritizes useful evidence and portable behavior over adding more mandatory process.

## Report a problem

Include the release, agent host/version, operating system, expected behavior, actual behavior and a minimal redacted example. Distinguish commands that ran from instructions the agent only read. Never attach secrets, private plans, customer data, hidden system prompts or unredacted session transcripts.

For a false positive or missed defect, identify the requirement and the actual implementation consequence. A stylistic preference alone is not a plan defect.

## Make a change

1. Open an issue for a significant behavior or dependency change before implementing it.
2. Keep changes focused. Preserve user permissions, repository conventions, report freshness and honest evidence labels.
3. For renderer changes, add a regression that exercises the observable failure; do not test wording for its own sake.
4. Run the checks below and state the limits of your testing in the PR.

```bash
python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py'
python3 scripts/check_package.py
python3 scripts/demo.py --output /tmp/plan-validation-demo
```

If Claude Code is installed, also run `claude plugin validate .` and `claude plugin validate .claude-plugin/plugin.json`.

No third-party Python packages are required. Do not introduce runtime dependencies without a concrete need and maintainer agreement. Update both plugin versions and the marketplace version together for a release. Wiki source files live in `docs/wiki/`; maintainers publish them to the GitHub wiki.

Be specific, respectful and open to corrections. Give credit for contributed ideas and code. See [docs/evaluation.md](docs/evaluation.md) for behavior evaluation; passing renderer tests alone does not validate the agent workflow.
