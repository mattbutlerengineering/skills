#!/usr/bin/env python3
"""plane_drift: the one cross-plane drift rule (ADR-0032, ADR-0060).

ADR-0032 makes the breakdown row authoritative and the tracker issue its
one-way mirror. Drift is the two planes disagreeing, and exactly one
question answers it: given the rows and the live issue listing, where do
they contradict each other?

Two tools ask it and do different things with the answer — `sweeps.py
reconcile` files an intake issue, `dashboard.py` renders a section — so
the rule is a module and each tool is a caller. It is PURE: the listing
arrives as data, so neither caller's runner reaches this file, and no
test here needs one.

The callers differ in exactly one respect, and it is a real difference
rather than one copy being weaker: whether a row whose mirror is *absent
from the listing* is drift. `sweeps.live_issues` ABORTS on a truncated
window, so absence there means the issue is genuinely gone. The
dashboard reports truncation and renders on, so it cannot tell "gone"
from "past the window" and declines to guess. That is the
`absent_is_drift` argument — one branch, named, instead of two
implementations that quietly disagree.

Conventions match the modules that call it: `drift:`-prefixed problem
strings for malformed input, and drift findings that are plain lines for
the caller to render or file.
"""
from knowledge_plane import row_done, row_tracker_issue


def issue_lifecycle(issue):
    """The `wo:` labels one issue-listing entry carries, sorted. Anything
    that is not a `{"name": ...}` object is ignored rather than guessed
    at — the shape is gh's, and a changed shape becomes a drift report's
    silence, not a traceback in a scheduled run."""
    labels = issue.get("labels")
    names = [entry.get("name") for entry in labels
             if isinstance(entry, dict)] if isinstance(labels, list) else []
    return sorted(name for name in names
                  if isinstance(name, str) and name.startswith("wo:"))


def _describe(labels):
    return ", ".join(labels) if labels else "no wo: label"


def reconcile_drift(rows, issues, absent_is_drift=True):
    """PURE: (breakdown rows, the live issue listing) -> (drift lines,
    problems).

    Every line names a breakdown path and an issue NUMBER, never a work
    order id: the row is identified by where it lives, which is also where
    a human goes to fix it. The knowledge plane is authoritative in every
    comparison — a line says what the dispatch plane must be brought to,
    never the reverse (ADR-0032).

    `rows` is (display path, lines) per breakdown, so the caller owns how
    paths are spelled and this stays a pure function.

    `absent_is_drift` is the caller's claim about its own listing: True
    only if a missing issue means gone rather than unread. It gates the
    membership check alone — every other class compares a row against an
    issue the listing actually produced, which is a definite fact
    whatever a window hid.
    """
    index, problems = {}, []
    for position, issue in enumerate(issues):
        if not isinstance(issue, dict) or not isinstance(
                issue.get("number"), int):
            problems.append(f"drift: issue listing entry {position} has no"
                            " usable number")
            continue
        index[issue["number"]] = issue
    drift, mirrored = [], {}
    for path, lines in rows:
        for line in lines:
            number = row_tracker_issue(line)
            if number is None:
                continue
            mirrored.setdefault(number, []).append(path)
            issue = index.get(number)
            if issue is None:
                if absent_is_drift:
                    drift.append(f"{path}: a row mirrors #{number}, which is"
                                 " not in the issue listing")
                continue
            labels = issue_lifecycle(issue)
            merged = "wo:merged" in labels
            state = str(issue.get("state") or "").lower()
            if row_done(line):
                if not merged:
                    drift.append(f"{path}: a checked row mirrors #{number},"
                                 f" which carries {_describe(labels)} — the"
                                 " row says merged")
                elif state == "open":
                    drift.append(f"{path}: a checked row mirrors #{number},"
                                 " which is labelled wo:merged but still open")
            elif merged:
                drift.append(f"{path}: an unchecked row mirrors #{number},"
                             " which is labelled wo:merged — the issue is"
                             " ahead of the row")
            elif state == "closed":
                drift.append(f"{path}: an unchecked row mirrors #{number},"
                             f" which is closed carrying {_describe(labels)}"
                             " — the row says the work is outstanding")
    for number, paths in sorted(mirrored.items()):
        if len(paths) > 1:
            drift.append(f"#{number} is mirrored by {len(paths)} rows"
                         f" ({', '.join(sorted(set(paths)))}) — an issue"
                         " mirrors one work order")
    for number, issue in sorted(index.items()):
        labels = issue_lifecycle(issue)
        if not labels:
            continue
        if len(labels) > 1:
            drift.append(f"#{number} carries {len(labels)} lifecycle labels"
                         f" at once ({', '.join(labels)}) — the state"
                         " machine allows one")
        if number not in mirrored:
            drift.append(f"#{number} carries {_describe(labels)} but no"
                         " breakdown row mirrors it — the dispatch plane is"
                         " ahead of the knowledge plane")
    return drift, problems
