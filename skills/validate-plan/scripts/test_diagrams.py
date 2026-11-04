"""Validation, escaping and layout regressions for report diagrams."""

import copy
import html
import re
import unittest

import sys

from render_report import diagrams  # the one module object the renderer uses

BRANCH_W, GAP, LIMITS, PAD, STEP_W, ZONE_W = (diagrams.BRANCH_W, diagrams.GAP, diagrams.LIMITS, diagrams.PAD,
                                              diagrams.STEP_W, diagrams.ZONE_W)
find_overlap, layout_boxes = diagrams.find_overlap, diagrams.layout_boxes
render_diagram, validate_diagrams = diagrams.render_diagram, diagrams.validate_diagrams
AVERAGE_WIDTH = {"t": 7, "s": 6}  # average SVG units per character that set LIMITS: 13 px and 11 px text


ZONES = {
    "kind": "zones",
    "eyebrow": "Architecture · planned",
    "title": "Who talks to whom",
    "description": "The caller asks the retry helper, which sends requests to the remote API.",
    "caption": "The helper waits between tries.",
    "zones": [
        {"label": "Your app", "nodes": [
            {"id": "caller", "title": "Caller", "sub": "asks for a request"},
            {"id": "helper", "title": "Retry helper", "sub": "waits, then tries again"},
        ], "chain": True},
        {"label": "Remote service", "nodes": [
            {"id": "api", "title": "API endpoint", "sub": "may answer 503"},
        ]},
    ],
    "links": [
        {"from": "helper", "to": "api", "label": "request", "sub": "HTTPS"},
        {"from": "api", "to": "helper", "label": "result"},
    ],
}

FLOW = {
    "kind": "flow",
    "eyebrow": "Flow · planned",
    "title": "One request, start to finish",
    "description": "A request is sent; on failure it is retried or reported.",
    "caption": "Retries stop after five tries.",
    "steps": [
        {"title": "Send the request", "sub": "first try, no wait"},
        {"title": "It fails", "sub": "timeout or 5xx answer"},
    ],
    "branches": [
        {"from_step": 2, "title": "Retry", "sub": "up to 5 tries", "tone": "retry", "returns_to": 1},
        {"from_step": 2, "title": "Give up", "sub": "report the error", "tone": "stop"},
    ],
}

PROBE = "</text><script>x</script>\"'&"


def probe(limit=None):
    return PROBE if limit is None else PROBE[:limit]


def zones(**changes):
    diagram = copy.deepcopy(ZONES)
    diagram.update(changes)
    return diagram


def flow(**changes):
    diagram = copy.deepcopy(FLOW)
    diagram.update(changes)
    return diagram


def node(node_id, title="Node", sub="sub line"):
    return {"id": node_id, "title": title, "sub": sub}


def text_widths(boxes):
    return [box[3] for box in boxes if box[0] in ("text", "label")]


def fill(key):
    """The widest text that still passes: at most the limit in characters and the room in width."""
    font, text = diagrams.FONT[key], ""
    while len(text) < LIMITS[key]:
        fits = [char for char in "WNHAxri." if diagrams.text_units(text + char, font) <= diagrams.ROOM[key]]
        if not fits:
            break
        text += fits[0]
    return text


def worst_zones():
    """Three full zones, every label as wide as it may be, links both ways and elbows."""
    def full_node(zone, row):
        return {"id": f"{zone}{row}", "title": fill("node_title"), "sub": fill("node_sub")}

    def link(source, target):
        return {"from": source, "to": target, "label": fill("link_label"), "sub": fill("link_sub")}

    return {
        "kind": "zones",
        "eyebrow": "W" * LIMITS["eyebrow"],
        "title": "W" * LIMITS["title"],
        "description": "Worst case.",
        "caption": "Worst case.",
        "zones": [
            {"label": fill("zone_label"), "nodes": [full_node(zone, row) for row in range(1, 6)], "chain": True}
            for zone in "abc"
        ],
        "links": [
            link("a1", "b1"), link("b2", "a2"), link("a3", "b5"), link("b4", "a1"), link("b5", "a4"),
            link("b1", "c3"), link("c2", "b1"), link("b3", "c3"), link("c4", "b4"), link("c5", "b3"),
        ],
    }


