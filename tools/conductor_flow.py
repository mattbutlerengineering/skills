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
state and left only for the step it stalled in, after a retry answer —
or for merged, after a `merged` answer to the stall a PR merged outside
the batch raises (#938). `blocked` is written only by conductor.answer,
and left only for merged, when close finds the item's PR merged after
the block. The Owner's 2026-10-10 answers (breakdown.md Notes, rows
0157 and 0158) settle the launch record, readiness, gate asks and
verdicts used here.
"""
import re

import conductor_consent as consent
import conductor_landed as landed
import factory_config
from cli import CLI_FAILURES, detail
from conductor import (BLOCK, COMPLETED, TERMINAL, answers, append,
                       ask_row, current_state, item_branch, item_view,
                       parsed_at, stamp, view)
from conductor_spend import LOST
from knowledge_plane import parse_row
from protocol import read_frontmatter

STEPS = ("spec", "build", "verify", "review", "ship")
SEQUENCE = ("planned", "spec", "awaiting-gate", "build", "verify",
            "review", "reviewed", "ship", "merging", "merged")
# lean: fixed wall-clock limits per size (architecture.md); the trigger
# to tune one is a scorecard showing it fire on a healthy run.
WALL_CLOCK_MINUTES = {"S": 45, "M": 90, "L": 180}
# Cheapest first, so retry-up takes the next band to the right.
BANDS = factory_config.BANDS
STALL_OPTIONS = ("retry", "retry-up", "block")
GATE_OPTIONS = ["approve", "block"]
PAUSE_OPTIONS = ["resume", "stop"]
# A batch-level answer with one of these choices holds all dispatch.
HOLD_CHOICES = ("decline", "stop")
FAILURE_PAUSE = 3
GATE_PATH = re.compile(r"docs/adr/.+|docs/design/.+|(?:.+/)?"
                       r"(?:prd|architecture)\.md")
VERDICTS = ("pass", "changes")


def shipped_items(rows):
    """The plan's items whose ship step completed, in plan order."""
    read = view(rows)
    return [entry["item"] for entry in (read["plan"] or {}).get("items", [])
            if read["items"][entry["item"]]["state"] == "ship"
            and read["items"][entry["item"]]["completed"]]


def stalled_merges(rows):
    """The plan's items stalled in a merge turn (from `merging`), in plan
    order: a retry resumes them as a merge, which needs its cover read
    like a shipped item's — a renumbered gate file can leave a train
    item owing its own merge ask."""
    read = view(rows)
    return [entry["item"] for entry in (read["plan"] or {}).get("items", [])
            if read["items"][entry["item"]]["state"] == "stalled"
            and read["items"][entry["item"]]["last"]["from"] == "merging"]


def merge_due(rows, facts, policy=None):
    """The shipped items, and the items stalled in a merge turn, that
    wait for a merge ask the Conductor words: conductor_consent.cover
    reads them OWED, and no ask is pending, whether the item's own (a
    stall's included) or a train listing it. `facts` maps an item to its
    branch facts; an item with no gate_blobs read yet is not judged.
    PURE."""
    given = answers(rows)
    pending = [row for row in rows if row["kind"] == "ask"
               and row["ask_kind"] == "merge" and row["id"] not in given]
    due = []
    for item in shipped_items(rows) + stalled_merges(rows):
        blobs = facts.get(item, {}).get("gate_blobs")
        if blobs is None or item_view(rows, item)["pending"] is not None \
                or any(item in row.get("covers", []) for row in pending):
            continue
        if consent.cover(rows, item, blobs, policy)[0] == consent.OWED:
            due.append(item)
    return due


def standing_due(rows, facts, policy=None):
    """The merge-due items no merge ask covers at all, answered or not:
    the ones the standing policy may cover (ADR-0086). Once the Owner
    has a merge ask on an item, the Owner's answer decides it. PURE."""
    asked = set()
    for row in rows:
        if row["kind"] == "ask" and row["ask_kind"] == "merge":
            asked.update([row["item"], *row.get("covers", [])])
    return [item for item in merge_due(rows, facts, policy)
            if item not in asked]


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
                    for row in item_view(rows, item)["states"])
        return ["reviewed"] if fixed else ["reviewed", "build"]
    following = SEQUENCE.index(state) + 1
    return list(SEQUENCE[following:following + 1])


# States that are not steps resume at their next step (#1870): the gate
# answer is already in at awaiting-gate, and a reviewed item ships.
RESUMES = {"awaiting-gate": "build", "reviewed": "ship"}


