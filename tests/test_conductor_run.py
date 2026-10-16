"""conductor_run.py (PRD-0013, WO-0158): one metered headless Worker run
per step. Every harness, git and gh call goes through an injected fake —
no model ever runs — and tests assert the EXACT problem strings and rows.
"""
import contextlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from datetime import datetime, timedelta, timezone
from pathlib import Path

import conductor
import conductor_run

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
from fake_gh import FakeGh  # noqa: E402
from fake_git import FakeGit  # noqa: E402
import git_repo  # noqa: E402
from test_conductor_flow import (BUDGET, PLAN, START,  # noqa: E402
                                 answered, failed, launch, moved, ran,
                                 run_id, stall_ask)

LEDGER = "docs/factory/batches/b1/ledger.jsonl"
NOW = datetime(2026, 10, 10, 12, 30, tzinfo=timezone.utc)
POLICY_PLAN = dict(PLAN, policy={
    "routing": {"mechanical": "haiku", "implementation": "sonnet",
                "architecture_review": "fable"},
    "effort": {"mechanical": "low", "implementation": "medium",
               "architecture_review": "high"}})
BASE = [POLICY_PLAN] + START[1:]
RESULT = {"type": "result", "subtype": "success", "is_error": False,
          "total_cost_usd": 1.25,
          "usage": {"input_tokens": 100, "output_tokens": 20},
          "modelUsage": {"m": {}}}


class FakeEvents(list):
    timed_out = False


class Harness:
    """A stand-in for cli.harness_run: records the call, lets `act`
    write files into the Worker's cwd, and yields canned events."""

    def __init__(self, events=(RESULT,), act=None, timed_out=False,
                 missing=False):
        self.events, self.act = list(events), act
        self.timed_out, self.missing = timed_out, missing
        self.calls = []

    @contextlib.contextmanager
    def __call__(self, cmd, cwd, timeout, env=None, spawn=None):
        self.calls.append({"cmd": cmd, "cwd": cwd, "timeout": timeout,
                           "env": env})
        if self.missing:
            raise FileNotFoundError(2, "No such file or directory",
                                    "claude")
        if self.act:
            self.act(Path(cwd))
        events = FakeEvents(self.events)
        events.timed_out = self.timed_out
        yield events


def pr_body(path):
    (path / "pr-body.md").write_text("Body\n")


# The breakdown every item worktree checks out: the order #14 resolves
# through (issue #857), with the Accept line its block carries.
ORDER_ROW = "- [ ] **WO-0180** order — size:S, blocked by: — (tracker: #14)"
BREAKDOWN = f"# Breakdown\n\n{ORDER_ROW}\n  - Accept: the order lands.\n"


def add_worktree(args):
    """A FakeGit answer: `worktree add -b <branch> <path>` makes the
    directory, as git does, checks out the breakdown, and prints
    nothing."""
    Path(args[4], "docs").mkdir(parents=True)
    Path(args[4], "docs", "breakdown.md").write_text(BREAKDOWN)
    return ""


def Git(tmp, changed="", shows=None, failing=None, log="", heads=None,
        pushurls=""):
    """FakeGit over a scratch tree: the main checkout is `tmp`, every
    branch head is c0ffee (or `heads`, a callable answer), `git log`
    prints `log`, the item diff is `changed`, and a ref holds a file only
    when `shows` maps "<ref>:<path>" to its text — so an absent ledger is
    one ls-tree lists nothing for and git show fails on. `pushurls` is
    what `config --get-regexp` prints in any checkout (none: git exits
    1). `failing` is the argv prefix whose call git rejects."""
    shows = shows or {}

    def listed(args):
        return args[-1] + "\n" if f"{args[2]}:{args[-1]}" in shows else ""

    def listed_runs(args):
        ref, path = args[3], args[-1]
        prefix = f"{ref}:{path}/"
        kids = sorted(key[len(ref) + 1:] for key in shows
                      if key.startswith(prefix))
        return "".join(kid + "\n" for kid in kids)

    def in_a_checkout(args):
        return pushurls if "--get-regexp" in args else ""
    return FakeGit({
        ("-C",): in_a_checkout,
        ("rev-parse",): heads or "c0ffee\n",
        ("rev-parse", "--path-format=absolute", "--git-common-dir"):
            f"{Path(tmp) / '.git'}\n",
        ("worktree", "add"): add_worktree, ("log",): log,
        ("diff",): changed, ("ls-tree", "--name-only"): listed,
        ("ls-tree", "-r", "--name-only"): listed_runs,
        # Read at call time: a Worker's commit changes what a ref holds.
        ("show",): lambda args: shows.get(args[-1], "")},
        failing=failing)


def Gh(prs=(), body="Spec this.", title="t", fail=None, state="open"):
    """The one fake gh, answering issue view and pr list; `fail` is the
    argv prefix whose call is rejected with HTTP 422. `state` is what
    `gh issue view --json state` reports; a create is refused when it is
    closed."""
    return FakeGh(
        answers={("issue", "view"): json.dumps({"title": title,
                                                "body": body,
                                                "state": state}),
                 ("pr", "list"): json.dumps([{"number": n} for n in prs])},
        failing=fail,
        error=subprocess.CalledProcessError(1, "gh", stderr="HTTP 422"))


WORKTREE = ".claude/worktrees/conductor-b1-{n}"


class RunCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "conductor"
        self.root.mkdir()
        self.clock = lambda: NOW
        # The launch guard reads a netrc file (re-review R3): the suite
        # never reads the machine's own.
        self.no_netrc = Path(self.tmp.name) / "netrc"
        self.config(300)

    def config(self, cap):
        path = self.root / ".github/factory.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"monthly_cap_usd": cap}))

    def ledger(self, *rows):
        path = self.root / LEDGER
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))

    def run_step(self, item, step, harness, git=None, gh=None, rows=BASE):
        self.ledger(*rows)
        self.git = git or Git(self.tmp.name)
        self.gh = gh or Gh()
        self.harness = harness
        result = conductor_run.run_step(
            self.root, "b1", item, step, self.clock, git=self.git,
            gh=self.gh, harness=harness, pid=777, netrc=self.no_netrc)
        self.rows, _ = conductor.load(self.root, "b1")
        return result

    def worktree(self, item):
        return Path(self.tmp.name) / WORKTREE.format(n=item[1:])

    def spend(self, item):
        runs = self.worktree(item) / "docs/factory/costs/runs"
        rows = []
        if runs.is_dir():
            for path in sorted(runs.glob("*.jsonl")):
                rows.extend(json.loads(line)
                            for line in path.read_text().splitlines()
                            if line.strip())
        return rows


