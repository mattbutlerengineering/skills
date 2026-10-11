#!/usr/bin/env python3
"""conductor_flow: the item state machine and the stall rule in `next`
(PRD-0013, WO-0157), split from conductor.py by capability (breakdown
assumption 6). It imports conductor.py's row grammar and ledger writes,
which keep one owner.

An item moves only along

  planned -> spec -> awaiting-gate -> build -> verify -> review
          -> reviewed -> ship -> merging -> merged

A fix may skip awaiting-gate when its branch changes no gate file; an
order starts at build; review returns to build once, for the reviewer's
first request for changes. `stalled` is reachable from any non-terminal
state and left only for the step it stalled in, after a retry answer.
`blocked` is written only by conductor.answer. The Owner's 2026-10-10
answers (breakdown.md Notes, rows 0157 and 0158) settle the launch
record, readiness, gate asks and verdicts used here.
"""
import json
import os
import re
from datetime import datetime, timezone

import factory_config
from cli import CLI_FAILURES, detail
from conductor import (AT_FORMAT, BLOCK, TERMINAL, answers, append,
                       ask_row, current_state, load, next_ask, stamp)

STEPS = ("spec", "build", "verify", "review", "ship")
SEQUENCE = ("planned", "spec", "awaiting-gate", "build", "verify",
            "review", "reviewed", "ship", "merging", "merged")
# lean: fixed wall-clock limits per size (architecture.md); the trigger
# to tune one is a scorecard showing it fire on a healthy run.
WALL_CLOCK_MINUTES = {"S": 45, "M": 90, "L": 180}
# Cheapest first, so retry-up takes the next band to the right.
BANDS = factory_config.BANDS
STALL_OPTIONS = ("retry", "retry-up", "block")
RETRIES = ("retry", "retry-up")
GATE_OPTIONS = ["approve", "block"]
PAUSE_OPTIONS = ["resume", "stop"]
# A batch-level answer with one of these choices holds all dispatch.
HOLD_CHOICES = ("decline", "stop")
FAILURE_PAUSE = 3
COMPLETED = "completed"
GATE_PATH = re.compile(r"docs/adr/.+|docs/design/.+|(?:.+/)?"
                       r"(?:prd|architecture)\.md")
UNCHECKED_ROW = re.compile(r"- \[ \] .*")
VERDICTS = ("pass", "changes")


def item_branch(batch, item):
    """The item's branch (Owner, 2026-10-10): conductor/<batch>-<n>."""
    return f"conductor/{batch}-{item[1:]}"


def plan_row(rows):
    return next((row for row in rows if row["kind"] == "plan"), None)


def plan_entry(rows, item):
    plan = plan_row(rows)
    return next((entry for entry in (plan or {}).get("items", [])
                 if entry["item"] == item), None)


def _states(rows, item):
    return [row for row in rows
            if row["kind"] == "state" and row["item"] == item]


def _unanswered(rows, item):
    given = answers(rows)
    return next((row for row in rows if row["kind"] == "ask"
                 and row["item"] == item and row["id"] not in given), None)


def latest_answer(rows, item, ask_kind, after=-1):
    """The latest answer to an ask of this kind on the item, written
    after row index `after`, or None."""
    asks = {row["id"] for row in rows if row["kind"] == "ask"
            and row["item"] == item and row["ask_kind"] == ask_kind}
    found = [row for index, row in enumerate(rows) if index > after
             and row["kind"] == "answer" and row["ask"] in asks]
    return found[-1] if found else None


def _successors(item_type, state, rows, item):
    """The states the item may enter from `state` along its sequence."""
    if state == "planned":
        return ["build"] if item_type == "order" else ["spec"]
    if state == "spec":
        return (["awaiting-gate", "build"] if item_type == "fix"
                else ["awaiting-gate"])
    if state == "build":
        return ["build", "verify"]
    if state == "review":
        fixed = any(row["from"] == "review" and row["to"] == "build"
                    for row in _states(rows, item))
        return ["reviewed"] if fixed else ["reviewed", "build"]
    following = SEQUENCE.index(state) + 1
    return list(SEQUENCE[following:following + 1])


def _stalled_problems(rows, item, to):
    states = _states(rows, item)
    stalled_at = rows.index(states[-1])
    resumed = latest_answer(rows, item, "stall", after=stalled_at)
    if to != states[-1]["from"] or resumed is None \
            or resumed["choice"] not in RETRIES:
        return [f"cd: {item} leaves stalled only for"
                f" {states[-1]['from']}, after a retry answer"]
    return []


