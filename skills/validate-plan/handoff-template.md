# Fresh-session handoff

Write a launch prompt targeting **50–80 words**, with an 80-word maximum for new reports. Fill paths and scope from verified evidence; leave no placeholders. A shorter prompt is fine when sufficient. Do not paste hashes, test logs, dependency inventories, decision history or workflow instructions into it: those stay in the linked report and repository instructions.

Use the user's chosen phase/task range, or the whole validated scope when no narrower scope was requested. Say “all validated phases” only when they were all validated and are ready. Never expand a phase review to the whole plan. Pasting the prompt requests the named implementation; it grants no additional external-action permissions.

```text
Work in `[repository path]`. Implement [selected phase/tasks or all validated phases] from `[PLAN path]`.

Read `[SPEC path]`, `[report.md path]`, its context.json, and repository instructions first. Confirm the selected scope is ready and validation still applies. Follow recorded decisions, permissions, checks and reviews; preserve unrelated work.

Report results and any defaults chosen. Stop at the selected scope.
```

The agent reads the report and context before implementation to recover document hashes, Git state, approvals, research limits, defaulted choices and required reviews. Missing or changed evidence requires reconciliation first; a short prompt is not permission to skip those checks. Use absolute paths to the saved report source and context so a fresh session can read them without a browser. Wrap each path in backticks; a backtick-quoted absolute path counts as one word, even when it contains spaces.

For **Ready after approvals**, name only the approved independent tasks and state which tasks must wait. Keep the same length limit; point to Open items for the full approval record.

For **Not ready**, use a short remediation prompt instead of the implementation prompt. Name the blocker and point to the same documents/report/context for its evidence, permissions and required checks. Include `Do not start dependent implementation.` Do not include an `Implement ...` instruction anywhere in it. Preserve these rules for historical reports without rewriting their saved prompts.
