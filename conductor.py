#!/usr/bin/env python3
"""conductor: the Conductor's batch tool (PRD-0013) and the batch
ledger's one owner.

The `conduct` skill's compute half, in work_queue.py's conventions: pure
functions with every input passed in, a thin main, cd:-prefixed problem
strings, cli.report for the exit. Root-only: not mirrored into the
factory payload (architecture.md). Capabilities that would push this
file past the 800-line ceiling live in sibling modules that import its
row grammar (breakdown assumption 6): conductor_plan (plan, open).

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
import sys
from datetime import datetime, timezone
from pathlib import Path

from cli import gh_runner, report, runner
from cost_ledger import ISSUE_KEY
from knowledge_plane import repo_root

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


def is_text(value):
    return isinstance(value, str) and bool(value.strip())


def _ask_problems(row):
    problems = []
    if row.get("ask_kind") not in ASK_KINDS:
        problems.append(f"ask_kind {row.get('ask_kind')!r} is not one of"
                        f" {', '.join(ASK_KINDS)}")
    options = row.get("options")
    if not (isinstance(options, list) and options
            and all(is_text(option) for option in options)
            and len(set(options)) == len(options)):
        problems.append("options must be a non-empty list of distinct"
                        " non-empty strings")
    elif row.get("recommended") not in options:
        problems.append(f"recommended {row.get('recommended')!r} is not"
                        " among the options")
    problems += [f"{field} must be a non-empty string"
                 for field in ("question", "why") if not is_text(row[field])]
    return problems


def _answer_problems(row):
    problems = [f"{field} must be a non-empty string"
                for field in ("ask", "choice") if not is_text(row[field])]
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


def stamp(now):
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
        row = {"at": stamp(now), "kind": "ask", "item": item,
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
        return {"at": stamp(now), "kind": "answer", "item": asked["item"],
                "ask": ask_id, "choice": choice, "note": note}, []
    return append(root, batch, build)


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
    # The capability siblings import this module's row grammar, so they
    # are imported here, not at the top: one owner, no import cycle.
    import conductor_plan
    problems = None
    if argv[:1] == ["plan"]:
        problems = conductor_plan.plan_cli(root, argv[1:], now, run, git)
    elif argv[:1] == ["open"] and len(argv) >= 3:
        problems = conductor_plan.open_cli(root, argv[1:], now, run, git)
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
