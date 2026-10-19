---
stage: verify
run: feature:decompose-outcome-signals
date: 2026-10-18
assumptions:
  - "No live interview: the autorun brief holds no Verify-specific answers, so the skill's defaults were taken. The criteria list is prd.md's nine success criteria, plus the breakdown acceptance criteria no PRD criterion covers (one section, at the end)."
  - "Recommended default taken (reproducing the record on the same refs): HEAD has moved two commits past the record's head (4f727c1), so this clone's refs are no longer the refs the record read. The record-time ref set was rebuilt in a scratch mirror clone (`git clone --mirror` of this repo, `refs/heads/feat/decompose-outcome-signals` reset to 4f727c1, tree checked out at 4f727c1). The tool's own digest line is the proof that the ref set matches: it printed the record's digest 802d11762774. Nothing in this repo's refs or tree was changed."
  - "Recommended default taken (flake investigation): six full-suite runs (five at the default 8 workers, one at -j 16) plus one per-module timing run through run_tests' own run_all. The brief sets no count; the orchestrator suggested 3 to 5."
---

# Verification: Decompose outcome signals from git history

## Summary

9 of 9 PRD success criteria PASS, 0 FAIL, 0 NOT RUN. The breakdown
acceptance criteria not covered by a PRD criterion also pass. The
committed snapshot is reproduced byte for byte when the tool is rerun
with `--record` on the record-time refs. On today's refs the output
differs from the snapshot in one run's line (this run's own), the two
aggregates that line feeds, and the digest. The difference is explained
under criterion 8: the implement commit 56baba9 landed after the record.
Not verified: the Implement-stage flake. It did not recur in six full
runs and its module could not be identified, so it stays an open
unknown (see Not verified).

## Criteria & evidence

### 1. One invocation measures every run directory holding a `breakdown.md` and prints a per-run row for each plus an aggregate, in the problem-string / count contract

- Check: count the run directories with a `breakdown.md`, then run
  `python3 decompose_signals.py` at HEAD 56baba9 and count its run lines.
  Also run `python3 factory.py decompose-signals` and compare.
