---
name: assembly-line
description: Generate the assembly line — one self-contained animated HTML page that draws every run in the current repo as a crate on an isometric factory floor, one machine per pipeline stage, finished runs raising a named building each in the city at the end of the line, hover and click detail on every station and crate, a play-and-scrub replay of the repo's history, and a GIF export for a README. Use when the user wants to see all the work moving through the pipeline as a factory or assembly line, watch the repo's history replay, show the factory to someone, or put an animated clip of it on a README. Facts come from the shipped assembly_line.py tool, never re-derived. Not the pipeline-board (a static swimlane SVG of active runs only) and not a stage skill — directly invoked, owns no run artifact, changes nothing in the repo unless asked to publish.
---

# Assembly Line

Produce one `.html` page: the repo's pipeline as an animated factory.
Every run is a crate at the station its next stage names, a run's work
orders are parts inside Implement, and finished runs raise the
city at the end of the line: one named building per shipped run. The facts are stated by `assembly_line.py` and inlined
verbatim; the drawing is the page template's. Nothing is drawn or
placed by hand.

Work these steps in order.

## 1. Write the page

Run the shipped tool — it lives two directories above this skill's
directory in the same checkout:

    python3 <this skill's directory>/../idea-to-prod-runtime/assembly_line.py [repo root]

The repo root defaults to the working directory. The tool writes the
page to a new file in the system temp directory, outside the repo's
tracked tree, and prints its absolute path. `--out PATH` writes exactly
that path instead.

**A nonzero exit means no page.** Print the tool's problem output and
stop — never write or patch a page by hand, and never place a run
yourself. The tool is the only owner of placement and dates.

Done when: the printed path exists, or the failure has been surfaced and
work has stopped.

## 2. Hand it over

Open the page, or hand its path to the user, whichever the session
supports. Tell the user what it holds, in one or two sentences, from
the page's own header line (repo, active and completed counts, as-of
date) — not from your own count. Point at the five things to do on it:

- Read it at a glance: the chip strip across the top is the pipeline in
  order with each station's live count, the amber chip and sign mark the
  busiest station, and the "How to read this" key opens on load.
  Clicking a chip flies the camera to its station and pins its list.
  For a cold room, the Tour button walks the floor in five beats —
  entry, build, the pile-up, the city — and ends in the replay.
- Find one run: the header's "find a run…" box (every slug offered)
  flies to its crate and pins its row; ◉ trace on any pinned row
  replays that run's journey solo, every other crate hidden until
  Esc or the banner's stop.
- Hover any machine or crate to see what that step does and what is in
  it; click to pin the full list, Esc to close. Scroll or pinch to
  zoom, drag to pan, double-click to reset.
- Press Play (or Space) to replay the repo's history; drag the scrubber,
  step a day with ← and →, or jump back with the "today" button. The
  big date over the floor says where in time the view is. Dates are to
  the day from artifact frontmatter, and order within a day is
  inferred, as the page says under the bar.
- Press Export clip for a looping GIF of the replay, and share any
  view as a link: the page writes #day=, #run=, #station=, #trace=,
  #tour and #view= into the address bar as you drive, and the links
  work live — pasting one into an open page's bar applies it, and
  clearing the bar resets to today. Press / to jump to the finder.

The page follows the system's light or dark scheme, and it is one file
with no network access: nothing leaves the machine it is opened on.

If the browser cannot draw the factory, the page says so and lists every
run by station instead; the facts are the same.

Done when: the user has the page and knows those controls.

## 3. Put it on a README (only when asked)

The page is disposable by default. When the user wants the factory on a
README or a launch post:

1. Run the tool again with `--publish <dir>` (for example
   `--publish docs/factory`). It writes `<dir>/index.html` in the repo,
   for the user to commit.
2. Open that page and press **Export clip**. The download is a looping
   GIF named after the repo; the user moves it beside the page.
3. Give the user the README line to add: the GIF as the image, linked to
   the published page — its GitHub Pages URL when Pages serves that
   directory, otherwise the committed file. For a repo `OWNER/REPO`
   published to `docs/factory` with Pages serving `docs/`:

       [![The assembly line](https://raw.githubusercontent.com/OWNER/REPO/main/docs/factory/REPO-assembly-line.gif)](https://OWNER.github.io/REPO/factory/)

A README shows the GIF; it cannot run the interactive page. Committing
and pushing stay the user's decision: this skill never commits.

Done when: the user has the published page, the GIF and the README line,
or was not asking for them.

## Installed by the skills CLI

This copy came from this repo's `npx` branch. The plugin root these
steps name is the sibling folder `../idea-to-prod-runtime/`, which holds the
pipeline protocol, `CONTEXT.md`, `factory/` and every root tool. Where a
step runs a tool from the plugin root or the factory repo checkout, run
`python3 <this skill's directory>/../idea-to-prod-runtime/<tool>.py`. A stamped
repo's `tools/factory/` copy still wins wherever a step says so. Two
plugin features are absent: the `/idea-to-prod:<skill>` names (use
`/<skill>`) and the house-voice output style.
