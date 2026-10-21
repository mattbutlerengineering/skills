---
stage: decompose
run: feature:decompose-lessons
date: 2026-10-20
assumptions:
  - "No live review of the cut: autorun-brief.md holds Owner decisions 1-3 (what to drive, pair source, prepare-and-stop release) and says nothing about milestones or sizing. Milestone boundaries and sizes are the skill's own defaults: each milestone independently demonstrable, one item per sitting, vertical slices where the architecture allows. Milestone 1 is the lesson operations and the file (the invariants, no git). Milestone 2 is pair derivation. Milestone 3 is voting and the single-writer update. Milestone 4 is the comparison and the front door. Milestone 5 is the Decompose skill read step, the docs and the whole-repo verify."
  - "Test-first ordering follows the repo's TDD rule: each implementation item is blocked by a tests item whose Accept says its cases run and fail against the tree before the implementation lands."
  - "No work-order ids and no tracker markers: the brief says issue 988 seeds the run, no work order is mirrored, and detectors C and I scan every markdown file. Items carry short labels (S1, S2, ...) at the start of the bold span, the form size-band-calibration used. Fixture run refs and lesson ids are built in the test file, not written here, and no sample lesson id appears in this file."
  - "Dual-membership pin placement, derived from ADR-0113 and ADR-0112: the pin moves in the item that first adds each import. S4 adds cli, S12 adds factory_config, so the set grows 50 to 51 to 52 one pair per item. decompose_signals is root-only and crosses nothing, so S6 edits no pin. S18 asserts the final count of 52 pairs."
  - "Derived, not stated: the tool is built as one module, decompose_lessons.py, in the order lesson operations, file, pairs, votes and update, comparison, front door, because architecture.md lists the components as pure functions with the front door last. All tests go in tests/test_decompose_lessons.py unless an item says otherwise, with a fixture record list, a temp dir and an injected git runner, as architecture.md's Stack section says."
  - "Skill change handling, from ADR-0095 and architecture.md: the SKILL.md step lands in its own tests-then-edit pair, lint.py is re-run after editing it, and no item touches .claude-plugin/plugin.json; the wave's release PR bumps it. The final verify checks that skills/ edits are limited to skills/decompose."
  - "No design gap found, so nothing is routed to Architect. Architecture.md's pair rule, lesson identity, vote step, treated definition, file shape, output strings, exit codes and floor owner are specific enough to write acceptance lines from."
---

# Breakdown: A ranked lessons file for Decompose

Progress lives in the checkboxes below. Implement checks items off as their
acceptance criteria are met. Every implementation item is blocked by the
tests item that pins it. All tests go in `tests/test_decompose_lessons.py`
unless an item says otherwise, and they run through the public interface
with a fixture record list and an injected git runner (architecture.md,
Stack).

## Milestone 1: lessons are added, edited, voted and removed, and the file round-trips

When this milestone is done, `decompose_lessons.add`, `edit`, `upvote`,
`downvote`, `load` and `dump` keep the lesson invariants over a JSONL file
on fixture lessons alone, with no git and no run records.

- [x] **S1 Lesson operation tests** — cases for `add`, `edit`, `upvote` and `downvote` over fixture lesson lists — size:M
  - Accept: the module holds these cases, each asserting exact values and that the input list is not mutated. ADD with no source run returns the original list and the problem `decompose-lessons: add refused: <id> cites no source run`. ADD with sources returns a new list holding the lesson at importance 2 with its sources and an empty `voted`. UPVOTE takes 2 to 3 and DOWNVOTE takes 2 to 1, each leaving `sources` intact. DOWNVOTE from 1 removes the lesson from the list, and a lesson at 1 left alone remains; no lesson is stored below 1. A vote or EDIT naming an unknown id returns the original list, the problem `decompose-lessons: <op> refused: no lesson <id>`, and creates nothing. EDIT changes text and keeps importance, sources and `voted`; an EDIT that would leave no source run is refused like an ADD. Before the module exists the test module fails on import.
  - Blocked by: —