def _stalled_problems(rows, found, to, fields):
    stalled, resumed = found["last"], found["resumed"]
    if to == landed.MERGED:
        # A PR merged outside the batch (#938): the answer records it.
        if resumed is not None and resumed["choice"] == landed.MERGED:
            return []
        return [f"cd: {found['item']} leaves stalled for merged only after"
                " a merged answer to its stall ask"]
    resume = RESUMES.get(stalled["from"], stalled["from"])
    if to != resume or not found["retry"]:
        return [f"cd: {found['item']} leaves stalled only for"
                f" {resume}, after a retry answer"]
    # An idle stall names its live run (_in_flight): that run keeps its
    # worktree until its finishing run row lands, or `next` writes a lost
    # one for a runner found dead.
    if found["in_flight"]:
        return [f"cd: {found['item']}'s {stalled['from']} run"
                f" {stalled['run_id']} is still in flight"]
    # A launch carries a fresh run id; `next`'s bookkeeping resume
    # carries the completed run's own (#939).
    run = delivered_run(rows, found)
    if run is not None and fields.get("run_id") != run["run_id"]:
        return [f"cd: {found['item']}'s {to} run {run['run_id']} completed;"
                " its bookkeeping is retried by next, never by another"
                " Worker run"]
    return []


def transition_problems(rows, item, to, fields):
    """Problems with moving `item` to `to` (with these extra state-row
    fields) given the ledger's rows. Empty means the move is legal."""
    found = item_view(rows, item)
    entry, state = found["entry"], found["state"]
    if found["unknown"]:
        return [found["unknown"]]
    if state == "blocked" and to == landed.MERGED:
        # Its PR merged after the block (#938): close reconciles it.
        return []
    if state in TERMINAL:
        return [f"cd: {item} is {state}, and {state} is terminal"]
    if to == "blocked":
        return [f"cd: {item} is blocked only by a {BLOCK} answer to one of"
                " its asks"]
    waiting = found["pending"]
    if waiting is not None and to != "stalled":
        return [f"cd: {item} has an unanswered ask ({waiting['id']})"]
    if to == "stalled":
        return ([] if state != "stalled"
                else [f"cd: {item} cannot move from stalled to stalled"])
    if state == "stalled":
        return _stalled_problems(rows, found, to, fields)
    if to not in _successors(entry["type"], state, rows, item):
        return [f"cd: {item} cannot move from {state} to {to}"]
    if state == "awaiting-gate":
        opened = found["gate"]
        if opened is None or opened["choice"] != "approve":
            return [f"cd: {item} leaves awaiting-gate only after an"
                    " approve answer to its gate ask"]
    if to == "reviewed" and fields.get("verdict") == "pass" \
            and fields.get("reviewer_run") in fields.get("author_runs", []):
        return [f"cd: {item} reviewed pass refused: reviewer run"
                f" {fields['reviewer_run']} is among its author runs"]
    # A launched step leaves only once its finishing run row exists, so a
    # second runner from a stale `next` never shares its worktree.
    if found["in_flight"]:
        return [f"cd: {item}'s {state} run {found['last']['run_id']} is"
                " still in flight"]
    return []


# The reason a launch state row carries: its `to` is the step launched,
# and the row names the Worker's run_id (conductor_run._launch).
LAUNCHED = "launched"


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


def stall_options(band):
    """The stall ask's options for a step run at `band`: retry-up only
    below the top band."""
    return [option for option in STALL_OPTIONS
            if option != "retry-up" or band != BANDS[-1]]


def _choices(options):
    """The question's closing choice, naming only `options` (#725)."""
    words = [OPTION_WORDS[option] for option in options]
    said = ", or ".join([", ".join(words[:-1]), words[-1]])
    return said[0].upper() + said[1:] + "?"


def stall_rows(rows, now, entry, reason, cause, recommended, why,
               options=None, **fields):
    """[state row, stall ask] for an item that stalls in its current
    state, for `reason` of class `cause` (conductor.CAUSES, #819).
    retry-up is offered only when the run leaving this state (if any — a
    dead runner leaves none) was not already at the top band: the
    planned band alone misses a prior retry-up bump (#732). `options`
    given replace the band's; `fields` go on the state row."""
    item = entry["item"]
    found = item_view(rows, item)
    state, finishing = found["state"], found["finishing"]
    band = (finishing["band"] if finishing is not None
            else found["steps"].get(state, {}).get("band"))
    if options is None:
        options = stall_options(band)
    if cause == "delivery-failed" or band is None:
        # The Worker finished; a retry redoes its bookkeeping (#939),
        # and no band is involved. A state with no step (`merging`)
        # has no band to move up from either (#1874).
        options = [option for option in options if option != "retry-up"]
    moved = state_row(now, item, state, "stalled", reason, cause=cause,
                      **fields)
    asked, problems = ask_row(
        rows + [moved], now, item, "stall",
        f"{item} stalled in {state}: {reason}. {_choices(options)}",
        options, recommended, why)
    return [moved, asked], problems


