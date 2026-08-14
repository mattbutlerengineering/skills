#!/usr/bin/env python3
"""rejection_mining: the weekly toolsmith-queue harvest (PRD-0001
§User stories, WO-0018).

The toolsmith charter's Mine stage wants the correction stream in one
place before any rule is written. Two streams exist on the dispatch
plane, and this tool reads both through the injected gh runner (same
seam as gate_digest.py, so tests never touch the network):

- gate rejections — a `wo:` queue stay that ended WITHOUT the gate's
  pass label. These are exactly the stays gate_digest.gate_passages
  deliberately skips: a flip to wo:failed / wo:blocked records no
  latency row there, so this tool is where those flips finally land.
- PR change-requests — CHANGES_REQUESTED reviews on the work orders'
  PRs, joined to their WO through the `Closes #N` grammar
  (knowledge_plane.CLOSES_TOKEN).

The harvest is upserted as one pinned, marker-tagged queue issue —
the gate digest's tracker idiom (ADR-0035): created and pinned on
first run, edited in place every week after. Recurrence counts lead
each entry because the charter counts recurrences before writing a
rule — one rejection is an anecdote — and the evidence is quoted
(review bodies excerpted), never summarized into existence.

Conventions match gate_digest.py: functions return rm:-prefixed problem
strings; the CLI prints them and exits nonzero.

  python3 rejection_mining.py mine
        Harvest gate rejections and change-requested reviews for the
        mirrored work orders, then create-or-update the pinned
        toolsmith-queue issue.
"""
import os
import sys
from datetime import datetime, timezone

from cli import CLI_FAILURES as GH_FAILURES
from cli import detail as gh_detail
from cli import full_window, gh_json, gh_runner, report, write_outputs
from gate_digest import GATES, label_events, mirror_map
from knowledge_plane import CLOSES_TOKEN, repo_root

# First line of the queue issue's body — how the weekly run finds its
# own issue among the open ones (the gate digest's marker idiom).
MARKER = "<!-- factory-toolsmith-queue -->"
QUEUE_TITLE = "Toolsmith queue — mined rejections"

# gh truncates a windowed listing silently; the window size is declared
# once so the full-window report and the --limit can never drift apart.
LIST_WINDOW = 1000
ISSUE_ARGS = ("issue", "list", "--state", "all", "--json",
              "number,title,state,labels,body", "--limit",
              str(LIST_WINDOW))
PR_ARGS = ("pr", "list", "--state", "all", "--json",
           "number,state,body,reviews", "--limit", str(LIST_WINDOW))


def gate_rejections(events):
    """[(gate, stay ended at)] — every completed queue stay in one
    issue's label history that the gate's pass label never confirmed.
    The confirmation window matches gate_digest.gate_passages — from
    the stay's start up to the gate's next re-entry — so the two tools
    partition completed stays between them: every stay is a passage
    there or a rejection here, never both. An open stay is still
    waiting, not rejected."""
    rejections = []
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
        entries = [start for start, _ in stays]
        for index, (start, left) in enumerate(stays):
            window_end = entries[index + 1] if index + 1 < len(entries) \
                else None
            confirmed = any(
                start <= ts and (window_end is None or ts < window_end)
                for ts in confirmations)
            if not confirmed:
                rejections.append((gate, left))
    return sorted(rejections, key=lambda item: item[1])


def _excerpt(body):
    """The first line of a review body, or a stated absence — the quote
    is the evidence, so an empty one must be visibly empty rather than
    a blank that reads as a rendering bug."""
    first = (body or "").strip().splitlines()
    return first[0].strip() if first else "(no comment)"


def change_requests(listing, mirror):
    """[(wo, pr number, excerpt)] — every CHANGES_REQUESTED review on a
    PR whose Closes link names a mirrored work order. A PR closing no
    mirrored issue is not factory output and is skipped."""
    mined = []
    for entry in listing:
        number = entry.get("number")
        orders = [mirror[int(ref)]
                  for ref in CLOSES_TOKEN.findall(entry.get("body") or "")
                  if int(ref) in mirror]
        if not isinstance(number, int) or not orders:
            continue
        for review in entry.get("reviews") or []:
            if not isinstance(review, dict) or \
                    (review.get("state") or "").upper() != \
                    "CHANGES_REQUESTED":
                continue
            for wo in orders:
                mined.append((wo, number, _excerpt(review.get("body"))))
    return mined


def compose_queue(rejections_by_wo, requests_by_wo, day):
    """The queue issue's body: marker first, then one section per work
    order with corrections, most corrections first (recurrence is the
    rule-writing signal), each with its quoted evidence line."""
    orders = sorted(
        set(rejections_by_wo) | set(requests_by_wo),
        key=lambda wo: (-(len(rejections_by_wo.get(wo, ())) +
                          len(requests_by_wo.get(wo, ()))), wo))
    lines = [MARKER, f"{QUEUE_TITLE} — {day}", ""]
    if not orders:
        lines.append("No corrections mined.")
    for wo in orders:
        rejections = rejections_by_wo.get(wo, [])
        requests = requests_by_wo.get(wo, [])
        lines.append(f"- **{wo}** — "
                     f"{len(rejections) + len(requests)} correction(s)")
        for gate, ended in rejections:
            lines.append(f"  - {gate} gate rejection at {ended}")
        for number, excerpt in requests:
            lines.append(f'  - PR #{number} change-request: "{excerpt}"')
    lines += ["", "Updated weekly by rejection mining (WO-0018);"
              " recurrences are counted before a rule is written —"
              " one rejection is an anecdote (toolsmith charter,"
              " Mine stage)."]
    return "\n".join(lines) + "\n"


