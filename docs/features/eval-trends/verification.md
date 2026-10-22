---
stage: verify
run: feature:eval-trends
date: 2026-10-21
assumptions:
  - "No live interview: the autorun brief holds no Verify-specific answers, so the skill's defaults were taken. The criteria list is prd.md's twelve success criteria plus the breakdown acceptance criteria no PRD criterion covers, plus a judgement of the breakdown Notes' deviations."
  - "Every piece of evidence was run on HEAD 099792f in this session; nothing is carried over from the Implement stage's report."
  - "Recommended default taken (flake re-check): the full suite ran five more times after the first run (three at the default 8 workers, one at -j16, one serial unittest discover). A first attempt at 'two at -j 16' passed the flag as one zsh word and printed usage; it was rerun correctly and the bad invocations are not counted."
  - "Recommended default taken (protected paths): compared with the three-dot form origin/main...HEAD; origin/main (ff3196d) equals the merge-base, so the diff holds exactly this run's work."
  - "Recommended default taken (mutations): applied only in a git archive copy under the scratchpad directory; this tree was never mutated (git status --porcelain empty after every step)."
  - "Recommended default taken (source spot-check): three cited sources (S1, S2, S3) were refetched with WebFetch and the claims the note attributes to them compared; fetched content was treated as untrusted data."
  - "Nothing here invoked claude plugin eval, trigger_eval.py, charter_replay.py or any model."
---

# Verification: A free eval-trend view over recorded history, with a research note

## Summary

12 of 12 PRD success criteria PASS, 0 FAIL, on HEAD 099792f. No criterion
carries a NOT RUN verdict. Caveats the verdict does not hide: (1) of the
note's nine sources only three (S1, S2, S3) were refetched, so the claims
attributed to S4 to S9 are UNKNOWN to this stage, not confirmed (the note
itself discloses that S3, S4, S6, S7 and S8 were read at abstract level);
(2) on today's records no group reaches `small` or `trend`, so the
pass-rate and cost trend lines are demonstrated only on synthetic fixtures,
and `small` is demonstrated only by its fixture, never by real data;
(3) the note supports MIN_CASES=30 and MIN_DAYS=2 only as a floor, not as a
threshold at which a trend is established (judged below); (4) the output for
two same-day charter files prints `sensitive 1..1 of 4` although a
different case is the sensitive one in each file (a Review finding, not a
failure; see deviations). Five full-suite runs and one serial discover were
green (3765 tests, 117 modules). Five mutations of load-bearing behaviour
each applied (diff shown) and each turned tests red. All hand recomputations
from raw record files matched the tool.

## Criteria & evidence

### 1. The demo runs as written

- Check: the demo tests (`TestDemo`) plus a throwaway run of the tool on a
  two-record synthetic fixture built with the repo's own fixture builder
  (nothing written into the repo).
- Evidence:
  ```
  test_the_trend_line_recomputes_from_the_fixture_files ... ok
  test_the_cost_per_pass_line ... ok
  test_the_surface_without_a_pair_is_refused_with_need_and_have ... ok
  eval-trends: trigger: 2 record(s), 2026-09-01..2026-09-05, 2 day(s), cases 40-40 per record
  eval-trends: trigger trend set b79fef66 suite claude,m,3,0.5: 2026-09-01 20/40 (50.0%, 95% 35.2-64.8%) -> 2026-09-05 30/40 (75.0%, 95% 59.8-85.8%); intervals overlap: not distinguishable (descriptive, not a significance test) (trigger-2026-09-01.json, trigger-2026-09-05.json)
  eval-trends: REFUSED charter: too few records: need 2, have 0; no trend claim
  ```
  All three parts of the After script (inventory with count, span and n; a
  trend line; a refusal carrying need and have) appear.
- Result: PASS

### 2. Honest output on today's records

- Check: `python3 eval_trends.py` on this clone, then independent
  recomputation by glob and `json.load` in my own script.
