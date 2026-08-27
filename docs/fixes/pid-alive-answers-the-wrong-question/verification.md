---
stage: verify
run: maintenance:pid-alive-answers-the-wrong-question
date: 2026-08-27
---

# Verification

Every criterion below comes from a work item's `Accept:` line in
`defect.md` — a maintenance run has no PRD to draw from. Evidence is
quoted command output, not a summary of it.

## 1. The CLI copy is pinned and fixed

**Criterion:** the new test fails against the current predicate for the
right reason, and passes after the fix; `tests.test_cli_process_reaping`
is green.

**RED**, against the unmodified predicate:

```
  File ".../tests/test_cli_process_reaping.py", line 173, in
      test_an_uncollected_dead_process_is_not_alive
    self.assertFalse(pid_alive(pid),
                     "a terminated process must read as dead")
AssertionError: True is not false : a terminated process must read as dead

Ran 1 test in 0.002s

FAILED (failures=1)
```

The failure is the intended one. The `os.kill(pid, 0)` precondition on
the line above did not raise, so the process-table entry was present:
the test really was in the zombie state and not passing for the
uninteresting reason that the pid had already gone.

**GREEN**, after the fix:

```
Ran 1 test in 0.007s

OK
```

**Whole suite:**

```
Ran 4 tests in 3.264s

OK
```

## 2. The charter-replay copy is pinned and fixed

**Criterion:** the new test fails first and passes after; the offline
half of `tests.test_charter_replay` is green; the live replay is never
run.

This copy was fixed before its test was written, so a RED could not be
observed in passing. Rather than assert one, the naive predicate was
restored in that file alone, the test run, and the fix put back:

```
naive predicate restored for the RED check
=== RED (naive predicate) ===
Ran 1 test in 0.003s

FAILED (failures=1)

=== GREEN (fix restored) ===
Ran 1 test in 0.006s

OK
```

**Live replay: not run.** `charter_replay.py` costs real model spend and
is never executed by this run or by CI. Only `tests/test_charter_replay.py`
ran, which drives fake `claude` executables placed on `PATH` and makes
no API call.

## 3. The CLI-seam copy is pinned and fixed

**Criterion:** the new test fails against the naive predicate for the
right reason, passes after the fix, and `tests.test_cli` is green.

This copy was not in the original scope — see `defect.md` Notes for why
the run missed it. It was found by an AST scan for verbatim-duplicated
helper bodies across `tests/`, which reported `pid_alive` in three
files, not two.

RED, against `tests/test_cli.py:384` as it stood:

```
AssertionError: True is not false : a terminated process must read as dead

Ran 1 test in 0.003s

FAILED (failures=1)
```

The precondition `os.kill(pid, 0)` inside the test passed on the way to
that failure, so the pid still had a process-table entry — the predicate
was wrong about a zombie, not merely about a vanished pid.

GREEN, after applying the same `process_state` predicate:

```
Ran 1 test in 0.008s

OK
```

and the whole suite this copy belongs to, including the two grace-loop
tests that consume it (`test_a_timeout_flips_timed_out_and_reaps_the_group`,
`test_a_dead_leaders_grandchild_is_still_reaped`):

```
Ran 58 tests in 4.038s

OK
```

## 4. The battery is green

**Criterion:** full suite OK, lint 0, gates 0, selftest ok, quoted.

```
Ran 1347 tests in 15.980s

OK
--- lint ---
lint: 0 problem(s) across 24 skills
--- gates ---
gates: 0 problem(s)
selftest: ok
```

1347 is 1344 on `main` plus this run's three regression tests — one per
copy. (An earlier battery in this run read 1346, before the third copy
was found.) one-owner is 9, the standing baseline — unchanged, and it
would not have moved either way: the pass excludes `tests/**`, which is
precisely why three verbatim copies of one helper went unnoticed.

## Not verified, and why

- **That this fixes the five journal flakes.** It does not, and the run
  never claimed it would. `defect.md` records the refutation: an orphan
  is collected in 3.5 ms against a 2000 ms budget. The flake's own cause
  stays open, with PID reuse the leading untested candidate.
- **Behaviour under a root uid.** The sandbox where those flakes appear
  runs as root; this machine does not, and the run did not simulate one.
  The fix is uid-independent by construction — it reads a state field
  rather than exercising a permission — but that reasoning is not a
  measurement.
- ~~**Behaviour on Linux.**~~ **Closed.** The branch was pushed and the
  validator ran it on Linux, taking the `/proc` path this machine never
  exercises. The run cited here is `33101089817` — the first Linux run
  (`33099721069`, 1346 tests) predated the third copy and so proved the
  `/proc` branch for only two of them:

  ```
  lint: 0 problem(s) across 24 skills
  gates: 0 problem(s)
  selftest: ok
  Ran 1347 tests in 12.952s
  ```

  The `review`, `needs-review-label` and `merged-label` jobs are
  `skipped`, which is correct and not a failure: all three are gated on
  `pull_request` actions, and this was a branch push with no PR.
## The suite-timing anomaly, chased and closed

This battery ran in 16.3 s where the same suite took ~103 s in two other
worktrees earlier today. A 6x difference is not something to wave
through, so it was measured against an unmodified baseline rather than
explained:

```
  baseline      run 1: 16s
  baseline      run 2: 15s
  run-pidalive  run 1: 16s
  run-pidalive  run 2: 16s
```

`main` is also ~16 s. **This change causes no speedup**, and none is
claimed. The earlier ~103 s figures came from batteries run as
background jobs alongside other concurrent work; the difference was
contention in the measurement, not a property of the code.

Worth recording for its own sake: a suite time quoted from a loaded
machine is off by 6x here. Timings taken that way should not be compared
against each other.

The first attempt to measure this returned four empty values — the
redirection sent `time`'s own output to `/dev/null` along with the
suite's. Recorded so the bad measurement is not mistaken for a result.