def _timelines(mirrored, run, problems):
    """{issue number: label events} for every mirrored issue gh can
    answer for; a failed fetch is a problem, never a silently thinner
    harvest — the queue still posts, and next week's re-scan of the
    same history catches up (the upsert is idempotent)."""
    events = {}
    for number in mirrored:
        path = f"repos/{{owner}}/{{repo}}/issues/{number}/timeline"
        try:
            pages, suffix = gh_json(["api", path, "--paginate",
                                     "--slurp"], run, expect=list)
        except GH_FAILURES as err:
            problems.append(f"rm: gh api timeline for #{number} failed:"
                            f" {gh_detail(err)}")
            continue
        if suffix:
            problems.append(f"rm: gh api timeline for #{number} {suffix}")
            continue
        events[number] = label_events(
            [event for page in pages for event in page])
    return events


def _change_requests(mirror, run, problems):
    """change_requests over a live pr listing; a failed listing is a
    problem plus an empty stream, never a lost harvest — the gate
    rejections still post."""
    try:
        listing, suffix = gh_json(list(PR_ARGS), run, expect=list)
    except GH_FAILURES as err:
        problems.append(f"rm: gh pr list failed: {gh_detail(err)}")
        return []
    if suffix:
        problems.append(f"rm: gh pr list {suffix}")
        return []
    window = full_window(listing, LIST_WINDOW)
    if window:
        problems.append(f"rm: gh pr list {window}")
    return change_requests(listing, mirror)


def _post_queue(existing, body, run, problems):
    """Create-or-update the queue issue — gate_digest._post_digest's
    contract: the edit path re-pins and tolerates the refusal (a human
    unpin heals next week), the create path's pin failure IS a
    problem."""
    if existing is not None:
        try:
            run(["issue", "edit", str(existing), "--body", body])
        except GH_FAILURES as err:
            problems.append(f"rm: gh issue edit {existing} failed:"
                            f" {gh_detail(err)}")
            return
        try:
            run(["issue", "pin", str(existing)])
        except GH_FAILURES:
            pass
        return
    try:
        url = run(["issue", "create", "--title", QUEUE_TITLE,
                   "--body", body]).strip()
    except GH_FAILURES as err:
        problems.append(f"rm: gh issue create failed: {gh_detail(err)}")
        return
    try:
        run(["issue", "pin", url.rsplit("/", 1)[-1]])
    except GH_FAILURES as err:
        problems.append(f"rm: gh issue pin failed: {gh_detail(err)}")


def run_mine(root, run=gh_runner, clock=None):
    """(outputs, problems) for the mine command: harvest both correction
    streams for the mirrored work orders and create-or-update the
    pinned queue issue. outputs carries a one-line reason with the
    candidate and correction counts."""
    clock = clock or (lambda: datetime.now(timezone.utc))
    now = clock()
    mirror = mirror_map(root)
    try:
        listing, suffix = gh_json(list(ISSUE_ARGS), run, expect=list)
    except GH_FAILURES as err:
        return {}, [f"rm: gh issue list failed: {gh_detail(err)}"]
    if suffix:
        return {}, [f"rm: gh issue list {suffix}"]
    problems = []
    window = full_window(listing, LIST_WINDOW)
    if window:
        problems.append(f"rm: gh issue list {window}")

    mirrored = sorted(entry["number"] for entry in listing
                      if entry.get("number") in mirror)
    events_by_issue = _timelines(mirrored, run, problems)
    rejections_by_wo = {}
    for number, events in sorted(events_by_issue.items()):
        for rejection in gate_rejections(events):
            rejections_by_wo.setdefault(mirror[number],
                                        []).append(rejection)
    requests_by_wo = {}
    for wo, number, excerpt in _change_requests(mirror, run, problems):
        requests_by_wo.setdefault(wo, []).append((number, excerpt))

    body = compose_queue(rejections_by_wo, requests_by_wo,
                         now.date().isoformat())
    open_issues = [entry for entry in listing
                   if (entry.get("state") or "").upper() == "OPEN"]
    existing = next((entry["number"] for entry in
                     sorted(open_issues, key=lambda e: e["number"])
                     if (entry.get("body") or "").startswith(MARKER)),
                    None)
    _post_queue(existing, body, run, problems)

    candidates = set(rejections_by_wo) | set(requests_by_wo)
    corrections = sum(len(v) for v in rejections_by_wo.values()) + \
        sum(len(v) for v in requests_by_wo.values())
    return ({"reason": f"rm: {len(candidates)} candidate WO(s),"
                       f" {corrections} correction(s) mined"},
            problems)


def main(argv, env=None, root=None, run=gh_runner, clock=None):
    env = os.environ if env is None else env
    root = root or repo_root()
    if argv == ["mine"]:
        outputs, problems = run_mine(root, run=run, clock=clock)
        write_outputs(env, outputs)
        if outputs.get("reason"):
            print(outputs["reason"])
    else:
        print(__doc__.strip())
        return 2
    return report("rejection_mining", problems)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
