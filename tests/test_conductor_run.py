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
from test_conductor_flow import (PLAN, START, answered,  # noqa: E402
                                 launch, moved, ran, run_id, stall_ask)

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


def Git(tmp, changed="", shows=None, fail=None):
    """A git port over a scratch tree: worktree add makes the directory;
    every other call is recorded (run.calls) and answered from canned
    output. `fail` names an argument whose call is rejected."""
    calls = []

    def run(args):
        calls.append(args)
        if fail and fail in args:
            raise subprocess.CalledProcessError(1, args, stderr="rejected")
        out = ""
        if args[:1] == ["rev-parse"] and "--git-common-dir" in args:
            out = str(Path(tmp) / ".git") + "\n"
        elif args[:1] == ["rev-parse"]:
            out = "c0ffee\n"
        elif args[:2] == ["worktree", "add"]:
            Path(args[4]).mkdir(parents=True)
        elif "diff" in args:
            out = changed
        elif "show" in args:
            out = (shows or {}).get(args[-1], "")
        return subprocess.CompletedProcess(args, 0, stdout=out, stderr="")
    run.calls = calls
    return run


def Gh(prs=(), body="Spec this.", title="t", fail=None):
    """The one fake gh, answering issue view and pr list; `fail` is the
    argv prefix whose call is rejected with HTTP 422."""
    return FakeGh(
        answers={("issue", "view"): json.dumps({"title": title,
                                                "body": body}),
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
        path = self.worktree(item) / "docs/factory/costs.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()]


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
            subprocess.run(["git", "init", "-q", str(work)], check=True)
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
            subprocess.run(["git", "init", "-q", str(work)], check=True)
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
            subprocess.run(["git", "init", "-q", "--bare", str(origin)],
                           check=True)
            subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                           check=True, capture_output=True)
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
        self.assertEqual(json.loads(kept.read_text()), RESULT)
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
        self.assertIn(["-C", wt, "add", "docs/factory/costs.jsonl"],
                      self.git.calls)
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
        self.assertEqual(len(self.harness.calls), 1)

    def test_a_wall_clock_kill_records_the_ceiling_and_stalls(self):
        self.run_step("#12", "spec", Harness(events=[], timed_out=True))
        self.assertEqual(self.spend("#12")[0]["cost"], 3.0)
        self.assertEqual(self.spend("#12")[0]["outcome"],
                         "killed:cost-at-ceiling")
        self.assertEqual(self.rows[-2]["reason"],
                         "killed at its 90-minute wall-clock limit")

    def test_an_unaccountable_result_records_the_ceiling_and_stalls(self):
        bad = dict(RESULT, total_cost_usd="lots")
        self.run_step("#12", "spec", Harness(events=[bad], act=pr_body))
        self.assertEqual(self.spend("#12")[0]["cost"], 3.0)
        self.assertEqual(self.spend("#12")[0]["outcome"],
                         "unaccounted:cost-at-ceiling")
        self.assertEqual(self.stalled(), ("stalled", "stall"))

    def test_a_completed_run_without_pr_body_stalls(self):
        self.run_step("#12", "spec", Harness())
        self.assertEqual(self.rows[-2]["reason"],
                         "the run completed but left no pr-body.md")

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
                      git=Git(self.tmp.name, fail="push"))
        self.assertTrue(self.rows[-2]["reason"].startswith(
            "pushing conductor/b1-12 failed: rejected"))
        self.assertFalse([c for c in self.gh.calls if c[0] == "pr"])

    def test_a_failed_pr_open_stalls(self):
        self.run_step("#12", "spec", Harness(act=pr_body),
                      gh=Gh(fail=["pr", "create"]))
        self.assertEqual(self.rows[-2]["reason"],
                         "opening or updating the PR failed: HTTP 422")

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
            "config: factory.json names no positive monthly_cap_usd"])


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
        git = Git(self.tmp.name, changed=f"{path}\n")
        if ran is not None:
            git = self.moving_head(git, ran)
        self.run_step("#14", "review", Harness(act=act), git=git,
                      gh=Gh(title="WO-0180"), rows=self.REVIEWING)

    @staticmethod
    def moving_head(git, ran):
        """The fake git, with the branch head moving once the review
        Worker has run (its own commits land on the branch)."""
        def run(args):
            out = git(args)
            if args[:1] == ["rev-parse"] and "--git-common-dir" not in args:
                head = "a1fter" if ran else "bef0re"
                return subprocess.CompletedProcess(args, 0, f"{head}\n", "")
            return out
        run.calls = git.calls
        return run

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
