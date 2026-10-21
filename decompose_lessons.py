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
import subprocess
import sys
import tempfile
from pathlib import Path

import decompose_signals
import factory_config
from cli import CLI_FAILURES, detail, read_file, report, runner

LABEL = "decompose-lessons"
USAGE = "python3 decompose_lessons.py [update]"
LESSONS_PATH = "docs/factory/decompose-lessons.jsonl"
NO_PAIR = f"{LABEL}: no contrast pair found \u2014 no lesson derived"
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


# Pair derivation. Only the three outcome signals decompose_signals
# measures exist here (re-plan, design gaps, review-traced), so a band
# miss or a retro note has no input to reach. Records are as measure
# returns them.

# The re-plan detail ties break in this order.
REPLAN_DETAILS = ("added", "dropped", "split", "merged")
REPLAN_PHRASES = {"added": "adding rows", "dropped": "dropping rows",
                  "split": "splitting rows", "merged": "merging rows"}


def kind(ref):
    """A run ref's kind, its prefix: feature, maintenance or product."""
    return ref.split(":")[0]


def _name(ref):
    return ref.partition(":")[2] or ref


def _signals():
    """(RunRecord field, count field, denominator field or None) for each
    signal, in decompose_signals' report order."""
    return [(field, num, den) for _, field, num, den
            in decompose_signals.SIGNALS]


def _hit_label(value, num):
    """(label, count) of one measurable signal value, else None."""
    if "unmeasurable" in value:
        return None
    return value.get("label", "observed"), value.get(num, 0)


def _detail(field, value):
    if field == "replan":
        return max(REPLAN_DETAILS, key=lambda name: value[name])
    return "routed" if field == "design_gaps" else "named"


def _figure(ref, value, label, num, den):
    count = value.get(num, 0)
    if den is None:
        return f"{_name(ref)} {count} route(s) ({label})"
    unit = "items" if den == "items_at_d" else "findings"
    return f"{_name(ref)} {count} of {value.get(den, 0)} {unit} ({label})"


def _text(field, run_kind, detail, hit, clean, num, den):
    (h_ref, h_val, h_label), (c_ref, c_val, c_label) = hit, clean
    contrast = (f"{_figure(h_ref, h_val, h_label, num, den)},"
                f" {_figure(c_ref, c_val, c_label, num, den)}")
    if field == "replan":
        lead = (f"{run_kind} runs that re-planned mostly by"
                f" {REPLAN_PHRASES[detail]}")
    elif field == "design_gaps":
        lead = f"{run_kind} runs routed back to Architect"
    else:
        lead = f"{run_kind} runs whose review findings name an item"
    return f"{lead}: {contrast}"


def pairs(records, skip=()):
    """Contrast pairs {signal, kind, detail, hit, clean, text}: each
    measurable hit run (count above 0) on a signal, unless its ref is in
    `skip`, paired with the first clean run (count 0) in record order
    that has the hit run's kind and label. No clean run, no pair."""
    found = []
    for field, num, den in _signals():
        for hit in records:
            figure = _hit_label(hit[field], num)
            if figure is None or figure[1] == 0 or hit["run"] in skip:
                continue
            label, run_kind = figure[0], kind(hit["run"])
            clean = next((r for r in records
                          if kind(r["run"]) == run_kind
                          and _hit_label(r[field], num)
                          == (label, 0)), None)
            if clean is None:
                continue
            detail = _detail(field, hit[field])
            text = _text(field, run_kind, detail,
                         (hit["run"], hit[field], label),
                         (clean["run"], clean[field], label), num, den)
            found.append({"signal": field, "kind": run_kind,
                          "detail": detail, "hit": hit["run"],
                          "clean": clean["run"], "text": text})
    return found


def pair_id(pair):
    """The lesson id a pair collapses to: <signal>/<kind>/<detail>."""
    return f"{pair['signal']}/{pair['kind']}/{pair['detail']}"


