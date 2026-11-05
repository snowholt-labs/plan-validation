#!/usr/bin/env python3
"""Render a complete validation report as a local, self-contained HTML document.

Uses only Python's standard library. Markdown support is deliberately limited to
the report contract: headings, paragraphs, lists, tables, links and fenced code.
Raw HTML is escaped; no scripts or remote assets from the report are executed.
"""

import argparse
import base64
import hashlib
import html
import importlib.util
import json
import os
import re
import sys
import webbrowser
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlsplit


def load_sibling(name):
    """Load a module from this script's folder by path, so neither ``python -I`` nor an installed
    package of the same name changes which file runs. It is registered under a private name, so
    every importer of this renderer shares one module object."""
    path = Path(__file__).resolve().with_name(f"{name}.py")
    key = f"_validate_plan_{name}"
    loaded = sys.modules.get(key)
    if loaded is not None and Path(loaded.__file__).resolve() == path:
        return loaded
    spec = importlib.util.spec_from_file_location(key, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        del sys.modules[key]
        raise
    return module


diagrams = load_sibling("diagrams")
render_diagram, validate_diagrams = diagrams.render_diagram, diagrams.validate_diagrams


ASSETS = Path(__file__).resolve().parents[1] / "assets"
READABLE_HEADINGS = (
    "Can implementation start?", "Plan scores", "Specification scores", "How certain we are",
    "What changed", "Open items", "What we checked", "Start the next session",
)
SOURCE_HEADINGS = (
    "Verdict", "PLAN comparison", "SPEC comparison", "Decision confidence",
    "Changes", "Open items", "Verification and checkout", "Fresh-session handoff",
)
HISTORICAL_PREFIX = "HISTORICAL PROMPT — DO NOT EXECUTE.\nDocument identity, Git state or approvals need revalidation before implementation.\n\n"
HISTORICAL_TEXT = ("Document identity, Git state or approvals changed or could not be checked. "
                   "This is a historical prompt. Revalidate the changed scope before using it.")
HISTORICAL_WARNING = f'<p class="warning">{HISTORICAL_TEXT}</p>'
# Version 5 has no re-run: drift advice says to reconcile the change or validate the changed scope again.
V5_RECONCILE = "Reconcile the change before building, or validate the changed scope again."
V5_DRIFT_TEXT = "The plan or spec changed or could not be read after this validation. " + V5_RECONCILE
V5_HISTORICAL_PREFIX = f"HISTORICAL PROMPT — DO NOT EXECUTE.\nDocument identity, Git state or approvals changed. {V5_RECONCILE}\n\n"
RUN_FIRST_TEXT = "Run validation again first, with the re-run prompt in the Summary; start a phase only after that run."
RUN_FIRST_NOTE = f'<p class="warning">{RUN_FIRST_TEXT}</p>'
# Held phase prompt files carry this note, so a copied file cannot start a phase before the re-run.
HELD_PREFIX = ("HELD PROMPT — DO NOT START YET.\nRun validation again first, with the re-run prompt from this "
               "validation report; start a phase only after that run.\n\n")
# Phase IDs become file names, so they cannot contain path separators.
PHASE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]{0,15}\Z")
CONFIDENCE_LEVELS = ("High", "Medium", "Low")
# Any "implement" instruction, except a negated one such as "Do not implement".
IMPLEMENT = re.compile(r"(?<!not )(?<!n't )(?<!never )\bimplement\b", re.I)
# Version 4 prompts also reject the other verb forms ("implements", "implementing", "reimplement",
# "re-implement"). Descriptive words such as "implemented" or "implementation" stay allowed.
IMPLEMENT_VERB = re.compile(r"\b(?:re-?)?implement(?:s|ing)?\b", re.I)
# Text ending in a negation: "not", "cannot", "n't" (straight or curly) or "never".
NEGATION = re.compile(r"(?:\b(?:can)?not|[a-z]n['’]t|\bnever)\s+$", re.I)
# Saved version 1-3 reports keep the negation rule they were rendered with.
LEGACY_NEGATION = re.compile(r"(?:\bnot|n't|\bnever)\s+$", re.I)
QUOTED_SPAN = re.compile(r"`([^`\n]*)`")
FILE_EXTENSION = re.compile(r"\.[A-Za-z0-9]+\Z")


def quoted_path(span):
    """Whether a backtick-quoted span (version 4) names an absolute path rather than a command or prose.

    The span has no whitespace and starts with ~/, a drive (C:\\ or C:/) or /. A / path also needs a first
    segment without a colon and, without a file extension, a second segment, so a quoted slash command
    such as `/feature-dev:implement`, `/implement` or `/implement/` is not a path. A span with whitespace
    is read as text, except a document path the report records exactly (see without_paths).
    """
    if re.search(r"\s", span):
        return False
    if span.startswith("/"):
        first, _, rest = span[1:].partition("/")
        return bool(first) and ":" not in first and bool(rest.strip("/") or FILE_EXTENSION.search(span))
    return re.match(r"~/|[A-Za-z]:[\\/]", span) is not None


def without_paths(text, names=(), padded=False):
    """Text with each quoted path, and each quoted name in names (the recorded document paths, which may
    hold spaces), replaced by one word, so it is neither counted nor checked as words. The implement check
    pads the word with spaces, so a word right after the closing backtick stays separate."""
    replacement = " path " if padded else "path"
    def word(match):
        return replacement if match.group(1) in names or quoted_path(match.group(1)) else match.group(0)
    return QUOTED_SPAN.sub(word, text)


def spaced(text):
    """Single spaces, so a wrapped sentence still reads as one."""
    return re.sub(r"\s+", " ", text)


def implement_instruction(text, names=()):
    """The first form of the verb outside a quoted path that does not directly follow a negation word
    on its own line. Every line break (CR and Unicode separators too) ends a negation."""
    text = without_paths("\n".join(text.splitlines()), names, padded=True)
    for match in IMPLEMENT_VERB.finditer(text):
        if not NEGATION.search(text[:match.start()].rsplit("\n", 1)[-1]):
            return match
    return None


MAX_RUNS = 3
RERUN_RECOMMENDATIONS = ("yes", "no", "stop")
WATCH_KINDS = ("gap", "limit", "risk", "fixed")


def fenced_blocks(source):
    """Return outer block spans without mistaking nested shorter fences for ends."""
    blocks, offset, opening = [], 0, None
    for line in source.splitlines(keepends=True):
        text = line.rstrip("\r\n")
        if opening is None:
            match = re.fullmatch(r" {0,3}(`{3,})[^`]*", text)
            if match:
                opening = (offset, offset + len(line), match.group(1))
        elif re.fullmatch(r" {0,3}" + re.escape(opening[2]) + r"`*[ \t]*", text):
            start, body_start, _ = opening
            blocks.append((start, offset + len(line), body_start, offset))
            opening = None
        offset += len(line)
    if opening is not None:
        raise ValueError("Unclosed fenced code block")
    return blocks


def escape(value):
    return html.escape(str(value), quote=True)


def plain(value):
    return re.sub(r"[*`]", "", value).strip()


MARKDOWN_LINK = r"\[([^\]]+)\]\(([^\s)]+)\)"  # groups: label, URL


def inline(value):
    """Escape text before adding only our own markup, including inside links."""
    pattern = rf"(`+)(.+?)\1|{MARKDOWN_LINK}|\*\*(.+?)\*\*"
    out, pos = [], 0
    for match in re.finditer(pattern, value):
        out.append(escape(value[pos:match.start()]))
        if match.group(1):
            out.append(f"<code>{escape(match.group(2))}</code>")
        elif match.group(3):
            label, url = match.group(3, 4)
            try:
                allowed = urlsplit(url).scheme.lower() in {"https", "http"}
            except ValueError:
                allowed = False
            if allowed and not any(ord(char) < 32 for char in url):
                out.append(f'<a href="{escape(url)}" rel="noreferrer noopener">{inline(label)}</a>')
            else:
                out.append(inline(label))
        else:
            out.append(f"<strong>{inline(match.group(5))}</strong>")
        pos = match.end()
    out.append(escape(value[pos:]))
    return "".join(out)


def cells(line):
    # A pipe within inline code is content, not a column delimiter.
    chunks, current, fence, i = [], [], 0, 0
    line = line.strip().strip("|")
    while i < len(line):
        char = line[i]
        if char == "\\" and i + 1 < len(line) and line[i + 1] == "|":
            current.append("|")
            i += 2
            continue
        if char == "`":
            end = i
            while end < len(line) and line[end] == "`":
                end += 1
            size = end - i
            fence = size if not fence else (0 if size == fence else fence)
            current.append(line[i:end])
            i = end
            continue
        if char == "|" and not fence:
            chunks.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        i += 1
    return chunks + ["".join(current).strip()]


