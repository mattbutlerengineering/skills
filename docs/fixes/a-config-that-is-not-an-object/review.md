---
stage: review
run: maintenance:a-config-that-is-not-an-object
date: 2026-08-30
assumptions: []
---

# Review: a config that is not an object

Self-authored. ADR-0036 clause 2 still requires a non-authoring reviewer;
this records what the run found reviewing itself.

## Findings

### 1. Where the rule lives — resolved, and it changed the design

The first cut guarded `load` alone. That fixes the five runtime callers
and leaves detector F — the CI gate — still raising, because F parses
each candidate home itself rather than going through `load`. Guarding
only the seam would have shipped a fix whose own reproduction still
reproduced.

The second cut guarded both call sites with a local `isinstance` check.
That is two copies of one rule, in exactly the two places this repo has
already paid for disagreeing (detector F's field grammar was folded into
`factory_config.config_problems` for this reason).

Shipped: `object_problems` in `factory_config`, beside `config_problems`,
returning **unlocated** suffixes that each caller prefixes — the split
`cost_ledger.line_problems` already uses. One rule, two labels, no third
copy possible.

### 2. Why F skips its field checks rather than reporting them too — kept

On a non-object, F `continue`s instead of also running the key-set
checks. Reporting `budgets_usd must map exactly S, M, L` about the number
`5` describes the checker's confusion, not the file. This matches the
`is not valid JSON` branch immediately above it, and matches the
reasoning PR #394's `object_problems` docstring gives for the same
choice in `lint.py`.

### 3. The per-file skip is not a per-run skip — pinned

`continue`, not `return`. A broken payload copy must not hide a broken
installed copy, since F's whole reason for checking every candidate is
that the two homes drift independently.
`test_a_non_object_home_does_not_mask_the_other_home` pins it; without
that test the `continue`/`return` distinction is invisible.

### 4. Naming collision with PR #394 — deliberate, noted

`lint.py` grows an `object_problems(data, label)` on PR #394 and this run
adds `factory_config.object_problems(config)`. Same name, different
signature, different module, no import between them.

This is **not** a candidate for a shared module: CLAUDE.md's bar is
multiple real callers AND observed divergence, and these two have
neither — they are two modules independently applying one language rule,
the way half a dozen modules independently call `isinstance`. Recorded
as a backlog seed instead, because the *class* now has four instances and
the real question is whether a detector should find the fifth.

### 5. Accessors left unguarded — deliberate

`resolve_cap` and friends still open with `config.get(...)` and no
dict-check. `load` is now the only way a config enters, and it
establishes the shape — the same read-contract `cost_ledger.read`
documents. Adding a second check per accessor is defensive code for a
state that can no longer occur (implementation-discipline.md). The
invariant is stated in `object_problems`' docstring, where a future
caller will read it.

## Scope

Two modules, four files (each mirrored), six tests, one manifest
regeneration. Nothing else in the diff.
