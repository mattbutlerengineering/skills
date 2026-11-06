---
stage: verify
run: feature:assembly-line
date: 2026-11-06
assumptions:
  - "The Owner's autorun brief (2026-11-06) decides the four human-judgement criteria: Verify records them as NOT RUN, with the reason, and the run continues through Ship; none is marked passed."
  - "Browser checks ran in Google Chrome 150 (headless, a dedicated profile) driven by the omp browser tool, pages served from a throwaway local http.server on 127.0.0.1; the visible-window frame-rate run used the tool's shared Chromium (ANGLE Metal, Apple M1 Pro) before that browser stopped delivering animation frames, so it is the only visible-window measurement."
  - "Run counts are the working tree's on 2026-11-06 (107 runs here: this run now sits at Verify); PRD-0021's '106 runs' was the count when it was written."
---

# Verification: An animated assembly line of every run in the repo, with a history replay

## Summary

PRD-0021 has 12 success criteria: 8 PASS (machine-checked this stage), 0
FAIL, 4 NOT RUN. The four NOT RUN criteria are the human-judgement ones the
Owner chose to carry forward: **Style match**, **Cold-viewer test**, **The
Owner would show it**, and **The demo runs as written**. They are unknown,
not passed, so this verdict is "every machine-checkable criterion passes;
the quality bar is still open" and never "all criteria pass". One further
sub-claim is unconfirmed this stage: the GIF autoplaying inline on
github.com (**Adopter clip**) rests on WO-0213's earlier push, not re-run
here (see Not verified). The breakdown's 17 Accept lines (WO-0198 to
WO-0214): 17 verified by suite or live check, 0 failed; the parts of them
that are screenshots or recordings attached to a pull request are not
re-created here. Suite: `run_tests.py` 4078 tests, lint, kb drift, gates and
the gates selftest all report 0 problems.

## Criteria & evidence

### Suite, lint, drift, gates (every item's regression floor)

- Check: ran the four repo checks at the worktree root.
- Evidence:
  ```
  $ python3 run_tests.py | tail -1
  tests: 4078 tests across 131 modules in 26.8s on 8 workers, 0 problem(s)
  $ python3 lint.py
  lint: 0 problem(s) across 36 skills
  $ python3 kb.py drift
  drift: 0 problem(s)
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS

### PRD: No setup, any repo

- Check: ran `python3 assembly_line.py` in this repo and in
  `~/github/mattbutlerengineering` (it already had uncommitted changes
  that are not mine; the tool wrote only to /tmp, a read-only run of
  that tree), nothing installed or configured first (the tool is stdlib
  Python plus the committed page and `vendor/three/`). Also `--publish`
  and a root with no `docs/`.
- Evidence:
  ```
  $ python3 assembly_line.py --out /tmp/al-verify-skills.html
  /private/tmp/al-verify-skills.html            (exit 0)
  $ (cd ~/github/mattbutlerengineering && python3 .../assembly_line.py --out /tmp/al-verify-mbe.html)
  /private/tmp/al-verify-mbe.html               (exit 0)
  $ python3 assembly_line.py --publish /tmp/al-pub
  /private/tmp/al-pub/index.html                (exit 0; 3,063,324 bytes)
  $ python3 assembly_line.py /tmp/al-nodocs
  board: /tmp/al-nodocs has no docs/ tree
  assembly_line: 1 problem(s)                   (exit 1; nothing written)
  ```
  The page loaded in Chrome 150 with exactly one network request, for the
  file itself (`GET http://127.0.0.1:8765/al-verify-skills.html 200`).
- Result: PASS

### PRD: Complete and exact

- Check: parsed each written page's inlined model; compared it with
  `board.py`'s JSON run for run (station and ladder for every active run),
  checked each run directory appears once, and compared each Implement
  run's work orders with its `breakdown.md` checkbox rows.
