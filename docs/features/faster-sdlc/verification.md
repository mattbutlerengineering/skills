---
stage: verify
run: feature:faster-sdlc
date: 2026-11-02
assumptions:
  - "No prd.md exists (the run entered at Decompose by the Owner's choice, recorded in breakdown.md). The criteria list is therefore the 11 breakdown rows' `Accept:` lines, as the skill's step 3 allows, plus the brief. No PRD criterion is invented or backfilled."
  - "Recommended default taken (checked-on-decision rows): the CI before/after record and the Merge-wait record are checked in breakdown.md on explicit Owner decisions over a missed numeric bar. They are judged here against their Accept lines as written, and reported as FAIL on the original bar with the Owner's decision named. They are never reported as passes of the original bar."
  - "Recommended default taken (Owner steps): an Accept line's Owner step that is not repo state (memory note, session permission, trigger) is recorded as an Owner step with the evidence the Notes give, labelled NOT RUN here, and never as a pass."
  - "Recommended default taken (timing bars): two timing bars (under 8s for tests/test_conductor_merge.py; under 25s for `make check`) cannot be measured on this machine today (load average 191 to 207 during the run). They are labelled NOT RUN, not judged from a loaded number in either direction."
---

# Verification: a faster verify loop, no version-bump treadmill, no merge-queue wait

## Summary

**11 criteria (the 11 breakdown rows): 4 PASS, 2 FAIL on the original bar,
5 PASS on repo state with a NOT RUN part.** Nothing is an unqualified
pass over the unknowns below.

- **2 FAIL on the original bar, checked on an Owner decision**: CI
  before/after record (whole-run median rose 62.0s to 79.5s; the `check`
  job's median fell 48.0s to 23.0s, which is what the Owner checked it
  on) and Merge-wait record (p90 7.5h, bar was under 4h; p90 fell from
  13.5h, which is what the Owner checked it on).
- **5 rows with a NOT RUN part**: Shared conductor-merge fixture (the
  under-8s timing, plus a test count that moved from 50 after #916's
  facet split), make check calls the runner (the under-25s timing),
  Rewrite the version rule (the memory-note Owner step), Queue profile
  (the session-permission Owner step) and Merge-train routine (the
  trigger Owner step). Their repo-state criteria all pass.
- **5 NOT RUN items in all**: two timing bars, and three Owner steps that
  are not repo state: the memory note, the session permission, and the
  `factory-merge-train` trigger (outside the repo, so its existence is
  unknown to this run).

