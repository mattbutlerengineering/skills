---
run: maintenance:dedup-identity-has-two-owners
date: 2026-08-25
origin: docs/backlog.md seed 49 (from: maintenance:one-fact-one-owner)
---

# Autorun brief

## What and why

`budget_guard.record` writes its own copy of ADR-0041's cost-ledger dedup
identity — `existing.get("wo") == wo and existing.get("run_id") == run_id` —
inside a module that already imports `cost_ledger` and calls
`cost_ledger.read(root)` four lines earlier. `cost_ledger.row_key` owns that
identity and its docstring says so. Fold the second owner into the first.

Found unaided by the one-owner pre-pass; adjudicated at full depth by that
run's review, which called it the strongest evidence the same-keys rule
earns its place. Folding it was out of scope there — that run was building
the finder, not cleaning up after it.

## Run scale

Maintenance, scoped fix. `re-entry: architect` — the change is small but it
is a seam question (which module owns an identity, and what the tolerant
`.get()` in the copy was ever protecting against), so the architecture and
breakdown legs run.

## Scope

**In:** `budget_guard.record`'s dedup check, its tests, and whatever the
fold reveals about the `.get()`/`[]` asymmetry between the two copies.

**Out:** every other one-owner standing finding, including
`budget_guard.py:55 CONTINUE` / `cost_report.py:44 CONTINUE`, which is a
different pair with a different remedy. Out too: any change to ADR-0041's
identity itself — this run makes one module state it, not a different fact.

## Success criteria

- `budget_guard.record` reads the dedup identity through the seam.
- Mutating `cost_ledger.row_key` makes a `budget_guard` test fail. Today it
  does not, and that is the defect's signature.
- `one_owner.py` no longer reports the `record`/`row_key` pair, and reports
  no new group.
- The battery stays green: unittest, `lint.py`, `gates.py`, `--selftest`.

## Constraints already decided

- **Stdlib only.**
- `budget_guard.py` **is** in `factory_init.MIRRORS`, so the payload copy and
  `factory/manifest.json` move in the same commit
  (`python3 factory_init.py update-manifest`).
- The ledger is append-only; no stage may write to `docs/factory/costs.jsonl`
  except through `budget_guard.py record`, and this run has no reason to.
- Never fabricate run, eval or ledger evidence.
- Branch from `origin/main`, never from another open PR's tip.

## Release authorization

**None.** Prepare-and-stop: pre-flight, open the PR, write `release.md`,
stop. No merge, no tag, no publish. ADR-0036 clause 2 independently forbids
the author merging.