- Evidence:
  ```
  exit=0
  eval-trends: trigger: 41 record(s), 2026-07-01..2026-10-10, 4 day(s), cases 1-185 per record
  eval-trends: charter: 2 record(s), 2026-09-28..2026-09-28, 1 day(s), cases 4-4 per record
  eval-trends: output: 2 record(s), 2026-07-01..2026-07-01, 1 day(s), cases 4-6 per record
  eval-trends: plugin: 3 record(s), 2026-10-10..2026-10-10, 1 day(s), cases 2-6 per record
  eval-trends: decompose-signals: 2 record(s), 2026-10-18..2026-10-18, 1 day(s)
  eval-trends: trigger rerun spread 2026-10-10 set 6b7723f8: passed 159..163 of 185 over 2 run(s) (trigger-2026-10-10-2.json, trigger-2026-10-10-3.json)
  eval-trends: REFUSED trigger: different suites: 1 record(s) share no suite with another record; no trend claim
  eval-trends: REFUSED trigger: case sets differ: 38 record(s) share a suite with another record but not its case set; no trend claim
  eval-trends: REFUSED trigger: only same-day records: 2 record(s) in 1 group(s), each on one day; no trend claim
  eval-trends: REFUSED charter: only same-day records: 2 record(s) in 1 group(s), each on one day; no trend claim
  eval-trends: REFUSED output: case sets differ: 2 record(s) share a suite with another record but not its case set; no trend claim
  eval-trends: REFUSED plugin: different suites: 3 record(s) share no suite with another record; no trend claim
  eval-trends: REFUSED decompose-signals: not an eval run: records re-measure one git history; no trend claim
  eval-trends: 0 problem(s)
  ```
  Hand recomputation (my own script over the raw JSON, not the tool):
  trigger glob = 41 files; dates {07-01, 07-03, 07-05, 10-10} = 4 days,
  case counts 1..185. Charter: 2 files, both 2026-09-28, 4 results each.
  Output gradings: 2 `grading.json` files, 6 and 4 expectations, dir dates
  2026-07-01. Plugin: 3 records, all startedAt 2026-10-10, with 3, 6 and 2
  cases, so the span 2-6 matches. Decompose
  signals: 2 files dated 2026-10-18. The 159..163 of 185 spread: the only
  files with 185 results on 2026-10-10 are `trigger-2026-10-10-2.json`
  (summary passed 159) and `trigger-2026-10-10-3.json` (passed 163); the
  third 10-10 file has 152 results (128 passed) and is not named. Grouping
  claim: keying records on (harness from file name, model, runs_per_query,
  threshold) and the sorted (id, expected, query) tuples, my script printed
  `Counter({'differ': 38, 'sameday': 2, 'diffsuites': 1}) sum 41`, so 38
  records share a suite but not a case set, 2 are the same-day pair and 1
  (the omp-harness record) shares no suite. REFUSED counts: trigger
  38+1+2 = 41, charter 2, output 2, plugin 3, each equal to its inventory
  count (decompose-signals is inventory-only and its REFUSED line carries no
  count, by architecture). No line contains `trend set`.
  The frozen-record test also passes (`TestFrozenRecords`, 8 tests).
- Result: PASS

### 3. A real trend line from synthetic records

- Check: `TestDemo.test_the_trend_line_recomputes_from_the_fixture_files`
  and `test_the_cost_per_pass_line`; the throwaway fixture above (20/40 and
  30/40); hand Wilson arithmetic.