- Evidence:
  ```
  $ ls docs/breakdown.md docs/features/*/breakdown.md docs/fixes/*/breakdown.md 2>/dev/null | wc -l
        36
  $ python3 decompose_signals.py; echo "exit $?"
  decompose-signals: refs read — refs/heads (401), refs/pr (13), refs/remotes/origin (184), refs/remotes/pr (488); refs/stash skipped; digest 06361a9947ab
  decompose-signals: boundary rule — a boundary is observed when its commit subject reads docs(<any scope>): <stage>, the stage a whole word, and the commit changes that stage's artifact in the run's own directory; any other boundary is inferred (ADR-0109)
  decompose-signals: feature:codex-style-standards-enforcement — decompose inferred ebe8b2a, implement inferred 5f30760; re-plan 0 of 14 (added 0, dropped 0, split 0, merged 0; renamed 14) inferred; design gaps 0 inferred; review-traced 3 of 12 findings name an item
  decompose-signals: feature:decompose-outcome-signals — decompose observed de92f3c, implement observed 56baba9; re-plan 2 of 13 (added 2, dropped 0, split 0, merged 0; renamed 0) observed; design gaps 1 observed; review-traced unmeasurable — no review.md
  decompose-signals: feature:docs-audit — decompose inferred da4b751, implement inferred bdac934; re-plan 0 of 11 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 9 findings name an item
  decompose-signals: feature:factory-evolution-v1 — decompose inferred abed301, implement inferred aa5e19f; re-plan 0 of 8 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 3 of 10 findings name an item
  decompose-signals: feature:fail-closed-roll-up — decompose observed 637f2e7, implement observed 27467df; re-plan 0 of 7 (added 0, dropped 0, split 0, merged 0; renamed 0) observed; design gaps 0 observed; review-traced 0 of 11 findings name an item
  decompose-signals: feature:faster-sdlc — decompose inferred 406c370, implement inferred 76053d1; re-plan 0 of 11 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced unmeasurable — no review.md
  decompose-signals: feature:first-live-dispatch — decompose inferred 5540dd9, implement inferred fbfa3c3; re-plan 1 of 8 (added 1, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 10 of 13 findings name an item
  decompose-signals: feature:launch-demo — decompose inferred c9808b1, implement inferred d4ff044; re-plan 0 of 14 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 3 of 10 findings name an item
  decompose-signals: feature:lean-and-polish — decompose inferred e24b6b3, implement inferred bdba36e; re-plan 0 of 3 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 0 findings — review.md has no finding heading
  decompose-signals: feature:lean-in-the-build — decompose inferred faddef2, implement inferred 833b22c; re-plan 0 of 3 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 3 findings name an item
  decompose-signals: feature:orchestrator — decompose inferred 75e3bf7, implement inferred 0724c31; re-plan 0 of 12 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 8 findings name an item
  decompose-signals: feature:pipeline-board — decompose inferred 4b1b72a, implement inferred 44385da; re-plan 0 of 6 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 4 findings name an item
  decompose-signals: feature:pocock-1-3-takeaways — decompose inferred 9129d61, implement inferred 7c195d6; re-plan 0 of 14 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 5 findings name an item
  decompose-signals: feature:pr-body-preflight — decompose observed 772e374, implement observed 766292c; re-plan 0 of 9 (added 0, dropped 0, split 0, merged 0; renamed 0) observed; design gaps 1 observed; review-traced 0 of 15 findings name an item
  decompose-signals: feature:process-dashboard — decompose inferred 87b59eb, implement inferred c7d51cf; re-plan 0 of 11 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 4 findings name an item
  decompose-signals: feature:readme-skill-map — decompose inferred 2973bbc, implement inferred 4e87871; re-plan 0 of 6 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 4 findings name an item
  decompose-signals: feature:seed-backlog — decompose inferred 1ac1042, implement inferred d8c822f; re-plan 0 of 7 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 2 findings name an item
  decompose-signals: feature:software-factory — decompose observed 0661682, implement inferred 0b706b5; re-plan 0 of 18 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 5 findings name an item
  decompose-signals: maintenance:a-blind-find-is-not-a-failed-agent — decompose inferred b28d953, implement inferred 69bb5a4; re-plan 0 of 4 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 1 of 4 findings name an item
  decompose-signals: maintenance:a-timestamp-the-digest-cannot-parse — decompose inferred e8aae36, implement inferred 6adb359; re-plan 6 of 7 (added 0, dropped 6, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 1 findings name an item
  decompose-signals: maintenance:closed-intake-mutes-the-detector — decompose inferred ee5532c, implement inferred 664d8c1; re-plan 0 of 4 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 0 of 4 findings name an item
  decompose-signals: maintenance:dedup-identity-has-two-owners — decompose inferred 88fbb34, implement inferred befc6e2; re-plan 0 of 3 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 1 of 1 findings name an item
  decompose-signals: maintenance:deepening-cli-seams — decompose none, implement none; re-plan unmeasurable — the first version (ec957eb) already checks 9 of 9 rows; design gaps unmeasurable — the first version (ec957eb) already checks 9 of 9 rows; review-traced 2 of 5 findings name an item
  decompose-signals: maintenance:deepening-tool-seams — decompose inferred 4a287ff, implement inferred 80f5496; re-plan 0 of 15 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 3 of 4 findings name an item
  decompose-signals: maintenance:empty-is-not-the-same-as-broken — decompose inferred 738573f, implement inferred 8d7e5de; re-plan 0 of 4 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 1 of 2 findings name an item
  decompose-signals: maintenance:gate-timeline-timestamp-trust — decompose none, implement none; re-plan unmeasurable — the first version (b4dd17a) already checks 2 of 2 rows; design gaps unmeasurable — the first version (b4dd17a) already checks 2 of 2 rows; review-traced 0 of 3 findings name an item
  decompose-signals: maintenance:marker-diagnostics-that-lie — decompose inferred 5d993dc, implement inferred 7b7ad04; re-plan 0 of 5 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 0 of 5 findings name an item
  decompose-signals: maintenance:one-fact-one-owner — decompose none, implement none; re-plan unmeasurable — the first version (a527688) already checks 1 of 13 rows; design gaps unmeasurable — the first version (a527688) already checks 1 of 13 rows; review-traced 3 of 8 findings name an item
  decompose-signals: maintenance:one-fence-rule — decompose inferred 7da232d, implement inferred e72f059; re-plan 0 of 4 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 0 of 4 findings name an item
  decompose-signals: maintenance:one-guarded-file-read — decompose inferred 110ffc6, implement inferred 5e5f494; re-plan 0 of 18 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 1 of 11 findings name an item
  decompose-signals: maintenance:one-labels-walk — decompose none, implement none; re-plan unmeasurable — the first version (45f4b43) already checks 1 of 3 rows; design gaps unmeasurable — the first version (45f4b43) already checks 1 of 3 rows; review-traced 0 of 2 findings name an item
  decompose-signals: maintenance:quoted-token-is-not-a-claim — decompose none, implement none; re-plan unmeasurable — the first version (5210702) already checks 1 of 2 rows; design gaps unmeasurable — the first version (5210702) already checks 1 of 2 rows; review-traced 0 of 3 findings name an item
  decompose-signals: maintenance:row-done-guard — decompose none, implement none; re-plan unmeasurable — the first version (4520083) already checks 1 of 1 rows; design gaps unmeasurable — the first version (4520083) already checks 1 of 1 rows; review-traced 0 of 3 findings name an item
  decompose-signals: maintenance:run-discovery-ignores-open-prs — decompose inferred e142434, implement inferred d0a8a6c; re-plan 0 of 4 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 1 of 2 findings name an item
  decompose-signals: maintenance:the-digest-says-what-it-could-read — decompose inferred ca717be, implement inferred fa1954f; re-plan 0 of 5 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 0 of 2 findings name an item
  decompose-signals: maintenance:the-reviewer-token-runs-agent-code — decompose observed ba286e5, implement observed 755dc8c; re-plan 0 of 13 (added 0, dropped 0, split 0, merged 0; renamed 0) observed; design gaps 0 observed; review-traced 0 of 5 findings name an item
  decompose-signals: aggregate re-plan — observed 2/42 over 4 run(s); inferred 7/219 over 26 run(s); combined 9/261 over 30 run(s); unmeasurable 6 run(s)
  decompose-signals: aggregate design gaps — observed 2/4 over 4 run(s); inferred 0/18 over 18 run(s); combined 2/22 over 22 run(s); unmeasurable 14 run(s)
  decompose-signals: aggregate review-traced — observed 32/184 over 34 run(s); inferred 0/0 over 0 run(s); combined 32/184 over 34 run(s); unmeasurable 2 run(s)
  decompose-signals: 36 run(s), 0 problem(s)
  exit 0
  $ python3 factory.py decompose-signals > ds_factory.txt; cmp ds.txt ds_factory.txt && echo same
  factory exit 0
  same
  ```
  36 run lines, three aggregate lines, and the `cli.report` summary
  `decompose-signals: 36 run(s), 0 problem(s)`.
