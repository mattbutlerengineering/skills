---
stage: verify
run: maintenance:the-selftest-cannot-see-a-dodge
date: 2026-10-18
assumptions:
  - "No prd.md exists for a maintenance run, so the criteria walked below are the autorun brief's Success criteria and defect.md's Expected clause, plus each work item's Accept line that no criterion covers, plus the stamped-repo run the orchestrator asked for. defect.md's Work items stand in for breakdown.md (re-entry: implement), and all nine are checked, so the soft gate holds."
  - "The four reversions are applied by a scratchpad script (mutate_verify.py) to a detached scratch worktree at aa0d38d, and then to a freshly stamped temp repo, never to the working tree. Each reversion is applied alone, its landing is checked (new text present, old text absent), the selftest runs, and the file's original bytes are written back before the next one. Both scratch trees were removed afterwards."
  - "A control run puts origin/main's gates_selftest.py into the same scratch worktree and replays the four reversions, to show the new rows are what turn the selftest red. That control is not asked for by the brief; it is the skill's default of proving the evidence, not the summary."
  - "origin/main had not moved: `git fetch origin` left it at f8c16d9, and `git merge-base --is-ancestor origin/main HEAD` held, so no merge was needed before verifying."
---

# Verification: the selftest cannot see a dodge

## Summary

8 criteria: 8 PASS, 0 FAIL, 0 NOT RUN. On HEAD `aa0d38d`, `gates.py
--selftest` prints `selftest: ok`. Each of the four reversions (O's date,
M's date, H's date, H's zero count) turns it to `selftest: FAIL` with one
failure line, naming only that reversion's own row and its own artifact
path. With origin/main's selftest, the same four reversions all print
`selftest: ok`. The same holds in a freshly stamped temp repo through
`python3 tools/factory/gates.py --selftest`, the consumer path the brief
names. The root and payload `gates_selftest.py` are byte-identical and
detector E is clean. The whole battery is green. Next stage: Review.

## Criteria & evidence

### 1. The selftest prints `selftest: ok` on the fixed tree

Source: brief Success criterion 1, and the Accept lines of the four row
work items ("passes on today's code").

- Check: `python3 gates.py --selftest` on HEAD, tree clean
- Evidence:
  ```
  $ git rev-parse --short HEAD
  aa0d38d
  $ python3 gates.py --selftest
  selftest: ok
  ```
- Result: PASS

### 2. Each reverted fix fails the selftest, naming only its own row

Source: brief Success criterion 2, defect.md Expected (items 1 to 4),
and the Accept lines of the "Mutation proof" and four row work items
(each expected string names its own artifact path; the H rows are
path-specific). The reversions are the defect brief's own shapes: a raw
compare at the `check_prd_coverage` call site (O), the same at the
`check_capture_completeness` call site (M), a raw compare in
`_rollup_applies` (H date), and `_names_unknown` returning
`bool(SUMMARY_UNKNOWN_TERM.search(line))` (H zero).

- Check: in a detached scratch worktree at `aa0d38d`, run
  `python3 -I <scratchpad>/mutate_verify.py <wt>/gates.py "python3
  gates.py --selftest" <wt>`, then `git status --porcelain` there
- Evidence:
  ```
  aa0d38d
  selftest: ok
  baseline exit=0
  === reversion O (landed: True)
  O quoted date: expected a problem containing 'docs/features/demo/prd.md:12 PRD-0001 §Actors is cited by no breakdown row', got []
  selftest: FAIL
  exit=1
  === reversion M (landed: True)
  M quoted date: expected a problem containing "docs/fixes/demo/defect.md missing required section 'Root-cause hypothesis'", got []
  selftest: FAIL
  exit=1
  === reversion Hdate (landed: True)
  H quoted date: expected a problem containing 'docs/features/rollup/verification.md:7 summary "Summary" neither counts nor names', got []
  selftest: FAIL
  exit=1
  === reversion Hzero (landed: True)
  H zero count: expected a problem containing 'docs/features/rollup/verification.md:7 summary "Summary" neither counts nor names', got []
  selftest: FAIL
  exit=1
  restored: True
  ```
  The control: origin/main's `gates_selftest.py` copied into the same
  worktree, the same four reversions replayed. None is caught, so the
  new rows are what catch them.
  ```
  $ git show origin/main:gates_selftest.py > gates_selftest.py
  === reversion O (landed: True)
  selftest: ok
  exit=0
  === reversion M (landed: True)
  selftest: ok
  exit=0
  === reversion Hdate (landed: True)
  selftest: ok
  exit=0
  === reversion Hzero (landed: True)
  selftest: ok
  exit=0
  restored: True
  ```
- Result: PASS

### 3. A stamped repo's own selftest sees each reversion

Source: the brief's Run scale (a stamped repo runs only
`tools/factory/gates.py --selftest`), and the orchestrator's instruction
for this stage. A temp dir under the scratchpad is `git init`-ed and
stamped from this branch, its selftest is run, then the four reversions
are applied to the stamped `tools/factory/gates.py` one at a time.

- Check: `python3 factory_init.py stamp <tmp>`, then from `<tmp>`:
  `cmp`, `python3 tools/factory/gates.py --selftest`, and the mutation
  script against `<tmp>/tools/factory/gates.py`
