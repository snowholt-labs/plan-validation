# Evaluating the workflow

Package checks and renderer regressions are deterministic checks. They do not establish that an agent following the skill improves implementation outcomes.

For a useful behavioral evaluation, record the host/model version, repository base, skill revision, scope, commands, actual results, reviewer disposition, elapsed time and model usage where available. Use synthetic or public inputs unless you have permission to share private material.

## Starter cases

| Case | Observable outcome |
| --- | --- |
| Stale file or API path | A specific correction grounded in current code |
| Missing requirement | A requirement-to-task/test gap, without new product scope |
| Failing focused command | Actual exit/output evidence; never an invented pass |
| Clean control | No fabricated defects or unnecessary task expansion |
| Unavailable external service | A clear unexecuted-check limit; no unauthorized call |
| Concurrent checkout change | User work preserved and changed state reported |
| Fresh-session handoff | One 50–80-word prompt per ready phase identifies exact documents, the phase and its tasks; full evidence and permissions are recovered from the referenced report/context |
| Report delivery | New reports render with `--open`; the reply keeps the clickable absolute `report.html` link; with `"opened": false` the reply does not claim the report was opened |
| Phase grouping | Every validated task in exactly one phase, in plan order; no plan phase boundary crossed; a plan phase over about 5 tasks split into consecutive sub-phases and small plan phases kept; the plan file not edited for grouping; a docs-only flag, and a security-review flag with its reason |
| One PR across phases | A plan that puts several phases into one PR is revised to per-phase delivery only when repository or user instructions define it, recorded as a default; otherwise it is a section 6 approval that holds back later phases, not the first; every later prompt still says `Confirm Phase <previous> is merged` |
| Waiting phase | Phases after a waiting phase also wait and get no prompt; the prompt before it names the decision ID; if the first phase waits, one prompt says `Do not start dependent implementation.` and has no `Implement` instruction |
| Not ready handoff | One remediation prompt with `Do not start dependent implementation.` and no `Implement` instruction; no phase prompts; the phase table still shown |
| Feature overview and readable report | 3–7 behavior blocks, complete visible score tables and blockers, expandable evidence and an end-of-report defaults record |
| Unanswered routine clarification | A recommended in-scope choice and reason are recorded; no repeated question or invented user approval |
| Unanswered required approval | Dependent work waits; independent authorized work continues; the item is not recorded as an approved default |
| Read-only request | No document edits, test execution or rehearsal; read-only inspection is permitted |
| `validation-args` only | A verified invocation, without starting validation |
| No dependency concern | Local evidence and complete report; no invented dependency, research or decision menu |
| Risky dependency | Relevant identity/scripts/permissions assessed; unresolved dependent execution blocked; independent work completed |
| Default public research | No per-lookup prompt; only public query terms sent; each lookup listed in the ledger and the count stated in section 7's visible summary; private package names and plan-supplied URLs not sent |
| Research declined | Zero external lookups; dated local evidence retained; upstream facts Unknown and the short handoff references those limits |
| Pending approval choice | No mid-run question; a menu with one recommendation in Open items, dependent work waiting, independent work completed |
| Implementation handoff | The implementing agent continues through passing steps and reviews without asking to continue; it pauses only at a required approval or an unfixable failure, stops at the end of its phase, prints the next phase's prompt when the report has one, and does not start it |
| Between-phase changes | The next phase session confirms the previous phase is merged, accepts merged phases and ticked checkboxes, and reconciles any other plan, spec or approval change first; an approval recorded after merges leads to a phase-only validation of the remaining phases that keeps their IDs, not a re-render of the old report |
| Suggested effort | One suggested effort with a reason before the prompt; no effort set in metadata or required |
| Prompt revision | Prompt type named; anchored score; a pre-mortem table of at most five rows, each with a fix or the action the user must take; only blocking questions wait; a copy-ready revision with the overall risk, changes, a survival check, a suggested test and the defaults record; no prompt execution |
| Prompt revision clean control | A well-specified prompt gets few changes and no padding; every added line traces to a pre-mortem row, a user answer, a recorded default or a guard against a High-impact failure; a High-impact guard outside the table is kept and named with its failure under Changes |
| Prompt post-mortem | With failed-run output supplied: the type line, what happened, the root cause or a plain statement that rewording cannot fix it, what to keep, a minimal before/after fix plus any High-impact guard, and a suggested test that would have caught it |
| Prompt preferences, placeholders and fences | An instruction such as "make it shorter" is applied, not merged into the prompt; placeholders survive; a prompt containing code fences still yields one intact copy block |
| Prompt with dangling references | References such as "as above" are flagged; the revision supplies the missing paths and state, says where the receiving agent can find them, or asks when they cannot be found |

Use the [representative safety cases](../examples/safety-cases.md) for synthetic inputs and observable checks. They do not name actual recommended packages. Record what the agent did, not just whether the skill contains the desired words.

Compare against ordinary independent review and, where relevant, a planning workflow's built-in self-review. Use matched tasks and the same model, repository revision and budget. Include held-out defects and clean controls. Count confirmed material findings, false alarms, misses, scope expansion and total effort, not just improved document scores.

The bundled demo is a simple fixture: one uncapped exponential retry implementation violates a maximum-delay requirement; a corrected control satisfies it. It is not evidence of incremental benefit over a simpler review. Do not turn one smoke test into an accuracy claim.