- Evidence:
  ```
  skills model runs 107 unique dirs 107 dups [] active 91 board runs 91 completed 16 attention 0 board attention 0
  skills states {'done': 539, 'current': 91, 'skipped': 124, 'ahead': 18} mismatch 0 []
  skills completed runs all have retro: True 16
  mbe model runs 53 unique dirs 53 dups [] active 33 board runs 33 completed 20 attention 0 board attention 0
  mbe states {'done': 196, 'current': 33, 'skipped': 27, 'ahead': 38} mismatch 0 []
  mbe completed runs all have retro: True 20
  (no PART MISMATCH lines: every Implement run's work orders equal its breakdown rows, done count included)
  last-arrival!=station: [] (both repos)
  ```
  The 107 run directories on disk under `docs/features/*` and
  `docs/fixes/*` equal the 107 model runs. mattbutlerengineering's
  phantom product run is present as placed (`product idea` at Idea,
  `ref` product, dir `docs`). Page parts: in mattbutlerengineering,
  hovering `ui-quality-loop`'s and `venue-scoped-routes`'s crates is
  consistent with the model (`maintenance:venue-scoped-routes` 33 rows, 31
  done; its `breakdown.md` holds 31 checked and 2 open rows).
- Result: PASS

### PRD: Completed is its own bucket

- Check: from the same models: every `station: completed` run has a
  `retro.md` carrying `users-observed` or neither field; no `operate`
  run has a `retro.md`; the fallback page and the factory's Completed
  tile counts equal the model.
- Evidence:
  ```
  skills completed runs all have retro: True 16
  skills operate runs with retro.md present (should be incomplete ones only): 0
  mbe completed runs all have retro: True 20
  mbe operate runs with retro.md present (should be incomplete ones only): 0
  skills per station: {'verify': 1, 'operate': 75, 'completed': 16, 'implement': 15}
  hover OPERATE:   "Shipped, waiting on a retro.  75 runs"
  hover COMPLETED: "Finished runs: retro written, on the shelves.  16 runs"
  ```
  Reading note: the "shipped and awaiting a retro" label is on the
  Operate station's hover text; a crate's own hover at Operate does not
  repeat it (`maintenance · at Operate`, dir, skipped stages). I read the
  criterion as the station label and recorded the gap for Review.
- Result: PASS

### PRD: Hover explains

- Check: swept the mouse over this repo's factory page (1440×900) and
  recorded every distinct card; swept mattbutlerengineering's for a crate
  with work orders.
- Evidence:
  ```
  IMPLEMENT  Assembles the parts: the code, work order by work order.  15 runs · as of 2026-11-06  oldest: a-broken-taxonomy-passes-the-gate, ...
  VERIFY     Scans the build against the PRD's criteria.  1 run · as of 2026-11-06  oldest: assembly-line
  CAPTURE / IDEA / PRD / UX DESIGN / ARCHITECT / DECOMPOSE / REVIEW / SHIP / OPERATE / COMPLETED / NEEDS ATTENTION: each card showed name, one-line description and count (all 12 stations plus the bin, 54 distinct cards in the sweep)
  CRATE: MAINTENANCE:A-BROKEN-TAXONOMY-PASSES-THE-GATE  maintenance · at Implement  docs/fixes/...  skipped: Architect, Decompose  already has: Verify, Review, Ship
  CRATE: MAINTENANCE:VENUE-SCOPED-ROUTES (mbe)  maintenance · at Implement · 31/33 WOs
  ```
- Result: PASS

### PRD: Replay