def prior_stalls(rows, item, step):
    """[(run row or None, stall reason)], oldest first: the item's latest
    consecutive runs of `step` that each ended in a stall. A run of the
    step that did not stall ends the streak."""
    found = item_view(rows, item)
    by_id = {row["run_id"]: row for row in found["runs"]}
    launches = []
    for row in found["states"]:
        if row["to"] == step and "run_id" in row:
            launches.append([by_id.get(row["run_id"]), None])
        elif row["to"] == "stalled" and row["from"] == step and launches:
            launches[-1][1] = row["reason"]
    streak = []
    for run, reason in launches:
        streak = streak + [(run, reason)] if reason is not None else []
    return streak


def delivered_run(rows, found):
    """The completed run row behind an item's delivery-failed stall
    (#939) — its Worker finished; the spend commit, push or PR did not
    — else None. The retry of such a stall is `next`'s bookkeeping
    turn, never another Worker run."""
    last = found["last"]
    if found["state"] != "stalled" or last.get("cause") != "delivery-failed":
        return None
    earlier = prior_stalls(rows, found["item"], last["from"])
    run = earlier[-1][0] if earlier else None
    return run if run is not None and run["outcome"] == COMPLETED else None


def worker_advice(rows, entry, step, band, reason, result=None, cause=None):
    """(recommended, why) for the stall ask of a failed Worker run of
    `step` at `band`, from the item's rows before that run launched
    (#725) and the run's `result` event when the harness gave one. A
    delivery failure (`cause`, #939) recommends retry for the
    bookkeeping it redoes. Otherwise a first failure recommends retry,
    unless it is a budget stop whose result shows the ceiling never let
    the Worker start (#936); that, like a second consecutive budget stop
    at the same band, recommends retry-up while it is offered and the
    run was not already one band up, else block, since the ceiling is
    the same and so is the outcome."""
    if cause == "delivery-failed":
        return "retry", DELIVERY_WHY
    earlier = prior_stalls(rows, entry["item"], step)
    stopped = reason == BUDGET_REASON
    figures = never_started(result) if stopped and not earlier else None
    if figures is not None:
        return _ceiling_advice(rows, entry, step, band, FIRST_BUDGET_WHY,
                               figures)
    if not earlier:
        return "retry", WORKER_WHY
    run, last = earlier[-1]
    if stopped and last == BUDGET_REASON \
            and (run or {}).get("band") == band:
        return _ceiling_advice(rows, entry, step, band, REPEAT_BUDGET_WHY,
                               {})
    return "retry", ATTEMPT_WHY.format(n=len(earlier) + 1, step=step)


def _ceiling_advice(rows, entry, step, band, why, figures):
    """(recommended, why) when the outcome repeats at the step's ceiling:
    retry-up while it is offered and the run was not already one band
    up, else block. `why` is filled with the step, its ceiling, the
    remedy, and `figures`."""
    policy = item_view(rows, entry["item"])["steps"][step]
    up = "retry-up" in stall_options(band) \
        and band == policy["band"] and not policy["bumped"]
    return ("retry-up" if up else BLOCK), why.format(
        step=step, ceiling=policy["ceiling_usd"],
        remedy=("retry it one band up, on a stronger model" if up
                else "block it"), **figures)


def _output_tokens(result):
    """A result event's output tokens: usage's, else the per-model sum
    from modelUsage, which is where a budget stop leaves its counts
    (#725). Both were metered by cli.read_execution before a budget
    stop reaches the stall rule, so the counts are integers."""
    tokens = (result.get("usage") or {}).get("output_tokens", 0)
    return tokens or sum(counts.get("outputTokens", 0)
                         for counts in (result.get("modelUsage") or {})
                         .values())


