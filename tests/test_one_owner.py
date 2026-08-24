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
                       markers, source_files)

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


def check_tree(adrs=("0037",), adr_status="accepted", **modules):
    """check() against a fixture tree of literal modules — never the live
    tree, so no case here decays as the tree is cleaned. A `|` in a name
    is a path separator. `adrs` are the decision records the tree holds,
    so a marker's citation has something to resolve against."""
    with tempfile.TemporaryDirectory() as tmp:
        fixture = FixtureTree(tmp)
        for number in adrs:
            fixture.write(f"docs/adr/{number}-a-decision.md",
                          f"# A decision\n\n- Status: {adr_status}\n")
        listing = []
        for name, source in modules.items():
            rel = f"{name.replace('|', '/')}.py"
            fixture.write(rel, source)
            listing.append(rel)
        return check(fixture.root, run=fake_git("\n".join(listing) + "\n"))


def carve(counterpart, adr="ADR-0037",
          reason="ADR-0037 sanctions the alias so problem strings read"
                 " unchanged"):
    """One well-formed carve-out marker line."""
    return f"# one-owner: {counterpart} ({adr}) — {reason}"


def runner_git(*counterparts):
    """A module whose git_runner carries the given carve-out markers."""
    return "".join(f"{carve(c)}\n" for c in counterparts) + \
        "git_runner = runner('git')\n"


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


# The miss-3 shape from defect.md's evidence table, frozen as this pass's
# acceptance fixture: cli.label_names (622e2bf, 2026-08-10, #247) and the
# labels walk that became plane_drift.issue_lifecycle (f38fbdd,
# 2026-08-10, #204). Two genuinely different walks — one drops a nameless
# label at extraction, the other admits None and filters a line later —
# over the same two keys.
#
# Closed in the tree by f79410e (#334): issue_lifecycle now reads through
# the seam. These strings do NOT move with it. They are the historical
# shape the pass must keep finding, and rebasing them onto folded code
# would delete the evidence that it can.
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


# The real three-line comment block above budget_guard.py:111, the shape
# the design's first annotation actually has to fit into.
GIT_RUNNER_BLOCK = """# The real git CLI (cli.runner): a failed or missing git raises
# GIT_FAILURES, and push_wip turns that into a bg: problem string rather
# than a traceback.
git_runner = runner("git")
"""
MARK = "# one-owner: dashboard.git_runner (ADR-0037) — callers alias to"\
       " their own names"
GRAMMAR = "# one-owner: <module>.<name> (ADR-####) — <reason>"


