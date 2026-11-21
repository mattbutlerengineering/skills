#!/usr/bin/env python3
"""work-queue: plan a batch of work orders to run in parallel.

implement-queue's work-order planner under `source: work-orders`
(ADR-0127, which retired the `work-queue` skill; ADR-0032 two planes). It COMPUTES and prices a batch; it never dispatches, never
labels, never merges — the skill runs the agents, and a human merges the
PRs (ADR-0033 gate 3). Same compute/mutate split as cost_report.py.

  python3 tools/work_queue.py plan         the batch, as a report
  python3 tools/work_queue.py plan --json  the same batch, machine-readable

A work order is eligible only when BOTH planes agree (ADR-0032: the
dispatch plane never runs ahead of the knowledge plane):

  knowledge plane  an unchecked breakdown row whose every `blocked by:`
                   edge is already checked off
  dispatch plane   its mirrored issue carrying wo:ready-for-agent — the
                   label the repo OWNER applies, which is what makes this
                   queue opt-in rather than "everything not done yet". The
                   latest labeled event's actor is checked against the
                   repo owner (assembler.actor_is_owner); anyone else's
                   label is inert, and an unreadable labeler fails closed

Batch size is factory.json's wip_cap minus the orders already in flight
(open issues on wo:in-progress), and the batch is priced from each row's
`size:` band against month-to-date ledger spend plus the in-flight orders'
budgets and monthly_cap_usd (ADR-0034), so an over-cap batch is refused
BEFORE any agent is paid for.

Conventions match lint.py/gates.py: functions return label-prefixed
problem strings; the CLI prints them and exits nonzero.
"""
import json
import sys
from datetime import datetime, timezone

import assembler
import cost_ledger
import factory_config
from cli import gh_read, gh_runner, label_names, report
from human_gates import read_labelers
from knowledge_plane import repo_root, work_orders
from validator import CLAIM_LABEL

# The ready label is assembler's (it is the one detector J reads), so the
# listing cannot ask for a label the dispatch plane does not apply.
LIST_ARGS = ["issue", "list", "--label", assembler.READY_LABEL,
             "--state", "open", "--json", "number,labels"]
# The claim label is validator's (the dispatch legs write it, ADR-0045):
# an order on it is in flight, holding a wip slot and budgeted money the
# ledger has not recorded yet.
IN_FLIGHT_ARGS = ["issue", "list", "--label", CLAIM_LABEL,
                  "--state", "open", "--json", "number"]
# Why a ready issue whose labeler cannot be established is held back.
UNKNOWN_LABELER = (f"carries {assembler.READY_LABEL}, but who applied it"
                   " could not be read — held back until it can be"
                   " (ADR-0032)")
# The repository variable naming the owner login for an org-owned repo
# (#2105); assembler.yml reads it as vars.FACTORY_OWNER_LOGIN.
OWNER_VARIABLE = "FACTORY_OWNER_LOGIN"
# How far back the ready listing can see. cli.gh_read owns the window —
# the limit it sends gh and the truncation it reports are the same
# number — so it can only be typed once, and the duplicate literal this
# constant used to disagree with has nowhere left to live.
LIST_WINDOW = 100
# Cheapest band first: a batch that spends its cap on one L order drains
# less queue than the same money across three S ones, and a cheap order
# that fails costs less to have tried.
SIZE_ORDER = {"S": 0, "M": 1, "L": 2}


def _utcnow():
    return datetime.now(timezone.utc)


def rows(root):
    """{work order: row facts} for every breakdown row.

    Read from knowledge_plane.work_orders' WO index (issue #885), so a
    duplicated row resolves to the one the dispatcher resolves — the
    first — and carries the same `clashes` it refuses on. Nothing
    downstream re-reads or re-parses a row.
    """
    return rows_and_problems(root)[0]


def rows_and_problems(root):
    """(rows, read problems): rows() plus every breakdown that could not
    be read — "nothing is ready" and "I could not read the plan" must not
    look the same. Clashes are not here: each rides its row's deferral."""
    fields = ("wo", "done", "size", "issue", "blockers", "unreadable",
              "clashes")
    index, problems = work_orders(root)
    found = {wo: {**{field: row[field] for field in fields},
                  "where": f"{row['path'].relative_to(root)}"
                           f":{row['lineno']}"}
             for wo, row in index["wo"].items()}
    return found, [f"wq: {p}" for p in problems
                   if p.startswith("cannot read")]


