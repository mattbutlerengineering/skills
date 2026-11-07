---
stage: operate
run: feature:decompose-lessons
date: 2026-11-07
users-observed: 0
signal-source: "Live `python3 decompose_lessons.py` from /tmp/dc-retro (HEAD = origin/main) on 2026-11-07; `ls docs/factory/decompose-lessons.jsonl` (absent) and `git log --all -- docs/factory/decompose-lessons.jsonl` (empty); `git log --oneline --since=2026-10-21 -- decompose_lessons.py tests/test_decompose_lessons.py` (2 commits); `gh pr view 1050` (MERGED 2026-10-21T00:55:46Z); `gh issue list --search decompose-lessons` (#1053, #1061, #1069, #1071); breakdown.md assumptions in five later runs; plugin-evals/records/2026-10-26-2.json; AGENTS.md line 103; .claude-plugin/plugin.json (0.27.0). No person was observed using the ledger."
---

# Retro: A ranked lessons file for Decompose

## Outcomes vs. intent

### A lesson exists only with source runs cited
- What happened: unobserved in use; the ledger does not exist. `ls docs/factory/decompose-lessons.jsonl` -> no such file; `git log --all -- docs/factory/decompose-lessons.jsonl` prints nothing, so no lesson was ever committed. The rule is enforced in code and tests only (verification.md: 13 of 13 PRD criteria PASS, each with a mutation that made tests fail). After release the rule was hardened by two fixes: ec8159f (ADR-0116, per-signal seen) and 132c08a (ADR-0117, hit run seen before its clean partner).
- Signal strength: unobserved

### A lesson decays to removal at 0
- What happened: unobserved in use. No lesson has been voted on, because none exists. Only the scratch-clone runs in verification.md exercised votes. Review found that a drop followed by a second voter wedged `update` permanently (7631066 fixed it before merge), so the decay path was already wrong once before release.
- Signal strength: unobserved

### The Decompose skill reads the file at draft time
- What happened: the skill step shipped (skills/decompose/SKILL.md step 3, "Read past lessons") and reached installed plugins through #1053 (plugin 0.22.0, now 0.27.0). Five later Decompose breakdowns record running it and finding nothing: house-voice ("it is absent, so nothing was weighed"), polish-blockers-and-patterns, review-interface-pass, reviewer-blind-cutoff and svg-mechanical-check (each says `docs/factory/decompose-lessons.jsonl` does not exist; git dates the house-voice and svg-mechanical-check breakdowns 2026-11-04). Five agent drafts read the step and none consumed a lesson. No breakdown.md cites a lesson id. These are agent runs, not people, so they count toward nothing.
- Signal strength: measured (the read happened five times; the consumption count is 0)

### Ledger state and the treated-versus-untreated comparison
- What happened: `update` has never been run by the Owner (no ledger, no commit touching it; release.md Owner step 3 is unmet). Live output of `python3 decompose_lessons.py` (no argument, read-only, exit 0) on 2026-11-07:
  ```
  decompose-lessons: 22 contrast pair(s) from 22 hit run(s): re-plan 3, design gaps 2, review-traced 17
  decompose-lessons: no verdict: 0 treated run(s) is below the minimum of 5
  decompose-lessons: unmeasurable re-plan run(s): maintenance:deepening-cli-seams, maintenance:gate-timeline-timestamp-trust, maintenance:one-fact-one-owner, maintenance:one-frontmatter-end, maintenance:one-labels-walk, maintenance:quoted-token-is-not-a-claim, maintenance:row-done-guard
  decompose-lessons: 50 run(s), 0 problem(s)
  ```
  The tool has 22 pairs to derive (18 at release, per breakdown.md Notes), but 0 treated runs against a floor of 5, so the loop cannot yet say whether lessons lower the re-plan rate. The experiment the idea named has not started.
- Signal strength: measured (tool output; the comparison itself has no verdict)

## Open debt

The run's own items, listed and counted toward nothing:
- Owner step 3 unmet: the first `docs/factory/decompose-lessons.jsonl` is not committed and `update` never ran. The idea's Success sentence cannot be tested in the wild until it is.
- Owner step 4 unmet: ADR-0113 is still `provisional` and now "superseded in part by ADR-0116" (docs/adr/README.md row 136); ADR-0116 is itself superseded in part by ADR-0117 (provisional). Three provisional ADRs deep on one tool.
- Launch brief not produced (release.md assumption 6; `launch_demo.py config` said SHIP). Never run.
- Closed since release: wave chore(release) #1053 (Owner step 2; done); #1061 (deferred major per-signal seen plus four minors, `type:chore`, closed 2026-10-24); #1069 (hit run seen before its clean partner).
- Still deferred from review.md with no issue found: vote order changes the outcome; a zero-item treated pool reads "not higher"; no file size cap; the S9 no-hand-written-seed gap (a well-formed, sourced, fabricated lesson loads; the PR diff is the control); the treated-run count starts at the decompose commit, before the skill reached users (review.md Minor). The last one is observable now: the plugin shipped in 0.22.0, after the ancestry cut.
- 7 `maintenance:*` re-plan runs are unmeasurable (live output), an upstream `decompose_signals.py` gap, not this run's.
- AGENTS.md line 103 says the Decompose harness `plugin-evals/decompose/` "has never been run". That claim is stale; see the Environment table.

