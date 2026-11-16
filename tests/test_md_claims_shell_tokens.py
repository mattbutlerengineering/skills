"""Audit defect #1858: md_claims reads fd redirects, option values and
here-strings as the shell does."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import md_claims  # noqa: E402


class TestShellTokens(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        (self.root / "Makefile").write_text("build:\n\techo\n")
        (self.root / "other.mk").write_text("build:\n\techo\n")
        (self.root / "x.ts").write_text("1\n")

    def check(self, *lines):
        (self.root / "README.md").write_text(
            "\n".join(["```sh", *lines, "```", ""]))
        return md_claims.check(self.root)

    def test_fd_redirect_is_not_an_operand(self):
        self.assertEqual(self.check("make build 2>&1 | tee log"), [])

    def test_make_option_values_are_not_targets(self):
        self.assertEqual(self.check("make -j 4 build"), [])

    def test_make_dash_f_reads_that_makefile(self):
        self.assertEqual(self.check("make -f other.mk build"), [])
        self.assertEqual(self.check("make -f other.mk nope"), [
            "md-claims: README.md:2: make target 'nope' is not defined"
            " in other.mk"])

    def test_interpreter_option_value_is_not_the_script(self):
        self.assertEqual(self.check("node -r ts-node/register x.ts"), [])

    def test_here_string_does_not_open_a_heredoc(self):
        self.assertEqual(self.check("cat <<< word", "make missing-target",
                                    "word"), [
            "md-claims: README.md:3: make target 'missing-target' is not"
            " defined in Makefile"])


if __name__ == "__main__":
    unittest.main()
