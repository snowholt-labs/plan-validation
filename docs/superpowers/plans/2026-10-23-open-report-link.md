# Open the Report Automatically Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in `--open` flag to `render_report.py` that opens `report.html` in the default graphical browser, and make the `validate-plan` skill use it.

**Architecture:** A small helper, `open_report(path)`, decides whether a graphical browser can be used and starts it without waiting. `main()` calls it only after every file is written, adds `opened` to the JSON output and prints a stderr note when the report was not opened. The skill text and docs switch new runs to `--open` and keep the existing `report.html` link.

**Tech Stack:** Python 3.10+ standard library (`webbrowser`, `os`, `sys`), `unittest`.

**Spec:** `docs/superpowers/specs/2026-10-23-open-report-link-design.md`

## Global Constraints

- No new dependency. Use Python's standard `webbrowser` module only.
- `--open` never makes rendering fail: files written, JSON printed, exit code 0.
- Never launch a terminal browser (such as `lynx` or `w3m`) and never block waiting for a browser.
- On non-macOS, non-Windows systems, skip opening when neither `DISPLAY` nor `WAYLAND_DISPLAY` is set.
- `opened` is `true` or `false` with `--open`, and absent without it. `true` means a launch was started, not that a window appeared.
- CI, tests and `scripts/demo.py` never open a browser. No test launches a real browser.
- No `CHANGELOG.md` entry in this PR.
- Branch `feature/open-report-link`; one PR into `main`, label `enhancement`, PR body from `.github/PULL_REQUEST_TEMPLATE.md`; code and security review before the PR; merge only with the maintainer's approval, using a merge commit.

## Review Focus

- `$BROWSER` set to a console browser (for example `BROWSER=lynx`) on a desktop: expect no launch and `opened: false`, not a hijacked terminal. Test in Task 1.
- Run directory path with spaces: expect a percent-encoded `file://` URI that opens the right file. Test in Task 1.
- Opener raises (for example `webbrowser.Error` or `OSError`): expect a normal render, `opened: false` and one stderr line. Test in Task 1.
- Rejected report with `--open`: expect exit 1 and no browser call. Test in Task 1.
- Agent claims the report opened when `opened` is false: expect no such claim. Covered by the evaluation case in Task 2.

---

### Task 1: Renderer `--open` flag

**Files:**
- Modify: `skills/validate-plan/scripts/render_report.py` (imports at the top; new helper above `main()`; `main()` around lines 563–590)
- Test: `skills/validate-plan/scripts/test_render_report.py`
- Also commit: `docs/superpowers/specs/2026-10-23-open-report-link-design.md`, `docs/superpowers/plans/2026-10-23-open-report-link.md`

**Interfaces:**
- Produces: `open_report(path: Path) -> tuple[bool, str]` in `render_report.py`. Returns `(True, "")` when a launch was started, otherwise `(False, reason)` with a short reason such as `"no display"`, `"no graphical browser"` or the exception text.
- Produces: CLI flag `--open` (`action="store_true"`) and the JSON key `opened`.

- [ ] **Step 1: Write the failing tests**

Add `import contextlib`, `import io`, `import os` and `from unittest import mock` to the test file, and import `open_report` and `render_report` itself (`import render_report`). Add a helper that runs `render_report.main()` in-process so the opener can be replaced:

```python
def run_main(self, directory, source, context, *extra):
    (directory / "in.md").write_text(source, encoding="utf-8")
    (directory / "in.json").write_text(json.dumps(context), encoding="utf-8")
    argv = ["render_report.py", "--report", str(directory / "in.md"), "--context", str(directory / "in.json"),
            "--output", str(directory / "report.html"), *extra]
    out, err, code = io.StringIO(), io.StringIO(), 0
    with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            render_report.main()
        except SystemExit as exit_:
            code = exit_.code or 0
    return code, out.getvalue(), err.getvalue()
```

Tests in `ReportTests`, using the existing valid report and context fixture that `test_main_writes_one_file_per_phase_and_marks_historical_files` uses:

```python
def test_open_launches_browser_after_report_is_written(self):
    out = Path(self.directory.name) / "run dir"
    out.mkdir()
    calls = []
    def fake_open(path):
        calls.append(path)
        self.assertTrue((out / "report.html").is_file())
        return True, ""
    with mock.patch.object(render_report, "open_report", fake_open):
        code, stdout, _ = self.run_main(out, *self.two_phase(), "--open")
    self.assertEqual(code, 0)
    self.assertEqual(calls, [(out / "report.html").resolve()])
    self.assertIs(json.loads(stdout)["opened"], True)

def test_open_failure_still_renders(self):
    # opener reports failure -> exit 0, opened False, one stderr line containing "Browser not opened"
    ...

def test_without_open_flag_no_browser_and_no_opened_key(self):
    # open_report patched with a mock -> mock not called; "opened" not in the JSON

def test_rejected_report_with_open_calls_no_browser(self):
    # break the report (for example a wrong verdict line) -> code == 1; mock not called
```

`open_report` tests patch `sys.platform`, `os.environ` and `webbrowser` and never launch anything:

