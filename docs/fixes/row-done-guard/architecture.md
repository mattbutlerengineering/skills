---
stage: architect
run: maintenance:row-done-guard
date: 2026-08-23
assumptions: ["Chosen without live interview: this run is autorun-driven, so the option comparison is decided on the measured call-site facts in defect.md and on ADR-0058's own record, both cited so the operator can overturn it by reading rather than re-deriving.", "No ADR is offered. ADR-0058 already named this exact gap in its Consequences ('it is seeded, not decided here'), so the decision is unsurprising in context, one line to revert, and carries no trade-off the artifact cannot hold. ADR-0058 is NOT edited to point at this run — a live ADR is superseded or amended by a new one, never rewritten in place."]
---

# Architecture: the guard goes at the owner, not at the caller that noticed

## Approach

Give `row_done` the same `ROW.match` guard its six siblings apply, in the
same shape they use. Change nothing else.

The defect is not that detector G reads the line badly; it is that the
module answers "is this a breakdown row" twice and the two answers differ.
Fixing the answer at its owner fixes every reader at once — the four
already-guarded call sites keep behaving identically, and detector G, the
one path where the difference escapes, stops counting a line no other tool
can parse.

## Components

### `knowledge_plane.row_done` — the checked-row accessor

- Responsibility: whether a line is a breakdown row AND its box is
  checked. Gains the first half, which it has been assuming since it
  arrived on 2026-08-10.
- Written in the siblings' shape — `if not ROW.match(line): return False`
  — rather than as a compound boolean, because reading like its siblings
  is the substance of the fix, not decoration.
- Collaborators: `ROW` and `DONE_ROW`, both already in this module;
  `gates.merged_wo_rows`, `work_queue.rows`, `plane_drift`, and the
  dashboard's drift check, none of which change.

### `gates.merged_wo_rows` — detector G

- **Unchanged.** It keeps `WO_TOKEN.search(line)` and its ADR-0043
  pre-ledger exclusion. What changes is what `row_done` hands it.
- This is the component the run is *about* and the one it does not touch;
  see the rejected alternative below.

## Data model

No change. A breakdown row is still a line of markdown, read on demand by
accessors that own its grammar; nothing is stored, parsed once, or cached.

## Interfaces & contracts

### `row_done(line) -> bool`

- Input: one line of a breakdown file, untrusted in the sense that a human
  typed it.
- Output: `True` only when the line is a row by `ROW`'s grammar and its
  box is checked. **The contract narrows**: lines matching `DONE_ROW` but
  not `ROW` move from `True` to `False`.
- Failure modes: none raised, unchanged. The narrowing is the whole change
  and is stated here so it is not discovered.

### What the narrowing costs, measured

Zero rows in the tree today. Every breakdown line was scanned through both
grammars (`defect.md`, *What is NOT claimed*): 1460 lines, 0
disagreements. So detector G's count does not move on this repo — the
change is a contract repair whose observable effect is on lines nobody has
written yet.

That measurement is the evidence ADR-0058 said this deserved when it left
the gap open, and it is the reason the fix does not need a staged rollout
or a warning period.

## Stack & dependencies

Nothing new. Both regexes already exist in the module; the change adds no
import and no dependency. `knowledge_plane.py` is a `factory_init.MIRRORS`
entry, so the edit carries a regenerated payload copy and manifest in the
same commit.

## Decisions & alternatives

- **Guard at `row_done`** over **fixing detector G's call site to use
  `row_work_order`** — the call-site change would also close the escape,
  and it is a real improvement on its own terms (G reads a raw line where
  a guarded accessor exists). It loses as *the fix* because it patches the
  one caller that noticed while leaving the grammar wrong at its owner, so
  the next caller to reach `row_done` without a sibling inherits the same
  trap. Worth doing; worth doing separately. Seeded at Operate.
- **Guard at `row_done`** over **retiring `DONE_ROW` and expressing
  `row_done` as `ROW` plus a box test** — attractive, because once the
  guard is in place `DONE_ROW`'s only remaining job is choosing which box.
  It loses because ADR-0058 measured and accepted the current roster
  eleven days ago; collapsing it is a roster decision, and riding one on a
  correctness fix is how the roster got stale the first time.
- **Guard at `row_done`** over **leaving it and documenting the quirk** —
  rejected because the quirk's cost is paid by whoever hits it: a
  detector-G problem naming a work order no other tool can see, debugged
  at the detector rather than at the typo that caused it.
- **Compound boolean** over **the siblings' early-return shape** —
  rejected on the run's own thesis. The accessor should be visibly one of
  a family.

## ADRs

None, and deliberately. ADR-0058's Consequences already record this gap
and say closing it "is a behaviour change with its own risk; it is seeded,
not decided here" — so the decision is expected rather than surprising,
and the evidence it asked for is `defect.md`'s scan plus this artifact.
ADR-0058 stays exactly as written: a live ADR is amended or superseded by
a new one, never edited to point at the run that resolved something it
listed as open.
