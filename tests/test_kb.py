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
import socket
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import git_repo  # noqa: E402
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

    def test_summary_over_its_cap(self):
        self.indexed("cache")
        self.kb_page("long", summary="y" * (kb.SUMMARY_CAP + 1))
        self.assertEqual(self.lint()[0],
                         f"kb: docs/kb/long.md summary is"
                         f" {kb.SUMMARY_CAP + 1} bytes, over its"
                         f" {kb.SUMMARY_CAP}-byte cap — say the one fact")

    def test_summary_at_its_cap_passes(self):
        self.indexed("cache")
        self.kb_page("long", summary="y" * kb.SUMMARY_CAP)
        self.assertEqual(kb.index(self.root), [])
        self.assertEqual(self.lint(), [])

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

    def test_titled_and_angle_bracket_links_resolve(self):
        write(self.root / "docs" / "my notes.md", "x\n")
        self.kb_page("cache", body='See [auth](auth.md "Auth") and'
                     ' [n](<../my notes.md>) and [g](<gone.md> "G").\n')
        self.indexed("auth")
        self.assertEqual([p for p in self.lint() if "links to" in p], [
            "kb: docs/kb/cache.md links to 'gone.md', which does not exist"])

    def test_bracketed_lists_parse_like_bare_ones(self):
        self.kb_page("cache", sources="[src/a.py]", related="[auth]")
        self.indexed("auth")
        self.assertEqual(self.lint(), [])


def aged(extra, **fields):
    """page()'s text with the extra frontmatter lines (ADR-0125's
    optional outside-check fields) after the four required ones."""
    head, rest = page(**fields).split("\n---\n", 1)
    return f"{head}\n{extra}\n---\n{rest}"


