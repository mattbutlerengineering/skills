---
stage: operate
run: product | feature:<slug>
date: YYYY-MM-DD
users-observed: <N — 0 is a valid count>
signal-source: <where the count comes from: analytics, support inbox, your own usage, none>
---

# Retro: <title>

## Outcomes vs. intent

### <Success criterion / intended outcome>

- What happened: <observed outcome — with no one observed, the state it is in, never that it landed>
- Signal strength: <anecdote | pattern | measured | unobserved>

## Open debt

Issues this run itself filed — Review deferrals, Verify carry-forwards —
are the run's debt, never feedback (the protocol's "The Operate
population" section says which issues are the run's own).

- <#N — what it defers, and from which stage>

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
