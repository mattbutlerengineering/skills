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
  python3 dashboard.py serve [--port N] [--config PATH]
                                            the localhost console:
                                            binds 127.0.0.1 only,
                                            GET / serves the page,
                                            GET /api/repos lists the
                                            configured set, GET
                                            /api/repo?i=N gathers one
                                            repo fresh per request,
                                            POST /api/backlog-order
                                            saves a backlog order

The repo set (which checkouts the console observes) is operator state,
not repo state: argv paths win, else ~/.process-dashboard.json
({"repos": [...]}) — deliberately not factory.json, which is per-repo.
Conventions match the sibling tools: functions return
dashboard:-prefixed problem strings; the CLI prints them and exits
nonzero via cli.report.
"""
import hashlib
import json
import re
import statistics
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from cli import CLI_FAILURES, gh_read, gh_runner, label_names
from cli import read_file, report, runner
import cost_ledger
import cost_report
import factory_config
from human_gates import (GATES, label_events, refused_timestamps,
                         waiting_since)
from knowledge_plane import (CLOSES_TOKEN, WO_TOKEN, breakdown_files,
                             mirror_map, row_size, row_title,
                             row_tracker_issue, row_work_order, run_dirs)
import plane_drift
from protocol import (RUN_ARTIFACTS, next_stage, parse_backlog, run_ref)

CONFIG_PATH = Path.home() / ".process-dashboard.json"

# ADR-0037 has callers alias the seam to their own names "so their
# problem strings read unchanged" — recorded deliberate, not folded:
# one-owner: one_owner.git_runner (ADR-0061) — ADR-0037 sanctions the alias
git_runner = runner("git")

# The two shapes a github.com origin takes; group 1 is the owner/repo
# slug either way.
_REMOTE = re.compile(
    r"^(?:git@github\.com:|https://github\.com/)([^/]+/[^/]+?)(?:\.git)?$")

# How far back the dispatch-plane listings can see. cli.gh_read owns
# the window — the limit it sends gh and the truncation it reports are
# the same number, so the two can no longer drift apart.
LIST_WINDOW = 1000


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
    except (OSError, UnicodeDecodeError) as err:
        return [], [f"dashboard: cannot read {path}: {err}"]
    except json.JSONDecodeError as err:
        return [], [f"dashboard: {path} is not valid JSON: {err}"]
    repos = config.get("repos") if isinstance(config, dict) else None
    if not isinstance(repos, list) or \
            not all(isinstance(entry, str) for entry in repos):
        return [], [f"dashboard: {path} must be a JSON object with a"
                    " \"repos\" list of paths"]
    return repos, []


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
    """Whole seconds from a GitHub timestamp to now. Not
    human_gates.waited_seconds: that one takes two GitHub timestamps,
    this takes a live datetime for `now`, and the rendering is the
    dashboard's. The Z-suffix replace is the same documented compat
    quirk (fromisoformat accepts Z only from 3.11)."""
    then = datetime.fromisoformat(since.replace("Z", "+00:00"))
    return int((now - then).total_seconds())


def _timeline(slug, number, run, problems):
    """One issue's label events, None on a failed or unparseable fetch —
    the item still lists, just without an age (the gate_digest rule:
    a failed fetch is a problem, never a lost queue item). None, not
    []: [] is a timeline that was read and holds nothing, and _queues
    must tell an unreadable age from an unknown one (#665).

    A fetch that succeeds can still carry an event label_events refuses
    for a malformed timestamp — reported here, since a successful read
    leaves read.problems silent about it (#491)."""
    path = f"repos/{slug}/issues/{number}/timeline"
    read = gh_read(["api", path, "--paginate", "--slurp"],
                   f"gh api timeline for #{number}", label="dashboard",
                   run=run)
    problems.extend(read.problems)
    if read.value is None:
        return None
    raw = [event for page in read.value for event in page]
    refused = refused_timestamps(raw)
    if refused:
        problems.append(f"dashboard: timeline for #{number} refused"
                        f" {refused} malformed timestamp(s)")
    return label_events(raw)


def _listing(slug, run, problems):
    """The one windowed issue listing (--state all) both dispatch-plane
    sections read — the queues filter it to open issues, the drift
    check compares row checkboxes against its states. None on a failed
    or unparseable list; the sections stay empty and render on."""
    read = gh_read(
        ["issue", "list", "-R", slug, "--state", "all", "--json",
         "number,title,state,labels,url"],
        "gh issue list", label="dashboard", run=run, window=LIST_WINDOW)
    problems.extend(read.problems)
    return read.value


def _queues(slug, listing, mirror, run, now, problems):
    """The open mirrored issues waiting at each human gate, in gate
    then issue order, aged from the current stay's labeled event when
    the timeline yields one. `aged` says whether the timeline could be
    read at all — the difference between an unknown age (read, no
    arrival) and an unreadable one (fetch failed), the same fact
    gate_digest's Item carries under the same name."""
    entries = []
    for gate, queue_label, _, _ in GATES:
        for issue in sorted(listing, key=lambda e: e.get("number") or 0):
            number = issue.get("number")
            if number not in mirror or \
                    (issue.get("state") or "").upper() != "OPEN" or \
                    queue_label not in label_names(issue):
                continue
            events = _timeline(slug, number, run, problems)
            since = waiting_since(events or [], queue_label)
            entries.append({
                "gate": gate,
                "issue": number,
                "title": issue.get("title") or "",
                "waited_s": _age_seconds(since, now) if since else None,
                "aged": events is not None,
                "url": issue.get("url") or "",
            })
    return entries


def _pr_by_issue(slug, run, problems):
    """{issue number: PR entry} from one windowed pr list — the PR that
    names the issue in its body's closing clause (the validator's
    CLOSES_TOKEN grammar: how a merged PR names the one work order it
    implements). A merged PR outranks an open one outranks a
    closed-unmerged one; within a rank the newest wins. None on a
    failed list — the table renders on without PR joins."""
    read = gh_read(
        ["pr", "list", "-R", slug, "--state", "all", "--json",
         "number,state,body,url,reviews"],
        "gh pr list", label="dashboard", run=run, window=LIST_WINDOW)
    problems.extend(read.problems)
    if read.value is None:
        return None
    rank = {"MERGED": 2, "OPEN": 1, "CLOSED": 0}
    best = {}
    for entry in read.value:
        number = entry.get("number")
        if not isinstance(number, int):
            continue
        key = (rank.get((entry.get("state") or "").upper(), 0), number)
        for issue in CLOSES_TOKEN.findall(entry.get("body") or ""):
            held = best.get(int(issue))
            if held is None or key > held[0]:
                best[int(issue)] = (key, entry)
    return {issue: entry for issue, (_, entry) in best.items()}


def _spend(entries):
    """{WO token: recorded ledger spend} over already-read entries. A
    work order with no rows has no spend (None downstream), never $0 —
    an absent ledger reads as no entries, and a malformed line already
    arrived as read()'s ledger:-prefixed problem, never a silently
    smaller sum.

    Which rows count is cost_ledger.dispatched's rule, not a second copy
    of it: a gate-latency observation (ADR-0041) is a $0 wait record
    rather than a run, so a work order with only gate rows would
    otherwise land here with a key worth 0.0 — the measured $0.00 the
    page renders instead of the em dash it keeps for an unmeasured one,
    and the by_wo padding cost_report.aggregate names as the reason the
    rule exists. _metrics reads the same list from the same
    cost_ledger.read call and keeps that rule through aggregate; this is
    the console's other reader of it."""
    spend = {}
    for entry in cost_ledger.dispatched(entries):
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
    # ADR-0084: a run with no work order is keyed by its issue. Its spend
    # follows the work orders, labelled as an issue, never as an order.
    for key in sorted(key for key in spend
                      if cost_ledger.ISSUE_KEY.fullmatch(key)):
        entries.append({"wo": key, "title": f"issue {key} (no work order)",
                        "size": None, "state": None, "pr": None, "url": "",
                        "spend": spend[key]})
    return entries


def _metrics(root, entries, month, problems):
    """The ledger metrics over already-read entries — the report
    month's spend against factory.json's cap, mean cost per work order
    (lifetime), median gate wait — or None when nothing is recorded
    yet: an absent or empty ledger is "no runs recorded yet", never a
    $0.00 that reads as measured-and-free. cost_report.aggregate owns
    the rollup math (gate rows out of every spend figure),
    cost_ledger.gate_wait the gate rows, factory_config the cap. The
    cap resolves only once entries exist, so a plain pipeline repo
    never reports a missing factory.json."""
    if not entries:
        return None
    lifetime = cost_report.aggregate(entries)
    config, config_problems = factory_config.load(root)
    cap = None
    if not config_problems:
        cap, config_problems = factory_config.resolve_cap(config)
    problems.extend(config_problems)
    waits = [wait[1] for wait in map(cost_ledger.gate_wait, entries)
             if wait is not None]
    return {
        "month_spend": cost_report.aggregate(entries,
                                             month)["total_cost"],
        "cap": cap,
        "cost_per_wo": (round(lifetime["total_cost"]
                              / len(lifetime["by_wo"]), 2)
                        if lifetime["by_wo"] else None),
        "gate_wait_median": (round(statistics.median(waits))
                             if waits else None),
        "acceptance": None,
        "rework": None,
    }


# WO-0018's correction stream: one JSON object per line naming the
# corrected work order. The miner ships later; this reader depends on
# nothing more than the wo field, so the stream can grow without
# breaking the join.
CORRECTIONS = "docs/factory/corrections.jsonl"


def _corrections(root, problems):
    """{WO token: correction count} from the corrections stream. An
    absent file is silent — the stream starts when the miner ships,
    absence is normal, not an error — but a present line that cannot be
    accounted to a work order is a problem, never a silently smaller
    rework rate."""
    text, problem = read_file(root / CORRECTIONS, CORRECTIONS, str)
    if problem:
        problems.append(f"dashboard: {problem}")
    if text is None:
        return {}
    counts = {}
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as err:
            problems.append(f"dashboard: {CORRECTIONS}:{lineno} is not"
                            f" valid JSON: {err}")
            continue
        wo = record.get("wo") if isinstance(record, dict) else None
        if not isinstance(wo, str) or not WO_TOKEN.fullmatch(wo):
            problems.append(f"dashboard: {CORRECTIONS}:{lineno} names"
                            " no wo")
            continue
        counts[wo] = counts.get(wo, 0) + 1
    return counts


def _rates(prs, mirror, corrections):
    """(acceptance, rework) over the mirrored work orders' landed PRs,
    or None when none have merged — nothing to rate is None, never a
    0.0 that reads as measured. acceptance: the share merged with no
    changes-requested review (first-pass at the merge gate). rework:
    the share with a changes-requested review or a recorded correction
    — review data alone makes the two complements; the corrections
    stream (WO-0018) widens rework past what review saw."""
    merged = []
    for issue, entry in (prs or {}).items():
        wo = mirror.get(issue)
        if wo is None or (entry.get("state") or "").upper() != "MERGED":
            continue
        changes = any(
            (review.get("state") or "").upper() == "CHANGES_REQUESTED"
            for review in entry.get("reviews") or []
            if isinstance(review, dict))
        merged.append((wo, changes))
    if not merged:
        return None
    accepted = sum(1 for _, changes in merged if not changes)
    reworked = sum(1 for wo, changes in merged
                   if changes or corrections.get(wo))
    return (round(accepted / len(merged), 2),
            round(reworked / len(merged), 2))


def gather(repo_path, run=gh_runner, git=git_runner, clock=None):
    """One repo path -> the per-repo state dict (WO-0019 skeleton;
    WO-0020 adds the gate queues, WO-0021 the drift findings, WO-0022
    the factory-output join, WO-0023 the ledger metrics, WO-0029 the
    backlog section). Active runs
    per the protocol: at least one artifact and not complete. Every
    failure is a problem string in the dict — fail loud, render on. A
    repo with no mirrored rows is a plain pipeline repo: no git or gh
    call is made at all."""
    clock = clock or (lambda: datetime.now(timezone.utc))
    root = Path(repo_path)
    # resolve() for the name only: `gather .` must not report name ""
    # (path stays as given — it is the caller's vocabulary).
    state = {"repo": {"path": str(root), "name": root.resolve().name,
                      "remote": None},
             "runs": [], "queues": [], "backlog": None, "output": [],
             "drift": [], "metrics": None, "problems": []}
    if not root.is_dir():
        state["problems"].append(
            f"dashboard: {repo_path} is not a directory")
        return state
    state["backlog"] = _backlog(root, state["problems"])
    for run_dir in run_dirs(root):
        if not any((run_dir / artifact).is_file()
                   for artifact in RUN_ARTIFACTS):
            continue
        stage = next_stage(run_dir)
        if stage == "complete":
            continue
        state["runs"].append({
            "ref": run_ref(root, run_dir),
            "dir": str(run_dir.relative_to(root)),
            "stage": stage,
        })
    now = clock()
    ledger, ledger_problems = cost_ledger.read(root)
    state["problems"].extend(ledger_problems)
    state["metrics"] = _metrics(root, ledger,
                                now.date().isoformat()[:7],
                                state["problems"])
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
                                          now, state["problems"])
                rows = [(str(path.relative_to(root)), lines)
                        for path, lines in breakdown_files(root)]
                # absent_is_drift=False: this listing is windowed and
                # renders on when truncated, so a mirror it never saw
                # says nothing. sweeps aborts instead, and claims True.
                drift, drift_problems = plane_drift.reconcile_drift(
                    rows, listing, absent_is_drift=False)
                state["drift"] = drift
                state["problems"].extend(drift_problems)
                prs = _pr_by_issue(slug, run, state["problems"])
                state["output"] = _output(root, by_number, prs,
                                          _spend(ledger))
                rates = _rates(prs, mirror,
                               _corrections(root, state["problems"]))
                if rates is not None:
                    metrics = state["metrics"] or {
                        "month_spend": None, "cap": None,
                        "cost_per_wo": None, "gate_wait_median": None}
                    metrics["acceptance"], metrics["rework"] = rates
                    state["metrics"] = metrics
    return state


BACKLOG = "docs/backlog.md"
_STALE = "dashboard: backlog changed underneath; refresh"


def backlog_hash(text):
    """The optimistic-concurrency token: gather stamps it, the Save
    posts it back, and reorder refuses when the file moved on."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _backlog(root, problems):
    """The backlog section of the state dict: content hash plus the
    seeds the page lists, or None on a repo without one — the backlog
    is advisory and optional (ADR-0029), so absent is normal, never a
    problem."""
    text, problem = read_file(root / BACKLOG, BACKLOG, str)
    if problem:
        problems.append(f"dashboard: {problem}")
    if text is None:
        return None
    return {"hash": backlog_hash(text),
            "seeds": [{"line": entry["line"], "text": entry["text"],
                       "claimed": entry["claimed"]}
                      for entry in parse_backlog(text)]}


def reorder_backlog(text, posted_hash, order):
    """(new text, problems) — apply a posted seed order to backlog
    text. Permutation-only over the seed lines parse_backlog
    identifies (ADR-0029): order lists their 1-based line numbers in
    the desired sequence, each seed line moves wholesale (claim marker
    riding along), and every other line — header prose, blanks,
    malformed bullets — keeps its exact position. The console never
    adds, drops, or edits a seed; producers append (ADR-0029)."""
    if posted_hash != backlog_hash(text):
        return None, [_STALE]
    seed_lines = [entry["line"] for entry in parse_backlog(text)]
    if sorted(order) != seed_lines:
        return None, ["dashboard: order is not a permutation of the "
                      "current seed lines"]
    lines = text.splitlines()
    reordered = list(lines)
    for position, source in zip(seed_lines, order):
        reordered[position - 1] = lines[source - 1]
    tail = "\n" if text.endswith("\n") else ""
    return "\n".join(reordered) + tail, []


DEFAULT_PORT = 7700
PAGE = Path(__file__).with_name("dashboard.html")


def respond(target, repos_fn, gather_fn):
    """(status, payload) for one GET — the read endpoints' pure half,
    the seam every handler test pins (the HTTP class below is a thin
    shim and never opens in tests). / serves the console page as-is
    (a str payload — the shim's content-type cue), re-read per request
    so an edit shows on reload. /api/repos lists the configured set
    with indices so the page knows how many /api/repo calls to fire;
    /api/repo?i=N gathers one repo fresh; an unparseable or
    out-of-range index and any other path are 404. An unreadable
    config is the whole-page 500 — the one failure the page cannot
    render past."""
    url = urlsplit(target)
    if url.path == "/":
        # Hand-written rather than cli.read_file (ADR-0075): an absent
        # page is an OSError message here, where read_file gives
        # (None, None).
        try:
            return 200, PAGE.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as err:
            return 500, {"problems": [
                f"dashboard: cannot read dashboard.html: {err}"]}
    if url.path == "/api/repos":
        repos, problems = repos_fn()
        if problems:
            return 500, {"problems": problems}
        return 200, {"repos": [
            {"i": index, "path": path, "name": Path(path).name}
            for index, path in enumerate(repos)]}
    if url.path == "/api/repo":
        repos, problems = repos_fn()
        if problems:
            return 500, {"problems": problems}
        try:
            index = int(parse_qs(url.query).get("i", [""])[0])
        except ValueError:
            index = -1
        if not 0 <= index < len(repos):
            return 404, {"problems": ["dashboard: no such repo index"]}
        return 200, gather_fn(repos[index])
    return 404, {"problems": ["dashboard: no such path"]}


def respond_post(target, body, repos_fn):
    """(status, payload) for one POST — the write endpoint's pure
    half. /api/backlog-order applies a posted seed order to the
    indexed repo's backlog: 204 rewrites the file once; a stale hash
    is 409 and a non-permutation 400 (reorder_backlog's exact problem
    strings); an unreadable or unwritable file is 500 with the OS
    detail. Payload is None on 204 — the one bodyless response."""
    url = urlsplit(target)
    if url.path != "/api/backlog-order":
        return 404, {"problems": ["dashboard: no such path"]}
    repos, problems = repos_fn()
    if problems:
        return 500, {"problems": problems}
    try:
        posted = json.loads(body)
        index = posted["i"]
        posted_hash = posted["hash"]
        order = posted["order"]
    except (ValueError, KeyError, TypeError):
        posted_hash = order = index = None
    if not (isinstance(posted_hash, str) and isinstance(order, list)
            and all(isinstance(line, int) and not isinstance(line, bool)
                    for line in order)):
        return 400, {"problems": [
            "dashboard: body must be JSON with i, hash, and an order "
            "of line numbers"]}
    if not (isinstance(index, int) and not isinstance(index, bool)
            and 0 <= index < len(repos)):
        return 404, {"problems": ["dashboard: no such repo index"]}
    path = Path(repos[index]) / BACKLOG
    # Hand-written rather than cli.read_file (ADR-0075): an absent
    # backlog is an OSError message here, where read_file gives
    # (None, None).
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        return 500, {"problems": [
            f"dashboard: cannot read {BACKLOG}: {err}"]}
    new_text, reorder_problems = reorder_backlog(text, posted_hash,
                                                 order)
    if reorder_problems:
        status = 409 if reorder_problems == [_STALE] else 400
        return status, {"problems": reorder_problems}
    try:
        path.write_text(new_text, encoding="utf-8")
    except OSError as err:
        return 500, {"problems": [
            f"dashboard: cannot write {BACKLOG}: {err}"]}
    return 204, None


def content_length(declared):
    """(byte count, problems) for a Content-Length header value.

    RFC 9110 §8.6 makes it a non-negative integer, so anything else is a
    bad request, not a crash: `int()` on it raised straight out of
    do_POST and the client got no HTTP response at all — the connection
    just closed. Absent is 0; a bodyless POST is well formed.

    `isascii()` is not decoration. `str.isdigit()` is TRUE for '\u00b2',
    which `int()` refuses, and U+00B2 is latin-1 byte 0xB2 — precisely
    what http.client decodes a header into. isdigit() alone would leave
    the crash reachable through an ordinary request.

    A negative value never reaches the read for a second reason:
    `rfile.read(-1)` reads to EOF, which wedges the handler thread.
    """
    if declared is None:
        return 0, []
    if not (declared.isascii() and declared.isdigit()):
        return None, [f"dashboard: Content-Length {declared!r} is not a"
                      " non-negative integer"]
    return int(declared), []


class _Handler(BaseHTTPRequestHandler):
    """Thin shim over respond(): JSON in, JSON out, no logic. serve()
    subclasses it with the injected repos_fn/gather_fn; per-request
    logging is silenced — the CLI's stdout carries problem strings,
    not access logs."""

    repos_fn = None
    gather_fn = None

    def do_GET(self):
        status, payload = respond(self.path, type(self).repos_fn,
                                  type(self).gather_fn)
        html = isinstance(payload, str)
        body = (payload if html else json.dumps(payload)).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8"
                         if html else "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length, problems = content_length(
            self.headers.get("Content-Length"))
        if problems:
            status, payload = 400, {"problems": problems}
        else:
            body = self.rfile.read(length).decode("utf-8", "replace")
            status, payload = respond_post(self.path, body,
                                           type(self).repos_fn)
        body_bytes = (b"" if payload is None
                      else json.dumps(payload).encode("utf-8"))
        self.send_response(status)
        if payload is not None:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)

    def log_message(self, *_args):
        pass


def serve(port, config_path=None, server_cls=None):
    """Run the console server on 127.0.0.1 only — the write endpoint
    exists (WO-0029), so the console is never exposed off-box in v1 (no
    auth story by design). The repo set re-reads per request, so a
    config edit shows on the next page load. Returns the problem list
    for cli.report ([] on a clean Ctrl-C)."""
    handler = type("Handler", (_Handler,), {
        "repos_fn": staticmethod(lambda: repo_set([], config_path)),
        "gather_fn": staticmethod(gather)})
    try:
        httpd = (server_cls or ThreadingHTTPServer)(("127.0.0.1", port),
                                                    handler)
    except (OSError, OverflowError) as err:
        return [f"dashboard: cannot bind 127.0.0.1:{port}: {err}"]
    print(f"dashboard: http://127.0.0.1:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return []


def _serve_args(argv):
    """(port, config path, problems) for the serve leg: --port N and
    --config PATH, both optional, anything else a problem."""
    port, config, problems = DEFAULT_PORT, None, []
    index = 0
    while index < len(argv):
        flag = argv[index]
        if flag not in ("--port", "--config"):
            problems.append(
                f"dashboard: unrecognized serve argument {flag!r}")
            index += 1
            continue
        if index + 1 >= len(argv):
            problems.append(f"dashboard: {flag} needs a value")
            break
        value = argv[index + 1]
        if flag == "--config":
            config = value
        else:
            try:
                port = int(value)
            except ValueError:
                problems.append(
                    f"dashboard: --port {value!r} is not a number")
        index += 2
    return port, config, problems


def main(argv):
    if len(argv) == 2 and argv[0] == "gather":
        state = gather(argv[1])
        print(json.dumps(state, indent=2))
        return report("dashboard", state["problems"])
    if argv and argv[0] == "serve":
        port, config, problems = _serve_args(argv[1:])
        if problems:
            return report("dashboard", problems)
        return report("dashboard", serve(port, config))
    print(__doc__.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
