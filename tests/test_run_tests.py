"""run_tests.py — the parallel test runner (faster-sdlc #903).

Every case drives main() through a fake spawn port: what each module's
`python3 -m unittest tests.<module>` child would print and exit with is
declared per case, so no case here forks a Python. The one live pin is
discovery against the real tests/ directory, which is cheap (a glob).
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import run_tests

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling helper import
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]

PASSING = "...\n" + "-" * 70 + "\nRan 3 tests in 0.010s\n\nOK\n"
FAILING = ("F\n" + "=" * 70 + "\nFAIL: test_x (tests.test_b.T.test_x)\n"
           + "-" * 70 + "\nRan 1 test in 0.002s\n\nFAILED (failures=1)\n")


class FakeSpawn:
    """The runner's subprocess port: `spawn(cmd, cwd) -> (code, output)`.
    `answers` maps a module name to the (exit code, combined output) its
    child prints; an unlisted module passed with PASSING's three tests.
    Every call lands in `calls` as (cmd, cwd)."""

    def __init__(self, answers=None):
        self.answers = answers or {}
        self.calls = []

    def __call__(self, cmd, cwd):
        self.calls.append((list(cmd), cwd))
        return self.answers.get(cmd[-1], (0, PASSING))


def tree(root, *names):
    """A repo root whose tests/ holds the named files (plus a fixtures
    directory and a helper, which discovery must skip)."""
    tests = root / "tests"
    (tests / "fixtures" / "orientation").mkdir(parents=True)
    (tests / "fixtures" / "orientation" / "test_not_a_module.py").write_text(
        "", encoding="utf-8")
    (tests / "helper.py").write_text("", encoding="utf-8")
    for name in names:
        (tests / name).write_text("", encoding="utf-8")
    return root


class TreeCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tree(Path(tmp.name), "test_b.py", "test_a.py",
                         "test_c_long.py")
        self.spawn = FakeSpawn()

    def run_cli(self, argv, spawn=None, cpu_count=lambda: 4):
        return cli_contract.capture(
            run_tests.main, argv, spawn=spawn or self.spawn, root=self.root,
            cpu_count=cpu_count)


class TestDiscover(TreeCase):
    def test_every_test_module_directly_under_tests_in_module_form(self):
        self.assertEqual(run_tests.discover(self.root),
                         ["tests.test_a", "tests.test_b", "tests.test_c_long"])

    def test_the_live_tree_discovers_this_suite_and_only_real_files(self):
        modules = run_tests.discover(REPO_ROOT)
        self.assertIn("tests.test_run_tests", modules)
        self.assertIn("tests.test_conductor_merge", modules)
        for module in modules:
            self.assertTrue(
                (REPO_ROOT / module.replace(".", "/")).with_suffix(".py")
                .is_file(), module)


class TestSchedule(unittest.TestCase):
    MODULES = ["tests.test_a", "tests.test_b", "tests.test_c"]

    def test_longest_first_from_the_timings(self):
        self.assertEqual(
            run_tests.schedule(self.MODULES, {"tests.test_c": 20.5,
                                              "tests.test_a": 1.0,
                                              "tests.test_b": 7.4}),
            ["tests.test_c", "tests.test_b", "tests.test_a"])

    def test_no_timings_means_alphabetical(self):
        self.assertEqual(run_tests.schedule(list(reversed(self.MODULES)), {}),
                         self.MODULES)

    def test_an_untimed_module_sorts_after_the_timed_ones_alphabetically(
            self):
        self.assertEqual(
            run_tests.schedule(["tests.test_new", "tests.test_a",
                                "tests.test_b"], {"tests.test_a": 2.0}),
            ["tests.test_a", "tests.test_b", "tests.test_new"])


class TestLoadTimings(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "timings.json"

    def test_a_committed_file_is_read(self):
        self.path.write_text(json.dumps({"tests.test_a": 1.5}),
                             encoding="utf-8")
        self.assertEqual(run_tests.load_timings(self.path),
                         {"tests.test_a": 1.5})

    def test_absent_is_empty(self):
        self.assertEqual(run_tests.load_timings(self.path), {})

    def test_unreadable_is_empty(self):
        for text in ("not json", "[1, 2]", '{"tests.test_a": "slow"}'):
            with self.subTest(text=text):
                self.path.write_text(text, encoding="utf-8")
                self.assertEqual(run_tests.load_timings(self.path), {})
        self.path.write_bytes(b"\xff\xfe")
        self.assertEqual(run_tests.load_timings(self.path), {})


class TestMain(cli_contract.CliContract, TreeCase):
    usage_fragment = "python3 run_tests.py"

    def test_each_module_runs_as_its_own_unittest_child_in_the_root(self):
        code, _ = self.run_cli([])
        self.assertEqual(code, 0)
        self.assertEqual(
            sorted(self.spawn.calls),
            [(["python3", "-m", "unittest", module], self.root)
             for module in ("tests.test_a", "tests.test_b",
                            "tests.test_c_long")])

    def test_a_clean_run_prints_the_total_test_count_and_exits_0(self):
        code, out = self.run_cli([])
        self.assertEqual(code, 0)
        self.assertRegex(
            out.splitlines()[-1],
            r"^tests: 9 tests across 3 modules in \d+\.\ds on 4 workers,"
            r" 0 problem\(s\)$")

    def test_a_planted_failure_exits_1_and_names_the_module_then_its_output(
            self):
        spawn = FakeSpawn({"tests.test_b": (1, FAILING)})
        code, out = self.run_cli([], spawn=spawn)
        self.assertEqual(code, 1)
        self.assertIn("tests: tests.test_b failed\n" + FAILING, out)
        self.assertNotIn("tests.test_a failed", out)
        self.assertTrue(out.splitlines()[-1].endswith(", 1 problem(s)"))

    def test_a_child_that_never_reports_a_count_is_a_failure(self):
        spawn = FakeSpawn({"tests.test_a": (0, "Segmentation fault\n")})
        code, out = self.run_cli([], spawn=spawn)
        self.assertEqual(code, 1)
        self.assertIn("tests: tests.test_a failed\nSegmentation fault\n",
                      out)
        self.assertIn("tests: 6 tests across 3 modules", out)

    def test_the_longest_module_is_spawned_first(self):
        (self.root / "tests" / "timings.json").write_text(
            json.dumps({"tests.test_c_long": 20.0, "tests.test_a": 1.0}),
            encoding="utf-8")
        self.run_cli(["-j", "1"])
        self.assertEqual([cmd[-1] for cmd, _ in self.spawn.calls],
                         ["tests.test_c_long", "tests.test_a",
                          "tests.test_b"])

    def test_dash_j_overrides_the_cpu_count(self):
        code, out = self.run_cli(["-j", "2"])
        self.assertEqual(code, 0)
        self.assertIn(" on 2 workers,", out.splitlines()[-1])

    def test_the_cpu_count_is_the_default_worker_count(self):
        _, out = self.run_cli([], cpu_count=lambda: 12)
        self.assertIn(" on 12 workers,", out.splitlines()[-1])

    def test_a_bad_dash_j_prints_usage_and_exits_2(self):
        for argv in (["-j"], ["-j", "x"], ["-j", "0"], ["-j", "-1"]):
            with self.subTest(argv=argv):
                code, out = self.run_cli(argv)
                self.assertEqual(code, 2)
                self.assertIn(self.usage_fragment, out)
        self.assertEqual(self.spawn.calls, [])

    def test_record_writes_the_timings_file_after_a_clean_run(self):
        path = self.root / "tests" / "timings.json"
        code, _ = self.run_cli(["--record"])
        self.assertEqual(code, 0)
        timings = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(sorted(timings),
                         ["tests.test_a", "tests.test_b", "tests.test_c_long"])
        for value in timings.values():
            self.assertIsInstance(value, float)

    def test_record_leaves_the_timings_alone_after_a_failure(self):
        path = self.root / "tests" / "timings.json"
        path.write_text('{"tests.test_a": 1.0}', encoding="utf-8")
        spawn = FakeSpawn({"tests.test_b": (1, FAILING)})
        code, _ = self.run_cli(["--record"], spawn=spawn)
        self.assertEqual(code, 1)
        self.assertEqual(path.read_text(encoding="utf-8"),
                         '{"tests.test_a": 1.0}')


if __name__ == "__main__":
    unittest.main()
