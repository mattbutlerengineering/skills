---
stage: review
run: maintenance:a-call-site-list-that-drifted
date: 2026-08-30
assumptions: []
---

# Review: a call-site list that drifted

Self-authored; ADR-0036 clause 2 still wants a non-authoring reviewer.

## Findings

### 1. Correcting the number would have been the same defect — resolved

The obvious fix is `s/Five/Three/` and a corrected list. That restores
the claim and restores the mechanism that let it rot: nothing checks it,
so the next fold breaks it again silently. The list is derived in a test
instead. This is the fix pattern the previous two instances of this
class also landed on.

### 2. The test asserts in both directions — kept, and it earns it

`assertEqual(documented, actual)` on sets, not `assertTrue(all(...))`.
The stale claim would have survived a one-directional check: every
module it named that was still a caller *was* still a caller. What was
wrong was the extras and the count. Both mutations are recorded in
`verification.md` §2–§3.

### 3. The delimiter is a real coupling, and it is guarded — accepted

The test reads a `Call sites (...): <modules> — ` shape out of prose.
Prose can be reworded, so the test carries an explicit failure message
naming the shape it needs, rather than silently matching nothing and
passing. That message is what fired in the red run.

### 4. Whether this should be a repo-wide detector — deliberately not now

A checker that finds every stale enumeration in every docstring is a
genuinely interesting tool and a genuinely hard one (it must decide what
counts as a claim). `one_owner.py` is the precedent for that kind of
pass, and it is a pre-pass rather than a gate for exactly this reason.
Out of scope here; noted so the question is not lost.

### 5. Scope stayed at one docstring — held

The audit that found this surfaced other enumerations in the same sweep
(`cli.gh_read`'s "fourteen call sites", `cli`'s "Two tools",
`plane_drift`'s "Two tools"). `cli.gh_read`'s was checked by hand and is
CORRECT — fourteen sites, counted. The others are historical
("Before this seam ...") and describe the past, not the present. Only
the one live, wrong claim is fixed here.