def never_started(result):
    """The {"turns", "tokens"} a budget-stopped run ended at when they
    show its ceiling went before the Worker started — under
    STARTED_TURNS turns and STARTED_OUTPUT_TOKENS output tokens (#936)
    — else None; also None for no event, or one with no num_turns
    count, so nothing unreadable reads as a run that never started."""
    turns = (result or {}).get("num_turns")
    if isinstance(turns, bool) or not isinstance(turns, int):
        return None
    figures = {"turns": turns, "tokens": _output_tokens(result)}
    started = turns >= STARTED_TURNS \
        or figures["tokens"] >= STARTED_OUTPUT_TOKENS
    return None if started else figures


def queue_stall(root, batch, now, item, reason, cause, recommended, why,
                run_id=None):
    """(rows written, problems): stall the item and queue its ask,
    refused unless the item may move to stalled and, given `run_id`, its
    last launch is that run's: a stale runner never writes a stall onto
    an item that stalled, blocked or relaunched in the meantime."""
    return append(root, batch, lambda rows: guarded_stall(
        rows, now, item, reason, cause, recommended, why, run_id))


def guarded_stall(rows, now, item, reason, cause, recommended, why,
                  run_id=None):
    """(stall rows, problems) over `rows`, under queue_stall's refusals.
    PURE: the runner writes them with its run row (#2160)."""
    found = item_view(rows, item)
    if found["unknown"]:
        return None, [found["unknown"]]
    problems = transition_problems(rows, item, "stalled", {})
    if not problems and run_id is not None \
            and found["last"].get("run_id") != run_id:
        problems = [f"cd: {item}'s state moved on from run {run_id}"]
    if problems:
        return None, problems
    return stall_rows(rows, now, found["entry"], reason, cause,
                      recommended, why)


OPTION_WORDS = {"retry": "retry", "retry-up": "retry one band up",
                "block": "block", landed.MERGED: "treat it as merged"}
WORKER_WHY = ("a first failure is evidence about the item as often as about"
              " the agent, so nothing retries without your answer")
DELIVERY_WHY = ("the Worker finished; only its spend commit, push or PR"
                " failed, so a retry redoes that bookkeeping in your"
                " session and launches no run")
ATTEMPT_WHY = ("attempt {n} at {step} failed after an earlier one did, so"
               " the item is as likely a cause as the agent; nothing"
               " retries without your answer")
# The stall reason conductor_run gives a run the harness stopped at its
# --max-budget-usd ceiling.
BUDGET_STOP = "error_max_budget_usd"
BUDGET_REASON = f"the Worker run ended {BUDGET_STOP}"
REPEAT_BUDGET_WHY = ("a second consecutive budget stop on {step} at the same"
                     " ${ceiling:.2f} ceiling: the outcome repeats at that"
                     " ceiling, so a plain retry spends it again; {remedy}")
# A budget stop under these counts never let the Worker start (#936):
# review-1 of consumer batch b20261013 stopped after 5 turns and 1,072
# output tokens, its ceiling spent loading the brief and the tree, so the
# outcome repeats at that ceiling as surely as after a second stop. A
# Worker that started writes tool calls every turn, so its output runs
# to thousands of tokens within ten turns (#725's stop had 9,000).
STARTED_TURNS = 10
STARTED_OUTPUT_TOKENS = 2000
FIRST_BUDGET_WHY = ("a first budget stop on {step} at its ${ceiling:.2f}"
                    " ceiling after {turns} turn(s) and {tokens} output"
                    " tokens: the ceiling never let the Worker start, so a"
                    " plain retry spends it again; {remedy}")
IDLE_WHY = ("a dead runner or an idle step is evidence about the run more"
            " than about the item")
CHANGES_WHY = "a second request for changes is evidence about the item"
# The stall reason of a second request for changes: the scorecard counts
# it as a review change.
CHANGES_AGAIN = "the reviewer requested changes a second time"


def review_change(row):
    """True for a ledger row recording a request for changes: a review
    sent back to build, or a second request that stalled the item. The
    rule rejection_mining reads Conductor rework by (#800)."""
    return (row["kind"] == "state" and row["from"] == "review"
            and (row["to"] == "build" or row["reason"] == CHANGES_AGAIN))