class TestMarkers(unittest.TestCase):
    """The carve-out, read where the definition is. It travels with the
    code, dies with the code, and is read by whoever reviews the diff that
    would otherwise add a second owner — which is the half of ADR-0039's
    roster that stayed correct."""

    def test_a_marker_directly_above_a_definition_is_read(self):
        found, problems = markers(
            "budget_guard.py", f"{MARK}\ngit_runner = runner('git')\n")
        self.assertEqual(problems, [])
        self.assertEqual(found, [Marker("budget_guard.py", 1, "git_runner",
                                        "dashboard.git_runner", "ADR-0037",
                                        "callers alias to their own names")])

    def test_a_marker_mid_block_among_ordinary_comments_is_read(self):
        source = GIT_RUNNER_BLOCK.replace(
            "# GIT_FAILURES", f"{MARK}\n# GIT_FAILURES")
        found, problems = markers("budget_guard.py", source)
        self.assertEqual(problems, [])
        self.assertEqual([(m.lineno, m.owner, m.counterpart) for m in found],
                         [(2, "git_runner", "dashboard.git_runner")])

    def test_a_blank_line_ends_the_block_so_the_marker_attaches_to_nothing(self):
        """Locality is the whole mechanism: a marker one blank line away
        is not above the definition, it is merely near it."""
        found, problems = markers(
            "budget_guard.py", f"{MARK}\n\ngit_runner = runner('git')\n")
        self.assertEqual(found, [])
        self.assertEqual(problems,
                         ["one-owner: budget_guard.py:1 is a one-owner marker"
                          " above no definition"])

    def test_a_marker_above_something_that_states_no_fact_attaches_to_nothing(self):
        found, problems = markers("a.py", f"{MARK}\nimport os\n")
        self.assertEqual(found, [])
        self.assertEqual(problems,
                         ["one-owner: a.py:1 is a one-owner marker above no"
                          " definition"])

    def test_an_unreadable_marker_is_a_problem_never_a_permission(self):
        for text in ("# one-owner: dashboard.git_runner — no citation",
                     "# one-owner: (ADR-0037) — no counterpart",
                     "# one-owner: dashboard.git_runner (0037) — bad token",
                     "# one-owner: dashboard.git_runner (ADR-0037) no dash"):
            with self.subTest(text=text):
                found, problems = markers(
                    "a.py", f"{text}\ngit_runner = runner('git')\n")
                self.assertEqual(found, [])
                self.assertEqual(
                    problems,
                    [f"one-owner: a.py:1 is not a readable one-owner marker"
                     f" (expected `{GRAMMAR}`)"])

    def test_a_bare_marker_waives_nothing(self):
        """gates.NO_WO_DECLARATION already applies this rule to the other
        place a change may excuse itself: the declaration owes a reason."""
        for text in ("# one-owner: dashboard.git_runner (ADR-0037) —",
                     "# one-owner: dashboard.git_runner (ADR-0037) —   "):
            with self.subTest(text=text):
                found, problems = markers(
                    "a.py", f"{text}\ngit_runner = runner('git')\n")
                self.assertEqual(found, [])
                self.assertEqual(
                    problems,
                    ["one-owner: a.py:1 marks git_runner deliberate with no"
                     " reason — a bare marker waives nothing"])

    def test_a_hash_inside_a_string_or_docstring_is_not_a_comment(self):
        """one_owner.py's own self-reference hazard, at its interface: the
        tool is in its own universe and its grammar is a comment pattern,
        so the grammar is documented in its DOCSTRING. A line scan would
        read that documentation as a live marker."""
        source = (f'"""Docs.\n\n    {MARK}\n"""\n'
                  f'GRAMMAR = "{MARK}"\n')
        self.assertEqual(markers("one_owner.py", source), ([], []))

    def test_a_marker_problem_silences_nothing(self):
        """In every failure case the group still reports: a marker that
        cannot be read is not a permission."""
        for text in (f"{MARK.split(' —')[0]} — ", "# one-owner: nonsense"):
            with self.subTest(text=text):
                found = check_tree(
                    budget_guard=f"{text}\ngit_runner = runner('git')\n",
                    dashboard="git_runner = runner('git')\n")
                self.assertIn(
                    "one-owner: budget_guard.py:2 git_runner and"
                    " dashboard.py:1 git_runner state the same value — one"
                    " fact, one owner", found)
                self.assertEqual(len(found), 2, found)


