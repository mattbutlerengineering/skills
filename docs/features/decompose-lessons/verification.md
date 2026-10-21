---
stage: verify
run: feature:decompose-lessons
date: 2026-10-20
assumptions:
  - "No live interview: the autorun brief holds no Verify-specific answers, so the skill's defaults were taken. The criteria list is prd.md's thirteen success criteria plus the breakdown acceptance criteria no PRD criterion covers (last section), plus a judgement of breakdown Notes' seven deviations."
  - "Every piece of evidence was run on HEAD cb1151b in this session; nothing is carried over from the Implement stage's report."
  - "Recommended default taken (flake re-check): five full-suite runs, three at the default 8 workers, one at -j 16, one serial unittest discover."
  - "Recommended default taken (protected paths): compared with the three-dot form origin/main...HEAD, so main's own moves do not count as this branch's changes."
  - "Recommended default taken (update verb): run only in a scratch git clone under the scratchpad; this repo never gained docs/factory/decompose-lessons.jsonl."
---

# Verification: A ranked lessons file for Decompose

## Summary

13 of 13 PRD success criteria PASS, 0 FAIL, 0 NOT RUN, on HEAD cb1151b. The
breakdown acceptance criteria no PRD criterion covers also pass. Five full
runs were green (3542 tests, 109 modules). Four mutations of load-bearing
behaviour each applied (diff shown) and each made tests fail. None of the
seven Implement deviations contradicts a PRD criterion. Two caveats the
verdict does not hide: (1) the PRD criterion "no lesson ships as a
hand-written seed" is pinned by a weakened test (a lessons file that exists
must load clean); the absence itself was checked here by hand, not by a
test. (2) On this clone the comparison refuses a verdict (0 treated runs, floor 5),
so the treated-versus-untreated arithmetic is proven by fixture tests only,
never live. See Not verified.

## Criteria & evidence

### 1. ADD with no source run exits nonzero with a problem string naming the missing source, and leaves the file byte-identical

- Check: called the public operation, ran the tool-level tests.
- Evidence:
  ```
  add([], "x/y/z","t",[]) -> ([], ['decompose-lessons: add refused: x/y/z cites no source run'])
  tests: test_add_with_no_source_run_is_refused_and_returns_the_original ... ok
         test_a_fold_problem_leaves_the_file_byte_identical ... ok
         test_a_lesson_operation_problem_abandons_the_whole_fold ... ok
  ```
  (Exit 1 on problems and a byte-identical file: TestFrontDoor and TestUpdate cases, in the 70/70 passing run below.)
- Result: PASS

### 2. A passing ADD writes importance 2 with its source runs; read back from the file

- Evidence:
  ```
  add([], "x/y/z","t",["feature:a"]) -> [{'id':'x/y/z','importance':2,'text':'t','sources':['feature:a'],'voted':[]}]
  scratch update wrote: {"id": "replan/maintenance/dropped", "importance": 2, ... "sources": ["maintenance:a-blind-find-is-not-a-failed-agent", "maintenance:a-timestamp-the-digest-cannot-parse"], "voted": []}
  tests: test_add_returns_a_new_list_at_importance_two, test_the_first_update_writes_the_derived_file ... ok
  ```
- Result: PASS

### 3. UPVOTE 2 -> 3, DOWNVOTE 2 -> 1, sources intact

- Evidence:
  ```
  upvote  -> importance 3 sources ['feature:a']
  downvote -> importance 1
  tests: test_upvote_takes_two_to_three_and_keeps_the_sources ... ok
         test_downvote_takes_two_to_one_and_keeps_the_sources ... ok
  ```
- Result: PASS

### 4. DOWNVOTE to 0 removes the line; a lesson at 1 remains; never stored at 0 or negative

- Evidence:
  ```
  downvote(<lesson at 1>) -> ([], [])
  tests: test_downvote_from_one_removes_the_lesson ... ok
         test_a_lesson_at_one_left_alone_remains ... ok
         test_votes_come_first_then_adds_then_the_drop_stays_dropped ... ok
  ```
  Mutation M2 (below) shows the threshold is pinned.
- Result: PASS

### 5. A vote or EDIT naming a nonexistent lesson is refused and creates nothing

