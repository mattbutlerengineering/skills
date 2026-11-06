---
stage: ux-design
run: feature:assembly-line
date: 2026-11-05
---

# UX: An animated assembly line of every run in the repo, with a history replay

Terms: a **station** is one pipeline stage's tile and machine; a **crate**
is one run; a **part** is one work order (breakdown row); the **floor** is
the whole factory view; the **transport bar** is the replay controls; the
**hover card** and **pinned panel** are the two detail surfaces.

## Scenario walkthroughs

### 1. The 75-crate pile

- Actor and goal: Presenter, explaining why 75 runs sit at Operate.
- Steps: hover the Operate station → hover card: "Operate: shipped,
  waiting on a retro", count 75, the 5 oldest runs → click the station →
  pinned panel lists all 75, oldest first → click one run → its crate
  lifts and outlines on the pallet stack.
- Result: completes.

### 2. The cold watch

- Actor and goal: Cold viewer, with no narration, naming the stages and
  the busiest station within 30 seconds.
- Steps: the page opens on today: every station tile carries its stage
  name on its floor plate, the belt runs in reading order (left to right,
  then right to left, then left to right) and the tallest pallet stack
  carries the largest count tag → Presenter (or the viewer) presses play
  → crates flow along the single belt in order and stacks rise where work
  waits.
- Result: completes; whether it is enough is the PRD's cold-viewer test.

### 3. The messy repo

- Actor and goal: Repo owner in mattbutlerengineering, trusting the floor.
- Steps: run the skill → the floor shows the phantom product run as a
  crate at Idea, its hover card reading "product · docs/ · at Idea ·
  already has: Architect", so the owner can see why it is there → a run the placement
  tool cannot orient appears in the Needs-attention bin at the floor's
  edge with its reason on hover, never on a station.
- Result: completes for display. Whether the phantom run should exist at
  all is recorded under Dependencies surfaced for Architect.

### 4. Empty or brand-new repo

- Actor and goal: Repo owner in a repo with no runs, or only completed
  ones.
- Steps: run the skill → no runs: belts and machines idle-animate, every
  station shows count 0, a centred floor sign reads "No runs yet — start
  one with /idea", transport bar disabled → only completed: the
  warehouse shelves hold every run, every station is 0, play replays
  them all the way to the shelves.
- Result: completes.

### 5. Scrub, then hover

- Actor and goal: Presenter, showing what a station held on a past date.
- Steps: press play → pause → drag the scrubber to 2026-09-01 → the
  floor shows every crate where it stood at the end of that day, the header reads
  "as of 2026-09-01" → hover a station → the hover card's count and runs
  are those of 2026-09-01 → click → pinned panel titled "Implement · as
  of 2026-09-01", whose work-order rows read "progress as of today"
  (no record says which boxes were ticked on 2026-09-01).
- Result: completes.

### 6. README to the interactive page

- Actor and goal: Adopter, from the README to the live factory.
- Steps: the README shows the exported looping clip of the replay →
  click it → the link opens the interactive floor.
- Result: completes for the flow; where the linked page lives is open
  (PRD Open questions, Architect).

### 7. A maintenance run skips stages

- Actor and goal: Repo owner watching a maintenance run, and a feature
  run whose PRD skipped UX.
- Steps: the maintenance crate is born at Capture, rides its side belt
  and joins the main belt at Architect (`re-entry: architect`) or at
  Implement (`re-entry: implement`) → a crate passing a skipped station
  rides straight through: the machine does not touch it and the hover
  card for that crate lists the stage as skipped.
- Result: completes.

### 8. A huge breakdown

- Actor and goal: Presenter, showing a run with 30 work orders.
- Steps: at Implement every crate carries a small parts tray whose fill
  shows done out of total → hover the crate: "12 / 30 work orders" →
  click the crate → its tray expands into all 30 parts, finished ones
  green, open ones grey, and the pinned panel lists every work order with
  its state.
- Result: completes; parts are all shown on demand, not all at once.

## Code facts

- Placement — `board.py`: emits `runs` (each with `ref`, `kind`, `slug`,
  `dir`, `ladder` of stage/state, `progress`) and `attention` (a `dir`
  and a `reason` for each run it cannot orient). A run is in exactly one
  of the two.
- `board.py` drops completed runs entirely (`gather` skips a ladder that
  is all done, and `active_runs` never yields a run with a complete
  retro). The Completed warehouse needs them.
- `board.py` reports `progress` as counts only (`done`, `total`), and
  only when the current stage is implement. The expanded tray and panel
  need each work order's name and state.
