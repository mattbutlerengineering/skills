#!/usr/bin/env python3
"""eval-trends: a read-only view of eval pass-rate trends over recorded history.

Reads the eval records the repo already holds (evals/results/ and
plugin-evals/records/), groups the records that are comparable (same
suite, same case set), and prints per-surface pass-rate trends with a
Wilson 95 percent interval, cost per pass where a record carries one,
and a REFUSED line wherever the records cannot support a trend claim
(ADR-0115; the run is docs/features/eval-trends/).

READ-ONLY, FREE AND LOCAL. It opens every record for reading, writes
nothing, and calls no model, no `claude` and no network. NOT A GATE: a
refusal is data and exits 0. Descriptive only: an interval comparison is
not a significance test, and a trend line is never a claim that an eval
improved.
"""
import hashlib
import math
from collections import defaultdict

# A trend needs at least MIN_DAYS distinct days and MIN_CASES cases in every
# record of the group. A convention, chosen with the Wilson arithmetic in
# docs/features/eval-trends/architecture.md; the research note argues it.
MIN_CASES = 30
MIN_DAYS = 2
Z = 1.96


def wilson(hits, n):
    """The 95 percent Wilson score interval for hits of n, as fractions."""
    p = hits / n
    scale = 1 + Z * Z / n
    centre = (p + Z * Z / (2 * n)) / scale
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / scale
    return max(0.0, centre - half), min(1.0, centre + half)


def day_interval(rows):
    """[min lower, max upper] over the Wilson intervals of one day's rows.

    The hull, not a pooled interval: reruns share cases, so pooling would
    shrink the interval as if n had grown."""
    intervals = [wilson(r["hits"], r["n"]) for r in rows]
    return min(lo for lo, _ in intervals), max(hi for _, hi in intervals)


def cost_per_pass(rows):
    """Summed costUsd over summed passed cases to four decimals, or None
    when any row carries no cost or no case passed (the line is refused)."""
    if any(r["cost"] is None for r in rows):
        return None
    passed = sum(r["hits"] for r in rows)
    if passed == 0:
        return None
    return round(sum(r["cost"] for r in rows) / passed, 4)


def case_set_hex(case_set):
    """The first 8 hex of a sha256 of the sorted case tuples: a label for
    printing, never the identity groups rely on (they key on the tuples)."""
    return hashlib.sha256(
        repr(tuple(sorted(case_set))).encode("utf-8")).hexdigest()[:8]


def group_rows(rows):
    """{(suite, case_set): rows ordered by (day, file)} for one surface."""
    groups = defaultdict(list)
    for r in rows:
        groups[(r["suite"], r["case_set"])].append(r)
    return {key: sorted(members, key=lambda r: (r["day"], r["file"]))
            for key, members in groups.items()}


def _group_state(members):
    """(state, reason) shared by the records of one group of 2 or more."""
    if len({r["day"] for r in members}) < MIN_DAYS:
        return "same-day", None
    if any(r["n"] < MIN_CASES for r in members):
        return "small", None
    return "trend", None


def _single_reason(key, groups):
    """Why a lone record has no partner: another group shares its suite
    but not its case set, or no other group shares its suite."""
    suite = key[0]
    return ("case sets differ"
            if any(other[0] == suite and other != key for other in groups)
            else "different suites")


def classify(rows):
    """Every row of one surface with exactly one state and reason added,
    in input order, as new dicts (the input is never mutated).

    too few records: the surface holds fewer than 2 rows. single: its
    group holds one record (reason: case sets differ | different suites).
    same-day: its group spans one day. small: it spans MIN_DAYS or more
    but some record has fewer than MIN_CASES cases. trend: otherwise."""
    groups = group_rows(rows)
    out = []
    for r in rows:
        key = (r["suite"], r["case_set"])
        if len(rows) < 2:
            state, reason = "too few records", None
        elif len(groups[key]) == 1:
            state, reason = "single", _single_reason(key, groups)
        else:
            state, reason = _group_state(groups[key])
        out.append({**r, "state": state, "reason": reason})
    return out
