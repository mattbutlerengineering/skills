#!/usr/bin/env python3
"""decompose-lessons: a voted, sourced lessons file derived from run outcomes.

Step 3 of the Decompose learning loop (issue #988; the run is
docs/features/decompose-lessons/, ADR-0113). Contrast pairs of a hit run
and a clean run of the same kind, read from decompose_signals' records,
collapse to lessons that live in docs/factory/decompose-lessons.jsonl
with an importance count: a new lesson starts at 2, a later treated run
votes it up or down by 1, and it is removed at 0.

DERIVED ONLY. No command takes lesson text from a person or a model, and
retro prose and band misses never reach a pair. `update` is the single
writer and the Owner runs it.

READ-ONLY AND LOCAL except `update`'s one whole-file write. git is reached
only through cli.runner, injected as `run`, and only with the read-only
verbs decompose_signals uses plus `log` and `merge-base`; the tool never
fetches.

NOT A GATE. An empty pair set and a refused verdict are data.
"""
import json
import os
import tempfile
from pathlib import Path

from cli import read_file

LABEL = "decompose-lessons"
LESSONS_PATH = "docs/factory/decompose-lessons.jsonl"
FIELDS = ("id", "importance", "text", "sources", "voted")


def _lesson(lid, text, sources, importance=2, voted=()):
    return {"id": lid, "importance": importance, "text": text,
            "sources": list(sources), "voted": list(voted)}


def _find(lessons, lid):
    return next((n for n, entry in enumerate(lessons)
                 if entry["id"] == lid), None)


def _refused(op, why):
    return f"{LABEL}: {op} refused: {why}"


def add(lessons, lid, text, sources):
    """(new list, problems): the lesson at importance 2. Refused, with the
    original list back, when it cites no source run or the id exists."""
    if not sources:
        return lessons, [_refused("add", f"{lid} cites no source run")]
    if _find(lessons, lid) is not None:
        return lessons, [_refused("add", f"{lid} already exists")]
    return [*lessons, _lesson(lid, text, sources)], []


def edit(lessons, lid, text, sources=None):
    """(new list, problems): the lesson's text changed, and its sources
    replaced when given; importance and voted are kept. Refused when the
    id is unknown or the edit would leave no source run."""
    at = _find(lessons, lid)
    if at is None:
        return lessons, [_refused("edit", f"no lesson {lid}")]
    kept = lessons[at]["sources"] if sources is None else list(sources)
    if not kept:
        return lessons, [_refused("edit", f"{lid} cites no source run")]
    changed = {**lessons[at], "text": text, "sources": kept}
    return [*lessons[:at], changed, *lessons[at + 1:]], []


def _vote(op, step, lessons, lid, voter):
    at = _find(lessons, lid)
    if at is None:
        return lessons, [_refused(op, f"no lesson {lid}")]
    importance = lessons[at]["importance"] + step
    if importance < 1:
        return [*lessons[:at], *lessons[at + 1:]], []
    voted = [*lessons[at]["voted"], voter]
    changed = {**lessons[at], "importance": importance, "voted": voted}
    return [*lessons[:at], changed, *lessons[at + 1:]], []


def upvote(lessons, lid, voter):
    """(new list, problems): importance + 1, `voter` recorded in voted."""
    return _vote("upvote", 1, lessons, lid, voter)


def downvote(lessons, lid, voter):
    """(new list, problems): importance - 1, `voter` recorded in voted; the
    lesson is removed when that would leave it below 1 (dropped at 0)."""
    return _vote("downvote", -1, lessons, lid, voter)


# The file: line 1 is {"seen": [...]}, every other line one lesson, sorted
# by id (ADR-0113). One validator serves both directions, so a file that
# loads is a file that dumps.

def _field_problem(entry):
    """The first reason one lesson object is malformed, or None."""
    for field in FIELDS:
        value = entry.get(field)
        text_ok = isinstance(value, str) and (field != "id" or value)
        list_ok = isinstance(value, list) and all(
            isinstance(item, str) for item in value)
        number_ok = isinstance(value, int) and not isinstance(value, bool)
        ok = {"id": text_ok, "text": text_ok, "importance": number_ok,
              "sources": list_ok, "voted": list_ok}[field]
        if not ok:
            return f"missing or malformed field {field}"
    if not entry["sources"]:
        return "cites no source run"
    if entry["importance"] < 1:
        return f"importance {entry['importance']} is below 1"
    return None


def _lesson_problems(lessons, shown):
    """Label-prefixed problems for lessons in file order (line 2 on)."""
    problems, ids = [], set()
    for n, entry in enumerate(lessons, start=2):
        why = _field_problem(entry)
        if why is None and entry["id"] in ids:
            why = f"duplicate id {entry['id']}"
        if why:
            problems.append(f"{LABEL}: {shown} line {n}: {why}")
        ids.add(entry.get("id"))
    return problems


def _parse(text, shown):
    """(lessons, seen, problems) for the file text."""
    lessons, seen, problems = [], [], []
    for n, line in enumerate(text.splitlines(), start=1):
        try:
            value = json.loads(line)
        except ValueError:
            return [], [], [f"{LABEL}: {shown} line {n}: not valid JSON"]
        if not isinstance(value, dict):
            return [], [], [f"{LABEL}: {shown} line {n}: not a JSON object"]
        if n == 1:
            if not isinstance(value.get("seen"), list):
                return [], [], [f"{LABEL}: {shown} line 1: expected the"
                                " seen header"]
            seen = value["seen"]
        else:
            lessons.append(value)
    problems = _lesson_problems(lessons, shown)
    return ([], [], problems) if problems else (lessons, seen, [])


def load(path, shown=None):
    """(lessons, seen, problems) from the lessons file. A missing or empty
    file is no lessons and no seen; any problem returns nothing else."""
    shown = shown or Path(path).name
    text, problem = read_file(path, shown, str)
    if problem:
        return [], [], [f"{LABEL}: {problem}"]
    return _parse(text, shown) if text else ([], [], [])


def serialize(lessons, seen):
    """The file text: the seen header, then lessons sorted by id."""
    rows = [{"seen": sorted(seen)}, *sorted(lessons, key=lambda e: e["id"])]
    return "".join(json.dumps(row, ensure_ascii=False) + "\n"
                   for row in rows)


def dump(path, lessons, seen, shown=None):
    """problems. Writes the whole file through a temp file and os.replace,
    so a failure leaves the original untouched. Invalid lessons write
    nothing; no lessons and no seen creates no file."""
    shown = shown or Path(path).name
    problems = _lesson_problems(sorted(lessons, key=lambda e: e["id"]),
                                shown)
    if problems or not (lessons or seen):
        return problems
    path = Path(path)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=path.parent, delete=False,
                prefix=f".{path.name}.") as handle:
            temp = handle.name
            handle.write(serialize(lessons, seen))
        os.replace(temp, path)
    except OSError as err:
        if temp:
            Path(temp).unlink(missing_ok=True)
        return [f"{LABEL}: cannot write {shown}: {err}"]
    return []