- Result: PASS

### 2. Every per-run boundary is labelled `observed` or `inferred`, and the aggregate prints observed, inferred and combined figures for each of the three signals

- Check: the output above, plus the boundary tests through the public
  interface.
- Evidence (from the output in criterion 1, and the test run):
  ```
  decompose-signals: feature:fail-closed-roll-up — decompose observed 637f2e7, implement observed 27467df; re-plan 0 of 7 (...) observed; ...
  decompose-signals: feature:software-factory — decompose observed 0661682, implement inferred 0b706b5; re-plan 0 of 18 (...) inferred; ...
  decompose-signals: aggregate re-plan — observed 2/42 over 4 run(s); inferred 7/219 over 26 run(s); combined 9/261 over 30 run(s); unmeasurable 6 run(s)
  decompose-signals: aggregate design gaps — observed 2/4 over 4 run(s); inferred 0/18 over 18 run(s); combined 2/22 over 22 run(s); unmeasurable 14 run(s)
  decompose-signals: aggregate review-traced — observed 32/184 over 34 run(s); inferred 0/0 over 0 run(s); combined 32/184 over 34 run(s); unmeasurable 2 run(s)

  test_any_scope_and_no_em_dash_is_observed (...TestObservedDecompose...) ... ok
  test_the_earliest_commit_changing_the_breakdown (...TestInferredDecompose...) ... ok
  test_observed_is_the_earliest_implement_commit_after_d (...TestImplement...) ... ok
  test_inferred_is_the_earliest_later_version_with_a_done_row (...TestImplement...) ... ok
  ```
  (The `(...)` in the first two lines elides the five counts already
  quoted in full under criterion 1.) Runs with no boundary print
  `decompose none, implement none` and carry the reason on each signal
  (criterion 3).
- Result: PASS

### 3. Each unmeasurable run is printed by name with a reason and is left out of every aggregate count

- Check: the unmeasurable lines in the output, and the arithmetic of each
  aggregate (measured runs + unmeasurable runs = 36).
