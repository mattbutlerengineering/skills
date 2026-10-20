---
stage: verify
run: feature:decompose-outcome-signals
date: 2026-10-18
assumptions:
  - "No live interview: the autorun brief holds no Verify-specific answers, so the skill's defaults were taken. The criteria list is prd.md's nine success criteria, plus the breakdown acceptance criteria no PRD criterion covers (one section, at the end)."
  - "Re-verify after the Architect re-entry (Owner decision 7, ADR-0111, S14 to S16): neither the verify skill nor pipeline-protocol.md says whether a re-run writes a new file or updates the old one, so the skill's default was taken: one verification.md per run, rewritten in place against the current tree (HEAD 4278f94). The previous version (95b130d, verified at 56baba9) stays in git history. Every piece of evidence below was re-run on 4278f94; nothing is carried over from it."
  - "Recommended default taken (reproducing the second record on the same refs): HEAD has moved two commits past the second record's head (76b59fe to 4278f94), so this clone's refs are not the refs that record read. The record-time ref set was rebuilt in a scratch clone (`git clone --mirror` of this repo, `core.bare false`, `refs/heads/feat/decompose-outcome-signals` reset to 76b59fe, tree checked out with `git reset --hard`). The tool's own digest line proves the ref set matches: it printed the record's digest 69e5099cd97f. Nothing in this repo's refs or tree was changed."
  - "Recommended default taken (flake re-check): five full-suite runs, four sequential at the default 8 workers and one at -j 16. The orchestrator asked for at least 3."
---

# Verification: Decompose outcome signals from git history

## Summary

9 of 9 PRD success criteria PASS, 0 FAIL, 0 NOT RUN, on HEAD 4278f94
after Review's fixes and the ADR-0111 last-tick change. The breakdown
acceptance criteria not covered by a PRD criterion (S1 to S16) also
pass. The second record (`decompose-signals-2026-10-18-2.json`) is
reproduced byte for byte by `--record` on its record-time refs. The
first record is byte-unchanged since the commit that added it. On all 4
runs with an observed implement commit, that commit is the first commit
after D that checks every row. The Implement-stage flake did not recur
in five full-suite runs; its cause stays an open unknown (see Not
verified).

## Criteria & evidence

### 1. One invocation measures every run directory holding a `breakdown.md` and prints a per-run row for each plus an aggregate, in the problem-string / count contract

- Check: count the run directories with a `breakdown.md`, run
  `python3 decompose_signals.py` at HEAD 4278f94, count its run lines,
  and compare `python3 factory.py decompose-signals` with it.
