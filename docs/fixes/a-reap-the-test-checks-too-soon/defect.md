---
stage: capture
run: maintenance:a-reap-the-test-checks-too-soon
date: 2026-10-10
re-entry: implement
assumptions: ["no live interview: the brief is the orchestrator's dispatch instructions (autorun-brief.md); every answer below is from the CI log and this session's experiments", "re-entry implement (the skill's default for a scoped fix): the change is a test-helper grace budget, no design decision", "class scope: the two verbatim sibling grace loops (tests/test_cli_process_reaping.py, tests/test_charter_replay.py) are fixed in the same run, as the pid_alive precedent did, because they share the mechanism byte for byte", "the late-death regression test is added to tests/test_cli.py only (the copy that flaked); the siblings get a one-off RED/GREEN in verification.md instead, to avoid adding ~5 s of real waiting to the suite"]
---

# Defect: a reap the test checks too soon

## Defect (or Condition)

`TestHarnessRun.assert_grandchild_reaped` (tests/test_cli.py) gives a
grandchild that `harness_run` has SIGKILLed **two seconds of wall-clock
time** to disappear, then asserts it is gone:

```python
deadline = time.time() + 2
while time.time() < deadline and pid_alive(pid):
    time.sleep(0.05)
self.assertFalse(pid_alive(pid), "grandchild survived harness_run")
```

The property under test is *harness_run signals the whole group*. The
fake grandchild is `sleep 300`, so a grandchild that was never signalled
lives for 300 s. What the assertion actually checks is narrower: that a
signalled grandchild has also **finished dying, as observed by the test,
within 2 s of wall time**. `cli.harness_run` makes no latency promise —
its own docstring says killed grandchildren are "signalled, not reaped".

Expected: a grandchild that was signalled passes; one that was not fails.
Observed: a grandchild whose death is observed later than 2 s after the
helper starts looking fails as a "survivor".

## Reproduction / Evidence

