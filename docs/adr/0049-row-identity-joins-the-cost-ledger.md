# The row identity joins the cost ledger

- Status: accepted
- Date: 2026-08-05

Amends ADR-0041. Its dedup rule reads "the passage timestamp keys
`run_id`, so a daily re-scan of the same label history dedups instead
of double-recording" — but the identity that makes the rule work, the
`(wo, run_id)` tuple, lived in gate_digest.py as two inline subscripts.
`cost_ledger.gate_entry` composed the run_id that keys the row while a
different module decided what a row's identity IS: change the gate
run_id grammar and the dedup breaks silently one file away. The same
review found detector G re-implementing read()'s file read with a
body-identical, prefix-different cannot-read string, and the gates
suite pinning G against hand-built rows in a shape no current writer
produces.

## Decision

**The ledger seam owns row identity and the labelled read.**
`cost_ledger.row_key` is ADR-0041's dedup identity — `(wo, run_id)` —
in the module that composes both fields; the gate digest dedups through
it. `cost_ledger.load(root, label, …)` is the one existence check,
OSError translation, and located-problem grammar; `read()` and
detector G are thin over it, so "cannot read" and the per-line strings
literally cannot diverge (an absent ledger is `None`, never conflated
with an empty one, because G's merged-row rule bites only once the
ledger exists).

The read contract is settled on the docstring side, not with
accessors: `read()`'s entries are validated dicts and callers
subscript `LEDGER_FIELDS` freely — per-field accessors would be pure
pass-throughs, below the seam bar. What the seam owns are the semantic
rules over a row: `row_key`, `in_month`, `gate_wait`, `wo_token`.

## Consequences

- Changing the gate run_id grammar and the dedup key is one edit in one
  file, pinned by seam tests instead of a neighbour's subscripts.
- The gates suite builds its ledger fixtures through
  `cost_ledger.entry` and `cost_ledger.COST_LEDGER`; exactly one
  explicitly-labelled legacy (pre-`at`) fixture remains, because G
  gates the real ledger, which still holds such rows.
- `cost_report.guard` returns a named result (`GuardResult`) instead of
  a positional 6-tuple, and `cost_report.decide` gains the fail-closed
  spend validation its budget_guard twin already had. The twins' shared
  threshold shape is deliberately NOT extracted: their reason grammars
  diverge structurally, and a parameterized helper would be a forced
  seam — revisit only if the copies drift again.