- Check: scrubbed this repo's page to 2026-09-01 and compared every
  crate with the model's history; pressed Play, paused (date held), resumed
  and let the 30 s replay finish; compared all 107 crates' visibility,
  position and station after the last frame with the opening snapshot. The
  per-arrival dating rules (first artifact, stage-completing artifact,
  Implement's span, inferred same-day arrivals) are pinned by
  `tests/test_assembly_line.py` in the 4078-test run above, not by this
  browser sweep.
- Evidence:
  ```
  SCRUB 2026-09-01: {"day":"2026-09-01","meta":"49 active · 8 completed · as of 2026-09-01","bad":0,"vis":57}
  mid-play: { day: '2026-07-18', play: '❚❚ Pause', playing: true }
  paused: {"day":"2026-07-18","playing":false,"play":"▶ Play"} {"day":"2026-07-18","playing":false}
  end: {"playing":false,"day":"2026-11-06 (today)","meta":"91 active · 16 completed · as of 2026-11-06","crates":107,"diffVsOpening":0}
  day readout while playing: 2026-07-09, 07-14, 07-18, ... 09-02, 09-06 ... (monotonic)
  ```
- Result: PASS

### PRD: Replay honesty

- Check: read the page's transport footer.
- Evidence:
  ```
  Dates to the day from artifact frontmatter; order within a day is inferred; work-order progress is today's.
  ```
  (It says the order is inferred; it does not add "from stage order" as the
  PRD's wording does. The inferred arrivals show a dashed shadow, per
  WO-0211, seen in the earlier run's notes, not re-checked here.)
- Result: PASS

### PRD: Style match

- Check: not run. Needs the Owner's eye on the page beside his three
  reference images (true isometric view, outlined flat shading,
  green/grey/purple, one tile per stage).
- Evidence: none. The page opens as a pale-green ground with grey
  plates and machines, green belts and purple accents (screenshot taken
  this stage, not a verdict on style match).
- Result: NOT RUN — human judgement; the Owner decided to carry it to
  Review and Ship.

### PRD: Moving parts, smoothly

- Check: (a) in Chrome 150 headless on this repo's page, sampled every
  scene object's world matrix and material colour 650 ms apart and
  bucketed the changes by nearest station tile; emulated
  `prefers-reduced-motion: reduce` and repeated. (b) Frame rate: the
  page's own per-second `requestAnimationFrame` counter through a full 30 s
  replay of this repo's 107 runs, on this machine (MacBookPro18,3, Apple
  M1 Pro, 16 GB, 2021).
- Evidence:
  ```
  normal:  {"reducedMotion":false,"total":520,"counts":{"capture":31,"idea":22,"prd":48,"ux-design":63,"architect":79,"decompose":46,"implement":56,"verify":30,"review":38,"ship":50,"operate":40,"completed":16,"bin":1}}
  reduced: {"reducedMotion":true,"total":0,"counts":{}}
  visible Chromium window (ANGLE Metal, Apple M1 Pro), 30 s replay, 31 samples:
  [60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60]  min 60 mean 60.0
  hidden headless Chromium (same machine, load average 5.3), 30 s replay, two runs:
  run 1: 35 samples, min 32.9, mean 54.2
  run 2: [61,60,57,59.5,...,58.5,59,58.5,47.2,48,46.8,41.9,46.6,39.7,52.6,50.6,51.6,60]  min 39.7, mean 55.9
  ```
  Every station tile has changing objects (bucketing by nearest tile is
  approximate), and reduced motion freezes all of them. The visible run
  holds 60 fps throughout; the two hidden-headless runs dip to 33 to 40 fps
  in the late replay, a background-rendering context that is not what the
  criterion measures. I did not re-measure the visible window afterwards:
  that browser stopped delivering animation frames for the rest of the
  stage (rAF ticks 0 in 1.5 s), so there is one visible-window measurement,
  and the dips are recorded rather than dismissed.
- Result: PASS

### PRD: Cold-viewer test

- Check: not run. Needs 3 people who have never seen the factory, each
  watching the replay for up to 30 s.
- Evidence: none.
- Result: NOT RUN — human judgement; carried forward by the Owner's decision.

### PRD: The Owner would show it

- Check: not run. Needs the Owner's choice of this page over the old
  board for a real presentation, and the occasion recorded.
- Evidence: none.
- Result: NOT RUN — human judgement; carried forward by the Owner's decision.

### PRD: Adopter clip

- Check: pressed Export clip on this repo's page in Chrome 150; decoded the
  downloaded blob with `ImageDecoder`; forced `getImageData` to throw and
  pressed Export again; read the skill's README steps and the tool's
  `--publish` output.
- Evidence:
  ```
  Clip exported (4.6 MB). Commit it and reference it from your README as an image.
  {"size":4817352,"head":"GIF89a","w":720,"h":450,"loopExt":true,"frames":141,"err":null}   repetitionCount: Infinity
  {"status":"Export failed: simulated encoder failure. Nothing was downloaded.","downloads":0,"exportDisabled":false,"playDisabled":false}
  skills/assembly-line/SKILL.md §3: "[![The assembly line](https://raw.githubusercontent.com/OWNER/REPO/main/docs/factory/REPO-assembly-line.gif)](https://OWNER.github.io/REPO/factory/)"
  ```
  An animated image format, looping forever, the README line links it to
  the published page. That github.com renders it inline-animated is
  WO-0213's recorded push to `scratch/assembly-line-gif-check` (since
  deleted); this stage did not push, so that part is prior evidence.
- Result: PASS (export, loop and README line); the GitHub autoplay is
  prior evidence only, see Not verified

### PRD: The demo runs as written

- Check: not run as written; that needs the Owner opening the factory and
  following the three steps. The machine-visible parts were exercised above
  (every run at its station with the Operate pile of 75; Play moves
  crates to Completed with the last frame equal to the snapshot; hover
  names each station and its items).
