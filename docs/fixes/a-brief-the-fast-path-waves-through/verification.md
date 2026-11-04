---
stage: verify
run: maintenance:a-brief-the-fast-path-waves-through
date: 2026-11-03
assumptions: []
---

# Verification: a brief the fast path waves through

## Summary

11 criteria (the brief's Success criteria and the work items' Accept lines, overlaps merged): 11 PASS, 0 FAIL, 0 NOT RUN, 0 unknown. The regression test is red on the pre-fix classifier (`FAILED (failures=9)`) and green on the fix (`Ran 24 tests ... OK`). `python3 run_tests.py`, `lint.py`, `kb.py drift`, `gates.py` and `gates.py --selftest` all pass on this tree. Qualification, disclosed rather than hidden: the first full-suite runs during Implement failed one wall-clock test each under load (recorded in `defect.md` Notes); this Verify's run happened at load average 12.6 and passed clean, so the clean result is a real pass but timing-sensitive. Items not examined are listed under "Not verified".

## Criteria & evidence

### A diff touching only an `autorun-brief.md` prints `fast-path: review (<path>)`, exit 1 (was `low-risk`, exit 0)

- Check: fresh temp git repo (`main` holds `docs/features/x/autorun-brief.md`, `docs/fixes/y/autorun-brief.md`, `docs/features/x/breakdown.md`, and near-miss names); one branch per edit; the worktree's `python3 fast_path.py main <branch>`.
- Evidence:
  ```
  edit docs/features/x/autorun-brief.md
  fast-path: review (docs/features/x/autorun-brief.md)
  exit 1
  edit docs/fixes/y/autorun-brief.md
  fast-path: review (docs/fixes/y/autorun-brief.md)
  exit 1
  ```
  Before (pre-fix classifier, from the failing tests): `(0, 'fast-path: low-risk\n') != (1, 'fast-path: review (docs/fixes/y/autorun-brief.md)\n')`.
- Result: PASS

### Other run-artifact files stay `low-risk` (neighbour and near-miss names)

- Check: same temp repo; edit a neighbour and two near-miss basenames.
- Evidence:
  ```
  edit docs/features/x/breakdown.md
  fast-path: low-risk
  exit 0
  edit docs/features/z/my-autorun-brief.md
  fast-path: low-risk
  exit 0
  edit docs/features/z/autorun-brief-notes.md
  fast-path: low-risk
  exit 0
  ```
  Matcher in `fast_path.py`: `GATE_NAMES = ("prd.md", "architecture.md", "autorun-brief.md")`, an exact-basename match (`path.rsplit("/", 1)[-1] in GATE_NAMES`), so no other artifact basename is gated.
- Result: PASS

### A rename of a brief into or out of the run directory routes to review

- Check: same temp repo, `git mv` commits.
- Evidence:
  ```
  rename brief y->q
  fast-path: review (docs/fixes/q/autorun-brief.md)
  exit 1
  rename brief out
  fast-path: review (docs/fixes/y/autorun-brief.md)
  exit 1
  rename into brief
  fast-path: review (docs/features/z/autorun-brief.md)
  exit 1
  ```
- Result: PASS

### Failing tests first: red before the fix, green after (the regression test)

