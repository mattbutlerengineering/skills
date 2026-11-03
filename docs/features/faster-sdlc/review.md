---
stage: review
run: feature:faster-sdlc
date: 2026-11-02
assumptions:
  - "Scope: the run has no prd.md or architecture.md and no 'diff since the run began' on this branch (it adds only run artifacts), so the reviewed change set is the code the run's tracker rows shipped to main, identified from breakdown.md's Notes and `git log`, plus the rename-fix commit `9670deb` on this branch in the re-review. The Design pass checks against the accepted ADRs the run wrote (0095, 0096, 0097) and the cited ADR-0087/0088, since there is no architecture.md."
  - "Recommended default taken (draft-first): severities below are the reviewer's draft; the Owner arbitrates. The rename finding was ranked Critical because it let a gate-path change classify low-risk under an auto-merge rule; the skill's fix loop blocked Ship until it was fixed. It is now fixed (re-review, 2026-11-02)."
  - "Recommended default taken (no code edits): this stage edits no code. The Critical was routed to Implement (`9670deb`) and re-verified, and this re-review checks that fix."
  - "The Major was kept open until the Owner decided; they chose 'Fix now' (breakdown.md Notes 2026-11-02) and it is now fixed by 63e7732 (ADR-0121, provisional) and re-reviewed (second re-review, 2026-11-02). Severities of the two new Minors are the reviewer's draft; the Owner arbitrates, and a Major ranking would block Ship until they fix or defer it."
---

# Review: a faster verify loop, no version-bump treadmill, no merge-queue wait

## Scope

Soft gate: the predecessor `verification.md` exists (dated 2026-11-02,
HEAD `d4d5c5b`), so this review is not inverted.

Reviewed range, two parts:

1. **This branch**: `git diff origin/main...HEAD` (origin/main `36bbab1`)
   is `docs/features/faster-sdlc/breakdown.md` (4 lines) and
   `verification.md` (379 lines new), 2 files, run artifacts only.
