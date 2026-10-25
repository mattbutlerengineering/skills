---
stage: verify
run: maintenance:seen-before-partner
date: 2026-10-24
assumptions:
  - "No prd.md exists for a maintenance run, so the criteria are defect.md's defect and Expected clauses, breakdown.md's Accept lines (P1 to P4, all four checked, so the soft gate holds), architecture.md's pinned behaviours, and the autorun brief's constraints (no skills/ or plugin.json change, no new import, dual-membership pin 55, no permanent test against main, no lessons file in the repo, nothing paid)."
  - "origin/main is ec8159f (fetched at the start of this stage) and an ancestor of HEAD 13c40f5 (`git merge-base --is-ancestor`), so no merge was needed. The unfixed tree is `git archive origin/main` extracted to `$S/main`; the fixed tree is `git archive HEAD` at `$S/head`; the mutation trees are `git archive HEAD` copies `$S/mut/m1..m7`; the real-history checkout is `git clone` at HEAD in `$S/clone`. `$S` is the scratchpad `/private/tmp/claude-501/-Users-mbutler-github-skills/2c98a723-2833-4868-8bbf-e4099b478ada/scratchpad/sbp`. No mutation was applied in this tree and no code was changed by this stage."
  - "Capture's repro script (`repro_issue.py`, in the scratchpad above `sbp`) was re-run unchanged on both trees. It stubs `decompose_lessons.treated` to count every record as treated, standing in for the git ancestry check; the idempotence fuzz does the same, with a random treated subset when votes are on."
  - "The idempotence check is a fresh randomized generator (`$S/idem.py`, seeds 0 to 1499, 3 stages, 3 to 7 runs, both kinds, both hit labels, counts 0 to 3, each signal maturing at a random stage, runs arriving at random stages), not Architect's earlier fuzz. Its counts therefore differ from architecture.md's (576 of 3,000 sequences gain a lesson here against 101 there); the properties checked are the same."
  - "The unfixed-main failure of the new tests is shown by copying HEAD's tests/test_decompose_lessons.py into a copy of origin/main (`$S/redcopy`), because the tests are not on main."
  - "Nothing was run live: no model, no `claude plugin eval`, trigger_eval.py or charter_replay.py, and no CI. `treated()` is stubbed wherever the fuzz and repro need votes; the real git ancestry check is exercised only by the real-history CLI run, where the repo has no lessons file to vote on."
---

# Verification: a hit run seen before its clean partner still pairs

## Summary

15 criteria: 15 PASS, 0 FAIL, 0 NOT RUN. The issue's repro is red on
origin/main (update 1 over H alone, update 2 over H + C writes the file but
prints no `ADD replan/feature/added`; the lesson is absent for ever) and green
on HEAD (update 2 prints it, update 3 is `unchanged`, the lesson ids equal the
single-update control). The symmetric case derives on both trees. The eight
new tests fail on origin/main's `decompose_lessons.py` (3 failures, 2 errors;
the other three are regression guards that pass on both by design) and pass on
HEAD (109 tests). Seven mutations of the fixed code were applied; six turn
tests red and one survives (`pairs` taking the last partner), recorded below
as a gap that predates this run, with the first-partner rule confirmed by a
one-off check. A repeated `update` never changes the file in 3,000 random
sequences on HEAD. The real repo history through the CLI writes a file
byte-identical to origin/main's code (96 entries, 6,331 bytes) and a second
`update` is `unchanged`. The whole repo is green: `run_tests.py` (default and
`-j 1`), serial `unittest discover`, `lint.py`, `kb.py drift`, `gates.py` and
`gates.py --selftest`. Observations, not failures: the first-partner mutation
survives the suite, three lines in `decompose_lessons.py` exceed 79 columns
(280, 403, 525; all three pre-date this run), and 576 of 3,000 sequences gain
a lesson on HEAD in this fuzz. See Not verified for what no check here can
show. Next stage: Review.

## Criteria & evidence

### 1. Defect case 1: a hit run seen before its clean partner pairs once the partner arrives (red on origin/main, green on HEAD)

