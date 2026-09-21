---
stage: review
run: maintenance:a-crashed-run-is-recorded-as-a-no-fire
date: 2026-08-27
assumptions: []
---

# Review: a crashed run is recorded as a no-fire

## Scope

The diff since this run began: `trigger_eval.py` (`score_case`,
`summarize`, `run_eval`, `print_report`), `tests/harness_contract.py`
(+2 contract tests), `tests/test_trigger_eval_scoring.py` (+3 tests),
and `tests/test_trigger_eval_run_eval.py` (one test class deleted).
Three passes: correctness, design, security.

Two items below need a human, and neither is a code defect: finding 1 is
a deliberate deferral of a CLI contract change, and finding 2 is the
deletion of a test that pinned the old behaviour.

## Findings

### Major: a partially crashed eval can still exit 0

- Scenario: `--runs-per-query 3`, and 2 of the 3 runs for a case raise
  (harness flake, a timeout, a transient auth failure). The surviving
  run routes correctly, so `runs=1`, `correct_rate = 1/1 = 1.0`, the
  case passes, `summary["failed"] == 0`, and `main` returns
  `0 if output["summary"]["failed"] == 0 else 1` — success, on one third
  of the intended evidence.
- This is a regression *introduced by this run*, and it deserves naming
  as such. The old bucketing was wrong for the right-sounding reason: it
  put those 2 crashes in `fired["none"]`, which dropped `correct_rate`
  to 0.33 — under the default 0.5 threshold — so the case failed and the
  eval exited 1. A broken mechanism was producing a defensive outcome.
  Removing the mechanism removed the outcome with it.
- Decision: **half fixed, half deferred.** `print_report` now states the
  loss — `errors=N` on the case's own line, plus
  `warning: N run(s) failed and were not scored — this eval measured
  less than it launched` under the summary — so the human running the
  eval cannot miss it. Covered by `TestPrintReportNamesLostRuns`
  (3 tests), which failed first against the old renderer.
- Deferred, for a human: whether `main` should also exit nonzero. The
  change is one line —
  `return 0 if summary["failed"] == 0 and not summary["errors"] else 1`
  — and the argument for it is this repo's own eval-honesty rule: an
  eval that lost runs measured less than it claims, and exit 0 asserts
  a completeness it does not have. The arguments against are that it
  changes a CLI contract, and that `main()` has **no test coverage at
  all** (nor does `print_report`, before this run) — so an unattended
  agent would be changing an untested exit-code contract outside this
  run's brief. That is a decision to take deliberately, not by default.

### Minor: `summarize` reads `fired` and `errors` with different care

- Scenario: not reachable today. Within `run_eval`, `summarize` only
  ever sees freshly scored results, so both keys are present. But the
  two lines sit adjacent and disagree: the new confusion guard indexes
  `r["fired"]` directly while the summary total uses
  `r.get("errors", 0)` precisely so older records stay readable. A
  future caller that passes loaded snapshot records to `summarize` —
  there is none today — would get a `KeyError` from one line and a
  silent `0` from the other.
- Decision: deferred. `summarize` has exactly one caller, and inventing
  defensiveness for a caller that does not exist is the speculative
  error the repo's own discipline rules out. Recorded here so the next
  reader knows the asymmetry is noticed rather than accidental.

### Minor: `errors_by_case.setdefault(case_id, 0)` is redundant

- Scenario: none — it cannot misbehave. The `setdefault` seeds the key
  on every future, and the read at the end is already
  `errors_by_case.get(case["id"], 0)`, so the seeding line changes no
  outcome. It mirrors the `fired_by_case.setdefault(...)` line directly
  above it, which *is* load-bearing (it guarantees a Counter exists for
  every case that launched a run).
- Decision: kept. Removing it would break the visual parallel between
  the two accumulators for no behavioural gain.

## Human sign-off required: a pinned test was deleted

Not a finding against the code — a change to what the repo has recorded,
which is the user's call rather than mine.
`TestWorkerExceptionBucketsAsNone` in
`tests/test_trigger_eval_run_eval.py` asserted
`result["fired"] == {"none": 2}` under a missing CLI. This run deletes
it. The full reasoning is in `defect.md`; the short version is that it
encoded no decision anybody made:

- no ADR mentions the bucketing;
- `plans/002-cover-run-eval-fanout.md`, which wrote the test, calls its
  tests "characterization tests of existing behavior", lists
  "`trigger_eval.py` unmodified" as a done criterion, and makes a real
  fan-out bug a **STOP condition** — "report it, don't fix production
  code here";
- that same plan's test-plan line names this case "worker exception
  bucketed as `"none"` with a warning (**the silent-failure path**)".

So the test pinned a behaviour its own author had labelled a silent
failure and been forbidden from fixing. Its load-bearing half — *never
crash* — survives, and is now checked for **both** harnesses by
`test_a_crashed_run_is_an_error_not_a_no_fire` in the shared contract,
which also asserts `errors`, `runs`, and the summary total. It was
deleted rather than rewritten because keeping a claude-only duplicate of
a contract test would state one fact twice.

If that reasoning is rejected, the revert is small and self-contained:
restore the class and the four imports it used, and drop the `errors`
accounting.

## Passes with no findings

- **Security.** No secrets, no new input surface, no injection point.
  The warning line interpolates the exception via `{err}` exactly as
  before this run; the only new interpolations are integers the process
  computed itself.
- **Design.** The change matches the module's existing shape: scoring
  stays a pure function of counts, `run_eval` keeps orchestration, and
  the new field is additive with a `.get` reader so previously recorded
  snapshots in `evals/results/` stay loadable — which the repo's
  append-only rule requires. The `errors` default of `0` on `score_case`
  keeps all eleven pre-existing direct call sites in
  `tests/test_trigger_eval_scoring.py` (lines 49-90) valid unmodified —
  verified by count, not assumed.

## Verdict

Ready to ship as a prepared, unmerged branch. No critical findings. The
one major is fixed on its visible half and deferred on its contract half
with the exact change written down; both minors are deliberate.

Two items are the human's, not mine: the deleted pinned test above, and
the deferred exit-code decision. Per ADR-0036 clause 2 this branch also
cannot be self-merged — a non-authoring reviewer must re-execute
verification and record it on the PR.