class TestHarnessCommand(unittest.TestCase):
    def test_every_flag_is_composed_in_one_place(self):
        cmd = conductor_run.harness_command("Brief", "sonnet", "medium",
                                            3.0)
        self.assertEqual(cmd[:11], [
            "claude", "-p", "Brief", "--model", "sonnet", "--effort",
            "medium", "--max-budget-usd", "3.00", "--output-format",
            "json"])
        self.assertEqual(cmd[11], "--allowedTools")
        tools = cmd[12:]
        self.assertEqual(tools, list(conductor_run.ALLOWED_TOOLS))
        self.assertFalse([t for t in tools if "push" in t or "gh" in t])

    def test_make_is_narrowed_to_make_check(self):
        # Review major 3: `make wo-failed` and `make wo-merged` write gh
        # labels; a Worker needs only the check target.
        makes = [t for t in conductor_run.ALLOWED_TOOLS if "make" in t]
        self.assertEqual(makes, ["Bash(make check)"])


def sh(cwd, *args, env=None):
    return subprocess.run(["git", "-C", str(cwd), *args], env=env,
                          capture_output=True, text=True)


class TestWorkerEnv(unittest.TestCase):
    """Review major 3: "no push, no gh" is the Worker's environment, not
    a line in its brief. What is enforced is asserted on the env handed
    to the harness, and the push block is run against a real git."""

    OWNER = {"PATH": os.environ.get("PATH", ""), "HOME": "/home/o",
             "GH_TOKEN": "t1", "GITHUB_TOKEN": "t2", "GH_HOST": "h",
             "GH_ENTERPRISE_TOKEN": "t3", "GITHUB_ENTERPRISE_TOKEN": "t4",
             "GH_CONFIG_DIR": "/home/o/.config/gh",
             "GIT_ASKPASS": "/askpass", "SSH_ASKPASS": "/askpass",
             "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "remote.origin"
             ".pushurl", "GIT_CONFIG_VALUE_0": "git@github.com:o/r.git",
             "CLAUDECODE": "1"}

    def env(self, gh_dir="/empty"):
        return conductor_run.worker_env(self.OWNER, "b1", gh_dir)

    def test_no_github_credential_reaches_the_worker(self):
        env = self.env()
        for name in ("GH_TOKEN", "GITHUB_TOKEN", "GH_HOST",
                     "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN",
                     "GIT_ASKPASS", "SSH_ASKPASS", "CLAUDECODE"):
            self.assertNotIn(name, env)
        self.assertEqual(env["GH_CONFIG_DIR"], "/empty")
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(env["CONDUCTOR_WORKER"], "b1")
        self.assertEqual(env["HOME"], "/home/o")

    def test_a_worker_writes_no_bytecode(self):
        # #726: a Worker's gate run in its worktree must not rewrite a
        # tracked __pycache__/*.pyc, or the next merge of main refuses.
        self.assertEqual(self.env()["PYTHONDONTWRITEBYTECODE"], "1")

    def test_the_owners_git_config_entries_are_replaced(self):
        env = self.env()
        count = int(env["GIT_CONFIG_COUNT"])
        pairs = [(env[f"GIT_CONFIG_KEY_{i}"], env[f"GIT_CONFIG_VALUE_{i}"])
                 for i in range(count)]
        rewrite = "url./dev/null/conductor-worker-may-not-push/" \
            ".pushInsteadOf"
        self.assertEqual(pairs, [(rewrite, "https://"),
                                 (rewrite, "http://"),
                                 ("credential.helper", "")])
        self.assertEqual(env["GIT_SSH_COMMAND"], "false")

    def test_a_worker_push_to_any_remote_url_fails(self):
        # No network: an ssh push dies at GIT_SSH_COMMAND, an https one
        # is rewritten to a local path that cannot exist.
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "w"
            git_repo.init(work)
            for key, value in (("user.email", "t@example.com"),
                               ("user.name", "t"),
                               ("commit.gpgsign", "false")):
                sh(work, "config", key, value)
            sh(work, "commit", "-q", "--allow-empty", "-m", "c")
            owner = {k: v for k, v in os.environ.items()
                     if not k.startswith("GIT_")}
            env = conductor_run.worker_env(owner, "b1", tmp)
            for target in ("git@github.com:o/r.git",
                           "ssh://git@github.com/o/r.git", "gh-alias:o/r",
                           "https://github.com/o/r.git",
                           "https://x-access-token:t@github.com/o/r.git",
                           "http://example.com/r.git"):
                pushed = sh(work, "push", target, "HEAD:refs/heads/x",
                            env=env)
                self.assertNotEqual(pushed.returncode, 0, target)
                self.assertTrue(
                    "Could not read from remote repository"
                    in pushed.stderr, (target, pushed.stderr))

    def test_a_configured_pushurl_is_not_rewritten(self):
        # Re-review R3, the limit worker_env leaves: pushInsteadOf skips
        # a remote's explicit pushurl, so git dials it (a closed local
        # port here) with no helper to hand it a token. push_gaps
        # refuses a launch while one is configured.
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "w"
            git_repo.init(work)
            for key, value in (("user.email", "t@example.com"),
                               ("user.name", "t"),
                               ("commit.gpgsign", "false"),
                               ("remote.o.url", "https://127.0.0.1:9/r"),
                               ("remote.o.pushurl",
                                "https://127.0.0.1:9/o/r.git")):
                sh(work, "config", key, value)
            sh(work, "commit", "-q", "--allow-empty", "-m", "c")
            owner = {k: v for k, v in os.environ.items()
                     if not k.startswith("GIT_")}
            env = conductor_run.worker_env(owner, "b1", tmp)
            pushed = sh(work, "push", "o", "HEAD:refs/heads/x", env=env)
            self.assertNotEqual(pushed.returncode, 0)
            self.assertIn("127.0.0.1", pushed.stderr)
            self.assertNotIn("conductor-worker-may-not-push",
                             pushed.stderr)

    def test_a_make_check_push_to_a_local_repo_still_works(self):
        # The suite's merge-turn tests push to a local bare origin; the
        # Worker's `make check` must still pass them.
        with tempfile.TemporaryDirectory() as tmp:
            origin, work = Path(tmp) / "origin.git", Path(tmp) / "w"
            git_repo.init(origin, "--bare")
            git_repo.clone(origin, work)
            for key, value in (("user.email", "t@example.com"),
                               ("user.name", "t"),
                               ("commit.gpgsign", "false")):
                sh(work, "config", key, value)
            sh(work, "commit", "-q", "--allow-empty", "-m", "c")
            owner = {k: v for k, v in os.environ.items()
                     if not k.startswith("GIT_")}
            env = conductor_run.worker_env(owner, "b1", tmp)
            self.assertEqual(sh(work, "push", "-q", "origin",
                                "HEAD:refs/heads/x", env=env).returncode,
                             0)
            self.assertEqual(sh(work, "fetch", "-q", "origin",
                                env=env).returncode, 0)

    def test_the_harness_gets_the_scrubbed_env_and_an_empty_gh_dir(self):
        seen = {}

        def look(cwd):
            seen["gh_dir"] = sorted(os.listdir(
                harness.calls[0]["env"]["GH_CONFIG_DIR"]))
            pr_body(cwd)
        harness = Harness(act=look)
        with tempfile.TemporaryDirectory() as tmp, \
                unittest.mock.patch.dict(os.environ, {"GH_TOKEN": "t"}):
            root = Path(tmp) / "conductor"
            (root / "docs/factory/batches/b1").mkdir(parents=True)
            (root / LEDGER).write_text("".join(json.dumps(r) + "\n"
                                               for r in BASE))
            (root / ".github").mkdir()
            (root / ".github/factory.json").write_text(
                '{"monthly_cap_usd": 300}')
            conductor_run.run_step(root, "b1", "#12", "spec", lambda: NOW,
                                   git=Git(tmp), gh=Gh(), harness=harness,
                                   pid=777, netrc=Path(tmp) / "netrc")
        env = harness.calls[0]["env"]
        self.assertNotIn("GH_TOKEN", env)
        self.assertEqual(seen["gh_dir"], [])
        self.assertFalse(Path(env["GH_CONFIG_DIR"]).exists())


