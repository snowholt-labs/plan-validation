# Fresh-session handoff

Write a launch prompt targeting **50–80 words**, with an 80-word maximum for new reports. Fill paths and scope from verified evidence; leave no placeholders. A shorter prompt is fine when sufficient. Do not paste hashes, test logs, dependency inventories, decision history or workflow instructions into it: those stay in the linked report and repository instructions.

Use the user's chosen phase/task range, or the whole validated scope when no narrower scope was requested. Say “all validated phases” only when they were all validated and are ready. Never expand a phase review to the whole plan. Pasting the prompt requests the named implementation; it grants no additional external-action permissions.

```text
Work in `[repository path]`. Implement [selected phase/tasks or all validated phases] from `[PLAN path]`.

Read `[SPEC path]`, `[report.md path]`, its context.json and repository instructions; confirm the scope is ready and still valid. Follow recorded decisions, permissions and reviews; preserve unrelated work.

Do not ask to continue between steps. Stop only for approvals required by repository rules or the report, unfixable failures, or the scope end. Report results and defaults chosen.
```

The continuation sentences stop the implementing agent from pausing after each passing step or review to ask whether to continue, while keeping approval gates from repository rules and the report, such as a merge that needs the maintainer, inside the prompt itself. Keep these sentences when shortening; shorten the scope wording instead, and point to Open items for long waiting-task lists.

The agent reads the report and context before implementation to recover document hashes, Git state, approvals, research limits, defaulted choices and required reviews. Missing or changed evidence requires reconciliation first; a short prompt is not permission to skip those checks. Use absolute paths to the saved report source and context so a fresh session can read them without a browser. Wrap each path in backticks; a backtick-quoted absolute path counts as one word, even when it contains spaces.

For **Ready after approvals**, name only the approved independent tasks and state which tasks must wait. Keep the same length limit; point to Open items for the full approval record.

For **Not ready**, use a short remediation prompt instead of the implementation prompt. Name the blocker and point to the same documents/report/context for its evidence, permissions and required checks. Include `Do not start dependent implementation.` Do not include an `Implement ...` instruction anywhere in it. Preserve these rules for historical reports without rewriting their saved prompts.

## Suggested effort

Before the fenced prompt, add one line suggesting a reasoning effort for the next session (implementation or remediation), with a short reason. For example: `Suggested effort: medium. Two small tasks with focused tests.` Recommend the lowest level that fits: low for documentation-only or mechanical edits, medium for routine tasks with clear tests, and high for migrations, security boundaries, concurrency or several dependent phases. Suggest a higher host-specific level only when the evidence shows high would not be enough. This is advice: the user sets the effort in their host. Do not put it inside the prompt, set it in skill metadata or require it.
