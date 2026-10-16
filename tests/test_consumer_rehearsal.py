"""The no-spend consumer rehearsal (#831): a stamped consumer repo
driven through the Conductor's plan, open, a stubbed run and close,
offline and with no spend.

Every defect the retro (docs/features/orchestrator/retro.md) found in
batches b20261012 and b20261013 lived in a consumer repo, and the
2026-10-11 dry run stopped at plan, so each was found during a paid
batch. Here git is real (a scratch consumer and a bare origin in a temp
directory), the harness is a stub that emits one success result event,
and gh is FakeGh, whose repo plays the consumer's own auto-merge. The
rehearsal pins the ones that would recur only in a consumer:

- #708: `run` in a repo whose main never held docs/factory/costs.jsonl
  launches, and records its spend row.
- #710: `open` from a linked worktree anchors the batch worktree at the
  main checkout, never nested in the linked one.
- #821: reservations read the consumer's 3-digit ADR files, not the
  payload's ADR citations, and a second open batch reserves above the
  first.
- #807: `close --merge` succeeds when the repo's auto-merge landed the
  closing PR after the Conductor pushed.
- #850: factory.json's conductor.worktree_setup (here a no-op that
  leaves a marker) runs in the item worktree, never the batch worktree.

JSON formatting and labels are not asserted here (#832, #834). The
husky hook dir is present but not installed (no core.hooksPath), as in
a checkout before `npm install`: with it installed and no node_modules,
the run's spend commit fails, which is #833's open decision.
"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import conductor
import factory_init

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_gh import FakeGh  # noqa: E402
import git_repo  # noqa: E402
from test_conductor_plan import AGENTS, CONFIG, OWNER, clock, issue  # noqa: E402,E501
from test_conductor_run import Harness, pr_body  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
BATCH, OTHER = "b20261014", "b20261015"
SETUP = [sys.executable, "-c", "open('setup-ran', 'w').close()"]
CLOSING = conductor.batch_branch(BATCH)
# The consumer's own files beside the stamp: a node toolchain it has not
# installed, a husky hook dir, 3-digit ADRs and an auto-merge workflow.
CONSUMER = {
    "package.json": json.dumps({
        "name": "consumer", "private": True,
        "scripts": {"prepare": "husky", "format:check": "prettier --check"
                    " ."}}, indent=2) + "\n",
    ".prettierrc": "{}\n",
    ".husky/pre-commit": "npx lint-staged\n",
    ".github/workflows/auto-merge.yml": (
        "name: auto-merge\non: pull_request\npermissions:\n"
        "  contents: write\n  pull-requests: write\njobs:\n  merge:\n"
        "    runs-on: ubuntu-latest\n    steps:\n"
        "      - run: gh pr merge --auto --squash \"$PR\"\n"),
    **{f"docs/adr/ADR-0{n}-decision-{n}.md": f"# ADR-0{n}\n"
       for n in range(20, 27)},
}


def git_port(cwd):
    """The conductor's git port, as cli.runner("git") is, run from
    `cwd`: what the Conductor's own process is when it runs there."""
    def run(args, input=None):
        return subprocess.run(["git", *args], cwd=cwd, check=True,
                              capture_output=True, text=True, input=input)
    return run


class AutoMergingGh(FakeGh):
    """FakeGh whose repo auto-merges the closing PR (#807): once the
    Conductor asks for its open PR after pushing, the repo has already
    squash-merged it at the head origin holds, and moved main."""

    def __init__(self, origin, issues):
        self.origin = origin
        super().__init__({
            ("repo", "view"): json.dumps(OWNER),
            ("issue", "view"): lambda args: json.dumps(
                dict(issues[int(args[2])], title=f"Issue {args[2]}",
                     body="Make it so.")),
            ("pr", "list", "--head"): self.pr_list,
            ("label", "list"): "[]"})

    def head(self, branch):
        return subprocess.run(
            ["git", "rev-parse", f"refs/heads/{branch}"], cwd=self.origin,
            check=True, capture_output=True, text=True).stdout.strip()

    def pr_list(self, args):
        branch, state = args[3], args[5]
        if branch != CLOSING:
            return "[]"
        if state == "open":
            subprocess.run(["git", "update-ref", "refs/heads/main",
                            self.head(branch)], cwd=self.origin, check=True)
            return "[]"
        return json.dumps([{"number": 6, "headRefOid": self.head(branch),
                            "mergeCommit": {"oid": self.head("main")}}])


