# decompose_grade is an offline scorer beside a harness suite, and joins the root-only importers

- Status: provisional
- Date: 2026-10-20

Recorded by the `decompose-eval-suite` feature run
(`docs/features/decompose-eval-suite/`), unattended, so it is provisional.
It follows ADR-0081 (the plugin-eval tree), ADR-0093 (tags) and ADR-0113
for the dual-membership pin.

## Context

Step 4 of the Decompose learning loop (#989) needs a score plus text saying
why a candidate breakdown failed. `claude plugin eval --help` documents
grader types `regex`, `tool_order`, `tool_used`, `file_exists`, `llm` and
`baseline`; there is no grader that runs code. A regex can read a produced
file but cannot compute coverage or resolve a dependency, and an `llm` or
`baseline` grader is a paid model call. Two things outlive the commit: that
split, and the root-only to mirrored import edges the scorer adds. After
ADR-0113 the pinned set is 52 pairs over nine mirrored modules.

## Decision

- The Decompose suite under `plugin-evals/decompose/` holds harness graders
  only and is never run by the repo's checks. The deterministic score lives in
  `decompose_grade.py`, run by hand or by its tests on a breakdown.md and the
  fixture architecture. The two are separate scorers; neither claims to
  reproduce the other. Comparing them needs a paid run with `--keep-temp` and
  is a follow-up that needs the Owner's say-so.
- The suite needs no `.claude-plugin/plugin.json` edit: `experimental.evals`
  already names the `plugin-evals` directory and a suite is found by its
  layout. So ADR-0095 is not engaged and the version is untouched.
- `decompose_grade` is root-only and a leaf, not a seam: no payload tool
  imports it, and the seam rule's multiple callers and observed divergence are
  absent. It imports `cli` and `knowledge_plane` (mirrored) and
  `decompose_signals` (root-only). The set becomes 54 pairs: the `cli.py` row
  gains `decompose_grade` and the `knowledge_plane.py` row gains it.
  `tests/test_dual_membership.py`'s pin carries the two new pairs, and
  `factory.py`'s `VERBS` gains a `decompose-grade` row.

## Rejected alternatives

- **One in-harness scorer.** Not deterministic, paid on every score, and a
  regex cannot compute the four classes.
- **Running the Python grader from inside a case** (a `Bash(python3 *)` grant
  or the scaffold). No grader type consumes its output, and the producing model
  could read or run the grader.
- **Placing the grader in `eval_schema.py`.** That module owns case and results
  shape (ADR-0022, ADR-0024); scoring one skill's artifact is another fact, and
  it would give `eval_schema` the `knowledge_plane` and `decompose_signals`
  imports.

## Consequences

- A suite score and an offline score exist side by side with no recorded
  agreement. Until a paid run is compared, the offline score is validated only
  against hand-built cuts, and LEDGER maturity does not move (ADR-0012,
  ADR-0019).
- A change to the pin set, to the grader types the harness documents, or to the
  one-case suite is a new ADR.