class TestBrief(unittest.TestCase):
    def brief(self, step, issue_body=None):
        return conductor_run.compose_brief(
            step=step, item="#12", item_type="feature",
            worktree="/w", branch="conductor/b1-12",
            block={"adr": [90, 91]}, wo="WO-0170",
            context="ROW AND PACK", issue_body=issue_body, ceiling=3.0)

    def test_the_brief_has_its_fixed_sections(self):
        text = self.brief("build")
        for heading in ("## Objective", "## Output", "## Tools",
                        "## Boundaries", "## Context budget"):
            self.assertIn(heading, text)
        self.assertIn("Implement WO-0170 test-first", text)
        self.assertIn("Work only in /w", text)
        self.assertIn("adr 90-91", text)
        self.assertIn("never edit .claude-plugin/plugin.json's version",
                      text)
        self.assertIn("leave pr-body.md uncommitted", text)
        self.assertIn("never git push", text)
        self.assertIn("$3.00", text)
        self.assertIn("ROW AND PACK", text)

    def test_only_a_spec_brief_carries_the_issue_body(self):
        self.assertIn("ISSUE TEXT", self.brief("spec", "ISSUE TEXT"))
        self.assertIn("stop-after: decompose",
                      self.brief("spec", "ISSUE TEXT"))
        self.assertNotIn("ISSUE TEXT", self.brief("verify", "ISSUE TEXT"))

    def test_a_review_brief_asks_for_a_verdict_and_overrides_the_exit(self):
        text = self.brief("review")
        self.assertIn("`verdict: pass` or `verdict: changes`", text)
        self.assertIn("post no comment, apply no label and merge nothing",
                      text)
        self.assertIn("Commit nothing but review.md", text)

    def test_a_ship_brief_commits_nothing_but_release_md(self):
        self.assertIn("Commit nothing but release.md", self.brief("ship"))