class TestConsumerRehearsal(unittest.TestCase):
    """plan, open, answer, a stubbed run, block, close and close --merge,
    in order, in one scratch consumer."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name).resolve()
        home = self.tmp / "home"
        home.mkdir()
        env = mock.patch.dict(os.environ, {
            "HOME": str(home), "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
            "GIT_AUTHOR_NAME": "Owner", "GIT_AUTHOR_EMAIL": "o@example.com",
            "GIT_COMMITTER_NAME": "Owner",
            "GIT_COMMITTER_EMAIL": "o@example.com"})
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop(conductor.WORKER_ENV, None)
        self.origin = self.tmp / "origin.git"
        self.checkout = self.tmp / "consumer"
        git_repo.init(self.origin, "--bare", "-b", "main")
        git_repo.init(self.checkout, "-b", "main")
        self.assertEqual(factory_init.stamp(REPO, self.checkout), [])
        for path, text in CONSUMER.items():
            (self.checkout / path).parent.mkdir(parents=True, exist_ok=True)
            (self.checkout / path).write_text(text)
        (self.checkout / ".github/factory.json").write_text(
            json.dumps(dict(CONFIG, conductor={"worktree_setup": SETUP})))
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "chore: stamp the factory")
        self.git("remote", "add", "origin", str(self.origin))
        self.git("push", "-q", "-u", "origin", "main")
        self.issues = {12: issue(12), 13: issue(13)}
        self.gh = AutoMergingGh(self.origin, self.issues)
        # The Owner's session works from a linked worktree (#710).
        self.linked = self.checkout / ".claude/worktrees/owner-docs"
        self.git("worktree", "add", "-q", "-b", "owner-docs",
                 str(self.linked), "origin/main")

    def git(self, *args, cwd=None):
        return git_port(cwd or self.checkout)(list(args)).stdout

    def conduct(self, argv, cwd, **ports):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = conductor.main(argv, env={}, clock=clock, root=cwd,
                                  run=self.gh, git=git_port(cwd),
                                  netrc=self.tmp / "netrc", **ports)
        return code, out.getvalue()

    def rows(self, worktree, batch=BATCH):
        rows, problems = conductor.load(worktree, batch)
        self.assertEqual(problems, [])
        return rows

    def reserved(self, worktree, batch):
        return {row["what"]: row["values"] for row in self.rows(
            worktree, batch) if row["kind"] == "reserve"}

    def test_a_stamped_consumer_runs_a_batch_end_to_end(self):
        agents = ["--agents", str(AGENTS)]
        code, out = self.conduct(["plan", *agents, "#12"], self.linked)
        self.assertEqual((code, out.splitlines()[0]),
                         (0, "cd: 1 item(s) planned"), out)

        # #710: opened from a linked worktree, anchored at the checkout.
        code, out = self.conduct(["open", BATCH, *agents, "#12"],
                                 self.linked)
        self.assertEqual(code, 0, out)
        batch_wt = self.checkout / conductor.batch_worktree(BATCH)
        self.assertIn(f"cd: opened {batch_wt}", out)
        self.assertFalse((self.linked / ".claude/worktrees").exists())

        # #821: ADRs above the consumer's 3-digit ADR-026, not above the
        # payload's ADR-00NN citations; a second open batch's block
        # starts above the first's.
        first = self.reserved(batch_wt, BATCH)
        self.assertEqual({kind: values[0] for kind, values in first.items()},
                         {"prd": 1, "adr": 27, "wo": 1}, first)
        code, out = self.conduct(["open", OTHER, *agents, "#13"],
                                 self.checkout)
        self.assertEqual(code, 0, out)
        second = self.reserved(
            self.checkout / conductor.batch_worktree(OTHER), OTHER)
        for kind, values in first.items():
            self.assertGreater(min(second[kind]), max(values), kind)

        spend = self.rows(batch_wt)[-1]
        self.assertEqual(spend["ask_kind"], "spend")
        code, out = self.conduct(["answer", BATCH, spend["id"], "approve"],
                                 batch_wt)
        self.assertEqual(code, 0, out)

        # #708: origin/main holds no costs.jsonl, and the run launches,
        # meters the stubbed result and commits its spend row.
        self.assertNotIn("docs/factory/costs.jsonl",
                         self.git("ls-tree", "-r", "--name-only",
                                  "origin/main"))
        harness = Harness(act=pr_body)
        code, out = self.conduct(["run", BATCH, "#12", "spec"], batch_wt,
                                 harness=harness)
        self.assertEqual(code, 0, out)
        run_id = conductor.run_id(BATCH, "#12", "spec", 1)
        self.assertEqual(out.splitlines()[0], f"cd: run {run_id} completed")
        self.assertEqual(len(harness.calls), 1)
        item_wt = self.checkout / conductor.item_worktree(BATCH, "#12")
        self.assertTrue((item_wt / "setup-ran").is_file())
        self.assertFalse((batch_wt / "setup-ran").exists())
        item_branch = conductor.item_branch(BATCH, "#12")
        self.assertIn(run_id, self.git(
            "show", f"{item_branch}:docs/factory/costs/runs/{run_id}.jsonl"))
        self.assertNotIn("docs/factory/costs.jsonl", self.git(
            "ls-tree", "-r", "--name-only", item_branch))
        self.assertTrue((batch_wt / conductor.RUNS.format(batch=BATCH)
                         / f"{run_id}.json").is_file())
        self.assertTrue(self.gh.called("pr", "create", "--head",
                                       item_branch))
        self.assertEqual([row["outcome"] for row in self.rows(batch_wt)
                          if row["kind"] == "run"], ["completed"])

        # The Owner blocks the item, so the batch can close.
        code, out = self.conduct(
            ["ask", BATCH, "--kind", "clarify", "--item", "#12",
             "--question", "Stop here?", "--option", "block",
             "--option", "continue", "--recommended", "block", "--why",
             "a rehearsal"], batch_wt)
        self.assertEqual(code, 0, out)
        code, out = self.conduct(["answer", BATCH, out.splitlines()[0], "block"],
                                 batch_wt)
        self.assertEqual(code, 0, out)

        code, out = self.conduct(["close", BATCH], batch_wt)
        self.assertEqual(code, 0, out)
        self.assertIn(f"cd: closed batch {BATCH}: merged none; blocked #12",
                      out)
        self.assertEqual(self.git("rev-parse", CLOSING, cwd=self.origin),
                         self.git("rev-parse", "HEAD", cwd=batch_wt))
        closing = self.rows(batch_wt)[-1]
        self.assertEqual(closing["ask_kind"], "merge")
        code, out = self.conduct(["answer", BATCH, closing["id"], "merge"],
                                 batch_wt)
        self.assertEqual(code, 0, out)

        # #807: the repo's auto-merge lands the closing PR first.
        code, out = self.conduct(["close", BATCH, "--merge"], batch_wt,
                                 sleep=lambda seconds: None)
        self.assertEqual(code, 0, out)
        self.assertIn(f"cd: batch {BATCH}'s closing PR #6 was already"
                      " merged by the repo as", out)
        self.assertFalse(self.gh.called("pr", "merge"))
        on_main = self.git("show", "main:" + conductor.LEDGER.format(
            batch=BATCH), cwd=self.origin)
        self.assertIn(f'"{closing["id"]}"', on_main.split("\n")[-2])


if __name__ == "__main__":
    unittest.main()