**The CI failure.** Run `36517898314` attempt 1, job `109244186130`
(PR #600, head `ba34095`), `ubuntu-24.04` runner image `20260920.314`:

```
FAIL: test_a_timeout_flips_timed_out_and_reaps_the_group (test_cli.TestHarnessRun...)
  File ".../tests/test_cli.py", line 610, in test_a_timeout_flips_timed_out_and_reaps_the_group
    self.assert_grandchild_reaped()
  File ".../tests/test_cli.py", line 585, in assert_grandchild_reaped
    self.assertFalse(pid_alive(pid), "grandchild survived harness_run")
AssertionError: True is not false : grandchild survived harness_run
Ran 1827 tests in 17.568s
FAILED (failures=1)
```

Attempt 2 of the same run (job `109244703416`) passed:
`Ran 1827 tests in 17.479s`. At `ba34095`, `harness_run`,
`assert_grandchild_reaped`, `process_state` and `pid_alive` are
byte-identical to `main` (the PR's `cli.py` hunks are elsewhere), so the
failure is not something PR #600 introduced. The line numbers prove the
post-#571 `process_state` predicate was in force: on Linux it reads
`/proc/<pid>/stat` and calls a zombie dead, so the grandchild had a
process-table entry in a **non-zombie** state when the 2 s ran out.

**Deterministic reproduction** (work item 1): a real `sleep 300` whose
SIGKILL is delivered 2.5 s after the helper starts looking — a correctly
signalled grandchild whose death lands late — fails the unmodified helper
every time with `grandchild survived harness_run`. Quoted RED/GREEN in
`verification.md`.

## Root-cause hypothesis

**Demonstrated:** the assertion fails whenever the interval between the
helper starting to look and the grandchild's death being visible exceeds
2 s of `time.time()`, regardless of whether `harness_run` signalled it.

**Hypothesis, not finding:** what stretched that interval on the runner.
Two candidates, neither measured on the runner:

1. **A wall-clock step.** The deadline is `time.time()`, which steps when
   time sync corrects a freshly provisioned VM's clock; a forward step
   shrinks the 2 s window, possibly to one poll. Weak circumstantial
   support only: the failing attempt's wall span from
   `python3 -m unittest` to `FAILED` is 18.98 s against a monotonic
   `Ran ... in 17.568s` (1.41 s over), where the passing attempt's is
   18.01 s against 17.479 s (0.53 s over). That ~0.9 s gap is equally
   explained by a colder start, so it proves nothing.
2. **Scheduling delay.** The SIGKILLed `sleep` must be scheduled to run
   its exit; on a 4-vCPU runner VM with steal time it may not be for a
   while.

Either way the fix is the same: the window must be sized to the failure
mode it detects (300 s of survival), not to how fast a death usually is,
and must be measured on a clock that cannot step.

## Blast radius

Test-only. No shipped module changes; `cli.py` is a
`factory_init.MIRRORS` entry and is **not** touched, so no manifest
regeneration. The cost is a red CI check on unrelated PRs (PR #600 was
re-run to green), and a reviewer's time spent deciding it was a flake.

Three verbatim copies of the 2 s grace loop exist and all carry the
defect: `tests/test_cli.py` (`assert_grandchild_reaped`, two tests),
`tests/test_cli_process_reaping.py` and `tests/test_charter_replay.py`
(each `assert_grandchild_reaped(self, watcher)`). Found with
`grep -rn "time.time() + 2" tests/`, which returns exactly those three
grace loops and the `test_cli.py` PID-file wait.

## Ruled out

- **Zombie-blindness.** Fixed by #571 and in force in the failing run
  (see the line-number argument above): a zombie reads dead on Linux.
- **A PR #600 regression.** `harness_run` and the helper are identical at
  the failing head and on `main`; attempt 2 of the same run passed.
- **Work already in flight.** No open PR touches these helpers (only
  #618 is open, a harness-registry change); the older reaping-flake
  branches (`fix/cli-test-flake-under-load` #529,
  `fix/cli-test-flake-siblings` #531,
  `fix/charter-replay-reaping-flake` #551) are all merged, and fixed the
  *timeout* side (readiness-gated clock), not this grace loop.
- **PID reuse.** Not re-measured on the runner. The precedent run refuted
  it on darwin by three orders of magnitude (29 pids/s under the suite's
  load against ~25000/s needed). Even the kernel's smallest default
  `pid_max` of 32768 would need ~8000 pids/s to wrap inside the 4 s
  window, and systemd on 64-bit Ubuntu raises it far higher. Recorded as
  reasoning, not a runner measurement.
- **harness_run failing to signal the grandchild.** Not reproduced: the
  fake's `sleep 300 &` runs without job control and so stays in the
  leader's group, and the sibling dead-leader test exercises the same
  kill on every run. If the kill were missing, the grandchild would
  survive 300 s and the larger window still fails — the mutation check in
  work item 2 proves that.

## Work items

- [ ] **Reproduce and pin the late death** — add a regression test to
  `tests/test_cli.py` that hands `assert_grandchild_reaped` a real
  process SIGKILLed 2.5 s after it starts looking.
  - Accept: the test fails against the current helper with
    `grandchild survived harness_run`, and passes after the fix.
- [ ] **Widen and de-step the window in `tests/test_cli.py`** — grace
  budget sized to the 300 s survival it detects, measured on
  `time.monotonic()`.
  - Accept: `tests.test_cli` green; with the group kill mutated out of
    `harness_run`, the two reaping tests still fail with
    `grandchild survived harness_run` (mutation reverted afterwards).
- [ ] **Same fix in the two sibling copies** —
  `tests/test_cli_process_reaping.py`, `tests/test_charter_replay.py`.
  - Accept: a one-off late-death probe fails each unmodified helper and
    passes each fixed one; both modules green (charter replay offline
    half only — never the live replay).
- [ ] **Battery green, and the flake loop** — the repo's verification
  set, plus the target test looped 50x under CPU load before and after.
  - Accept: suite OK, `lint: 0 problem(s)`, `gates: 0 problem(s)`,
    `selftest: ok`, quoted in `verification.md`.

## Notes

- 2026-10-10: the three grace-loop helpers are verbatim duplicates, as
  were the three `pid_alive` copies before them — the second time one
  defect has had to be fixed three times. Logged, not fixed: extracting a
  shared test helper is a design change outside `re-entry: implement`,
  and `one_owner.py` excludes `tests/**`.
