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


def _lesson(lid, text, sources, importance=2, voted=()):
    return {"id": lid, "importance": importance, "text": text,
            "sources": list(sources), "voted": list(voted)}


def _find(lessons, lid):
    return next((n for n, entry in enumerate(lessons)
                 if entry["id"] == lid), None)


def _refused(op, why):
    return f"decompose-lessons: {op} refused: {why}"


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
