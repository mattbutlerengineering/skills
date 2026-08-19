"""human_gates: what the three human gates are, and how to read one
issue's label history against them (ADR-0056).

The gates are the factory's only human decision points (ADR-0033;
CONTEXT.md: PRD approval, blueprint/ADR approval, PR merge), so their
queues live on the work orders' mirrored issues as `wo:` lifecycle
labels (ADR-0032, ADR-0035): `wo:draft` waits at the PRD gate,
`wo:prd-approved` at the blueprint gate, `wo:needs-review` at the merge
gate. This module owns that vocabulary and the walk over it — the
label-event stream, the completed-stay partition, and the current
stay's start.

Its callers are thin: gate_digest.py keeps the confirmed stays as
latency rows, rejection_mining.py harvests the rest, dashboard.py ages
the open ones, and gates.py's detector J asks which labels the gates
name. They differ in what a stay MEANS to them, never in what a stay
IS, which is the whole reason this is one module and their fetches,
posts and compositions are not.

Pure by construction: no gh, no ledger, no filesystem, no clock. Events
in, gate facts out, testable with a literal list — which is why the
timeline fetch that produces those events stays with the tools that own
its failure meaning (ADR-0051).
"""
from collections import namedtuple
from datetime import datetime

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
    label. Detector J's one reach into this module
    (gates.LABEL_DECLARERS): the taxonomy must carry all of them, and
    the detector should not know how many label fields a row has."""
    return {label for gate in GATES for label in (gate.queue, gate.passed)}


def _parse_ts(iso):
    """GitHub timestamps end in Z; fromisoformat only accepts that from
    3.11, and local runs may be older."""
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def waited_seconds(start, end):
    """Whole seconds between two GitHub timestamps."""
    return int((_parse_ts(end) - _parse_ts(start)).total_seconds())


def label_events(timeline):
    """[(timestamp, 'labeled'|'unlabeled', label name)] from a GitHub
    issue timeline, in timeline (chronological) order. Anything that is
    not a well-formed label flip is not this module's business; an
    unusable timeline is the fetcher's problem, never this walk's."""
    events = []
    for event in timeline:
        kind = event.get("event")
        if kind not in ("labeled", "unlabeled"):
            continue
        name = (event.get("label") or {}).get("name")
        ts = event.get("created_at")
        if name and ts:
            events.append((ts, kind, name))
    return events


def completed_stays(events, gate):
    """[(start, end, confirmed)] — every stay in one gate's queue that
    was entered AND left, with `confirmed` true when the gate's pass
    label was applied inside that stay's window: from its start up to
    the gate's next re-entry. So a flip to any other label (rejection,
    block) leaves the stay unconfirmed even when the gate is re-entered
    and passed later.

    This is the invariant made executable. A completed stay is confirmed
    or it is not, so the digest and the miner partition one list between
    them — every stay a passage there or a rejection here, never both —
    instead of agreeing by two hand-written window tests. An open stay
    is absent: still waiting, neither passage nor rejection."""
    confirmations = [ts for ts, kind, name in events
                     if kind == "labeled" and name == gate.passed]
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
    for index, (start, end) in enumerate(stays):
        next_start = (stays[index + 1][0] if index + 1 < len(stays)
                      else None)
        confirmed = any(
            start <= ts and (next_start is None or ts < next_start)
            for ts in confirmations)
        completed.append((start, end, confirmed))
    return completed


def gate_passages(events):
    """[(gate, waited seconds, passed at)] — every confirmed gate
    passage in one issue's label history, in pipeline then stay order.
    Re-entering a gate yields one passage per confirmed stay."""
    return [(gate.name, waited_seconds(start, end), end)
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
