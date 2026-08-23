"""one_owner.py — the pre-pass that asks whether a fact is stated twice.

The tool this repo's "one fact, one owner" bar never had
(docs/fixes/one-fact-one-owner/). Every case here runs against LITERAL
fact sites or FIXTURE TREES, never against the live tree, so the suite
does not decay as the tree is cleaned — that is the point of the
historical fixtures in TestHistoricalInstances, which reproduce shapes
the tree no longer holds.
"""
import unittest
from pathlib import Path

from one_owner import FactSite, Group, Marker, fact_sites, groups


def site(kind, path, lineno, name, identity):
    return FactSite(kind, path, lineno, name, identity)


def value(path, lineno, name, identity):
    return site("same-value", path, lineno, name, identity)


def keys(path, lineno, name, identity):
    return site("same-keys", path, lineno, name, identity)


def sites_of(**modules):
    """fact_sites over literal module sources, keyed by module name.
    Returns (every site, every problem) so a case can hand the sites
    straight to groups()."""
    found, problems = [], []
    for name, source in modules.items():
        module_sites, module_problems = fact_sites(f"{name}.py", source)
        found += module_sites
        problems += module_problems
    return found, problems


def named(found):
    """(identity, [module.name, ...]) per group — what a case asserts
    when the identity's exact bytes are not the point."""
    return [(group.identity,
             [f"{Path(s.path).stem}.{s.name}" for s in group.sites])
            for group in groups(found)]


class TestGroups(unittest.TestCase):
    """The pure core: group fact sites by identity, keep the ones whose
    members span two or more distinct modules. No filesystem, no
    subprocess, no clock — a literal list in, groups out, so the tool and
    its suite cannot get different answers from the same data."""

    def test_two_members_in_distinct_modules_group(self):
        sites = [value("a.py", 10, "ONE", "'x'"),
                 value("b.py", 20, "TWO", "'x'")]
        self.assertEqual(groups(sites),
                         [Group("'x'", [sites[0], sites[1]])])

    def test_two_members_in_the_same_module_do_not(self):
        """One module restating its own value is not two owners."""
        self.assertEqual(groups([value("a.py", 10, "ONE", "'x'"),
                                 value("a.py", 20, "TWO", "'x'")]), [])

    def test_a_lone_member_is_not_a_group(self):
        self.assertEqual(groups([value("a.py", 10, "ONE", "'x'")]), [])

    def test_three_members_in_three_modules_group_as_one(self):
        sites = [value("a.py", 10, "ONE", "'x'"),
                 value("b.py", 20, "TWO", "'x'"),
                 value("c.py", 30, "THREE", "'x'")]
        self.assertEqual(groups(sites), [Group("'x'", list(sites))])

    def test_different_kinds_never_share_a_group(self):
        """Identity is only meaningful inside its kind: a value spelled
        `labels, name` and a key set of {labels, name} are not the same
        fact."""
        found = groups([value("a.py", 1, "ONE", "labels, name"),
                        value("b.py", 1, "TWO", "labels, name"),
                        keys("c.py", 1, "three", "labels, name"),
                        keys("d.py", 1, "four", "labels, name")])
        self.assertEqual([g.sites[0].kind for g in found],
                         ["same-keys", "same-value"])

    def test_identical_identities_sort_deterministically(self):
        """Two groups can carry the same identity across kinds, and the
        members of one group can share a path prefix — the order is a
        contract, because the suite asserts exact strings."""
        sites = [keys("d.py", 1, "four", "labels, name"),
                 keys("c.py", 1, "three", "labels, name"),
                 value("b.py", 9, "TWO", "labels, name"),
                 value("a.py", 3, "ONE", "labels, name"),
                 value("b.py", 2, "ZERO", "'x'"),
                 value("a.py", 4, "NIL", "'x'")]
        first = groups(sites)
        self.assertEqual(groups(list(reversed(sites))), first)
        self.assertEqual(
            [(g.identity, [(s.path, s.lineno) for s in g.sites])
             for g in first],
            [("'x'", [("a.py", 4), ("b.py", 2)]),
             ("labels, name", [("c.py", 1), ("d.py", 1)]),
             ("labels, name", [("a.py", 3), ("b.py", 9)])])

    def test_it_is_total_and_raises_on_nothing(self):
        for argument in ([], (), iter([]), [value("a.py", 1, "N", "'x'")]):
            with self.subTest(argument=argument):
                self.assertEqual(groups(argument), [])


# The miss-1 shape from defect.md's evidence table: gates.MERGED_ROW
# (208ffdb, 2026-07-11, #130) and knowledge_plane.DONE_ROW (4333370,
# 2026-08-10, #221), byte-identical in pattern AND flags.
CHECKED_ROW = r'''re.compile(r"^\s*[-*+]\s+\[x\]", re.IGNORECASE)'''
CHECKED_ROW_IDENTITY = r"re.compile('^\\s*[-*+]\\s+\\[x\\]', re.IGNORECASE)"


