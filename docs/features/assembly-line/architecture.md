---
stage: architect
run: feature:assembly-line
date: 2026-11-05
---

# Architecture: An animated assembly line of every run in the repo, with a history replay

## Approach

A root tool states the facts and a fixed page template draws them, the
pipeline-board split (ADR-0062) applied to a richer surface.
`assembly_line.py` reads one repo: placement from `board.gather`,
completed runs and stage states from `protocol.py`, work-order rows from
`knowledge_plane.breakdown_rows`, and each artifact's frontmatter
`date:`. It folds them into one JSON model, a snapshot plus a day-tick
replay timeline, and writes one self-contained HTML file: the template
`assembly_line.html` with the model and the vendored three.js inlined
(ADR-0124). The page derives no pipeline fact; it only draws, animates,
interpolates within a day, and exports its own replay as a GIF. The
alternative shape, the agent authoring the scene per invocation as the
diagram skills do, loses on the PRD's "every repo gets the same
factory" and on exactness, since a model-written scene is a second
deriver of placement.

## Components

### `assembly_line.py` (root tool)

- Responsibility: the factory model for one repo: every run once
  (active, completed or attention), its ladder, its dated stage history,
  its work orders, and the replay timeline; and writing the page.
- Collaborators: `board.gather` (active-run placement and the attention
  list, verbatim), `protocol.run_dirs`, `protocol.next_stage`,
  `protocol.stage_states`, `protocol.read_frontmatter`,
  `protocol.breakdown_path`, `knowledge_plane.breakdown_rows`,
  `cli.report` (problem strings).

### `assembly_line.html` (root page template)

- Responsibility: drawing and interaction. The isometric scene (one tile
  per station, the serpentine belt, machines, crates, pallet stacks with
  count tags, the warehouse, the Needs-attention bin), idle animation,
  replay playback with even intra-day spread and the dashed-shadow
  mark, the hover card, the pinned panel, the transport bar, reduced
  motion, the no-WebGL fallback list, and GIF export.
- Collaborators: the inlined model (read-only) and the inlined
  three.js. It lives beside the tool, as `dashboard.html` does beside
  `dashboard.py`.

### `vendor/three/` (vendored library)

- Responsibility: three.js v0.187.0 build files and licence, copied
  verbatim into each page (ADR-0124).
- Collaborators: read as text by `assembly_line.py`; executed only in
  the page.

### `skills/assembly-line/SKILL.md` (utility skill)

- Responsibility: invoke the tool from the target repo, open the page,
  surface the tool's problem output and stop on failure, and walk the
  Owner through Export and `--publish` for the README. Directly invoked,
  owns no run artifact (ADR-0023).
- Collaborators: `assembly_line.py`, located two directories above the
  skill as pipeline-board locates `board.py`.

## Data model

Access patterns, all reads, all from one invocation's snapshot: (1) the
floor today: every run's station; (2) a scrubbed day: every run's
station at that day's end; (3) a station's runs, oldest first; (4) a
run's work orders. Consistency: one snapshot per invocation; nothing is
written back and nothing is live.

```json
{
  "generated": "2026-11-05T10:00:00+00:00",
  "repo": "skills",
  "stations": ["capture", "idea", "prd", "ux-design", "architect",
               "decompose", "implement", "verify", "review", "ship",
               "operate", "completed"],
  "runs": [{
    "ref": "feature:eval-trends", "kind": "feature", "slug": "eval-trends",
    "dir": "docs/features/eval-trends",
    "status": "active | completed | attention",
    "station": "implement",
    "ladder": [{"stage": "idea", "state": "done"}],
    "reason": null,
    "history": [{"day": "2026-10-21", "station": "idea", "inferred": false}],
    "work_orders": [{"title": "…", "done": true}]
  }],
  "timeline": {"first_day": "2026-07-01", "last_day": "2026-11-05"}
}
```

- `station` for an active run is `board.gather`'s current stage; for a
  completed run, `completed`; for an attention run, null with `reason`
  from `board.gather`. Invariant, owned by the tool: every run directory
  `protocol.run_dirs` lists that holds a run artifact appears exactly
  once.
- `history` is the ordered list of station arrivals: the run enters its
  first station on its first artifact's date and reaches each later
  station on the date of the artifact that completed the stage before
  it; Implement starts on the breakdown's date (or `defect.md`'s when
  the breakdown is inline) and ends on `verification.md`'s. Skipped
  stages produce no arrival. `inferred` is true for every arrival that
  shares its day with another arrival of the same run (the page's dashed
  shadow). The last arrival equals `station`, so the replay's last frame
  is the snapshot.
- An artifact with no readable `date:` takes the nearest earlier dated
  artifact's date in the same run, marked `inferred`; a run with none
  enters on `last_day`.
