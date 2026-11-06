---
stage: decompose
run: feature:assembly-line
date: 2026-11-05
---

# Breakdown: An animated assembly line of every run in the repo, with a history replay

Progress lives in the checkboxes below. Implement checks items off as their
acceptance criteria are met. Tool tests go in `tests/test_assembly_line.py`,
run through `gather`, `render` and `main` with fixture trees built in a temp
directory, and never touch the network. Page items are checked in a real
browser on a page the tool wrote for this repo, as `ux.md` and
`architecture.md` describe it.

## Milestone 1: every run, exactly once, in a page

When this milestone is done, `python3 assembly_line.py` writes a
self-contained page for any repo that lists every run at its station
(the no-WebGL fallback list), with the full model inlined. No factory
yet, but the facts are complete and pinned.

- [x] **WO-0198** Snapshot model tests — `gather` cases over fixture trees — size:S, blocked by: — (PRD-0021 §Success criteria)
  - Accept: the cases build trees holding a feature run at Implement with a breakdown, a feature run whose PRD skipped UX, a maintenance run with `re-entry: implement` (inline breakdown) and one with `re-entry: architect`, a completed run (retro with population line) and a pre-ADR-0102 retro with neither field, a run whose artifacts cannot be read, a gapped ladder (a done stage after current), and a `docs/` root holding only `architecture.md`. They assert: every run directory holding a run artifact appears exactly once in `runs`; active runs' `station` and `ladder` equal `board.gather`'s for the same tree; completed runs have `station: completed`; the unreadable run is `status: attention` with `board.gather`'s reason and no `history`; `work_orders` lists each breakdown row's title and done state for runs at or past Implement, and its length equals `protocol.checkbox_progress`'s total for that breakdown. Before `gather` exists they fail on the missing module.
- [x] **WO-0199** Snapshot model — `assembly_line.gather(root)` returning `(model, problems)` — size:M, blocked by: WO-0198 (PRD-0021 §Success criteria, §User stories)
  - Accept: the WO-0198 cases pass. `gather` takes placement and attention from `board.gather` verbatim and completed runs from `protocol.run_dirs` plus `protocol.next_stage`; a search of `assembly_line.py` finds no stage-order or artifact-table literal of its own. A root with no `docs/` returns `board.gather`'s problem string and no model.
- [x] **WO-0200** History tests — cases for `history` and `timeline` — size:S, blocked by: WO-0199 (PRD-0021 §Success criteria)
  - Accept: cases assert, per architecture.md's Data model: a run enters its first station on its first artifact's date; each later arrival is on the date of the artifact that completed the stage before it; Implement starts on the breakdown's date (`defect.md`'s when inline) and ends on `verification.md`'s; skipped stages produce no arrival; every arrival sharing a day with another arrival of the same run is `inferred: true`; an undated artifact takes the nearest earlier dated artifact's date, marked inferred; a run with no dates enters on `last_day`; the last arrival's station equals `station` for every active and completed run; `timeline.first_day` and `last_day` bound every arrival. Before the fields exist the cases fail.
- [x] **WO-0201** History and timeline — `history` per run and `timeline` in the model — size:M, blocked by: WO-0200 (PRD-0021 §Success criteria, §User stories)
  - Accept: the WO-0200 cases pass, and dates are read only through `protocol.read_frontmatter`. On this repo, every active and completed run's last arrival equals its `station` (a throwaway check over the real tree, output recorded in the PR).
