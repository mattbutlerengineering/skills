"""md_claims.py (issue #685): the deterministic half of the audit skill's
markdown-claims mode. It extracts the claims a human-facing doc makes
that a lookup can settle — links, inline paths, fenced shell commands —
and checks each one against the tree without ever running a documented
command.

Pinned against tempfile fixture trees, through the public interface:
check() returns the exact problem strings, extract() the claim records,
main() the summary line and exit code.
"""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import md_claims  # noqa: E402

FENCE = "```"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def shell(*lines, lang="sh"):
    return "\n".join([FENCE + lang, *lines, FENCE, ""])


class Tree(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def readme(self, text):
        write(self.root / "README.md", text)

    def check(self, paths=None):
        return md_claims.check(self.root, paths)


class LinkClaims(Tree):
    def test_a_missing_relative_link_is_a_problem(self):
        self.readme("See [setup](docs/setup.md).\n")
        self.assertEqual(self.check(), [
            "md-claims: README.md:1: link target 'docs/setup.md' does not"
            " exist"])

    def test_present_links_urls_and_anchors_pass(self):
        write(self.root / "docs" / "setup.md", "# Setup\n")
        self.readme("[a](docs/setup.md#install) [b](https://x.io/y)"
                    " [c](#top) [d](/docs/setup.md) [e](mailto:a@b.c)\n")
        self.assertEqual(self.check(), [])

    def test_a_link_resolves_against_the_linking_doc(self):
        write(self.root / "docs" / "a.md", "[b](b.md) [up](../README.md)\n")
        write(self.root / "docs" / "b.md", "\n")
        self.readme("\n")
        self.assertEqual(self.check(), [])

    def test_links_in_fences_and_inline_code_are_examples(self):
        self.readme("`[x](gone.md)`\n" + shell("echo '[y](gone.md)'",
                                               lang="md"))
        self.assertEqual(self.check(), [])


class PathClaims(Tree):
    def test_a_missing_inline_path_is_a_problem(self):
        self.readme("The config lives in `config/app.toml`.\n")
        self.assertEqual(self.check(), [
            "md-claims: README.md:1: path 'config/app.toml' does not exist"])

    def test_a_present_path_passes_with_its_line_suffix(self):
        write(self.root / "src" / "app.py", "\n")
        self.readme("See `src/app.py:12` and `src/app.py` and `src/`.\n")
        self.assertEqual(self.check(), [])

    def test_a_bare_filename_passes_when_it_exists_anywhere(self):
        write(self.root / "pkg" / "deep" / "tool.py", "\n")
        self.readme("Run `tool.py` from its package.\n")
        self.assertEqual(self.check(), [])

    def test_a_bare_filename_found_nowhere_is_a_problem(self):
        self.readme("Edit `settings.yml`.\n")
        self.assertEqual(self.check(), [
            "md-claims: README.md:1: path 'settings.yml' does not exist"])

    def test_a_slashed_path_passes_as_a_suffix_of_a_real_path(self):
        write(self.root / "templates" / "tools" / "gate.py", "\n")
        self.readme("A stamped repo gets `tools/gate.py`.\n")
        self.assertEqual(self.check(), [])

    def test_a_parent_relative_path_passes_as_a_suffix(self):
        write(self.root / "docs" / "protocol.md", "\n")
        self.readme("Skills read `../../docs/protocol.md`.\n")
        self.assertEqual(self.check(), [])

    def test_non_paths_are_not_claims(self):
        self.readme("`owner/repo` `--flag` `<slug>/x.md` `docs/*.md`"
                    " `$HOME/x.md` `~/x.md` `/etc/hosts.txt`"
                    " `a b/c.md` `idea-to-prod@skills` `https://x.io/a.md`"
                    " `docs/{a,b}.md` `x.y`"
                    " `.py` `routine/` `.agents/`\n")
        self.assertEqual(self.check(), [])


class CommandClaims(Tree):
    def test_a_missing_script_is_a_problem(self):
        self.readme(shell("python3 tools/run.py --fast"))
        self.assertEqual(self.check(), [
            "md-claims: README.md:2: command runs 'tools/run.py', which"
            " does not exist"])

    def test_a_flag_the_script_never_mentions_is_a_problem(self):
        write(self.root / "run.py",
              "parser.add_argument('--fast')\nparser.add_argument('--n')\n")
        self.readme(shell("python3 -I run.py --fast --n=3 --slow"))
        self.assertEqual(self.check(), [
            "md-claims: README.md:2: flag '--slow' does not appear in"
            " run.py"])

    def test_a_flag_prefix_is_not_a_mention(self):
        write(self.root / "run.py", "'--fast-mode'\n")
        self.readme(shell("python3 run.py --fast"))
        self.assertEqual(self.check(), [
            "md-claims: README.md:2: flag '--fast' does not appear in"
            " run.py"])

    def test_a_path_shaped_program_must_exist(self):
        write(self.root / "scripts" / "ok.sh", "case --go\n")
        self.readme(shell("./scripts/ok.sh --go && scripts/gone.sh"))
        self.assertEqual(self.check(), [
            "md-claims: README.md:2: command runs 'scripts/gone.sh', which"
            " does not exist"])

    def test_cd_moves_the_base_for_the_rest_of_the_line(self):
        write(self.root / "pkg" / "run.py", "\n")
        self.readme(shell("cd pkg && python3 run.py"))
        self.assertEqual(self.check(), [])

    def test_a_script_may_resolve_against_the_doc_directory(self):
        write(self.root / "pkg" / "run.py", "\n")
        write(self.root / "pkg" / "README.md", shell("python3 run.py"))
        self.assertEqual(self.check(["pkg"]), [])

    def test_make_targets_are_checked_against_the_makefile(self):
        write(self.root / "Makefile", ".PHONY: check\ncheck lint: deps\n"
                                      "\ttrue\nX := 1\n")
        self.readme(shell("make check lint V=1", "make -C . chek"))
        self.assertEqual(self.check(), [
            "md-claims: README.md:3: make target 'chek' is not defined in"
            " Makefile"])

    def test_make_without_a_makefile_is_a_problem(self):
        self.readme(shell("make check"))
        self.assertEqual(self.check(), [
            "md-claims: README.md:2: command runs make, but no Makefile"
            " exists in ."])

    def test_package_scripts_are_checked(self):
        write(self.root / "package.json", '{"scripts": {"test": "x"}}\n')
        self.readme(shell("npm run test", "pnpm run build", "yarn add x"))
        self.assertEqual(self.check(), [
            "md-claims: README.md:3: script 'build' is not defined in"
            " package.json"])

    def test_console_blocks_check_only_prompted_lines(self):
        self.readme(shell("$ python3 gone.py", "python3 output.py",
                          lang="console"))
        self.assertEqual(self.check(), [
            "md-claims: README.md:2: command runs 'gone.py', which does"
            " not exist"])

    def test_external_programs_placeholders_and_heredocs_are_skipped(self):
        self.readme(shell(
            "# python3 commented.py",
            "git log --oneline --bogus",
            "python3 <skill dir>/tool.py",
            "python3 -m unittest discover tests",
            "FOO=1 python3 \"$DIR/x.py\"",
            "cat > out.txt <<'EOF'",
            "python3 inside-heredoc.py",
            "EOF",
            "python3 a.py \\",
            "  --x",
            "echo 'unbalanced",
            "python3 swallowed-by-the-open-quote.py"))
        write(self.root / "a.py", "'--x'\n")
        self.assertEqual(self.check(), [])

    def test_a_quoted_argument_may_span_lines(self):
        self.readme(shell("python3 -c \"import x", "print(x)\"",
                          "python3 gone.py"))
        self.assertEqual(md_claims.extract(self.root), [
            {"file": "README.md", "line": 2, "kind": "command",
             "text": "python3 -c \"import x\nprint(x)\""},
            {"file": "README.md", "line": 4, "kind": "command",
             "text": "python3 gone.py"}])
        self.assertEqual(self.check(), [
            "md-claims: README.md:4: command runs 'gone.py', which does"
            " not exist"])

    def test_only_shell_fences_hold_commands(self):
        self.readme(shell("python3 gone.py", lang="python"))
        self.assertEqual(self.check(), [])


class Scope(Tree):
    def test_the_default_set_is_readme_root_docs_and_docs_tree(self):
        write(self.root / "CONTRIBUTING.md", "`a/gone.md`\n")
        write(self.root / "docs" / "x" / "y.md", "`b/gone.md`\n")
        write(self.root / "docs" / "2026-01-01-snapshot.md", "`c/gone.md`\n")
        write(self.root / "CLAUDE.md", "`d/gone.md`\n")
        write(self.root / "src" / "notes.md", "`e/gone.md`\n")
        self.readme("\n")
        self.assertEqual(self.check(), [
            "md-claims: CONTRIBUTING.md:1: path 'a/gone.md' does not exist",
            "md-claims: docs/x/y.md:1: path 'b/gone.md' does not exist"])

    def test_explicit_paths_replace_the_default_set(self):
        write(self.root / "CLAUDE.md", "`d/gone.md`\n")
        self.readme("`r/gone.md`\n")
        self.assertEqual(self.check(["CLAUDE.md"]), [
            "md-claims: CLAUDE.md:1: path 'd/gone.md' does not exist"])

    def test_an_explicit_path_that_does_not_exist_is_a_problem(self):
        self.assertEqual(self.check(["nope.md"]), [
            "md-claims: nope.md does not exist"])

    def test_the_ignore_marker_covers_its_line_the_next_and_a_fence(self):
        self.readme("<!-- md-claims: ignore --> `a/gone.md`\n"
                    "<!-- md-claims: ignore -->\n"
                    "`b/gone.md`\n"
                    "<!-- md-claims: ignore -->\n"
                    + shell("python3 gone.py", "python3 gone2.py")
                    + "`c/gone.md`\n")
        self.assertEqual(self.check(), [
            "md-claims: README.md:9: path 'c/gone.md' does not exist"])


class Extract(Tree):
    def test_extract_lists_every_claim_with_its_kind(self):
        self.readme("[s](docs/s.md) uses `src/a.py`.\n"
                    + shell("python3 src/a.py --x"))
        self.assertEqual(md_claims.extract(self.root), [
            {"file": "README.md", "line": 1, "kind": "link",
             "text": "docs/s.md"},
            {"file": "README.md", "line": 1, "kind": "path",
             "text": "src/a.py"},
            {"file": "README.md", "line": 3, "kind": "command",
             "text": "python3 src/a.py --x"}])


class Main(Tree):
    def run_main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = md_claims.main(list(argv))
        return code, out.getvalue()

    def test_check_prints_problems_and_a_summary(self):
        self.readme("`a/gone.md`\n")
        code, out = self.run_main("check", str(self.root))
        self.assertEqual((code, out), (1, (
            "md-claims: README.md:1: path 'a/gone.md' does not exist\n"
            "md-claims: 1 problem(s) across 1 doc(s)\n")))

    def test_a_clean_tree_exits_zero(self):
        self.readme("Nothing to see.\n")
        self.assertEqual(self.run_main("check", str(self.root)),
                         (0, "md-claims: 0 problem(s) across 1 doc(s)\n"))

    def test_extract_prints_json(self):
        self.readme("`src/a.py`\n")
        code, out = self.run_main("extract", str(self.root))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), [
            {"file": "README.md", "line": 1, "kind": "path",
             "text": "src/a.py"}])

    def test_paths_follow_the_root(self):
        write(self.root / "CLAUDE.md", "`a/gone.md`\n")
        code, out = self.run_main("check", str(self.root), "CLAUDE.md")
        self.assertEqual(code, 1)
        self.assertIn("md-claims: CLAUDE.md:1:", out)

    def test_bad_usage_exits_two(self):
        self.assertEqual(self.run_main(), (2, md_claims.USAGE + "\n"))
        self.assertEqual(self.run_main("fix"), (2, md_claims.USAGE + "\n"))


if __name__ == "__main__":
    unittest.main()
