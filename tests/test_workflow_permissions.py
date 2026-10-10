"""Every workflow job's GITHUB_TOKEN grant, pinned.

A job that reaches the issue tracker with `contents: read` alone does not
fail in CI. It fails in production, once, on a schedule, in a run nobody
is watching -- and this repo has already paid for that: issue #297 was
the weekly toolsmith harvest silently listing no PRs because
toolsmith-mine.yml never granted `pull-requests: read`. The fix that
shipped (PR #303) came with a regression test for that one workflow.
Six other jobs escalate their grants and had nothing.

The gap is easy to miss because something *does* go red when a grant is
deleted -- the payload mirror stops matching its root file. That failure
is about lockstep, not about permissions, and it disappears the moment
the edit follows this repo's documented procedure and runs
`python3 factory_init.py update-manifest`, which syncs the payload copy.
With the mirror synced, dropping `issues: write` from cost-report.yml,
gate-digest.yml, assembler.yml and validator.yml leaves the entire
battery green.

Why a recorded table rather than a derivation from what each job runs:
two things defeat the derivation. Jobs reach the tracker through `make`
targets whose recipes pass a VERB (`validator.py lifecycle` writes issue
labels, `validator.py review` posts a PR comment), so module granularity
over-approximates; and workflow comments mention `make` targets the job
does not run, so text matching over-approximates again. Both directions
of over-approximation turn correct workflows red, which is worse than
the hole. A grant is also exactly the kind of thing that should not
change quietly: making it a two-file edit is the point, not a cost.

Root workflows only. gates' lockstep tests already pin each payload copy
byte-for-byte against its root file, so asserting here would be a second
owner of that claim.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"

# workflow -> job -> (effective permissions, why the job needs them).
# "Effective" means the job's own `permissions:` block when it has one,
# and the workflow-level block otherwise -- the same resolution GitHub
# applies. Closed against the directory in both directions below, so a
# new workflow or a new job cannot land unrecorded.
EXPECTED = {
    "assembler.yml": {
        "dispatch": ({"contents": "read", "issues": "write"},
                     "resolves the order and flips wo:ready-for-agent ->"
                     " wo:in-progress (the claim) before any agent code runs"),
        "agent": ({"contents": "read"},
                  "runs the chartered agent, and nothing else -- the agent"
                  " executes code it wrote, so its job holds no write grant"
                  " (ADR-0077: the token is the push boundary, not the tool"
                  " allowlist)"),
        "deliver": ({"contents": "write", "pull-requests": "write",
                     "issues": "write", "actions": "write"},
                    "from a fresh checkout, pushes the order's branch out of"
                    " the agent's bundle, opens its PR, commits the spend"
                    " row, flips wo:failed, and hands off to the validator"
                    " with `gh workflow run` (WO-0030) -- GitHub suppresses"
                    " the pull_request event for a PR the GITHUB_TOKEN"
                    " opened, so the dispatch is the only way the validator"
                    " ever runs"),
    },
    "charter-replay.yml": {
        "replay": ({"contents": "read"}, "runs `make check` and nothing else"),
    },
    "cost-report.yml": {
        "report": ({"contents": "read", "issues": "write"},
                   "files the weekly cost report with `gh issue create`"),
    },
    "design.yml": {
        "web-quality": ({"contents": "read"}, "runs Playwright, writes nothing"),
    },
    "gate-digest.yml": {
        "digest": ({"contents": "write", "issues": "write"},
                   "commits the appended gate-latency ledger rows, and"
                   " creates/edits/pins the digest issue"),
    },
    "sweeps.yml": {
        "label-drift": ({"contents": "read", "issues": "write"},
                        "files one intake issue on drift"),
        "reconcile": ({"contents": "read", "issues": "write"},
                      "files the cross-plane reconciliation report"),
        "sentry": ({"contents": "read", "issues": "write"},
                   "files one intake issue per unresolved error"),
    },
    "toolsmith-mine.yml": {
        "mine": ({"contents": "read", "issues": "write",
                  "pull-requests": "read"},
                 "reads the PR listing it harvests (#297) and posts the"
                 " queue issue"),
    },
    "validator.yml": {
        "check": ({"contents": "read", "pull-requests": "read"},
                  "runs `make check`; reads the dispatched PR to synthesize"
                  " its event"),
        "review": ({"contents": "read", "pull-requests": "write"},
                   "posts the review comment on the PR"),
        "needs-review-label": ({"contents": "read", "issues": "write",
                                "pull-requests": "read"},
                               "applies wo:needs-review to the issue; reads"
                               " the dispatched PR to synthesize its event"),
        "merged-label": ({"contents": "read", "issues": "write"},
                         "applies wo:merged to the issue"),
    },
}

JOB_HEAD = re.compile(r"^  ([\w-]+):$")


def scalar_block(lines, start, indent):
    """The `key: value` pairs of a block, skipping comments and stopping
    at the first line that is not one."""
    got, i = {}, start
    while i < len(lines) and lines[i].startswith(indent):
        stripped = lines[i].strip()
        if stripped.startswith("#"):
            i += 1
            continue
        if ":" not in stripped:
            break
        key, value = stripped.split(":", 1)
        got[key] = value.strip()
        i += 1
    return got


def job_permissions(path):
    """{job: effective permissions} for one workflow file.

    A hand parse, like every other workflow reader here -- this repo is
    stdlib-only and there is no PyYAML to reach for. It fails rather than
    returning {} when it finds no jobs, because the tests below assert
    inside loops over it.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    top, jobs, job, in_jobs = {}, {}, None, False
    for i, line in enumerate(lines):
        if line.rstrip() == "permissions:" and not in_jobs:
            top = scalar_block(lines, i + 1, "  ")
        elif line.rstrip() == "jobs:":
            in_jobs = True
        elif in_jobs and JOB_HEAD.match(line):
            job = JOB_HEAD.match(line).group(1)
            jobs[job] = dict(top)
        elif in_jobs and job and line.strip() == "permissions:":
            jobs[job] = scalar_block(lines, i + 1, "      ")
    return jobs