- Evidence:
  ```
  upvote([], "nope","r") -> ([], ['decompose-lessons: upvote refused: no lesson nope'])
  edit([], "nope","t")   -> ([], ['decompose-lessons: edit refused: no lesson nope'])
  test_a_vote_or_edit_on_an_unknown_id_creates_nothing ... ok
  ```
- Result: PASS

### 6. EDIT keeps importance and sources; refused if it would leave no source

- Evidence:
  ```
  edit(<lesson>, "x/y/z","new", []) -> (original list, ['decompose-lessons: edit refused: x/y/z cites no source run'])
  edit(<lesson at 3, voted>, "x/y/z","new") -> [{'id':'x/y/z','importance':3,'text':'new','sources':['feature:a'],'voted':['feature:b']}]
  tests: test_edit_changes_text_and_keeps_importance_sources_and_voted, test_an_edit_that_leaves_no_source_run_is_refused ... ok
  ```
- Result: PASS

### 7. Pairs only from re-plan, design-gap and review signals; a fixture band miss and retro note yield no lesson

- Evidence:
  ```
  test_band_misses_and_retro_notes_reach_no_pair_or_lesson ... ok
  test_pairs_match_the_hand_worked_history ... ok
  imports of decompose_lessons.py: json os subprocess sys tempfile pathlib decompose_signals factory_config cli
  ```
  The module has no import of size_band_calibration or any retro reader, so there is no path for either input.
- Result: PASS

### 8. Empty history leaves the file empty/absent and prints that no pair was found

- Evidence:
  ```
  pairs([]) -> []        NO_PAIR = "decompose-lessons: no contrast pair found — no lesson derived"
  tests: test_a_history_with_no_pair_is_empty_and_has_the_string,
         test_no_pair_prints_the_no_pair_string_and_writes_nothing,
         test_no_pair_and_no_file_writes_nothing,
         test_an_empty_write_creates_no_file ... ok
  ```
- Result: PASS

### 9. Decompose skill text references the file and the absent-or-empty case

- Evidence:
  ```
  skills/decompose/SKILL.md step 3 (git diff): "If the target repo has `docs/factory/decompose-lessons.jsonl`, read it. ... When the file is absent, or holds only the `seen` header, draft as before and say nothing. When it is malformed, say so once and draft as before. This step only reads the file; ..."
  tests: TestSkillStep x4 (reads as hypotheses; absent/empty/malformed; never runs the tool or writes the file; sits between soft gate and draft) ... ok
  ```
- Result: PASS

### 10. Every printed figure computed from run records; no hand-written seed ships

- Check: ran the tool on this clone and recomputed by hand from `python3 decompose_signals.py`.
- Evidence:
  ```
  $ python3 decompose_lessons.py
  decompose-lessons: 18 contrast pair(s) from 18 hit run(s): re-plan 3, design gaps 2, review-traced 13
  decompose-lessons: no verdict: 0 treated run(s) is below the minimum of 5
  decompose-lessons: 38 run(s), 0 problem(s)          (exit 0)

  By hand from decompose_signals.py output:
   re-plan hits (count>0): decompose-outcome-signals 2/13, first-live-dispatch 4/8, a-timestamp-the-digest-cannot-parse 6/7 = 3
   design-gap hits: decompose-outcome-signals 1, pr-body-preflight 1 = 2
   review-traced hits (>0 of N): codex-style 3, decompose-outcome-signals 2, factory-evolution-v1 3, first-live-dispatch 10, launch-demo 3,
     deepening-cli-seams 2, deepening-tool-seams 3, one-fact-one-owner 3, one-guarded-file-read 1, a-blind-find 1, dedup-identity 1,
     empty-is-not-the-same 1, run-discovery 1 = 13
   3 + 2 + 13 = 18 hit runs, each with a clean run of its kind and label (fail-closed-roll-up for observed feature, codex-style
     for inferred feature, a-blind-find for inferred maintenance) -> 18 pairs.   MATCHES.
  One hit run: first-live-dispatch re-plan 4 of 8, added 3, split 1 -> detail "added" (largest, ties n/a), lesson id replan/feature/added,
     tool text for the scratch run lists it among sources: ["...first-live-dispatch"].   MATCHES.
  Treated runs: no lessons file is committed -> 0 treated -> "no verdict" below floor 5.   MATCHES.

  $ ls docs/factory/decompose-lessons.jsonl  ->  No such file or directory; git status --porcelain prints nothing
  ```
  The figures are asserted with fixtures in TestPairs / TestFrontDoor (test_the_report_prints_pairs_lessons_comparison_and_summary).
