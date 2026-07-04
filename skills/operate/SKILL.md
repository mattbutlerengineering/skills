---
name: operate
description: Use when shipped work has been in users' hands and it's time to capture feedback and run a retrospective — closing the loop into the next idea or the next fix. Defects and degradations observed here are first-class retro seeds; recurring ones become preventive work. Produces retro.md, completing the run.
---

# Operate

Close the loop: gather what actually happened after shipping, compare it to
what the run intended, and turn the difference into the next run's input.
Scoped to feedback capture and retrospective — not monitoring infrastructure.

## Process

1. Read `../../docs/pipeline-protocol.md` for run discovery, gating, and
   frontmatter conventions.

2. **Soft gate.** Predecessor artifact: `release.md`. If missing, apply soft
   gating.

3. **Let it breathe.** If the release just happened, say so and offer to
   return once there's real usage to reflect on — a retro written an hour
   after shipping reflects hopes, not outcomes.

4. **Capture outcomes.** Against `prd.md`'s success criteria and `idea.md`'s
   success-in-one-sentence — or, in a maintenance run, against `defect.md`:
   is the defect gone, did the blast radius quiet down? What actually
   happened? Gather whatever signal exists — user feedback, your own usage,
   error reports, the absence of complaints. Label the strength of each
   signal honestly (anecdote vs. pattern).

5. **Retrospect on the run itself.** Walk the stages: where did the pipeline
   help, where did it drag, which artifact earned its keep, which stage got
   skipped or backfilled and was that right? Keep / change / stop — a few
   sharp entries beat an exhaustive ceremony.

6. **Seed the next runs.** Every gap, complaint, and "next time" becomes a
   one-line idea seed — the natural input to the next Idea-stage run.
   Defects and degradations are first-class seeds too: a fresh defect
   seeds a capture (a new maintenance run), and a defect class that keeps
   recurring seeds preventive work — a refactor brief or a feature run —
   not another one-off fix.

7. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)
   into the run directory as `retro.md` with protocol frontmatter. This
   completes the run.

## Rules

- Outcomes over activity: "we shipped it" is not an outcome; "it gets used
  for X" or "nobody used it" is.
- The retro judges the process and the bet, not the people.
- Don't skip seeding: a retro that produces no next-idea seeds usually means
  the outcome questions weren't really answered.