def markdown(source):
    lines, result, i = source.splitlines(), [], 0
    lists = []

    def close_lists(min_indent=-1):
        while lists and lists[-1][0] >= min_indent:
            _, tag = lists.pop()
            result.append(f"</li></{tag}>")

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        i += 1
        if not stripped:
            continue
        item = re.match(r"^(\s*)([-*]|\d+\.)\s+(.+)$", line)
        if item:
            indent, marker, text = item.groups()
            depth, tag = len(indent), "ol" if marker[0].isdigit() else "ul"
            close_lists(depth + 1)
            if lists and lists[-1][0] == depth and lists[-1][1] != tag:
                close_lists(depth)
            if lists and lists[-1][0] == depth:
                result.append("</li><li>" + inline(text))
            else:
                result.append(f"<{tag}><li>{inline(text)}")
                lists.append((depth, tag))
            continue
        close_lists()
        if stripped.startswith("```"):
            fence = re.match(r"`{3,}", stripped).group()
            block = []
            while i < len(lines) and not re.fullmatch(re.escape(fence) + r"`*", lines[i].strip()):
                block.append(lines[i])
                i += 1
            if i == len(lines):
                raise ValueError("Unclosed fenced code block")
            i += 1
            result.append("<pre><code>" + escape("\n".join(block)) + "</code></pre>")
        elif re.match(r"^#{1,6}\s", stripped):
            level = min(len(stripped.split()[0]) + 1, 6)
            result.append(f"<h{level}>{inline(stripped.split(' ', 1)[1])}</h{level}>")
        elif stripped.startswith("|") and i < len(lines) and re.match(r"^\|?[\s:|\-]+\|\s*$", lines[i]):
            headers = cells(line)
            i += 1
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                row = cells(lines[i])
                if len(row) != len(headers):
                    raise ValueError("Table row has a different number of columns")
                rows.append("<tr>" + "".join(f"<td>{inline(cell)}</td>" for cell in row) + "</tr>")
                i += 1
            result.append('<div class="table-scroll" role="region" aria-label="Report table" tabindex="0"><table><thead><tr>' +
                          "".join(f'<th scope="col">{inline(cell)}</th>' for cell in headers) +
                          "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>")
        elif stripped in {"---", "***"}:
            result.append("<hr>")
        else:
            result.append(f"<p>{inline(line)}</p>")
    close_lists()
    return "\n".join(result)


def outside_fences(source):
    """Blank fenced content while keeping offsets and line breaks."""
    for start, end, _, _ in reversed(fenced_blocks(source)):
        source = source[:start] + re.sub(r"[^\n]", " ", source[start:end]) + source[end:]
    return source


def sections(source):
    # Prompt content may itself contain numbered Markdown headings.
    outside_code = outside_fences(source)
    found = list(re.finditer(r"^## ([1-8])[.)] +(.+)$", outside_code, re.M))
    if [match.group(1) for match in found] != list("12345678"):
        raise ValueError("Report must contain exactly eight numbered level-two sections, 1 through 8")
    return [(match.group(2), source[match.end():found[index + 1].start() if index < 7 else len(source)].strip())
            for index, match in enumerate(found)]


def score(value):
    value = plain(value)
    if value.lower() in {"unknown", "not recovered"}:
        return None
    result = Decimal(value)
    if not result.is_finite() or not 0 <= result <= 10:
        raise ValueError("Scores must be between 0 and 10, or Unknown")
    return result


def scores(section):
    rows = [cells(line) for line in section.splitlines() if line.strip().startswith("|")]
    if len(rows) != 8 or any(len(row) != 4 for row in rows):
        raise ValueError("Each score table needs a header, separator, five dimensions and Average /10")
    if "/10" not in rows[0][1] or "/10" not in rows[0][2] or plain(rows[-1][0]).lower() != "average /10":
        raise ValueError("Score columns and average must be labeled /10")
    means = []
    for column in (1, 2):
        values = [score(row[column]) for row in rows[2:7]]
        average = None if None in values else (sum(values) / 5).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        if score(rows[-1][column]) != average:
            raise ValueError("Declared average differs from the five dimension scores")
        means.append("Unknown" if average is None else str(average))
    return means


def context_documents(context):
    """The documents list, checked for shape first so a malformed context gets a message, not a traceback."""
    documents = context.get("documents", [])
    if not isinstance(documents, list) or not all(
            isinstance(doc, dict) and all(isinstance(doc.get(field), str) for field in ("label", "path", "sha256"))
            for doc in documents):
        raise ValueError("Context documents must be a list of objects with label, path and sha256 strings")
    if len(documents) != 2 or {doc["label"] for doc in documents} != {"PLAN", "SPEC"}:
        raise ValueError("Context must identify exactly PLAN and SPEC")
    for doc in documents:
        if not re.fullmatch(r"[0-9a-f]{64}", doc["sha256"]):
            raise ValueError("Each document needs its full recorded SHA256")
        if not Path(doc["path"]).is_absolute():
            raise ValueError("Document paths must be absolute")
        if "\0" in doc["path"]:
            raise ValueError("Document paths cannot contain a NUL character")
        try:
            # Strict UTF-8, as the page is written: os.fsencode would let U+DC80-U+DCFF through.
            doc["path"].encode("utf-8")
        except UnicodeError:
            raise ValueError("Document paths must be valid UTF-8 (no unpaired surrogate characters) so the page can show them") from None
    return documents


def document_checks(context):
    results = []
    for doc in context_documents(context):
        expected, path = doc["sha256"], Path(doc["path"])
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            actual = None
        results.append((doc, actual == expected))
    return results


def text_fields(record, keys):
    return isinstance(record, dict) and all(isinstance(record.get(key), str) and record[key].strip() for key in keys)


def feature_overview(feature):
    if not text_fields(feature, ("summary",)):
        raise ValueError("Feature overview needs a plain-language summary")
    steps = feature.get("steps")
    if not isinstance(steps, list) or not 3 <= len(steps) <= 7 or not all(text_fields(step, ("title", "description")) for step in steps):
        raise ValueError("Feature overview needs 3–7 blocks with a title and description")
    layout = feature.get("layout", "flow")
    if layout not in ("flow", "blocks"):
        raise ValueError("Feature layout must be flow or blocks")
    blocks = []
    for index, step in enumerate(steps):
        arrow = '<span class="step-arrow" aria-hidden="true">→</span>' if layout == "flow" and index < len(steps) - 1 else ''
        blocks.append('<li><h3>' + escape(step["title"]) + '</h3><p>' + escape(step["description"]) + '</p>' + arrow + '</li>')
    tag = "ol" if layout == "flow" else "ul"
    # More than five cards in one row become too narrow to read.
    vertical = " vertical" if layout == "flow" and len(steps) > 5 else ""
    return ('<section id="feature-overview" aria-labelledby="feature-heading"><h2 id="feature-heading">Feature at a glance</h2>'
            '<p>' + escape(feature["summary"]) + f'</p><{tag} class="feature-{layout}{vertical}" role="list">' + ''.join(blocks) + f'</{tag}></section>')


def defaulted_decisions(decisions):
    if not isinstance(decisions, list) or not all(text_fields(item, ("question", "decision", "reason")) for item in decisions):
        raise ValueError("Decisions made without a reply need question, decision and reason; use [] when none")
    if decisions:
        content = '<p>These routine defaults are recommendations used, not user approval. Required approvals remain in Open items.</p><ul>'
        for item in decisions:
            content += '<li><strong>' + escape(item["question"]) + '</strong><p>' + escape(item["decision"]) + '</p><p>Why: ' + escape(item["reason"]) + '</p></li>'
        content += '</ul>'
    else:
        content = '<p>None. No unanswered routine questions were defaulted.</p>'
    return ('<aside id="defaulted-decisions" class="decisions" aria-labelledby="decisions-heading">'
            '<h2 id="decisions-heading">Decisions made without your reply</h2>' + content + '</aside>')


def detail_marker(source, number):
    """Return the one allowed Technical details marker, or None."""
    fences = fenced_blocks(source)
    markers = [match for match in re.finditer(r"^#{3,6}[ \t]+technical details[ \t]*$", source, re.M | re.I)
               if not any(start <= match.start() < end for start, end, _, _ in fences)]
    if not markers:
        return None
    if number not in (1, 4, 5, 7) or len(markers) != 1:
        raise ValueError("Technical details are allowed once in sections 1, 4, 5 or 7; scores, open items and handoff stay visible")
    return markers[0]


def visible_part(source, number):
    marker = detail_marker(source, number)
    return source[:marker.start()] if marker else source


def decision_table(source):
    """Return the first table outside code whose first header is Decision."""
    tables, rows = [], []
    for line in outside_fences(source).splitlines() + [""]:
        if line.strip().startswith("|"):
            rows.append(cells(line))
        elif rows:
            tables.append(rows)
            rows = []
    return next((table for table in tables if plain(table[0][0]).lower() == "decision"), [])


