---
stage: decompose
run: feature:faster-sdlc
date: 2026-10-14
assumptions:
  - "No architecture.md: the Owner chose to proceed with assumptions over a backfill interview. The design below comes from timings measured on origin/main (8528b1d) on 2026-10-14, recorded under Notes."
  - "No work-order ids: this run has no PRD (detector A requires one per WO row), so the rows are plain items mirrored to plain type:chore issues, the CLAUDE.md path for non-work-order tasks. Each row carries its issue as (tracker: #N)."
  - "The parallel runner is root-only (ADR-0060's rule: mirrored iff a payload tool imports it). factory_init's product_makefile transform keeps writing `python3 -m unittest discover -q tests` into the payload Makefile, so stamped repos are unchanged."
  - "Release PRs per wave already exist on main (plugin 0.9.0 through 0.19.0 each shipped in one chore(release) PR), and the Conductor's merge step 3 already bumps at merge time. What is left of the churn is the stated rule in CLAUDE.md and AGENTS.md, which still tells every branch to bump. Milestone 2 changes the rule; it adds no new bump mechanism."
  - "Milestone 3 adds no merge tool. implement-queue already takes open PRs first (Phase 0) and runs a serial merge train (Phase 3). The milestone gives this repo the queue profile it has lacked, a fast-path classifier and a schedule."
  - "No gate fails a branch that bumps the version: a stale cache from a late bump costs less than a false red on a legitimate release PR. Recorded in the new ADR (the Version-rule ADR item) as a rejected alternative."
---

# Breakdown: a faster verify loop, no version-bump treadmill, no merge-queue wait

Progress lives in the checkboxes below. Implement checks items off as their
acceptance criteria are met. Rows use the house grammar: a size class and blocking edges. Every row is test-first.

## Milestone 1: `make check` runs its tests in parallel, locally and in CI

