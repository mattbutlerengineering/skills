---
stage: verify
run: maintenance:a-reap-the-test-checks-too-soon
date: 2026-10-10
---

# Verification

Every criterion is a work item's `Accept:` line in `defect.md` — a
maintenance run has no PRD. Evidence is quoted command output from this
machine (macOS, Darwin 25.5.0, Python 3.14.6, 8 cores).

## 1. The late death is reproduced and pinned

**Criterion:** a regression test fails against the current helper with
`grandchild survived harness_run`, and passes after the fix.

The test, `TestHarnessRun.test_a_grandchild_that_dies_late_is_not_a_survivor`,
writes the PID of a real `sleep 300` to the PID file and SIGKILLs it
2.5 s after `assert_grandchild_reaped` starts looking — a correctly
signalled grandchild whose death lands after the old 2 s window. The
helper's own predicate (`pid_alive`, the post-#571 one) does the
observing; nothing is faked.

**RED**, against the unmodified helper — the same message as the CI
failure in run `36517898314`:

```
    self.assertFalse(pid_alive(pid), "grandchild survived harness_run")
AssertionError: True is not false : grandchild survived harness_run

Ran 1 test in 2.097s

FAILED (failures=1)
```

**GREEN**, after the fix, three runs:

```
Ran 1 test in 2.620s  OK
Ran 1 test in 2.605s  OK
Ran 1 test in 2.599s  OK
```

and ten more in a loop after the battery: `late-death test: 10/10 OK`.

Deterministic by construction: the kill is scheduled at 2.5 s and the old
window closes at 2.0 s, so the RED does not depend on load.

## 2. The window is widened and de-stepped without losing its teeth

**Criterion:** `tests.test_cli` green; with the group kill mutated out of
`harness_run`, the two reaping tests still fail with
`grandchild survived harness_run`; mutation reverted.

```
Ran 89 tests in 6.683s

OK
```

**Mutation**: `os.killpg(process.pid, signal.SIGKILL)` in `cli.py`
replaced with a leader-only `process.kill()`. The mutation is proven to
have landed (the grep printed the mutated line) before the tests ran:

```
202:            process.kill()  # MUTATION: leader only
FAIL: test_a_timeout_flips_timed_out_and_reaps_the_group (...)
AssertionError: True is not false : grandchild survived harness_run
FAIL: test_a_dead_leaders_grandchild_is_still_reaped (...)
AssertionError: True is not false : grandchild survived harness_run
Ran 2 tests in 63.406s
FAILED (failures=2)
cli.py restored (no diff)
```

The wider window still catches an unsignalled grandchild; it now takes
~30 s per test to say so on that failure path. The passing path is
unchanged in speed — the loop exits on the first poll that sees the
death. `cli.py` was restored from a copy and `git diff --stat cli.py` is
empty, so the mirrored file is untouched and no manifest regeneration is
due.

## 3. The sibling copies take the same fix

**Criterion:** a one-off late-death probe fails each unmodified helper
and passes each fixed one; both modules green.

The probe (a scratch script, not committed) builds each class's
`assert_grandchild_reaped(watcher)` with a finished watcher thread
holding the PID of a real `sleep 300` SIGKILLed 2.5 s in.

RED, before:

```
test_cli_process_reaping: RED  True is not false : grandchild survived run_single_query
test_charter_replay: RED  True is not false : grandchild survived claude_runner
```

GREEN, after:

```
test_cli_process_reaping: GREEN (late death accepted)
test_charter_replay: GREEN (late death accepted)
```

The three modules together:

```
Ran 156 tests in 16.016s

OK
```

`grep -rn "time.time() + 2" tests/` now returns nothing. The live
charter replay was never run (real model spend); `tests/test_charter_replay.py`
drives fake `claude` executables only.

## 4. Battery green, and the flake loop

**Criterion:** suite OK, lint 0, gates 0, selftest ok; target test looped
50x under CPU load before and after.

```
Ran 1945 tests in 34.787s

OK
lint: 0 problem(s) across 25 skills
gates: 0 problem(s)
selftest: ok
```

1945 is `origin/main`'s 1944 (counted by test discovery over a
`git archive` export) plus this run's one regression test.

**Flake loop**, `test_a_timeout_flips_timed_out_and_reaps_the_group`,
50 consecutive runs with 16 `yes > /dev/null` burners on 8 cores:

```
[before] load during run: { 74.86 34.81 21.57 }
[before] 0 failure(s) in 50 runs with 16 CPU burners

[after] load during run: { 134.77 71.04 39.87 }
[after] 0 failure(s) in 50 runs with 16 CPU burners
```

Read honestly: CPU load alone **does not reproduce** the CI failure on
this machine, so the before/after loop shows no regression, not a fix.
The fix is proven by §1 and §3, where the late death is injected, not by
this loop.

`one_owner.py` (a review pre-pass, not a gate) reports 6 problems, none
in a file this run touched — it excludes `tests/**`.

## Not verified, and why

- **What delayed the death on the runner.** The two candidates in
  `defect.md` (a wall-clock step; scheduling delay on the VM) are
  unmeasured. The fix covers both — `time.monotonic()` cannot step, and
  30 s is 15x the old window — but which one fired is not known.
- **Linux.** The `/proc` branch of `pid_alive` did not run here; CI on
  the PR runs it.
- **A death slower than 30 s.** Not covered by design: the window must
  stay under the fakes' 300 s survival to mean anything.