- Evidence:
  ```
  decompose-signals: maintenance:deepening-cli-seams — decompose none, implement none; re-plan unmeasurable — the first version (ec957eb) already checks 9 of 9 rows; design gaps unmeasurable — the first version (ec957eb) already checks 9 of 9 rows; review-traced 2 of 5 findings name an item
  decompose-signals: feature:lean-and-polish — ...; design gaps unmeasurable — no "Design gaps found" section at the decompose boundary; review-traced 0 findings — review.md has no finding heading
  decompose-signals: feature:faster-sdlc — ...; review-traced unmeasurable — no review.md

  re-plan:       combined 30 run(s) + unmeasurable 6  = 36
  design gaps:   combined 22 run(s) + unmeasurable 14 = 36
  review-traced: combined 34 run(s) + unmeasurable 2  = 36

  test_an_unmeasurable_run (tests.test_decompose_signals.TestTheFiveFixtureRuns.test_an_unmeasurable_run) ... ok
  ```
  The sums are read off the three aggregate lines quoted under
  criterion 1. Six runs are unmeasurable on re-plan, all with the
  `already checks` reason. Re-plan and design gaps are unmeasurable per
  signal, so a run can be unmeasurable on one and measured on another.
- Result: PASS

### 4. The output names the refs that were read and the subject-match rule that was applied

- Check: the two header lines.
- Evidence:
  ```
  decompose-signals: refs read — refs/heads (401), refs/pr (13), refs/remotes/origin (184), refs/remotes/pr (488); refs/stash skipped; digest 06361a9947ab
  decompose-signals: boundary rule — a boundary is observed when its commit subject reads docs(<any scope>): <stage>, the stage a whole word, and the commit changes that stage's artifact in the run's own directory; any other boundary is inferred (ADR-0109)
  ```
- Result: PASS

### 5. The tool makes no network call: a test or a code read shows it runs no fetch, and its only external CLI is git through `cli.py`

- Check: the two no-network tests, a code read of imports and git calls,
  and a grep for network verbs.
- Evidence:
  ```
  test_only_local_read_only_verbs_are_run (tests.test_decompose_signals.TestNoNetwork.test_only_local_read_only_verbs_are_run) ... ok
  test_the_module_names_no_network_verb (tests.test_decompose_signals.TestNoNetwork.test_the_module_names_no_network_verb) ... ok
  test_only_local_read_only_verbs_are_run_end_to_end (tests.test_decompose_signals.TestReportFailures.test_only_local_read_only_verbs_are_run_end_to_end) ... ok

  $ grep -nE "^import|^from|subprocess|urllib|socket|http" decompose_signals.py
  20:import datetime
  21:import hashlib
  22:from collections import Counter
  23:import re
  24:import sys
  25:from pathlib import Path
  27:from cli import CLI_FAILURES, detail, read_file, report, runner
  28:from eval_schema import write_snapshot
  29:from knowledge_plane import (BLOCKED_BY, ROW, WO_TOKEN, breakdown_files,
  31:from protocol import STAGE_ARTIFACTS, run_ref
  $ grep -nE '_git\(|runner\(' decompose_signals.py
  58:def _git(run, root, args, input=None):
  91:    out, problems = _git(run, root, ["for-each-ref",
  109:        out, problems = _git(
  122:    return _git(run, root, ["show", f"{sha}:{path}"])
  546:    dirty, failed = _git(run, root, ["status", "--porcelain", "--",
  548:    head, failed_head = _git(run, root, ["rev-parse", "HEAD"])
  573:    run = run or runner("git", timeout=GIT_TIMEOUT)
  $ grep -nE "fetch|ls-remote|pull|remote" decompose_signals.py
  11:cli.runner and injected as `run`; the tool never fetches. PR head refs
  12:are read only once they are fetched, which is a manual step:
  14:    git fetch origin '+refs/pull/*/head:refs/remotes/pr/*'
  67:    """refs/remotes/<remote> for a remote-tracking ref, else the first two
  70:    depth = 3 if parts[1:2] == ["remotes"] and len(parts) > 3 else 2
  ```
  Line 109 is the `log` call. Every `fetch` / `remote` hit is the
  docstring's manual step or the ref-namespace helper; no git verb
  besides `for-each-ref`, `log`, `show`, `status` and `rev-parse` is
  run, and the only process launched is `cli.runner("git", ...)`.