- [x] **S2 Lesson operations** — root-level `decompose_lessons.py` with `add`, `edit`, `upvote` and `downvote` as architecture.md's Lesson operations describes — size:M
  - Accept: the S1 tests pass. Each function is pure over a list and returns `(new_list, problems)`; none raises on a bad id. The module imports only the standard library and is not in `factory_init.MIRRORS`. The module docstring's first line states what it does.
  - Blocked by: S1 Lesson operation tests
- [x] **S3 File tests** — cases for `load` and `dump` over temp files — size:M
  - Accept: the module holds these cases. A file with a `{"seen": [...]}` first line and lesson lines round-trips byte-identically through `load` then `dump`, lessons sorted by id and `seen` sorted. A malformed line, a lesson with no sources, a duplicate id and an importance below 1 each give a problem naming the line number and nothing is written. A missing file loads as no lessons and no `seen`. `dump` writes the whole file through a temp file and `os.replace`, asserted by a failing replace leaving the original file byte-identical. A write whose list is empty and whose `seen` is empty creates no file. Before `load` and `dump` exist the cases fail.
  - Blocked by: S2 Lesson operations
- [x] **S4 File** — `load` and `dump` as architecture.md's File describes — size:S
  - Accept: the S3 tests pass and every earlier test still passes. The file is read through `cli.read_file`, with no retyped guarded-read logic. `tests/test_dual_membership.py`'s pin gains `(decompose_lessons, cli)`, its pair-count comment reads 51, and the test passes.
  - Blocked by: S3 File tests

## Milestone 2: contrast pairs are derived from measured runs

When this milestone is done, `decompose_lessons.pairs` turns a list of run records into contrast pairs of a hit run and a clean run of the same kind and label, for the three signals only, and the lesson each pair collapses to has a derived id and text.

- [x] **S5 Pair derivation tests** — cases for `pairs` and the lesson each pair collapses to, over a fixture record list worked by hand — size:M
  - Accept: the module holds these cases, each asserting exact values with the expected pairs computed by hand in the test, none copied from the tool. Each measurable hit run on re-plan, design gaps or review-traced is paired with the first clean run in run-path order whose run-ref prefix (feature, maintenance, product) and observed-or-inferred label equal the hit run's. A hit run with no clean run of its kind and label yields no pair. An unmeasurable run is never hit and never clean. A fixture history that also holds a band miss and a retro note produces no pair and no lesson citing either. The detail is the largest of added, dropped, split, merged with ties in that order for re-plan, `routed` for design gaps and `named` for review-traced; two pairs with the same id collapse to one lesson holding both sources. The text is the fixed template over the pair's numbers and contains no advice. A history with no pair gives an empty result and the string `decompose-lessons: no contrast pair found — no lesson derived`. Before `pairs` exists the cases fail.
  - Blocked by: S4 File
- [x] **S6 Pair derivation** — `pairs` as architecture.md's Pair derivation describes — size:M
  - Accept: the S5 tests pass and every earlier test still passes. Records come from `decompose_signals.measure` as given and no run-kind or label logic is copied out of it beyond reading the run-ref prefix and the label. The module imports the standard library, `cli` and `decompose_signals` only, and `tests/test_dual_membership.py` still passes unchanged, since `decompose_signals` is root-only.
  - Blocked by: S5 Pair derivation tests

## Milestone 3: later runs vote and `update` is the single writer

When this milestone is done, `decompose_lessons.votes` and the update fold take an existing file plus fixture records and a fixture git history to a new list of lessons, voted, extended and decayed, with dropped lessons staying dropped.

- [x] **S7 Voting tests** — cases for `votes` and `treated` with an injected git runner — size:M
  - Accept: the module holds these cases. A voter is a run not in `seen`, of the lesson's kind, whose decompose label is observed, whose signal is measurable and which is treated. A voter that hit the lesson's signal DOWNVOTEs and a clean voter UPVOTEs, and each voter votes once per lesson, recorded in `voted` so a second pass changes nothing. `treated` is true only when the commit that first added the lessons file is an ancestor of the run's decompose boundary commit, asserted by a recording fake runner that shows `git merge-base --is-ancestor` and a first-add lookup and no other git verb outside `decompose_signals`' read-only set. A voter that predates the file does not vote. A run with an inferred boundary does not vote. A runner failure or timeout is a problem and no vote is returned. Before `votes` and `treated` exist the cases fail.
  - Blocked by: S6 Pair derivation
