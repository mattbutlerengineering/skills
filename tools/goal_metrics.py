#!/usr/bin/env python3
"""goal_metrics: ADR-0135's four goal metrics over merged pull requests.

    python3 tools/goal_metrics.py [--days N] [--owner LOGIN]
                                  [--append docs/factory/goal-metrics.jsonl]

Prints one JSON row, then the `goal: N problem(s)` summary; --append also
adds the row to the JSON-lines ledger. Nothing is written when a gh read
fails or comes back truncated, so a ledger row is always a whole window.

- product PR: a merged PR touching a shipped path (SHIPPED_PREFIXES,
  SHIPPED_FILES); every other merged PR is overhead.
- overhead_ratio: overhead PRs / all PRs merged in the window.
- lead_time_hours_median: per product PR merged in the window, merge time
  minus the earlier of its creation and its earliest closing issue's.
- unattended_share: product PRs merged in the window with no Owner
  commit, review or comment before the merge. Agent commits carry no
  GitHub login, so a commit bearing the Owner's login is a real touch.
- escape_rate: product PRs merged in the window and at least HINDSIGHT
  days ago that a later merged PR names within HINDSIGHT days — a revert
  mentioning #N, or a `Fixes-PR: #N` line — or, when that fix names no
  PR at all, a `fix` PR touching one of the same shipped files.
"""
import argparse
import json
import re
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cli import CLI_FAILURES, detail, gh_read, gh_runner, report

LABEL = "goal"
WINDOW = 1000
HINDSIGHT = 14
SHIPPED_PREFIXES = ("skills/", ".claude-plugin/", "factory/templates/")
SHIPPED_FILES = ("docs/pipeline-protocol.md",)
# No `commits`: gh nests commit authors under each page of 100 PRs, past
# GraphQL's 500,000-node ceiling, so commit logins are a REST read per
# product PR (read_commits) instead.
PR_FIELDS = ("number,title,body,createdAt,mergedAt,files,"
             "closingIssuesReferences,reviews,comments")
COMMIT_READERS = 8
FIXES_PR = re.compile(r"^Fixes-PR:\s*#(\d+)", re.MULTILINE)
FIX_TITLE = re.compile(r"^fix(\([^)]*\))?!?:")


def is_shipped(path):
    return path.startswith(SHIPPED_PREFIXES) or path in SHIPPED_FILES


def parse_time(stamp):
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def shipped_files(record):
    return {f["path"] for f in record.get("files") or []
            if is_shipped(f["path"])}


def lead_hours(record, issue_created):
    starts = [parse_time(record["createdAt"])]
    starts += [parse_time(issue_created[ref["number"]])
               for ref in record.get("closingIssuesReferences") or []
               if ref["number"] in issue_created]
    return (parse_time(record["mergedAt"]) - min(starts)).total_seconds() / 3600


def touched_by(record, owner):
    merged = parse_time(record["mergedAt"])
    if any(author.get("login") == owner
           for commit in record.get("commits") or []
           for author in commit.get("authors") or []):
        return True
    events = [(r.get("author") or {}, r.get("submittedAt"))
              for r in record.get("reviews") or []]
    events += [(c.get("author") or {}, c.get("createdAt"))
               for c in record.get("comments") or []]
    return any(author.get("login") == owner and stamp
               and parse_time(stamp) < merged for author, stamp in events)


def names(fix, number):
    """Whether merged PR `fix` names PR `number` as the one it repairs."""
    text = f"{fix.get('title') or ''}\n{fix.get('body') or ''}"
    if fix["title"].startswith("Revert") and f"#{number}" in text:
        return True
    return str(number) in FIXES_PR.findall(fix.get("body") or "")


def escaped(record, later):
    merged = parse_time(record["mergedAt"])
    deadline = merged + timedelta(days=HINDSIGHT)
    files = shipped_files(record)
    for fix in later:
        moment = parse_time(fix["mergedAt"])
        if not merged < moment <= deadline:
            continue
        if names(fix, record["number"]):
            return True
        if (FIX_TITLE.match(fix["title"])
                and not FIXES_PR.search(fix.get("body") or "")
                and files & shipped_files(fix)):
            return True
    return False


def share(part, whole):
    return None if not whole else round(len(part) / len(whole), 4)