class TestCompletedRun(RunCase):
    def test_a_completed_build_writes_one_run_row_and_one_spend_row(self):
        path = "docs/features/x/breakdown.md"
        shows = {f"conductor/b1-13:{path}": "- [x] **WO-0170** a\n"
                                            "- [ ] **WO-0171** b\n"}
        git = Git(self.tmp.name, changed=f"{path}\n", shows=shows)

        def work(cwd):
            # The Worker checks its row off and commits it.
            pr_body(cwd)
            shows[f"conductor/b1-13:{path}"] = ("- [x] **WO-0170** a\n"
                                                "- [x] **WO-0171** b\n")
        rows = BASE + [launch("#13", "planned", "spec"), ran("#13", "spec")]
        summary, problems = self.run_step("#13", "build",
                                          Harness(act=work), git=git,
                                          rows=rows)
        self.assertEqual(problems, [])
        self.assertIsNone(summary["stall"])
        rid = "conductor-b1-13-build-1"
        self.assertEqual(self.rows[-2], {
            "at": "2026-10-10T12:30:00Z", "kind": "state", "item": "#13",
            "from": "spec", "to": "build", "reason": "launched",
            "run_id": rid, "pid": 777})
        self.assertEqual(self.rows[-1], {
            "at": "2026-10-10T12:30:00Z", "kind": "run", "item": "#13",
            "step": "build", "charter": "swe", "band": "implementation",
            "model": "m", "models_reported": ["m"],
            "effort": "medium", "run_id": rid, "pid": 777,
            "outcome": "completed"})
        self.assertEqual(self.spend("#13"), [{
            "wo": "WO-0171", "run_id": rid, "model": "m", "tokens": 120,
            "cost": 1.25, "outcome": "completed", "at": "2026-10-10"}])
        kept = self.root / "docs/factory/batches/b1/runs" / f"{rid}.json"
        # #832: the indented form a consumer's prettier check accepts.
        self.assertEqual(kept.read_text(), (
            '{\n  "type": "result",\n  "subtype": "success",\n'
            '  "is_error": false,\n  "total_cost_usd": 1.25,\n'
            '  "usage": {\n    "input_tokens": 100,\n'
            '    "output_tokens": 20\n  },\n'
            '  "modelUsage": {\n    "m": {}\n  }\n}\n'))
        self.assertEqual(summary["outcome"], "completed")

    def test_a_build_that_leaves_its_row_unchecked_stalls(self):
        # Review finding: a completed build run that checked nothing off
        # left the row unchecked, so `next` offered build again, forever,
        # each run spending up to its ceiling with no new consent.
        path = "docs/features/x/breakdown.md"
        git = Git(self.tmp.name, changed=f"{path}\n", shows={
            f"conductor/b1-13:{path}": "- [ ] **WO-0171** b\n"})
        rows = BASE + [launch("#13", "planned", "spec"), ran("#13", "spec")]
        summary, problems = self.run_step("#13", "build",
                                          Harness(act=pr_body), git=git,
                                          rows=rows)
        self.assertEqual(problems, [])
        self.assertEqual(summary["stall"],
                         "the build run completed but left WO-0171"
                         " unchecked")
        self.assertEqual([r["kind"] for r in self.rows[-3:]],
                         ["run", "state", "ask"])
        self.assertEqual(self.rows[-2]["cause"], "agent-failed")
        self.assertEqual(self.rows[-1]["ask_kind"], "stall")

    def test_the_harness_runs_bound_by_policy_in_the_item_worktree(self):
        self.run_step("#12", "spec", Harness(act=pr_body))
        call = self.harness.calls[0]
        self.assertEqual(call["cwd"], str(self.worktree("#12")))
        self.assertEqual(call["timeout"], 90 * 60)
        self.assertEqual(call["env"]["CONDUCTOR_WORKER"], "b1")
        cmd = call["cmd"]
        self.assertEqual(cmd[cmd.index("--model") + 1], "m")
        self.assertIn(["worktree", "add", "-b", "conductor/b1-12",
                       str(self.worktree("#12")), "origin/main"],
                      self.git.calls)

    def test_a_non_build_step_is_keyed_by_its_issue(self):
        self.run_step("#12", "spec", Harness(act=pr_body))
        self.assertEqual(self.spend("#12")[0]["wo"], "#12")

    def test_the_branch_is_committed_pushed_and_its_pr_opened(self):
        self.run_step("#12", "spec", Harness(act=pr_body))
        wt = str(self.worktree("#12"))
        rel = "docs/factory/costs/runs/conductor-b1-12-spec-1.jsonl"
        self.assertIn(["-C", wt, "add", rel], self.git.calls)
        self.assertNotIn(["-C", wt, "add", "docs/factory/costs.jsonl"],
                         self.git.calls)
        self.assertFalse((self.worktree("#12")
                          / "docs/factory/costs.jsonl").exists())
        self.assertIn(["-C", wt, "commit", "-m",
                       "chore(cost): conductor-b1-12-spec-1"],
                      self.git.calls)
        self.assertIn(["-C", wt, "push", "-u", "origin",
                       "conductor/b1-12"], self.git.calls)
        self.assertFalse([c for c in self.git.calls
                          if any("force" in a for a in c)])
        self.assertIn(["pr", "create", "--head", "conductor/b1-12",
                       "--base", "main", "--title",
                       "#12: conductor batch b1", "--body-file", "Body\n"],
                      self.gh.calls)

    def test_a_closed_issue_does_not_open_a_pr(self):
        summary, problems = self.run_step(
            "#12", "spec", Harness(act=pr_body), gh=Gh(state="CLOSED"))
        self.assertEqual(problems, [])
        self.assertEqual(summary["stall"],
                         "refusing to open a PR for #12: the issue is"
                         " already closed")
        self.assertFalse([c for c in self.gh.calls if c[:2] == ["pr",
                                                                "create"]])

    def test_an_unreadable_issue_state_does_not_open_a_pr(self):
        gh = FakeGh(
            answers={("issue", "view"): json.dumps(
                {"title": "t", "body": "Spec this.", "state": "open"}),
                     ("pr", "list"): "[]"},
            failing=["issue", "view", "12", "--json", "state"],
            error=subprocess.CalledProcessError(
                1, "gh", stderr="HTTP 502"))
        summary, problems = self.run_step(
            "#12", "spec", Harness(act=pr_body), gh=gh)
        self.assertEqual(problems, [])
        self.assertEqual(summary["stall"],
                         "refusing to open a PR for #12: cd: gh issue view"
                         " #12 failed: HTTP 502")
        self.assertFalse([c for c in gh.calls if c[:2] == ["pr", "create"]])

    def test_a_missing_issue_state_does_not_open_a_pr(self):
        gh = FakeGh(answers={
            ("issue", "view", "12", "--json", "state"): "{}",
            ("issue", "view"): json.dumps(
                {"title": "t", "body": "Spec this.", "state": "open"}),
            ("pr", "list"): "[]"})
        summary, problems = self.run_step(
            "#12", "spec", Harness(act=pr_body), gh=gh)
        self.assertEqual(problems, [])
        self.assertEqual(summary["stall"],
                         "refusing to open a PR for #12: its issue state"
                         " could not be read")
        self.assertFalse([c for c in gh.calls if c[:2] == ["pr", "create"]])

    def test_an_existing_feature_directory_does_not_open_a_pr(self):
        git = Git(self.tmp.name,
                  changed="docs/features/ship-pr/breakdown.md\n",
                  shows={"origin/main:docs/features/ship-pr": ""})
        summary, problems = self.run_step(
            "#12", "spec", Harness(act=pr_body), git=git)
        self.assertEqual(problems, [])
        self.assertEqual(summary["stall"],
                         "refusing to open a PR for #12:"
                         " docs/features/ship-pr already exists on"
                         " origin/main")
        self.assertFalse([c for c in self.gh.calls if c[:2] == ["pr",
                                                                "create"]])

    def test_a_new_feature_directory_still_opens_a_pr(self):
        git = Git(self.tmp.name,
                  changed="docs/features/brand-new/breakdown.md\n")
        summary, problems = self.run_step(
            "#12", "spec", Harness(act=pr_body), git=git)
        self.assertEqual(problems, [])
        self.assertIsNone(summary["stall"])
        self.assertTrue([c for c in self.gh.calls if c[:2] == ["pr",
                                                               "create"]])

    def test_an_open_pr_is_updated_even_when_the_issue_is_closed(self):
        summary, problems = self.run_step(
            "#12", "spec", Harness(act=pr_body),
            gh=Gh(prs=[44], state="closed"))
        self.assertEqual(problems, [])
        self.assertIsNone(summary["stall"])
        self.assertFalse([c for c in self.gh.calls if c[:2] == ["pr",
                                                                "create"]])

    def test_an_open_pr_is_updated_not_duplicated(self):
        self.run_step("#12", "spec", Harness(act=pr_body), gh=Gh(prs=[44]))
        body = str(self.worktree("#12") / "pr-body.md")
        self.assertIn(["api", "-X", "PATCH",
                       "repos/{owner}/{repo}/pulls/44", "-F",
                       f"body=@{body}"], self.gh.calls)
        self.assertFalse([c for c in self.gh.calls if c[:2] == ["pr",
                                                                "create"]])

    def test_the_issue_body_reaches_only_a_spec_brief(self):
        self.run_step("#12", "spec", Harness(act=pr_body),
                      gh=Gh(body="SECRET-ISSUE-TEXT"))
        self.assertIn("SECRET-ISSUE-TEXT", self.harness.calls[0]["cmd"][2])

    def test_seq_counts_earlier_runs_of_the_step(self):
        rows = BASE + [launch("#14", "planned", "build"),
                       moved("#14", "build", "stalled"),
                       stall_ask("ask-2", "#14"),
                       answered("ask-2", "retry", "#14")]
        self.run_step("#14", "build", Harness(act=pr_body),
                      gh=Gh(title="WO-0180: order"), rows=rows)
        self.assertEqual(self.rows[-1]["run_id"], "conductor-b1-14-build-2")
        self.assertEqual(self.spend("#14")[0]["wo"], "WO-0180")

    def test_an_order_is_briefed_from_its_breakdown_row_not_its_title(self):
        # Issue #857: the order leg resolves #14 through the work_orders
        # index the dispatcher reads; the issue title names nothing.
        self.run_step("#14", "build", Harness(act=pr_body),
                      gh=Gh(title="WO-9999: a title naming another order"))
        brief = self.harness.calls[0]["cmd"][2]
        self.assertIn(f"{ORDER_ROW}\n  - Accept: the order lands.", brief)
        self.assertNotIn("WO-9999", brief)
        self.assertEqual(self.spend("#14")[0]["wo"], "WO-0180")

    def test_an_order_no_breakdown_row_mirrors_is_not_launched(self):
        with unittest.mock.patch.dict(globals(),
                                      {"BREAKDOWN": "# Breakdown\n"}):
            summary, problems = self.run_step(
                "#14", "build", Harness(act=pr_body),
                gh=Gh(title="WO-0180: order"))
        self.assertEqual(problems, ["cd: no breakdown row mirrors #14"])
        self.assertEqual(self.harness.calls, [])

    def test_retry_up_runs_one_band_up(self):
        rows = BASE + [launch("#14", "planned", "build"),
                       moved("#14", "build", "stalled"),
                       stall_ask("ask-2", "#14"),
                       answered("ask-2", "retry-up", "#14")]
        self.run_step("#14", "build", Harness(act=pr_body),
                      gh=Gh(title="WO-0180: order"), rows=rows)
        self.assertEqual((self.rows[-1]["band"], self.rows[-1]["model"],
                          self.rows[-1]["effort"]),
                         ("architecture_review", "fable", "high"))

    def test_retry_up_is_not_re_offered_after_a_run_at_the_top_band(self):
        # #732: a stalled run already bumped to the top band must not
        # have retry-up offered again — a further retry-up would run at
        # the same band it just failed at.
        rows = BASE + [launch("#14", "planned", "build"),
                       moved("#14", "build", "stalled"),
                       stall_ask("ask-2", "#14"),
                       answered("ask-2", "retry-up", "#14")]
        self.run_step("#14", "build", Harness(missing=True),
                      gh=Gh(title="WO-0180: order"), rows=rows)
        self.assertEqual(self.rows[-1]["options"], ["retry", "block"])

    def test_a_renumbered_block_briefs_its_live_numbers(self):
        # #694: the brief once kept each kind's last reserve row, so a
        # renumber row hid the numbers the item still holds.
        def reserve(what, values, **extra):
            return {"at": PLAN["at"], "kind": "reserve", "item": "#14",
                    "what": what, "values": values, **extra}
        rows = BASE + [reserve("prd", [5, 6]), reserve("adr", [90, 91]),
                       reserve("adr", [120], renumbered_from=[90])]
        self.run_step("#14", "build", Harness(act=pr_body),
                      gh=Gh(title="WO-0180: order"), rows=rows)
        self.assertIn("reserved block (prd 5-6, adr 91,120)",
                      self.harness.calls[0]["cmd"][2])


