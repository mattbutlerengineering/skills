#!/usr/bin/env python3
"""validator: the brain behind .github/workflows/validator.yml (PRD-0001;
ADR-0032 lifecycle labels, ADR-0033 gate 3).

The workflow names no commands of its own — it runs `make` targets, and the
two that need judgment land here. Both read the pull_request event payload
(GITHUB_EVENT_PATH) and mutate GitHub through the gh CLI, which is injected
so tests never touch the network (same shape as label_sync.py).
Conventions match gates.py/label_sync.py: functions return V:-prefixed
problem strings; the CLI prints them and exits nonzero.

  python3 validator.py review --findings <file> [--status <rc>]
        Post the check run's output on the PR as review findings, from an
        actor that is not the PR's author — PRD-0001: no work is verified by
        the agent that produced it. Refuses to post (nonzero, nothing said)
        when the posting identity is the author. Red findings are posted and
        do NOT fail the review job: failing the build is the check job's
        work, and a reviewer that goes silent on red is useless.

  python3 validator.py lifecycle --label wo:merged
        Make <label> the only wo: lifecycle label on the work order's
        mirrored issue (ADR-0032: exactly one at a time). The issue number
        comes from the breakdown row, never from the issue itself — the
        knowledge plane is authoritative and the mirror is one-way.
"""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import gates
import label_sync

LIFECYCLE_PREFIX = "wo:"
# A breakdown row is a checkbox line; its work order is its FIRST WO token
# (later ones are blocking edges). Notes are prose, never rows.
ROW = re.compile(r"^\s*[-*]\s*\[[ xX]\]\s")
TRACKER = re.compile(r"\(tracker:\s*#(\d+)\)")
REVIEW_MARKER = "<!-- factory-review -->"
MAX_FINDINGS_CHARS = 12000


def lifecycle_labels(root):
    """(the wo: state machine's labels in taxonomy order, problems)."""
    labels, problems = label_sync.load_labels(root)
    names = [label["name"] for label in labels
             if label["name"].startswith(LIFECYCLE_PREFIX)]
    return names, problems


def tracker_issue(root, wo):
    """(the work order's mirrored issue number, problems), read from its
    breakdown row — ADR-0032: the dispatch mirror is one-way, so the
    knowledge plane, not the issue, says which issue a work order owns."""
    for run in gates.run_dirs(root):
        breakdown = run / "breakdown.md"
        if not breakdown.is_file():
            continue
        for line in breakdown.read_text(encoding="utf-8").splitlines():
            tokens = gates.WO_TOKEN.findall(line)
            if not ROW.match(line) or not tokens or tokens[0] != wo:
                continue
            match = TRACKER.search(line)
            if match:
                return int(match.group(1)), []
            return None, [f"V: {wo} has no (tracker: #N) mirror on its"
                          " breakdown row"]
    return None, [f"V: {wo} has no breakdown row"]


def transition(current, lifecycle, label):
    """(add, remove) making `label` the issue's only lifecycle label.
    Orthogonal families (size/risk/type/source/flags) are never touched."""
    add = [] if label in current else [label]
    remove = [name for name in current
              if name in lifecycle and name != label]
    return add, remove


def actor_conflict(author, reviewer):
    """PRD-0001: no work is verified by the agent that produced it. An
    unnamed reviewer is a conflict too — an anonymous posting identity
    cannot be shown to differ from the author."""
    if not reviewer.strip():
        return ["V: the reviewing actor is unnamed (set FACTORY_REVIEW_LOGIN)"]
    if author.strip().lower() == reviewer.strip().lower():
        return [f"V: {author} authored this PR and cannot review it —"
                " generation and verification must be separate actors (set"
                " FACTORY_REVIEW_TOKEN and FACTORY_REVIEW_LOGIN to a"
                " non-authoring identity)"]
    return []


def render_findings(wo, author, reviewer, output, status):
    """The review comment body: who reviewed whom, the verdict, and the
    literal output that produced it (truncated, never summarised away)."""
    verdict = "PASS" if status == 0 else "FAIL"
    if len(output) > MAX_FINDINGS_CHARS:
        output = (output[:MAX_FINDINGS_CHARS]
                  + "\n… truncated; see the check job's log for the rest.\n")
    return (
        f"{REVIEW_MARKER}\n"
        f"## Factory review — {wo}\n\n"
        f"Reviewed by `{reviewer}`, who is not the author `{author}`"
        " (PRD-0001: generation and verification are separate actors;"
        " ADR-0033: the agent reviewer pre-chews the PR so the human gate is"
        " judgment, not linting).\n\n"
        f"**Detectors and tests: {verdict}**\n\n"
        "<details><summary>Check output</summary>\n\n"
        f"```text\n{output.rstrip()}\n```\n\n"
        "</details>\n")


