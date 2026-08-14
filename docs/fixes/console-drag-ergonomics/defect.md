---
stage: capture
run: maintenance:console-drag-ergonomics
date: 2026-08-14
re-entry: implement
assumptions:
  - "Interview satisfied from the operator's same-day first-use report
    (2026-08-14, quoted below) and the process-dashboard retro's Change
    entry rather than a fresh question-at-a-time interview — the loop
    was routed here by the operator choosing 'Drag-fix run' minutes
    after reporting the defect, so the knowledge was already on the
    record."
  - "Scope held to the seed's text: click-to-move controls plus one
    verified browser reorder. Debugging HTML5 drag pointer physics is
    explicitly out (retro's Change entry chose the fallback control
    over the pointer chase); drag stays as-is alongside the new
    controls."
---

# Defect: Console backlog reorder never lands from a real browser

## Defect

The console's backlog panel supports drag-and-drop reordering of
unclaimed seeds, but in a real browser the drag is hard to use and no
reorder has ever actually landed. Expected: the operator moves a seed
row, the panel marks the order unsaved, Save rewrites `docs/backlog.md`
with claim markers intact. Observed: the operator found the drag
"difficult", was unsure whether it did anything, and the file never
changed.

## Reproduction / Evidence

- Operator report, first real use (2026-08-14): "it difficult to drag
  and drop but i think it works?"
- Corroboration: `docs/backlog.md` showed no rewrite after that session
  — whatever happened in the browser, no reorder landed. Which link
  failed (drag start, drop registration, or Save never pressed) was not
  observed; the operator couldn't tell either, which is itself part of
  the defect (no feedback affordance).
- Predicted: `verification.md` of feature:process-dashboard flagged
  "hand-in-browser drag" as the one unverified flow; the retro's Change
  entry commits drag-and-drop work to a hand-in-browser check in the
  same work order from now on.

The save path itself is not in question — see Ruled out.

## Root-cause hypothesis

Hypothesis, not a finding: HTML5 drag-and-drop ergonomics. Seed rows
are small targets with no insertion indicator, text selection competes
with drag initiation on text-heavy rows, and a drop outside a row's
hitbox silently does nothing — so drags feel inert and the operator
cannot tell whether the order changed. It is also possible Save was
never pressed because the "(unsaved order)" marker never appeared.
Untested; the fix route (click-to-move fallback) does not depend on
which link failed.

## Blast radius

One operator, the backlog panel of the operator console only, since
first use 2026-08-14. Effect: backlog prioritization from the console —
a PRD-level capability of the just-shipped run — is unusable in
practice; the workaround is editing `docs/backlog.md` by hand. No data
risk: the worst browser outcome is a no-op or a 409 on stale hash;
claim markers are preserved server-side. Review and Ship scale small.

## Ruled out

- Server-side save path — verified end-to-end at the HTTP layer during
  the process-dashboard run (204 rewrite with markers intact, 409 on
  stale hash, permutation guard; evidence quoted in that run's
  `verification.md` and `release.md`).
- `applyMove` pure reorder logic — node-harness pinned, including the
  +1 index adjustment when moving down.
- `renderBacklog` dirty-state rendering (Save button enable/disable,
  "(unsaved order)" marker) — node-harness pinned against canned
  states.

## Work items

- [ ] **Click-to-move controls** — add ▲/▼ move buttons to each
  unclaimed seed row in `dashboard.html`, wired through `applyMove` and
  the existing dirty/save path; real `<button>` elements so the flow is
  keyboard-usable.
  - Accept: node-harness tests pin that buttons render only on
    unclaimed rows, edge rows are handled (first movable row's ▲ and
    last movable row's ▼ disabled), and the click path produces the
    same order/dirty state `applyMove` gives a drag. Full battery
    green.
- [ ] **Hand-in-browser reorder lands** — with the operator, perform
  one reorder from the page using the new controls and Save it.
  - Accept: `docs/backlog.md` is rewritten — git diff shows the seed
    lines permuted with every origin/claim marker intact — and the
    operator confirms the flow felt usable. Same work order as the
    controls, per the retro's Change entry.

## Notes

Origin seed claimed in `docs/backlog.md`:
"Console backlog drag is finicky in a real browser — add click-to-move
controls and verify one reorder lands from the page
(from: feature:process-dashboard)
(claimed: maintenance:console-drag-ergonomics)".
