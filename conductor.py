#!/usr/bin/env python3
"""conductor: the Conductor's batch tool (PRD-0013) and the batch
ledger's one owner.

The `conduct` skill's compute half, in work_queue.py's conventions: pure
functions with every input passed in, a thin main, cd:-prefixed problem
strings, cli.report for the exit. Root-only: not mirrored into the
factory payload (architecture.md).

  python3 conductor.py plan <#N>...
        Price and order a batch of issues and show each item's reserved
        number block. Writes nothing.
  python3 conductor.py open <batch> <#N>...
        Plan, then create the conductor/<batch> branch and worktree from
        origin/main, write the plan and reserve rows, and queue the spend
        ask.
  python3 conductor.py next <batch>
        The oldest unanswered ask, as JSON ({"ask": row or null}).
  python3 conductor.py ask <batch> --kind K --question Q --option O
                           [--option O ...] --recommended O --why W
                           [--item #N] [--covers #N ...]
        Append an ask row with a fresh id and print the id.
  python3 conductor.py answer <batch> <ask-id> <choice> [--note TEXT]
        Append the Owner's answer row. Written only straight after the
        Owner picks that option in this session; refused for any call
        with CONDUCTOR_WORKER set.

The batch ledger (docs/factory/batches/<batch>/ledger.jsonl) is
append-only JSONL. Every row has `at`, `kind` and `item`; ROW_FIELDS
holds each kind's own fields. A line that does not parse, or breaks its
kind's rules, fails the reader with its file and line: it is never
skipped, because "could not read" must not read as "nothing to do".
"""
import fcntl
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import assembler
import factory_config
import work_queue
from cli import (CLI_FAILURES, detail, gh_read, gh_runner, label_names,
                 report, runner)
from cost_ledger import ISSUE_KEY
from knowledge_plane import ADR_TOKEN, PRD_TOKEN, WO_TOKEN, repo_root

LEDGER = "docs/factory/batches/{batch}/ledger.jsonl"
BATCH_NAME = re.compile(r"[a-z0-9][a-z0-9-]*")
AT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
AT_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
WORKER_ENV = "CONDUCTOR_WORKER"

# kind -> (required fields, optional fields), beyond at/kind/item: the
# architecture's batch-ledger table. An ask's own kind is `ask_kind`,
# since the row's `kind` is already "ask".
ROW_FIELDS = {
    "plan": (("batch", "items", "policy", "estimate_usd",
              "month_to_date_usd", "cap_usd"), ()),
    "reserve": (("what", "values"), ("renumbered_from",)),
    "state": (("from", "to", "reason"),
              ("verdict", "author_runs", "reviewer_run", "pr", "sha",
               "checks")),
    "run": (("step", "charter", "band", "model", "models_reported",
             "effort", "run_id", "pid", "outcome"), ()),
    "ask": (("id", "ask_kind", "question", "options", "recommended",
             "why"), ("covers", "gate_blobs")),
    "answer": (("ask", "choice", "note"), ()),
    "close": (("merged", "blocked"), ()),
}
COMMON_FIELDS = ("at", "kind", "item")
# A state row into these states carries the fields that prove it.
STATE_FIELDS = {"reviewed": ("author_runs", "reviewer_run", "verdict"),
                "merged": ("checks", "pr", "sha")}
ASK_KINDS = ("spend", "gate", "merge", "stall", "clarify")


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _ask_problems(row):
    problems = []
    if row.get("ask_kind") not in ASK_KINDS:
        problems.append(f"ask_kind {row.get('ask_kind')!r} is not one of"
                        f" {', '.join(ASK_KINDS)}")
    options = row.get("options")
    if not (isinstance(options, list) and options
            and all(_text(option) for option in options)
            and len(set(options)) == len(options)):
        problems.append("options must be a non-empty list of distinct"
                        " non-empty strings")
    elif row.get("recommended") not in options:
        problems.append(f"recommended {row.get('recommended')!r} is not"
                        " among the options")
    problems += [f"{field} must be a non-empty string"
                 for field in ("question", "why") if not _text(row[field])]
    return problems


def _answer_problems(row):
    problems = [f"{field} must be a non-empty string"
                for field in ("ask", "choice") if not _text(row[field])]
    if not isinstance(row["note"], str):
        problems.append("note must be a string")
    return problems


