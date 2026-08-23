"""one_owner.py — the pre-pass that asks whether a fact is stated twice.

The tool this repo's "one fact, one owner" bar never had
(docs/fixes/one-fact-one-owner/). Every case here runs against LITERAL
fact sites or FIXTURE TREES, never against the live tree, so the suite
does not decay as the tree is cleaned — that is the point of the
historical fixtures in TestHistoricalInstances, which reproduce shapes
the tree no longer holds.
"""
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import one_owner
from one_owner import (FactSite, Group, Marker, check, fact_sites, groups,
                       source_files)

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling helper import
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
from fixture_tree import FixtureTree  # noqa: E402


def fake_git(listing, calls=None):
    """A fake cli.runner("git") answering one `ls-files` listing, so no
    case here shells out. `listing` is the newline-joined paths git
    tracks; `calls` collects the argument lists it was asked for."""
    def run(args):
        if calls is not None:
            calls.append(list(args))
        return subprocess.CompletedProcess(args, 0, stdout=listing,
                                           stderr="")
    return run


def failing_git(err):
    def run(args):
        raise err
    return run


def check_tree(**modules):
    """check() against a fixture tree of literal modules — never the live
    tree, so no case here decays as the tree is cleaned. A `|` in a name
    is a path separator."""
    with tempfile.TemporaryDirectory() as tmp:
        fixture = FixtureTree(tmp)
        listing = []
        for name, source in modules.items():
            rel = f"{name.replace('|', '/')}.py"
            fixture.write(rel, source)
            listing.append(rel)
        return check(fixture.root, run=fake_git("\n".join(listing) + "\n"))


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


class TestSourceFiles(unittest.TestCase):
    """The universe. It comes from `git ls-files` and from nothing else —
    a filesystem walk is WRONG here, and wrong in the one way that would
    discredit the tool on its first run."""

    ARGS = ["ls-files", "--", "*.py"]

    def tree(self, tmp, **files):
        fixture = FixtureTree(tmp)
        for rel, text in files.items():
            fixture.write(rel.replace("|", "/"), text)
        return fixture.root

    def test_the_universe_is_what_git_tracks_not_what_the_disk_holds(self):
        """defect.md's Notes: at HEAD an rglob finds 248 Python files
        where git tracks 96, and 152 of the difference are stale
        `.claude/worktrees/agent-*` checkouts holding MERGED_ROW
        definitions the tracked tree deleted at 7988962. They are hidden
        only by `.git/info/exclude:11`, which is LOCAL and UNCOMMITTED, so
        no committed file can be relied on to hide them. A walking tool
        would report a duplicate that does not exist, on its first run,
        on the very symbol the class is famous for."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self.tree(
                tmp, **{"gates.py": "A = 'x'\n",
                        ".claude|worktrees|agent-1|gates.py": "A = 'x'\n"})
            calls = []
            files, problems = source_files(
                root, run=fake_git("gates.py\n", calls))
        self.assertEqual(problems, [])
        self.assertEqual([path for path, _ in files], ["gates.py"])
        self.assertEqual(calls, [["-C", str(root), *self.ARGS]])

    def test_the_payload_mirror_and_the_suite_are_outside_the_universe(self):
        """factory/templates/tools/factory/ is a deliberate byte-identical
        mirror whose equality detector E already owns — reading it would
        report seventeen tools as duplicates of themselves — and
        factory/evals/fixtures/ holds intentionally broken repos. A test
        asserting an exact string IS that string's pin, not a second
        owner of it."""
        listing = ("cli.py\n"
                   "factory/templates/tools/factory/cli.py\n"
                   "factory/evals/fixtures/x/repo/src/errors.py\n"
                   "tests/test_cli.py\n")
        with tempfile.TemporaryDirectory() as tmp:
            root = self.tree(
                tmp, **{"cli.py": "A = 'x'\n",
                        "factory|templates|tools|factory|cli.py": "A = 'x'\n",
                        "factory|evals|fixtures|x|repo|src|errors.py": "A = 1\n",
                        "tests|test_cli.py": "A = 'x'\n"})
            files, problems = source_files(root, run=fake_git(listing))
        self.assertEqual(problems, [])
        self.assertEqual([path for path, _ in files], ["cli.py"])

    def test_files_come_back_sorted_by_path_with_their_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.tree(tmp, **{"b.py": "B = 'b'\n", "a.py": "A = 'a'\n"})
            files, problems = source_files(root, run=fake_git("b.py\na.py\n"))
        self.assertEqual(problems, [])
        self.assertEqual(files, [("a.py", "A = 'a'\n"), ("b.py", "B = 'b'\n")])

    def test_a_failed_or_missing_git_is_a_problem_not_a_traceback(self):
        err = subprocess.CalledProcessError(
            128, ["git"], stderr="fatal: not a git repository\n")
        with tempfile.TemporaryDirectory() as tmp:
            files, problems = source_files(tmp, run=failing_git(err))
        self.assertEqual(files, [])
        self.assertEqual(problems,
                         ["one-owner: git ls-files failed: fatal: not a git"
                          " repository"])

    def test_a_missing_git_binary_reports_the_os_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            files, problems = source_files(
                tmp, run=failing_git(FileNotFoundError("no git here")))
        self.assertEqual(files, [])
        self.assertEqual(problems,
                         ["one-owner: git ls-files failed: no git here"])

    def test_a_file_that_cannot_be_read_is_reported_and_skipped(self):
        """One unreadable file must not take the run with it — the rest
        still contributes."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self.tree(tmp, **{"good.py": "A = 'x'\n"})
            (root / "bad.py").write_bytes(b"A = '\xff\xfe'\n")
            files, problems = source_files(
                root, run=fake_git("bad.py\ngood.py\ngone.py\n"))
        self.assertEqual([path for path, _ in files], ["good.py"])
        self.assertEqual(len(problems), 2, problems)
        self.assertTrue(problems[0].startswith(
            "one-owner: bad.py cannot be read: "), problems[0])
        self.assertTrue(problems[1].startswith(
            "one-owner: gone.py cannot be read: "), problems[1])

    def test_an_empty_universe_is_never_silently_clean(self):
        """A broken environment must never read as "no duplicates"."""
        for listing in ("", "\n", "tests/test_cli.py\nfactory/x.py\n"):
            with self.subTest(listing=listing):
                with tempfile.TemporaryDirectory() as tmp:
                    self.tree(tmp, **{"tests|test_cli.py": "A = 1\n",
                                      "factory|x.py": "A = 1\n"})
                    files, problems = source_files(tmp,
                                                   run=fake_git(listing))
                self.assertEqual(files, [])
                self.assertEqual(problems,
                                 ["one-owner: no Python files to read — an"
                                  " empty universe is never a clean one"])


