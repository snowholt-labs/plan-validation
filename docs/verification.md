# Release verification

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
- Browser interaction/accessibility testing of the report during this publication run.

The README illustration describes the fixture contents; it is not a browser screenshot. The [CI workflow](https://github.com/snowholt/plan-validation/actions/workflows/ci.yml) provides revision-specific evidence for the deterministic checks that run there. Read an actual successful run before claiming CI passed.