def _at_problems(value):
    valid = isinstance(value, str) and AT.fullmatch(value)
    if valid:
        try:
            datetime.strptime(value, AT_FORMAT)
        except ValueError:
            valid = False
    if valid:
        return []
    return [f"at {value!r} is not a UTC timestamp (YYYY-MM-DDTHH:MM:SSZ)"]


def row_problems(row):
    """Unlocated problems for one parsed ledger row: its kind, its field
    set, then its kind's value rules. The one rule every reader and
    writer of the ledger applies."""
    kind = row.get("kind")
    if kind not in ROW_FIELDS:
        return [f"kind {kind!r} is not a batch ledger row kind"]
    required, optional = ROW_FIELDS[kind]
    problems = []
    missing = sorted(set(COMMON_FIELDS + required) - set(row))
    if missing:
        problems.append(f"{kind} row is missing field(s):"
                        f" {', '.join(missing)}")
    unknown = sorted(set(row) - set(COMMON_FIELDS + required + optional))
    if unknown:
        problems.append(f"{kind} row has unknown field(s):"
                        f" {', '.join(unknown)}")
    if missing:
        return problems
    problems += _at_problems(row["at"])
    item = row["item"]
    if item is not None and not (isinstance(item, str)
                                 and ISSUE_KEY.fullmatch(item)):
        problems.append(f"item {item!r} is not an issue key (#<n>) or null")
    if kind == "state" and row["to"] in STATE_FIELDS:
        absent = [field for field in STATE_FIELDS[row["to"]]
                  if field not in row]
        if absent:
            problems.append(f"state row to {row['to']} is missing"
                            f" field(s): {', '.join(absent)}")
    if kind == "ask":
        problems += _ask_problems(row)
    if kind == "answer":
        problems += _answer_problems(row)
    return problems


def parse(text, shown):
    """(rows, problems) for a ledger's text: every non-blank line parsed
    and checked, problems located as `cd: <shown>:<lineno> <suffix>`.
    Rows are None when any line has a problem: the reader fails, it never
    skips a line."""
    rows, problems = [], []
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except (ValueError, RecursionError) as err:
            problems.append(f"cd: {shown}:{lineno} is not valid JSON: {err}")
            continue
        if not isinstance(row, dict):
            problems.append(f"cd: {shown}:{lineno} is not a JSON object")
            continue
        problems += [f"cd: {shown}:{lineno} {suffix}"
                     for suffix in row_problems(row)]
        rows.append(row)
    return (None, problems) if problems else (rows, [])


def _ledger(root, batch):
    """(path, shown, problems) for a batch's ledger. The batch name lands
    in a path, so anything but a slug is refused before it is used."""
    if not (isinstance(batch, str) and BATCH_NAME.fullmatch(batch)):
        return None, None, [f"cd: batch {batch!r} is not a batch name"
                            " (lowercase letters, digits and hyphens)"]
    shown = LEDGER.format(batch=batch)
    path = Path(root) / shown
    if not path.is_file():
        return None, shown, [f"cd: no batch ledger at {shown}"]
    return path, shown, []


def _read_locked(handle, shown):
    handle.seek(0)
    try:
        text = handle.read()
    except UnicodeDecodeError as err:
        return None, [f"cd: cannot read {shown}: {err}"]
    return parse(text, shown)


def load(root, batch):
    """(rows, problems): every row of the batch's ledger, in order, read
    under a shared lock so a concurrent append is never seen half
    written. rows is None on any problem."""
    path, shown, problems = _ledger(root, batch)
    if problems:
        return None, problems
    try:
        with open(path, encoding="utf-8") as handle:
            fcntl.flock(handle, fcntl.LOCK_SH)
            return _read_locked(handle, shown)
    except OSError as err:
        return None, [f"cd: cannot read {shown}: {err}"]


def append(root, batch, build):
    """(row, problems): build the next row from the ledger's current rows
    and append it, holding an exclusive lock across the read and the
    write so concurrent runners serialise. build(rows) returns (row,
    problems); a row that breaks the grammar is refused, and nothing is
    written on any problem. Never creates a ledger: `open` does."""
    path, shown, problems = _ledger(root, batch)
    if problems:
        return None, problems
    try:
        with open(path, "a+", encoding="utf-8") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            rows, problems = _read_locked(handle, shown)
            if problems:
                return None, problems
            row, problems = build(rows)
            if problems:
                return None, problems
            handle.seek(0, os.SEEK_END)
            handle.write(json.dumps(row) + "\n")
            return row, []
    except OSError as err:
        return None, [f"cd: cannot write {shown}: {err}"]


