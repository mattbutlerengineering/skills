---
stage: architect
run: maintenance:dedup-identity-has-two-owners
date: 2026-08-25
ux: skipped — no user-facing surface; the change is one comparison inside a factory tool
assumptions: ["The fold's shape was not chosen on taste. `gate_digest` is the other module that dedupes ledger rows and it already does exactly this, so the design question reduced to `match the sibling` — recorded as D1 rather than argued from scratch.", "The refusal message is treated as a fixed contract: two tests pin it byte-for-byte and this run has no mandate to reword it. The fold changes what is compared, not what is said."]
---

# Architecture: fold the dedup identity into its seam

## Approach

Delete `budget_guard.record`'s inline identity and read it through
`cost_ledger.row_key`, the function whose docstring already claims it. One
comparison changes; no signature, no message, no behaviour.

## The design was already made, one module over

`gate_digest` is the only other caller that dedupes ledger rows, and it
reads the identity through the seam (`gate_digest.py:116-127`):

```python
    The dedup identity is cost_ledger.row_key
    ...
    recorded = {cost_ledger.row_key(entry) for entry in existing}
    ...
            if cost_ledger.row_key(row) not in recorded:
```

So `budget_guard.record` is not one of two equal owners — it is the **odd
one out** among the seam's two dedupe callers. That settles the shape: the
fold matches the sibling rather than inventing a third idiom.

### D1 — how the comparison is written

**Chosen:** a set of recorded identities, membership-tested.

```python
    recorded = {cost_ledger.row_key(existing) for existing in entries}
    if cost_ledger.row_key(row) in recorded:
```

**Rejected — `any(row_key(e) == row_key(row) for e in entries)`.** Same
result, recomputes the new row's identity once per ledger line, and reads as
a scan where the message says *"is already in the ledger"*. The set says
membership, which is what the refusal means.

**Rejected — a new `cost_ledger.contains(entries, row)` helper.** It would be
a pass-through over `row_key`, and `read`'s own docstring already draws that
line: *"What the seam owns are the semantic rules over a row: row_key
(identity), in_month (window), gate_wait (gate rows), wo_token (typed
token)"*. Identity comparison is owned; wrapping it again adds a name
without adding a fact. It would also give the seam a function with one
caller, which the repo's seam bar rejects.

## The `.get()` disappears, and that is a decision

The inline copy is tolerant — `existing.get("wo")` — where the seam
subscripts. Folding removes the tolerance, and that is correct rather than
incidental:

- `cost_ledger.read`'s stated contract is that `entries` are validated
  dicts, established at the read: *"callers subscript LEDGER_FIELDS
  freely"*.
- `record` returns early on any problem from `read`, so no unvalidated row
  reaches the comparison.
- The tolerance was also **wrong on its own terms**: two rows each missing
  `wo` compare `None == None` and read as duplicates. Defensive code for an
  impossible state that would have misbehaved if the state occurred.

An invariant that cannot be violated does not get a runtime check; it gets
the seam's subscript and this paragraph.

## Components

| Component | Responsibility | Change |
| --- | --- | --- |
| `cost_ledger.row_key` | ADR-0041's `(wo, run_id)` identity | none — it already owns it |
| `budget_guard.record` | Refuse a shape-invalid or already-recorded row before the append | reads the identity through the seam |
| `budget_guard.record_run` | `record` with spend read from the harness file | none — it inherits `record`'s guard |
| `factory/templates/tools/factory/budget_guard.py` | The mirrored payload copy | regenerated with the manifest |

## Contracts

**Unchanged, and pinned by existing tests:**

- `record(root, wo, run_id, model, tokens, cost, outcome, at) -> [problem]`,
  empty on success.
- The refusal string, byte-for-byte:
  `bg: refusing to record {wo}: run_id {run_id!r} is already in the ledger — recording it twice would double-count the run against the monthly cap`
  (`tests/test_budget_guard.py:371` and `:478`).
- Order of refusals: shape, then read problems, then double-count. The fold
  sits inside the third and moves nothing.

**Newly required:**

- Mutating `cost_ledger.row_key`'s identity must fail a `budget_guard`
  test. That is the coupling the defect showed missing, and the only way to
  prove the fold took: a test that passes both before and after proves
  nothing about ownership.

## Failure modes

- **An entry missing a keyed field** now raises `KeyError` instead of
  comparing `None`. Unreachable through `record` (the read contract, plus
  the early return), and a raise is the honest outcome if the contract is
  ever broken — a silent wrong answer in a double-count guard is the worse
  half of that trade.
- **An empty ledger** builds an empty set and the membership test is False.
  Same as today.

## Stack

Nothing new. Stdlib only; `budget_guard` already imports `cost_ledger`.

## Mirroring

`budget_guard.py` is in `factory_init.MIRRORS`, so the payload copy and
`factory/manifest.json` are regenerated with
`python3 factory_init.py update-manifest` in the same commit. Detector E
gates manifest↔payload; `tests/test_factory_init.py` pins payload↔root.
