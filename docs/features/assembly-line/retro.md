---
stage: operate
run: feature:assembly-line
date: 2026-11-09
users-observed: 1
signal-source: "A scan on 2026-11-09 of the Owner's local agent session transcripts, for tool calls naming the assembly-line tool, page or published URL after the squash-merge (2026-11-06T17:08Z), window 2026-11-06T17:08Z to 2026-11-09T20:43Z, the newest event in the omp store (the Claude Code store ends 2026-11-09T05:10Z). Two stores: the Claude Code projects directory for this machine's user and the omp session store. 25 transcript files matched: 14 in the Owner's second repo (3 top-level sessions and 11 subagent transcripts), 10 in this repo and 1 with a single mention in a third. The one person is the Owner; the 10 in this repo are maintenance of it, not use. Plus `gh issue list --state all --search 'assembly line'` for issues created after the merge. One account, one machine; nobody else's use is visible."
---

# Retro: An animated assembly line of every run in the repo, with a history replay

## Read this first: days, one person

The run merged on 2026-11-06 (PR #1168, `9804284`) and this retro is written on
2026-11-09, three days later. It reflects days of use by one person, the Owner,
who also wrote the idea. Almost all of what happened after the merge is this
repo polishing its own page, which is the repo's own work and not users. The
only use that is not maintenance is the Owner putting the page in a second
repo of his own on 2026-11-09 (and a first attempt there on 2026-11-07).
`users-observed` is therefore 1, and it is the author. No cold viewer, no
adopter and nobody outside this machine is observed, and the scan cannot see
them: a scan limit, not a finding that nobody used it.

## Population

Counts only, from the scan in `signal-source`:

| Measure | Count |
|---|---|
| Transcript files matching, after the merge | 25 |
| Sessions in the Owner's second repo that used or built around the tool | 3 (one omp session on 2026-11-09, two Claude Code sessions on 2026-11-07 and 2026-11-09, the first with 11 subagent transcripts) |
| Runs of `assembly_line.py` itself in that repo, 2026-11-09 | 4 (help, one publish, two page writes), pattern-counted |
| Transcript files in this repo that touched the tool, page or published URL | 10 (stage runs, the Operate runs, one long polish session), the repo's own work |
| Tool errors in those sessions (a problem string or traceback in a result) | 0 |
| Workarounds in the second repo | 3: a symlink to give a worktree a different directory name, because the page names the repo from the directory (`board.py` line 94); diffing the installed plugin copy against a fresh clone and updating it before running; apparently, a repo-side generator step and a CI step that fetch the tool pinned to a commit (2026-11-07) instead of using the installed skill (read from the edits, not confirmed) |
| Complaints in a session, said to the agent | not counted; the Owner's complaints reached the tracker (next row) |
| Issues about the page created after the merge | 213 (211 titled "Assembly line:" plus the Pages-publish and plugin-release issues), 0 open on 2026-11-09; created 2026-11-06 to 2026-11-08 |

Who filed the 213: all from the Owner's account, in a two-day run (62 on
2026-11-07, 150 on 2026-11-08). Their bodies read as inspection findings (a
CDP pass, an axe-core pass, WebKit and phone viewport sweeps, a screen-reader
pass), one reads "Owner direction". They are not a crowd; they are one
person's agents exercising the page, so they are evidence of what the page does
under inspection, labelled below as a single-source pattern.

None of the 213 cites `review.md` or `verification.md`, and none was created
before the merge, so none is the run's own debt (the PRD's "The Operate
population" rule). #1167, the closing target Ship opened, was created five
minutes before the merge and is the run's own.

## Outcomes vs. intent

### No setup, any repo (PRD criterion 1; idea.md's "one skill invocation with no setup")

- What happened: the tool wrote pages in this repo and in the second repo at
  Verify (`verification.md` §No setup, any repo). After the merge the Owner took
  it into the second repo on 2026-11-09: it ran there, produced a page, and
  he published it through that repo's own CI. It was not setup-free in practice:
  the installed plugin copy had to be refreshed, the page named the repo from
  the directory name (a worktree gave the wrong name, worked around with a
  symlink), and the page had to be wired into an existing Pages-publishing
  workflow by hand (the skill's publish step covers a repo whose Pages serves
  `docs/`).
- Signal strength: anecdote (one person, two repos). It runs; it is not zero-setup.

### Complete and exact (PRD criterion 2)