def eligible(found, ready_issues, held=None, in_flight=frozenset()):
    """PURE: ([candidate rows], [why each other open row is not one]).

    Reports the near-misses deliberately. A queue that just says "nothing
    to do" is indistinguishable from one that is mis-wired, and this queue
    has two planes to disagree about — saying WHICH plane holds a work
    order back is most of its value.

    `held` maps a ready issue to why its label does not count (owner_holds:
    not the owner's, or a labeler nobody could read); `in_flight` is the
    issues already on the claim label.
    """
    held = held or {}
    candidates, deferred = [], []
    for wo, row in sorted(found.items()):
        if row["clashes"]:
            # Checked off or not, the dispatcher refuses a row another row
            # duplicates (issue #885) — the clash is what holds it back.
            deferred.extend(f"{wo}: {clash}" for clash in row["clashes"])
            continue
        if row["done"]:
            continue
        # The blocker predicate is the dispatcher's own, so the planner
        # and assembler.yml's labeled-event path cannot drift apart.
        blocked = assembler.held_by_blockers(row, found)
        if blocked:
            deferred.append(f"{wo}: {blocked}")
        elif row["issue"] is None:
            deferred.append(f"{wo}: its row carries no (tracker: #N) mirror,"
                            " so no issue can carry the ready label")
        elif row["issue"] in in_flight:
            # Before the ready test: a claimed order has left the ready
            # label by design, and "no open issue carries it" would send
            # the owner to re-arm an order that is already running.
            deferred.append(f"{wo}: issue #{row['issue']} is already in"
                            f" flight on {CLAIM_LABEL}")
        elif row["issue"] not in ready_issues:
            # Says only what the listing proves. It covers OPEN issues, so
            # a miss means "no open issue #N carries the label" — which is
            # ALSO how a closed issue looks, and telling someone to label a
            # closed issue is advice that cannot work. The reconcile sweep
            # owns diagnosing that drift; this line points at it instead of
            # fetching the whole tracker to duplicate it.
            deferred.append(f"{wo}: no open issue #{row['issue']} carries"
                            f" {assembler.READY_LABEL} — the owner applies"
                            " that label, and it does nothing on a closed issue; the"
                            " reconcile sweep reports a row whose issue was"
                            " closed")
        elif row["issue"] in held:
            deferred.append(f"{wo}: issue #{row['issue']}"
                            f" {held[row['issue']]}")
        else:
            candidates.append(row)
    return candidates, deferred


def priced(candidates, config):
    """PURE: (candidates with a `budget`, problems), cheapest band first.

    A row whose size the budget table does not cover is dropped with its
    config: problem rather than run at an unknown price — ADR-0034's
    fail-closed rule, applied before the money is spent instead of after.
    """
    out, problems = [], []
    for row in candidates:
        budget, trouble = factory_config.resolve_budget(row["size"], config)
        if trouble:
            problems += [f"wq: {row['wo']} ({row['where']}) {t}"
                         for t in trouble]
            continue
        out.append(dict(row, budget=budget))
    return sorted(out, key=lambda r: (SIZE_ORDER.get(r["size"], 3),
                                      r["wo"])), problems


def in_flight_budget(found, in_flight, config):
    """PURE: (dollars budgeted for the orders already in flight,
    problems). Each in-flight issue is priced from its mirrored row's
    `size:` band, the same table a candidate is priced from; an issue no
    row mirrors, or a band the table does not cover, is a problem — an
    unknown committed spend is not a zero one (ADR-0034, fail closed)."""
    by_issue = {row["issue"]: row for row in found.values()
                if row["issue"] is not None}
    total, problems = 0.0, []
    for number in sorted(in_flight):
        row = by_issue.get(number)
        if row is None:
            problems.append(f"wq: issue #{number} is on {CLAIM_LABEL} but"
                            " no breakdown row mirrors it, so its budget"
                            " is unknown")
            continue
        budget, trouble = factory_config.resolve_budget(row["size"], config)
        problems += [f"wq: {row['wo']} ({row['where']}) {t}"
                     for t in trouble]
        if not trouble:
            total += budget
    return total, problems


