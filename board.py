#!/usr/bin/env python3
"""board: the pipeline-board model — every active run placed on its own
ladder — as one JSON document on stdout (feature:pipeline-board).

Facts only, per ADR-0062: the pipeline-board skill renders this output
verbatim and derives nothing. A run appears in `runs` or `attention`,
never both and never neither; completed runs (retro.md) appear nowhere.
Same seam discipline as orientation_pack: functions take `root` and
read real files under it, tested against tempfile fixture trees.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import cli
from knowledge_plane import run_dirs
from protocol import (MAINTENANCE_STAGE_ARTIFACTS, STAGE_ARTIFACTS,
                      breakdown_path, checkbox_progress, run_ref,
                      stage_states)

# Any stage artifact marks a run as begun — the protocol's "at least
# one artifact" half of active, derived from the tables so a new stage
# row is picked up here without a second list.
_ARTIFACTS = sorted({artifact for _, artifact
                     in STAGE_ARTIFACTS + MAINTENANCE_STAGE_ARTIFACTS})


def _reason(err):
    """A per-run failure as one bounded line for the attention strip."""
    text = " ".join(str(err).split()) or type(err).__name__
    return text[:300]


def _position(ladder):
    """How far along its own ladder the current stage sits, 0.0..1.0 —
    ladders differ in length across run kinds, so the fraction is what
    "furthest along" means when sorting them together."""
    for index, row in enumerate(ladder):
        if row["state"] == "current":
            return index / max(len(ladder) - 1, 1)
    return 1.0


def _run_entry(root, run_dir):
    """One active run as the model's contract fields. Raises whatever
    orientation raises — gather turns that into an attention entry."""
    ref = run_ref(root, run_dir)
    kind, _, slug = ref.partition(":")
    if not slug:  # the product run: ref is bare "product"
        kind, slug = "product", root.resolve().name
    ladder = [{"stage": stage, "state": state}
              for stage, state in stage_states(run_dir)]
    current = next((row["stage"] for row in ladder
                    if row["state"] == "current"), None)
    progress = None
    if current == "implement":
        done, total = checkbox_progress(breakdown_path(run_dir))
        progress = {"done": done, "total": total}
    return {"ref": ref, "kind": kind, "slug": slug,
            "dir": str(run_dir.relative_to(root)),
            "ladder": ladder, "progress": progress}


def gather(root, clock=None):
    """(model, problems). The one repo-level problem — no docs/ tree —
    yields (None, [it]); everything narrower stays inside the model, so
    an empty board or a broken run renders honestly instead of aborting
    (PRD-0004)."""
    clock = clock or (lambda: datetime.now().astimezone())
    root = Path(root)
    if not (root / "docs").is_dir():
        return None, [f"board: {root} has no docs/ tree"]
    runs, attention = [], []
    for run_dir in run_dirs(root):
        try:
            if not any((run_dir / artifact).is_file()
                       for artifact in _ARTIFACTS):
                continue
            if (run_dir / "retro.md").is_file():
                continue
            entry = _run_entry(root, run_dir)
            if all(row["state"] == "done" for row in entry["ladder"]):
                continue  # complete without retro.md: not active
            runs.append(entry)
        except Exception as err:  # noqa: BLE001 — per-run honesty:
            # a run this tool cannot orient is reported with its
            # reason, never guessed onto a stage and never fatal.
            attention.append({"dir": str(run_dir.relative_to(root)),
                              "reason": _reason(err)})
    runs.sort(key=lambda entry: (-_position(entry["ladder"]),
                                 entry["slug"]))
    model = {"generated": clock().isoformat(timespec="seconds"),
             "repo": root.resolve().name,
             "runs": runs, "attention": attention}
    return model, []


def main(argv):
    """`python3 board.py [root]` — root defaults to the working
    directory, the way the skill invokes it from a target repo."""
    root = argv[0] if argv else "."
    model, problems = gather(root)
    if problems:
        return cli.report("board", problems)
    print(json.dumps(model, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
