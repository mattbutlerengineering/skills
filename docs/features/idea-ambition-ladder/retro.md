---
stage: operate
run: feature:idea-ambition-ladder
date: 2026-11-07
users-observed: 7
signal-source: "7 distinct post-release runs whose idea.md carries a `## Ambition rung` section, enumerated with `git log --diff-filter=A --since=2026-10-21 -- 'docs/features/*/idea.md' 'docs/fixes/*/idea.md'` plus a date-frontmatter sweep of every idea.md in /tmp/dc-retro and `grep -l '^## Ambition rung' docs/features/*/idea.md` (7 hits after excluding this run's own): eval-trends, house-voice, svg-mechanical-check, review-interface-pass, polish-blockers-and-patterns, reviewer-blind-cutoff, assembly-line. These are runs, not 7 people: all are the same Owner's autorun pipeline, and only one (assembly-line) records a human pick. No live-console idea.md exists on origin/main (the feat/live-console-idea branch is unmerged). Also read: plugin-evals/records/2026-10-26.json and 2026-10-26-3.json, issues #994/#1064/#1118, docs/fixes/idea-reseed-duplicates and idea-keeps-the-coined-phrase, docs/backlog.md `from:` lines. The run's own debt (#1064) is not counted as feedback."
---

# Retro: An ambition ladder for the Idea stage

## Outcomes vs. intent

Table behind the sections below. Source: each idea.md's `## Ambition rung` section, read 2026-11-07. "Seeded" = a `from: feature:<slug>` line in docs/backlog.md and the commit that added it (`git log -S`).

| Run (idea.md date) | Chosen | How picked | Four tests | Not-taken rungs seeded to backlog |
|---|---|---|---|---|
| eval-trends (2026-10-21) | Showstopper | default, "brief silent" | all pass | Moonshot, backlog line 133, in the run's own PR 7fea67b |
| house-voice (2026-10-25) | Showstopper | default, "brief silent" | all pass | **No.** Moonshot carried in idea.md "Not taken"; line 173 appeared only on 2026-11-07 (3e3e8aa, Operate) |
| polish-blockers-and-patterns (2026-11-04) | Showstopper | default, "brief is silent" | pass; test 3 "pass, thinly" | Moonshot, line 165, in b2a2a7c |
| review-interface-pass (2026-11-04) | Showstopper | default, "brief names no pick" | pass, answered from the brief, "not from a run on a real UI diff" | Moonshot, line 166, in c056de7 |
| reviewer-blind-cutoff (2026-11-04) | **Solid** | Showstopper tried, failed test 2 twice, demoted | n/a after demotion | Showstopper and Moonshot, lines 163, 164, in e63f7fb |
| svg-mechanical-check (2026-11-04) | Showstopper | default, "no pick and no ladder answer" | all pass | Moonshot, line 161, in bf406db |
| assembly-line (2026-11-05) | Showstopper | **asked**: "Owner picked Showstopper" | all pass, timing caveat recorded | Moonshot, line 167, in 9804284 |

