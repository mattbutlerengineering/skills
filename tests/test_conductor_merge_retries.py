"""conductor_merge.py's retried merge turns: a turn that stalled part
way through its own commits must not leave its retry stuck or wrong. A
facet of tests/test_conductor_merge.py (its TurnCase harness, scratch
repo and fake ports), split out so the merge-turn suites run as parallel
modules (#916).

- Step 3's bump is judged against the branch's committed plugin.json,
  not the worktree's: a turn that wrote the bump and stalled before its
  commit (a failed regeneration, staging or commit) leaves the version
  written but uncommitted, and its retry must still regenerate, commit
  and reserve it.
- Step 2's mechanical conflicts, in the factory source repo, are the
  manifest and plugin.json's version line: a turn that committed its
  bump and stalled conflicts on that line once main's version moves, and
  every retry would stall on it.
"""
import json
import sys
import unittest
from pathlib import Path

import conductor_merge as merge

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_conductor_flow import START, answered  # noqa: E402
from test_conductor_merge import (BRANCH, SEED, SHIPPED,  # noqa: E402
                                  TurnCase, sh, write)

PLUGIN = ".claude-plugin/plugin.json"
RED_RUN = {"name": "validate", "status": "completed", "conclusion": "failure"}


def plugin(version, name="p", description=None):
    text = SEED[PLUGIN].replace("0.7.3", version).replace(
        '"name": "p"', f'"name": "{name}"')
    if description is not None:
        text = text.replace('"name"', f'"description": "{description}",\n'
                            '  "name"')
    return text


class RetryCase(TurnCase):
    def retry(self, gh=None, tool=None):
        """Answer the first turn's stall `retry` and run the turn again,
        on a fresh log: what the retry alone did."""
        rows = [row for row in self.rows if row not in START]
        self.assertEqual(rows[-1]["ask_kind"], "stall")
        self.ledger(START + rows + [answered(rows[-1]["id"], "retry",
                                             "#12")])
        self.log = []
        self.gh = gh or self.fake_gh()
        summary, problems = merge.merge_turn(
            self.root, "b1", "#12", self.clock, self.git, self.gh,
            tool or self.tool(), self.clock.sleep, pid=555)
        self.rows = merge.load(self.root, "b1")[0]
        return summary, problems

    def version(self, ref=BRANCH):
        return json.loads(sh(self.repo, "show", f"{ref}:{PLUGIN}"))["version"]

    def reserved(self):
        return [row["values"] for row in self.rows
                if row["kind"] == "reserve"
                and row["what"] == "plugin-version"]


class TestBumpJudgedOnTheCommit(RetryCase):
    def test_a_bump_written_but_not_committed_is_committed(self):
        self.item({"skills/x/SKILL.md": "x\n"})
        write(self.wt, {PLUGIN: plugin("0.7.4")})
        self.assertEqual(merge.bump_version(self.git, self.tool(), self.wt,
                                            BRANCH), "0.7.4")
        self.assertEqual(self.version(), "0.7.4")
        self.assertEqual(sh(self.repo, "show", "--name-only", "--format=",
                            BRANCH).split(), [PLUGIN,
                                              "factory/manifest.json"])
        self.assertEqual(sh(self.wt, "status", "--porcelain"), "")

    def test_a_committed_bump_is_not_bumped_again(self):
        self.item({"skills/x/SKILL.md": "x\n"})
        merge.bump_version(self.git, self.tool(), self.wt, BRANCH)
        head = self.head()
        self.assertIsNone(merge.bump_version(self.git, self.tool(),
                                             self.wt, BRANCH))
        self.assertEqual(self.head(), head)

    def test_a_retry_after_a_failed_regeneration_commits_the_bump(self):
        self.item({"skills/x/SKILL.md": "x\n"})
        summary, problems = self.turn(
            SHIPPED, tool=self.tool(fail="update-manifest"))
        self.assertEqual(problems, [])
        self.assertEqual(summary["stall"], "regenerating the manifest"
                         " failed: make: *** [check] Error 1")
        summary, problems = self.retry()
        self.assertEqual((problems, summary["stall"]), ([], None))
        self.assertEqual(self.version("origin/" + BRANCH), "0.7.4")
        self.assertTrue(self.calls("tool", "update-manifest"))
        self.assertEqual(sh(self.wt, "status", "--porcelain"), "")
        self.assertEqual(self.reserved(), [["0.7.4"]])


