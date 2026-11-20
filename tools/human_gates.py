"""human_gates: what the three human gates are, and how to read one
issue's label history against them (ADR-0056).

The gates are the factory's only human decision points (ADR-0033;
CONTEXT.md: PRD approval, blueprint/ADR approval, PR merge), so their
queues live on the work orders' mirrored issues as `wo:` lifecycle
labels (ADR-0032, ADR-0035): `wo:draft` waits at the PRD gate,
`wo:prd-approved` at the blueprint gate, `wo:needs-review` at the merge
gate. This module owns that vocabulary and the walk over it — the
label-event stream, the completed-stay partition, the current stay's
start, the open queues aged from it, and (read_timelines) the one read
that produces the stream and says what its admission refused.

Its callers are thin: gate_digest.py keeps the confirmed stays as
latency rows, rejection_mining.py harvests the rest, dashboard.py ages
the open ones, gates.py's detector J asks which labels the gates
name, validator.py reads GATES, trace.py reads a run's timelines, and
work_queue.py asks who applied its ready label. They differ in what a stay MEANS to them, never in what a stay
IS, which is the whole reason this is one module and their posts and
compositions are not.

Pure but for three functions: no ledger, no filesystem, no clock (`now`
is an argument). read_timelines is the exception ADR-0090 made,
read_labelers (the same read, asking who applied a label — work_queue's
owner-only ready label, ADR-0032) the second, and read_gate_issues (the
listing plus read_timelines) the third — all
read gh, but only through the injected runner at cli's gh port, so
tests still never touch the network. ADR-0056 had kept that read in each
tool; the #491 refusal then had to be wired into each copy, and one
copy missed it (#791). Everything else is events in, gate facts out,
testable with a literal list.
"""
import json
import re
import subprocess
from collections import namedtuple
from datetime import datetime, timezone

from cli import CLI_FAILURES, GhResult, detail, gh_read, label_names

# A gate's ledger name, the wo: label an issue carries while waiting,
# the label whose application confirms the pass (a flip to anything else
# — wo:blocked, wo:failed — is not a passage), and the digest heading.
# Named rather than positional so detector J can ask for the labels
# instead of slicing gate[1:3]; the sites that iterate the rows still
# unpack them positionally (cost_report.GuardResult's precedent).
Gate = namedtuple("Gate", "name queue passed heading")

# The three gates in pipeline order. Six label slots, five distinct
# labels: passing the PRD gate is entering the blueprint gate's queue.
GATES = (
    Gate("prd", "wo:draft", "wo:prd-approved", "PRD gate"),
    Gate("blueprint", "wo:prd-approved", "wo:blueprint-approved",
         "Blueprint gate"),
    Gate("merge", "wo:needs-review", "wo:merged", "Merge gate"),
)


def gate_labels():
    """Every label the three gates name — each queue and each pass
    label. Detector J's one reach into this module (LABELS below, which
    gates.declared_labels reads): the taxonomy must carry all of them,
    and the detector should not know how many label fields a row has."""
    return {label for gate in GATES for label in (gate.queue, gate.passed)}


LABELS = tuple(sorted(gate_labels()))


def _parse_ts(iso):
    """GitHub timestamps end in Z; fromisoformat only accepts that from
    3.11, and local runs may be older."""
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def _is_timestamp(value):
    """The module's one answer to "is this a timestamp", asked once at
    admission so nothing downstream has to ask it again.

    Two clauses, and the second is the one that is easy to miss: the
    value must parse, AND it must carry a UTC offset. "2026-08-01"
    parses cleanly to a naive datetime, and subtracting a naive datetime
    from an aware one raises TypeError — the same crash this guard
    exists to prevent, one step further along. Parseability alone is not
    the precondition waited_seconds needs.

    The isinstance test is not decoration either: `value` is a field of
    a decoded API response, and a non-string one would fail inside
    _parse_ts with an AttributeError from .replace rather than a parse
    error, which is a worse thing to depend on."""
    if not isinstance(value, str):
        return False
    try:
        return _parse_ts(value).tzinfo is not None
    except ValueError:
        return False