## Run retrospective
- Keep: the mutation-sweep verification (verification.md names the mutation each test killed) and the review's adversarial hunt, which found the wedged-`update` and prompt-injection surface before merge. Also splitting the ledger's one writer (`update`, Owner-run) from the read-only default; the live call today was safe.
- Change: build the consumer's feed before the consumer. This run shipped a reader of a file nobody was told to create; two weeks and five Decompose drafts later it is still absent. Decide in the PRD who writes the first ledger and when, and put that as a numbered Ship gate or a queue item, not an Owner footnote. Also, the treated-run definition (git ancestry) was known in review to start before users, and shipped anyway; a definition the review calls wrong should be an Architect amendment, not a deferral.
- Stop: shipping a deferred major (#1061) whose fix changes the on-disk shape; it cost two superseding ADRs (0116, 0117) in a fortnight. Stop recording "deferred" for a shape change; either fix before the file exists (when migration is free) or record why not.

## Environment
| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| Wedged `update`: a second voter on a dropped lesson aborted every later fold | review.md Major 1, fixed in 7631066 | judgement | the review skill's pass (adversarial sequence over state changes); the regression test in tests/test_decompose_lessons.py now pins it |
| A review with no finding heading was read as a clean observed run | review.md Major 2, fixed in d1746fe | mechanical | tests/test_decompose_lessons.py (fixture review with no heading) |
| Ledger text was an unvalidated prompt-injection surface | review.md Major 3, fixed in bad1b98 and 94186f3 | judgement | the review skill's pass (untrusted-data-into-prompt check); the `load` template check now enforces it |
| Per-run `seen` lost a signal that matured later | review.md Major (deferred); #1061; fixed ec8159f (ADR-0116) | judgement | the review skill's pass (state recorded at time T vs. data completed at T+n); no deterministic check exists |
| A hit run seen before its clean partner never paired | #1069; fixed 132c08a (ADR-0117) | mechanical | tests/test_decompose_lessons.py (order-permutation fixture of seen, hit and clean runs) |
| PRD criterion 10's no-seed clause tested only "an existing file loads clean" | verification.md line 244 | mechanical | the review skill's pass (a committed ledger needs its derivation re-run in the PR); no deterministic check exists today |
| Stale pair counts (26/4/145) in architecture.md vs. 18 shipped | breakdown.md Notes S5/S6; release.md deferred list | mechanical | kb.py drift does not cover architecture figures; a `gates.py` detector for numbers in run docs does not exist; leave to the review skill's pass |
| AGENTS.md says the decompose harness "has never been run" after plugin-evals/records/2026-10-26-2.json ran it | AGENTS.md line 103 vs. record 2026-10-26-2.json (suite ablation with-without, tagFilters ["decompose"], 1 case `csv-export-cut`, costUsd 1.4333, startedAt 2026-10-26T02:55:58Z, overallPassRate 0.667, meanDelta +0.278, casesPassed 0 of 1); commit dfa41f9 (2026-10-25) added "first idea and decompose eval records" | mechanical | kb.py drift (a claim about a harness "never run" against the existence of a record under plugin-evals/records/) |
| AGENTS.md on-demand-tools section drifted from CLAUDE.md (5 bullets missing) | #1071 (closed) | mechanical | kb.py drift (already caught it; no new carrier) |

## Idea seeds
- A Ship gate that, for any new consumer of an Owner-written file, names who commits the first file and when, so "reader shipped, file absent" cannot close an Operate stage as "released".
- Rewrite the treated-run cutoff to the plugin-release commit (the chore(release) that carried the skill step, #1053) instead of the decompose commit, so the first-5-treated floor counts only drafts that could read the file.
- A `kb.py drift` check: a "never been run" / "has never been run" claim in AGENTS.md or CLAUDE.md fails when a record for that harness exists under plugin-evals/records/ or evals/results/.
- Step 4's first record (plugin-evals/records/2026-10-26-2.json, one case, casesPassed 0 of 1) is not enough to judge the lessons; extend the decompose suite past one case before using it as the lesson-treated control.
- Run `update` once in a scratch clone on the Owner's request and publish the resulting ledger as a PR, to start the treated count.

## Run complete
2026-11-07 — 0 users observed; the tool and skill step are in installed plugins (plugin 0.27.0), but the ledger is uncommitted, `update` has never run, and the treated count is 0 of 5 required; the bet is unmeasured.
