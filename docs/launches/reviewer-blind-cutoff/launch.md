---
launch: reviewer-blind-cutoff
date: 2026-11-04
sources: [docs/features/reviewer-blind-cutoff/prd.md, docs/features/reviewer-blind-cutoff/verification.md]
video: launch.mp4
---

# Launch: The reviewer scores blind, and the score is shown

## What it is

The automatic reviewer that can approve pull requests for merging is no longer told where the passing line sits. It gives a score out of ten, and the queue decides pass or flag from that score alone.

## What it does

The passing line now lives in one small tool, and the reviewer's prompt never mentions it. A score at or above the line passes, a lower one flags, and a score that is missing or makes no sense is treated as an error that never merges. Every verdict comment now opens with the score and the result, so anyone can read how each pull request was judged.

## How it helps

A reviewer that cannot see the line cannot quietly score to it. Because every score is now posted, the Owner can later check whether scores bunch up at the line, which was impossible before.
