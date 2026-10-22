#!/usr/bin/env python3
"""eval-trends: a read-only view of eval pass-rate trends over recorded history.

Reads the eval records the repo already holds (evals/results/ and
plugin-evals/records/), groups the records that are comparable (same
suite, same case set), and prints per-surface pass-rate trends with a
Wilson 95 percent interval, cost per pass where a record carries one,
and a REFUSED line wherever the records cannot support a trend claim
(ADR-0115; the run is docs/features/eval-trends/).

READ-ONLY, FREE AND LOCAL. It reads every record, writes nothing, and
calls no model, no CLI and no network. NOT A GATE: a
refusal is data and exits 0. Descriptive only: an interval comparison is
not a significance test, and a trend line is never a claim that an eval
improved.
"""
import datetime
import hashlib
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

from cli import read_file, report
from eval_schema import HARNESSES, parse_results_stem

LABEL = "eval-trends"
SURFACES = ("trigger", "charter", "output", "plugin", "decompose-signals")
NOTE = "docs/research/eval-quality-metrics-2026-10-21.md"
USAGE = "python3 eval_trends.py [<repo-root>]"
HEADER = (f"{LABEL}: descriptive only; a REFUSED line means the records "
          "cannot support a trend claim, not that nothing changed")
NOT_COMPUTED = (f"{LABEL}: not computed from any record: judge drift, "
                f"contamination, saturation, flake rate; see {NOTE}")
SIGNALS_REFUSED = (f"{LABEL}: REFUSED decompose-signals: not an eval run: "
                   "records re-measure one git history; no trend claim")
OVERLAP = ("intervals overlap: not distinguishable "
           "(descriptive, not a significance test)")
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# A trend needs at least MIN_DAYS distinct days and MIN_CASES cases in every
# record of the group. A convention, chosen with the Wilson arithmetic in
# docs/features/eval-trends/architecture.md; the research note argues it.
MIN_CASES = 30
MIN_DAYS = 2
MIN_RECORDS = 2
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


_ORDER = re.compile(r"\d{4}-\d{2}-\d{2}(?:-(\d+))?(?:\.json)?$")


def _order(file):
    """A file's place among same-day collisions: the unsuffixed name is
    first, then -2, -3 ... (plain string order puts -2 before the bare
    name, since - sorts before .)."""
    match = _ORDER.search(file)
    return int(match[1]) if match and match[1] else 1