```python
def test_open_report_skips_without_display(self):
    with mock.patch.object(sys, "platform", "linux"), mock.patch.dict(os.environ, {}, clear=True), \
         mock.patch("webbrowser.get") as get:
        self.assertEqual(open_report(Path("/tmp/x/report.html"))[0], False)
    get.assert_not_called()

def test_open_report_refuses_console_browser(self):
    # linux, DISPLAY=":0"; webbrowser.get returns webbrowser.GenericBrowser("lynx"), then webbrowser.Elinks("elinks")
    # -> (False, ...) for both, and neither browser's open() is called (patch open() on each instance)

def test_open_report_uses_percent_encoded_file_uri(self):
    # linux, DISPLAY=":0"; webbrowser.get returns a mock that is a webbrowser.BackgroundBrowser instance
    # path Path("/tmp/run dir/report.html") -> browser.open called once with "file:///tmp/run%20dir/report.html"; result (True, "")

def test_open_report_returns_false_when_browser_raises(self):
    # browser.open raises webbrowser.Error("boom") -> (False, reason) with "boom" in reason; no exception escapes
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py' -k open`
Expected: ERROR, `ImportError: cannot import name 'open_report'`.

- [ ] **Step 3: Implement `open_report(path: Path) -> tuple[bool, str]` and the `--open` flag in `render_report.py`**

- `open_report`: on `sys.platform` other than `darwin` and `win32`, return `(False, "no display")` when neither `DISPLAY` nor `WAYLAND_DISPLAY` is set. Get the browser with `webbrowser.get()`. On those same systems, accept the browser only when `isinstance(browser, webbrowser.BackgroundBrowser) or getattr(browser, "background", False)`; otherwise return `(False, "no graphical browser")`. Plain `GenericBrowser` (console browsers such as `lynx` and unknown `$BROWSER` commands) and `Elinks` run in the foreground and block, while `xdg-open` is a `BackgroundBrowser` and Chrome or Firefox set `background = True`. On macOS and Windows, use the browser as returned. Otherwise call `browser.open(path.as_uri(), new=2)` and return `(bool(result), "" if result else "browser did not start")`. Catch `webbrowser.Error` and `OSError` and return `(False, str(error))`.
- `main()`: add `parser.add_argument("--open", action="store_true", help="open report.html in the default graphical browser")`. After the `try` block succeeds, build the existing JSON dict; when `args.open`, call `open_report(args.output.resolve())`, set `"opened"`, and when not opened print `Browser not opened: <reason>` to `sys.stderr`. Call `open_report` through the module name lookup (a plain call inside `main()` does this), so the test patch takes effect.

- [ ] **Step 4: Run the full suite and the package checks**

Run:
```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skills/validate-plan/scripts -p 'test_*.py'
python3 scripts/check_package.py
python3 scripts/demo.py --output "$(mktemp -d)/demo"
```
Expected: all tests pass; `check_package.py` passes; the demo completes and no browser opens.

- [ ] **Step 5: Commit**

```bash
git branch --show-current   # must print feature/open-report-link
git add skills/validate-plan/scripts/render_report.py skills/validate-plan/scripts/test_render_report.py \
  docs/superpowers/specs/2026-10-23-open-report-link-design.md docs/superpowers/plans/2026-10-23-open-report-link.md
git commit -m "Add an opt-in --open flag that opens the rendered report in the browser"
```

### Task 2: Skill text, documentation and evaluation case

**Files:**
- Modify: `skills/validate-plan/references/html-report.md` (render command at line 49; Delivery section around lines 165–181)
- Modify: `skills/validate-plan/SKILL.md` (Return paragraph at line 68; Resume or repeat section at line 70 onward)
- Modify: `site/src/content/docs/reports-and-handoffs.md` (command and paragraph at lines 57–64)
- Modify: `docs/evaluation.md` (Starter cases table)

**Interfaces:**
- Consumes: the `--open` flag and the `opened` JSON key from Task 1.

- [ ] **Step 1: Update the render command and Delivery text in `html-report.md`**

Append `--open` to the command on line 49. In Delivery, add: new reports are rendered with `--open`; keep the clickable absolute link to `report.html`; when the renderer prints `"opened": false`, do not say the report was opened.

- [ ] **Step 2: Update `SKILL.md`**

In the Return paragraph, after the link requirement, add one sentence: render new reports with `--open`, and mention that the report was sent to the browser only when the renderer printed `"opened": true`. In Resume or repeat, add: pass `--open` on a re-render only when the user asked to see the report again.

- [ ] **Step 3: Update `reports-and-handoffs.md`**

Add `  --output /path/to/run/report.html \` then `  --open` to the example command. After "No hosting or network service is needed.", add: "With `--open`, the helper also opens the report in your default browser when a desktop is available; otherwise use the `report.html` link."

- [ ] **Step 4: Add the evaluation case to `docs/evaluation.md`**

Add a row after "Fresh-session handoff":

```markdown
| Report delivery | New reports render with `--open`; the reply keeps the clickable absolute `report.html` link; with `"opened": false` the reply does not claim the report was opened |
```

- [ ] **Step 5: Run the checks**

Run:
```bash
python3 scripts/check_package.py
cd site && npm ci && npm test && npm run build
```
Expected: both pass. If Claude Code is installed, also run `claude plugin validate .` and `claude plugin validate .claude-plugin/plugin.json`; both pass.

- [ ] **Step 6: Commit**

```bash
git branch --show-current   # must print feature/open-report-link
git add skills/validate-plan/references/html-report.md skills/validate-plan/SKILL.md \
  site/src/content/docs/reports-and-handoffs.md docs/evaluation.md
git commit -m "Render new reports with --open and document browser opening"
```

## After the tasks

Run `/code-review` and `/security-review` on `main..feature/open-report-link`, fix confirmed findings, then open one PR into `main` (label `enhancement`, template sections, no milestone). Wait for the `verify` check, post one review-summary comment, and ask the maintainer before merging with a merge commit. After merge, the maintainer runs one validation in Claude Code and confirms the report opens in Chrome.