QUOTED_PATH = re.compile(r"`(?:/|~/|[A-Za-z]:[\\/])[^`\n]*`")


def word_count(handoff, version=4, names=()):
    # A backtick-quoted absolute path is one word. Version 4 uses the implement check's rule: a path
    # with spaces counts each word unless it is a recorded document path. Saved version 1-3 reports
    # keep the rule they were rendered with, where any quoted absolute path is one word.
    return len((without_paths(handoff, names) if version >= 4 else QUOTED_PATH.sub("path", handoff)).split())


def section_content(source, number):
    """Collapse explicitly marked evidence, never infer what is safe to hide."""
    marker = detail_marker(source, number)
    if not marker:
        return markdown(source)
    summary, detail = source[:marker.start()].strip(), source[marker.end():].strip()
    if not summary or not detail:
        raise ValueError("Technical details need a visible summary and nonempty evidence")
    return markdown(summary) + '<details class="technical-details"><summary>Technical details</summary>' + markdown(detail) + '</details>'


def phase_plan(context, verdict):
    """Return the validated phase list: every task once, in plan order."""
    inventory = context.get("task_inventory")
    if (not isinstance(inventory, list) or not inventory or not all(isinstance(task, str) and task.strip() for task in inventory)
            or len(set(inventory)) != len(inventory)):
        raise ValueError("Phase grouping needs task_inventory: a nonempty list of unique task IDs")
    phases = context.get("phases")
    if not isinstance(phases, list) or not phases:
        raise ValueError("Phase grouping needs a nonempty phases list")
    seen, covered, waiting = set(), [], False
    for phase in phases:
        if not isinstance(phase, dict):
            raise ValueError("Phase entries must be objects")
        pid = phase.get("id")
        if not isinstance(pid, str) or not PHASE_ID.fullmatch(pid) or pid.lower() in seen:
            raise ValueError(f"Phase ID {pid!r} must be unique, 1-16 letters, digits, dots or hyphens, starting with a letter or digit")
        seen.add(pid.lower())
        if not text_fields(phase, ("title",)):
            raise ValueError(f"Phase {pid} needs a title")
        tasks = phase.get("tasks")
        if not isinstance(tasks, list) or not tasks or not all(isinstance(task, str) for task in tasks):
            raise ValueError(f"Phase {pid} needs a nonempty list of task IDs")
        covered.extend(tasks)
        if type(phase.get("docs_only")) is not bool or type(phase.get("security_review")) is not bool:
            raise ValueError(f"Phase {pid} needs boolean docs_only and security_review")
        if phase["docs_only"] and phase["security_review"]:
            raise ValueError(f"Phase {pid} cannot be docs-only and need a security review")
        if phase["security_review"] and not text_fields(phase, ("security_reason",)):
            raise ValueError(f"Phase {pid} needs a security_reason")
        status = phase.get("status")
        if status not in ("ready", "waiting"):
            raise ValueError(f"Phase {pid} status must be ready or waiting")
        if status == "waiting" and not text_fields(phase, ("waits_for",)):
            raise ValueError(f"Phase {pid} must name what it waits for")
        if waiting and status == "ready":
            raise ValueError(f"Phase {pid} cannot start before an earlier waiting phase")
        waiting = waiting or status == "waiting"
    if covered != inventory:
        raise ValueError("Phases must cover task_inventory exactly once, in plan order")
    if waiting and verdict.lower() == "ready":
        raise ValueError("Phase waiting for approval contradicts a Ready verdict")
    return phases


def phase_status(phase, verdict, current, rerun_first=False, version=4):
    """Return the escaped status shown for a phase in section 8 and on the Summary."""
    if phase["status"] == "waiting":
        return "Waits for " + inline(phase["waits_for"])
    # A remediation-only or historical report never shows a phase as startable.
    if verdict.lower() == "not ready":
        return "Waits for remediation"
    if not current:
        return "Reconcile before starting" if version >= 5 else "Revalidate before starting"
    # A version 4 yes asks for another run before any phase starts.
    return "Run validation again first" if rerun_first else "Can start"


def phase_table(phases, verdict, current, rerun_first=False, version=4):
    rows = ''.join('<tr>' + ''.join(f'<td>{cell}</td>' for cell in (
        escape(phase["id"]) + ': ' + inline(phase["title"]), escape(", ".join(phase["tasks"])),
        "Docs only" if phase["docs_only"] else "Code",
        "Yes — " + inline(phase["security_reason"]) if phase["security_review"] else "No",
        phase_status(phase, verdict, current, rerun_first, version))) + '</tr>' for phase in phases)
    head = ''.join(f'<th scope="col">{title}</th>' for title in ("Phase", "Tasks", "Kind", "Security review", "Status"))
    return f'<div class="table-scroll" role="region" aria-label="Phase plan" tabindex="0"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'


def recorded_names(context, run_files=()):
    """Quoted paths a version 4 or later prompt may name even with spaces: the recorded PLAN and SPEC paths and
    this run's own files (report.md and context.json, which main() passes in as run_files)."""
    return {doc["path"] for doc in context_documents(context)} | set(run_files)


def handoff_prompts(section, version, verdict, context, run_files=()):
    """Return validated (start, end, text) prompt spans and their (phase_id, prompt) pairs."""
    prompts = [(start, end, section[body_start:body_end].rstrip("\n")) for start, end, body_start, body_end in fenced_blocks(section)]
    # Version 4 reads the recorded document paths as names, even with spaces.
    names = recorded_names(context, run_files) if version >= 4 else set()
    ready = []
    if version >= 3 and verdict.lower() != "not ready":
        ready = [phase["id"] for phase in phase_plan(context, verdict) if phase["status"] == "ready"]
    if ready:
        if len(prompts) != len(ready):
            raise ValueError("Section 8 needs one fenced prompt per ready phase, in order")
    elif len(prompts) != 1:
        raise ValueError("Section 8 must contain one complete fenced handoff")
    for index, (_, _, prompt) in enumerate(prompts):
        if not prompt.strip():
            raise ValueError("Section 8 must contain one complete fenced handoff")
        if version >= 2 and word_count(prompt, version, names) > 80:
            raise ValueError("Fresh-session handoff must be at most 80 words; link to the plan, spec and report for details and wrap paths in backticks")
        if version >= 3:
            try:
                fenced_blocks(prompt)
            except ValueError:
                raise ValueError("A phase prompt has an unclosed inner code fence; use a longer outer fence") from None
        if ready:
            # Every stop sentence names this phase, unnegated. "Phase 1.2", "Phase 1-b" and
            # "Phase 12" are other phases; a sentence-ending period is not.
            own = re.compile(rf"{re.escape(ready[index])}(?![A-Za-z0-9-]|\.[A-Za-z0-9])", re.I)
            negated = NEGATION if version >= 4 else LEGACY_NEGATION
            stops = list(re.finditer(r"\bstop\s+at\s+the\s+end\s+of\s+phase\s+", prompt, re.I))
            if not stops or any(not own.match(prompt, stop.end()) or negated.search(prompt[:stop.start()]) for stop in stops):
                raise ValueError(f"Phase {ready[index]} prompt must say: Stop at the end of Phase {ready[index]}")
            # A later phase starts only once the previous one is merged; saved prompts stay as written.
            if index and context.get("kind") == "new":
                checks = list(re.finditer(rf"\bconfirm\s+phase\s+{re.escape(ready[index - 1])}\s+is\s+merged\b", prompt, re.I))
                if all(negated.search(prompt[:check.start()]) for check in checks):
                    raise ValueError(f"Phase {ready[index]} prompt must say: Confirm Phase {ready[index - 1]} is merged")
    # With no startable phase, a version 3 or later prompt is a remediation prompt even before Not ready.
    if verdict.lower() == "not ready" or (version >= 3 and not ready):
        first = prompts[0][2]
        if version >= 4:
            # Like the re-run prompt, for new and saved reports alike; the required sentence may wrap.
            implement = implement_instruction(first, names)
            first = spaced(first)
        else:
            implement = IMPLEMENT.search(first)
        if implement:
            raise ValueError(f"The remediation prompt cannot contain an Implement instruction: {implement.group(0)}")
        if "do not start dependent implementation" not in first.lower():
            raise ValueError("Not ready requires a remediation prompt stating: Do not start dependent implementation")
    return prompts, list(zip(ready, (prompt for _, _, prompt in prompts)))


def short_text(value, name, limit):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty text")
    if len(value) > limit:
        raise ValueError(f"{name} must be at most {limit} characters")


def names_id(identifier, text):
    """Whether text names a decision ID as a whole word.

    The same boundary rule as phase IDs: D1 is not D10, D1.2 or D1-b; a sentence-ending period is fine.
    """
    return re.search(rf"(?<![A-Za-z0-9.-]){re.escape(identifier)}(?![A-Za-z0-9-]|\.[A-Za-z0-9])", text) is not None