- What happened: state at ship, `verification.md` PASS (107 runs and 53 runs
  placed once, `board.py` agreeing). Afterwards the tracker holds placement-adjacent
  findings, not a placement error: unreadable runs missing from the header
  summary (#1270), the attention bin having two names and claiming an order (#1390),
  amber crates vanishing into the amber bin (#1560), stale mid-replay header
  counts (#1360, #1364). All closed.
- Signal strength: pattern, single source (the Owner's inspection passes).

### Completed is its own bucket; hover explains (PRD criteria 3 and 4)

- What happened: the bucket became a city of one building per completed run
  (#1216, "Owner direction"), a design change the PRD did not describe, so what
  shipped is not what Verify tested. Hover findings followed: hover cards sliding under the
  legend and the panel (#1342), going stale while the replay moves (#1366, #1516), a
  building described as a crate (#1284). The "shipped, awaiting a retro" line the
  Review deferred (a minor in `review.md`) is not among them.
- Signal strength: anecdote for the city (one explicit direction); pattern, single source, for the hover findings.

### Replay and replay honesty (PRD criteria 5 and 6)

- What happened: pacing is where the findings cluster: crates teleporting between
  stations (#1264, #1266), half the replay showing days where nothing happens
  (#1308, #1410), a trace too fast to follow (#1378) and too long after the story
  ends (#1256), the clip's stamp day (#1252). The replay's last frame equalling the snapshot, the
  criterion Verify tested, is not what any of them is about.
- Signal strength: pattern, single source.

### Style match, cold-viewer test, the Owner would show it, the demo runs as written (PRD criteria 7, 9, 10, 12; idea.md's presenter and cold-viewer halves)

- What happened: all four are still NOT RUN. Nothing was recorded since Ship: no
  verdict beside the three reference images, no three cold viewers, no named
  presentation occasion, no run of the three-step demo as written. What exists is
  indirect: the Owner has published the page, opened 213 issues on it, opened #1200,
  whose body cites the open cold-viewer criterion, and adopted it in a second repo. That is investment, not the recorded choice the
  criterion asks for, and nothing here marks any of the four passed.
- Signal strength: unobserved for all four.

### Moving parts, smoothly (PRD criterion 8)

- What happened: the 60 fps visible-window measurement stands alone. After
  the merge: tiny belt parts costing a third of every frame (#1420), an idle page
  drawing at display rate forever (#1230), and every station's machine moving
  whether or not it has work (#1428), which sits against the criterion's
  "every station has at least one continuously animated mechanism". Whether
  the PRD's criterion or the later fix wins is the Owner's.
- Signal strength: pattern, single source.

### Adopter clip (PRD criterion 11)

- What happened: findings on the exported clip after the merge: it weighs
  6.4 MB (#1184), teleports crates (#1266), keeps ghosts of earlier frames
  (#1556), signs too small to read (#1368). GitHub autoplay of the committed GIF
  was never re-checked after Verify ("prior evidence only").
- Signal strength: pattern, single source; the autoplay claim is unobserved.

### idea.md's success sentence

- What happened: three halves. "Every run exactly once, no setup, in both repos":
  met in this repo and the second at Verify, and the second repo ran it on
  2026-11-09 with the workarounds above. "The Owner picks it over the old board
  to show the factory": not recorded. "Someone who has never seen the factory
  can name the stages within 30 seconds": not tested. The sentence stands half measured.
- Signal strength: unobserved for the second and third halves.

## Open debt

The run's own debt. None of it is feedback and none counts toward the population.

- #1167 — the closing target Ship opened (a tracker record, created before the merge).
- The deferred minors in `review.md` (crate hover at Operate, the honesty line's
  wording, headless frame-rate dips): no issue was opened for them; the
  later issues overlap them without citing them.
- The four NOT RUN criteria and the GitHub autoplay check, carried forward by the Owner's
  decision at Verify and Review.
- #1617, #1688 — the Operate backlog issue and this stage's own tracking issue, filed after the merge and about the missing retro, not feedback on the page.

## Run retrospective

Stages: Idea 2026-11-05, Verify, Review and Ship on 2026-11-06 under one autorun brief,
seventeen work orders (WO-0198 to WO-0214), one ADR (0124), 4080 tests green at ship.

- Keep: the autorun brief's honest carry of the four human criteria as NOT RUN, not
  passed: Verify and Review never marked one passed and Ship listed them as the open
  quality bar, so this retro can say they are open and not wonder. Keep Review's
  security pass on the page (no `innerHTML`, model as `application/json`, `</`
  escaped): 213 later issues and none is an injection. Keep the vendored-library
  decision with the real size from the tarball in ADR-0124 (the 814 KB figure was
  caught at Implement, not at Ship).
- Change: a presentation surface that ships with every human criterion open and every
  machine criterion green gets its defects found afterwards in bulk: 213 issues in
  two days, from one person's inspection passes (keyboard focus, contrast, phones,
  dark mode, forced colours, WebKit). Most are the kind an automated pass names, so
  a pass of that kind belongs inside Verify for a UI that is the deliverable, not
  after the merge. Also set the success measure for the human criteria before
  Ship: a named occasion and a date, so "would show it" can be answered.
- Stop: reading a green machine verdict as "the page is ready to show". The
  presenter criteria were the point, and they were exactly the ones not run.

## Environment

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| `assembly_line.py` raised a traceback on an unwritable `--out` or `--publish`, against AGENTS.md's problem-string contract; only Review found it | `review.md` §Major, fixed in `47dba2d` | mechanical | `tests/cli_contract.py`, the shared CLI contract suite: add a pin that every tool taking an output path reports a problem string and exits 1 on an unwritable one. Today it pins only the summary line and a usage error, so a new tool passes it with a raising write |
| A run slug or work-order title spelling a slot name corrupted the page (`render` replaced slots in sequence); found by Review reading `render` | `review.md` §Minor, fixed in `47dba2d` | mechanical | `tests/test_assembly_line.py`, which now holds `test_slot_names_inside_the_model_are_data_not_slots`; the missing carrier was a property test over every slot name at Implement, since the template's slots are enumerable |
| WCAG contrast failures, a missing `main` landmark, no `color-scheme`, an unnamed canvas and unnamed controls reached the merged page and were found by later passes (#1210, #1346 to #1350, #1404, #1482) | the 213 issues; `review.md` §Domain passes read `lang`, `aria-label` and Escape handling by eye | mechanical | `tests/test_assembly_line.py`: static pins on the written page (a `<main>`, a `color-scheme` declaration, a named canvas) and a contrast ratio computed from the palette table. No existing check or CI job opens the page at all; the page's behaviour is guarded by no hook and no CI job, which is a finding, not the baseline |
| Verify and the later polish passes tested one engine (Chromium; #1214 counts nineteen passes); WebKit's missing `dblclick` on touch (#1526) and engine support unrecorded (#1214) surfaced after the merge | `verification.md` assumptions (Chrome 150 only); #1214, #1526 | judgement | `skills/verify/SKILL.md`: a UI deliverable names the engines it claims and records the ones not run. A cross-engine run needs a browser matrix no existing job provides |
| ADR-0124's first draft carried an 814 KB figure from a CDN's on-the-fly minification that the release does not ship (the real size is 2.1 MB), caught at Implement | `breakdown.md` Notes (WO-0203) | judgement | `skills/architect/SKILL.md`: a size or count an ADR rests on names the command that measured it. Not a mechanical check; the figure is a claim about an outside artifact |
| The page names the repo from the directory name, so a worktree or temp checkout is mislabelled; the Owner symlinked around it on 2026-11-09 | the 2026-11-09 consumer session (scan above); `board.py` line 94 | mechanical | `tests/test_assembly_line.py`: a fixture that runs the tool from a directory whose name is not the repo's and pins the name source; the carrier is a `--name` flag or the git remote, decided by the seed below |

## Idea seeds

- Run the four human criteria for the assembly line, or retire them with a recorded reason: show the page cold to three people who have not seen the factory and time the stage naming, line the page up beside the three reference images, and name one presentation occasion, then record it as an addendum to verification.md (from: feature:assembly-line)
- Re-run the Operate scan one week after 2026-11-09, counting sessions outside this repo's own maintenance, runs of the tool in other repos, workarounds and any occasion the page was shown, and record the counts in a follow-up retro (from: feature:assembly-line)
- Add a pin to `tests/cli_contract.py` that every root tool taking `--out` or `--publish` reports a problem string and exits 1 on an unwritable target, so a raising write fails CI (from: feature:assembly-line)
- Pin the page's static accessibility facts in `tests/test_assembly_line.py`: a `<main>` landmark, a `color-scheme` declaration, an accessible name on the canvas, and contrast ratios computed from the COLORS table against the 4.5:1 and 3:1 thresholds (from: feature:assembly-line)
- Add a smoke step to `.github/workflows/pages.yml` that loads the built page in headless Chromium and fails on a console error or a page with no canvas and no fallback list (from: feature:assembly-line)
- Name the repo on the page from `--name` or the git remote, not the directory name, so a worktree or temp checkout is not mislabelled, and say so in skills/assembly-line/SKILL.md (from: feature:assembly-line)
- Add a consumer section to skills/assembly-line/SKILL.md for a repo whose Pages already publishes through a workflow, and for refreshing a stale installed plugin copy before running, since the 2026-11-09 adoption did both by hand (from: feature:assembly-line)
- Decide whether the PRD's "every station's mechanism moves continuously" or the later idle-motion fix (#1428) wins, and record the choice in prd.md or an ADR so the criterion and the page do not contradict (from: feature:assembly-line)

## Run complete

Closed 2026-11-09 on three days of use by one person, population 1 observed (the
Owner, in a second repo). Every outcome above reads `unobserved`, anecdote or a
single-source pattern, and the four human-judgement criteria stay open. The seeds
above are the input to the next Idea-stage run; the first useful one is the
cold-viewer and presentation record, which is the part of the success sentence
nothing has measured.
