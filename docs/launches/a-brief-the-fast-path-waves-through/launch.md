---
launch: a-brief-the-fast-path-waves-through
date: 2026-11-03
sources: [docs/fixes/a-brief-the-fast-path-waves-through/defect.md, docs/fixes/a-brief-the-fast-path-waves-through/verification.md, docs/fixes/a-brief-the-fast-path-waves-through/release.md]
video: launch.mp4
---

# Launch: A run's instructions now need a person to approve them

## What it is

Low-risk changes can merge on their own once the checks are green. Until now, that included a change to the one file an unattended run treats as its instructions. This release closes that gap.

## What it does

An edit to a run's brief now always goes to a person for review, wherever the file lives. Edits to the other files in a run still take the quick route.

## How it helps

Nobody can quietly widen what an unattended run is allowed to do by sneaking a change through the automatic merge. The cost is that a change touching only a brief now waits for a human.
