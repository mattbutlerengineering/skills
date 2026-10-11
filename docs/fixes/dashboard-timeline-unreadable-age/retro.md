---
stage: operate
run: maintenance:dashboard-timeline-unreadable-age
date: 2026-10-11
assumptions:
  - "Written the same day as the release, against the let-it-breathe step, at the owner's choice ('Close out the batch'). The live dashboard has no queued gate item today, so no usage signal exists to wait for. Outcomes below are what was measured at release, labelled as such."
  - "Outcomes are measured against defect.md's work-item Accept lines, because a maintenance run has no prd.md."
---

# Retro: an unreadable timeline is not an unknown age

## Outcomes vs. intent

### The queue entry says whether its timeline was read

- What happened: `_timeline` returns `None` on a failed or unparseable fetch, and every queue entry carries `aged`. The red-first tests failed on the unfixed code and pass on main (`verification.md`).
- Signal strength: measured (tests).

### The page marks an unreadable age

- What happened: `renderNeedsYou` appends "age unknown (timeline unreadable)" when `aged` is false, and the node render harness pins it.
- Signal strength: measured (tests). It has not been observed live: `dashboard.py gather .` on main returns no queued items today (`release.md`, Post-release).

### Real-world effect

- What happened: none observable yet. The next time a timeline fetch fails while an item waits at a gate, the operator sees "unreadable" instead of a blank age.
- Signal strength: none yet.

## Run retrospective

- Keep: **the Conductor-style batch.** One Worker per item, a reviewer that did not write it, a fixer, then a pairwise merge test before either PR merged. Two items went from issue to main in one sitting with no conflict, and each independent review found something the author missed.
- Keep: **the coordinator alone writes shared files.** Only the retro-carriers Worker touched `docs/backlog.md`, so the batch's two branches shared no file and the merge test was trivially clean.
- Change: **the build brief should say where a reproduction script lives.** The Worker quoted output from a scratchpad script that never reached the branch, and the reviewer caught it (`review.md`, first minor).
- Stop: nothing.

## Environment

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| Run artifacts quoted output from a script that was not in the tree | `review.md` §"the reproduction cites an uncommitted script" | mechanical | gates detector I already checks markdown links against the tree. Extending it to a `python3 <path>` command quoted in a run artifact, whose path exists nowhere in the tree, would catch it |
| A new test asserted the `aged` flag but not its problem strings | `review.md` §"the unparseable-timeline test does not pin its problem strings" | judgement | `skills/implement/SKILL.md` already says to assert observable outcomes; the independent review is the carrier that caught it, so no new rule |

## Idea seeds

Appended to `docs/backlog.md`:

- Detector I does not check script paths that run artifacts quote in commands

## Run complete

Closed 2026-10-11. Released as `669e0fe` (#667). The seed above is the input to the next run.
