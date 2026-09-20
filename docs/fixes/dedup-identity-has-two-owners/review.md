---
stage: review
run: maintenance:dedup-identity-has-two-owners
date: 2026-08-25
assumptions: ["Scaled as the protocol asks for a scoped maintenance fix: three passes over this run's diff, with Verify's regression as the floor. The correctness pass went at the fold's equivalence claim rather than at the fold's shape — `semantically identical today` is the claim a six-line change like this actually rests on, and it is checkable.", "The review's own finding was fixed and then proved in a throwaway worktree in both directions, the same way Verify proved the fold."]
---

# Review: fold the dedup identity into its seam

## What was examined

`git diff 88fbb34..HEAD` — `budget_guard.py`, its payload mirror,
`factory/manifest.json`, `tests/test_budget_guard.py`, and the run
artifacts. Three passes: correctness, design, security.

Six changed lines of logic. The reviewable claim is bigger than the diff:
*this comparison means exactly what the old one meant, and will keep
meaning what the seam means.* The first half is checkable today, the second
is what the new test is for.

## F1 — the coupling test caught one direction of drift, not both. **Minor. Fixed.**

As written at I1, the test compared `record`'s verdict against the seam's
for a single candidate: same `(wo, run_id)`, different `model`. That catches
an identity that **grows** — the mutation `defect.md` used.

It does not catch one that **shrinks**. Narrow `row_key` to `(entry["wo"],)`
and the seam starts calling two different runs of one work order duplicates,
while a stale inline copy keeps accepting them. Both the seam and the old
copy answer "not a duplicate" for the model candidate, so the single-candidate
test agrees with itself and passes.

**Failure scenario.** ADR-0041's identity is narrowed — say gate rows move
to their own keying and `run_id` stops being part of the cost identity. The
seam changes, this suite stays green, and `record` silently keeps accepting
rows the ledger now considers already present. Double-counted spend against
the monthly cap, which is the failure `record` exists to prevent, reached by
the opposite road from the one this run measured.

**Fix.** Two candidates, each differing from the recorded row in exactly one
field — a new `model` (ignored by today's identity, honoured by a wider one)
and a new `run_id` (honoured by today's, ignored by a narrower one) — each in
its own subTest and its own ledger.

Proved the same way the fold was, in a throwaway worktree. Narrowed seam,
**pre-fold** code:

```
AssertionError: False != True : record and cost_ledger.row_key disagree about whether ('WO-0007', 'r-2', 'claude-sonnet-5') is already in the ledger
FAILED (failures=1)
```

Narrowed seam, **folded** code:

```
Ran 1 test in 0.002s

OK
```

So both directions now fail before the fold and pass after it.

## Correctness pass — the equivalence claim, checked rather than asserted

The fold replaces a comparison against the *parameters* with a comparison
against `row_key` of the *built row*. That is only a no-op if `entry()`
passes `wo` and `run_id` through untouched, so I read it rather than assumed
it:

```python
LEDGER_FIELDS = ("wo", "run_id", "model", "tokens", "cost", "outcome")
...
    record = dict(zip(LEDGER_FIELDS, (wo, run_id, model, tokens, cost,
                                      outcome)))
```

A positional `zip`, no normalisation, no coercion — `row_key(row)` is
`(wo, run_id)` exactly. **Equivalence holds.**

The rest of the pass:

- **`.get()` → subscript on existing entries.** Identical whenever the key
  is present, which `cost_ledger.read`'s stated contract guarantees, and
  `record` returns before the comparison on any read problem. The only
  behaviour that changes is in a state the contract forbids, where a raise
  beats the old silent `None == None` duplicate. Architecture records this
  as a decision; I re-derived it and agree.
- **Set vs `any()`.** Same result. `entries` is already fully materialised by
  `read`, so building the set adds one pass over a list that was in memory
  anyway — no new I/O, no new failure mode.
- **The refusal message and its ordering.** Untouched, and both byte-for-byte
  pins pass unedited — including the one reaching it through `record_run`,
  which is the path that proves `record_run` still inherits the guard rather
  than having grown a copy.
- **Empty ledger.** Empty set, membership False, append. Same as before.

## Design pass

No deviation from `architecture.md`; the Notes section of `breakdown.md` is
empty because nothing disagreed with the design.

The strongest thing about this change is that it did not invent anything:
`gate_digest.py:116-127` already dedupes ledger rows through
`cost_ledger.row_key` with the same set-membership shape. After the fold the
seam has two callers that dedupe and both read the identity the same way,
which is the state the seam bar exists to produce. The rejected
`cost_ledger.contains()` helper would have undone that by adding a name over
a rule the seam already owns.

**Left deliberately.** `budget_guard.py:55 CONTINUE` and
`cost_report.py:44 CONTINUE` are a second one-owner pair in the same module,
excluded by the brief. Different fact, different remedy, and folding it here
would have made this diff a cleanup rather than a fix. Still open, still on
the pre-pass:

```
one-owner: 8 problem(s)
```

## Security pass

Nothing. No new input, no new boundary, no subprocess, no file write beyond
the append that already existed, and the append is still gated by the same
two refusals in the same order. The change cannot make `record` write a row
it would previously have refused on shape, because the shape check runs
first and is untouched.

Worth stating for the merger, since this is the double-count guard: the fold
does not weaken the guard. Under today's identity it refuses exactly what it
refused before — the regression proves that in both directions, and the two
message pins prove the refusal still reads the same.

## State after the fix

Detached worktree at the branch tip, `git status --porcelain` empty:

```
Ran 1345 tests in 16.954s

OK
lint: 0 problem(s) across 24 skills
gates: 0 problem(s)
selftest: ok
one-owner: 8 problem(s)
```

Still 1345, the count Verify recorded: F1's fix added a second candidate
inside the existing case as a subTest, and subTests do not raise the test
count. Worth saying out loud, because a reviewer reading only the totals
would conclude the review added no coverage — the coverage is in the two
worktree runs above, not in the number.

No critical findings. F1 fixed in this run.
