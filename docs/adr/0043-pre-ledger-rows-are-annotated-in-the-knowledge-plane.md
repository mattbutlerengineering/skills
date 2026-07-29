# Pre-ledger rows are annotated in the knowledge plane

- Status: accepted
- Date: 2026-07-28

## Context

Detector G's cross-check — a merged work order must have a cost-ledger
line (ADR-0034) — activates when `docs/factory/costs.jsonl` exists. That
trigger silently assumed the file's existence implied the factory had
been dispatching. ADR-0041 broke the assumption: the daily gate digest
writes gate-latency rows into the same file, so its first observation
(WO-0001's merge wait, commit f5a37aa) created the ledger on its own and
G began demanding spend rows for WO-0002–WO-0017 — the factory's own
bootstrap work orders, all merged before the ledger was born. The bot's
direct push triggered no CI, leaving main silently red.

Those rows can never be satisfied honestly: fabricating spend lines for
runs that predate cost tracking is exactly what the eval-honesty rules
forbid (ADR-0012). Rejected alternatives:

- **Dormant until the first spend row.** A time bomb — the first real
  dispatched run would re-fire all 16 problems and block its own PR.
- **An exemption list in gates.py or factory.json.** Both are mirrored
  into stamped repos (detector E), so one repo's WO ids would leak into
  every product repo's detector policy.

## Decision

The exemption is a fact about a work order, so it lives in the knowledge
plane on the row it describes (ADR-0004): a breakdown row merged before
the ledger existed carries a trailing `(pre-ledger)` annotation, and
G's merged-row-must-be-recorded check skips annotated rows
(`gates.PRE_LEDGER_MARK`). The reverse check — a recorded wo must have a
breakdown row — is untouched, and the annotation waives nothing else.

The grammar mirrors into stamped repos; the annotations do not (they are
per-repo artifact state). A brownfield repo adopting the factory
(ADR-0028) marks its own pre-adoption work orders the same way.

## Consequences

- The 16 bootstrap rows in docs/features/software-factory/breakdown.md
  carry the annotation; `python3 gates.py` is green again on main.
- WO-0001 is not annotated: its gate row already records it, and it is
  ledger-era by construction — the ledger was born with its merge.
- A future work order missing its ledger line still fires G; the
  annotation is a historical fact, never an escape hatch for new work.
  A reviewer seeing `(pre-ledger)` on a new row should treat it as
  drift.