def candidates(pair_list):
    """The lessons the pairs collapse to, sorted by id: {id, text,
    sources}. The text is the first pair's; the sources are every hit
    and clean run of the pairs with that id, sorted."""
    grouped = {}
    for pair in pair_list:
        entry = grouped.setdefault(
            pair_id(pair), {"id": pair_id(pair), "text": pair["text"],
                            "sources": set()})
        entry["sources"].update((pair["hit"], pair["clean"]))
    return [{**entry, "sources": sorted(entry["sources"])}
            for _, entry in sorted(grouped.items())]


# Voting. A voter is a run whose draft could have read the file: its
# decompose commit descends from the commit that first added the lessons
# file. git is reached through the injected runner, read-only.

def _git(run, root, args):
    """(CompletedProcess or None, problems) for one git call."""
    try:
        return run(args, cwd=str(root)), []
    except CLI_FAILURES as err:
        return None, [f"{LABEL}: git {args[0]} failed: {detail(err)}"]


def _first_add(run, root):
    """(oldest commit adding the lessons file or None, problems)."""
    done, problems = _git(run, root, ["log", "--diff-filter=A",
                                      "--format=%H", "--", LESSONS_PATH])
    if done is None:
        return None, problems
    shas = done.stdout.split()
    return (shas[-1] if shas else None), []


def _descends(run, root, first, sha):
    """(True when `first` is an ancestor of `sha`, problems): exit 1 is
    the answer no, any other failure a problem."""
    try:
        run(["merge-base", "--is-ancestor", first, sha], cwd=str(root))
        return True, []
    except subprocess.CalledProcessError as err:
        if err.returncode == 1:
            return False, []
        return False, [f"{LABEL}: git merge-base failed: {detail(err)}"]
    except CLI_FAILURES as err:
        return False, [f"{LABEL}: git merge-base failed: {detail(err)}"]


def treated(root, run, records):
    """(refs of the runs whose decompose commit descends from the commit
    that first added the lessons file, problems). No such commit, or a
    run with no decompose commit, is not treated; a git failure gives no
    runs and the problem."""
    first, problems = _first_add(run, root)
    if first is None:
        return set(), problems
    found = set()
    for rec in records:
        sha = rec["decompose"].get("sha")
        if sha is None:
            continue
        yes, problems = _descends(run, root, first, sha)
        if problems:
            return set(), problems
        if yes:
            found.add(rec["run"])
    return found, []


def _lesson_parts(lid):
    signal, run_kind, _ = lid.split("/", 2)
    return signal, run_kind


def _ballot(lesson_entry, rec):
    """The vote one voter casts on one lesson, or None when it may not."""
    signal, run_kind = _lesson_parts(lesson_entry["id"])
    num = {field: n for field, n, _ in _signals()}.get(signal)
    figure = _hit_label(rec[signal], num) if num else None
    if figure is None or kind(rec["run"]) != run_kind \
            or rec["run"] in lesson_entry["voted"]:
        return None
    return "downvote" if figure[1] else "upvote"


def votes(root, run, lessons, records, seen):
    """(ballots, problems): (op, lesson id, run ref) for each treated,
    unseen run with an observed decompose boundary and a measurable
    signal, once per lesson. A git failure gives no ballots."""
    kinds = {_lesson_parts(entry["id"])[1] for entry in lessons}
    eligible = [rec for rec in records
                if rec["run"] not in seen and kind(rec["run"]) in kinds
                and rec["decompose"].get("label") == "observed"]
    if not eligible:
        return [], []
    voters, problems = treated(root, run, eligible)
    if problems:
        return [], problems
    ballots = []
    for entry in lessons:
        for rec in eligible:
            op = _ballot(entry, rec) if rec["run"] in voters else None
            if op:
                ballots.append((op, entry["id"], rec["run"]))
    return ballots, []


# The update fold: votes on existing lessons, then ADD or EDIT from new hit
# runs, then the drop at 0 (a vote that takes a lesson below 1 removes it).
# A lesson dropped this fold is not re-added by it, and every hit run is
# folded into `seen`, so it cannot return from the same runs.

