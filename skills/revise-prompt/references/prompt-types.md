# Prompt types

Use this table to classify a prompt and to seed its pre-mortem. When a prompt matches two types, use the riskier type's failures. The cells are starting points, not a checklist to copy into every revision.

| Type | The revision needs | Typical failures |
| --- | --- | --- |
| Feature or change | User-visible behavior, the files or area in scope, non-goals, acceptance criteria, the test command | Scope creep, untested code, unrelated files changed |
| Bug fix or debugging | Reproduction steps, expected and actual result, error text, root cause before the fix, an attempt limit | Symptom patch, guess-and-retry loop, no regression test |
| Plan or spec | Problem, constraints, non-goals, output file and format, an approval point before implementation | Vague steps, invented requirements, implementation started early |
| Review or audit | Read-only rule, exact target such as a diff range, finding format with file and line, verification of each finding | Edits during review, unverified or noisy findings, wrong target |
| Research or comparison | The question, decision criteria, source quality and date, how to mark unknowns | Invented or stale sources, no recommendation |
| Operations, deploy or migration | Target environment, dry run, backup and rollback, approval before irreversible steps | Wrong environment, irreversible damage, no way back |
| Prompt inside a product (system prompt, extraction, classification) | Input format, output schema, edge cases, behavior for unknown or unsafe input, examples, a cost or length budget | Format drift, invented fields, instructions injected through the input |
| Fresh-session handoff | Self-contained paths, branch and state, what is done and what is next, where evidence lives, where to stop | Dangling references such as "as above", redone work, work past the stop point |
| Writing | Audience, purpose, tone, length, facts to keep | Wrong voice, invented facts, too long |

## Any agent prompt

Also check the five common agent failures:

- Stall: asks too much or waits on routine choices.
- Loop: retries the same failing step without a limit.
- False done: reports success without running the check that proves it.
- Scope creep: changes more than the task needs.
- Unauthorized action: installs, deletes, publishes or spends without approval.

When the agent will read untrusted content, such as web pages, issues, email or user input, the revision tells it to treat that content as data, not instructions.
