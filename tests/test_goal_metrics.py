"""goal_metrics.py (ADR-0135, #2346) — the four goal metrics.

The pure half, compute(), is exercised directly over hand-built PR
records; main() runs against the shared FakeGh and an injected clock,
and its problem strings are asserted exactly.
"""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

import goal_metrics

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_gh import FakeGh  # noqa: E402

NOW = datetime(2026, 11, 24, tzinfo=timezone.utc)
OWNER = "owner"


def iso(days_ago, hours=0):
    moment = NOW - timedelta(days=days_ago) + timedelta(hours=hours)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def pr(number, merged_days_ago, files, title="feat: x", body="",
       created_days_ago=None, issues=(), commit_logins=("",),
       reviewers=(), commenters=()):
    merged = iso(merged_days_ago)
    created = iso(merged_days_ago + 1 if created_days_ago is None
                  else created_days_ago)
    return {
        "number": number, "title": title, "body": body,
        "createdAt": created, "mergedAt": merged,
        "files": [{"path": p} for p in files],
        "closingIssuesReferences": [{"number": n} for n in issues],
        "commits": [{"authors": [{"login": login}]}
                    for login in commit_logins],
        "reviews": [{"author": {"login": login}, "submittedAt": created}
                    for login in reviewers],
        "comments": [{"author": {"login": login}, "createdAt": created}
                     for login in commenters],
    }


def compute(prs, issues=None, days=28):
    return goal_metrics.compute(prs, issues or {}, OWNER, NOW, days)


class ShippedPathTest(unittest.TestCase):
    def test_product_paths_are_shipped(self):
        for path in ("skills/next/SKILL.md", ".claude-plugin/plugin.json",
                     "factory/templates/Makefile",
                     "docs/pipeline-protocol.md"):
            self.assertTrue(goal_metrics.is_shipped(path), path)

    def test_factory_paths_are_overhead(self):
        for path in ("tools/gates.py", "docs/adr/0135-x.md", "CLAUDE.md",
                     "docs/pipeline-protocol.md.bak", "skillset/x"):
            self.assertFalse(goal_metrics.is_shipped(path), path)


class OverheadRatioTest(unittest.TestCase):
    def test_counts_merged_prs_touching_no_shipped_path(self):
        row = compute([
            pr(1, 2, ["skills/a/SKILL.md"]),
            pr(2, 3, ["tools/gates.py"]),
            pr(3, 4, ["tools/x.py", "skills/b/SKILL.md"]),
            pr(4, 5, ["docs/adr/x.md"]),
        ])
        self.assertEqual(row["merged_prs"], 4)
        self.assertEqual(row["product_prs"], 2)
        self.assertEqual(row["overhead_ratio"], 0.5)

    def test_prs_merged_before_the_window_are_ignored(self):
        row = compute([pr(1, 2, ["tools/a.py"]),
                       pr(2, 40, ["skills/a/SKILL.md"])])
        self.assertEqual(row["merged_prs"], 1)
        self.assertEqual(row["overhead_ratio"], 1.0)

    def test_empty_window_reports_none(self):
        row = compute([])
        self.assertIsNone(row["overhead_ratio"])
        self.assertIsNone(row["lead_time_hours_median"])
        self.assertIsNone(row["unattended_share"])
        self.assertIsNone(row["escape_rate"])