def _stamp(now):
    return now.astimezone(timezone.utc).strftime(AT_FORMAT)


def _answers(rows):
    return {row["ask"]: row for row in rows if row["kind"] == "answer"}


def next_ask(rows):
    """The oldest unanswered ask row, or None: the decision queue shows
    one question at a time."""
    answered = _answers(rows)
    return next((row for row in rows
                 if row["kind"] == "ask" and row["id"] not in answered),
                None)


def ask(root, batch, now, item, ask_kind, question, options, recommended,
        why, covers=None):
    """(row, problems): append an ask row with a fresh id (ask-<n>, one
    past the batch's ask count)."""
    def build(rows):
        count = sum(1 for row in rows if row["kind"] == "ask")
        row = {"at": _stamp(now), "kind": "ask", "item": item,
               "id": f"ask-{count + 1}", "ask_kind": ask_kind,
               "question": question, "options": list(options),
               "recommended": recommended, "why": why}
        if covers:
            row["covers"] = list(covers)
        return row, [f"cd: ask refused: {problem}"
                     for problem in row_problems(row)]
    return append(root, batch, build)


def answer(root, batch, now, ask_id, choice, note, env):
    """(row, problems): append the Owner's answer to one ask. Refused for
    an unknown ask, an answered ask, a choice outside its options, and
    any call made with CONDUCTOR_WORKER set. That flag stops a confused
    Worker, not a hostile one; the trigger to harden it is an answer row
    whose timing matches no Owner turn."""
    if env.get(WORKER_ENV):
        return None, [f"cd: answer refused: {WORKER_ENV} is set, and a"
                      " Worker never answers an ask"]

    def build(rows):
        asked = next((row for row in rows if row["kind"] == "ask"
                      and row["id"] == ask_id), None)
        if asked is None:
            return None, [f"cd: no ask {ask_id} in this batch"]
        given = _answers(rows).get(ask_id)
        if given is not None:
            return None, [f"cd: ask {ask_id} is already answered"
                          f" ({given['choice']!r})"]
        if choice not in asked["options"]:
            return None, [f"cd: {choice!r} is not an option of ask"
                          f" {ask_id} ({', '.join(asked['options'])})"]
        return {"at": _stamp(now), "kind": "answer", "item": asked["item"],
                "ask": ask_id, "choice": choice, "note": note}, []
    return append(root, batch, build)


# --- plan and open -----------------------------------------------------
# The policy below was accepted by the Owner on 2026-10-10 (breakdown.md
# Notes): steps per item type, the step-to-charter table, the type labels,
# and the reserved block sizes.

ITEM_STEPS = {"feature": ("spec", "build", "verify", "review", "ship"),
              "fix": ("spec", "build", "verify", "review", "ship"),
              "order": ("build", "verify", "review", "ship")}
# step -> charter, fixed here as assembler.CHARTER_BY_TYPE fixes type ->
# charter; `build` runs whatever charter the issue's type: label selects.
STEP_CHARTERS = {"spec": "architect", "verify": "qa", "review": "reviewer",
                 "ship": "qa"}
TYPE_BY_LABEL = {"type:feature": "feature", "type:defect": "fix",
                 "type:chore": "fix"}
# lean: fixed block sizes per item type. The ceiling is an item that
# needs more numbers than its block; its Worker stops and says so. The
# trigger to size blocks per item is a scorecard showing that stop fire.
BLOCK_SIZES = {"feature": {"prd": 1, "adr": 3, "wo": 10},
               "fix": {"adr": 1, "wo": 5},
               "order": {}}
ID_TOKENS = (("prd", PRD_TOKEN), ("adr", ADR_TOKEN), ("wo", WO_TOKEN))
# docs/ only: tests and fixtures carry example ids in the nine-thousands
# that no run ever used, and a block above them would leave the 4-digit
# grammar.
ID_GREP = ["grep", "-h", "-o", "-E", "(PRD|ADR|WO)-[0-9]{4}", "origin/main",
           "--", "docs"]