Real commands run on this branch (HEAD `d4d5c5b`, origin/main `36bbab1`):
`run_tests.py` 3965 tests, 0 problems; `lint.py`, `kb.py drift`,
`gates.py`, `gates.py --selftest` all clean; the runner's count equals
`unittest discover`'s (3965 = 3965). The branch's own diff against
origin/main is `breakdown.md` alone, so the implementation under
verification is what main already carries (PRs #913, #914 and later).

## Criteria & evidence

### 1. Shared conductor-merge fixture (#902)

- Check: read the `TurnCase` fixture and its isolation pins; ran the
  module and its facet siblings; timed the module.
- Evidence:
  ```
  $ grep -n "class TestFixtureIsolation" tests/test_conductor_merge.py
  416:class TestFixtureIsolation(TurnCase):
  $ python3 -m unittest tests.test_conductor_merge tests.test_run_tests tests.test_fast_path tests.test_gates.TestLockstep
  Ran 104 tests in 20.124s
  OK
  $ python3 -m unittest tests.test_conductor_merge_stalls   -> Ran 10 tests
  $ python3 -m unittest tests.test_conductor_merge_reservations -> Ran 4 tests
  $ uptime
  load average: 191.69, 170.56, 112.17
  $ time python3 -m unittest tests.test_conductor_merge
  Ran 43 tests in 20.019s
  OK
  real 0m20.155s   user 0m4.737s   sys 0m6.062s
  ```
  Notes (2026-10-15, #916) record the idle number for this module as
  6.1s, from the quiet-machine read. This run did not reproduce it: the
  machine was at load 191.
- Result: PASS on repo state (per-subclass fixture with per-test copies,
  `TestFixtureIsolation` pins, module and siblings green). **NOT RUN**: the
  under-8s bar, which cannot be timed at load 191 (20.0s wall on 10.8s of
  CPU). The Owner moved the bar to #916 (Notes, 2026-10-15). Also, the
  "exactly 50 tests" line is superseded: the module now holds 43 tests
  after #916's facet split moved 14 to two sibling modules (57 in all),
  so the count in the Accept line no longer describes the tree.

### 2. Parallel test runner (#903)

- Check: ran the runner and the serial discover on this tree and
  compared counts; read the runner's tests for each Accept clause.
- Evidence:
  ```
  $ python3 run_tests.py
  tests: 3965 tests across 126 modules in 73.8s on 8 workers, 0 problem(s)
  exit=0
  $ python3 -m unittest discover tests
  Ran 3965 tests in 212.246s
  OK
  $ python3 run_tests.py -h
  usage: python3 run_tests.py [-j N] [--record]
    -j N      workers in flight at once (default: os.cpu_count())
  $ grep -n "def test" tests/test_run_tests.py   (excerpt)
  88:    def test_longest_first_from_the_timings(self):
  95:    def test_no_timings_means_alphabetical(self):
  122:    def test_unreadable_is_empty(self):
  134:    def test_each_module_runs_as_its_own_unittest_child_in_the_root(self):
  143:    def test_a_clean_run_prints_the_total_test_count_and_exits_0(self):
  151:    def test_a_planted_failure_exits_1_and_names_the_module_then_its_output(
  177:    def test_dash_j_overrides_the_cpu_count(self):
  182:    def test_the_cpu_count_is_the_default_worker_count(self):
  $ ls tests/timings.json run_tests.py
  run_tests.py
  tests/timings.json
  ```
- Result: PASS. The planted-failure behaviour is pinned by a unit test
  through a fake spawn port; it was not re-planted against the real tree
  in this run.

### 3. make check calls the runner (#904)

- Check: read the Makefile and the payload respelling; ran `make check`
  and the pinning tests.
- Evidence:
  ```
  $ grep -n "run_tests" Makefile
  46:	python3 run_tests.py
  $ grep -n "run_tests" factory_init.py
  86:    serial: the root's parallel runner (run_tests.py) is root-only, so
  91:    command = command.replace("python3 run_tests.py",
  92:                              "python3 -m unittest discover tests")
  93:    return command.replace("unittest discover tests",
  94:                           "unittest discover -q tests")
  $ grep -n "CANONICAL_CHECK" tests/test_gates.py   (TestLockstep)
  3314:    CANONICAL_CHECK = ["python3 gates.py",
  3316:                       "python3 run_tests.py"]
  $ grep -n "run_tests" CLAUDE.md AGENTS.md README.md
  CLAUDE.md:10:- `python3 run_tests.py` — the full suite, one `python3 -m unittest
  AGENTS.md:10:- `python3 run_tests.py` — the full suite, one `python3 -m unittest
  README.md:174:- `python3 run_tests.py` — the full offline suite, one process per test module in parallel: ...
  $ time make check
  gates: 0 problem(s)
  selftest: ok
  tests: 3965 tests across 126 modules in 68.0s on 8 workers, 0 problem(s)
  real 1m11.460s   (load average 207)
  ```
  `tests.test_gates.TestLockstep` and `tests.test_factory_init` are in the
  3965-test green run above. Neither a second `factory_init.py
  update-manifest` run nor the "three consecutive runs" was repeated here;
  Notes (2026-10-14) record them. This run has two green parallel runs
  (73.8s and 68.0s inside `make check`).
- Result: PASS on repo state (runner behind `make check`, payload
  respelling, lockstep and respelling pins, docs name it). **NOT RUN**:
  the under-25s bar; 71.5s at load 207 says nothing about an idle
  machine. The Owner moved it to #916 (Notes, 2026-10-15).

### 4. CI before/after record (#905)

- Check: read the Notes entries; the numbers are the Notes' own and were
  not re-read from `gh run list` in this run.
- Evidence (quoted from breakdown.md Notes):
  ```
  2026-10-15: last 10 before, median 62.0s; first 10 after, median 79.5s
  (whole-run, created to updated). The `check` job's median fell from
  48.0s to 23.0s. The gap: the runner halved the job, and the whole-run
  median is a runner-queue number this repo does not control.
  2026-10-24: checked on the Owner's decision ("Check it on job
  evidence"). The Accept line stands as written and the 2026-10-15 gap
  entry stays the record of the miss.
  ```
- Result: **FAIL on the Accept line as written** (the after-median, 79.5s, is
  not lower than 62.0s). Checked on the Owner's decision on the job-level
  median (48.0s to 23.0s). Flagged for human review.

### 5. Version-rule ADR (#906)

- Check: read ADR-0095's head and body for each Accept clause; read the
  index.
- Evidence:
  ```
  $ head -12 docs/adr/0095-*.md
  # The plugin version moves only in a release PR or at a Conductor merge
  - Status: accepted (Owner, 2026-10-15)
  - Date: 2026-10-14
  ... It supersedes no ADR: the rule it replaces lives only in CLAUDE.md and AGENTS.md ...
  $ grep -n "bump_version\|Rejected alternative" docs/adr/0095-*.md
  28:step 3: `conductor_merge.bump_version` sets the branch's version to
  45:3. **A Conductor merge bumps at step 3**, as `bump_version` already
  49:## Rejected alternative
  $ grep -n "0095" docs/adr/README.md
  118:| 0095 (index link elided) | The plugin version moves only in a release PR or at a Conductor merge | accepted (Owner, 2026-10-15) |
  $ python3 gates.py
  gates: 0 problem(s)
  ```
  The ADR's status is `accepted (Owner, 2026-10-15)`, past the row's
  "Proposed" (the grammar has no `Proposed`; Notes 2026-10-14 and the
  Owner's acceptance 2026-10-15). The "five merge-and-re-bump commits"
  clause was not re-counted against the git history of
  `feat/kb-weknora-lessons` in this run.
- Result: PASS

### 6. Rewrite the version rule (#907)

- Check: read the bullet in both files; grep for the old wording; run
  lint and gates.
- Evidence:
  ```
  $ sed -n 116,121p CLAUDE.md
  (bullet at 118-121: "...never touch the version** (ADR-0095). A wave's `chore(release)` PR bumps it once after ... (`conductor_merge.bump_version`). Installed plugin caches refresh only when the version moves ...")
  $ grep -n "ADR-0095" AGENTS.md
  118:  version** (ADR-0095). A wave's `chore(release)` PR bumps it once after
  $ git grep -n "version with any" -- . ':!docs/adr' ':!docs/features'
  (no output)
  $ python3 lint.py
  lint: 0 problem(s) across 35 skills
  $ python3 gates.py
  gates: 0 problem(s)
  ```
  The only other `git grep` hits are inside `docs/adr/` and the dated
  run artifacts `docs/features/faster-sdlc/breakdown.md`, which the
  Accept line excludes.
- Result: PASS on repo state. **Owner step, NOT RUN here**: the memory
  note `parallel-pr-wave-single-version-bump`. Notes (2026-10-14) say it
  is done; the note is outside the repo and this run did not read it.

### 7. Auto-merge ADR for this repo (#908)

- Check: read ADR-0096 for each clause.
- Evidence:
  ```
  $ head -3 docs/adr/0096-*.md
  # This repo opts in to implement-queue auto-merge, with a docs fast path
  - Status: accepted (Owner, 2026-10-15)
  $ grep -n "0.64\|factory/templates\|The fast-path rule\|cross-pr-merge-hazards\|update-branch" docs/adr/0096-*.md
  20:0.64h, p75 2.0h, p90 13.5h. 24 PRs (16%) were open longer than 4h, and
  39:   `factory/templates/**`, `.github/**` and `.claude-plugin/plugin.json`.
  42:3. **The fast-path rule**: every changed path is under `docs/` and none
  52:   together (`docs/kb/cross-pr-merge-hazards.md`: number collisions, a
  54:   merge the train runs `update-branch` on that PR and waits for a
  $ ls docs/adr | grep 009[5-7]
  0095-...  0096-...  0097-...
  ```
  `gates.py` is clean (above). The Owner gate (acceptance) is recorded in
  the ADR and in Notes 2026-10-15.
- Result: PASS

### 8. Fast-path classifier (#909)

- Check: ran the CLI on real refs for each exit code; ran the test
  module.
- Evidence:
  ```
  $ python3 fast_path.py origin/main HEAD
  fast-path: low-risk                      exit=0   (diff is breakdown.md/verification-run docs only)
  $ python3 fast_path.py origin/main origin/main
  fast-path: review (empty diff)           exit=1
  $ python3 fast_path.py 3d2b5b7 36bbab1
  fast-path: review (skills/implement-queue/references/reviewer-contract.md)   exit=1
  $ python3 fast_path.py origin/main~3 origin/main
  fast-path: review (.claude-plugin/plugin.json)   exit=1
  $ python3 fast_path.py origin/main nosuchref
  fast-path: git diff --name-only origin/main...nosuchref failed: 'git <command> [<revision>...] -- [<file>...]'   exit=2
  $ python3 -m unittest -v tests.test_fast_path
  ... test_a_docs_prefix_is_a_directory_not_a_substring ... ok
  ... test_an_empty_diff_is_review ... ok
  ... test_every_gate_path_under_docs_is_review ... ok
  ... test_a_ref_that_does_not_resolve_is_the_same_case ... ok
  Ran 11 tests in 0.001s
  OK
  ```
  The Notes count 14 cases; this tree runs 11 in `tests.test_fast_path`.
  I did not reconcile the difference (the row asks for the exact strings,
  and the quoted CLI output shows each). The `docs/adr/x.md` and
  `docs/features/a/prd.md` review cases are covered by
  `test_every_gate_path_under_docs_is_review` by name; I did not read
  that test's body to confirm those two paths.
- Result: PASS

### 9. Queue profile for this repo (#910)

- Check: read the profile; the Phase 0 dry run is in Notes.
- Evidence:
  ```
  $ sed -n 1,13p .claude/implement-queue.md
  merge: auto
  required_check: check
  hold_labels: [needs-review]
  gate_paths:
    - "docs/adr/**"  - "docs/design/**"  - "**/prd.md"  - "**/architecture.md"
    - "factory/templates/**"  - ".github/**"  - ".claude-plugin/plugin.json"
  $ grep -n -A2 "## fast-path" .claude/implement-queue.md
  ## fast-path
      python3 fast_path.py origin/main HEAD
  ```
  Notes 2026-10-15 quote the dry run: `#914 human gate: gate path
  docs/adr/0095-...md`. That run was not repeated here.
- Result: PASS on repo state, with the dry run taken from Notes, not
  re-run. **Owner step, NOT RUN**: the session permission for `gh pr merge
  <N> --auto --squash --delete-branch`; Notes call it "still open".

### 10. Merge-train routine (#911)

- Check: read the routine, its marker test and its listings.
- Evidence:
  ```
  $ ls docs/factory
  costs.jsonl  doc-gardener-routine.md  hourly-improvement-routine.md  improvement-routine.md  merge-train-routine.md  queue-groomer-routine.md  retro-reflect-routine.md  routine-markers.md
  $ grep -n "Phase 0\|Phase 3\|claims no issue\|factory-merge-train-journal" docs/factory/merge-train-routine.md
  4: open pull requests: Phase 0 (pre-flight) and Phase 3 (merge train) of
  8: performs. It claims no issue and implements nothing: ...
  30: `<!-- factory-merge-train-journal -->` and the state line's
  $ grep -n "merge-train" tests/test_routine_markers.py
  25:    "merge-train-routine.md": _WEEKLY_LOOKUP,
  36:                         "merge-train-routine.md",
  $ grep -n "merge-train" CLAUDE.md AGENTS.md
  CLAUDE.md:185:- `docs/factory/merge-train-routine.md` — the scheduled
  AGENTS.md:185:- `docs/factory/merge-train-routine.md` — the scheduled
  ```
  `docs/factory/` has no README; the listing the Accept line means is
  the CLAUDE.md and AGENTS.md routine-protocol list (line 185).
- Result: PASS on repo state. **Owner step, NOT RUN here**: the trigger.
  CLAUDE.md line 188 and Notes 2026-10-15 say `factory-merge-train` was
  created; the trigger is outside the repo and was not queried.

### 11. Merge-wait record (#912)

- Check: read the Notes entries (the numbers come from `gh pr list`; they
  were not re-queried in this run).
- Evidence (quoted from breakdown.md Notes, 2026-11-02):
  ```
  Window: 104 PRs, merged 2026-10-16 00:39 to 2026-10-31 17:37 UTC.
  median 0.56h (0.64h), p90 7.5h (13.5h), 17 PRs (16%) open longer than
  4h holding 79% of all open-hours (96%). ... it misses the 4h bar.
  2026-11-02: checked on the Owner's decision ("Accept on partial
  evidence"). The Accept line stands as written and the entry above stays
  the record of the miss.
  ```
- Result: **FAIL on the Accept line as written** (p90 7.5h is not under
  4h). Checked on the Owner's decision on the movement against baseline
  (p90 13.5h to 7.5h). The long waits behind the tail (#1131, #1070,
  #1040, #1072) are unattributed. Flagged for human review.

## Repo-wide commands (run from the worktree)

```
$ python3 run_tests.py
tests: 3965 tests across 126 modules in 73.8s on 8 workers, 0 problem(s)
exit=0
$ python3 lint.py
lint: 0 problem(s) across 35 skills
$ python3 kb.py drift
drift: 0 problem(s)
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
$ python3 -m unittest discover tests
Ran 3965 tests in 212.246s
OK
```

## Failures

- **CI before/after record** and **Merge-wait record** miss their Accept
  lines as written; both are checked on recorded Owner decisions. No
  route back to Implement is proposed: the Owner chose to accept the
  evidence. The routing question for a reviewer is whether those two
  checks should stay checked.
- No failing command, test or gate.

## Not verified

- The under-8s (`test_conductor_merge`) and under-25s (`make check`)
  timing bars: the machine's load average was 191 to 207, so no idle
  timing could be taken. The Owner moved both to #916; Notes 2026-10-15
  record 6.1s and 14.2s on a quiet machine, which this run did not
  reproduce.
- The three Owner steps: memory note, session permission, trigger.
- `gh run list` and `gh pr list` numbers for rows 4 and 11: taken from
  Notes, not re-queried.
- The Phase 0 dry run (row 9): taken from Notes, not re-run.
- The ADR-0095 churn count (five commits on `feat/kb-weknora-lessons`)
  and `factory_init.py update-manifest` byte-identity: not re-checked.
- The planted-failure and `-j` behaviours of `run_tests.py` are pinned by
  unit tests with a fake port and were not exercised against the real
  tree.
- Lesson for the next PRD: the milestones' goals (faster CI, lower merge
  wait) each rest on one measurement window, with no control for load or
  PR volume, and the two bars written against the whole run missed while
  the part the repo controls (the `check` job) moved. Write the bar
  against the quantity the repo controls.