- Evidence:
  ```
  $ python3 factory_init.py stamp <tmp>
  factory-init: 0 problem(s)
  stamp exit=0
  $ cmp tools/factory/gates_selftest.py <repo>/gates_selftest.py && echo "stamped copy == branch root copy"
  stamped copy == branch root copy
  $ python3 tools/factory/gates.py --selftest
  selftest: ok
  exit=0
  === reversion O (landed: True)
  O quoted date: expected a problem containing 'docs/features/demo/prd.md:12 PRD-0001 §Actors is cited by no breakdown row', got []
  selftest: FAIL
  exit=1
  === reversion M (landed: True)
  M quoted date: expected a problem containing "docs/fixes/demo/defect.md missing required section 'Root-cause hypothesis'", got []
  selftest: FAIL
  exit=1
  === reversion Hdate (landed: True)
  H quoted date: expected a problem containing 'docs/features/rollup/verification.md:7 summary "Summary" neither counts nor names', got []
  selftest: FAIL
  exit=1
  === reversion Hzero (landed: True)
  H zero count: expected a problem containing 'docs/features/rollup/verification.md:7 summary "Summary" neither counts nor names', got []
  selftest: FAIL
  exit=1
  restored: True
  $ python3 tools/factory/gates.py --selftest
  selftest: ok
  after restore exit=0
  ```
- Result: PASS

### 4. The in-repo mutation pins pass

Source: Implement's logged assumption (defect.md Notes): two
`TestSelftest` tests keep the mutation proof running after this run.
They patch `gates._grandfathered` with a raw compare and expect exactly
the three date rows to fail, and patch `gates._names_unknown` with a
zero-blind search and expect exactly the zero-count row to fail.

- Check: both tests run by name, verbosely
- Evidence:
  ```
  $ python3 -m unittest -v tests.test_gates.TestSelftest.test_selftest_fails_when_the_date_checks_compare_the_raw_string tests.test_gates.TestSelftest.test_selftest_fails_when_a_zero_count_names_the_unknown
  The zero-count row: a _names_unknown that ignored the zero ... ok

  ----------------------------------------------------------------------
  Ran 2 tests in 0.859s

  OK
  ```
- Result: PASS

### 5. Root and payload copies are identical, and detector E is clean

Source: brief Success criterion 3, and the Accept line of the "Payload
mirror and manifest" work item.

- Check: `cmp`, `shasum`, the manifest entry, a count of stray patch
  files, and `gates.check_scaffold_sync`
- Evidence:
  ```
  $ cmp gates_selftest.py factory/templates/tools/factory/gates_selftest.py && echo "cmp: identical"
  cmp: identical
  $ shasum -a 256 gates_selftest.py factory/templates/tools/factory/gates_selftest.py
  a99ad94afaa70636d10af357b55f7bf53bc4d4709edbe31578ce845451c488e0  gates_selftest.py
  a99ad94afaa70636d10af357b55f7bf53bc4d4709edbe31578ce845451c488e0  factory/templates/tools/factory/gates_selftest.py
  $ grep -n '"templates/tools/factory/gates_selftest.py"' factory/manifest.json
  45:    "templates/tools/factory/gates_selftest.py": "a99ad94afaa70636d10af357b55f7bf53bc4d4709edbe31578ce845451c488e0",
  check_scaffold_sync (E) -> []
  stray .orig/.rej files: 0
  ```
- Result: PASS

### 6. The shared fixture builders' callers stay green, and scope held

Source: the Accept line of the "Shared builders stay green" work item,
and the brief's Out list (no `gates.py` change, no
`.claude-plugin/plugin.json` change). The branch adds 32 lines to
`tests/test_gates.py` and deletes none, and does not touch
`tests/test_knowledge_plane.py`.

- Check: the two modules run together; `git diff` over the files that
  must not change
- Evidence:
  ```
  $ python3 -m unittest tests.test_gates tests.test_knowledge_plane
  Ran 364 tests in 5.064s
  OK
  $ git diff --stat origin/main...HEAD -- gates.py .claude-plugin/ tests/test_knowledge_plane.py
  (empty)
  $ git diff --numstat origin/main...HEAD -- tests/
  32	0	tests/test_gates.py
  ```
- Result: PASS

### 7. The backlog claim is in place

Source: the Accept line of the "Backlog claim" work item.

- Check: grep for the claim on `docs/backlog.md`
- Evidence:
  ```
  $ grep -n 'claimed: maintenance:the-selftest-cannot-see-a-dodge' docs/backlog.md | grep -o '^[0-9]*:\|(claimed: [^)]*)$'
  124:
  (claimed: maintenance:the-selftest-cannot-see-a-dodge)
  ```
- Result: PASS

### 8. The whole-repo battery passes

Source: brief Success criterion 4, and the Accept line of the
"Whole-repo checks" work item.

- Check: the four CI commands on HEAD `aa0d38d`, tree clean
- Evidence:
  ```
  $ python3 run_tests.py
  tests: 3325 tests across 106 modules in 17.0s on 8 workers, 0 problem(s)
  $ python3 lint.py
  lint: 0 problem(s) across 34 skills
  $ python3 kb.py drift
  drift: 0 problem(s)
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS

## Failures

none.

## Not verified

- **A real consumer repo after its next payload update.** Criterion 3
  stamps a fresh temp repo from this branch, which is the same payload
  path, but no existing stamped repo was updated with `factory_init.py
  update`. That waits for the owed `chore(release)` PR (ADR-0095).
- **The seed's combined reversion** (a raw compare inside
  `_grandfathered`, blinding O, M and H's dates together) was not re-run
  as a file edit here. Implement's Notes quote it failing the three date
  rows, and criterion 4's first test pins the same shape by patching
  `_grandfathered` and asserting exactly those three labels.
