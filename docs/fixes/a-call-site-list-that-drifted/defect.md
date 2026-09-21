---
stage: capture
run: maintenance:a-call-site-list-that-drifted
date: 2026-08-30
re-entry: implement
assumptions: ["no user-supplied brief exists for this run; the defect was
  found by a stated-convention audit of the repo's own docstrings"]
---

# Defect: a call-site list that drifted

## Defect

`knowledge_plane.row_done` — the one owner of the checked-row grammar
(ADR-0058) — enumerates its own callers:

```python
    The one owner of the checked-row grammar (ADR-0058). Five call sites
    ask: detector G's merged_wo_rows, the reconcile sweep, the work
    queue's row read, and the dashboard's drift check twice.
```

Every part of that count is wrong. Derived from the source, the callers
are:

| module | site |
|---|---|
| `gates.py` | detector G's merged-row walk |
| `work_queue.py` | the row read |
| `plane_drift.py` | the shared cross-plane drift rule |

Three, not five. And neither the reconcile sweep nor the dashboard calls
it at all — `sweeps.py` and `dashboard.py` contain no reference to
`row_done`:

```
$ grep -n "row_done" sweeps.py dashboard.py
  (no matches)
```

## Why it happened

ADR-0060 (shipped in #316, `refactor(factory): one cross-plane drift
rule, one absence policy`) folded the reconcile sweep's drift check and
the dashboard's into one shared `plane_drift.reconcile_drift`. Three call
sites became one. The docstring still describes the world before that
fold, naming two modules that stopped asking and counting a third site
that no longer exists.

## Why it matters

This is documentation, so nothing computes a wrong answer. What it costs
is the thing the docstring exists to buy: `row_done` is a declared
single-owner grammar, and its caller list is how a reader — or an agent
picking up a work order — knows the blast radius of changing it. A list
that names `sweeps.py` sends that reader to a module with nothing in it,
and a list that says "five" invites the assumption that two sites were
missed rather than that the list is stale.

It is also the third recorded instance of one pattern in this repo: a
docstring claim that ENUMERATES goes stale silently, because nothing
checks it. Enumerations are the highest-yield target precisely because
they are the most specific and the least maintained.

## Reproduction

```
$ python3 -c "
import ast, pathlib
for p in sorted(pathlib.Path('.').glob('*.py')):
    if p.name == 'knowledge_plane.py': continue
    for n in ast.walk(ast.parse(p.read_text())):
        if isinstance(n, ast.Call):
            f = n.func
            name = getattr(f, 'id', None) or getattr(f, 'attr', None)
            if name == 'row_done': print(' ', p.name)
"
  gates.py
  plane_drift.py
  work_queue.py
```

Against a docstring that names five sites, two of them in modules that
do not appear above.

## Fix

Not "correct the number" — that is the same defect one edit later. The
list is DERIVED in a test and compared to the prose in both directions,
so the docstring keeps the useful enumeration and can no longer drift
from it. The listing gets a delimited form
(`Call sites (...): <modules> — `) so the test has something precise to
read, and the docstring is normalised before matching so a rewrap does
not fail the test for the wrong reason.

## Notes

Found by the stated-convention audit technique: take a module's own
docstring claim and test it against the code. `knowledge_plane.py` is
also touched by open PR #328, which APPENDS to this same docstring
without correcting the enumeration above it — contention is recorded in
the PR body.
