# Fresh-session handoff

Write one launch prompt per ready phase, each targeting **50–80 words**, with an 80-word maximum for new reports. Fill paths, phase IDs and task lists from verified evidence; leave no placeholders. A shorter prompt is fine when sufficient. Do not paste hashes, test logs, dependency inventories, decision history or workflow instructions into it: those stay in the linked report and repository instructions.

Each prompt names exactly one phase from the phase grouping in `context.json`, in plan order, and stops at the end of that phase. Never expand a phase review to the whole plan. Pasting a prompt requests only the named phase; it grants no additional external-action permissions.

```text
Work in `[repository path]`. Implement Phase [N] (Tasks [list]) from `[PLAN path]`.

Read `[SPEC path]`, `[report.md path]`, its context.json and repository instructions. Confirm Phase [N-1] is merged and the scope is still valid. Follow recorded decisions, permissions and reviews; preserve unrelated work.

Do not ask to continue between steps. Stop only for required approvals or unfixable failures. Stop at the end of Phase [N] and print the Phase [N+1] prompt from the report; do not start it. Report results and defaults chosen.
```

Variants:

- **First phase:** drop "Phase [N-1] is merged and", so it reads "Confirm the scope is still valid."
- **Last phase:** end with "Stop at the end of Phase [N]; it is the last phase."
- **Phase before a waiting phase:** end with "Stop at the end of Phase [N]. Phase [N+1] waits for [decision]; there is no prompt for it yet." Name only the decision ID (for example `D1`), because a descriptive decision pushes this variant past 80 words.

The renderer requires each ready-phase prompt to contain `Stop at the end of Phase <id>` for its own phase. When a prompt runs long, write the task list as a range (`Tasks 4–6`) and point to Open items; keep the continuation and stop sentences.

The continuation sentences stop the implementing agent from pausing after each passing step or review to ask whether to continue, while keeping approval gates from repository rules and the report, such as a merge that needs the maintainer, inside the prompt itself. The stop sentence keeps the session inside its phase: the maintainer merges the phase and starts the next one in a fresh session.

The agent reads the report and context before implementation to recover document hashes, Git state, approvals, research limits, defaulted choices and required reviews. Missing or changed evidence requires reconciliation first; a short prompt is not permission to skip those checks. Use absolute paths to the saved report source and context so a fresh session can read them without a browser. Wrap each path in backticks; a backtick-quoted absolute path counts as one word, even when it contains spaces.

## Expected changes between phases

After the first phase, the plan branch has moved: earlier phases are merged into it and their task checkboxes are ticked. That is expected and is not drift. To check, compare the plan and spec with `revised-plan.md` and `revised-spec.md` in the report's run directory (for example with `diff`) and treat only `- [ ]` to `- [x]` changes as expected. Any other change to the plan, spec or approvals needs reconciliation before implementation.

## Ready after approvals and Not ready

For **Ready after approvals**, phases run in order, so a waiting phase holds back every later phase. Give prompts only for the ready phases before the first waiting phase, and end the last of them with the waiting variant naming the decision ID. Open items keeps the full approval record. When the first phase waits, no phase can start: section 8 holds one prompt that names what to resolve and says `Do not start dependent implementation.`, with no `Implement ...` instruction.

For **Not ready**, use one short remediation prompt instead of phase prompts. Name the blocker and point to the same documents/report/context for its evidence, permissions and required checks. Include `Do not start dependent implementation.` Do not include an `Implement ...` instruction anywhere in it. Preserve these rules for historical reports without rewriting their saved prompts.

## Suggested effort

Before the fenced prompts, add one line suggesting a reasoning effort for the next sessions (implementation or remediation), with a short reason; one line covers all phases. For example: `Suggested effort: medium. Two small tasks with focused tests.` Recommend the lowest level that fits: low for documentation-only or mechanical edits, medium for routine tasks with clear tests, and high for migrations, security boundaries, concurrency or several dependent phases. Suggest a higher host-specific level only when the evidence shows high would not be enough. This is advice: the user sets the effort in their host. Do not put it inside the prompt, set it in skill metadata or require it.
