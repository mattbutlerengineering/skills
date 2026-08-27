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

## 3. The battery is green

**Criterion:** full suite OK, lint 0, gates 0, selftest ok, quoted.

```
tests exit=0
Ran 1346 tests in 16.271s

OK
--- lint ---
lint: 0 problem(s) across 24 skills
--- gates ---
gates: 0 problem(s)
selftest: ok
--- one-owner (pre-pass, not a gate) ---
one-owner: 9 problem(s)
```

1346 is 1344 on `main` plus this run's two regression tests. one-owner
is 9, the standing baseline — unchanged, and it would not have moved
either way: the pass excludes `tests/**`, which is precisely why the
duplicated helper went unnoticed.

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
  exercises (run `33099721069`, `check` job):

  ```
  lint: 0 problem(s) across 24 skills
  gates: 0 problem(s)
  selftest: ok
  Ran 1346 tests in 12.918s
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
