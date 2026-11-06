#!/usr/bin/env python3
"""assembly_line: the factory model for one repo — every run exactly once
(active, completed or attention), its ladder, its dated station history
and its work orders — and the self-contained page that draws it
(feature:assembly-line).

Facts only, per ADR-0062: placement and attention come from board.gather
verbatim, stage rules from protocol, breakdown rows from
knowledge_plane. The page derives nothing; it draws this model.
"""
import sys
from pathlib import Path

import board
import cli
from knowledge_plane import breakdown_rows, run_dirs
from protocol import (MAINTENANCE_STAGE_ARTIFACTS, RUN_ARTIFACTS,
                      STAGE_ARTIFACTS, breakdown_path)

COMPLETED = "completed"
# Every station on the floor, in belt order: the maintenance ladder's
# entry (capture) beside the feature ladder, then the warehouse.
STATIONS = ([MAINTENANCE_STAGE_ARTIFACTS[0][0]]
            + [stage for stage, _ in STAGE_ARTIFACTS] + [COMPLETED])
IMPLEMENT = "implement"


def _row_title(row):
    """A breakdown row's title: its WO title when it carries one, else
    the line's own text after the box, bold marks dropped, up to the
    em-dash metadata clause."""
    if row["title"]:
        return row["title"]
    text = row["text"].split("]", 1)[1].replace("**", "")
    return text.split(" — ")[0].strip()


def _work_orders(run_dir, ladder):
    """Every breakdown row (title, done) for a run at or past Implement;
    [] before it. Progress is today's: checkbox ticks carry no date."""
    reached = [row["stage"] for row in ladder
               if row["state"] in ("done", "current")]
    if IMPLEMENT not in reached:
        return []
    path = breakdown_path(run_dir)
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [{"title": _row_title(row), "done": row["done"]}
            for row in breakdown_rows(lines)]


def _is_run(run_dir):
    return any((run_dir / name).is_file() for name in RUN_ARTIFACTS)


def _attention(root, run_dir, reason):
    ref, kind, slug = board.run_identity(root, run_dir)
    return {"ref": ref, "kind": kind, "slug": slug,
            "dir": str(run_dir.relative_to(root)), "status": "attention",
            "station": None, "ladder": [], "reason": reason,
            "history": [], "work_orders": []}


def _placed(root, run_dir, entry, status):
    current = next((row["stage"] for row in entry["ladder"]
                    if row["state"] == "current"), None)
    return {"ref": entry["ref"], "kind": entry["kind"],
            "slug": entry["slug"], "dir": entry["dir"], "status": status,
            "station": current if status == "active" else COMPLETED,
            "ladder": entry["ladder"], "reason": None, "history": [],
            "work_orders": _work_orders(run_dir, entry["ladder"])}


def gather(root, clock=None):
    """(model, problems). board.gather's one repo-level problem — no
    docs/ tree — is this tool's too: (None, [it]). Otherwise every run
    directory holding a run artifact is in `runs` exactly once: active
    as board places it, attention with board's reason, and every other
    run is complete (orientation's word) and sits in Completed."""
    root = Path(root)
    placed, problems = board.gather(root, clock)
    if problems:
        return None, problems
    active = {entry["dir"]: entry for entry in placed["runs"]}
    attention = {entry["dir"]: entry["reason"]
                 for entry in placed["attention"]}
    runs = []
    for run_dir in run_dirs(root):
        rel = str(run_dir.relative_to(root))
        if rel in active:
            runs.append(_placed(root, run_dir, active[rel], "active"))
            continue
        if rel in attention:
            runs.append(_attention(root, run_dir, attention[rel]))
            continue
        try:
            if not _is_run(run_dir):
                continue
            entry = board.run_entry(root, run_dir)
            runs.append(_placed(root, run_dir, entry, COMPLETED))
        except (OSError, ValueError) as err:
            runs.append(_attention(root, run_dir, board.reason(err)))
    model = {"generated": placed["generated"], "repo": placed["repo"],
             "stations": STATIONS, "runs": runs}
    return model, []


def main(argv):
    """`python3 assembly_line.py [root]`."""
    root = argv[0] if argv else "."
    model, problems = gather(root)
    if problems:
        return cli.report("assembly_line", problems)
    return 0
