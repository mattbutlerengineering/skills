---
stage: verify
run: maintenance:lessons-per-signal-seen
date: 2026-10-23
assumptions:
  - "No prd.md exists for a maintenance run, so the criteria are defect.md's three defects with their Expected clauses, the nine breakdown items' Accept lines, architecture.md's exact strings, and the autorun brief's constraints (no skill edit, no new import, pin 55, no permanent test against main, no lessons file in the repo, nothing paid). All nine breakdown items are checked, so the soft gate holds."
  - "origin/main is aa0c939 and is an ancestor of HEAD 7819cc2 (`git merge-base --is-ancestor`), so no merge was needed. The 'unfixed' tree is `git archive origin/main` extracted to `$S/main`; the mutation trees are `git archive HEAD` copies `$S/mut/m1..m9`. `$S` is the scratchpad `/private/tmp/claude-501/-Users-mbutler-github-skills/9a27056e-40ad-47c2-a869-dd1e59a7bd2e/scratchpad/lps`. No mutation was applied in this tree."
  - "Capture's original scripts survived under the earlier scratchpad `cap/`; repro1 (lost signal) and repro2 (zero-item) were re-run unchanged except that the repo path comes from `$REPO`. repro3 (unbounded read) is replaced by a sparse-file test of the new bound. The vote-path reproduction is new (the defect names it but Capture did not script it); it stubs `treated()` to count every record as treated, standing in for the git ancestry check, on both trees."
  - "Per-signal seen end to end ran in a `git clone` of this repo checked out at HEAD under `$S/clone`, with the real CLI (`python3 decompose_lessons.py update`), so the real run history is measured. The repo's own `docs/factory/decompose-lessons.jsonl` was never written."
  - "Nothing was run live: no model, no `claude plugin eval`, trigger_eval.py or charter_replay.py."
---

# Verification: a lessons ledger that keeps a signal that matures later

## Summary