2. **The shipped feature code**, already on main, from the Notes' PR refs:
   `91bb51b` (#913: `run_tests.py`, `tests/test_run_tests.py`,
   `tests/timings.json`, `Makefile`, the shared `TurnCase` fixture),
   `3eed60a` (#914: ADR-0095, ADR-0096, CLAUDE.md/AGENTS.md version rule),
   `3aef35e` (#915: `fast_path.py`, `tests/test_fast_path.py`,
   `.claude/implement-queue.md`, `docs/factory/merge-train-routine.md`,
   ADR-0097), `8cd1929` (#921: trigger record). `git log --since=2026-10-13
   --until=2026-10-17` over those paths lists exactly these, plus unrelated
   `08db1d1`/`dbb77cc`/`9b37349`, which I did not review.

Commands run here, in the worktree (load average 178 during the run):

- `python3 fast_path.py origin/main HEAD` -> `fast-path: low-risk`, exit 0.
- `python3 fast_path.py origin/main nosuchref` -> `fast-path: git diff --name-only origin/main...nosuchref failed: 'git <command> [<revision>...] -- [<file>...]'`, exit 2.
- `python3 -m unittest tests.test_fast_path` -> `Ran 11 tests ... OK`.
- `python3 -m unittest tests.test_conductor_merge` -> `Ran 43 tests in 19.390s`, OK; `..._stalls` 10 tests, `..._reservations` 4 tests.
- `python3 adr_status.py .` for the live-ADR list (0095, 0096 `accepted (Owner, 2026-10-15)`; 0097 `provisional`).
- Two reproductions in a throwaway repo under `/tmp/fpt` (finding 1) and a `run_tests.main` call against an empty root (finding 4).

Re-review commands (after the fix, `9670deb`; HEAD `21ae6be`):

- `git show 9670deb`, `git diff bd63999..HEAD --stat` (4 files:
  `breakdown.md`, `verification.md`, `fast_path.py`,
  `tests/test_fast_path.py`).
- `git show bd63999:fast_path.py` into a temp copy of the tree, then
  `python3 -m unittest tests.test_fast_path.TestRealGit` there: 3 tests,
  `failures=2` (quoted under finding 1). `python3 -m unittest
  tests.test_fast_path` on the worktree: `Ran 14 tests ... OK`.
- `python3 fast_path.py origin/main nosuchref` (exit 2, new string) and
  bare `python3 fast_path.py` (exit 2, new USAGE).
- A copy-detection repro in `/tmp/cp` (finding 1, "Copy detection").

Second re-review commands (after the instruction-docs fix, `63e7732`;
HEAD `15812bc`):

- `git show 63e7732` (6 files), `git diff c826be9..HEAD --stat` (8 files;
  the code is `fast_path.py`, `tests/test_fast_path.py`,
  `.claude/implement-queue.md`).
- A probe of `fast_path.is_gate_path`/`classify` over 13 paths
  (directory without slash, `.bak` suffixes, nested same-name, case,
  `./`-prefix) and `fast_path.gate_globs()`.
- `python3 -m unittest tests.test_fast_path` -> `Ran 17 tests ... OK`;
  two mutations of `.claude/implement-queue.md` in a `git archive` copy
  at `/tmp/pin`, each failing `TestProfilePin`.
- `python3 adr_status.py .` for ADR-0096 (`active`, "amended by") and
  ADR-0121.
- Reads of `assembler.yml`, `gate-digest.yml`, `conductor.py`,
  `conductor_close.py`, `cost_ledger.py` and `skills/autorun/SKILL.md`
  for the survey's exclusions and the `costs.jsonl` claim.

Not reviewed: the GitHub-side behavior of the `check` job and of
`gh pr view --json files` (no network read here); the memory note and the
`factory-merge-train` trigger (outside the repo).

## Findings

### Critical (FIXED in `9670deb`, re-reviewed): fast-path classifier read `git diff --name-only` with rename detection on, so a gate-path file moved into `docs/` was classified low-risk

- Scenario (original): `fast_path.changed_paths` ran `git diff --name-only
  <base>...<head>`. Git's default rename detection lists only the
  *destination* of a rename. Reproduced in `/tmp/fpt` (base commit has
  `.github/workflows/validator.yml` and `docs/adr/0001-x.md`; the PR branch
  `git mv`s them to `docs/validator.yml.txt` and `docs/old-0001.md`):
  ```
  $ git diff --name-only base...pr
  docs/old-0001.md
  docs/validator.yml.txt
  $ git diff --no-renames --name-only base...pr
  .github/workflows/validator.yml
  docs/adr/0001-x.md
  docs/old-0001.md
  docs/validator.yml.txt
  $ python3 fast_path.py base pr
  fast-path: low-risk
  exit=0
  ```
  So a PR that moved a file out of a gate path (`docs/adr/**`,
  `**/prd.md`, `.github/**`, `factory/templates/**`,
  `.claude-plugin/plugin.json`) into `docs/`, with similarity of 50% or
  more, was reported as touching only `docs/...`, and under `merge: auto`
  (ADR-0096 decision 3, ADR-0088) would need only a green `check` to merge
  with no human.
- Fix evidence (re-review of `git show 9670deb` and `git diff
  bd63999..HEAD`): `changed_paths` now runs `git diff --name-only
  --no-renames <base>...<head>` (`fast_path.py:63`), so a rename lists its
  source as a deletion and its destination as an addition and the gate
  rule sees both. The code diff is those two files only (`fast_path.py`,
  `tests/test_fast_path.py`); the rest of `bd63999..HEAD` is the run's
  artifacts.
  - *Three-dot diff:* `--no-renames` is a diff-option and `<base>...<head>`
    is the revision argument; the flag sits before the range, as git
    expects, and the fix is exercised end to end by the real-git tests
    below, which use the `base...HEAD` form through `main`.
  - *Copy detection:* `-C`/`--find-copies` is not on by default; no
    `diff.renames` is set in this host's git config (`git config -l`
    shows no `diff.*`). Copy detection also cannot hide a gate path: a
    copy leaves its source unchanged, so the source is not a changed
    path either way. Reproduced in `/tmp/cp` (`.github/w.yml` copied to
    `docs/w.txt` with one added line): `git diff --name-only base...HEAD`
    lists only `docs/w.txt` under default config, under
    `-c diff.renames=copies`, and with `--no-renames`, correctly, since
    the gate file was not touched. A user's `diff.renames=copies` config
    cannot reintroduce the hole: `--no-renames` overrides it.
  - *New tests:* `TestRealGit` (`tests/test_fast_path.py`) builds real temp
    repos through `git_repo.init` and runs `fast_path.main` with a git
    port bound to that repo: a gate file renamed into `docs/` must print
    `fast-path: review (.github/workflows/validator.yml)` exit 1; a
    non-docs `lint.py` renamed into `docs/lint.txt` must print
    `fast-path: review (lint.py)`; a rename inside `docs/` clear of gates
    stays `fast-path: low-risk`. Against the old code (a temp copy of the
    tree with `git show bd63999:fast_path.py` as `fast_path.py`):
    ```
    $ python3 -m unittest tests.test_fast_path.TestRealGit
    AssertionError: Tuples differ: (0, 'fast-path: low-risk\n') != (1, 'fast-path: review (.github/workflows/validator.yml)\n')
    Ran 3 tests in 1.536s
    FAILED (failures=2)
    ```
    So the two review cases fail on the old code, and the third (the
    low-risk control) passes on both, as it should. On the fixed tree:
    `python3 -m unittest tests.test_fast_path` -> `Ran 14 tests ... OK`.
  - *Exit-2 strings:* the three problem-string tests and `USAGE` now say
    `git diff --name-only --no-renames ...`; the live run prints
    `fast-path: git diff --name-only --no-renames origin/main...nosuchref
    failed: ...` exit 2, and the bare run prints the updated USAGE, exit 2.
  - *Docstring/USAGE:* the module docstring and `USAGE` match the command
    the code runs. No other caller of the old string in the tree (the
    only consumer is the queue profile's `fast-path` hook, which reads the
    first output line, unchanged).
  - *Regression check:* none found. A side effect worth noting, not a
    finding: `python3 fast_path.py origin/main HEAD` on this branch now
    prints `fast-path: review (fast_path.py)` because HEAD changes a root
    Python file; correct under the rule.
- Standard: none (`standards.json` has 4 advisory statements; none
  matches).
- Decision: **fixed** by `9670deb` (breakdown row 12, tracker none, no
  issue created); re-verified in `verification.md` (`21ae6be`) and
  re-reviewed here. No Critical remains unfixed. The adjacent suspicion
  on `skills/implement-queue/SKILL.md` (`gate_paths`) was investigated by
  the Implement stage and is unproven, see Not examined in the Verdict.

### Major (FIXED in `63e7732`, ADR-0121, re-reviewed): ADR-0096 fast-path rule `docs/` + not-gate let a docs-only PR rewrite the instructions agents run, including the merge train's own protocol

- Scenario (original): the rule was "every changed path is under `docs/`
  and none is a gate path". `docs/` holds `docs/pipeline-protocol.md`
  (the protocol every skill is told to read), `docs/standards.json` (the
  review skill's standards index) and `docs/factory/*-routine.md`,
  including `docs/factory/merge-train-routine.md`, which the scheduled
  Sonnet routine reads each 4 hours. A PR that edited
  `merge-train-routine.md` to drop the one-at-a-time or `update-branch`
  step, or edited the protocol to loosen a gate, was `fast-path:
  low-risk` and, with a green `check`, auto-merged with no review and no
  human. ADR-0096's Consequences never mentioned that `docs/` carries
  executable-by-agent instructions.
- Fix evidence (`git show 63e7732`, `git diff c826be9..HEAD`; the code
  diff is `fast_path.py`, `tests/test_fast_path.py`,
  `.claude/implement-queue.md`, ADR-0096's status line, ADR-0121 and the
  index row):
  - *Entries and matching, run:* `GATE_PREFIXES` gains `docs/factory/`
    (prefix, with the slash), `GATE_FILES` gains
    `docs/pipeline-protocol.md` and `docs/standards.json` (exact
    match). `is_gate_path` over probes: `docs/factory/x`,
    `docs/factory/sub/costs.jsonl`, `docs/pipeline-protocol.md`,
    `docs/standards.json` -> gate, `classify` -> `('review', path)`.
    `docs/factory` (no slash; git lists files, and a file of that name
    cannot sit beside the directory), `docs/pipeline-protocol.md.bak`,
    `docs/standards.json.bak`, `docs/factory-notes.md`,
    `docs/sub/pipeline-protocol.md` and `docs/Pipeline-protocol.md` ->
    not gate, `low-risk`. That is the intended split: the files are
    exact, the directory is a prefix, and a neighbour or a nested
    same-name file does not trip the gate, as the profile's anchored
    globs read. Deleting or renaming the protocol away lists it under
    `--no-renames`, so it gates (`9670deb`). A path git quotes
    (non-ASCII, `"docs/..."`) fails the `docs/` prefix test and routes
    to review, the safe direction.
  - *`gate_globs()` rendering:* returns `['docs/adr/**', 'docs/design/**',
    'factory/templates/**', '.github/**', 'docs/factory/**',
    '**/prd.md', '**/architecture.md', '.claude-plugin/plugin.json',
    'docs/pipeline-protocol.md', 'docs/standards.json']`, ten globs, the
    same ten as the profile's `gate_paths` (the pin test passes).
    `{prefix}**` is correct because every prefix ends in `/`; `**/{name}`
    matches the classifier's any-depth basename rule.
  - *Pin test:* see the resolved Minor below; the two mutations fail it.
  - *Tests:* `test_the_instruction_docs_agents_obey_are_review` (five
    paths incl. `costs.jsonl`), the neighbour-stays-low-risk test, and
    `TestProfilePin`; the old low-risk case moved from
    `docs/factory/merge-train-routine.md` to `docs/setup.md`. Module:
    `python3 -m unittest tests.test_fast_path` -> `Ran 17 tests ... OK`
    (Notes say 17, was 14: true). `python3 fast_path.py origin/main HEAD`
    -> `fast-path: review (.claude/implement-queue.md)`, exit 1, correct
    under the rule (a `.claude/` file is not a docs path).
  - *ADR-0121 read in full:* provisional (written unattended; correct per
    the protocol), dated 2026-11-02, amends ADR-0096 decisions 2 and 3,
    cites the Owner's "Fix now" (matches `breakdown.md` Notes
    2026-11-02), with decision, rejected alternatives and an "If
    rejected" section. "ADR-0096's seven" is right (ADR-0087's four plus
    three). "18 references under `skills/`" is right (`grep -rn` count
    18, in 17 files). The routine list matches `AGENTS.md:177-189`. It
    passes the protocol's ADR test as an amendment of an accepted ADR.
    Number: 0121 is free on the local `origin/main` (highest 0120), not
    fetched.
  - *Amend, not rewrite:* ADR-0096's diff is its status line only
    (`accepted (Owner, 2026-10-15)` -> `amended by ADR-0121 (the gate
    paths and fast-path rule; accepted by the Owner 2026-10-15)`); its
    Decision is untouched, as the protocol's "Never rewrite" requires.
    `adr_status.py .` reads it as `standing: active`, and the compliance
    reference treats "amended by" as live, so the amendment is read
    with the ADR. The index row carries the same status. The Decision
    section still says seven gate paths while ten are live; that is the
    accepted cost of the rule and the status line points the reader on.
  - *Regression check:* none found. Side effect: a `docs/factory/` row
    append is now review-routed; the claim that no automated flow
    loses the fast path is checked for `costs.jsonl`, incomplete for the
    rest of the directory (new Minor below).
- Standard: none
- Decision: **fixed** (breakdown Milestone 3 row "Fast-path gates the
  instruction docs", tracker none, no issue created); re-verified in
  `verification.md` (`15812bc`) and re-reviewed here. Fixed, not
  deferred: the Owner chose "Fix now", so the earlier "open, awaiting
  the Owner" status is closed. Residual instruction-source exclusions
  are the new Minors below.

### Minor (RESOLVED in `63e7732`): the classifier's gate list and the queue profile's `gate_paths` were two copies with no test pinning them equal

- Scenario (original): `fast_path.py` hardcoded `GATE_PREFIXES`,
  `GATE_NAMES` and `GATE_FILES`; `.claude/implement-queue.md` listed
  `gate_paths` as globs; no test related them, so an Owner adding a path
  to the profile left the classifier saying low-risk for it.
- Fix evidence: `TestProfilePin` (`tests/test_fast_path.py`) parses the
  profile's `gate_paths` block and asserts `sorted(globs) ==
  sorted(fast_path.gate_globs())`. I mutated a temp copy of the tree
  (`git archive HEAD` into `/tmp/pin`): deleting the profile's
  `"docs/standards.json"` line, and separately changing
  `"docs/factory/**"` to `"docs/factory/"`, each made
  `python3 -m unittest tests.test_fast_path.TestProfilePin` fail
  (`FAILED (failures=1)`, 1 test); the unmutated tree passes (module:
  `Ran 17 tests ... OK`). Limits: `gate_globs()` is derived from the same
  constants the classifier uses, so the test pins the profile's spelling
  to the classifier's constants, not the skill's glob matcher to
  `is_gate_path`; and the parser reads the block line by line, so a
  reformat of the profile (flow list, single quotes, comment) fails the
  test loudly rather than passing, the safe direction.
- Standard: none
- Decision: **resolved** by `63e7732`; no residual drift risk found beyond
  the matcher limit above, listed under Not examined.

### Minor: the exit-2 reason shows git's usage line, not its error

- Scenario: for an unresolved ref, `fast_path.py` prints
  `fast-path: git diff --name-only origin/main...nosuchref failed: 'git
  <command> [<revision>...] -- [<file>...]'` (run above). `cli.detail`
  surfaces the last stderr line, which for this git failure is the usage
  hint; the useful line is `fatal: ambiguous argument ... unknown
  revision`. Behavior is correct (exit 2, fail closed, ADR-0088) but the
  problem string tells the reader nothing about the cause.
- Standard: none
- Decision: deferred — cosmetic to an operator reading the queue's
  report; the verdict is right.

### Minor: `run_tests.py` exits 0 when it discovers no modules

- Scenario: `run_tests.main` with a root that has no `tests/test_*.py`
  prints `tests: 0 tests across 0 modules in 0.0s on 8 workers, 0
  problem(s)` and returns 0 (run above against an empty root). `discover`
  with nothing found in a real checkout would be a renamed or missing
  `tests/` directory; `make check` stays green with zero tests, where
  unittest discover would report `NO TESTS RAN` and exit nonzero.
  The per-module path already fails closed (a child with no `Ran N tests`
  line is a failure, `run_tests.py:75-80`); the zero-module case does not.
- Standard: none
- Decision: deferred — root is derived from `__file__`, so it needs a
  restructure of `tests/` to trigger, and CI would also lose its tests
  loudly elsewhere (`gates.py`). One line (`if not modules: return 2`)
  closes it whenever Implement is next in the file.

### Minor: the Notes' fast-path test count was wrong, and two Accept lines are checked against numbers the tree no longer holds

- Scenario: breakdown.md Notes 2026-10-15 say `tests/test_fast_path.py`
  has "14 cases"; at the time of the first review `grep -n "def test"`
  listed 10 methods and the module ran 11 (the 11th inherited from
  `cli_contract.CliContract`). Likewise the row-1 Accept line says "exactly
  50 tests"; the module now runs 43 (14 moved to two siblings by #916's
  facet split; 43 + 10 + 4 = 57 in all). Re-review: the fix adds three
  real-git tests and the module now runs 14, so the Notes' "14" is true of
  today's tree by coincidence, not because it was ever reconciled; the
  row-1 "50" gap stands. The verification reports the gaps honestly
  (`verification.md` rows 1 and 8).
