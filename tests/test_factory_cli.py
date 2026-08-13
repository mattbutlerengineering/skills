"""factory.py — the one front door over the root tools' CLI legs
(issue #237). A router, not a seam: these tests pin that every verb
reaches the module main() that already exists (with that main's own
calling convention), that the verb table is DERIVED from the CLI-bearing
root modules rather than restated beside them, and that the index the
tools never had (`factory.py help`) names every verb.
"""
import importlib
import inspect
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import factory


class TestVerbTableIsDerived(unittest.TestCase):
    """Issue #237's hard constraint: a hand-maintained list of subcommands
    beside the real tools drifts the first time a tool is added or
    retired. The table is pinned to a mechanical scan of the root — a new
    `if __name__ == "__main__":` guard breaks this test until the tool
    gets its verb."""

    ROOT = Path(factory.__file__).resolve().parent
    GUARD = 'if __name__ == "__main__":'

    def cli_bearing_modules(self):
        return {path.stem for path in self.ROOT.glob("*.py")
                if path.stem != "factory"
                and self.GUARD in path.read_text(encoding="utf-8")}

    def test_every_cli_bearing_root_module_has_exactly_one_verb(self):
        routed = [module for module, _ in factory.VERBS.values()]
        self.assertEqual(sorted(routed), sorted(set(routed)),
                         "a module is routed to by two verbs")
        self.assertEqual(set(routed), self.cli_bearing_modules())

    def test_the_verb_is_the_module_name_hyphenated(self):
        """One vocabulary, not two: the verb IS the module's name."""
        for verb, (module_name, _) in factory.VERBS.items():
            self.assertEqual(verb, module_name.replace("_", "-"))

    def test_each_row_declares_the_convention_its_main_accepts(self):
        """ADR-0054: the convention column was the table's last hand-kept
        fact, so it is derived here too — a main that grows or loses its
        argv parameter fails this test until its row follows. The
        derivation lives in the test, not in the router: factory.py runs
        on every push and must import one module per invocation, not
        fourteen.

        `bare` means the main has NO argv slot, not merely that it can be
        called with no arguments. A main whose argv slot carries a
        default (`main(argv=None)`) binds `main()` happily and then reads
        the *process's* argv — under the front door that is
        `["charter-replay"]`, and argparse rejects it. So the discriminator
        is the slot's existence, and the row must say `argv` wherever one
        exists.
        """
        for verb, (module_name, style) in sorted(factory.VERBS.items()):
            with self.subTest(verb=verb):
                positional = [
                    p for p in inspect.signature(
                        importlib.import_module(module_name)
                        .main).parameters.values()
                    if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
                if positional:
                    # what makes the slot's existence readable as "argv":
                    # every root main spells its first positional that way
                    self.assertEqual(positional[0].name, "argv")
                self.assertEqual(style, "argv" if positional else "bare")

    def test_a_bare_verb_reads_nothing_from_the_process_argv(self):
        """The failure the rule above prevents, driven end to end: a
        `bare` row means factory calls `main()`, so any argv the main
        then resolves for itself comes from `sys.argv` — which under the
        front door holds the verb, not the tool's arguments."""
        for verb, (module_name, style) in sorted(factory.VERBS.items()):
            if style != "bare":
                continue
            with self.subTest(verb=verb):
                params = inspect.signature(
                    importlib.import_module(module_name).main).parameters
                self.assertEqual(
                    list(params), [],
                    f"{verb} is routed bare but its main takes parameters;"
                    " factory.main() would leave them to sys.argv")


class TestDispatch(unittest.TestCase):
    def test_every_verb_reaches_its_module_main(self):
        for verb, (module_name, style) in factory.VERBS.items():
            with self.subTest(verb=verb):
                with mock.patch(f"{module_name}.main",
                                return_value=0) as fake:
                    self.assertEqual(factory.main([verb]), 0)
                if style == "bare":
                    fake.assert_called_once_with()
                else:
                    fake.assert_called_once_with([])

    def test_arguments_pass_through_verbatim(self):
        with mock.patch("gates.main", return_value=3) as fake:
            self.assertEqual(factory.main(["gates", "--selftest"]), 3)
        fake.assert_called_once_with(["--selftest"])

    def test_a_bare_main_refuses_extra_arguments(self):
        """lint/trigger-eval mains take nothing; dropping the caller's
        arguments silently would look like they applied."""
        with mock.patch("lint.main") as fake:
            out = io.StringIO()
            with redirect_stdout(out):
                code = factory.main(["lint", "--fast"])
        self.assertEqual(code, 2)
        fake.assert_not_called()
        self.assertIn("factory: lint takes no arguments", out.getvalue())

    def test_the_delegates_exit_code_comes_back_unchanged(self):
        with mock.patch("validator.main", return_value=1) as fake:
            self.assertEqual(factory.main(["validator", "review"]), 1)
        fake.assert_called_once_with(["review"])


class TestIndex(unittest.TestCase):
    def test_help_lists_every_verb(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = factory.main(["help"])
        self.assertEqual(code, 0)
        for verb in factory.VERBS:
            self.assertIn(verb, out.getvalue())

    def test_no_arguments_prints_usage_and_exits_2(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(factory.main([]), 2)
        self.assertIn("factory", out.getvalue())

    def test_an_unknown_verb_is_a_problem_not_a_traceback(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = factory.main(["deploy"])
        self.assertEqual(code, 2)
        self.assertIn("factory: unknown verb 'deploy'", out.getvalue())


if __name__ == "__main__":
    unittest.main()