def v4_fields(context, open_items):
    """Return the checked version 4 header, diagram, decision and watch-list data."""
    if "feature" in context:
        raise ValueError("Version 4 drops feature (Feature at a glance); describe the design in diagrams")
    short_text(context.get("project"), "project", 40)
    short_text(context.get("audience"), "audience", 60)
    accent, title = context.get("title_accent"), context.get("title")
    # Counted on the raw title: the page splits it around the accent before escaping each part.
    if not isinstance(accent, str) or not accent.strip() or not isinstance(title, str) or title.count(accent) != 1:
        raise ValueError("title_accent must be text that appears exactly once in title")
    diagrams = validate_diagrams(context.get("diagrams"))
    decisions = context.get("open_decisions")
    if not isinstance(decisions, list):
        raise ValueError("open_decisions must be a list; use [] when none")
    text, seen = plain(open_items), set()
    for number, item in enumerate(decisions, 1):
        if not text_fields(item, ("id", "question", "recommendation", "holds_back")):
            raise ValueError(f"Open decision {number} needs id, question, recommendation, confidence and holds_back")
        if not PHASE_ID.fullmatch(item["id"]):
            raise ValueError(f"Open decision {number} id must be 1-16 letters, digits, dots or hyphens, starting with a letter or digit")
        if item["id"].lower() in seen:
            raise ValueError(f"Open decision {number} id {item['id']} must be unique")
        seen.add(item["id"].lower())
        if item.get("confidence") not in CONFIDENCE_LEVELS:
            raise ValueError(f"Open decision {item['id']} confidence must be High, Medium or Low")
        if not names_id(item["id"], text):
            raise ValueError(f"Open decision {item['id']} must also appear in section 6 (Open items)")
    watch = context.get("watch_list")
    if not isinstance(watch, list):
        raise ValueError("watch_list must be a list; use [] when none")
    for number, item in enumerate(watch, 1):
        if not text_fields(item, ("title", "body")):
            raise ValueError(f"watch_list item {number} needs kind, title and body")
        if item.get("kind") not in WATCH_KINDS:
            raise ValueError(f"watch_list item {number} kind must be gap, limit, risk or fixed")
        short_text(item["title"], f"watch_list item {number} title", 60)
    return {"diagrams": diagrams, "decisions": decisions, "watch": watch}


def is_absolute(path):
    return path.startswith("/") or re.match(r"[A-Za-z]:[\\/]", path) is not None


def rerun_check(context, verdict, confidence, plan_revised, spec_revised, run_files=()):
    """Return the checked "Run validation again" data of a saved version 4 report (spec Part 2)."""
    run = context.get("validation_run")
    if not isinstance(run, dict):
        raise ValueError("validation_run must be an object with number, plan_key and scope")
    number = run.get("number")
    if type(number) is not int or not 1 <= number <= MAX_RUNS:
        raise ValueError(f"validation_run number must be a whole number from 1 to {MAX_RUNS}")
    previous = run.get("previous_report")
    if previous is not None and (not isinstance(previous, str) or not is_absolute(previous)):
        raise ValueError("validation_run previous_report must be an absolute path")
    if number > 1 and previous is None:
        raise ValueError("validation_run previous_report is required from run 2")
    reset = run.get("reset", False)
    if type(reset) is not bool or (reset and number != 1):
        raise ValueError("validation_run reset must be true or false, and a reset run is run 1")
    phases = context["phases"]
    scope = run.get("scope")
    # Phase IDs may contain hyphens, so the scope is compared whole, never split.
    if scope not in ("full", f"phases:{phases[0]['id']}-{phases[-1]['id']}"):
        raise ValueError("validation_run scope must be full or phases:<first>-<last> with the first and last phase IDs")
    key = run.get("plan_key")
    if (not isinstance(key, str) or not key.strip() or is_absolute(key) or key.startswith("\\")
            or ".." in re.split(r"[\\/]", key)):
        raise ValueError("validation_run plan_key must be the plan's path relative to the repository root")
    plan = next(doc for doc in context_documents(context) if doc["label"] == "PLAN")
    if not plan["path"].replace("\\", "/").endswith("/" + key.replace("\\", "/")):
        raise ValueError("validation_run plan_key must end the PLAN document's path")

    rerun = context.get("rerun")
    if not isinstance(rerun, dict):
        raise ValueError("rerun must be an object with recommendation, reasons and, for yes, prompt")
    recommendation = rerun.get("recommendation")
    if recommendation not in RERUN_RECOMMENDATIONS:
        raise ValueError("rerun recommendation must be yes, no or stop")
    reasons = rerun.get("reasons")
    if (not isinstance(reasons, list) or not 1 <= len(reasons) <= 4
            or not all(isinstance(reason, str) and reason.strip() for reason in reasons)):
        raise ValueError("rerun reasons must be a list of 1-4 nonempty strings")
    triggers = []
    if confidence == "Unknown" or int(confidence[:-1]) < 70:
        triggers.append("confidence below 70%")
    if any(average == "Unknown" or Decimal(average) < Decimal("8.0") for average in (plan_revised, spec_revised)):
        triggers.append("revised average below 8.0")
    if verdict.lower() == "not ready":
        triggers.append("verdict Not ready")
    if number == MAX_RUNS and recommendation == "yes":
        raise ValueError(f"rerun cannot be yes at run {MAX_RUNS}; recommend stop, or no when nothing fires")
    if triggers and recommendation == "no":
        allowed = "stop" if number == MAX_RUNS else "yes or stop"
        raise ValueError("Run validation again: " + ", ".join(triggers) + f"; recommend {allowed}, not no")
    prompt = rerun.get("prompt")
    if recommendation != "yes":
        if prompt is not None:
            raise ValueError("Only a yes rerun recommendation has a prompt")
    else:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("A yes rerun recommendation needs a prompt")
        names = recorded_names(context, run_files)
        if word_count(prompt, 4, names) > 80:
            raise ValueError("The rerun prompt must be at most 80 words; wrap paths in backticks")
        # Compare with single spaces, so a wrapped prompt still says each sentence.
        joined = spaced(prompt)
        label = f"run {number + 1} of {MAX_RUNS}"
        if not re.search(rf"\b{label}\b", joined, re.I):
            raise ValueError(f"The rerun prompt must say {label}")
        # Quoted paths are names, not instructions, even when they contain the word.
        if implement_instruction(prompt, names):
            raise ValueError("The rerun prompt cannot contain an Implement instruction")
        if "do not start dependent implementation" not in joined.lower():
            raise ValueError("The rerun prompt must say: Do not start dependent implementation.")
        # Only a new version 4 run checked the scope and order sentences, the invocation, the document
        # paths and the previous report. Version 4 now renders saved reports only, which keep their
        # prompt as their run wrote it.
    return {"number": number, "recommendation": recommendation, "reasons": reasons,
            "prompt": prompt if recommendation == "yes" else None, "triggers": triggers}


def scope_section(context):
    """Return the scope comparison card shown at the start of section 5."""
    scope = context["scope"]
    scope_rows = scope["rows"]
    scope_table = '<div class="table-scroll" role="region" aria-label="Scope comparison" tabindex="0"><table><thead><tr>'
    scope_table += ''.join(f'<th scope="col">{title}</th>' for title in ["Measure", "Original", "Revised", "Reason / evidence"])
    scope_table += '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{inline(str(row[key]))}</td>' for key in ["metric", "original", "revised", "reason"]) + '</tr>' for row in scope_rows) + '</tbody></table></div>'
    return '<aside id="scope" class="scope"><h3>Scope &amp; complexity</h3><p>' + inline(scope["explanation"]) + '</p>' + scope_table + '<p><strong>Approval basis.</strong> ' + inline(scope["approval"]) + '</p></aside>'


def prompt_toolbar(target, action, current, warning, held=False, ids=False):
    """A prompt's copy button; the historical warning when not current; the run-first note while held."""
    if held:
        return RUN_FIRST_NOTE
    if not current:
        return warning
    button_id, status_id = (' id="copy-prompt"', ' id="copy-status"') if ids else ("", "")
    return (f'<button{button_id} class="copy-prompt" type="button" data-copy-target="{escape(target)}">{action}</button>'
            f'<span{status_id} class="copy-status" role="status" aria-live="polite"></span>')