- Evidence:
  ```
  $ git rev-parse HEAD
  4278f94e4699c0196227d8886390da5f445931b2
  $ ls docs/breakdown.md docs/features/*/breakdown.md docs/fixes/*/breakdown.md 2>/dev/null | wc -l
        36
  $ python3 decompose_signals.py > ds.txt; echo "exit $?"
  exit 0
  $ cat ds.txt
  decompose-signals: refs read — refs/heads (401), refs/pr (13), refs/remotes/origin (184), refs/remotes/pr (488); refs/stash skipped; digest 5b9094b14e3b
  decompose-signals: boundary rule — a boundary is observed when its commit subject reads docs(<any scope>): <stage>, the stage a whole word, and the commit changes that stage's artifact in the run's own directory; any other boundary is inferred: decompose at the commit that first adds breakdown.md, implement at the first later commit that checks every row (ADR-0109, ADR-0111)
  decompose-signals: feature:codex-style-standards-enforcement — decompose inferred ebe8b2a, implement inferred 675e9f4; re-plan 0 of 14 (added 0, dropped 0, split 0, merged 0; renamed 14) inferred; design gaps 0 inferred; review-traced 3 of 12 findings name an item
  decompose-signals: feature:decompose-outcome-signals — decompose observed de92f3c, implement observed 56baba9; re-plan 2 of 13 (added 2, dropped 0, split 0, merged 0; renamed 0) observed; design gaps 1 observed; review-traced 1 of 9 findings name an item
  decompose-signals: feature:docs-audit — decompose inferred da4b751, implement inferred d03a0ba; re-plan 0 of 11 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 9 findings name an item
  decompose-signals: feature:factory-evolution-v1 — decompose inferred abed301, implement inferred 8ebfd12; re-plan 0 of 8 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 3 of 10 findings name an item
  decompose-signals: feature:fail-closed-roll-up — decompose observed 637f2e7, implement observed 27467df; re-plan 0 of 7 (added 0, dropped 0, split 0, merged 0; renamed 0) observed; design gaps 0 observed; review-traced 0 of 11 findings name an item
  decompose-signals: feature:faster-sdlc — decompose inferred 406c370, implement none; re-plan unmeasurable — no implement boundary: no later commit checks every row; design gaps 0 inferred; review-traced unmeasurable — no review.md
  decompose-signals: feature:first-live-dispatch — decompose inferred 5540dd9, implement inferred 7442916; re-plan 4 of 8 (added 3, dropped 0, split 1, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 10 of 13 findings name an item
  decompose-signals: feature:launch-demo — decompose inferred c9808b1, implement inferred ab37864; re-plan 0 of 14 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 3 of 10 findings name an item
  decompose-signals: feature:lean-and-polish — decompose inferred e24b6b3, implement inferred bdba36e; re-plan 0 of 3 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 0 findings — review.md has no finding heading
  decompose-signals: feature:lean-in-the-build — decompose inferred faddef2, implement inferred a3bc5c3; re-plan 0 of 3 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 3 findings name an item
  decompose-signals: feature:orchestrator — decompose inferred 75e3bf7, implement inferred 527d305; re-plan 0 of 12 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 8 findings name an item
  decompose-signals: feature:pipeline-board — decompose inferred 4b1b72a, implement inferred 2205a07; re-plan 0 of 6 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 4 findings name an item
  decompose-signals: feature:pocock-1-3-takeaways — decompose inferred 9129d61, implement inferred 482f1f1; re-plan 0 of 14 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 5 findings name an item
  decompose-signals: feature:pr-body-preflight — decompose observed 772e374, implement observed 766292c; re-plan 0 of 9 (added 0, dropped 0, split 0, merged 0; renamed 0) observed; design gaps 1 observed; review-traced 0 of 15 findings name an item
  decompose-signals: feature:process-dashboard — decompose inferred 87b59eb, implement inferred b1f8c18; re-plan 0 of 11 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 4 findings name an item
  decompose-signals: feature:readme-skill-map — decompose inferred 2973bbc, implement inferred 1fed0ce; re-plan 0 of 6 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 4 findings name an item
  decompose-signals: feature:seed-backlog — decompose inferred 1ac1042, implement inferred df6323e; re-plan 0 of 7 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 2 findings name an item
  decompose-signals: feature:software-factory — decompose observed 0661682, implement inferred 0802c5c; re-plan 0 of 18 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 5 findings name an item
  decompose-signals: maintenance:a-blind-find-is-not-a-failed-agent — decompose inferred b28d953, implement inferred 263eba4; re-plan 0 of 4 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 1 of 4 findings name an item
  decompose-signals: maintenance:a-timestamp-the-digest-cannot-parse — decompose inferred e8aae36, implement inferred 6adb359; re-plan 6 of 7 (added 0, dropped 6, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 1 findings name an item
  decompose-signals: maintenance:closed-intake-mutes-the-detector — decompose inferred ee5532c, implement inferred ef972b3; re-plan 0 of 4 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 0 of 4 findings name an item
  decompose-signals: maintenance:dedup-identity-has-two-owners — decompose inferred 88fbb34, implement inferred cc0e297; re-plan 0 of 3 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 1 of 1 findings name an item
  decompose-signals: maintenance:deepening-cli-seams — decompose none, implement none; re-plan unmeasurable — the first version (ec957eb) already checks 9 of 9 rows; design gaps unmeasurable — the first version (ec957eb) already checks 9 of 9 rows; review-traced 2 of 5 findings name an item
  decompose-signals: maintenance:deepening-tool-seams — decompose inferred 4a287ff, implement inferred a4f6310; re-plan 0 of 15 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 3 of 4 findings name an item
  decompose-signals: maintenance:empty-is-not-the-same-as-broken — decompose inferred 738573f, implement inferred 39ab6af; re-plan 0 of 4 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 1 of 2 findings name an item
  decompose-signals: maintenance:gate-timeline-timestamp-trust — decompose none, implement none; re-plan unmeasurable — the first version (b4dd17a) already checks 2 of 2 rows; design gaps unmeasurable — the first version (b4dd17a) already checks 2 of 2 rows; review-traced 0 of 3 findings name an item
  decompose-signals: maintenance:marker-diagnostics-that-lie — decompose inferred 5d993dc, implement inferred 0fd706a; re-plan 0 of 5 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 0 of 5 findings name an item
  decompose-signals: maintenance:one-fact-one-owner — decompose none, implement none; re-plan unmeasurable — the first version (a527688) already checks 1 of 13 rows; design gaps unmeasurable — the first version (a527688) already checks 1 of 13 rows; review-traced 3 of 8 findings name an item
  decompose-signals: maintenance:one-fence-rule — decompose inferred 7da232d, implement inferred b5c3974; re-plan 0 of 4 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 4 findings name an item
  decompose-signals: maintenance:one-guarded-file-read — decompose inferred 110ffc6, implement inferred e974147; re-plan 0 of 18 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 1 of 11 findings name an item
  decompose-signals: maintenance:one-labels-walk — decompose none, implement none; re-plan unmeasurable — the first version (45f4b43) already checks 1 of 3 rows; design gaps unmeasurable — the first version (45f4b43) already checks 1 of 3 rows; review-traced 0 of 2 findings name an item
  decompose-signals: maintenance:quoted-token-is-not-a-claim — decompose none, implement none; re-plan unmeasurable — the first version (5210702) already checks 1 of 2 rows; design gaps unmeasurable — the first version (5210702) already checks 1 of 2 rows; review-traced 0 of 3 findings name an item
  decompose-signals: maintenance:row-done-guard — decompose none, implement none; re-plan unmeasurable — the first version (4520083) already checks 1 of 1 rows; design gaps unmeasurable — the first version (4520083) already checks 1 of 1 rows; review-traced 0 of 3 findings name an item
  decompose-signals: maintenance:run-discovery-ignores-open-prs — decompose inferred e142434, implement inferred 50173f7; re-plan 0 of 4 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 1 of 2 findings name an item
  decompose-signals: maintenance:the-digest-says-what-it-could-read — decompose inferred ca717be, implement inferred b7b625f; re-plan 0 of 5 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 0 of 2 findings name an item
  decompose-signals: maintenance:the-reviewer-token-runs-agent-code — decompose observed ba286e5, implement observed 755dc8c; re-plan 0 of 13 (added 0, dropped 0, split 0, merged 0; renamed 0) observed; design gaps 0 observed; review-traced 0 of 5 findings name an item
  decompose-signals: aggregate re-plan — observed 2/42 over 4 run(s); inferred 10/208 over 25 run(s); combined 12/250 over 29 run(s); unmeasurable 7 run(s)
  decompose-signals: aggregate design gaps — observed 2/4 over 4 run(s); inferred 0/18 over 18 run(s); combined 2/22 over 22 run(s); unmeasurable 14 run(s)
  decompose-signals: aggregate review-traced — observed 33/193 over 35 run(s); inferred 0/0 over 0 run(s); combined 33/193 over 35 run(s); unmeasurable 1 run(s)
  decompose-signals: 36 run(s), 0 problem(s)
  $ python3 factory.py decompose-signals > ds_factory.txt; echo "factory exit $?"; cmp ds.txt ds_factory.txt && echo same
  factory exit 0
  same
  $ grep -c "^decompose-signals: \(feature\|maintenance\|product\):" ds.txt
  36
  ```
  36 run lines, three aggregate lines, and the `cli.report` summary
  `decompose-signals: 36 run(s), 0 problem(s)`.
