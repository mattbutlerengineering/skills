---
stage: idea
run: feature:svg-mechanical-check
date: 2026-11-04
assumptions:
  - "Ambition rung: the autorun brief names no pick and no ladder answer, so the skill's recommended default, Showstopper, is taken; the Moonshot is seeded."
  - "Verbatim framing: the brief carries no first-person pitch, so the quote is the seed line the Owner's research produced (docs/backlog.md, shortlist 4 of the jakubkrehel research note), not a spoken sentence."
  - "Interview answers (problem, who, why now, evidence, hunch, success, unknowns) are the brief's Idea inputs, which the brief states are the orchestrator's reading of the seed and the research note; nothing beyond them is filled in."
  - "Backlog line 91 (the boilerplate's missing root width/height) is left unclaimed at Idea; the brief says to mark it claimed if the fix lands in this run, which is a later stage's act."
---

# Idea: a mechanical SVG check for the diagram skills

> A mechanical check in `architecture-diagram`'s step 7 (and the pure-SVG path of `animated-diagram`): parse the file with stdlib `xml.etree` under `python3 -I`, fail on duplicate ids, unresolved `url(#...)` references, any external `href`, or a missing root width/height, and read the smallest text tier at README embed width.

Origin: the seed on `docs/backlog.md` line 142 (claimed: feature:svg-mechanical-check), from `docs/research/jakubkrehel-skills-2026-10-31.md`, shortlist row 4. Related seed: backlog line 91, the `architecture-diagram` scaffold with a viewBox and no root width/height.

In-flight check: ran on 2026-11-04 by the orchestrator before this stage, outcome: clean. No open pull request, unmerged branch or worktree does this seed's work; the only open pull request is #1153, a release bump. Recorded from the orchestrator's report; this stage did not rerun it.

## Problem

Someone generating a diagram with `architecture-diagram` or `animated-diagram` checks the SVG by eye at step 7. Defects a parser catches in a second ship anyway (a duplicate id, a reference to an id that is not there, an external link, no intrinsic size) and are found later, by hand, by someone looking at the rendered page.

## Who has it

Plugin users of the two diagram skills, both draft, and this repo's own README skill map. They cope by eye and by hand-editing the file after it ships.

## Why now

The research note of 2026-10-31 shortlisted it as Adopt, and the check needs no new dependency: the standard library parses the file.

## Evidence

Observed in this repo, not anecdote: the readme-skill-map run hand-fixed a missing root width/height and 8 to 9px text tiers (backlog line 91 and that run's verification). That is two defects found in this repo's own artifact. External, and data only: another author's verification step does the same parse. Nothing here measures how often users of the two skills hit these defects; that count is unobserved.

## Ambition rung

Chosen: Showstopper (default taken, see `assumptions:`), in the seed's words: "fail on duplicate ids, unresolved `url(#...)` references, any external `href`, or a missing root width/height, and read the smallest text tier at README embed width".
Not taken: Moonshot: a rendered check that rasterizes the diagram in a browser at embed width and compares it to a reference (seeded, backlog line 161); Solid: the four failures only, with no text-size reading.
Demo: pass — the check run on a defective SVG prints one named line per defect, and on a clean one prints a pass and the smallest text size at embed width.
Removes a step: pass — the by-eye step 7 inspection for these defects is gone; the check names them before the file ships.
Only this product: pass — the check sits at step 7 of the skill that produced the file and reads the skill's own scaffold conventions (viewBox, ids, tiers), which a generic linter does not know.
Achievable: pass — riskiest piece is refusing DTDs and entities while parsing with `xml.etree`; a two-day spike builds fixtures (billion-laughs, external entity, clean file) and shows the parser refuses each before expansion.

## The demo

Before: a diagram with no root width/height, a duplicate id, a dangling `url(#...)` and an external `href` ships and is noticed in a README as a thumbnail. After: the check prints each of the four by name and exits non-zero, then on the fixed file prints a pass with the smallest text size at embed width.

## Riskiest piece + spike

Parsing untrusted SVG safely: `xml.etree` is not hardened against entity expansion, so the check must refuse a DTD or entity declaration before parsing rather than rely on the parser. Spike (about two days): fixture files with an entity-expansion payload and an external entity, and a test that the check rejects both without expanding them.

## Cheapest kill test

Run the four detections by hand over the current `assets/boilerplate.svg`, the `animated-diagram` boilerplate and the README skill map. If none of the three shows a defect beyond the known missing width/height, the check is catching nothing the eye misses and the idea is weak.

## Solution hunch

A stdlib check run over the produced SVG at step 7. Whether it is an inline `python3 -I -c` snippet in the skill or a script shipped in the skill directory is Architect's call. A hunch, not a design.

## Success in one sentence

On an SVG with a missing root width/height, a duplicate id, a dangling `url(#...)` and an external `href`, the check fails and names each one; on a clean SVG it passes and reports the smallest text size at embed width.

## Unknowns & risks

- Untrusted input: the check must refuse DTDs and entities, not become a vector itself.
- "Smallest text tier at embed width" needs an embed width and the viewBox scale; what it reads and what it refuses is undefined.
- Animated SVG (SMIL and CSS) may reference ids in ways a naive `url(#...)` check misreads, for example `begin="id.end"` or `href` inside `<use>`.
- The skill's own `assets/boilerplate.svg` fails the check today (backlog line 91); the scaffold must be fixed in this run or the skill ships broken.
- Whether a shipped script belongs in the plugin payload depends on the packaging rules (lint, factory manifest); unknown until Architect reads them.
- Scope edge: if the check finds defects in the README skill map, they are recorded as a seed, not fixed here.