- Check: `python3 -I repro_issue.py <tree>` run inside `$S/main` (origin/main, the unfixed tree) and `$S/head` (HEAD). H is `feature:h` re-plan 2 of 10, C is `feature:c` 0 of 8; two maintenance runs keep a ledger on disk.
- Evidence (origin/main):
  ```
  stage1 (H only): (['decompose-lessons: ADD replan/maintenance/dropped', 'decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'], [])
  header after 1: {"seen": ["replan:feature:h", "replan:maintenance:m", "replan:maintenance:n"]}
  stage2 (H + C): (['decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'], [])
  stage3 (H + C again): (['decompose-lessons: unchanged'], [])
  lesson ids: ['replan/maintenance/dropped']
  control (H + C once): (['decompose-lessons: ADD replan/feature/added', 'decompose-lessons: ADD replan/maintenance/dropped', 'decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'], [])
  ```
  HEAD:
  ```
  stage1 (H only): (['decompose-lessons: ADD replan/maintenance/dropped', 'decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'], [])
  header after 1: {"seen": ["replan:feature:h", "replan:maintenance:m", "replan:maintenance:n"]}
  stage2 (H + C): (['decompose-lessons: ADD replan/feature/added', 'decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'], [])
  stage3 (H + C again): (['decompose-lessons: unchanged'], [])
  lesson ids: ['replan/feature/added', 'replan/maintenance/dropped']
  control (H + C once): (['decompose-lessons: ADD replan/feature/added', 'decompose-lessons: ADD replan/maintenance/dropped', 'decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'], [])
  ```
  On origin/main stage 2 prints no `ADD replan/feature/added` and the lesson id is missing from the file; on HEAD stage 2 prints it and the id set equals the control's. The header after stage 1 is identical on both (`replan:feature:h` seen).
- Result: PASS

### 2. Symmetric case: a clean run seen before any hit exists still derives the lesson, header unchanged

- Check: case 2 of the same script on both trees.
- Evidence (identical on origin/main and HEAD):
  ```
  stage1 (C only): (['decompose-lessons: ADD replan/maintenance/dropped', 'decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'], [])
  header after 1: {"seen": ["replan:feature:c", "replan:maintenance:m", "replan:maintenance:n"]}
  stage2 (H + C): (['decompose-lessons: ADD replan/feature/added', 'decompose-lessons: wrote docs/factory/decompose-lessons.jsonl'], [])
  lesson ids: ['replan/feature/added', 'replan/maintenance/dropped']
  header after 2: {"seen": ["replan:feature:c", "replan:feature:h", "replan:maintenance:m", "replan:maintenance:n"]}
  ```
  The header after each stage is byte-identical to what the old rule writes (architecture.md, accepted change 5).
- Result: PASS

### 3. The new tests fail against origin/main's `decompose_lessons.py` and pass on HEAD

- Check: HEAD's `tests/test_decompose_lessons.py` copied into a copy of origin/main (`$S/redcopy`), `python3 -m unittest tests.test_decompose_lessons` there and in `$S/head`. The eight added tests are the `+    def test` lines of `git diff origin/main -- tests/test_decompose_lessons.py`.
- Evidence (origin/main code, HEAD tests):
  ```
  ERROR: test_partners_are_the_clean_runs_of_a_kind_and_label_in_order (tests.test_decompose_lessons.TestFold...)
  ERROR: test_spent_is_only_a_seen_hit_run_with_a_seen_partner (tests.test_decompose_lessons.TestFold...)
  FAIL: test_a_seen_hit_run_pairs_when_its_partner_arrives_later (tests.test_decompose_lessons.TestFold...)
  FAIL: test_an_unpaired_hit_run_that_votes_still_pairs_later (tests.test_decompose_lessons.TestFold...)
  FAIL: test_a_hit_run_seen_before_its_partner_is_derived_later (tests.test_decompose_lessons.TestUpdate...)
  Ran 109 tests in 0.058s
  FAILED (failures=3, errors=2)
  ```
  HEAD:
  ```
  Ran 109 tests in 0.055s
  OK
  ```
  The three added tests that pass on origin/main are regression guards for behaviour that must not change (`test_a_seen_hit_run_with_a_seen_partner_stays_skipped`, `test_a_repeat_after_the_late_partner_is_unchanged`, `test_a_clean_run_seen_before_any_hit_still_derives_later`). breakdown.md P1 requires cases 1, 5 and 6 to fail before P2; all three do (the `_partners` and `_spent` cases error because the helpers do not exist on main).
