---
stage: review
run: feature:faster-sdlc
date: 2026-11-02
assumptions:
  - "Scope: the run has no prd.md or architecture.md and no 'diff since the run began' on this branch (it adds only run artifacts), so the reviewed change set is the code the run's tracker rows shipped to main, identified from breakdown.md's Notes and `git log`. The Design pass checks against the accepted ADRs the run wrote (0095, 0096, 0097) and the cited ADR-0087/0088, since there is no architecture.md."
  - "Recommended default taken (draft-first): severities below are the reviewer's draft; the Owner arbitrates. The rename finding is ranked Critical because it lets a gate-path change classify low-risk under an auto-merge rule; the skill's fix loop then blocks Ship until it is fixed or the Owner re-ranks it."
  - "Recommended default taken (no code edits): the skill routes a Critical finding to Implement, so nothing was fixed on this branch."
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

Not reviewed: the GitHub-side behavior of the `check` job and of
`gh pr view --json files` (no network read here); the memory note and the
`factory-merge-train` trigger (outside the repo).

## Findings

### Critical: fast-path classifier reads `git diff --name-only` with rename detection on, so a gate-path file moved into `docs/` is classified low-risk

- Scenario: `fast_path.changed_paths` runs `git diff --name-only
  <base>...<head>` (`fast_path.py:62`). Git's default rename detection
  lists only the *destination* of a rename. Reproduced in `/tmp/fpt`
  (base commit has `.github/workflows/validator.yml` and
  `docs/adr/0001-x.md`; the PR branch `git mv`s them to
  `docs/validator.yml.txt` and `docs/old-0001.md`):
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
  So a PR that deletes (moves out) a file under a gate path
  (`docs/adr/**`, `**/prd.md`, `.github/**`, `factory/templates/**`,
  `.claude-plugin/plugin.json`), or moves one in docs with edits at
  similarity of 50% or more (for example an ADR renamed to
  `docs/x.md` with its Decision rewritten), is reported as touching only
  `docs/...`. Under `merge: auto` (ADR-0096 decision 3, ADR-0088) that
  classification is the review, so the PR needs only a green `check` to
  merge with no human. The gate-path rule exists so those paths always
  keep a human merge (ADR-0087). Other defences exist (a moved workflow
  means no `check` run, and `gates.py` and the tests may fail on a
  missing ADR or index row), but the classifier is the control ADR-0096
  names for this decision, and none of them is its contract. Test
  coverage misses it: `tests/test_fast_path.py` feeds a fake git port the
  already-listed paths, so no test builds a rename.
  `skills/implement-queue/SKILL.md:198` (condition 4, `gate_paths`) may
  share the blind spot if it reads `gh pr view --json files`; I did not
  verify that and list it as a suspicion, not a finding.
- Standard: none (`standards.json` has 4 advisory statements; none
  matches).
