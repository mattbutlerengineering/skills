---
stage: verify
run: maintenance:tool-duplicates-that-drifted
date: 2026-10-25
---

# Verification: root tools hold second copies of one fact, and several have drifted

## Summary

8 PASS, 0 FAIL, 1 NOT RUN across 9 criteria, on HEAD `37b3439`.

- Each consolidated item's new tests fail against `origin/main`'s versions
  of the changed modules and pass on HEAD. The three readers that raised
  `RecursionError` and the dashboard that raised `UnicodeDecodeError` now
  report a problem instead.
- `one_owner.py` is down from 9 findings to 1. The one left is the COSTS
  pair, which the sibling run `a-spend-row-stalls-the-merge` (#1106) folds,
  so the target of 0 holds only once that merges in.
- NOT RUN: the scheduled gate digest and rejection miner against live
  GitHub. Their suites drive them through the injected gh port only.

## Criteria & evidence

### 1. New tests red on main's modules, green on HEAD

- Check: a scratch extract of HEAD with `origin/main`'s versions of the 14
  changed source modules dropped in. Then `python3 -m unittest
  tests.test_json_lines tests.test_knowledge_plane tests.test_cli
  tests.test_human_gates tests.test_dashboard` there and on HEAD. The
  scratch tree was removed after.
- Evidence:
  ```
  # origin/main's modules
  ERROR: test_conductor_close_history_refuses_the_file
  RecursionError: Stack overflow (used 16352 kB) while decoding a JSON array from a unicode string
  ERROR: test_dashboard_corrections_reports_the_line
  RecursionError: Stack overflow (used 16352 kB) while decoding a JSON array from a unicode string
  ERROR: test_kb_harvest_skips_the_line
  RecursionError: Stack overflow (used 16352 kB) while decoding a JSON array from a unicode string
  ERROR: test_a_run_that_cannot_be_oriented_is_a_problem_not_a_crash
  UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 56: invalid start byte
  ImportError: cannot import name 'active_runs' from 'knowledge_plane'
  ImportError: cannot import name 'read_gate_issues' from 'human_gates'
  Ran 228 tests
  FAILED (errors=13)

  # HEAD 37b3439
  Ran 355 tests in 8.336s
  OK
  ```
- Result: PASS

### 2. One repo-path rule, and the detectors' findings move only where intended

- Check:
  - `TestRepoPath`;
  - `python3 kb.py drift` on HEAD;
  - `md_claims.py check` over one extract of `origin/main`, run with main's
    md_claims and then with HEAD's, diffing the findings.
- Evidence:
  ```
  drift: 0 problem(s)

  # md_claims over the same tree
  before: md-claims: 547 problem(s) across 739 doc(s)
  after:  md-claims: 600 problem(s) across 739 doc(s)
  added 53 removed 0; the added paths by extension:
    46 jsonl
     6 html
     1 svg
  > md-claims: docs/backlog.md:99: path 'docs/factory/corrections.jsonl' does not exist
  ```
  - Every added finding names a path with an extension md_claims' old list
    did not know.
  - Some are truly dangling: `docs/factory/corrections.jsonl` is written by
    nothing.
  - About 20 name files that exist only once a tool has run, for example
    `docs/factory/decompose-lessons.jsonl` (written by `decompose_lessons
    update`) and launch-demo's `title.html` and `outro.html`. md_claims
    cannot tell those from dangling paths. That is new noise in an
    on-demand pass that is not a gate (corrected after review).
  - No finding was lost.
  - kb drift, the one of the two in CI, is unchanged.
- Result: PASS

### 3. One pinned-issue upsert and one gate-issue read

- Check: `TestUpsertPinnedIssue`, `TestReadGateIssues`, and the gate_digest
  and rejection_mining suites with their exact-string assertions untouched.
- Evidence:
  ```
  $ python3 -m unittest tests.test_gate_digest tests.test_rejection_mining tests.test_human_gates tests.test_cli
  Ran 221 tests in 8.012s
  OK
  ```
- Result: PASS

### 4. One JSON-lines reader

- Check: `tests/test_json_lines.py`. The seam cases, plus one case for each
  reader that raised before (criterion 1 quotes the red).
- Evidence:
  ```
  $ python3 -m unittest tests.test_json_lines tests.test_cost_ledger tests.test_conductor tests.test_conductor_close tests.test_kb_harvest tests.test_dashboard tests.test_cli
  Ran 458 tests in 8.811s
  OK
  ```
- Result: PASS

### 5. One active-run walk; the dashboard survives a broken run

- Check:
  - `TestActiveRuns`, the new dashboard case, and the board suite;
  - board and dashboard on this repo;
  - the dashboard's run count on HEAD against `origin/main`.
- Evidence:
  ```
  $ python3 -m unittest tests.test_board tests.test_dashboard tests.test_knowledge_plane
  Ran 198 tests in 0.190s
  OK
  $ python3 board.py . > /dev/null && echo board-renders
  board-renders
  HEAD:        83 runs; orient problems: []
  origin/main: 82 runs on main code
  ```
  The one extra run is this run's own directory, which `origin/main` does
  not hold.
- Result: PASS

### 6. The coincidences are marked, and one_owner reads clean but for the sibling's pair

- Check: `python3 one_owner.py` on HEAD.
- Evidence:
  ```
  one-owner: conductor_merge.py:75 COSTS and cost_ledger.py:29 COST_LEDGER state the same value — one fact, one owner
  one-owner: 1 problem(s)
  ```
  This is down from 9 on `origin/main` (defect.md quotes all nine). The COSTS
  pair is #1106's.
- Result: PASS

### 7. Backlog seed claimed and two follow-ups seeded

- Check: the claimed seed and the two new lines in `docs/backlog.md`, read
  through `protocol.parse_backlog`, and gates.
- Evidence:
  ```
  $ grep -c "(claimed: maintenance:tool-duplicates-that-drifted)" docs/backlog.md
  1
  $ python3 gates.py
  gates: 0 problem(s)
  ```
- Result: PASS

### 8. Payload regenerated and repo checks green

- Check: `python3 factory_init.py update-manifest`, then the four CI
  commands on HEAD.
- Evidence:
  ```
  factory-init: 0 problem(s)
  tests: 3925 tests across 123 modules in 41.6s on 8 workers, 0 problem(s)
  lint: 0 problem(s) across 35 skills
  drift: 0 problem(s)
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS

### 9. The scheduled digest and miner run unchanged against live GitHub

- Check: none run. It needs the `gate-digest` and `rejection-mining`
  workflows to run on main after the merge.
- Evidence: none.
- Result: NOT RUN

## Failures

None.

## Not verified

- Criterion 9: the live scheduled runs. Their suites drive every gh call
  through `FakeGh`, with the exact problem strings pinned, so a change in
  call shape would have failed there.
- `one_owner.py` reaching 0 depends on #1106 merging first.
