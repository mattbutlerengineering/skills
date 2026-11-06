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
from datetime import date
from pathlib import Path

import board
import cli
from knowledge_plane import breakdown_rows, run_dirs
from protocol import (MAINTENANCE_STAGE_ARTIFACTS, RUN_ARTIFACTS,
                      STAGE_ARTIFACTS, breakdown_path, is_maintenance_run,
                      read_frontmatter)

COMPLETED = "completed"
# Every station on the floor, in belt order: the maintenance ladder's
# entry (capture) beside the feature ladder, then the warehouse.
STATIONS = ([MAINTENANCE_STAGE_ARTIFACTS[0][0]]
            + [stage for stage, _ in STAGE_ARTIFACTS] + [COMPLETED])
IMPLEMENT = "implement"
# Implement writes no artifact of its own; the run leaves it when
# Verify's artifact lands (PRD-0021 §Success criteria, Replay).
LEAVES_IMPLEMENT = dict(STAGE_ARTIFACTS)["verify"]


def _artifact_day(path):
    """The artifact's frontmatter `date:` as an ISO day, or None when
    the file is absent or carries no readable date."""
    if not path.is_file():
        return None
    value = (read_frontmatter(path) or {}).get("date") or ""
    try:
        return date.fromisoformat(value.strip()[:10]).isoformat()
    except ValueError:
        return None


def _history(run_dir, ladder, status, fallback_day):
    """Station arrivals in belt order. The run enters its first station
    on that station's artifact date and reaches each later station on
    the date of the artifact that completed the station before it.
    Skipped and done-ahead stages are never visited. A missing date
    takes the previous arrival's day; a day earlier than the previous
    arrival is raised to it; a run with no dates at all enters on
    fallback_day. Every such arrival, and every arrival sharing its day
    with another of the same run, is `inferred`."""
    table = dict(MAINTENANCE_STAGE_ARTIFACTS if is_maintenance_run(run_dir)
                 else STAGE_ARTIFACTS)
    visited = []
    for row in ladder:
        if row["state"] in ("done", "current"):
            visited.append(row["stage"])
        if row["state"] == "current":
            break
    if status == COMPLETED:
        visited.append(COMPLETED)
    if not visited:
        return []
    first = _artifact_day(run_dir / table[visited[0]])
    hops = [[visited[0], first, False]]
    if first is None:
        days = [day for day in (_artifact_day(run_dir / name)
                                for name in RUN_ARTIFACTS) if day]
        hops[0][1:] = [min(days) if days else fallback_day, True]
    for before, station in zip(visited, visited[1:]):
        name = LEAVES_IMPLEMENT if before == IMPLEMENT else table[before]
        day = _artifact_day(run_dir / name)
        previous = hops[-1][1]
        if day is None or day < previous:
            hops.append([station, previous, True])
        else:
            hops.append([station, day, False])
    counts = {}
    for _, day, _ in hops:
        counts[day] = counts.get(day, 0) + 1
    return [{"station": station, "day": day,
             "inferred": inferred or counts[day] > 1}
            for station, day, inferred in hops]


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


def _placed(root, run_dir, entry, status, fallback_day):
    current = next((row["stage"] for row in entry["ladder"]
                    if row["state"] == "current"), None)
    return {"ref": entry["ref"], "kind": entry["kind"],
            "slug": entry["slug"], "dir": entry["dir"], "status": status,
            "station": current if status == "active" else COMPLETED,
            "ladder": entry["ladder"], "reason": None,
            "history": _history(run_dir, entry["ladder"], status,
                                fallback_day),
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
    today = placed["generated"][:10]
    runs = []
    for run_dir in run_dirs(root):
        rel = str(run_dir.relative_to(root))
        try:
            if rel in attention:
                runs.append(_attention(root, run_dir, attention[rel]))
            elif rel in active:
                runs.append(_placed(root, run_dir, active[rel], "active",
                                    today))
            elif _is_run(run_dir):
                entry = board.run_entry(root, run_dir)
                runs.append(_placed(root, run_dir, entry, COMPLETED, today))
        except (OSError, ValueError) as err:
            runs.append(_attention(root, run_dir, board.reason(err)))
    days = [hop["day"] for run in runs for hop in run["history"]]
    last_day = max(days + [today])
    model = {"generated": placed["generated"], "repo": placed["repo"],
             "stations": STATIONS, "runs": runs,
             "timeline": {"first_day": min(days or [last_day]),
                          "last_day": last_day}}
    return model, []


def main(argv):
    """`python3 assembly_line.py [root]`."""
    root = argv[0] if argv else "."
    model, problems = gather(root)
    if problems:
        return cli.report("assembly_line", problems)
    return 0
