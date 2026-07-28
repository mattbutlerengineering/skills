# Detector G's merged-order rule anchors to the run epoch

- Status: accepted
- Date: 2026-07-28

Amends ADR-0041. Its consequences promised one behaviour; detector G's
implementation did the opposite, and a routine gate-digest commit turned
`main` red. This ADR records the correction.

## Context

ADR-0041 widened the cost ledger to hold gate-latency rows and stated, in
its own consequences: *"a merged order's ledger presence can now be
satisfied by a gate row alone; G's per-run guarantees stay anchored to
dispatched runs recording themselves … not to the ledger's mere
non-emptiness."*

But `check_cost_ledger` gated its merged-order cross-check on
`if not ledger.is_file(): return []` — the ledger's mere existence, which
is exactly its non-emptiness. That was harmless only while no ledger
existed. When the daily gate digest (WO-0017, ADR-0041) wrote the ledger's
first row — a single $0 gate-latency row for WO-0001 — the file came into
being, and G flipped from silent to demanding a dispatched-run line for
every merged order. Sixteen bootstrap orders (WO-0002..WO-0017), genuinely
merged before cost recording existed and so carrying no ledger line, all
became findings. `main` went red on a commit that changed no detector and
no breakdown row. The implementation contradicted ADR-0041's stated
consequence.

## Decision

The merged-order cross-check anchors to the **run-accounting epoch**, not
the ledger file's existence. G tracks whether any parsed row is a
dispatched run — an entry whose outcome is not a gate wait, tested with the
existing `cost_ledger.gate_wait` predicate — and only once one exists does
a merged order without a line become a finding. A ledger holding only
gate-latency rows has begun no run accounting, so orders merged before the
first run are not yet owed a line.

G's other halves are unchanged: a recorded work order (gate row or run row)
must still have a breakdown row; the line grammar still gates every row;
and a merged order satisfied by a gate row alone stays satisfied
(ADR-0041).

## Consequences

- `main` is green: its ledger is one gate row, so the merged-order rule
  stays silent until dispatched runs begin recording.
- The guarantee is **deferred, not weakened**. The moment a dispatched run
  records itself, the epoch opens and every merged order — including the
  sixteen historical bootstrap orders — is checked again. Those orders
  predate cost recording and need a durable reconciliation before then: a
  genesis boundary that distinguishes pre-cost-recording orders from
  accountable ones. This ADR does not supply it; a follow-up work item
  tracks it, and until it lands the epoch anchor holds the line.
- The pin lives at G's own suites: `tests/test_factory_gates.py`'s
  `TestCostLedger` (a gate-only ledger stays silent; a dispatched run
  reopens the check) and the shipped selftest's dirty/clean trees, which
  carry run rows and so exercise the epoch-open path unchanged.