def verdict_rows(rows, now, item, verdict, reviewer_run, head):
    """(rows to write, problems): the review step's verdict on `rows`.
    pass writes `reviewed` with the item's author runs (every run but a
    review) and `head`, the item branch head the review run was launched
    on, which the merge holds the merged tree to; the first `changes`
    returns the item to build for one fix step; the second stalls it.
    PURE."""
    if verdict not in VERDICTS:
        return None, [f"cd: verdict {verdict!r} is not pass or changes"]
    found = item_view(rows, item)
    entry = found["entry"]
    if found["unknown"]:
        return None, [found["unknown"]]
    if verdict == "pass":
        fields = {"verdict": "pass",
                  "author_runs": list(found["author_runs"]),
                  "reviewer_run": reviewer_run, "reviewed_head": head}
        to, reason = "reviewed", "the reviewer passed it"
    else:
        fields, to = {}, "build"
        reason = "the reviewer requested changes; one fix step"
        if "build" not in _successors(entry["type"], "review", rows, item):
            return stall_rows(rows, now, entry, CHANGES_AGAIN,
                              "changes-again", BLOCK, CHANGES_WHY)
    problems = transition_problems(rows, item, to, fields)
    if problems:
        return None, problems
    return [state_row(now, item, current_state(rows, item), to, reason,
                      **fields)], []


def record_verdict(root, batch, now, item, verdict, reviewer_run, head):
    """(rows written, problems): append the review step's verdict rows
    (verdict_rows) under the ledger lock."""
    return append(root, batch, lambda rows: verdict_rows(
        rows, now, item, verdict, reviewer_run, head))


NO_VERDICT = "review.md carries no verdict: pass|changes line"


def unrecorded_reviews(rows):
    """The plan's items whose review run completed with no verdict row
    after it (record_verdict moves the item out of `review`): the ones
    whose review.md verdict `next` reads, in case their runner died
    before recording it (stall rule 1). PURE."""
    read = view(rows)
    found = [read["items"][entry["item"]]
             for entry in (read["plan"] or {}).get("items", [])]
    return [one["item"] for one in found
            if one["state"] == "review" and one["completed"]]


def recorded_verdict(rows, now, item, run_id, verdict):
    """(stall reason or None, verdict rows, problems) for review run
    `run_id`, completed with `verdict` read from review.md (None: none
    read): the rows record_verdict would have written, over `rows`. The
    head the run was launched on is its launch row's reviewed_head.
    PURE."""
    launch = next((row for row in reversed(rows) if row["kind"] == "state"
                   and row["item"] == item and row["to"] == "review"
                   and row.get("run_id") == run_id and "pid" in row), {})
    if verdict is None:
        return NO_VERDICT, [], []
    if "reviewed_head" not in launch:
        return (f"review run {run_id}'s launch recorded no reviewed head,"
                " so its verdict cannot be recorded"), [], []
    written, problems = verdict_rows(rows, now, item, verdict, run_id,
                                     launch["reviewed_head"])
    return None, written or [], problems


def review_verdict(git, worktree, branch):
    """The review.md verdict on the item branch, or None."""
    changed, problems = changed_files(git, branch)
    for path in [] if problems else changed:
        if path.endswith("/review.md") and (worktree / path).is_file():
            fields = read_frontmatter(worktree / path) or {}
            verdict = (fields.get("verdict") or "").strip()
            return verdict if verdict in VERDICTS else None
    return None


def held(rows):
    """True when a batch-level ask is unanswered or was answered with a
    choice that holds dispatch (a declined spend, a stopped pause). A
    train or closing merge ask holds no Worker step."""
    given = answers(rows)
    for row in rows:
        if row["kind"] == "ask" and row["item"] is None \
                and row["ask_kind"] != "merge":
            answer = given.get(row["id"])
            if answer is None or answer["choice"] in HOLD_CHOICES:
                return True
    return False


def _failure_streak(rows):
    """Consecutive failed runs since the last batch pause ask."""
    start = max((index for index, row in enumerate(rows)
                 if row["kind"] == "ask" and row["item"] is None
                 and row["ask_kind"] == "stall"
                 and row["options"] == PAUSE_OPTIONS), default=-1)
    streak = 0
    for row in rows[start + 1:]:
        if row["kind"] == "run":
            streak = streak + 1 if row["outcome"] != COMPLETED else 0
    return streak


def needs_facts(rows):
    """The items whose finished spec or build step needs branch facts
    (gate blobs, unchecked rows) before `survey` can say what follows."""
    read = view(rows)
    found = [read["items"][entry["item"]]
             for entry in (read["plan"] or {}).get("items", [])]
    return [one["item"] for one in found
            if one["state"] in ("spec", "build") and one["completed"]]


def landed_rows(rows, now, entry, found, unchecked):
    """[state row, stall ask] for an item whose PR the repo merged
    outside the batch (#938, conductor_landed): the stall row carries
    the PR, so the same PR is never asked about twice."""
    pr, state = found["pr"], item_view(rows, entry["item"])["state"]
    recommended, why = landed.advice(state, unchecked, pr)
    return stall_rows(rows, now, entry, landed.REASON.format(pr=pr),
                      landed.CAUSE, recommended, why,
                      options=landed.OPTIONS, pr=pr)


