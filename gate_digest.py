#!/usr/bin/env python3
"""gate_digest: the daily gate-queue digest and gate-latency capture
(PRD-0001 user story 4, WO-0017; ADR-0041).

The three gates are human decision points (CONTEXT.md: PRD approval,
blueprint/ADR approval, PR merge), so their queues live on the work
orders' mirrored issues as `wo:` lifecycle labels (ADR-0032, ADR-0035):
`wo:draft` waits at the PRD gate, `wo:prd-approved` at the blueprint
gate, `wo:needs-review` at the merge gate. This tool reads those queues
and each mirrored issue's label timeline through an injected gh runner
(same seam as validator.py, so tests never touch the network), then:

- posts the digest — one marker-tagged issue, created and pinned on
  first run, edited in place every day after (ADR-0035: the digest posts
  to the tracker);
- captures gate latency — every confirmed passage (queue label removed
  AND the gate's pass label applied) becomes a $0 gate-latency row in
  docs/factory/costs.jsonl via cost_ledger.gate_entry (ADR-0041),
  deduped against rows already recorded so a daily re-scan never
  double-records.

The workflow (.github/workflows/gate-digest.yml) owns the one git
mutation — committing the appended ledger rows — signalled through the
`changed` step output; everything gh-shaped stays here, unit-tested.
Conventions match validator.py: functions return gd:-prefixed problem
strings; the CLI prints them and exits nonzero.

  python3 gate_digest.py daily
        Read the gate queues, append new gate-latency rows to the cost
        ledger, and create-or-update the pinned digest issue. Writes
        `changed` ('true'/'false': did the ledger gain rows?) to
        $GITHUB_OUTPUT for the workflow's commit step.
"""
import json
import os
import sys
from datetime import datetime, timezone

import cost_ledger
from cli import CLI_FAILURES as GH_FAILURES
from cli import detail as gh_detail
from cli import gh_runner
from cli import write_outputs
from knowledge_plane import (breakdown_files, repo_root, row_tracker_issue,
                             row_work_order)

# The three gates in pipeline order: ledger gate name, the wo: label an
# issue carries while waiting, the label whose application confirms the
# pass (a flip to anything else — wo:blocked, wo:failed — is not a
# passage), and the digest heading.
GATES = (
    ("prd", "wo:draft", "wo:prd-approved", "PRD gate"),
    ("blueprint", "wo:prd-approved", "wo:blueprint-approved",
     "Blueprint gate"),
    ("merge", "wo:needs-review", "wo:merged", "Merge gate"),
)

# First line of the digest issue's body — how the daily run finds its own
# issue among the open ones (same idiom as validator.py's REVIEW_MARKER).
DIGEST_MARKER = "<!-- factory-gate-digest -->"
DIGEST_TITLE = "Factory gate queue"


def _parse_ts(iso):
    """GitHub timestamps end in Z; fromisoformat only accepts that from
    3.11, and local runs may be older."""
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def _seconds(start, end):
    return int((_parse_ts(end) - _parse_ts(start)).total_seconds())


def label_events(timeline):
    """[(timestamp, 'labeled'|'unlabeled', label name)] from a GitHub
    issue timeline, in timeline (chronological) order. Anything that is
    not a well-formed label flip is not this tool's business."""
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


def gate_passages(events):
    """[(gate, waited seconds, passed at)] — every confirmed gate passage
    in one issue's label history. A passage needs the queue label applied
    then removed AND the gate's pass label applied within that stay —
    from the wait's start up to the gate's next re-entry — so a flip to
    any other label (rejection, block) records nothing even when the
    gate is re-entered and passed later. Re-entering a gate yields one
    passage per confirmed stay."""
    passages = []
    for gate, queue, pass_label, _ in GATES:
        confirmations = [ts for ts, kind, name in events
                         if kind == "labeled" and name == pass_label]
        stays = []
        entered = None
        for ts, kind, name in events:
            if name != queue:
                continue
            if kind == "labeled":
                entered = ts
            elif kind == "unlabeled" and entered is not None:
                stays.append((entered, ts))
                entered = None
        for index, (start, end) in enumerate(stays):
            next_start = (stays[index + 1][0] if index + 1 < len(stays)
                          else None)
            if any(c >= start and (next_start is None or c < next_start)
                   for c in confirmations):
                passages.append((gate, _seconds(start, end), end))
    return passages


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