class LeadTimeTest(unittest.TestCase):
    def test_measures_from_the_earliest_linked_issue(self):
        # merged 2 days ago; issue opened 4 days ago -> 48h
        row = compute([pr(1, 2, ["skills/a/SKILL.md"], issues=[7, 8])],
                      issues={7: iso(4), 8: iso(3)})
        self.assertEqual(row["lead_time_hours_median"], 48.0)

    def test_falls_back_to_pr_creation_without_an_issue(self):
        row = compute([pr(1, 2, ["skills/a/SKILL.md"],
                          created_days_ago=3)])
        self.assertEqual(row["lead_time_hours_median"], 24.0)

    def test_issue_opened_after_the_pr_uses_the_pr(self):
        row = compute([pr(1, 2, ["skills/a/SKILL.md"], issues=[7],
                          created_days_ago=5)], issues={7: iso(3)})
        self.assertEqual(row["lead_time_hours_median"], 72.0)

    def test_median_over_product_prs_only(self):
        row = compute([
            pr(1, 2, ["skills/a/SKILL.md"], created_days_ago=3),
            pr(2, 2, ["skills/a/SKILL.md"], created_days_ago=4),
            pr(3, 2, ["skills/a/SKILL.md"], created_days_ago=12),
            pr(4, 2, ["tools/a.py"], created_days_ago=20),
        ])
        self.assertEqual(row["lead_time_hours_median"], 48.0)


class UnattendedShareTest(unittest.TestCase):
    def test_owner_commit_review_or_comment_is_a_touch(self):
        row = compute([
            pr(1, 2, ["skills/a/SKILL.md"]),
            pr(2, 2, ["skills/a/SKILL.md"], commit_logins=("", OWNER)),
            pr(3, 2, ["skills/a/SKILL.md"], reviewers=(OWNER,)),
            pr(4, 2, ["skills/a/SKILL.md"], commenters=(OWNER,)),
        ])
        self.assertEqual(row["unattended_share"], 0.25)

    def test_other_actors_are_not_touches(self):
        row = compute([pr(1, 2, ["skills/a/SKILL.md"],
                          commit_logins=("someone",),
                          reviewers=("reviewerbot",),
                          commenters=("reviewerbot",))])
        self.assertEqual(row["unattended_share"], 1.0)

    def test_owner_activity_after_the_merge_is_not_a_touch(self):
        record = pr(1, 2, ["skills/a/SKILL.md"])
        record["comments"] = [{"author": {"login": OWNER},
                               "createdAt": iso(1)}]
        self.assertEqual(compute([record])["unattended_share"], 1.0)


class EscapeRateTest(unittest.TestCase):
    def test_a_revert_naming_the_pr_is_an_escape(self):
        row = compute([
            pr(1, 20, ["skills/a/SKILL.md"]),
            pr(2, 18, ["skills/a/SKILL.md"], title='Revert "feat: x"',
               body="Reverts #1"),
        ])
        self.assertEqual(row["escaped"], [1])

    def test_a_fixes_pr_trailer_is_an_escape(self):
        row = compute([
            pr(1, 20, ["skills/a/SKILL.md"]),
            pr(2, 25, ["skills/b/SKILL.md"]),
            pr(3, 18, ["tools/x.py"], title="fix: y",
               body="Fixes-PR: #1"),
        ])
        self.assertEqual(row["escaped"], [1])
        self.assertEqual(row["escape_rate"], 0.5)

    def test_a_fix_touching_the_same_shipped_file_is_an_escape(self):
        row = compute([
            pr(1, 20, ["skills/a/SKILL.md", "tools/x.py"]),
            pr(2, 18, ["skills/a/SKILL.md"], title="fix(next): y"),
        ])
        self.assertEqual(row["escaped"], [1])

    def test_a_fix_naming_another_pr_skips_the_file_fallback(self):
        row = compute([
            pr(1, 20, ["skills/a/SKILL.md"]),
            pr(2, 22, ["skills/a/SKILL.md"]),
            pr(3, 18, ["skills/a/SKILL.md"], title="fix: y",
               body="Fixes-PR: #2"),
        ])
        self.assertEqual(row["escaped"], [2])

    def test_a_fix_after_fourteen_days_or_a_shared_tool_is_not(self):
        row = compute([
            pr(1, 27, ["skills/a/SKILL.md", "tools/x.py"]),
            pr(2, 15, ["tools/x.py"], title="fix: y"),
            pr(3, 10, ["skills/a/SKILL.md"], title="fix: z"),
        ])
        self.assertEqual(row["escaped"], [])
        self.assertEqual(row["escape_rate"], 0.0)

    def test_only_prs_with_fourteen_days_of_hindsight_are_judged(self):
        row = compute([
            pr(1, 5, ["skills/a/SKILL.md"]),
            pr(2, 3, ["skills/a/SKILL.md"], title="fix: y"),
        ])
        self.assertIsNone(row["escape_rate"])