class TestFailedRun(RunCase):
    def stalled(self):
        return self.rows[-2]["to"], self.rows[-1]["ask_kind"]

    def test_a_missing_harness_is_agent_failed_at_cost_zero(self):
        self.run_step("#12", "spec", Harness(missing=True))
        self.assertEqual(self.spend("#12")[0]["cost"], 0.0)
        self.assertEqual(self.spend("#12")[0]["outcome"], "agent-failed")
        run = [r for r in self.rows if r["kind"] == "run"][-1]
        self.assertEqual(run["outcome"], "agent-failed")
        self.assertEqual(self.stalled(), ("stalled", "stall"))
        self.assertEqual(self.rows[-2]["cause"], "agent-failed")
        self.assertEqual(len(self.harness.calls), 1)

    def test_a_wall_clock_kill_records_the_ceiling_and_stalls(self):
        self.run_step("#12", "spec", Harness(events=[], timed_out=True))
        self.assertEqual(self.spend("#12")[0]["cost"], 3.0)
        self.assertEqual(self.spend("#12")[0]["outcome"],
                         "killed:cost-at-ceiling")
        self.assertEqual((self.rows[-2]["reason"], self.rows[-2]["cause"]),
                         ("killed at its 90-minute wall-clock limit",
                          "timeout"))

    def test_an_unaccountable_result_records_the_ceiling_and_stalls(self):
        bad = dict(RESULT, total_cost_usd="lots")
        self.run_step("#12", "spec", Harness(events=[bad], act=pr_body))
        self.assertEqual(self.spend("#12")[0]["cost"], 3.0)
        self.assertEqual(self.spend("#12")[0]["outcome"],
                         "unaccounted:cost-at-ceiling")
        self.assertEqual(self.stalled(), ("stalled", "stall"))

    def test_a_completed_run_without_pr_body_stalls(self):
        self.run_step("#12", "spec", Harness())
        self.assertEqual((self.rows[-2]["reason"], self.rows[-2]["cause"]),
                         ("the run completed but left no pr-body.md",
                          "agent-failed"))

    def test_rows_written_after_the_run_carry_the_time_it_ended(self):
        # Review minor 1: stamped with the launch time, a stall ask after
        # a 90-minute run read as 90 minutes of Owner wait.
        ended = NOW + timedelta(minutes=90)
        times = [NOW]

        def work(cwd):
            times[0] = ended
        self.clock = lambda: times[0]
        self.run_step("#12", "spec", Harness(act=work))
        self.assertEqual([(r["kind"], r["at"]) for r in self.rows[-4:]], [
            ("state", "2026-10-10T12:30:00Z"),
            ("run", "2026-10-10T14:00:00Z"),
            ("state", "2026-10-10T14:00:00Z"),
            ("ask", "2026-10-10T14:00:00Z")])

    def test_a_body_left_by_an_earlier_step_is_not_this_steps_output(self):
        # Review minor 7: pr-body.md stayed in the worktree, so from the
        # second step on the no-pr-body.md stall could never fire.
        self.worktree("#12").mkdir(parents=True)
        pr_body(self.worktree("#12"))
        self.run_step("#12", "spec", Harness())
        self.assertEqual(self.rows[-2]["reason"],
                         "the run completed but left no pr-body.md")

    def test_the_body_is_cleared_once_delivered(self):
        # Left behind, it would also be an untracked file the merge
        # turn's clean-worktree check stalls on.
        self.run_step("#12", "spec", Harness(act=pr_body))
        self.assertIsNone(self.rows[-1].get("ask_kind"))
        self.assertFalse((self.worktree("#12") / "pr-body.md").exists())

    def test_a_failed_push_stalls_and_opens_no_pr(self):
        self.run_step("#12", "spec", Harness(act=pr_body),
                      git=Git(self.tmp.name, failing=[
                          "-C", str(self.worktree("#12")), "push"]))
        self.assertTrue(self.rows[-2]["reason"].startswith(
            "pushing conductor/b1-12 failed: fatal: rejected"))
        self.assertEqual(self.rows[-2]["cause"], "delivery-failed")
        self.assertFalse([c for c in self.gh.calls if c[0] == "pr"])

    def test_a_failed_pr_open_stalls(self):
        self.run_step("#12", "spec", Harness(act=pr_body),
                      gh=Gh(fail=["pr", "create"]))
        self.assertEqual((self.rows[-2]["reason"], self.rows[-2]["cause"]),
                         ("opening or updating the PR failed: HTTP 422",
                          "delivery-failed"))

    def test_a_launch_the_state_machine_refuses_spawns_nothing(self):
        summary, problems = self.run_step("#12", "verify", Harness())
        self.assertIsNone(summary)
        self.assertEqual(problems,
                         ["cd: #12 cannot move from planned to verify"])
        self.assertEqual(self.harness.calls, [])

    def test_an_unknown_item_or_step_is_refused(self):
        self.assertEqual(self.run_step("#99", "spec", Harness())[1],
                         ["cd: #99 is not an item of this batch's plan"])
        self.assertEqual(self.run_step("#14", "spec", Harness())[1],
                         ["cd: #14 has no spec step"])


