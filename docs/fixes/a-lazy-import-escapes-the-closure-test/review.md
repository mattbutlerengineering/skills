---
stage: review
run: maintenance:a-lazy-import-escapes-the-closure-test
date: 2026-08-30
assumptions: []
---

# Review: a lazy import escapes the payload closure test

Self-authored; ADR-0036 clause 2 still wants a non-authoring reviewer.

## Findings

### 1. It extends the existing class rather than starting a new file — kept

`TestPayloadToolsImport` already owns "every mirrored tool's imports
resolve inside the payload". This is the same invariant over the other
half of the import surface, and its docstring already tells the
`rejection_mining`/`sweeps` story that motivates both. Splitting the
lazy half into a separate file would be its own drift — two homes for
one rule.

The cost is contention: `tests/test_factory_init.py` is a busy file and
several open PRs touch it. Accepted, because the alternative is worse
and the conflict is additive.

### 2. The unfollowed-shape assertion is the load-bearing one — kept

The obvious version of this test derives a set and asserts it is a
subset of MIRRORS. That version **passes when the derivation breaks** —
a new import shape yields an empty set, and the empty set is a subset of
everything. So the derivation reports what it could not follow, and that
list must be empty. Criterion 4 mutates exactly this.

Same reasoning behind `assertTrue(names, ...)`: an empty universe is
never a clean one, the posture `one_owner.source_files` already takes.

### 3. Scanning only `gates.py` — deliberate, and stated

Swept every mirrored tool for `importlib` / `__import__`: `gates.py` is
the only one. Generalising the scan across all 17 payload modules today
would be a loop over a single item, and speculative generality is what
this repo's implementation discipline asks not to write. The limit is
recorded in `verification.md` under what-is-not-verified so it reads as
a boundary rather than an oversight.

### 4. The list is derived, not typed — non-negotiable here

Hard-coding `{"assembler", "human_gates", "label_sync"}` would be one
line instead of forty and wrong the day a fourth lazy import appears.
This repo shipped exactly that defect a day ago
(`docs/fixes/a-call-site-list-that-drifted/`), where a hand-typed
docstring enumeration outlived the code it described. The forty lines
buy a test that cannot go stale silently.

### 5. The false-negative mutation is disclosed — necessary, not optional

`verification.md` §5 records that criterion 2 first reported `OK`
because the mutation never landed, and that the confirming grep used the
same wrong quoting and appeared to agree. Hiding it would leave a
verification section whose evidence was, for one run, fabricated by
accident. It is the second instance of that pattern in two runs, which
makes it a habit worth naming rather than an incident worth burying.

### 6. Not a gates detector — same reasoning as the shadow run

Consistent with `docs/fixes/a-shadowed-definition-is-invisible/`: the
check needs the real repo tree, `gates.py` is mirrored (so a detector
costs a payload copy, a manifest regeneration, and a conflict with
#377), and `tests/test_factory_init.py` is already the established home
for payload-structural invariants. Downstream stamped repos therefore do
not inherit this check — the same accepted trade, stated the same way.
