---
stage: idea
run: feature:polish-blockers-and-patterns
date: 2026-11-04
origin: docs/backlog.md seeds "A named blocker list in `polish`" and "A grep-able detection-pattern table in `polish`'s `inspect` move" (both claimed in place, from session:2026-10-31)
assumptions:
  - "Ambition rung: the brief names none, so the skill's recommended default, Showstopper, is taken."
  - "The four Showstopper tests were run silently from the brief and the seed text; test 3 passes only on a thin reading (see Ambition rung)."
  - "In-flight guard: the orchestrator ran it on 2026-11-04 and reported no open PR, unmerged branch or worktree doing this seed's work (the only open PR is #1153, a release bump). This stage did not rerun it; a glance at `git worktree list` shows only the other four parallel runs' worktrees, none on skills/polish."
  - "Research item 5 (scenario axes in `states`) is left in the research note, not seeded; the brief says to seed it only if Idea or Architect judges it should be recorded, and this stage does not."
---

# Idea: named blockers and code detection patterns in polish

> A named blocker list in `polish` that is high severity on sight ... so "ranked by who is locked out" becomes checkable; A grep-able detection-pattern table in `polish`'s `inspect` move ... so the code-only reading step 6 already requires when nothing renders finds something. (Owner's research seeds, `docs/backlog.md` lines 140 and 141; Owner's instruction: "Do all of these in parallel".)

## Problem

A person running `polish` on a UI gets a ranking "by who is locked out"
with no named set of what locks people out. Step 5's accessibility floor
has six items, and eight known blockers sit outside it (loss at 320px or
200% zoom, meaning by color alone, a destructive action with no confirm or
undo, truncation with no way back, content hidden past a scroll edge with
no cue, an error naming no recovery, a semantic color used against its
meaning, a state change carried by motion alone). And when nothing renders,
step 6 requires a code-only reading but gives it no patterns to look for,
so it finds little.

## Who has it

Plugin users running `polish` (status draft; routing 10 of 10 on the
2026-10-10 trigger eval). Today they cope with the reviewer's own judgement
of severity and memory of what to grep for. The users' own experience of
this has not been observed; see Evidence.

## Why now

The 2026-10-31 research note (`docs/research/jakubkrehel-skills-2026-10-31.md`)
shortlisted both, as rows 2 and 3. The same note says its research item 5
(scenario axes in `states`) is worth doing only when `polish` is next
edited for these two, so this is the cheap moment to touch `polish`. Both
seeds are body-only.

## Evidence

External practitioner lists plus a gap measured against polish's own text;
no observed miss is recorded. jakubkrehel/skills' `better-interface`
blocker list and its domain skills' "Before you finish" pattern tables
(external, MIT, no evals published). The gap (six floor items, no eight
blockers, no code patterns) is read from `skills/polish/SKILL.md` step 5
and `references/moves.md`, not from a user failure. Label: anecdote at
most; nobody has been seen missing a blocker because it was unnamed.

## Ambition rung

Chosen: Showstopper (default; the brief is silent), in the Owner's words: "so \"ranked by who is locked out\" becomes checkable"
Not taken: Moonshot: a stdlib scanner that runs the pattern table over a source tree and prints file, line, pattern and WCAG id (seeded to `docs/backlog.md`); Solid: add the blocker list and the table as text, nothing more (never seeded)
Demo: pass — polish run on code with nothing rendered prints findings, each with a pattern, a file and a WCAG 2.2 id, ranked by the named blockers.
Removes a step: pass — the reviewer no longer recalls what to grep for or invents a severity order; the table and list supply both.
Only this product: pass, thinly — it rests on polish's own "ranked by who is locked out" floor and its step 6 code-only reading, which a generic checklist lacks; the lists themselves are external, restated.
Achievable: pass — riskiest piece is correct WCAG 2.2 ids; spike of about two days: draft the table and check every id against the WCAG 2.2 text, marking any that cannot be checked.

## The demo

Before: `polish` on a stylesheet and markup with no running page returns a
vague reading and a severity order from taste. After: the same run lists
rows such as `outline: none` with no `:focus-visible` replacement and
`maximum-scale=1`, each with its criterion id, ranked with the named
blockers first.

## Riskiest piece + spike

Wrong WCAG 2.2 criterion ids (a wrong id reads as authority). Spike, about
two days: draft the ten to fifteen rows, check each id against the WCAG 2.2
text, and drop or mark any id that cannot be checked.

## Cheapest kill test

Run `polish` code-only on one real UI file set before and after the edit
and compare what it names. No change in what it finds kills the idea. This
needs a model run, so it is NOT RUN in this pipeline (brief: no spend).

## Solution hunch

A short blocker list that sets severity and adds no rules, folded into the
step 5 floor and `inspect`'s ranking; and a framework-neutral pattern
table beside `inspect`'s existing thresholds in `references/moves.md`.
Both restated in this repo's words, with a credit line in the skill and in
the README credits paragraph, the way `polish` credits Impeccable.

## Success in one sentence

`polish` names the blockers that are high on sight (the floor plus the
eight), and `inspect` carries 10 to 15 framework-neutral pattern rows with
correct WCAG 2.2 ids on the accessibility rows, with the description
unchanged and the battery green.

## Unknowns & risks

- `polish` turns into a checklist. The list sets severity only.
- Patterns stay React-flavoured. They must be framework-neutral.
- WCAG criterion ids are wrong. Cite only ids checked against the WCAG 2.2 text; mark any that cannot be checked.
- Overlap with the sibling `review-interface-pass` run's removed-signals reference: that one reads diffs, this one reads surfaces and code.
- No observed miss exists, so whether either list changes what `polish` finds is untested; the check needs a paid run and is NOT RUN here.
- Out of scope: research item 5 and any description change; any `review` change belongs to another run.