def transition_problems(rows, item, to, fields):
    """Problems with moving `item` to `to` (with these extra state-row
    fields) given the ledger's rows. Empty means the move is legal."""
    entry = plan_entry(rows, item)
    if entry is None:
        return [f"cd: {item} is not an item of this batch's plan"]
    state = current_state(rows, item)
    if state in TERMINAL:
        return [f"cd: {item} is {state}, and {state} is terminal"]
    if to == "blocked":
        return [f"cd: {item} is blocked only by a {BLOCK} answer to one of"
                " its asks"]
    waiting = _unanswered(rows, item)
    if waiting is not None and to != "stalled":
        return [f"cd: {item} has an unanswered ask ({waiting['id']})"]
    if to == "stalled":
        return ([] if state != "stalled"
                else [f"cd: {item} cannot move from stalled to stalled"])
    if state == "stalled":
        return _stalled_problems(rows, item, to)
    if to not in _successors(entry["type"], state, rows, item):
        return [f"cd: {item} cannot move from {state} to {to}"]
    if state == "awaiting-gate":
        opened = latest_answer(rows, item, "gate")
        if opened is None or opened["choice"] != "approve":
            return [f"cd: {item} leaves awaiting-gate only after an"
                    " approve answer to its gate ask"]
    if to == "reviewed" and fields.get("verdict") == "pass" \
            and fields.get("reviewer_run") in fields.get("author_runs", []):
        return [f"cd: {item} reviewed pass refused: reviewer run"
                f" {fields['reviewer_run']} is among its author runs"]
    return []


def state_row(now, item, frm, to, reason, **fields):
    return {"at": stamp(now), "kind": "state", "item": item, "from": frm,
            "to": to, "reason": reason, **fields}


def move(root, batch, now, item, to, reason, **fields):
    """(row, problems): append one state row, refused unless the move is
    legal on the ledger's rows as they stand under the lock."""
    def build(rows):
        problems = transition_problems(rows, item, to, fields)
        if problems:
            return None, problems
        return state_row(now, item, current_state(rows, item), to, reason,
                         **fields), []
    return append(root, batch, build)


def _band(entry, step):
    return next((s["band"] for s in entry["steps"] if s["step"] == step),
                None)


def stall_rows(rows, now, entry, reason, recommended, why):
    """[state row, stall ask] for an item that stalls in its current
    state. retry-up is offered only below the top band."""
    item = entry["item"]
    state = current_state(rows, item)
    band = _band(entry, state)
    options = [option for option in STALL_OPTIONS
               if option != "retry-up" or band != BANDS[-1]]
    moved = state_row(now, item, state, "stalled", reason)
    asked, problems = ask_row(
        rows + [moved], now, item, "stall",
        f"{item} stalled in {state}: {reason}. Retry, retry one band up,"
        " or block?", options, recommended, why)
    return [moved, asked], problems


def queue_stall(root, batch, now, item, reason, recommended, why):
    """(rows written, problems): stall the item and queue its ask."""
    def build(rows):
        entry = plan_entry(rows, item)
        if entry is None:
            return None, [f"cd: {item} is not an item of this batch's plan"]
        return stall_rows(rows, now, entry, reason, recommended, why)
    return append(root, batch, build)


IDLE_WHY = ("a dead runner or an idle step is evidence about the run more"
            " than about the item")
CHANGES_WHY = "a second request for changes is evidence about the item"


def record_verdict(root, batch, now, item, verdict, reviewer_run):
    """(rows written, problems): the review step's verdict. pass writes
    `reviewed` with the item's author runs (every run but a review);
    the first `changes` returns the item to build for one fix step; the
    second stalls it."""
    if verdict not in VERDICTS:
        return None, [f"cd: verdict {verdict!r} is not pass or changes"]

    def build(rows):
        entry = plan_entry(rows, item)
        if entry is None:
            return None, [f"cd: {item} is not an item of this batch's plan"]
        if verdict == "pass":
            authors = [row["run_id"] for row in rows if row["kind"] == "run"
                       and row["item"] == item and row["step"] != "review"]
            fields = {"verdict": "pass", "author_runs": authors,
                      "reviewer_run": reviewer_run}
            to, reason = "reviewed", "the reviewer passed it"
        else:
            fields, to = {}, "build"
            reason = "the reviewer requested changes; one fix step"
            if "build" not in _successors(entry["type"], "review", rows,
                                          item):
                return stall_rows(rows, now, entry, "the reviewer requested"
                                  " changes a second time", BLOCK,
                                  CHANGES_WHY)
        problems = transition_problems(rows, item, to, fields)
        if problems:
            return None, problems
        return [state_row(now, item, current_state(rows, item), to, reason,
                          **fields)], []
    return append(root, batch, build)