- Result: PASS (the no-seed half rests on the manual `ls` above and on the diff against origin/main listing no .jsonl; the test guarding it was weakened, see Deviations 3)

### 11. Stdlib only, no network call

- Evidence:
  ```
  imports: json os subprocess sys tempfile pathlib; local: decompose_signals factory_config cli
  grep -n "import socket|urllib|http" decompose_lessons.py -> no matches
  test_the_module_imports_no_network_module ... ok
  test_only_log_and_merge_base_are_reached ... ok   (git verbs the voting path may run)
  ```
- Result: PASS

### 12. `.claude-plugin/plugin.json` version unchanged

- Evidence:
  ```
  $ git diff --stat origin/main...HEAD -- .claude-plugin/plugin.json factory/templates cost_ledger.py decompose_signals.py factory_init.py
  (empty)
  $ grep version .claude-plugin/plugin.json -> "version": "0.21.1"
  $ git diff --name-only origin/main...HEAD -- skills -> skills/decompose/SKILL.md
  ```
  The branch touches 14 files: CLAUDE.md, CONTEXT.md, decompose_lessons.py, ADR-0113 and its README row, the run directory's markdown, factory.py (VERBS row), skills/decompose/SKILL.md, tests/test_decompose_lessons.py, tests/test_dual_membership.py (50 -> 52 pairs). No protected path appears.
- Result: PASS

### 13. run_tests, lint, kb drift, gates, gates --selftest all pass

- Evidence:
  ```
  python3 run_tests.py        tests: 3542 tests across 109 modules in 27.9s on 8 workers, 0 problem(s)
  python3 run_tests.py        tests: 3542 tests across 109 modules in 28.4s on 8 workers, 0 problem(s)
  python3 run_tests.py        tests: 3542 tests across 109 modules in 25.6s on 8 workers, 0 problem(s)
  python3 run_tests.py -j 16  tests: 3542 tests across 109 modules in 29.7s on 16 workers, 0 problem(s)
  python3 -m unittest discover tests   Ran 3542 tests in 89.557s  OK   (exit 0)
  python3 lint.py             lint: 0 problem(s) across 34 skills
  python3 kb.py drift         drift: 0 problem(s)
  python3 gates.py            gates: 0 problem(s)
  python3 gates.py --selftest selftest: ok
  python3 -m unittest tests.test_dual_membership tests.test_factory_cli   Ran 19 tests ... OK
  git status --porcelain      (empty)
  ```
- Result: PASS (no flake in five runs)

## Breakdown acceptance criteria no PRD criterion covers

### Scratch `update`: a real file is produced, well-formed with sources, and a second update is idempotent

- Check: `git clone` of this repo into the scratchpad (`.../scratchpad/clone`), `update` twice there, `cmp` the files. This repo was never written to.
- Evidence:
  ```
  $ python3 decompose_lessons.py update      (scratch clone)
  decompose-lessons: ADD design_gaps/feature/routed
  decompose-lessons: ADD replan/feature/added
  decompose-lessons: ADD replan/maintenance/dropped
  decompose-lessons: ADD review/feature/named
  decompose-lessons: ADD review/maintenance/named
  decompose-lessons: wrote docs/factory/decompose-lessons.jsonl
  decompose-lessons: 0 problem(s)            exit 0
  file: line 1 {"seen": [30 run refs]}; 5 lesson lines, each importance 2, 2 to 9 sources, "voted": []
  $ python3 decompose_lessons.py update      (second time)
  decompose-lessons: unchanged               exit 0 ; cmp: IDENTICAL
  $ python3 decompose_lessons.py             (report from the file)
  decompose-lessons: replan/feature/added importance 2 — feature runs that re-planned mostly by adding rows: decompose-outcome-signals 2 of 13 items (observed), fail-closed-roll-up 0 of 7 items (observed) (sources: feature:codex-style-standards-enforcement, feature:decompose-outcome-signals, feature:fail-closed-roll-up, feature:first-live-dispatch)
  ```
  The five ids equal the five lessons architecture.md predicted.
