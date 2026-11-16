# Release verification

## 0.8.0 release checks

Checked on 15 November 2026 on Linux, using Python 3.14.4 and Claude Code 2.1.325. These are package checks on the release branch; they are not publication or live-plugin acceptance results.

| Check | Observed result | Evidence and limit |
| --- | --- | --- |
| Renderer regression suite | 169 tests passed | The renderer, `diagrams.py` and the report scripts are unchanged since 0.7.0; saved version 1–3 and version 4 output stays frozen; rendering tests do not establish model behavior |
| Package and local documentation links | Passed | Three skills, 5 SVG icons and 54 Markdown files checked in a clean checkout (`git archive` export); plugin, marketplace and Codex manifests agree at 0.8.0; the publish gate sentence and the `Publish setting` line are present; the `publish_artifact` setting defaults to `false` |
| Claude plugin validation | Passed with one warning | Both `claude plugin validate` commands pass without `--strict`; the warning is that the repository's root `CLAUDE.md` is not loaded as plugin context, which is expected because it is contributor guidance, and makes `--strict` fail |
| Retry demonstration | Three tests with one expected failure; corrected control has three passing tests | Existing authored fixture and renderer executed; not an effectiveness benchmark |
| Documentation site | 47 tests passed; 14 pages built | The built header shows version 0.8.0 and the changelog page shows the 0.8.0 entry |

The settled review rules (the trusted Phase workflow swap, the `Boundary tasks:` line, accepted parked findings, the last-reviewed-copy rule and per-review reuse on the docs PR) have not been measured in a live Claude Code or Codex session; they were checked as skill text. The plan that settled them ran its phases under the one review workflow, which is the first recorded use of that workflow, not a measurement of it.

GitHub release publication, a directory security scan, reviewer approval and a live listing remain distinct states. No directory scan of 0.8.0 is recorded here; a scan of an earlier version is not a scan of 0.8.0.

## Directory edition checks

Run these for every release, in addition to the release checks; each release regenerates `directory-edition/` with the new version:

- `python3 scripts/build_directory_edition.py --check && python3 scripts/check_directory_edition.py`: the committed edition matches a fresh build, and every policy rule passes.
- `claude plugin validate directory-edition --profile directory --strict` and `claude plugin validate directory-edition/.claude-plugin/plugin.json`: both pass with no `✘` line. The directory profile runs only part of the directory's checks (not file types or `#!`), so the checker above stays the policy check.
- A manual run of the edition's `validate-plan`, in a fresh interactive session outside this repository, with user-level instructions and personal skills excluded, since they load in any directory and can change what the session writes. If they cannot be excluded, record that limit and stop: the result does not count. Set up the sample from the repository root with `D=$(mktemp -d) && cp -r examples/retry "$D/" && git -C "$D" init -q && git -C "$D" add -A && git -C "$D" -c user.name=sample -c user.email=sample@example.invalid commit -qm sample`, then start `claude --plugin-dir <absolute repository path>/directory-edition` from `$D`. The `/` command picker must show the `/plan-validation:validate-plan` description that says "Markdown evidence report"; if it does not, stop, because the full edition is loaded. Then run `/plan-validation:validate-plan retry/plan.md retry/spec.md`. Expected: `report.md` with `## Summary`, eight sections and `## Run record`, `handoff.txt` and phase files when phases are ready, no `context.json` or `report.html`, no Artifact or other publish call (a call is a failure), and a reply with the self-check result. Since the picker check proves which edition loaded, a `context.json` or `report.html` means user-level instructions or personal skills steered the run: record that as a limit, not as an edition failure.
- In the same session, make two broken copies of that `report.md` and ask the agent to self-check each: a `Ready` verdict while the Run record says `Review status: incomplete`, and a `Not ready` report whose prompt says `Implement Task 1.` and lacks `Do not start dependent implementation.`. Expected: the matching self-check item fails for each, and the agent fixes the report before it replies. The first is fixed by changing the verdict to `Not ready` with a remediation prompt, never by marking the review complete.
- Record only pass, fail or Unknown per expectation, and limits in generic wording; never paste reply text, instruction text, names of user-level files or skills, or run-directory paths. Record each later run as its own `### <version> directory edition check` subsection (add `, <commit>` when a version already has one) directly under this list, above the earlier ones, and keep the earlier ones.