- `board.py` reports no dates. The replay needs each artifact's `date:`.
- `board.py` names the product run after the repo directory (`slug` is
  `root.resolve().name`), and treats any `docs/` root holding a stage
  artifact as the product run; in mattbutlerengineering a plain
  `docs/architecture.md` makes one at Idea.
- `board.py` exits nonzero with `board: <root> has no docs/ tree` when
  there is no `docs/`; the pipeline-board skill then draws nothing.
- The pipeline-board skill (`skills/pipeline-board/SKILL.md`) writes its
  output outside the repo's tracked tree and never commits it.

## Flows

### Primary: present the factory

1. Repo owner invokes the skill in a repo.
2. The floor opens on today: stations, crates, stacks and the warehouse,
   all idle-animating.
3. Presenter hovers stations and crates to explain; clicks to pin detail.
4. Presenter presses play; the replay runs from the first artifact date to
   today in 30 s (or 60 s), then settles on today.
5. Presenter pauses and scrubs to a date to point at a moment.

### Export the adopter clip

1. Repo owner asks the skill for the clip.
2. The skill writes a looping animated image of the replay and names the
   link target for the interactive floor.
3. Repo owner commits the clip and references it from the README.

## Screens

### The floor

```
┌ skills · 90 active · 16 completed · as of 2026-11-05 ──────────────┐
│                                                       ┌ Operate ─┐ │
│  [Capture]╮                                           │ 75 runs  │ │
│  [Idea]═▶[PRD]═▶[UX]═▶[Architect]                     │ oldest ▾ │ │
│                            ║                          │ • slug-a │ │
│  [Verify]◀═[Implement]◀═[Decompose]                   │ • slug-b │ │
│     ║        ▣▣▣ 15                                   │   …      │ │
│  [Review]═▶[Ship]═▶[Operate]═▶[Completed]             └──────────┘ │
│                    ▣▣▣ 75 ⬆     ▤▤ 16                              │
│  ⚠ Needs attention: 0                                              │
├────────────────────────────────────────────────────────────────────┤
│ ▶  ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━○ 2026-07-01 → today  30s|60s│
│    dates to the day from artifact frontmatter; order within a day  │
│    is inferred                                                     │
└────────────────────────────────────────────────────────────────────┘
```

- Isometric tiles in the Owner's reference style (idea.md, Look): one
  floor plate per station, its stage name painted on the plate, one
  continuous belt in pipeline order. Capture sits beside Idea and feeds
  the main belt at Architect or Implement through a side belt.
- Every station animates continuously (belt rollers, its machine's
  motion), crates or not.
- A station queues up to 6 crates on the belt in front of its machine;
  more stack on pallets beside the tile, and a floating count tag shows
  the exact number. The busiest station is the tallest stack.
- Machines: Capture, a repair bench where a worker opens a returned
  crate; Idea, an intake dock where a worker builds a new crate; PRD, a
  label printer stamping a spec sheet on the crate; UX, a design bench
  with a worker sketching on a tablet; Architect, a gantry crane lowering
  a blueprint frame; Decompose, an arm opening the crate into parts;
  Implement, twin robot arms assembling the parts; Verify, a tunnel
  scanner whose light turns green; Review, an inspector with a tablet
  stamping approval; Ship, packing and a forklift loading a cart;
  Operate, an outbound dock of delivered carts waiting on a retro;
  Completed, warehouse shelving that fills.
- Header: repo name, active count, completed count, "as of <date>"
  (today, or the scrubbed date).
- Needs-attention bin at the floor's edge with its count; empty bin when
  zero.
- Purpose: see all the work and where it waits.
- Empty state: walkthrough 4.
- Loading state: the floor plate outlines draw first, then machines and
  crates; the transport bar stays disabled until the replay timeline is
  ready.
- Error state: if the browser cannot draw the floor, the page says so in
  one line and shows the same facts as a plain list per station, so the
  work is still all visible. If the repo has no `docs/` tree, the skill
  stops with the placement tool's message and writes no page, as
  pipeline-board does.

### Hover card

```
┌ OPERATE ─────────────────────────────┐
│ Shipped, waiting on a retro          │
│ 75 runs · as of 2026-11-05           │
│ oldest: slug-a, slug-b, slug-c, …    │
└──────────────────────────────────────┘
┌ crate: maintenance:some-slug ────────┐
│ maintenance · at Implement · 2/3 WOs │
│ skipped: Architect, Decompose        │
└──────────────────────────────────────┘
```