REGISTER = """# Process register

| Process | What it is | Metric | Last real catch | Status |
|---|---|---|---|---|
| fresh | x | quality | 2026-11-19, [#1](u): caught | keep |
| boundary | x | quality | 2026-09-24, [#2](u): caught | keep |
| stale | x | none stated | 2026-08-28, [#3](u): caught | sunset-candidate |
| silent | x | none stated | none found | sunset-candidate |
"""


class SunsetFlagTest(unittest.TestCase):
    def test_flags_rows_with_no_catch_in_sixty_days(self):
        self.assertEqual(goal_metrics.sunset_flags(REGISTER, NOW),
                         ["boundary", "stale", "silent"])

    def test_a_catch_exactly_sixty_days_old_is_kept(self):
        on_the_line = REGISTER.replace("2026-09-24", "2026-09-25")
        self.assertEqual(goal_metrics.sunset_flags(on_the_line, NOW),
                         ["stale", "silent"])

    def test_none_found_flags_even_when_the_note_names_a_date(self):
        text = REGISTER.replace(
            "| silent | x | none stated | none found |",
            "| silent | x | none stated | none found (cites 2026-11-20) |")
        self.assertIn("silent", goal_metrics.sunset_flags(text, NOW))

    def test_text_without_the_table_flags_nothing(self):
        self.assertEqual(goal_metrics.sunset_flags("# nothing\n", NOW), [])


def gh_answers(prs, issues=(), owner="owner"):
    return {
        ("repo", "view"): json.dumps({"owner": {"login": owner}}),
        ("pr", "list"): json.dumps(prs),
        ("issue", "list"): json.dumps(list(issues)),
    }