- Decision: **open, unfixed — fix required before Ship** (a Critical per
  the skill's fix loop). Fix shape for Implement: add `--no-renames` to
  the diff args (or `--name-status` and take both sides of `R`/`C`), plus
  a real-git test (a temp repo with a rename out of a gate path) beside
  the fake-port ones. Not done here: this stage does not edit code.

### Major: ADR-0096 fast-path rule `docs/` + not-gate lets a docs-only PR rewrite the instructions agents run, including the merge train's own protocol

- Scenario: the rule is "every changed path is under `docs/` and none is
  a gate path" (`fast_path.py:34-38`). `docs/` holds `docs/pipeline-protocol.md`
  (the protocol every skill is told to read), `docs/standards.json` (the
  review skill's standards index) and `docs/factory/*-routine.md`,
  including `docs/factory/merge-train-routine.md`, which the scheduled
  Sonnet routine reads each 4 hours. A PR that edits `merge-train-routine.md`
  to drop the one-at-a-time or `update-branch` step, or edits the
  protocol to loosen a gate, is `fast-path: low-risk` and, with a green
  `check`, auto-merges with no review and no human. ADR-0096's
  Consequences discuss that `.claude/` and root Python are not gate paths
  but never mention that `docs/` carries executable-by-agent
  instructions. This is a deviation from the Owner's intent in
  `docs/features/faster-sdlc/breakdown.md` (gate paths so release PRs
  keep a human merge), not a coding error.
- Standard: none
- Decision: deferred to the Owner — an ADR amendment is owed, not a code
  fix: either add `docs/factory/**`, `docs/pipeline-protocol.md` and
  `docs/standards.json` to the three-plus-four gate paths (profile and
  `GATE_PREFIXES`), or record the risk as accepted. Reason: the choice
  trades merge speed against a human merge on docs the agents obey, which
  is the Owner's call.

### Minor: the classifier's gate list and the queue profile's `gate_paths` are two copies with no test pinning them equal

- Scenario: `fast_path.py:28-31` hardcodes `GATE_PREFIXES`, `GATE_NAMES`
  and `GATE_FILES`; `.claude/implement-queue.md:4-11` lists `gate_paths`
  as globs. `git grep -n "GATE_PREFIXES\|implement-queue.md" -- tests
  '*.py'` finds no test relating them. An Owner who adds a path to the
  profile (as ADR-0096's Consequences invite: "the Owner may add them to
  `gate_paths` later") leaves the classifier still saying low-risk for
  that path whenever it sits under `docs/`. The Notes 2026-10-15 even say
  the profile is the policy. The two sources of truth drift silently.
- Standard: none
- Decision: deferred — a pin test (parse the profile's `gate_paths`,
  assert each is classified review) is cheap, but nothing is broken today:
  the two lists agree on this tree. Revisit with the Major above, which
  already changes both lists.

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

### Minor: the Notes' fast-path test count is wrong, and two Accept lines are checked against numbers the tree no longer holds

- Scenario: breakdown.md Notes 2026-10-15 say `tests/test_fast_path.py`
  has "14 cases"; `grep -n "def test" tests/test_fast_path.py` lists 10
  test methods and `python3 -m unittest tests.test_fast_path` runs 11
  (the 11th comes from the inherited `cli_contract.CliContract`). Neither
  is 14, so the Notes overstate. Likewise the row-1 Accept line says "exactly
  50 tests"; the module now runs 43 (14 moved to two siblings by #916's
  facet split; 43 + 10 + 4 = 57 in all). The verification reports both
  gaps honestly (`verification.md` rows 1 and 8) but nothing in
  breakdown.md Notes reconciles them, so a reader of Notes alone gets 14
  and 53.
- Standard: none
- Decision: deferred — records only; no behavior depends on the
  numbers. A Notes correction at the next Operate touch is enough.

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

**Not ready to ship: one Critical finding is unfixed.** The fast-path
classifier misreads a rename out of a gate path as docs-only (finding 1,
reproduced), which the skill's fix loop requires fixed before Ship, by
Implement and then re-verified. The Owner owns the Major (an ADR
amendment on docs-as-instructions), which is open and deferred. Minors 3
to 6 are deferred with reasons.

Fail-closed roll-up, nothing here reads as a pass over these unknowns:

- **Not examined**: the GitHub-side `gate_paths` check's handling of
  renames (suspicion, unverified); `check` job behavior on a PR that
  moves a workflow; the memory note and the `factory-merge-train`
  trigger (Owner steps outside the repo, NOT RUN in verification too).
- **Inherited NOT RUN from verification, not re-run here**: the two
  timing bars (under-8s `test_conductor_merge`, under-25s `make check`;
  load average was 178 to 191) and the rows-4/11 `gh` numbers, which
  were taken from Notes.
- **Not run**: the five review passes were run by reading the code and
  the commands cited; no mutation or property test of `fast_path`
  beyond the rename reproduction.
- The branch itself is only run artifacts; its own change is safe to
  commit, and this verdict is about the shipped code it documents.
