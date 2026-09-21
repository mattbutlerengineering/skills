---
stage: verify
run: maintenance:a-crashed-run-is-recorded-as-a-no-fire
date: 2026-08-27
assumptions: []
---

# Verification: a crashed run is recorded as a no-fire

## Summary

Five criteria, five PASS. The defect is demonstrated end to end through
`run_eval`'s public interface on the pre-fix module and shown corrected
at HEAD: a distractor case that scored a **clean pass on two runs that
never happened** now scores no pass and reports two errors, and the four
phantom entries it put into the confusion matrix are gone.

The regression test failed first, for the right reason, before the fix
existed. Depth note: the fix touches recorded eval-output semantics and
deletes a test that pinned the old behaviour — both are verified below,
and the deletion is routed to `review.md` for human sign-off.

## Criteria & evidence

### 1. A failed run is counted as a failure, not as a no-fire

- Check: run the new contract test against the **pre-fix** module
  (`git show HEAD~1:trigger_eval.py` laid over the post-fix tests in a
  scratch checkout), then against HEAD. RED must precede GREEN.
- Evidence — RED, pre-fix module:
  ```
  ERROR: test_a_crashed_run_is_an_error_not_a_no_fire (tests.test_trigger_eval_run_eval.FakeClaudeTest...)
  A run that failed is not evidence that the router declined.
    File ".../tests/harness_contract.py", line 113, in test_a_crashed_run_is_an_error_not_a_no_fire
      self.assertEqual(result["errors"], 2)
  KeyError: 'errors'

  Ran 9 tests in 1.106s
  FAILED (errors=4)
  ```
  The pre-fix module has no `errors` field at all, so the test dies at
  its first assertion. That is honest RED but it stops short of the
  bucketing itself, so criterion 1 is carried by the direct
  demonstration below rather than by this traceback alone.
- Evidence — the defect through the public interface, both modules, with
  `PATH` pointed at an empty directory so every worker raises:
  ```
  ########## BEFORE (pre-fix module) ##########
    d: pass=True  runs=2 fired={"none": 2} errors=<absent>
    a: pass=False runs=2 fired={"none": 2} errors=<absent>
    summary: 1/2 passed, errors=<absent>
    confusion: {"none": {"none": 2}, "idea": {"none": 2}}
  ########## AFTER (HEAD) ##########
    d: pass=False runs=0 fired={} errors=2
    a: pass=False runs=0 fired={} errors=2
    summary: 0/2 passed, errors=4
    confusion: {}
  ```
  Case `d` is a distractor: expected to fire nothing. Before the fix it
  is recorded as a **pass** — `runs=2`, `fired={"none": 2}` — on two
  runs that raised before reaching the router. After, it holds zero
  observations and passes nothing.
- Evidence — GREEN at HEAD, both harness twins:
  ```
  .................
  Ran 17 tests in 2.365s

  OK
  ```
- Result: PASS

### 2. The recorded output states the failures, per case and in the summary

- Check: the same demonstration; read `errors` per result and in the
  summary.
- Evidence — the per-case and summary fields, HEAD versus pre-fix:
  ```
  AFTER   d: pass=False runs=0 fired={} errors=2
  AFTER   a: pass=False runs=0 fired={} errors=2
  AFTER   summary: 0/2 passed, errors=4

  BEFORE  d: pass=True  runs=2 fired={"none": 2} errors=<absent>
  BEFORE  a: pass=False runs=2 fired={"none": 2} errors=<absent>
  BEFORE  summary: 1/2 passed, errors=<absent>
  ```
  Pre-fix the field is absent entirely — the failure left no trace in
  the record at all.
- Evidence — the human-facing report names the loss too, after the
  review finding below was fixed:
  ```
  ......................
  Ran 22 tests in 0.003s

  OK
  ```
  `tests/test_trigger_eval_scoring.TestPrintReportNamesLostRuns`, whose
  RED before the fix was:
  ```
  AssertionError: '2 run(s) failed' not found in
  '  [PASS] c1: expected=prd fired=[prdx1]\ntrigger eval: 1/1 passed\n...'
  ```
- Result: PASS

### 3. No existing field changes when nothing fails

- Check: the three pre-existing contract tests in
  `tests/harness_contract.py` must pass **unmodified**, and `errors`
  must be `0` throughout a clean run
  (`test_errors_are_zero_on_a_clean_run`).
- Evidence: the 17-test twin run above is green, and
  `git diff HEAD~1 -- tests/harness_contract.py` is additive only —
  45 insertions, 0 deletions:
  ```
   tests/harness_contract.py           | 45 +++++++++++++++++++++++++++++++++++++
  ```
  The `errors` reader in `summarize` uses `r.get("errors", 0)`, so
  result records written before this change stay readable.
- Result: PASS

### 4. The confusion matrix records no phantom observation

- Check: with every run crashing, `confusion` must be empty rather than
  carrying counts the router never produced.
- Evidence:
  ```
  BEFORE  confusion: {"none": {"none": 2}, "idea": {"none": 2}}
  AFTER   confusion: {}
  ```
  Four fires recorded, before, for a router that was never reached.
- Result: PASS

### 5. Battery green

- Check: the repo's four commands, each measured unpiped so the exit
  code is the command's own.
- Evidence:
  ```
  Ran 1350 tests in 15.946s

  OK
  tests exit=0
  --- lint ---
  lint: 0 problem(s) across 24 skills
  lint exit=0
  --- gates ---
  gates: 0 problem(s)
  gates exit=0
  selftest: ok
  ```
  1350 tests against a **1344** baseline, measured on the merge-base
  with `origin/main` rather than assumed: +6. The three touched files
  account for all of it, 33 tests to 39 — two added to the contract and
  run by both twins (+4), the pinned test deleted (-1), and three added
  for the review finding below (+3). See the deviations in `defect.md`.
  ```
  --- baseline (merge-base with origin/main) ---
  Ran 1344 tests in 15.388s      # whole suite
  Ran 33 tests in 1.617s         # the three touched files
  --- HEAD ---
  Ran 39 tests in 2.176s         # the three touched files
  ```
- Evidence — `one_owner.py`, the free pre-pass (not a gate):
  ```
  one-owner: 9 problem(s)
  ```
  Unchanged from the pre-run baseline of 9, so this change introduces no
  new duplicated fact.
- Result: PASS

## Failures

None.

## Not verified

- **Linux/CI.** All evidence above is macOS (darwin 25.5.0) and local.
  CI evidence is recorded in `release.md` after the push, not here.
- **A real harness crash.** Every failure above is induced by removing
  the binary from `PATH`. That reaches the same `except Exception` arm
  as a genuine mid-run crash, but it is not a demonstration that a
  *partially* completed run — some workers succeeding, some raising —
  accounts correctly. The contract test crashes every run. A mixed run
  is covered only by construction (`fired` and `errors` are accumulated
  independently per future), not by a test.
- **The printed confusion table.** `print_summary`'s stderr rendering is
  unchanged and untested here; the empty-row guard was verified through
  the `confusion` dict, not through its printed form.
- **`errors` in `evals/results/` snapshots.** No eval was run — the real
  routing eval costs money and is out of scope for this run — so no
  snapshot carrying the new field exists yet. The field is additive and
  readers use `.get`, but the first real snapshot is unverified.