def _build_usd(ceiling, rows):
    """The build's price: one run per breakdown row, each up to the
    build step's `ceiling` (the --max-budget-usd it runs under)."""
    return round(rows * ceiling, 2)


def _gate_question(entry, ceiling, rows, review):
    """The gate ask, which doubles as the build-spend question
    (architecture.md, `plan`): the plan priced one build run, so the
    item is re-priced with one per breakdown row, and the review that
    reads what those rows produce is priced beside it (#936) at its
    `review` ceiling — one run, already in the plan estimate, so it is
    stated rather than added to the re-price."""
    item = entry["item"]
    build = _build_usd(ceiling, rows)
    repriced = entry["estimate_usd"] - ceiling + build
    return (f"{item}'s spec is ready for its gate: approve these gate files,"
            f" its build of {rows} breakdown row(s) at up to"
            f" ${ceiling:.2f} each (${build:.2f}) and its review of what"
            f" those rows produce at up to ${review:.2f}, re-pricing {item}"
            f" at ${repriced:.2f} against its ${entry['estimate_usd']:.2f}"
            " plan estimate?")


def _after_step(rows, now, entry, launched, facts, policy):
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
        steps = item_view(rows, item)["steps"]
        ceiling = steps["build"]["ceiling_usd"]
        unchecked = facts[item]["unchecked"]
        asked, problems = ask_row(
            rows + [moved], now, item, "gate", _gate_question(
                entry, ceiling, unchecked, steps["review"]["ceiling_usd"]),
            GATE_OPTIONS, "approve",
            f"the spec step completed; {files}", gate_blobs=blobs,
            build_usd=_build_usd(ceiling, unchecked))
        return None, ([moved, asked] if not problems else [])
    if state == "build":
        if entry["type"] == "order":
            return "verify", []
        if item not in facts:
            return None, []
        return ("build" if facts[item]["unchecked"] else "verify"), []
    if state == "ship":
        if "gate_blobs" not in facts.get(item, {}):
            return None, []
        reading, _ = consent.cover(rows, item, facts[item]["gate_blobs"],
                                   policy)
        if reading != consent.OWED:
            return ("merge" if reading == consent.COVERED else None), []
        standing = facts[item].get("standing")
        if standing is not None and not standing["problems"]:
            return "merge", [consent.consent_row(
                now, item, standing["labels"], standing["policy"])]
        return None, []
    return {"verify": "review"}.get(state), []


def _in_flight(rows, now, entry, launched, alive):
    """(True when the launched step's runner is still running, stall
    rows when it has died or idled). A dead runner's run gets its run
    row first (#937): outcome LOST, under the policy it was launched
    with, so the stall offers retry-up by the band it ran at (#732) and
    the spend row `next` charges joins it like any failed run's. An
    idle runner is alive and may yet write its own, so its stall row
    names its run and pid: the run stays in flight (_stalled_flight)."""
    pid, lost, running = launched["pid"], [], {}
    if not alive(pid):
        reason = f"its runner (pid {pid}) is gone with no finishing run row"
        lost = [lost_run_row(rows, now, entry, launched)]
    else:
        limit = 2 * WALL_CLOCK_MINUTES[entry["size"]]
        idle = (now - parsed_at(launched["at"])).total_seconds() / 60
        if idle <= limit:
            return True, []
        reason = f"no state change for over {limit} minutes"
        running = {"run_id": launched["run_id"], "pid": pid}
    written, _ = stall_rows(rows + lost, now, entry, reason, "runner-lost",
                            "retry", IDLE_WHY, **running)
    return False, lost + written


def _stalled_flight(rows, now, entry, stalled, alive):
    """(in flight?, rows to write) for an idle stall's run with no
    finishing run row: in flight while its runner lives; once that
    runner is found dead, its lost run row (#937), which `next` charges
    the ceiling, so the retry may launch."""
    if alive(stalled["pid"]):
        return True, []
    launched = next(row for row in item_view(rows, entry["item"])["states"]
                    if row["to"] == stalled["from"]
                    and row.get("run_id") == stalled["run_id"])
    return False, [lost_run_row(rows, now, entry, launched)]


