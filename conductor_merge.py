#!/usr/bin/env python3
"""conductor_merge: `conductor.py merge <batch> <item>` (PRD-0013,
WO-0160, WO-0161), split from conductor.py by capability (breakdown
assumption 6). It imports conductor.py's row grammar and
conductor_flow's state machine, which keep one owner.

The precondition is pure over the ledger's rows and the item branch's
gate blobs. An item merges only when it is reviewed with a pass verdict
from a reviewer run distinct from every author run, its ship step has
completed, and an answer covers it: its own merge ask answered `merge`,
or a train ask whose `covers` lists it answered `train`, with every
earlier item in that train already merged. An item whose branch changes
a gate file rides a train only when each gate file's blob id equals the
one approved at its gate asks; otherwise it needs its own merge ask
(ADR-0036 condition 3, as architecture.md reads it — flagged for the
Owner).
"""
import json
import re
import time
from collections import Counter
from pathlib import Path

import conductor_flow as flow
import conductor_plan
import conductor_run
from cli import CLI_FAILURES, detail, gh_read, runner
from conductor import BLOCK, answers, append, current_state, is_text, \
    load, stamp
from cost_ledger import ISSUE_KEY

# The consenting choice of a merge ask: an item's own ask, and a train
# ask that covers several items in order.
MERGE_CHOICE = "merge"
TRAIN_CHOICE = "train"


def _refused(text):
    return [f"cd: merge refused: {text}"]


def _reviewed_problems(rows, item):
    """The reviewed-pass half of the precondition: the item's last
    `reviewed` row is a pass, and its reviewer run is none of the item's
    author runs (as recorded, and every non-review run in the ledger)."""
    passes = [row for row in rows if row["kind"] == "state"
              and row["item"] == item and row["to"] == "reviewed"]
    if not passes or passes[-1].get("verdict") != "pass":
        return _refused(f"{item} has no reviewed pass")
    reviewer = passes[-1]["reviewer_run"]
    authors = set(passes[-1]["author_runs"]) | {
        row["run_id"] for row in rows if row["kind"] == "run"
        and row["item"] == item and row["step"] != "review"}
    if reviewer in authors:
        return _refused(f"{item}'s reviewer run {reviewer} is among its"
                        " author runs")
    return []


def _shipped_problems(rows, item):
    """From `ship`, the ship step's finishing run must have completed."""
    states = [row for row in rows
              if row["kind"] == "state" and row["item"] == item]
    if states[-1]["to"] != "ship":
        return []
    run_id = states[-1].get("run_id")
    finished = [row for row in rows if row["kind"] == "run"
                and run_id is not None and row["run_id"] == run_id]
    if not finished or finished[-1]["outcome"] != flow.COMPLETED:
        return _refused(f"{item}'s ship step has not completed")
    return []


def _consents(rows, item):
    """(own, trains): the merge asks covering the item whose answer
    consents — its own asks answered `merge`, and train asks listing it
    answered `train` — in ledger order."""
    given = answers(rows)
    own, trains = [], []
    for row in rows:
        if row["kind"] != "ask" or row["ask_kind"] != "merge":
            continue
        choice = (given.get(row["id"]) or {}).get("choice")
        if row["item"] == item and choice == MERGE_CHOICE:
            own.append(row)
        elif item in row.get("covers", []) and choice == TRAIN_CHOICE:
            trains.append(row)
    return own, trains


def _approved_blobs(rows, item):
    """{gate path: blob id} approved at the item's gate asks, the later
    approval winning for a path approved twice."""
    given = answers(rows)
    approved = {}
    for row in rows:
        if row["kind"] == "ask" and row["item"] == item \
                and row["ask_kind"] == "gate" \
                and (given.get(row["id"]) or {}).get("choice") == "approve":
            approved.update(row.get("gate_blobs") or {})
    return approved