class TestWorkflowPermissions(unittest.TestCase):
    def parsed(self):
        found = {p.name: job_permissions(p)
                 for p in sorted(WORKFLOWS.glob("*.yml"))}
        self.assertTrue(found, f"no workflows parsed out of {WORKFLOWS}")
        for name, jobs in found.items():
            self.assertTrue(jobs, f"parsed no jobs out of {name}")
        return found

    def test_every_job_holds_exactly_its_recorded_grant(self):
        """The whole grant, not just the presence of one key. A job that
        gains `contents: write` it does not need is as much a finding as
        one that loses the `issues: write` it does."""
        for name, jobs in self.parsed().items():
            for job, perms in jobs.items():
                with self.subTest(workflow=name, job=job):
                    # An unrecorded job is the closure test's finding, not
                    # this one's; reporting it as a bare KeyError here would
                    # bury the readable failure under a traceback.
                    recorded = EXPECTED.get(name, {}).get(job)
                    if recorded is None:
                        continue
                    expected, why = recorded
                    self.assertEqual(perms, expected, why)

    def test_the_table_names_every_workflow_and_every_job(self):
        """Forward closure: a new workflow, or a new job in an existing
        one, is unrecorded until someone records it. Without this the
        table is a list of the jobs that happened to exist the day it was
        written, and the next scheduled job ships ungoverned."""
        found = self.parsed()
        self.assertEqual(sorted(found), sorted(EXPECTED))
        for name, jobs in found.items():
            self.assertEqual(sorted(jobs), sorted(EXPECTED[name]), name)

    def test_the_table_names_nothing_that_is_gone(self):
        """Reverse closure: a workflow or job deleted from the tree must
        be deleted from the table too, or the table starts describing a
        repo that no longer exists."""
        found = self.parsed()
        for name, jobs in EXPECTED.items():
            self.assertIn(name, found)
            for job in jobs:
                self.assertIn(job, found[name], name)

    def test_a_dropped_grant_is_what_this_catches(self):
        """The defect, replayed against the assertion rather than the
        tree: #297's shape is a grant that quietly goes missing, and the
        mirror-lockstep tests that appear to cover it stop firing as soon
        as the edit runs `factory_init.py update-manifest` like the
        contributing procedure says to."""
        perms, why = EXPECTED["cost-report.yml"]["report"]
        without = {k: v for k, v in perms.items() if k != "issues"}
        with self.assertRaises(self.failureException):
            self.assertEqual(without, perms, why)


if __name__ == "__main__":
    unittest.main()
