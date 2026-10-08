---
stage: idea
run: feature:readme-skill-map
date: 2026-10-07
---

# Idea: a README figure that shows every skill working together

## Problem

I open the README of a plugin that promises to take an idea to production,
and I get an eleven-box chain of stages. Fine. Then I hit sixty lines of
prose that mention, one clause at a time, thirteen more skills I did not
know existed — a router, an unattended driver, a PR-feedback worker, a
queue drainer, an installer and its doctor, three audit-shaped skills, and
a family of diagram makers. I cannot tell from the page which of those I
should reach for in my situation, or how any of them touches the chain I
was just shown. Thirty seconds in, I still cannot answer "what does this
do for me and where do I start".

## Who has it

- **Adopters, first.** Anyone evaluating the plugin from the public README.
  Today they cope by reading the whole prose block, opening `skills/` on
  GitHub and reading twenty-five `SKILL.md` descriptions, or installing
  the plugin and typing `/` to see what autocompletes.
- **The owner and dispatched agents, second.** The README is the roster
  they re-read to remember which skill owns what. Today that is a search
  through prose, not a glance at a map.

## Why now

The repository became public on 2026-10-07, so the README is the front
door for the first time, and plugin 0.3.0 landed the same day with the
full twenty-five-skill roster. The utility block has grown one clause per
skill since ADR-0023 and an uncommitted edit in flight (the `lean` and
`polish` skills) is about to add two more.

## Evidence

Anecdote only; no user report exists yet. Two signs the roster is hard to
hold in one head:

- The prose block grew skill by skill, each new one appended as another
  sentence, and now runs sixty lines with no structure a reader can scan.
- `plugin.json`'s own utility-skill list drifted out of sync with
  `skills/` once (a backlog seed, since resolved by the
  plugin-description-drift fix), so even the maintainer's machine-checked
  list could not keep the roster straight.

Nobody has been observed bouncing off the README; the absence is recorded
as absence, not as evidence either way.

## Solution hunch

One committed, theme-aware SVG in the README where the mermaid chain is
now, made with the plugin's own diagram skill (`architecture-diagram` or
`animated-diagram`), so the front-page figure is itself proof that the
diagram skills work. The stage spine runs through the middle; the utility
skills cluster around the moments a person reaches for them — before a run
exists, while driving one, around a pull request, installing the factory,
reshaping a codebase, drawing pictures — each with a one-line "why". The
prose block shrinks to a table. Which skill draws it, how the clusters are
cut, and whether the figure moves are the architect's decisions, not this
brief's.

## Success in one sentence

A newcomer opening the public README can say, within thirty seconds and
without scrolling past the figure, what the pipeline does, that utility
skills surround it, and which one to reach for in their situation — and a
mechanical check keeps the figure naming every skill in `skills/` so it
cannot rot the way `plugin.json`'s list did.

## Unknowns & risks

- **Rendering.** GitHub serves README images through its proxy, so the SVG
  must embed no external fonts or requests, and whether its
  `prefers-color-scheme` switch survives inside an `<img>` must be checked
  on the real page, not assumed.
- **Judging.** "Award-winning" has no outside judge yet; the thirty-second
  test can only be run on a stand-in reader before ship, and that result
  enters the record as anecdote.
- **Density.** Twenty-five boxes (twenty-seven once `lean` and `polish`
  land) on one figure may be unreadable at README width; the figure may
  want to be one picture with layers rather than one flat picture.
- **A second roster that rots.** The figure is hand-placed; every new
  skill needs a redraw. Without a mechanical roster check it lies within a
  quarter.
- **Dogfooding in public.** If the diagram skill's output needs heavy
  hand-editing to be good, the front page advertises a weakness of the
  very skill it was drawn with.
- **Adjacent edit in flight.** The lean-and-polish worktree's uncommitted
  README change touches the same prose block; the figure and table should
  leave room for those two skills so the two edits do not fight.