def _held(rows):
    """True when a batch-level ask is unanswered or was answered with a
    choice that holds dispatch (a declined spend, a stopped pause)."""
    given = answers(rows)
    for row in rows:
        if row["kind"] == "ask" and row["item"] is None:
            answer = given.get(row["id"])
            if answer is None or answer["choice"] in HOLD_CHOICES:
                return True
    return False


def _failure_streak(rows):
    """Consecutive failed runs since the last batch pause ask."""
    start = max((index for index, row in enumerate(rows)
                 if row["kind"] == "ask" and row["item"] is None
                 and row["options"] == PAUSE_OPTIONS), default=-1)
    streak = 0
    for row in rows[start + 1:]:
        if row["kind"] == "run":
            streak = streak + 1 if row["outcome"] != COMPLETED else 0
    return streak


def _at(value):
    return datetime.strptime(value, AT_FORMAT).replace(tzinfo=timezone.utc)


def needs_facts(rows):
    """The items whose finished spec or build step needs branch facts
    (gate blobs, unchecked rows) before `survey` can say what follows."""
    plan = plan_row(rows) or {}
    found = []
    for entry in plan.get("items", []):
        item = entry["item"]
        states = _states(rows, item)
        if not states or states[-1]["to"] not in ("spec", "build"):
            continue
        finished = _finishing(rows, states[-1])
        if finished is not None and finished["outcome"] == COMPLETED:
            found.append(item)
    return found


def _finishing(rows, launched):
    run_id = launched.get("run_id")
    return next((row for row in rows if row["kind"] == "run"
                 and row["run_id"] == run_id), None) if run_id else None


def _after_step(rows, now, entry, launched, facts):
    """(ready step or None, rows to write) once the item's launched step
    has finished with a completed run."""
    item, state = entry["item"], launched["to"]
    if state == "spec":
        if item not in facts:
            return None, []
        blobs = facts[item]["gate_blobs"]
        if entry["type"] != "feature" and not blobs:
            return "build", []
        moved = state_row(now, item, "spec", "awaiting-gate",
                          f"spec run {launched['run_id']} completed")
        files = (f"the gate files are {', '.join(sorted(blobs))}" if blobs
                 else "the item branch changes no gate file")
        asked, problems = ask_row(
            rows + [moved], now, item, "gate",
            f"{item}'s spec is ready for its gate: approve these gate files"
            " and start the build?", GATE_OPTIONS, "approve",
            f"the spec step completed; {files}", gate_blobs=blobs)
        return None, ([moved, asked] if not problems else [])
    if state == "build":
        if entry["type"] == "order":
            return "verify", []
        if item not in facts:
            return None, []
        return ("build" if facts[item]["unchecked"] else "verify"), []
    return {"verify": "review"}.get(state), []


def _in_flight(rows, now, entry, launched, alive):
    """(True when the launched step's runner is still running, stall
    rows when it has died or idled)."""
    pid = launched["pid"]
    if not alive(pid):
        reason = f"its runner (pid {pid}) is gone with no finishing run row"
    else:
        limit = 2 * WALL_CLOCK_MINUTES[entry["size"]]
        idle = (now - _at(launched["at"])).total_seconds() / 60
        if idle <= limit:
            return True, []
        reason = f"no state change for over {limit} minutes"
    written, _ = stall_rows(rows, now, entry, reason, "retry", IDLE_WHY)
    return False, written


def _candidate(rows, now, entry, alive, facts):
    """(ready step or None, in flight?, rows to write) for one item."""
    item = entry["item"]
    state = current_state(rows, item)
    states = _states(rows, item)
    if state in TERMINAL or state == "merging":
        return None, False, []
    if state == "stalled":
        resumed = latest_answer(rows, item, "stall",
                                 after=rows.index(states[-1]))
        if _unanswered(rows, item) is None and resumed is not None \
                and resumed["choice"] in RETRIES:
            return states[-1]["from"], False, []
        return None, False, []
    if _unanswered(rows, item) is not None:
        return None, False, []
    if state == "planned":
        return entry["steps"][0]["step"], False, []
    if state == "reviewed":
        return "ship", False, []
    if state == "awaiting-gate":
        opened = latest_answer(rows, item, "gate")
        return ("build" if opened and opened["choice"] == "approve"
                else None), False, []
    launched = states[-1]
    if "run_id" not in launched:
        return state, False, []
    finished = _finishing(rows, launched)
    if finished is None:
        flying, written = _in_flight(rows, now, entry, launched, alive)
        return None, flying, written
    if finished["outcome"] != COMPLETED:
        return None, False, []
    ready, written = _after_step(rows, now, entry, launched, facts)
    return ready, False, written


