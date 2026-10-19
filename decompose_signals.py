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
import datetime
import hashlib
from collections import Counter
import re
import sys
from pathlib import Path

from cli import CLI_FAILURES, detail, read_file, report, runner
from eval_schema import write_snapshot
from knowledge_plane import (BLOCKED_BY, ROW, WO_TOKEN, breakdown_files,
                             breakdown_rows, repo_root, row_title, unfenced)
from protocol import STAGE_ARTIFACTS, run_ref

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
# ADR-0109's rule, printed in every report and written into every record.
RULE = ("a boundary is observed when its commit subject reads"
        " docs(<any scope>): <stage>, the stage a whole word, and the commit"
        " changes that stage's artifact in the run's own directory; any"
        " other boundary is inferred (ADR-0109)")
USAGE = "python3 decompose_signals.py [--record]"
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
        # upgrade if a record ever reports it. --full-history: default
        # simplification follows only a merge's TREESAME parent, so a run
        # branch that merged its trunk could hide its own boundaries.
        out, problems = _git(
            run, root, ["log", "--stdin", "--full-history",
                        "--author-date-order", "--reverse", "--name-only",
                        _FORMAT, "--", *PATHSPECS],
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


def _unique_titles(items):
    """{normalized title: key} for the titles that are non-empty and occur
    once in their version — a repeated title is ambiguous, so it matches
    nothing by title."""
    seen = Counter(title for title, _ in items.values())
    return {title: key for key, (title, _) in items.items()
            if title and seen[title] == 1}


def _match(old, new):
    """{D key: I key}, one-to-one, under Owner decision 6: a title pass
    over unique titles, then a key pass over what is left."""
    old_titles, new_titles = _unique_titles(old), _unique_titles(new)
    pairs = {old_titles[t]: new_titles[t]
             for t in old_titles if t in new_titles}
    taken = set(pairs.values())
    pairs.update({k: k for k in old
                  if k not in pairs and k in new and k not in taken})
    return pairs


def replan(d_lines, i_lines, d_sha, i_sha):
    """The work-item diff between the decompose (D) and implement (I)
    versions: {items_at_d, added, dropped, split, merged, renamed, count},
    or {unmeasurable: reason} when a version repeats a key. Items match
    by title first, then by key; a title match whose keys differ is a
    rename, never a re-plan. A split or a merge is read only from
    citations, and a dropped key some I-version item still uses names
    that item, so it is never cited."""
    old, reason = _version(d_lines, d_sha)
    new, reason = (None, reason) if reason else _version(i_lines, i_sha)
    if reason:
        return {"unmeasurable": reason}
    pairs = _match(old, new)
    matched = set(pairs.values())
    added = [k for k in new if k not in matched]
    dropped = [k for k in old if k not in pairs]
    citable = set(added) | {k for k in dropped if k not in new}
    cited = {k: _cites(new[k][1], citable) - {k} for k in new}
    split = sum(1 for k in matched if len(cited[k] & set(added)) > 1)
    split += sum(1 for d in dropped
                 if sum(1 for a in added if d in cited[a]) > 1)
    merged = sum(1 for a in added if len(cited[a] & set(dropped)) > 1)
    return {"items_at_d": len(old), "added": len(added),
            "dropped": len(dropped), "split": split, "merged": merged,
            "renamed": sum(1 for d, i in pairs.items() if d != i),
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
        # A cherry-picked or rebased copy on another ref keeps the
        # subject and author date: one route, however many refs hold it.
        routes = len({(c["author_time"], c["subject"])
                      for c in _within(commits, d, i)
                      if _observed(c, run_rel, "architect")})
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


def _reader(root, run, problems):
    """A cached read(sha, path): each version is shown once, and a failed
    show is one problem however many signals ask for it."""
    cache = {}

    def read(sha, path):
        if (sha, path) not in cache:
            text, failed = read_version(root, run, sha, path)
            problems.extend(failed)
            cache[sha, path] = text
        return cache[sha, path]
    return read


def _replan(bounds, path, read):
    d, i = bounds["decompose"], bounds["implement"]
    for boundary in (d, i):
        if "unmeasurable" in boundary:
            return {"unmeasurable": boundary["unmeasurable"]}
    d_text, i_text = read(d["sha"], path), read(i["sha"], path)
    if d_text is None or i_text is None:
        return {"unmeasurable": READ_FAILED}
    diff = replan(d_text.splitlines(), i_text.splitlines(), d["sha"],
                  i["sha"])
    if "unmeasurable" in diff:
        return diff
    both = d["label"] == i["label"] == "observed"
    return {"label": "observed" if both else "inferred", **diff}


def _run_record(root, run_dir, lines, commits, read, problems):
    rel = run_dir.relative_to(root).as_posix()
    path = f"{rel}/{ARTIFACT['decompose']}"
    bounds = boundaries(commits, rel, read)
    d = bounds["decompose"]
    d_text = read(d["sha"], path) if "sha" in d else None
    review_text, problem = read_file(run_dir / ARTIFACT["review"],
                                     f"{rel}/{ARTIFACT['review']}", str)
    if problem:
        problems.append(f"{LABEL}: {problem}")
        review = {"unmeasurable": READ_FAILED}
    else:
        review = review_findings(review_text, lines)
    return {"run": run_ref(root, run_dir), "path": rel, **bounds,
            "replan": _replan(bounds, path, read),
            "design_gaps": design_gaps(commits, rel, bounds, d_text),
            "review": review}


# (signal, RunRecord field, numerator field, denominator field or None
# for one per measured run), in report order.
SIGNALS = (("re-plan", "replan", "count", "items_at_d"),
           ("design gaps", "design_gaps", "routes", None),
           ("review-traced", "review", "named", "findings"))
POPULATIONS = ("observed", "inferred")


def _aggregate(runs):
    """Per signal, each population's {runs, numerator, denominator} plus
    the combined figure and the unmeasurable run count. Unmeasurable never
    reaches a count; a review with no finding heading is observed 0/0."""
    aggregate = {}
    for signal, field, num, den in SIGNALS:
        measured = [r[field] for r in runs if "unmeasurable" not in r[field]]
        figures = {}
        for population in (*POPULATIONS, "combined"):
            chosen = [m for m in measured if population == "combined"
                      or m.get("label", "observed") == population]
            figures[population] = {
                "runs": len(chosen),
                "numerator": sum(m.get(num, 0) for m in chosen),
                "denominator": sum(m.get(den, 0) if den else 1
                                   for m in chosen)}
        figures["unmeasurable"] = len(runs) - len(measured)
        aggregate[signal] = figures
    return aggregate


def measure(root, run):
    """(result, problems): the refs read, their digest, the rule, one
    RunRecord per run with a breakdown in run-path order, and the
    aggregate; result is None when the history could not be read."""
    root = Path(root)
    history, problems = read_history(root, run)
    if history is None:
        return None, problems
    read = _reader(root, run, problems)
    runs = [_run_record(root, path.parent, lines, history["commits"], read,
                        problems)
            for path, lines in sorted(breakdown_files(root))]
    return {"refs": history["refs"], "refs_digest": history["digest"],
            "rule": RULE, "runs": runs, "aggregate": _aggregate(runs)}, \
        problems


def _boundary(stage, boundary):
    if "unmeasurable" in boundary:
        return f"{stage} none"
    return f"{stage} {boundary['label']} {boundary['sha'][:7]}"


def _signal(record, signal, field):
    value = record[field]
    if "unmeasurable" in value:
        return f"{signal} unmeasurable — {value['unmeasurable']}"
    if field == "replan":
        return (f"re-plan {value['count']} of {value['items_at_d']} (added"
                f" {value['added']}, dropped {value['dropped']}, split"
                f" {value['split']}, merged {value['merged']}; renamed"
                f" {value['renamed']}) {value['label']}")
    if field == "design_gaps":
        return f"design gaps {value['routes']} {value['label']}"
    if not value["findings"]:
        return "review-traced 0 findings — review.md has no finding heading"
    return (f"review-traced {value['named']} of {value['findings']}"
            " findings name an item")


def render(result):
    """The report's lines, header first and aggregate last."""
    refs = ", ".join(f"{ns} ({n})" for ns, n in result["refs"].items())
    lines = [f"{LABEL}: refs read — {refs or 'none'}; {STASH} skipped;"
             f" digest {result['refs_digest'][:12]}",
             f"{LABEL}: boundary rule — {result['rule']}"]
    for record in result["runs"]:
        parts = [f"{_boundary('decompose', record['decompose'])},"
                 f" {_boundary('implement', record['implement'])}"]
        parts += [_signal(record, signal, field)
                  for signal, field, _, _ in SIGNALS]
        lines.append(f"{LABEL}: {record['run']} — {'; '.join(parts)}")
    for signal, figures in result["aggregate"].items():
        shown = "; ".join(
            f"{population} {f['numerator']}/{f['denominator']} over"
            f" {f['runs']} run(s)"
            for population, f in ((p, figures[p])
                                  for p in (*POPULATIONS, "combined")))
        lines.append(f"{LABEL}: aggregate {signal} — {shown}; unmeasurable"
                     f" {figures['unmeasurable']} run(s)")
    return lines


def record(root, run, result, problems):
    """Write the snapshot through eval_schema and return its path, or
    None with a refusal appended to `problems`: a record must be
    reproducible from the refs, so docs/ must be clean and the
    measurement problem-free."""
    if problems:
        problems.append(f"{LABEL}: --record refused: the measurement has"
                        " problems")
        return None
    dirty, failed = _git(run, root, ["status", "--porcelain", "--",
                                     "docs/"])
    head, failed_head = _git(run, root, ["rev-parse", "HEAD"])
    if failed or failed_head:
        problems.extend(failed + failed_head)
        return None
    if dirty.strip():
        problems.append(f"{LABEL}: --record refused: git status"
                        " --porcelain -- docs/ is not empty")
        return None
    snapshot = {"date": datetime.date.today().isoformat(),
                "head": head.strip(), **result}
    path = write_snapshot(snapshot, root / "evals" / "results",
                          "decompose-signals")
    return path.relative_to(root).as_posix()


def main(argv, root=None, run=None):
    """`python3 decompose_signals.py [--record]` — print every run's
    signals and the aggregate; with --record, also write them as an
    append-only snapshot. Exit 0 when nothing failed (unmeasurable runs
    included), 1 with problems, 2 on an unknown argument."""
    if argv not in ([], ["--record"]):
        print(f"{LABEL}: {' '.join(argv)!r} — unknown argument\n\n"
              f"  {USAGE}")
        return 2
    root = Path(root) if root is not None else repo_root()
    run = run or runner("git", timeout=GIT_TIMEOUT)
    result, problems = measure(root, run)
    for line in render(result) if result else []:
        print(line)
    if result and argv:
        path = record(root, run, result, problems)
        if path:
            print(f"{LABEL}: recorded {path}")
    return report(LABEL, problems,
                  prefix=f"{len(result['runs']) if result else 0} run(s), ")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