- Standard: none
- Decision: deferred — records only; no behavior depends on the
  numbers. A Notes correction at the next Operate touch is enough.

### Minor (new): the new real-git tests assume a git environment that signs nothing and uses the default config

- Scenario: `TestRealGit.repo` runs `git commit` through `git_repo.init`'s
  helper without disabling `commit.gpgsign` or pinning `GIT_CONFIG_*`. A
  developer or CI image whose global git config sets `commit.gpgsign=true`
  (with no usable key) would see `repo()` raise `CalledProcessError`, so
  the three tests error rather than fail. This is an inference from git's
  behavior; I did not reproduce it, and none of this host's global config
  has `diff.*` or `commit.gpgsign` set. It cannot make the classifier read
  low-risk (a test error is a failure, so it fails loud), it only costs
  noise. The classifier itself is immune to `diff.renames` or
  `diff.renameLimit` config because `--no-renames` overrides it (checked
  with `git -c diff.renames=copies diff --name-only --no-renames`).
- Standard: none
- Decision: deferred — one `-c commit.gpgsign=false` away if it ever bites;
  nothing has reported it.

### Minor (new, re-review 2): the survey calls the run-artifact trees "not instructions", but `docs/features/<slug>/autorun-brief.md` is the standing instruction an autorun resume obeys