def survey(rows, now, wip_cap, alive, facts):
    """(ready steps, rows to write, problems): PURE over the ledger's
    rows. Ready steps are [{"item", "step"}] in plan order, at most
    wip_cap minus the runs in flight, and none while dispatch is held.
    Rows to write are new stall and gate asks with their state moves,
    and the batch pause after FAILURE_PAUSE consecutive failed runs.
    `facts` maps an item to its branch facts (gate_blobs, unchecked)."""
    plan = plan_row(rows)
    if plan is None:
        return None, None, ["cd: the batch ledger has no plan row"]
    writes, candidates, flying = [], [], 0
    for entry in plan["items"]:
        ready, in_flight, written = _candidate(rows + writes, now, entry,
                                               alive, facts)
        writes += written
        flying += in_flight
        if ready is not None:
            candidates.append({"item": entry["item"], "step": ready})
    if _failure_streak(rows) >= FAILURE_PAUSE and not _held(rows):
        asked, _ = ask_row(
            rows + writes, now, None, "stall",
            f"Three consecutive Worker runs failed in batch {plan['batch']}."
            " Resume dispatch, or stop?", PAUSE_OPTIONS, "stop",
            "three failures in a row point at the batch or the harness more"
            " than at any one item")
        writes.append(asked)
    if _held(rows + writes):
        return [], writes, []
    return candidates[:max(0, wip_cap - flying)], writes, []


# --- branch facts, read through the git port ---------------------------

def _git(git, args, what):
    try:
        return git(args).stdout, []
    except CLI_FAILURES as err:
        return None, [f"cd: git {what} failed: {detail(err)}"]


def changed_files(git, branch):
    out, problems = _git(git, ["diff", "--name-only",
                               f"origin/main...{branch}"],
                         f"diff for {branch}")
    return (None, problems) if problems else (out.split(), [])


def gate_blobs(git, branch):
    """({gate path: blob id}, problems) for the gate files the item
    branch changes against origin/main."""
    changed, problems = changed_files(git, branch)
    if problems:
        return None, problems
    gates = [path for path in changed if GATE_PATH.fullmatch(path)]
    if not gates:
        return {}, []
    out, problems = _git(git, ["ls-tree", branch, "--", *gates],
                         f"ls-tree for {branch}")
    if problems:
        return None, problems
    blobs = {}
    for line in out.splitlines():
        meta, _, path = line.partition("\t")
        blobs[path] = meta.split()[2]
    return blobs, []


def unchecked_rows(git, branch):
    """(unchecked top-level breakdown rows, problems) from the
    breakdown.md or defect.md the item branch changes."""
    changed, problems = changed_files(git, branch)
    if problems:
        return None, problems
    rows = []
    for path in changed:
        if not path.endswith(("/breakdown.md", "/defect.md")):
            continue
        out, problems = _git(git, ["show", f"{branch}:{path}"],
                             f"show {branch}:{path}")
        if problems:
            return None, problems
        rows += [line for line in out.splitlines()
                 if UNCHECKED_ROW.fullmatch(line)]
    return rows, []


def branch_facts(git, batch, items):
    """({item: {"gate_blobs", "unchecked"}}, problems) for these items."""
    facts = {}
    for item in items:
        branch = item_branch(batch, item)
        blobs, problems = gate_blobs(git, branch)
        if problems:
            return None, problems
        rows, problems = unchecked_rows(git, branch)
        if problems:
            return None, problems
        facts[item] = {"gate_blobs": blobs, "unchecked": len(rows)}
    return facts, []


def pid_alive(pid):
    """True while a process with this pid exists (signal 0 probes)."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def advance(root, batch, now, wip_cap, alive, git):
    """(result, problems): `next`. Reads branch facts for finished steps,
    then surveys and writes new asks under the ledger lock."""
    rows, problems = load(root, batch)
    if problems:
        return None, problems
    facts, problems = branch_facts(git, batch, needs_facts(rows))
    if problems:
        return None, problems
    outcome = {}

    def build(rows):
        ready, writes, problems = survey(rows, now, wip_cap, alive, facts)
        outcome.update(ready=ready, writes=writes or [], rows=rows)
        return writes, problems
    _, problems = append(root, batch, build)
    if problems:
        return None, problems
    recorded = [row["id"] for row in outcome["writes"]
                if row["kind"] == "ask"]
    return {"ask": next_ask(outcome["rows"] + outcome["writes"]),
            "ready": outcome["ready"], "recorded": recorded}, []


def next_cli(root, batch, args, now, git, alive):
    if args:
        return None
    config, problems = factory_config.load(root)
    if problems:
        return problems
    wip = config.get("wip_cap")
    if isinstance(wip, bool) or not isinstance(wip, int) or wip < 1:
        return ["cd: factory.json wip_cap must be a positive integer"]
    result, problems = advance(root, batch, now, wip, alive or pid_alive,
                               git)
    if result is not None:
        print(json.dumps(result, indent=2))
    return problems
