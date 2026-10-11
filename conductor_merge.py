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
import conductor_flow as flow
from conductor import answers, current_state

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
    if problems:
        return problems
    own, trains = _consents(rows, item)
    if own:
        return []
    if not trains:
        return _refused(f"no merge answer covers {item}")
    return _train_problems(rows, item, trains[-1], blobs)