def report_sections(parts, version, verdict, prompts, pairs, context, current, marks=None, warning=HISTORICAL_WARNING,
                    rerun_first=False, hold_phases=False):
    """Return the eight report sections; section 8 holds the prompts and their copy buttons."""
    handoff = prompts[0][2]
    scope_html = scope_section(context)
    body = []
    for index, (heading, content) in enumerate(parts, 1):
        if version >= 2:
            heading = READABLE_HEADINGS[index - 1]
        if index == 8:
            if version >= 2:
                detail_marker(content, index)
            intro = content
            for start, end, _ in reversed(prompts):
                intro = intro[:start] + intro[end:]
            content_html = markdown(intro)
            if version >= 3:
                content_html += phase_table(context["phases"], verdict, current, rerun_first, version)
            if pairs:
                titles = {phase["id"]: phase["title"] for phase in context["phases"]}
                for phase_id, prompt in pairs:
                    target = escape("handoff-" + phase_id)
                    toolbar = prompt_toolbar("handoff-" + phase_id, f"Copy Phase {escape(phase_id)} prompt", current, warning, hold_phases)
                    content_html += (f'<h3>Phase {escape(phase_id)}: {inline(titles[phase_id])}</h3><div class="prompt-toolbar">' + toolbar
                                     + f'</div><pre id="{target}" tabindex="0">' + escape(prompt) + '</pre>')
            else:
                # In version 3 a single prompt is always a remediation prompt.
                action = "Copy implementation prompt" if verdict.lower().startswith("ready") and version < 3 else "Copy remediation prompt"
                toolbar = prompt_toolbar("handoff", action, current, warning, ids=True)
                content_html += '<div class="prompt-toolbar">' + toolbar + '</div><pre id="handoff" tabindex="0">' + escape(handoff) + '</pre>'
        else:
            content_html = section_content(content, index) if version >= 2 else markdown(content)
        mark_html = marks[index - 1] if marks else ""
        body.append(f'<section id="section-{index}" aria-labelledby="heading-{index}"><div class="section-heading">{mark_html}<span>{index:02}</span><h2 id="heading-{index}">{inline(heading)}</h2></div>' + (scope_html if index == 5 else "") + content_html + '</section>')
    return body


def freshness_state(version, fingerprints_match, current):
    """Return the plain-text sentence about document identity shown in the page header."""
    if version >= 2:
        state = "Plan and spec match the saved review." if fingerprints_match else "Plan or spec changed or could not be read."
        # Version 5 gives the same advice as its historical warning.
        stale = " This handoff is historical. " + (V5_RECONCILE if version >= 5 else "Recheck the saved evidence before starting.")
    else:
        state = "Document fingerprints match the saved validation." if fingerprints_match else "Document fingerprints differ or files are unavailable."
        stale = " The handoff is historical; refresh its evidence before implementation."
    return state if current else state + stale


def identity_details(checks, context):
    """Return the collapsed document identity and provenance block."""
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    doc_html = ''.join('<li><strong>' + escape(doc["label"]) + '</strong> · ' + ("matches" if matches else "changed / unavailable") + '<br><code>' + escape(doc["path"]) + '</code><br><small>SHA256 ' + escape(doc["sha256"]) + '</small></li>' for doc, matches in checks)
    return ('<details class="identity"><summary>Document identity &amp; report provenance</summary><ul>' + doc_html
            + '</ul><p>HTML generated ' + escape(stamp) + '. ' + escape(context.get("provenance", "")) + '</p></details>')


SHAPES = {
    "circle": '<circle cx="6" cy="6" r="5"/>',
    "ring": '<circle class="ring" cx="6" cy="6" r="4.6"/>',
    "diamond": '<path d="M6 .6L11.4 6L6 11.4L.6 6z"/>',
    "triangle": '<path d="M6 .8L11.4 10.8H.6z"/>',
    "square": '<rect x="1" y="1" width="10" height="10" rx="3"/>',
}
SECTION_SHAPES = ("circle", "diamond", "triangle", "square")
# Each kind is shown by colour, shape and a word.
WATCH_STYLE = {"gap": ("ring", "Gap"), "limit": ("square", "Limit"), "risk": ("triangle", "Risk"), "fixed": ("circle", "Fixed")}
VERDICT_STYLE = {"ready": ("chip-ok", "circle"), "ready after approvals": ("chip-wait", "diamond"), "not ready": ("chip-stop", "triangle")}
CONFIDENCE_STYLE = {"High": ("chip-ok", "circle"), "Medium": ("chip-wait", "diamond"), "Low": ("chip-stop", "triangle")}


def mark(shape):
    return f'<svg class="mark" viewBox="0 0 12 12" aria-hidden="true" focusable="false">{SHAPES[shape]}</svg>'


def chip(css, shape, words):
    """A status pill: colour, shape and words, never colour alone. ``words`` is escaped markup."""
    return f'<span class="chip {css}">{mark(shape)}<span>{words}</span></span>'


def plural(count, word):
    return f"{count} {word}{'' if count == 1 else 's'}"


def count_card(tab, items, noun, nouns, label, empty, hint):
    if not items:
        return f'<div class="count count-none"><strong>None</strong><span>{label}</span><small>{empty}</small></div>'
    # A link to the panel, so the card also works without JavaScript, when every panel shows in order.
    return (f'<a class="count" href="#panel-{tab}" data-open-tab="{tab}"><strong>{len(items)}</strong>'
            f'<span>{noun if len(items) == 1 else nouns}</span><small>{hint}</small></a>')


def holds_back_work(item):
    """Only "Nothing" or "None" (any case, emphasis or closing punctuation) holds back no work."""
    value = re.sub(r"[*_`]", "", item["holds_back"]).strip().rstrip(".!;:").strip().casefold()
    return value not in {"nothing", "none"}


def answer_hint(decisions):
    holding = [item for item in decisions if holds_back_work(item)]
    if not holding:
        first = "Nothing is held back"
    else:
        # The hint sits inside a link, which may hold no other link, so Markdown links keep only their text.
        text = plain(re.sub(MARKDOWN_LINK, r"\1", holding[0]["holds_back"]))
        first = escape(holding[0]["id"]) + " holds back " + escape(text)
        if len(holding) > 1:
            rest = len(holding) - 1
            first += f" · {rest} more {'holds' if rest == 1 else 'hold'} back work"
    return first + " · each has a recommendation"


def watch_hint(watch):
    phrases = {"fixed": ("fixed in the plan", "fixed in the plan"), "gap": ("open gap", "open gaps"),
               "limit": ("limit to know", "limits to know"), "risk": ("risk to watch", "risks to watch")}
    parts = []
    for kind in ("fixed", "gap", "limit", "risk"):
        count = sum(item["kind"] == kind for item in watch)
        if count:
            parts.append(f"{count} {phrases[kind][count != 1]}")
    return " · ".join(parts)


RERUN_STYLE = {"yes": ("chip-wait", "diamond"), "no": ("chip-ok", "circle"), "stop": ("chip-stop", "triangle")}


def historical_warning_v4(rerun, fingerprints_match):
    """The historical warning of a saved version 4 report; when the plan or spec changed, it names the re-run
    instead of more review. At the run limit or after a recorded stop it says what revalidating takes, whatever drifted."""
    if rerun["number"] >= MAX_RUNS:
        # Only after a merge does a phase-only validation of the phases still to build start its own count.
        advice = ("The run limit is reached for this scope, so revalidating it needs your explicit reset of the run count "
                  "(once another phase has merged, a phase-only validation of the phases still to build counts separately); "
                  "do not run more review rounds, and decide the next step yourself.")
    elif rerun["recommendation"] == "stop":
        # Drift does not override a recorded stop: its reasons say the user decides first.
        advice = "The recorded answer is stop, so decide the next step yourself before revalidating; do not run more review rounds."
    elif fingerprints_match:
        # Only Git state or approvals drifted, so the shared sentence is the whole advice.
        return HISTORICAL_WARNING
    else:
        # Later runs may exist, so a saved report names no run number.
        advice = "Run validation again instead of more review rounds, if the 3-run limit allows."
    changed = "" if fingerprints_match else " The plan or spec changed or could not be read after this validation."
    return f'<p class="warning">{HISTORICAL_TEXT}{changed} {advice}</p>'


def historical_warning_v5(fingerprints_match):
    """The version 5 historical warning: reconcile the change or validate again; it names no run or limit."""
    if fingerprints_match:
        # Only Git state or approvals drifted.
        return f'<p class="warning">This is a historical prompt. Git state or approvals changed after this validation. {V5_RECONCILE}</p>'
    return f'<p class="warning">This is a historical prompt. {V5_DRIFT_TEXT}</p>'


def rerun_label(rerun):
    """A saved report shows the recommendation as recorded, as it does the verdict."""
    return "Recorded: run validation again: " + rerun["recommendation"]


