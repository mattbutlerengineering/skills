#!/usr/bin/env python3
"""one_owner: a read-only pre-pass asking which facts have two owners.

This repo's bar is one fact, one owner — CLAUDE.md states it as the
shared-module rule and half a dozen ADRs are each one instance of a
human enforcing it by hand, after the fact. Nothing mechanical asked
the question until this file, and the only finder the class had (a
human reading the tree during a deepening review) has a measured hit
rate of 4 of 7 (docs/fixes/one-fact-one-owner/defect.md).

DELIBERATELY SYNTACTIC AND DELIBERATELY SHALLOW. It answers "is this
stated twice?", never "do these two things mean the same thing?" — the
second question is semantic comparison, which costs more to maintain
than the manual review it replaces. A re-implementation of a rule in
different words is a known miss, pinned as one in
tests/test_one_owner.py rather than chased.

NOT A GATE. It is outside `make check` and outside every workflow: a
finding is a question for a human, and must never colour main red.
"""
import ast
import sys
from collections import namedtuple
from pathlib import Path

from cli import CLI_FAILURES, detail, report, runner
from knowledge_plane import repo_root

# The real git CLI (cli.runner): a failed or missing git raises
# CLI_FAILURES, and source_files turns that into a one-owner: problem
# string rather than a traceback.
git_runner = runner("git")

# The payload under factory/templates/tools/factory/ is a deliberate
# byte-identical mirror of the root tools, whose equality detector E
# already owns, and factory/evals/fixtures/ holds intentionally broken
# repos. A test asserting an exact string IS that string's pin rather
# than a second owner of it.
EXCLUDED = ("factory/", "tests/")

# What one module states, at one place. `identity` is the grouping key
# and `lineno` is the definition's own line — the join key a marker
# above it is attached by.
FactSite = namedtuple("FactSite",
                      ("kind", "path", "lineno", "name", "identity"))

# One recorded deliberate second owner, read at the definition it
# excuses. `lineno` is the marker comment's own line, `owner` the name
# of the definition it sits above.
Marker = namedtuple("Marker", ("path", "lineno", "owner", "counterpart",
                               "adr", "reason"))

# One identity owned by two or more distinct modules.
Group = namedtuple("Group", ("identity", "sites"))


def groups(sites):
    """PURE: fact sites in, the groups whose members span two or more
    distinct modules out, sorted by identity and then by kind.

    Kind is part of the grouping key as well as the sort: a value that
    happens to be spelled like a key set is not the same fact. Members
    are sorted by path then line, and the whole answer is deterministic
    — the suite asserts exact strings, so order is a contract. Total: it
    raises on nothing.
    """
    by_identity = {}
    for site in sites:
        by_identity.setdefault((site.kind, site.identity), []).append(site)
    found = [Group(identity,
                   sorted(members, key=lambda site: (site.path, site.lineno)))
             for (_, identity), members in by_identity.items()
             if len({member.path for member in members}) > 1]
    return sorted(found, key=lambda group: (group.identity,
                                            group.sites[0].kind))


def _stated_value(node):
    """The identity of a module-level binding's value, or None when the
    value states no fact. ast.unparse normalises source text, so a
    re-wrapped or re-quoted copy has the same identity and formatting
    can never hide one.

    The floor is STRUCTURAL, never a character count: a bare numeric,
    boolean or None literal is a tuning knob two modules may set alike
    without either owning anything. A knob has no principled length, so
    a length threshold would be a number nobody could ever argue about.
    """
    if isinstance(node, ast.Constant) and (
            node.value is None or isinstance(node.value, (bool, int, float,
                                                          complex))):
        return None
    return ast.unparse(node)


def _read_keys(node):
    """The named external shape a function reads: every string literal it
    uses as a `.get("...")` argument or a `[...]` subscript, anywhere in
    its body. How the key is spelled does not matter — a seam retyped
    with subscripts reads the same shape as one retyped with .get.
    """
    keys = set()
    for child in ast.walk(node):
        if (isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr == "get" and child.args
                and isinstance(child.args[0], ast.Constant)
                and isinstance(child.args[0].value, str)):
            keys.add(child.args[0].value)
        elif (isinstance(child, ast.Subscript)
                and isinstance(child.slice, ast.Constant)
                and isinstance(child.slice.value, str)):
            keys.add(child.slice.value)
    return keys


