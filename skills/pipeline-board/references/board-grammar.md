# Board grammar — geometry, glyphs, model keys, checklist

The board-specific rules only. Every shared visual value — tokens,
typography, theme mechanics, the no-shadow/no-hue discipline — comes
from `../../architecture-diagram/references/design-system.md`, the
family's one owner of the look. This file adds what a swimlane board
needs on top and mirrors the `board.py` output contract the skill
renders verbatim (ADR-0062).

## Geometry — 8px grid, fixed columns

| Region | Values |
|--------|--------|
| Canvas | width 880; margins 24; content 24..856 |
| Header | eyebrow baseline y=34, serif title y=58, subtitle y=76 |
| Label column | x=24..216 (slug + kind sublabel, left-aligned) |
| Stage columns | ten columns of 64 starting x=216; column *i* (0-based) center = `248 + 64·i` |
| Column heads | mono 9 uppercase abbreviations, baseline y=104: Idea PRD UX Arch Dcmp Impl Vrfy Rvw Ship Oper |
| Lane rows | height 56; first band y=112..168; glyph center = band top + 24; slug baseline = top + 28; kind baseline = top + 42; hairline rule at each band bottom |
| Attention strip | only when `attention` is non-empty: heading 24 below last rule, one mono row per entry at 18 spacing, closing hairline |
| Legend | single row, 22 above the bottom edge |
| Height | `112 + 56·runs + (attention ? 24 + 18·entries + 14 : 0) + 56`, rounded up to the 8px grid; adjust `viewBox` and the ground rect together |

## Maintenance column mapping

The maintenance ladder has 8 rungs to the feature ladder's 10. Capture
spans the Idea–PRD–UX columns as one chip (`x=224, width=176, height
20, rx=2`, fill `--chip`, stroke `--rule`, label `CAPTURE ✓` — accent
stroke and label instead when capture is the current stage); architect
onward aligns 1:1 with the remaining seven columns. Never draw a
maintenance glyph in a column its ladder doesn't have.

## Glyph roster — state → mark

| `state` | Mark |
|---------|------|
| `done` | check path `M(cx-9) cy l3.5 4 6.5 -8`, stroke `--muted` 1.4 |
| `current` | filled circle r 5.5, `--accent` — the board's only accent use, with the progress count |
| `current` at implement | accent ring r 5.5 + right-half fill (`M cx (cy-5.5) a5.5 5.5 0 0 1 0 11 Z`) + mono 9 `done/total` in `--accent` centered 16 below |
| `ahead` | dot r 1.5, fill `--ahead` |
| `skipped` | 10px horizontal line, stroke `--skip`, round caps |

## The model, verbatim

`board.py` (two directories above this skill) prints the only facts the
board may state. Keys per run entry: `ref`, `kind`, `slug`, `dir`,
`ladder` (ordered `{stage, state}` rows — render in this order),
`progress` (`{done, total}` or null — non-null only at implement).
Top level: `generated`, `repo`, `runs` (pre-sorted furthest-along
first; never re-sort), `attention` (`{dir, reason}` rows). A nonzero
exit means no board: surface the tool's problem output and stop.

## Empty and edge states

- **No active runs**: header and legend render as normal; the lane area
  carries one centered `.subtitle` line — `No active runs`.
- **Attention entries**: one mono row each — `dir — reason` — under the
  `NEEDS ATTENTION` heading in `--assumed`. Runs in the strip never get
  a lane.
- **Long slugs**: truncate to fit the label column with a trailing `…`;
  the full ref belongs in the `<desc>`.

## Aesthetic checklist — Verify applies item by item

1. One accent: current-stage marks and progress counts are the only
   `--accent` uses; every other mark is ink at an opacity.
2. Editorial type: serif title, mono uppercase eyebrow/column heads,
   sans slugs, mono counts — per the design system's roles.
3. Hairlines at `--rule`, width 1; no shadows, no glows, no
   color-per-kind palette.
4. Coordinates sit on the 8px grid (glyph centers may sit on the 4px
   half-grid); columns at the fixed geometry above.
5. Dark flip: the `@media (prefers-color-scheme: dark)` block overrides
   tokens only, and both themes stay legible.
6. Self-contained and still: no scripts, external fonts, external
   images, or animation; the ground rect paints `--paper`.
7. Legend names every glyph the board uses; the subtitle carries the
   snapshot timestamp; sort-order note present.
8. Deliberate layout: fixed columns, aligned baselines, spans over
   per-cell improvisation — nothing that reads as auto-layout output.