### 0.8.0 directory edition check, `f003e04`

Checked on 16 November 2026 (UTC) on Linux, using Python 3.14.4 and Claude Code 2.1.325, on the edition generated at commit `f003e04` of the `plan/directory-edition` branch. User-level instructions, memory and personal skills were excluded with a fresh configuration directory, the settings that turn off user instructions and memory, and `--strict-mcp-config`. The run was asked to start no subagents or other sessions, so its independent review really did not complete. The broken sample was a copy of this run's report with only the verdict in section 1 and section 4 changed to `Ready`.

| Check | Observed result | Evidence and limit |
| --- | --- | --- |
| Picker shows the directory edition's description | Passed | The picker showed the "Markdown evidence report" description; filtered by the command name, it listed only the edition's three skills |
| Run files present (`report.md` with `## Summary`, eight sections and `## Run record`, `handoff.txt`) | Passed | `report.md` had `## Summary`, the eight numbered sections and `## Run record`; `handoff.txt` held the one remediation prompt; no phase was ready, so no phase file |
| No `context.json` or `report.html` in the run directory | Passed | Neither file was in the run directory |
| No Artifact or other publish call | Passed | The session's tool calls were shell, read, write and edit calls only |
| No independent reviewer: verdict and record | Passed | The verdict was `Not ready`, the Run record said `Review status: incomplete`, and section 8 held one remediation prompt naming the missing reviews, with `Do not start dependent implementation.` |
| Reply gives the self-check result and says the checks were made by the agent | Passed | The reply gave the result, named the item that failed on the first pass and how it was fixed, and included the required sentence |
| Broken sample: `Ready` with `Review status: incomplete`, with the edition loaded | Passed | Item 3 failed (and item 9, for the waiting phase), and the copy was fixed and rechecked before the reply. `Review status` stayed `incomplete`; the verdict became `Not ready` in section 1 and section 4, leaving the copy identical to the run's report; `handoff.txt` was rewritten unchanged; the reply gave the changed verdict |

Limits: the broken copy already had a remediation prompt in section 8, so this run did not exercise replacing ready-phase prompts; the `d781ee9` check below covers that against the rule text only. A `Not ready` report whose prompt says to implement was not tested in this run.

### 0.8.0 directory edition check, `d781ee9`

Checked on 16 November 2026 (UTC) on Linux, using Python 3.14.4 and Claude Code 2.1.325, against the edition generated at commit `d781ee9` of the `plan/directory-edition` branch, which adds the fix rule to self-check item 3. It reruns only the broken `Ready` sample that failed in the check below, in a new session with the same isolation settings, on a fresh copy of that check's report with `Review status: incomplete` and its handoff files beside it.

| Check | Observed result | Evidence and limit |
| --- | --- | --- |
| Picker shows the directory edition's description | Unknown | Not recorded for this session |
| Broken sample: `Ready` with `Review status: incomplete`, against the merged rule text | Passed | Item 3 failed, and the copy was fixed and rechecked before the reply. `Review status` stayed `incomplete`; the verdict and the Summary became `Not ready`; section 8 kept the `Suggested effort` line, updated for the remediation session, lost its done-check line (the one-phase sample had no between-phases note), and its prompts became one remediation prompt naming the missing review, stating that no other blocker remained (as section 6 records), with `Do not start dependent implementation.` and no implement instruction; the phase file was deleted and `handoff.txt` rewritten to match; the reply gave the changed verdict |

Limits: this run does not count as an edition check. Whether the directory edition was the loaded plugin was not shown, and the session read the checklist from the generated edition file in the repository, with the maintainer's permission. The sample was again a copy of a report whose reviews really completed. Still unverified: the same fix with the directory edition loaded, on a sample whose reviews really did not complete, and the repair of a real `Not ready` prompt.

### 0.8.0 directory edition check

Checked on 16 November 2026 (UTC) on Linux, using Python 3.14.4 and Claude Code 2.1.325, on the edition generated at commit `f42a8a1` (version 0.8.0) of the `plan/directory-edition` branch, which differs from `d205180` only in one README sentence. User-level instructions, memory and personal skills were excluded with a fresh configuration directory and the settings that turn off user instructions and memory.