def rerun_card(rerun):
    """The Summary's "Run validation again" card of a saved version 4 report. A yes shows its prompt
    without a copy button: its run label may be stale, since later runs can exist."""
    reasons = "".join(f"<li>{inline(reason)}</li>" for reason in rerun["reasons"])
    triggers = ('<p class="rerun-triggers">Triggers: ' + escape(", ".join(rerun["triggers"])) + "</p>") if rerun["triggers"] else ""
    prompt = ""
    if rerun["prompt"] is not None:
        prompt = f'<h4 class="prompt-title">Re-run prompt</h4><pre id="rerun-prompt" tabindex="0">{escape(rerun["prompt"])}</pre>'
    return (f'<div id="rerun" class="card rerun"><h3>{rerun_label(rerun)}</h3>'
            f'<p class="rerun-run">Run {rerun["number"]} of at most {MAX_RUNS}</p><ul>{reasons}</ul>{triggers}{prompt}</div>')


def has_rerun(context):
    """Whether a report carries the re-run fields: only version 4 does. Version 5 dropped re-validation."""
    return context.get("format_version") == 4


def waits_for_rerun(context, pairs):
    """Whether a saved version 4 report's ready phases wait for the re-run its rerun yes asked for.

    Only a Ready or Ready after approvals report with a ready phase has phase prompts (pairs).
    """
    return bool(has_rerun(context) and pairs and context["rerun"]["recommendation"] == "yes")


def phases_held(context, current, pairs):
    """Whether the page and prompt files hold the phase prompts: they wait for a re-run and are still current."""
    return bool(current and waits_for_rerun(context, pairs))


def prompt_prefix(context, current, pairs):
    """The note that starts handoff.txt and each phase prompt file: historical, held or none."""
    if not current:
        return V5_HISTORICAL_PREFIX if context.get("format_version", 1) >= 5 else HISTORICAL_PREFIX
    return HELD_PREFIX if phases_held(context, current, pairs) else ""


# The start of a sentence that negates what follows: "Do not", "Don't", "Never", "You need not",
# "You do not need to", "There is no need to". The whole lead must be the negation, so a conditional such as
# "If you do not run validation again first, ..." is not excused.
NEGATED_LEAD = re.compile(r"(?:(?:you|we)\s+)?(?:do\s+not|don['’]t|never|cannot|can['’]t|must\s+not|need\s+not"
                          r"|(?:do\s+not|don['’]t|never)\s+(?:need|have)\s+to|(?:there\s+is\s+)?no\s+need\s+to)\s+", re.I)
# A condition after the phrase still sends the reader to a re-run in some cases.
CONDITION = re.compile(r"\b(?:unless|except|if|until|when|once)\b", re.I)
LIST_MARKER = re.compile(r"\s*(?:[-+*]|\d+[.)])\s+")
RUN_FIRST = re.compile(r"\brun validation again first\b", re.I)
RERUN_MENTION = re.compile(r"\brerun\.txt\b|\bre-?run prompt\b", re.I)


def sentences(chunk):
    """Each sentence of a section 8 chunk, line by line, without emphasis or a list marker. A line break ends
    a sentence, as it ends a negation in implement_instruction."""
    for line in re.sub(r"[*_`]", "", chunk).splitlines():
        line = LIST_MARKER.sub("", line, count=1) if LIST_MARKER.match(line) else line
        for sentence in re.split(r"(?<=[.!?;])\s+", line):
            if sentence.strip():
                yield sentence.strip()


def run_first_note(section, prompts, context):
    """A new (version 5) report has no re-run, so section 8 and its prompts never send the reader to one.

    "Run validation again first" is allowed only in a sentence that starts by negating it and adds no condition.
    rerun.txt and the re-run prompt are never named. A saved report keeps its section 8 as its run wrote it.
    """
    if context.get("kind") != "new":
        return
    intro = section
    for start, end, _ in reversed(prompts):
        intro = intro[:start] + intro[end:]
    # Each prompt is read on its own, so its first sentence starts at the beginning of the text.
    for chunk in [intro] + [text for _, _, text in prompts]:
        for sentence in sentences(chunk):
            for match in RUN_FIRST.finditer(sentence):
                if NEGATED_LEAD.fullmatch(sentence[:match.start()]) and not CONDITION.search(sentence[match.end():]):
                    continue
                raise ValueError("Section 8 says to run validation again first, but new reports have no re-run; remove that line")
            if RERUN_MENTION.search(sentence):
                raise ValueError("Section 8 names the re-run prompt or rerun.txt, but new reports have no re-run prompt "
                                 "or rerun.txt; remove that line")


