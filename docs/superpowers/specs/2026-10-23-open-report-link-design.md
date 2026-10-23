# Open the report automatically design

Date: 2026-10-23. Status: draft for maintainer review.

## Intent

When `validate-plan` finishes, the chat gives a link to the report. In the maintainer's last run (Claude Code in the Ghostty terminal, Linux), clicking that link opened the run directory in the file manager. The maintainer then had to find `report.html` and open it in the browser by hand.

The goal: the report opens in the browser on its own when validation finishes, so no click is needed.

Cause of the folder opening:

- Verified: the failing reply already had a correct link, `[report.html](file:///<run-directory>/report.html)`, and `report.html` existed. On this machine `text/html` opens in Chrome.
- Inference: the terminal handles `file://` links differently from web links. Ghostty's GTK build sends web links to the desktop's "open URI" service but handles file links separately, and a similar Ghostty report on macOS shows local HTML links opening the file manager. Not confirmed by reading Ghostty's code.

So the plugin cannot fix the click on a `file://` link by changing the link text. Opening the browser from the renderer avoids the terminal entirely.

## Goals

1. **Opt-in auto-open.** A new `--open` flag makes `render_report.py` open `report.html` in the default graphical browser after all files are written.
2. **Skill uses it.** The skill tells the agent to render with `--open` on every new validation run.
3. **Link stays as a backup.** The final reply keeps the existing clickable absolute link to `report.html`.

## Non-goals

- No local web server and no `http://` link. Decided with the maintainer on 2026-10-23: auto-open is enough. The skill's existing optional `127.0.0.1` preview text stays as is.
- No upload or hosting: no Claude Artifacts and no Codex-hosted pages. The report holds plan details that should stay on the machine, and Artifacts are not available in Codex.
- No change to the link format, the report's content, format versions or validation rules.

## Anti-goals

These would make the change a failure even if a browser opens:

- `--open` makes rendering fail. A missing or broken browser is never an error: the files are written, the JSON is printed, and the exit code stays 0.
- The renderer launches a terminal browser (such as `lynx` or `w3m`) inside the agent's terminal, or blocks waiting for a browser to exit.
- CI, tests or `scripts/demo.py` open a browser. Only the agent's real run passes `--open`.
- A new dependency. Use Python's standard `webbrowser` module only.

## Behavior

### Renderer

- `--open`:
  - Runs only after a successful render. A rejected report opens nothing.
  - Opens the `file://` URI of the absolute `report.html` path (`Path.as_uri()`, which percent-encodes spaces).
  - Uses a graphical browser only, and never falls back to a console browser on any platform (a `$BROWSER` such as `lynx` is refused on macOS and Windows too). On Linux and other non-macOS, non-Windows systems, also skip opening when neither `DISPLAY` nor `WAYLAND_DISPLAY` is set (for example over SSH or in a sandbox). How to enforce this inside `webbrowser` is left to the builder.
  - Does not wait for the browser to exit. The launched browser does not inherit the renderer's stdin, stdout or stderr, so a caller that captures the output never waits for the browser and the JSON output stays clean. (`webbrowser` itself may wait up to 5 seconds for a Chrome or Firefox remote-control call.)
  - Any error while choosing or starting the browser, including an invalid `$BROWSER` value, counts as not opened.
  - Adds `"opened": true` or `"opened": false` to the JSON output. `true` means a browser launch was started; `webbrowser` cannot confirm that a window appeared. Without `--open`, `opened` is absent.
  - If opening is skipped or fails, prints one short note to stderr (for example `Browser not opened: no display`) and still exits 0.

### Skill text

- `SKILL.md` (Return section) and `references/html-report.md` (render command and Delivery): render new reports with `--open`. The final reply keeps the clickable absolute link to `report.html`. When `opened` is true, the reply may say the report was sent to the browser; when false, it says nothing about opening.
- Resume or repeat: a re-render of a saved report uses `--open` only when the user asked to see the report again.

### Docs

- `site/src/content/docs/reports-and-handoffs.md`: add `--open` to the example command and one sentence: the report opens in the default browser when a desktop is available; otherwise use the link.
- `CHANGELOG.md`: no entry in this PR. The changelog has no unreleased section; the next release PR adds the entry.
- `docs/evaluation.md`: add one case: a run with a desktop renders with `--open` and keeps the link; a run with `opened: false` does not claim the report was opened.

## Tests

In `skills/validate-plan/scripts/test_render_report.py`. Each test replaces the browser opener; none launches a real browser.

- With `--open`, the opener is called once with the `file://` URI of `report.html`, and only after `report.html` exists; `opened` is true. Use a run directory name with a space.
- With `--open` and an opener that returns false or raises (including `webbrowser.get()` raising for a malformed `$BROWSER`), the render still succeeds, `opened` is false and the note goes to stderr.
- With `--open` on Linux and no display variables, the opener is not called and `opened` is false.
- A console browser (`lynx` as a plain command, or `Elinks`) is refused on Linux, macOS and Windows without being called.
- A background launcher that keeps running does not hold the renderer's stdout or stderr: a caller capturing the output through pipes returns promptly. Use a stand-in process such as `sleep`, never a real browser.
- Without `--open`, the opener is not called and `opened` is absent.
- A rejected report with `--open` calls no opener.

CI (`unittest`, `check_package.py`, `demo.py`) keeps passing without opening anything.

## Verification limits

- Tests prove the renderer's output and calls, not that a window appears. After merge, the maintainer runs one validation in Claude Code with the updated plugin and confirms the report opens in Chrome. If it does not, that is a follow-up, not a reason to revert.
- Claude Code on the maintainer's machine runs without a sandbox and has `DISPLAY` and `WAYLAND_DISPLAY` set (verified 2026-10-23).
- Codex: the sandbox may block launching a browser. Then `opened` is false and the link remains. Not tested in Codex.

## Delivery

- Branch `feature/open-report-link` from `main`.
- Not docs-only (skill text and scripts change), so code and security review apply before the PR. One PR into `main`, label `enhancement`, merged with a merge commit after the maintainer approves.

## Left to the builder

- How to code the graphical-browser and non-blocking rules in Behavior above (which classes are refused and which fds are redirected are fixed there and in the plan).
- The exact wording of the stderr note and the skill sentences, within the rules above.
- Test structure and helper names, following the existing test file.