class TestCheck(unittest.TestCase):
    """The whole answer: a sorted list of one-owner:-prefixed problem
    strings. These are the bytes a person reads, so they are pinned
    exactly — against fixture trees, never the live tree."""

    def test_an_uncovered_same_value_group_names_both_owners(self):
        self.assertEqual(
            check_tree(gates=f"MERGED_ROW = {CHECKED_ROW}\n",
                       knowledge_plane=f"DONE_ROW = {CHECKED_ROW}\n"),
            ["one-owner: gates.py:1 MERGED_ROW and knowledge_plane.py:1"
             " DONE_ROW state the same value — one fact, one owner"])

    def test_an_uncovered_same_keys_group_names_the_keys(self):
        self.assertEqual(
            check_tree(cli=LABEL_NAMES, plane_drift=ISSUE_LIFECYCLE),
            ["one-owner: cli.py:1 label_names and plane_drift.py:1"
             " issue_lifecycle read the same payload keys (labels, name)"
             " — one fact, one owner"])

    def test_every_member_is_listed_sorted_by_path_then_line(self):
        self.assertEqual(
            check_tree(assembler="\nREADY_LABEL = 'wo:ready-for-agent'\n",
                       validator="READY_LABEL = 'wo:ready-for-agent'\n",
                       work_queue="\n\nREADY_LABEL = 'wo:ready-for-agent'\n"),
            ["one-owner: assembler.py:2 READY_LABEL, validator.py:1"
             " READY_LABEL and work_queue.py:3 READY_LABEL state the same"
             " value — one fact, one owner"])

    def test_a_tree_with_one_owner_per_fact_reports_nothing(self):
        self.assertEqual(check_tree(a="A = 'x'\n", b="B = 'y'\n"), [])

    def test_the_same_tree_yields_byte_identical_output_twice(self):
        """Determinism is part of the contract — it is what lets the suite
        assert exact strings at all."""
        modules = {"gates": f"MERGED_ROW = {CHECKED_ROW}\n",
                   "knowledge_plane": f"DONE_ROW = {CHECKED_ROW}\n",
                   "cli": LABEL_NAMES, "plane_drift": ISSUE_LIFECYCLE}
        self.assertEqual(check_tree(**modules), check_tree(**modules))

    def test_reading_and_parsing_problems_reach_the_caller(self):
        found = check_tree(broken="def (:\n", gates="A = 'x'\n",
                           knowledge_plane="B = 'x'\n")
        self.assertEqual(len(found), 2, found)
        self.assertTrue(found[0].startswith(
            "one-owner: broken.py cannot be parsed: "), found[0])
        self.assertEqual(found[1],
                         "one-owner: gates.py:1 A and knowledge_plane.py:1 B"
                         " state the same value — one fact, one owner")

    def test_a_broken_environment_never_reads_as_no_duplicates(self):
        err = subprocess.CalledProcessError(128, ["git"], stderr="fatal: x\n")
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(check(tmp, run=failing_git(err)),
                             ["one-owner: git ls-files failed: fatal: x"])

    def test_check_raises_on_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsInstance(check(tmp, run=fake_git("")), list)


class TestMain(cli_contract.CliContract, unittest.TestCase):
    """The command. Exiting nonzero on a finding is correct AND is wired
    into no gate: the tool is deliberately outside `make check`, so a
    finding never colours main red."""

    usage_fragment = "python3 one_owner.py"

    def run_cli(self, argv):
        return cli_contract.capture(one_owner.main, argv)

    def test_a_finding_prints_through_the_report_epilogue(self):
        with unittest.mock.patch.object(
                one_owner, "check",
                return_value=["one-owner: a.py:1 A and b.py:1 B state the"
                              " same value — one fact, one owner"]):
            code, out = self.run_cli([])
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines()[-1], "one-owner: 1 problem(s)")

    def test_a_clean_tree_exits_zero_with_the_exact_summary_line(self):
        with unittest.mock.patch.object(one_owner, "check", return_value=[]):
            code, out = self.run_cli([])
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[-1], "one-owner: 0 problem(s)")


class TestFrontDoor(unittest.TestCase):
    def test_the_tool_has_a_verb_and_a_docstring_summary(self):
        """factory.index() reads each module's docstring first line, and
        test_factory_cli derives the verb table from a scan for the
        __main__ guard — so a guard with no verb breaks the build."""
        import factory
        self.assertEqual(factory.VERBS["one-owner"], ("one_owner", "argv"))
        self.assertTrue((one_owner.__doc__ or "").strip().splitlines()[0])


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
