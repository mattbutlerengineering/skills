---
stage: operate
run: feature:decompose-eval-suite
date: 2026-11-07
users-observed: 0
signal-source: "Live `python3 decompose_grade.py` on this run's own breakdown.md + architecture.md (2026-11-07); `plugin-evals/records/2026-10-26-2.json` (json walk); `git log --since=2026-10-22 -- decompose_grade.py tests/test_decompose_grade.py plugin-evals/decompose` (0 commits); `gh issue list --state all --search 'decompose_grade OR decompose-eval-suite'` (#1064, #989, #1071); `grep -rn decompose_grade docs/ --include=*.md` outside this run (ADR-0114/0119 index, other runs' architecture/breakdown/verification, docs/research/desloppify-2026-10-31.md: all cite it as an existing tool, none ran it on a breakdown); AGENTS.md/CLAUDE.md line 103; LEDGER.md decompose row; `python3 eval_trends.py`."
---

# Retro: A scored, offline-gradable eval suite for Decompose

## Outcomes vs. intent
### A grader run on a known-good and a known-bad fixture cut gives different, explained scores, offline (idea.md "Success in one sentence"; PRD criteria 1 to 6)
- What happened: Held at release by tests, not by any later use. verification.md: 11 of 11 PRD criteria PASS on HEAD de59da1, with mutation checks that fail 4 to 8 tests each. No person has been observed running `decompose_grade.py` since release: `git log --since=2026-10-22 -- decompose_grade.py tests/test_decompose_grade.py plugin-evals/decompose` prints nothing, and no issue or doc records a grade of a real breakdown (docs/research/desloppify-2026-10-31.md and other runs' docs cite the tool by name only).
- Signal strength: unobserved

### The grader's score means something on a real breakdown (the PRD's "a score means something"; review.md deferred minor on 1.000)
- What happened: Measured state 2026-11-07, `python3 decompose_grade.py docs/features/decompose-eval-suite/breakdown.md docs/features/decompose-eval-suite/architecture.md` (exit 1): `decompose-grade: score 0.753 (coverage 0.625, dependencies 0.500, accept 0.889, sizing 1.000)`, `decompose-grade: 20 problem(s)`. Lines: 3 `coverage-miss` (Dependency check; Report and front door; Cuts and fixtures), 15 `dangling-blocked-by` (e.g. `S6 is blocked by "clause"`, `S2 is blocked by "sub-bullets"`), 2 `untestable-accept` (S7, S9). Every one is a false positive: this run's own breakdown is verified green and its architecture names those components, but the milestone-style rows use prose `Blocked by` and component names the fixture-calibrated parser does not match. AGENTS.md line 103 states this limit ("calibrated to fixture-spelled breakdowns and is not a retroactive audit of shipped runs"). So the only real-breakdown reading ever taken is 20 defects the tool should not claim, and the PRD's own run is a grader failure on its author. Caveat applies; this is not evidence the grader is wrong on fixture-spelled cuts.
- Signal strength: measured

### The suite is accepted by `claude plugin eval` and separates the skill from no skill (PRD criterion 7, "wired so `--tag decompose` selects it"; the run's explicit non-goal was no paid run)
- What happened: Contradicts the docs. `plugin-evals/records/2026-10-26-2.json` is a real with/without run of this suite: `suite.tagFilters ["decompose"]`, `ablation "with-without"`, one case `plugin-evals/decompose/csv-export-cut`, 3 runs per arm, `costUsd 1.4333`, `startedAt 2026-10-26T02:55:58Z`, `partial false`, `claudeVersion 2.1.310`, model claude-sonnet-5. Aggregates: `score 0.944`, `passRate 0.667`, `scoreWithout 0.667`, `passRateWithout 0`, `meanDelta 0.278`, `casesPassed 0` of 1 (threshold 1, so one with-arm run at 0.833 failed `blocked-by-names-real-items`; the other two with-arm runs scored 1). The harness discovered the case (the review "note" about `fixtures/` having no `case.yaml` is answered: no discovery failure, case ran, partial false). It was added to main in #1119 (dfa41f9, 2026-10-25, "first idea and decompose eval records"), 5 days after release, by someone other than this run. Without-arm weakness: all three without runs fail `has-rows` (the regex `^- \[ \] \*\*` is the skill's TEMPLATE row format) and the arm has no `skill-fired` grader result, so part of the 0.278 delta is a template-spelling and routing artifact, not breakdown quality; the idea.md risk "fixtures that only mirror the template" shows up here as measured behaviour. n = 3 per arm, one case, one fixture, one model: a pattern at best. LEDGER.md decompose row is unchanged (`used-once`, feature:seed-backlog, trigger 3/4); no illegitimate move: ADR-0019 and ledger rules keep eval results out of maturity, and `git log -- LEDGER.md` shows no edit citing this run.
- Signal strength: pattern

### Nothing else changed: no LEDGER move, no skill edit, no version bump (PRD criteria 9 to 10)
- What happened: Held. release.md protected-path diff empty at HEAD fc31bb6. Since release, `plugin-evals/records/` gained 3 files dated 2026-10-26 (2026-10-26.json is not this suite; 2026-10-26-3.json has `tagFilters ["idea"]`), all from #1119, none altered the LEDGER. `eval_trends.py` 2026-11-07: `plugin: 6 record(s), 2026-10-10..2026-10-26` and `REFUSED plugin: different suites ... no trend claim`; the decompose record is one suite point, so no trend over Decompose exists.
- Signal strength: measured

### A later prompt optimizer can consume score plus text feedback (PRD user story 6, issue #989 step 4)
- What happened: Unobserved. No optimizer ran; #989 closed 2026-10-21 with the PR and the GEPA/TextGrad step is not started in any issue found by `gh issue list --search decompose`. The grader's feedback is also only usable as a floor: review.md reproduced a 1.000 on four `Accept: <component> is basically fine and nice overall` rows.
- Signal strength: unobserved

## Open debt
Not feedback; listed, counted toward nothing.
- #1064 (closed 2026-10-26, type:chore): the run's two deferred review minors under "Decompose grader" (the CLI summary carries no "no defect the grader knows" caveat; no input size cap, about 2.5 s at 1.2 MB) plus "First paid runs". Its "First paid runs" paragraph says the decompose suite "has never run"; the decompose record landed in the same night's #1119, so the paragraph was already stale when the issue closed. The deferred minors themselves have no later commit touching `decompose_grade.py`.
- review.md deferred and noted minors: footer on the summary line (Owner call), size cap, `fixtures/` without `case.yaml` (now answered by record 2026-10-26-2; the note is closable).
- Unmet release.md Owner steps: ADR-0114 is still `Status: provisional` (docs/adr/0114-*.md); launch brief not produced (`launch_demo.py config` printed SHIP; no brief exists); pending wave release PR for the Decompose skill change from decompose-lessons not confirmed by this run.
- Placeholder-scan branch `feat/decompose-placeholder-scan` (idea.md assumption) and the first paid run's follow-ups (does the grader agree with the llm graders on the 3 with-arm and 3 without-arm breakdowns? the records hold the graders' verdicts, not the breakdowns) have no issue.

