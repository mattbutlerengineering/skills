---
launch: pipeline-board
date: 2026-10-08
sources: [docs/features/pipeline-board/prd.md, docs/features/pipeline-board/verification.md, docs/features/pipeline-board/release.md]
video: launch.mp4
---

# Launch: The pipeline board

## What it is

The pipeline board is a one-page picture of every piece of work in flight
and the step each one has reached. It is drawn on demand from the notes
each run leaves behind, so there is nothing to keep up to date. You open
it when you want to get your bearings without running anything.

## What it does

You ask for the board and a small tool reads every run's notes to state
which step each one is on. It lists every active run once, tells feature
work from maintenance work, and shows how far along the building step has
come. The picture is a single file with no outside dependencies, so it
opens anywhere and can be sent as it is.

## How it helps

Instead of walking folders and running commands, you find where every run
stands in one glance. Anyone you share it with can read it with no
repository and no tools installed. The board never changes a run; it only
shows where things stand.