- Result: PASS

### 6. Tests through the public interface cover a run with no re-plans, a split item, a run routed back to Architect, a run with only inferred boundaries, and an unmeasurable run, each asserting exact output strings

- Check: `python3 -m unittest -v tests.test_decompose_signals`, and a read
  of the five fixture tests. Each one drives `main([])` against a real
  temp git repo and asserts the whole run line with `assertEqual`.
- Evidence:
  ```
  test_a_run_routed_back_to_architect (tests.test_decompose_signals.TestTheFiveFixtureRuns.test_a_run_routed_back_to_architect) ... ok
  test_a_run_with_a_split_item (tests.test_decompose_signals.TestTheFiveFixtureRuns.test_a_run_with_a_split_item) ... ok
  test_a_run_with_no_re_plans (tests.test_decompose_signals.TestTheFiveFixtureRuns.test_a_run_with_no_re_plans) ... ok
  test_a_run_with_only_inferred_boundaries (tests.test_decompose_signals.TestTheFiveFixtureRuns.test_a_run_with_only_inferred_boundaries) ... ok
  test_an_unmeasurable_run (tests.test_decompose_signals.TestTheFiveFixtureRuns.test_an_unmeasurable_run) ... ok
  test_a_renumbering_between_d_and_i_is_no_re_plan (tests.test_decompose_signals.TestARenumberedRun.test_a_renumbering_between_d_and_i_is_no_re_plan) ... ok
  test_the_exact_report (tests.test_decompose_signals.TestTheWholeReport.test_the_exact_report) ... ok
  ----------------------------------------------------------------------
  Ran 72 tests in 7.911s

  OK
  ```
  For example, the split case asserts
  `... re-plan 3 of 2 (added 2, dropped 0, split 1, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced unmeasurable — no review.md`
  as one exact string (tests/test_decompose_signals.py, line 707).
- Result: PASS

### 7. For the review-traced signal, a run with findings that name no item and a run with no `review.md` print different strings, and a test asserts both

- Check: the review-shape tests, and real-repo output.
- Evidence:
  ```
  test_no_review_md (tests.test_decompose_signals.TestReviewShapes.test_no_review_md) ... ok
  test_a_review_with_no_finding_heading (tests.test_decompose_signals.TestReviewShapes.test_a_review_with_no_finding_heading) ... ok
  test_findings_that_name_an_item (tests.test_decompose_signals.TestReviewShapes.test_findings_that_name_an_item) ... ok

  real output, three distinct shapes:
  feature:faster-sdlc — ...; review-traced unmeasurable — no review.md
  feature:lean-and-polish — ...; review-traced 0 findings — review.md has no finding heading
  feature:docs-audit — ...; review-traced 0 of 9 findings name an item
  ```
  `test_a_review_with_no_finding_heading` asserts the exact string and
  `assertNotEqual` against the no-review.md string. docs-audit shows the
  third case, findings that name no item (`0 of 9`), which also reads
  differently from `no review.md`.
- Result: PASS

### 8. The first real numbers are committed append-only as the tool's unedited output, and rerunning on the same refs gives the same numbers

- Check: (a) the snapshot's history; (b) rebuild the record-time refs in a
  scratch mirror clone, rerun the tool there with and without `--record`,
  `cmp` the written file with the committed one, and diff `render()` of
  the committed snapshot against the rerun; (c) diff the committed
  snapshot against today's output on the current refs, and explain each
  difference.
