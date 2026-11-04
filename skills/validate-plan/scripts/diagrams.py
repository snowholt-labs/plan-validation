"""Validate report diagram data and draw it as escaped inline SVG.

Uses only Python's standard library. The agent describes diagrams as data in
``context.json``; this module rejects data that breaks a limit or whose layout
would collide, and never moves or shortens text. Every text value is escaped.
"""

import html
import re
import unicodedata


LIMITS = {"eyebrow": 40, "title": 60, "node_title": 24, "node_sub": 30, "zone_label": 28,
          "link_label": 14, "link_sub": 18, "branch_title": 14, "branch_sub": 18}
CHAR_WIDTH = {"t": 7, "s": 6}  # SVG units per character: 13 px titles and labels, 11 px sub-lines
FONT = {key: "s" if key.endswith("_sub") else "t" for key in LIMITS}
SIZE = {"t": 13, "s": 11}
PAD = 10
MARGIN = 6
HEAD = 8  # arrowhead length and width
HALF_STROKE = 0.75

ZONE_W, GAP, PILL_H, PILL_GAP, LABEL_H = 220, 132, 48, 22, 34
ROW = PILL_H + PILL_GAP
# Elbow lanes as offsets into the gap. At the limits, link text spans offsets 12-120
# and arrowheads 0-8 and 124-132, so the first lane on each side always stays clear.
FORWARD_LANES = (122, 116, 110, 104)
BACKWARD_LANES = (10, 16, 22, 28)
ELBOW_ARRIVAL = 10  # an elbow reaches its target this far off the centre line

STEP_W, STEP_H, STEP_GAP, NUM_R = 260, 48, 22, 12
BRANCH_W, BRANCH_GAP, BRANCH_SPACING = 130, 40, 24
FLOW_W = 608
NUM_AREA = PAD + 2 * NUM_R
STEP_TEXT_W = STEP_W - NUM_AREA  # width that holds step text, padding included
TONE_RX = {"retry": 14, "stop": 3, "note": 8}
PILL_RX = 12

NODE_ID = re.compile(r"[a-z][a-z0-9-]{0,23}")
MARKERS = (("ar", "ar"), ("fwd", "ar-fwd"), ("back", "ar-back"), ("dash", "ar-dash"))
SHAPES = ("pill", "badge")
TEXTS = ("text", "label")


def text_width(value):
    """Count wide and full-width characters twice so wide scripts cannot overflow."""
    return sum(2 if unicodedata.east_asian_width(char) in ("W", "F") else 1 for char in value)


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def check_text(record, key, where, number, limit=None, required=True):
    if not required and record.get(key) is None:
        return
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Diagram {number}: {where}{key} must be nonempty text")
    if limit and text_width(value) > LIMITS[limit]:
        raise ValueError(f"Diagram {number}: {where}{key} is longer than {LIMITS[limit]} characters ({limit})")


def sized_list(value, low, high, what, number):
    if not isinstance(value, list) or not low <= len(value) <= high or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"Diagram {number}: {what} must be a list of {low} to {high} objects")
    return value


