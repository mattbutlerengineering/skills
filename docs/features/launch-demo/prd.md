---
stage: prd
run: feature:launch-demo
date: 2026-10-08
id: PRD-0009
ux: not-applicable
ux-reason: no interactive surface; the video's storyboard (title card, steps, outro) is the architect's and implementer's concern, not a flow or screen
assumptions:
  - "Interview answers came from the autorun brief and idea.md, not a live interview; every section below traces to the brief's Feature, Scope (IN/OUT/DECIDED), Tracker, User-facing surface or Release authorization sections, or to idea.md's Problem, Who has it, Evidence, Solution hunch, Success and Unknowns sections."
  - "Typed id PRD-0009 assigned as the next free id (highest existing is PRD-0008), and coverage waivers added under the context sections following PRD-0008's pattern, so the breakdown cites Success criteria alone (ADR-0004, ADR-0072). The brief is silent on both."
  - "Actors are cut three ways from idea.md's 'Who has it' and the brief's 'invoked by an agent or a person at a CLI': the owner, the invoker (the Ship stage when the repo's config says so, or a person or agent invoking the skill directly), and the viewer. Because publishing outside the repo is out of scope, the only viewer this run can reach is one who opens the brief at its in-repo path. Taken without user input."
  - "'Short' is bounded structurally, not numerically: one video is one happy path — title card, the steps the driver script performs, outro — and its duration is recorded in verification.md. Neither idea.md nor the brief gives a ceiling in seconds; the owner can set one after watching the first mp4 (Open questions). Taken without user input."
  - "The new skill's LEDGER row lands at draft with no evidence, as every utility skill has since ADR-0023 set that bar; this run's own verification is the skill's test, not a launch that used it, so it graduates nothing. Taken without user input."
---

# PRD: Launch demo

## Problem statement

<!-- coverage-waiver: context for the requirements below, not a deliverable; the Success criteria carry the work every breakdown row cites -->

The factory merges work without the owner at the keyboard — autorun and
work-queue here, auto-merge in the monorepo — so a feature lands with a
pull request title and nothing else: no plain description of what it is or
how it helps, and no short video of it working. Writing the description and
recording a walkthrough are the two steps still done by hand, so they get
skipped, and for anyone who did not read the diff the feature might as well
not have shipped. The owner finds out by reading PR titles, or not at all;
the people a feature was for find it by stumbling on it. Evidence is
anecdote and labelled so: two monorepo feature PRs merged on 2026-10-07 and
2026-10-08 with a title as their whole description; this repo's own
`release.md` is an operational record with no reader-facing line about what
shipped; the changelog seed this run claims sat unclaimed for three months.
No outside demand signal was gathered, and that silence is recorded as
silence.

## Solution

<!-- coverage-waiver: narrates the same deliverables the Success criteria check one by one; the breakdown rows cite those criteria, not this summary -->

A utility skill, `launch-demo`, shipped from this repo and configured by
each repo that consumes it. Given one launched feature and the consuming
repo's config block, it produces a launch brief with two halves: copy —
what the feature is, what it does, how it helps — written from the run's
artifacts (`prd.md`, `verification.md`, `release.md`) or, where no run
exists, from the PR body and changelog; and a short narrated mp4 — a
scripted walkthrough of the feature's happy path, recorded by a terminal
recorder (vhs) or a browser recorder (Playwright), narrated by a free local
voice reading lines cut from the copy, muxed by ffmpeg with a title card and
captions — published at a path inside the repo. It fires from the Ship
stage when the config says so, or on demand. When the video tools are not
installed it produces the copy, names what is missing, and never fakes a
video. Where the config lives, how the driver script learns the happy path,
and the storyboard are the architect's calls, not this document's.

## Actors

<!-- coverage-waiver: names who is involved; no actor is itself something to build -->

- **Owner** — the solo builder running several repos where agents ship
  unattended; writes each consuming repo's config, watches the mp4, and
  merges (ADR-0033 gate 3).
- **Invoker** — whatever fires the skill: the Ship stage of a run in a repo
  whose config says `when: ship`, or a person or agent invoking it directly
  for one launched feature.
