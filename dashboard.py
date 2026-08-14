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
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from cli import CLI_FAILURES, full_window, gh_json, gh_runner, label_names
from cli import detail as run_detail
from cli import report, runner
from gate_digest import GATES, label_events, mirror_map, waiting_since
from knowledge_plane import run_dirs
from protocol import (MAINTENANCE_STAGE_ARTIFACTS, STAGE_ARTIFACTS,
                      next_stage)

CONFIG_PATH = Path.home() / ".process-dashboard.json"

git_runner = runner("git")

# The two shapes a github.com origin takes; group 1 is the owner/repo
# slug either way.
_REMOTE = re.compile(
    r"^(?:git@github\.com:|https://github\.com/)([^/]+/[^/]+?)(?:\.git)?$")

# gh truncates a windowed listing silently (the gate_digest rule); the
# window is declared once beside the --limit that carries it.
LIST_WINDOW = 1000

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


def remote_slug(repo_path, git=git_runner):
    """(owner/repo slug, problems) from the checkout's origin — how the
    dispatch-plane reads scope their gh calls and how the page builds
    links. A repo without a readable github.com origin yields (None,
    [the one problem]); callers skip the dispatch plane and render on."""
    try:
        url = git(["-C", str(repo_path), "config", "--get",
                   "remote.origin.url"]).stdout.strip()
    except CLI_FAILURES:
        return None, [f"dashboard: {repo_path} has no readable"
                      " remote.origin.url"]
    match = _REMOTE.match(url)
    if not match:
        return None, [f"dashboard: {repo_path} remote {url} is not"
                      " a github.com remote"]
    return match.group(1), []


def _age_seconds(since, now):
    """Whole seconds from a GitHub timestamp to now. The Z-suffix
    replace is gate_digest's documented compat quirk (fromisoformat
    accepts Z only from 3.11)."""
    then = datetime.fromisoformat(since.replace("Z", "+00:00"))
    return int((now - then).total_seconds())


def _timeline(slug, number, run, problems):
    """One issue's label events, [] on a failed or unparseable fetch —
    the item still lists, just without an age (the gate_digest rule:
    a failed fetch is a problem, never a lost queue item)."""
    path = f"repos/{slug}/issues/{number}/timeline"
    try:
        pages, suffix = gh_json(["api", path, "--paginate", "--slurp"],
                                run, expect=list)
    except CLI_FAILURES as err:
        problems.append(f"dashboard: gh api timeline for #{number}"
                        f" failed: {run_detail(err)}")
        return []
    if suffix:
        problems.append(f"dashboard: gh api timeline for #{number}"
                        f" {suffix}")
        return []
    return label_events([event for page in pages for event in page])


def _queues(slug, mirror, run, now, problems):
    """The open mirrored issues waiting at each human gate, in gate
    then issue order, aged from the current stay's labeled event when
    the timeline yields one."""
    listing, suffix = None, None
    try:
        listing, suffix = gh_json(
            ["issue", "list", "-R", slug, "--state", "open", "--json",
             "number,title,labels,url", "--limit", str(LIST_WINDOW)],
            run, expect=list)
    except CLI_FAILURES as err:
        problems.append(f"dashboard: gh issue list failed:"
                        f" {run_detail(err)}")
        return []
    if suffix:
        problems.append(f"dashboard: gh issue list {suffix}")
        return []
    window = full_window(listing, LIST_WINDOW)
    if window:
        problems.append(f"dashboard: gh issue list {window}")
    entries = []
    for gate, queue_label, _, _ in GATES:
        for issue in sorted(listing, key=lambda e: e.get("number") or 0):
            number = issue.get("number")
            if number not in mirror or \
                    queue_label not in label_names(issue):
                continue
            events = _timeline(slug, number, run, problems)
            since = waiting_since(events, queue_label)
            entries.append({
                "gate": gate,
                "issue": number,
                "title": issue.get("title") or "",
                "waited_s": _age_seconds(since, now) if since else None,
                "url": issue.get("url") or "",
            })
    return entries


def gather(repo_path, run=gh_runner, git=git_runner, clock=None):
    """One repo path -> the per-repo state dict (WO-0019 skeleton;
    WO-0020 adds the gate queues). Active runs per the protocol: at
    least one artifact and not complete. Every failure is a problem
    string in the dict — fail loud, render on. A repo with no mirrored
    rows is a plain pipeline repo: no git or gh call is made at all."""
    clock = clock or (lambda: datetime.now(timezone.utc))
    root = Path(repo_path)
    # resolve() for the name only: `gather .` must not report name ""
    # (path stays as given — it is the caller's vocabulary).
    state = {"repo": {"path": str(root), "name": root.resolve().name,
                      "remote": None},
             "runs": [], "queues": [], "problems": []}
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
    mirror = mirror_map(root)
    if mirror:
        slug, remote_problems = remote_slug(root, git)
        state["repo"]["remote"] = slug
        state["problems"].extend(remote_problems)
        if slug:
            state["queues"] = _queues(slug, mirror, run, clock(),
                                      state["problems"])
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