- Evidence: none for the run as written.
- Result: NOT RUN — human judgement; carried forward by the Owner's decision.

### Breakdown Accept lines not already a PRD criterion

- WO-0198, WO-0200, WO-0202: the cases exist and pass; `tests/test_assembly_line.py` holds 26 test methods and runs inside the 4078.
- WO-0199, WO-0201: `gather`, `history`, `timeline` pass those cases; on the real trees `last-arrival!=station: []` for both repos (above); `assembly_line.py` carries no stage-order literal (pinned by the suite).
- WO-0203: with WebGL stubbed off in Chrome 150 (`getContext` returns null for webgl), both repos' pages showed the notice and the lists:
  ```
  skills: notice "This browser cannot draw the factory (no WebGL), so it shows a plain list of every run by station."  sections Capture:0 Idea:0 PRD:0 UX Design:0 Architect:0 Decompose:0 Implement:15 Verify:1 Review:0 Ship:0 Operate:75 Completed:16 Needs attention:0  li 107  canvas 0  requests: only the page
  mbe:    sections Capture:1 Idea:2 PRD:0 UX Design:0 Architect:0 Decompose:0 Implement:2 Verify:3 Review:0 Ship:3 Operate:22 Completed:20 Needs attention:0  li 53
  ```
  The missing-key notice is pinned by the suite; not re-driven in a browser here.
- WO-0204: both repos' counts equal `board.py`'s (91 and 33), shown above.
- WO-0205: `vendor/three/` sha256 equals the npm tarball's `three@0.187.0` (`npm pack` this stage): `three.core.js` 613e370f…d78578, `three.module.js` 104f5614…ee341, LICENSE 8b378ebe…b5bc, identical; NOTICE names it; `npx_bundle.py` lists `assembly_line.html` and `vendor/`; the page makes no network request.
- WO-0206, WO-0208: screenshot of this repo's page shows twelve plates labelled, one belt, the Capture side belt, the warehouse and the orange bin; count tags 75 / 1 / 15 / 16 equal Operate, Verify, Implement, Completed; the Operate pile is the tallest.
- WO-0207: all 12 stations animate and reduced motion opens still (see Moving parts).
- WO-0209: hover card shown; the click-to-pin panel, run lift and Esc were not re-driven here (WO-0209's notes record them).
- WO-0210, WO-0211: scrubber bounds `20639` to `20764` (2026-07-05 to 2026-11-06), 30 s/60 s buttons present, "as of" header after scrubbing, last frame equals the snapshot (above); the dashed-shadow and skipped-station ride were not re-driven here.
- WO-0212: measured above (60 fps visible window).
- WO-0213: export decoded, loops, failure path (above).
- WO-0214: the skill file exists; `assembly-line` is in `protocol.UTILITY_SKILLS` (printed `True`), README.md's table, LEDGER.md (row `assembly-line | draft`) and the plugin description; the only `plugin.json` change against the merge-base is the description (version untouched, ADR-0095); lint, gates and `run_tests.py` pass (top of this file).
- Result: PASS

## Failures

none among the machine-checkable criteria. Observations routed to Review,
not failures:

- Crate hover at Operate does not say "shipped, awaiting a retro"; only the
  station hover does (Completed is its own bucket).
- The honesty line says order within a day is "inferred" but does not name
  stage order.
- Hidden-headless frame rate dips to 33 to 40 fps late in the replay
  (visible window held 60), so the visible-window measurement stands alone.

## Not verified

- Style match, Cold-viewer test, The Owner would show it, The demo runs as
  written: human-only, recorded NOT RUN above by the Owner's decision to
  continue through Ship. Review and Ship carry them as the quality bar
  still open.
- The GIF autoplaying on github.com: needs a push to a scratch branch; this
  stage does not push. Evidence is WO-0213's note from 2026-11-05 only.
- Click-to-pin panel, crate lift and Esc (WO-0209), the dashed inferred
  shadow and the skipped-station ride (WO-0211), and the missing-key
  fallback notice in a browser: no machine check was re-run this stage
  beyond the suite.
- A second visible-window frame-rate run, and a measurement on any other
  2021-or-later laptop.
- Screenshots and recordings WO-0206 and WO-0207 attach to the pull request:
  created at the pull request, not in this stage.
