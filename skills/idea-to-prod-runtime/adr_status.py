#!/usr/bin/env python3
"""adr-status: every ADR in a repo's docs/adr/ with its status and standing, as JSON.

Facts only, per ADR-0062: the review skill's ADR compliance pass (issue
#684) checks a diff against the ADRs this tool calls live, and never
reads a status line itself. Which files are ADRs, their status and their
standing have one owner, knowledge_plane's ADR record (issue #747) — the
same reading gates detectors C, D and K use: only full supersession
retires a decision, so "superseded in part by" and "amended by" stay live.

Standing, per ADR (knowledge_plane.standing):
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
import sys
from pathlib import Path

import cli
from knowledge_plane import adr_records


def _entry(root, record):
    path, by = record["path"], record["superseded_by"]
    return {"id": f"ADR-{record['number']}",
            "file": path.relative_to(root).as_posix(),
            "title": record["title"],
            "status": record["status"],
            "standing": record["standing"],
            "superseded_by": f"ADR-{by}" if by else None}


def gather(root):
    """(model, problems). The problems are a root that is not a
    directory and an ADR that cannot be read (knowledge_plane.read_adrs,
    issue #855); everything else is a fact inside the model."""
    root = Path(root)
    if not root.is_dir():
        return None, [f"adr-status: {root} is not a directory"]
    records, problems = adr_records(root)
    if problems:
        return None, [f"adr-status: {problem}" for problem in problems]
    records = sorted(records, key=lambda record: (int(record["number"]),
                                                  record["path"]))
    return {"adrs": [_entry(root, record) for record in records]}, []


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
