---
stage: capture
run: maintenance:idea-keeps-the-coined-phrase
date: 2026-10-25
re-entry: implement
intake: #1118
---

# Defect: Idea briefs paraphrase away the pitch's coined phrase

## Defect (or Condition)

The `ladder-brief` case seeds a pitch that coins "self-healing shift rota".
No brief written with the plugin kept it: `keeps-users-words` failed 3 of 3
in the first paid run (`plugin-evals/records/2026-10-26.json`). Expected:
the user's own name for the idea survives into the brief.

## Reproduction / Evidence

- Three single-arm runs, 0 of 9 briefs kept the phrase: the first paid run,
  a re-run with a rule added to Rules (reverted in #1119), and a
  `--keep-temp` run on main ($1.51).
- The kept briefs show the cause. Every section is filled from the
  interview answers ("rebuilding the rota by hand"), and the pitch is never
  quoted. `TEMPLATE.md` has no place for the user's own framing of the
  idea; its only quote slot is the rung's sentence.

## Root-cause hypothesis

Confirmed by the kept briefs, not a guess: the template gives the pitch's
framing nowhere to go, so sharpening the Problem section from the answers
drops it.

## Blast radius

Every Idea run whose user coined a name for the idea. The brief reads as
the model's framing rather than the user's, which the skill's first rule
forbids. Since the template was written.

## Ruled out

- A rule in the skill's Rules section alone: re-run, still 0 of 3.
- Editing the grader: eval honesty; the grader is unchanged.

## Work items

- [x] Tests pin a framing line under the template's title and the write
      step's instruction to fill it, red on origin/main.
- [x] `TEMPLATE.md` quotes the user's framing verbatim under the title;
      the write step says to fill it from the pitch or first message.
