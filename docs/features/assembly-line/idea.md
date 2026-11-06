---
stage: idea
run: feature:assembly-line
date: 2026-11-05
origin: "Owner's /idea request on 2026-11-05, interviewed live. Not a backlog seed: no matching line is claimed."
assumptions:
  - "In-flight check ran, nothing matches. `git branch -a --no-merged origin/main` and `git worktree list` were read; branches touching the surface by name (board, console, dashboard, visual, animat, live) were opened. feature/pipeline-board and feature/pipeline-board-v2 are the shipped pipeline-board runs. feat/live-console-idea carries an unmerged live-console run, Decompose done, whose headline is decisions waiting on the operator, read from session hooks: no stage view, no animation. No branch carries an assembly-line or animated-stage run."
  - "Adjacent shipped work, recorded rather than treated as a match: the pipeline-board skill (board.py states placement; the skill renders a static swimlane SVG of active runs, no hover, completed runs omitted) and the process-dashboard console (dashboard.py serve: runs, gate queues, spend, drift, as tables). The animated-diagram skill owns the family's motion style for hand-authored diagrams, not live repo data."
  - "Outside corroboration (the optional last30days check) was not offered: the evidence question was answered by the Owner's own use, which outside evidence cannot corroborate."
  - "Ambition ladder asked as one question (feature-run form). Owner picked Showstopper. The four tests were run silently and all pass, with the timing caveat recorded under Achievable."
---

# Idea: An animated assembly line of every run in the repo, with a history replay

> I want to be able to visualize all of the work in each step. 2d modules diagram each module looks like a mchine animated assembly line. I want it to look like an animated assembly like. I should be able to hover over each step and see what is being done in that step. All work should be visible on this visualization. completed work should also be it's own bucket.

## Problem

The pipeline is a factory, but no view of it looks like one or lets you
point at a step. Three things are missing at once:

- **Where work piles up.** A static swimlane does not read as a queue, so
  bottlenecks and parked work are invisible. On 2026-11-05, `board.py` in
  this repo listed 87 active runs: 71 parked at Operate (shipped, no
  retro), 15 at Implement, 1 at Idea. Nothing makes that pile show.
- **What a step is doing.** The board says a run sits at a stage, not what
  happens there: which work orders are in flight inside Implement, what
  the stage produces.
- **Output.** Completed runs disappear from the board, so the factory
  never shows what it has produced. Completed work needs its own bucket.

## Who has it

- **The Owner, as presenter.** Matt shows the factory to others, live on a
  screen-share or in a meeting, and today narrates over a static SVG or a
  terminal. He also wants it in his other repos (mattbutlerengineering is
  the named one) to see the work there.
- **Prospective adopters.** Developers deciding whether to install the
  plugin, seeing it on a README or a launch post with nobody there to
  narrate. Today they get a static board and prose.
- **Consumer-repo owners.** Anyone using the plugin runs the skill in their
  own repo and sees that repo's line. It ships as a vended skill, not a
  one-off picture of this repo.

## Why now

To show the factory to others. The Owner wants to vend the skill, and the
existing visual is not something he would show: a viewer who has never
seen the factory has to get it from the picture.

## Evidence

- **Anecdote (the Owner, 2026-11-05):** "I don't use it because it's not
  good enough." The pipeline-board skill shipped and its own author does
  not reach for it. This is the strongest evidence and it is one person.
- **Measured (this repo, 2026-11-05):** 100 run directories under
  `docs/features/` and `docs/fixes/`; `board.py` reports 87 active, 71 of
  them at Operate. A list of that length is a scroll, not a glance.
- **Repo signal, not viewer evidence:** the repo already invested in
  visuals aimed at this audience (readme-skill-map, pipeline-board,
  animated-diagram, launch-demo). No viewer feedback on any of them is
  recorded.

## Ambition rung

Chosen: Showstopper, in the user's words: "I want it to look like an animated assembly like" — and press play to watch the repo's history run down the line
Not taken: Solid: an animated snapshot of the line as it stands now, with hover and a Completed bucket and no replay; Moonshot: a live floor across every repo you own, parts moving in real time as agents work, hosted and viewable on a phone — seeded to docs/backlog.md
Demo: pass — press play and about 100 runs flow machine to machine over months of history in about 30 seconds while the Completed bucket fills
Removes a step: pass — the presenter no longer narrates the stages, and a consumer repo needs no setup: the line is read from artifacts already there
Only this product: pass — every run artifact carries a dated frontmatter line (523 of 523 in this repo), so the stage history is already recorded by the pipeline itself
Achievable: pass — riskiest piece is a truthful replay timeline under squash merges plus smooth motion for about 100 parts in one self-contained file; two-day spike below

## The demo

Before: a static swimlane of 87 rows that its author does not use, and a
presenter explaining what each column means. After: one machine per stage
on a belt; press play and the repo's runs enter, move station to station
as each stage's artifact lands, pile up where work actually waited, and
drop into the Completed bucket; hover any machine to see what that step
does and which items are in it.

## Riskiest piece + spike