- Check: copied the tree to a temp dir, replaced `fast_path.py` with `git show d5adfab^:fast_path.py`, ran `python3 -m unittest tests.test_fast_path` (the tests are the fix commit's); then ran the same on the fix.
- Evidence:
  ```
  pre-fix:
  FAIL: test_a_brief_alone_names_itself ... (path='docs/features/x/autorun-brief.md')
  FAIL: test_a_brief_alone_names_itself ... (path='docs/fixes/y/autorun-brief.md')
  FAIL: test_an_autorun_brief_at_any_depth_is_review ... (path='docs/features/x/autorun-brief.md')
  FAIL: test_an_autorun_brief_at_any_depth_is_review ... (path='docs/fixes/y/autorun-brief.md')
  FAIL: test_the_brief_glob_is_in_the_classifiers_list
  FAIL: test_the_profile_gate_paths_equal_the_classifiers_list
  FAIL: test_a_brief_edit_in_real_git_is_review
  FAIL: test_a_brief_renamed_into_a_run_directory_is_review
  FAIL: test_a_brief_renamed_out_of_its_run_directory_is_review
  AssertionError: Tuples differ: (0, 'fast-path: low-risk\n') != (1, 'fast-path: review (docs/features/x/autorun-brief.md)\n')
  Ran 24 tests in 1.048s
  FAILED (failures=9)

  fix:
  Ran 24 tests in 1.124s

  OK
  ```
  (`defect.md` Notes say `failures=8` for the Implement-time red run; this run counts 9 failing items, since subTest cases count separately and the near-miss count differs. Both are red; the 9 is what was observed here.)
- Result: PASS

### The profile's `gate_paths` equals `fast_path.gate_globs()` (pin test passes)

- Check: `TestProfilePin` (included in the green run above) parses `gate_paths:` in `.claude/implement-queue.md` and compares to `gate_globs()`; also printed the list.
- Evidence:
  ```
  ['**/prd.md', '**/architecture.md', '**/autorun-brief.md', '.claude-plugin/plugin.json', 'docs/pipeline-protocol.md', 'docs/standards.json']
  True True        # glob in gate_globs(); glob present in implement-queue.md
  .claude/implement-queue.md:10:  - "**/autorun-brief.md"
  ```
  Pre-fix the pin test failed with `Lists differ` (above), so it does bind the two lists.
- Result: PASS

### ADR-0122 provisional; README row and ADR-0121 status line point at each other

- Check: grep.
- Evidence:
  ```
  docs/adr/0122-the-fast-path-gates-the-autorun-brief.md:  - Status: provisional
  docs/adr/README.md:144: | 0121 | The fast path gates the docs agents obey | amended by ADR-0122 (the run directories' survey: the autorun brief is a gate path; provisional) |
  docs/adr/README.md:145: | 0122 | The fast path gates the autorun brief | provisional |
  docs/adr/0121-the-fast-path-gates-the-docs-agents-obey.md:3:- Status: amended by ADR-0122 (the run directories' survey: the autorun brief is a gate path; provisional)
  ```
  ADR-0122 itself links back to ADR-0121 ("Amends ADR-0121").
- Result: PASS

### Backlog line 143 claimed, no other line changes

- Check: `sed -n 143p docs/backlog.md`; `git diff d5adfab^ d5adfab -- docs/backlog.md`.
- Evidence:
  ```
  - Add `**/autorun-brief.md` to the fast-path gate list and the queue profile's `gate_paths`, and decide with the Owner whether other `docs/features/**` files are instruction sources (from: feature:faster-sdlc) (claimed: maintenance:a-brief-the-fast-path-waves-through)
  diff: exactly one `-` line and one `+` line (line 143).
  ```
- Result: PASS

### `python3 run_tests.py` passes

- Check: ran on this tree.
- Evidence:
  ```
  tests: 3978 tests across 126 modules in 30.7s on 8 workers, 0 problem(s)
   14:34:04  up 19 days 17:34,  4 users,  load average: 12.64, 15.97, 16.58
  ```
  Also `python3 -m unittest tests.test_fast_path` alone: `Ran 24 tests in 2.522s` / `OK`.
- Result: PASS

### `python3 lint.py` passes

- Evidence:
  ```
  lint: 0 problem(s) across 35 skills
  ```
- Result: PASS

### `python3 kb.py drift` passes

- Evidence:
  ```
  drift: 0 problem(s)
  ```
- Result: PASS

### `python3 gates.py && python3 gates.py --selftest` pass

- Evidence:
  ```
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS

## Failures

none.

## Not verified

- Mirrors: `fast_path.py` and `implement-queue.md` absent from `factory_init.MIRRORS` was taken from Capture/Implement (`grep -c` 0), not re-run here; `git status` showed a clean tree after the gates, so nothing mirrored drifted.
- The `implement-queue` skill's GitHub-side `gate_paths` matcher: out of scope by the brief (backlog line 144's seed); not checked.
- Operate-stage and merge-train behaviour on a real PR: not exercised (prepare-and-stop run; no merge).
- Load: the machine was loaded (load average about 12 to 16) during this run; the suite passed regardless, so no load-failure label applies, but a re-run under different load was not done.
