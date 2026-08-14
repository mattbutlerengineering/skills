#!/usr/bin/env python3
"""dashboard: the process console's gather half (PRD-0002, WO-0019).

The operator-level console over the state the process already writes —
run artifacts (knowledge plane), the tracker mirror (dispatch plane),
the cost ledger. This module is the compute side: one repo path in, one
state dict out, built on the seams that already answer every question —
knowledge_plane.run_dirs walks the candidate run directories and
protocol.next_stage orients each one — so the console renders state, it
never re-derives it. Operator-level, never stamped (the console
observes stamped repos from one seat; it is not in factory_init.MIRRORS
and no product repo runs it in CI).

  python3 dashboard.py gather <repo-path>   one repo's state dict as
                                            JSON on stdout — the
                                            testable seam and the
                                            scripting hook

The repo set (which checkouts the console observes) is operator state,
not repo state: argv paths win, else ~/.process-dashboard.json
({"repos": [...]}) — deliberately not factory.json, which is per-repo.
Conventions match the sibling tools: functions return
dashboard:-prefixed problem strings; the CLI prints them and exits
nonzero via cli.report.
"""
import json
import sys
from pathlib import Path

from cli import report
from knowledge_plane import run_dirs
from protocol import (MAINTENANCE_STAGE_ARTIFACTS, STAGE_ARTIFACTS,
                      next_stage)

CONFIG_PATH = Path.home() / ".process-dashboard.json"

# Every artifact filename that marks a run dir as *a run at all* — the
# protocol's active-run rule ("at least one artifact") over both
# orientation tables. "code" never appears: implement's artifact is the
# breakdown's checkboxes, already covered by decompose's row.
_ARTIFACTS = sorted({artifact for _, artifact in
                     STAGE_ARTIFACTS + MAINTENANCE_STAGE_ARTIFACTS})


def repo_set(argv_paths, config_path=None):
    """(repo paths, problems): the checkouts the console observes. Argv
    wins; an absent config with no argv is the "no repos configured"
    empty state, not a problem — the page points at the config; only an
    unreadable or misshapen config is a problem."""
    if argv_paths:
        return list(argv_paths), []
    path = Path(config_path) if config_path else CONFIG_PATH
    if not path.is_file():
        return [], []
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except OSError as err:
        return [], [f"dashboard: cannot read {path}: {err}"]
    except json.JSONDecodeError as err:
        return [], [f"dashboard: {path} is not valid JSON: {err}"]
    repos = config.get("repos") if isinstance(config, dict) else None
    if not isinstance(repos, list) or \
            not all(isinstance(entry, str) for entry in repos):
        return [], [f"dashboard: {path} must be a JSON object with a"
                    " \"repos\" list of paths"]
    return repos, []


def _run_ref(root, run_dir):
    """The protocol run-ref for a candidate directory: docs/ is the
    product run; docs/features/<slug> and docs/fixes/<slug> carry their
    scale in the parent name."""
    rel = run_dir.relative_to(root)
    if rel == Path("docs"):
        return "product"
    scale = "feature" if rel.parent.name == "features" else "maintenance"
    return f"{scale}:{rel.name}"


def gather(repo_path):
    """One repo path -> the per-repo state dict (WO-0019: repo, active
    runs with orientation stage, problems; later orders grow the dict).
    Active per the protocol: at least one artifact and not complete.
    Every failure is a problem string in the dict — fail loud, render
    on."""
    root = Path(repo_path)
    # resolve() for the name only: `gather .` must not report name ""
    # (path stays as given — it is the caller's vocabulary).
    state = {"repo": {"path": str(root), "name": root.resolve().name},
             "runs": [], "problems": []}
    if not root.is_dir():
        state["problems"].append(
            f"dashboard: {repo_path} is not a directory")
        return state
    for run_dir in run_dirs(root):
        if not any((run_dir / artifact).is_file()
                   for artifact in _ARTIFACTS):
            continue
        stage = next_stage(run_dir)
        if stage == "complete":
            continue
        state["runs"].append({
            "ref": _run_ref(root, run_dir),
            "dir": str(run_dir.relative_to(root)),
            "stage": stage,
        })
    return state


def main(argv):
    if len(argv) == 2 and argv[0] == "gather":
        state = gather(argv[1])
        print(json.dumps(state, indent=2))
        return report("dashboard", state["problems"])
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
