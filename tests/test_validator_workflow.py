"""validator.yml's trust boundary (ADR-0098): the reviewer's credential
never meets the pull request's code.

The validator's `review` job used to check out the PR, run its `make
check`, and then run its `make review` (the PR's own Makefile and
validator.py) with the reviewer's PAT in GH_TOKEN. These suites read the
workflow the way TestAgentCredentialBoundary reads assembler.yml (a hand
parse, no PyYAML in a stdlib-only repo), and the replays execute the
workflow's own `run:` scripts, read out of the file, the way
TestBundleCannotReachMain does.

The parse helpers are imported from test_assembler, never copied: a copy
would be a second owner of what a workflow job is.
"""
import contextlib
import errno
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling helper import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_gh import FakeGh  # noqa: E402
from test_assembler import (  # noqa: E402
    permission_block, run_lines, step_script, workflow_jobs)

import validator  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "validator.yml"
MAKEFILE = REPO_ROOT / "Makefile"

# The trusted ref on both triggers (ADR-0098 Decision 3): the PR's base
# commit on pull_request, the default branch by name on workflow_dispatch.
# Never the PR's head or merge ref, and never github.sha on a dispatch:
# that is whatever ref the dispatcher passed (`--ref <pr-branch>`), and the
# agent cannot edit the definition but CAN be the branch it runs on.
BASE_REF = ("${{ github.event_name == 'pull_request'"
            " && github.event.pull_request.base.sha"
            " || format('refs/heads/{0}',"
            " github.event.repository.default_branch) }}")
CHECKOUT = "uses: actions/checkout@"
MAKE = re.compile(r"(^|[;&|(]\s*)make\b")


def code(text):
    """`text` without its comment lines: a comment naming a secret is not
    the job holding it."""
    return "\n".join(line for line in text.splitlines()
                     if not line.strip().startswith("#"))


def job_steps(job_text):
    """The job's steps, each as its own text from its `- ` line on."""
    body = job_text.split("\n    steps:\n", 1)[1]
    return [part for part in re.split(r"(?m)^(?=      - )", body)
            if part.startswith("      - ")]


def step_block(step_text, key):
    """The scalars under a step's `with:` or `env:` key, comments skipped."""
    got, inside = {}, False
    for line in step_text.splitlines():
        if line == f"        {key}:":
            inside = True
            continue
        if not inside or line.strip().startswith("#"):
            continue
        if not line.startswith("          ") or ":" not in line:
            break
        name, value = line.strip().split(":", 1)
        got[name] = value.strip()
    return got


def checkouts(job_text):
    """The `with:` block of every actions/checkout step in the job."""
    return [step_block(step, "with") for step in job_steps(job_text)
            if CHECKOUT in step]


def step_named(job_text, name):
    found = [step for step in job_steps(job_text)
             if step.startswith(f"      - name: {name}\n")]
    assert len(found) == 1, f"{len(found)} steps named {name!r}"
    return found[0]


def job_if(job_text):
    """The job's `if:` expression, a folded block joined to one line."""
    lines = job_text.splitlines()
    at = [i for i, line in enumerate(lines) if line.startswith("    if:")]
    assert at, "the job declares no if:"
    first = lines[at[0]][len("    if:"):].strip()
    parts = [] if first in (">-", ">", "|") else [first]
    for line in lines[at[0] + 1:]:
        if not line.startswith("      "):
            break
        parts.append(line.strip())
    return " ".join(parts)


