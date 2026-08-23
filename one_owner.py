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
from collections import namedtuple

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


def fact_sites(path, source):
    """([FactSite, ...], problems) for one module, in source order.

    `same-value` — a module-level `NAME = <expr>` binding. Claim: these
    two modules state the same value. This is the MERGED_ROW / DONE_ROW
    shape.

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
    return sorted(found, key=lambda site: (site.lineno, site.name)), []