def _train_problems(rows, item, train, blobs):
    covers = train["covers"]
    for earlier in covers[:covers.index(item)]:
        state = current_state(rows, earlier)
        if state != "merged":
            return _refused(f"{item} rides train {train['id']} behind"
                            f" {earlier}, which is {state}, not merged")
    approved = _approved_blobs(rows, item)
    for path in sorted(blobs):
        if approved.get(path) != blobs[path]:
            return _refused(f"{item}'s gate file {path} is not the one"
                            " approved at its gate ask; it needs its own"
                            " merge ask")
    return []


def merge_problems(rows, item, blobs):
    """Problems refusing a merge of `item`, PURE over the ledger's rows
    and `blobs` ({gate path: blob id} the item branch changes). Empty
    means the merge may proceed."""
    if flow.plan_entry(rows, item) is None:
        return [f"cd: {item} is not an item of this batch's plan"]
    problems = (_reviewed_problems(rows, item)
                or flow.transition_problems(rows, item, "merging", {})
                or _shipped_problems(rows, item))
    return problems or cover_problems(rows, item, blobs)


def cover_problems(rows, item, blobs):
    """The answer half of merge_problems: an own merge answer, or a
    train answer with the earlier items merged and the gate blobs as
    approved. Re-run after the merge turn updates the branch."""
    own, trains = _consents(rows, item)
    if own:
        return []
    if not trains:
        return _refused(f"no merge answer covers {item}")
    return _train_problems(rows, item, trains[-1], blobs)


# --- the merge turn (WO-0161) ------------------------------------------

PLUGIN = ".claude-plugin/plugin.json"
MANIFEST = "factory/manifest.json"
VERSION = re.compile(r'("version"\s*:\s*")([^"]*)(")')
SEMVER = re.compile(r"(\d+)\.(\d+)\.(\d+)")
# lean: fixed waits (architecture.md); the trigger to tune one is a
# scorecard showing it fire on a healthy batch.
WAIT_MINUTES = 30
POLL_SECONDS = 30
GREEN = ("success", "skipped", "neutral")
RETRY = "retry"
QUEUE_QUERY = ("query($owner:String!,$name:String!){repository(owner:"
               '$owner,name:$name){mergeQueue(branch:"main"){id}}}')
PREFIXES = {"prd": "PRD", "adr": "ADR", "wo": "WO"}
ADR_FILE = re.compile(r"docs/adr/(\d{4})-[^/]+")
RETRY_WHY = ("a timeout, an ejection or a failed call may be transient; the"
             " branch is left as pushed")
BLOCK_WHY = ("a non-mechanical merge failure needs a fix step or a human,"
             " not a blind retry; the branch is left as pushed")


class Stall(Exception):
    """A merge-turn step that cannot finish mechanically: the turn stops
    and queues a stall ask, recommending `retry` or `block`."""

    def __init__(self, reason, recommended=BLOCK):
        super().__init__(reason)
        self.reason, self.recommended = reason, recommended


def _git(git, worktree, args, what, recommended=BLOCK):
    try:
        return git(["-C", str(worktree), *args]).stdout
    except CLI_FAILURES as err:
        raise Stall(f"{what} failed: {detail(err)}", recommended)


def _regenerate(tool, worktree):
    try:
        tool(["python3", str(worktree / "factory_init.py"),
              "update-manifest"])
    except CLI_FAILURES as err:
        raise Stall(f"regenerating the manifest failed: {detail(err)}")


def update_branch(git, tool, worktree, branch):
    """Steps 1-2: merge origin/main into the item branch. costs.jsonl
    merges by union (.gitattributes); a conflict in the manifest alone
    is resolved by regeneration; any other conflict aborts the merge."""
    _git(git, worktree, ["fetch", "origin", "main"], "fetching origin/main",
         RETRY)
    try:
        git(["-C", str(worktree), "merge", "--no-edit", "origin/main"])
        return
    except CLI_FAILURES as err:
        failure = detail(err)
    conflicted = _git(git, worktree, ["diff", "--name-only",
                                      "--diff-filter=U"],
                      "listing conflicts").split()
    if conflicted != [MANIFEST]:
        _git(git, worktree, ["merge", "--abort"], "aborting the merge")
        raise Stall(f"merging origin/main into {branch} conflicts in"
                    f" {', '.join(conflicted)}" if conflicted
                    else f"merging origin/main into {branch} failed:"
                    f" {failure}")
    _regenerate(tool, worktree)
    _git(git, worktree, ["add", "-A", "--", "factory"],
         "staging the regenerated manifest")
    _git(git, worktree, ["commit", "--no-edit"],
         "committing the merge of origin/main")


