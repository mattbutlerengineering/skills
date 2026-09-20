---
stage: capture
run: maintenance:dedup-identity-has-two-owners
date: 2026-08-25
re-entry: architect
severity: latent
assumptions: ["Severity is `latent`, not `bug`: today both owners state the same identity, so nothing is miscounted right now. What is broken is the coupling — the copy cannot follow the seam, and the reproduction below shows it failing to.", "The reproduction mutates the seam in a throwaway detached worktree, never in the checkout. `docs/factory/costs.jsonl` was not touched; every ledger in the probe is a fresh tempdir."]
---

# Defect: the cost-ledger dedup identity has two owners

## What is wrong

`cost_ledger.row_key` owns ADR-0041's dedup identity and says so
(`cost_ledger.py:126`):

```python
def row_key(entry):
    """The row's (wo, run_id) identity — ADR-0041's dedup rule in the
    module that composes both fields: ..."""
    return entry["wo"], entry["run_id"]
```

`budget_guard.record` states the same identity again, inline
(`budget_guard.py:197`), in a module that already imports the seam and
called `cost_ledger.read(root)` three lines earlier:

```python
    entries, problems = cost_ledger.read(root)
    ...
    if any(existing.get("wo") == wo and existing.get("run_id") == run_id
           for existing in entries):
```

The repo's own pre-pass finds it unaided:

```
one-owner: budget_guard.py:167 record and cost_ledger.py:126 row_key read the same payload keys (run_id, wo) — one fact, one owner
```

## Reproduction — the two owners do not move together

Mutate the seam's identity to three fields in a throwaway worktree at
`622e7c0`:

```python
-    return entry["wo"], entry["run_id"]
+    return entry["wo"], entry["run_id"], entry["model"]
```

The seam's own suite notices, once:

```
FAIL: test_the_identity_is_wo_plus_run_id (tests.test_cost_ledger.TestRowKey.test_the_identity_is_wo_plus_run_id)
Ran 52 tests in 0.012s
FAILED (failures=1)
```

The module that copies the identity notices **nothing**:

```
Ran 47 tests in 0.277s

OK
```

And the two now disagree about the same pair of rows. One ledger, one
`(WO-0001, run-1)`, two different models — under the mutated identity the
seam calls them distinct and `budget_guard` still calls them a duplicate:

```
seam says distinct: True
budget_guard says: ["bg: refusing to record WO-0001: run_id 'run-1' is already in the ledger — recording it twice would double-count the run against the monthly cap"]
```

That is the whole defect in one line of output: the writer's refusal rule
and the reader's identity rule are separate facts that happen to agree
today.

## Why it matters

`record`'s refusal is the thing standing between a re-recorded run and a
double-count against ADR-0034's monthly circuit breaker. If ADR-0041's
identity is ever widened, narrowed, or renamed, the seam moves and this
copy does not — and the failure is silent in both directions:

- **Copy too narrow** → rows the seam calls distinct get refused, and real
  spend never reaches the ledger. The cap then under-counts, which is the
  exact failure `record` exists to prevent.
- **Copy too wide** → rows the seam calls identical get appended twice and
  the month double-counts.

Neither shows up as an exception. Both show up as a wrong number in a
circuit breaker nobody looks at until it fires.

## The tolerant `.get()` is a second, smaller finding

The copy uses `existing.get(...)`; the seam subscripts. That asymmetry is
not a style difference — `cost_ledger.read`'s docstring makes subscripting
the contract:

```
THE READ CONTRACT: entries are validated dicts — the full shape is
established right here, so callers subscript LEDGER_FIELDS freely
```

and `record` returns early when `read` reports any problem, so every entry
reaching the check is validated. The `.get()` defends a state that cannot
occur, and it defends it *wrongly*: two rows each missing `wo` would compare
`None == None` and read as duplicates. Unreachable today, and worth deleting
rather than preserving through the fold.

## Where it came from

Backlog seed 49, written by `maintenance:one-fact-one-owner`. That run found
the pair, adjudicated it at full depth, and deliberately left the fold out
of scope — it was building the finder, not cleaning up after it.

## Not reproduced

Nothing about the *live* ledger. `docs/factory/costs.jsonl` was never read
for this brief and never written; the probe above builds its own ledger in a
tempdir. No claim is made here about spend already recorded.
