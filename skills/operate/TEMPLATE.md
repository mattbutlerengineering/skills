---
stage: operate
run: product | feature:<slug>
date: YYYY-MM-DD
---

# Retro: <title>

## Outcomes vs. intent

### <Success criterion / intended outcome>

- What happened: <observed outcome>
- Signal strength: <anecdote | pattern | measured>

## Run retrospective

- Keep: <what worked>
- Change: <what to do differently>
- Stop: <what wasn't worth it>

## Environment

One row per mistake the run recorded, naming what in the environment
would have caught it; a retro without this section reads as no
environment findings, not as a defect.

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| <what went wrong> | <artifact and heading or line, e.g. `verification.md` §Criterion 2> | <mechanical or judgement> | <an existing lint checker, gates detector, hook, CI job, `CLAUDE.md` line or `docs/standards.json` statement> |

## Idea seeds

- <One-line seed for a future run>

## Run complete

<Date closed. Seeds above are the input to the next Idea-stage run.>
