---
launch: svg-mechanical-check
date: 2026-11-04
sources: [docs/features/svg-mechanical-check/prd.md, docs/features/svg-mechanical-check/verification.md]
video: launch.mp4
---

# Launch: A mechanical check for the diagrams you generate

## What it is

This is a small checker for the picture files that the two diagram skills produce. It reads the file the way a browser would, without running anything in it. It refuses files that try to pull in outside content.

## What it does

It names every broken link, repeated name and missing size it finds in the picture. When the picture is clean, it says so and reports the smallest text size at the width the picture will have on a page. It also refuses a file that could be used to trick the reader, and says why.

## How it helps

Mistakes that used to be found later by someone squinting at a rendered page are now caught in a second, before the diagram is handed over. The starting templates pass the check, so a new diagram begins correct.
