---
stage: capture
run: maintenance:row-done-guard
date: 2026-08-23
re-entry: architect
assumptions: ["re-entry is architect, not implement: adding the guard changes what a shipped detector counts as a merged work order, and knowledge_plane.py is the ADR-0037/0039 seam whose row grammar ADR-0058 already adjudicated once. Which function absorbs the change — the accessor or detector G's call site — is a decision to record, not a line to write.", "Severity is judged on the contract, not on today's tree: the scan below found zero live instances, and this brief says so rather than implying a live break."]
---

# Defect: one accessor's idea of a row is not the other four's

Origin: backlog seed `docs/backlog.md:41` (from: session:2026-08-22),
claimed as `(claimed: maintenance:row-done-guard)`. Tracking issue #327.

## Defect

`knowledge_plane.row_done` (knowledge_plane.py:181) is the only `row_*`
accessor that does not apply the module's own `ROW.match` guard:

```python
ROW = re.compile(r"^\s*[-*+]\s+\[[ xX]\]\s")
DONE_ROW = re.compile(r"^\s*[-*+]\s+\[x\]", re.IGNORECASE)

def row_done(line):
    return bool(DONE_ROW.match(line))
```

`ROW` requires whitespace after the closing bracket. `DONE_ROW` does not.
Every sibling — `row_work_order`, `row_tracker_issue`, `row_pre_ledger`,
`row_size`, `row_title`, `row_blockers` — opens with `if not ROW.match(line)`
and returns its empty value. `row_done` returns `True`.

Expected: one module, one answer to "is this line a breakdown row".
Observed: two, and the shipped detector that reads the raw line rather
than a sibling accessor is where they diverge.

## Reproduction / Evidence

Driven at `622e7c0` through the public accessors:

```
'- [x]a **WO-0002** no space after the box — size:M, blocked by: —'
  row_done=True  row_work_order=None  row_size=None  row_title=None  row_blockers=[]  row_pre_ledger=False
'- [x]**WO-0003** bold straight after the box — size:L'
  row_done=True  row_work_order=None  row_size=None  row_title=None  row_blockers=[]  row_pre_ledger=False
```

## Blast radius — narrower than the seed said, and the narrowing is the point

The seed states that "the five call sites that ask whether a row is done
therefore disagree with the four that ask anything else". The tree does
not do that. Three of the five reach `row_done` only through a sibling
that has already applied the guard, so a malformed line never arrives:

- `work_queue.rows` (work_queue.py:70) — gated by `row_work_order(line)`
  at :67, which returns `None` and `continue`s.
- `plane_drift` (plane_drift.py:90) and the dashboard drift check that
  calls it — gated by `row_tracker_issue(line)` at :77, same shape.

**`gates.merged_wo_rows` (gates.py:581) is the one unguarded path**, and
it is unguarded exactly because it uses no sibling accessor:

```python
            wo = WO_TOKEN.search(line)
            if (row_done(line) and wo
                    and not row_pre_ledger(line)):
```

`WO_TOKEN.search` reads the raw line, so it finds the token in a row no
accessor will parse. `row_pre_ledger` *does* apply the guard and returns
`False` — which passes the `not`. Detector G therefore counts the line as
a merged work order owing a ledger row, while every other reader of the
same line considers it no row at all.

## What is NOT claimed

No live instance exists. Every breakdown row in the tree today was
scanned through the same accessors:

```
lines scanned: 1460
disagreements in the tree today: 0
```

So this is a latent contract defect, not a live break: the cost is that a
typo in a breakdown row would produce a detector-G problem naming a work
order that no other tool can see, and the first person to hit it would
debug the detector rather than the row. That is the severity being
claimed — no more.

## Why it was left alone before

ADR-0058 collapsed the checkbox-regex roster from three owners to two and
its run found this. It was deliberately not folded in, because adding the
guard moves what a shipped detector counts and that deserves its own
evidence rather than a ride on a refactor. This run is that evidence.