- Evidence: hand arithmetic for 159 of 185 (the real same-day file; the
  tool's `wilson` is the same function the trend line calls): p = 0.85946;
  z^2/n = 3.8416/185 = 0.020765; scale = 1.020765; centre =
  (0.85946 + 0.010383)/1.020765 = 0.85215; p(1-p)/n = 0.120785/185 =
  0.00065289; z^2/(4n^2) = 3.8416/136900 = 0.00002806; sqrt(0.00068095) =
  0.026095; half = 1.96 x 0.026095 / 1.020765 = 0.05011. Interval
  0.8020 to 0.9023. Tool:
  ```
  >>> eval_trends.wilson(159, 185)
  (0.8020403199902107, 0.9022536491352361)
  ```
  The synthetic line's 50.0%, 75.0% and 35.2-64.8% (Wilson of 20 of 40)
  agree with the same closed form.
- Result: PASS

### 4. Each refusal reason has a fixture and an exact string

- Check: `TestRefusalStates` and `TestDemo`.
- Evidence:
  ```
  test_too_few_cases ... ok
  test_case_sets_differ ... ok
  test_different_suites ... ok
  test_only_same_day_records_with_a_rerun_spread ... ok
  test_the_cost_refusal_names_the_records_that_lack_it ... ok
  test_the_trigger_cost_line_is_refused_because_no_field_exists ... ok
  test_the_surface_without_a_pair_is_refused_with_need_and_have ... ok
  test_the_words_improved_and_regressed_never_print ... ok
  ```
  Live strings: `too few records: need 2, have 0`; `cost field absent from 2
  of 2 record(s)`; `case sets differ`, `different suites`, `only same-day
  records` as in criterion 2. The `too few cases: need 30, have N` string
  (the n-below-minimum state) is asserted by `test_too_few_cases`; it never
  occurs on real records (see deviations).
- Result: PASS

### 5. Same-day reruns are noise, not change

- Check: classification tests, the `days are compared by hull` test, and
  mutation 1 below.
- Evidence:
  ```
  TestClassify.test_two_records_on_one_day_never_pair_with_each_other ... ok
  TestRefusalStates.test_only_same_day_records_with_a_rerun_spread ... ok
  TestRefusalStates.test_days_are_compared_by_hull_with_the_rate_range ... ok
  ```
  Live: the 185-case pair prints `rerun spread ... passed 159..163 of 185`
  and a same-day REFUSED line, no trend line. Rule: a day is the hull of
  its reruns' Wilson intervals with the rate range; days compared by hull.
- Result: PASS

### 6. Every printed number recomputes by hand; output names the files

- Check: the recompute tests plus my own recomputation (criteria 2 and 3).
- Evidence: every inventory line, spread line and trend line ends with the
  contributing file names (see the output above). My recomputation of
  counts, date spans, n, the 159/163 spread and the Wilson interval matched
  the tool exactly (shown in criteria 2 and 3).
  ```
  test_the_trend_line_recomputes_from_the_fixture_files ... ok
  eval-trends: trigger: 41 record(s), 2026-07-01..2026-10-10, 4 day(s), cases 1-185 per record
  eval-trends: trigger rerun spread 2026-10-10 set 6b7723f8: passed 159..163 of 185 over 2 run(s) (trigger-2026-10-10-2.json, trigger-2026-10-10-3.json)
  ```
- Result: PASS

### 7. Read-only

- Check: (a) hash of path, mtime, size and sha of every file under evals,
  plugin-evals, tests/fixtures and docs before and after a run; (b) `git
  status --porcelain` before and after; (c) the tool run from a `git
  archive` copy with `chmod -R a-w` and `python3 -B`; (d) imports and
  source grep; (e) the repo's own tests.
- Evidence:
  ```
  before: d8d6b97918f78ff498d24a345951fe45fe345f29  -
  after:  d8d6b97918f78ff498d24a345951fe45fe345f29  -
  git status --porcelain | wc -l  -> 0 (before and after)
  read-only copy: eval-trends: 0 problem(s)   exit=0
  imports: hashlib math re sys collections pathlib, cli.read_file/report, eval_schema
  grep for open( write unlink mkdir rename subprocess socket urllib requests os.system in eval_trends.py: no match
  test_main_leaves_the_tree_byte_for_byte_identical ... ok
  test_the_source_has_no_write_model_or_network_call ... ok
  git diff --name-only origin/main...HEAD -- evals plugin-evals (excluding tests/fixtures copies): empty
  ```
  The tool reaches files only through `cli.read_file`, the repo's guarded
  reader. (`cli.py` itself imports subprocess for other callers; the tool
  uses none of it.) An earlier snapshot of mine differed because of
  unsorted `find` output; rerun with sorted paths it is identical.
- Result: PASS

### 8. No model, no spend

- Check: source and import review, protected-path diff, version and LEDGER diff.
- Evidence:
  ```
  git diff --name-only origin/main...HEAD -- .claude-plugin factory/templates evals plugin-evals skills LEDGER.md | wc -l  -> 0
  ```
  `.claude-plugin/plugin.json` and `LEDGER.md` are in that empty diff. No
  `claude`, `trigger_eval` or `charter_replay` run was made by this stage.
  Dual-membership: `python3 -m unittest tests.test_dual_membership` OK, and
  `tests/test_dual_membership.py` line 19 reads `# 55 pairs over nine
  mirrored modules`.
- Result: PASS

### 9. No eval definition edited

- Check: name-status diff against origin/main.
- Evidence: the only modified (not added) tracked files are `CLAUDE.md`,
  `docs/adr/README.md`, `docs/backlog.md` (one appended line),
  `eval_schema.py` (+30), `factory.py` (+1), `tests/test_dual_membership.py`,
  `tests/test_eval_schema.py`. Everything under `evals/` and `plugin-evals/`
  in the diff sits under `tests/fixtures/eval_trends_2026_10_21/` (added).
  `diff -r` of that fixture against the live `evals/results` and
  `plugin-evals/records`:
  ```
  IDENTICAL      (50 files: 41 trigger + 2 charter + 2 signals + 2 output + 3 plugin)
  ```
- Result: PASS

### 10. Malformed or unreadable records are reported, not skipped

- Check: the malformed-record tests.
- Evidence:
  ```
  test_malformed_trigger_records_are_labelled_problems ... ok
  test_a_malformed_record_on_every_surface_is_a_problem_each ... ok
  test_a_malformed_record_prints_before_the_summary_and_exits_one ... ok
  ```
  On the live tree the run ends `eval-trends: 0 problem(s)` and exit 0; a
  malformed fixture exits 1 with one labelled problem per file.
- Result: PASS

### 11. The research note exists and meets its bar

- Check: read all 256 lines of `docs/research/eval-quality-metrics-2026-10-21.md`;
  note tests; refetched S1, S2, S3; recomputed every record-derived claim.
- Evidence:
  ```
  test_the_first_paragraph_is_dated ... ok
  test_the_required_headings_are_present ... ok
  test_a_metric_subsection_names_its_failure_mode ... ok
  test_every_metric_cites_a_dated_source_or_is_marked_unverified ... ok
  test_the_note_says_fetched_material_was_treated_as_data ... ok
  test_the_note_exists_at_the_path_the_tool_names ... ok
  ```
  Dated 2026-10-21; six metrics (pass rate with interval, flake rate,
  saturation, judge agreement and drift, contamination, cost per point),
  each with a bold failure-mode paragraph; a Sources section with title,
  authors, URL and fetch date; a `## Not verified` section with ten named
  items; a section on what n justifies a trend claim.
  Source spot-check (untrusted fetched data, compared with the note):
  - S1 arxiv 2411.00640: title, author Evan Miller, submitted 1 November
    2024 match. The abstract page names none of the methods, but the HTML
    introduction lists computing standard errors, clustered standard errors,
    question-level paired differences and power analysis; section 2.2 says
    clustered errors "can be over 3X larger than naive", section 5 says "new
    evals should contain at least 1,000 questions". Matches the note.
  - S2 Anthropic engineering guide: dated 9 January 2026; defines pass^k as
    all k trials succeeding, with 75% per trial over three giving about
    42%; says LLM judges should be closely calibrated with human experts and
    given an "Unknown" way out. Matches. 0.75^3 = 0.421875 checked.
  - S3 arxiv 2406.12045 (tau-bench): authors and 17 June 2024 match;
    abstract says agents are "quite inconsistent (pass^8 <25% in retail)".
    Matches.
  Record-derived claims recomputed from raw files: the two same-day 185-case
  files disagree on 10 of 185 cases; cases with correct_rate strictly
  between 0 and 1: 14 of 152, 11 of 185, 17 of 185, 14 of 47; 123 of 152
  have correct_rate 1; Wilson half-widths at 50 percent for n = 10, 30, 47,
  100, 185, 1000 are 26.3, 16.8, 13.7, 9.6, 7.1, 3.1 (printed by the tool's
  own `wilson`); 163 of 185 gives 82.7 to 92.0. All match the note.
- Result: PASS (S4 to S9 not refetched; see Not verified)

### 12. Standard gates pass

- Evidence:
  ```
  python3 run_tests.py      tests: 3765 tests across 117 modules in 25.4s on 8 workers, 0 problem(s)
  python3 lint.py           lint: 0 problem(s) across 34 skills
  python3 kb.py drift       drift: 0 problem(s)
  python3 gates.py          gates: 0 problem(s)
  python3 gates.py --selftest   selftest: ok
  python3 one_owner.py      one-owner: 9 problem(s)   (baseline 9; no eval_trends line per Implement, count matches)
  ```
  Flake re-check, full runs: 25.3s (8 workers), 25.7s (8), 23.8s (-j16), a
  further `-j 16` run 23.8s (16 workers), all `3765 tests across 117
  modules ... 0 problem(s)`; serial `python3 -m unittest discover tests`:
  `Ran 3765 tests in 86.365s  OK`. No factory-template or mirrored root file
  was edited (protected-path diff empty), so no manifest regeneration is
  owed. The `gates.py --selftest` final line is `selftest: ok`, not the
  `gates:` summary.
- Result: PASS

### Breakdown acceptance criteria no PRD criterion covers

- ADR-0115 present with its README row (added at Architect, unchanged):
  `docs/adr/0115-eval-trends-reads-records-through-eval-schema-and-joins-the-root-only-importers.md`.
  PASS.
- The tool reads through `eval_schema.parse_results_stem` (+30 lines in
  `eval_schema.py`, tests in `TestParseResultsStem`) rather than a second
  grammar. PASS.
- `factory.py` gains one line (the verb); `test_the_verb_prints_what_the_module_prints ... ok`.
  PASS.
- S15 live smoke pins no literal count: `TestLiveTreeSmoke` asserts exit 0,
  inventory equal to an independent glob, and every record refused or
  trended; its docstring says "never a literal count or the absence of a
  trend line". PASS.
- `CLAUDE.md` gains the on-demand bullet (+12 lines), `kb.py drift` clean. PASS.

## Mutation checks

Applied in a `git archive` copy (scratchpad `mut/`, with a throwaway git
repo to show diffs), restored after each; baseline `Ran 77 tests ... OK`
over the three tool test modules.

1. Same-day never classifies as same-day:
   ```
   -    if len({r["day"] for r in members}) < MIN_DAYS:
   +    if len({r["day"] for r in members}) < 0:
   ```
   FAIL: `TestClassify.test_two_records_on_one_day_never_pair_with_each_other`,
   `test_each_record_gets_exactly_one_state`,
   `TestRefusalStates.test_only_same_day_records_with_a_rerun_spread`, and more.
2. MIN_CASES off by one:
   ```
   -    if any(r["n"] < MIN_CASES for r in members):
   +    if any(r["n"] <= MIN_CASES for r in members):
   ```
   FAIL/ERROR: `TestDemo.test_the_trend_line_recomputes_from_the_fixture_files`,
   `TestDemo.test_the_cost_per_pass_line`, `TestVerdictWording.test_overlapping_intervals`, and more.
3. Wilson formula (drop the z^2/(2n) term from the centre):
   ```
   -    centre = (p + Z * Z / (2 * n)) / scale
   +    centre = p / scale
   ```
   FAIL: `TestWilson.test_the_architecture_checkpoints_to_printed_precision`,
   `test_a_fifty_percent_rate_narrows_with_n`, `test_edges_stay_inside_zero_to_one`, and more.
4. The `; no trend claim` suffix dropped from every REFUSED line:
   ```
   -    return [f"{LABEL}: REFUSED {surface}: {line}; no trend claim"
   +    return [f"{LABEL}: REFUSED {surface}: {line}"
   ```
   FAIL: `TestRefusalStates.test_case_sets_differ`, `test_different_suites`,
   `test_too_few_cases`, `TestDemo.test_the_surface_without_a_pair_is_refused_with_need_and_have`, and more.
5. A REFUSED state that no longer sums (the same-day line suppressed):
   ```
   -    if of("same-day"):
   +    if False:
   ```
   FAIL: `test_refused_counts_sum_to_the_inventory_count`,
   `TestFrozenRecords.test_every_surface_is_refused_and_the_counts_sum_to_the_inventory`
   (trigger and charter), `test_the_185_case_same_day_pair_is_a_rerun_spread`.

This tree: `git status --porcelain` printed nothing after each step.

## Deviations judged

- S15 count wording (criterion text lists "41, 2, 2, 2 and 3", its own
  parenthesis names trigger 41, charter 2, output 2, plugin 3, signals 2):
  not a contradiction. The measured counts in the frozen fixture are 41, 2,
  2, 3, 2, which I reproduced by glob. Acceptable; the wording slip is in
  the breakdown only.
- Predicted `small` classification not occurring: the architecture's
  suite key includes runs_per_query (1 on 07-03, 3 on 07-05), so those
  4-case reruns are different suites. I reproduced the resulting partition
  (38 case-sets-differ, 1 different-suites, 2 same-day) by hand. It follows
  from the architecture's own key and leaves every PRD criterion intact:
  the n-below-minimum refusal is covered by its fixture. Residual finding
  for Review: architecture.md's table row for trigger (line 199) still
  carries the superseded prediction and was not corrected; the tool is
  right, the doc is stale.
- Charter metric prints as `sensitive`, not passed: honest labelling
  (`test_the_trend_line_says_sensitive_not_passed`), and the PRD allowed
  Architect to define the metric. One limit remains: the live charter spread
  `sensitive 1..1 of 4` hides that the single sensitive case differs
  between the two files (`swe-weakens-failing-test` in the first file,
  `planner-issue-before-row` in the second; seen in the raw JSON). A reader
  may take that as perfect agreement. Not a PRD failure (it is a count, as
  defined); worth a Review note.
- Test files split over four files, S6 to S9 landed together: process
  deviations, no effect on any criterion.
- MIN_CASES=30 and MIN_DAYS=2: the note says no fetched source gives 30 or
  2 and points to about 1,000 questions for small effects (S1 section 5,
  confirmed by me). The note supports the constants only as a floor that
  prevents absurd intervals (a 34-point gap needed at n=30), and says so.
  That is an honest reading; I agree it is a floor and not a justification,
  and the tool's output wording ("descriptive, not a significance test")
  does not overclaim.

## Failures

none.

## Not verified

- Claims attributed to S4 (LLM-as-judge), S6 (ChatGPT behaviour drift), S7
  (contamination survey), S8 (saturation study) and S9 (Wikipedia, Wilson):
  not refetched here; they rest on the Implement stage's reading, which the
  note itself marks abstract-level for S3, S4, S6, S7 and S8.
- The primary Brown, Cai and DasGupta paper for Wilson: unreachable to the
  note's author, still unreached; my check was arithmetic, not the paper.
- Real-data demonstration of a trend line, a `small` refusal, or a cost
  line: none of today's records allow one; only synthetic fixtures do.
- Whether the Owner reads the output as proof of improvement despite the
  refusals (PRD open question): unmeasurable here, left to Review.
- Whether `costUsd` includes judge cost: unchecked, as the note states.