def _pull_request(env):
    """(the pull_request payload, problems) from the CI event file."""
    pr, error = gates.pr_event(env)
    if error:
        return None, [f"V: {error}"]
    if pr is None:
        return None, ["V: no pull_request in the CI event payload"]
    return pr, []


def _work_order(pr):
    """(the work order the PR cites, problems). Detector B already fails a
    PR that cites none, so reaching here without one is a real break."""
    match = gates.WO_TOKEN.search(pr.get("body") or "")
    if not match:
        return None, ["V: PR body cites no work-order id"]
    return match.group(0), []


def post_review(number, body, run):
    """Post (or update) the review comment. gh has nothing to edit on the
    first run of a PR, so a failing --edit-last falls back to a new
    comment — that keeps one live comment per PR instead of a thread of
    stale ones."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "review.md"
        path.write_text(body, encoding="utf-8")
        args = ["pr", "comment", str(number), "--body-file", str(path)]
        try:
            try:
                run([*args[:3], "--edit-last", *args[3:]])
            except label_sync.GH_FAILURES:
                run(args)
        except label_sync.GH_FAILURES as err:
            return [f"V: gh pr comment failed: {label_sync.gh_detail(err)}"]
    return []


def run_review(root, findings, status, env, run=label_sync.gh_runner):
    """The review job: post the check findings as a non-authoring actor."""
    pr, problems = _pull_request(env)
    if problems:
        return problems
    author = (pr.get("user") or {}).get("login") or ""
    problems = actor_conflict(author, env.get("FACTORY_REVIEW_LOGIN", ""))
    if problems:
        return problems
    try:
        output = Path(findings).read_text(encoding="utf-8")
    except OSError as err:
        return [f"V: cannot read findings file {findings}: {err}"]
    wo, _ = _work_order(pr)
    body = render_findings(wo or "(no work order cited)", author,
                           env["FACTORY_REVIEW_LOGIN"], output, status)
    return post_review(pr.get("number"), body, run)


def run_lifecycle(root, label, env, run=label_sync.gh_runner):
    """The merged-label job: flip the cited work order's lifecycle label."""
    lifecycle, problems = lifecycle_labels(root)
    if problems:
        return problems
    if label not in lifecycle:
        return [f"V: {label} is not a lifecycle label in the taxonomy"]
    pr, problems = _pull_request(env)
    if problems:
        return problems
    wo, problems = _work_order(pr)
    if problems:
        return problems
    number, problems = tracker_issue(root, wo)
    if problems:
        return problems
    try:
        current = json.loads(
            run(["issue", "view", str(number), "--json", "labels"]))
    except label_sync.GH_FAILURES as err:
        return [f"V: gh issue view {number} failed:"
                f" {label_sync.gh_detail(err)}"]
    names = [entry.get("name") for entry in current.get("labels", [])]
    add, remove = transition(names, lifecycle, label)
    if not add and not remove:
        return []
    args = ["issue", "edit", str(number)]
    for name in add:
        args += ["--add-label", name]
    for name in remove:
        args += ["--remove-label", name]
    try:
        run(args)
    except label_sync.GH_FAILURES as err:
        return [f"V: gh issue edit {number} failed:"
                f" {label_sync.gh_detail(err)}"]
    return []


def parse(argv):
    """(command, options) for a well-formed invocation, else (None, None)."""
    if not argv:
        return None, None
    command, rest, options = argv[0], argv[1:], {}
    while rest:
        if not rest[0].startswith("--") or len(rest) < 2:
            return None, None
        options[rest[0][2:]] = rest[1]
        rest = rest[2:]
    if command == "review" and set(options) <= {"findings", "status"}:
        status = options.get("status", "0")
        if not status.isdigit():
            return None, None
        return command, {"findings": options.get("findings", "findings.txt"),
                         "status": int(status)}
    if command == "lifecycle" and set(options) == {"label"}:
        return command, options
    return None, None


def main(argv, env=None, run=label_sync.gh_runner):
    env = os.environ if env is None else env
    root = gates.repo_root()
    command, options = parse(argv)
    if command == "review":
        problems = run_review(root, options["findings"], options["status"],
                              env=env, run=run)
    elif command == "lifecycle":
        problems = run_lifecycle(root, options["label"], env=env, run=run)
    else:
        print(__doc__.strip())
        return 2
    for problem in problems:
        print(problem)
    print(f"validator: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