- [ ] **Shared conductor-merge fixture** — Share one seeded git fixture across each `TurnCase` subclass in `tests/test_conductor_merge.py` — size:S, blocked by: — (tracker: #902)
  - Accept: `TurnCase` builds the seed repo, its bare origin and the configured clone once per subclass (`setUpClass`, keyed on the subclass, because subclasses override `configure` and `SEED`). Each test gets a private copy, so a test that pushes to origin or commits in the worktree cannot change what a sibling test sees. A planted test that commits to origin, followed by one that asserts origin's head is the seed commit, passes in both orders. The module still runs exactly 50 tests, all passing, and `python3 -m unittest tests.test_conductor_merge` finishes in under 8s on the Owner's 8-core machine (20.5s before).
- [ ] **Parallel test runner** — `run_tests.py`, stdlib, one subprocess per test module — size:M, blocked by: — (tracker: #903)
  - Accept: `python3 run_tests.py` discovers `tests/test_*.py` and runs each module as its own `python3 -m unittest tests.<module>` subprocess, across `os.cpu_count()` workers by default, with `-j N` to override it. It schedules modules longest-first from a committed timings file, falling back to alphabetical order when the file is absent or unreadable. It prints the total test count, and that count equals `python3 -m unittest discover tests`'s count on the same tree. It exits 0 only when every module passes. A planted failing test exits nonzero and prints `tests: <module> failed`, followed by that module's output. Stdlib only, and covered by `tests/test_run_tests.py`, which uses a fake subprocess port.
- [ ] **make check calls the runner** — root Makefile only; payload unchanged — size:S, blocked by: Parallel test runner (tracker: #904)
  - Accept: the root `Makefile`'s `check` target runs `python3 run_tests.py` in place of `unittest discover tests`. `factory_init`'s `product_makefile` transform maps that line back to `python3 -m unittest discover -q tests`, so the generated payload Makefile is byte-identical to before. `tests/test_gates.py::TestLockstep` and `tests/test_factory_init.py` pass. `factory_init.py update-manifest` is re-run and the manifest committed. The CLAUDE.md Verify list names the runner. The full suite passes in parallel on three consecutive runs, and `make check` finishes in under 25s locally (about 83s serial today).
- [ ] **CI before/after record** — prove CI got faster — size:S, blocked by: make check calls the runner (tracker: #905)
  - Accept: this file's Notes record the median `validator` push-run duration over the last 10 runs before "make check calls the runner" merged and over the first 10 after, both read from `gh run list`. If the after-median is not lower, the row stays unchecked and the gap is logged.

## Milestone 2: branches stop bumping the plugin version

- [ ] **Version-rule ADR** — New ADR: the plugin version moves only in a release PR or at the Conductor's merge — size:S, blocked by: — (tracker: #906)
  - Accept: the next free `docs/adr/NNNN-*.md` exists with status Proposed. It records the observed churn (five merge-and-re-bump commits on `feat/kb-weknora-lessons` between 2026-10-07 and 2026-10-14), the existing practice it ratifies (one `chore(release)` PR per wave, and the Conductor's `bump_version` at merge step 3), and the rejected gate alternative. It supersedes no ADR, because the old rule lives only in CLAUDE.md and AGENTS.md. `docs/adr/README.md` lists it, and `gates.py` passes.
- [ ] **Rewrite the version rule** — CLAUDE.md and AGENTS.md — size:S, blocked by: Version-rule ADR (tracker: #907)
  - Accept: the "Bump `.claude-plugin/plugin.json`'s version" bullet in CLAUDE.md and AGENTS.md now says that feature and fix branches never touch the version, that a wave's release PR bumps it once, and that a Conductor merge bumps it at step 3, citing the Version-rule ADR. `git grep -n "version with any"` matches nothing outside `docs/adr/` and dated run artifacts. `lint.py` and `gates.py` report 0 problems. Owner step, not repo state: update the memory note `parallel-pr-wave-single-version-bump` to match.

## Milestone 3: a green PR merges without waiting for an Owner session

- [ ] **Auto-merge ADR for this repo** — this repo opts in to ADR-0087 auto-merge, with an ADR-0088 fast path for docs-only PRs — size:S, blocked by: — (tracker: #908)
  - Accept: the next free `docs/adr/NNNN-*.md` after the Version-rule ADR exists with status Proposed. It cites the measured wait (Notes), says that ADR-0087's four conditions apply unchanged to every open PR in this repo whatever its author or branch, and names the gate paths this repo adds to ADR-0087's defaults: `factory/templates/**`, `.github/**` and `.claude-plugin/plugin.json`, so release PRs keep a human merge, consistent with Milestone 2. It defines the fast-path rule: every changed path is under `docs/` and none is a gate path. It records the cross-PR hazard (`docs/kb/cross-pr-merge-hazards.md`) and how the merge train handles it: one merge at a time, with update-branch and a green `check` before the next. `gates.py` passes. Owner gate: the rows below wait for the Owner to accept this ADR.
- [ ] **Fast-path classifier** — `fast_path.py`, stdlib, root-only — size:S, blocked by: Auto-merge ADR for this repo (tracker: #909)
  - Accept: `python3 fast_path.py <base> <head>` exits 0 and prints `fast-path: low-risk` when every path in `git diff --name-only <base>...<head>` matches the ADR's fast-path rule. It exits 1 and prints `fast-path: review (<first non-matching path>)` otherwise, and on an empty diff. It exits 2 with a `fast-path:` problem string when git fails or a ref does not resolve, which is ADR-0088's fail-closed case. Covered by `tests/test_fast_path.py` through a fake git port, which asserts each exact string, including `docs/adr/x.md` and `docs/features/a/prd.md` classified as review.
- [ ] **Queue profile for this repo** — `.claude/implement-queue.md` with `merge: auto` — size:S, blocked by: Fast-path classifier (tracker: #910)
  - Accept: the profile sets `merge: auto`, `required_check: check` (the validator workflow's gate job), the default `hold_labels`, `gate_paths` set to ADR-0087's defaults plus the ADR's three additions, and a `fast-path` hook that runs `python3 fast_path.py origin/main HEAD`. An implement-queue Phase 0 dry run, with nothing claimed and nothing merged, lists every open PR with its verdict (merge, review first, human gate, or wait) and its reason. The Notes record that run. Owner step, not repo state: add the session permission that ADR-0087's merge command needs (`gh pr merge <N> --auto --squash --delete-branch`), since without it the runtime denies the merge and the skill never retries.
- [ ] **Merge-train routine** — a scheduled implement-queue pass that only clears open PRs — size:S, blocked by: Queue profile for this repo (tracker: #911)
  - Accept: `docs/factory/merge-train-routine.md` defines a routine in the queue groomer's pattern. It runs implement-queue's Phase 0 and Phase 3 against open PRs only, claims no new issue, uses the markers in `docs/factory/routine-markers.md`, and reports each run in one comment on a named journal issue. `docs/factory/` lists it beside the other routine protocols. Owner step, not repo state: create the trigger (cadence recommendation: every 4 hours). Triggers are the Owner's decision, as with the deferred roster routines.
- [ ] **Merge-wait record** — prove the queue wait shrank — size:S, blocked by: Merge-train routine (tracker: #912)
  - Accept: two weeks after the routine's first run, Notes record the same three numbers as the baseline over the PRs merged since then: median open-to-merge time, p90, and the share of open-hours held by PRs open longer than 4h. The row is checked only if p90 is under 4h. Otherwise it stays unchecked and the gap is logged.

## Design gaps found

None. Two open judgments are the Owner's: the Version-rule ADR and the Auto-merge ADR both land as Proposed, and Milestone 3's later rows wait on the second one.

## Notes

- 2026-10-14 baseline, origin/main 8528b1d, 107 files under tests/: `python3 -m unittest discover tests` takes 82.5s wall at 73% of one core. Slowest modules: `test_conductor_merge` 20.5s (50 tests, each building a fresh seed, bare origin, clone and worktree), `test_cli` 7.4s, `test_conductor_portable` 4.5s. `lint.py` takes 0.09s and `gates.py` 0.5s. Validator CI runs took 40–190s.
- 2026-10-14 merge-wait baseline, the last 150 merged PRs (`gh pr list --state merged --limit 150`): median open-to-merge time 0.64h, p75 2.0h, p90 13.5h. 24 PRs (16%) were open longer than 4h, and they hold 96% of all PR open-hours. The longest were routine and agent PRs from 2026-09-28 that sat about 9 days, until the next Owner merge session. By day, merges come in bursts: 52 on 2026-10-14, none from 2026-09-29 through 2026-10-06. main has no branch protection (`docs/kb/main-unprotected.md`).