def plan_batch(found, ready_issues, config, spent_usd, held=None,
               in_flight=frozenset()):
    """PURE: (batch, deferred, problems) — the whole planning decision.

    Every input is passed in, so planning is testable with no repo, no
    network and no clock. Orders already in flight hold wip slots and
    their size-band budgets count as spent before any candidate is
    priced — the Conductor survey's rule (wip_cap minus the runs in
    flight), since the ledger records a run only once it ends.
    """
    candidates, deferred = eligible(found, ready_issues, held, in_flight)
    ordered, problems = priced(candidates, config)
    committed, flight_problems = in_flight_budget(found, in_flight, config)
    if flight_problems:
        return [], sorted(deferred), problems + flight_problems + [
            "wq: an order in flight cannot be priced — refusing to plan a"
            " batch against a spend it cannot know"]
    cap, cap_problems = factory_config.resolve_cap(config)
    problems += cap_problems
    if cap is None:
        # Fail closed, the rule priced already applies one function up: a
        # cap that does not resolve is an UNKNOWN ceiling, not an absent
        # one, and skipping the comparison plans a batch against it. Same
        # answer the sibling tools give the same config — cost_report
        # PAUSEs, budget_guard hard-stops. resolve_cap reports None only
        # with a problem, so the cause is already in `problems`; this
        # line is the decision, the way the wip_cap refusal below is.
        return [], sorted(deferred), problems + [
            "wq: no monthly cap could be resolved — refusing to plan a"
            " batch it cannot price"]
    wip = config.get("wip_cap")
    if not isinstance(wip, int) or isinstance(wip, bool) or wip < 1:
        return [], sorted(deferred), problems + [
            "wq: factory.json wip_cap must be a positive integer —"
            " refusing to guess a batch size"]
    flying = (f" ({len(in_flight)} already in flight)" if in_flight
              else "")
    committed_note = (f" ${committed:.2f} budgeted in flight," if in_flight
                      else "")
    batch, projected = [], 0.0
    for row in ordered:
        if len(batch) >= wip - len(in_flight):
            deferred.append(f"{row['wo']}: over the wip_cap of {wip}"
                            f" this round{flying}")
        elif spent_usd + committed + projected + row["budget"] > cap:
            deferred.append(
                f"{row['wo']}: would put the month over its ${cap:.2f} cap"
                f" (${spent_usd:.2f} spent,{committed_note}"
                f" ${projected:.2f} already"
                f" planned, size:{row['size']} budgets"
                f" ${row['budget']:.2f})")
        else:
            batch.append(row)
            projected += row["budget"]
    return batch, sorted(deferred), problems


def ready_issue_numbers(run=None):
    """(issue numbers carrying the ready label, problems), or (None,
    problems) when the listing cannot be trusted — the caller must then
    hold back every row rather than explain it. NETWORK.

    An unreachable tracker is a problem, never an empty queue: "nothing is
    ready" and "I could not ask" must not look the same to the caller, or
    a broken token reads as a drained backlog.

    A truncated window REFUSES here rather than warning, the same rule as
    sweeps.live_issues: past the window an issue is simply absent, and
    absence is exactly what `eligible` reads as a finding — it would
    defer a ready order with "no open issue #N carries the label" and
    send the owner to apply a label the issue may already carry.
    """
    # The full-window RULE is cli.gh_read's; the message stays this
    # caller's own (ADR-0066). gh_read's default note tells whoever
    # reads it to "raise the window or narrow the query" as if either
    # were reachable right now — but LIST_WINDOW is a module constant,
    # and in a stamped repo this tool is a mirrored payload copy, so
    # neither remedy exists at runtime. The remedy is real, it is just a
    # code edit in the tool's own source, not something this message
    # should imply is one flag away.
    numbers, _, problems = ready_issues(run)
    return numbers, problems


def ready_issues(run=None):
    """(ready issue numbers, {number: why its ready label does not
    count}, problems) — ready_issue_numbers plus the holds the listing's
    own labels prove. The claim strips wo:failed and the other lifecycle
    labels, so planning a budget-exhausted order (ADR-0034: "the
    dispatcher refuses a budget-exhausted order until the owner clears
    the label") or one already on another lifecycle label would pay an
    agent and erase the state that said not to. assembler.run_resolve
    refuses the first already."""
    entries, problems = _open_entries(LIST_ARGS, "ready", "LIST_ARGS", run)
    if entries is None:
        return None, {}, problems
    numbers, holds = set(), {}
    for item in entries:
        if not (isinstance(item, dict) and isinstance(item.get("number"),
                                                      int)):
            continue
        numbers.add(item["number"])
        names = label_names(item)
        if assembler.EXHAUSTED_LABEL in names:
            holds[item["number"]] = (
                f"carries {assembler.EXHAUSTED_LABEL} — the owner clears"
                " it before the order may run again (ADR-0034)")
            continue
        # wo:failed is the terminal state an owner re-arms from: the
        # claim stripping it is the retry, so only a live lifecycle label
        # beside the ready one holds an order back.
        others = sorted(name for name in names if name.startswith("wo:")
                        and name not in (assembler.READY_LABEL, "wo:failed"))
        if others:
            holds[item["number"]] = (
                f"also carries {', '.join(others)} — one lifecycle label"
                " at a time, and the claim would strip it (ADR-0032)")
    return numbers, holds, []


