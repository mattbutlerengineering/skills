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

A DELIBERATE second owner is annotated where it is defined, in the
contiguous comment block immediately above the definition:

    # one-owner: <module>.<name> (ADR-####) — <reason>

The reason is required — a bare marker waives nothing. Silence is a
property of the whole GROUP, never of one marker: a group is quiet only
when every member carries a marker AND every member is named by some
other member's marker, so a new owner cannot admit itself. Every marker
must also match a duplicate this pass actually finds, so a carve-out
whose counterpart was deleted, renamed or folded is itself a finding.

THE GRAMMAR IS DOCUMENTED HERE AND IN NO COMMENT IN THIS FILE. This
module is inside its own file universe and its marker grammar is a
comment pattern, so a `# one-owner:` comment written here would be read
as a live carve-out of the tool's own.

NOT A GATE. It is outside `make check` and outside every workflow: a
finding is a question for a human, and must never colour main red.
"""
import ast
import io
import re
import sys
import tokenize
from collections import namedtuple
from pathlib import Path

from cli import CLI_FAILURES, detail, report, runner
from knowledge_plane import repo_root

# The real git CLI (cli.runner): a failed or missing git raises
# CLI_FAILURES, and source_files turns that into a one-owner: problem
# string rather than a traceback.
# ADR-0037 has callers alias the seam to their own names "so their
# problem strings read unchanged" — recorded deliberate, not folded:
# one-owner: budget_guard.git_runner (ADR-0061) — ADR-0037 sanctions the alias
git_runner = runner("git")

# The payload under factory/templates/tools/factory/ is a deliberate
# byte-identical mirror of the root tools, whose equality detector E
# already owns, and factory/evals/fixtures/ holds intentionally broken
# repos. A test asserting an exact string IS that string's pin rather
# than a second owner of it.
EXCLUDED = ("factory/", "tests/")

# The marker grammar, as a reader is told to write it. A string, never a
# comment — see the docstring.
MARKER_GRAMMAR = "# one-owner: <module>.<name> (ADR-####) — <reason>"

_LEAD = re.compile(r"^#\s*one-owner:")
_MARKER = re.compile(r"^#\s*one-owner:\s*"
                     r"(?P<counterpart>[A-Za-z_]\w*\.[A-Za-z_]\w*)\s*"
                     r"\((?P<adr>ADR-\d{4})\)\s*—(?P<reason>.*)$")

# What one module states, at one place. `identity` is the grouping key
# and `lineno` is the definition's own line — the join key a marker
# above it is attached by.
# `lineno` and `attach` are two different questions about one definition.
# `lineno` is where a problem string points a reader — the `def` or the
# assignment. `attach` is where a comment block written above the
# definition ends, which for a decorated one is its first decorator. They
# are equal for everything else.
FactSite = namedtuple("FactSite",
                      ("kind", "path", "lineno", "attach", "name",
                       "identity"))

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
        # An ast.Assign has no decorator_list, so there is no second line
        # to carry and attach is the assignment's own.
        found += [FactSite("same-value", path, node.lineno, node.lineno,
                           target.id, identity)
                  for target in node.targets if isinstance(target, ast.Name)]
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        keys = _read_keys(node)
        if len(keys) > 1:
            # min, not decorator_list[0]: the list is source-ordered, but
            # min says the earliest decorator wins without the reader
            # having to know that.
            attach = min((d.lineno for d in node.decorator_list),
                         default=node.lineno)
            found.append(FactSite("same-keys", path, node.lineno, attach,
                                  node.name, ", ".join(sorted(keys))))
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


def _standalone_comments(source):
    """{lineno: comment text} for every comment that IS its own line.

    Tokenized rather than line-scanned, and that is load-bearing: a `#`
    inside a string or a docstring is not a comment, which is the only
    thing that lets this tool document its own marker grammar in its own
    docstring without reporting itself. A trailing comment after code is
    not a carve-out either — a marker sits above what it excuses.
    """
    found = {}
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if (token.type == tokenize.COMMENT
                    and not token.line[:token.start[1]].strip()):
                found[token.start[0]] = token.string
    except (tokenize.TokenError, SyntaxError, IndentationError):
        pass  # fact_sites reports the unparseable module; one report is enough
    return found


def markers(path, source):
    """([Marker, ...], problems) for one module: the deliberate second
    owners it records, read at the definitions they excuse.

    Comments are absent from the AST, so this is a line scan joined to
    fact_sites by the DEFINITION's lines — the one place the two readers
    of a file meet. A marker attaches only from inside the contiguous
    comment block immediately above a fact site; a blank line ends the
    block, because a marker one line away is near a definition rather
    than above it.

    "Above" means above the whole definition, decorators included. The
    join walks up from both `site.lineno` and `site.attach`, so a marker
    written above a decorated function attaches, and so does one written
    between its decorator and its `def` — the only placement that worked
    before `attach` existed.

    In every failure below the marker silences nothing: a marker that
    cannot be read is not a permission.
    """
    sites, _ = fact_sites(path, source)
    comments = _standalone_comments(source)
    owner_of = {}
    for site in sites:
        # Both lines, because both placements are above the definition to
        # a reader: the block above its first decorator, and the block
        # between that decorator and the `def`. For everything else the
        # two starts are equal and the second walk repeats the first.
        for start in (site.lineno, site.attach):
            lineno = start - 1
            while lineno in comments:
                owner_of[lineno] = site
                lineno -= 1
    found, problems = [], []
    for lineno in sorted(comments):
        text = comments[lineno]
        if not _LEAD.match(text):
            continue
        match = _MARKER.match(text)
        if not match:
            problems.append(f"one-owner: {path}:{lineno} is not a readable"
                            " one-owner marker (expected"
                            f" `{MARKER_GRAMMAR}`)")
            continue
        site = owner_of.get(lineno)
        if site is None:
            problems.append(f"one-owner: {path}:{lineno} is a one-owner"
                            " marker above no definition")
            continue
        reason = match.group("reason").strip()
        if not reason:
            problems.append(f"one-owner: {path}:{lineno} marks {site.name}"
                            " deliberate with no reason — a bare marker"
                            " waives nothing")
            continue
        found.append(Marker(path, lineno, site.name,
                            match.group("counterpart"), match.group("adr"),
                            reason))
    return found, problems


def _ident(path, name):
    """`<module>.<name>` — how a marker names an owner."""
    return f"{Path(path).stem}.{name}"


def _adr_ids(root):
    """The decision records this repo holds, as citable ids."""
    directory = Path(root) / "docs" / "adr"
    return {f"ADR-{path.name[:4]}" for path
            in directory.glob("[0-9][0-9][0-9][0-9]-*.md")
            } if directory.is_dir() else set()


def _coverage(found_groups, marks):
    """UNDER-COVERAGE. A group is silent only when every member carries a
    marker AND every member is named by some OTHER member's marker.

    The rule is stated over the group rather than per-pair because that
    is the only shape in which a new owner cannot admit itself: admitting
    it means editing an existing owner's file, where a reviewer is
    already looking. A group nobody has marked at all is the plain
    finding.
    """
    by_owner = {}
    for marker in marks:
        by_owner.setdefault((marker.path, marker.owner), []).append(marker)
    problems = []
    for group in found_groups:
        carried = {site: by_owner.get((site.path, site.name), [])
                   for site in group.sites}
        if not any(carried.values()):
            problems.append(_finding(group))
            continue
        for site in group.sites:
            if not carried[site]:
                problems.append(f"one-owner: {site.path}:{site.lineno}"
                                f" {site.name} joins a recorded deliberate"
                                " group without a marker — a new owner"
                                " cannot admit itself")
            elif not any(marker.counterpart == _ident(site.path, site.name)
                         for other in group.sites if other != site
                         for marker in carried[other]):
                problems.append(f"one-owner: {site.path}:{site.lineno}"
                                f" {site.name} carries a marker but no other"
                                " owner names it — an existing owner must"
                                " vouch for a new one")
    return problems


def _rent(found_groups, marks, sites, adr_ids):
    """OVER-COVERAGE. Every marker must match a duplicate this pass
    actually finds, and must cite a record that exists.

    A carve-out list nothing re-checks is the condition this tool exists
    to fix, so a marker whose counterpart was deleted, renamed or folded
    is itself a finding: the list cannot rot quietly.

    Whether the cited record is still LIVE is deliberately not checked.
    The status grammar's owner is gates.ADR_STATUS, and importing a
    detector module from a tool is the coupling ADR-0058 removed; folding
    that grammar into a seam is its own decision, not a ride-along.
    """
    defined = {_ident(site.path, site.name) for site in sites}
    group_of = {(site.path, site.name): group
                for group in found_groups for site in group.sites}
    problems = []
    for marker in marks:
        if marker.counterpart not in defined:
            problems.append(f"one-owner: {marker.path}:{marker.lineno} names"
                            f" {marker.counterpart}, which is not defined in"
                            " this repo")
        else:
            group = group_of.get((marker.path, marker.owner))
            peers = {_ident(site.path, site.name)
                     for site in group.sites} if group else set()
            if marker.counterpart not in peers:
                problems.append(f"one-owner: {marker.path}:{marker.lineno}"
                                f" {marker.owner} is marked deliberate"
                                f" against {marker.counterpart}, but nothing"
                                " duplicates it — remove the marker")
        if marker.adr not in adr_ids:
            problems.append(f"one-owner: {marker.path}:{marker.lineno} cites"
                            f" {marker.adr}, which is not in docs/adr/")
    return problems


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
    sites, marks = [], []
    for path, source in files:
        found, trouble = fact_sites(path, source)
        sites += found
        problems += trouble
        marked, marker_trouble = markers(path, source)
        marks += marked
        problems += marker_trouble
    found_groups = groups(sites)
    problems += _coverage(found_groups, marks)
    problems += _rent(found_groups, marks, sites, _adr_ids(root))
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