def bump_version(git, tool, worktree, branch):
    """Step 3: when the item touched skills/, set the branch's plugin
    version to origin/main's with the patch part bumped, regenerate the
    manifest that pins it, and commit. The new version, or None."""
    changed, problems = flow.changed_files(git, branch)
    if problems:
        raise Stall(problems[0][len("cd: "):], RETRY)
    if not any(path.startswith("skills/") for path in changed):
        return None
    shown = _git(git, worktree, ["show", f"origin/main:{PLUGIN}"],
                 f"reading origin/main's {PLUGIN}")
    try:
        current = json.loads(shown).get("version")
    except (ValueError, AttributeError):
        current = None
    parts = SEMVER.fullmatch(current) if isinstance(current, str) else None
    if parts is None:
        raise Stall(f"origin/main's plugin version {current!r} is not"
                    " MAJOR.MINOR.PATCH")
    major, minor, patch = parts.groups()
    version = f"{major}.{minor}.{int(patch) + 1}"
    path = worktree / PLUGIN
    text = path.read_text(encoding="utf-8")
    bumped = VERSION.sub(lambda m: m.group(1) + version + m.group(3), text,
                         count=1)
    if bumped == text:
        return None
    path.write_text(bumped, encoding="utf-8")
    _regenerate(tool, worktree)
    _git(git, worktree, ["add", "-A", "--", PLUGIN, "factory"],
         "staging the version bump")
    _git(git, worktree, ["commit", "-m",
                         f"chore(release): plugin version {version}"],
         "committing the version bump")
    return version


def _reserved(rows, item):
    """{kind: set of numbers} the item holds, renumbered ones included."""
    held = {kind: set() for kind in PREFIXES}
    for row in rows:
        if row["kind"] == "reserve" and row["item"] == item \
                and row["what"] in held:
            held[row["what"]].update(row["values"])
    return held


def _texts(git, worktree, path):
    """(origin/main's lines, the branch's lines) of one changed path: a
    path new on the item has no main lines; a deleted one no branch
    lines. surrogateescape round-trips any bytes the rewrite keeps."""
    try:
        main = git(["show", f"origin/main:{path}"]).stdout
    except CLI_FAILURES:
        main = ""
    head = worktree / path
    text = head.read_text(encoding="utf-8", errors="surrogateescape") \
        if head.is_file() else ""
    return main.splitlines(keepends=True), text.splitlines(keepends=True)


def added_marks(main_lines, head_lines):
    """For each branch line, True when the item added it: a line is
    main's while origin/main's copy of the file still has one unclaimed."""
    remaining = Counter(main_lines)
    marks = []
    for line in head_lines:
        marks.append(remaining[line] == 0)
        remaining[line] -= 1 if remaining[line] else 0
    return marks


def _token(kind, number):
    return re.compile(rf"\b{PREFIXES[kind]}-{number:04d}\b")


def _used(held, files, new_paths):
    """{kind: numbers} of the item's block it actually used: cited in a
    line it added, or naming an ADR file it added."""
    used = {}
    for kind, numbers in held.items():
        for number in sorted(numbers):
            cited = any(_token(kind, number).search(line)
                        for lines, marks in files.values()
                        for line, added in zip(lines, marks) if added)
            named = kind == "adr" and any(
                ADR_FILE.fullmatch(path)
                and int(ADR_FILE.fullmatch(path).group(1)) == number
                for path in new_paths)
            if cited or named:
                used.setdefault(kind, []).append(number)
    return used


