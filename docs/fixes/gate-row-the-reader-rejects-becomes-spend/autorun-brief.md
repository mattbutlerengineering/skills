# Autorun brief — a gate row the reader rejects becomes spend

## Provenance

No user-supplied brief exists for this run. It was authored from this
session's own investigation under a standing autorun instruction. The
candidate came from searching the uncontended modules for writer/reader
asymmetries — a composer and a parser of the same string grammar that
disagree about what is well-formed. `cost_ledger.py` is touched by no
open pull request.

## What and why

`cost_ledger.gate_entry` composes a gate-latency row's `outcome` field
by interpolation and validates nothing. `cost_ledger.gate_wait` parses
that field with `GATE_OUTCOME`, which admits only `[a-z]+` for the gate
name and `\d+` for the seconds. The writer can therefore emit a row its
own reader refuses.

A refused row does not merely lose its wait observation. `dispatched()`
selects spend rows as "everything `gate_wait` does not claim", so the
refused row is counted as a dispatched run — and `dispatched()` is, by
its own docstring, the one row-selection rule behind both month-to-date
figures, including the number ADR-0034's monthly cap is compared
against.

## Scale and re-entry

Maintenance run, slug `gate-row-the-reader-rejects-becomes-spend`.
Re-entry is `implement`: the grammar already has an owner
(`GATE_OUTCOME`); what is missing is the writer deferring to it.

## Scope

In: make `gate_entry` incapable of emitting a row `gate_wait` rejects,
with the reader's regex as the single authority so the two cannot
diverge again.

Out: the three shipped gate names are all well-formed today, so this
changes no existing behaviour and rewrites no existing ledger row.
`docs/factory/costs.jsonl` is not touched by this run. Out: whether
`human_gates.waited_seconds` can return a negative — a separate
question in a module PR #326 claims.

## Constraints

Stdlib only. The cost ledger takes rows only via `budget_guard.py
record`; no ledger row is written by this run.

## Release authorization

None. Ship prepares and stops.
