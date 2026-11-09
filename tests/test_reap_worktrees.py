"""reap_worktrees.py — every case runs through `main` with a fake command
runner over a temp directory tree; no network, no real git worktrees."""
import io
import json
import os
import subprocess
import tempfile
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import reap_worktrees

# selective package-style runs need tests/ on sys.path for git_repo
sys.path.insert(0, str(Path(__file__).resolve().parent))
import git_repo  # noqa: E402

TIP = "a" * 40
OTHER = "b" * 40


def proc(out="", rc=0, err=""):
    return subprocess.CompletedProcess([], rc, out, err)


def z(repo, head, branch, *more):
    """`git worktree list --porcelain -z` text: the main checkout first,
    then (path, head, branch-or-None) per extra worktree."""
    out = ""
    for path, tip, ref in ((repo, head, branch),) + more:
        out += f"worktree {path}\0HEAD {tip}\0"
        out += f"branch {ref}\0\0" if ref else "detached\0\0"
    return out


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
        if "ls-files" in a:
            return "ls-files"
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
        return z(self.repo, OTHER, "refs/heads/main",
                 *([(self.wt, tip, branch)]
                   + ([(self.out_wt, tip, "refs/heads/main")] if extra
                      else [])))

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
                         [["git", "branch", "-D", "--", "work"]])
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
        self.assertNotIn(["git", "branch", "-D", "--", "main"], fake.calls)

    def test_status_overrides_repo_config_that_hides_files(self):
        fake = Fake(self.listing())
        self.go(fake)
        self.assertEqual(fake.ran("status"), [[
            "git", "-C", self.wt, "status", "--porcelain",
            "--untracked-files=all", "--ignore-submodules=none"]])

    def test_locked_worktree_is_kept_in_dry_run_and_apply(self):
        text = self.listing(extra=False).replace(
            "branch refs/heads/work\0\0", "branch refs/heads/work\0locked\0\0")
        for apply in (False, True):
            with self.subTest(apply=apply):
                fake = Fake(text)
                code, out = self.go(fake, apply=apply)
                self.assertEqual(code, 0)
                self.assertIn(f"reap: keep {self.wt} (locked)", out)
                self.assertNotIn("would-remove", out)
                self.assertFalse(fake.ran("remove"))
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
                         ["--is-ancestor", TIP, "refs/remotes/origin/main"])
        self.assertTrue(fake.ran("remove"))

    def test_merge_base_names_the_full_remote_ref(self):
        fake = Fake(self.listing(), merged=[])
        self.go(fake)
        self.assertEqual(fake.ran("merge-base"), [
            ["git", "merge-base", "--is-ancestor", TIP,
             "refs/remotes/origin/main"]])

    def test_list_is_nul_separated(self):
        fake = Fake(self.listing())
        self.go(fake)
        self.assertEqual(fake.ran("list"), [
            ["git", "-C", self.repo, "worktree", "list", "--porcelain", "-z"]])

    def test_branch_delete_failure_is_a_problem(self):
        fake = Fake(self.listing(), over={"branch-D": proc(rc=1, err="boom")})
        code, out = self.go(fake)
        self.assertEqual(code, 1)
        self.assertIn(f"reap: {self.wt}: branch work not deleted: "
                      "`git branch -D -- work` exited 1: boom", out)


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
        text = self.listing(extra=False) + z(
            self.repo, OTHER, None, (sib, TIP, "refs/heads/z"))[
                len(f"worktree {self.repo}\0HEAD {OTHER}\0detached\0\0"):]
        fake = Fake(text)
        _, out = self.go(fake)
        self.assertIn(f"reap: skip {sib}", out)
        self.assertEqual(len(fake.ran("remove")), 1)

    def test_symlinked_scope_root_is_resolved(self):
        real = os.path.join(self.repo + "-store")
        os.makedirs(os.path.join(real, "agent-1"))
        os.rename(os.path.join(self.repo, ".claude", "worktrees"),
                  os.path.join(self.repo, "gone"))
        os.symlink(real, os.path.join(self.repo, ".claude", "worktrees"))
        fake = Fake(self.listing(extra=False))
        _, out = self.go(fake)
        self.assertTrue(fake.ran("remove"), out)

    def test_symlink_pointing_out_of_scope_is_not_reaped(self):
        target = os.path.join(self.repo + "-elsewhere")
        os.makedirs(target)
        link = os.path.join(self.repo, ".claude", "worktrees", "agent-link")
        os.symlink(target, link)
        text = self.listing(extra=False) + z(
            self.repo, OTHER, None, (link, TIP, "refs/heads/l"))[
                len(f"worktree {self.repo}\0HEAD {OTHER}\0detached\0\0"):]
        fake = Fake(text)
        _, out = self.go(fake)
        self.assertEqual(len(fake.ran("remove")), 1)
        self.assertIn(f"reap: skip {link}", out)

    def test_duplicate_realpath_is_judged_once(self):
        link = os.path.join(self.repo + "-alias")
        os.symlink(self.wt, link)
        text = self.listing(extra=False) + z(
            self.repo, OTHER, None, (link, TIP, "refs/heads/work"))[
                len(f"worktree {self.repo}\0HEAD {OTHER}\0detached\0\0"):]
        fake = Fake(text)
        _, out = self.go(fake)
        self.assertEqual(len(fake.ran("remove")), 1)
        self.assertEqual(out.count("removed"), 2)  # one line + summary

    def test_path_with_newline_is_handled_and_one_line(self):
        odd = os.path.join(self.repo, ".claude", "worktrees", "a\nb")
        os.makedirs(odd)
        text = z(self.repo, OTHER, "refs/heads/main",
                 (odd, TIP, "refs/heads/odd"))
        fake = Fake(text)
        code, out = self.go(fake)
        self.assertEqual(code, 0)
        self.assertEqual(fake.ran("remove"), [["git", "worktree", "remove", odd]])
        self.assertIn(f"reap: removed {odd.replace(chr(10), chr(92) + 'n')} (", out)
        self.assertTrue(all(l.startswith("reap:") for l in out.splitlines()))

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
        r = ("`git -C %s status --porcelain --untracked-files=all "
             "--ignore-submodules=none` exited 128: fatal" % self.wt)
        self.keep(Fake(self.listing(),
                       over={"status": proc(rc=128, err="fatal")}), r, r)

    def test_hidden_index_flags_are_dirty(self):
        for tag in ("h", "S", "s", "x"):
            with self.subTest(tag=tag):
                fake = Fake(self.listing(), over={
                    "ls-files": proc(f"H a\0{tag} f\0")})
                self.keep(fake, "dirty (hidden index flags)")

    def test_normal_index_tags_are_clean(self):
        fake = Fake(self.listing(), over={"ls-files": proc("H a\0M b\0")})
        code, _ = self.go(fake)
        self.assertEqual(code, 0)
        self.assertTrue(self.removed(fake))

    def test_failed_ls_files_fails_closed(self):
        r = (f"`git -C {self.wt} ls-files -v -z` exited 128: bad")
        self.keep(Fake(self.listing(),
                       over={"ls-files": proc(rc=128, err="bad")}), r, r)

    def test_worktree_containing_another_is_kept(self):
        inner = os.path.join(self.wt, ".claude", "worktrees", "B")
        os.makedirs(inner)
        text = self.listing(extra=False) + z(
            self.repo, OTHER, None, (inner, TIP, "refs/heads/inner"))[
                len(f"worktree {self.repo}\0HEAD {OTHER}\0detached\0\0"):]
        fake = Fake(text)
        for apply in (False, True):
            code, out = self.go(fake, apply=apply)
            self.assertIn(
                f"reap: keep {self.wt} (contains worktree {inner})", out)
        self.assertEqual(code, 0)
        self.assertNotIn(["git", "worktree", "remove", self.wt], fake.calls)

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
                  "refs/remotes/origin/main")

    def test_merged_pr_with_different_head_oid(self):
        fake = Fake(self.listing(), merged=[{"headRefOid": OTHER}],
                    over={"merge-base": proc(rc=1)})
        self.keep(fake, "tip not merged: no merged PR carries it and it is "
                        "not on refs/remotes/origin/main")

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
        text = self.listing(extra=False) + z(
            self.repo, OTHER, None, (second, TIP, "refs/heads/two"))[
                len(f"worktree {self.repo}\0HEAD {OTHER}\0detached\0\0"):]

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

    def test_no_fetch_dry_run_never_fetches_or_removes(self):
        fake = Fake(self.listing())
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = reap_worktrees.main(
                ["--no-fetch"], runner=fake, cwd=self.repo,
                size=lambda p: 1, which=lambda b: "x")
        self.assertEqual(code, 0)
        self.assertFalse(fake.ran("fetch"))
        self.assertFalse(fake.ran("remove"))
        self.assertIn("would-remove", buf.getvalue())

    def test_apply_with_no_fetch_is_refused(self):
        fake = Fake(self.listing())
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = reap_worktrees.main(["--apply", "--no-fetch"], runner=fake,
                                       cwd=self.repo)
        self.assertEqual(code, 2)
        self.assertEqual(fake.calls, [])

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