def _allocate(rows, on_main, collided):
    """{kind: {old: new}}: each collided number moves to the next number
    above everything on origin/main and every block in the batch."""
    moves = {}
    for kind, numbers in collided.items():
        taken = set(on_main[kind]) | {
            value for row in rows if row["kind"] == "reserve"
            and row["what"] == kind for value in row["values"]}
        top = max(taken, default=0)
        for number in numbers:
            top += 1
            if top > 9999:
                raise Stall(f"{PREFIXES[kind]}-{number:04d} is taken on"
                            " origin/main and cannot be renumbered:"
                            f" {PREFIXES[kind]}-{top} would leave the"
                            " 4-digit grammar")
            moves.setdefault(kind, {})[number] = top
    return moves


def _rewrite(line, moves, stems):
    for kind, pairs in moves.items():
        for old, new in pairs.items():
            line = _token(kind, old).sub(f"{PREFIXES[kind]}-{new:04d}",
                                         line)
    for old, new in stems.items():
        line = line.replace(old, new)
    return line


def _renumber(git, worktree, files, new_paths, moves):
    """Rename the item's ADR files and rewrite every line it added, then
    commit. Lines that are origin/main's are never touched."""
    renames = {}
    for path in new_paths:
        found = ADR_FILE.fullmatch(path)
        number = int(found.group(1)) if found else None
        if number in moves.get("adr", {}):
            renames[path] = (f"docs/adr/{moves['adr'][number]:04d}"
                             f"{path[len('docs/adr/0000'):]}")
    for old, new in renames.items():
        if (worktree / new).exists():
            raise Stall(f"{old} cannot be renumbered: {new} already exists")
        _git(git, worktree, ["mv", old, new], f"renaming {old}")
    stems = {Path(old).stem: Path(new).stem for old, new in renames.items()}
    touched = list(renames.values())
    for path, (lines, marks) in files.items():
        rewritten = [_rewrite(line, moves, stems) if added else line
                     for line, added in zip(lines, marks)]
        if rewritten != lines:
            target = renames.get(path, path)
            (worktree / target).write_text("".join(rewritten),
                                           encoding="utf-8",
                                           errors="surrogateescape")
            touched.append(target)
    _git(git, worktree, ["add", "--", *sorted(set(touched))],
         "staging the renumber")
    spans = ", ".join(f"{PREFIXES[kind]}-{old:04d} to"
                      f" {PREFIXES[kind]}-{new:04d}"
                      for kind, pairs in moves.items()
                      for old, new in pairs.items())
    _git(git, worktree, ["commit", "-m", f"chore(conductor): renumber {spans}"],
         "committing the renumber")


def confirm_reservations(rows, item, git, worktree, branch):
    """Step 4: every reserved number the item used must still be free on
    origin/main. A collision is renumbered mechanically (file name, and
    every line the item added); returns the reserve rows' fields
    ({what, values, renumbered_from}) for each renumbered kind."""
    held = _reserved(rows, item)
    if not any(held.values()):
        return []
    on_main, problems = conductor_plan.ids_on_main(git)
    if not problems:
        changed, problems = flow.changed_files(git, branch)
    if problems:
        raise Stall(problems[0][len("cd: "):], RETRY)
    files, new_paths = {}, []
    for path in changed:
        main_lines, head_lines = _texts(git, worktree, path)
        if not main_lines and head_lines:
            new_paths.append(path)
        files[path] = (head_lines, added_marks(main_lines, head_lines))
    collided = {kind: [n for n in numbers if n in on_main[kind]]
                for kind, numbers in _used(held, files, new_paths).items()}
    collided = {kind: numbers for kind, numbers in collided.items()
                if numbers}
    if not collided:
        return []
    moves = _allocate(rows, on_main, collided)
    _renumber(git, worktree, files, new_paths, moves)
    return [{"what": kind, "values": list(pairs.values()),
             "renumbered_from": list(pairs)}
            for kind, pairs in moves.items()]