# #725: the headless CLI's budget-stop result, usage zeroed and the
# counts only per model.
BUDGET_STOP = {"type": "result", "subtype": "error_max_budget_usd",
               "is_error": True, "total_cost_usd": 3.064511,
               "errors": ["Reached maximum budget ($3.06)"],
               "permission_denials": [],
               "usage": {"input_tokens": 0, "output_tokens": 0},
               "modelUsage": {"m": {"inputTokens": 40, "outputTokens": 9000,
                                    "cacheReadInputTokens": 900000,
                                    "cacheCreationInputTokens": 60000}}}
SPEC_LOG = ("chore(cost): conductor-b1-12-spec-1\n"
            "docs(#12): breakdown\n"
            "docs(#12): prd and architecture\n"
            "chore(cost): conductor-b1-12-spec-0\n"
            "feat: not this run's\n")


class TestRetryAfterBudgetStop(RunCase):
    """#725: a retry after a budget stop continues the committed work,
    a repeat budget stop recommends no plain retry, and the stop's
    tokens are metered with its cost."""

    RETRY = BASE + failed("#12", "planned", "spec",
                          band="architecture_review")

    def brief(self):
        return self.harness.calls[0]["cmd"][2]

    def test_a_budget_stop_meters_its_tokens_with_its_cost(self):
        self.run_step("#12", "spec", Harness(events=[BUDGET_STOP]))
        row = self.spend("#12")[0]
        self.assertEqual((row["tokens"], row["cost"], row["outcome"]),
                         (969040, 3.064511, "agent-failed"))
        self.assertEqual((self.rows[-2]["reason"], self.rows[-2]["cause"]),
                         (BUDGET, "ceiling"))

    def test_a_budget_stop_is_kept_as_prettier_would_write_it(self):
        # #832: a consumer's prettier check rewrote compact runs/*.json,
        # and would rewrite plain indent=2 too: it keeps a short array on
        # one line.
        self.run_step("#12", "spec", Harness(events=[BUDGET_STOP]))
        [kept] = (self.root / "docs/factory/batches/b1/runs").glob("*.json")
        self.assertEqual(kept.read_text(), (
            '{\n  "type": "result",\n'
            '  "subtype": "error_max_budget_usd",\n'
            '  "is_error": true,\n  "total_cost_usd": 3.064511,\n'
            '  "errors": ["Reached maximum budget ($3.06)"],\n'
            '  "permission_denials": [],\n'
            '  "usage": {\n    "input_tokens": 0,\n'
            '    "output_tokens": 0\n  },\n'
            '  "modelUsage": {\n    "m": {\n      "inputTokens": 40,\n'
            '      "outputTokens": 9000,\n'
            '      "cacheReadInputTokens": 900000,\n'
            '      "cacheCreationInputTokens": 60000\n    }\n  }\n}\n'))

    def test_a_retry_is_briefed_with_the_work_already_committed(self):
        self.run_step("#12", "spec", Harness(act=pr_body),
                      git=Git(self.tmp.name, log=SPEC_LOG), rows=self.RETRY)
        self.assertIn(
            "## Prior work\n\n"
            "The previous spec run, conductor-b1-12-spec-1, ended: " + BUDGET
            + ". These commits it made are already on conductor/b1-12, the"
            " head this worktree is at:\n"
            "- docs(#12): breakdown\n"
            "- docs(#12): prd and architecture\n"
            "Do not repeat that work. Check it against the objective, finish"
            " only what is missing (at the least, write pr-body.md), and"
            " stop.\n", self.brief())
        self.assertNotIn("not this run's", self.brief())

    def test_a_workers_own_cost_commit_is_prior_work(self):
        # #771: only a commit naming a run id is a spend commit; a
        # Worker's `chore(cost): ...` commit is work the run made.
        log = ("chore(cost): conductor-b1-12-spec-1\n"
               "chore(cost): raise the default monthly cap\n"
               "docs(#12): breakdown\n")
        self.run_step("#12", "spec", Harness(act=pr_body),
                      git=Git(self.tmp.name, log=log), rows=self.RETRY)
        self.assertIn("- chore(cost): raise the default monthly cap\n"
                      "- docs(#12): breakdown\n", self.brief())

    def test_a_retry_with_nothing_committed_has_no_prior_work(self):
        self.run_step("#12", "spec", Harness(act=pr_body),
                      git=Git(self.tmp.name,
                              log="chore(cost): conductor-b1-12-spec-1\n"),
                      rows=self.RETRY)
        self.assertNotIn("## Prior work", self.brief())

    def test_a_first_run_reads_no_log(self):
        self.run_step("#12", "spec", Harness(act=pr_body))
        self.assertFalse([c for c in self.git.calls if c[:1] == ["log"]])
        self.assertNotIn("## Prior work", self.brief())

    def test_a_first_budget_stop_recommends_retry(self):
        self.run_step("#12", "spec", Harness(events=[BUDGET_STOP]))
        asked = self.rows[-1]
        self.assertEqual((asked["recommended"], asked["why"]), (
            "retry", "a first failure is evidence about the item as often"
                     " as about the agent, so nothing retries without your"
                     " answer"))

    def test_a_second_budget_stop_at_the_top_band_recommends_block(self):
        self.run_step("#12", "spec", Harness(events=[BUDGET_STOP]),
                      git=Git(self.tmp.name, log=SPEC_LOG), rows=self.RETRY)
        asked = self.rows[-1]
        self.assertEqual(asked["question"], f"#12 stalled in spec: {BUDGET}."
                         " Retry, or block?")
        self.assertEqual((asked["options"], asked["recommended"],
                          asked["why"]), (
            ["retry", "block"], "block",
            "a second consecutive budget stop on spec at the same $3.00"
            " ceiling: the outcome repeats at that ceiling, so a plain"
            " retry spends it again; block it"))


