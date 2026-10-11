---
stage: verify
run: maintenance:one-fence-rule
date: 2026-10-10
assumptions:
  - "Criteria source: there is no prd.md (maintenance run, re-entry: architect). The list is defect.md's three success criteria (S1-S3) plus every breakdown.md acceptance clause they do not already cover (B1-B3)."
  - "Red-before evidence was produced in a detached worktree at 008dd34 (the run's merge base with main) with this branch's test files copied in. The run's own code was not present there."
  - "trigger_eval.py and charter_replay.py were not run. They are real model runs, available on demand only, and no criterion names them."
---

# Verification: one fence rule

Verified at `b5c3974`: five commits on top of `main` at `008dd34`.

## Summary

**6 criteria: 6 PASS, 0 FAIL.** One definition of the fence rule now
exists, in `knowledge_plane.py`. Both of defect.md's repros print no
problem. The three new regression cases fail on the old code and pass on
the new. No existing test was edited.

## Criteria & evidence

### S1: both repros from defect.md produce no problem

- Check: the repros were re-run through their entry points
  (`gates.check_blueprint_drift` on the four-backtick `architecture.md`,
  and `validator._unquoted` on the four-backtick body). Each was then
  pinned as a regression test and run against both the old and the new
  code.
- Evidence (new tree):
  ```
  D: []
  _unquoted: ['after'] unfenced: ['after']
  ```
  Old code (`008dd34`) with the new tests:
  ```
  FAIL: test_a_tilde_line_inside_a_backtick_fence_is_content (tests.test_gates.TestArchitectureDrift...)
  AssertionError: Lists differ: ['D: docs/features/software-factory/archit[75 chars]le)'] != []
  FAIL: test_a_quoted_fence_inside_a_longer_fence_is_content (tests.test_gates.TestArchitectureDrift...)
  AssertionError: Lists differ: ['D: docs/features/software-factory/archit[75 chars]le)'] != []
  FAIL: test_a_quoted_fence_inside_a_longer_fence_is_content (tests.test_validator.TestRunLifecycle...)
  AssertionError: Lists differ: ['V: none of the work orders this PR cites[111 chars]ses'] != []
  Ran 3 tests in 0.006s
  FAILED (failures=3)
  ```
  New code:
  ```
  test_a_tilde_line_inside_a_backtick_fence_is_content (tests.test_gates.TestArchitectureDrift...) ... ok
  test_a_quoted_fence_inside_a_longer_fence_is_content (tests.test_gates.TestArchitectureDrift...) ... ok
  one-fence-rule's repro: a four-backtick block quoting a markdown ... ok
  ```
- Result: PASS

### S2: one definition of the fence rule (breakdown closure grep)

- Check: `grep -nE '^(FENCE_OPEN|FENCE_CLOSE|ARCH_FENCE|FENCES) *=' *.py`,
  followed by a grep for any surviving private walker or retired constant.
- Evidence:
  ```
  knowledge_plane.py:89:FENCE_OPEN = re.compile(r"^\s*(?P<marker>`{3,}|~{3,})(?P<info>.*)$")
  knowledge_plane.py:90:FENCE_CLOSE = re.compile(r"^\s*(?P<marker>`{3,}|~{3,})[ \t]*$")
  $ grep -nE '_fence_open|_fence_closes|_unfenced|ARCH_FENCE\b|FENCES\b' *.py
  (end)
  ```
- Result: PASS

### S3: existing tests pass unchanged, and every check is green

- Check: confirm that no test was removed or edited, then run the full
  verify set.
- Evidence: the only `-` lines in `git diff 008dd34..HEAD -- tests/` are
  the import list in `tests/test_knowledge_plane.py`, which was widened
  to import the new names:
  ```
  20	0	tests/test_gates.py
  45	2	tests/test_knowledge_plane.py
  16	0	tests/test_validator.py
  -                             mirror_map, parse_run, repo_root, row_done,
  -                             row_work_order, run_dirs, sanitize)
  ```
  ```
  $ python3 -m unittest tests.test_gates.TestEvidenceHonesty tests.test_gates.TestCaptureCompleteness \
      tests.test_gates.TestNeedsClarification tests.test_gates.TestPrdCoverage \
      tests.test_gates.TestArchitectureDrift tests.test_validator.TestRunLifecycle
  Ran 109 tests in 0.131s
  OK
  $ python3 -m unittest discover tests
  Ran 2106 tests in 28.624s
  OK
  lint: 0 problem(s) across 31 skills
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS

### B1: TestFences pins the rule at its new interface (item 1)

- Check: run `tests.test_knowledge_plane.TestFences` verbosely. It covers
  `~~~` inside a backtick fence, three backticks inside four, a longer
  closer, the backtick-info rule, leading whitespace, an unterminated
  fence, and 1-based line numbers. Before the move it failed with an
  ImportError, because the names did not exist yet.
- Evidence:
  ```
  test_a_longer_closer_closes ... ok
  test_backtick_info_with_a_backtick_does_not_open ... ok
  test_leading_whitespace_is_allowed ... ok
  test_line_numbers_are_one_based ... ok
  test_three_backticks_inside_four_is_content ... ok
  test_tilde_inside_backtick_fence_is_content ... ok
  test_unterminated_fence_swallows_the_rest ... ok
  ```
- Result: PASS

### B2: payload twins synced and manifest regenerated (items 1-3)

- Check: `cmp` each edited root tool against its
  `factory/templates/tools/factory/` twin. Detector E, which compares
  the manifest against the payload, runs inside `gates.py` (S3).
- Evidence:
  ```
  knowledge_plane.py: twin identical
  gates.py: twin identical
  validator.py: twin identical
  factory-init: 0 problem(s)
  ```
- Result: PASS

### B3: commits read like the breakdown

- Check: `git log --oneline 008dd34..HEAD`.
- Evidence:
  ```
  b5c3974 docs(fixes): check off one-fence-rule's closure item
  dda7cb6 fix(validator): the skip gate tracks fences through the one fence rule
  734340b fix(gates): detector D tracks fences through the one fence rule
  e72f059 refactor: move the strict fence walker into knowledge_plane
  7da232d docs(fixes): capture and decompose the one-fence-rule run
  ```
- Result: PASS

## Failures

None.

## Not verified

- The validator's accepted behaviour change (architecture.md, *Decisions*:
  a ```` ``` ```` line whose info string contains a backtick no longer
  opens a fence in `_unquoted`) has no validator-level test. It is pinned
  only at the shared rule, by
  `TestFences.test_backtick_info_with_a_backtick_does_not_open`.
- Live CI on a PR event (detector B) has not run yet; it runs when the
  PR opens.
- `trigger_eval.py` and `charter_replay.py` were not run. They are paid,
  on-demand model runs that no criterion names.