def check_zones(diagram, number):
    zones = sized_list(diagram.get("zones"), 1, 3, "zones", number)
    zone_of = {}
    for zi, zone in enumerate(zones):
        check_text(zone, "label", f"zones[{zi}].", number, "zone_label")
        if not isinstance(zone.get("chain", False), bool):
            raise ValueError(f"Diagram {number}: zones[{zi}].chain must be true or false")
        for ni, node in enumerate(sized_list(zone.get("nodes"), 1, 5, f"zones[{zi}].nodes", number)):
            where = f"zones[{zi}].nodes[{ni}]."
            node_id = node.get("id")
            if not isinstance(node_id, str) or not NODE_ID.fullmatch(node_id):
                raise ValueError(f"Diagram {number}: {where}id must be 1 to 24 lowercase letters, digits or hyphens, starting with a letter")
            if node_id in zone_of:
                raise ValueError(f"Diagram {number}: {where}id {node_id!r} is used twice")
            zone_of[node_id] = zi
            check_text(node, "title", where, number, "node_title")
            check_text(node, "sub", where, number, "node_sub", required=False)
    links = diagram.get("links", [])
    if not isinstance(links, list) or not all(isinstance(link, dict) for link in links):
        raise ValueError(f"Diagram {number}: links must be a list of objects")
    for li, link in enumerate(links):
        where = f"links[{li}]."
        for end in ("from", "to"):
            if not isinstance(link.get(end), str) or link[end] not in zone_of:
                raise ValueError(f"Diagram {number}: {where}{end} names no node: {link.get(end)!r}")
        source, target = zone_of[link["from"]], zone_of[link["to"]]
        if source == target:
            raise ValueError(f"Diagram {number}: {where} joins two nodes of one zone; use chain instead")
        if abs(source - target) != 1:
            raise ValueError(f"Diagram {number}: {where} joins zones that are not neighbours")
        check_text(link, "label", where, number, "link_label")
        check_text(link, "sub", where, number, "link_sub", required=False)


def check_flow(diagram, number):
    steps = sized_list(diagram.get("steps"), 2, 7, "steps", number)
    for si, step in enumerate(steps):
        check_text(step, "title", f"steps[{si}].", number, "node_title")
        check_text(step, "sub", f"steps[{si}].", number, "node_sub", required=False)
    branches = diagram.get("branches", [])
    if branches != []:
        sized_list(branches, 1, 2, "branches", number)
    used = set()
    for bi, branch in enumerate(branches):
        where = f"branches[{bi}]."
        start = branch.get("from_step")
        if not is_int(start) or not 1 <= start <= len(steps):
            raise ValueError(f"Diagram {number}: {where}from_step must be a step number from 1 to {len(steps)}")
        check_text(branch, "title", where, number, "branch_title")
        check_text(branch, "sub", where, number, "branch_sub", required=False)
        if branch.get("tone") not in TONE_RX:
            raise ValueError(f"Diagram {number}: {where}tone must be retry, stop or note")
        back = branch.get("returns_to")
        if back is not None:
            if start in used:
                raise ValueError(f"Diagram {number}: {where}returns_to is allowed only on the first branch from a step")
            if not is_int(back) or not 1 <= back < start:
                raise ValueError(f"Diagram {number}: {where}returns_to must be an earlier step number")
        used.add(start)


def validate_diagrams(value):
    """Return the diagrams unchanged, or raise ValueError for data that breaks the contract."""
    if not isinstance(value, list) or not 1 <= len(value) <= 3:
        raise ValueError("Diagrams must be a list of 1 to 3 items")
    for number, diagram in enumerate(value, 1):
        if not isinstance(diagram, dict):
            raise ValueError(f"Diagram {number} must be an object")
        for key in ("eyebrow", "title", "description", "caption"):
            check_text(diagram, key, "", number, key if key in LIMITS else None)
        if diagram.get("kind") == "zones":
            check_zones(diagram, number)
        elif diagram.get("kind") == "flow":
            check_flow(diagram, number)
        else:
            raise ValueError(f"Diagram {number}: kind must be zones or flow")
        problem = find_overlap(layout_boxes(diagram))
        if problem:
            raise ValueError(f"Diagram {number} overlaps: {problem}")
    return value


# Layout. Items carry what rendering needs; layout_boxes projects them to boxes.

def text_item(kind, value, cls, font, x, baseline, anchor="start", group=None):
    width = text_width(value) * CHAR_WIDTH[font]
    left = x - width / 2 if anchor == "middle" else x
    box = (left, baseline - 0.8 * SIZE[font], width, SIZE[font])
    return {"kind": kind, "box": box, "text": value, "cls": cls, "x": x, "y": baseline, "anchor": anchor, "group": group}


def pill_items(record, left, y, width, cls, rx, text_x=None, group=None):
    x = left + PAD if text_x is None else text_x
    items = [{"kind": "pill", "box": (left, y, width, PILL_H), "cls": cls, "rx": rx, "group": group}]
    sub = record.get("sub")
    items.append(text_item("text", record["title"], "t", "t", x, y + (20 if sub else 29), group=group))
    if sub:
        items.append(text_item("text", sub, "s", "s", x, y + 36, group=group))
    return items


