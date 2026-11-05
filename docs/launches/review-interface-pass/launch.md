---
launch: review-interface-pass
date: 2026-11-04
sources: [docs/features/review-interface-pass/prd.md, docs/features/review-interface-pass/verification.md]
video: launch.mp4
---

# Launch: Code review now checks what an interface change took away

## What it is

Code review now has an extra look for changes to screens and styles. It reads the lines a change deleted, not just the lines it left behind. It runs on its own whenever a change touches interface files.

## What it does

When a change removes a spoken label, a focus outline or a motion preference, the review reports it. When the same change puts an equivalent back in the same place, the review stays quiet. Each finding says whether the change introduced the problem, broke something that worked, or found one that was already there.

## How it helps

A lost label or focus ring is invisible in the finished code, so it used to ship unseen. Now it is caught while the change is still a draft. Changes with no interface files are never slowed down by it.
