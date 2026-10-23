---
stage: verify
run: maintenance:eval-trends-honest-output
date: 2026-10-22
assumptions:
  - "No prd.md exists for a maintenance run, so the criteria are defect.md's three defects (with their Expected clauses), its four work items' Accept lines, and the autorun brief's constraints (read-only, no new import, pin 55, no permanent test against main, stdlib only). defect.md's Work items stand in for breakdown.md (re-entry: implement) and all four are checked, so the soft gate holds."
  - "origin/main is 8bf52f5 and is an ancestor of HEAD bd399ef (`git merge-base --is-ancestor`), so no merge was needed. The 'unfixed' tree is `git archive origin/main` extracted to a scratchpad copy; the mutation trees are `git archive HEAD` copies. No mutation was applied in this tree; `git status --porcelain` printed nothing after them."
  - "The real-over-bound case is a sparse file of 4 MiB + 1 byte (0 bytes on disk) in the scratchpad, deleted afterwards. Small-file cases patch the constant (mock / module attribute) as the brief allows. 'No read' is shown by replacing eval_trends.read_file with a function that exits `READ ATTEMPTED` and observing that it never fires."
  - "Nothing was run live: no model, no `claude plugin eval`, trigger_eval.py or charter_replay.py."
---

# Verification: eval_trends prints output it cannot back

## Summary

14 criteria: 14 PASS, 0 FAIL, 0 NOT RUN. Each defect reproduces on
origin/main and is changed on HEAD; the new tests fail on origin/main's
`eval_trends.py` (4 failures, 4 errors) and pass on HEAD; seven mutations
of the fixed code each turn at least one test red. The real repo's output
is byte-identical to origin/main's, the whole suite is green on three runs
plus a serial `unittest discover`, and lint, drift, gates, selftest are
clean; `one_owner.py` is at its baseline of 9. Two observations are
recorded, not failures: `architecture.md:170` still prints `95%` in both
day slots of the grammar line (line 171 then qualifies the multi-record
day), and the symlinked-record refusal also converts a main-side crash on
a dangling link (see criterion 5). Next stage: Review.

## Criteria & evidence

Scratch: `S=/private/tmp/claude-501/-Users-mbutler-github-skills/9a27056e-40ad-47c2-a869-dd1e59a7bd2e/scratchpad`;
`$S/main` is `git archive origin/main`; `$R` is this repo.

### 1. Defect 1: an empty or record-less root says so in one line (was: 13 lines, `0 problem(s)`)

- Check: `python3 eval_trends.py` on an empty directory and on `docs` (exists, holds no records), on HEAD and on the origin/main copy
- Evidence (HEAD):
  ```
  ### FIXED $S/v/empty
  eval-trends: no records found under $S/v/empty
  eval-trends: 0 problem(s)
  exit=0
  ### FIXED /Users/mbutler/github/skills/docs
  eval-trends: no records found under /Users/mbutler/github/skills/docs
  eval-trends: 0 problem(s)
  exit=0
  ```
  origin/main, same two roots: the 13-line output of defect.md (`eval-trends: trigger: 0 record(s)` ... `REFUSED decompose-signals ...` ... `eval-trends: 0 problem(s)`), exit=0, identical for both roots.
- Result: PASS

### 2. A mistyped path is still a usage error; a root with one malformed record is still a failure and is not "empty"

- Check: nonexistent path; a root holding `evals/results/trigger-2026-07-01.json` = `{}`; HEAD and origin/main
- Evidence (HEAD; origin/main prints the same, line for line):
  ```
  eval-trends: '$S/v/nonexist' is not a directory

    python3 eval_trends.py [<repo-root>]
  exit=2
  ...
  eval-trends: trigger: 0 record(s)
  ...(five 0-record / REFUSED lines, as main)
  eval-trends: evals/results/trigger-2026-07-01.json missing field date
  eval-trends: 1 problem(s)
  exit=1
  ```
  No `no records found` line appears on the malformed root.
- Result: PASS

### 3. The real repo's output is byte-identical to origin/main's tool on the same tree

