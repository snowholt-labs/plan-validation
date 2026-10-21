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
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlsplit


ASSETS = Path(__file__).resolve().parents[1] / "assets"
READABLE_HEADINGS = (
    "Can implementation start?", "Plan scores", "Specification scores", "How certain we are",
    "What changed", "Open items", "What we checked", "Start the next session",
)
SOURCE_HEADINGS = (
    "Verdict", "PLAN comparison", "SPEC comparison", "Decision confidence",
    "Changes", "Open items", "Verification and checkout", "Fresh-session handoff",
)
# Phase IDs become file names, so they cannot contain path separators.
PHASE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]{0,15}\Z")


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


def inline(value):
    """Escape text before adding only our own markup, including inside links."""
    pattern = r"(`+)(.+?)\1|\[([^\]]+)\]\(([^\s)]+)\)|\*\*(.+?)\*\*"
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


def document_checks(context):
    documents = context.get("documents", [])
    if len(documents) != 2 or {doc.get("label") for doc in documents} != {"PLAN", "SPEC"}:
        raise ValueError("Context must identify exactly PLAN and SPEC")
    results = []
    for doc in documents:
        expected = doc.get("sha256", "")
        if not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("Each document needs its full recorded SHA256")
        path = Path(doc["path"])
        if not path.is_absolute():
            raise ValueError("Document paths must be absolute")
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


def word_count(handoff):
    # A backtick-quoted absolute path is one word, even when it contains spaces.
    return len(re.sub(r"`(?:/|~/|[A-Za-z]:[\\/])[^`\n]*`", "path", handoff).split())


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