- Station card: stage name, one line on what it does, count as of the
  floor's date, the 5 oldest runs. Crate card: run ref, kind, current
  stage, skipped stages, stages already done ahead of the current one
  ("already has: …", the ladder's gap), and work orders done/total at
  Implement; attention crates show their reason instead.
- Purpose: name and explain whatever is under the cursor.
- Empty state: a station with nothing in it shows its line and "0 runs".
- Loading/Error: none of their own; the card reads what the floor holds.

### Pinned panel

```
┌ Implement · as of 2026-09-01 ─── ✕ ┐
│ 15 runs, oldest first              │
│ ▸ feature:some-slug      12/30 ·today│
│   ☑ WO title …                     │
│   ☐ WO title …                     │
│ ▸ maintenance:other-slug  0/3 ·today│
└────────────────────────────────────┘
```

- Opens on clicking a station or crate; lists every run in that station
  (expanding a run lists its work orders and their state). Clicking a run
  lifts and outlines its crate. Esc, ✕ or clicking empty floor closes it.
- Purpose: the complete list behind any count.
- Empty state: "No runs here as of <date>".
- Loading/Error: none of their own.

### Transport bar

- Play/pause, a scrubber from the first artifact date to today, the date
  readout, a 30 s / 60 s speed toggle, and the honesty line ("dates to
  the day from artifact frontmatter; order within a day is inferred;
  work-order progress is today's").
- Scrubbing or pausing moves the floor and every detail surface to that
  date; reaching the end settles on today.
- Replay timing: the day is the tick, and the scrubber snaps to days. A
  scrubbed date shows end-of-day state. Within a played day, a run's
  transitions that day are spread evenly in stage order, so a crate whose
  every artifact shares one date still rides each station in turn rather
  than jumping. While a crate is moving on inferred order it carries a
  dashed shadow, which clears when the day closes.
- Work-order progress has no dates (checkbox ticks are undated), so
  during a replay Implement trays show their part count with a neutral
  fill; the done/total fill appears only on today.
- Empty state: disabled when there are no runs.

## Conventions to match

- The diagram family's honesty rules: one self-contained file, no
  external requests (`skills/animated-diagram/SKILL.md`,
  `skills/pipeline-board/SKILL.md`).
- Reduced motion, as the animated-diagram skill checks it: under
  `prefers-reduced-motion: reduce` the floor opens still, idle animation
  stays off, and the replay advances only when played.
- Placement is the placement tool's, rendered verbatim, never re-derived
  (pipeline-board).
- Deliberate departure: the family's theme-aware palette is replaced by
  the Owner's reference palette (green, grey, purple on a pale ground).

## Dependencies surfaced for Architect

- Completed runs, per-work-order names and states, and per-artifact
  dates are not in `board.py`'s output; the floor needs all three while
  placement keeps one owner.
- The phantom product run in repos whose `docs/` root holds ordinary
  project docs (mattbutlerengineering): show it as-is, or teach the
  placement tool to tell the two apart (PRD Open questions).
- The adopter clip must be committed, while pipeline-board's convention
  is to write outside the tracked tree; the clip's path and the linked
  page's home are open (PRD Open questions).
- The no-drawing fallback (plain list per station) needs the browser
  capability check the renderer choice implies.

## Deliberately not designed

- Sound, camera orbit and zoom: a fixed isometric view.
- Mobile layout: the floor is designed for a laptop or a shared screen.
- Search or filtering in the pinned panel.
- Any action on a run from the page (PRD Out of scope).
- A replay position for Needs-attention runs: they have no orientable
  stage history, so they sit in the bin for the whole replay.

## Review

- Review: independent (fresh reviewer subagent, given idea.md, prd.md,
  ux.md and the code-fact paths; reported 4 High, 0 Critical, and
  confirmed every code fact).
- H1, the pinned panel showed work-order ticks as of a past date that no
  record holds — fixed: walkthrough 5 and the panel read "progress as of
  today", trays show a neutral fill during replay, and the honesty line
  says work-order progress is today's.
- H2, no motion rule for same-day runs, the PRD's open question to UX —
  fixed: Replay timing rule under Transport bar (day tick, end-of-day
  scrub state, even spread in stage order, dashed shadow while inferred).
- H3, a `fix:` ref the placement tool never produces — fixed: walkthrough
  7 and the sketches say `maintenance:`.
- H4, the ladder's done-ahead gap was not shown, so walkthrough 3 could
  not explain the phantom run — fixed: the crate card lists "already
  has: …" and walkthrough 3 quotes it.
- Below High, also fixed: the floor's attention label now matches the
  bin's name, and attention runs' replay position is recorded above.
- Re-walked all eight walkthroughs after the fixes using only controls
  defined here; each completes as recorded.