- **Viewer** — whoever the feature was for (eat-sheet operators, visitors
  to the owner's site, people installing this plugin); in this run, anyone
  who opens the brief at its in-repo path.

## User stories

<!-- coverage-waiver: each story is realized through the Success criteria the breakdown rows cite, not built as separate work -->

1. As the **owner**, I want a plain description of each launched feature —
   what it is, what it does, how it helps — written from the run's own
   artifacts, so that I learn what shipped without reading the diff.
2. As the **owner**, I want a short narrated video of the feature working,
   so that I can see it work, and show someone, without running it myself.
3. As the **owner**, I want one config block per consuming repo — when it
   fires, what to record against, which recorder, which voice, where it
   publishes — so that the tooling lives here and any repo can adopt it.
4. As the **owner**, I want a missing video tool named in the output and
   the copy still produced, so that I never receive a fake video and never
   lose the description.
5. As an **invoker**, I want Ship to fire the skill when the repo's config
   says `when: ship`, so that the brief exists the moment the feature
   launches with no step done by hand.
6. As an **invoker**, I want to run the skill directly against a feature
   that has no run directory, so that a feature that shipped from a bare
   pull request still gets its brief.
7. As a **viewer**, I want the copy and the video to be about the feature
   and to say what it does for me, so that I learn it exists without
   stumbling on it.

## Success criteria

- [ ] **Terminal recorder, end to end.** On the owner's machine, with vhs,
  `say` and ffmpeg installed, one invocation of the skill produces a
  narrated mp4 of one of this plugin's own skills (which one is Verify's
  choice, recorded). The file exists at the configured publish path;
  `ffprobe` reports one video stream and one audio stream; a frame taken
  at the start shows a title card naming the feature; the captions are the
  narration lines, every narration line is cut from the copy, and the
  video ends with an outro. `verification.md` records the invocation, the
  `ffprobe` output in a fenced block, the duration, and the title-card
  frame (check: read the record; the owner watches the mp4 before merge,
  per the brief's Release authorization).
- [ ] **Browser recorder, smoke-tested.** With Playwright installed, the
  same skill records a local fixture page served by `python3 -m
  http.server` — the page and its driver script are committed fixtures,
  not a real app — and produces an mp4 narrated and muxed the same way.
  `verification.md` records the command and the `ffprobe` output in a
  fenced block and says in those words that this proves the recorder on a
  fixture, not on a web app (check: read the record).
- [ ] **Copy from artifacts, or from the pull request.** For a feature
  with a run directory, the copy is written from `prd.md`,
  `verification.md` and `release.md`; for one without, from the PR body
  and changelog. Either way the copy has three labelled parts — what it
  is, what it does, how it helps — and names no file path, function or
  identifier a reader of the diff would need (check: `verification.md`
  shows both paths' copy in fenced blocks, each with the inputs it was
  written from named).
- [ ] **Copy-only degradation.** In an environment where none of vhs,
  ffmpeg, Playwright or the configured voice command is on `PATH`, the
  same invocation produces the copy, names each missing tool in its
  output, and writes no video file — no placeholder, no empty mp4
  (check: `verification.md` shows that run's output in a fenced block
  and an `ls` of the publish path showing copy only).
- [ ] **A free voice, no key, no spend by default.** Narration is rendered
  by the config's voice command; absent, the platform's free local engine
  (`say` on macOS; `espeak-ng` or Piper on a Linux runner). The default
  path makes no network request and reads no API key; a hosted voice is
  reachable only by a repo pointing its config's voice command at one
  (check: the skill's text and tooling name no hosted TTS endpoint or key
  variable; the config documents the swap).
- [ ] **Per-repo config, validated.** The skill reads one config block per
  repo naming at least: when it fires (`ship`, or on demand only), what to
  record against (a URL or a command), which recorder (terminal or
  browser), the voice command, and the publish path inside the repo. An
  absent voice command takes the free default above; every other absent
  or malformed field is reported as a label-prefixed problem string, never
  defaulted silently (check: tests assert the exact problem string through
  the public interface for each field).
- [ ] **Two triggers, Ship otherwise untouched.** Ship fires the skill
  when the config says `when: ship` and `release.md` records that it did,
  or that it degraded to copy-only; with no config, or any other `when`,
  Ship behaves exactly as on `main`. Direct invocation works with no run in
  flight (check: `git diff main -- skills/ship/` shows the hook and
  nothing else; `git diff main -- skills/next/` is empty; `python3
  lint.py` passes `check_skill_recitals` and `check_router`).
- [ ] **A utility skill, on every roster.** `launch-demo` is in
  `protocol.UTILITY_SKILLS`, owns no artifact and has no `TEMPLATE.md`
  (ADR-0023). The README's utility table has a row with a one-line why,
  the README figure names it, `LEDGER.md` has a `draft` row, the plugin
  description names it, and `evals/routing.json` carries at least three
  cases expecting it with no existing case edited. The plugin version is
  `0.4.0` (check: `python3 lint.py` prints `lint: 0 problem(s)`; `git diff
  main -- .claude-plugin/plugin.json` changes only the version and the
  description; `git diff main -- evals/routing.json` is additive).
- [ ] **Stdlib only; tools are the consuming repo's.** Every Python file
  this run adds imports the standard library alone. vhs, ffmpeg,
  Playwright and the voice command are invoked as external CLIs through
  `cli.py`'s runner conventions, and tests exercise them with injected
  fake runners so CI runs no real recorder. Any Python tool that ships to
  stamped repos is listed in `factory_init.MIRRORS` and the manifest is
  regenerated in the same change (check: an import sweep over the added
  files; `python3 gates.py` passes detector E).
- [ ] **Battery.** `python3 -m unittest discover tests` prints `OK`,
  `python3 lint.py` prints `lint: 0 problem(s)`, and `python3 gates.py &&
  python3 gates.py --selftest` prints `gates: 0 problem(s)` and `selftest:
  ok`.

## Out of scope

<!-- coverage-waiver: exclusions: by definition nothing here is decomposed into work -->

- **CI-event triggers** (merge to main, release tag) — seeded to the
  backlog at Operate; they need a factory workflow template and would
  double the run.
- **Recording a real web app** (eat-sheet, the monorepo), and the seeded
  demo account and data that would need — the browser path ships, proven
  on a fixture page only.
- **Hosted text-to-speech as a default**, any API key, any spend on
  narration.
- **Publishing anywhere outside the repo** — marketing sites, social, a
  CDN.
- **Changing `release.md`'s shape** beyond the line that records the hook
  fired or degraded.
- **A live browser agent clicking around** — a deterministic generated
  driver script is the decided approach: cheaper, repeatable, fails loudly.
- **A GIF variant, Remotion, or any composition beyond ffmpeg.**
- **Tracker work** beyond the one plain tracking issue Ship opens as the
  pull request's closing anchor; no seeding, no mirroring.

## Open questions

<!-- coverage-waiver: questions settled downstream by Architect, Verify or the owner at merge, not requirements of this run -->

- Where the config block lives and its exact shape — stamped repos already
  have `factory.json` and its reader `factory_config.py`; this repo is the
  first consumer. — Architect.
- How the driver script learns the happy path when more than one source
  exists (an E2E test, `ux.md`, verification evidence, the PR body) and
  what happens when none does: copy-only, or a refusal that says why. —
  Architect, under idea.md's second risk.
- Which parts are the agent's (the copy, the driver script) and which are
  a shipped tool's (probing for tools, rendering, muxing), given the
  stdlib rule and `cli.py`'s conventions. — Architect.
- Where inside the repo the brief publishes, and whether a committed mp4
  belongs in git at all or the publish path should be an ignored
  directory — a video per launch grows a repo fast. — Architect.
- The storyboard — title card, step pacing, caption placement, outro —
  and how narration lines are cut from the copy. — Architect and
  implementer.
- The copy-only run's exit status, and how Ship records the degradation
  so a reader of `release.md` sees it. — Architect.
- Which Linux voice (`espeak-ng` or Piper) is the runner default; only
  macOS `say` is exercised in this run. — Architect.
- Which of this plugin's own skills the terminal demo records, and how
  Playwright with its browsers reaches the verifier's machine. — Verify,
  recorded with the commands.
- A numeric ceiling for "short", once there is an mp4 to judge. — Owner,
  after watching the first one.