def _format_wait(seconds):
    days, rest = divmod(seconds, 86400)
    hours = rest // 3600
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h"
    return "<1h"


def compose_digest(queues, as_of):
    """The digest issue body: marker first (how the next run finds it),
    then one section per gate listing every waiting item and how long it
    has waited. Deterministic text, same discipline as
    cost_report.compose_report. queues is [(heading, queue label,
    [(issue number, title, waited seconds or None)])] — the mirrored
    issue's title already leads with its WO token, so the line never
    repeats it."""
    lines = [DIGEST_MARKER, f"# {DIGEST_TITLE} — {as_of}"]
    for heading, queue_label, items in queues:
        lines += ["", f"## {heading} ({queue_label})"]
        if not items:
            lines.append("- (empty)")
        for number, title, waited in items:
            item = f"- #{number} {title}"
            if waited is not None:
                item += f" — waiting {_format_wait(waited)}"
            lines.append(item)
    lines += ["", "Updated daily by the gate digest (WO-0017); a passage"
              " lands a gate-latency row in "
              f"{cost_ledger.COST_LEDGER} (ADR-0041)."]
    return "\n".join(lines) + "\n"


LIST_ARGS = ("issue", "list", "--state", "all", "--json",
             "number,title,state,labels,body", "--limit", "1000")


def mirror_map(root):
    """{tracker issue number: WO token} from the breakdown rows. The
    knowledge plane is authoritative and the mirror one-way (ADR-0032):
    a row with no (tracker: #N) simply is not in any queue, and an issue
    with no row is not a work order."""
    mapping = {}
    for _, lines in breakdown_files(root):
        for line in lines:
            wo = row_work_order(line)
            number = row_tracker_issue(line)
            if wo and number is not None:
                mapping[number] = wo
    return mapping


def _issue_labels(entry):
    return [(label.get("name") or "") for label in entry.get("labels") or []]


def _timelines(mirrored, run, problems):
    """{issue number: label events} for every mirrored issue gh can
    answer for; a failed fetch is a problem, never a lost queue item
    (the digest still lists the issue, just without an age, and the next
    daily run re-scans — dedup makes the catch-up safe)."""
    events = {}
    for number in mirrored:
        path = f"repos/{{owner}}/{{repo}}/issues/{number}/timeline"
        try:
            pages = json.loads(run(["api", path, "--paginate", "--slurp"]))
        except GH_FAILURES as err:
            problems.append(f"gd: gh api timeline for #{number} failed:"
                            f" {gh_detail(err)}")
            continue
        events[number] = label_events(
            [event for page in pages for event in page])
    return events


def _capture_latency(root, mirror, events_by_issue, problems):
    """Append every not-yet-recorded gate passage to the cost ledger and
    return the new rows. run_id keys the passage timestamp, so a daily
    re-scan of the same history appends nothing."""
    existing, ledger_problems = cost_ledger.read(root)
    problems.extend(ledger_problems)
    recorded = {(entry["wo"], entry["run_id"]) for entry in existing}
    new_rows = []
    for number, events in sorted(events_by_issue.items()):
        for gate, waited, passed_at in gate_passages(events):
            row = cost_ledger.gate_entry(mirror[number], gate, waited,
                                         passed_at)
            if (row["wo"], row["run_id"]) not in recorded:
                new_rows.append(row)
    for row in new_rows:
        cost_ledger.append(root, row)
    return new_rows