class TestCoverage(unittest.TestCase):
    """The design question's answer, exercised. Silence is a property of
    the whole GROUP, never of one marker — which is what makes ADR-0039's
    failure (a fourth owner arriving nineteen days later and nothing
    re-reading the roster) impossible rather than merely discouraged."""

    def test_a_fully_covered_group_is_silent(self):
        self.assertEqual(
            check_tree(budget_guard=runner_git("dashboard.git_runner"),
                       dashboard=runner_git("budget_guard.git_runner")), [])

    def test_a_third_unmarked_owner_makes_the_group_speak_again(self):
        """A NEW OWNER CANNOT ADMIT ITSELF. Admitting it means editing an
        existing owner's file, where a reviewer is already looking. This
        is the ADR-0039 failure, made impossible."""
        self.assertEqual(
            check_tree(budget_guard=runner_git("dashboard.git_runner"),
                       dashboard=runner_git("budget_guard.git_runner"),
                       one_owner="git_runner = runner('git')\n"),
            ["one-owner: one_owner.py:1 git_runner joins a recorded"
             " deliberate group without a marker — a new owner cannot admit"
             " itself"])

    def test_a_member_no_other_member_names_is_not_vouched_for(self):
        """Self-admission through the back door: a newcomer that writes
        its own marker still needs an existing owner to name it."""
        self.assertEqual(
            check_tree(budget_guard=runner_git("dashboard.git_runner"),
                       dashboard=runner_git("budget_guard.git_runner"),
                       one_owner=runner_git("budget_guard.git_runner")),
            ["one-owner: one_owner.py:2 git_runner carries a marker but no"
             " other owner names it — an existing owner must vouch for a new"
             " one"])

    def test_a_marker_pays_rent_or_it_is_a_finding(self):
        """Over-coverage. A carve-out whose counterpart was deleted,
        renamed or folded matches nothing — the list cannot rot quietly,
        because dead entries are findings."""
        self.assertEqual(
            check_tree(budget_guard=runner_git("dashboard.git_runner"),
                       dashboard="git_runner = runner('gh')\n"),
            ["one-owner: budget_guard.py:1 git_runner is marked deliberate"
             " against dashboard.git_runner, but nothing duplicates it —"
             " remove the marker"])

    def test_a_counterpart_this_repo_does_not_define(self):
        self.assertEqual(
            check_tree(budget_guard=runner_git("nowhere.gone")),
            ["one-owner: budget_guard.py:1 names nowhere.gone, which is not"
             " defined in this repo"])

    def test_a_citation_must_resolve_to_a_file_in_docs_adr(self):
        self.assertEqual(
            check_tree(
                budget_guard="".join([
                    carve("dashboard.git_runner", adr="ADR-9999"), "\n",
                    "git_runner = runner('git')\n"]).replace("\n\n", "\n"),
                dashboard=runner_git("budget_guard.git_runner")),
            ["one-owner: budget_guard.py:1 cites ADR-9999, which is not in"
             " docs/adr/"])

    def test_status_liveness_is_deliberately_not_checked(self):
        """The status grammar's owner is gates.ADR_STATUS, and importing a
        detector module from a tool is the coupling ADR-0058 removed.
        Folding ADR_STATUS into knowledge_plane is its own decision, not a
        ride-along — so a superseded citation resolves, and the deferral is
        visible in the suite rather than only in prose."""
        self.assertEqual(
            check_tree(adr_status="superseded by ADR-0060",
                       budget_guard=runner_git("dashboard.git_runner"),
                       dashboard=runner_git("budget_guard.git_runner")), [])

    def test_a_marker_that_cannot_be_read_never_buys_silence(self):
        """The whole group speaks, because the unreadable marker covered
        nothing."""
        found = check_tree(
            budget_guard=f"# one-owner: nonsense\n{runner_git()}",
            dashboard=runner_git("budget_guard.git_runner"))
        self.assertIn(
            "one-owner: budget_guard.py:2 git_runner joins a recorded"
            " deliberate group without a marker — a new owner cannot admit"
            " itself", found)
        self.assertIn(
            "one-owner: budget_guard.py:1 is not a readable one-owner marker"
            f" (expected `{GRAMMAR}`)", found)

    def test_check_still_raises_on_nothing(self):
        self.assertIsInstance(
            check_tree(a=f"# one-owner: x.y (ADR-0037) —\n{runner_git()}",
                       b=runner_git("nowhere.gone")), list)