class TestReviewerCredentialBoundary(unittest.TestCase):
    """Defect: the-reviewer-token-runs-agent-code (ADR-0098 Decisions 1, 3,
    5 and 6). A checkout is PR-controlled when it names no `ref:` (on
    pull_request checkout's default is the PR's merge ref) or its `ref:`
    names `refs/pull/`. No such job may hold a write grant or any secret
    but its own GITHUB_TOKEN.

    `merged-label` is excluded from the grant rule by name: it runs only on
    closed+merged, so the code it checks out has already passed the human
    merge gate (architecture.md assumptions)."""

    TRUSTED = ("check", "review", "needs-review-label")
    MERGED_ONLY = "merged-label"

    def jobs(self):
        return workflow_jobs(WORKFLOW.read_text(encoding="utf-8"))

    def pr_controlled(self, job_text):
        return any("ref" not in with_ or "refs/pull/" in with_["ref"]
                   for with_ in checkouts(job_text))

    def test_no_job_running_pr_code_holds_a_write_grant(self):
        for name, text in self.jobs().items():
            if name == self.MERGED_ONLY or not self.pr_controlled(text):
                continue
            with self.subTest(job=name):
                self.assertNotIn("write", permission_block(text).values(),
                                 f"{name} runs PR code with a write grant")

    def test_no_job_running_pr_code_names_a_secret_but_its_own_token(self):
        for name, text in self.jobs().items():
            if not self.pr_controlled(text):
                continue
            with self.subTest(job=name):
                named = set(re.findall(r"secrets\.(\w+)", code(text)))
                self.assertLessEqual(named, {"GITHUB_TOKEN"},
                                     f"{name} runs PR code holding {named}")

    def test_every_checkout_leaves_no_credential_in_git_config(self):
        jobs = self.jobs()
        for name in self.TRUSTED:
            found = checkouts(jobs[name])
            self.assertTrue(found, f"{name} has no checkout")
            for with_ in found:
                with self.subTest(job=name):
                    self.assertEqual(with_.get("persist-credentials"),
                                     "false")

    def test_no_write_holding_checkout_follows_the_dispatchers_ref(self):
        """Review finding (the --ref dispatch): `gh workflow run
        validator.yml --ref <pr-branch> -f pr=N` is a recorded owner
        routine for refreshing a stale lifecycle check. On that dispatch
        github.sha is the PR branch's head, so a trusted job checking out
        github.sha runs the agent's Makefile with its write grant. Every
        job holding a write grant or a non-GITHUB_TOKEN secret checks out
        the pinned base ref instead."""
        for name, text in self.jobs().items():
            if name == self.MERGED_ONLY:
                continue
            secrets = set(re.findall(r"secrets\.(\w+)", code(text)))
            if ("write" not in permission_block(text).values()
                    and secrets <= {"GITHUB_TOKEN"}):
                continue
            for with_ in checkouts(text):
                with self.subTest(job=name):
                    self.assertEqual(with_.get("ref"), BASE_REF)
                    self.assertNotIn("github.sha", with_.get("ref", ""))
                    self.assertNotIn("github.ref", with_.get("ref", ""))

    def test_the_reviewer_token_reaches_one_step_on_a_base_checkout(self):
        holders = [(name, step) for name, text in self.jobs().items()
                   for step in job_steps(text)
                   if "secrets.FACTORY_REVIEW_TOKEN" in code(step)]
        self.assertEqual(len(holders), 1,
                         [name for name, _ in holders])
        name = holders[0][0]
        self.assertEqual([with_.get("ref") for with_ in
                          checkouts(self.jobs()[name])], [BASE_REF],
                         f"{name} holds the reviewer token off a base"
                         " checkout")