ISSUE_FIELDS = "number,state,author,labels"
WORKTREES = ".claude/worktrees"
SPEND_OPTIONS = ["approve", "decline"]


def ids_in_use(git):
    """({kind: highest number}, problems) for the PRD, ADR and WO ids on
    origin/main, through knowledge_plane's token grammars. Over-counts
    any id merely cited, which is the safe direction. grep's exit 1 is
    "no match", so every kind is 0."""
    try:
        text = git(ID_GREP).stdout
    except subprocess.CalledProcessError as err:
        if err.returncode != 1:
            return None, [f"cd: git grep origin/main failed: {detail(err)}"]
        text = ""
    except CLI_FAILURES as err:
        return None, [f"cd: git grep origin/main failed: {detail(err)}"]
    return {kind: max((int(match.group(0)[-4:])
                       for match in token.finditer(text)), default=0)
            for kind, token in ID_TOKENS}, []


def repo_owner(run):
    """(the repo owner's login, problems), failing closed."""
    result = gh_read(["repo", "view", "--json", "owner"], "gh repo view",
                     "cd", run=run, expect=dict)
    if result.problems:
        return None, result.problems
    login = (result.value.get("owner") or {}).get("login")
    if not _text(login):
        return None, ["cd: gh repo view names no owner"]
    return login, []


def read_issues(numbers, run):
    """(issues, problems): one read per issue. Any failed or incomplete
    read refuses the whole batch: "could not ask" never reads as
    "nothing to do"."""
    issues, problems = [], []
    for number in numbers:
        operation = f"gh issue view #{number}"
        result = gh_read(["issue", "view", str(number), "--json",
                          ISSUE_FIELDS], operation, "cd", run=run,
                         expect=dict)
        if result.problems:
            problems += result.problems
            continue
        value = result.value
        if not (all(field in value for field in ISSUE_FIELDS.split(","))
                and isinstance(value["labels"], list)
                and isinstance(value["author"], dict)):
            problems.append(f"cd: {operation} returned an incomplete issue")
            continue
        issues.append(value)
    return (None, problems) if problems else (issues, [])


def _deferral(issue, labels, owner):
    """(item type, size, reason): reason is None for a plannable issue."""
    if (issue["state"] or "").upper() != "OPEN":
        return None, None, "closed"
    author = issue["author"].get("login")
    if author != owner:
        return None, None, (f"authored by {author}, not the repo owner"
                            f" {owner}")
    if assembler.READY_LABEL in labels:
        item_type = "order"
    else:
        typed = [name for name in labels if name.startswith("type:")]
        if not typed:
            return None, None, "no type: label"
        if typed[0] not in TYPE_BY_LABEL:
            return None, None, f"{typed[0]} is not plannable"
        item_type = TYPE_BY_LABEL[typed[0]]
    size = next((name[len("size:"):] for name in labels
                 if name in ("size:S", "size:M", "size:L")), None)
    if size is None:
        return None, None, "no size: label"
    return item_type, size, None


def _steps(item_type, labels, config, agents_dir, ceiling):
    """(the item's priced steps, problems): step, charter, band, then
    (model, effort) from policy."""
    steps, problems = [], []
    for step in ITEM_STEPS[item_type]:
        charter = STEP_CHARTERS.get(step) or assembler.select_charter(labels)
        band, found = assembler.charter_band(agents_dir, charter)
        problems += found
        if band is None:
            continue
        model, found = factory_config.resolve_model(band, config)
        problems += found
        effort, found = factory_config.resolve_effort(band, config)
        problems += found
        steps.append({"step": step, "charter": charter, "band": band,
                      "model": model, "effort": effort,
                      "ceiling_usd": ceiling})
    return steps, problems


