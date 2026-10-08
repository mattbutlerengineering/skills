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

## Feedback on hand at Operate (2026-10-08)

Collected by the orchestrating session; the Operate stage's only source
beside the artifacts. Every signal below is anecdote-strength unless it
says otherwise.

- **Owner, at the gate (2026-10-07 local):** asked "What should this
  resume do?" with the rendered page linked, chose "I've looked;
  squash-merge #615" — approval of the figure as rendered, no change
  requested. Asked on 2026-10-08 whether to run the retro now or let it
  breathe, chose "Run the retro now" and added no further words.
- **Release outcome:** PR #615 squash-merged as `15caaa9`; anchor issue
  #614 closed on merge; branch deleted locally and on origin, so the
  uncropped 1.88 MB screenshots at the branch's `07ff88a` are
  unreachable; main's `check` run on `15caaa9` succeeded; `python3
  lint.py` on main prints 0 problems with `check_readme_figure`
  registered.
- **Home page at full README width:** observed by the orchestrator with
  headless Chrome (1280px window, 1x, light scheme, signed out) on the
  repository home page after the merge — the figure renders in the
  README column with the loop, six cards and legend legible. Dark was
  not re-captured on the home page; the blob-view proof in
  verification.md used the same mechanism.
- **Outside signal at retro time:** 0 stars, 0 forks, 0 watchers; no PR
  comment beyond the factory review; no issue opened since the merge.
  The repository has been public for about one day. Absence, not
  evidence.
- **Known consequences left open:** installed plugin caches (0.3.0)
  still carry the mermaid until the next version bump; the
  lean-and-polish worktree will fail lint on rebase until `lean` and
  `polish` get a table row and a figure `<text>`; two deferred minors in
  review.md (filename sublabels that stand in for three stage names; the
  embed check's substring form).
- **Process observations for the environment retro:** the 1.88 MB
  screenshots were caught only by Review's judgement — no mechanical
  check in `gates.py` or CI looks at added-binary size; the ledger rows'
  `at` field is UTC while `run_id` carries the local date (budget_guard
  stamps UTC by design); `gh pr merge --delete-branch` fails to delete
  the local branch from a worktree layout where main is checked out
  elsewhere (the remote branch had to be deleted by hand); the harness's
  permission classifier stopped `gh pr merge` until the owner answered a
  direct question; the orchestrator's first home-page capture missed the
  README because the file list pushed it below a 1800px window.
