---
stage: capture
run: maintenance:a-permission-drop-nothing-fails-on
date: 2026-08-30
re-entry: implement
intake: #419
assumptions:
  - "The fix is a recorded per-job table, not a derivation from what each job runs. The derivation was built first and is reproduced below with the two over-approximations that killed it; recording the attempt rather than only the conclusion is the point, because the next person to look at this will have the same idea."
  - "Root workflows only. gates' lockstep tests already pin each payload copy byte-for-byte to its root file, so asserting the payload's permissions here would be a second owner of that claim (ADR-0061)."
  - "The grant each job needs is read off what the job does, not off a GitHub permissions reference. Where a grant is non-obvious -- assembler's `actions: write` -- the reason recorded in the table is the one the workflow's own comment gives."
---

# Defect: a permission drop nothing fails on

Filed as intake issue #419 on 2026-08-30.

## Defect

Six workflow jobs escalate their `GITHUB_TOKEN` permissions above the
repo-level default, and the escalation can be deleted with a green
battery.

```
$ # delete `issues: write` from cost-report.yml, gate-digest.yml,
$ # assembler.yml and validator.yml, then do what CLAUDE.md says to do
$ # after any mirrored edit:
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)
$ python3 -m unittest discover tests
Ran 1346 tests ... OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
```

Each of those four jobs exists to write to the tracker:

| job | what it writes |
| --- | --- |
| `cost-report.yml:report` | the weekly cost report, via `gh issue create` |
| `gate-digest.yml:digest` | creates, edits and pins the digest issue |
| `assembler.yml:dispatch` | flips `wo:in-progress` / `wo:failed` |
| `validator.yml:needs-review-label`, `:merged-label` | applies `wo:needs-review`, `wo:merged` |

## Why it reads as covered

Deleting a grant does turn something red:

```
FAIL: test_every_mirrored_root_file_matches_its_payload_copy (mirror='.github/workflows/cost-report.yml')
FAIL: test_the_payload_cost_report_workflow_is_the_mirror_of_this_repo_s
```

Those are lockstep failures. They assert that the two copies agree, not
that either copy is right, and they stop firing the moment the edit is
completed properly with `update-manifest`. The net catches the
half-finished edit and passes the finished one.

Two jobs are genuinely covered:
`sweeps.yml` by `test_it_can_write_issues_and_only_read_code`, and
`toolsmith-mine.yml` by `tests/test_rejection_mining.py:304`. The other
six had nothing.

## Precedent

Issue #297 was this defect, in production: the weekly toolsmith harvest
listed no PRs because `toolsmith-mine.yml` never granted
`pull-requests: read`. It failed on a schedule, silently, in a run
nobody watches. PR #303 fixed it and added a regression test covering
that one workflow.

## The derivation that was tried and rejected

The obvious fix is to derive the needed grant from what the job runs:
find the `make` targets in the job's steps, resolve each to the module
its recipe runs, and call a module tracker-writing if its source builds a
`gh` argv like `["issue", "create"]`. That was built. It reports:

```
tracker-writing modules: ['gate_digest', 'label_sync', 'rejection_mining', 'sweeps', 'validator']
MISSING validator.yml:check needs issues: write (make review)
MISSING validator.yml:review needs issues: write (make review)
```

Both are wrong, for two independent reasons:

1. **Verb granularity.** `validator.py lifecycle` writes issue labels;
   `validator.py review` posts a PR comment. The Makefile recipe carries
   the verb, the module does not, so classifying at module granularity
   marks the `review` job as needing `issues: write`.
2. **Comments.** `validator.yml:check` was flagged because line 75 — a
   comment in the gap before the next job — says "ANY other caller of
   `make review`". Text matching cannot tell a comment from a step.

Both errors turn a correct workflow red. A test that cries wolf about
permissions is worse than the hole, because the first thing a maintainer
does with it is delete it.

## Work items

1. A per-job effective-permissions table, with a reason per entry.
   **Accept:** dropping `issues: write` from any of the four jobs fails
   by name, with the reason in the message, after `update-manifest`.
2. Closure in both directions against the workflow directory.
   **Accept:** a new workflow, a new job, and a table entry for a
   deleted job each fail.
3. No false failure on the current tree. **Accept:** full battery green.