def spend_line(run, cost, at="2026-10-05", wo="#90"):
    return json.dumps({"wo": wo, "run_id": run, "model": "m", "tokens": 1,
                       "cost": cost, "outcome": "completed", "at": at})


MAIN_COSTS = "origin/main:docs/factory/costs.jsonl"


class TestMonthlyCap(RunCase):
    """Review major 2: a launch is checked against the monthly cap at run
    time, counting main's spend, the batch's item branches and the
    ceilings of runs still in flight."""

    def over(self, rows=BASE, shows=None):
        self.config(10)
        return self.run_step("#12", "spec", Harness(act=pr_body),
                             git=Git(self.tmp.name, shows=shows), rows=rows)

    def test_a_launch_that_would_pass_the_cap_pauses_dispatch(self):
        summary, problems = self.over(shows={MAIN_COSTS: "\n".join([
            spend_line("old", 50.0, at="2026-09-30"),
            spend_line("a", 8.0)]) + "\n"})
        self.assertIsNone(summary)
        self.assertEqual(problems, [
            "cd: launching #12 spec ($3.00 ceiling) would put the month at"
            " $11.00 against its $10.00 cap; dispatch is paused behind"
            " ask-2"])
        self.assertEqual(self.harness.calls, [])
        self.assertEqual(self.rows[-1], {
            "at": "2026-10-10T12:30:00Z", "kind": "ask", "item": None,
            "id": "ask-2", "ask_kind": "spend",
            "question": "Launching #12 spec ($3.00 ceiling) would put the"
                        " month at $11.00 against its $10.00 cap. Resume"
                        " dispatch, or stop?",
            "options": ["resume", "stop"], "recommended": "stop",
            "why": "the monthly cap is ADR-0034's breaker; raise"
                   " monthly_cap_usd in factory.json first, or a resumed"
                   " launch asks again"})
        self.assertFalse([r for r in self.rows if r["kind"] == "state"])

    def test_in_flight_ceilings_and_item_branch_spend_count(self):
        branch = "conductor/b1-13:docs/factory/costs.jsonl"
        rows = BASE + [launch("#13", "planned", "spec"),
                       ran("#13", "spec"),
                       launch("#14", "planned", "build")]
        line = spend_line("conductor-b1-13-spec-1", 2.5, wo="#13")
        _, problems = self.over(rows=rows, shows={
            MAIN_COSTS: spend_line("a", 2.0) + "\n",
            # main's rows again on the branch count once
            branch: spend_line("a", 2.0) + "\n" + line + "\n"})
        self.assertEqual(problems, [
            "cd: launching #12 spec ($3.00 ceiling) would put the month at"
            " $10.50 against its $10.00 cap; dispatch is paused behind"
            " ask-2"])

    def test_item_branch_spend_in_a_run_file_counts(self):
        run = "conductor-b1-13-spec-1"
        rows = BASE + [launch("#13", "planned", "spec"),
                       ran("#13", "spec"),
                       launch("#14", "planned", "build")]
        line = spend_line(run, 2.5, wo="#13")
        _, problems = self.over(rows=rows, shows={
            MAIN_COSTS: spend_line("a", 2.0) + "\n",
            f"conductor/b1-13:docs/factory/costs/runs/{run}.jsonl":
                line + "\n"})
        self.assertEqual(problems, [
            "cd: launching #12 spec ($3.00 ceiling) would put the month at"
            " $10.50 against its $10.00 cap; dispatch is paused behind"
            " ask-2"])

    def test_a_launch_within_the_cap_runs(self):
        summary, problems = self.over(shows={
            MAIN_COSTS: spend_line("a", 7.0) + "\n"})
        self.assertEqual(problems, [])
        self.assertEqual(summary["outcome"], "completed")

    def test_a_held_batch_gets_no_second_pause_ask(self):
        rows = BASE + [dict(stall_ask("ask-2", None, ("resume", "stop")),
                            ask_kind="spend")]
        _, problems = self.over(rows=rows, shows={
            MAIN_COSTS: spend_line("a", 8.0) + "\n"})
        self.assertEqual(problems, [
            "cd: launching #12 spec ($3.00 ceiling) would put the month at"
            " $11.00 against its $10.00 cap; dispatch is paused behind"
            " ask-2"])
        self.assertEqual(len([r for r in self.rows if r["kind"] == "ask"]),
                         2)

    def test_no_cap_refuses_the_launch(self):
        (self.root / ".github/factory.json").write_text("{}")
        self.ledger(*BASE)
        _, problems = conductor_run.run_step(
            self.root, "b1", "#12", "spec", lambda: NOW,
            git=Git(self.tmp.name), gh=Gh(), harness=Harness(act=pr_body),
            pid=777, netrc=self.no_netrc)
        self.assertEqual(problems, [
            "config: factory.json names no positive monthly_cap_usd",
            "cd: launching #12 spec was refused; dispatch is paused behind"
            " ask-2"])


