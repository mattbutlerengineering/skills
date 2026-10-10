# Autorun brief — maintenance:a-reap-the-test-checks-too-soon

**Provenance.** Written by the driving agent from the orchestrator's
dispatch instructions on 2026-10-10, before Capture. It records those
instructions; it is not a live user interview. Anything the instructions
did not settle is logged as an assumption in the artifact that decided
it.

## What and why

Beads `wo-0wu` (P3): `tests/test_cli.py`
`TestHarnessRun.test_a_timeout_flips_timed_out_and_reaps_the_group`
failed once on CI —
`AssertionError: True is not false : grandchild survived harness_run` —
in run `36517898314`, job `109244186130`, PR #600, 2026-09-29 03:37Z.
The same commit passed in two other CI runs and locally, and the PR did
not touch `cli.py`. The working hypothesis handed over is a timing race
in the reaping assertion on a loaded runner, in the family of the
`pid_alive` fix (#571, beads `wo-50k`,
`docs/fixes/pid-alive-answers-the-wrong-question/`).

## Scale

Maintenance run. Re-entry depth is Capture's call; the expectation is
`re-entry: implement` unless the evidence shows a design question.

## Method

- Reproduce the race deterministically before fixing it (for example by
  injecting delay), so the fix is proven rather than hoped.
- For a flake, show repeated runs of the target test under load, before
  and after, where feasible.
- Where a stage offers a recommended default, take it and log it under
  that artifact's `assumptions:`. A question with no default that the
  evidence cannot answer stops the run and is reported.

## Verification

Quote real output of `python3 -m unittest discover tests`,
`python3 lint.py`, and `python3 gates.py && python3 gates.py --selftest`.
Never fabricate evidence. Run gates again after writing docs (detector C
scans run artifacts for work-order tokens).

## Constraints

Stdlib only. Work only in the `fix/reaping-test-flake` worktree. Any edit
to a `factory_init.MIRRORS` file or `factory/templates/**` requires
`python3 factory_init.py update-manifest` and a committed manifest.

## Tracker

Do not touch beads; the orchestrator closes `wo-0wu`. No GitHub issue
exists for the defect: create one plain anchor issue for the PR's
`Closes #N` line — never #178 or #181.

## Release authorization

Push the branch by name and open one non-draft PR to `main`, body per the
protocol's "Pull request body" section. Then stop: no merge.
