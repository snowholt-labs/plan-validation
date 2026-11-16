# Plan Validation: directory edition

This folder is the directory edition of Plan Validation, a Claude Code plugin with three skills: `validate-plan` reviews, rehearses and revises an implementation plan against its approved specification, `validation-args` prepares the inputs for a validation run, and `revise-prompt` reviews and improves a prompt without executing it. The edition is generated from the full plugin's skill sources, so both editions follow the same validation workflow and the same eight-section report contract.

## What this edition leaves out

The directory edition ships only Markdown, text, JSON and image files. It therefore leaves out:

- the HTML report: `validate-plan` writes the report as Markdown (`report.md`) with its handoff files;
- the renderer checks: the full plugin validates every report with a script before delivering it;
- Codex support: this edition is for Claude Code only;
- artifact publishing: this edition never publishes a report.

Report checks in this edition are done by the agent, not by code. Before it replies, the agent runs a written self-check on the report and its handoff files, fixes any failed item and states the result in its reply. A script would catch a mistake the agent misses, so the full plugin remains the recommended install.

## Install one edition only

Install one edition only: both use the name `plan-validation`. Installing both makes their commands clash. To use the full plugin instead, remove this edition and run these commands in your terminal:

```bash
claude plugin marketplace add snowholt-labs/plan-validation
claude plugin install plan-validation@snowholt-plugins
```

The full plugin, its documentation and its source are at https://github.com/snowholt-labs/plan-validation.

## License

Apache-2.0. See `LICENSE` and `NOTICE.txt` in this folder.
