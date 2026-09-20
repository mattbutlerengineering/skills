---
stage: verify
run: maintenance:dedup-identity-has-two-owners
date: 2026-08-25
assumptions: ["The centrepiece is the regression from defect.md, run in both directions: mutate the seam BEFORE the fold (the copy does not follow) and AFTER (it does). A same-shape test that passes in both states would prove nothing, which is the defect's own signature.", "Every battery measurement was taken in a detached worktree at cc0e297 whose `git status --porcelain` is empty — another session's untracked ADR fails detector D in the shared checkout, unchanged from the previous run."]
---

# Verification: fold the dedup identity into its seam

## C1 — `record` reads the identity through the seam

**Check.** The diff.

```diff
-    if any(existing.get("wo") == wo and existing.get("run_id") == run_id
-           for existing in entries):
+    # Through the seam, never a second copy: cost_ledger.row_key owns
+    # ADR-0041's identity, and gate_digest's dedup already reads it this
+    # way. Subscripting is safe here because read() returns validated rows
+    # and the problem branch above already returned.
+    recorded = {cost_ledger.row_key(existing) for existing in entries}
+    if cost_ledger.row_key(row) in recorded:
```

Six lines changed in one function; no signature, no message, no other call
site. **PASS.**

## C2 — the regression: mutating the seam now reaches this suite

The mutation is the one `defect.md` recorded — `row_key` widened to a
three-field identity in a throwaway worktree:

```diff
-    return entry["wo"], entry["run_id"]
+    return entry["wo"], entry["run_id"], entry["model"]
```

**Before the fold**, with the new test present and the old inline copy still
in place:

```
AssertionError: True != False : record and cost_ledger.row_key disagree about whether ('WO-0007', 'r-1', 'claude-haiku-4-5') is already in the ledger

Ran 48 tests in 0.272s

FAILED (failures=1)
```

**After the fold**, same mutation, same test:

```
Ran 48 tests in 0.271s

OK
```

Read together those two runs are the whole verification. The seam moved; the
copy did not follow and the suite said so; the fold made it follow. Before
this run the same mutation produced `Ran 47 tests / OK` — the module noticed
nothing at all.

**PASS.**

## C3 — the one-owner pair is gone, and nothing took its place

Findings sorted and compared across the fold, not eyeballed:

```
=== groups removed by the fold ===
one-owner: budget_guard.py:167 record and cost_ledger.py:126 row_key read the same payload keys (run_id, wo) — one fact, one owner
=== groups ADDED by the fold ===
(empty above means none)
```

Total, at the branch tip:

```
one-owner: 8 problem(s)
```

Nine before, eight after, and the one that left is the one this run exists
to remove. **PASS.**

## C4 — the refusal contract is unchanged

Both cases pinning the refusal string byte-for-byte
(`tests/test_budget_guard.py:371` and `:478`, the second reaching it through
`record_run`) pass untouched — neither was edited by this run:

```
Ran 48 tests in 0.309s

OK
```

**PASS.**

## C5 — the payload and manifest moved with the root

```
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)

 M factory/manifest.json
 M factory/templates/tools/factory/budget_guard.py
```

The payload diff is the root diff, and `tests/test_factory_init.py` (which
pins payload↔root) passes:

```
Ran 52 tests in 1.529s

OK
```

Detector E, which gates manifest↔payload, reports nothing at the tip — see
the battery below. **PASS.**

## C6 — the battery

Detached worktree at `cc0e297`, `git status --porcelain` empty:

```
Ran 1345 tests in 16.582s

OK
lint: 0 problem(s) across 24 skills
gates: 0 problem(s)
selftest: ok
```

The count is one higher than the base this branch was cut from, and the
delta is measured rather than inferred — same worktree procedure at
`622e7c0`:

```
Ran 1344 tests in 16.052s

OK
```

One test added, none removed or edited. **PASS.**

## What was NOT verified

- **Nothing was measured against the live ledger.** `docs/factory/costs.jsonl`
  was neither read nor written by any stage of this run; every probe builds
  its own ledger in a tempdir. The fold changes what `record` compares, not
  what is already recorded, so no claim is made about existing rows.
- **`gate_digest`'s dedup was read, not re-verified.** It is the precedent
  the design follows (`gate_digest.py:116-127`) and this run does not touch
  it; its own suite passes in the battery above, unchanged.
- **The `KeyError` path is unreachable, so it is untested.** Architecture
  records why: `cost_ledger.read`'s contract validates entries and `record`
  returns early on any read problem. Writing a test for it would mean
  building a state the module's own contract forbids.
- **The contaminated checkout persists.** `python3 gates.py` in the working
  checkout still fails on another session's untracked ADR file, exactly as
  the previous run recorded. Unchanged by this run, and the reason every
  number above comes from a worktree.