- Check: both tools run with the same explicit root `$R`; `diff`, `cmp`, and the default-root run; before/after hashes of `evals/results`, `plugin-evals/records`, `tests/fixtures` (content and mtimes)
- Evidence:
  ```
  diff $S/fixed.out $S/main.out && echo BYTE-IDENTICAL  ->  BYTE-IDENTICAL   (17 lines, fixed=0 main=0)
  cmp ok; default-root run `python3 eval_trends.py` == explicit-root output (exit 0)
  before: 32452675ce869c98556dfea31968438712286719 / b24ecd1e4aa5a239aaeaf6ef2a3c5f58cc3b81fb
  after:  32452675ce869c98556dfea31968438712286719 / b24ecd1e4aa5a239aaeaf6ef2a3c5f58cc3b81fb
  (content hash / mtime hash, both unchanged; last line `eval-trends: 0 problem(s)`)
  ```
- Result: PASS

### 4. Defect 2: a multi-record day prints `range lo-hi`, never `95%`; a single-record day keeps `95% lo-hi`

- Check: root with `trigger-2026-07-01` (12/30) and two 2026-07-02 reruns (24/30, 27/30), HEAD vs origin/main
- Evidence:
  ```
  FIXED: 2026-07-01 12/30 (40.0%, 95% 24.6-57.7%) -> 2026-07-02 24..27/30 (80.0..90.0%, range 62.7-96.5%); intervals do not overlap ...
  MAIN : 2026-07-01 12/30 (40.0%, 95% 24.6-57.7%) -> 2026-07-02 24..27/30 (80.0..90.0%, 95% 62.7-96.5%); intervals do not overlap ...
  ```
  `git grep -n -i -E "95%|hull"` excluding verification.md/release.md/review.md and this run's directory: the only code site is `eval_trends.py:449 label = "95%" if len(rows) == 1 else "range"`; tests carry `95%` only on single-record expectations (`test_eval_trends_render.py:53,337`) and `assertNotIn("95%", day2)` (`:296`); `architecture.md:143` ("interval = hull of Wilson intervals") and `:295` name the hull as a hull, not as 95; `architecture.md:170` (grammar, see Observations) and `:171`:
  `where a single-record day prints its Wilson interval as `95% <lo>-<hi>%`, and a multi-record day prints its lowest-to-highest rate and, in place of `95%`, `range <lo>-<hi>%`: the span its reruns' own intervals cover (no confidence level claimed)`.
  The `_day_text` docstring no longer says "95 percent hull" (diff above in `git diff origin/main...HEAD -- eval_trends.py`).
- Result: PASS

### 5. Defect 3a: a symlinked record, a record under a symlinked directory, and a dangling link are each one labelled problem, exit 1, no row, no read; a symlinked ROOT is allowed