def _read(gh, args, operation, expect=dict):
    """A gh read's value, or a retry stall naming why it failed."""
    result = gh_read(args, operation, run=gh, expect=expect)
    if result.problems:
        raise Stall(result.problems[0], RETRY)
    return result.value


def _pr_number(gh, branch):
    listed = _read(gh, ["pr", "list", "--head", branch, "--state", "open",
                        "--json", "number"], "gh pr list", expect=list)
    if len(listed) != 1 or not isinstance(listed[0], dict) \
            or not isinstance(listed[0].get("number"), int):
        raise Stall(f"{branch} has {len(listed)} open PRs, not one")
    return listed[0]["number"]


def _check_runs(value):
    runs = value.get("check_runs")
    if not (isinstance(runs, list) and all(
            isinstance(run, dict) and is_text(run.get("name"))
            for run in runs)):
        raise Stall("gh api check-runs returned unreadable check runs",
                    RETRY)
    return runs


def wait_checks(gh, sha, clock, sleep):
    """Step 7: {check name: conclusion} once every check run on the new
    head has completed green. A red run stalls at once; none finishing
    within WAIT_MINUTES stalls as a timeout."""
    started = clock()
    while True:
        runs = _check_runs(_read(
            gh, ["api", f"repos/{{owner}}/{{repo}}/commits/{sha}/check-runs"
                 "?per_page=100"], f"gh api check-runs for {sha[:12]}"))
        red = sorted(run["name"] for run in runs
                     if run.get("status") == "completed"
                     and run.get("conclusion") not in GREEN)
        if red:
            raise Stall(f"checks failed on {sha[:12]}: {', '.join(red)}")
        if runs and all(run.get("status") == "completed" for run in runs):
            return {run["name"]: run["conclusion"] for run in runs}
        if (clock() - started).total_seconds() >= WAIT_MINUTES * 60:
            raise Stall(f"checks on {sha[:12]} did not finish within"
                        f" {WAIT_MINUTES} minutes", RETRY)
        sleep(POLL_SECONDS)


def has_queue(gh):
    """True when main has a merge queue (mergeQueue(branch: "main") is
    non-null), read at merge time."""
    value = _read(gh, ["api", "graphql", "-f", f"query={QUEUE_QUERY}",
                       "-F", "owner={owner}", "-F", "name={repo}"],
                  "gh api graphql mergeQueue")
    repository = (value.get("data") or {}).get("repository")
    if not isinstance(repository, dict):
        raise Stall("gh api graphql mergeQueue named no repository", RETRY)
    return repository.get("mergeQueue") is not None


def land(gh, pr, head, queued, clock, sleep):
    """Step 8: squash-merge the checked head, or, with a queue, enqueue
    it (gh pr merge enqueues when main requires a queue, which then owns
    the strategy) and wait for merged or ejected. The merge sha."""
    try:
        gh(["pr", "merge", str(pr), "--squash", "--match-head-commit",
            head])
    except CLI_FAILURES as err:
        raise Stall(f"gh pr merge #{pr} failed: {detail(err)}", RETRY)
    started = clock()
    while True:
        view = _read(gh, ["pr", "view", str(pr), "--json",
                          "state,mergeCommit,isInMergeQueue"],
                     f"gh pr view #{pr}")
        state = view.get("state")
        if state == "MERGED":
            sha = (view.get("mergeCommit") or {}).get("oid")
            if not is_text(sha):
                raise Stall(f"PR #{pr} merged with no merge commit sha",
                            RETRY)
            return sha
        if state != "OPEN":
            raise Stall(f"PR #{pr} is {str(state).lower()}, not merged")
        if not queued:
            raise Stall(f"PR #{pr} is still open after gh pr merge", RETRY)
        if not view.get("isInMergeQueue"):
            raise Stall(f"PR #{pr} was ejected from the merge queue")
        if (clock() - started).total_seconds() >= WAIT_MINUTES * 60:
            raise Stall(f"PR #{pr} did not merge from the queue within"
                        f" {WAIT_MINUTES} minutes", RETRY)
        sleep(POLL_SECONDS)