def in_flight_issue_numbers(run=None):
    """(issue numbers carrying the claim label, problems), or (None,
    problems) when the listing cannot be trusted. NETWORK. Same refusal
    rule as ready_issue_numbers: an in-flight order past the window would
    silently free its wip slot and its budget."""
    return _open_numbers(IN_FLIGHT_ARGS, "in-flight", "IN_FLIGHT_ARGS",
                         run)


def _open_numbers(args, noun, args_name, run):
    entries, problems = _open_entries(args, noun, args_name, run)
    if entries is None:
        return None, problems
    return {item["number"] for item in entries if isinstance(item, dict)
            and isinstance(item.get("number"), int)}, []


def _open_entries(args, noun, args_name, run):
    read = gh_read(list(args), "gh issue list", label="wq",
                   run=run or gh_runner, window=LIST_WINDOW,
                   full_note=(
                       f"returned a full {LIST_WINDOW}-entry window —"
                       f" older {noun} orders are invisible; LIST_WINDOW"
                       " is a code constant in work_queue.py, not a"
                       " runtime option, so the fix is raising it there"
                       f" (or narrowing {args_name}) and redeploying"))
    if read.value is None or read.truncated:
        return None, read.problems
    return read.value, []


def owner_override(run):
    """(the FACTORY_OWNER_LOGIN repository variable's value or None,
    problems), failing closed — None with no problem means it is unset.

    An organization-owned repo's github.repository_owner is the org, which
    never labels anything, so assembler.yml compares the labeler against
    `vars.FACTORY_OWNER_LOGIN || github.repository_owner` (#2105). The
    planner reads the same repository variable so it agrees with the
    workflow; a variable set only at the org level is invisible to
    `gh variable list` here, so set it on the repository."""
    read = gh_read(["variable", "list", "--json", "name,value"],
                   "gh variable list", label="wq", run=run)
    if read.value is None:
        return None, read.problems
    for item in read.value:
        if isinstance(item, dict) and item.get("name") == OWNER_VARIABLE:
            value = item.get("value")
            if isinstance(value, str) and value.strip():
                return value.strip(), []
    return None, []


def repo_owner(run):
    """(the owner's login, problems), failing closed — the login
    assembler.yml compares against: the FACTORY_OWNER_LOGIN repository
    variable when set, else github.repository_owner."""
    override, problems = owner_override(run)
    if problems:
        return None, problems
    if override is not None:
        return override, []
    read = gh_read(["repo", "view", "--json", "owner"], "gh repo view",
                   label="wq", run=run, expect=dict)
    if read.value is None:
        return None, read.problems
    login = (read.value.get("owner") or {}).get("login")
    if not isinstance(login, str) or not login.strip():
        return None, ["wq: gh repo view names no owner"]
    return login, []


def owner_holds(numbers, run=None):
    """({ready issue: why its label does not count}, problems), or (None,
    problems) when the owner cannot be named. NETWORK.

    ADR-0032: only the repo owner may apply wo:ready-for-agent, and a
    label from anyone else is inert. The owner is repo_owner's: the
    FACTORY_OWNER_LOGIN repository variable when set, else the repo's
    owner login. The latest labeled event's actor
    (human_gates.read_labelers) is judged by assembler.actor_is_owner, the
    workflow's own authority. A timeline that could not be read, or holds
    no such event, fails closed: the issue is held back with a problem,
    never counted as the owner's.
    """
    if not numbers:
        return {}, []
    run = run or gh_runner
    owner, problems = repo_owner(run)
    if owner is None:
        return None, problems
    labelers, problems = read_labelers(sorted(numbers),
                                       assembler.READY_LABEL, run, "wq")
    held = {}
    for number in sorted(numbers):
        actor = labelers.get(number)
        if number not in labelers:
            # Unread: read_labelers already said why in `problems`.
            held[number] = UNKNOWN_LABELER
        elif actor is None:
            held[number] = UNKNOWN_LABELER
            problems.append(f"wq: issue #{number}'s timeline holds no event"
                            f" applying {assembler.READY_LABEL}, so who"
                            " applied it is unknown")
        elif not assembler.actor_is_owner(actor, owner)[0]:
            held[number] = (f"carries {assembler.READY_LABEL} applied by"
                            f" {actor or '(unnamed)'}, not the owner —"
                            " inert (ADR-0032)")
    return held, problems


