#!/usr/bin/env python3
"""orientation_pack: the knowledge-plane context bundle folded into a
dispatched work order's prompt (WO-0015; ADR-0032 dispatch plane).

Named orientation_pack.py, not orientation.py: this repo's root already
carries an unrelated orientation.py — ADR-0021's CLI adapter over
protocol.py's next_stage, the idea-to-prod pipeline's "which stage is
next" tool, with its own tests/test_orientation.py and
tests/fixtures/orientation/. The factory shares this repo's root
namespace with that pipeline, so the two "orientation" concepts needed
different names; see docs/features/software-factory/breakdown.md's
WO-0015 Notes for the citation.

Same seam discipline as assembler.py: every function takes `root` (a repo
tree, not an injected reader object) and reads real files under it, tested
against tempfile fixture trees. And the same prompt-injection boundary
(ADR-0032): orientation_pack takes root, a work order id, and the
repo-controlled breakdown ROW — never an issue body or GitHub event, so
there is no channel for attacker-controlled text to reach the pack.
"""
import ast
import re
from pathlib import Path

import gates

# Bare filenames a breakdown row names in prose ("assembler.yml + guards",
# "budget_guard.py + handoff.py + cost ledger") — a best-effort scan of the
# row text, not a path resolver; _resolve_file below turns a match into a
# real repo path.
FILENAME_TOKEN = re.compile(r"\b[\w-]+\.(?:py|yml|yaml|md|json)\b")


def cited_adrs(row):
    """ADR numbers the row cites, in citation order, deduplicated. Same
    grammar gates.ADR_TOKEN reads elsewhere in the knowledge plane (detector
    C's link integrity, detector D's blueprint drift) — a row that names no
    ADR cites none; that is a fact about the row, not a gap here."""
    return list(dict.fromkeys(gates.ADR_TOKEN.findall(row)))


def adr_path(root, number):
    """The docs/adr file for a 4-digit ADR number, or None. Same glob
    gates.check_blueprint_drift uses to walk the blueprint plane."""
    adr_dir = Path(root) / "docs" / "adr"
    if not adr_dir.is_dir():
        return None
    matches = sorted(adr_dir.glob(f"{number}-*.md"))
    return matches[0] if matches else None


def _resolve_file(root, name):
    """The first repo file matching a bare filename a row names, or None.
    Rows name files without a path ("assembler.yml"), so this is a search,
    not a lookup; sorted() keeps it deterministic when a name is not
    unique."""
    matches = sorted(Path(root).rglob(name))
    return matches[0] if matches else None


def _python_structure(path):
    """(docstring headline, [top-level def/class names]) for a .py file,
    read via ast so nothing executes."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    doc = ast.get_docstring(tree)
    headline = doc.strip().splitlines()[0] if doc else "(no module docstring)"
    names = [node.name for node in tree.body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                   ast.ClassDef))]
    return headline, names


def codegraph_summary(root, row):
    """A lightweight structural map of the repo files a breakdown row names:
    for a .py file, its module docstring headline and top-level def/class
    names (via ast — nothing executes); for anything else, just that it
    exists in the tree. Pure over `root` + `row`, stdlib-only, no dependency
    graph — the minimum that lets a dispatched agent orient before reading
    blind."""
    root = Path(root)
    lines = []
    for name in dict.fromkeys(FILENAME_TOKEN.findall(row)):
        path = _resolve_file(root, name)
        if path is None:
            continue
        rel = path.relative_to(root).as_posix()
        if path.suffix == ".py":
            headline, names = _python_structure(path)
            listing = ", ".join(names) if names else "(no top-level defs)"
            lines.append(f"- {rel} — {headline}\n  {listing}")
        else:
            lines.append(f"- {rel}")
    if not lines:
        return "(no repo files named on this row were found)"
    return "\n".join(lines)


def orientation_pack(root, wo, row):
    """The orientation pack for a dispatched work order: CONTEXT.md, the
    ADRs the row cites, and a codegraph summary of the files it names — the
    knowledge-plane context WO-0015 promises the assembler prompt. Pure over
    `root` + `row`: every byte is a repo file reached from the
    repo-controlled breakdown row, never an issue body (ADR-0032's
    prompt-injection boundary — this function does not even accept one)."""
    root = Path(root)
    context_path = root / "CONTEXT.md"
    context = (context_path.read_text(encoding="utf-8")
               if context_path.is_file() else "(no CONTEXT.md at repo root)")
    parts = [f"## Orientation pack: {wo}\n", "### CONTEXT.md\n", context]
    for number in cited_adrs(row):
        path = adr_path(root, number)
        if path is None:
            continue
        parts.append(f"### ADR-{number}: {path.stem}\n")
        parts.append(path.read_text(encoding="utf-8"))
    parts.append("### Codegraph summary\n")
    parts.append(codegraph_summary(root, row))
    return "\n".join(parts)