def page_v4(context, fields, parts, verdict, confidence, plan, spec, prompts, pairs, current, checks):
    """Return the version 4 or 5 page: header card, score strip, tabs (Summary, answers, watch list, full report).
    Version 5 has no rerun (fields["rerun"] is None): no re-run pill or card, and its own historical warning."""
    css = (ASSETS / "report-v4.css").read_text()
    js = (ASSETS / "report-v4.js").read_text()
    favicon = base64.b64encode((ASSETS / "favicon.svg").read_bytes()).decode()
    script_hash = base64.b64encode(hashlib.sha256(js.encode()).digest()).decode()
    icon = (ASSETS / "report-icon.svg").read_text().strip().replace("<svg ", '<svg class="hero-icon" aria-hidden="true" focusable="false" ', 1)
    decisions, watch, phases, rerun = fields["decisions"], fields["watch"], context["phases"], fields["rerun"]
    version = context["format_version"]
    # A yes with a ready phase asks for another run before any phase starts.
    rerun_first = waits_for_rerun(context, pairs)
    # Current phase prompts wait for that run: no copy button, no download, the re-run card first.
    hold_phases = phases_held(context, current, pairs)
    fingerprints_match = all(matches for _, matches in checks)
    if has_rerun(context):
        warning = historical_warning_v4(rerun, fingerprints_match)
    else:
        warning = historical_warning_v5(fingerprints_match)

    # Header card. The accent is split from the raw title, then each part is escaped.
    before, accent, after = context["title"].partition(context["title_accent"])
    heading = escape(before) + "<em>" + escape(accent) + "</em>" + escape(after)
    kicker = " · ".join((escape(context["project"]), escape(context["audience"]), "Evidence as of " + escape(context["validation_date"])))
    recorded = context["kind"] == "saved" or not current
    status = "Recorded: " + verdict if recorded else verdict
    pills = [chip(*VERDICT_STYLE[verdict.lower()], escape(status)),
             chip("chip-info", "square", plural(len(phases), "phase") + " · " + plural(len(context["task_inventory"]), "task"))]
    if has_rerun(context):
        pills.append(chip(*RERUN_STYLE[rerun["recommendation"]], rerun_label(rerun)))
    if not current:
        pills.append(chip("chip-wait", "triangle", "Historical"))
    pills_html = '<ul class="pills" role="list">' + "".join(f"<li>{pill}</li>" for pill in pills) + "</ul>"
    notes = "".join('<p class="note-title"><strong>' + escape(note["title"]) + "</strong></p><p>" + inline(note["body"]) + "</p>" for note in context.get("notes", []))
    notes_html = f'<div class="notes">{notes}</div>' if notes else ""
    prompt_download = '<a href="handoff.txt" download>Prompt .txt</a>' if current and not hold_phases else ""
    hero = (f'<header class="hero"><div class="hero-text"><p class="kicker">{kicker}</p><h1>{heading}</h1>'
            f'<p class="lead">{inline(context["summary"])}</p>{pills_html}'
            f'<p class="freshness">{escape(freshness_state(version, fingerprints_match, current))} {inline(context["freshness"])}</p>{notes_html}'
            f'<div class="actions"><a href="report.md" download>Source Markdown</a>{prompt_download}'
            f'<button id="print-report" type="button">Print / PDF</button></div></div>{icon}</header>')
    scores_html = ('<div class="scores">'
                   f'<div class="score"><span class="score-label">PLAN · average /10</span><strong>{plan[0]} <span class="arrow">→</span> {plan[1]}</strong></div>'
                   f'<div class="score"><span class="score-label">SPEC · average /10</span><strong>{spec[0]} <span class="arrow">→</span> {spec[1]}</strong></div>'
                   f'<div class="score"><span class="score-label">Evidence confidence</span><strong>{escape(confidence)}</strong>'
                   '<small>Subjective estimate, not a measured probability</small></div></div>')

    # Tabs: a tab whose list is empty is left out.
    tabs = [("summary", "Summary", None)]
    if decisions:
        tabs.append(("answer", "Needs your answer", len(decisions)))
    if watch:
        tabs.append(("watch", "Watch list", len(watch)))
    tabs.append(("full", "Full report", None))
    tab_html = "".join(
        f'<button id="tab-{name}" type="button" role="tab" aria-controls="panel-{name}" aria-selected="{"true" if index == 0 else "false"}" '
        f'tabindex="{0 if index == 0 else -1}">{label}' + (f' <span class="badge">{count}</span>' if count else "") + "</button>"
        for index, (name, label, count) in enumerate(tabs))
    tablist = f'<div role="tablist" class="tabs" hidden aria-label="Report views">{tab_html}</div>'

    def panel(name, title, content):
        return (f'<section id="panel-{name}" class="panel" role="tabpanel" aria-labelledby="tab-{name}" tabindex="0">'
                f'<h2 class="panel-title">{title}</h2>{content}</section>')

    # Summary: diagrams, count cards, next session, re-run card.
    figures = '<div class="figs">' + "".join(render_diagram(diagram, index) for index, diagram in enumerate(fields["diagrams"], 1)) + "</div>"
    counts = ('<div class="counts">'
              + count_card("answer", decisions, "needs your answer", "need your answer", "Decisions", "No approvals are pending", answer_hint(decisions))
              + count_card("watch", watch, "item on the watch list", "items on the watch list", "Watch list", "No gaps, limits or risks recorded", watch_hint(watch))
              + "</div>")
    cards = []
    for phase in phases:
        state = phase_status(phase, verdict, current, rerun_first, version)
        style = ("chip-ok", "circle") if state == "Can start" else ("chip-wait", "diamond")
        flags = [chip(*style, "Ready" if state == "Can start" else state)]
        if phase["docs_only"]:
            flags.append(chip("chip-info", "square", "Docs only"))
        if phase["security_review"]:
            flags.append(chip("chip-info", "diamond", "Security review"))
        tasks = ("Task " if len(phase["tasks"]) == 1 else "Tasks ") + escape(", ".join(phase["tasks"]))
        cards.append(f'<li class="phase-card"><p class="phase-head">Phase {escape(phase["id"])} · {tasks}</p>'
                     f'<p class="phase-title">{inline(phase["title"])}</p><p class="phase-flags">{"".join(flags)}</p></li>')
    if pairs:
        phase_id, prompt = pairs[0]
        target, action, prompt_title = "summary-handoff-" + phase_id, f"Copy Phase {escape(phase_id)} prompt", f"Phase {escape(phase_id)} prompt"
    else:
        prompt, target, action, prompt_title = prompts[0][2], "summary-handoff", "Copy remediation prompt", "Remediation prompt"
    toolbar = prompt_toolbar(target, action, current, warning, hold_phases)
    next_session = (f'<div class="card next"><h3>Next session</h3><ul class="phase-cards" role="list">{"".join(cards)}</ul>'
                    f'<h4 class="prompt-title">{prompt_title}</h4><div class="prompt-toolbar">{toolbar}</div>'
                    f'<pre id="{escape(target)}" tabindex="0">{escape(prompt)}</pre>'
                    '<p><a href="#section-8">All prompts: Full report, section 8</a></p></div>')
    rerun_html = rerun_card(rerun) if has_rerun(context) else ""
    ordered = rerun_html + next_session if hold_phases else next_session + rerun_html
    panels = [panel("summary", "Summary", figures + counts + ordered)]

    if decisions:
        head = "".join(f'<th scope="col">{title}</th>' for title in ("ID", "Question", "Recommendation", "Confidence", "Holds back"))
        rows = "".join(
            f'<tr><td><a href="#section-6">{escape(item["id"])}</a></td><td>{inline(item["question"])}</td>'
            f'<td>{inline(item["recommendation"])}</td><td>{chip(*CONFIDENCE_STYLE[item["confidence"]], item["confidence"])}</td>'
            f'<td>{inline(item["holds_back"])}</td></tr>' for item in decisions)
        panels.append(panel("answer", "Needs your answer",
                            '<p>Each decision has a recommendation. The full options are in <a href="#section-6">Full report, section 6</a>.</p>'
                            '<div class="table-scroll" role="region" aria-label="Decisions that need your answer" tabindex="0">'
                            f'<table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'))
    if watch:
        items = "".join(
            f'<article class="watch watch-{item["kind"]}"><p class="watch-kind">{mark(WATCH_STYLE[item["kind"]][0])}'
            f'<span>{WATCH_STYLE[item["kind"]][1]}</span></p><h3>{escape(item["title"])}</h3><p>{inline(item["body"])}</p></article>'
            for item in watch)
        panels.append(panel("watch", "Watch list", f'<div class="watch-grid">{items}</div>'))

    marks = [mark(SECTION_SHAPES[index % len(SECTION_SHAPES)]) for index in range(8)]
    sections_html = "".join(report_sections(parts, version, verdict, prompts, pairs, context, current, marks, warning, rerun_first, hold_phases))
    panels.append(panel("full", "Full report", sections_html + defaulted_decisions(context["decisions_without_reply"]) + identity_details(checks, context)))

    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-{script_hash}'; img-src data:; base-uri 'none'; form-action 'none'">