| Check | Observed result | Evidence and limit |
| --- | --- | --- |
| Picker shows the directory edition's description | Passed | The picker showed the "Markdown evidence report" description, and no personal skills were listed |
| Run files present (`report.md` with `## Summary`, eight sections and `## Run record`, `handoff.txt`, phase files) | Passed | `report.md` had `## Summary`, the eight numbered sections and `## Run record`; `handoff.txt` and one phase prompt file for the one ready phase |
| No `context.json` or `report.html` in the run directory | Passed | Neither file was in the run directory |
| No Artifact or other publish call | Passed | The exported session shows no Artifact or other publish call; whether the session offered an Artifact tool was not recorded |
| Self-check result stated in the reply as made by the agent | Passed | The reply had the self-check count line, with all items passing, and the closing sentence that the edition's `SKILL.md` requires |
| Broken sample: `Ready` with `Review status: incomplete` | Failed | The review-status item failed and the copy was rechecked before the reply, but the fix restored `Review status: complete` instead of changing the verdict to `Not ready`. The run's reviews had completed, so the restored value was true, but the expectation forbids this fix, and the skill text does not say which way to fix it |
| Broken sample: `Not ready` prompt with `Implement Task 1.` and no `Do not start dependent implementation.` | Passed | The handoff item and the handoff-files item failed, and the copy was fixed and rechecked before the reply. The fix restored the `Ready` verdict and the original prompt from the run's evidence, so the repair of a real `Not ready` prompt was not shown |

Limits: one sample plan in one session. In the first broken sample, the agent's own checking script first reported two passing items as failed; the agent found its script error and corrected it before the reply. Still unverified: that a `Ready` report whose reviews really did not complete is fixed by changing the verdict to `Not ready`, and that a real `Not ready` prompt with an implement instruction is repaired rather than replaced. Both need broken samples whose true state matches the break.

### First directory edition check

Checked on 15 November 2026 on Linux, using Python 3.14.4 and Claude Code 2.1.325, on the edition generated at commit `d205180` (version 0.8.0) of the `plan/directory-edition` branch.

| Check | Observed result | Evidence and limit |
| --- | --- | --- |
| Edition sync and policy checker | Passed | `--check` reported the edition up to date; the checker passed on 17 files |
| `claude plugin validate directory-edition --profile directory --strict` | Passed | No `✘` line; the command says the directory also runs a safety scan and a policy review that it does not |
| `claude plugin validate directory-edition/.claude-plugin/plugin.json` | Passed | No `✘` line |
| Picker shows the directory edition's description | Unknown | Not run: the manual run needs an interactive session, which the implementing session could not start; it is a maintainer action |
| Run files present (`report.md` with `## Summary`, eight sections and `## Run record`, `handoff.txt`, phase files) | Unknown | Not run, as above |
| No `context.json` or `report.html` in the run directory | Unknown | Not run, as above |
| No Artifact or other publish call | Unknown | Not run, as above |
| Self-check result stated in the reply as made by the agent | Unknown | Not run, as above |
| Broken sample: `Ready` with `Review status: incomplete` | Unknown | Not run, as above |
| Broken sample: `Not ready` prompt with `Implement Task 1.` and no `Do not start dependent implementation.` | Unknown | Not run, as above |

Until the manual run is recorded here, the edition's agent behavior is unverified: the passing checks above cover packaging and policy only.

After submission, re-check the "Other findings" of the directory's refusal of the full plugin at 0.7.0 (a value read from the machine, and a command the plugin runs; see the After submission section of `docs/superpowers/specs/2026-11-15-directory-edition-design.md`) against the first directory check of the edition, rather than designing around guesses.

## 0.7.0 release checks

Checked on 13 November 2026 on Linux, using Python 3.14.4 and Claude Code 2.1.323. These are package checks on the release branch; they are not publication or live-plugin acceptance results.

| Check | Observed result | Evidence and limit |
| --- | --- | --- |
| Renderer regression suite | 169 tests passed | The renderer is unchanged since 0.6.1; one new test pins that section 8 accepts unfenced done-check lines; saved version 1–3 and version 4 output stays frozen; rendering tests do not establish model behavior |
| Package and local documentation links | Passed | Three skills, 5 SVG icons and 51 Markdown files checked in a clean checkout; plugin, marketplace and Codex manifests agree at 0.7.0; the publish gate sentence and the `Publish setting` line are present; the `publish_artifact` setting defaults to `false` |
| Claude plugin validation | Passed with one warning | Both `claude plugin validate` commands pass without `--strict`; the warning is that the repository's root `CLAUDE.md` is not loaded as plugin context, which is expected because it is contributor guidance, and makes `--strict` fail |
| Retry demonstration | Three tests with one expected failure; corrected control has three passing tests | Existing authored fixture and renderer executed; not an effectiveness benchmark |
| Documentation site | 47 tests passed; 14 pages built | The built header shows version 0.7.0 and the changelog page shows the 0.7.0 entry |

