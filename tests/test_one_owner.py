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


# The miss-3 shape from defect.md's evidence table, still live at HEAD as
# this run's acceptance fixture: cli.label_names (622e2bf, 2026-08-10,
# #247) and the labels walk that became plane_drift.issue_lifecycle
# (f38fbdd, 2026-08-10, #204). Two genuinely different walks — one drops
# a nameless label at extraction, the other admits None and filters a
# line later — over the same two keys.
LABEL_NAMES = """def label_names(payload):
    labels = payload.get("labels") if isinstance(payload, dict) else payload
    if not isinstance(labels, list):
        return []
    return [entry["name"] for entry in labels
            if isinstance(entry, dict)
            and isinstance(entry.get("name"), str) and entry["name"]]
"""
ISSUE_LIFECYCLE = """def issue_lifecycle(issue):
    labels = issue.get("labels")
    names = [entry.get("name") for entry in labels
             if isinstance(entry, dict)] if isinstance(labels, list) else []
    return sorted(name for name in names
                  if isinstance(name, str) and name.startswith("wo:"))
"""


class TestSameKeys(unittest.TestCase):
    """`same-keys`: a function definition, identified by the named
    external shape it reads. The claim is that two functions read the
    same payload keys, which in this repo is what a seam owns — so it
    finds a retyped seam even when the two bodies share no text."""

    def test_two_walks_over_the_same_two_keys_are_two_owners(self):
        found, problems = sites_of(cli=LABEL_NAMES,
                                   plane_drift=ISSUE_LIFECYCLE)
        self.assertEqual(problems, [])
        self.assertEqual(named(found),
                         [("labels, name", ["cli.label_names",
                                            "plane_drift.issue_lifecycle"])])

    def test_the_floor_is_two_keys_because_the_fixture_has_exactly_two(self):
        """A floor of three loses the acceptance fixture. Asserted at the
        boundary rather than assumed: one key is not a shape."""
        one, problems = sites_of(a='def f(p):\n    return p.get("labels")\n')
        self.assertEqual((one, problems), ([], []))
        two, problems = sites_of(
            a='def f(p):\n    return p.get("labels"), p.get("name")\n')
        self.assertEqual(problems, [])
        self.assertEqual([(s.kind, s.name, s.identity) for s in two],
                         [("same-keys", "f", "labels, name")])

    def test_get_and_subscript_are_the_same_read(self):
        """The shape is what is read, not how — a seam retyped with
        subscripts is the same second owner."""
        found, problems = sites_of(
            a='def f(p):\n    return p.get("labels"), p.get("name")\n',
            b='def g(p):\n    return p["labels"], p["name"]\n')
        self.assertEqual(problems, [])
        self.assertEqual(named(found), [("labels, name", ["a.f", "b.g"])])

    def test_key_sets_that_merely_overlap_are_not_one_fact(self):
        """Identity is the whole set. Two functions sharing one key of
        three have not stated the same shape, and treating them as one
        owner is how a checker starts crying wolf."""
        found, problems = sites_of(
            a='def f(p):\n    return p["labels"], p["name"]\n',
            b='def g(p):\n    return p["name"], p["state"]\n')
        self.assertEqual(problems, [])
        self.assertEqual(groups(found), [])

    def test_a_nested_function_is_reached(self):
        """The rule is "a function definition anywhere in the module" —
        a retyped seam hidden one level down is still a second owner."""
        found, problems = sites_of(a=(
            "def outer(payload):\n"
            "    def inner(entry):\n"
            '        return entry.get("labels"), entry.get("name")\n'
            "    return inner\n"))
        self.assertEqual(problems, [])
        self.assertIn(("same-keys", "inner", "labels, name"),
                      [(s.kind, s.name, s.identity) for s in found])

    def test_both_kinds_come_back_from_one_module_in_source_order(self):
        """The two identities together cover both mechanical forms
        defect.md's Target state names, and one module can state both."""
        found, problems = sites_of(a=(
            "LABEL = 'wo:ready-for-agent'\n"
            "\n"
            "\n"
            'def f(p):\n    return p["labels"], p["name"]\n'))
        self.assertEqual(problems, [])
        self.assertEqual([(s.kind, s.lineno, s.name) for s in found],
                         [("same-value", 1, "LABEL"), ("same-keys", 4, "f")])


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