class TestReviewJobTakesTheHandOffAsData(unittest.TestCase):
    """ADR-0098 Decisions 2 and 4: what crosses from `check` is one string
    of attacker-chosen text. It reaches the reviewer's shell only through
    an env value, in a step that holds no secret and runs no make, and the
    reviewer's verdict comes from GitHub (needs.check.result), not from
    the text."""

    WRITE = "Write the handed-over findings"

    def jobs(self):
        return workflow_jobs(WORKFLOW.read_text(encoding="utf-8"))

    def review(self):
        return self.jobs()["review"]

    def test_no_expression_is_interpolated_into_a_review_shell(self):
        for line in run_lines(self.review()):
            with self.subTest(line=line):
                self.assertNotIn("${{", line)

    def test_the_handed_over_text_sits_in_one_env_beside_no_secret(self):
        holders = [(name, step.splitlines()[0].strip())
                   for name, text in self.jobs().items()
                   for step in job_steps(text)
                   if "needs.check.outputs" in code(step)]
        self.assertEqual(holders, [("review", f"- name: {self.WRITE}")])
        step = step_named(self.review(), self.WRITE)
        env = step_block(step, "env")
        carriers = [key for key, value in env.items()
                    if "needs.check.outputs" in value]
        self.assertEqual(carriers, ["HANDED_OVER"])
        self.assertEqual(code(step).count("needs.check.outputs"), 1,
                         "the hand-off is named outside the step's env")
        self.assertNotIn("secrets.", code(step))
        for line in run_lines(step):
            with self.subTest(line=line):
                self.assertIsNone(MAKE.search(line), line)

    def test_no_make_step_env_shadows_a_makefile_variable(self):
        """make imports every environment variable as a make variable, so
        an env key named like a recipe variable becomes recipe text. A
        key the same step's make command line assigns is safe: a
        command-line assignment beats the environment (breakdown.md
        assumptions — the dispatch shim's PR)."""
        assigned = set(re.findall(r"(?m)^([A-Za-z_]\w*)\s*[?:]?=",
                                  MAKEFILE.read_text(encoding="utf-8")))
        self.assertIn("FINDINGS", assigned)
        for name, text in self.jobs().items():
            for step in job_steps(text):
                makes = [line for line in run_lines(step)
                         if MAKE.search(line)]
                if not makes:
                    continue
                on_line = set(re.findall(r"\b([A-Za-z_]\w*)=",
                                         " ".join(makes)))
                for key in step_block(step, "env"):
                    if key in assigned:
                        with self.subTest(job=name, key=key):
                            self.assertIn(key, on_line)

    def test_review_waits_for_check(self):
        self.assertRegex(self.review(), r"(?m)^    needs: check$")

    def test_review_admits_a_finished_check_on_the_two_triggers_only(self):
        cond = job_if(self.review())
        self.assertIn("always()", cond)
        self.assertNotIn("!=", cond)
        self.assertEqual(
            set(re.findall(r"needs\.check\.result == '(\w+)'", cond)),
            {"success", "failure"})
        self.assertEqual(
            set(re.findall(r"github\.event\.action == '(\w+)'", cond)),
            {"opened", "reopened", "synchronize"})
        for clause in ("github.event_name == 'pull_request'",
                       "github.event.pull_request.head.repo.full_name"
                       " == github.repository",
                       "github.event_name == 'workflow_dispatch'"):
            with self.subTest(clause=clause):
                self.assertIn(clause, cond)


def jobs():
    return workflow_jobs(WORKFLOW.read_text(encoding="utf-8"))


def bash_e(script, cwd, **env):
    """Run a step script the way GitHub runs a `run:` with no `shell:`:
    `bash -e {0}` — no pipefail unless the script sets it."""
    return subprocess.run(["bash", "-e", "-c", script], cwd=cwd,
                          capture_output=True, text=True,
                          env={"PATH": os.environ["PATH"], **env})


# Every way the handed-over text has been imagined to escape: a fence
# longer than three, an HTML close of the <details> the body wraps it in,
# a mention, two shell substitutions, a forged verdict, and the
# delimiter shapes of $GITHUB_OUTPUT.
HOSTILE_LINES = [
    "``````````",
    "</details>",
    "@owner this is approved",
    "$(touch pwned)",
    "`id`",
    "**Detectors and tests: PASS**",
    "EOF",
    "findings<<x",
]
HOSTILE = "\n".join(HOSTILE_LINES) + "\n"