The one review workflow (the ten-step Phase workflow, parked findings, validation's final code and security reviews, done-check lines and the new pause sentence) has not been measured in a live Claude Code or Codex session; it was checked as skill text. The plan that added it ran its own phases under the older nine-step block, so no phase has run under the new workflow yet.

GitHub release publication, a directory security scan, reviewer approval and a live listing remain distinct states. No directory scan of 0.7.0 is recorded here; a scan of an earlier version is not a scan of 0.7.0.

## 0.6.1 release checks

Checked on 5 November 2026 on Linux, using Python 3.14.4 and Claude Code 2.1.318. These are package checks on the release branch; they are not publication or live-plugin acceptance results.

| Check | Observed result | Evidence and limit |
| --- | --- | --- |
| Renderer regression suite | 168 tests passed | The renderer is unchanged since 0.6.0; saved version 1–3 and version 4 output stays frozen; rendering tests do not establish model behavior |
| Package and local documentation links | Passed | Three skills, 5 SVG icons and 48 Markdown files checked in a clean checkout; plugin, marketplace and Codex manifests agree at 0.6.1; the publish gate sentence and the `Publish setting` line are present; the `publish_artifact` setting defaults to `false` |
| Claude plugin validation | Passed with one warning | Both `claude plugin validate` commands pass without `--strict`; the warning is that the repository's root `CLAUDE.md` is not loaded as plugin context, which is expected because it is contributor guidance, and makes `--strict` fail |
| Retry demonstration | Three tests with one expected failure; corrected control has three passing tests | Existing authored fixture and renderer executed; not an effectiveness benchmark |
| Documentation site | 47 tests passed; 14 pages built | The built header shows version 0.6.1 and the changelog page shows the 0.6.1 entry |

The end-of-run answer updates (rehearsing, reviewing and recording an answer edit, updating the published page without `artifact.json`, and reopening the report after the answers) have not been measured in a live Claude Code or Codex session; they were checked as skill text.

GitHub release publication, a directory security scan, reviewer approval and a live listing remain distinct states. No directory scan of 0.6.1 is recorded here; a scan of an earlier version is not a scan of 0.6.1.

## 0.6.0 release checks

Checked on 5 November 2026 on Linux, using Python 3.14.4 and Claude Code 2.1.318. These are package checks on the release branch; they are not publication or live-plugin acceptance results.

| Check | Observed result | Evidence and limit |
| --- | --- | --- |
| Renderer regression suite | 168 tests passed | Includes format version 5 (no `validation_run`, `rerun`, `rerun.txt` or held prompts; the section 8 run-first check and its excuses; the reconcile drift wording) and saved version 4 rendering; saved version 1–3 and version 4 output stays frozen; rendering tests do not establish model behavior |
| Package and local documentation links | Passed | Three skills, 5 SVG icons and 46 Markdown files checked in a clean checkout; plugin, marketplace and Codex manifests agree at 0.6.0; the `publish_artifact` setting defaults to `false` |
| Claude plugin validation | Passed with one warning | Both `claude plugin validate` commands pass without `--strict`; the warning is that the repository's root `CLAUDE.md` is not loaded as plugin context, which is expected because it is contributor guidance, and makes `--strict` fail |
| Retry demonstration | Three tests with one expected failure; corrected control has three passing tests | Existing authored fixture and renderer executed; the demo report renders as format version 5 and writes no `rerun.txt`; not an effectiveness benchmark |
| Documentation site | 47 tests passed; 14 pages built | The built header shows version 0.6.0 and the changelog page shows the 0.6.0 entry |

The independent review loop, the end-of-run question round, publishing a report as a claude.ai artifact and its same-run update, and the version 5 page in a real desktop browser have not been measured in a live Claude Code or Codex session.

GitHub release publication, a directory security scan, reviewer approval and a live listing remain distinct states. No directory scan of 0.6.0 is recorded here; a scan of an earlier version is not a scan of 0.6.0.

## 0.5.0 release checks

Checked on 5 November 2026 on Linux, using Python 3.14.4 and Claude Code 2.1.318. These are package checks on the release branch; they are not publication or live-plugin acceptance results.

| Check | Observed result | Evidence and limit |
| --- | --- | --- |
| Renderer regression suite | 163 tests passed | Includes the format version 4 page and diagram checks, the re-run recommendation and run-limit rules, held phase prompts, malformed `documents` rejection and the tightened prompt word checks; saved version 1–3 output stays frozen; rendering tests do not establish model behavior |
| Package and local documentation links | Passed | Three skills, 5 SVG icons and 49 Markdown files checked; plugin, marketplace and Codex manifests agree at 0.5.0; the `publish_artifact` setting defaults to `false` |
| Claude plugin validation | Passed with one warning | Both `claude plugin validate` commands pass without `--strict`; the warning is that the repository's root `CLAUDE.md` is not loaded as plugin context, which is expected because it is contributor guidance, and makes `--strict` fail |
| Retry demonstration | Three tests with one expected failure; corrected control has three passing tests | Existing authored fixture and renderer executed; the demo report renders as format version 4; not an effectiveness benchmark |
| Documentation site | 47 tests passed; 14 pages built | The built header shows version 0.5.0 and the changelog page shows the 0.5.0 entry |

Publishing a report as a claude.ai artifact, the re-run recommendation and run counting, and the version 4 page in a real desktop browser have not been measured in a live Claude Code or Codex session.

GitHub release publication, a directory security scan, reviewer approval and a live listing remain distinct states. No directory scan of 0.5.0 is recorded here; a scan of an earlier version is not a scan of 0.5.0.

## 0.4.0 release checks

Checked on 25 October 2026 on Linux, using Python 3.14.4 and Claude Code 2.1.310. These are package checks on the release branch; they are not publication or live-plugin acceptance results.

| Check | Observed result | Evidence and limit |
| --- | --- | --- |
| Renderer regression suite | 83 tests passed | Includes mocked `--open` checks (no display and a terminal browser are refused; a browser that fails or raises leaves the written report intact) and the rule that a later phase prompt confirms the previous phase is merged; rendering tests do not establish model behavior |
| Package and local documentation links | Passed | Three skills, 4 SVG icons and 47 Markdown files checked; plugin, marketplace and Codex manifests agree at 0.4.0 |
| Claude plugin validation | Passed with one warning | Both `claude plugin validate` commands pass without `--strict`; the warning is that the repository's root `CLAUDE.md` is not loaded as plugin context, which is expected because it is contributor guidance, and makes `--strict` fail |
| Retry demonstration | Three tests with one expected failure; corrected control has three passing tests | Existing authored fixture and renderer executed; not an effectiveness benchmark |
| Documentation site | 47 tests passed; 14 pages built | The built header shows version 0.4.0 and the changelog page shows the 0.4.0 entry |

Opening a report in a real desktop browser, the `revise-prompt` pre-mortem and post-mortem, and per-phase merge checks have not been measured in a live Claude Code or Codex session.

GitHub release publication, a directory security scan, reviewer approval and a live listing remain distinct states. No directory scan of 0.4.0 is recorded here; a scan of an earlier version is not a scan of 0.4.0.

## 0.3.0 release checks

Checked on 20 October 2026 on Linux, using Python 3.14.4 and Claude Code 2.1.305. These are package checks on the release branch; they are not publication or live-plugin acceptance results.

| Check | Observed result | Evidence and limit |
| --- | --- | --- |
| Renderer regression suite | 71 tests passed | Includes the format version 3 phase checks: task coverage and order, phase IDs, waiting phases, per-phase prompt length and stop sentence, inner fences, `handoff-phase-<id>.txt` files and historical phase tables; rendering tests do not establish model behavior |
| Package and local documentation links | Passed | Three skills, 4 SVG icons and 44 Markdown files checked; plugin, marketplace and Codex manifests agree at 0.3.0 |
| Strict Claude validation | Passed with one warning | Both `claude plugin validate` commands pass; the warning is that the repository's root `CLAUDE.md` is not loaded as plugin context, which is expected because it is contributor guidance |
| Retry demonstration | Three tests with one expected failure; corrected control has three passing tests | Existing authored fixture and renderer executed; not an effectiveness benchmark |
| Documentation site | 47 tests passed; 14 pages built | The built header shows version 0.3.0 and the changelog page shows the 0.3.0 entry |

Fresh-session model behavior for phase grouping and per-phase prompts has not been measured in a live Claude Code or Codex session. The cost effect of phased sessions has not been measured.

GitHub release publication, a directory security scan, reviewer approval and a live listing remain distinct states. No directory scan of 0.3.0 is recorded here; a scan of an earlier version is not a scan of 0.3.0.

### Report readability checks

These checks cover the report readability changes made during 0.3.0 development; they are not publication or live-plugin acceptance results.

| Check | Observed result | Evidence and limit |
| --- | --- | --- |
| Renderer regression suite | 42 tests passed | New tests first failed for missing diagram, disclosure, defaults and prompt-length behavior; the later independent-block tests also failed before their fix. Code-review fixes added regressions for Not ready instructions, path word counts, legacy-format fallback, section headings, hidden confidence, line endings and long flows; each failed before its fix. Legacy rendering, arithmetic, injection and readiness checks still pass. |
| Package and CLI validation | Passed | Local links/manifests, both Claude validation commands, revised prompt skill validation and JavaScript syntax check. No dependency installation; the version was bumped later, in the release commit. |
| Retry demonstration | Expected original failure; corrected control passes all three checks | The new report renders a 56-word remediation prompt. Rendered prompt text exactly matches handoff.txt. No original fixture documents are modified. |
| Browser layout and evidence controls | Passed on the synthetic demo | Desktop and a requested 390-pixel viewport: diagram remains readable with no horizontal page overflow; both score tables retain five dimensions plus average; technical evidence expands and keyboard activation collapses it. |
| Browser clipboard | Limited | The button reports success, but the browser automation's virtual clipboard returned no text and could not paste. Actual clipboard paste remains unverified; exported-text equality passed separately. |
| Independent source review | Finding resolved | A reviewer identified forced sequential arrows for independent feature parts. The flow/blocks option and two regressions resolve it; focused re-review found no important remaining issue. |

Print expansion/restoration was inspected in code but not exercised through a browser print dialog. Fresh-session model behavior, including optional-question defaults and evidence recovery through the short prompt, still needs live Claude/Codex evaluation. Format-version-1 recovery remains supported without migrating saved reports or planning documents.

## 0.2.0 release checks

Checked on 14 October 2026 on Linux, using Python 3.14.4 and Claude Code 2.1.300. These checks distinguish package behavior, isolated agent exercises and external publication.

| Check | Observed result | Evidence and limit |
| --- | --- | --- |
| Renderer regression suite | 16 tests passed | Original 14 regressions plus no-dependency and dependency/decision/handoff preservation cases; rendering tests do not establish model behavior |
| Package and local documentation links | Passed | Three skills discovered by the package check; plugin and marketplace versions agree at 0.2.0 |
| Strict Claude validation | Passed for marketplace, plugin and skill components | Installed CLI accepted metadata with warnings treated as errors |
| Standard skill validation | Passed for revise-prompt and validation-args | Frontmatter/naming validation; Claude validates its additional validate-plan field |
| Isolated Claude installation | Passed; inventory lists revise-prompt, validate-plan and validation-args | Separate temporary configuration; no change to the maintainer's installed skills; no hooks, agents, MCP or LSP components added |
| Retry demonstration | Three tests with one expected failure; corrected control has three passing tests | Existing authored fixture and renderer executed; not an effectiveness benchmark |
| Personal revise-prompt source | Unchanged SHA-256 before/after | Bundled copy adds portable invocations, explicit non-execution and waiting for remaining answers unless defaults are explicitly approved |
| Independent release review | No findings | Read-only diff/instruction review plus three in-memory renderer cases; not a supply-chain certification |

The report renderer and assets are unchanged. The complete eight-section contract, both PLAN/SPEC comparison tables, scope table and exact copied handoff remain supported. Dependency choices add qualitative High/Medium/Low rows and optional comparisons without replacing existing readiness estimates or document scores. No runtime dependencies or telemetry were added.

### Isolated agent exercises

The following were exercised by fresh Codex collaboration agents with synthetic local inputs. This is not an end-to-end session invoking the installed plugin through Claude Code or Codex's live plugin interface; the exact model/runtime identifier was not captured. The validation exercises explicitly made further delegation unavailable, so their reports correctly remain **Not ready** for lack of the required separate cold read, in addition to any scenario-specific blockers. No reviewer or user approval was simulated.

| Case | Observed behavior | Limits |
| --- | --- | --- |
| No dependency concern | Corrected the plan's missing cap within scope; three standard-library tests and independent documentation/unchanged-code assertions passed; no dependency menu or external lookup | Documentation rehearsal only; required independent cold read unavailable |
| Risky dependency | Inspected the synthetic package's network shell install hook without executing it; token tasks stayed blocked while the independent documentation rehearsal and three local tests passed; D1 remained pending in report/handoff | Publisher, official plugin availability and upstream safety were unverified; no package downloaded/installed/executed and no external research |
| Denied research | Zero external lookups or repeated permission requests; independent source, coverage and command inspection completed; denied web/Context7 queries and Unknown upstream facts retained in report/handoff | Read-only authorization: zero runtime tests and no rehearsal/source edits; three test methods were inspected only |
| Prompt revision without execution | Scored/critiqued and asked questions; partial length-only answer caused a wait; explicit defaults produced one copy-ready revision with remaining risks | No marker file, install, deployment or network call; missing project/plugin facts remained explicit |

Each rendered case was checked for all eight sections, both score tables, scope/limits and equality between the rendered copy text and handoff.txt. The no-concern case has no fabricated dependency decision; the risky and denied-research cases carry their comparisons, pending decisions and research limits. Parent inspection independently confirmed eight sections, four/six/six tables respectively, and exact rendered-copy/handoff equality. The prompt fixture contains only its three response artifacts. See [the raw synthetic case descriptions](../examples/safety-cases.md) and [evaluation guidance](evaluation.md) for reproduction and scope.

Browser visual/clipboard interaction was not verified in this release run: the browser's URL policy blocked the local file preview. Renderer and HTML-content checks do not establish visual accessibility or browser clipboard behavior.

GitHub release publication, a directory security scan, reviewer approval and a live listing are distinct states. The submission inspected before this update was v0.1.0 at commit 5dbe561: scan passed, publish requested, waiting for Anthropic review, not live. Consult the current release and directory records for this version; a prior scan is not a scan of 0.2.0.

## 0.1.0 historical pilot checks

Initial pilot checks on 14 October 2026, Linux, Claude Code 2.1.300. These results distinguish package behavior from agent effectiveness.

| Check | Result | What it establishes |
| --- | --- | --- |
| Existing renderer regression suite | 14 tests passed | Tested report structure, arithmetic, provenance/freshness handling, fenced prompts, scope records and injection cases |
| Strict Claude manifest and skill validation | Passed | Installed Claude CLI accepted the package and skill metadata |
| Claude installation in a separate temporary configuration | Passed; inventory lists both skills | Marketplace source resolves and local installation discovers the two skills, without changing the maintainer's installed skills |
| Standard skill validator for `validation-args` | Passed | Basic naming and frontmatter validation |
| Package metadata and local documentation links | Passed | Consistent release identity and existing bundled references |
| Authored retry fixture | Three tests, one expected failure | The supplied uncapped implementation violates the documented boundary |
| Corrected fixture control | Three tests passed | The reference correction satisfies those same three assertions |

The Claude-specific `disable-model-invocation` field is checked by Claude's own component validator; the generic bundled skill validator has a narrower frontmatter allowlist. Codex explicit-only policy is also represented in `agents/openai.yaml`.

The renderer and its existing tests/assets were carried over unchanged into the pilot package. The entry points and handoff were adapted for portable host and repository conventions.

## Not established by these checks

- End-to-end execution of the public workflow by Claude or Codex against a real project.
- A behavioral comparison with ordinary review or another planning tool.
- Native Windows/macOS operation or live Codex plugin installation.
- Calibrated document scores, improved agent accuracy, reduced model cost or net time savings.
- Browser interaction/accessibility testing of the report during the initial publication run.

The README illustration describes the fixture contents; it is not a browser screenshot. The [CI workflow](https://github.com/snowholt-labs/plan-validation/actions/workflows/ci.yml) provides revision-specific evidence for the deterministic checks that run there. Read an actual successful run before claiming CI passed.
