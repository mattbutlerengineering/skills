"""reap_worktrees.py — every case runs through `main` with a fake command
runner over a temp directory tree; no network, no real git worktrees."""
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout

import reap_worktrees

TIP = "a" * 40
OTHER = "b" * 40


def proc(out="", rc=0, err=""):
    return subprocess.CompletedProcess([], rc, out, err)


class Fake:
    """Routes a command to a canned result by a (binary, subcommand
    keyword) match; records every argv. `over` maps a key to a result or
    an exception to raise."""

    def __init__(self, listing, over=None, merged=None):
        self.listing = listing
        self.over = over or {}
        self.merged = merged if merged is not None else [{"headRefOid": TIP}]
        self.calls = []

    def key(self, a):
        if a[0] == "lsof":
            return "lsof"
        if a[0] == "gh":
            return "gh-open" if "open" in a else "gh-merged"
        if "status" in a:
            return "status"
        if "fetch" in a:
            return "fetch"
        if "list" in a:
            return "list"
        if "merge-base" in a:
            return "merge-base"
        if "remove" in a:
            return "remove"
        if "-D" in a:
            return "branch-D"
        raise AssertionError(a)

    def __call__(self, args, cwd=None):
        self.calls.append(list(args))
        k = self.key(args)
        if k in self.over:
            r = self.over[k]
            if isinstance(r, Exception):
                raise r
            return r
        return {"list": proc(self.listing),
                "gh-merged": proc(json.dumps(self.merged))}.get(k, proc())

    def ran(self, key):
        return [c for c in self.calls if self.key(c) == key]