def arrow(points, cls, marker, group=None):
    return {"kind": "arrow", "points": points, "cls": cls, "marker": marker, "group": group}


def arrow_boxes(item):
    points, boxes = item["points"], []
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        boxes.append(("line", min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)))
    (qx, qy), (px, py) = points[-2], points[-1]
    if py == qy:
        boxes.append(("head", px if px > qx else px - HEAD, py - HEAD / 2, HEAD, HEAD))
    else:
        boxes.append(("head", px - HEAD / 2, py if py > qy else py - HEAD, HEAD, HEAD))
    return boxes


def item_boxes(item):
    return arrow_boxes(item) if item["kind"] == "arrow" else [(item["kind"],) + tuple(item["box"])]


def zone_items(diagram):
    zones, items, place = diagram["zones"], [], {}
    top = MARGIN + LABEL_H
    for zi, zone in enumerate(zones):
        left, group = MARGIN + zi * (ZONE_W + GAP), "z-" + "abc"[zi]
        items.append(text_item("label", zone["label"], "zl", "t", left + PAD, MARGIN + 22, group=group))
        for row, node in enumerate(zone["nodes"]):
            y = top + row * ROW
            place[node["id"]] = (zi, row)
            items += pill_items(node, left, y, ZONE_W, "pill", PILL_RX, group=group)
            if row and zone.get("chain"):
                centre = left + ZONE_W / 2
                items.append(arrow([(centre, y - PILL_GAP), (centre, y - HEAD)], "ar", "ar", group))
    centre_line = lambda row: top + row * ROW + PILL_H / 2  # noqa: E731
    elbows = []
    for link in diagram.get("links", []):
        (source_zone, source_row), (target_zone, target_row) = place[link["from"]], place[link["to"]]
        forward = target_zone > source_zone
        gap = MARGIN + min(source_zone, target_zone) * (ZONE_W + GAP) + ZONE_W
        y = centre_line(source_row)
        items.append(text_item("label", link["label"], "lb", "t", gap + GAP / 2, y - 8, "middle"))
        if link.get("sub"):
            items.append(text_item("label", link["sub"], "ls", "s", gap + GAP / 2, y + 14, "middle"))
        start, end = (gap, gap + GAP) if forward else (gap + GAP, gap)
        tip = end - HEAD if forward else end + HEAD
        cls, marker = ("ar ar-fwd", "fwd") if forward else ("ar ar-back", "back")
        if source_row == target_row:
            items.append(arrow([(start, y), (tip, y)], cls, marker))
        else:
            arrive = centre_line(target_row) + (-ELBOW_ARRIVAL if target_row > source_row else ELBOW_ARRIVAL)
            lanes = [gap + offset for offset in (FORWARD_LANES if forward else BACKWARD_LANES)]
            elbows.append(([[(start, y), (lane, y), (lane, arrive), (tip, arrive)] for lane in lanes], cls, marker))
    # Every label, straight arrow and elbow arrowhead is known before any lane is chosen.
    known = [box for item in items for box in item_boxes(item)]
    known += [arrow_boxes(arrow(options[0], cls, marker))[-1] for options, cls, marker in elbows]
    for options, cls, marker in elbows:
        chosen = options[0]
        for points in options:
            lines = arrow_boxes(arrow(points, cls, marker))[:-1]
            if not any(conflict(new, old) for new in lines for old in known):
                chosen = points
                break
        items.append(arrow(chosen, cls, marker))
        known += arrow_boxes(items[-1])[:-1]
    return len(zones) * ZONE_W + (len(zones) - 1) * GAP + 2 * MARGIN, items


