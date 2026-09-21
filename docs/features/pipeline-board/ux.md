---
stage: ux-design
run: feature:pipeline-board
date: 2026-08-25
---

# UX: Pipeline board

## Flows

### Orient (primary — operator)

1. Operator asks for the board (invokes the utility skill in the target
   repo, no arguments needed).
2. The board file is generated from run state at that moment and opened
   (browser/preview).
3. Operator reads the board: one row per active run, current stage
   highlighted. Orientation complete — no commands, no follow-up required.

### Share (secondary — operator → viewer)

1. Operator generates the board as above.
2. Operator sends the file itself (or a screenshot of it).
3. Viewer opens it anywhere — no repo, tooling, or network needed — and
   reads it identically.

Every PRD user story is reachable: stories 1–2 land in Orient step 3,
story 3 in Orient steps 1–2, story 4 in Share.

## Screens

### The board (the only surface)

```
┌──────────────────────────────────────────────────────────────┐
│ Pipeline board                                               │
│ skills · 4 active runs · snapshot 2026-08-25 09:41           │
│──────────────────────────────────────────────────────────────│
│              Idea PRD  UX  Arch Dcmp Impl Vrfy Rvw Ship Oper │
│ one-labels-… [─ Capture ✓ ─] ✓    ✓    ✓    ✓   ✓   ✓   ●  │
│   maintenance                                                │
│ ···························· hairline ······················ │
│ first-live-…  ✓    ✓   ✓   ✓    ✓    ◐    ·   ·   ·    ·  │
│   feature                          1/9                       │
│ marker-diag… [─ Capture ✓ ─] ✓    ✓    ◐    ·   ·   ·    ·  │
│   maintenance                      2/5                       │
│ pipeline-bo…  ✓    ●   ·   ·    ·    ·    ·   ·   ·    ·  │
│   feature                                                    │
│──────────────────────────────────────────────────────────────│
│ ⚠ needs attention (section present only when non-empty)      │
│   some-run — defect.md has no re-entry: field                │
│──────────────────────────────────────────────────────────────│
│ ✓ done · ● current · ◐ in progress n/m · · ahead · — skipped │
│ [─ Capture ─] maintenance entry · sorted furthest-along first│
└──────────────────────────────────────────────────────────────┘
```

Anatomy, top to bottom:

- **Header** — title; repo name, active-run count, and snapshot timestamp
  (the board is a moment in time and says so).
- **Swimlanes** — one row per active run, stages as columns in pipeline
  order. Row label is the run slug with its kind (feature / maintenance /
  product) beneath. Cells: `✓` stage complete, `●` current stage
  (accent color — the board's focal element), `◐` current-with-progress
  (Implement only, checkbox count `n/m` beneath), `·` not yet reached,
  `—` stage skipped by rule (e.g. `ux: not-applicable`, or Arch/Dcmp on a
  `re-entry: implement` maintenance run). Maintenance rows open with a
  single `Capture` cell spanning the Idea–UX columns — those stages do
  not exist for that ladder, and the board never implies they do.
  Rows sorted furthest-along first; hairline rules between rows.
- **Needs-attention strip** — only rendered when some run cannot be
  oriented (malformed frontmatter, contradictory artifacts). Each entry:
  run slug + one-line reason. Unorientable runs appear here and never in
  the lanes — no guessed placement, no silent drop.
- **Footer legend** — glyph meanings, capture-span note, sort order.

- Purpose: answer "which step is each task on?" in one glance.
- Empty state: header + footer render as normal; the lane area reads
  "No active runs" — styled, not an error.
- Loading state: none — the file is a finished snapshot; there is no
  in-surface loading. (Generation-time progress is the harness's concern,
  not this surface's.)
- Error state: per-run failures go to the needs-attention strip (above).
  A repo-level failure (no docs/ tree at all, unreadable filesystem)
  aborts generation with a problem message instead of producing a
  misleading board — matching the "render honestly" rule: render what is
  known, refuse when nothing is.

## Conventions to match

- The diagram-design editorial system the user referenced: warm-paper
  light canonical look, single accent color reserved for current-stage
  markers (the 1–2 focal elements), 1px hairline rules, editorial type
  hierarchy (serif display title, sans body, mono for slugs/counts),
  deliberate grid-aligned layout — visibly not default-mermaid output.
- Dark variant via `prefers-color-scheme`, mirroring the sibling
  architecture-diagram skill's theme convention.
- Self-contained single file, no external requests (PRD success
  criterion; also the sibling diagram skills' rule).
- Stage names and run-kind vocabulary come from the pipeline protocol —
  the board uses the protocol's terms (Idea…Operate, Capture, feature /
  maintenance / product), never invented ones.

## Deliberately not designed

- Interactivity of any kind (hover, click-to-inspect, presenter mode) —
  PRD out of scope.
- Motion/animation — still figure only.
- Staleness indicators and next-stage hints on rows — offered at
  interview, declined for v1; the row carries slug, kind, and Implement
  progress only.
- Column compression for long pipelines on narrow viewports — the board
  targets a comfortable landscape figure; responsive reflow is deferred
  polish.
- Print styling.