- [x] **S8 Voting** — `votes` and `treated` as architecture.md's Voting describes — size:M
  - Accept: the S7 tests pass and every earlier test still passes. Git is reached only through `cli.runner`, injected, and the module makes no network call. Vote application goes through `upvote` and `downvote`, with no second copy of the step or removal rule.
  - Blocked by: S7 Voting tests
- [x] **S9 Update fold tests** — cases for the pure update fold and its write over a temp dir — size:M
  - Accept: the module holds these cases, each asserting exact output lines and file contents. The order is votes on existing lessons, then ADD or EDIT from new hit runs, then drop at 0. Each ADD, EDIT, UPVOTE, DOWNVOTE and drop prints one line naming the lesson id, then `decompose-lessons: wrote <path>`, or `decompose-lessons: unchanged` when nothing changed. Every run folded in is added to `seen`. A lesson dropped at 0 does not return on the next update from the same fixture runs, because its hit runs are in `seen`. A history with no pair and no file writes nothing and leaves no file. A lesson operation problem abandons the whole update with the file byte-identical, and so does a malformed existing file, which prints its line number. A `measure` result with problems writes nothing. The tool ships no lesson: the repo holds no `docs/factory/decompose-lessons.jsonl` hand-written seed, asserted on the working tree. Before the fold exists the cases fail.
  - Blocked by: S8 Voting
- [x] **S10 Update fold** — the update fold and its single whole-file write — size:M
  - Accept: the S9 tests pass and every earlier test still passes. The write is the only one `dump` performs; no command takes lesson text from a person.
  - Blocked by: S9 Update fold tests

## Milestone 4: the tool reports and compares through one command

When this milestone is done, `python3 decompose_lessons.py` prints pair count, lessons and the treated-versus-untreated re-plan comparison, `update` writes the file, and `python3 factory.py decompose-lessons` reaches both.

- [x] **S11 Comparison tests** — cases for `compare` over fixture records and a fixed treated set — size:M
  - Accept: the module holds these cases, each recomputing the figures in the test from the fixture records. Re-plan is pooled as the sum of `count` over the sum of `items_at_d`, over observed-label measurable runs only, split into treated and untreated. At or above `factory_config.resolve_calibrate_floor` treated runs the line is `decompose-lessons: re-plan treated <c>/<i> over <r> run(s), untreated <c>/<i> over <r> run(s) (observed only; <u> unmeasurable); descriptive, treated higher|not higher`. Below the floor the line is `decompose-lessons: no verdict: <r> treated run(s) is below the minimum of <floor>` and no rate is printed. Unmeasurable runs are counted and named, never counted as zero. Before `compare` exists the cases fail.
  - Blocked by: S10 Update fold
- [ ] **S12 Comparison** — `compare` as architecture.md's Comparison describes — size:S
  - Accept: the S11 tests pass and every earlier test still passes. The floor is read through `factory_config.resolve_calibrate_floor`, not a local 5. `tests/test_dual_membership.py`'s pin gains `(decompose_lessons, factory_config)`, so the set is 52 pairs as ADR-0113 records, its pair-count comment is updated, and the test passes.
  - Blocked by: S11 Comparison tests
- [ ] **S13 Report and front door tests** — end-to-end cases that drive `main([])` and `main(["update"])` against fixture records, a temp lessons file and an injected runner, asserting stdout and exit codes — size:M
  - Accept: the module holds these cases, each asserting exact strings. `main([])` prints in this order the pair-count line `decompose-lessons: <p> contrast pair(s) from <h> hit run(s): re-plan <a>, design gaps <b>, review-traced <c>`, one `decompose-lessons: <id> importance <n> — <text> (sources: <runs>)` line per lesson, the comparison line, and the `cli.report` summary; with no pair it prints the no-pair string instead of the count line. `main([])` writes nothing and the file is byte-identical afterwards. `main(["update"])` performs the S9 fold and exits 0. Exit codes: 0 with an empty pair set and with a refused verdict, 1 when `measure` or the file reports problems, 2 with usage on any unknown argument. A check that the module source imports no network module. Before `render` and `main` exist the cases fail.
  - Blocked by: S12 Comparison
