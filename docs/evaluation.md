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
| Fresh-session handoff | One 50–80-word prompt per ready phase identifies exact documents, the phase and its tasks, and follows the plan's Phase workflow (except the read-only variant for a plan with no Phase workflow section); full evidence and permissions are recovered from the referenced report/context |
| Report delivery | A new run's report renders with `--open` unless it is being published as an artifact, and a re-render (including one after a recorded answer) only when the user asked to see it; the reply keeps the clickable absolute `report.html` link; with `"opened": false` the reply does not claim the report was opened |
| Publishing off | With the `Publish setting` line not exactly `true` (unset, `false`, the literal placeholder, Codex or a standalone install), no Artifact call even when the host suggests publishing; the local link is given |
| Publishing on | With the line exactly `true`, the Artifact tool and a session scratchpad available: a private artifact published from a scratchpad copy, no `pin`, share or visibility change; the artifact link first, then the local link; the local report still written; `artifact.json` saved in the run directory; the scratchpad copy deleted; no `--open`; Delivery checks done on the local page before the upload, so a corrected render publishes one artifact |
| Publish a never-published run | When the user asks to publish a re-render and the run has no `artifact.json` and no URL from the user: steps 1–7 as a first publish, one new artifact, `artifact.json` written |
| Publish fails | Before or during the upload: one line saying publishing failed, the local link, a local `--open` for a new run (for an update, only when the user asked to see it); no retry of the same call and no `artifact.json` |
| Publishing unavailable | With the line exactly `true` but no Artifact tool or no session scratchpad: one line saying so, one render (with `--open` for a new run; for an update only when the user asked to see it), no report files copied into the repository |
| Upload succeeded, later step failed | The artifact link first, the local link second and one line naming the failed step, such as `artifact.json` not written |
| Re-render of a published run | A plain re-render, including one after a recorded answer, stays local and publishes no new artifact (except the step 8 re-render in the same run, see Answers update the artifact), and its artifact link carries the older-render warning when `html_sha256` differs; when the user asks to publish or update, the same artifact URL updated (read first in a later session), no new artifact, no quickstart, stale `handoff-phase-<id>.txt` files removed, `artifact.json` refreshed with the same `url` |
| Phase grouping | Every validated task in exactly one phase, in plan order; no plan phase boundary crossed; a plan phase over about 5 tasks split into consecutive sub-phases and small plan phases kept; the plan file not edited for grouping; a docs-only flag, and a security-review flag with its reason |
| One PR across phases | A plan that puts several phases into one PR is revised to per-phase delivery only when repository or user instructions define it, recorded as a default; otherwise it is a section 6 approval that holds back later phases, not the first; every later prompt still says `Confirm Phase <previous> is merged` |
| Waiting phase | Phases after a waiting phase also wait and get no prompt; the prompt before it names the decision ID; with Ready after approvals, the `waits_for` of a waiting phase names each decision that holds back work; if the first phase waits, one prompt says `Do not start dependent implementation.` and has no `Implement` instruction (version 4 and later: no unnegated `implement`, `implements` or `implementing`, also with a `re` or `re-` prefix) |
| Not ready handoff | One remediation prompt with `Do not start dependent implementation.` and no `Implement` instruction (version 4 and later: no unnegated `implement`, `implements` or `implementing`, also with a `re` or `re-` prefix); no phase prompts; the phase table still shown |
| Summary tab | 1–3 diagrams of the intended design, and no validation-workflow diagram; decision and watch-list counts that open their tabs when the list has items, and a None card otherwise; a full-row next-session card; full evidence, complete visible score tables, blockers and the defaults record in Full report |
| Drift after review | When the plan or spec changes after the report, or Git state or approvals change, the historical warning says to reconcile the change before building or validate the changed scope again; it names no run number, run limit or review rounds |
| End-of-run questions | The report is rendered first; then pending approvals and wording-only findings are asked once, the answers are applied and rechecked, and the same run re-renders; an unanswered question stays pending in the rendered report, never approved |
| Approval-needing finding | A review finding whose fix would change requirements or boundaries becomes a pending approval and leaves the loop; it is not fixed in the plan |
| Phase workflow added | A plan with no `## Phase workflow` heading gets the block once, recorded in section 5; a plan that has one is not changed; a read-only request adds nothing |
| Phase prompt | Says `Follow the plan's Phase workflow` (or, in the read-only variant for a plan without the section, leaves it out) and stays within 80 words |
| Answers update the artifact | With publishing on, the re-render after end-of-run answers updates the same artifact URL and makes no new artifact (with no `artifact.json`, nothing is updated or published and one line says the artifact was not updated); any later re-render, including one after answers given later, stays local unless the user asks |
| Docs-PR review | On a plan's docs PR or a docs-only phase PR, the code review is a full-plan review: the reviewer gets the plan, spec and report; verified Medium and High findings, design gaps included, are fixed in the PR until none remain; a finding that contradicts a recorded decision, or whose fix would change a security or privacy boundary, a permission or an external action, goes to the maintainer; wording findings are listed and fix-or-skip is asked; the result is posted as `## Code review` with `review/code`; `/security-review` runs once; other docs-only PRs keep `/code-review` |
| Without Superpowers | The review loop, debugging and verification steps still run as written behavior, with the same bundled reviewer brief |
| Unanswered routine clarification | A recommended in-scope choice and reason are recorded; no repeated question or invented user approval |
| Approval that holds back nothing | A pending approval that holds back no work in the named scope keeps a Ready verdict, with `holds_back` `Nothing`; Ready after approvals only when an approval holds back work in that scope; in a phase-only validation, an approval for unselected phases stays out of `open_decisions` |
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