def lost_run_row(rows, now, entry, launched):
    """The run row of a run whose runner died (#937): the launch row's
    run id and pid, the step's policy as the rows before that launch
    resolved it (a retry-up's bump included, as the runner read it),
    no model reported, and outcome LOST."""
    item, step = entry["item"], launched["to"]
    policy = item_view(rows[:rows.index(launched)], item)["steps"][step]
    return {"at": stamp(now), "kind": "run", "item": item, "step": step,
            "charter": policy["charter"], "band": policy["band"],
            "model": policy["model"], "models_reported": [],
            "effort": policy["effort"], "run_id": launched["run_id"],
            "pid": launched["pid"], "outcome": LOST}


def _unrecorded(rows, now, entry, found, alive, facts):
    """Rows for a finished run its runner recorded nothing after (stall
    rule 1): a run that did not complete, or a completed review with no
    verdict row. While its runner is alive and within twice the step's
    wall-clock limit of the run row, [] — it may yet record its own.
    Once it is not, a failed run stalls, and a review's verdict, read
    from review.md into facts[item]["verdict"], is recorded as the
    runner would have, or the item stalls; [] until that read is in."""
    item, run, launched = entry["item"], found["finishing"], found["last"]
    limit = 2 * WALL_CLOCK_MINUTES[entry["size"]]
    ended = f"its run {run['run_id']} ended {run['outcome']}, and"
    if not alive(run["pid"]):
        reason = (f"{ended} its runner (pid {run['pid']}) is gone with"
                  " nothing recorded after it")
    elif (now - parsed_at(run["at"])).total_seconds() / 60 > limit:
        reason = (f"{ended} nothing was recorded after it for over {limit}"
                  " minutes")
    else:
        return []
    if found["completed"]:
        if "verdict" not in facts.get(item, {}):
            return []
        # verdict_rows cannot refuse here: the item is in review with no
        # pending ask and its run finished, so its problems are unused.
        failed, written, _ = recorded_verdict(
            rows, now, item, run["run_id"], facts[item]["verdict"])
        if failed is None:
            return written
        reason = failed
    recommended, why = worker_advice(rows[:rows.index(launched)], entry,
                                     launched["to"], run["band"], reason)
    written, _ = stall_rows(rows, now, entry, reason, "agent-failed",
                            recommended, why)
    return written


def _merge_gone(rows, now, entry, merging, alive):
    """Stall rows for a merge turn whose process is gone with no merged
    row (an interrupted turn), else []. A stall from `merging` resumes
    as a merge after a retry answer."""
    pid = merging.get("pid")
    if pid is None or alive(pid):
        return []
    written, _ = stall_rows(
        rows, now, entry, f"its merge turn (pid {pid}) is gone with no"
        " merged row", "runner-lost", "retry", IDLE_WHY)
    return written


def _candidate(rows, now, entry, alive, facts, policy):
    """(ready step or None, in flight?, rows to write) for one item. A
    PR the repo merged outside the batch (#938, facts["merged_pr"])
    stalls the item instead of launching its next step, once per PR;
    a `merged` answer to that stall records the PR as the merge."""
    item = entry["item"]
    found = facts.get(item, {}).get("merged_pr")
    if found is not None and landed.answered_merged(item_view(rows, item)):
        reason, fields = landed.merge(found)
        return None, False, [state_row(now, item, "stalled", landed.MERGED,
                                       reason, **fields)]
    ready, in_flight, written = _step(rows, now, entry, alive, facts,
                                      policy)
    if ready in (None, "merge") or found is None or written \
            or landed.asked(rows, item, found["pr"]):
        return ready, in_flight, written
    stalled, _ = landed_rows(rows, now, entry, found,
                             facts[item].get("unchecked"))
    return None, False, stalled