**Timeline truth.** Git cannot time the stages: on `origin/main`, 82 of
99 runs landed every artifact in one squash commit, so a commit-time
replay would jump most runs from Idea to the end. Frontmatter `date:`
fields time every artifact, but only to the day, and only 21 runs span
more than one day; order within a day has to come from stage order, which
is inferred, not observed.

Spike (about two days): build the replay timeline for this repo's 100
runs from frontmatter dates (git only as a fallback), render it with
about 100 moving parts in one self-contained file, and check two things:
that motion stays smooth at that part count, and that day-resolution
history still reads as work flowing and piling up rather than everything
teleporting together. Run it once in mattbutlerengineering to confirm
it needs no setup there.

## Cheapest kill test

Render that throwaway replay of this repo and show it cold to one person
who has never seen the factory. If, after 30 seconds, they cannot say
what the stages are and where work piles up, or the Owner still would
not choose it over the old board to present, the idea is dead in this
form.

## Solution hunch

A hunch, not a design: a vended utility skill, like pipeline-board,
that reads the same run facts (`board.py` already owns placement) plus
each artifact's date, and renders one self-contained file.

- Stations: Idea → PRD → UX Design → Architect → Decompose → Implement →
  Verify → Review → Ship → Operate → Completed. Maintenance runs enter at
  a Capture station.
- Parts: one per run. Inside the Implement machine, that run's breakdown
  rows are smaller parts, open or finished.
- Hover: a machine shows what the stage does and what is in it; a part
  shows the run, its current artifact and its work-order progress.
- Completed: runs whose retro carries its population line, piled in their
  own bucket.
- Replay: play and scrub over the dated history; the snapshot is the last
  frame.

**Look (Owner, 2026-11-05):** "i want the visualization to look something
like this but animated. award winning. incredible. impressive. exciting.
easy to understand." The Owner supplied three stock illustrations as the
target; they are watermarked or licensed images, so they are described
here and not committed:

- Flat isometric vector line art: a true isometric (orthographic) view,
  thin dark outlines, flat fills with three tones per box (light top,
  mid and dark sides), no gradients or textures.
- A small palette on a pale pastel ground: lime-green belt surfaces and
  shelf tops, cool greys for machines and frames, purple for workers and
  accents.
- Vocabulary: roller conveyors with legs and visible rollers, belts that
  turn corners, tunnel scanners, gantry and articulated robot arms,
  workbenches, workers in hard hats, cardboard crates, pallets, shelving,
  forklifts and small delivery carts.
- Modular: one reference is a grid of nine self-contained isometric
  tiles, each a different station on its own floor plate. That maps
  directly onto one tile per pipeline stage, joined by belts.

Hunch at the metaphor (for PRD and UX to test, not settled): a crate per
run; Decompose as an arm that opens a crate into small parts, one per
work order; Implement as robot arms working those parts; Verify as the
tunnel scanner; Review as a worker inspecting with a tablet; Ship as
carts carrying finished crates out; Completed as the shelving and
pallets, filling up as runs finish.

Hunch at the renderer: three.js with an orthographic isometric camera
gives that exact projection, with flat per-face colours and edge lines
for the outlined look and hover via picking. The machines are built
from code, not imported models. The scene is a fixed template the skill
fills with data, never redrawn by the model each run, so every repo gets
the same factory. three.js v0.187.0 is MIT and about 814 KB minified,
bundled into the file so it needs no network.

## Success in one sentence

In this repo and in mattbutlerengineering, one skill invocation with no
setup draws a line that has every run and work order on it exactly once,
the Owner picks it over the old board to show the factory, and someone
who has never seen the factory can name the stages and where work piles
up within 30 seconds of watching the replay.

## Unknowns & risks

- **Replay honesty.** Intra-day order is inferred from stage order; a
  replay that looks precise but isn't misleads viewers. The view must say
  what is observed (the day) and what is inferred (order within it).
- **README embed.** A README cannot run scripts or WebGL, so a three.js
  line never plays there; adopters would see a recorded clip of the
  replay. Whether that is enough, or a plain animated SVG is also needed,
  is open.
- **First bundled third-party code.** Shipping three.js in the plugin is
  a new precedent beside ADR-0008 (self-contained skills) and the
  diagram skills' no-external-requests check; it needs its own ADR.
- **The bar is taste.** "Award winning, incredible, impressive" is not
  checkable as written; PRD has to turn it into tests a render can pass
  or fail, beside the 30-second cold-viewer test.
- **Scale.** A repo with hundreds of runs, or 71 parts parked at one
  station, could turn the line into clutter; the pile has to read as a
  pile, not a smear.
- **What counts as Completed.** The protocol's complete run (retro with
  population line) leaves 71 shipped runs here at Operate. Showing them
  truthfully may make the factory look stuck to a viewer, which could
  hurt the demo; relabelling them would be untrue.
- **It becomes a toy.** Animation that delights once and tells the Owner
  nothing on the second viewing fails the "I'd use it" half of success.
- **Overlap with pipeline-board.** Two skills that place runs on stages
  is a second owner of the same picture; whether this replaces the board
  or sits beside it is open, and `board.py` must stay the one owner of
  placement either way.