- Check: roots built under `$S/sym` (file link to a record outside the root; directory link to a copied `decompose-2026-07-01` outside; dangling link; the root itself a link). HEAD vs origin/main; on HEAD with `eval_trends.read_file` replaced by a function that exits `READ ATTEMPTED` (it never fired).
- Evidence (HEAD, grep of the relevant lines):
  ```
  file link:   eval-trends: evals/results/trigger-2026-07-01.json is a symlink; not read          | 1 problem(s) | exit=1 | trigger: 0 record(s)
  dir link:    eval-trends: evals/results/output/decompose-2026-07-01/grading.json is under a symlinked directory; not read | 1 problem(s) | exit=1 | output: 0 record(s)
  dangling:    eval-trends: evals/results/trigger-2026-07-01.json is a symlink; not read          | 1 problem(s) | exit=1
  link root:   eval-trends: trigger: 1 record(s), 2026-07-01..2026-07-01, 1 day(s), cases 47-47 per record ... 0 problem(s) | exit=0
  ```
  origin/main on the same roots: file link `trigger: 1 record(s) ... 0 problem(s)` exit=0 (followed); dir link `output: 1 record(s) ... 0 problem(s)` exit=0 (followed); symlinked root identical to HEAD; dangling link a crash:
  ```
  File ".../main/eval_trends.py", line 202, in _trigger_row
      if data.get("harness", harness) != harness:
  AttributeError: 'NoneType' object has no attribute 'get'
  exit=1
  ```
  (a pre-existing traceback on a dangling link that the HEAD refusal also removes; not in the brief's scope, noted as a side effect.)
- Result: PASS

### 6. Defect 3b: a file one byte over MAX_RECORD_BYTES is refused unread; a file exactly at the bound is read

- Check: (a) a 16,388-byte record with the constant patched to 16,388 and to 16,387; (b) a real sparse file of 4 MiB + 1 byte (`os.stat` 4194305, 0 bytes on disk) with the real constant, through the CLI and with `read_file` booby-trapped; (c) a sparse file of exactly 4 MiB
- Evidence:
  ```
  at bound (patched=size):      trigger: 1 record(s) ... 0 problem(s)            exit=0
  one over (patched=size-1):    eval-trends: evals/results/trigger-2026-07-01.json is 16388 bytes, above the 16387-byte bound; not read
                                eval-trends: 1 problem(s)                        exit=1   (READ ATTEMPTED never fired)
  sparse 4 MiB+1, real constant: eval-trends: evals/results/trigger-2026-07-01.json is 4194305 bytes, above the 4194304-byte bound; not read
                                eval-trends: 1 problem(s)                        exit=1   (CLI; and booby-trapped read_file: never fired)
  sparse exactly 4 MiB:          eval-trends: evals/results/trigger-2026-07-01.json is not valid JSON: Expecting value: line 1 column 1 (char 0)   exit=1  (read, then rejected as malformed: at the bound is read)
  ```
  The constant is `MAX_RECORD_BYTES = 4 * 1024 * 1024`, 59.4x the largest real record (70,641 bytes, defect.md table); `test_the_bound_is_a_clear_multiple_of_the_largest_real_record` asserts >= 50x.
- Result: PASS

### 7. The regression tests fail on the unfixed code and pass on the fixed code

- Check: origin/main extracted to `$S/red`; HEAD's `tests/test_eval_trends.py` and `tests/test_eval_trends_render.py` copied over; `eval_trends.py` there is origin/main's (`diff -q` differs from HEAD's, as expected)
- Evidence:
  ```
  RED  (origin/main eval_trends.py): Ran 74 tests ... FAILED (failures=4, errors=4)
    ERROR: test_a_dangling_symlink_is_a_problem_too
    ERROR: test_a_file_at_the_bound_is_read              (no MAX_RECORD_BYTES to patch)
    ERROR: test_one_byte_over_the_bound_is_refused_unparsed
    ERROR: test_the_bound_is_a_clear_multiple_of_the_largest_real_record
    FAIL:  test_a_symlinked_directory_above_a_record_is_a_problem
    FAIL:  test_a_symlinked_record_is_a_problem_not_a_row
    FAIL:  test_an_empty_root_prints_one_line_and_exits_zero
    FAIL:  test_days_are_compared_by_hull_with_the_rate_range
  GREEN (HEAD): Ran 74 tests in 0.084s  OK
  ```
  The two control tests that pass on both (`test_a_root_with_a_record_is_unchanged`, `test_a_root_whose_only_record_is_malformed_is_not_empty`) are guards against over-firing, not regressions; they are exercised by mutation 2 below.
- Result: PASS

### 8. Mutation: the no-records line

- Check: in a `git archive HEAD` copy, run `tests.test_eval_trends tests.test_eval_trends_render`
- Evidence:
  ```
  -    if not rows and not problems:  # empty or mistyped root, not a quiet one
  +    if False:  # empty or mistyped root, not a quiet one
  FAIL: test_an_empty_root_prints_one_line_and_exits_zero ... FAILED (failures=1)

  -    if not rows and not problems:  # ...
  +    if not rows:  # ...                       (fires when a malformed record exists)
  FAIL: test_a_root_whose_only_record_is_malformed_is_not_empty ... FAILED (failures=1)
  ```
- Result: PASS

### 9. Mutation: size comparison `>` to `>=`, and the size check removed

- Evidence:
  ```
  -    if size > MAX_RECORD_BYTES:
  +    if size >= MAX_RECORD_BYTES:
  FAIL: test_a_file_at_the_bound_is_read ... FAILED (failures=1)

  -    if size > MAX_RECORD_BYTES:
  +    if False:
  ERROR: test_one_byte_over_the_bound_is_refused_unparsed ... FAILED (errors=1)
  ```
- Result: PASS

### 10. Mutation: symlink check dropped

- Evidence:
  ```
  -    if path.is_symlink():
  +    if False:
  ERROR: test_a_dangling_symlink_is_a_problem_too
  FAIL: test_a_symlinked_record_is_a_problem_not_a_row        FAILED (failures=1, errors=1)
  ```
- Result: PASS

### 11. Mutation: hull label back to `95%` for multi-record days

- Evidence:
  ```
  -    label = "95%" if len(rows) == 1 else "range"
  +    label = "95%"
  FAIL: test_days_are_compared_by_hull_with_the_rate_range ... FAILED (failures=1)
  ```
- Result: PASS

### 12. Mutation: directory-symlink check dropped

- Evidence:
  ```
  -    if any((Path(root) / parent).is_symlink()
  +    if False and any((Path(root) / parent).is_symlink()
  FAIL: test_a_symlinked_directory_above_a_record_is_a_problem ... FAILED (failures=1)
  ```
  All seven mutants were in `$S/mut_*` copies; `git status --porcelain` in this tree printed nothing.
- Result: PASS

### 13. Scope and read-only claims

- Check: one-off commands
- Evidence:
  ```
  git diff --stat origin/main...HEAD:
   architecture.md (1 line), autorun-brief.md, defect.md, eval_trends.py (+50/-), tests/test_eval_trends.py (+67), tests/test_eval_trends_render.py (28)   6 files
  import lines added across eval_trends.py and both tests: `+from unittest import mock` (stdlib, test_eval_trends.py only); eval_trends.py adds none
  tests.test_dual_membership: Ran 3 tests ... OK; ROOT_ONLY_IMPORTS_MIRRORED has 55 pairs
  grep of the added test lines for origin/main|git |subprocess|unchanged against|main: no matches
  evals/results, plugin-evals/records, tests/fixtures: content and mtime hashes equal before and after a run (criterion 3)
  ```
  `.claude-plugin/plugin.json` and `LEDGER.md` are not in the diff stat.
- Result: PASS

### 14. Whole-repo checks

- Evidence:
  ```
  python3 run_tests.py           tests: 3781 tests across 118 modules in 28.9s on 8 workers, 0 problem(s)   exit=0
  python3 run_tests.py (again)   tests: 3781 tests across 118 modules in 28.1s on 8 workers, 0 problem(s)   exit=0
  python3 run_tests.py -j 16     tests: 3781 tests across 118 modules in 25.0s on 16 workers, 0 problem(s)   exit=0
  python3 -m unittest discover tests   Ran 3781 tests in 87.646s  OK
  python3 lint.py                lint: 0 problem(s) across 34 skills
  python3 kb.py drift            drift: 0 problem(s)
  python3 gates.py               gates: 0 problem(s)
  python3 gates.py --selftest    selftest: ok
  python3 one_owner.py           one-owner: 9 problem(s)   (baseline 9)
  ```
- Result: PASS

## Failures

none.

## Observations (not failures)

- `docs/features/eval-trends/architecture.md:170`, the trend-line grammar, still writes `95%` in both day slots; line 171, directly under it, states that a multi-record day prints `range` in place of `95%`. A strict reader of line 170 alone could still read the second slot as 95. Review may want the grammar line to show the alternation; left as written because the work item's Accept line asked only that the text be updated.
- Two of the seven mutants (the no-records `if False` and the size `>=`) are each caught by exactly one test; the others by one or two. No mutant survived.

## Not verified

- A multi-record `range` line on the real tree: none prints today (every real group is refused), so the label is verified on a built root and in tests only.
- Behavior on a filesystem where `stat` fails after `glob` (a race); `_refusal` returns None there and `read_file` reports it. Not exercised.
- Windows symlink semantics; the tool and run are macOS-only here.
- No live eval, model, routing or charter-replay run (by instruction).