- Result: PASS

### 4. Mutations of the fixed code: each made in a `git archive HEAD` copy, shown applied, each turning at least one test red

- Check: `$S/mut.py` copies `$S/head` to `$S/mut/mN`, asserts the target text occurs exactly once, replaces it, prints the unified diff, then runs `python3 -m unittest tests.test_decompose_lessons` in the copy. Output in `$S/mut.out`.
- Evidence (diff lines, then result; names truncated of their class):
  ```
  ## m1 fold skips all seen (skip=set(seen))
  -    new_pairs = pairs(records, skip=_spent(records, set(seen)))
  +    new_pairs = pairs(records, skip=set(seen))
  FAIL: test_a_seen_hit_run_pairs_when_its_partner_arrives_later
  FAIL: test_an_unpaired_hit_run_that_votes_still_pairs_later
  FAIL: test_a_hit_run_seen_before_its_partner_is_derived_later
  ['Ran 109 tests in 0.456s', 'FAILED (failures=3)']
  ## m2 _spent ignores the seen-partner condition
  -            if any(seen_key(field, c["run"]) in seen for c in _partners(
  -                    records, field, num, kind(hit["run"]), figure[0])):
  +            if True:
  ['Ran 109 tests in 0.246s', 'FAILED (failures=4)']
  ## m3 _partners ignores the label
  -            and _hit_label(r[field], num) == (label, 0)]
  +            and _hit_label(r[field], num) is not None and _hit_label(r[field], num)[1] == 0]
  ['Ran 109 tests in 0.254s', 'FAILED (failures=7)']
  ## m4 _partners ignores the run kind
  -    return [r for r in records if kind(r["run"]) == run_kind
  +    return [r for r in records if True
  ['Ran 109 tests in 0.423s', 'FAILED (failures=6)']
  ## m5 pairs takes the last partner
  -            clean = next(iter(_partners(records, field, num, run_kind,
  -                                        label)), None)
  +            _p = _partners(records, field, num, run_kind, label)
  +            clean = _p[-1] if _p else None
  ['Ran 109 tests in 0.254s', 'OK']
  ## m6 _spent partner need not be seen
  -            if any(seen_key(field, c["run"]) in seen for c in _partners(
  +            if any(True for c in _partners(
  ['Ran 109 tests in 0.262s', 'FAILED (failures=4)']
  ## m7 _spent counts clean runs as spent too (drops the count-0 guard)
  -            if figure is None or figure[1] == 0 \
  -                    or seen_key(field, hit["run"]) not in seen:
  +            if figure is None or seen_key(field, hit["run"]) not in seen:
  ['Ran 109 tests in 0.163s', 'FAILED (failures=1)']
  ```
  Red tests include, for m1, the three tests of criterion 3; for m2 and m6, `test_spent_is_only_a_seen_hit_run_with_a_seen_partner`; for m3 and m4, `test_partners_are_the_clean_runs_of_a_kind_and_label_in_order`, `test_pairs_match_the_hand_worked_history` and `test_two_pairs_with_one_id_collapse_to_one_lesson_with_both_sources`; for m7 only `test_spent_is_only_a_seen_hit_run_with_a_seen_partner`. m5 is the survivor: no test places two clean runs of the same kind and label before a hit run and checks which one is the exemplar. The same m5 change applied to origin/main's inline form of that lookup also leaves its 101 tests green (`m5main`, `Ran 101 tests ... OK`), so the gap predates this run. Criterion 5 covers the behaviour directly.