class Case(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = os.path.realpath(tmp.name)
        self.wt = os.path.join(self.repo, ".claude", "worktrees", "agent-1")
        self.out_wt = os.path.join(self.repo + "-wt-other")
        for p in (self.wt, self.out_wt):
            os.makedirs(p)
        with open(os.path.join(self.wt, "f"), "w") as f:
            f.write("x" * 100)

    def listing(self, branch="refs/heads/work", tip=TIP, extra=True):
        text = f"worktree {self.repo}\nHEAD {OTHER}\nbranch refs/heads/main\n\n"
        text += f"worktree {self.wt}\nHEAD {tip}\n"
        text += f"branch {branch}\n\n" if branch else "detached\n\n"
        if extra:
            text += (f"worktree {self.out_wt}\nHEAD {tip}\n"
                     "branch refs/heads/main\n\n")
        return text

    def go(self, fake, apply=True):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = reap_worktrees.main(
                ["--apply"] if apply else [], runner=fake, cwd=self.repo,
                size=lambda p: 100, which=lambda b: "/usr/sbin/lsof")
        return code, buf.getvalue()

    def removed(self, fake):
        return bool(fake.ran("remove"))


class Passing(Case):
    def test_apply_removes_and_deletes_branch(self):
        fake = Fake(self.listing())
        code, out = self.go(fake)
        self.assertEqual(code, 0)
        self.assertEqual(fake.ran("remove"),
                         [["git", "worktree", "remove", self.wt]])
        self.assertEqual(fake.ran("branch-D"),
                         [["git", "branch", "-D", "work"]])
        self.assertIn(f"reap: removed {self.wt} (100 B, branch work deleted)",
                      out)
        self.assertIn("reap: removed 1, kept 0, freed 100 B (100 bytes)", out)
        self.assertTrue(out.endswith("reap: 0 problem(s)\n"))

    def test_fetch_runs_first_with_prune(self):
        fake = Fake(self.listing())
        self.go(fake)
        self.assertEqual(fake.calls[0],
                         ["git", "-C", self.repo, "fetch", "origin", "--prune"])

    def test_dry_run_removes_nothing(self):
        fake = Fake(self.listing())
        code, out = self.go(fake, apply=False)
        self.assertEqual(code, 0)
        self.assertFalse(fake.ran("remove"))
        self.assertFalse(fake.ran("branch-D"))
        self.assertIn(f"reap: would-remove {self.wt} (100 B)", out)
        self.assertIn("would remove 1, kept 0, would free 100 B", out)

    def test_never_forces(self):
        fake = Fake(self.listing())
        self.go(fake)
        self.assertTrue(all("--force" not in c and "-f" not in c
                            for c in fake.calls))

    def test_main_branch_is_never_deleted(self):
        fake = Fake(self.listing(branch="refs/heads/main"))
        self.go(fake)
        self.assertTrue(fake.ran("remove"))
        self.assertFalse(fake.ran("branch-D"))

    def test_detached_skips_pr_test_and_deletes_no_branch(self):
        fake = Fake(self.listing(branch=None),
                    over={"merge-base": proc()})
        code, out = self.go(fake)
        self.assertEqual(code, 0)
        self.assertFalse(fake.ran("gh-open"))
        self.assertFalse(fake.ran("gh-merged"))
        self.assertTrue(fake.ran("remove"))
        self.assertFalse(fake.ran("branch-D"))

    def test_ancestor_of_origin_main_is_merged_evidence(self):
        fake = Fake(self.listing(), merged=[])
        code, _ = self.go(fake)
        self.assertEqual(code, 0)
        self.assertEqual(fake.ran("merge-base")[0][-3:],
                         ["--is-ancestor", TIP, "origin/main"])
        self.assertTrue(fake.ran("remove"))

    def test_branch_delete_failure_is_a_problem(self):
        fake = Fake(self.listing(), over={"branch-D": proc(rc=1, err="boom")})
        code, out = self.go(fake)
        self.assertEqual(code, 1)
        self.assertIn(f"reap: {self.wt}: branch work not deleted: "
                      "`git branch -D work` exited 1: boom", out)


class Scope(Case):
    def test_out_of_scope_listed_not_reaped(self):
        fake = Fake(self.listing())
        _, out = self.go(fake)
        self.assertIn(f"reap: skip {self.out_wt} "
                      f"(outside .claude/worktrees, 100 B)", out)
        self.assertEqual(len(fake.ran("remove")), 1)
        self.assertNotIn(self.out_wt, " ".join(sum(fake.calls, [])))

    def test_main_checkout_is_never_touched(self):
        fake = Fake(self.listing(extra=False))
        self.go(fake)
        self.assertEqual(fake.ran("remove"),
                         [["git", "worktree", "remove", self.wt]])

    def test_sibling_prefix_is_not_in_scope(self):
        sib = os.path.join(self.repo, ".claude", "worktrees-old", "x")
        os.makedirs(sib)
        text = self.listing(extra=False) + (
            f"worktree {sib}\nHEAD {TIP}\nbranch refs/heads/z\n\n")
        fake = Fake(text)
        _, out = self.go(fake)
        self.assertIn(f"reap: skip {sib}", out)
        self.assertEqual(len(fake.ran("remove")), 1)

    def test_checkout_the_run_is_in_is_kept(self):
        fake = Fake(self.listing())
        buf = io.StringIO()
        with redirect_stdout(buf):
            reap_worktrees.main(["--apply"], runner=fake, cwd=self.wt,
                                size=lambda p: 1, which=lambda b: "x")
        self.assertFalse(fake.ran("remove"))
        self.assertIn("(the checkout this run is in)", buf.getvalue())


class FailsClosed(Case):
    def keep(self, fake, reason, problem=None):
        code, out = self.go(fake)
        self.assertFalse(self.removed(fake))
        self.assertFalse(fake.ran("branch-D"))
        self.assertIn(f"reap: keep {self.wt} ({reason})", out)
        if problem:
            self.assertEqual(code, 1)
            self.assertIn(f"reap: {self.wt}: {problem}", out)
        else:
            self.assertEqual(code, 0)
        return out

    def test_dirty_tree(self):
        self.keep(Fake(self.listing(), over={"status": proc(" M x\n")}),
                  "dirty: uncommitted changes")

    def test_status_command_failure(self):
        r = "`git -C %s status --porcelain` exited 128: fatal" % self.wt
        self.keep(Fake(self.listing(),
                       over={"status": proc(rc=128, err="fatal")}), r, r)

    def test_busy_directory(self):
        self.keep(Fake(self.listing(), over={"lsof": proc("COMMAND\n")}),
                  "busy: open files under the path")

    def test_lsof_stderr_is_failure_even_with_exit_one(self):
        r = "lsof wrote to stderr: lsof: status error"
        self.keep(Fake(self.listing(),
                       over={"lsof": proc(rc=1, err="lsof: status error\n")}),
                  r, r)

    def test_lsof_missing_binary(self):
        fake = Fake(self.listing(), over={"lsof": FileNotFoundError("lsof")})
        code, out = self.go(fake)
        self.assertEqual(code, 1)
        self.assertFalse(self.removed(fake))
        self.assertIn("lsof could not run", out)

    def test_lsof_not_on_path(self):
        fake = Fake(self.listing())
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = reap_worktrees.main(["--apply"], runner=fake, cwd=self.repo,
                                       size=lambda p: 1, which=lambda b: None)
        self.assertEqual(code, 1)
        self.assertFalse(fake.ran("lsof"))
        self.assertIn("lsof not on PATH", buf.getvalue())

    def test_missing_path(self):
        os.remove(os.path.join(self.wt, "f"))
        os.rmdir(self.wt)
        fake = Fake(self.listing())
        code, out = self.go(fake)
        self.assertEqual(code, 1)
        self.assertFalse(self.removed(fake))
        self.assertIn("path does not exist", out)

    def test_open_pr(self):
        self.keep(Fake(self.listing(), over={"gh-open": proc("#1 x\n")}),
                  "open PR for branch")

    def test_failed_gh_open_call(self):
        r = ("`gh pr list --head work --state open` exited 1: "
             "HTTP 502")
        self.keep(Fake(self.listing(),
                       over={"gh-open": proc(rc=1, err="HTTP 502")}), r, r)

    def test_gh_missing(self):
        fake = Fake(self.listing(), over={"gh-open": FileNotFoundError("gh")})
        code, out = self.go(fake)
        self.assertEqual(code, 1)
        self.assertFalse(self.removed(fake))
        self.assertIn("gh could not run", out)

    def test_gh_stderr_notice_alone_is_not_an_open_pr(self):
        fake = Fake(self.listing(),
                    over={"gh-open": proc("", 0, "no pull requests match")})
        code, _ = self.go(fake)
        self.assertEqual(code, 0)
        self.assertTrue(self.removed(fake))

    def test_unmerged_tip(self):
        self.keep(Fake(self.listing(), merged=[],
                       over={"merge-base": proc(rc=1)}),
                  "tip not merged: no merged PR carries it and it is not on "
                  "origin/main")

    def test_merged_pr_with_different_head_oid(self):
        fake = Fake(self.listing(), merged=[{"headRefOid": OTHER}],
                    over={"merge-base": proc(rc=1)})
        self.keep(fake, "tip not merged: no merged PR carries it and it is "
                        "not on origin/main")

    def test_failed_gh_merged_call(self):
        r = ("`gh pr list --head work --base main --state merged --json "
             "headRefOid` exited 1: nope")
        self.keep(Fake(self.listing(),
                       over={"gh-merged": proc(rc=1, err="nope")}), r, r)

    def test_gh_merged_garbage_json(self):
        r = "gh merged-PR list was not the expected JSON"
        self.keep(Fake(self.listing(), over={"gh-merged": proc("<html>")}),
                  r, r)

    def test_merge_base_error_is_failure_not_unmerged_or_pass(self):
        fake = Fake(self.listing(), merged=[],
                    over={"merge-base": proc(rc=128, err="bad object")})
        code, out = self.go(fake)
        self.assertEqual(code, 1)
        self.assertFalse(self.removed(fake))
        self.assertIn("exited 128: bad object", out)

    def test_remove_failure_keeps_branch(self):
        fake = Fake(self.listing(), over={"remove": proc(rc=1, err="locked")})
        code, out = self.go(fake)
        self.assertEqual(code, 1)
        self.assertFalse(fake.ran("branch-D"))
        self.assertIn("remove failed", out)

    def test_one_failure_does_not_block_the_others(self):
        second = os.path.join(self.repo, ".claude", "worktrees", "agent-2")
        os.makedirs(second)
        text = self.listing(extra=False) + (
            f"worktree {second}\nHEAD {TIP}\nbranch refs/heads/two\n\n")

        class Mixed(Fake):
            def __call__(s, args, cwd=None):
                if "status" in args and self.wt in args:
                    return proc(" M x\n")
                return super().__call__(args, cwd)
        fake = Mixed(text)
        code, _ = self.go(fake)
        self.assertEqual(code, 0)
        self.assertEqual(fake.ran("remove"),
                         [["git", "worktree", "remove", second]])


class FetchAndUsage(Case):
    def test_failed_fetch_removes_nothing(self):
        fake = Fake(self.listing(),
                    over={"fetch": proc(rc=1, err="network down")})
        code, out = self.go(fake)
        self.assertEqual(code, 1)
        self.assertEqual(len(fake.calls), 1)
        self.assertIn("reap: git fetch origin --prune failed, nothing "
                      "removed: `git fetch` exited 1: network down", out)

    def test_fetch_that_cannot_run_removes_nothing(self):
        fake = Fake(self.listing(), over={"fetch": OSError("no git")})
        code, _ = self.go(fake)
        self.assertEqual(code, 1)
        self.assertFalse(self.removed(fake))

    def test_failed_listing(self):
        fake = Fake(self.listing(), over={"list": proc(rc=128, err="x")})
        code, out = self.go(fake)
        self.assertEqual(code, 1)
        self.assertIn("reap: cannot list worktrees", out)

    def test_bad_usage(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(reap_worktrees.main(["--force"]), 2)
        self.assertIn("usage:", buf.getvalue())


class Helpers(unittest.TestCase):
    def test_parse_worktrees(self):
        text = ("worktree /r\nHEAD 1\nbranch refs/heads/main\n\n"
                "worktree /r/.claude/worktrees/a\nHEAD 2\ndetached\n")
        self.assertEqual(reap_worktrees.parse_worktrees(text), [
            {"path": "/r", "head": "1", "branch": "main"},
            {"path": "/r/.claude/worktrees/a", "head": "2", "branch": None}])

    def test_human(self):
        self.assertEqual(reap_worktrees.human(512), "512 B")
        self.assertEqual(reap_worktrees.human(1536), "1.5 KB")
        self.assertEqual(reap_worktrees.human(3 * 1024 ** 3), "3.0 GB")


if __name__ == "__main__":
    unittest.main()
