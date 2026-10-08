# Autorun brief: readme-skill-map

Collected 2026-10-07 from the owner, one question at a time, after the
Idea stage had already run interactively. This brief is not an artifact.

## Feature

Update the README so one figure demonstrates how all of the plugin's
skills work together in a workflow — the pipeline stages and the utility
skills around them — and says why each utility skill matters. The owner's
words: "a award winning diagram / visualization that demonstrates how all
of the skills work together in a workflow. Include the additional skills
and why they matter too."

## Scale

Feature run, slug `readme-skill-map`, artifacts under
`docs/features/readme-skill-map/`. Branch `feat/readme-skill-map`,
worktree `.claude/worktrees/readme-skill-map`.

## Idea-stage inputs

Already captured in `idea.md` (problem, who, why now, evidence, hunch,
success, unknowns) — stages read that artifact; this brief does not
restate it. Answers given during that interview: sufferers are adopters
first and the owner/agents second; why-now is the public flip and plugin
0.3.0 on 2026-10-07; evidence is anecdote only and labelled so; hunch is
one committed SVG drawn by the plugin's own diagram skill; success is the
thirty-second test backed by a mechanical roster check; unknowns are
rendering, judging, density, roster rot, dogfooding in public, and the
adjacent uncommitted README edit (lean/polish).

## Scope

IN:
- Replace the README's mermaid chain with one committed, self-contained
  SVG figure that renders on GitHub in light and dark mode.
- Collapse the utility-skill prose under `## Stages` to a table with a
  one-line "why it matters" per skill.
- A stdlib test or lint check that the figure and the table name every
  directory in `skills/` (the taxonomy owner is `protocol.py`;
  `lint.check_readme_skills` and `lint.check_readme_no_orphans` already
  hold README.md to the roster — extend that pattern, do not add a
  second roster).
- Leave room for `lean` and `polish`, two skills an uncommitted edit in
  `.claude/worktrees/lean-and-polish-skills` is about to add.

OUT:
- Changing any skill's text or behaviour.
- The plugin version (`.claude-plugin/plugin.json`) — README changes need
  no bump; README.md is not in `factory_init.MIRRORS`.
- The Install, Usage and Development sections of the README.
- An animated HTML variant or an interactive presenter.

DECIDED:
- The figure is drawn with the plugin's own diagram skill
  (`architecture-diagram` or `animated-diagram`; the architect chooses and
  says why) so the front page is proof the diagram skills work.
- No external fonts, scripts or requests in the SVG; it must survive
  GitHub's image proxy inside an `<img>` or `<picture>`.
- Readable at README width; one figure, layered if density demands.
- `## Stages` heading stays (lint scopes its orphan check to it); inside
  that section every slug-shaped backtick token must be a registered
  skill, so the table backticks only skill slugs.
- Stdlib only, as everywhere in this repo.

## Tracker

No tracker seeding and no tracker interaction. The one exception is the
release step below.

## User-facing surface

The README is read by people but is a static document with no
interaction. The brief's recommendation is `ux: not-applicable` with the
reason "static document; the figure's visual design is the architect's
and implementer's concern, not a flow or screen". The PRD decides.

## Release authorization

The project's release is a squash merge to `main` (ADR-0033 gate 3). This
run is authorized to: push the branch by name, create ONE plain tracking
issue as the pull request's `Closes #N` anchor (detector B has no waiver
for that half; precedent #610, #612; never #178 or #181), and open the
pull request — non-draft, body per the protocol's "Pull request body"
section, with a `No work order:` line and no bare work-order id in
unquoted prose. Ship then STOPS: no merge. The owner judges the rendered
figure on GitHub and merges.

## Standing instructions for every stage

Answer interview questions from `idea.md` and this brief. Where both are
silent and the stage skill offers a recommended default, take it and log
it under `assumptions:`; where there is no default — including every
evidentiary question — stop and surface. Never fabricate verification
evidence: run the real commands (`python3 -m unittest discover tests`,
`python3 lint.py`, `python3 gates.py && python3 gates.py --selftest`).
Commit each stage's artifact on the branch before handing back.