def flow_items(diagram):
    items, right = [], MARGIN + STEP_W
    for si, step in enumerate(diagram["steps"]):
        y = MARGIN + si * ROW
        items += pill_items(step, MARGIN, y, STEP_W, "pill", PILL_RX, text_x=MARGIN + NUM_AREA + PAD)
        cx, cy = MARGIN + PAD + NUM_R, y + STEP_H / 2
        items.append({"kind": "badge", "box": (cx - NUM_R, cy - NUM_R, 2 * NUM_R, 2 * NUM_R), "cx": cx, "cy": cy})
        items.append(text_item("text", str(si + 1), "num", "t", cx, cy + 4.5, "middle"))
        if si:
            centre = MARGIN + STEP_W / 2
            items.append(arrow([(centre, y - STEP_GAP), (centre, y - HEAD)], "ar", "ar"))
    first_from = set()
    for branch in diagram.get("branches", []):
        y = MARGIN + (branch["from_step"] - 1) * ROW
        centre = y + STEP_H / 2
        if branch["from_step"] in first_from:
            left = right + BRANCH_GAP + BRANCH_W + BRANCH_SPACING
            below, middle = y + STEP_H + STEP_GAP / 2, left + BRANCH_W / 2
            fork = right + PAD
            items.append(arrow([(right, centre + 12), (fork, centre + 12), (fork, below), (middle, below),
                                (middle, y + STEP_H + HEAD)], "ar", "ar"))
        else:
            left = right + BRANCH_GAP
            items.append(arrow([(right, centre), (left - HEAD, centre)], "ar", "ar"))
        first_from.add(branch["from_step"])
        items += pill_items(branch, left, y, BRANCH_W, "pill pill-" + branch["tone"], TONE_RX[branch["tone"]])
        if branch.get("returns_to") is not None:
            lane = right + BRANCH_GAP / 2
            arrive = MARGIN + (branch["returns_to"] - 1) * ROW + STEP_H / 2 + ELBOW_ARRIVAL
            items.append(arrow([(left, centre - 12), (lane, centre - 12), (lane, arrive), (right + HEAD, arrive)],
                               "ar ar-dash", "dash"))
    return FLOW_W, items


def layout(diagram):
    width, items = zone_items(diagram) if diagram["kind"] == "zones" else flow_items(diagram)
    boxes = [box for item in items for box in item_boxes(item)]
    height = max(y + h for _, _, y, _, h in boxes) + MARGIN
    return [("view", 0, 0, width, height)] + boxes, items


def layout_boxes(diagram):
    """Return ``(kind, x, y, width, height)`` for the view, every shape, text line and line segment."""
    return layout(diagram)[0]


# Overlap rules, shared by validate_diagrams and the layout tests.

def hits(a, b):
    return a[1] < b[1] + b[3] and b[1] < a[1] + a[3] and a[2] < b[2] + b[4] and b[2] < a[2] + a[4]


def inside(a, b, slack=1e-6):
    return (a[1] >= b[1] - slack and a[2] >= b[2] - slack
            and a[1] + a[3] <= b[1] + b[3] + slack and a[2] + a[4] <= b[2] + b[4] + slack)


def thick(box):
    kind, x, y, w, h = box
    if kind != "line":
        return box
    return (kind, x, y - HALF_STROKE, w, 2 * HALF_STROKE) if h == 0 else (kind, x - HALF_STROKE, y, 2 * HALF_STROKE, h)


def conflict(a, b):
    """Whether two boxes collide. Lines may cross at right angles but never run alongside each other."""
    kinds = {a[0], b[0]}
    if kinds == {"line"}:
        if (a[4] == 0) != (b[4] == 0):
            return False
        axis = 1 if a[4] == 0 else 2  # the coordinate along the line
        across = 2 if axis == 1 else 1
        span = 3 if axis == 1 else 4
        return abs(a[across] - b[across]) < 4 and max(a[axis], b[axis]) < min(a[axis] + a[span], b[axis] + b[span])
    if kinds == {"pill", "badge"}:
        return False  # find_overlap checks that each badge sits inside a pill
    if a[0] in TEXTS and b[0] in SHAPES or b[0] in TEXTS and a[0] in SHAPES:
        text, shape = (a, b) if a[0] in TEXTS else (b, a)
        return hits(text, shape) and (text[0] == "label" or not inside(text, shape))
    return hits(thick(a), thick(b))


