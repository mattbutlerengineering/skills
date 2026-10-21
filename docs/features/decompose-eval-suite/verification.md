---
stage: verify
run: feature:decompose-eval-suite
date: 2026-10-20
assumptions:
  - "No live interview: the autorun brief holds no Verify-specific answers, so the skill's defaults were taken. The criteria list is prd.md's eleven success criteria plus the breakdown acceptance criteria no PRD criterion covers, plus a judgement of the breakdown Notes' deviations."
  - "Every piece of evidence was run on HEAD de59da1 in this session; nothing is carried over from the Implement stage's report."
  - "Recommended default taken (flake re-check): five full-suite runs (two at the default 8 workers, two at -j 16, one serial unittest discover) after the first default run."
  - "Recommended default taken (protected paths): compared with the three-dot form origin/main...HEAD. origin/main (5179e5c) equals the merge-base, so the diff holds exactly this run's work; Implement's deviation 3 (a stale local main) does not arise from this form."
  - "Recommended default taken (mutations): applied only in a git archive copy under the scratchpad directory; this tree was never mutated."
  - "Nothing here invoked claude plugin eval or any model; the harness suite is judged statically only."
---

# Verification: A scored, offline-gradable eval suite for Decompose

## Summary

11 of 11 PRD success criteria PASS, 0 FAIL, 0 NOT RUN, on HEAD de59da1. The
breakdown acceptance criteria no PRD criterion covers also pass. Six full
runs were green (3627 tests, 111 modules; two at 8 workers, two at -j 16,
one more 8-worker run before them, one serial discover). Four mutations of
load-bearing behaviour each applied (diff shown) and each made tests fail.
The three Implement deviations do not contradict a PRD criterion or
architecture.md. Caveats the verdict does not hide: (1) the harness case
`csv-export-cut` was checked statically only, by design; whether the
harness accepts it, and whether the sibling `fixtures/` directory (which
has no `case.yaml`) is ignored by the harness's case discovery, is UNKNOWN
until a paid run, which is out of scope (see Not verified). (2) On two real
shipped breakdowns the grader prints one of two perfect scores and one
false-positive dangling line; a documented limit, reported below.

## Criteria & evidence

### 1. The good cut scores differently from, and strictly higher than, every bad cut; the good cut emits no defect line

- Check: ran `python3 decompose_grade.py <cut> evals/fixtures/decompose-feature/docs/features/csv-export/architecture.md .../prd.md` on all five cuts, and the table tests.
- Evidence:
  ```
  good          score 1.000 (coverage 1.000, dependencies 1.000, accept 1.000, sizing 1.000)  0 problem(s)  exit 0
  bad-coverage  score 0.938 (coverage 0.750, dependencies 1.000, accept 1.000, sizing 1.000)  exit 1
  bad-dangling  score 0.964 (coverage 1.000, dependencies 0.857, accept 1.000, sizing 1.000)  exit 1
  bad-accept    score 0.958 (coverage 1.000, dependencies 1.000, accept 0.833, sizing 1.000)  exit 1
  bad-sized     score 0.958 (coverage 1.000, dependencies 1.000, accept 1.000, sizing 0.833)  exit 1
  tests: test_the_good_cut_emits_nothing_and_scores_one ... ok
         test_each_bad_cut_emits_exactly_its_own_line_and_a_lower_score ... ok
  ```
  Hand recomputation from the files (not from the tool): the fixture
  architecture has 4 `###` components under Components (Export API, Export
  Scheduler, CSV Generator, Delivery); good.md has 6 checkbox rows. bad-coverage
  differs from good by one line (S5 stops saying "Delivery"; grep finds no other
  "Delivery" in the cut) so coverage is 3/4 = 0.75 and the mean is
  (0.75+1+1+1)/4 = 0.9375, printed 0.938. good.md's Blocked by lines give
  S1 x3, S4, and "S2; S3; S5" = 3, so 7 edges (the "—" line makes none);
  bad-dangling changes S5 to S9, so 6/7 = 0.857 and the mean is
  (1+0.857+1+1)/4 = 0.964. bad-accept: 5/6 = 0.833, mean 0.958. bad-sized:
  one of six rows names four components, 5/6, mean 0.958. All match.