def _queues(mirror, open_issues, events_by_issue, now):
    """[(heading, queue label, items)] for compose_digest: the open
    mirrored issues currently carrying each gate's queue label, oldest
    issue first, aged from the current stay's labeled event when the
    timeline yielded one."""
    queues = []
    for _, queue_label, _, heading in GATES:
        items = []
        for entry in sorted(open_issues, key=lambda e: e["number"]):
            number = entry["number"]
            if number not in mirror or \
                    queue_label not in _issue_labels(entry):
                continue
            since = waiting_since(events_by_issue.get(number, []),
                                  queue_label)
            waited = _seconds(since, now.isoformat()) if since else None
            items.append((number, entry.get("title") or "", waited))
        queues.append((heading, queue_label, items))
    return queues


def _post_digest(digest, body, run, problems):
    """Create-or-update the digest issue. The edit path re-pins and
    tolerates the refusal: re-pinning a pinned issue fails, and gh gives
    no cheap way to tell that steady state from a real one — the retry
    exists so a human unpin heals on the next daily run instead of
    rotting. The create path's pin failure IS a problem (nothing else
    would ever retry a digest that was born unpinned and stayed so)."""
    if digest is not None:
        try:
            run(["issue", "edit", str(digest), "--body", body])
        except GH_FAILURES as err:
            problems.append(f"gd: gh issue edit {digest} failed:"
                            f" {gh_detail(err)}")
            return
        try:
            run(["issue", "pin", str(digest)])
        except GH_FAILURES:
            pass
        return
    try:
        url = run(["issue", "create", "--title", DIGEST_TITLE,
                   "--body", body]).strip()
    except GH_FAILURES as err:
        problems.append(f"gd: gh issue create failed: {gh_detail(err)}")
        return
    try:
        run(["issue", "pin", url.rsplit("/", 1)[-1]])
    except GH_FAILURES as err:
        problems.append(f"gd: gh issue pin failed: {gh_detail(err)}")


def run_daily(root, run=gh_runner, clock=None):
    """(outputs, problems) for the daily command: capture new gate
    latency into the cost ledger, then create-or-update the pinned
    digest — the rows are the data half of the work order, the digest
    only points at them. outputs carries `changed` ('true' when ledger
    rows were appended — the workflow's cue to commit) and a one-line
    reason."""
    clock = clock or (lambda: datetime.now(timezone.utc))
    now = clock()
    mirror = mirror_map(root)
    try:
        listing = json.loads(run(list(LIST_ARGS)))
    except GH_FAILURES as err:
        return ({"changed": "false"},
                [f"gd: gh issue list failed: {gh_detail(err)}"])
    problems = []
    mirrored = sorted(entry["number"] for entry in listing
                      if entry.get("number") in mirror)
    events_by_issue = _timelines(mirrored, run, problems)
    new_rows = _capture_latency(root, mirror, events_by_issue, problems)

    open_issues = [entry for entry in listing
                   if (entry.get("state") or "").upper() == "OPEN"]
    queues = _queues(mirror, open_issues, events_by_issue, now)
    body = compose_digest(queues, now.date().isoformat())
    digest = next((entry["number"] for entry in
                   sorted(open_issues, key=lambda e: e["number"])
                   if (entry.get("body") or "").startswith(DIGEST_MARKER)),
                  None)
    _post_digest(digest, body, run, problems)

    waiting = sum(len(items) for _, _, items in queues)
    return ({"changed": "true" if new_rows else "false",
             "reason": f"gd: {waiting} item(s) waiting,"
                       f" {len(new_rows)} new gate-latency row(s)"},
            problems)


def main(argv, env=None, root=None, run=gh_runner, clock=None):
    env = os.environ if env is None else env
    root = root or repo_root()
    if argv == ["daily"]:
        outputs, problems = run_daily(root, run=run, clock=clock)
        write_outputs(env, outputs)
        if outputs.get("reason"):
            print(outputs["reason"])
    else:
        print(__doc__.strip())
        return 2
    for problem in problems:
        print(problem)
    print(f"gate_digest: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