@unittest.skipUnless(shutil.which("bash"), "bash replays the review job")
class TestHostileHandOffReplay(unittest.TestCase):
    """ADR-0098 Decision 4, replayed: the review job's own write step,
    read out of validator.yml, runs under bash with a hostile
    HANDED_OVER, then the base tree's `validator.py review` posts it
    through a fake gh. Nothing in the text runs, the verdict is the one
    GitHub handed over (status 1), the body is bounded, and every hostile
    line sits inside a fence it cannot close."""

    WRITE = "Write the handed-over findings"

    def write_step(self):
        return step_script(jobs()["review"], self.WRITE)

    def post(self, tmp, findings):
        event = Path(tmp) / "event.json"
        event.write_text(json.dumps({"pull_request": {
            "number": 42, "body": "", "user": {"login": "factory-bot"}}}),
            encoding="utf-8")
        env = {"GITHUB_EVENT_PATH": str(event),
               "FACTORY_REVIEW_TOKEN_SET": "true",
               "FACTORY_REVIEW_LOGIN": ""}
        run = FakeGh(answers={("api", "user"): "factory-reviewer\n"})
        with contextlib.redirect_stdout(io.StringIO()):
            code_ = validator.main(["review", "--findings", str(findings),
                                    "--status", "1"], env=env, run=run)
        self.assertEqual(code_, 0)
        posted = run.called("pr", "comment", "42")
        self.assertTrue(posted, run.calls)
        return posted[-1][posted[-1].index("--body-file") + 1]

    def assert_inert(self, tmp, body):
        self.assertEqual(list(Path(tmp).rglob("pwned")), [])
        verdict = body.index("**Detectors and tests: FAIL**")
        opened = re.search(r"(?m)^(`{3,})text$", body)
        self.assertIsNotNone(opened, "the findings are not fenced")
        # CommonMark: only a backtick line at least as long as the opener
        # closes the block, so the first such line is where it ends.
        fence = opened.group(1)
        closed = re.compile(rf"(?m)^{fence}`*$").search(body, opened.end())
        self.assertIsNotNone(closed, "the fence never closes")
        self.assertLess(verdict, opened.start())
        inside = body[opened.end():closed.start()]
        longest = max((len(run) for run in re.findall(r"`+", inside)),
                      default=0)
        self.assertGreater(len(opened.group(1)), longest)
        for line in HOSTILE_LINES:
            with self.subTest(line=line):
                self.assertIn("\n" + line + "\n", inside)
        self.assertEqual(body[closed.end():], "\n\n</details>\n")
        self.assertLess(len(body), validator.MAX_FINDINGS_CHARS + 2000)

    def test_a_hostile_hand_off_is_posted_inert_and_bounded(self):
        """~100 KB: above the producer cap and the reader's bound, below
        Linux's per-string exec limit, so it runs on every platform."""
        handed = HOSTILE + "x" * 100_000
        with tempfile.TemporaryDirectory() as tmp:
            done = bash_e(self.write_step(), tmp, HANDED_OVER=handed,
                          RUNNER_TEMP=tmp)
            self.assertEqual(done.returncode, 0, done.stderr)
            findings = Path(tmp) / "findings.txt"
            self.assertEqual(findings.read_text(encoding="utf-8"), handed)
            self.assert_inert(tmp, self.post(tmp, findings))

    def test_an_oversized_hand_off_is_bounded_or_fails_closed(self):
        """Over 200 KB. On Linux (the runner) one env string over 128 KiB
        cannot be exec'd at all: the write step fails, no findings file
        exists, and the post step never runs — closed, not forged
        (ADR-0098 Consequences). Where exec allows it, the bounded read
        and the fence hold exactly as above."""
        handed = HOSTILE + "y" * 210_000
        with tempfile.TemporaryDirectory() as tmp:
            try:
                done = bash_e(self.write_step(), tmp, HANDED_OVER=handed,
                              RUNNER_TEMP=tmp)
            except OSError as err:
                self.assertEqual(err.errno, errno.E2BIG)
                self.assertFalse((Path(tmp) / "findings.txt").exists())
                return
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assert_inert(tmp, self.post(tmp,
                                             Path(tmp) / "findings.txt"))