def _apply_ballots(lessons, ballots):
    """(lessons, lines, dropped ids, problems); a problem abandons all."""
    lines, dropped = [], []
    for op, lid, voter_ref in ballots:
        step = upvote if op == "upvote" else downvote
        lessons, problems = step(lessons, lid, voter_ref)
        if problems:
            return lessons, [], [], problems
        lines.append(f"{LABEL}: {op.upper()} {lid}")
        if _find(lessons, lid) is None:
            lines.append(f"{LABEL}: DROP {lid}")
            dropped.append(lid)
    return lessons, lines, dropped, []


def _apply_candidates(lessons, found, dropped):
    """(lessons, lines, problems): ADD a new id, EDIT a known id whose
    sources grew, nothing for an id dropped in this fold."""
    lines = []
    for cand in found:
        lid = cand["id"]
        at = _find(lessons, lid)
        if lid in dropped:
            continue
        if at is None:
            lessons, problems = add(lessons, lid, cand["text"],
                                    cand["sources"])
            op = "ADD"
        else:
            merged = sorted({*lessons[at]["sources"], *cand["sources"]})
            if merged == sorted(lessons[at]["sources"]):
                continue
            lessons, problems = edit(lessons, lid, cand["text"], merged)
            op = "EDIT"
        if problems:
            return lessons, [], problems
        lines.append(f"{LABEL}: {op} {lid}")
    return lessons, lines, []


def fold(lessons, seen, records, ballots):
    """(lessons, seen, lines, problems) after one update over `records`
    and the `ballots` votes() returned. Pure; on a problem the inputs
    come back unchanged with no lines."""
    voted, vote_lines, dropped, problems = _apply_ballots(lessons, ballots)
    if problems:
        return lessons, seen, [], problems
    new_pairs = pairs(records, skip=set(seen))
    grown, add_lines, problems = _apply_candidates(
        voted, candidates(new_pairs), dropped)
    if problems:
        return lessons, seen, [], problems
    complete = {rec["run"] for rec in records
                if "sha" in rec["implement"]}
    folded = (set(seen) | complete | {p["hit"] for p in new_pairs}
              | {ref for _, _, ref in ballots})
    return grown, sorted(folded), vote_lines + add_lines, []


def update(root, run, measure=decompose_signals.measure):
    """(lines, problems): load the file, measure, vote, fold and write the
    whole file once. A problem anywhere leaves the file untouched."""
    path = Path(root) / LESSONS_PATH
    lessons, seen, problems = load(path, LESSONS_PATH)
    if problems:
        return [], problems
    result, problems = measure(root, run)
    if result is None or problems:
        return [], problems
    ballots, problems = votes(root, run, lessons, result["runs"], seen)
    if problems:
        return [], problems
    new, new_seen, lines, problems = fold(lessons, seen, result["runs"],
                                          ballots)
    if problems:
        return [], problems
    old_text, problem = read_file(path, LESSONS_PATH, str)
    if problem:
        return [], [f"{LABEL}: {problem}"]
    if not new and old_text is None:
        return [NO_PAIR, f"{LABEL}: unchanged"], []
    if serialize(new, new_seen) == old_text:
        return [*lines, f"{LABEL}: unchanged"], []
    problems = dump(path, new, new_seen, LESSONS_PATH)
    if problems:
        return [], problems
    return [*lines, f"{LABEL}: wrote {LESSONS_PATH}"], []


# Comparison: re-plan pooled (sum of count over sum of items_at_d) over
# observed-label measurable runs, treated against untreated. Descriptive
# only: at present volume one re-plan moves the rate about 4 points, so no
# significance is claimed, and the floor is factory_config's.

def _pool(runs):
    """(re-plans, items, run count) summed over replan values."""
    return (sum(v["count"] for v in runs), sum(v["items_at_d"] for v in runs),
            len(runs))