class TestHistoricalInstances(unittest.TestCase):
    """defect.md's evidence table, reproduced as FIXTURES rather than read
    off the live tree — two of the three instances a manual deepening
    review read past at fbfa3c3 (2026-08-17), measured hit rate 4 of 7.

    Fixture, not invention: each module below cites the commit and PR that
    created the shape it reproduces, so a later reader can tell one from
    the other. They are fixtures precisely so the suite does not decay as
    the tree is cleaned — two of the three shapes are already gone from
    HEAD, and the third is seeded for folding at docs/backlog.md:46.
    """

    # Miss 1 — gates.MERGED_ROW (208ffdb, 2026-07-11, #130) and
    # knowledge_plane.DONE_ROW (4333370, 2026-08-10, #221): byte-identical
    # in pattern AND flags, nineteen days after ADR-0039 fixed the roster
    # at three owners. Closed by ADR-0058 at 7988962 (#312).
    MISS_1_GATES = ('# gates.py:106 at fbfa3c3 — created 208ffdb (#130)\n'
                    f'MERGED_ROW = {CHECKED_ROW}\n')
    MISS_1_KNOWLEDGE_PLANE = (
        '# knowledge_plane.py:94 at fbfa3c3 — created 4333370 (#221)\n'
        f'DONE_ROW = {CHECKED_ROW}\n')

    # Miss 3 — cli.label_names (622e2bf, 2026-08-10, #247) and
    # sweeps.issue_lifecycle (f38fbdd, 2026-08-10, #204), created the same
    # day. ADR-0060 moved the copy into plane_drift.issue_lifecycle
    # without changing a byte, which is why it was the one-owner run's
    # acceptance fixture rather than its cleanup target. Closed by f79410e
    # (#334), the run this pass's own standing output prompted.
    MISS_3_CLI = ('# cli.py:349 at fbfa3c3 — created 622e2bf (#247)\n'
                  + LABEL_NAMES)
    MISS_3_SWEEPS = ('# sweeps.py:220 at fbfa3c3 — created f38fbdd (#204)\n'
                     + ISSUE_LIFECYCLE)

    def test_miss_1_the_checked_row_grammar_with_two_owners(self):
        self.assertEqual(
            check_tree(gates=self.MISS_1_GATES,
                       knowledge_plane=self.MISS_1_KNOWLEDGE_PLANE),
            ["one-owner: gates.py:2 MERGED_ROW and knowledge_plane.py:2"
             " DONE_ROW state the same value — one fact, one owner"])

    def test_miss_3_the_labels_walk_with_two_strictnesses(self):
        """The two walks genuinely differ — one drops a nameless label at
        extraction, the other admits None and filters a line later — and
        share no identical text. Same rule, two strictnesses, one of them
        undocumented; the shape they DO share is the two keys."""
        self.assertEqual(
            check_tree(cli=self.MISS_3_CLI, sweeps=self.MISS_3_SWEEPS),
            ["one-owner: cli.py:2 label_names and sweeps.py:2"
             " issue_lifecycle read the same payload keys (labels, name)"
             " — one fact, one owner"])

    def test_both_misses_in_one_tree_are_two_findings(self):
        """The tree the review actually read: both shapes present at once,
        each its own finding, sorted."""
        self.assertEqual(
            check_tree(cli=self.MISS_3_CLI, gates=self.MISS_1_GATES,
                       knowledge_plane=self.MISS_1_KNOWLEDGE_PLANE,
                       sweeps=self.MISS_3_SWEEPS),
            ["one-owner: cli.py:2 label_names and sweeps.py:2"
             " issue_lifecycle read the same payload keys (labels, name)"
             " — one fact, one owner",
             "one-owner: gates.py:2 MERGED_ROW and knowledge_plane.py:2"
             " DONE_ROW state the same value — one fact, one owner"])