- Evidence:
  ```
  (a)
  $ git log --format='%h %s' -- evals/results/decompose-signals-2026-10-18.json
  27bd1b0 chore(decompose-signals): S13 record the first real numbers
   evals/results/decompose-signals-2026-10-18.json | 1135 +++++++++++++++++++++++
   1 file changed, 1135 insertions(+)

  (b) scratch mirror clone, feat/decompose-outcome-signals reset to 4f727c1, tree at 4f727c1
  $ git rev-parse HEAD
  4f727c1bdeed70a19a6dca248e79090919657e5c
  $ python3 decompose_signals.py
  exit 0
  decompose-signals: refs read — refs/heads (401), refs/pr (13), refs/remotes/origin (184), refs/remotes/pr (488); refs/stash skipped; digest 802d11762774
  decompose-signals: aggregate re-plan — observed 0/29 over 3 run(s); inferred 7/232 over 27 run(s); combined 7/261 over 30 run(s); unmeasurable 6 run(s)
  decompose-signals: aggregate design gaps — observed 1/3 over 3 run(s); inferred 0/19 over 19 run(s); combined 1/22 over 22 run(s); unmeasurable 14 run(s)
  decompose-signals: aggregate review-traced — observed 32/184 over 34 run(s); inferred 0/0 over 0 run(s); combined 32/184 over 34 run(s); unmeasurable 2 run(s)
  decompose-signals: 36 run(s), 0 problem(s)
  $ python3 decompose_signals.py --record
  decompose-signals: recorded evals/results/decompose-signals-2026-10-18.json
  decompose-signals: 36 run(s), 0 problem(s)
  record exit 0
  $ cmp evals/results/decompose-signals-2026-10-18.json /Users/mbutler/github/skills/evals/results/decompose-signals-2026-10-18.json && echo "BYTE-IDENTICAL to committed snapshot"
  BYTE-IDENTICAL to committed snapshot
  $ sed '$d' repro_out.txt | diff - rendered.txt && echo "IDENTICAL: ..."
  IDENTICAL: render(committed snapshot) == rerun on record-time refs (41 lines)

  (c) render(committed snapshot) against today's output at 56baba9
  1c1
  < decompose-signals: refs read — ...; refs/stash skipped; digest 802d11762774
  ---
  > decompose-signals: refs read — ...; refs/stash skipped; digest 06361a9947ab
  4c4
  < decompose-signals: feature:decompose-outcome-signals — decompose observed de92f3c, implement inferred a8dbcb9; re-plan 0 of 13 (added 0, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced unmeasurable — no review.md
  ---
  > decompose-signals: feature:decompose-outcome-signals — decompose observed de92f3c, implement observed 56baba9; re-plan 2 of 13 (added 2, dropped 0, split 0, merged 0; renamed 0) observed; design gaps 1 observed; review-traced unmeasurable — no review.md
  39,40c39,40
  < decompose-signals: aggregate re-plan — observed 0/29 over 3 run(s); inferred 7/232 over 27 run(s); combined 7/261 over 30 run(s); unmeasurable 6 run(s)
  < decompose-signals: aggregate design gaps — observed 1/3 over 3 run(s); inferred 0/19 over 19 run(s); combined 1/22 over 22 run(s); unmeasurable 14 run(s)
  ---
  > decompose-signals: aggregate re-plan — observed 2/42 over 4 run(s); inferred 7/219 over 26 run(s); combined 9/261 over 30 run(s); unmeasurable 6 run(s)
  > decompose-signals: aggregate design gaps — observed 2/4 over 4 run(s); inferred 0/18 over 18 run(s); combined 2/22 over 22 run(s); unmeasurable 14 run(s)
  ```
  On the same refs the numbers are identical, so the criterion holds.
  On today's refs, every difference comes from one cause: the branch
  tip moved from 4f727c1 to 56baba9. The digest covers the ref tips, so
  it changes. This run's own line changes because 56baba9 is its
  observed `implement —` commit. At record time no such commit existed,
  so the implement boundary was the inferred first tick a8dbcb9 (the S2
  commit). The (D, I] window now runs to 56baba9. It holds the two items
  added at the Architect re-entry (S12a, S12b), which gives `added 2`,
  and the architect commit d9ee471, which gives `design gaps 1`. The run
  moves from the inferred to the observed population, and that accounts
  for every aggregate change (observed re-plan +1 run, 0/29 to 2/42;
  inferred −1 run, 7/232 to 7/219; design gaps likewise). The other 35
  run lines are identical, and so is the review-traced aggregate.
- Result: PASS

### 9. `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`, `python3 gates.py` and `python3 gates.py --selftest` all pass

- Check: each command at HEAD 56baba9 with a clean tree. The test suite
  ran six times (see Not verified for the flake).
