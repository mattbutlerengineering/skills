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
        the agent that produced it. The reviewing identity is derived from
        the TOKEN (see reviewer_login), not from a variable that declares it;
        anything unresolved or self-reviewing refuses to post (nonzero,
        nothing said). Red findings are posted and do NOT fail the review
        job: failing the build is the check job's work, and a reviewer that
        goes silent on red is useless.

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
from knowledge_plane import (CLOSES_TOKEN, WO_TOKEN, repo_root,
                             row_work_order, run_dirs)

LIFECYCLE_PREFIX = "wo:"
# The row grammar itself is knowledge_plane.ROW/row_work_order — the same
# rule the assembler dispatches with, so the two cannot diverge.
TRACKER = re.compile(r"\(tracker:\s*#(\d+)\)")
REVIEW_MARKER = "<!-- factory-review -->"
MAX_FINDINGS_CHARS = 12000
# Who a workflow's own GITHUB_TOKEN posts as. GitHub fixes this — it is a
# property of the token, not a setting, which is what makes it safe to assume
# when no FACTORY_REVIEW_TOKEN was supplied.
GITHUB_TOKEN_LOGIN = "github-actions[bot]"


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
    for run in run_dirs(root):
        breakdown = run / "breakdown.md"
        if not breakdown.is_file():
            continue
        for line in breakdown.read_text(encoding="utf-8").splitlines():
            if row_work_order(line) != wo:
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


def reviewer_login(env, run):
    """(the login the review token actually posts as, problems).

    The TOKEN is the authority, never a human-maintained variable. A declared
    login proves nothing about who the token posts as, and the moment the two
    disagree PRD-0001's non-authoring property lapses SILENTLY: point
    FACTORY_REVIEW_TOKEN at the assembler bot's PAT, leave FACTORY_REVIEW_LOGIN
    unset, and a guard that compares the author against the declaration sees
    two different strings, posts, and reports success — while the bot reviews
    its own PR.

    Two token provenances, both derived, and the caller must DECLARE which:
      - FACTORY_REVIEW_TOKEN_SET=false: GH_TOKEN is the workflow's own
        GITHUB_TOKEN, whose posting identity GitHub fixes at
        GITHUB_TOKEN_LOGIN. Asking it is pointless — `gh api user` needs a
        user-scoped token.
      - FACTORY_REVIEW_TOKEN_SET=true: ask the token who it is.
    An ABSENT flag is not "false". Inside validator.yml both env values come
    from one condition and cannot disagree, but any OTHER caller of `make
    review` in a stamped repo (WO-0005's assembler running a re-review job
    with its PAT in GH_TOKEN) would otherwise reintroduce the original bug
    verbatim: a reviewer ASSERTED to be github-actions[bot] while posting as
    factory-bot. Detector E pins factory/templates/**, not a downstream
    repo's other workflows, so nothing else would catch it.

    An identity that cannot be resolved fails CLOSED — the caller posts
    nothing. A reviewer who cannot be named cannot be shown to differ from
    the author, and an unnamed reviewer is exactly the failure this guards.
    """
    provenance = env.get("FACTORY_REVIEW_TOKEN_SET", "").strip().lower()
    if provenance not in ("true", "false"):
        return None, ["V: the review step did not declare the token's"
                      " provenance (FACTORY_REVIEW_TOKEN_SET) — refusing"
                      " to post"]
    if provenance == "false":
        return GITHUB_TOKEN_LOGIN, []
    try:
        login = run(["api", "user", "--jq", ".login"]).strip()
    except label_sync.GH_FAILURES as err:
        return None, ["V: cannot resolve the reviewing identity from"
                      " FACTORY_REVIEW_TOKEN (gh api user failed:"
                      f" {label_sync.gh_detail(err)}) — refusing to post"]
    if not login:
        return None, ["V: FACTORY_REVIEW_TOKEN resolves to no login —"
                      " refusing to post"]
    return login, []