def plan_batch(issues, owner, config, spent, highest, agents_dir):
    """(plan, problems): PURE over already-read inputs. Each plannable
    issue becomes an item priced from budgets_usd by its size, split
    equally across its steps as their ceilings, with a reserved block
    above the highest id in use and above every earlier block. Every
    other issue is one deferral line. A config problem plans nothing."""
    cap, problems = factory_config.resolve_cap(config)
    if problems:
        return None, problems
    next_free = {kind: highest[kind] + 1 for kind in highest}
    items, deferred, total = [], [], 0
    for issue in issues:
        key = f"#{issue['number']}"
        labels = label_names(issue)
        item_type, size, reason = _deferral(issue, labels, owner)
        if reason is None:
            estimate, found = factory_config.resolve_budget(size, config)
            problems += found
            if found:
                continue
            left = cap - spent - total
            if estimate > left:
                reason = (f"its ${estimate:.2f} estimate is over the"
                          f" ${left:.2f} left of the ${cap:.2f} monthly cap")
        if reason is not None:
            deferred.append(f"{key} deferred: {reason}")
            continue
        steps, found = _steps(item_type, labels, config, agents_dir,
                              round(estimate / len(ITEM_STEPS[item_type]),
                                    2))
        for problem in found:
            if problem not in problems:
                problems.append(problem)
        block = {}
        for kind, count in BLOCK_SIZES[item_type].items():
            block[kind] = list(range(next_free[kind],
                                     next_free[kind] + count))
            next_free[kind] += count
        total += estimate
        items.append({"item": key, "type": item_type, "size": size,
                      "steps": steps, "estimate_usd": estimate, "after": [],
                      "block": block})
    if problems:
        return None, problems
    return {"items": items, "deferred": deferred, "estimate_usd": total,
            "month_to_date_usd": spent, "cap_usd": cap,
            "policy": {"routing": config.get("routing"),
                       "effort": config.get("effort")}}, []


def _span(values):
    return (str(values[0]) if len(values) == 1
            else f"{values[0]}-{values[-1]}")


def compose_plan(plan):
    """The plan as report lines: per item its steps and block, then the
    batch estimate against the cap, then one line per deferral."""
    lines = [f"cd: {len(plan['items'])} item(s) planned"]
    for item in plan["items"]:
        block = ", ".join(f"{kind} {_span(values)}"
                          for kind, values in item["block"].items())
        lines.append(f"  {item['item']}  {item['type']}  size:{item['size']}"
                     f"  ${item['estimate_usd']:.2f}"
                     f"  reserves {block or 'nothing'}")
        lines += [f"    {s['step']:<6}  {s['charter']:<9}  {s['band']:<19}"
                  f"  {s['model']}  {s['effort']}  ${s['ceiling_usd']:.2f}"
                  for s in item["steps"]]
    left = plan["cap_usd"] - plan["month_to_date_usd"]
    lines.append(f"  batch estimate ${plan['estimate_usd']:.2f} against"
                 f" ${left:.2f} left of the ${plan['cap_usd']:.2f}"
                 " monthly cap")
    lines += [f"  {line}" for line in plan["deferred"]]
    return lines


def open_batch(root, batch, plan, now, git):
    """(the batch worktree, problems): create conductor/<batch> and its
    worktree from origin/main, write the plan row and one reserve row per
    block, and queue the spend ask. Refuses an empty plan, a bad batch
    name and an existing worktree before git runs."""
    if not (isinstance(batch, str) and BATCH_NAME.fullmatch(batch)):
        return None, [f"cd: batch {batch!r} is not a batch name"
                      " (lowercase letters, digits and hyphens)"]
    if not plan["items"]:
        return None, ["cd: nothing to open: every issue was deferred"]
    shown = f"{WORKTREES}/conductor-{batch}"
    worktree = Path(root) / shown
    if worktree.exists():
        return None, [f"cd: {shown} already exists"]
    try:
        git(["worktree", "add", "-b", f"conductor/{batch}", str(worktree),
             "origin/main"])
    except CLI_FAILURES as err:
        return None, [f"cd: git worktree add failed: {detail(err)}"]
    at = _stamp(now)
    rows = [{"at": at, "kind": "plan", "item": None, "batch": batch,
             "items": [{key: value for key, value in item.items()
                        if key != "block"} for item in plan["items"]],
             "policy": plan["policy"], "estimate_usd": plan["estimate_usd"],
             "month_to_date_usd": plan["month_to_date_usd"],
             "cap_usd": plan["cap_usd"]}]
    rows += [{"at": at, "kind": "reserve", "item": item["item"],
              "what": kind, "values": values}
             for item in plan["items"]
             for kind, values in item["block"].items()]
    ledger = worktree / LEDGER.format(batch=batch)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger, "x", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        handle.write("".join(json.dumps(row) + "\n" for row in rows))
    left = plan["cap_usd"] - plan["month_to_date_usd"]
    estimate = plan["estimate_usd"]
    _, problems = ask(
        worktree, batch, now, None, "spend",
        f"Spend up to ${estimate:.2f} on batch {batch}"
        f" ({len(plan['items'])} item(s))?", SPEND_OPTIONS, "approve",
        f"the ${estimate:.2f} estimate fits the ${left:.2f} left of the"
        f" ${plan['cap_usd']:.2f} monthly cap")
    return worktree, problems