def _reserve(root, batch, clock, item, fields):
    _, problems = append(root, batch, lambda rows: (
        [{"at": stamp(clock()), "kind": "reserve", "item": item, **one}
         for one in fields], []))
    return problems


def _turn(root, batch, item, ports, worktree):
    """Steps 1-8 on a turn already moved to `merging`. (pr, sha, checks),
    or raises Stall; ledger problems are returned as the last value."""
    git, gh, tool, clock, sleep = ports
    branch = flow.item_branch(batch, item)
    update_branch(git, tool, worktree, branch)
    version = bump_version(git, tool, worktree, branch)
    rows, problems = load(root, batch)
    if problems:
        return None, problems
    renumbered = confirm_reservations(rows, item, git, worktree, branch)
    fields = renumbered + ([{"what": "plugin-version",
                             "values": [version]}] if version else [])
    problems = _reserve(root, batch, clock, item, fields) if fields else []
    if problems:
        return None, problems
    blobs, problems = flow.gate_blobs(git, branch)
    if problems:
        raise Stall(problems[0][len("cd: "):], RETRY)
    changed = cover_problems(rows, item, blobs)
    if changed:
        raise Stall(changed[0][len("cd: "):])
    try:
        tool(["make", "-C", str(worktree), "check"])
    except CLI_FAILURES as err:
        raise Stall(f"make check failed on {branch}: {detail(err)}")
    _git(git, worktree, ["push", "origin", branch], f"pushing {branch}",
         RETRY)
    head = _git(git, worktree, ["rev-parse", "HEAD"], "reading HEAD").strip()
    pr = _pr_number(gh, branch)
    checks = wait_checks(gh, head, clock, sleep)
    sha = land(gh, pr, head, has_queue(gh), clock, sleep)
    return {"pr": pr, "sha": sha, "checks": checks}, []


def merge_turn(root, batch, item, clock, git, gh, tool, sleep):
    """(summary, problems): one merge turn. problems when the
    precondition refuses (nothing is touched) or a ledger write fails;
    a turn that cannot finish mechanically queues a stall ask and leaves
    the branch as pushed — never a forced push, never a retry."""
    rows, problems = load(root, batch)
    if problems:
        return None, problems
    blobs, problems = flow.gate_blobs(git, flow.item_branch(batch, item))
    if problems:
        return None, problems
    problems = merge_problems(rows, item, blobs)
    if problems:
        return None, problems
    worktree, problems = conductor_run.worktree_path(git, batch, item)
    if not problems and not worktree.is_dir():
        problems = [f"cd: no item worktree at {worktree}"]
    if problems:
        return None, problems
    _, problems = flow.move(root, batch, clock(), item, "merging",
                            "merge turn")
    if problems:
        return None, problems
    try:
        merged, problems = _turn(root, batch, item,
                                 (git, gh, tool, clock, sleep), worktree)
    except Stall as stall:
        _, problems = flow.queue_stall(
            root, batch, clock(), item, stall.reason, stall.recommended,
            RETRY_WHY if stall.recommended == RETRY else BLOCK_WHY)
        return {"item": item, "stall": stall.reason}, problems
    if problems:
        return None, problems
    _, problems = flow.move(root, batch, clock(), item, "merged",
                            f"merged as {merged['sha']}", **merged)
    return {"item": item, "stall": None, **merged}, problems


def merge_cli(root, args, clock, git, gh, tool=None, sleep=None):
    if len(args) != 2 or not ISSUE_KEY.fullmatch(args[1]):
        return None
    summary, problems = merge_turn(
        root, args[0], args[1], clock, git, gh,
        tool or (lambda argv: runner(argv[0])(argv[1:])),
        sleep or time.sleep)
    if summary is not None:
        print(f"cd: merge of {summary['item']} stalled: {summary['stall']}"
              if summary["stall"] else
              f"cd: merged {summary['item']} as {summary['sha']}"
              f" (PR #{summary['pr']})")
    return problems