class TestPluginVersionConflict(RetryCase):
    def committed_bump_then_main_moves(self, item_plugin=None,
                                       main_plugin=None):
        """The first turn commits its 0.7.4 bump and pushes, then stalls
        on a red check; another merge lands 0.7.5 on main."""
        files = {"skills/x/SKILL.md": "x\n"}
        if item_plugin is not None:
            files[PLUGIN] = item_plugin
        self.item(files)
        summary, problems = self.turn(
            SHIPPED, gh=self.fake_gh(checks=([RED_RUN],)))
        self.assertEqual(problems, [])
        self.assertTrue(summary["stall"].startswith("checks failed"))
        self.assertEqual(self.version(), "0.7.4")
        self.main_moves({PLUGIN: main_plugin or plugin("0.7.5"),
                         "factory/manifest.json": '{"files": "main"}\n'})

    def test_a_version_moved_on_main_is_rebumped_from_main(self):
        self.committed_bump_then_main_moves()
        summary, problems = self.retry()
        self.assertEqual((problems, summary["stall"]), ([], None))
        self.assertEqual(self.version("origin/" + BRANCH), "0.7.6")
        self.assertEqual(sh(self.repo, "show", f"{BRANCH}:factory/"
                            "manifest.json"), '{"files": "regenerated"}\n')
        self.assertEqual(self.reserved(), [["0.7.4"], ["0.7.6"]])
        sh(self.repo, "merge-base", "--is-ancestor", "origin/main", BRANCH)

    def test_the_items_other_plugin_edits_are_kept(self):
        self.committed_bump_then_main_moves(
            item_plugin=plugin("0.7.3", description="the item's"))
        summary, problems = self.retry()
        self.assertEqual((problems, summary["stall"]), ([], None))
        self.assertEqual(sh(self.repo, "show", f"{BRANCH}:{PLUGIN}"),
                         plugin("0.7.6", description="the item's"))

    def test_mains_other_plugin_edits_are_kept(self):
        self.committed_bump_then_main_moves(
            main_plugin=plugin("0.7.5", description="main's"))
        summary, problems = self.retry()
        self.assertEqual((problems, summary["stall"]), ([], None))
        self.assertEqual(sh(self.repo, "show", f"{BRANCH}:{PLUGIN}"),
                         plugin("0.7.6", description="main's"))

    def test_a_conflict_beyond_the_version_line_stalls(self):
        self.committed_bump_then_main_moves(
            item_plugin=plugin("0.7.3", name="item"),
            main_plugin=plugin("0.7.5", name="main"))
        head = self.head()
        summary, problems = self.retry()
        self.assertEqual(problems, [])
        self.assertEqual(summary["stall"], f"merging origin/main into"
                         f" {BRANCH} conflicts in {PLUGIN},"
                         " factory/manifest.json")
        self.assertEqual(self.head(), head)
        self.assertFalse((self.repo / ".git/worktrees/conductor-b1-12/"
                          "MERGE_HEAD").exists())

    def test_a_consumer_repo_stalls_on_a_plugin_conflict(self):
        sh(self.wt, "rm", "-q", "tools/factory_init.py")
        self.item({PLUGIN: plugin("0.8.0")})
        self.main_moves({PLUGIN: plugin("0.7.5")})
        summary, problems = self.turn(SHIPPED)
        self.assertEqual(problems, [])
        self.assertEqual(summary["stall"], f"merging origin/main into"
                         f" {BRANCH} conflicts in {PLUGIN}")


if __name__ == "__main__":
    unittest.main()