class TestAge(Tree):
    """ADR-0125: a page declares what it was checked against, when, and
    for how long; lint ages that declaration against an injected today
    and runs nothing to do it."""

    FRESH = ("checked-against: the GitHub API; not GitHub's docs\n"
             "checked: 2026-10-01\nmax-age: 30d")

    def setUp(self):
        super().setUp()
        self.kb_page("cache")

    def declare(self, extra, slug="gh"):
        write(self.root / "docs" / "kb" / f"{slug}.md", aged(extra))
        self.assertEqual(kb.index(self.root), [])

    def lint_on(self, today):
        return kb.lint(self.root, git=lambda args: "", today=today)

    def page_named(self, slug):
        return next(p for p in kb.pages(self.root) if p["slug"] == slug)

    def test_one_day_past_due_is_one_problem(self):
        self.declare(self.FRESH)
        self.assertEqual(self.lint_on(date(2026, 11, 1)), [
            "kb: docs/kb/gh.md is past its declared age: checked"
            " 2026-10-01, max-age 30d, due 2026-10-31 — re-check it"])

    def test_on_the_due_date_it_is_still_fresh(self):
        self.declare(self.FRESH)
        self.assertEqual(self.lint_on(date(2026, 10, 31)), [])

    def test_age_problems_reads_one_page(self):
        self.declare(self.FRESH)
        gh = self.page_named("gh")
        self.assertEqual(kb.age_problems(gh, date(2026, 10, 31)), [])
        self.assertEqual(kb.age_problems(gh, date(2026, 12, 1)), [
            "kb: docs/kb/gh.md is past its declared age: checked"
            " 2026-10-01, max-age 30d, due 2026-10-31 — re-check it"])

    def test_checked_without_max_age_names_the_missing_field(self):
        self.declare("checked-against: the GitHub API\nchecked: 2026-10-01")
        self.assertEqual(self.lint_on(date(2026, 10, 2)), [
            "kb: docs/kb/gh.md declares an outside check but is missing"
            " field 'max-age'"])

    def test_max_age_alone_names_both_missing_fields(self):
        self.declare("max-age: 30d")
        self.assertEqual(self.lint_on(date(2026, 10, 2)), [
            "kb: docs/kb/gh.md declares an outside check but is missing"
            " field 'checked-against'",
            "kb: docs/kb/gh.md declares an outside check but is missing"
            " field 'checked'"])

    def test_empty_checked_against(self):
        self.declare("checked-against:\nchecked: 2026-10-01\nmax-age: 30d")
        self.assertEqual(self.lint_on(date(2026, 10, 2)), [
            "kb: docs/kb/gh.md has an empty 'checked-against'"])

    def test_checked_that_is_not_a_date(self):
        for value in ("yesterday", "2026-13-01", "2026/10/01"):
            with self.subTest(value=value):
                self.declare("checked-against: the GitHub API\n"
                             f"checked: {value}\nmax-age: 30d")
                self.assertEqual(self.lint_on(date(2026, 10, 2)), [
                    f"kb: docs/kb/gh.md checked {value!r} is not a"
                    " YYYY-MM-DD date"])

    def test_checked_after_today(self):
        self.declare(self.FRESH)
        self.assertEqual(self.lint_on(date(2026, 9, 30)), [
            "kb: docs/kb/gh.md checked 2026-10-01 is after today"
            " (2026-09-30)"])

    def test_max_age_that_is_not_whole_days(self):
        for value in ("0d", "30", "thirty"):
            with self.subTest(value=value):
                self.declare("checked-against: the GitHub API\n"
                             f"checked: 2026-10-01\nmax-age: {value}")
                self.assertEqual(self.lint_on(date(2027, 10, 2)), [
                    f"kb: docs/kb/gh.md max-age {value!r} is not a whole"
                    " number of days like 30d"])

    def test_checked_against_alone_never_ages(self):
        self.declare("checked-against: macOS zsh with gh 2.62; not Linux CI")
        self.assertEqual(self.lint_on(date(2036, 1, 1)), [])

    def test_a_page_with_none_of_the_fields_has_no_age(self):
        self.assertEqual(kb.index(self.root), [])
        self.assertEqual(self.lint_on(date(2036, 1, 1)), [])
        self.assertEqual(
            kb.age_problems(self.page_named("cache"), date(2036, 1, 1)), [])

    def test_the_index_line_never_carries_the_fields(self):
        self.declare(self.FRESH)
        block = kb.render_index(kb.pages(self.root))
        for field in ("checked-against", "checked", "max-age", "30d"):
            self.assertNotIn(field, block)

    def test_the_age_check_runs_nothing(self):
        self.declare(self.FRESH)
        self.declare("max-age: thirty", slug="bad")

        def refuse(*args, **kwargs):
            raise AssertionError("the age check ran something")

        with mock.patch.object(kb.cli, "runner", refuse), \
                mock.patch.object(socket, "socket", refuse):
            problems = self.lint_on(date(2026, 11, 1))
            direct = (kb.age_problems(self.page_named("bad"),
                                      date(2026, 11, 1))
                      + kb.age_problems(self.page_named("gh"),
                                        date(2026, 11, 1)))
        expected = [
            "kb: docs/kb/bad.md declares an outside check but is missing"
            " field 'checked-against'",
            "kb: docs/kb/bad.md declares an outside check but is missing"
            " field 'checked'",
            "kb: docs/kb/bad.md max-age 'thirty' is not a whole number of"
            " days like 30d",
            "kb: docs/kb/gh.md is past its declared age: checked"
            " 2026-10-01, max-age 30d, due 2026-10-31 — re-check it"]
        self.assertEqual(problems, expected)
        self.assertEqual(direct, expected)


class TestStale(unittest.TestCase):
    """Freshness against a real git history: a page is stale once any
    source it cites changed between its verified commit and HEAD."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        git_repo.init(self.root)
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

    def test_renamed_source_names_where_it_went(self):
        self.indexed(sources="src/a.py", verified=self.sha)
        git(self.root, "mv", "src/a.py", "src/c.py")
        git(self.root, "commit", "-qm", "rename")
        self.assertEqual(kb.lint(self.root), [
            "kb: docs/kb/cache.md cites source 'src/a.py', which does not"
            " exist",
            f"kb: docs/kb/cache.md is stale: src/a.py (renamed to"
            f" src/c.py) changed since verified {self.sha[:7]} — re-verify"
            " it"])

    def test_deleted_source_has_no_rename_hint(self):
        self.indexed(sources="src/a.py", verified=self.sha)
        git(self.root, "rm", "-q", "src/a.py")
        git(self.root, "commit", "-qm", "delete")
        self.assertEqual(kb.lint(self.root)[1],
                         f"kb: docs/kb/cache.md is stale: src/a.py changed"
                         f" since verified {self.sha[:7]} — re-verify it")

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