- [ ] **S14 Report and front door** — `render`, `main` and the `factory.py` verb — size:M
  - Accept: the S13 tests pass and every earlier test still passes. Output goes through `cli.report`, so the summary prefix is computed. `factory.VERBS` gains `"decompose-lessons": ("decompose_lessons", "argv")` and `tests/test_factory_cli.py` passes. `tests/test_dual_membership.py` passes with 52 pairs.
  - Blocked by: S13 Report and front door tests

## Milestone 5: Decompose reads the file, the docs name the tool and the repo checks pass

When this milestone is done, the Decompose skill reads the lessons file at draft time, CLAUDE.md and CONTEXT.md name the tool and its vocabulary, and every CI check is green over the finished change with `skills/` touched only under `skills/decompose`.

- [ ] **S15 Skill step tests** — cases on `skills/decompose/SKILL.md` text — size:S
  - Accept: the module holds a case asserting the skill text names `docs/factory/decompose-lessons.jsonl`, treats each line as a hypothesis ordered by importance and never a rule or a reason to relax an `Accept:` line, and states the absent-or-empty case (draft unchanged, no message) and the malformed case (say so once, draft unchanged). A case asserts the skill text does not tell Decompose to run `decompose_lessons.py` or to write the file. The cases fail against the unedited skill.
  - Blocked by: S14 Report and front door
- [ ] **S16 Skill step** — one step in `skills/decompose/SKILL.md` between the soft gate and the draft, per architecture.md's Skill step — size:S
  - Accept: the S15 tests pass. `python3 lint.py` is re-run after the edit and prints `lint: 0 problem(s)`. `git diff --name-only main...HEAD -- skills/` lists only paths under `skills/decompose/`. `.claude-plugin/plugin.json` is unchanged (ADR-0095: the wave's release PR bumps it).
  - Blocked by: S15 Skill step tests
- [ ] **S17 Docs** — the CLAUDE.md "on demand, free" bullet beside `decompose_signals.py` and a CONTEXT.md entry for **Decompose lesson** — size:S
  - Accept: CLAUDE.md names `python3 decompose_lessons.py` as free, outside every gate and making no network call, says `update` is the one writer and is run by the Owner, and names `docs/factory/decompose-lessons.jsonl`. CONTEXT.md defines **Decompose lesson** as a derived, sourced, voted line whose importance starts at 2 and which is removed at 0. Neither doc contains a work-order token or sample lesson id that detectors C and I would scan, and `python3 kb.py drift` still prints `drift: 0 problem(s)`.
  - Blocked by: S16 Skill step
- [ ] **S18 Whole-repo verify** — the four CI checks and the scope checks over the finished change — size:S
  - Accept: `python3 run_tests.py` exits 0; `python3 lint.py` prints `lint: 0 problem(s)`; `python3 kb.py drift` prints `drift: 0 problem(s)`; `python3 gates.py` and `python3 gates.py --selftest` print `gates: 0 problem(s)`. `tests/test_dual_membership.py` passes with 52 pairs. `git diff --name-only main...HEAD` shows `skills/` edits only under `skills/decompose/`, no change to `.claude-plugin/plugin.json`, `factory_init.MIRRORS`, `factory/templates/`, `cost_ledger.py` or `decompose_signals.py`, and no committed `docs/factory/decompose-lessons.jsonl` unless `update` produced it. `python3 decompose_lessons.py` on this clone exits 0 and prints either the no-pair string or the lessons, and a comparison or a no-verdict line.
  - Blocked by: S17 Docs

## Design gaps found

none.

## Notes

