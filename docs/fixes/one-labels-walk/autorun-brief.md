# Autorun brief: maintenance:one-labels-walk

Not an artifact. The brief autorun collects once, standing in for the
interviews the stages would otherwise run.

## Origin

Backlog seed `docs/backlog.md:46` (from: maintenance:deepening-tool-seams),
claimed as `(claimed: maintenance:one-labels-walk)`. Tracking issue #334.

## Run scale

Maintenance, slug `one-labels-walk`, artifacts at
`docs/fixes/one-labels-walk/`. Entry is capture with
`re-entry: architect`: the change decides whether a module documented as
PURE may import the CLI seam, which is a design question, not a typo.

## Scope

**In.** `plane_drift.issue_lifecycle` stops reimplementing the labels-array
walk and reads names through `cli.label_names`, the seam ADR-0037 gives
that convention to. The one-owner pre-pass's standing miss-3 group closes.
The stale "STILL OPEN at HEAD" comment in `tests/test_one_owner.py` moves
to the closed form its miss-1 sibling already uses.

**Out.** Everything else in the one-owner pre-pass's nine standing groups
— READY_LABEL's three owners, `budget_guard.record` vs `cost_ledger.row_key`,
the CONTINUE and ROOT pairs, the remaining key-set groups. Each is its own
seed and its own decision; `docs/backlog.md:53` says so explicitly. Nothing
about `cli.label_names` itself changes, and no caller of it moves.

## Constraints

- Stdlib only. Battery is `python3 -m unittest discover tests`,
  `python3 lint.py`, `python3 gates.py && python3 gates.py --selftest`.
  `python3 one_owner.py` is a free review pre-pass, never a gate.
- `plane_drift.py` is root-only (ADR-0060: neither caller ships), so this
  run is expected to produce **no manifest churn** — worth stating up
  front, because seven PRs are open against `factory/manifest.json` and
  each collision costs a rebase.
- Never fabricate evidence. `evals/results/` is untouched.

## Release authorization

**None.** Prepare-and-stop: pre-flight, open the PR, write `release.md`,
merge nothing. ADR-0036 clause 2 independently requires a non-authoring
reviewer to re-execute the verification before merge.

## Tracker

Issue #334 tracks the run. Work items carry no `(tracker: #N)` reference
and mint no `WO-####` id — ADR-0032 forbids running the dispatch plane
ahead of the knowledge plane, and this run dispatches nothing.