def _utc_z(iso):
    """An admitted timestamp respelled as UTC "YYYY-MM-DDTHH:MM:SSZ",
    GitHub's own form. Downstream takes the date from the first ten
    characters (a ledger row's `at`) and embeds the string in a run_id,
    so an offset or basic-format spelling would date a row by its local
    day, or give it an `at` the ledger refuses — and refuse the digest's
    whole batch on every later run, since timelines never change."""
    return _parse_ts(iso).astimezone(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def waited_seconds(start, end):
    """Whole seconds between two GitHub timestamps.

    Both are offset-aware ISO-8601 by precondition, established by
    label_events, which admits no event whose timestamp fails either
    clause of _is_timestamp.
    So this raises only for a programming error at a future call site
    that sources its timestamps somewhere else — do not add a handler
    here, which would put a second owner on a policy the admission gate
    already holds."""
    return int((_parse_ts(end) - _parse_ts(start)).total_seconds())


def _admit_raw(timeline):
    """([(raw event, kind, name)] admitted, refused count): the one walk
    over a raw GitHub timeline — every event classed as a label flip
    carrying a name, split into admitted (timestamp reads as one) and
    refused (it does not). One loop reading the payload's
    `event`/`label`/`created_at` keys, so _admit and read_labelers
    cannot drift apart — the second clause of "well-formed" is still
    asked exactly once, by `_is_timestamp`."""
    admitted = []
    refused = 0
    for event in timeline:
        kind = event.get("event")
        if kind not in ("labeled", "unlabeled"):
            continue
        name = (event.get("label") or {}).get("name")
        if not name:
            continue
        if _is_timestamp(event.get("created_at")):
            admitted.append((event, kind, name))
        else:
            refused += 1
    return admitted, refused


def _admit(timeline):
    """(admitted [(UTC timestamp, kind, name)], refused count) —
    _admit_raw's walk, respelled. label_events keeps the admitted list;
    read_timelines also reports the refused count."""
    admitted, refused = _admit_raw(timeline)
    return ([(_utc_z(event["created_at"]), kind, name)
             for event, kind, name in admitted], refused)


def label_events(timeline):
    """[(timestamp, 'labeled'|'unlabeled', label name)] from a GitHub
    issue timeline, in timeline (chronological) order. Anything that is
    not a well-formed label flip is not this module's business; an
    unusable timeline is the fetcher's problem, never this walk's.

    Well-formed means all three: a label flip, carrying a name, and
    carrying a timestamp that reads as one. The third clause is what
    lets every function downstream take ISO-8601 as given, and every
    admitted timestamp is respelled in UTC Z form (_utc_z).

    Silent on purpose: it returns no problems for any of the three
    clauses. read_timelines is the one caller that reports what the
    third clause refused, so no tool can read a timeline and forget to
    (ADR-0090)."""
    return _admit(timeline)[0]


def read_timelines(numbers, run, label, slug="{owner}/{repo}"):
    """({issue number: label events}, problems) for each issue in
    `numbers`, read through the injected gh runner at cli's gh port —
    the one timeline read the gate tools share (ADR-0090).

    An issue whose fetch failed or did not parse is ABSENT from the
    map, never present-and-empty: [] is a history that was read and
    holds nothing, and open_queues tells an unreadable age from an
    unknown one by that difference (#665). Its problem is gh_read's.

    A fetch that succeeds can still carry an otherwise-well-formed
    label flip whose created_at does not read as a timestamp. Admission
    drops it, and this says so as a `<label>: timeline for #N refused`
    problem (#491): the read succeeded, so gh_read said nothing, and a
    dropped `unlabeled` leaves its stay open — a lost rejection for the
    miner, a wrong age for the queues (#740). A nameless or non-flip
    event is not a refusal.

    `label` is the caller's problem-string label ("gd", "rm",
    "dashboard"); `slug` is gh's {owner}/{repo} placeholder unless the
    caller reads another repo."""
    events = {}
    problems = []
    for number in numbers:
        timeline, read_problems = _read_timeline(number, run, label, slug)
        problems.extend(read_problems)
        if timeline is None:
            continue
        admitted, refused = _admit(timeline)
        if refused:
            problems.append(_refusal(label, number, refused))
        events[number] = admitted
    return events, problems


def _read_timeline(number, run, label, slug):
    """(one issue's raw timeline events, pages flattened, or None when
    the fetch failed or did not parse, problems) — the gh read itself."""
    path = f"repos/{slug}/issues/{number}/timeline"
    read = gh_read(["api", path, "--paginate", "--slurp"],
                   f"gh api timeline for #{number}", label=label, run=run)
    if read.value is None:
        return None, list(read.problems)
    return ([event for page in read.value for event in page],
            list(read.problems))


def _refusal(label, number, refused):
    return (f"{label}: timeline for #{number} refused {refused} malformed"
            " timestamp(s)")


def read_labelers(numbers, name, run, label, slug="{owner}/{repo}"):
    """({issue number: login of the actor whose `labeled` event for
    `name` is the timeline's latest}, problems) — the same read and
    admission as read_timelines, kept with each flip's actor.

    The value is None when the timeline holds no admitted labeled event
    for `name`, and "" when that event names no actor. An issue whose
    fetch failed, or whose timeline admission refused any flip, is
    ABSENT with a problem: a dropped flip could be the latest
    application, so a caller deciding WHO applied a label (the dispatch
    plane's owner-only ready label, ADR-0032) must fail closed rather
    than read an earlier actor as the current one."""
    labelers = {}
    problems = []
    for number in numbers:
        timeline, read_problems = _read_timeline(number, run, label, slug)
        problems.extend(read_problems)
        if timeline is None:
            continue
        admitted, refused = _admit_raw(timeline)
        if refused:
            problems.append(_refusal(label, number, refused))
            continue
        actor = None
        for event, kind, flipped in admitted:
            if kind == "labeled" and flipped == name:
                actor = (event.get("actor") or {}).get("login") or ""
        labelers[number] = actor
    return labelers, problems


# GitHub search answers at most 1000 results per query, whatever
# --limit asks for, so a search read windowed any wider would be capped
# silently. At exactly this window a capped search reads as a full one,
# and cli.gh_read reports it.
SEARCH_WINDOW = 1000
# What makes a label a lifecycle label (plane_drift.issue_lifecycle).
LIFECYCLE_PREFIX = "wo:"
# The fields both the digest and the miner read.
ISSUE_FIELDS = "number,title,state,labels,body"
# gh's words for a REST read of a number that is no issue here: never
# one (404) or deleted (410).
ABSENT = re.compile(r"\(HTTP 4(?:04|10)\)$")


def _issue_by_number(number, fields, run, label, slug):
    """(entry, problems) for one issue read by number through the REST
    API, projected to `fields` and spelled as an issue-list entry
    (state upper-cased). entry is None, with no problem, for a number
    the whole-tracker listing would not have held either: no such issue,
    a pull request, or an issue transferred away (answered under another
    number). Any other failure is a problem."""
    operation = f"gh api issue #{number}"
    try:
        out = run(["api", f"repos/{slug}/issues/{number}"])
    except subprocess.CalledProcessError as err:
        if ABSENT.search(detail(err)):
            return None, []
        return None, [f"{label}: {operation} failed: {detail(err)}"]
    except CLI_FAILURES as err:
        return None, [f"{label}: {operation} failed: {detail(err)}"]
    try:
        value = json.loads(out)
    except json.JSONDecodeError as err:
        return None, [f"{label}: {operation} returned unparseable JSON:"
                      f" {err}"]
    if not isinstance(value, dict):
        return None, [f"{label}: {operation} returned"
                      f" {type(value).__name__} where dict was expected"]
    if "pull_request" in value or value.get("number") != number:
        return None, []
    # REST's `url` is the API address; `gh issue list --json url` gives
    # the github.com page, which is what every reader links to.
    spelled = {**value, "state": str(value.get("state") or "").upper(),
               "url": value.get("html_url")}
    return {name: spelled.get(name) for name in fields.split(",")}, []


def read_work_order_issues(numbers, fields, run, label,
                           slug="{owner}/{repo}"):
    """GhResult(listing, problems, truncated): every issue carrying a
    `wo:` label, plus each of `numbers` (the issues breakdown rows
    mirror) that carries none — exactly the entries the reconcile sweep,
    the gate digest, the rejection miner and the dashboard read from
    what used to be one whole-tracker listing, which went red each time
    the tracker outgrew its window.

    Three reads. The repo's live labels, so a `wo:` label outside the
    taxonomy is still searched for (an issue can carry only a label the
    repo has). One search over all of them (GitHub reads comma-separated
    label values as OR). Then each mirrored number the search did not
    return, by number: a mirrored issue that lost its last `wo:` label
    is still one the readers compare. listing is None when any read is
    unusable or a by-number read fails — a missing mirrored issue is a
    finding to reconcile, so a read that may have dropped one must not
    look complete. A full window on either listing read flips
    `truncated` and is the caller's to word, as gh_read's always is."""
    # gh resolves {owner}/{repo} only in an api path; a named repo (the
    # dashboard observes other checkouts) scopes the listings with -R.
    scope = [] if slug == "{owner}/{repo}" else ["-R", slug]
    labels = gh_read(["label", "list", *scope, "--json", "name"],
                     "gh label list", label, run, window=SEARCH_WINDOW)
    if labels.value is None:
        return labels
    lifecycle = sorted({name for name in label_names(labels.value)
                        if name.startswith(LIFECYCLE_PREFIX)})
    listing, problems = [], list(labels.problems)
    truncated = labels.truncated
    if lifecycle:
        query = "label:" + ",".join(f'"{name}"' for name in lifecycle)
        read = gh_read(["issue", "list", *scope, "--state", "all",
                        "--search", query, "--json", fields],
                       "gh issue list", label, run, window=SEARCH_WINDOW)
        if read.value is None:
            return GhResult(None, problems + read.problems, False)
        listing, truncated = list(read.value), truncated or read.truncated
        problems += read.problems
    listed = {entry.get("number") for entry in listing
              if isinstance(entry, dict)}
    for number in sorted(set(numbers) - listed):
        entry, failed = _issue_by_number(number, fields, run, label, slug)
        if failed:
            return GhResult(None, problems + failed, False)
        if entry is not None:
            listing.append(entry)
    return GhResult(listing, problems, truncated)


GateIssues = namedtuple("GateIssues",
                        "listing truncated mirrored events problems")


def read_gate_issues(mirror, run, label):
    """GateIssues for a gate reader's startup: read_work_order_issues
    for the issues the dispatch plane mirrors (`mirror`,
    knowledge_plane.mirror_map), then read_timelines for those it found.
    An unusable listing reads no timelines and answers listing None. A
    full window is the caller's to word (`truncated`). The gate digest
    and the rejection miner share it (two copies until the 2026-10-25
    consolidation)."""
    read = read_work_order_issues(mirror, ISSUE_FIELDS, run, label)
    if read.value is None:
        return GateIssues(None, read.truncated, [], {}, list(read.problems))
    mirrored = sorted(entry["number"] for entry in read.value
                      if entry.get("number") in mirror)
    # A failed timeline read is a problem, never a lost item: the issue
    # stays listed and the next scheduled run re-scans.
    events, problems = read_timelines(mirrored, run, label)
    return GateIssues(read.value, read.truncated, mirrored, events,
                      list(read.problems) + problems)


def completed_stays(events, gate):
    """[(start, end, confirmed)] — every stay in one gate's queue that
    was entered AND left, with `confirmed` true when the gate's pass
    label was applied inside that stay's window: from its start up to
    the gate's next re-entry. So a flip to any other label (rejection,
    block) leaves the stay unconfirmed even when the gate is re-entered
    and passed later.

    A stay ends when its queue label is removed or, for a confirmed stay,
    at its first pass label if that came earlier (ADR-0074, amending
    ADR-0056): ADR-0032's one-lifecycle-label rule is not enforced when
    a human applies a gate label, so an added pass label must not leave
    the stay running until the next automated flip.

    This is the invariant made executable. A completed stay is confirmed
    or it is not, so the digest and the miner partition one list between
    them — every stay a passage there or a rejection here, never both —
    instead of agreeing by two hand-written window tests. An open stay
    is absent: still waiting, neither passage nor rejection."""
    confirmations = [ts for ts, kind, name in events
                     if kind == "labeled" and name == gate.passed]
    # Every queue-label entry, the open stay's included: a pass label
    # beside an open re-entered stay belongs to that stay, never to the
    # completed one before it. Compared as parsed instants, so a
    # timestamp that is not GitHub's `...Z` form still orders.
    entries = [ts for ts, kind, name in events
               if kind == "labeled" and name == gate.queue]
    stays = []
    entered = None
    for ts, kind, name in events:
        if name != gate.queue:
            continue
        if kind == "labeled":
            entered = ts
        elif kind == "unlabeled" and entered is not None:
            stays.append((entered, ts))
            entered = None
    completed = []
    for start, end in stays:
        begun = _parse_ts(start)
        next_start = next((_parse_ts(ts) for ts in entries
                           if _parse_ts(ts) > begun), None)
        inside = [ts for ts in confirmations
                  if begun <= _parse_ts(ts)
                  and (next_start is None or _parse_ts(ts) < next_start)]
        # A confirmed stay ends at its pass label when that came first
        # (ADR-0074): a pass label ADDED beside the queue label leaves the
        # queue label on until some later flip strips it, and that gap is
        # automation's, not the human's wait.
        completed.append((start, min([end, *inside], key=_parse_ts), bool(inside)))
    return completed


def gate_passages(events):
    """[(gate, waited seconds, passed at, stay started at)] — every
    confirmed gate passage in one issue's label history, in pipeline then
    stay order. Re-entering a gate yields one passage per confirmed stay.
    The start is the queue label's add time, which no change to how the
    walk computes the end can move — the ledger keys on it (ADR-0132)."""
    return [(gate.name, waited_seconds(start, end), end, start)
            for gate in GATES
            for start, end, confirmed in completed_stays(events, gate)
            if confirmed]


def gate_rejections(events):
    """[(gate, stay ended at)] — the completed stays the pass label
    never confirmed, oldest first. The complement of gate_passages over
    the same list."""
    return sorted(((gate.name, end)
                   for gate in GATES
                   for _, end, confirmed in completed_stays(events, gate)
                   if not confirmed),
                  key=lambda item: item[1])


def waiting_since(events, queue_label):
    """The timestamp the issue's current stay in `queue_label` began, or
    None when the label is not currently applied (or the labeled event
    fell off the fetched timeline — the item still lists, just without an
    age)."""
    since = None
    for ts, kind, name in events:
        if name != queue_label:
            continue
        since = ts if kind == "labeled" else None
    return since


# One open issue waiting at a gate: the listing entry as the caller read
# it (title, url and the rest are the caller's to render), whole seconds
# waited, and whether its timeline was read at all. `aged` is False only
# for an unread timeline, which is a different fact from a `waited` of
# None on a read one (no arrival at this gate) — so it is named, never
# inferred (#665).
Waiting = namedtuple("Waiting", "issue waited aged")


def _waits_at(entry, mirror, queue_label):
    return entry.get("number") in mirror and \
        queue_label in label_names(entry)


def waiting_issues(open_issues, mirror):
    """The numbers of the open mirrored issues waiting at any gate,
    ascending — the timelines a caller that reads only what it ages must
    read before open_queues can age them. Same membership as
    open_queues, by construction."""
    return sorted({entry["number"] for entry in open_issues
                   for gate in GATES
                   if _waits_at(entry, mirror, gate.queue)})


def open_queues(open_issues, mirror, events_by_issue, now):
    """[(Gate, [Waiting])] for all three gates in pipeline order, each
    listing the open mirrored issues carrying its queue label, issue
    number ascending, aged from the current stay's labeled event at the
    aware datetime `now` — the queues gate_digest posts and dashboard
    renders, built once (ADR-0090).

    `open_issues` is the caller's already-filtered open listing.
    `events_by_issue` is read_timelines' map: an absent issue was not
    read (aged False), a present one with no arrival has no age."""
    queues = []
    for gate in GATES:
        items = []
        for entry in sorted(open_issues,
                            key=lambda e: e.get("number") or 0):
            if not _waits_at(entry, mirror, gate.queue):
                continue
            events = events_by_issue.get(entry["number"])
            since = waiting_since(events or [], gate.queue)
            waited = (waited_seconds(since, now.isoformat())
                      if since else None)
            items.append(Waiting(entry, waited, events is not None))
        queues.append((gate, items))
    return queues
