#!/usr/bin/env python3
"""adr-status: every ADR in a repo's docs/adr/ with its status and standing, as JSON.

Facts only, per ADR-0062: the review skill's ADR compliance pass (issue
#684) checks a diff against the ADRs this tool calls live, and never
reads a status line itself. The status grammar has one owner,
gates.ADR_STATUS (detector D): only full supersession retires a
decision, so "superseded in part by" and "amended by" stay live.

Standing, per ADR:
  active        accepted, or amended by a later ADR
  provisional   recorded without live confirmation — live, held softer
  partial       superseded in part — live outside the superseded part
  retired       superseded by a later ADR — not checked
  unrecognized  no status, or one outside the grammar (a repo with its
                own convention); the raw text is reported for the
                reviewer to read

A repo with no docs/adr/ has no ADRs to check: an empty list, not an
error. Same seam discipline as board.py: functions take `root` and read
real files under it, tested against tempfile fixture trees.
"""
import json
import re
import sys
from pathlib import Path

import cli
import gates
from protocol import read_frontmatter

# An ADR file is named by its number: this repo's `0062-slug.md`, or the
# `ADR-007-slug.md` form other repos use. README.md and TEMPLATE.md carry
# no number and are skipped by the same test.
ADR_FILE = re.compile(r"^(?:ADR-?)?(?P<num>\d+)\b", re.IGNORECASE)


def standing(text):
    """The standing of one raw status text under gates.ADR_STATUS."""
    match = gates.ADR_STATUS.match(text or "")
    if not match:
        return "unrecognized"
    if match.group("retired"):
        return "retired"
    head = match.group(1)
    if head == "provisional":
        return "provisional"
    if head.startswith("superseded in part"):
        return "partial"
    return "active"


def _status(path):
    """The raw status text: the `- Status:` line (gates' own reader), else
    a frontmatter `status:` field, else None."""
    _, text = gates._adr_status(path)  # gates owns the Status-line read
    if text is None:
        text = ((read_frontmatter(path) or {}).get("status") or "").strip()
    return text or None


def _title(path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _entry(root, path, number):
    text = _status(path)
    match = gates.ADR_STATUS.match(text or "")
    by = match.group("by") if match and match.group("retired") else None
    return {"id": f"ADR-{number}",
            "file": path.relative_to(root).as_posix(),
            "title": _title(path),
            "status": text,
            "standing": standing(text),
            "superseded_by": f"ADR-{by}" if by else None}


def gather(root):
    """(model, problems). The one problem is a root that is not a
    directory; everything else is a fact inside the model."""
    root = Path(root)
    if not root.is_dir():
        return None, [f"adr-status: {root} is not a directory"]
    adr_dir = root / "docs" / "adr"
    found = []
    if adr_dir.is_dir():
        for path in sorted(adr_dir.glob("*.md")):
            match = ADR_FILE.match(path.name)
            if match:
                found.append((int(match.group("num")), path,
                              match.group("num")))
    return {"adrs": [_entry(root, path, number)
                     for _, path, number in sorted(found)]}, []


def main(argv):
    """`python3 adr_status.py [root]` — root defaults to the working
    directory, the way the review skill invokes it from a target repo."""
    root = argv[0] if argv else "."
    model, problems = gather(root)
    if problems:
        return cli.report("adr-status", problems)
    print(json.dumps(model, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
