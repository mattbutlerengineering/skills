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
    read_components(architecture_text)
    if not read_items(breakdown_text):
        return {"score": 0.0, "parts": {name: 0.0 for name in PARTS},
                "feedback": [NO_ITEMS]}
    parts = {name: 1.0 for name in PARTS}
    return {"score": combine(parts), "parts": parts, "feedback": []}
