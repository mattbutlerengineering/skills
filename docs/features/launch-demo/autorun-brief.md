# Autorun brief: launch-demo

Collected 2026-10-08 from the owner, one question at a time, after the
Idea stage had already run interactively. This brief is not an artifact.

## Feature

A launch demo nobody made by hand. When a feature launches in any
consuming repo, produce one artifact with two halves: a plain description
of what shipped and how it helps, and a short narrated video showing it
working. The owner's words: "I want to be able to automatically record
product demos / features as they are launched. It should give a
description of the product, how it helps, etc. I want a short video
showing how it works. Can that be automated with AI?" And: "I don't want
this feature to be specific to any repo. I want to provide the tooling in
this repo and be able to consume and configure it in other repos."

## Scale

Feature run, slug `launch-demo`, artifacts under
`docs/features/launch-demo/`. Branch `feat/launch-demo`, worktree
`.claude/worktrees/launch-demo`. Origin: the backlog seed "Ship should
include a changelog / release-notes step (from: session:2026-07-05)",
claimed in `docs/backlog.md` as `(claimed: feature:launch-demo)`.

## Idea-stage inputs

Already captured in `idea.md` (problem, who, why now, evidence, hunch,
success, unknowns) — stages read that artifact; this brief does not
restate it. Answers given during that interview: the problem is that
features ship silently because the factory merges unattended; the
sufferer is the owner first and whoever the feature was for second, with
the explicit constraint that the tool is for any repo and any viewer;
why-now is the unattended factory; evidence is owner conviction plus
observed counts, all anecdote, with the community check offered and not
taken; the hunch is both halves in one artifact with per-app config of
when it fires; success is "a tool in this repo produces the demo video
and description for a launched feature, and each app that consumes it
configures when that happens"; the biggest risk is no environment to
record against.

## Scope

IN:
- A new utility skill `launch-demo` (ADR-0023 kind: directly invoked,
  owns no run artifact, never routed to) that produces, for one launched
  feature, a launch brief: the copy (what it is, what it does, how it
  helps) and a short narrated video.
- Copy is written from the run's artifacts (`prd.md`, `verification.md`,
  `release.md`) when a run exists, otherwise from the PR body and
  changelog. This delivers the claimed changelog seed.
- Video is a scripted walkthrough: a driver script generated from the
  feature's happy path (E2E test, `ux.md`, verification evidence, or the
  PR body), recorded headlessly, with narration lines rendered to audio
  and muxed by ffmpeg with a title card and captions.
- Two recorders. Terminal: a vhs tape rendered to video, for CLI tools
  and this plugin's own skills. Browser: a Playwright script recorded
  with Playwright's built-in video against a URL the config names.
- A per-repo config block the skill reads: when it fires, what to record
  against (URL or command), which recorder, the TTS command, and where
  the artifact publishes (a path in the repo). Where the config lives
  and its exact shape are the architect's call; stamped repos already
  have `factory.json` and its reader `factory_config.py`.
- Two triggers in v1: the Ship stage fires it when the config says
  `when: ship`, and a direct invocation fires it on demand.
- Narration defaults to a free local TTS engine (`say` on macOS,
  `espeak-ng` or Piper on a Linux runner); a repo swaps in a hosted
  voice by pointing the config's TTS command at it with its own key.
- Verification proves the terminal recorder end to end: a real narrated
  mp4 of one of this plugin's own skills, produced with the vhs, `say`,
  and ffmpeg installed on the owner's machine. The browser recorder is
  verified by a smoke test: Playwright records a local fixture page
  served by `python3 -m http.server`, not a real app.
- README and LEDGER rows for the new skill; lint's roster checks and
  the README figure check must stay green.

OUT:
- CI-event triggers (merge to main, release tag). Seeded to the backlog
  at Operate, not built: they need a factory workflow template and
  double the run.
- Recording a real web app (eat-sheet, the monorepo). The browser path
  ships but is proven only on a fixture page in this run.
- Hosted TTS as a default, any API key, any spend on narration.
- Publishing anywhere outside the repo (marketing sites, social, a CDN).
- Changing the Ship stage's `release.md` shape beyond the hook that
  fires the skill when configured.
- A GIF variant, Remotion, or any composition beyond ffmpeg.

DECIDED:
- Stdlib only for this repo's own Python, as everywhere. vhs, ffmpeg,
  Playwright, and the TTS engine are the consuming repo's dependencies,
  invoked as external CLIs through `cli.py`'s conventions; a missing
  tool is reported, never worked around with a fake video.
- A deterministic generated driver script is preferred over a live
  browser agent clicking around: cheaper, repeatable, fails loudly.
- The copy half must work with no video tools installed at all; the
  skill degrades to copy-only and says so.
- Any Python tool that ships to stamped repos is mirrored per
  `factory_init.MIRRORS`; after touching anything under
  `factory/templates/**` or a mirrored root file, run
  `python3 factory_init.py update-manifest` and commit the manifest.
- Plugin version bumps 0.3.0 → 0.4.0 in `.claude-plugin/plugin.json`
  because `skills/` gains a skill (installed caches go stale otherwise).

## Tracker

No tracker seeding and no tracker interaction. The one exception is the
release step below.

## User-facing surface

The skill is invoked by an agent or a person at a CLI and reads a config
block; its output (copy and an mp4) is watched by people but has no
interaction. The brief's recommendation is `ux: not-applicable` with the
reason "no interactive surface; the video's storyboard (title card,
steps, outro) is the architect's and implementer's concern, not a flow or
screen". The PRD decides.

## Release authorization

The project's release is a squash merge to `main` (ADR-0033 gate 3). This
run is authorized to: push the branch by name, create ONE plain tracking
issue as the pull request's `Closes #N` anchor (detector B has no waiver
for that half; precedent #610, #612, #614; never #178 or #181), bump the
plugin version to 0.4.0 on the branch, and open the pull request —
non-draft, body per the protocol's "Pull request body" section, with a
`No work order:` line and no bare work-order id in unquoted prose. Ship
then STOPS: no merge. The owner watches the mp4 and merges.

## Standing instructions for every stage

Answer interview questions from `idea.md` and this brief. Where both are
silent and the stage skill offers a recommended default, take it and log
it under `assumptions:`; where there is no default — including every
evidentiary question — stop and surface. Never fabricate verification
evidence: run the real commands (`python3 -m unittest discover tests`,
`python3 lint.py`, `python3 gates.py && python3 gates.py --selftest`).
Commit each stage's artifact on the branch before handing back.
