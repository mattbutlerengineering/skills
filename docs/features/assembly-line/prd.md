---
stage: prd
run: feature:assembly-line
id: PRD-0021
date: 2026-11-05
ux: required
assumptions:
  - "Interview held live with the Owner on 2026-11-05: actors, the quality bar, out-of-scope and the adopter view were each picked from offered options. The quality bar and adopter-view questions were re-asked once as a single pick after an empty answer; nothing was defaulted."
  - "PRD-0021 is the next free id: the highest on origin/main and on every unmerged branch is PRD-0020."
  - "idea.md's The demo is prose, not a numbered script; it is copied as the steps of the 'demo runs as written' criterion."
  - "The renderer the idea brief names (three.js) is a technology choice, so it is parked under Open questions for Architect, per the prd skill's rule."
---

# PRD: An animated assembly line of every run in the repo, with a history replay

## Problem statement

The pipeline is a factory, but no view of it looks like one. The shipped
pipeline-board draws a static swimlane of active runs; its own author does
not use it ("it's not good enough"). In it, work piling up does not read
as a queue (on `origin/main` today, 75 of 90 active runs sit at Operate),
nothing says what a step is doing, and finished runs vanish, so the
factory never shows its output. The Owner wants to show the factory to
other people and to run the same view in his other repos; the current
visual is not something he would show.

## Solution

A utility skill, vended with the plugin, that turns any repo's pipeline
runs into an animated isometric factory in the style of the Owner's
reference illustrations (flat outlined line art; green belts, grey
machines, purple accents). Each pipeline stage is a machine tile joined to
the next by a conveyor; each run is a crate at the station it is on; a
run's work orders are small parts inside Implement; finished runs stack in
a Completed warehouse. Hovering a station explains what that step does and
lists what is in it; hovering a crate names the run and its progress.
Pressing play replays the repo's history from its dated artifacts, crates
moving station to station and filling the warehouse. The same skill can
export a looping clip of the replay for a README or post.

## Actors

- **Presenter** — the Owner, driving the factory live in a meeting or
  screen-share, hovering to explain each step.
- **Cold viewer** — someone who has never seen the factory, watching it
  once, live or recorded.
- **Adopter** — a developer deciding whether to install the plugin, who
  meets the factory on a README or launch post with nobody there.
- **Repo owner** — anyone who runs the skill in their own repo (the Owner
  in mattbutlerengineering, or any consumer) to see that repo's work.

## User stories

1. As a Repo owner, I want one skill invocation to draw my repo's factory
   with no setup, so that I see all of its work without configuring
   anything.
2. As a Repo owner, I want every run and every work order on the line
   exactly once, with finished runs in their own Completed area, so that
   I can trust the picture is the whole of the work.
3. As a Presenter, I want to hover any station and see what that step
   does and what is in it, so that I can explain the pipeline by pointing.
4. As a Presenter, I want to play, pause and scrub a replay of the repo's
   history, so that I can show months of output in about 30 seconds.
5. As a Cold viewer, I want the stages and the busiest station to be
   obvious from the picture, so that I understand the factory without
   being taught it.
6. As an Adopter, I want a looping clip of the replay on the README that
   links to the interactive factory, so that I see the factory working
   before I install anything.
7. As a Presenter, I want the replay to say which timing is recorded and
   which is inferred, so that what I show is not more precise than the
   repo's history.

## Success criteria

- [ ] **No setup, any repo.** One skill invocation produces the factory
      in this repo and in mattbutlerengineering, with nothing installed or
      configured in either first.
- [ ] **Complete and exact.** For both repos, every run directory appears
      exactly once, at the station the pipeline's own orientation rules
      put it (pipeline-board's placement tool agrees run for run), and
      each Implement run shows exactly as many parts as its breakdown has
      rows, open and finished distinguished.
- [ ] **Completed is its own bucket.** Runs the protocol counts complete
      (retro with its population line) appear only in the Completed area;
      shipped runs without one stay at Operate, labelled as shipped and
      awaiting a retro on hover, not relabelled as complete.
- [ ] **Hover explains.** Hovering each station shows the stage's name,
      a one-line description of what it does, and the runs currently in
      it; hovering a crate shows the run's name, kind, current stage and,
      in Implement, work orders done out of total.
- [ ] **Replay.** Play, pause and scrub work; the replay's clock shows the
      date; each crate enters on its first artifact's date and reaches
      each station on that stage artifact's date; the last frame equals
      the snapshot.
- [ ] **Replay honesty.** The page states that dates come from artifact
      frontmatter to the day and that order within a day is inferred from
      stage order.
- [ ] **Style match.** Placed beside the Owner's three reference images,
      the Owner judges it the same style (true isometric view, outlined
      flat shading, green/grey/purple palette, one tile per stage) and the
      verdict is recorded in the run's verification.
- [ ] **Moving parts, smoothly.** Every station has at least one
      continuously animated mechanism (belt, arm, scanner, cart), and the
      replay of this repo's 106 runs holds about 60 frames per second on
      a 2021-or-later laptop, measured and recorded.
- [ ] **Cold-viewer test.** Shown cold, at least 2 of 3 people who have
      never seen the factory name the stages in order and the busiest
      station within 30 seconds of watching the replay; results recorded.
- [ ] **The Owner would show it.** The Owner chooses it over the old
      board for a real presentation, and the occasion is recorded.
- [ ] **Adopter clip.** The skill exports a looping clip of the replay
      that plays inline on a GitHub README and links to the interactive
      factory.
- [ ] **The demo runs as written.**
      1. Open the factory for this repo; it shows every run at its
         station, work piled up where it actually waits.
      2. Press play: crates enter, move machine to machine as each stage's
         artifact lands, pile up where work waited, and drop into
         Completed.
      3. Hover any machine: it says what that step does and which items
         are in it.

## Out of scope

- Live or real-time updates: each invocation is a snapshot plus replay.
- Several repos in one view (the backlog's live-floor seed).
- Acting from the page: no merge, gate pass or any write; display only.
- Open pull requests and agent sessions as items: runs and work orders
  only.
- Retiring or replacing the pipeline-board skill; that is decided after
  this ships.

## Open questions

- Renderer: the idea brief's hunch is three.js with an orthographic
  isometric camera and flat outlined faces, bundled into the output file.
  Shipping bundled third-party code is a first for the plugin and needs an
  ADR beside ADR-0008. — Architect, with the Owner's approval.
- Where the interactive factory the README clip links to lives (a file in
  the repo, GitHub Pages, or a release asset). — Architect and the Owner.
- Whether placement extends pipeline-board's tool or a new reader wraps
  it; placement must keep one owner either way. — Architect.
- The station-by-station metaphor (crate opened into parts at Decompose,
  arms at Implement, scanner at Verify, and so on) and how the replay
  shows inferred timing. — UX Design.
- How a 75-crate pile at one station reads as a pile rather than clutter.
  — UX Design.