class MainTest(unittest.TestCase):
    def run_main(self, argv, fake):
        out = io.StringIO()
        with redirect_stdout(out):
            code = goal_metrics.main(argv, run=fake, now=NOW)
        return code, out.getvalue()

    def test_prints_the_row_and_reads_the_owner_from_the_repo(self):
        fake = FakeGh(gh_answers(
            [pr(1, 2, ["skills/a/SKILL.md"], issues=[9],
                reviewers=("owner",))],
            issues=[{"number": 9, "createdAt": iso(4)}]))
        code, out = self.run_main([], fake)
        self.assertEqual(code, 0)
        row = json.loads(out.splitlines()[0])
        self.assertEqual(row["date"], "2026-11-24")
        self.assertEqual(row["owner"], "owner")
        self.assertEqual(row["lead_time_hours_median"], 48.0)
        self.assertEqual(row["unattended_share"], 0.0)
        self.assertIn("goal: 0 problem(s)", out)

    def test_commit_logins_come_from_one_rest_read_per_product_pr(self):
        listed = [pr(1, 2, ["skills/a/SKILL.md"]), pr(2, 2, ["tools/a.py"])]
        for record in listed:
            del record["commits"]
        answers = gh_answers(listed)
        answers[("api", "repos/{owner}/{repo}/pulls/1/commits")] = \
            "\nowner\n"
        fake = FakeGh(answers)
        code, out = self.run_main(["--owner", "owner"], fake)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.splitlines()[0])
                         ["unattended_share"], 0.0)
        api_calls = [c for c in fake.calls if c[0] == "api"]
        self.assertEqual(len(api_calls), 1)

    def test_a_failed_commit_read_is_a_problem(self):
        listed = [pr(1, 2, ["skills/a/SKILL.md"])]
        fake = FakeGh(gh_answers(listed), failing=["api"])
        code, out = self.run_main(["--owner", "owner"], fake)
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), [
            "goal: gh api commits for #1 failed: boom",
            "goal: 1 problem(s)",
        ])

    def test_owner_flag_skips_the_repo_read(self):
        fake = FakeGh(gh_answers([]))
        self.run_main(["--owner", "someone"], fake)
        self.assertFalse(any(c[:2] == ["repo", "view"] for c in fake.calls))

    def test_append_writes_one_jsonl_row(self):
        fake = FakeGh(gh_answers([pr(1, 2, ["tools/a.py"])]))
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "goal-metrics.jsonl"
            ledger.write_text('{"date": "2026-11-17"}\n')
            code, _ = self.run_main(["--append", str(ledger)], fake)
            lines = ledger.read_text().splitlines()
        self.assertEqual(code, 0)
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[1])["overhead_ratio"], 1.0)

    def test_markdown_prints_a_table_and_still_appends_json(self):
        fake = FakeGh(gh_answers([pr(1, 2, ["skills/a/SKILL.md"],
                                    created_days_ago=3)]))
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "goal-metrics.jsonl"
            code, out = self.run_main(["--owner", "o", "--markdown",
                                       "--append", str(ledger)], fake)
            appended = json.loads(ledger.read_text())
        self.assertEqual(code, 0)
        self.assertEqual(appended["lead_time_hours_median"], 24.0)
        self.assertEqual(out.splitlines()[:8], [
            "## Goal metrics (ADR-0135), 28 days to 2026-11-24",
            "",
            "| Metric | Value |",
            "| --- | --- |",
            "| Lead time, median (product PRs) | 24.0 h |",
            "| Escape rate | n/a |",
            "| Unattended share | 100.0% |",
            "| Overhead ratio | 0.0% (0 of 1 merged PRs) |",
        ])

    def test_the_register_flags_ride_the_row_and_the_table(self):
        fake = FakeGh(gh_answers([]))
        with tempfile.TemporaryDirectory() as tmp:
            register = Path(tmp) / "process-register.md"
            register.write_text(REGISTER)
            code, out = self.run_main(["--owner", "o", "--register",
                                       str(register)], fake)
            _, table = self.run_main(["--owner", "o", "--markdown",
                                      "--register", str(register)], fake)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.splitlines()[0])["sunset_flags"],
                         ["boundary", "stale", "silent"])
        self.assertIn("Sunset candidates (no real catch in 60 days):"
                      " boundary, stale, silent.", table)

    def test_a_missing_register_flags_nothing(self):
        fake = FakeGh(gh_answers([]))
        code, out = self.run_main(["--owner", "o", "--register",
                                   "/nonexistent/register.md"], fake)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.splitlines()[0])["sunset_flags"],
                         [])

    def test_a_failed_pr_read_is_a_problem_and_writes_nothing(self):
        fake = FakeGh(gh_answers([]), failing=["pr", "list"])
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "goal-metrics.jsonl"
            code, out = self.run_main(["--append", str(ledger)], fake)
            self.assertFalse(ledger.exists())
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), [
            "goal: gh pr list failed: boom",
            "goal: 1 problem(s)",
        ])

    def test_the_pr_read_spans_the_window_plus_the_hindsight(self):
        fake = FakeGh(gh_answers([]))
        self.run_main(["--days", "7", "--owner", "o"], fake)
        listing = next(c for c in fake.calls if c[:2] == ["pr", "list"])
        self.assertIn("merged:>=2026-11-03", listing)

    def test_a_full_window_is_a_problem(self):
        prs = [pr(n, 2, ["tools/a.py"]) for n in range(3)]
        fake = FakeGh(gh_answers(prs))
        original = goal_metrics.WINDOW
        goal_metrics.WINDOW = 3
        try:
            code, out = self.run_main(["--owner", "o"], fake)
        finally:
            goal_metrics.WINDOW = original
        self.assertEqual(code, 1)
        self.assertIn("goal: gh pr list returned a full 3-entry window",
                      out)


if __name__ == "__main__":
    unittest.main()