def fact_sites(path, source):
    """([FactSite, ...], problems) for one module, in source order.

    `same-value` — a module-level `NAME = <expr>` binding. Claim: these
    two modules state the same value. This is the MERGED_ROW / DONE_ROW
    shape.

    `same-keys` — a function definition anywhere in the module, read at
    least TWO named keys deep. Claim: these two functions read the same
    named external shape, which in this repo is what a seam owns. This is
    the retyped-seam shape defect.md's evidence table calls miss 3, and it
    works because two walks over one shape agree about the keys even when
    their code shares no text and their strictnesses differ.
    The floor is two keys and not three because the acceptance fixture's
    shared set is exactly {labels, name} — the fixture derives the
    threshold, rather than a threshold deciding the fixture.

    Unparseable source is REPORTED, never swallowed: a module that
    silently contributed nothing would take the tool quiet exactly when
    someone broke the file it was watching. Every other module still
    contributes.
    """
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as err:
        return [], [f"one-owner: {path} cannot be parsed: {err}"]
    found = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        identity = _stated_value(node.value)
        if identity is None:
            continue
        found += [FactSite("same-value", path, node.lineno, target.id,
                           identity)
                  for target in node.targets if isinstance(target, ast.Name)]
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        keys = _read_keys(node)
        if len(keys) > 1:
            found.append(FactSite("same-keys", path, node.lineno, node.name,
                                  ", ".join(sorted(keys))))
    return sorted(found, key=lambda site: (site.lineno, site.name)), []


def source_files(root, run=git_runner):
    """([(repo-relative posix path, source text), ...], problems), sorted
    by path — every module this repo owns, and nothing else.

    THE FILE LIST COMES FROM GIT, never from a filesystem walk. At HEAD an
    rglob finds 248 Python files where git tracks 96: 152 of the
    difference are stale `.claude/worktrees/agent-*` checkouts, months-old
    full copies holding definitions the tracked tree has since deleted.
    They are hidden by `.git/info/exclude`, which is LOCAL and
    UNCOMMITTED, so no committed file can be relied on to hide them. A
    walking tool would report a duplicate that does not exist, on its
    first run.

    An EMPTY universe is never silently clean: a broken environment must
    never read as "no duplicates", so an empty file list carries a
    problem of its own. One unreadable file is reported and skipped; the
    rest of the run is unaffected.
    """
    try:
        listed = run(["-C", str(root), "ls-files", "--", "*.py"]).stdout
    except CLI_FAILURES as err:
        return [], [f"one-owner: git ls-files failed: {detail(err)}"]
    files, problems = [], []
    for rel in sorted(line.strip() for line in listed.splitlines()
                      if line.strip()):
        if rel.startswith(EXCLUDED):
            continue
        try:
            files.append((rel, (Path(root) / rel).read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError) as err:
            problems.append(f"one-owner: {rel} cannot be read: {err}")
    if not files:
        problems.append("one-owner: no Python files to read — an empty"
                        " universe is never a clean one")
    return files, problems


def _members(sites):
    """Every owner of one fact, as a reader's list: `a and b` for a pair,
    `a, b and c` beyond it."""
    parts = [f"{site.path}:{site.lineno} {site.name}" for site in sites]
    return f"{', '.join(parts[:-1])} and {parts[-1]}"


def _finding(group):
    """One uncovered group, as the line a person reads."""
    claim = ("state the same value" if group.sites[0].kind == "same-value"
             else f"read the same payload keys ({group.identity})")
    return f"one-owner: {_members(group.sites)} {claim} — one fact, one owner"


def check(root, run=git_runner):
    """The whole answer: a sorted list of `one-owner: `-prefixed problem
    strings for one tree, read at one instant.

    There is no storage, no state file and no baseline. Every comparison
    is within a single read of a single working tree, so there is nothing
    to be eventually consistent with — and a baseline of "findings we
    already know about" would be a roster under another name, rotting the
    way the roster this tool exists to replace did.

    Deterministic: the same tree yields byte-identical output in the same
    order, which is what lets the suite assert exact strings. Raises on
    nothing — every failure is a problem string.
    """
    files, problems = source_files(root, run)
    sites = []
    for path, source in files:
        found, trouble = fact_sites(path, source)
        sites += found
        problems += trouble
    problems += [_finding(group) for group in groups(sites)]
    return sorted(problems)


def main(argv):
    """`python3 one_owner.py` — no options in this cut. Exiting nonzero on
    a finding is correct and is wired into no gate: a finding is a
    question for a human, never a reason to colour main red."""
    if argv:
        print(f"one-owner: {' '.join(argv)!r} — this tool takes no"
              " arguments\n\n  python3 one_owner.py")
        return 2
    return report("one-owner", check(repo_root()))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
