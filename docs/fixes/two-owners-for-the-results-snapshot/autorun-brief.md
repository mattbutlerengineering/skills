# Autorun brief — two owners for the results snapshot

## Provenance

No user-supplied brief exists for this run. It was authored from this
session's own investigation under a standing autorun instruction. The
candidate was not invented: it came from enumerating the nine findings
`python3 one_owner.py` reports, mapping each to the open-PR contention
set, and following the one lead whose modules no pull request claims.
`one_owner.py` does not itself flag this pair — it compares stated
values and payload-key reads, and two structurally identical function
bodies are neither. The pair surfaced while confirming the `ROOT`
finding it *does* report.

## What and why

`trigger_eval.record` and `charter_replay.record` are the same function
written twice. Both create the results directory, both ask
`eval_schema.results_path` for the name, both serialise with
`json.dumps(output, indent=2) + "\n"` in utf-8, both return the path.
They differ only in the kind string they pass and, for trigger, a
`harness` keyword.

`evals/results/` is the repo's append-only honesty substrate: LEDGER
maturity graduates only via real runs recorded there. A serialisation
change applied to one writer and not the other puts two on-disk formats
in that tree, and the tree is never rewritten to reconcile them.

## Scale and re-entry

Maintenance run, slug `two-owners-for-the-results-snapshot`. Re-entry is
`implement`: the defect is a duplicated fact with an established owner
(`eval_schema`, ADR-0022/ADR-0024), so no design stage is required.

## Scope

In: give `eval_schema` the snapshot writer, route both callers through
it, keep both call sites' observable output identical.

Out: the `ROOT` duplication `one_owner.py` reports between the same two
modules — a separate fact with a separate owner question. Out: the
`record` name collision with `budget_guard.record`, which is a different
function entirely.

## Constraints

Stdlib only. Never run `trigger_eval.py` or `charter_replay.py` live —
both spend real money on model runs. Offline unit tests are the whole
verification surface here.

## Release authorization

None. Ship prepares and stops.