## Run retrospective
- Keep: Test-first with mutation checks in verification.md (4 to 8 tests fail per mutant); Review's reproduction of the vacuous-1.0 input (majors found by running, not reading); the "no paid run" scope fence, which kept cost at $0 inside the run; the honest "calibrated to fixtures, not an audit" sentence that made the live 0.753 on its own breakdown interpretable rather than alarming.
- Change: Run one cheap paid with-without case at ship instead of deferring, or leave the doc claim un-asserted. The authored claim "has never been run" was true for about 5 days and then false in two docs (AGENTS.md:103, CLAUDE.md:103) and one issue body (#1064), with no owner for updating it. Also: grade at least one real, non-fixture breakdown (this run's own) before shipping, since that is the first thing anyone will try and it returns 20 false defects.
- Stop: Writing state-of-the-world sentences ("has never been run", "no LEDGER change") into stable docs; write the rule (what moves maturity) and cite the record directory instead.

## Environment
| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| AGENTS.md and CLAUDE.md say the decompose harness suite "is authored and has never been run" after `plugin-evals/records/2026-10-26-2.json` ran it (stale since #1119, 2026-10-25) | AGENTS.md:103, CLAUDE.md:103; record `tagFilters ["decompose"]`, `costUsd 1.4333`; #1064 body repeats it | judgement: a "never run" claim has no machine form, and kb.py drift checks path and string references, not prose liveness; but the signal is mechanical (a `plugin-evals/records/*.json` whose `suite.tagFilters` names a suite the doc calls never-run) | the doc-gardener routine (journal #586) with a scripted check in `kb.py drift`, if the Owner wants one: flag any "never been run" sentence beside a suite that has a record. Today only the gardener's read catches it |
| Major: architecture whose component names are all under 4 chars scored coverage 1.0 / sizing 1.0 | review.md Major, fixed cb18259 | judgement (needed a reader to imagine the input); the fix is now mechanical via a test | review skill's pass on "vacuous 1.0 on empty gradable set"; pinned by `tests/test_decompose_grade.py` |
| Minor: comma inside a `Blocked by` label reported as dangling edge | review.md Minor, fixed 66280ad; reproduced today as 15 `dangling-blocked-by` false positives on this run's own breakdown | judgement for the first case, mechanical for the rest: a test that grades every `docs/features/*/breakdown.md` already on main and asserts no more than N false defects would catch spelling drift | `tests/test_decompose_grade.py` (add a real-breakdown regression set) |
| Two load-bearing branches (`MIN_WORDS`, Accept continuation line) unguarded | review.md Minor, mutants `MIN_WORDS = 2` and dropped continuation passed, fixed 3efbddd | mechanical (mutation check) | the verification.md mutation step, already used; no new carrier |
| architecture.md's Accept text contradicted the code | review.md Minor, fixed efcbb5d; breakdown.md Notes S9 records the same spec contradiction | judgement | review skill's pass (spec vs code read) |
| Spec ambiguity read literally would let filler pass | breakdown.md Notes 2026-10-20 S9 | judgement | review skill's pass; Build notes already carry it |
| Local `main` ref behind the branch base made the scope diff over-report | breakdown.md Notes 2026-10-20 S18 | mechanical | `python3 gates.py` (or the Ship pre-flight) comparing against `origin/main`, which Ship already does via `git fetch origin` |
| `plugin-evals/decompose/fixtures/` without `case.yaml` unknown to harness | review.md Minor (note); resolved by record 2026-10-26-2 (no discovery error) | mechanical once run | the paid first run itself; the note should be closed by whoever cites the record |

## Idea seeds
- Close the "has never been run" lines in AGENTS.md and CLAUDE.md to cite `plugin-evals/records/2026-10-26-2.json` (score 0.944, delta +0.278, n=3), and decide whether `kb.py drift` should flag a "never run" claim beside a recorded suite.
- Make `decompose_grade.py` parse the milestone-style breakdowns that real runs produce (prose `Blocked by`, component names in backticks) so grading a shipped breakdown stops returning 20 false defects, or have it exit 2 with "not fixture-spelled" instead of scoring.
- Rerun the decompose suite with `skill-fired` and `has-rows` removed from the delta (or applied to both arms) and a second fixture; today's 0.278 mixes skill effect with template-spelling and routing.
- Print a one-line "no defect the grader knows, not a quality score" footer when the grade is 1.000 (the #1064 deferred item, an Owner call).
- Feed the three with-arm records' failing `blocked-by-names-real-items` run to the grader offline to measure whether the deterministic and llm graders agree (needs the stored breakdowns, which records do not hold).

## Run complete
2026-11-07. Shipped and held by tests; the harness suite ran once on 2026-10-26 (a real run the run's own docs deny), the grader has no observed use and returns false positives on real breakdowns, 0 users observed, one doc claim to correct.