def worst_flow(branches):
    return {
        "kind": "flow",
        "eyebrow": "W" * LIMITS["eyebrow"],
        "title": "W" * LIMITS["title"],
        "description": "Worst case.",
        "caption": "Worst case.",
        "steps": [{"title": fill("node_title"), "sub": fill("node_sub")} for _ in range(7)],
        "branches": [
            dict(branch, title=fill("branch_title"), sub=fill("branch_sub")) for branch in branches
        ],
    }


class DiagramValidationTests(unittest.TestCase):
    def rejects(self, value, *needles):
        with self.assertRaises(ValueError) as caught:
            validate_diagrams(value)
        message = str(caught.exception)
        self.assertTrue(message.startswith("Diagram"), message)
        for needle in needles:
            self.assertIn(needle, message)
        return message

    def test_valid_zones_and_flow_render(self):
        checked = validate_diagrams([ZONES, FLOW])
        self.assertEqual(len(checked), 2)
        sections = [render_diagram(diagram, index) for index, diagram in enumerate(checked, 1)]
        self.assertEqual(len(sections), 2)
        for index, (section, diagram) in enumerate(zip(sections, checked), 1):
            self.assertTrue(section.startswith(f'<section class="fig" aria-labelledby="dg-{index}-h">'))
            self.assertEqual(section.count('role="img"'), 1)
            self.assertEqual(len(re.findall(r"<title\b", section)), 1)
            descs = re.findall(r"<desc\b[^>]*>(.*?)</desc>", section, re.S)
            self.assertEqual([html.unescape(desc) for desc in descs], [diagram["description"]])
            self.assertIn(f'url(#dg-{index}-m-', section)
        self.assertIn('<circle class="num"', sections[1])
        self.assertIn('<text class="numt"', sections[1])
        self.assertIn('class="dg-w2"', sections[0])
        self.assertIn('class="dg-flow"', sections[1])
        for node_id in ("caller", "helper", "api"):
            self.assertNotIn(f'id="{node_id}"', sections[0])
        for dom_id in re.findall(r'\bid="([^"]*)"', "".join(sections)):
            self.assertTrue(dom_id.startswith("dg-"), dom_id)

    def test_diagram_count_and_kind(self):
        self.rejects([])
        self.rejects([ZONES] * 4)
        self.rejects([zones(kind="tree")])
        self.rejects(ZONES)
        self.rejects("diagrams")
        self.rejects([["not", "a", "dict"]])

    def test_zone_and_node_limits(self):
        self.rejects([zones(zones=[])])
        self.rejects([zones(zones=[{"label": f"Zone {n}", "nodes": [node(f"n{n}")]} for n in range(4)], links=[])])
        self.rejects([zones(zones=[{"label": "Empty", "nodes": []}], links=[])])
        six = [node(f"n{n}") for n in range(6)]
        self.rejects([zones(zones=[{"label": "Busy", "nodes": six}], links=[])])
        self.rejects([zones(zones=[{"label": "One", "nodes": [node("n1", title="x" * 25)]}], links=[])], "node_title")
        validate_diagrams([zones(zones=[{"label": "One", "nodes": [node("n1", title="x" * 24)]}], links=[])])
        # Wide characters count twice, so they cannot overflow the pill.
        self.rejects([zones(zones=[{"label": "One", "nodes": [node("n1", title="字" * 13)]}], links=[])], "node_title")
        validate_diagrams([zones(zones=[{"label": "One", "nodes": [node("n1", title="字" * 12)]}], links=[])])
        # 26, not 28: a 28-capital zone label ran past the viewBox in the third zone.
        self.rejects([zones(zones=[{"label": "x" * 27, "nodes": [node("n1")]}], links=[])], "zone_label")
        validate_diagrams([zones(zones=[{"label": "s" * 26, "nodes": [node("n1")]}], links=[])])  # narrow letters
        self.rejects([zones(eyebrow="x" * 41)], "eyebrow")
        self.rejects([zones(title="x" * 61)], "title")

    def test_links_name_existing_neighbouring_nodes(self):
        self.rejects([zones(links=[{"from": "helper", "to": "nowhere", "label": "request"}])], "nowhere")
        three = [
            {"label": "One", "nodes": [node("one")]},
            {"label": "Two", "nodes": [node("two")]},
            {"label": "Three", "nodes": [node("three")]},
        ]
        self.rejects([zones(zones=three, links=[{"from": "one", "to": "three", "label": "skip"}])])
        self.rejects([zones(links=[{"from": "caller", "to": "helper", "label": "call"}])], "chain")
        duplicate = copy.deepcopy(ZONES["zones"])
        duplicate[1]["nodes"].append(node("caller"))
        self.rejects([zones(zones=duplicate)], "caller")
        for bad in ("Caller", "a b", 'section-6"', "caller\n", "", "9lives", "x" * 25):
            bad_zones = copy.deepcopy(ZONES["zones"])
            bad_zones[0]["nodes"][0]["id"] = bad
            self.rejects([zones(zones=bad_zones, links=[])])
        self.rejects([zones(links=[{"from": "helper", "to": "api", "label": "x" * 15}])], "link_label")
        self.rejects([zones(links=[{"from": "helper", "to": "api", "label": "ok", "sub": "x" * 19}])], "link_sub")

    def test_flow_steps_and_branches(self):
        self.rejects([flow(steps=[{"title": "Only"}], branches=[])])
        self.rejects([flow(steps=[{"title": f"Step {n}"} for n in range(8)], branches=[])])
        three = [{"from_step": 1, "title": "B", "tone": "note"}] * 3
        self.rejects([flow(branches=three)])
        for bad in (0, 3, "2", True):
            self.rejects([flow(branches=[{"from_step": bad, "title": "B", "tone": "note"}])])
        steps = [{"title": f"Step {n}"} for n in range(1, 5)]
        for bad in (0, 3, 4, "1", True):
            self.rejects([flow(steps=steps, branches=[{"from_step": 3, "title": "B", "tone": "retry", "returns_to": bad}])])
        validate_diagrams([flow(steps=steps, branches=[{"from_step": 3, "title": "B", "tone": "retry", "returns_to": 2}])])
        self.rejects([flow(branches=[
            {"from_step": 2, "title": "Give up", "tone": "stop"},
            {"from_step": 2, "title": "Retry", "tone": "retry", "returns_to": 1},
        ])])
        self.rejects([flow(branches=[{"from_step": 2, "title": "B", "tone": "warn"}])])
        self.rejects([flow(branches=[{"from_step": 2, "title": "x" * 15, "tone": "note"}])], "branch_title")
        self.rejects([flow(branches=[{"from_step": 2, "title": "B", "sub": "x" * 19, "tone": "note"}])], "branch_sub")
        self.rejects([flow(steps=[{"title": "x" * 25}, {"title": "Two"}], branches=[])], "node_title")
        self.rejects([flow(steps=[{"title": "One", "sub": "x" * 31}, {"title": "Two"}], branches=[])], "node_sub")

    def test_required_text_fields(self):
        for key in ("eyebrow", "title", "description", "caption"):
            for base in (ZONES, FLOW):
                missing = copy.deepcopy(base)
                del missing[key]
                self.rejects([missing], key)
                blank = copy.deepcopy(base)
                blank[key] = "   "
                self.rejects([blank], key)
                wrong = copy.deepcopy(base)
                wrong[key] = 7
                self.rejects([wrong], key)

    def test_links_sharing_a_row_in_one_gap_are_explained(self):
        # Only a link and its reverse may share a row of one gap; a third link there is rejected.
        both_ways = [
            {"from": "caller", "to": "api", "label": "request"},
            {"from": "api", "to": "caller", "label": "response"},
            {"from": "caller", "to": "api", "label": "again"},
        ]
        self.rejects([zones(links=both_ways)], "links[2]", "same row", "links[0]", "different rows")
        two = copy.deepcopy(ZONES["zones"])
        two[1]["nodes"].append(node("api2"))
        same_pill = [
            {"from": "helper", "to": "api", "label": "request"},
            {"from": "helper", "to": "api2", "label": "again"},
        ]
        self.rejects([zones(zones=two, links=same_pill)], "links[1]", "same row")

    def test_link_and_its_reverse_share_a_row(self):
        one_each = [{"label": "Client", "nodes": [node("a")]}, {"label": "Server", "nodes": [node("b")]}]
        pair = [{"from": "a", "to": "b", "label": "request"}, {"from": "b", "to": "a", "label": "result"}]
        diagram = zones(zones=one_each, links=pair)
        validate_diagrams([diagram])
        self.assertIsNone(find_overlap(layout_boxes(diagram)))
        rows = [box for box in layout_boxes(diagram) if box[0] == "line" and box[4] == 0]
        self.assertEqual(len({box[2] for box in rows}), 2)  # two parallel lines, not one shared line
        self.assertEqual(render_diagram(diagram, 1).count("marker-end="), 2)
        # Pairs on neighbouring rows, every label and sub-label as wide as it may be, still fit.
        two_each = [{"label": "Client", "nodes": [node("a1"), node("a2")]},
                    {"label": "Server", "nodes": [node("b1"), node("b2")]}]
        full = {"label": fill("link_label"), "sub": fill("link_sub")}
        stacked = [dict(full, **{"from": source, "to": target})
                   for source, target in (("a1", "b1"), ("b1", "a1"), ("b2", "a2"), ("a2", "b2"))]
        diagram = zones(zones=two_each, links=stacked)
        validate_diagrams([diagram])
        self.assertIsNone(find_overlap(layout_boxes(diagram)))
        # The spec example (an elbow each way between different rows) still renders.
        validate_diagrams([ZONES])
        self.assertIn('class="dg-w2"', render_diagram(ZONES, 1))

    def test_pair_text_stays_with_its_own_line(self):
        # Mirrored: forward text above its line, backward text below its line, label nearest, sub-label outside.
        one_each = [{"label": "Client", "nodes": [node("a")]}, {"label": "Server", "nodes": [node("b")]}]
        pair = [{"from": "a", "to": "b", "label": "request", "sub": "HTTPS"},
                {"from": "b", "to": "a", "label": "result", "sub": "JSON"}]
        _, items = diagrams.layout(zones(zones=one_each, links=pair))
        text = {item["text"]: item["y"] for item in items if item["kind"] == "label" and item["cls"] in ("lb", "ls")}
        forward, backward = [item["points"][0][1] for item in items if item["kind"] == "arrow"]
        self.assertLess(forward, backward)
        self.assertLess(text["HTTPS"], text["request"])
        self.assertLess(text["request"], forward)
        self.assertLess(backward, text["result"])
        self.assertLess(text["result"], text["JSON"])

    def test_elbow_reaches_a_row_that_holds_a_pair(self):
        # The elbow must arrive clear of the pair's arrowheads instead of failing on coordinates.
        rows = [{"label": "Left", "nodes": [node("a1"), node("a2")]}, {"label": "Right", "nodes": [node("b1"), node("b2")]}]
        pair = [{"from": "a1", "to": "b1", "label": "request", "sub": "HTTPS"},
                {"from": "b1", "to": "a1", "label": "result", "sub": "JSON"}]
        for extra in ({"from": "b2", "to": "a1", "label": "late reply"}, {"from": "a2", "to": "b1", "label": "retry"}):
            with self.subTest(extra=extra):
                diagram = zones(zones=rows, links=pair + [extra])
                validate_diagrams([diagram])
                self.assertIsNone(find_overlap(layout_boxes(diagram)))
        flipped = [{"from": "a2", "to": "b2", "label": "request"}, {"from": "b2", "to": "a2", "label": "result"}]
        for extra in ({"from": "b1", "to": "a2", "label": "late reply"}, {"from": "a1", "to": "b2", "label": "retry"}):
            with self.subTest(extra=extra):
                validate_diagrams([zones(zones=rows, links=flipped + [extra])])

    def test_renderer_and_tests_share_one_diagrams_module(self):
        import render_report
        self.assertIs(render_report.diagrams, sys.modules["_validate_plan_diagrams"])
        self.assertIs(diagrams, render_report.diagrams)
        self.assertFalse(hasattr(diagrams, "CHAR_WIDTH"))

    def test_wide_glyphs_must_fit_their_shape(self):
        one = lambda **fields: [{"label": fields.get("label", "One"), "nodes": [node("n1", title=fields.get("title", "Node"))]},  # noqa: E731
                                {"label": "Two", "nodes": [node("n2")]}]
        link = lambda **fields: [dict({"from": "n1", "to": "n2", "label": "ok"}, **fields)]  # noqa: E731
        wide = "is too wide for its shape; shorten it"
        self.rejects([zones(zones=one(title="W" * LIMITS["node_title"]), links=[])], "zones[0].nodes[0].title", wide)
        self.rejects([zones(zones=one(label="W" * LIMITS["zone_label"]), links=[])], "zones[0].label", wide)
        self.rejects([zones(zones=one(), links=link(label="W" * LIMITS["link_label"]))], "links[0].label", wide)
        self.rejects([zones(zones=one(), links=link(sub="W" * LIMITS["link_sub"]))], "links[0].sub", wide)
        self.rejects([flow(branches=[{"from_step": 2, "title": "W" * LIMITS["branch_title"], "tone": "note"}])],
                     "branches[0].title", wide)
        self.rejects([flow(steps=[{"title": "M" * LIMITS["node_title"]}, {"title": "Two"}], branches=[])],
                     "steps[0].title", wide)
        # Realistic capitals and mixed case at the limits still pass.
        for title in ("PAYMENT SERVICE ADAPTERS", "Payment service adapters", "Remove unused migrations"):
            self.assertEqual(len(title), LIMITS["node_title"])
            validate_diagrams([zones(zones=one(title=title), links=[])])
        for label in ("PAYMENT SERVICE ADAPTERS", "Payments and billing tools"):
            validate_diagrams([zones(zones=one(label=label), links=[])])
        self.assertEqual(len("Payments and billing tools"), LIMITS["zone_label"])
        validate_diagrams([zones(zones=one(), links=link(label="returns result", sub="after a short wait"))])
        validate_diagrams([flow(branches=[{"from_step": 2, "title": "Retry the call", "sub": "waits, then tries",
                                           "tone": "retry"}])])

    def test_symbols_and_emoji_count_wide(self):
        # Chromium draws these at 0.84-1.25 em; a joiner and a variation selector draw nothing.
        for symbol in ("\u2714", "\u26a0", "\u2764", "\u2605", "\u2705", "\U0001f680"):
            self.assertGreaterEqual(diagrams.text_units(symbol, "t"), 1.25 * 13, symbol)
        self.assertEqual(diagrams.text_units("\u2764\ufe0f", "t"), diagrams.text_units("\u2764", "t"))
        self.assertEqual(diagrams.text_units("\u200d", "t"), 0)
        self.rejects([zones(zones=[{"label": "One", "nodes": [node("n1", title="\u2705" * 12)]}], links=[])],
                     "too wide")

    def test_tone_must_be_text(self):
        for tone in (["retry"], {"retry": 1}, None, 3):
            self.rejects([flow(branches=[{"from_step": 2, "title": "B", "tone": tone}])], "tone")

    def test_overlapping_returns_are_explained(self):
        steps = [{"title": f"Step {n}"} for n in range(1, 6)]
        branches = [
            {"from_step": 3, "title": "Retry", "tone": "retry", "returns_to": 1},
            {"from_step": 5, "title": "Again", "tone": "retry", "returns_to": 2},
        ]
        self.rejects([flow(steps=steps, branches=branches)], "branches[1].returns_to", "branches[0]")
        apart = [dict(branches[0], from_step=2), dict(branches[1], from_step=5, returns_to=3)]
        validate_diagrams([flow(steps=steps, branches=apart)])

    def test_overlap_backstop_rejects_real_diagram(self):
        # Two elbows reach one pill from the same side; only the layout check sees it.
        three = [
            {"label": "Left", "nodes": [node("a1"), node("a2"), node("a3")]},
            {"label": "Right", "nodes": [node("b1"), node("b2"), node("b3")]},
        ]
        links = [{"from": "a1", "to": "b3", "label": "one"}, {"from": "a2", "to": "b3", "label": "two"}]
        self.rejects([zones(zones=three, links=links)], "overlaps")


