"""kb.py (ADR-0078, issue #625): the knowledge-base skill's shipped tool —
the inline index it writes into the always-loaded file, and the lint that
keeps docs/kb/ honest.

Pinned against tempfile fixture trees, and for staleness against a real
throwaway git repo (the assembler tests' pattern): the claim under test
is "a cited source changed since the verified commit", which only git
can answer.
"""
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import kb  # noqa: E402


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def page(summary="Why the cache is keyed by tenant.", sources="src/a.py",
         verified="abc1234", related="", body="Body.\n"):
    fields = {"summary": summary, "sources": sources,
              "verified": verified, "related": related}
    lines = "\n".join(f"{key}: {value}" for key, value in fields.items()
                      if value is not None)
    return f"---\n{lines}\n---\n\n# Title\n\n{body}"


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), "-c", "user.email=t@example.com",
         "-c", "user.name=Tester", "-c", "commit.gpgsign=false", *args],
        check=True, capture_output=True, text=True).stdout.strip()


def run_main(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = kb.main(argv)
    return code, out.getvalue()


class Tree(unittest.TestCase):
    """A repo root with a CLAUDE.md and a source file every page cites."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        write(self.root / "CLAUDE.md", "# Notes\n\nKeep this.\n")
        write(self.root / "src" / "a.py", "x = 1\n")

    def kb_page(self, slug, **fields):
        write(self.root / "docs" / "kb" / f"{slug}.md", page(**fields))

    def lint(self):
        return kb.lint(self.root, git=lambda args: "")


class TestIndex(Tree):
    def test_no_kb_directory_is_the_one_problem(self):
        self.assertEqual(kb.index(self.root), [
            "kb: no docs/kb/ directory — the knowledge-base skill's"
            " setup flow creates it"])

    def test_no_always_loaded_file_is_a_problem(self):
        (self.root / "CLAUDE.md").unlink()
        self.kb_page("cache")
        self.assertEqual(kb.index(self.root), [
            "kb: neither CLAUDE.md nor AGENTS.md exists to hold the index"])

    def test_writes_one_line_per_page_between_markers(self):
        self.kb_page("cache")
        self.kb_page("auth", summary="Tokens are minted by the gateway.")
        self.assertEqual(kb.index(self.root), [])
        text = (self.root / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Notes\n\nKeep this.\n"))
        block = text[text.index(kb.BEGIN):]
        self.assertTrue(block.rstrip("\n").endswith(kb.END))
        self.assertIn("- docs/kb/auth.md: Tokens are minted by the"
                      " gateway.\n- docs/kb/cache.md: Why the cache is"
                      " keyed by tenant.\n", block)

    def test_index_is_idempotent(self):
        self.kb_page("cache")
        kb.index(self.root)
        once = (self.root / "CLAUDE.md").read_text(encoding="utf-8")
        kb.index(self.root)
        self.assertEqual(
            (self.root / "CLAUDE.md").read_text(encoding="utf-8"), once)
        self.assertEqual(once.count(kb.BEGIN), 1)

    def test_rewrites_the_block_in_place_and_keeps_what_follows(self):
        self.kb_page("cache")
        kb.index(self.root)
        path = self.root / "CLAUDE.md"
        path.write_text(path.read_text(encoding="utf-8") + "\n## After\n",
                        encoding="utf-8")
        self.kb_page("cache", summary="Changed summary.")
        kb.index(self.root)
        text = path.read_text(encoding="utf-8")
        self.assertIn("- docs/kb/cache.md: Changed summary.\n", text)
        self.assertNotIn("keyed by tenant", text)
        self.assertTrue(text.endswith("\n## After\n"))

    def test_writes_every_always_loaded_file_present(self):
        write(self.root / "AGENTS.md", "# Agents\n")
        self.kb_page("cache")
        self.assertEqual(kb.index(self.root), [])
        for name in ("CLAUDE.md", "AGENTS.md"):
            self.assertIn("- docs/kb/cache.md:",
                          (self.root / name).read_text(encoding="utf-8"))

    def test_refuses_a_page_without_a_summary(self):
        self.kb_page("cache", summary=None)
        self.assertEqual(kb.index(self.root), [
            "kb: docs/kb/cache.md is missing frontmatter field 'summary'"])
        self.assertNotIn(kb.BEGIN, (self.root / "CLAUDE.md").read_text(
            encoding="utf-8"))

    def test_refuses_an_index_over_budget(self):
        for n in range(40):
            self.kb_page(f"page-{n:02d}", summary="x" * 60)
        size = len(kb.render_index(kb.pages(self.root)).encode("utf-8"))
        self.assertEqual(kb.index(self.root), [
            f"kb: the index is {size} bytes, over its {kb.INDEX_BUDGET}-byte"
            " budget — shorten summaries or merge pages"])
        self.assertNotIn(kb.BEGIN, (self.root / "CLAUDE.md").read_text(
            encoding="utf-8"))


class TestLint(Tree):
    def indexed(self, *slugs):
        for slug in slugs:
            self.kb_page(slug)
        self.assertEqual(kb.index(self.root), [])

    def test_clean_tree_has_no_problems(self):
        self.indexed("cache")
        self.assertEqual(self.lint(), [])

    def test_no_kb_directory(self):
        self.assertEqual(self.lint(), [
            "kb: no docs/kb/ directory — the knowledge-base skill's"
            " setup flow creates it"])

    def test_missing_frontmatter_block_and_fields(self):
        self.indexed("cache")
        write(self.root / "docs" / "kb" / "bare.md", "# No frontmatter\n")
        self.kb_page("partial", sources="", verified=None, related=None)
        self.assertEqual(self.lint(), [
            "kb: docs/kb/bare.md has no frontmatter block",
            "kb: docs/kb/partial.md is missing frontmatter field 'sources'",
            "kb: docs/kb/partial.md is missing frontmatter field 'verified'",
            "kb: docs/kb/partial.md is missing frontmatter field 'related'",
            "kb: docs/kb/bare.md is an orphan: the index in CLAUDE.md"
            " does not list it — run kb.py index",
            "kb: docs/kb/partial.md is an orphan: the index in CLAUDE.md"
            " does not list it — run kb.py index",
        ])

    def test_no_index_block(self):
        self.kb_page("cache")
        self.assertEqual(self.lint(), [
            "kb: CLAUDE.md has no knowledge-base index — run kb.py index"])

    def test_orphan_and_dangling_entries(self):
        self.indexed("cache", "gone")
        (self.root / "docs" / "kb" / "gone.md").unlink()
        self.kb_page("fresh")
        self.assertEqual(self.lint(), [
            "kb: docs/kb/fresh.md is an orphan: the index in CLAUDE.md"
            " does not list it — run kb.py index",
            "kb: the index in CLAUDE.md lists docs/kb/gone.md, which does"
            " not exist",
        ])

    def test_out_of_date_summary(self):
        self.indexed("cache")
        self.kb_page("cache", summary="A new summary.")
        self.assertEqual(self.lint(), [
            "kb: the index in CLAUDE.md is out of date with the page"
            " summaries — run kb.py index"])

    def test_over_budget(self):
        self.indexed("cache")
        for n in range(40):
            self.kb_page(f"page-{n:02d}", summary="x" * 60)
        size = len(kb.render_index(kb.pages(self.root)).encode("utf-8"))
        problems = self.lint()
        self.assertEqual(problems[0],
                         f"kb: the index is {size} bytes, over its"
                         f" {kb.INDEX_BUDGET}-byte budget — shorten"
                         " summaries or merge pages")

    def test_broken_sources_related_and_links(self):
        self.kb_page("cache", sources="src/a.py, src/missing.py",
                     related="auth, nowhere",
                     body="See [auth](auth.md), [gone](gone.md),"
                          " [web](https://example.com) and [top](#top).\n")
        self.indexed("auth")
        self.assertEqual(self.lint(), [
            "kb: docs/kb/cache.md cites source 'src/missing.py', which"
            " does not exist",
            "kb: docs/kb/cache.md relates to 'nowhere', which is not a"
            " page in docs/kb/",
            "kb: docs/kb/cache.md links to 'gone.md', which does not exist",
        ])

    def test_bracketed_lists_parse_like_bare_ones(self):
        self.kb_page("cache", sources="[src/a.py]", related="[auth]")
        self.indexed("auth")
        self.assertEqual(self.lint(), [])


class TestStale(unittest.TestCase):
    """Freshness against a real git history: a page is stale once any
    source it cites changed between its verified commit and HEAD."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        git(self.root, "init", "-q")
        write(self.root / "CLAUDE.md", "# Notes\n")
        write(self.root / "src" / "a.py", "x = 1\n")
        write(self.root / "src" / "b.py", "y = 1\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "one")
        self.sha = git(self.root, "rev-parse", "HEAD")

    def indexed(self, **fields):
        write(self.root / "docs" / "kb" / "cache.md", page(**fields))
        self.assertEqual(kb.index(self.root), [])

    def test_unchanged_sources_are_fresh(self):
        self.indexed(sources="src/a.py", verified=self.sha)
        write(self.root / "src" / "b.py", "y = 2\n")
        git(self.root, "commit", "-qam", "two")
        self.assertEqual(kb.lint(self.root), [])

    def test_changed_source_makes_the_page_stale(self):
        self.indexed(sources="src/a.py, src/b.py", verified=self.sha)
        write(self.root / "src" / "a.py", "x = 2\n")
        git(self.root, "commit", "-qam", "two")
        self.assertEqual(kb.lint(self.root), [
            f"kb: docs/kb/cache.md is stale: src/a.py changed since"
            f" verified {self.sha[:7]} — re-verify it"])

    def test_unknown_verified_sha(self):
        self.indexed(verified="0" * 40)
        self.assertEqual(kb.lint(self.root), [
            f"kb: docs/kb/cache.md verified {'0' * 40!r} is not a commit"
            " in this repository"])

    def test_git_unavailable_is_a_problem_not_a_traceback(self):
        self.indexed(verified=self.sha)

        def broken(args):
            raise OSError("No such file or directory: 'git'")

        self.assertEqual(kb.lint(self.root, git=broken), [
            "kb: git is unavailable: No such file or directory: 'git'"])


class TestMain(Tree):
    def test_lint_reports_through_the_problem_contract(self):
        code, out = run_main(["lint", str(self.root)])
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines()[-1], "kb: 1 problem(s)")

    def test_index_then_stats(self):
        self.kb_page("cache")
        code, out = run_main(["index", str(self.root)])
        self.assertEqual((code, out), (0, "kb: 0 problem(s)\n"))
        code, out = run_main(["stats", str(self.root)])
        self.assertEqual(code, 0)
        stats = json.loads(out)
        self.assertEqual(stats["pages"], 1)
        self.assertEqual(stats["index_budget"], kb.INDEX_BUDGET)
        self.assertEqual(
            stats["index_bytes"],
            len(kb.render_index(kb.pages(self.root)).encode("utf-8")))
        self.assertEqual(stats["page_lines"], {"cache": 10})

    def test_usage(self):
        code, out = run_main(["frobnicate"])
        self.assertEqual(code, 2)
        self.assertIn("usage: kb.py", out)


if __name__ == "__main__":
    unittest.main()