- Scenario: the Notes' survey (`breakdown.md` 2026-11-02) and ADR-0121's
  Rejected alternatives exclude `docs/features`, `docs/fixes`,
  `docs/research`, `docs/launches` as "outputs of stages, not
  instructions". Most are. `docs/features/<slug>/autorun-brief.md` is
  not: `skills/autorun/SKILL.md:20` ("holds `autorun-brief.md`, this is a
  resume") and `:115` make it the instruction source a resumed autorun
  answers from, and this run's own stage assignments say to answer from
  the brief and keep its bounds (no push, no merge, no version bump).
  A docs-only PR that edits a brief on main (for example, adding "you
  may merge") is not a gate path, so it classifies `fast-path:
  low-risk` and, under `merge: auto`, merges unreviewed; the next resume
  of that run obeys the edited brief. Exposure is lower than the closed
  Major's: it touches one run's brief, and only a run resumed from main;
  the protocol and the routine protocols touch every run and a 4-hourly
  job. The brief is also Owner-authored, so an edit is visible in the
  PR, which no human is obliged to read on the fast path.
- Standard: none
- Decision: deferred — reason: narrower exposure, an Owner-authored file,
  and the ADR already tells the Owner they may add paths to `gate_paths`
  later; the fix is a `**/autorun-brief.md` entry in the profile and
  `GATE_NAMES`, which the pin test then keeps in step. The survey's
  wording "outputs of stages, not instructions" is wrong for this one
  file, and ADR-0121's rejected-alternatives list should say so at the
  next amendment. Flagged for the Owner: if they rank it Major, Ship
  waits on their fix-or-defer. The survey's other exclusions hold on the
  evidence: `docs/kb/**` is indexed by `AGENTS.md:208-221` for
  consultation; `docs/output-evals.md` is human-started
  (`evals/README.md:15`, per the Notes); `docs/launch-demo.json` is read
  by `launch_demo.py`. `docs/backlog.md` is read by the hourly routine as
  input (`hourly-improvement-routine.md:86,137`) and can steer which
  seed it picks up, but it is the advisory seed inbox (ADR-0029) and the
  routine's own output goes through review: a steering surface, not an
  instruction source. Recorded, not a finding.

### Minor (new, re-review 2): the "no automated flow loses the fast path" claim covers `costs.jsonl` only, not the other files under `docs/factory/`

- Scenario: ADR-0121 Consequences and the Notes survey say the assembler
  and gate-digest workflows push their `costs.jsonl` rows to main
  directly. Checked and true: `assembler.yml:311-318` (`tail -n 1 ...
  >> costs.jsonl`, then `git push origin HEAD:main`) and
  `gate-digest.yml:57-60` (`git add docs/factory/costs.jsonl`, `git
  commit`, `git push`); `cost-report.yml:51` only reads it. But the
  prefix `docs/factory/**` also covers three other writers' output:
  `docs/factory/batches/<batch>/ledger.jsonl` (`conductor.py:135`),
  `docs/factory/costs/runs/` per-run spend files (`cost_ledger.py:34`,
  `conductor_close.py` `carry_blocked_spend`) and
  `docs/factory/scorecards.jsonl` (`conductor_close.py:53`), which land
  on a batch branch and reach main by PR. None is tracked on main today
  (`git ls-files docs/factory` lists only the routines,
  `routine-markers.md` and `costs.jsonl`), and the conductor's closing
  merge goes through its own Owner ask (ADR-0085), not the queue's
  fast-path hook (`fast_path` appears only in the profile, the
  merge-train and hourly routines, `factory.py` and tests), so I found no
  flow that loses a fast path it had. The claim was audited for one file
  of four and states more than was checked.
- Standard: none
- Decision: deferred — reason: no observed behavior is wrong; a
  conductor batch PR is code plus ledger, so it is review-routed
  already. Correct the sentence at the next Notes/ADR touch to say what
  was audited, or confirm the conductor's PR never enters the queue.

## Honesty of the Owner-checked rows and the verification

Judged against the artifacts, not the code:

- **CI before/after record (#905) and Merge-wait record (#912)** are
  checked `[x]` in breakdown.md although each Accept line, read as
  written, missed (whole-run median 62.0s to 79.5s; p90 7.5h against a
  bar of under 4h). The Notes keep the miss, the numbers and the Owner's
  quoted decision in both cases, and the Accept lines were not edited.
  Verification reports both as **FAIL on the Accept line as written**
  and flags them for human review. That is honest. One residual
  weakness is structural: a `[x]` box reads as "criteria met" to anyone
  counting checkboxes (`breakdown.md` says Implement checks items off
  "as their acceptance criteria are met"). The honest signal lives in the
  Notes, not on the row. The verification answers the routing question
  its Failures section raises with "the Owner chose to accept"; I concur
  those two checks should stay checked only with that caveat, and I don't
  recommend un-checking.
- **Rows 1 and 3** (#902, #904) were also checked on the Owner's decision
  (Notes 2026-10-15, "Follow-up issue, close both") with their timing
  bars moved to #916. Verification labels them PASS on repo state with a
  NOT RUN part, not FAIL, and the Summary counts "2 FAIL on the original
  bar" as the Owner-checked rows. That undercounts the rows the Owner
  waived: four rows carry a waived Accept clause, not two (the other two
  waived a timing bar, which verification explicitly could not measure
  at load 191, so NOT RUN is defensible). It is a wording gap, not a
  false claim.
- **Verification's discrepancies** (test_fast_path 11 vs Notes 14;
  test_conductor_merge 43 vs Accept's 50) are real; I reproduced both
  numbers (11 and 43) in Scope. The 14 comes from the Notes and is
  wrong, see the Minor above.

## Passes with no findings

- **Correctness**, other than the findings above: `run_tests.py`'s count
  parse, exit code and ordering logic read clean (`run_tests.py:75-80`
  fails a child that never prints `Ran N tests`); verification's
  3965 = 3965 count equality holds.
- **Security**, other than finding 1: no secrets, subprocess calls use
  list args (`run_tests.py:92`, `cli.runner("git")`), no injection
  surface in `fast_path.py` (refs go into one `base...head` argument
  to git, never a shell). A ref beginning with `-` could be read by git
  as an option; the caller (the queue profile hook) passes
  `origin/main HEAD`, so this is a suspicion with no caller that supplies
  it.
- **Design**: matches the codebase patterns (`cli.runner` git port, root-only
  per ADR-0060, `factory.VERBS`). ADR-0097 was written for the one
  decision that needed it (the dual-membership pin moved 40 to 41), and
  ADR-0095/0096 pass the protocol's ADR test (hard to reverse the
  consent model, surprising, real trade-off). No ADR was rewritten in
  place: ADR-0097 supersedes only ADR-0091's `cli.py` row, in part, per
  its status line.
- **Complexity**: against `lean`'s cut-list nothing in the run's diff
  is a confirmed cut. No `lean:` markers (`git grep -n "lean:" --
  fast_path.py run_tests.py` finds none).
- **ADR compliance**: live ADRs checked against the diff: 0021
  (fast_path prints a problem string, never a traceback: holds), 0060
  (both new tools root-only: holds), 0087 and 0088 (see findings 1 and 2),
  0091 (pin updated by 0097), 0095 (CLAUDE.md/AGENTS.md rule matches;
  verification greps clean), 0096. No other violations; subjects outside
  the diff are out of scope.
- **Domain passes**: none selected. The changed paths contain no
  payment words, migrations, SQL or schema files, or package manifests.
  The word `webhook` and `deposit` do not appear in the paths.
- **Standards**: `docs/standards.json` filtered to `factory`/`pipeline`:
  `stdlib-only` (both new root scripts import only the standard library
  and `cli`; clean). No finding cites a statement; none is `enforced`.

## Verdict

**Ready for Ship on this review's findings. No Critical is unfixed, no
Major is open, and nothing new above Minor was found.** Two bars, stated
separately so neither reads as a pass over the other:

- **Critical: fixed** (`9670deb`, re-reviewed in the first re-review,
  unchanged by `63e7732`: `--no-renames` is still at `fast_path.py:63`
  and `TestRealGit` still passes in the 17-test module).
- **Major: fixed** (`63e7732`, ADR-0121, on the Owner's "Fix now" in the
  autorun resume session, `breakdown.md` Notes 2026-11-02). Re-reviewed
  here with the prefix/exact-match behavior run, the pin test mutated to
  fail, and the ADR read in full (see the Major's Fix evidence). It was
  fixed, not deferred, so no Owner deferral is owed.
- **New findings in this pass:** two Minors (the `autorun-brief.md`
  exclusion, the incomplete `docs/factory/` side-effect survey), both
  deferred with reasons; neither blocks. Both are flagged for the
  Owner's review because the first one is the same kind of hole as the
  closed Major, at lower exposure, and the Owner arbitrates severity
  (draft-first). If the Owner ranks it Major, Ship waits on a
  fix-or-defer from them.
- **Minors:** the pin-test Minor is resolved by `63e7732`; the rest are
  deferred with reasons (exit-2 string, empty-discovery exit 0, Notes
  counts, gpgsign assumption, and the two new ones).

Fail-closed roll-up, nothing here reads as a pass over these unknowns:

- **Not examined**: the GitHub-side `gate_paths` check's handling of
  renames. The re-verify found the skill never states how it gets the
  changed-file list, so no rename handling exists to be wrong; whether
  `gh pr view --json files` reports a rename's old path was not tested
  (no network here). Still a suspicion, unproven rather than unchecked.
  Also not examined: `check` job behavior on a PR that moves a workflow;
  the memory note and the `factory-merge-train` trigger (Owner steps
  outside the repo, NOT RUN in verification too); whether the
  merge-train routine or the profile's GitHub-side check applies
  `docs/factory/**` with the same anchoring as `fast_path.py` (the pin
  test proves the spelling is equal, not that the skill's matcher agrees;
  no code in this repo implements that matcher, the skill's prose does).
- **Not examined**: ADR-0121's number against a fetched `origin/main`.
  The local `origin/main` ref's highest ADR is 0120 and no 0121 exists
  there; I did not fetch, so a collision with a branch merged since is
  unchecked (the protocol's merge-time renumber rule covers it).
- **Inherited NOT RUN from verification, not re-run here**: the two
  timing bars (under-8s `test_conductor_merge`, under-25s `make check`;
  load average was 178 to 191) and the rows-4/11 `gh` numbers, which
  were taken from Notes.
- **Not run**: the five review passes were run by reading the code and
  the commands cited; no mutation or property test of `fast_path` beyond
  the rename reproductions and the pin-test mutations above. Multi-commit
  rename chains (A to B to C inside one PR) were not built; three-dot
  diff compares the merge base to the head tree, so they reduce to the
  same source-and-destination lists, but that is reasoning, not a run.
  `tests/test_fast_path.py` was run on this host only, with its git
  2.50.1 and no `diff.*` config.
- **Not decided here**: the two Owner-checked rows whose Accept lines
  missed (CI before/after, Merge-wait) stay the Owner's call, as in the
  honesty section; this verdict does not re-open them.
- The branch's own change is run artifacts plus the two code fixes; it
  is safe to commit, and this verdict is about the shipped code it
  documents.