def group_rows(rows):
    """{(suite, case_set): rows ordered by (day, collision order, file)}
    for one surface."""
    groups = defaultdict(list)
    for r in rows:
        groups[(r["suite"], r["case_set"])].append(r)
    return {key: sorted(members, key=lambda r: (r["day"], _order(r["file"]), r["file"]))
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


class RecordError(Exception):
    """One record is malformed; the message is the reason in its problem."""


def _need(data, key, kind):
    """data[key] when present and an instance of kind, else RecordError."""
    if key not in data:
        raise RecordError(f"missing field {key}")
    if not isinstance(data[key], kind):
        raise RecordError(f"malformed field {key}")
    return data[key]


def _day(text, key):
    """The YYYY-MM-DD day a date or timestamp field opens with, which
    must be a real calendar day."""
    if not isinstance(text, str) or not DAY.match(text[:10]) \
            or len(text) < 10:
        raise RecordError(f"malformed field {key}")
    try:
        datetime.date.fromisoformat(text[:10])
    except ValueError:
        raise RecordError(f"malformed field {key}") from None
    return text[:10]


def _named_day(text, key, name_day):
    """_day, and the day must be the one the file's name carries: a
    record the name dates differently is not read, so it cannot move
    between days (or into a same-day group) by its content alone."""
    day = _day(text, key)
    if day != name_day:
        raise RecordError(f"{key} disagrees with its name")
    return day


def _entries(data, key, fields):
    """The list data[key], each entry an object holding every field."""
    entries = _need(data, key, list)
    for entry in entries:
        if not isinstance(entry, dict) \
                or any(field not in entry for field in fields):
            raise RecordError(f"malformed field {key}")
    return entries


def _trigger_row(rel, data):
    """The row for one trigger record, or RecordError."""
    parsed = parse_results_stem(rel.stem)
    if parsed is None or parsed[0] != "trigger":
        raise RecordError("name fits no results grammar")
    harness = parsed[1] or HARNESSES[0]  # the unmarked primary harness
    if data.get("harness", harness) != harness:
        raise RecordError(
            f"harness {data['harness']!r} disagrees with its name")
    day = _named_day(_need(data, "date", str), "date", parsed[2])
    results = _entries(data, "results", ("id", "expected", "query", "pass"))
    summary = _need(data, "summary", dict)
    hits = sum(1 for r in results if r["pass"])
    if summary.get("total") != len(results) \
            or summary.get("passed") != hits:
        raise RecordError("summary disagrees with its results")
    if summary.get("errors", 0):
        raise RecordError(f"records {summary['errors']} error(s)")
    case_set = tuple(sorted((r["id"], r["expected"], r["query"])
                            for r in results))
    suite = (harness, data.get("model"), data.get("runs_per_query"),
             data.get("threshold"))
    return {"surface": "trigger", "file": rel.name, "day": day,
            "suite": suite, "case_set": case_set, "n": len(results),
            "hits": hits, "cost": None}


def _charter_row(rel, data):
    """The row for one charter replay: the metric is the count of
    `sensitive` verdicts, a charter's guard noticing its own removal,
    never a pass rate."""
    parsed = parse_results_stem(rel.stem)
    if parsed is None or parsed[0] != "charter":
        raise RecordError("name fits no results grammar")
    day = _named_day(_need(data, "date", str), "date", parsed[2])
    arm = _need(data, "arm", str)
    charters = _need(data, "charters", dict)
    results = _entries(data, "results", ("id", "role", "verdict"))
    suite = (arm, data.get("model"), tuple(sorted(charters.items())))
    return {"surface": "charter", "file": rel.name, "day": day,
            "suite": suite,
            "case_set": tuple(sorted((r["id"], r["role"]) for r in results)),
            "n": len(results),
            "hits": sum(1 for r in results if r["verdict"] == "sensitive"),
            "cost": None}


def _output_row(rel, data):
    """The row for one output grading: the slug and date come from the
    directory name, through the one results-name parser."""
    parsed = parse_results_stem(rel.parent.name)
    if parsed is None or parsed[0] != "output":
        raise RecordError("name fits no results grammar")
    expectations = _entries(data, "expectations", ("text", "passed"))
    summary = _need(data, "summary", dict)
    hits = sum(1 for e in expectations if e["passed"])
    if summary.get("total") != len(expectations) \
            or summary.get("passed") != hits:
        raise RecordError("summary disagrees with its results")
    return {"surface": "output", "file": rel.parent.name, "day": parsed[2],
            "suite": (parsed[4],),
            "case_set": tuple(sorted((e["text"],) for e in expectations)),
            "n": len(expectations), "hits": hits, "cost": None}


def _plugin_case(case):
    """One plugin case as (name, prompt, graders' (name, markdown))."""
    graders = case["graders"]
    if not isinstance(graders, list) or any(
            not isinstance(g, dict) or "name" not in g for g in graders):
        raise RecordError("malformed field cases")
    return (case["name"], case["promptMarkdown"],
            tuple(sorted((g["name"], g.get("graderMarkdown") or "")
                         for g in graders)))


def _plugin_row(rel, data):
    """The row for one plugin-eval record. Cost is the recorded
    top-level costUsd, never summed across fields, decomposed or
    estimated."""
    if data.get("partial") is True:
        raise RecordError("is partial")
    day = _named_day(_need(data, "startedAt", str), "startedAt",
                     rel.stem[:10])  # plugin records are named <date>[-N]
    suite = _need(data, "suite", dict)
    tags = _need(suite, "tagFilters", list)
    cases = _entries(data, "cases", ("name", "promptMarkdown", "graders"))
    aggregates = _need(data, "aggregates", dict)
    n, hits = _need(aggregates, "casesTotal", int), \
        _need(aggregates, "casesPassed", int)
    cost = data.get("costUsd")
    if cost is not None and not isinstance(cost, (int, float)):
        raise RecordError("malformed field costUsd")
    return {"surface": "plugin", "file": rel.name, "day": day,
            "suite": (tuple(sorted(tags)), suite.get("ablation"),
                      suite.get("modelOverride"), suite.get("judgeModel"),
                      suite.get("threshold")),
            "case_set": tuple(sorted(_plugin_case(c) for c in cases)),
            "n": n, "hits": hits, "cost": cost}


def _signals_row(rel, data):
    """The inventory-only row for one decompose-signals record: its
    aggregates re-measure one git history at a head, not an eval case
    set, so it carries a day and nothing to compare."""
    parsed = parse_results_stem(rel.stem)
    if parsed is None or parsed[0] != "decompose-signals":
        raise RecordError("name fits no results grammar")
    return {"surface": "decompose-signals", "file": rel.name,
            "day": _named_day(_need(data, "date", str), "date", parsed[2]),
            "suite": None,
            "case_set": None, "n": None, "hits": None, "cost": None}


def measured(rows):
    """The rows that are eval runs: everything but the inventory-only
    surface. Only these may reach classify."""
    return [r for r in rows if r["surface"] != "decompose-signals"]


def _read_surface(root, pattern, row_of):
    """(rows, problems) for the files matching pattern under root, in
    sorted path order; each file is read through cli.read_file."""
    rows, problems = [], []
    for path in sorted(Path(root).glob(pattern)):
        rel = path.relative_to(root)
        data, problem = read_file(path, rel.as_posix(), dict)
        if problem:
            problems.append(f"{LABEL}: {problem}")
            continue
        try:
            row = row_of(rel, data)
            hash((row["suite"], row["case_set"]))  # groups key on these
            rows.append(row)
        except RecordError as err:
            problems.append(f"{LABEL}: {rel.as_posix()} {err}")
        except TypeError:  # an object or list where a scalar belongs
            problems.append(
                f"{LABEL}: {rel.as_posix()} malformed field values")
    return rows, problems


READERS = (("evals/results/trigger*.json", _trigger_row),
           ("evals/results/charter-*.json", _charter_row),
           ("evals/results/output/*/grading.json", _output_row),
           ("plugin-evals/records/*.json", _plugin_row),
           ("evals/results/decompose-signals-*.json", _signals_row))


def load_rows(root):
    """(rows, problems) for every record under root, surfaces in SURFACES
    order and files in sorted path order. A malformed record is one
    labelled problem and no row; an absent location is an empty surface."""
    rows, problems = [], []
    for pattern, row_of in READERS:
        found, bad = _read_surface(root, pattern, row_of)
        rows += found
        problems += bad
    return rows, problems


def _pct(x):
    return f"{x * 100:.1f}"


def _label(value):
    """A suite key as one printable token: scalars joined by commas,
    nested keys by plus signs, None as none."""
    if value is None:
        return "none"
    if isinstance(value, (tuple, list)):
        return "+".join(_label(v) for v in value)
    return str(value)


def _suite_label(suite):
    return ",".join(_label(part) for part in suite)


def _inventory_line(surface, rows):
    if not rows:
        return f"{LABEL}: {surface}: 0 record(s)"
    days = sorted({r["day"] for r in rows})
    head = (f"{LABEL}: {surface}: {len(rows)} record(s), "
            f"{days[0]}..{days[-1]}, {len(days)} day(s)")
    if surface == "decompose-signals":
        return head
    sizes = [r["n"] for r in rows]
    return f"{head}, cases {min(sizes)}-{max(sizes)} per record"


def _by_day(members):
    """{day: rows} for one group, days in order."""
    days = defaultdict(list)
    for r in members:
        days[r["day"]].append(r)
    return dict(sorted(days.items()))


def _metric(surface):
    """What a row's hits count: a charter's metric is its guard noticing
    its own removal, never a pass rate."""
    return "sensitive" if surface == "charter" else "passed"


def _day_text(rows):
    """hits/n, the rate and the 95 percent hull for one day of one group;
    a day of reruns prints its lowest-to-highest hits and rate."""
    lo, hi = day_interval(rows)
    n = rows[0]["n"]  # one case set, one n
    hits = sorted(r["hits"] for r in rows)
    if len(rows) == 1:
        counts, rate = f"{hits[0]}/{n}", _pct(hits[0] / n)
    else:
        counts = f"{hits[0]}..{hits[-1]}/{n}"
        rate = f"{_pct(hits[0] / n)}..{_pct(hits[-1] / n)}"
    word = " sensitive" if rows[0]["surface"] == "charter" else ""
    return f"{counts}{word} ({rate}%, 95% {_pct(lo)}-{_pct(hi)}%)"


def _files(members):
    return ", ".join(r["file"] for r in members)


def _spread_lines(surface, members):
    """One rerun-spread line per day of this group holding 2 or more."""
    return [
        f"{LABEL}: {surface} rerun spread {day} set "
        f"{case_set_hex(rows[0]['case_set'])}: {_metric(surface)} "
        f"{min(r['hits'] for r in rows)}..{max(r['hits'] for r in rows)} of "
        f"{rows[0]['n']} over {len(rows)} run(s) ({_files(rows)})"
        for day, rows in _by_day(members).items() if len(rows) >= 2]


def _cost_line(surface, members, first, last):
    """The cost-per-pass line for a trend group, or its refusal."""
    before, after = cost_per_pass(first), cost_per_pass(last)
    if before is not None and after is not None:
        return (f"{LABEL}: {surface} cost per pass: {first[0]['day']} "
                f"${before:.4f} -> {last[0]['day']} ${after:.4f} "
                f"({_files(members)})")
    absent = sum(1 for r in members if r["cost"] is None)
    why = (f"cost field absent from {absent} of {len(members)} record(s)"
           if absent else "no passed case to divide by")
    return f"{LABEL}: {surface} cost: REFUSED {why}; no trend claim"


def _trend_lines(surface, members):
    """The trend line and its cost line for one comparable group: first
    day against last day by interval overlap, never a verdict word."""
    days = _by_day(members)
    first, last = days[min(days)], days[max(days)]
    (lo1, hi1), (lo2, hi2) = day_interval(first), day_interval(last)
    verdict = OVERLAP if lo2 <= hi1 and lo1 <= hi2 \
        else "intervals do not overlap"
    trend = (f"{LABEL}: {surface} trend set "
             f"{case_set_hex(members[0]['case_set'])} suite "
             f"{_suite_label(members[0]['suite'])}: {first[0]['day']} "
             f"{_day_text(first)} -> {last[0]['day']} {_day_text(last)}; "
             f"{verdict} ({_files(members)})")
    return [trend, _cost_line(surface, members, first, last)]


def _refused_lines(surface, classified):
    """One REFUSED line per state present among the surface's records."""
    def of(state):
        return [r for r in classified if r["state"] == state]

    def reasoned(reason):
        return [r for r in of("single") if r["reason"] == reason]

    lines = []
    if len(classified) < MIN_RECORDS:  # also an empty surface
        lines.append(f"too few records: need {MIN_RECORDS}, "
                     f"have {len(classified)}")
    if reasoned("different suites"):
        lines.append(f"different suites: {len(reasoned('different suites'))}"
                     " record(s) share no suite with another record")
    if reasoned("case sets differ"):
        lines.append(f"case sets differ: {len(reasoned('case sets differ'))}"
                     " record(s) share a suite with another record but not"
                     " its case set")
    if of("same-day"):
        groups = len({(r["suite"], r["case_set"]) for r in of("same-day")})
        lines.append(f"only same-day records: {len(of('same-day'))} "
                     f"record(s) in {groups} group(s), each on one day")
    if of("small"):
        lines.append(f"too few cases: need {MIN_CASES}, have "
                     f"{max(r['n'] for r in of('small'))} in "
                     f"{len(of('small'))} record(s) over {MIN_DAYS}+ days")
    return [f"{LABEL}: REFUSED {surface}: {line}; no trend claim"
            for line in lines]


def _surface_lines(surface, rows):
    """Spread, trend, cost and REFUSED lines for one eval surface."""
    classified = classify(rows)
    state = {(r["suite"], r["case_set"]): r["state"] for r in classified}
    groups = sorted(group_rows(rows).items(),
                    key=lambda kv: (kv[1][0]["day"], _order(kv[1][0]["file"]),
                                    kv[1][0]["file"]))
    lines = [ln for _, members in groups
             for ln in _spread_lines(surface, members)]
    for key, members in groups:
        if state[key] == "trend":
            lines += _trend_lines(surface, members)
    return lines + _refused_lines(surface, classified)


def render(rows):
    """The whole view as lines, in the fixed order: header, one inventory
    line per surface, each surface's detail, the not-computed line."""
    by_surface = {s: [r for r in rows if r["surface"] == s]
                  for s in SURFACES}
    lines = [HEADER]
    lines += [_inventory_line(s, by_surface[s]) for s in SURFACES]
    for surface in SURFACES:
        if surface == "decompose-signals":
            lines.append(SIGNALS_REFUSED)
        else:
            lines += _surface_lines(surface, by_surface[surface])
    return lines + [NOT_COMPUTED]


def _usage(why):
    print(f"{LABEL}: {why}\n\n  {USAGE}")
    return 2


def main(argv):
    """`python3 eval_trends.py [<repo-root>]` — print the trend view of the
    records under the repo root (default: this module's directory). Exit 0
    when no record is malformed (a refusal is data), 1 with problems, 2 on
    a usage error."""
    if len(argv) > 1 or any(a.startswith("-") for a in argv):
        return _usage(f"{' '.join(argv)!r} — unknown argument")
    root = Path(argv[0]) if argv else Path(__file__).resolve().parent
    if not root.is_dir():
        return _usage(f"{str(root)!r} is not a directory")
    rows, problems = load_rows(root)
    for line in render(rows):
        print(line)
    return report(LABEL, problems)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