def actor_conflict(author, reviewer):
    """PRD-0001: no work is verified by the agent that produced it. An
    unnamed actor on EITHER side is a conflict too — a name that is not there
    compares unequal to every login, so the guard would pass on nothing
    rather than on a demonstrated difference."""
    if not reviewer.strip():
        return ["V: the reviewing actor is unnamed — no identity was resolved"
                " from the review token"]
    if not author.strip():
        return ["V: the PR's author is unnamed — an author who cannot be"
                " named cannot be shown to differ from the reviewer"]
    if author.strip().lower() == reviewer.strip().lower():
        return [f"V: {author} authored this PR and cannot review it —"
                " generation and verification must be separate actors (give"
                " the reviewer its own identity: FACTORY_REVIEW_TOKEN)"]
    return []


def declared_conflict(declared, reviewer):
    """FACTORY_REVIEW_LOGIN, if set, is an optional cross-check on the
    identity the token resolved to — never the authority. When it disagrees,
    the configuration is lying about who reviews, and a guard that cannot
    trust its own configuration stops rather than posts."""
    declared = declared.strip()
    if declared and declared.lower() != reviewer.strip().lower():
        return [f"V: FACTORY_REVIEW_LOGIN declares {declared} but the review"
                f" token posts as {reviewer} — refusing to post until the"
                " declaration matches the token"]
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


def cited_work_order(root, body):
    """(the work order this PR implements, problems).

    NOT "the first WO token in the body": the body is author-controlled prose
    that legitimately NAMES other work orders — a blocking edge ("builds on
    WO-0004"), a quoted Accept line — and taking the first token would flip
    the WRONG issue's lifecycle label on merge. The citation is structural
    instead: the work order a PR implements is the one whose breakdown row is
    mirrored to an issue the PR closes. Detector B already requires both
    halves of that (a WO token AND a Closes #N link), and the issue number
    still comes from the row, never from the body — ADR-0032's mirror stays
    one-way. Ambiguity fails CLOSED: nothing is labelled.
    """
    cited = list(dict.fromkeys(WO_TOKEN.findall(body)))
    if not cited:
        return None, ["V: PR body cites no work-order id"]
    closes = sorted({int(n) for n in CLOSES_TOKEN.findall(body)})
    if not closes:
        return None, ["V: PR body has no Closes #N link, so the work order it"
                      " implements cannot be told from the ones it only"
                      " mentions"]
    matched = [wo for wo in cited if tracker_issue(root, wo)[0] in closes]
    if len(matched) == 1:
        return matched[0], []
    if len(matched) > 1:
        return None, ["V: this PR closes the mirrored issues of more than one"
                      f" work order ({', '.join(matched)}); a work order is"
                      " one PR"]
    if len(cited) == 1:
        # One citation and it did not resolve: say why (no row, no tracker)
        # rather than hiding the reason behind "nothing matched".
        problems = tracker_issue(root, cited[0])[1]
        if problems:
            return None, problems
    closed = ", ".join(f"#{n}" for n in closes)
    return None, [f"V: none of the work orders this PR cites"
                  f" ({', '.join(cited)}) is mirrored to an issue it closes"
                  f" ({closed}) — a PR implements the work order whose"
                  " breakdown row it closes"]


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
    reviewer, problems = reviewer_login(env, run)
    if problems:
        return problems
    author = (pr.get("user") or {}).get("login") or ""
    problems = (actor_conflict(author, reviewer)
                + declared_conflict(env.get("FACTORY_REVIEW_LOGIN", ""),
                                    reviewer))
    if problems:
        return problems
    try:
        output = Path(findings).read_text(encoding="utf-8")
    except OSError as err:
        return [f"V: cannot read findings file {findings}: {err}"]
    # The heading is cosmetic. An unresolvable citation must not silence the
    # reviewer (the findings are the point) — but it must not name a work
    # order this PR may not implement either. Only the merged-label step,
    # which MUTATES an issue, is strict about it.
    wo, _ = cited_work_order(root, pr.get("body") or "")
    body = render_findings(wo or "(no work order resolved)", author, reviewer,
                           output, status)
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
    wo, problems = cited_work_order(root, pr.get("body") or "")
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
    root = repo_root()
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