Live tally: `grep -l '^## Ambition rung' docs/features/*/idea.md | wc -l` -> `7`. `grep -c 'Chosen: Showstopper'` -> 1 in six files, 0 in reviewer-blind-cutoff. No fix-run idea.md exists (docs/fixes/*/idea.md: no match); fixes start at capture.

### Idea briefs come out memorable as well as achievable (the Success sentence, issue #994)
- What happened: the section exists in 7 of 7 post-release feature briefs, so the step fires. Whether the briefs are more memorable is unmeasured: no reader or demo of any of them has been compared with a pre-ladder brief. The paid with/without suite (`plugin-evals/records/2026-10-26.json`, `ladder-brief`, 1 case) measured the harness side only: `overallScore 0.9`, `overallPassRate 0`, `meanDelta 0.6`, casesPassed 0 of 1. After the fixes in #1119/#1124 the re-run (`2026-10-26-3.json`) shows `overallPassRate 0.667`, casesPassed 0 of 1.
- Signal strength: pattern (existence); unobserved (memorability)

### The ladder is a choice, not a ritual (PRD: the user picks; Showstopper is the recommended default)
- What happened: 1 of 7 runs recorded a human pick (assembly-line, "asked as one question"). 5 took the default silently and wrote "brief silent" / "names no pick" into assumptions. 1 (reviewer-blind-cutoff) landed on Solid through the demotion rule. In 6 of 6 Showstopper runs every test is recorded "pass", one of them "pass, thinly" (polish, test 3) and one (review-interface-pass) answered "from the brief's Idea inputs, not from a run on a real UI diff". The only failure on record was caught by the demotion rule, which means the rule can bite. Verdict on the question: mostly rubber-stamping. In autorun the ladder asks nobody, the default always wins, and the tests are self-graded by the writer of the brief. The one demotion is the single piece of evidence the tests discriminate.
- Signal strength: pattern (7 runs, same Owner, same autorun path)

### The Moonshot is always seeded, never chosen (PRD item 4, ADR-0029 grammar)
- What happened: 6 of 7 runs seeded their unchosen larger rungs to docs/backlog.md; 5 did so inside the run's own PR. house-voice did not: its idea.md says the stage "commits only idea.md by instruction, so the seed text is carried in the Not taken line", and the backlog line arrived 2026-11-07, 13 days later, from Operate. eval-trends hit the same instruction on 10-21 but its PR still landed the seed. No run seeded Solid, as designed. No run chose the Moonshot.
- Signal strength: pattern

### The 30-second demo reaches launch-demo through the PRD (PRD item 5)
- What happened: unobserved. This retro did not check any of the 7 PRDs for a "the demo runs as written" criterion or a launch brief; house-voice and this run's release.md both record "Launch brief not produced". Not claimed.
- Signal strength: unobserved

### The ladder improves briefs or shipped features (verification.md "Not verified")
- What happened: unmeasured. No A/B of briefs exists. The only measured delta is the harness's `meanDelta 0.6` on one synthetic case, which says the plugin arm scores higher than the without arm on that case, nothing about adoption or quality.
- Signal strength: measured (harness, n=1 case); unobserved (briefs, features)

## Open debt

The run's own items, listed, counted toward nothing:
- Issue #1064 (CLOSED 2026-10-26) took the four review deferrals. Status of each, from the repo: duplicate seeds on re-run fixed (#1119, docs/fixes/idea-reseed-duplicates); coined-phrase loss found by the first paid run fixed (#1118, #1124). Still open by text in review.md and not seen resolved: the unconditional "Showstopper (recommended)" for tiny features; unspecified test lines and spike section on a Solid pick or declined ladder (reviewer-blind-cutoff hit exactly this branch and wrote "n/a after demotion" free-form); naming the riskiest piece beside "No solution design here"; phrase pins cannot catch contradictory prose.
- release.md Owner step 2 (wave chore(release) PR bumping plugin.json): done as #1053, CLOSED.
- release.md Owner step 3 (authorize `claude plugin eval . --tag idea`, cap 15 dollars): done, two records dated 2026-10-26 (cost $1.86 and $1.16). No LEDGER row was checked here.
- The idea.md assumption "autorun commits only idea.md" collides with the seed rule (house-voice never seeded). Not filed as an issue.
- Launch brief: not produced (release.md; `launch_demo.py config` said SHIP).
- AGENTS.md line 103 still says the decompose harness "has never been run"; `plugin-evals/records/2026-10-26-2.json` (tagFilters ["decompose"], startedAt 2026-10-26T02:55Z, costUsd 1.433, case csv-export-cut, `meanDelta 0.278`) says otherwise. That sentence is this cluster's stale doc, not this run's.

## Run retrospective

- Keep: the demotion rule (fail test 4 -> Solid, tell the user, seed the demoted rung). It fired for real once (reviewer-blind-cutoff) and produced a sensible brief. Keep the Moonshot-is-always-seeded rule: 6 of 7 runs followed it. Keep the mutant-sweep review that found the backlog newline corruption and the silent-pick major before any user saw it.
- Change: the autorun path needs an explicit instruction on seeding. 1 of 7 runs followed "commit only idea.md" and dropped the seed. Make the ladder step say the seed is written regardless, or say where it is carried and who writes it. The tests need an outside reader: every pass was written by the author of the brief, so a pass says little. Ask for the evidence clause (a number, a file, a command) rather than the word "pass". The review.md deferral about the Solid path was accurate, and a later run hit it; do not defer judgement of a path the pipeline will walk the next week.
- Stop: calling a section present in 7 of 7 briefs a success. Presence is the cheapest signal and this run's own tests pin only that the text asks. Stop letting "brief silent -> Showstopper" be logged as a decision; it is the absence of one.

## Environment

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| Demotion replaced the user's pick without telling them; no rule on seeding the demoted rung | review.md Major 1, fixed 87d1f3a | judgement | the review skill's pass (read skill text top to bottom as an agent would) |
| Append to a backlog without a trailing newline glues the seed onto the last line | review.md Major 2, fixed 87d1f3a | mechanical | tests/test_idea_ambition_ladder.py (pinned) |
| Prompts that feed the tests came after the tests | review.md Minor, fixed c888ca8 | judgement | the review skill's pass; the order test already added |
| Ten load-bearing branches unpinned (mutants survived) | review.md Minor, fixed f40745f | mechanical | tests/test_idea_ambition_ladder.py |
| Test phrase carried a wrong-case string | review.md, eaa784b follow-up; verification.md mutation FAIL lines | mechanical | tests/test_idea_ambition_ladder.py |
| Scope tests diffed against local `main`, which trails the branch base, and reported other runs' skills/decompose change | breakdown.md Notes, Deviation (S9, S11) | mechanical | tests/test_idea_ambition_ladder.py (now diffs against merge-base with origin/main) |
| Re-running Idea appends the seeds a second time | review.md Minor deferral, #1064, then docs/fixes/idea-reseed-duplicates/defect.md | mechanical | tests/test_idea_ambition_ladder.py |
| The pitch's coined phrase never reaches the brief | #1118, docs/fixes/idea-keeps-the-coined-phrase/defect.md: 0 of 9 briefs kept it | mechanical | plugin-evals/idea/ladder-brief grader `keeps-users-words` (caught it) |
| Phrase pins cannot catch contradictory prose | review.md Minor, deferred | judgement | the review skill's pass |
| Autorun's "commit only idea.md" instruction drops the seed the skill requires | house-voice idea.md assumptions; backlog line 173 added 2026-11-07 | judgement | the review skill's pass over an autorun brief against skills/idea/SKILL.md; no existing deterministic check names a seed-vs-brief conflict |
| Tests self-graded "pass" with nobody outside the author reading them | 6 of 6 Showstopper briefs all pass; review-interface-pass answered from the brief | judgement | the review skill's pass (read the evidence clause of each test line) |

## Idea seeds

- Ladder evidence clause: make the four test lines carry a command, file, or count each, so a reader can spot an asserted "pass" (6 of 6 Showstopper runs recorded all-pass).
- Seed-on-autorun: have the ladder step name who writes the seed when a stage "commits only idea.md" (house-voice's Moonshot sat unseeded 13 days).
- Ladder retrospective count: a free offline tool that counts `## Ambition rung` sections, chosen rung and default-vs-asked per idea.md, so "chosen or rubber-stamped" is a command and not a hand tally.
- Solid-path template: specify the four test lines, spike and demo for a Solid or demoted pick (reviewer-blind-cutoff wrote "n/a after demotion" free-form).
- Ladder A/B on briefs: compare a ladder brief with a pre-ladder brief of the same size for how memorable the demo is, before trusting `meanDelta 0.6` from one synthetic case.

## Run complete

2026-11-07 — the ladder fires (7 of 7 post-release briefs), but only 1 pick was a human's and 6 of 7 chose the default; whether it makes briefs better is unmeasured.
