---
stage: operate
run: feature:decompose-outcome-signals
date: 2026-11-07
users-observed: 0
signal-source: "No person observed using the tool. Checked 2026-11-07 from /tmp/dc-retro: `python3 decompose_signals.py` run live; `git log --oneline --since=2026-10-19 -- decompose_signals.py tests/test_decompose_signals.py` (empty); `ls evals/results | grep decompose` (two records, both 2026-10-18); `grep -rn decompose_signals` over code and docs; `gh issue list --state all --search decompose_signals` (only #986 closed, #1048 write-back chore); `git for-each-ref refs/remotes/pr`; plugin-evals/records/2026-10-26-2.json; AGENTS.md; ADR-0109/0110/0111 headers."
---

# Retro: Decompose outcome signals from git history

## Outcomes vs. intent

### One command prints re-plan, design-gap and review-traced counts per run and in aggregate, each boundary labelled observed or inferred
- What happened: measured state. `python3 decompose_signals.py` on 2026-11-07 exits clean with `decompose-signals: 50 run(s), 0 problem(s)`, per-run rows each labelled observed/inferred, and three aggregate lines, e.g. `aggregate re-plan — observed 2/126 over 12 run(s); inferred 10/286 over 31 run(s); combined 12/412 over 43 run(s); unmeasurable 7 run(s)`, `aggregate design gaps — observed 2/12 over 12 run(s); inferred 0/23 over 23 run(s); combined 2/35 over 35 run(s); unmeasurable 15 run(s)`, `aggregate review-traced — observed 38/281 over 50 run(s); … unmeasurable 0 run(s)`. It first printed 36 runs at release (release.md log step 5), so the tool keeps working as the repo grows. Nobody was observed running it. The only code that calls it is repo code: `decompose_lessons.py` (`import decompose_signals`, `decompose_signals.SIGNALS`, `.measure`) and `decompose_grade.py` (`item_keys`).
- Signal strength: measured (the tool's output). Use by a person: unobserved.

### Unmeasurable runs are named with a reason and kept out of aggregates; a zero is never read as "no data"
- What happened: measured state. Today's output names 7 runs unmeasurable for re-plan (e.g. `maintenance:deepening-cli-seams — … the first version (ec957eb) already checks 9 of 9 rows`) and 15 for design gaps (e.g. `no "Design gaps found" section at the decompose boundary`), and they are excluded from the aggregates above. One caveat is recorded in review.md and left unfixed: an empty `## Design gaps found` section prints as a missing one (reason string only).
- Signal strength: measured.

### The first real numbers are recorded append-only by the tool's own output and reproduce
- What happened: two records exist, `evals/results/decompose-signals-2026-10-18.json` and `-2026-10-18-2.json`, both release-day. `--record` has not run since: `git log --since=2026-10-19` on the tool and its tests shows only the merge commit 69e6290 (#1040), and `ls evals/results` has no later decompose-signals file. Verification reproduced the second record byte for byte on its record-time refs (verification.md Summary). Today's ref set has changed (`refs/remotes/pr` holds 492 refs where the records read 488; heads 448 vs 401), so today's output is not the record's reproduction, it is a new, unrecorded measurement. The records also count 36 runs against 50 today, so the baseline is already stale by 14 runs. They are not a series (ADR-0111, release.md Outcome).
- Signal strength: measured (reproduction at record time); drift since: measured, no one acted on it.

### The signals feed the later steps of the Decompose learning loop (#987, #988, #989)
- What happened: wired in code, not shown in use. `decompose_lessons.py` (shipped 2026-10-20, #1050) reads "the three outcome signals" from `decompose_signals.SIGNALS` and calls `decompose_signals.measure`; `decompose_grade.py` reuses `item_keys`; ADR-0112, 0113, 0114 and 0116 cite the tool. #986, #987, #988, #989 are all CLOSED (2026-10-20 to 2026-10-21). No file in the repo holds a lessons ledger (`git ls-files | grep -i lesson` shows only the tool, ADRs and run docs), so no lesson has been drawn from the numbers yet. Whether anyone changed the Decompose skill because of them: unobserved.
- Signal strength: pattern (three later runs depend on it structurally); decision impact: unobserved.

### Boundary refs are available (PR heads fetched), so the observed population is not the 3 runs idea.md feared
- What happened: `git for-each-ref refs/remotes/pr` shows 492 refs now, and `refs/pr` 13; the PR-head fetch is a manual step the tool never runs (AGENTS.md lines 59-66) and the record `refs` blocks show it had already been done by 2026-10-18 (488). Who ran it and when is unobserved; the count rose by 4 since the records, so it has been re-run or the refs were otherwise updated. Observed boundaries: 12 runs on the re-plan and design-gap signals today (vs 4 in release.md log step 5), so the idea.md fear that a tool "honestly measures 3 runs" did not hold, but 31 of 43 measurable re-plan runs are still inferred.
- Signal strength: measured (ref counts and aggregates), fetch ownership unobserved.

## Open debt

Listed, counted toward nothing.
- ADR-0109, ADR-0110, ADR-0111 are still unconfirmed. ADR-0109's status line reads `superseded in part by ADR-0111 (…; provisional)`; ADR-0110 and ADR-0111 read `Status: provisional`. release.md Owner step 2 not done. The records cite ADR-0109 and ADR-0111 in `rule`, and release.md says not to treat them as a baseline until confirmed.
- Launch brief not produced (release.md assumption 5, Outcome last bullet). `launch_demo.py config` said SHIP; no brief committed, none requested.
- Deferred review minors (release.md Outcome): empty "Design gaps found" section reads as missing; no `tests/timings.json` entry for `tests.test_decompose_signals` (run_tests.py reads that file); first record measured the run mid-flight.
- Implement-stage suite flake (`2 problem(s)`, unnamed ~60 s module) never recurred in Verify's five runs or Ship's; cause unknown (verification.md Not verified).
- Release step 4 (keep the branch or `refs/pull/1040/head` reachable): not observable here. Squash-merge hides the run's boundary commits otherwise, and the tool's "this run" row depends on them. Today the row resolves (`decompose observed de92f3c, implement observed 56baba9`).
- Write-back happened (release.md `outcome: released`, `released-at: 2026-10-20`; chore #1048 closed). No issue was filed for the run's debt.

## Run retrospective
- Keep: stopping Implement at S13 when the first `--record` read `re-plan 12 of 14` for codex-style-standards-enforcement and routing it back to Architect (breakdown.md Notes) rather than committing a lying baseline; the second record reproducing byte for byte under Verify; ADR-0111 only after measuring the premise on 4 runs; mutation checks in Review that found 5 surviving mutants.
- Change: take the baseline record only when the run is closed, not mid-flight (review.md: record 1 measured this run before its implement commit existed); confirm architecture assumptions against all runs with data before writing them into an ADR (review.md Major 2: ADR-0109's "windows agree" was falsified by the run's own row). Re-take a record after a fetch changes the ref set; the 2026-10-18 baseline predates 14 runs and 4 PR refs.
- Stop: citing the records as a baseline while the ADRs they cite are provisional and the Owner step stays open; counting the tool's existence as adoption. Nothing here shows a human read the numbers.

## Environment
| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| `git log` history simplification hid boundary commits behind a merge | review.md Major 1 | mechanical | `tests/test_decompose_signals.py` fixture of a squash-merged run branch (already how it was caught and fixed) |
| ADR claimed "the two implement windows agree today" on 3 runs; this run's row falsified it | review.md Major 2; verification.md Summary (ADR-0111) | judgement | review skill's pass: check every "agree today" claim against the full measured population |
| Cherry-picked/rebased architect commit counted as a second route | review.md Minor 1 | mechanical | `tests/test_decompose_signals.py` |
| Hyphenated compound (`implement-queue`) read as the stage word | review.md Minor 2 | mechanical | `tests/test_decompose_signals.py` |
| Survivors: split threshold `> 0` for `> 1`; missing `(?!-)` guard; 3 mutants of the ADR-0111 pass | review.md Minor 3 and re-run Minor | mechanical | `tests/test_decompose_signals.py` (the mutants were killed by added tests) |
| Empty "Design gaps found" section printed as missing | review.md Minor 4; release.md Outcome (deferred) | mechanical | `tests/test_decompose_signals.py` |
| No `tests/timings.json` entry for the new module | review.md Minor 5; release.md Outcome (deferred) | mechanical | `run_tests.py` and `tests/test_run_tests.py` (they read `tests/timings.json`) |
| First record measured the run mid-flight | review.md Minor 6; breakdown.md Notes S13 (codex row 12 of 14 false re-plans) | judgement | review skill's pass: a committed measurement must be taken at the stage it claims |
| ADR-0110 Context named `parse_row`; module imports `ROW` | review.md Minor 8 | mechanical | `kb.py drift` for ADR-to-code name claims, otherwise the review skill's pass |
| Unexplained Implement-stage suite flake (`2 problem(s)`) | verification.md Not verified | judgement | none yet; `run_tests.py` already counts failed modules |

## Idea seeds
- Re-run `python3 decompose_signals.py --record` on a schedule or at each Operate retro: records stopped 2026-10-18 while runs went from 36 to 50; an eval_trends line for `decompose-signals` would make the gap visible (it reports `2 record(s), 2026-10-18..2026-10-18`).
- Confirm or amend ADR-0109/0110/0111 so the records become citable; today every consumer (`decompose_lessons.py`, `decompose_grade.py`, ADR-0112..0116) builds on provisional ADRs.
- Make `decompose_signals.py` or `kb.py drift` check that `refs/remotes/pr` is non-empty and print its age, so the manual PR-head fetch is not an invisible precondition (31 of 43 re-plan runs are still inferred).
- Add an Operate-stage check that a tool's downstream consumer ran: `decompose_lessons.py` imports `SIGNALS` but no lessons ledger exists, so the loop's third step has no output on file.
- Correct AGENTS.md's "decompose harness … has never been run" (its line 103): plugin-evals/records/2026-10-26-2.json is a with/without run, `tagFilters: ["decompose"]`, 1 case (`csv-export-cut`), costUsd 1.433, started 2026-10-26T02:55Z. This is the neighbour tool's claim, and no step has the claim checked against records.

## Run complete
2026-11-07: shipped and merged (#1040), tool still runs clean (`50 run(s), 0 problem(s)`) and downstream code imports it, but 0 users observed, no record since release day, and the ADRs behind it are still provisional.
