#!/usr/bin/env python3
"""decompose-signals: Decompose outcome signals per run, from git history.

Step 1 of the Decompose learning loop (issue #986; the run is
docs/features/decompose-outcome-signals/). For every run directory with
a breakdown.md it finds the run's decompose and implement boundaries in
one git walk over every ref the clone holds (refs/stash excepted), and
labels each one observed or inferred under ADR-0109's rule.

READ-ONLY AND LOCAL. git is the only external CLI, reached through
cli.runner and injected as `run`; the tool never fetches. PR head refs
are read only once they are fetched, which is a manual step:

    git fetch origin '+refs/pull/*/head:refs/remotes/pr/*'

NOT A GATE. Unmeasurable is data, not a problem: a run whose history
cannot answer a signal is named with the reason and left out of that
signal's aggregate, never counted as zero.
"""
import hashlib
import re

from cli import CLI_FAILURES, detail
from knowledge_plane import breakdown_rows
from protocol import STAGE_ARTIFACTS

LABEL = "decompose-signals"
# Every call is local and read-only, so a retry after a timeout is safe.
GIT_TIMEOUT = 60
STASH = "refs/stash"
# stage -> the artifact its boundary commit writes (decompose and
# implement both write breakdown.md, architect architecture.md).
ARTIFACT = dict(STAGE_ARTIFACTS)
# ADR-0109, part 1: `docs(<any scope>): <stage>`, the stage a whole word.
SUBJECT = {stage: re.compile(rf"^docs\([^)]*\): {re.escape(stage)}\b")
           for stage in ARTIFACT}
# The run artifacts the walk is restricted to: every feature and fixes
# run's, and the product run's at the docs/ root.
PATHSPECS = tuple(
    spec for artifact in (ARTIFACT["decompose"], ARTIFACT["architect"])
    for spec in (f":(glob)docs/*/*/{artifact}", f"docs/{artifact}"))
# A NUL opens each commit record; unit separators split its header.
_FORMAT = "--format=%x00%H%x1f%at%x1f%s"


def _git(run, root, args, input=None):
    """(stdout, problems) for one git call."""
    try:
        return run(args, input=input, cwd=str(root)).stdout, []
    except CLI_FAILURES as err:
        return None, [f"{LABEL}: git {args[0]} failed: {detail(err)}"]


def _namespace(refname):
    """refs/remotes/<remote> for a remote-tracking ref, else the first two
    components (refs/heads, refs/tags, refs/pr, ...)."""
    parts = refname.split("/")
    depth = 3 if parts[1:2] == ["remotes"] and len(parts) > 3 else 2
    return "/".join(parts[:depth])


def _commits(out):
    """The walk's commit records, in walk order."""
    commits = []
    for record in out.split("\0")[1:]:
        header, _, rest = record.partition("\n")
        sha, author_time, subject = header.split("\x1f", 2)
        commits.append({"sha": sha, "author_time": int(author_time),
                         "subject": subject,
                         "files": [f for f in rest.splitlines() if f]})
    return commits


def read_history(root, run):
    """(history, problems). history is {refs: {namespace: count}, digest:
    sha256 hex of the sorted `refname sha` lines, commits: [{sha,
    author_time, subject, files}] oldest first in author-date order}, or
    None when for-each-ref or log fails."""
    out, problems = _git(run, root, ["for-each-ref",
                                     "--format=%(refname) %(objectname)"])
    if out is None:
        return None, problems
    lines = sorted(line for line in out.splitlines()
                   if line and line.split(" ", 1)[0] != STASH)
    names = [line.split(" ", 1)[0] for line in lines]
    refs = {}
    for name in names:
        refs[_namespace(name)] = refs.get(_namespace(name), 0) + 1
    digest = hashlib.sha256(
        "".join(f"{line}\n" for line in lines).encode()).hexdigest()
    commits = []
    if names:
        # lean: --name-only cannot tell a deletion from an edit, so a
        # deleted artifact's version read would fail as `read failed`;
        # no tracked commit deletes one today. --name-status is the
        # upgrade if a record ever reports it.
        out, problems = _git(
            run, root, ["log", "--stdin", "--author-date-order", "--reverse",
                        "--name-only", _FORMAT, "--", *PATHSPECS],
            input="".join(f"{name}\n" for name in names))
        if out is None:
            return None, problems
        commits = _commits(out)
    return {"refs": dict(sorted(refs.items())), "digest": digest,
            "commits": commits}, []


def read_version(root, run, sha, path):
    """(text of `path` at commit `sha`, problems); None on a failed show."""
    return _git(run, root, ["show", f"{sha}:{path}"])


def _done(text):
    """(checked rows, rows) in one breakdown version."""
    rows = breakdown_rows(text.splitlines())
    return sum(1 for r in rows if r["done"]), len(rows)


def _observed(commit, run_rel, stage):
    """ADR-0109: the subject names the stage and the commit writes the
    stage's artifact under this run's own directory."""
    return bool(SUBJECT[stage].match(commit["subject"])) and \
        f"{run_rel}/{ARTIFACT[stage]}" in commit["files"]


READ_FAILED = "read failed"


def boundaries(commits, run_rel, read):
    """{decompose: Boundary, implement: Boundary} for the run at `run_rel`
    (repo-relative, posix), each {sha, label} or {unmeasurable: reason}.
    `read(sha, path)` is a version's text, or None when it failed. A
    boundary that cannot be found makes every later one unmeasurable for
    the same reason."""
    path = f"{run_rel}/{ARTIFACT['decompose']}"
    touching = [(n, c) for n, c in enumerate(commits) if path in c["files"]]
    if not touching:
        return _both(f"no commit on the refs read changes {path}")
    found = next(((n, c) for n, c in touching
                  if _observed(c, run_rel, "decompose")), None)
    if found:
        (d_at, d), d_label = found, "observed"
    else:
        (d_at, d), d_label = touching[0], "inferred"
        text = read(d["sha"], path)
        if text is None:
            return _both(READ_FAILED)
        done, total = _done(text)
        if done:
            return _both(f"the first version ({d['sha'][:7]}) already"
                         f" checks {done} of {total} rows")
    later = [c for n, c in touching if n > d_at]
    return {"decompose": {"sha": d["sha"], "label": d_label},
            "implement": _implement(later, run_rel, path, read)}


def _both(reason):
    return {"decompose": {"unmeasurable": reason},
            "implement": {"unmeasurable": reason}}


def _implement(later, run_rel, path, read):
    """The implement Boundary among the breakdown commits after D."""
    for commit in later:
        if _observed(commit, run_rel, "implement"):
            return {"sha": commit["sha"], "label": "observed"}
    for commit in later:
        text = read(commit["sha"], path)
        if text is None:
            return {"unmeasurable": READ_FAILED}
        if _done(text)[0]:
            return {"sha": commit["sha"], "label": "inferred"}
    return {"unmeasurable":
            "no implement boundary: no later commit checks a row"}