def _step(rows, now, entry, alive, facts, policy):
    """(ready step or None, in flight?, rows to write) by the item's
    state alone; _candidate applies the merged-PR rule over it."""
    found = item_view(rows, entry["item"])
    state, launched = found["state"], found["last"]
    if state in TERMINAL:
        return None, False, []
    if state == "merging":
        return None, False, _merge_gone(rows, now, entry, launched, alive)
    if state == "stalled" and found["in_flight"]:
        flying, written = _stalled_flight(rows, now, entry, launched, alive)
        return None, flying, written
    if state == "stalled":
        # A finished run's bookkeeping is `next`'s own turn (#939), and
        # a merge turn that stalled resumes as a merge, not a step.
        if found["retry"] and delivered_run(rows, found) is None:
            resume = RESUMES.get(launched["from"], launched["from"])
            if resume != "merging":
                return resume, False, []
            # The turn re-checks the cover, so a merge it would refuse
            # waits for the merge ask merge_due raises.
            blobs = facts.get(entry["item"], {}).get("gate_blobs")
            covered = blobs is not None and consent.cover(
                rows, entry["item"], blobs, policy)[0] == consent.COVERED
            return ("merge" if covered else None), False, []
        return None, False, []
    if found["pending"] is not None:
        return None, False, []
    if state == "planned":
        return entry["steps"][0]["step"], False, []
    if state == "reviewed":
        return "ship", False, []
    if state == "awaiting-gate":
        opened = found["gate"]
        return ("build" if opened and opened["choice"] == "approve"
                else None), False, []
    if "run_id" not in launched:
        return state, False, []
    if found["in_flight"]:
        flying, written = _in_flight(rows, now, entry, launched, alive)
        return None, flying, written
    if not found["completed"] or state == "review":
        return None, False, _unrecorded(rows, now, entry, found, alive,
                                        facts)
    ready, written = _after_step(rows, now, entry, launched, facts,
                                 policy)
    return ready, False, written


def survey(rows, now, wip_cap, alive, facts, policy=None):
    """(ready steps, rows to write, problems): PURE over the ledger's
    rows. Ready steps are [{"item", "step"}] in plan order, at most
    wip_cap minus the runs in flight, and none while dispatch is held.
    Rows to write are new stall and gate asks with their state moves,
    and the batch pause after FAILURE_PAUSE consecutive failed runs.
    `facts` maps an item to its branch facts (gate_blobs, unchecked);
    `policy` is the resolved standing-consent policy (None: off)."""
    plan = view(rows)["plan"]
    if plan is None:
        return None, None, ["cd: the batch ledger has no plan row"]
    writes, candidates, flying = [], [], 0
    for entry in plan["items"]:
        ready, in_flight, written = _candidate(rows + writes, now, entry,
                                               alive, facts, policy)
        writes += written
        flying += in_flight
        if ready is not None:
            candidates.append({"item": entry["item"], "step": ready})
    if _failure_streak(rows) >= FAILURE_PAUSE and not held(rows):
        asked, _ = ask_row(
            rows + writes, now, None, "stall",
            f"Three consecutive Worker runs failed in batch {plan['batch']}."
            " Resume dispatch, or stop?", PAUSE_OPTIONS, "stop",
            "three failures in a row point at the batch or the harness more"
            " than at any one item")
        writes.append(asked)
    if held(rows + writes):
        return [], writes, []
    return candidates[:max(0, wip_cap - flying)], writes, []


# --- branch facts, read through the git port ---------------------------

def _git(git, args, what):
    try:
        return git(args).stdout, []
    except CLI_FAILURES as err:
        return None, [f"cd: git {what} failed: {detail(err)}"]


def _diff_entries(git, branch):
    """([(path, blob id on the branch)], problems) for what the item
    branch changes against origin/main. NUL-separated and rename-free,
    so a path with spaces or non-ASCII characters is read whole and the
    old side of a rename is a deletion; a deleted file's blob id is
    all zeros (#1871)."""
    out, problems = _git(git, ["diff", "--raw", "-z", "--no-renames",
                               "--no-abbrev", f"origin/main...{branch}"],
                         f"diff for {branch}")
    if problems:
        return None, problems
    tokens = [token for token in out.split("\0") if token]
    return [(path, meta.split()[3]) for meta, path
            in zip(tokens[0::2], tokens[1::2])], []


def changed_files(git, branch):
    entries, problems = _diff_entries(git, branch)
    return (None, problems) if problems else (
        [path for path, _ in entries], [])


def gate_blobs(git, branch):
    """({gate path: blob id}, problems) for the gate files the item
    branch changes against origin/main. A deleted gate file carries the
    all-zero id, which no approval ever equals."""
    entries, problems = _diff_entries(git, branch)
    if problems:
        return None, problems
    return {path: blob for path, blob in entries
            if GATE_PATH.fullmatch(path)}, []


def _unchecked(row):
    return row is not None and not row["done"]


def unchecked_rows(git, branch):
    """(unchecked top-level breakdown rows, problems) from the
    breakdown.md or defect.md the item branch changes. A row is
    knowledge_plane.parse_row's — any of `-`, `*`, `+` bullets, as
    protocol counts boxes — so a build the protocol still calls
    implement is never routed to verify here."""
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
                 if not line[:1].isspace() and _unchecked(parse_row(line))]
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