- Result: PASS

### 2. Every per-run boundary is labelled `observed` or `inferred`, and the aggregate prints observed, inferred and combined figures for each of the three signals

- Check: the output above, and the boundary tests through the public
  interface (`python3 -m unittest -v tests.test_decompose_signals`).
- Evidence (lines from criterion 1's output, then the test run):
  ```
  decompose-signals: feature:fail-closed-roll-up — decompose observed 637f2e7, implement observed 27467df; re-plan 0 of 7 (added 0, dropped 0, split 0, merged 0; renamed 0) observed; design gaps 0 observed; review-traced 0 of 11 findings name an item
  decompose-signals: feature:software-factory — decompose observed 0661682, implement inferred 0802c5c; re-plan 0 of 18 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 5 findings name an item
  decompose-signals: aggregate re-plan — observed 2/42 over 4 run(s); inferred 10/208 over 25 run(s); combined 12/250 over 29 run(s); unmeasurable 7 run(s)
  decompose-signals: aggregate design gaps — observed 2/4 over 4 run(s); inferred 0/18 over 18 run(s); combined 2/22 over 22 run(s); unmeasurable 14 run(s)
  decompose-signals: aggregate review-traced — observed 33/193 over 35 run(s); inferred 0/0 over 0 run(s); combined 33/193 over 35 run(s); unmeasurable 1 run(s)

  test_observed_is_the_earliest_implement_commit_after_d (tests.test_decompose_signals.TestImplement.test_observed_is_the_earliest_implement_commit_after_d) ... ok
  test_inferred_is_the_first_later_version_checking_every_row (tests.test_decompose_signals.TestImplement.test_inferred_is_the_first_later_version_checking_every_row)
  ADR-0111: the commit that checks the last row, not the first ... ok
  test_an_observed_implement_wins_over_an_earlier_all_checked (tests.test_decompose_signals.TestImplement.test_an_observed_implement_wins_over_an_earlier_all_checked) ... ok
  test_a_later_unchecked_row_does_not_move_it (tests.test_decompose_signals.TestImplement.test_a_later_unchecked_row_does_not_move_it) ... ok
  test_a_later_unchecked_row_after_unticking_does_not_move_it (tests.test_decompose_signals.TestImplement.test_a_later_unchecked_row_after_unticking_does_not_move_it) ... ok
  test_no_later_commit_checks_every_row (tests.test_decompose_signals.TestImplement.test_no_later_commit_checks_every_row) ... ok
  Ran 83 tests in 11.335s
  OK
  ```
  Runs with no boundary print `decompose none, implement none` and carry
  the reason on each signal (criterion 3).
- Result: PASS

### 3. Each unmeasurable run is printed by name with a reason and is left out of every aggregate count

- Check: the unmeasurable lines in criterion 1's output, and the
  arithmetic of each aggregate (measured runs + unmeasurable runs = 36).
- Evidence:
  ```
  decompose-signals: maintenance:deepening-cli-seams — decompose none, implement none; re-plan unmeasurable — the first version (ec957eb) already checks 9 of 9 rows; design gaps unmeasurable — the first version (ec957eb) already checks 9 of 9 rows; review-traced 2 of 5 findings name an item
  decompose-signals: feature:faster-sdlc — decompose inferred 406c370, implement none; re-plan unmeasurable — no implement boundary: no later commit checks every row; design gaps 0 inferred; review-traced unmeasurable — no review.md
  decompose-signals: feature:lean-and-polish — ...; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 0 findings — review.md has no finding heading

  re-plan:       combined 29 run(s) + unmeasurable 7  = 36
  design gaps:   combined 22 run(s) + unmeasurable 14 = 36
  review-traced: combined 35 run(s) + unmeasurable 1  = 36

  test_an_unmeasurable_run (tests.test_decompose_signals.TestTheFiveFixtureRuns.test_an_unmeasurable_run) ... ok
  ```
  The sums are read off the three aggregate lines in criterion 1. The 7
  re-plan unmeasurables are the six `already checks` runs plus
  faster-sdlc, which is new under ADR-0111 (criterion 8c). Review-traced
  went from 2 unmeasurable to 1 because this run now has a `review.md`
  (`review-traced 1 of 9 findings name an item`).
- Result: PASS

### 4. The output names the refs that were read and the subject-match rule that was applied

- Check: the two header lines of criterion 1's output.
- Evidence:
  ```
  decompose-signals: refs read — refs/heads (401), refs/pr (13), refs/remotes/origin (184), refs/remotes/pr (488); refs/stash skipped; digest 5b9094b14e3b
  decompose-signals: boundary rule — a boundary is observed when its commit subject reads docs(<any scope>): <stage>, the stage a whole word, and the commit changes that stage's artifact in the run's own directory; any other boundary is inferred: decompose at the commit that first adds breakdown.md, implement at the first later commit that checks every row (ADR-0109, ADR-0111)
  ```
  The rule line now names the inferred rule as well (S15).
- Result: PASS

### 5. The tool makes no network call: a test or a code read shows it runs no fetch, and its only external CLI is git through `cli.py`

- Check: the no-network tests, and the git invocation in the code.
- Evidence:
  ```
  test_only_local_read_only_verbs_are_run (tests.test_decompose_signals.TestNoNetwork.test_only_local_read_only_verbs_are_run) ... ok
  test_the_module_names_no_network_verb (tests.test_decompose_signals.TestNoNetwork.test_the_module_names_no_network_verb) ... ok
  test_only_local_read_only_verbs_are_run_end_to_end (tests.test_decompose_signals.TestReportFailures.test_only_local_read_only_verbs_are_run_end_to_end) ... ok

  decompose_signals.py, read_history (lines 97-119): the only git verbs are
  for-each-ref and `log --stdin --full-history --author-date-order --reverse --name-only`;
  read_version (line 131) runs `show <sha>:<path>`; the runner is cli.runner("git", timeout=GIT_TIMEOUT).
  ```
  Review's `--full-history` fix (1a7717a) adds a flag to the local
  `log` call only; no new verb.
- Result: PASS

### 6. Tests through the public interface cover a run with no re-plans, a split item, a run routed back to Architect, a run with only inferred boundaries, and an unmeasurable run, each asserting exact output strings

- Check: `python3 -m unittest -v tests.test_decompose_signals`.
- Evidence:
  ```
  test_a_run_routed_back_to_architect (tests.test_decompose_signals.TestTheFiveFixtureRuns.test_a_run_routed_back_to_architect) ... ok
  test_a_run_with_a_split_item (tests.test_decompose_signals.TestTheFiveFixtureRuns.test_a_run_with_a_split_item) ... ok
  test_a_run_with_no_re_plans (tests.test_decompose_signals.TestTheFiveFixtureRuns.test_a_run_with_no_re_plans) ... ok
  test_a_run_with_only_inferred_boundaries (tests.test_decompose_signals.TestTheFiveFixtureRuns.test_a_run_with_only_inferred_boundaries) ... ok
  test_an_unmeasurable_run (tests.test_decompose_signals.TestTheFiveFixtureRuns.test_an_unmeasurable_run) ... ok
  test_the_rule_names_its_adr (tests.test_decompose_signals.TestTheWholeReport.test_the_rule_names_its_adr) ... ok
  test_the_rule_names_the_last_tick (tests.test_decompose_signals.TestTheWholeReport.test_the_rule_names_the_last_tick) ... ok
  Ran 83 tests in 11.335s
  OK
  ```
  The module grew from 72 to 83 tests (Review's pins plus S14).
- Result: PASS

### 7. For the review-traced signal, a run with findings that name no item and a run with no `review.md` print different strings, and a test asserts both

- Check: the review-shape tests, and real-repo output.
- Evidence:
  ```
  test_no_review_md (tests.test_decompose_signals.TestReviewShapes.test_no_review_md) ... ok
  test_a_review_with_no_finding_heading (tests.test_decompose_signals.TestReviewShapes.test_a_review_with_no_finding_heading) ... ok
  test_findings_that_name_an_item (tests.test_decompose_signals.TestReviewShapes.test_findings_that_name_an_item) ... ok

  real output (criterion 1), three distinct shapes:
  feature:faster-sdlc — ...; review-traced unmeasurable — no review.md
  feature:lean-and-polish — ...; review-traced 0 findings — review.md has no finding heading
  feature:docs-audit — ...; review-traced 0 of 9 findings name an item
  ```
- Result: PASS

### 8. The real numbers are committed append-only as the tool's unedited output, and rerunning on the same refs gives the same numbers

Under Owner decision 7 there are now two records. (a) the second one
reproduces; (b) the first is unchanged; (c) the rule the second one was
taken under holds on this clone's history.

- Check (a): rebuild the second record's refs in a scratch mirror clone
  (branch reset to its `head`, 76b59fe), rerun with and without
  `--record`, `cmp` and hash the written file against the committed one,
  and diff `render()` of the committed record against the rerun.
- Evidence (a):
  ```
  $ python3 -c "import json;d=json.load(open('evals/results/decompose-signals-2026-10-18-2.json'));print(d['head'], d['refs_digest'], d['date'])"
  76b59fe7b79dbae448cfb1478dfe6d766e1153d2 69e5099cd97fa24d0a75da11fbfce75f1a57a6a176d69bfd55042a6ef568872e 2026-10-18

  scratch: git clone -q --mirror <repo> mirror/.git; git config core.bare false;
           git update-ref refs/heads/feat/decompose-outcome-signals 76b59fe7...; git reset -q --hard
  $ git rev-parse HEAD; git status --porcelain; ls evals/results/ | grep decompose
  76b59fe7b79dbae448cfb1478dfe6d766e1153d2
  decompose-signals-2026-10-18.json
  $ python3 decompose_signals.py > repro_out.txt; echo "exit $?"
  exit 0
  decompose-signals: refs read — refs/heads (401), refs/pr (13), refs/remotes/origin (184), refs/remotes/pr (488); refs/stash skipped; digest 69e5099cd97f
  $ python3 decompose_signals.py --record; echo "record exit $?"
  ... (the same 41 report lines) ...
  decompose-signals: recorded evals/results/decompose-signals-2026-10-18-2.json
  decompose-signals: 36 run(s), 0 problem(s)
  record exit 0
  $ cmp evals/results/decompose-signals-2026-10-18-2.json <repo>/evals/results/decompose-signals-2026-10-18-2.json && echo "BYTE-IDENTICAL to committed second record"
  BYTE-IDENTICAL to committed second record
  $ shasum -a 256 evals/results/decompose-signals-2026-10-18-2.json <repo>/evals/results/decompose-signals-2026-10-18-2.json
  758f8570fdc4ed5d5f069733b6d87cbb1a9dd7b4149add9c476722b79467c1d3  evals/results/decompose-signals-2026-10-18-2.json
  758f8570fdc4ed5d5f069733b6d87cbb1a9dd7b4149add9c476722b79467c1d3  <repo>/evals/results/decompose-signals-2026-10-18-2.json
  $ sed '$d' repro_out.txt | diff - rendered2.txt && echo "IDENTICAL: ..."
  IDENTICAL: render(second record) == rerun on record-time refs (41 lines)

  record-time output against today's output (HEAD 4278f94, this repo):
  $ diff repro_out.txt ds.txt
  1c1
  < decompose-signals: refs read — refs/heads (401), refs/pr (13), refs/remotes/origin (184), refs/remotes/pr (488); refs/stash skipped; digest 69e5099cd97f
  ---
  > decompose-signals: refs read — refs/heads (401), refs/pr (13), refs/remotes/origin (184), refs/remotes/pr (488); refs/stash skipped; digest 5b9094b14e3b
  ```
  The digest printed in the scratch clone is the record's
  `refs_digest` prefix, so the ref set is the one the record read. On
  today's refs only the digest moves (the branch tip moved to 4278f94);
  every run and aggregate line is identical.
- Check (b): the first record's history on this branch and its blob.
- Evidence (b):
  ```
  $ git log --format='%h %s' main..HEAD -- evals/results/
  1d7279e chore(decompose-signals): S16 record the second real numbers
  27bd1b0 chore(decompose-signals): S13 record the first real numbers
  $ git diff --stat main...HEAD -- evals/results/
   evals/results/decompose-signals-2026-10-18-2.json | 1129 ++++++++++++++++++++
   evals/results/decompose-signals-2026-10-18.json   | 1135 +++++++++++++++++++++
   2 files changed, 2264 insertions(+)
  $ git log --format=%h -1 -- evals/results/decompose-signals-2026-10-18.json
  27bd1b0
  $ git diff 27bd1b0 HEAD -- evals/results/decompose-signals-2026-10-18.json | wc -l
         0
  $ git rev-parse 27bd1b0:evals/results/decompose-signals-2026-10-18.json HEAD:evals/results/decompose-signals-2026-10-18.json
  bfa9dbd859e62711ede7792c16d383a9ba9768a6
  bfa9dbd859e62711ede7792c16d383a9ba9768a6
  scratch clone, after --record: cmp evals/results/decompose-signals-2026-10-18.json <repo>/... && echo "first record untouched by --record"
  first record untouched by --record
  ```
  Both records are pure additions; the first is touched by exactly one
  commit, and its blob at HEAD is the blob 27bd1b0 wrote.
  `diff render(first) render(second)` differs in 30 lines: the digest,
  the rule sentence, 25 run lines (24 inferred implement shas moved by
  ADR-0111, plus this run's own line, which moved to observed and gained
  a review.md), and the three aggregate lines. That is the change
  ADR-0111 accepts; the two records are compared run by run, never as
  one series.
- Check (c): ADR-0111's premise and its two named consequences. For each
  of the 4 runs with an observed implement commit, an independent script
  walks the tool's own commit order after the observed D and finds the
  first breakdown version whose checkboxes are all `[x]` (a plain
  checkbox regex, cross-checked against the tool's `_done`). Then the
  faster-sdlc versions, and the first-live-dispatch and faster-sdlc
  lines.
- Evidence (c):
  ```
  $ python3 lasttick.py docs/features/decompose-outcome-signals docs/features/fail-closed-roll-up docs/features/pr-body-preflight docs/fixes/the-reviewer-token-runs-agent-code
  docs/features/decompose-outcome-signals: observed implement 56baba9; first all-checked after D 56baba9 (15 of 15 boxes; tool _done 15/15) -> EQUAL
  docs/features/fail-closed-roll-up: observed implement 27467df; first all-checked after D 27467df (7 of 7 boxes; tool _done 7/7) -> EQUAL
  docs/features/pr-body-preflight: observed implement 766292c; first all-checked after D 766292c (9 of 9 boxes; tool _done 9/9) -> EQUAL
  docs/fixes/the-reviewer-token-runs-agent-code: observed implement 755dc8c; first all-checked after D 755dc8c (13 of 13 boxes; tool _done 13/13) -> EQUAL

  faster-sdlc versions on refs read: 21 (done,total) per version: [(0, 11), (0, 11), (1, 11), (1, 11), (1, 11), (4, 11), (4, 11), (7, 11), (7, 11), (7, 11), (7, 11), (9, 11), (9, 11), (9, 11), (9, 11), (9, 11), (9, 11), (9, 11), (9, 11), (9, 11), (9, 11)]

  decompose-signals: feature:faster-sdlc — decompose inferred 406c370, implement none; re-plan unmeasurable — no implement boundary: no later commit checks every row; design gaps 0 inferred; review-traced unmeasurable — no review.md
  decompose-signals: feature:first-live-dispatch — decompose inferred 5540dd9, implement inferred 7442916; re-plan 4 of 8 (added 3, dropped 0, split 1, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 10 of 13 findings name an item

  $ grep -c "no later commit checks a row" tests/test_decompose_signals.py decompose_signals.py
  tests/test_decompose_signals.py:0
  decompose_signals.py:0
  ```
  All 4 observed implement commits equal their first all-checked commit,
  as ADR-0111's Context claims. faster-sdlc never reaches 11 of 11 on
  the refs read (its last version is 9 of 11), so it is unmeasurable
  with the new fixed reason, and first-live-dispatch reads `re-plan 4 of
  8 (added 3, dropped 0, split 1, merged 0; …)`, both as ADR-0111 and
  S15 accept. Under the first-tick rule the previous Verify quoted
  first-live-dispatch as `implement inferred fbfa3c3; re-plan 1 of 8
  (added 1, …)` and faster-sdlc as `implement inferred 76053d1; re-plan
  0 of 11`. The old reason string is gone from code and tests.
- Result: PASS

### 9. `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`, `python3 gates.py` and `python3 gates.py --selftest` all pass

- Check: each command at HEAD 4278f94 with a clean tree. The suite ran
  five times (see Not verified for the flake).
- Evidence:
  ```
  $ for i in 1 2 3 4; do python3 run_tests.py > tests_$i.txt 2>&1; echo "run $i exit $?"; done
  tests: 3412 tests across 107 modules in 25.9s on 8 workers, 0 problem(s)
  tests: 3412 tests across 107 modules in 26.1s on 8 workers, 0 problem(s)
  tests: 3412 tests across 107 modules in 25.6s on 8 workers, 0 problem(s)
  tests: 3412 tests across 107 modules in 26.0s on 8 workers, 0 problem(s)
  run 1 exit 0
  run 2 exit 0
  run 3 exit 0
  run 4 exit 0
  $ grep -l "failed" tests_*.txt
  (no output)
  $ python3 run_tests.py -j 16 > tests_j16.txt 2>&1; echo "exit $?"; tail -n 1 tests_j16.txt
  exit 0
  tests: 3412 tests across 107 modules in 23.7s on 16 workers, 0 problem(s)
  $ python3 lint.py; echo "lint exit $?"
  lint: 0 problem(s) across 34 skills
  lint exit 0
  $ python3 kb.py drift; echo "drift exit $?"
  drift: 0 problem(s)
  drift exit 0
  $ python3 gates.py && python3 gates.py --selftest; echo "gates&&selftest exit $?"
  gates: 0 problem(s)
  selftest: ok
  gates&&selftest exit 0
  ```
  `gates.py --selftest` prints `selftest: ok`, not `gates: 0
  problem(s)`; exit 0 is the pass. lint and gates were run again after
  this file was written (see the commit's hand-off).
- Result: PASS

### Breakdown acceptance criteria not covered above (S1 to S16)

- Check: S1 to S12b and S14 are pinned by tests in
  `tests/test_decompose_signals.py`, `tests/test_eval_schema.py`,
  `tests/test_dual_membership.py` and `tests/test_factory_cli.py`, all
  run here. S12's and S15's "no protected path changed" and "one_owner
  names nothing in decompose_signals.py" were checked directly. S15's
  behaviour list and S16's record clauses are criterion 8. S13's
  unedited first record is criterion 8b.
- Evidence:
  ```
  $ python3 -m unittest tests.test_eval_schema tests.test_dual_membership tests.test_factory_cli
  Ran 91 tests in 0.537s

  OK
  $ python3 -c "import decompose_signals as d; print('RULE has ADR-0111:', 'implement at the first later commit that checks every row' in d.RULE and 'ADR-0111' in d.RULE)"
  RULE has ADR-0111: True
  $ python3 one_owner.py | grep -c decompose_signals
  0
  $ git diff --stat main...HEAD -- skills/ factory/templates/ .claude-plugin/plugin.json LEDGER.md factory_init.py
  (no output)
  $ grep -c '^- \[ \]' docs/features/decompose-outcome-signals/breakdown.md
  0
  ```
- Result: PASS

## Failures

none.

## Not verified

- **The Implement-stage flake.** Implement once saw `run_tests.py`
  report `2 problem(s)`, described as an unnamed 8-test, ~60 s module.
  It did not recur: the previous Verify ran the suite six times, and
  this one five more (four at 8 workers, one at 16), all
  `0 problem(s)`, with no `failed` line in any captured output. Wall
  time here was steady at 23.7 s to 26.1 s, against the 25 s to 71 s
  swing the previous Verify saw. The previous Verify's analysis stands:
  `N problem(s)` counts failed modules, no module runs near 60 s on
  this machine, and none of the 8-test modules imports
  `decompose_signals`. Neither its module nor its cause is known; it
  stays **unexplained and pre-existing-or-environmental**, not fixed.
- **Carried from Review, deferred, not re-tested here as findings:** an
  empty `## Design gaps found` section is reported as a missing one
  (reason string only, no number changes), and `tests/timings.json` has
  no entry for `tests.test_decompose_signals`. Both are recorded in
  review.md as deferred.
- **The scratch clone's refs are a reconstruction.** It carries every
  ref this clone holds except worktree-private ones, with one branch
  reset. The reproduction rests on the tool's digest matching the
  record's `refs_digest`, which covers every `refname sha` line read.
- The Owner has not confirmed ADR-0109, ADR-0110 or ADR-0111; all three
  stay provisional. ADR-0111's details were filled in by an unattended
  Architect re-entry. This stage checks that the records reproduce and
  that ADR-0111's measured premise holds; it does not cite either
  record as a baseline.