class TestReviewRun(RunCase):
    REVIEWING = BASE + [launch("#14", "planned", "build"),
                        ran("#14", "build"),
                        launch("#14", "build", "verify"),
                        ran("#14", "verify")]

    def review(self, verdict_line, ran=None):
        path = "docs/fixes/x/review.md"

        def act(cwd):
            pr_body(cwd)
            (cwd / "docs/fixes/x").mkdir(parents=True)
            (cwd / path).write_text(f"---\nstage: review\n{verdict_line}"
                                    "---\n# Review\n")
            if ran is not None:
                ran.append(True)
        git = Git(self.tmp.name, changed=f"{path}\n",
                  heads=None if ran is None else self.moving_head(ran))
        self.run_step("#14", "review", Harness(act=act), git=git,
                      gh=Gh(title="WO-0180"), rows=self.REVIEWING)

    @staticmethod
    def moving_head(ran):
        """A rev-parse answer: the branch head moves once the review
        Worker has run (its own commits land on the branch)."""
        return lambda args: "a1fter\n" if ran else "bef0re\n"

    def test_a_pass_verdict_marks_the_item_reviewed(self):
        self.review("verdict: pass\n")
        self.assertEqual(self.rows[-1]["to"], "reviewed")
        self.assertEqual(self.rows[-1]["reviewer_run"],
                         "conductor-b1-14-review-1")
        # The head the review run was launched on, read before it ran.
        self.assertEqual(self.rows[-1]["reviewed_head"], "c0ffee")
        self.assertIn(["rev-parse", "conductor/b1-14"], self.git.calls)

    def test_the_reviewed_head_is_read_before_the_review_worker_runs(self):
        # Re-review R2: a head read after the run would hide the review
        # Worker's own commits from the merge's drift check.
        self.review("verdict: pass\n", ran=[])
        self.assertEqual(self.rows[-1]["to"], "reviewed")
        self.assertEqual(self.rows[-1]["reviewed_head"], "bef0re")

    def test_a_missing_verdict_stalls(self):
        self.review("")
        self.assertEqual(self.rows[-2]["reason"],
                         "review.md carries no verdict: pass|changes line")


class TestRunCli(RunCase):
    def test_run_is_a_conductor_verb(self):
        self.ledger(*BASE)
        git = Git(self.tmp.name)
        with unittest.mock.patch.dict(os.environ, {"HOME": self.tmp.name}):
            code, out = cli_contract.capture(
                conductor.main, ["run", "b1", "#12", "spec"], env={},
                clock=lambda: NOW, root=self.root, run=Gh(), git=git,
                harness=Harness(act=pr_body))
        self.assertEqual(code, 0, out)
        self.assertIn("cd: run conductor-b1-12-spec-1 completed", out)

    def test_a_bad_item_argument_prints_usage(self):
        code, _ = cli_contract.capture(
            conductor.main, ["run", "b1", "12", "spec"], env={},
            clock=lambda: NOW, root=self.root)
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