- Result: PASS (6 of 7 mutations killed; every mutation of the new code `_spent`, `_partners` and fold's skip is killed; the one survivor is a pre-existing gap in `pairs`, reported under Not verified and for Review)

### 5. First partner in record order (architecture.md pinned behaviour), checked once by hand because mutation m5 survives

- Check: `$S/first.py <tree>`: H followed by two clean runs of the same kind and label, in both record orders, on HEAD and on origin/main.
- Evidence (identical on both trees):
  ```
  head
  [('feature:h', 'feature:c1')]
  [('feature:h', 'feature:c2')]
  main
  [('feature:h', 'feature:c1')]
  [('feature:h', 'feature:c2')]
  ```
  The exemplar is the first clean run in record order, as before.
- Result: PASS

### 6. A repeated `update` never changes the file (idempotence), votes on and off, no double vote

- Check: `$S/idem.py <tree> 1500` on HEAD and on origin/main: per sequence, 3 stages, each stage's `update` is run twice and the file bytes (and the problem list) compared after the first and second call. Votes off: nothing treated. Votes on: a random 70 percent of runs treated (stubbed). Counts are cumulative across the two passes.
- Evidence:
  ```
  ## head
  votes=False: 1500 sequences x 3 stages, each stage updated twice; sequences where the repeat changed the file: 0
  votes=True: 1500 sequences x 3 stages, each stage updated twice; sequences where the repeat changed the file: 0
  ## main
  votes=False: 1500 sequences x 3 stages, each stage updated twice; sequences where the repeat changed the file: 0
  votes=True: 1500 sequences x 3 stages, each stage updated twice; sequences where the repeat changed the file: 0
  ```
  A file that changed on a repeat would include a changed `voted` list or importance, so 0 also covers the double vote. The same runs, compared by final lesson ids: of 3,000 sequences, 0 have a lesson id on origin/main that HEAD lacks, and 576 have one HEAD derives that origin/main does not (the fix; see Summary for the count difference from architecture.md).
  ```
  of 3000 sequences: main derives an id HEAD lacks: 0 | HEAD derives an id main lacks: 576
  ```
- Result: PASS

### 7. Real repo history through the CLI at HEAD: update twice, second is `unchanged`, file identical to origin/main's code

- Check: `git clone` of this repo checked out at HEAD in `$S/clone` (no lessons file existed; this repo's own `docs/factory/decompose-lessons.jsonl` was never written). `python3 decompose_lessons.py update` twice, `cmp` of the file after each. Then a second clone with `decompose_lessons.py` replaced by origin/main's, one `update`, `cmp` against HEAD's file.
- Evidence:
  ```
  --- update 1
  decompose-lessons: ADD design_gaps/feature/routed
  decompose-lessons: ADD replan/feature/added
  decompose-lessons: ADD replan/maintenance/dropped
  decompose-lessons: ADD review/feature/named
  decompose-lessons: ADD review/maintenance/named
  decompose-lessons: wrote docs/factory/decompose-lessons.jsonl
  decompose-lessons: 0 problem(s)
  exit=0
  --- update 2
  decompose-lessons: unchanged
  decompose-lessons: 0 problem(s)
  exit=0
  CMP-IDENTICAL
  6331 docs/factory/decompose-lessons.jsonl
  96 entries sorted True unique True
  ```
  origin/main's code over the same history:
  ```
  decompose-lessons: ADD design_gaps/feature/routed
  decompose-lessons: ADD replan/feature/added
  decompose-lessons: ADD replan/maintenance/dropped
  decompose-lessons: ADD review/feature/named
  decompose-lessons: ADD review/maintenance/named
  decompose-lessons: wrote docs/factory/decompose-lessons.jsonl
  decompose-lessons: 0 problem(s)
       6331 docs/factory/decompose-lessons.jsonl
  96 entries
  MAIN-VS-HEAD-FILE-IDENTICAL
  ```
  Header and size match origin/main's output for this repo. The history has no hit run seen before a partner, so the fix changes nothing here; criterion 1 and 6 show the cases where it does.
- Result: PASS

### 8. `seen` stays exactly what ADR-0116 made it (header unchanged), with no new output line or problem string

- Check: header comparison in criteria 1, 2 and 7; diff of `decompose_lessons.py` against origin/main for new constants, outputs and imports.
- Evidence:
  ```
  $ git diff origin/main -U0 -- decompose_lessons.py | grep -E "^[+-] ?(import|from) "
  (no output)
  $ grep -c "^import\|^from" decompose_lessons.py   # HEAD
  10
  $ git show origin/main:decompose_lessons.py | grep -c "^import\|^from"
  10
  $ git diff origin/main --stat -- decompose_lessons.py
   decompose_lessons.py | 32 ++-
  ```
  The changed lines are `_partners`, `_spent`, `pairs` reading its partner from `_partners`, and `fold`'s `skip=_spent(records, set(seen))` (viewed in the file); `NO_PAIR`, `LABEL` and `MAX_LESSONS_BYTES` are not in the diff.
- Result: PASS

### 9. Whole suite green: `run_tests.py` (default and `-j 1`) and serial `unittest discover`

- Check: the three runs, exit codes captured; the serial one ran in the background to a file.
- Evidence:
  ```
  python3 run_tests.py        -> tests: 3814 tests across 118 modules in 28.6s on 8 workers, 0 problem(s)   rc=0
  python3 run_tests.py -j 1   -> tests: 3814 tests across 118 modules in 95.0s on 1 workers, 0 problem(s)    rc=0
  python3 -m unittest discover tests -> Ran 3814 tests in 140.179s / OK / exit=0
  ```
- Result: PASS

### 10. `lint.py`, `kb.py drift`, `gates.py`, `gates.py --selftest` all clean

- Check: each run on HEAD with the exit code captured.
- Evidence:
  ```
  lint: 0 problem(s) across 34 skills          rc=0
  drift: 0 problem(s)                          rc=0
  gates: 0 problem(s)                          rc=0
  selftest: ok                                 rc=0
  ```
- Result: PASS

### 11. Scope: no `skills/` or `.claude-plugin` change, no new import, pin 55, no lessons file, no test against main

- Check: one-off commands, not kept as tests.
- Evidence:
  ```
  $ git diff origin/main --name-only -- skills .claude-plugin | wc -l
         0
  $ git diff origin/main --name-only
  decompose_lessons.py
  docs/adr/0116-the-lessons-seen-header-is-one-entry-per-signal-and-run.md
  docs/adr/0117-a-hit-run-seen-before-its-clean-partner-still-pairs.md
  docs/adr/README.md
  docs/fixes/seen-before-partner/architecture.md
  docs/fixes/seen-before-partner/autorun-brief.md
  docs/fixes/seen-before-partner/breakdown.md
  docs/fixes/seen-before-partner/defect.md
  tests/test_decompose_lessons.py
  $ python3 -c "... len(test_dual_membership.ROOT_ONLY_IMPORTS_MIRRORED)"
  55
  $ python3 -m unittest tests.test_dual_membership  -> Ran 3 tests ... OK
  $ ls docs/factory/decompose-lessons.jsonl; git ls-files | grep -c decompose-lessons.jsonl
  ls: docs/factory/decompose-lessons.jsonl: No such file or directory
  0
  $ grep -c "unchanged against main\|origin/main" tests/test_decompose_lessons.py
  0
  ```
  `tests/test_dual_membership.py` is not in the diff, so the pin is untouched. The `decompose_lessons.py` import diff is empty (criterion 8). No paid run happened (Not verified).
- Result: PASS

### 12. ADR trail agrees with the code (P3)

- Check: ADR-0117 status and statement of behaviour, ADR-0116's status line, the README rows, and the drift check.
- Evidence:
  ```
  docs/adr/0117-...md:  - Status: provisional
  docs/adr/0116-...md:  - Status: superseded in part by ADR-0117 (the pairing skip rule; provisional)
  README.md:139 | 0116 | The lessons file's seen header is one entry per signal and run | superseded in part by ADR-0117 (the pairing skip rule; provisional) |
  README.md:140 | 0117 | A hit run seen before its clean partner still pairs when the partner arrives | provisional |
  README.md:136 | 0113 | (title unchanged) | superseded in part by ADR-0116 (the line-1 seen header entry shape; provisional) |
  drift: 0 problem(s)
  ```
  ADR-0117 states that the skip is decided from `seen` plus a seen partner and that what puts an entry in `seen` is unchanged, which is what criteria 1, 2 and 8 observe. The superseded part is the pairing-skip sentence, the same annotated form ADR-0113 carries for ADR-0116. `git diff origin/main --stat -- docs/adr` shows only these three files.
- Result: PASS

### 13. Accepted behaviour changes hold (architecture.md items 2 and 3): a spent pair stays dropped, and a seen hit run with a seen partner is skipped

- Check: the P1 tests that pin them, on HEAD, run by name.
- Evidence:
  ```
  $ python3 -m unittest -v tests.test_decompose_lessons.TestFold.test_a_seen_hit_run_with_a_seen_partner_stays_skipped tests.test_decompose_lessons.TestUpdate.test_a_clean_run_seen_before_any_hit_still_derives_later tests.test_decompose_lessons.TestUpdate.test_a_repeat_after_the_late_partner_is_unchanged
  test_a_seen_hit_run_with_a_seen_partner_stays_skipped ... ok
  test_a_clean_run_seen_before_any_hit_still_derives_later ... ok
  test_a_repeat_after_the_late_partner_is_unchanged ... ok
  Ran 3 tests ... OK
  ```
- Result: PASS

### 14. An unpaired hit run that votes still pairs later; the vote guard is untouched (P1 case 5)

- Check: criterion 3's `test_an_unpaired_hit_run_that_votes_still_pairs_later` (red on origin/main, green on HEAD), mutation m1 turning it red (criterion 4), and `votes`/`_ballot` absent from the `decompose_lessons.py` diff.
- Evidence:
  ```
  FAIL: test_an_unpaired_hit_run_that_votes_still_pairs_later (origin/main code, HEAD tests)
  FAIL: test_an_unpaired_hit_run_that_votes_still_pairs_later (mutation m1)
  OK on HEAD
  $ git diff origin/main -U0 -- decompose_lessons.py | grep -c "def votes\|def _ballot"
  0
  ```
- Result: PASS

### 15. Brief constraints: stdlib only, no network or model call, read-only on git history

- Check: no new import (criterion 8); the fixed code adds two pure functions; the stub of `treated()` is the only substitute for git in the fuzz.
- Evidence:
  ```
  $ git diff origin/main -U0 -- decompose_lessons.py | grep -E "^\+.*(subprocess|urllib|http|socket|open\()" | wc -l
  0
  ```
- Result: PASS

## Failures

none. One survivor is recorded, not a failure of a criterion: mutation m5
(`pairs` takes the last partner instead of the first) leaves the suite green.
It predates this run (origin/main's inline form of the same lookup also
survives it), the behaviour holds today (criterion 5), and a test that
places two clean runs of one kind and label before a hit run and pins the
exemplar would close it. That is a test to add in Review or a follow-up, not
a route back to Implement for this fix.

## Not verified

- No model run and no live `claude plugin eval`, `trigger_eval.py` or `charter_replay.py`: the change is a pure function inside a free root-only tool, and the brief forbids paid runs. LEDGER maturity is unaffected.
- `treated()` is stubbed in the repro and the fuzz (every record, or a random 70 percent, counts as treated). The real git ancestry check was exercised only by the real-history CLI run (criterion 7), where this repo has no lessons file, so no real vote was cast. Vote behaviour with real ancestry is covered only by the unit tests' `GitFake`.
- No CI run. Everything ran locally on one machine (Darwin, python3 as installed); the four CI jobs have not run on this branch.
- The fuzz generator is mine and covers replan, design-gaps and review counts 0 to 3 with at most 7 runs over 3 stages. It does not prove idempotence for larger ledgers or longer update sequences, and it exercises the file only through `update`, not hand-edited files.
- Mutation m5 survives, as recorded under Failures. Other mutations of untouched code (`votes`, `_ballot`, `fold`'s drop at 0) were out of scope: they are not changed by this run.
- The accepted behaviour changes the architecture documents but gives no test beyond the required ones (sources of a late earlier-in-order clean partner; a pair stranded by an ADR-0116-era file where hit and partner are both already seen) are not exercised here. The stranded case is a documented decision with a recovery (delete the file and run `update`); no lessons file exists in the repo to strand.
- The 79-column observation (lines 280, 403, 525) was measured, not judged: all three are the same length on origin/main, so this change did not add a long line.
- Merging is not verified or attempted: the brief does not authorise it.