class TestKnownMiss(unittest.TestCase):
    """The third historical instance, pinned as a KNOWN MISS.

    In the shape of tests/test_knowledge_plane.py:99-107: an absence
    asserted on purpose, so the limit lives in the suite rather than in
    someone's memory. The fixtures below are the two functions verbatim
    at fbfa3c3 — 7 statements over 69 lines against 3 over 21 — which is
    also what keeps this pin from passing vacuously: a fixture that
    failed to parse would put a problem in the list and fail the
    assertion.
    """

    RECONCILE_DRIFT = r'''def reconcile_drift(rows, issues):
    """PURE: (breakdown rows, the live issue listing) -> (drift lines,
    problems).

    Every line names a breakdown path and an issue NUMBER, never a work
    order id: the row is identified by where it lives, which is also where
    a human goes to fix it. The knowledge plane is authoritative in every
    comparison — a line says what the dispatch plane must be brought to,
    never the reverse (ADR-0032).

    `rows` is (display path, lines) per breakdown, so the caller owns how
    paths are spelled and this stays a pure function.
    """
    index, problems = {}, []
    for position, issue in enumerate(issues):
        if not isinstance(issue, dict) or not isinstance(
                issue.get("number"), int):
            problems.append(f"sweeps: issue listing entry {position} has no"
                            " usable number")
            continue
        index[issue["number"]] = issue
    drift, mirrored = [], {}
    for path, lines in rows:
        for line in lines:
            number = row_tracker_issue(line)
            if number is None:
                continue
            mirrored.setdefault(number, []).append(path)
            issue = index.get(number)
            if issue is None:
                drift.append(f"{path}: a row mirrors #{number}, which is not"
                             " in the issue listing")
                continue
            labels = issue_lifecycle(issue)
            merged = "wo:merged" in labels
            state = str(issue.get("state") or "").lower()
            if gates.MERGED_ROW.match(line):
                if not merged:
                    drift.append(f"{path}: a checked row mirrors #{number},"
                                 f" which carries {_describe(labels)} — the"
                                 " row says merged")
                elif state == "open":
                    drift.append(f"{path}: a checked row mirrors #{number},"
                                 " which is labelled wo:merged but still open")
            elif merged:
                drift.append(f"{path}: an unchecked row mirrors #{number},"
                             " which is labelled wo:merged — the issue is"
                             " ahead of the row")
            elif state == "closed":
                drift.append(f"{path}: an unchecked row mirrors #{number},"
                             f" which is closed carrying {_describe(labels)}"
                             " — the row says the work is outstanding")
    for number, paths in sorted(mirrored.items()):
        if len(paths) > 1:
            drift.append(f"#{number} is mirrored by {len(paths)} rows"
                         f" ({', '.join(sorted(set(paths)))}) — an issue"
                         " mirrors one work order")
    for number, issue in sorted(index.items()):
        labels = issue_lifecycle(issue)
        if not labels:
            continue
        if len(labels) > 1:
            drift.append(f"#{number} carries {len(labels)} lifecycle labels"
                         f" at once ({', '.join(labels)}) — the state"
                         " machine allows one")
        if number not in mirrored:
            drift.append(f"#{number} carries {_describe(labels)} but no"
                         " breakdown row mirrors it — the dispatch plane is"
                         " ahead of the knowledge plane")
'''
    DASHBOARD_DRIFT = r'''def _drift(root, states):
    """Cross-plane disagreement (ADR-0032: the row, never the issue, is
    authoritative — so the mirror must follow it): a row unchecked while
    its mirror is closed (the class issue #123 exposed), or checked
    while its mirror is still open. `states` maps issue number to its
    listed state; a mirror outside the listing says nothing — only
    definite disagreement is a finding."""
    findings = []
    for _, lines in breakdown_files(root):
        for line in lines:
            number = row_tracker_issue(line)
            state = states.get(number)
            if state is None:
                continue
            wo = row_work_order(line)
            if row_done(line) and state == "OPEN":
                findings.append(f"drift: {wo} row is checked but its"
                                f" mirror #{number} is still open")
            elif not row_done(line) and state == "CLOSED":
                findings.append(f"drift: {wo} row is unchecked but its"
                                f" mirror #{number} is closed")
'''

    def test_a_re_implementation_of_a_rule_is_not_found(self):
        # THIS IS THE AMENDED SUCCESS CRITERION. defect.md asked for a
        # test that would have caught each of the THREE historical
        # instances; the operator accepted the substitution on 2026-08-23,
        # and architecture.md records it under *Measured against the
        # tree*: the suite catches misses 1 and 3 and PINS miss 2 as a
        # known miss with the reason recorded. Verify scores against the
        # amended form and must say it was amended and why.
        #
        # Why it is a miss: no cheap syntactic rule reaches a
        # re-implementation. These two functions share no identical text
        # and one side carries a strictly narrower rule (three of the
        # eight classes, and a different absence policy). Two candidate
        # rules were built and lost on measured evidence —
        # whole-function-body identity yields ZERO groups at HEAD and at
        # fbfa3c3, and a seam-call fingerprint fires hardest on six
        # main()s that all call repo_root and report, while still missing
        # this pair. See architecture.md, *Decisions & alternatives*.
        # Closing it needs semantic comparison, which is exactly the
        # over-cleverness defect.md's hazard 2 names as a way this dies.
        self.assertEqual(
            check_tree(sweeps=self.RECONCILE_DRIFT,
                       dashboard=self.DASHBOARD_DRIFT), [],
            "A finding here is WELCOME NEWS, not a broken test: it means"
            " the rules got strong enough to reach a re-implementation."
            " Do not delete this case to make it pass — move it to"
            " TestHistoricalInstances and pin the string it now emits.")


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