- Result: PASS

### Mutation checks (copies via git archive in the scratchpad; this tree untouched)

- Evidence:
  ```
  M1 drop the source-required guard      -    if not sources:        +    if False:
     FAIL: test_add_with_no_source_run_is_refused_and_returns_the_original            (1 failure of 70)
  M2 removal threshold flipped           -    if importance < 1:     +    if importance < 0:   (lesson kept at 0)
     FAIL: test_downvote_from_one_removes_the_lesson; test_votes_come_first_then_adds_then_the_drop_stays_dropped  (2)
  M3 drop the seen-set re-derivation guard  -  pairs(records, skip=set(seen))  +  pairs(records, skip=set())
     FAIL: test_an_upvote_prints_one_line_and_moves_the_count; test_votes_come_first_then_adds_then_the_drop_stays_dropped  (2)
  M4 upvote step 1 -> 2                  -    _vote("upvote", 1, ...)  +  _vote("upvote", 2, ...)
     FAIL: test_upvote_takes_two_to_three_and_keeps_the_sources + 3 more              (4)
  $ git status --porcelain   (empty)
  ```
- Result: PASS (4 of 4 mutations caught)

### Judgement of the seven Implement deviations (breakdown Notes) against the PRD and architecture.md

- Check: read breakdown Notes against prd.md and architecture.md.
- Evidence:
  ```
  1. `edit` takes optional `sources`; votes take the voter ref. Does not contradict criterion 6: with `sources` omitted EDIT keeps them, and refuses when none remain; `update` uses it only to grow a lesson's sources. Slight widening past "keeps its source runs" (a caller may replace them; test_edit_may_replace_the_sources), still source-required. Acceptable.
  2. One pair per hit run (first clean run), so 18 pairs, not the 26/4/145 architecture.md measured under its all-clean-runs reading. Architecture's own pair rule text ("first in run-path order") says one exemplar per hit, and S5 pins it; I recomputed 18 by hand. No PRD criterion states a pair count. Acceptable; the architecture assumptions block's numbers are stale and Review may want that noted.
  3. `seen` takes every complete run, hit pairs and voters; and S9's "repo holds no hand-written seed" is asserted only as "an existing lessons file loads clean". This weakens the test behind PRD criterion 10's no-seed clause: a hand-written committed file that is well-formed and sourced would pass the test. Rationale (a literal absence test would fail the Owner's first `update` commit) is sound. I verified absence manually (criterion 10). It does not contradict the criterion's behaviour, but it is a test gap, listed under Not verified.
  4. Extra `unmeasurable re-plan run(s)` line. Consistent with architecture ("counted and named"). Acceptable.
  5. Zero-item untreated pool reads "not higher". Descriptive, no verdict claim. Acceptable.
  6. Skill steps renumbered 4 to 8. No reference by number; lint passes. Acceptable.
  7. (Note 3 sub-point) `update` EDITs a known id only when a new hit run grows its sources; a lesson dropped in a fold is not re-added by that fold. Consistent with the architecture's "dropped lessons cannot return from the same runs".
  ```
- Result: PASS (none contradicts a criterion; deviation 3 is a test-strength gap)

## Failures

none.

## Not verified

- The treated-versus-untreated re-plan comparison with real data: this clone has no committed lessons file, hence 0 treated runs and a "no verdict" line. The pooled arithmetic and the floor are verified by fixture tests (TestCompare) only.
- Voting against real git ancestry: verified with an injected runner (TestTreated, TestVotes); the scratch `update` had no committed lessons file, so no real treated voter existed.
- The Decompose skill's behaviour when an agent actually follows the new step: only the skill text is tested (no live eval; routing/charter evals cost money and are out of scope).
- The scratch clone's report listed a slightly different unmeasurable-run set than this repo's own run (the clone lacks some refs); pair counts and lessons were identical (18 pairs, same five ids).
- Test gap noted under deviation 3: nothing in the suite fails if a hand-written, well-formed, sourced lessons file is committed.
- Release coupling: the skill change reaches installed plugins only with the wave's release PR (ADR-0095); not checkable here.