class TestSameValue(unittest.TestCase):
    """`same-value`: a module-level `NAME = <expr>` binding, identified by
    ast.unparse(value). The claim is narrow and exact — these two modules
    state the same value — so nothing but structural equality groups."""

    def test_two_modules_binding_one_compiled_pattern_are_two_owners(self):
        found, problems = sites_of(
            gates=f"MERGED_ROW = {CHECKED_ROW}\n",
            knowledge_plane=f"DONE_ROW = {CHECKED_ROW}\n")
        self.assertEqual(problems, [])
        self.assertEqual(named(found),
                         [(CHECKED_ROW_IDENTITY,
                           ["gates.MERGED_ROW", "knowledge_plane.DONE_ROW"])])

    def test_formatting_and_line_wrapping_do_not_hide_a_copy(self):
        """ast.unparse normalises, so the identity is the value, not the
        bytes: a re-wrapped, re-quoted copy is the same fact."""
        found, problems = sites_of(
            gates=f"MERGED_ROW = {CHECKED_ROW}\n",
            knowledge_plane=(
                "DONE_ROW = re.compile(\n"
                "    '^\\\\s*[-*+]\\\\s+\\\\[x\\\\]',\n"
                "    re.IGNORECASE,\n"
                ")\n"))
        self.assertEqual(problems, [])
        self.assertEqual(named(found),
                         [(CHECKED_ROW_IDENTITY,
                           ["gates.MERGED_ROW", "knowledge_plane.DONE_ROW"])])

    def test_a_bare_numeric_boolean_or_none_is_a_knob_not_a_fact(self):
        """The floor is structural, not a character count: two modules
        holding 100 have not stated a shared fact, they have tuned the
        same knob."""
        for literal in ("100", "1000", "True", "False", "None", "0.5"):
            with self.subTest(literal=literal):
                found, problems = sites_of(sweeps=f"TITLE_LIMIT = {literal}\n",
                                           work_queue=f"LIST_WINDOW = {literal}\n")
                self.assertEqual(problems, [])
                self.assertEqual(groups(found), [])

    def test_a_shared_string_or_call_is_a_fact(self):
        """The other side of the same floor — a bare string IS a stated
        fact (`CONTINUE`, `wo:ready-for-agent`), and drops nothing."""
        found, problems = sites_of(budget_guard="CONTINUE = 'CONTINUE'\n",
                                   cost_report="CONTINUE = 'CONTINUE'\n")
        self.assertEqual(problems, [])
        self.assertEqual(named(found),
                         [("'CONTINUE'", ["budget_guard.CONTINUE",
                                          "cost_report.CONTINUE"])])

    def test_the_canonical_deliberate_pair_stays_silent_with_no_marker(self):
        """defect.md's headline false-positive risk. protocol._CHECKBOX
        and knowledge_plane.ROW, exactly as written at HEAD: near-identical
        to a human, different in pattern AND flags, so an exact identity
        never groups them. No carve-out is involved — the rule is exact,
        which is why the marker mechanism has to earn its keep elsewhere."""
        found, problems = sites_of(
            protocol=('_CHECKBOX = re.compile(r"^\\s*[-*+]\\s+\\[([ xX])\\]",'
                      " re.MULTILINE)\n"),
            knowledge_plane='ROW = re.compile(r"^\\s*[-*+]\\s+\\[[ xX]\\]\\s")\n')
        self.assertEqual(problems, [])
        self.assertEqual(groups(found), [])

    def test_only_module_level_bindings_count(self):
        """A binding inside a function is local state, not a stated fact
        the tree can have two owners of."""
        found, problems = sites_of(
            a="def build():\n    LABEL = 'wo:ready-for-agent'\n    return LABEL\n",
            b="LABEL = 'wo:ready-for-agent'\n")
        self.assertEqual(problems, [])
        self.assertEqual(groups(found), [])

    def test_sites_come_back_in_source_order(self):
        found, problems = sites_of(
            a="FIRST = 'x'\nSECOND = 'y'\nTHIRD = 'z'\n")
        self.assertEqual(problems, [])
        self.assertEqual([(s.kind, s.lineno, s.name) for s in found],
                         [("same-value", 1, "FIRST"), ("same-value", 2, "SECOND"),
                          ("same-value", 3, "THIRD")])

    def test_a_module_that_cannot_be_parsed_is_reported_never_swallowed(self):
        """A tool that silently skipped a module would go quiet exactly
        when someone broke the module it was watching. Every other module
        still contributes."""
        found, problems = sites_of(broken="def (:\n", gates="A = 'x'\n",
                                   knowledge_plane="B = 'x'\n")
        self.assertEqual(len(problems), 1)
        self.assertTrue(
            problems[0].startswith("one-owner: broken.py cannot be parsed: "),
            problems[0])
        self.assertEqual(named(found),
                         [("'x'", ["gates.A", "knowledge_plane.B"])])


class TestDataModel(unittest.TestCase):
    """architecture.md's Data model, pinned: three namedtuples and their
    fields, because the fields are what every other interface passes."""

    def test_the_three_shapes_carry_the_declared_fields(self):
        self.assertEqual(FactSite._fields,
                         ("kind", "path", "lineno", "name", "identity"))
        self.assertEqual(Marker._fields, ("path", "lineno", "owner",
                                          "counterpart", "adr", "reason"))
        self.assertEqual(Group._fields, ("identity", "sites"))


if __name__ == "__main__":
    unittest.main()
