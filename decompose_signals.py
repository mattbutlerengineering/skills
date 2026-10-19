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
from knowledge_plane import (BLOCKED_BY, ROW, WO_TOKEN, breakdown_rows,
                             row_title, unfenced)
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


# A short label leading the bold span (S1, A1, I2): the form the fix-run
# breakdowns and this run's own use. A word with more letters (ADR0109)
# or a range (S1-S3) is not one.
_LABEL = re.compile(r"([A-Z]{1,2}\d+[a-z]?)(?![\w-])")
_BOLD = re.compile(r"\*\*(.+?)\*\*")


def _item(line):
    """(key, normalized title) of one breakdown row line."""
    rest = line[ROW.match(line).end():]
    wo = WO_TOKEN.search(rest)
    if wo:
        title = row_title(line) or rest[wo.end():].split(" — ")[0]
        return wo.group(0), _normal(title)
    bold = _BOLD.match(rest.strip())
    if bold:
        label = _LABEL.match(bold.group(1).strip())
        if label:
            after = rest.replace("**", "").strip()[label.end():]
            title = after.strip(" —-:").split(" — ")[0]
            return label.group(1), _normal(title)
        key = bold.group(1).strip()
        return key, _normal(key)
    key = rest.split(" — ")[0].strip()
    return key, _normal(key)


def _normal(title):
    """A title compared for a rename: case, code marks, spacing and a
    trailing full stop are not part of it."""
    return " ".join(title.replace("`", "").lower().split()).rstrip(".:")


def item_keys(lines):
    """The work-item key of every row in one breakdown version, in order:
    its WO token, else a short label leading its bold span, else the
    bold text, else the row text up to the first ` — `."""
    return [_item(r["text"])[0] for r in breakdown_rows(lines)]


def _cites(line, keys):
    """The keys in `keys` that `line` names as whole tokens outside its
    `blocked by:` clause — a dependency is never a split or a merge."""
    clause = BLOCKED_BY.search(line)
    text = line[:clause.start()] + line[clause.end():] if clause else line
    return {key for key in keys
            if re.search(rf"(?<!\w){re.escape(key)}(?!\w)", text)}


def _version(lines, sha):
    """({key: (title, line)}, unmeasurable reason or None)."""
    items = {}
    for r in breakdown_rows(lines):
        key, title = _item(r["text"])
        if key in items:
            return None, f"duplicate work-item key {key} at {sha[:7]}"
        items[key] = (title, r["text"])
    return items, None


def replan(d_lines, i_lines, d_sha, i_sha):
    """The work-item diff between the decompose (D) and implement (I)
    versions: {items_at_d, added, dropped, split, merged, renamed, count},
    or {unmeasurable: reason} when a version repeats a key. A rename (a
    dropped and an added item with the same title) is not a re-plan; a
    split or a merge is read only from citations."""
    old, reason = _version(d_lines, d_sha)
    new, reason = (None, reason) if reason else _version(i_lines, i_sha)
    if reason:
        return {"unmeasurable": reason}
    added = [k for k in new if k not in old]
    dropped = [k for k in old if k not in new]
    renamed = 0
    for key in list(dropped):
        twin = next((a for a in added if new[a][0] == old[key][0]), None)
        if twin is not None:
            added.remove(twin)
            dropped.remove(key)
            renamed += 1
    cited = {k: _cites(new[k][1], set(added) | set(dropped)) - {k}
             for k in new}
    split = sum(1 for k in new if k in old and len(cited[k] & set(added)) > 1)
    split += sum(1 for d in dropped
                 if sum(1 for a in added if d in cited[a]) > 1)
    merged = sum(1 for a in added if len(cited[a] & set(dropped)) > 1)
    return {"items_at_d": len(old), "added": len(added),
            "dropped": len(dropped), "split": split, "merged": merged,
            "renamed": renamed,
            "count": len(added) + len(dropped) + split + merged}