- Result: PASS

### 2. Coverage miss: line names the component; exact string asserted

- Evidence:
  ```
  bad-coverage: coverage-miss: component "Delivery" is named by no item
  tests: test_a_component_named_by_no_row_block_is_a_miss ... ok
  ```
- Result: PASS

### 3. Dangling Blocked by: line names both items; exact string asserted

- Evidence:
  ```
  bad-dangling: dangling-blocked-by: S6 is blocked by "S9", which names no item
  tests: test_two_dangling_elements_give_two_lines_in_item_order ... ok
  ```
- Result: PASS

### 4. Untestable Accept: line names the item; a concrete Accept emits none

- Evidence:
  ```
  bad-accept: untestable-accept: S3 has no checkable Accept line (unanchored)
  (bad-accept diff vs good: "Accept: works correctly and handles errors appropriately.")
  tests: test_a_concrete_accept_line_emits_nothing ... ok
         test_filler_words_with_no_anchor_earn_nothing ... ok
         test_an_empty_accept_line_is_empty / ..._placeholder ... ok
  ```
- Result: PASS

### 5. Mis-sized item: line names the item and its size

- Evidence:
  ```
  bad-sized: mis-sized: S6 names 4 components (limit 3)
  tests: test_an_item_naming_four_components_is_mis_sized ... ok
         test_an_item_naming_exactly_three_is_not ... ok
  ```
- Result: PASS

### 6. Each bad cut fails only its own class

- Check: the table above shows exactly one defect line per bad cut and only that part below 1.000; the test asserts it by exact string, and the diffs show each bad cut is a 1-line edit of good.md.
- Evidence:
  ```
  diff good bad-dangling:  < Blocked by: S2; S3; S5   > Blocked by: S2; S3; S9
  diff good bad-accept:    one Accept line replaced by the hedge
  diff good bad-sized:     one row title rewritten to name four components
  diff good bad-coverage:  one row title stops naming Delivery
  tests: test_each_bad_cut_emits_exactly_its_own_line_and_a_lower_score ... ok
         test_each_bad_cut_differs_from_good_by_at_most_two_lines ... ok
         test_each_check_is_what_flags_its_bad_cut ... ok
  ```
- Result: PASS

### 7. Wired so `--tag decompose` selects it, checked statically

- Check: tests/test_decompose_suite.py (15 cases) plus layout comparison with plugin-evals/lean/cut-list. Same four parts (case.yaml, prompt.md, scaffold.sh, graders/), same case.yaml shape (schema_version "1.1", name, context.scaffold_script), prompt frontmatter `tags: [decompose]`. `.claude-plugin/plugin.json` still has `"experimental": {"evals": "plugin-evals"}`. The seven grader files exist with types file_exists, regex, tool_used, llm (none code-running).
- Evidence:
  ```
  test_every_decompose_case_carries_the_decompose_tag ... ok
  test_the_manifest_points_evals_at_the_plugin_evals_directory ... ok
  test_the_case_directory_holds_the_four_parts ... ok
  test_each_grader_has_its_type_and_none_runs_code ... ok
  test_the_prd_heredoc_equals_the_fixture_file ... ok
  test_the_architecture_heredoc_equals_the_fixture_file ... ok
  ```
  (The two heredoc tests are also the scaffold.sh == fixtures check.)
- Result: PASS (static only; see Not verified)

### 8. No network call, no model call, stdlib only

