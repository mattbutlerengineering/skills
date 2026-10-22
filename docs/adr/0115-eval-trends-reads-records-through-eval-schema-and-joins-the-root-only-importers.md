# eval_trends reads records through eval_schema's name inverse and joins the root-only importers of cli.py

- Status: provisional
- Date: 2026-10-21

Recorded by the `eval-trends` feature run (`docs/features/eval-trends/`),
unattended, so it is provisional. It follows ADR-0022 and ADR-0024 (the eval
schema and results grammar owner) and ADR-0110, ADR-0112, ADR-0113 and ADR-0114
for the dual-membership pin.

## Context

Issue #1027 asks for a view of eval quality over time. The records are the
append-only files under `evals/results/` and `plugin-evals/records/`. After
ADR-0114 the pinned root-only to mirrored set is 54 pairs over nine mirrored
modules. `eval_schema.py` owns the results naming grammar in one direction only:
`results_path` generates a name and a private regex checks a LEDGER link. A
reader that has a file name and needs kind, harness, date and collision suffix
has no function to ask. Two things outlive the commit: where that inverse lives,
and the import edge the reader adds.

## Decision

- `eval_schema.parse_results_stem(stem)` is added, the inverse of `results_path`
  for every results kind, built from the same `_HARNESS` and `_SUFFIX` pieces. A
  test pins it against `results_path`. The grammar still has one owner.
- `eval_trends.py` reads record fields itself, one small adapter per surface.
  Trigger and charter fields are written by `trigger_eval.py` and
  `charter_replay.py`, plugin records by the external `claude plugin eval`, and
  the tool is the only reader. The seam rule (multiple callers and observed
  divergence) is not met, so no normaliser is added to `eval_schema.py`.
- `eval_trends` is root-only and a leaf. It imports `cli` (mirrored) and
  `eval_schema` (root-only, not in `factory_init.MIRRORS`). One new pair,
  `eval_trends` to `cli`, so the set becomes 55; `tests/test_dual_membership.py`'s
  pin carries it, and `factory.py`'s `VERBS` gains an `eval-trends` row.
- The tool only reads: it writes nothing under `evals/results/` or
  `plugin-evals/records/`, runs no model and gates nothing.

## Rejected alternatives

- **A second regex in the tool.** The harness token list and the `-N` rule would
  exist twice, the divergence ADR-0024 moved the grammar to avoid.
- **A common-row normaliser in `eval_schema.py`.** One caller, and it would make
  `eval_schema` describe a record shape written by an external CLI.
- **Mirroring into the payload.** No payload tool calls it (ADR-0060 rule).

## Consequences

- A second reader of trigger or plugin record fields that diverges from the
  tool's copy is the trigger to move field extraction into `eval_schema.py`.
- A change to the pin set or to what the tool reads is a new ADR. A change to a
  threshold, a refusal string or the output order is a commit.
- LEDGER maturity does not move (ADR-0012, ADR-0019); the tool's output is not
  eval evidence.
