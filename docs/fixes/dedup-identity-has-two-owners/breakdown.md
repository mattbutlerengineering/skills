---
stage: decompose
run: maintenance:dedup-identity-has-two-owners
date: 2026-08-25
assumptions: ["One milestone, three items. The fold is one comparison, but the coupling test has to exist FIRST — a test written after the fold cannot distinguish `the fold took` from `the identity happens to agree`, which is the whole defect."]
---

# Breakdown: fold the dedup identity into its seam

## Milestone 1 — the copy is gone and the coupling is pinned

- [x] **I1 — pin the coupling before touching the code.** Add a
  `tests/test_budget_guard.py` case that reaches `record`'s dedup through
  `cost_ledger.row_key` rather than through a hand-written `(wo, run_id)`
  pair, so a change to the seam's identity reaches this suite.
  *Acceptance:* the new test passes on today's code, and fails when
  `cost_ledger.row_key` is mutated to a three-field identity in a throwaway
  worktree — the mutation that `defect.md` recorded as invisible to all 47
  budget_guard tests.

- [ ] **I2 — fold the comparison.** Replace
  `existing.get("wo") == wo and existing.get("run_id") == run_id` with a set
  of `cost_ledger.row_key(existing)` membership-tested against
  `cost_ledger.row_key(row)`, per architecture D1.
  *Acceptance:* `python3 one_owner.py` no longer reports the
  `budget_guard.py record` / `cost_ledger.py row_key` pair, reports no new
  group, and `tests/test_budget_guard.py` passes unchanged — including both
  cases pinning the refusal string byte-for-byte.

- [ ] **I3 — mirror and manifest.** Run
  `python3 factory_init.py update-manifest` and commit
  `factory/templates/tools/factory/budget_guard.py` and
  `factory/manifest.json` with the change.
  *Acceptance:* `python3 gates.py` reports no `E:` problem, and
  `tests/test_factory_init.py` passes.

## Notes

*(deviations logged here, dated, as they happen)*