- Evidence:
  ```
  $ python3 run_tests.py    (five sequential runs, default workers)
  tests: 3401 tests across 107 modules in 71.3s on 8 workers, 0 problem(s)
  run 1 exit 0
  tests: 3401 tests across 107 modules in 66.2s on 8 workers, 0 problem(s)
  run 2 exit 0
  tests: 3401 tests across 107 modules in 36.6s on 8 workers, 0 problem(s)
  run 3 exit 0
  tests: 3401 tests across 107 modules in 25.0s on 8 workers, 0 problem(s)
  run 4 exit 0
  tests: 3401 tests across 107 modules in 25.2s on 8 workers, 0 problem(s)
  run 5 exit 0
  $ python3 run_tests.py -j 16
  tests: 3401 tests across 107 modules in 22.5s on 16 workers, 0 problem(s)
  exit 0
  $ python3 lint.py
  lint: 0 problem(s) across 34 skills
  lint exit 0
  $ python3 kb.py drift
  drift: 0 problem(s)
  drift exit 0
  $ python3 gates.py
  gates: 0 problem(s)
  gates exit 0
  $ python3 gates.py --selftest
  selftest: ok
  selftest exit 0
  ```
  `gates.py --selftest` prints `selftest: ok`, not
  `gates: 0 problem(s)` as CLAUDE.md's Verify line suggests. Exit 0 is
  the pass. lint, drift and gates were run again after this file was
  written (see Hand-off).
- Result: PASS

### Breakdown acceptance criteria not covered above (S1–S13)

- Check: the S1–S12b acceptance criteria are pinned by the tests in
  `tests/test_decompose_signals.py`, `tests/test_eval_schema.py`,
  `tests/test_dual_membership.py` and `tests/test_factory_cli.py`, all
  run here. S12's "no protected path changed" and "one_owner names
  nothing in decompose_signals.py" were checked directly. S13's
  unedited-record clause is criterion 8.
- Evidence:
  ```
  $ python3 -m unittest tests.test_eval_schema tests.test_dual_membership tests.test_factory_cli
  Ran 91 tests in 0.523s

  OK
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

- **The Implement-stage flake.** Implement saw one `run_tests.py` run
  report `2 problem(s)`, described as an unnamed 8-test, ~60 s module.
  It did not recur here: six full runs reported 0 problem(s) (criterion
  9), and one more run through `run_tests.run_all` with per-module
  timing had no failure. What the investigation found:
  - `run_tests.py`'s `N problem(s)` counts failed **modules**, not
    failed tests, and `main` prints `tests: <module> failed` plus that
    module's own output before the summary line. So 2 problem(s) means
    two modules failed, and their names were printed above the summary.
    Implement's note says the output did not name the module, so it
    most likely saw only the tail. The 8 tests and 60 s were probably
    one failing module's own `Ran 8 tests in …` line.
  - No module comes near 60 s on this machine. The per-module run's
    slowest were test_conductor_merge 11.8 s (39 tests),
    test_decompose_signals 11.0 s (72), test_trace 10.5 s (16),
    test_gates 8.3 s (294) and test_cli 7.6 s (102). The 8-test modules
    are test_trigger_eval_run_eval_omp 1.6 s,
    test_shadowed_definitions 0.6 s, test_conductor_setup 0.2 s,
    test_factory_roles 0.1 s and test_model_routing 0.1 s. A 60 s,
    8-test module only fits heavy machine load. Wall time here swung
    from 71 s to 25 s between back-to-back runs with nothing else
    changed, which points to outside load on the host.
  - Relation to this run: no evidence links it. test_decompose_signals
    has 72 tests, not 8, and passed in every run. None of the 8-test
    modules imports `decompose_signals` or reads the refs or git walk.
    `grep -l decompose_signals` over the five 8-test modules printed
    nothing (exit 1).
    It is recorded as **unexplained and pre-existing-or-environmental**,
    not fixed. Neither its module nor its cause is known.
- **An observation, not a failure:** `tests/timings.json` has no entry
  for `tests.test_decompose_signals` (99 entries for 107 modules), so the
  runner schedules this 11 s module last, at 0 s, and it can stretch
  the wall time. A `python3 run_tests.py --record` after a clean run
  would fix it. That is outside this stage, and the file was not
  touched.
- **For Review and for #987:** the committed baseline measures this run
  while it was still in flight. Its row there reads `implement inferred
  a8dbcb9; re-plan 0 of 13 … inferred; design gaps 0 inferred`. Once
  this branch's implement commit exists, the same run reads `implement
  observed 56baba9; re-plan 2 of 13 … observed; design gaps 1 observed`.
  The record is honest for the refs it read, and the digest makes that
  checkable. But a calibration step that compares a later record with
  this one will see this run change population. It should compare
  per-run rows, not only aggregates.
- The Owner has not confirmed ADR-0109 or ADR-0110; both stay
  provisional. ADR-0109 says the Owner confirms it before the first
  record is cited. This stage does not cite the record. It only checks
  that the record can be reproduced.
