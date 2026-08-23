"""one_owner.py — the pre-pass that asks whether a fact is stated twice.

The tool this repo's "one fact, one owner" bar never had
(docs/fixes/one-fact-one-owner/). Every case here runs against LITERAL
fact sites or FIXTURE TREES, never against the live tree, so the suite
does not decay as the tree is cleaned — that is the point of the
historical fixtures in TestHistoricalInstances, which reproduce shapes
the tree no longer holds.
"""
import unittest

from one_owner import FactSite, Group, Marker, groups


def site(kind, path, lineno, name, identity):
    return FactSite(kind, path, lineno, name, identity)


def value(path, lineno, name, identity):
    return site("same-value", path, lineno, name, identity)


def keys(path, lineno, name, identity):
    return site("same-keys", path, lineno, name, identity)


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