- `work_orders` lists the run's breakdown rows (title and done) from
  `knowledge_plane.breakdown_rows`, present for runs at or past
  Implement; progress is today's only (checkbox ticks are undated).
- Attention runs carry no `history`; they sit in the bin for the whole
  replay.

## Interfaces & contracts

### `python3 assembly_line.py [root] [--out PATH] [--publish DIR]`

- Input: a repo root (default `.`). `--out` names the HTML file to write
  (default: a fresh file in the system temp directory, outside the
  tracked tree). `--publish DIR` writes `DIR/index.html` instead, for
  the Owner to commit beside the exported GIF.
- Output: writes the page; prints its absolute path on stdout; exit 0.
  `gather(root)` returns `(model, problems)` and `render(model, template,
  vendor)` returns the HTML text, the two seams tests pin.
- Failure modes: no `docs/` tree → `board.gather`'s problem string,
  exit 1, no page (as pipeline-board). Unreadable template or vendor
  file → `assembly_line: cannot read <path>: <reason>`, exit 1. A run
  that cannot be oriented never fails the tool: it is an attention run.
  Local files only, no network, no timeouts.

### The page's model contract

- Input: one `<script type="application/json">` block holding the model
  above, escaped so `</` cannot close it.
- Output: the floor, hover card, pinned panel, transport bar and Export
  button, per `ux.md`.
- Failure modes: WebGL unavailable → a one-line notice plus the plain
  per-station list from the same model; a model missing a required key
  → the same list with a notice naming the key, never a blank page.

### Export clip (in the page)

- Input: the Owner presses Export.
- Output: the page plays the replay at a fixed export size and frame
  rate, captures frames from its own canvas, encodes an animated GIF in
  the page (a first-party encoder in the template; the flat palette fits
  GIF's 256 colours) and downloads it.
- Failure modes: an encode error or a browser that blocks the download
  → an on-page message; nothing partial is offered.

## Stack & dependencies

- Python 3 standard library for the tool (`stdlib-only`).
- three.js v0.187.0, vendored and inlined (ADR-0124): one large library
  behind a narrow interface used only inside the page template.
- No GIF library: a first-party encoder in the template.
- Root placement for the tool, template and vendor folder, carried by
  `npx_bundle.py` (ADR-0120) alongside `dashboard.html`.

## Decisions & alternatives

- **A new tool `assembly_line.py`** over extending `board.py` — board's
  contract says completed runs appear nowhere (ADR-0062) and
  pipeline-board renders it verbatim; adding completed runs, dates and
  work orders there changes a shipped skill's input. The Owner chose
  this on 2026-11-05.
- **Bundle three.js** over a hand-written Canvas 2D isometric renderer —
  ADR-0124. Owner's choice, 2026-11-05.
- **A fixed page template filled with data** over the agent authoring
  the scene each run — determinism and one deriver of placement
  (ADR-0062).
- **The replay timeline built in Python** over in the page — the
  timing rules are policy and get unit tests against fixture trees; the
  page only spreads a day's arrivals evenly.
- **Frontmatter dates only** over a git-log fallback — 565 of 565
  artifacts here and 318 of 319 in mattbutlerengineering carry `date:`,
  squash merges make git times wrong for 86 of 106 runs, and a git
  read would add a subprocess seam with failure modes for no gain.
- **In-page GIF export** over a Python-written animated SVG — a second
  drawing of the factory would have to keep matching the first. Owner's
  choice, 2026-11-05.
- **Write outside the tree by default, `--publish DIR` on request** over
  always committing the page — pipeline-board's convention, with an
  explicit path when the Owner wants a Pages-hosted link. Owner's
  choice, 2026-11-05.
- **Show the phantom product run as placed** over teaching run
  discovery to tell project docs from run artifacts — run discovery is
  `protocol.py`'s and every stage depends on it; the page shows it with
  its directory and "already has" line so the owner sees why, and the
  discovery question is seeded to `docs/backlog.md`.

## ADRs

- [ADR-0124](../../adr/0124-the-assembly-line-page-bundles-three-js.md) — the assembly-line page bundles three.js.

## Traceability

| PRD criterion | Component |
|---|---|
| No setup, any repo | `assembly_line.py` (stdlib, local reads), skill |
| Complete and exact | `assembly_line.py` invariant; tests against `board.gather` |
| Completed is its own bucket | `assembly_line.py` (`protocol.next_stage`), page warehouse |
| Hover explains | page hover card and pinned panel |
| Replay; replay honesty | `history`/`inferred` in the tool; page transport bar |
| Style match; moving parts at 60 fps | page template with three.js |
| Cold-viewer test; the Owner would show it | the whole page; checked at Verify |
| Adopter clip | page Export; `--publish` |
| The demo runs as written | the whole flow |
