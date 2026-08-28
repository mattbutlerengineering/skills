---
stage: verify
run: maintenance:a-dead-cli-scores-as-a-pass
date: 2026-08-28
assumptions: []
---

# Verification — a dead CLI scores as a pass

Every criterion below was run on this branch. The three reproduction legs
from `defect.md` were re-run byte for byte with the same inputs, so the
before and after are comparable.

## 1. A transcript marked with an error cannot pass a forbid-only case

The forbid-only case set from `defect.md`, scored offline against a
recorded set with no entry for the case:

```
$ python3 charter_replay.py --cases cases.json --transcripts none.json
  [FAIL] forbid-only (swe): 0 tool call(s)
      replay: the run errored (no recorded transcript)
      error: no recorded transcript
charter replay (recorded-transcripts): 0/1 passed
exit=1
```

**Result:** PASS — before the fix this printed `[PASS]` and `1/1 passed`
with `exit=0`.

## 2. The failure names the error, and `failed` still means expectation ids

The record this run would write into `evals/results/`:

```json
{
  "id": "forbid-only",
  "role": "swe",
  "pass": false,
  "failed": [],
  "failures": [
    "replay: the run errored (no recorded transcript)"
  ],
  "tool_calls": 0,
  "error": "no recorded transcript"
}
```

`failed` is empty because no expectation failed — nothing was replayed to
fail one. The reason is in `failures`, which is what drives `pass`, the
summary, and the exit code.

**Result:** PASS

## 3. A transcript with no tool calls and no text cannot pass, unmarked

Leg C — the shape a `claude` that dies before writing an event produces,
which carries no error field at all:

```
$ python3 charter_replay.py --cases cases.json --transcripts empty.json
  [FAIL] forbid-only (swe): 0 tool call(s)
      replay: the run produced no tool calls and no text
charter replay (recorded-transcripts): 0/1 passed
exit=1
```

**Result:** PASS — this is the leg that left no trace at all before.

## 4. The live path, with no `claude` on PATH

No model launches, so this costs nothing:

```
$ env PATH=$EMPTY python3 charter_replay.py --cases cases.json
warning: a live replay spends real money on model runs
  [FAIL] forbid-only (swe): 0 tool call(s)
      replay: the run errored (claude CLI failed: [Errno 2] No such file or directory: 'claude')
      error: claude CLI failed: [Errno 2] No such file or directory: 'claude'
charter replay (live-model): 0/1 passed
exit=1
```

**Result:** PASS — a `--record` run in this state now writes a failing
snapshot rather than a `"source": "live-model"` pass.

## 5. Prose alone, and a tool call alone, are still evidence

The evidence rule must not quietly take back
`test_commands_scope_ignores_prose`: a run that only talked still ran.

```
$ python3 -m unittest tests.test_charter_replay.TestAVerdictNeedsEvidence \
    -k evidence -v
test_a_tool_call_alone_is_evidence ... ok
test_an_empty_transcript_cannot_pass_even_unmarked ... ok
test_an_errored_replay_that_still_did_work_cannot_pass ... ok
test_prose_alone_is_evidence ... ok
----------------------------------------------------------------------
Ran 4 tests in 0.001s

OK
```

**Result:** PASS

## 6. The shipped golden set is unaffected

Both synthetic variants replayed through the real golden case set — the
degradation-detection contract:

```
$ python3 -c "... run_suite(golden_cases(), recorded_runner) ..."
compliant {'total': 4, 'passed': 4, 'failed': 0}
degraded {'total': 4, 'passed': 0, 'failed': 4}
```

**Result:** PASS — compliant transcripts still pass, degraded ones still
fail, so the suite has not started "catching" degradation by failing
everything.

## 7. The suite exits nonzero end to end, through `main`

```
$ python3 -m unittest \
    tests.test_charter_replay.TestAVerdictNeedsEvidence.test_the_exit_code_follows -v
test_the_exit_code_follows ... ok
----------------------------------------------------------------------
Ran 1 test in 0.003s

OK
```

**Result:** PASS

## 8. The luck is pinned as luck

The golden set's requires are what saved it before this fix; these assert
that, and assert the fix holds without them:

```
$ python3 -m unittest \
    tests.test_charter_replay.TestTheGoldenSetsRequiresAreNotTheGuarantee -v
test_every_golden_case_fails_an_errored_replay ... ok
test_the_shipped_set_is_the_lucky_shape_this_guards ... ok
test_they_fail_for_the_evidence_reason_not_only_their_requires ... ok
----------------------------------------------------------------------
Ran 3 tests in 0.010s

OK
```

**Result:** PASS

## 9. The runner legs are pinned end to end, not just the pure function

Both real runner failure modes, through `claude_runner` with fake CLIs:

```
$ python3 -m unittest tests.test_charter_replay.TestClaudeRunnerLiveSeam -v \
    -k cannot_score_a_pass
test_a_dead_leaders_empty_transcript_cannot_score_a_pass ... ok
test_a_missing_cli_cannot_score_a_pass ... ok
----------------------------------------------------------------------
Ran 2 tests in 0.286s

OK
```

**Result:** PASS

## 10. The repo battery

```
=== unittest ===
Ran 1359 tests in 25.769s

OK
=== lint ===
lint: 0 problem(s) across 24 skills
=== gates ===
gates: 0 problem(s)
=== selftest ===
selftest: ok
=== one_owner ===
one-owner: 9 problem(s)
```

1359 is 1344 (`origin/main`) plus the 15 tests this run adds. `one_owner`
is unchanged at 9, so no new duplicated fact was introduced.

**Result:** PASS

## Not verified

```
Not run: a live charter replay against a real model.
```

**Result:** NOT RUN — a live replay costs money and is on-demand only
(CLAUDE.md). Everything this run changed is in the pure scoring seam,
which CI covers with no model in the loop; the live path was exercised
only in the failure mode that never launches a model (criterion 4).