<meta name="referrer" content="no-referrer"><link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,{favicon}">
<title>{escape(context["title"])}</title><style>{css}</style></head><body>
<a class="skip" href="#content">Skip to report</a>
<main id="content">{hero}
{scores_html}
{tablist}
{"".join(panels)}
</main><footer>Local report · No external fonts, scripts, analytics or network requests. Scores describe document quality; they do not guarantee implementation success.</footer><script>{js}</script></body></html>'''


class Rendered(tuple):
    """The result of render(): it unpacks as (page, handoff, current, rerun_prompt).

    Attributes for main(): pairs, the (phase_id, prompt) of each ready phase; prefix, the note that
    starts handoff.txt and each phase prompt file; held, whether those prompts wait for a re-run (version 4 only).
    """

    def __new__(cls, values, pairs, prefix):
        result = super().__new__(cls, values)
        result.pairs, result.prefix = pairs, prefix
        return result

    @property
    def held(self):
        return self.prefix == HELD_PREFIX


def render(source, context, run_files=()):
    """Validate and render a report. run_files are this run's own paths (report.md and context.json),
    which a version 4 or later prompt may quote even when they contain spaces."""
    version = context.get("format_version", 1)
    if type(version) is not int or version not in (1, 2, 3, 4, 5):
        raise ValueError("format_version must be 1 (legacy), 2, 3, 4 or 5")
    if context.get("kind") == "new" and version != 5:
        raise ValueError("New reports require format_version 5; earlier versions render saved reports only")
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    overview = feature_overview(context.get("feature")) if version in (2, 3) else ''
    defaults = defaulted_decisions(context.get("decisions_without_reply")) if version >= 2 else ''
    parts = sections(source)
    if any(not content for _, content in parts):
        raise ValueError("Every report section must contain its evidence or an explicit Unknown/None")
    if version >= 2 and [plain(heading).strip().lower() for heading, _ in parts] != [heading.lower() for heading in SOURCE_HEADINGS]:
        raise ValueError("Section headings must be: " + ", ".join(SOURCE_HEADINGS))
    plan, spec = scores(parts[1][1]), scores(parts[2][1])
    if version >= 2:
        decisions = decision_table(visible_part(parts[3][1], 4))
    else:
        decisions = [cells(line) for line in parts[3][1].splitlines() if line.strip().startswith("|")]
    if len(decisions) < 3 or any(len(row) != 4 for row in decisions):
        raise ValueError("Decision confidence requires a four-column table and at least one evidence row")
    verdict_match = re.match(r"(Ready after approvals|Not ready|Ready)\b", plain(parts[0][1]), re.I)
    if not verdict_match:
        raise ValueError("Section 1 must begin with Ready, Ready after approvals or Not ready")
    verdict = verdict_match.group(1)
    if version >= 3:
        phase_plan(context, verdict)
    if verdict.lower().startswith("ready") and context.get("review_status") != "complete":
        raise ValueError("A Ready report requires a completed cold read with findings dispositioned")
    verdict_source = visible_part(parts[0][1], 1) if version >= 2 else parts[0][1]
    confidence_match = re.search(r"Confidence:\s*(Unknown|\d+%)", plain(verdict_source), re.I)
    if not confidence_match:
        raise ValueError("Section 1 needs Confidence: <percentage or Unknown>")
    confidence = confidence_match.group(1)
    if confidence.lower() == "unknown":
        confidence = "Unknown"
    if confidence != "Unknown" and (not 0 <= int(confidence[:-1]) <= 100 or int(confidence[:-1]) % 5):
        raise ValueError("Confidence must be Unknown or a percentage in steps of five")
    prompts, pairs = handoff_prompts(parts[7][1], version, verdict, context, run_files)
    if version >= 4:
        fields = v4_fields(context, parts[5][1])
        if verdict.lower() == "ready after approvals" and not any(holds_back_work(item) for item in fields["decisions"]):
            raise ValueError("A Ready after approvals verdict needs its pending approvals in open_decisions, "
                             "and at least one that holds back work")
        if verdict.lower() == "ready after approvals":
            # A phase held back by a decision must wait for it, or it would get an implementation prompt.
            waits_for = [phase["waits_for"] for phase in context["phases"] if phase["status"] == "waiting"]
            for item in fields["decisions"]:
                if holds_back_work(item) and not any(names_id(item["id"], text) for text in waits_for):
                    raise ValueError(f"Open decision {item['id']} holds back work, so a waiting phase must name it in waits_for")
        if verdict.lower() == "ready" and any(holds_back_work(item) for item in fields["decisions"]):
            raise ValueError("A Ready verdict cannot have open decisions that hold back work; "
                             "set holds_back to Nothing or use Ready after approvals")
        if has_rerun(context):
            fields["rerun"] = rerun_check(context, verdict, confidence, plan[1], spec[1], run_files)
        else:
            if "validation_run" in context or "rerun" in context:
                raise ValueError("Version 5 reports have no validation_run or rerun; re-validation was removed")
            fields["rerun"] = None
        run_first_note(parts[7][1], prompts, context)
    handoff = prompts[0][2]
    if context.get("handoff_status") not in {"current", "historical"}:
        raise ValueError("Set handoff_status to current or historical after checking Git state and approvals")
    checks = document_checks(context)
    fingerprints_match = all(matches for _, matches in checks)
    current = fingerprints_match and context["handoff_status"] == "current"
    scope = context.get("scope", {})
    scope_rows = scope.get("rows", [])
    required_metrics = {"Delivery phases", "Implementation tasks", "Supporting tasks", "Numbered tasks", "Dependencies / services"}
    if not required_metrics.issubset({row.get("metric") for row in scope_rows}):
        raise ValueError("Scope comparison needs phases, implementation/supporting/numbered tasks and dependencies/services")
    if not scope.get("explanation") or not scope.get("approval"):
        raise ValueError("Scope comparison needs an explanation and approval basis (or Unknown)")
    if context.get("kind") not in {"saved", "new"}:
        raise ValueError("Context kind must be saved or new")
    prefix = prompt_prefix(context, current, pairs)
    marked = prefix + handoff
    if version >= 4:
        page = page_v4(context, fields, parts, verdict, confidence, plan, spec, prompts, pairs, current, checks)
        # A saved report's run label may be stale (later runs can exist), so only a new report writes rerun.txt.
        # Only a new version 4 run wrote rerun.txt; version 4 now renders saved reports only.
        return Rendered((page, marked, current, None), pairs, prefix)
    css = (ASSETS / "report.css").read_text()
    js = (ASSETS / "report.js").read_text()
    favicon = base64.b64encode((ASSETS / "favicon.svg").read_bytes()).decode()
    script_hash = base64.b64encode(hashlib.sha256(js.encode()).digest()).decode()
    body = report_sections(parts, version, verdict, prompts, pairs, context, current)
    title = escape(context["title"])
    note_html = ''.join('<article><h3>' + escape(note["title"]) + '</h3><p>' + inline(note["body"]) + '</p></article>' for note in context.get("notes", []))
    state = freshness_state(version, fingerprints_match, current)
    kind = context["kind"]
    label = "Saved validation" if kind == "saved" else "Validation report"
    status = "Recorded: " + verdict if kind == "saved" or not current else verdict
    prompt_download = '<a href="handoff.txt" download>Prompt .txt</a>' if current else ''
    overview_link = '<a href="#feature-overview">Feature overview</a>' if overview else ''
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-{script_hash}'; img-src data:; base-uri 'none'; form-action 'none'">
<meta name="referrer" content="no-referrer"><link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,{favicon}">
<title>{title} — Plan validation</title><style>{css}</style></head><body>
<a class="skip" href="#content">Skip to report</a>
<header><a class="wordmark" href="#top">PLAN VALIDATION</a><div class="header-actions"><a href="report.md" download>Source Markdown</a>{prompt_download}<button id="print-report" type="button">Print / PDF</button></div></header>
<main id="content"><div id="top" class="hero"><div class="eyebrow">{label} · {escape(context['validation_date'])}</div>
<h1>{title}</h1><p class="lead">{inline(context['summary'])}</p><div class="verdict">{escape(status)}</div>
<div class="metrics"><div><span>PLAN · average /10</span><strong>{plan[0]} <i>→</i> {plan[1]}</strong></div><div><span>SPEC · average /10</span><strong>{spec[0]} <i>→</i> {spec[1]}</strong></div><div><span>Evidence confidence</span><strong>{escape(confidence)}</strong><small>Subjective estimate, not a measured probability</small></div></div>
<p class="freshness">{escape(state)} {inline(context['freshness'])}</p></div>
<nav aria-label="Report sections">{overview_link}<a href="#section-1">Summary</a><a href="#section-2">Scores</a><a href="#scope">Scope</a><a href="#section-5">Changes</a><a href="#section-6">Open items</a><a href="#section-7">Checks</a><a href="#section-8">Start prompt</a></nav>
<div class="notes">{note_html}</div>{overview}{''.join(body)}
{identity_details(checks, context)}
{defaults}
</main><footer>Local report · No external fonts, scripts, analytics or network requests. Scores describe document quality; they do not guarantee implementation success.</footer><script>{js}</script></body></html>'''
    return Rendered((page, marked, current, None), pairs, prefix)


def foreground(browser):
    """Console browsers and unknown $BROWSER commands would run in the caller's terminal."""
    if isinstance(browser, webbrowser.GenericBrowser):
        return not isinstance(browser, webbrowser.BackgroundBrowser)
    return isinstance(browser, webbrowser.UnixBrowser) and not browser.background


def open_report(path):
    """Start the default graphical browser on path without waiting; return (opened, reason)."""
    if sys.platform not in ("darwin", "win32") and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return False, "no display"
    try:
        browser = webbrowser.get()
        if foreground(browser):
            return False, "no graphical browser"
        uri = path.as_uri()
        # A launched browser must not inherit our output, or a caller reading it waits for the browser to exit.
        sys.stdout.flush()
        sys.stderr.flush()
        null = os.open(os.devnull, os.O_RDWR)
        saved = []
        try:
            for fd in (0, 1, 2):
                saved.append((fd, os.dup(fd)))
                os.dup2(null, fd)
            result = browser.open(uri, new=2)
        finally:
            for fd, copy in saved:
                os.dup2(copy, fd)
                os.close(copy)
            os.close(null)
    except Exception as error:  # Opening is best effort and must never fail a written report.
        return False, str(error) or type(error).__name__
    return bool(result), "" if result else "browser did not start"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--context", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--open", action="store_true", help="open report.html in the default graphical browser")
    args = parser.parse_args()
    if args.output.name != "report.html":
        parser.error("Use a dedicated run directory with output named report.html")
    try:
        source = args.report.read_text(encoding="utf-8")
        context = json.loads(args.context.read_text(encoding="utf-8"))
        # This run's report.md and context.json, as given and absolute, so a prompt may quote them with spaces.
        run_files = {str(path) for file in (args.output.with_suffix(".md"), args.output.with_name("context.json"), args.context)
                     for path in (file, file.absolute(), file.resolve())}
        rendered = render(source, context, run_files)
        page, handoff, current, _ = rendered
        args.output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Delete the old prompt files before any write, so a failed write never leaves an earlier,
        # unmarked prompt beside a new page.
        rerun_path = args.output.with_name("rerun.txt")
        # A saved version 1-4 re-render keeps the rerun.txt an earlier version 4 run wrote. Version 5 has no
        # re-run, so its render deletes any.
        if context.get("kind") != "saved" or context.get("format_version", 1) >= 5:
            rerun_path.unlink(missing_ok=True)
        args.output.with_name("handoff.txt").unlink(missing_ok=True)
        for stale in args.output.parent.glob("handoff-phase-*.txt"):
            stale.unlink()
        if args.report.resolve() != args.output.with_suffix(".md").resolve():
            args.output.with_suffix(".md").write_text(source, encoding="utf-8")
        args.output.write_text(page, encoding="utf-8")
        args.output.with_name("handoff.txt").write_text(handoff + "\n", encoding="utf-8")
        phase_files = []
        # The phase files get the same historical or held note as handoff.txt, chosen once by render().
        held = rendered.held
        for phase_id, prompt in rendered.pairs:
            path = args.output.with_name(f"handoff-phase-{phase_id}.txt")
            path.write_text(rendered.prefix + prompt + "\n", encoding="utf-8")
            phase_files.append(str(path.resolve()))
    except (ValueError, KeyError, OSError, ArithmeticError) as error:
        parser.exit(1, f"Report not generated: {error}\n")
    result = {"html": str(args.output.resolve()), "handoff": str(args.output.with_name("handoff.txt").resolve()), "handoff_current": current, "handoff_held": held, "phase_handoffs": phase_files,
              "rerun": str(rerun_path.resolve()) if rerun_path.exists() else None}
    if args.open:
        result["opened"], reason = open_report(args.output.resolve())
        if not result["opened"]:
            print(f"Browser not opened: {reason}", file=sys.stderr)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