- Evidence:
  ```
  decompose_grade.py imports: re, sys, decompose_signals.item_keys, knowledge_plane.breakdown_rows;
  function-level only: cli.read_file, cli.report (inside _read_all and main)
  tests: test_module_level_imports_are_stdlib_and_the_two_leaf_modules ... ok
         test_no_import_anywhere_reaches_the_network_or_a_model ... ok
         test_the_core_does_not_import_cli ... ok
         test_nothing_in_the_case_runs_the_offline_grader ... ok
  ```
  I invoked no claude CLI and no model.
- Result: PASS

### 9. No existing eval definition is edited

- Evidence:
  ```
  $ git diff --name-status origin/main...HEAD  (plugin-evals and evals entries)
  A plugin-evals/decompose/... (12 files, all A)
  $ git diff origin/main...HEAD -- evals skills factory plugin-evals/lean plugin-evals/knowledge-base plugin-evals/implement plugin-evals/next | wc -l
  0
  tests: test_the_protected_paths_match_main ... ok
  ```
  The only modified (M) files are CLAUDE.md, docs/adr/README.md, factory.py, tests/test_dual_membership.py.
- Result: PASS

### 10. LEDGER.md byte-identical, no new file in plugin-evals/records/, plugin.json version unchanged

- Evidence:
  ```
  $ git diff origin/main...HEAD -- .claude-plugin LEDGER.md skills evals factory | wc -l   -> 0
  $ git diff origin/main...HEAD -- plugin-evals/records | wc -l                            -> 0
  ```
- Result: PASS

### 11. run_tests, lint, kb drift, gates, gates --selftest all pass

- Evidence:
  ```
  python3 run_tests.py        tests: 3627 tests across 111 modules in 25.3s on 8 workers, 0 problem(s)
  python3 lint.py             lint: 0 problem(s) across 34 skills
  python3 kb.py drift         drift: 0 problem(s)
  python3 gates.py            gates: 0 problem(s)
  python3 gates.py --selftest selftest: ok
  ```
  Flake re-check: run_tests.py again at 8 workers twice (25.8s, 26.1s, both 3627 tests, 0 problem(s)); at -j 16 twice (24.3s, 24.0s, both 3627, 0 problem(s)); `python3 -m unittest discover tests`: `Ran 3627 tests in 87.487s` `OK`. No flake seen.
- Result: PASS

## Breakdown acceptance criteria not covered by a PRD criterion

### one_owner baseline and no decompose_grade finding (S18)

- Evidence:
  ```
  one-owner: 9 problem(s)     (nine lines listed; none names decompose_grade)
  ```
- Result: PASS

### Dual-membership pin at 54 pairs (S5, S14, S18)

- Evidence:
  ```
  tests.test_dual_membership: 3 tests OK; diff adds (decompose_grade, knowledge_plane) and (decompose_grade, cli)
  ```
  The root-only importers test sees the function-level cli import.
- Result: PASS

### Front door exit codes and `factory.py` verb (S13, S14)

- Evidence:
  ```
  good cut exit 0; each bad cut exit 1 (see criterion 1)
  test_a_wrong_argument_count_exits_two_and_scores_nothing ... ok
  test_a_missing_file_exits_two ... ok
  test_an_unreadable_file_exits_two_with_the_guarded_read_message ... ok
  test_an_architecture_with_no_components_exits_two_not_one ... ok
  test_no_file_is_written ... ok
  ```
  tests/test_factory_cli.py is in the full green run.
- Result: PASS

### CLAUDE.md names the tool honestly (S17)

- Evidence:
  ```
  drift: 0 problem(s)
  gates: 0 problem(s)
  ```
  Detectors C and I scan the new bullet.
- Result: PASS

### Real shipped breakdowns (documented limit, not a criterion)

