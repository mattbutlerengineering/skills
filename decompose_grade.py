#!/usr/bin/env python3
"""decompose-grade: score a Decompose breakdown against its architecture.

Step 5 of the Decompose learning loop (the run is
docs/features/decompose-eval-suite/; ADR-0114). A pure, offline scorer for
one produced breakdown.md: given the breakdown, the architecture it was
drafted from and optionally the PRD, `grade` returns a score in [0, 1], four
part fractions and one exact feedback line per defect, the text an optimizer
needs to see why a candidate failed.

OFFLINE AND NOT A GATE. No network, no model, no git, no write. It is
calibrated to breakdowns drafted from a fixture (component names keep the
architecture's spelling), and is not a retroactive audit of shipped runs.
The harness suite under plugin-evals/decompose/ is a separate scorer; the
two are never compared here (ADR-0114).
"""
import re

from decompose_signals import item_keys
from knowledge_plane import breakdown_rows

LABEL = "decompose-grade"
PARTS = ("coverage", "dependencies", "accept", "sizing")
NO_ITEMS = "no-items: breakdown holds no checkbox work items"
NO_COMPONENTS = "holds no components"
_SECTION = re.compile(r"^##\s+(.*?)\s*$")
_HEADING = re.compile(r"^###\s+(.*?)\s*$")
_PAREN = re.compile(r"\s*\([^)]*\)\s*$")
# A component name shorter than this is not graded: a deliberate floor
# against substring hits.
MIN_NAME = 4
# An item naming more distinct components than this is more than one
# sitting (measured in architecture.md: 1 of 205 real rows exceeds 3).
MAX_SPAN = 3
_BLOCKED_BY = re.compile(r"blocked by:[ \t]*([^(\n]*)", re.IGNORECASE)
_NO_EDGE = {"", "—", "-", "none"}
_ACCEPT = re.compile(r"^\s*[-*+]\s+accept:[ \t]*(.*)$", re.IGNORECASE)
_BULLET = re.compile(r"^\s*[-*+]\s")
_SLOT = re.compile(r"<[^<>\n]+>")
_CODE = re.compile(r"`([^`\n]*)`")
_DIGITS = re.compile(r"\b\d+\b")
_WORD = re.compile(r"\w+")
MIN_WORDS = 3
# Phrases that say an Accept line is done without saying how to check it.
# The grader's own definition of vague, not read from the skill text; a
# phrase outside the list passes (a stated limit, architecture.md).
HEDGES = (
    "works correctly", "work correctly", "works as expected",
    "work as expected", "works properly", "works fine", "behaves correctly",
    "handles errors appropriately", "handles errors gracefully",
    "handles edge cases", "is complete", "is done", "is implemented",
    "as appropriate", "as needed",
)
_HEDGE = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(h) for h in HEDGES) + r")(?!\w)",
    re.IGNORECASE)


def read_items(breakdown_text):
    """[{key, block}] for every checkbox row, in order: the key is
    decompose_signals' (one owner of the key grammar), the block is the
    row plus its sub-bullets (knowledge_plane's one row walk)."""
    lines = breakdown_text.splitlines()
    return [{"key": key, "block": row["block"]}
            for key, row in zip(item_keys(lines), breakdown_rows(lines))]


def _section_headings(architecture_text, section):
    """The `###` headings under the `## <section>...` heading, in order."""
    found, inside = [], False
    for line in architecture_text.splitlines():
        heading = _SECTION.match(line)
        if heading:
            inside = heading.group(1).lower().startswith(section)
        elif inside and _HEADING.match(line):
            found.append(_HEADING.match(line).group(1))
    return found


def read_components(architecture_text):
    """The component names: `###` headings under `## Components`, a
    trailing parenthetical removed. ValueError when there are none."""
    names = [_PAREN.sub("", h) for h in
             _section_headings(architecture_text, "components")]
    if not names:
        raise ValueError(NO_COMPONENTS)
    return names


def _names(name, block):
    """True when `name` appears in `block` as a whole case-insensitive
    phrase."""
    return re.search(rf"(?<!\w){re.escape(name)}(?!\w)", block,
                     re.IGNORECASE) is not None


def _graded(components):
    return [name for name in components if len(name) >= MIN_NAME]


def check_coverage(items, components):
    """(fraction, feedback): the graded components some row block names."""
    graded = _graded(components)
    missed = [name for name in graded
              if not any(_names(name, i["block"]) for i in items)]
    feedback = [f'coverage-miss: component "{name}" is named by no item'
                for name in missed]
    return _fraction(len(graded) - len(missed), len(graded)), feedback


def _fraction(good, total):
    """good over total; 1.0 when nothing was there to grade."""
    return good / total if total else 1.0


def blockers(block):
    """The elements of a block's Blocked by clause (sub-bullet or inline),
    split on `;` and `,`; an empty, dash or `none` element is no edge."""
    clause = _BLOCKED_BY.search(block)
    if clause is None:
        return []
    parts = (p.strip(" .`*") for p in re.split(r"[;,]", clause.group(1)))
    return [p for p in parts if p.lower() not in _NO_EDGE]