def _within(commits, d, i):
    """The commits in the window (D, I], in walk order."""
    shas = [c["sha"] for c in commits]
    return commits[shas.index(d["sha"]) + 1:shas.index(i["sha"]) + 1]


# Decompose's TEMPLATE.md section: gaps routed back to Architect, or none.
_GAPS_HEADING = re.compile(r"^##\s+Design gaps found\s*$", re.IGNORECASE)
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
NO_GAPS_SECTION = 'no "Design gaps found" section at the decompose boundary'


def _gaps_words(text):
    """The words of the unfenced `## Design gaps found` section, emphasis
    stripped, or None when there is no such section or it says nothing."""
    words, inside = None, False
    for _, line in unfenced(text.splitlines()):
        heading = _HEADING.match(line)
        if inside and heading and len(heading.group(1)) <= 2:
            break
        if _GAPS_HEADING.match(line):
            inside, words = True, []
        elif inside:
            words += re.sub(r"[*_`]", "", line).split()
    return words or None


def design_gaps(commits, run_rel, bounds, d_text):
    """Routes back to Architect: {label, routes, source} or {unmeasurable:
    reason}. With D observed, the architect boundary commits for this run
    in (D, I], labelled as I is. With D inferred, the D version's `Design
    gaps found` section (`d_text`, None when its read failed): `none`
    gives 0 and anything else 1, labelled inferred."""
    d, i = bounds["decompose"], bounds["implement"]
    if "unmeasurable" in d:
        return {"unmeasurable": d["unmeasurable"]}
    if d["label"] == "observed":
        if "unmeasurable" in i:
            return {"unmeasurable": i["unmeasurable"]}
        routes = sum(1 for c in _within(commits, d, i)
                     if _observed(c, run_rel, "architect"))
        return {"label": i["label"], "routes": routes, "source": "subjects"}
    if d_text is None:
        return {"unmeasurable": READ_FAILED}
    words = _gaps_words(d_text)
    if words is None:
        return {"unmeasurable": NO_GAPS_SECTION}
    return {"label": "inferred",
            "routes": 0 if words[0].strip(".,:;!").lower() == "none" else 1,
            "source": "section"}


# A finding heading (levels 2 to 4, emphasis stripped) leads with a
# severity word or an ordinal label (F1, Finding 1, 1.).
_FINDING = re.compile(
    r"^(?:(?:critical|major|minor|low|medium|high)\b(?!-)"
    r"|F\d+\b|Finding\s+\d+\b|\d+\.)", re.IGNORECASE)


def _finding_level(line):
    """The heading level when `line` is a finding heading, else None."""
    heading = _HEADING.match(line)
    if not heading or not 2 <= len(heading.group(1)) <= 4:
        return None
    text = re.sub(r"[*_]", "", heading.group(2)).strip()
    return len(heading.group(1)) if _FINDING.match(text) else None


def _names(text, keys):
    return any(re.search(rf"(?<!\w){re.escape(key)}(?!\w)", text)
               for key in keys)


def review_findings(review_text, breakdown_lines):
    """The review tracer's three shapes: {unmeasurable: "no review.md"}
    when review_text is None; {findings: 0, reason: "no finding heading"};
    or {label: observed, findings: N, named: M}, M being the findings
    whose block holds a current work-item key as a whole token. A block
    runs from its heading to the next unfenced heading at its own level
    or above, or the next finding heading."""
    if review_text is None:
        return {"unmeasurable": "no review.md"}
    lines = review_text.splitlines()
    headings = [(n - 1, _HEADING.match(line), _finding_level(line))
                for n, line in unfenced(lines) if _HEADING.match(line)]
    keys = set(item_keys(breakdown_lines))
    found = named = 0
    for at, (start, _, level) in enumerate(headings):
        if level is None:
            continue
        end = next((n for n, heading, other in headings[at + 1:]
                    if other or len(heading.group(1)) <= level), len(lines))
        found += 1
        named += _names("\n".join(lines[start:end]), keys)
    if not found:
        return {"findings": 0, "reason": "no finding heading"}
    return {"label": "observed", "findings": found, "named": named}