- [x] **WO-0202** Page writer tests — cases for `render` and `main` — size:S, blocked by: WO-0199 (PRD-0021 §Success criteria)
  - Accept: cases assert: `main` with no flags writes a new file under the system temp directory and prints its absolute path, exit 0; `--out PATH` writes exactly PATH; `--publish DIR` writes `DIR/index.html`; a root with no `docs/` exits 1 with the problem string and writes nothing; an unreadable template or vendor file exits 1 with `assembly_line: cannot read <path>: <reason>`; a run slug containing `</script>` cannot close the model block (the written page parses the model back equal to `gather`'s). Before `render` exists they fail.
- [x] **WO-0203** Page writer and fallback list — `render`, `main`, and `assembly_line.html` with the fallback list — size:M, blocked by: WO-0201, WO-0202 (PRD-0021 §Success criteria)
  - Accept: the WO-0202 cases pass. `assembly_line.html`, opened in a browser with WebGL disabled, the page shows its one-line notice and one list per station (all twelve, Capture through Completed) holding every run in the model, plus the Needs-attention list; a model missing a required key shows the same list with a notice naming the key. The page makes no network request (browser network log empty beyond the file itself).
- [x] **WO-0204** Two-repo parity check — run the tool on this repo and on mattbutlerengineering — size:S, blocked by: WO-0203 (PRD-0021 §Success criteria, §Problem statement)
  - Accept: for both repos, with nothing installed or configured first, the page's lists hold every run directory exactly once and the active counts equal `python3 board.py`'s `runs` length; the counts and the phantom product run in mattbutlerengineering are recorded in the PR.

## Milestone 2: the factory floor

When this milestone is done, the page draws the isometric factory of
`ux.md` for today: every station animated, every crate in place, hover and
pin working.

- [ ] **WO-0205** Vendored three.js — `vendor/three/`, NOTICE, bundle and inlining — size:S, blocked by: WO-0203 (PRD-0021 §Success criteria, §Solution)
  - Accept: `vendor/three/` holds three.js v0.187.0's `three.module.min.js` and `three.core.min.js`, byte-identical to the published release, and its licence; `NOTICE` names it under ADR-0124; `npx_bundle.py` carries `assembly_line.html` and `vendor/three/` and `tests/test_npx_bundle.py` passes with the bundled tool writing a page; the written page inlines both files and loads them with no network request.
- [ ] **WO-0206** Isometric floor — tiles, serpentine belt, warehouse and bin — size:M, blocked by: WO-0205 (PRD-0021 §Solution, §Success criteria)
  - Accept: `assembly_line.html` draws an orthographic isometric view with one floor-plate tile per station in rows of four, its stage name painted on the plate, one continuous belt in pipeline order, the Capture side belt feeding the main belt, the Completed warehouse tile and the Needs-attention bin; flat per-face colours in the reference palette (green, grey, purple on a pale ground) with dark edge lines; a screenshot is attached to the PR.
- [ ] **WO-0207** Station machines — the twelve machines of ux.md, each animated — size:L, blocked by: WO-0206 (PRD-0021 §Success criteria)
  - Accept: each station shows the machine `ux.md` names for it (repair bench, intake dock, label printer, design bench, gantry crane, opening arm, twin assembly arms, tunnel scanner, inspector, packing and forklift, outbound dock, shelving), and each moves continuously with no crates present; under `prefers-reduced-motion: reduce` the floor opens still. A short screen recording is attached to the PR.
- [ ] **WO-0208** Crates, piles and parts — crates at stations, pallet stacks, count tags, parts trays — size:M, blocked by: WO-0207 (PRD-0021 §Problem statement, §Success criteria)
  - Accept: on this repo's page every run is one crate at its station; a station with more than 6 runs queues 6 on the belt and stacks the rest on pallets with a count tag equal to its run count; Completed holds every completed run on its shelves; each Implement crate carries a parts tray whose fill is done over total; the busiest station is the tallest stack.
- [ ] **WO-0209** Hover card and pinned panel — the two detail surfaces of ux.md — size:M, blocked by: WO-0208 (PRD-0021 §User stories, §Success criteria)
  - Accept: hovering any station shows its name, its one-line description, its count and its 5 oldest runs; hovering any crate shows ref, kind, station, skipped stages, "already has" stages and work orders done/total at Implement, and an attention crate shows its reason; clicking a station or crate opens the pinned panel listing every run there (expandable to work orders), clicking a run lifts and outlines its crate, and Esc, ✕ or empty floor closes it. Walkthroughs 1, 3 and 8 of ux.md each complete on this repo's or mattbutlerengineering's page.

## Milestone 3: the replay

When this milestone is done, Play replays the repo's history down the
line and settles on today, honestly timed.

- [ ] **WO-0210** Transport bar — play, pause, day-snapping scrubber, speed, honesty line — size:M, blocked by: WO-0209 (PRD-0021 §User stories, §Success criteria)
  - Accept: the bar shows play/pause, a scrubber from `first_day` to today snapping to days, the date readout, a 30 s / 60 s toggle and the honesty line from ux.md; scrubbing to a day puts every crate where its `history` places it at that day's end, and the header, hover card and panel read "as of" that day with work-order rows marked "progress as of today"; the bar is disabled when there are no runs; walkthroughs 4 and 5 complete.
- [ ] **WO-0211** Replay motion — crates ride the belt through each day's arrivals — size:M, blocked by: WO-0210 (PRD-0021 §Success criteria)
  - Accept: during play, a run's arrivals within one day are spread evenly over that day in stage order, so a run whose artifacts share one date visibly visits each station; an `inferred` arrival shows the dashed shadow until the day closes; a crate rides straight through a skipped station; Implement trays show a neutral fill during play; the replay's last frame equals the page's opening snapshot (crate-by-crate comparison in the PR); walkthroughs 2 and 7 complete.
- [ ] **WO-0212** Frame-rate check — 60 fps with this repo's runs — size:S, blocked by: WO-0211 (PRD-0021 §Success criteria)
  - Accept: a replay of this repo's page at 30 s, measured with the browser's performance tools on a 2021-or-later laptop, holds about 60 frames per second throughout; the measurement and machine are recorded in the PR.

## Milestone 4: shipped as a skill, with the adopter clip

When this milestone is done, any repo owner can invoke the skill, and the
Owner can put a clip on a README that links to the page.

- [ ] **WO-0213** GIF export — the Export button and the in-page encoder — size:M, blocked by: WO-0211 (PRD-0021 §User stories, §Success criteria)
  - Accept: in `assembly_line.html`, pressing Export plays the replay at the fixed export size and frame rate and downloads an animated GIF built by the page's own encoder (no added library); the GIF committed to a pushed scratch branch and referenced from a README as an image autoplays and loops when that README is viewed on GitHub; an encode failure shows an on-page message and downloads nothing.
- [ ] **WO-0214** The assembly-line skill — `skills/assembly-line/SKILL.md` and its registrations — size:S, blocked by: WO-0213, WO-0204 (PRD-0021 §Actors, §User stories, §Success criteria)
  - Accept: the skill runs the tool two directories above itself, opens the page, stops with the tool's problem output on a nonzero exit, and walks Export plus `--publish` for the README (walkthrough 6 completes); it is in `protocol.UTILITY_SKILLS`, README.md, LEDGER.md and the plugin description; `python3 lint.py`, `python3 gates.py` and `python3 run_tests.py` pass, and `python3 factory_init.py update-manifest` is run if any mirrored file changed.

## Design gaps found

none.

## Notes

- The Owner-judged criteria (style match beside the references, the
  cold-viewer test, the Owner choosing it for a real presentation) and
  "the demo runs as written" are checked at Verify against the finished
  page, not as items here.
- No ADR item: ADR-0124 and its index row were written at Architect.
- Rows carry work-order ids WO-0198 to WO-0214 (the highest on main and
  every unmerged branch was WO-0197); no tracker issue is created for
  them in this stage (ADR-0032: rows first, mirror optional).
- 2026-11-05, WO-0199: completed runs are found by elimination, not a
  second `next_stage` walk: every `knowledge_plane.run_dirs` directory
  holding a run artifact that `board.gather` neither places nor flags is
  complete by orientation's own rule. `board._run_entry` and
  `board._reason` became public (`run_entry`, `reason`) and
  `board.run_identity` was extracted so the attention entry's ref, kind
  and slug have one owner; board's output is unchanged.
- 2026-11-05, WO-0201: history throwaway check over the real trees —
  this repo 107 runs (91 active, 16 completed), mattbutlerengineering 53
  (33 active, 20 completed), zero runs whose last arrival differs from
  their station; timelines 2026-07-05 → 2026-11-05 and 2026-08-15 →
  2026-11-05.
- 2026-11-05, WO-0203: three.js v0.187.0's npm package ships no
  `.min.js` builds (its `build/` holds `three.module.js` and
  `three.core.js`); the 814 KB figure in ADR-0124's Consequences and in
  architecture.md was jsDelivr's on-the-fly minification, not the
  release. `vendor/three/` holds the release files byte-identical from
  the npm tarball (2,133,699 bytes, 417 KB gzipped) with its LICENSE,
  and a written page is about 3 MB. The decision is unchanged, so no new
  ADR; WO-0205's Accept is read with these two file names. The vendor
  files landed with WO-0203 because `main` reads them; WO-0205 still
  owns NOTICE, the npx bundle and the in-page loading.
- 2026-11-05, WO-0203: checked in headless Chromium with WebGL stubbed
  off — notice shown, twelve station lists plus Needs attention, 107
  list items for 107 runs, a page with `timeline` removed names it in
  the notice; the network log holds only the page (and the browser's
  own favicon probe).
- 2026-11-05, WO-0204: this repo — 107 runs listed once each (91 active,
  equal to `board.py`'s 91 `runs`; 16 completed; 0 attention).
  mattbutlerengineering — 53 runs listed once each (33 active, equal to
  `board.py`'s 33; 20 completed), including the phantom product run
  `docs` at Idea; four `docs/fixes/` directories hold no run artifact
  (`design.md` or `finding.md` only) and are not runs, as board agrees.