def describe(box):
    return f"{box[0]} at ({box[1]:g}, {box[2]:g})"


def find_overlap(boxes):
    """Return a description of the first collision in a layout, or None. ``boxes[0]`` is the view."""
    view, items = boxes[0], boxes[1:]
    for box in items:
        if not inside(box, view):
            return f"{describe(box)} leaves the diagram area"
        holders = [s for s in items if s[0] == "pill" or (box[0] == "text" and s[0] == "badge")]
        if box[0] in ("text", "badge") and not any(inside(box, s) for s in holders if s is not box):
            return f"{describe(box)} leaves its shape"
    for index, first in enumerate(items):
        for second in items[index + 1:]:
            if conflict(first, second):
                return f"{describe(first)} and {describe(second)}"
    return None


# Rendering.

def number(value):
    return f"{value:g}"


def render_item(item, prefix):
    kind = item["kind"]
    if kind == "pill":
        x, y, w, h = item["box"]
        return (f'<rect class="{item["cls"]}" x="{number(x)}" y="{number(y)}" width="{number(w)}" '
                f'height="{number(h)}" rx="{item["rx"]}"/>')
    if kind == "badge":
        return f'<circle class="num" cx="{number(item["cx"])}" cy="{number(item["cy"])}" r="{NUM_R}"/>'
    if kind == "arrow":
        path = "".join(("M" if i == 0 else "L") + f"{number(x)} {number(y)}" for i, (x, y) in enumerate(item["points"]))
        return f'<path class="{item["cls"]}" d="{path}" marker-end="url(#{prefix}m-{item["marker"]})"/>'
    anchor = ' text-anchor="middle"' if item["anchor"] == "middle" else ""
    return (f'<text class="{item["cls"]}" x="{number(item["x"])}" y="{number(item["y"])}"{anchor}>'
            f'{html.escape(item["text"], quote=True)}</text>')


def render_diagram(diagram, index):
    """Return one escaped ``<section class="fig">`` holding the diagram's heading, SVG and caption."""
    boxes, items = layout(diagram)
    prefix = f"dg-{int(index)}-"
    escape = lambda value: html.escape(value, quote=True)  # noqa: E731
    view = " ".join(number(value) for value in boxes[0][1:])
    svg_class = "dg-flow" if diagram["kind"] == "flow" else f'dg-w{len(diagram["zones"])}'
    markers = "".join(
        f'<marker id="{prefix}m-{name}" viewBox="0 0 {HEAD} {HEAD}" refX="0" refY="{HEAD // 2}" '
        f'markerWidth="{HEAD}" markerHeight="{HEAD}" markerUnits="userSpaceOnUse" orient="auto">'
        f'<path class="{cls}" d="M0 0L{HEAD} {HEAD // 2}L0 {HEAD}z"/></marker>'
        for name, cls in MARKERS
    )
    body, group = [], None
    for item in items:
        if item.get("group") != group:
            body.append("</g>" if group else "")
            group = item.get("group")
            body.append(f'<g class="{group}">' if group else "")
        body.append(render_item(item, prefix))
    body.append("</g>" if group else "")
    return (
        f'<section class="fig" aria-labelledby="{prefix}h">'
        f'<p class="fig-eyebrow">{escape(diagram["eyebrow"])}</p>'
        f'<h3 id="{prefix}h">{escape(diagram["title"])}</h3>'
        f'<div class="dg-wrap"><svg class="{svg_class}" viewBox="{view}" role="img" aria-labelledby="{prefix}t {prefix}d">'
        f'<title id="{prefix}t">{escape(diagram["title"])}</title><desc id="{prefix}d">{escape(diagram["description"])}</desc>'
        f'<defs>{markers}</defs>{"".join(body)}</svg></div>'
        f'<p class="fig-caption">{escape(diagram["caption"])}</p>'
        "</section>"
    )
