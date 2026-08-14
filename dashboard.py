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
import cost_ledger
from gate_digest import GATES, label_events, mirror_map, waiting_since
from knowledge_plane import (CLOSES_TOKEN, breakdown_files, row_done,
                             row_size, row_title, row_tracker_issue,
                             row_work_order, run_dirs)
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


def _listing(slug, run, problems):
    """The one windowed issue listing (--state all) both dispatch-plane
    sections read — the queues filter it to open issues, the drift
    check compares row checkboxes against its states. None on a failed
    or unparseable list; the sections stay empty and render on."""
    try:
        listing, suffix = gh_json(
            ["issue", "list", "-R", slug, "--state", "all", "--json",
             "number,title,state,labels,url", "--limit",
             str(LIST_WINDOW)],
            run, expect=list)
    except CLI_FAILURES as err:
        problems.append(f"dashboard: gh issue list failed:"
                        f" {run_detail(err)}")
        return None
    if suffix:
        problems.append(f"dashboard: gh issue list {suffix}")
        return None
    window = full_window(listing, LIST_WINDOW)
    if window:
        problems.append(f"dashboard: gh issue list {window}")
    return listing


def _queues(slug, listing, mirror, run, now, problems):
    """The open mirrored issues waiting at each human gate, in gate
    then issue order, aged from the current stay's labeled event when
    the timeline yields one."""
    entries = []
    for gate, queue_label, _, _ in GATES:
        for issue in sorted(listing, key=lambda e: e.get("number") or 0):
            number = issue.get("number")
            if number not in mirror or \
                    (issue.get("state") or "").upper() != "OPEN" or \
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


def _drift(root, states):
    """Cross-plane disagreement (ADR-0032: the row, never the issue, is
    authoritative — so the mirror must follow it): a row unchecked while
    its mirror is closed (the class issue #123 exposed), or checked
    while its mirror is still open. `states` maps issue number to its
    listed state; a mirror outside the listing says nothing — only
    definite disagreement is a finding."""
    findings = []
    for _, lines in breakdown_files(root):
        for line in lines:
            number = row_tracker_issue(line)
            state = states.get(number)
            if state is None:
                continue
            wo = row_work_order(line)
            if row_done(line) and state == "OPEN":
                findings.append(f"drift: {wo} row is checked but its"
                                f" mirror #{number} is still open")
            elif not row_done(line) and state == "CLOSED":
                findings.append(f"drift: {wo} row is unchecked but its"
                                f" mirror #{number} is closed")
    return findings


def _pr_by_issue(slug, run, problems):
    """{issue number: PR entry} from one windowed pr list — the PR that
    names the issue in its body's closing clause (the validator's
    CLOSES_TOKEN grammar: how a merged PR names the one work order it
    implements). A merged PR outranks an open one outranks a
    closed-unmerged one; within a rank the newest wins. None on a
    failed list — the table renders on without PR joins."""
    try:
        listing, suffix = gh_json(
            ["pr", "list", "-R", slug, "--state", "all", "--json",
             "number,state,body,url", "--limit", str(LIST_WINDOW)],
            run, expect=list)
    except CLI_FAILURES as err:
        problems.append(f"dashboard: gh pr list failed:"
                        f" {run_detail(err)}")
        return None
    if suffix:
        problems.append(f"dashboard: gh pr list {suffix}")
        return None
    window = full_window(listing, LIST_WINDOW)
    if window:
        problems.append(f"dashboard: gh pr list {window}")
    rank = {"MERGED": 2, "OPEN": 1, "CLOSED": 0}
    best = {}
    for entry in listing:
        number = entry.get("number")
        if not isinstance(number, int):
            continue
        key = (rank.get((entry.get("state") or "").upper(), 0), number)
        for issue in CLOSES_TOKEN.findall(entry.get("body") or ""):
            held = best.get(int(issue))
            if held is None or key > held[0]:
                best[int(issue)] = (key, entry)
    return {issue: entry for issue, (_, entry) in best.items()}


def _spend(root, problems):
    """{WO token: recorded ledger spend}. A work order with no rows has
    no spend (None downstream), never $0 — an absent ledger is silent
    (no runs yet, cost_ledger.read's own convention), and a malformed
    line arrives as read()'s ledger:-prefixed problem, never a silently
    smaller sum."""
    entries, ledger_problems = cost_ledger.read(root)
    problems.extend(ledger_problems)
    spend = {}
    for entry in entries:
        spend[entry["wo"]] = spend.get(entry["wo"], 0.0) + entry["cost"]
    return spend


def _output(root, by_number, prs, spend):
    """The factory-output table: one lifecycle entry per mirrored
    breakdown row, in breakdown order. state is the mirror's wo:* label
    (ADR-0032: the dispatch plane owns lifecycle; the row is the drift
    cross-check, never a second source), pr/url prefer the closing PR
    over the issue, spend is the ledger's recorded total for the work
    order."""
    entries = []
    for _, lines in breakdown_files(root):
        for line in lines:
            number = row_tracker_issue(line)
            wo = row_work_order(line)
            if number is None or wo is None:
                continue
            issue = by_number.get(number, {})
            lifecycle = next((name[len("wo:"):]
                              for name in label_names(issue)
                              if name.startswith("wo:")), None)
            pr = (prs or {}).get(number)
            entries.append({
                "wo": wo,
                "title": row_title(line),
                "size": row_size(line),
                "state": lifecycle,
                "pr": pr.get("number") if pr else None,
                "url": (pr.get("url") if pr else None)
                       or issue.get("url") or "",
                "spend": spend.get(wo),
            })
    return entries


def gather(repo_path, run=gh_runner, git=git_runner, clock=None):
    """One repo path -> the per-repo state dict (WO-0019 skeleton;
    WO-0020 adds the gate queues, WO-0021 the drift findings, WO-0022
    the factory-output join). Active runs per the protocol: at least
    one artifact and not complete. Every failure is a problem string in
    the dict — fail loud, render on. A repo with no mirrored rows is a
    plain pipeline repo: no git or gh call is made at all."""
    clock = clock or (lambda: datetime.now(timezone.utc))
    root = Path(repo_path)
    # resolve() for the name only: `gather .` must not report name ""
    # (path stays as given — it is the caller's vocabulary).
    state = {"repo": {"path": str(root), "name": root.resolve().name,
                      "remote": None},
             "runs": [], "queues": [], "output": [], "drift": [],
             "problems": []}
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
            listing = _listing(slug, run, state["problems"])
            if listing is not None:
                by_number = {entry["number"]: entry for entry in listing
                             if isinstance(entry.get("number"), int)}
                state["queues"] = _queues(slug, listing, mirror, run,
                                          clock(), state["problems"])
                state["drift"] = _drift(root, {
                    number: (entry.get("state") or "").upper()
                    for number, entry in by_number.items()})
                state["output"] = _output(
                    root, by_number,
                    _pr_by_issue(slug, run, state["problems"]),
                    _spend(root, state["problems"]))
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
