---
stage: idea
run: feature:launch-demo
date: 2026-10-08
origin: "backlog seed: Ship should include a changelog / release-notes step (from: session:2026-07-05) — absorbed as the copy half of this idea"
---

# Idea: a launch demo nobody made by hand

## Problem

I ship a feature and nobody hears about it. The factory now merges work
without me at the keyboard — autorun and work-queue here, auto-merge in the
monorepo — so a feature lands with a PR title and nothing else: no plain
description of what it is or how it helps, and no short video showing it
working. Writing that up and recording a walkthrough are the two steps still
done by hand, so they get skipped, and for anyone who did not read the diff
the feature might as well not have shipped.

## Who has it

- **The owner, first.** A solo builder running several repos where agents
  ship unattended. Today I cope by reading PR titles and the changelog, or
  by not finding out at all.
- **Whoever the feature was for.** eat-sheet operators, visitors to
  mattbutlerengineering.com, people installing this plugin. Today they learn
  a feature exists by stumbling on it.

The owner was explicit that this is not for any one repo or viewer: the
tooling lives in this repo, and every consuming app configures it.

## Why now

The factory ships unattended now. A year ago features landed slowly enough
to write the post by hand. Today the launch story is the only output of the
pipeline still produced manually, and the volume has outrun the hand.

## Evidence

All of this is anecdote.

- **Owner conviction.** "I want to create it. I care about it." No external
  demand signal was gathered; a community-scale check (last30days) was
  offered and not taken. Recorded as an unknown below, not as a finding
  against the idea.
- **Observed in the monorepo** (mattbutlerengineering/mattbutlerengineering,
  2026-10-07 to 2026-10-08): two feature PRs merged (#6142, #6156) with
  nothing beyond a PR title describing them to a reader. The other thirteen
  merges in the same window were chore and metrics commits.
- **Observed in this repo:** nine completed feature runs under
  `docs/features/`, and `release.md` is an operational record (pre-flight,
  rollback plan, release log) with no reader-facing description of what
  shipped. The backlog seed this run claims was filed on 2026-07-05 and sat
  unclaimed for three months.

## Solution hunch

One artifact, two halves, produced at the moment a consuming app says a
feature launched:

- **Copy.** A plain description of the feature, what it does, and how it
  helps, written by a model from the run's artifacts (`prd.md`,
  `verification.md`, `release.md`) or, where no run exists, from the PR body
  and changelog. This is the claimed changelog seed.
- **Video.** A short walkthrough recorded by driving the feature against a
  running instance (a browser agent for web apps, a terminal recorder for
  CLI tools), with a voiceover read from the copy.

The tooling ships from this repo. Each consuming app configures when it
fires (at Ship, on merge to main, on a release tag, on demand) and what to
record against. The copy half is easy; the video half is the hard part and
the part the owner actually asked for.

**How the video gets recorded (hunch, not design).** A model writes a short
driver script for the feature's happy path from the E2E test, `ux.md`, or
the PR body. For a web app, Playwright runs that script headlessly against
the preview-deploy URL with its built-in video recording; for a CLI tool, a
terminal renderer such as `vhs` plays a tape script to video. The copy
becomes per-step narration lines, a text-to-speech engine renders them, and
`ffmpeg` muxes audio onto video with a title card and captions. It runs in
the consuming repo's CI on that repo's trigger. A deterministic generated
script is preferred over a live browser agent: cheaper, repeatable, and a
bad script fails loudly instead of producing a wandering video. The
recorded instance needs a demo account with seeded data, or the walkthrough
shows empty screens.

Not designed here: how the recorder learns a feature's happy path, where the
artifact publishes, and the shape of the per-app config.

## Success in one sentence

A tool in this repo produces the demo video and description for a launched
feature, and each app that consumes it configures when that happens.

## Unknowns & risks

- **No environment to record against** (the most likely killer, per the
  owner). Without a preview deploy or a locally runnable app there is no
  video, only copy. Binary per repo, and it decides whether the first
  target must already have preview deploys.
- **Knowing the happy path.** The recorder must know what to click. Where no
  E2E test, `ux.md`, or verification evidence spells it out, the walkthrough
  is guesswork and the video shows the wrong thing.
- **Unattended quality.** A wrong or uncanny video sent to anyone is worse
  than silence. If the output has to be watched before it can be trusted,
  the manual step has not been removed.
- **Cost per demo.** Model, text-to-speech, and CI minutes per launch,
  against the consuming repo's monthly cap.
- **Heavy external dependencies.** A browser, ffmpeg, and text-to-speech are
  far outside this repo's stdlib-only rule for its own scripts. They would
  have to be the consuming app's dependencies, invoked as external CLIs.
- **Per-app trigger config.** "When it is generated" needs a config seam in
  each consuming repo; its shape is undecided.
- **No external demand signal.** Evidence is owner conviction plus observed
  counts. Silence from outside is recorded as silence, not as a finding.
