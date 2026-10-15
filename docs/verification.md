# Release verification

## Unreleased report readability changes

These checks cover the local source update; they are not publication or live-plugin acceptance results.

| Check | Observed result | Evidence and limit |
| --- | --- | --- |
| Renderer regression suite | 42 tests passed | New tests first failed for missing diagram, disclosure, defaults and prompt-length behavior; the later independent-block tests also failed before their fix. Code-review fixes added regressions for Not ready instructions, path word counts, legacy-format fallback, section headings, hidden confidence, line endings and long flows; each failed before its fix. Legacy rendering, arithmetic, injection and readiness checks still pass. |
| Package and CLI validation | Passed | Local links/manifests, both Claude validation commands, revised prompt skill validation and JavaScript syntax check. No dependency installation or release version change. |
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

The README illustration describes the fixture contents; it is not a browser screenshot. The [CI workflow](https://github.com/snowholt/plan-validation/actions/workflows/ci.yml) provides revision-specific evidence for the deterministic checks that run there. Read an actual successful run before claiming CI passed.