class DiagramRenderTests(unittest.TestCase):
    def test_diagram_text_is_escaped(self):
        zone = zones(
            eyebrow=probe(), title=probe(), description=probe(), caption=probe(),
            zones=[
                {"label": probe(LIMITS["zone_label"]), "nodes": [
                    {"id": "one", "title": probe(LIMITS["node_title"]), "sub": probe(LIMITS["node_sub"])},
                ]},
                {"label": probe(LIMITS["zone_label"]), "nodes": [
                    {"id": "two", "title": probe(LIMITS["node_title"]), "sub": probe(LIMITS["node_sub"])},
                ]},
            ],
            links=[{"from": "one", "to": "two", "label": probe(LIMITS["link_label"]), "sub": probe(LIMITS["link_sub"])}],
        )
        steps = flow(
            eyebrow=probe(), title=probe(), description=probe(), caption=probe(),
            steps=[{"title": probe(LIMITS["node_title"]), "sub": probe(LIMITS["node_sub"])}] * 2,
            branches=[{"from_step": 2, "title": probe(LIMITS["branch_title"]), "sub": probe(LIMITS["branch_sub"]),
                       "tone": "note"}],
        )
        output = "".join(render_diagram(d, i) for i, d in enumerate(validate_diagrams([zone, steps]), 1))
        self.assertNotIn("<script", output)
        self.assertIn("&lt;/text&gt;", output)
        self.assertIn("&quot;", output)
        for value in re.findall(r'=\s*"([^"]*)"', output):
            self.assertNotIn("<", value)
            self.assertNotIn("text&gt;", value)
            self.assertNotIn("script", value)

    def test_limits_fit_shapes(self):
        number_area = STEP_W - diagrams.STEP_TEXT_W
        holders = {
            "node_title": min(ZONE_W, STEP_W - number_area),
            "node_sub": min(ZONE_W, STEP_W - number_area),
            "zone_label": ZONE_W,
            "link_label": GAP,
            "link_sub": GAP,
            "branch_title": BRANCH_W,
            "branch_sub": BRANCH_W,
        }
        for key, width in holders.items():
            font = "s" if key.endswith("_sub") else "t"
            self.assertEqual(diagrams.FONT[key], font)
            # Average text at the limit fits the room, and the room plus padding fits the shape.
            self.assertLessEqual(LIMITS[key] * AVERAGE_WIDTH[font], diagrams.ROOM[key], key)
            self.assertLessEqual(diagrams.ROOM[key] + 2 * PAD, width, key)

    def assert_clean(self, diagram, width):
        validate_diagrams([diagram])
        boxes = layout_boxes(diagram)
        self.assertEqual(boxes[0][0], "view")
        self.assertEqual(boxes[0][1:4], (0, 0, width))
        self.assertIsNone(find_overlap(boxes))
        view = " ".join(f"{value:g}" for value in boxes[0][1:])
        self.assertIn(f'viewBox="{view}"', render_diagram(diagram, 1))
        return boxes

    def assert_full(self, boxes, keys):
        """The worst case really fills each field's room, to within one narrow letter."""
        widths = text_widths(boxes)
        for key in keys:
            room = diagrams.ROOM[key]
            self.assertTrue(any(room - 4 <= width <= room for width in widths), key)

    def test_layout_fits_and_never_overlaps(self):
        boxes = self.assert_clean(worst_zones(), 936)
        self.assert_full(boxes, ("node_title", "node_sub", "zone_label", "link_label", "link_sub"))
        self.assertGreaterEqual(sum(1 for box in boxes if box[0] == "line" and box[3] == 0), 6)  # elbow lanes

        both = worst_flow([
            {"from_step": 4, "tone": "retry", "returns_to": 1},
            {"from_step": 4, "tone": "stop"},
        ])
        apart = worst_flow([
            {"from_step": 2, "tone": "note"},
            {"from_step": 6, "tone": "retry", "returns_to": 1},
        ])
        for diagram in (both, apart):
            boxes = self.assert_clean(diagram, 608)
            self.assert_full(boxes, ("node_title", "node_sub", "branch_title", "branch_sub"))

        for count in (1, 2):
            small = zones(zones=ZONES["zones"][:count], links=ZONES["links"] if count == 2 else [])
            self.assert_clean(small, {1: 232, 2: 584}[count])

    def test_overlap_check_catches_collisions(self):
        view = ("view", 0, 0, 100, 100)
        self.assertIsNotNone(find_overlap([view, ("pill", 0, 0, 50, 50), ("pill", 40, 40, 50, 50)]))
        self.assertIsNotNone(find_overlap([view, ("pill", 0, 0, 50, 50), ("text", 40, 10, 20, 10)]))
        self.assertIsNotNone(find_overlap([view, ("label", 0, 0, 50, 10), ("line", 10, 5, 30, 0)]))
        self.assertIsNotNone(find_overlap([view, ("line", 0, 5, 50, 0), ("line", 20, 6, 50, 0)]))
        self.assertIsNotNone(find_overlap([view, ("pill", 60, 60, 50, 50)]))
        self.assertIsNone(find_overlap([view, ("line", 0, 50, 100, 0), ("line", 50, 0, 0, 100)]))


if __name__ == "__main__":
    unittest.main()