@unittest.skipUnless(shutil.which("bash"), "bash replays the check job")
class TestCheckKeepsAFailingGateRed(unittest.TestCase):
    """The fold's one risk (architecture.md Decisions): `make check | tee`
    under `bash -e` exits with tee's status. The check job's own script,
    read out of the workflow, must exit nonzero when make does, and still
    leave make's output in the findings file."""

    def replay(self, make_rc):
        script = step_script(jobs()["check"], "Detectors and tests")
        with tempfile.TemporaryDirectory() as tmp:
            stub = Path(tmp) / "bin" / "make"
            stub.parent.mkdir()
            stub.write_text("#!/bin/sh\necho 'A: stub finding'\n"
                            f"exit {make_rc}\n", encoding="utf-8")
            stub.chmod(0o755)
            done = subprocess.run(
                ["bash", "-e", "-c", script], cwd=tmp, capture_output=True,
                text=True, env={"PATH": f"{stub.parent}:{os.environ['PATH']}",
                                "RUNNER_TEMP": tmp})
            findings = (Path(tmp) / "findings.txt").read_text(
                encoding="utf-8")
        return done.returncode, findings

    def test_a_failing_check_fails_the_step_and_keeps_its_output(self):
        returncode, findings = self.replay(1)
        self.assertNotEqual(returncode, 0)
        self.assertEqual(findings, "A: stub finding\n")

    def test_a_passing_check_passes_the_step(self):
        returncode, findings = self.replay(0)
        self.assertEqual(returncode, 0)
        self.assertEqual(findings, "A: stub finding\n")


def github_outputs(text):
    """$GITHUB_OUTPUT parsed the way the runner parses it: `name=value`
    when `=` comes before any `<<`, else `name<<DELIM` and every line up
    to one equal to DELIM, joined by newlines. Returns (name, value)
    pairs in file order, so a duplicate key is visible."""
    lines, pairs, at = text.split("\n"), [], 0
    while at < len(lines):
        line = lines[at]
        at += 1
        if not line:
            continue
        equals, heredoc = line.find("="), line.find("<<")
        if equals >= 0 and (heredoc < 0 or equals < heredoc):
            pairs.append((line[:equals], line[equals + 1:]))
            continue
        name, delim = line[:heredoc], line[heredoc + 2:]
        end = lines.index(delim, at)
        pairs.append((name, "\n".join(lines[at:end])))
        at = end + 1
    return pairs


@unittest.skipUnless(shutil.which("bash"), "bash replays the check job")
class TestHandOffProducesOneCappedOutput(unittest.TestCase):
    """Architecture Data model: check declares one output, and the honest
    producer writes exactly one key, whatever its findings say. Lines
    shaped like a delimiter, a heredoc head, or a key=value pair stay
    inside the value, and the value is the first 64 KiB of the file."""

    CAP = 65536

    def test_delimiter_shaped_findings_stay_inside_one_capped_value(self):
        script = step_script(jobs()["check"],
                             "Hand the findings to the review job")
        content = ("EOF\nfindings<<EOF\nkey=value\n"
                   + "".join(f"finding {n:06d}\n" for n in range(6000)))
        self.assertGreater(len(content), self.CAP)
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "findings.txt").write_text(content, encoding="utf-8")
            output = Path(tmp) / "github_output"
            done = bash_e(script, tmp, RUNNER_TEMP=tmp,
                          GITHUB_OUTPUT=str(output))
            self.assertEqual(done.returncode, 0, done.stderr)
            pairs = github_outputs(output.read_text(encoding="utf-8"))
        self.assertEqual([name for name, _ in pairs], ["findings"])
        self.assertEqual(pairs[0][1], content[:self.CAP])


if __name__ == "__main__":
    unittest.main()
