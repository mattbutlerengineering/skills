---
launch: polish-blockers-and-patterns
date: 2026-11-04
sources: [docs/features/polish-blockers-and-patterns/prd.md, docs/features/polish-blockers-and-patterns/verification.md]
video: launch.mp4
---

# Launch: Polish names what locks people out

## What it is

The polish skill now keeps a named list of the flaws that lock people out of an interface. It also carries a table of code patterns to search for when nothing can be shown on a screen. Both are short, and both sit inside the skill's existing steps.

## What it does

The named flaws, such as a destructive action with no undo or meaning carried by color alone, count as high severity the moment they are seen. The pattern table lists a dozen things to look for in code, each in plain terms that fit any framework. Each accessibility row names the web accessibility criterion it breaks.

## How it helps

A review of a screen is ranked by who is locked out, and now there is a named list to rank against. When the screen cannot be run, the review still has something concrete to look for in the code. A small test keeps the list and the table from quietly shrinking.