def render(source, context):
    version = context.get("format_version", 1)
    if type(version) is not int or version not in (1, 2, 3):
        raise ValueError("format_version must be 1 (legacy), 2 or 3")
    if context.get("kind") == "new" and version != 3:
        raise ValueError("New reports require format_version 3; legacy rendering is for saved reports only")
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    overview = feature_overview(context.get("feature")) if version >= 2 else ''
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
    if version == 3:
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
    prompts = fenced_blocks(parts[7][1])
    if len(prompts) != 1:
        raise ValueError("Section 8 must contain one complete fenced handoff")
    _, _, prompt_start, prompt_end = prompts[0]
    handoff = parts[7][1][prompt_start:prompt_end].rstrip("\n")
    if not handoff.strip():
        raise ValueError("Section 8 must contain one complete fenced handoff")
    if version >= 2 and word_count(handoff) > 80:
        raise ValueError("Fresh-session handoff must be at most 80 words; link to the plan, spec and report for details and wrap paths in backticks")
    # Any "implement" instruction, except a negated one such as "Do not implement".
    implement = re.search(r"(?<!not )(?<!n't )(?<!never )\bimplement\b", handoff, re.I)
    if verdict.lower() == "not ready" and (implement or "do not start dependent implementation" not in handoff.lower()):
        raise ValueError("Not ready requires a remediation prompt stating: Do not start dependent implementation")
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
    scope_table = '<div class="table-scroll" role="region" aria-label="Scope comparison" tabindex="0"><table><thead><tr>'
    scope_table += ''.join(f'<th scope="col">{title}</th>' for title in ["Measure", "Original", "Revised", "Reason / evidence"])
    scope_table += '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{inline(str(row[key]))}</td>' for key in ["metric", "original", "revised", "reason"]) + '</tr>' for row in scope_rows) + '</tbody></table></div>'
    scope_html = '<aside id="scope" class="scope"><h3>Scope &amp; complexity</h3><p>' + inline(scope["explanation"]) + '</p>' + scope_table + '<p><strong>Approval basis.</strong> ' + inline(scope["approval"]) + '</p></aside>'
    css = (ASSETS / "report.css").read_text()
    js = (ASSETS / "report.js").read_text()
    favicon = base64.b64encode((ASSETS / "favicon.svg").read_bytes()).decode()
    script_hash = base64.b64encode(hashlib.sha256(js.encode()).digest()).decode()
    body = []
    for index, (heading, content) in enumerate(parts, 1):
        if version >= 2:
            heading = READABLE_HEADINGS[index - 1]
        if index == 8:
            if version >= 2:
                detail_marker(content, index)
            start, end, _, _ = prompts[0]
            intro = content[:start] + content[end:]
            action = "Copy implementation prompt" if verdict.lower().startswith("ready") else "Copy remediation prompt"
            if current:
                toolbar = f'<button id="copy-prompt" type="button">{action}</button><span id="copy-status" role="status" aria-live="polite"></span>'
            else:
                toolbar = '<p class="warning">Document identity, Git state or approvals changed or could not be checked. This is a historical prompt. Revalidate the changed scope before using it.</p>'
            content_html = markdown(intro) + '<div class="prompt-toolbar">' + toolbar + '</div><pre id="handoff" tabindex="0">' + escape(handoff) + '</pre>'
        else:
            content_html = section_content(content, index) if version >= 2 else markdown(content)
        body.append(f'<section id="section-{index}" aria-labelledby="heading-{index}"><div class="section-heading"><span>{index:02}</span><h2 id="heading-{index}">{inline(heading)}</h2></div>' + (scope_html if index == 5 else "") + content_html + '</section>')
    title = escape(context["title"])
    note_html = ''.join('<article><h3>' + escape(note["title"]) + '</h3><p>' + inline(note["body"]) + '</p></article>' for note in context.get("notes", []))
    if version >= 2:
        state = "Plan and spec match the saved review." if fingerprints_match else "Plan or spec changed or could not be read."
        stale = " This handoff is historical. Recheck the saved evidence before starting."
    else:
        state = "Document fingerprints match the saved validation." if fingerprints_match else "Document fingerprints differ or files are unavailable."
        stale = " The handoff is historical; refresh its evidence before implementation."
    if not current:
        state += stale
    kind = context.get("kind")
    if kind not in {"saved", "new"}:
        raise ValueError("Context kind must be saved or new")
    label = "Saved validation" if kind == "saved" else "Validation report"
    status = "Recorded: " + verdict if kind == "saved" or not current else verdict
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    doc_html = ''.join('<li><strong>' + escape(doc["label"]) + '</strong> · ' + ("matches" if matches else "changed / unavailable") + '<br><code>' + escape(doc["path"]) + '</code><br><small>SHA256 ' + escape(doc["sha256"]) + '</small></li>' for doc, matches in checks)
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
<details class="identity"><summary>Document identity &amp; report provenance</summary><ul>{doc_html}</ul><p>HTML generated {escape(stamp)}. {escape(context.get('provenance', ''))}</p></details>
{defaults}
</main><footer>Local report · No external fonts, scripts, analytics or network requests. Scores describe document quality; they do not guarantee implementation success.</footer><script>{js}</script></body></html>'''
    if not current:
        handoff = "HISTORICAL PROMPT — DO NOT EXECUTE.\nDocument identity, Git state or approvals need revalidation before implementation.\n\n" + handoff
    return page, handoff, current


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--context", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.name != "report.html":
        parser.error("Use a dedicated run directory with output named report.html")
    try:
        source = args.report.read_text(encoding="utf-8")
        context = json.loads(args.context.read_text(encoding="utf-8"))
        page, handoff, current = render(source, context)
        args.output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if args.report.resolve() != args.output.with_suffix(".md").resolve():
            args.output.with_suffix(".md").write_text(source, encoding="utf-8")
        args.output.write_text(page, encoding="utf-8")
        args.output.with_name("handoff.txt").write_text(handoff + "\n", encoding="utf-8")
    except (ValueError, KeyError, OSError, ArithmeticError) as error:
        parser.exit(1, f"Report not generated: {error}\n")
    print(json.dumps({"html": str(args.output.resolve()), "handoff": str(args.output.with_name("handoff.txt").resolve()), "handoff_current": current}))


if __name__ == "__main__":
    main()