class RealGit(unittest.TestCase):
    """A real temp repo: git is real, gh and lsof report nothing."""

    def git(self, *args, cwd):
        subprocess.run(["git", *args], cwd=cwd, check=True,
                       capture_output=True, env={
                           **os.environ, "GIT_AUTHOR_NAME": "t",
                           "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                           "GIT_COMMITTER_EMAIL": "t@t"})

    def runner(self, args, cwd=None):
        if args[0] == "gh":
            return proc("[]" if "--json" in args else "")
        if args[0] == "lsof":
            return proc()
        return subprocess.run(args, capture_output=True, text=True, cwd=cwd)

    def test_local_branch_or_tag_named_origin_main_cannot_stand_in(self):
        for kind in ("branch", "tag"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as t:
                t = os.path.realpath(t)
                origin, repo = os.path.join(t, "o.git"), os.path.join(t, "r")
                git_repo.init(origin, "--bare", "-b", "main")
                git_repo.clone(origin, repo)
                self.git("commit", "-q", "--allow-empty", "-m", "base",
                         cwd=repo)
                self.git("push", "-q", "origin", "HEAD:main", cwd=repo)
                wt = os.path.join(repo, ".claude", "worktrees", "w")
                self.git("worktree", "add", "-q", "-b", "work", wt, cwd=repo)
                self.git("commit", "-q", "--allow-empty", "-m", "unmerged",
                         cwd=wt)
                if kind == "branch":
                    self.git("branch", "origin/main", "work", cwd=repo)
                else:
                    self.git("tag", "origin/main", "work", cwd=repo)
                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = reap_worktrees.main(
                        ["--apply"], runner=self.runner, cwd=repo,
                        size=lambda p: 1, which=lambda b: "x")
                self.assertEqual(code, 0, buf.getvalue())
                self.assertIn("tip not merged", buf.getvalue())
                self.assertTrue(os.path.isdir(wt))

    def test_untracked_file_is_dirty_even_when_config_hides_it(self):
        with tempfile.TemporaryDirectory() as t:
            t = os.path.realpath(t)
            origin, repo = os.path.join(t, "o.git"), os.path.join(t, "r")
            git_repo.init(origin, "--bare", "-b", "main")
            git_repo.clone(origin, repo)
            self.git("commit", "-q", "--allow-empty", "-m", "base", cwd=repo)
            wt = os.path.join(repo, ".claude", "worktrees", "w")
            self.git("worktree", "add", "-q", "-b", "work", wt, cwd=repo)
            self.git("commit", "-q", "--allow-empty", "-m", "done", cwd=wt)
            self.git("push", "-q", "origin", "work:main", cwd=wt)
            self.git("config", "status.showUntrackedFiles", "no", cwd=repo)
            with open(os.path.join(wt, "scratch.txt"), "w") as f:
                f.write("unsaved")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = reap_worktrees.main(
                    ["--apply"], runner=self.runner, cwd=repo,
                    size=lambda p: 1, which=lambda b: "x")
            self.assertEqual(code, 0, buf.getvalue())
            self.assertIn("dirty: uncommitted changes", buf.getvalue())
            self.assertTrue(os.path.exists(os.path.join(wt, "scratch.txt")))

    def merged_worktree(self, t, name="w"):
        origin, repo = os.path.join(t, "o.git"), os.path.join(t, "r")
        git_repo.init(origin, "--bare", "-b", "main")
        git_repo.clone(origin, repo)
        with open(os.path.join(repo, "tracked.txt"), "w") as f:
            f.write("one\n")
        self.git("add", "tracked.txt", cwd=repo)
        self.git("commit", "-q", "-m", "base", cwd=repo)
        wt = os.path.join(repo, ".claude", "worktrees", name)
        self.git("worktree", "add", "-q", "-b", name, wt, cwd=repo)
        self.git("push", "-q", "origin", f"{name}:main", cwd=wt)
        return repo, wt

    def reap(self, repo):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = reap_worktrees.main(
                ["--apply"], runner=self.runner, cwd=repo,
                size=lambda p: 1, which=lambda b: "x")
        return code, buf.getvalue()

    def test_hidden_index_flags_keep_the_worktree(self):
        for flag in ("--assume-unchanged", "--skip-worktree"):
            with self.subTest(flag=flag), tempfile.TemporaryDirectory() as t:
                repo, wt = self.merged_worktree(os.path.realpath(t))
                self.git("update-index", flag, "tracked.txt", cwd=wt)
                with open(os.path.join(wt, "tracked.txt"), "w") as f:
                    f.write("edited\n")
                code, out = self.reap(repo)
                self.assertEqual(code, 0, out)
                self.assertIn("dirty (hidden index flags)", out)
                self.assertTrue(os.path.isdir(wt))

    def test_nested_worktree_survives_reaping_its_outer(self):
        with tempfile.TemporaryDirectory() as t:
            repo, outer = self.merged_worktree(os.path.realpath(t), "A")
            inner = os.path.join(outer, ".claude", "worktrees", "B")
            self.git("worktree", "add", "-q", "-b", "B", inner, cwd=outer)
            self.git("commit", "-q", "--allow-empty", "-m", "unpushed",
                     cwd=inner)
            scratch = os.path.join(inner, "scratch.txt")
            with open(scratch, "w") as f:
                f.write("unsaved")
            code, out = self.reap(repo)
            self.assertEqual(code, 0, out)
            self.assertIn(f"contains worktree {inner}", out)
            self.assertTrue(os.path.exists(scratch))
            self.assertTrue(os.path.isdir(outer))

    def test_nested_worktree_under_a_case_variant_path_survives(self):
        with tempfile.TemporaryDirectory() as t:
            t = os.path.realpath(t)
            probe = os.path.join(t, "Probe")
            os.mkdir(probe)
            if not os.path.exists(os.path.join(t, "pROBE")):
                self.skipTest("case-sensitive filesystem")
            repo, outer = self.merged_worktree(t, "outer")
            # As in the real repo, the nested worktree dir is ignored, so
            # the outer reads clean and only the nesting guard keeps it.
            with open(os.path.join(repo, ".git", "info", "exclude"), "a") as f:
                f.write(".claude/worktrees/\n")
            variant = os.path.join(repo, ".claude", "worktrees", "OUTER")
            inner = os.path.join(variant, ".claude", "worktrees", "inner")
            self.git("worktree", "add", "-q", "-b", "inner", inner, cwd=outer)
            self.git("commit", "-q", "--allow-empty", "-m", "unpushed",
                     cwd=inner)
            scratch = os.path.join(inner, "scratch.txt")
            with open(scratch, "w") as f:
                f.write("unsaved")
            code, out = self.reap(repo)
            self.assertEqual(code, 0, out)
            self.assertIn("contains worktree", out)
            self.assertTrue(os.path.exists(scratch))
            self.assertTrue(os.path.isdir(outer))

    def test_sparse_worktree_with_absent_skip_files_is_reaped(self):
        with tempfile.TemporaryDirectory() as t:
            repo, wt = self.merged_worktree(os.path.realpath(t))
            for d in ("keep", "other"):
                os.mkdir(os.path.join(wt, d))
                with open(os.path.join(wt, d, "f.txt"), "w") as f:
                    f.write("x\n")
            self.git("add", ".", cwd=wt)
            self.git("commit", "-q", "-m", "dirs", cwd=wt)
            self.git("push", "-q", "origin", "w:main", cwd=wt)
            self.git("sparse-checkout", "set", "keep", cwd=wt)
            self.assertFalse(os.path.exists(os.path.join(wt, "other")))
            code, out = self.reap(repo)
            self.assertEqual(code, 0, out)
            self.assertNotIn("hidden index flags", out)
            self.assertFalse(os.path.exists(wt))

    def test_skip_worktree_flag_on_a_present_file_keeps_the_worktree(self):
        # No sparse-checkout: the flag is set by hand, so status stays
        # silent about the edit and only the index-flag check sees it.
        with tempfile.TemporaryDirectory() as t:
            repo, wt = self.merged_worktree(os.path.realpath(t))
            self.git("update-index", "--skip-worktree", "tracked.txt", cwd=wt)
            with open(os.path.join(wt, "tracked.txt"), "w") as f:
                f.write("edited\n")
            code, out = self.reap(repo)
            self.assertEqual(code, 0, out)
            self.assertIn("dirty (hidden index flags)", out)
            self.assertTrue(os.path.isdir(wt))

    def test_sparse_worktree_keeps_an_edit_to_a_present_cone_file(self):
        # In sparse mode git clears skip-worktree on a present file, so
        # status itself reports the edit.
        with tempfile.TemporaryDirectory() as t:
            repo, wt = self.merged_worktree(os.path.realpath(t))
            os.mkdir(os.path.join(wt, "other"))
            with open(os.path.join(wt, "other", "f.txt"), "w") as f:
                f.write("x\n")
            self.git("add", ".", cwd=wt)
            self.git("commit", "-q", "-m", "dirs", cwd=wt)
            self.git("push", "-q", "origin", "w:main", cwd=wt)
            self.git("sparse-checkout", "set", "keep", cwd=wt)
            os.makedirs(os.path.join(wt, "other"), exist_ok=True)
            with open(os.path.join(wt, "other", "f.txt"), "w") as f:
                f.write("edited\n")
            code, out = self.reap(repo)
            self.assertEqual(code, 0, out)
            self.assertIn("dirty: uncommitted changes", out)
            self.assertTrue(os.path.isdir(wt))

    def test_branch_named_like_an_option_is_deleted(self):
        with tempfile.TemporaryDirectory() as t:
            repo, wt = self.merged_worktree(os.path.realpath(t))
            self.git("update-ref", "refs/heads/-x", "HEAD", cwd=wt)
            self.git("symbolic-ref", "HEAD", "refs/heads/-x", cwd=wt)
            code, out = self.reap(repo)
            self.assertEqual(code, 0, out)
            self.assertIn("branch -x deleted", out)
            self.assertFalse(os.path.exists(wt))
            ref = subprocess.run(
                ["git", "show-ref", "--verify", "--quiet", "refs/heads/-x"],
                cwd=repo)
            self.assertNotEqual(ref.returncode, 0)

    def test_a_truly_merged_tip_is_reaped(self):
        with tempfile.TemporaryDirectory() as t:
            t = os.path.realpath(t)
            origin, repo = os.path.join(t, "o.git"), os.path.join(t, "r")
            git_repo.init(origin, "--bare", "-b", "main")
            git_repo.clone(origin, repo)
            self.git("commit", "-q", "--allow-empty", "-m", "base", cwd=repo)
            wt = os.path.join(repo, ".claude", "worktrees", "w")
            self.git("worktree", "add", "-q", "-b", "work", wt, cwd=repo)
            self.git("commit", "-q", "--allow-empty", "-m", "done", cwd=wt)
            self.git("push", "-q", "origin", "work:main", cwd=wt)
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = reap_worktrees.main(
                    ["--apply"], runner=self.runner, cwd=repo,
                    size=lambda p: 1, which=lambda b: "x")
            self.assertEqual(code, 0, buf.getvalue())
            self.assertFalse(os.path.exists(wt))


class Helpers(unittest.TestCase):
    def test_parse_worktrees_splits_on_nul_and_keeps_newlines(self):
        text = z("/r", "1", "refs/heads/main",
                 ("/r/.claude/worktrees/a\nb", "2", None))
        self.assertEqual(reap_worktrees.parse_worktrees(text), [
            {"path": "/r", "head": "1", "branch": "main", "locked": False},
            {"path": "/r/.claude/worktrees/a\nb", "head": "2",
             "branch": None, "locked": False}])

    def test_parse_records_locked_with_or_without_a_reason(self):
        text = ("worktree /a\0HEAD 1\0detached\0locked\0\0"
                "worktree /b\0HEAD 2\0detached\0locked why\0\0")
        self.assertEqual(
            [w["locked"] for w in reap_worktrees.parse_worktrees(text)],
            [True, True])

    def test_human(self):
        self.assertEqual(reap_worktrees.human(512), "512 B")
        self.assertEqual(reap_worktrees.human(1536), "1.5 KB")
        self.assertEqual(reap_worktrees.human(3 * 1024 ** 3), "3.0 GB")


if __name__ == "__main__":
    unittest.main()