26 criteria: 26 PASS, 0 FAIL, 0 NOT RUN. The lost signal reproduces on
origin/main (update 1 with the review unmeasurable folds the run, update 2
says `unchanged` and no review lesson; the vote path likewise never votes)
and is fixed on HEAD (update 2 derives the review lesson and writes a file
byte-equal to the control; R votes `UPVOTE`, importance 2 to 3). The zero-item
line prints `not higher` on main for both pools and the three
no-comparison tails on HEAD. The 34 new or amended tests fail on origin/main's
`decompose_lessons.py` (31 failures, 3 errors, of 101) and pass on HEAD; nine
mutations of the fixed code each turn at least one test red. The real
clone's output is byte-identical to origin/main's, `skills/` is
byte-identical, no import changed, the pin is 55, and the whole suite is
green on three default runs, `-j 16`, `-j 1` and serial
`unittest discover`. Observations, not failures: three lines in
`decompose_lessons.py` exceed 79 columns (280, 379, 503), the
`>=` mutation is caught by exactly one test, and the new header is about
3.7x larger (architecture.md's accepted change 8; here 93 entries).
Next stage: Review.

## Criteria & evidence

### 1. Defect 1, lost signal: on origin/main update 2 is `unchanged` and no review lesson (reproduces); on HEAD the review lesson is derived

- Check: Capture's repro1, `REPO=<tree> python3 -I repro1.py`, on `$S/main` (origin/main) and on this tree. A: update 1 with R's review unmeasurable, update 2 with it landed. B: control, a single update after Review.
- Evidence (origin/main):
  ```
  == A: update between Implement and Review
  stage1 -> ['decompose-lessons: ADD design_gaps/feature/routed', 'decompose-lessons: ADD replan/feature/added', 'decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'] []
  stage2 -> ['decompose-lessons: unchanged'] []
  {"seen": ["feature:c", "feature:h", "feature:r"]}
  (2 lessons, no review/ lesson)
  == B: control, first update after Review
  stage2 -> [... 'decompose-lessons: ADD review/feature/named', 'decompose-lessons: wrote ...'] []
  ```
  HEAD:
  ```
  == A: update between Implement and Review
  stage1 -> ['decompose-lessons: ADD design_gaps/feature/routed', 'decompose-lessons: ADD replan/feature/added', 'decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'] []
  stage2 -> ['decompose-lessons: ADD review/feature/named', 'decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'] []
  {"seen": ["design_gaps:feature:c", ..., "replan:feature:r", "review:feature:c", "review:feature:h", "review:feature:r"]}
  {"id": "review/feature/named", ... "text": "feature runs whose review findings name an item: r 1 of 2 findings (observed), h 0 of 0 findings (observed)", "sources": ["feature:h", "feature:r"], ...}
  == B: control: stage2 -> ADD design_gaps, ADD replan, ADD review/feature/named, wrote ...
  ```
  The three lesson lines and the header printed for A and B on HEAD are identical (nine entries, three signals x three runs).
- Result: PASS (the control stays green on both trees)

### 2. The same loss on the vote path: on origin/main R never votes; on HEAD it does

- Check: new `repro_vote.py`: stage 0 records H (review hit) and C (clean) derive `review/feature/named`; stage 1 adds R with review unmeasurable; stage 2 R's review lands with 0 named. `treated()` stubbed to treat every record, on both trees.
- Evidence (origin/main):
  ```
  stage1 (R review unmeasurable) -> ['decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'] []
     lessons: [('review/feature/named', 2, [])]
  stage2 (R review landed, clean) -> ['decompose-lessons: unchanged'] []
     lessons: [('review/feature/named', 2, [])]
  ```
  HEAD:
  ```
  stage2 (R review landed, clean) -> ['decompose-lessons: UPVOTE review/feature/named', 'decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'] []
     lessons: [('review/feature/named', 3, ['feature:r'])]
  ```
- Result: PASS

### 3. The new tests are RED against origin/main's `decompose_lessons.py` and green on HEAD

- Check: HEAD's `tests/test_decompose_lessons.py` copied into a copy of origin/main (`$S/redcopy`); `python3 -m unittest tests.test_decompose_lessons` there and here.
- Evidence:
  ```
  redcopy (origin/main code): Ran 101 tests ... FAILED (failures=31, errors=3)
  FAIL: test_a_review_that_matures_after_an_update_is_still_derived (TestUpdate)
  FAIL: test_a_run_seen_for_replan_can_still_vote_on_a_review_lesson (TestVotes)
  FAIL: test_a_hit_run_is_skipped_only_for_the_signal_it_is_seen_for (TestPairs)
  FAIL: test_a_zero_item_pool_has_no_rate_and_the_line_says_so (TestCompare) [treated / untreated / both]
  FAIL: test_an_old_per_run_entry_is_refused_with_the_recovery (TestFile) [feature:c / product / maintenance:m]
  ERROR: test_a_file_above_the_bound_is_refused_unread; ERROR: test_a_file_at_the_bound_loads; ERROR: test_seen_key_builds_signal_colon_run_ref
  ... (34 in all)
  HEAD: Ran 101 tests in 0.050s  OK
  ```
- Result: PASS

### 4. Defect 2, zero-item pool: main prints `not higher` for both pools; HEAD prints the three tails

- Check: Capture's repro2 on both trees, then `main()` with an injected `measure` (`$S/zero.py`) for treated 0/0, untreated 0/0, both 0/0, two normal pools, and a below-floor pool.
- Evidence (repro2, origin/main then HEAD):
  ```
  ... treated 0/0 over 5 run(s), untreated 1/20 over 2 run(s) (observed only; 0 unmeasurable); descriptive, treated not higher
  ... treated 5/40 over 5 run(s), untreated 0/0 over 1 run(s) (observed only; 0 unmeasurable); descriptive, treated not higher
  HEAD:
  ... treated 0/0 over 5 run(s), untreated 1/20 ...; descriptive, no comparison: rate undefined for the treated pool (0 items)
  ... treated 5/40 over 5 run(s), untreated 0/0 over 1 run(s) ...; descriptive, no comparison: rate undefined for the untreated pool (0 items)
  ```
  `main()` on HEAD: untreated 0/0 and both-0/0 end `... for both pools (0 items)`, every case `exit 0`, the `0/0` figures still printed.
- Result: PASS

### 5. A normal pool and the below-floor line are unchanged

- Check: the same `zero.py` on origin/main and on HEAD, outputs compared case by case.
- Evidence (identical on origin/main and HEAD):
  ```
  ## normal higher      ... treated 3/8 over 1 run(s), untreated 0/8 over 1 run(s) (observed only; 0 unmeasurable); descriptive, treated higher
  ## normal not higher  ... treated 0/8 over 1 run(s), untreated 3/8 over 1 run(s) (observed only; 0 unmeasurable); descriptive, treated not higher
  ## below floor        decompose-lessons: no verdict: 0 treated run(s) is below the minimum of 1
  exit 0 in all three
  ```
- Result: PASS

### 6. Per-signal `seen` end to end: second `update` is `unchanged` and idempotent

- Check: scratch clone at HEAD, real CLI, `update` twice, `cmp`.
- Evidence:
  ```
  --- update 1
  decompose-lessons: ADD design_gaps/feature/routed
  decompose-lessons: ADD replan/feature/added
  decompose-lessons: ADD replan/maintenance/dropped
  decompose-lessons: ADD review/feature/named
  decompose-lessons: ADD review/maintenance/named
  decompose-lessons: wrote docs/factory/decompose-lessons.jsonl
  decompose-lessons: 0 problem(s)      exit=0
  --- update 2
  decompose-lessons: unchanged
  decompose-lessons: 0 problem(s)      exit=0
  cmp docs/factory/decompose-lessons.jsonl first.jsonl -> CMP-IDENTICAL
  ```
- Result: PASS

### 7. Header entries are `<signal>:<run ref>`, sorted and unique; a run seen for one signal stays eligible for another

- Check: parse line 1 of the clone's file.
- Evidence:
  ```
  93 entries; sorted: True unique: True
  all <signal>:<ref>: True
  Counter({'review': 39, 'replan': 31, 'design_gaps': 23})
  partial: maintenance:lessons-per-signal-seen ['design_gaps', 'replan']
  partial: feature:readme-skill-map ['review']
  partial: maintenance:run-discovery-ignores-open-prs ['replan', 'review']
  ... (19 runs seen for a strict subset of the signals)
  ```
  This run itself is seen for design_gaps and replan and not review (its `review.md` does not exist), so its review hit stays eligible when it lands; repro1 on HEAD (criterion 1) is the executed proof of that eligibility.
- Result: PASS

### 8. Migration refusal: old shape gives the exact string, exit 1, file untouched

- Check: scratch clone, header written by hand, `python3 decompose_lessons.py` and `... update`, compared against the file afterwards.
- Evidence:
  ```
  {"seen": ["feature:r"]}   (report and update)
  decompose-lessons: docs/factory/decompose-lessons.jsonl line 1: seen entry 'feature:r' is the old per-run shape (ADR-0116); delete the file and run update to rebuild it
  decompose-lessons: 1 problem(s)       exit=1   (file untouched)
  {"seen": ["product"]}  -> same string with 'product', exit=1
  ```
- Result: PASS

### 9. A garbage entry, a non-list header, a non-string entry; a valid new-shape file loads

- Evidence:
  ```
  {"seen": ["bogus"]}
  decompose-lessons: docs/factory/decompose-lessons.jsonl line 1: seen entry 'bogus' is not <signal>:<run ref>      exit=1
  80 x's -> "seen entry 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' is not <signal>:<run ref>" (60 characters)   exit=1
  {"seen": "feature:r"} and {"seen": [1]}
  decompose-lessons: docs/factory/decompose-lessons.jsonl line 1: expected the seen header      exit=1
  {"seen": ["replan:feature:r", "review:product"]}
  decompose-lessons: 42 run(s), 0 problem(s)      exit=0
  ```
- Result: PASS

### 10. Size bound: one byte above is refused and `read_file` never runs; exactly the bound is read

- Check: sparse files (4096 bytes on disk) of `MAX_LESSONS_BYTES + 1` and `MAX_LESSONS_BYTES`; `decompose_lessons.read_file` replaced by a trap printing `READ ATTEMPTED`, plus the CLI.
- Evidence:
  ```
  over 1048577 -> ([], [], ['decompose-lessons: docs/factory/decompose-lessons.jsonl is 1048577 bytes, above the 1048576-byte bound; not read'])   (no READ ATTEMPTED)
  at 1048576 (real read_file) -> ([], [], ['decompose-lessons: docs/factory/decompose-lessons.jsonl line 2: not valid JSON'])   (the file was read; its zero-fill content is junk)
  CLI report and update over the 1048577-byte file: the same refusal, "1 problem(s)", exit=1
  ```
  `MAX_LESSONS_BYTES = 1024 * 1024`, one definition (`grep -n MAX_LESSONS_BYTES decompose_lessons.py` line 42).
- Result: PASS

### 11. Real clone: output equals origin/main's with this clone as explicit root

- Check: `python3 decompose_lessons.py` here; origin/main's module with `main([], root=<this clone>)`; `diff`.
- Evidence:
  ```
  fixed exit=0   main exit=0
  $ diff real_main.out real_fixed.out && echo DIFF-EMPTY
  DIFF-EMPTY
  (4 lines; first: decompose-lessons: 20 contrast pair(s) from 20 hit run(s): re-plan 3, design gaps 2, review-traced 15; last: decompose-lessons: 42 run(s), 0 problem(s))
  ```
- Result: PASS

### 12. The Decompose skill needs no edit

- Check: `git diff --quiet origin/main -- skills`; `git diff --name-only origin/main | grep -E '^(skills/|\.claude-plugin)'`; the pinned skill-text test.
- Evidence:
  ```
  $ git diff --quiet origin/main -- skills && echo SKILLS-IDENTICAL
  SKILLS-IDENTICAL
  $ git diff --name-only origin/main | grep -E "^(skills/|\.claude-plugin)" || echo none
  none under skills/ or .claude-plugin
  $ python3 -m unittest tests.test_decompose_lessons
  Ran 101 tests in 0.050s   OK      (includes the pin at line 1266, "When the file is absent, or holds only the `seen` header,")
  ```
- Result: PASS

### 13. No new import; dual-membership stays 55

- Evidence:
  ```
  diff of the import/from lines, origin/main vs HEAD decompose_lessons.py -> IMPORTS-SAME
  added import lines in the tests diff -> (none)
  len(ROOT_ONLY_IMPORTS_MIRRORED) -> pairs 55
  tests.test_dual_membership: Ran 3 tests ... OK   (file not in the diff)
  ```
- Result: PASS

### 14. `docs/factory/decompose-lessons.jsonl` is absent from this repo

- Evidence:
  ```
  $ git ls-files docs/factory/decompose-lessons.jsonl
  (nothing)
  $ ls docs/factory/decompose-lessons.jsonl
  ls: docs/factory/decompose-lessons.jsonl: No such file or directory
  ```
- Result: PASS

### 15. No permanent test asserts "unchanged against main"

- Evidence:
  ```
  $ grep -n -iE "against main|origin/main|git archive|unchanged against" tests/test_decompose_lessons.py || echo "no match"
  no match
  ```
- Result: PASS

### 16. ADR trail: ADR-0113 and both README rows say superseded in part by ADR-0116; ADR-0116 is provisional

- Evidence:
  ```
  0113 file: - Status: superseded in part by ADR-0116 (the line-1 seen header entry shape; provisional)
  README:136 | [0113] ... | superseded in part by ADR-0116 (the line-1 seen header entry shape; provisional) |
  0116 file: - Status: provisional      README:139 | [0116] ... | provisional |
  ```
  `ls docs/adr` -> 116 numbered files, first `0001`, last `0116`, no duplicated prefix and no gap (checked mechanically). ADR-0116 names `MAX_LESSONS_BYTES` (1 MiB) and the refusals; `docs/features/decompose-lessons/architecture.md` gained three dated lines only (diffstat `3 +`).
- Result: PASS

### 17. Whole suite: three default runs, `-j 16`, `-j 1`, serial discover

- Evidence:
  ```
  tests: 3806 tests across 118 modules in 25.6s on 8 workers, 0 problem(s)   (x3: 25.6s, 25.8s, 25.6s)
  tests: 3806 tests across 118 modules in 24.0s on 16 workers, 0 problem(s)
  tests: 3806 tests across 118 modules in 94.5s on 1 workers, 0 problem(s)
  python3 -m unittest discover tests: Ran 3806 tests in 86.657s, OK (exit 0)
  ```
- Result: PASS

### 18. lint, drift, gates, selftest, one_owner

- Evidence:
  ```
  lint: 0 problem(s) across 34 skills
  drift: 0 problem(s)
  gates: 0 problem(s)
  selftest: ok
  one-owner: 9 problem(s)      (baseline 9; none names decompose_lessons: grep -c = 0)
  ```
- Result: PASS

### 19. Mutation M1, key by run only (`seen_key` returns the bare ref)

- Evidence:
  ```
  diff -    return f"{signal}:{ref}" / +    return ref in a git archive HEAD copy.
  Result:
  FAILED (failures=18); first test_a_ballot_after_the_lesson_dropped_in_the_same_fold_is_skipped, test_a_review_hit_with_no_implement_boundary_is_still_folded, test_a_run_unmeasurable_for_a_signal_is_not_seen_for_it.
  ```
- Result: PASS (caught)

### 20. Mutation M2, fold adds unmeasurable runs to seen

- Evidence:
  ```
  _measured's filter if _hit_label(rec[field], num) is not None -> if "sha" in rec["implement"] (the old "complete" rule).
  FAILED (failures=7):
  test_a_run_unmeasurable_for_a_signal_is_not_seen_for_it, test_seen_is_every_measured_signal_and_run_sorted, test_a_review_hit_with_no_implement_boundary_is_still_folded, and four more.
  ```
- Result: PASS (caught)

### 21. Mutation M3, `>` becomes `>=` on the size bound

- Evidence:
  ```
  -    if size > MAX_LESSONS_BYTES: / +    if size >= MAX_LESSONS_BYTES:.
  FAILED (failures=1):
  test_a_file_at_the_bound_loads.
  Only this one test guards the edge.
  ```
- Result: PASS (caught)

### 22. Mutation M4, old shape accepted silently

- Evidence:
  ```
  a return None inserted before the old-shape refusal in _entry_problem.
  FAILED (failures=6):
  test_an_old_per_run_entry_is_refused_with_the_recovery x3 (feature:c, product, maintenance:m) and the update and front-door old-shape tests.
  ```
- Result: PASS (caught)

### 23. Mutation M5, zero-item tail dropped for the untreated pool

- Evidence:
  ```
  (("treated", t), ("untreated", u)) -> (("treated", t),) in _verdict.
  FAILED (failures=2):
  test_a_zero_item_pool_has_no_rate_and_the_line_says_so for the untreated and both-pools subcases.
  ```
- Result: PASS (caught)

### 24. Mutations M6 and M7, votes ignoring per-signal seen

- Evidence:
  ```
  M6 removes or seen_key(signal, rec["run"]) in seen \ from _ballot:
  FAILED (failures=1), test_a_run_seen_for_replan_can_still_vote_on_a_review_lesson.
  M7 replaces the votes prefilter's seen_key(...) not in seen with True:
  FAILED (failures=1), test_a_run_seen_for_every_signal_its_lessons_use_costs_no_git.
  ```
- Result: PASS (both caught)

### 25. Mutations M8 and M9, pairs ignoring skip; stat guard disabled

- Evidence:
  ```
  M8 or seen_key(field, hit["run"]) in skip: -> or False: gives FAILED (failures=5) (test_a_lesson_dropped_at_zero_is_not_re_added_from_its_runs, test_an_upvote_prints_one_line_and_moves_the_count, test_votes_come_first_then_adds_then_the_drop_stays_dropped, and two more).
  M9 if size > MAX_LESSONS_BYTES: -> if False: gives FAILED (failures=1), test_a_file_above_the_bound_is_refused_unread.
  ```
- Result: PASS (both caught)

### 26. Implement's deviations judged

- Check: read the breakdown Notes and `git diff origin/main -- decompose_lessons.py` against architecture.md.
- Evidence and judgement:
  ```
  git diff origin/main -- decompose_lessons.py read against architecture.md; judgements below
  ```
  - Pins amended in the item that changed them (per-run seen fixtures and header literals, the every-complete-run test renamed `test_seen_is_every_measured_signal_and_run_sorted`, the dropped-lesson ballot test passing its voter as a measured record): each is a consequence of the accepted shape change and is recorded; no eval definition was weakened. Accepted.
  - `votes` prefilter is `any(run_kind == kind(run) and seen_key(signal, run) not in seen for signal, run_kind in parts)`, where architecture.md says "keeps a run only if it has at least one lesson signal it is unseen for"; it matches, and M7 shows it is pinned. Accepted.
  - `serialize` de-duplicates (`sorted(set(seen))`), as the architecture and S1 require. Accepted.
  - Three lines over 79 columns (`serialize` at 280, the `pairs` docstring at 379, the `votes` docstring at 503) and a `_ballot` docstring that restates its guard: cosmetic, `lint.py` is clean; flagged for Review, not a failure.
  - No string or constant changed after the ADR was written, so no ADR or architecture correction was owed (S8 Note holds: ADR-0116 matches the code).
- Result: PASS

## Failures

none.

## Not verified

- The Decompose skill's behaviour over a file in the new shape was not exercised (no model run, by instruction); the skill reads lines and not the header, and its pinned text test passes.
- The vote-path reproduction stubs `treated()` (the git ancestry check) on both trees; the real `treated` is covered by the module's own tests and the clone's real-history `update`, which has no treated runs (`0 treated run(s) is below the minimum of 5`).
- A run seen for replan but not review is shown by header inspection of the clone and by the repro1 stage-2 outcome, not by landing a real `review.md` in the clone.
- No lessons file exists on main, so the old-shape refusal was never tested against a real committed file; the recovery (delete and re-run `update`) was not exercised either, since the delete-and-rebuild path is just the first-update path of criterion 6.
- CI was not run (no push); the four CI commands were run locally.