def month_to_date(root, now):
    """(dollars recorded for `now`'s month, problems) — ADR-0034. What
    counts as spend is cost_ledger.dispatched's rule, the same row set the
    weekly cost report's month total is built from: a gate-latency
    observation is a wait record, not a run, and never counts (ADR-0041).
    The breaker's input and the report's figure therefore cannot drift
    apart."""
    entries, problems = cost_ledger.read(root)
    problems = problems + cost_ledger.future_problems(
        entries, now.strftime("%Y-%m-%d"))
    month = now.strftime("%Y-%m")
    total = sum(entry["cost"] for entry
                in cost_ledger.dispatched(entries, month))
    return total, problems


def compose_plan(batch, deferred, spent, wip):
    """The batch as report lines — the human half of `plan`, next to the
    `--json` payload's machine half. Named for what it renders: `report`
    belongs to the cli seam's epilogue (ADR-0051), which this tool's main
    also ends with."""
    lines = [f"wq: {len(batch)} work order(s) ready to run in parallel"
             f" (wip_cap {wip})"]
    lines += [f"  {row['wo']}  size:{row['size']}  ${row['budget']:.2f}"
              f"  issue #{row['issue']}  {row['where']}" for row in batch]
    if batch:
        lines.append(f"  projected ${sum(r['budget'] for r in batch):.2f}"
                     f" on top of ${spent:.2f} spent this month")
    lines += [f"  deferred {line}" for line in deferred]
    return lines


def main(argv, run=None, clock=None):
    if argv in (["-h"], ["--help"]):
        print(__doc__.strip())
        return 0
    if not argv or argv[0] != "plan":
        print(__doc__.strip())
        return 2
    root = repo_root()
    config, problems = factory_config.load(root)
    if problems:
        return report("wq", problems)
    ready, label_held, problems = ready_issues(run)
    held = in_flight = None
    if ready is not None:
        # Each read below is only asked once the one before it is
        # trusted: a plan over a listing it could not read plans nothing
        # either way, and stops at the first reason why.
        held, holds_problems = owner_holds(ready, run)
        problems += holds_problems
    if held is not None:
        held = {**held, **label_held}
    if held is not None:
        in_flight, flight_problems = in_flight_issue_numbers(run)
        problems += flight_problems
    if in_flight is None:
        ready = None
    found, read_problems = rows_and_problems(root)
    problems += read_problems
    if read_problems:
        problems.append("wq: a breakdown is unreadable — refusing to plan"
                        " over rows it cannot see")
    spent, ledger_problems = month_to_date(root, (clock or _utcnow)())
    problems += ledger_problems
    if ledger_problems:
        # Spend summed over the rows that parsed is understated, so a
        # batch priced against it would be priced against a lie (#1893):
        # fail closed like cost_report.guard and budget_guard.
        problems.append("wq: month-to-date spend is unreadable — refusing"
                        " to plan a batch it cannot price")
    trusted = ready is not None and not ledger_problems and not read_problems
    if not trusted:
        # An untrusted listing plans nothing and explains nothing: every
        # per-row deferral would be a claim about a listing that does not
        # cover the row. The problems already say why.
        batch, deferred = [], []
    else:
        batch, deferred, plan_problems = plan_batch(
            found, ready, config, spent, held, in_flight)
        problems += plan_problems
        # A ready label no row mirrors: the mirror ran ahead of the
        # breakdown, which ADR-0032 forbids — name it, never just omit it.
        mirrored = {row["issue"] for row in found.values()}
        deferred = sorted(deferred + [
            f"issue #{number} carries {assembler.READY_LABEL}, but no"
            " breakdown row mirrors it — the mirror ran ahead of the"
            " breakdown (ADR-0032)"
            for number in sorted(ready - mirrored)])
    if "--json" in argv:
        # The one leg cli.report does not fit: the problems already ride
        # inside the payload, so printing them again would both duplicate
        # them and put prose above the object a reader parses. Carved out
        # the way ADR-0051 carved out the usage epilogue — the seam does
        # not grow a "summary only" parameter for one caller. The summary
        # line stays in lockstep with the seam's grammar by test, since
        # nothing else bridges the two.
        print(json.dumps({"batch": batch, "deferred": deferred,
                          "problems": problems}, indent=2))
        print(f"wq: {len(problems)} problem(s)")
        return 1 if problems else 0
    if trusted:
        # No plan is rendered over an untrusted listing either: "0 work
        # order(s) ready" is a count of the queue, and this run is the one
        # that decided a broken listing must not be able to produce that
        # sentence. Refusing the rows and then announcing the batch size
        # would put the claim back in the first line a reader skims.
        for line in compose_plan(batch, deferred, spent,
                                 config.get("wip_cap")):
            print(line)
    return report("wq", problems)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