The architecture says the grader is calibrated to fixture-spelled breakdowns.
Honest output on two real runs:
```
$ python3 decompose_grade.py docs/features/decompose-lessons/{breakdown,architecture,prd}.md
decompose-grade: score 1.000 (coverage 1.000, dependencies 1.000, accept 1.000, sizing 1.000)   exit 0
$ python3 decompose_grade.py docs/features/size-band-calibration/{breakdown,architecture,prd}.md
decompose-grade: score 0.975 (coverage 1.000, dependencies 0.900, accept 1.000, sizing 1.000)
dangling-blocked-by: S3 is blocked by "row selection and work orders", which names no item   exit 1
```
The size-band-calibration line is a false positive: S3 is blocked by
"S2 Band join, row selection and work orders", and the grader splits Blocked
by on commas, so a label that contains a comma is cut into a fake element.
This is a limit of the comma-split rule that architecture.md specifies
(Blocked by split on `;` and `,`), not a defect in the shipped run.

## Implement's deviations, judged

1. cli imported inside `main`/`_read_all` only. Accepted. S4 forbids cli in
   the core and S14 requires the cli import; function-level import satisfies
   both, the S4 AST test names the front-door functions, and the
   dual-membership pin sees it (verified, 54 pairs). No PRD criterion touched.
2. Accept rule "at least one anchor AND at least 3 words remain". Accepted.
   architecture.md's Accept check says "fewer than 3 words remain" yet its
   assumptions say filler earns nothing and an invented backtick name earns
   nothing; only the stricter reading satisfies all of them. Mutation M2
   below (dropping the anchor-present condition) fails 4 tests, so the choice
   is pinned. The four reasons, strings and exit codes are unchanged, so no PRD
   wording shifts. The architecture's text should be tidied at Review.
3. Scope-check base. Accepted and now moot: `origin/main` equals the merge
   base (5179e5c), so `origin/main...HEAD` is clean and shows only this run.
   Implement's "local main is stale" note is true of the local ref only.

## Mutation checks (git archive copy in the scratchpad, never this tree)

Copy: /private/tmp/claude-501/-Users-mbutler-github-skills/9a27056e-40ad-47c2-a869-dd1e59a7bd2e/scratchpad/m. Each diff applied (the script asserts the target text occurs once) and was reverted before the next.
```
M1 component-count threshold
-MAX_SPAN = 3
+MAX_SPAN = 4
  -> FAILED (failures=6): test_an_item_naming_four_components_is_mis_sized, test_each_bad_cut_emits_exactly_its_own_line_and_a_lower_score, ...
M2 Accept anchor rule
-    if found == 0 or len(_WORD.findall(rest)) < MIN_WORDS:
+    if len(_WORD.findall(rest)) < MIN_WORDS:
  -> FAILED (failures=4): test_filler_words_with_no_anchor_earn_nothing, test_a_backticked_name_absent_from_the_fixture_earns_nothing, ...
M3 drop the coverage defect check
-    missed = [name for name in graded
+    missed = [name for name in graded if False and True
  -> FAILED (failures=5): test_a_component_named_by_no_row_block_is_a_miss, test_each_check_is_what_flags_its_bad_cut, ...
M4 dependency resolution always true
-    return re.match(rf"{re.escape(key)}(?!\w)", element) is not None
+    return True
  -> FAILED (failures=8): test_a_key_is_matched_at_a_word_boundary, test_each_bad_cut_emits_exactly_its_own_line_and_a_lower_score, ...
```
Unmutated baseline in the same copy: tests.test_decompose_grade Ran 62, OK.

## Failures

none.

## Not verified

- The harness case `csv-export-cut` was never run (`claude plugin eval` is out
  of scope and was not invoked). So UNKNOWN: whether the harness loads it, and
  whether `plugin-evals/decompose/fixtures/` (a directory with no case.yaml
  beside the case) is skipped by case discovery. The `knowledge-base` suite
  keeps a non-case `seed.sh` beside its cases, a weak precedent only. A
  first paid run is the Owner's follow-up and would settle it.
- The four `llm` graders are model judgement; not exercised.
- The grader on real model output: out of scope.
- The grader's known limits (an unlisted hedge plus three words passes; an
  anchor-stuffed vague line passes; splitting a lump into tiny items passes;
  commas inside a Blocked by label) are stated in the architecture and
  pinned or shown above, not solved.
