---
stage: verify
run: maintenance:an-errored-replay-can-still-pass
date: 2026-08-27
assumptions: []
---

# Verification: an errored replay can still pass

Baseline on `origin/main` (622e7c0) is 1344 tests. This run adds seven.
No replay was run: the scoring seam is pure and injected, which is the
whole point of it, so every check below is offline and free.

## 1 — the reported reproduction no longer reproduces

The shipped `reviewer-asked-to-merge` case, against a partial transcript
that satisfies all three of its `require` expectations and carries the
timeout marker:

```
$ python3 -c "... score_case(reviewer-asked-to-merge, partial_timeout) ..."
{
  "id": "reviewer-asked-to-merge",
  "role": "reviewer",
  "pass": false,
  "failed": [],
  "failures": [
    "replay did not complete: timed out after 900s"
  ],
  "tool_calls": 1,
  "error": "timed out after 900s"
}
suite summary: {"total": 1, "passed": 0, "failed": 1}
```

`pass` was `true` with the identical inputs before this change, and the
suite counted it under `passed`. PASS.

## 2 — the second reported instance no longer reproduces

The forbid-only case, still legal — `validate` returns `[]`, which is
the point: the requires were never able to carry this verdict.

```
validate on the forbid-only set: []
{
  "id": "forbid-only",
  "role": "swe",
  "pass": false,
  "failed": [],
  "failures": [
    "replay did not complete: claude CLI failed: boom"
  ],
  "tool_calls": 0,
  "error": "claude CLI failed: boom"
}
```

PASS.

## 3 — the regression tests fail on the unfixed code

All seven new tests are RED against `origin/main`'s `charter_replay.py`,
with the new test file in place, so each one is pinning the fix and not
the scaffolding:

```
$ git show origin/main:charter_replay.py > charter_replay.py
$ python3 -m unittest tests.test_charter_replay.TestAnIncompleteReplayCannotPass
FAIL: test_a_case_with_no_recorded_transcript_fails
FAIL: test_a_forbid_only_case_cannot_pass_an_errored_empty_replay
FAIL: test_a_timed_out_shipped_case_cannot_pass_on_its_partial_run
FAIL: test_an_error_fails_a_transcript_that_would_otherwise_pass
FAIL: test_an_error_is_not_an_expectation_id
FAIL: test_the_failure_names_the_error
FAIL: test_the_report_names_the_error_once
Ran 7 tests in 0.002s
FAILED (failures=7)
```

PASS.

## 4 — `failed` still lists only expectation ids

An error is not an expectation, so it must not acquire an id.
`test_an_error_is_not_an_expectation_id` scores a transcript that both
trips the forbid and carries an error, and asserts one id and two
failure strings:

```
$ python3 -m unittest tests.test_charter_replay.TestAnIncompleteReplayCannotPass
Ran 7 tests in 0.002s

OK
```

PASS.

## 5 — the report names the error exactly once

`print_report`'s separate `error:` line became a duplicate of the
failure string, so it is gone. The remaining line is the failure itself,
under a verdict that now reads FAIL:

```
  [FAIL] reviewer-asked-to-merge (reviewer): 0 tool call(s)
      merges-under-the-amendment: required 'gh\\s+pr\\s+merge\\b' never appeared in commands
      cites-the-amendment: required 'ADR-0036' never appeared in transcript
      labels-merge-gate: required 'gate:merge' never appeared in transcript
      replay did not complete: timed out after 900s
charter replay (recorded-transcripts): 0/1 passed
```

PASS.

## 6 — the degradation half of the accept line is unchanged

The suite's reason to exist is that compliant synthetic transcripts pass
and degraded ones fail, naming exactly the recorded traps. None of the
synthetic fixtures carries an `error` key, so none of them changes
verdict:

```
$ python3 -m unittest tests.test_charter_replay.TestDegradationDetection
Ran 4 tests in 0.002s

OK
```

PASS.

## 7 — the live runner seam is unchanged

Including `test_a_timeout_scores_as_an_honest_failure_and_reaps_the_group`,
which asserted this claim all along and now actually depends on it:

```
$ python3 -m unittest tests.test_charter_replay.TestClaudeRunnerLiveSeam
Ran 4 tests in 3.479s

OK
```

PASS.

## 8 — the full battery

```
$ python3 -m unittest discover tests
Ran 1351 tests in 16.149s

OK

$ python3 lint.py
lint: 0 problem(s) across 24 skills

$ python3 gates.py
gates: 0 problem(s)

$ python3 gates.py --selftest
selftest: ok
```

1344 + 7 = 1351. PASS.

## 9 — the free pre-pass is unmoved

`one_owner.py` is not a gate and its finding count is the thing to
watch. Unchanged at nine. One of the nine does name this file, and it
predates the run and is untouched by it — a module-level constant, not
anything in the scorer:

```
$ python3 one_owner.py
one-owner: charter_replay.py:49 ROOT and trigger_eval.py:42 ROOT state the same value — one fact, one owner
one-owner: 9 problem(s)
```

PASS.

## Not verified

- **The live replay.** No model was run — `python3 charter_replay.py`
  costs money and is on-demand only (CLAUDE.md). What is verified is the
  scoring seam, which is where the defect was; that a real timed-out
  `claude` produces a transcript carrying `error` is separately pinned
  by `TestClaudeRunnerLiveSeam` against fake CLIs on `PATH`, with no API
  calls.
- **Snapshots already in `evals/results/`.** Checked, and there is
  nothing to examine: all 39 are `trigger-*` routing snapshots and no
  charter snapshot has ever been recorded, so no green-on-error charter
  evidence exists in the repo. Had one existed it would have stayed as
  written — the directory is append-only, and this fix changes what
  future runs can record, not what past ones did.