def _resolves(element, key):
    return re.match(rf"{re.escape(key)}(?!\w)", element) is not None


def check_dependencies(items):
    """(fraction, feedback): resolved edges over edges. An element
    resolves when it starts with another item's key."""
    edges = [(i["key"], e) for i in items for e in blockers(i["block"])]
    dangling = [(key, e) for key, e in edges
                if not any(_resolves(e, other["key"]) for other in items
                           if other["key"] != key)]
    feedback = [f'dangling-blocked-by: {key} is blocked by "{e}",'
                " which names no item" for key, e in dangling]
    return _fraction(len(edges) - len(dangling), len(edges)), feedback


def build_anchors(architecture_text, prd_text=""):
    """The fixture tokens an Accept line can be anchored to: component and
    interface headings (lowercase), the fixture text a backticked span must
    appear in, and the digit runs the fixture holds."""
    text = f"{architecture_text}\n{prd_text}"
    headings = [_PAREN.sub("", h) for section in ("components", "interfaces")
                for h in _section_headings(architecture_text, section)]
    return {"headings": [h.lower() for h in headings], "text": text,
            "digits": frozenset(_DIGITS.findall(text))}


def accept_text(block):
    """The text of the block's `Accept:` sub-bullet, continuation lines
    included, or None when it has none."""
    found = None
    for line in block.splitlines()[1:]:
        match = _ACCEPT.match(line)
        if match:
            found = [match.group(1)]
        elif found is not None and not _BULLET.match(line):
            found.append(line.strip())
        elif found is not None:
            break
    return " ".join(found).strip() if found is not None else None


def _drop_anchors(text, anchors):
    """(text with every anchor removed, anchors found)."""
    found = 0

    def backticked(match):
        nonlocal found
        hit = match.group(1).strip() != "" and match.group(1) in anchors["text"]
        found += hit
        return " " if hit else match.group(0)

    def digits(match):
        nonlocal found
        hit = match.group(0) in anchors["digits"]
        found += hit
        return " " if hit else match.group(0)

    text = _CODE.sub(backticked, text)
    for heading in anchors["headings"]:
        text, count = re.subn(rf"(?<!\w){re.escape(heading)}(?!\w)", " ",
                              text, flags=re.IGNORECASE)
        found += count
    return _DIGITS.sub(digits, text), found


def accept_reason(block, anchors):
    """Why the block's Accept line is untestable (empty, placeholder or
    unanchored), or None when it is checkable."""
    text = accept_text(block)
    if text is None or not _WORD.search(text):
        return "empty"
    if _SLOT.search(_CODE.sub("", text)):
        return "placeholder"
    rest, found = _drop_anchors(_HEDGE.sub(" ", text), anchors)
    if found == 0 or len(_WORD.findall(rest)) < MIN_WORDS:
        return "unanchored"
    return None


def check_accept(items, anchors):
    """(fraction, feedback): the items whose Accept line is checkable."""
    reasons = [(i["key"], accept_reason(i["block"], anchors)) for i in items]
    feedback = [f"untestable-accept: {key} has no checkable Accept line"
                f" ({reason})" for key, reason in reasons if reason]
    return _fraction(sum(1 for _, r in reasons if r is None),
                     len(items)), feedback


def check_sizing(items, components):
    """(fraction, feedback): the items naming at most MAX_SPAN of the graded
    components (the list the coverage check grades), sub-bullets included."""
    graded = _graded(components)
    spans = [(i["key"], sum(1 for name in graded if _names(name, i["block"])))
             for i in items]
    feedback = [f"mis-sized: {key} names {count} components"
                f" (limit {MAX_SPAN})"
                for key, count in spans if count > MAX_SPAN]
    return _fraction(sum(1 for _, c in spans if c <= MAX_SPAN),
                     len(items)), feedback


def combine(parts):
    """The score: the mean of the four part fractions, 3 places."""
    return round(sum(parts[name] for name in PARTS) / len(PARTS), 3)


def summary(record):
    """The one-line report of a grade record."""
    parts = ", ".join(f"{name} {record['parts'][name]:.3f}"
                      for name in PARTS)
    return f"{LABEL}: score {record['score']:.3f} ({parts})"


def grade(breakdown_text, architecture_text, prd_text=""):
    """{score, parts, feedback} for one breakdown. Deterministic; defects
    are data, not exceptions. ValueError("holds no components") when the
    architecture names none."""
    components = read_components(architecture_text)
    items = read_items(breakdown_text)
    if not items:
        return {"score": 0.0, "parts": {name: 0.0 for name in PARTS},
                "feedback": [NO_ITEMS]}
    parts = {name: 1.0 for name in PARTS}
    feedback = []
    for name, (fraction, lines) in (
            ("coverage", check_coverage(items, components)),
            ("dependencies", check_dependencies(items)),
            ("accept", check_accept(
                items, build_anchors(architecture_text, prd_text))),
            ("sizing", check_sizing(items, components))):
        parts[name] = fraction
        feedback.extend(lines)
    return {"score": combine(parts),
            "parts": {name: round(v, 3) for name, v in parts.items()},
            "feedback": feedback}