def _plan(root, numbers, now, run, git):
    """(plan, problems): read every input, then plan_batch."""
    config, problems = factory_config.load(root)
    if problems:
        return None, problems
    owner, problems = repo_owner(run)
    if problems:
        return None, problems
    issues, problems = read_issues(numbers, run)
    if problems:
        return None, problems
    spent, problems = work_queue.month_to_date(root, now)
    if problems:
        return None, problems
    highest, problems = ids_in_use(git)
    if problems:
        return None, problems
    return plan_batch(issues, owner, config, spent, highest,
                      Path(root) / "factory" / "agents")


def _issue_numbers(args):
    if not args or not all(ISSUE_KEY.fullmatch(arg) for arg in args):
        return None
    return [int(arg[1:]) for arg in args]


def _plan_cli(root, args, now, run, git):
    numbers = _issue_numbers(args)
    if numbers is None:
        return None
    plan, problems = _plan(root, numbers, now, run, git)
    if plan is not None:
        print("\n".join(compose_plan(plan)))
    return problems


def _open_cli(root, args, now, run, git):
    numbers = _issue_numbers(args[1:])
    if numbers is None:
        return None
    plan, problems = _plan(root, numbers, now, run, git)
    if plan is None:
        return problems
    print("\n".join(compose_plan(plan)))
    worktree, problems = open_batch(root, args[0], plan, now, git)
    if worktree is not None:
        print(f"cd: opened {worktree}")
    return problems


def _flags(args, repeatable):
    """{flag: value or [values]} for `--flag value` pairs, or None when
    the args are not such pairs."""
    if len(args) % 2:
        return None
    flags = {}
    for flag, value in zip(args[::2], args[1::2]):
        if not flag.startswith("--"):
            return None
        if flag in repeatable:
            flags.setdefault(flag, []).append(value)
        elif flag in flags:
            return None
        else:
            flags[flag] = value
    return flags


def _ask_cli(root, batch, args, now):
    flags = _flags(args, ("--option", "--covers"))
    needed = ("--kind", "--question", "--option", "--recommended", "--why")
    if flags is None or any(flag not in flags for flag in needed) or set(
            flags) - set(needed) - {"--item", "--covers"}:
        return None
    row, problems = ask(root, batch, now, flags.get("--item"),
                        flags["--kind"], flags["--question"],
                        flags["--option"], flags["--recommended"],
                        flags["--why"], covers=flags.get("--covers"))
    if row is not None:
        print(row["id"])
    return problems


def _answer_cli(root, batch, args, now, env):
    if len(args) < 2:
        return None
    flags = _flags(args[2:], ())
    if flags is None or set(flags) - {"--note"}:
        return None
    _, problems = answer(root, batch, now, args[0], args[1],
                         flags.get("--note", ""), env)
    return problems


def _next_cli(root, batch, args):
    if args:
        return None
    rows, problems = load(root, batch)
    if rows is not None:
        print(json.dumps({"ask": next_ask(rows)}, indent=2))
    return problems


def main(argv, env=None, clock=None, root=None, run=gh_runner, git=None):
    env = os.environ if env is None else env
    now = (clock or (lambda: datetime.now(timezone.utc)))()
    root = root or repo_root()
    git = git or runner("git")
    problems = None
    if argv[:1] == ["plan"]:
        problems = _plan_cli(root, argv[1:], now, run, git)
    elif argv[:1] == ["open"] and len(argv) >= 3:
        problems = _open_cli(root, argv[1:], now, run, git)
    elif len(argv) >= 2:
        command, batch, args = argv[0], argv[1], argv[2:]
        if command == "next":
            problems = _next_cli(root, batch, args)
        elif command == "ask":
            problems = _ask_cli(root, batch, args, now)
        elif command == "answer":
            problems = _answer_cli(root, batch, args, now, env)
    if problems is None:
        print(__doc__.strip())
        return 2
    return report("cd", problems)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
