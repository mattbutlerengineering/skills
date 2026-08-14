---
stage: review
run: maintenance:console-drag-ergonomics
date: 2026-08-14
---

# Review: console-drag-ergonomics

Scope reviewed: the run's whole diff — `dashboard.html` (+28 lines),
`tests/test_dashboard.py` (+41), the run artifacts. Blast radius is one
operator's console panel, so this is a right-sized pass, not a board.

## Findings

1. **Minor, deferred — move buttons carry no accessible label.** The
   ▲/▼ buttons are real `<button>` elements (focusable, Enter/Space
   activate) but expose only the glyph as their name; a screen reader
   announces "black up-pointing triangle". An `aria-label="move up"`
   pair would fix it. Deferred: folded into the polish seed the retro
   records — the console has exactly one operator today and the glyphs
   are visually self-evident.
2. **Minor, deferred — repaint drops focus after each click.** Every
   move re-renders the whole backlog panel via `innerHTML`, so keyboard
   focus resets to the document; a keyboard user must Tab back to the
   row after each nudge. "Keyboard-usable" is therefore literal but
   tedious beyond one move. Same deferral, same seed — restoring focus
   to the moved row's button after `paint()` is the obvious shape.
3. **No blockers.** `nudge` guards the `indexOf === -1` case (without
   it, an unknown line plus `delta: 1` would silently move the first
   seed); the pinned tests cover both edges and the claimed-row
   exclusion; the wiring reuses the existing delegated listener rather
   than adding per-row handlers.

## Verdict

Ready to ship. Both findings are ergonomic residue on a fix that is
itself ergonomic residue — they belong in the next round's seed, not in
this run's scope.