def compute(prs, issue_created, owner, now, days):
    """The metrics row for the `days` window ending at `now`. `prs` are
    merged PR records (gh pr list --json PR_FIELDS), which may reach back
    before the window; `issue_created` maps issue number to createdAt."""
    start = now - timedelta(days=days)
    in_window = [p for p in prs if parse_time(p["mergedAt"]) >= start]
    product = [p for p in in_window if shipped_files(p)]
    judged = [p for p in product if parse_time(p["mergedAt"])
              <= now - timedelta(days=HINDSIGHT)]
    escapes = sorted(p["number"] for p in judged if escaped(p, prs))
    leads = [lead_hours(p, issue_created) for p in product]
    unattended = [p for p in product if not touched_by(p, owner)]
    return {
        "date": now.strftime("%Y-%m-%d"),
        "window_days": days,
        "owner": owner,
        "merged_prs": len(in_window),
        "product_prs": len(product),
        "overhead_ratio": share([p for p in in_window
                                 if not shipped_files(p)], in_window),
        "lead_time_hours_median": (round(statistics.median(leads), 1)
                                   if leads else None),
        "unattended_share": share(unattended, product),
        "escape_rate": share(escapes, judged),
        "escaped": escapes,
    }


def read_owner(run):
    read = gh_read(["repo", "view", "--json", "owner"], "gh repo view",
                   LABEL, run=run, expect=dict)
    if read.value is None:
        return None, read.problems
    return read.value["owner"]["login"], []


def read_commits(run, number):
    """(commits, problems) for PR `number`, shaped as gh pr list's
    `commits` so compute() reads either; agent commits answer ""."""
    try:
        out = run(["api", f"repos/{{owner}}/{{repo}}/pulls/{number}/commits",
                   "--paginate", "--jq", '.[].author.login // ""'])
    except CLI_FAILURES as err:
        return None, [f"{LABEL}: gh api commits for #{number} failed:"
                      f" {detail(err)}"]
    return [{"authors": [{"login": login}]}
            for login in out.split("\n")], []


def with_commits(run, prs, start):
    """`prs` with each in-window product PR's commits filled in."""
    wanted = [p for p in prs
              if parse_time(p["mergedAt"]) >= start and shipped_files(p)]
    with ThreadPoolExecutor(COMMIT_READERS) as pool:
        reads = list(pool.map(lambda p: read_commits(run, p["number"]),
                              wanted))
    problems = [problem for _, found in reads for problem in found]
    commits = {p["number"]: found for p, (found, _) in zip(wanted, reads)}
    return [{**p, "commits": commits.get(p["number"], [])} for p in prs], \
        problems


def read_window(run, since):
    prs = gh_read(["pr", "list", "--state", "merged", "--search",
                   f"merged:>={since}", "--json", PR_FIELDS],
                  "gh pr list", LABEL, run=run, window=WINDOW)
    issues = gh_read(["issue", "list", "--state", "all", "--search",
                      f"closed:>={since}", "--json", "number,createdAt"],
                     "gh issue list", LABEL, run=run, window=WINDOW)
    problems = prs.problems + issues.problems
    if problems:
        return None, None, problems
    created = {i["number"]: i["createdAt"] for i in issues.value}
    return prs.value, created, []


def main(argv=None, run=gh_runner, now=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=28)
    parser.add_argument("--owner")
    parser.add_argument("--append", type=Path)
    args = parser.parse_args(argv)
    now = now or datetime.now(timezone.utc)
    owner, problems = ((args.owner, []) if args.owner
                       else read_owner(run))
    if problems:
        return report(LABEL, problems)
    since = (now - timedelta(days=args.days + HINDSIGHT)).strftime("%Y-%m-%d")
    prs, created, problems = read_window(run, since)
    if not problems:
        prs, problems = with_commits(run, prs,
                                     now - timedelta(days=args.days))
    if problems:
        return report(LABEL, problems)
    row = json.dumps(compute(prs, created, owner, now, args.days),
                     sort_keys=True)
    print(row)
    if args.append:
        with args.append.open("a", encoding="utf-8") as ledger:
            ledger.write(row + "\n")
    return report(LABEL, [])


if __name__ == "__main__":
    sys.exit(main())