def compare(records, treated_set, floor):
    """The comparison lines: the verdict or refusal, then the unmeasurable
    runs by name when there are any. Unmeasurable and inferred runs are
    in neither pool; an unmeasurable run is never counted as zero."""
    observed = [(r["run"], r["replan"]) for r in records
                if r["replan"].get("label") == "observed"]
    unmeasurable = [r["run"] for r in records if "unmeasurable" in r["replan"]]
    t = _pool([v for ref, v in observed if ref in treated_set])
    u = _pool([v for ref, v in observed if ref not in treated_set])
    if t[2] < floor:
        lines = [f"{LABEL}: no verdict: {t[2]} treated run(s) is below the"
                 f" minimum of {floor}"]
    else:
        # lean: a zero-item untreated pool has no rate, so it reads "not
        # higher"; upgrade to a third wording if a repo ever reaches it.
        higher = u[1] > 0 and t[0] * u[1] > u[0] * t[1]
        lines = [f"{LABEL}: re-plan treated {t[0]}/{t[1]} over {t[2]}"
                 f" run(s), untreated {u[0]}/{u[1]} over {u[2]} run(s)"
                 f" (observed only; {len(unmeasurable)} unmeasurable);"
                 " descriptive, treated"
                 f" {'higher' if higher else 'not higher'}"]
    if unmeasurable:
        lines.append(f"{LABEL}: unmeasurable re-plan run(s):"
                     f" {', '.join(unmeasurable)}")
    return lines


# Report and front door.

def _hit_runs(records):
    """How many (signal, run) hits the records hold, with or without a
    clean run to pair them with."""
    return sum(1 for field, num, _ in _signals() for rec in records
               if (_hit_label(rec[field], num) or (0, 0))[1] > 0)


def _pair_line(pair_list, records):
    if not pair_list:
        return NO_PAIR
    per = {field: sum(1 for p in pair_list if p["signal"] == field)
           for field, _, _ in _signals()}
    return (f"{LABEL}: {len(pair_list)} contrast pair(s) from"
            f" {_hit_runs(records)} hit run(s): re-plan {per['replan']},"
            f" design gaps {per['design_gaps']}, review-traced"
            f" {per['review']}")


def render(pair_list, lessons, comparison, records):
    """The report's lines: the pair count (or the no-pair string), one
    line per lesson, then the comparison."""
    lines = [_pair_line(pair_list, records)]
    lines += [f"{LABEL}: {entry['id']} importance {entry['importance']}"
              f" \u2014 {entry['text']}"
              f" (sources: {', '.join(entry['sources'])})"
              for entry in lessons]
    return lines + comparison


def _status(root, run, measure):
    """(lines, runs read, problems) for the read-only report."""
    config, problems = factory_config.load(root)
    floor, floor_problems = (None, []) if problems else \
        factory_config.resolve_calibrate_floor(config)
    lessons, _, file_problems = load(Path(root) / LESSONS_PATH,
                                     LESSONS_PATH)
    problems = problems + floor_problems + file_problems
    if problems:
        return [], 0, problems
    result, problems = measure(root, run)
    if result is None:
        return [], 0, problems
    records = result["runs"]
    treated_set, treated_problems = treated(root, run, records)
    comparison = compare(records, treated_set, floor)
    lines = render(pairs(records), lessons, comparison, records)
    return lines, len(records), problems + treated_problems


def main(argv, root=None, run=None, measure=decompose_signals.measure):
    """`python3 decompose_lessons.py [update]` \u2014 print the pair count, the
    lessons and the treated-versus-untreated re-plan comparison; `update`
    folds new runs in and writes the file, the one writer. Exit 0 when
    nothing failed (an empty pair set and a refused verdict included), 1
    with problems, 2 on an unknown argument."""
    if argv not in ([], ["update"]):
        print(f"{LABEL}: {' '.join(argv)!r} \u2014 unknown argument\n\n"
              f"  {USAGE}")
        return 2
    root = Path(root) if root is not None else decompose_signals.repo_root()
    run = run or runner("git", timeout=decompose_signals.GIT_TIMEOUT)
    if argv:
        lines, problems = update(root, run, measure)
        prefix = ""
    else:
        lines, count, problems = _status(root, run, measure)
        prefix = f"{count} run(s), " if count else ""
    for line in lines:
        print(line)
    return report(LABEL, problems, prefix=prefix)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
