---
stage: prd
run: feature:reviewer-blind-cutoff
date: 2026-11-04
id: PRD-0016
ux: not-applicable
ux-reason: skill text and, where named, a stdlib check; no screen or flow
assumptions:
  - "Interview answers came from autorun-brief.md and idea.md, not a live interview; every section traces to the brief's Idea inputs, Scope, Constraints or User-facing surface sections, or to idea.md's Problem, Who has it, Evidence, Success and Unknowns sections."
  - "ux: not-applicable follows the brief's User-facing surface section, which reads the deliverable as skill text with no screen. Logged here as that section asks."
  - "Typed id PRD-0016 is the number the brief reserves for this run; this stage did not pick it."
  - "Idea.md chose the Solid rung and has no demo, so no 'the demo runs as written' criterion is written."
  - "The actor list (Owner, the two merging routines, the reviewer, the orchestrator) is taken from idea.md's Who has it and the brief's Origin section. Taken without user input."
  - "The rubric-bands question is left to Architect as an open question, as idea.md and the brief both leave it undecided; the criteria below hold whichever way it is settled."
  - "Criteria that name the threshold's single owner stay at the level of 'one place that the derivation and any check read'; which file or module is Architect's choice (the brief names one_owner.py as the checker, not the home)."
---

# PRD: Withhold the pass cutoff from the implement-queue reviewer

## Problem statement

<!-- coverage-waiver: the brief's Tracker section assigns no work-order ids, so no breakdown row can carry a PRD citation; the breakdown's Coverage table maps every Success criterion to its items -->

The Owner lets the implement-queue reviewer's verdict merge pull requests
unattended (`merge: auto` in `.claude/implement-queue.md`; ADR-0087,
ADR-0096). Today the reviewer is told where the line is ("7 or more
passes, 6 or less flags", `skills/implement-queue/references/reviewer-contract.md`
line 31) and returns its own `verdict`. A judge that knows the line can
score to it. The scores are never posted, so nobody can tell whether it
does: one reviewer score is findable in the last 150 PRs (PR #927,
"score 6"). The two routines that merge on this verdict,
`factory-merge-train` (every 4 hours) and `factory-hourly-improvement`
(hourly), trust it as returned.

This is prevention plus making the problem measurable. No anchoring
incident is on record, and nothing here claims one exists.

## Solution

<!-- coverage-waiver: the brief's Tracker section assigns no work-order ids, so no breakdown row can carry a PRD citation; the breakdown's Coverage table maps every Success criterion to its items -->

After this ships, the reviewer is given no pass threshold and returns a
score with its issues and assessment, not its own pass or flag. The
orchestrator derives pass or flag from the score against a threshold it
alone owns, in one place. Every verdict comment on a PR carries the
score as well as the verdict, so a later check can look for scores
clustering at the line. The threshold value and the 0 to 10 rubric scale
do not change.

## Actors

<!-- coverage-waiver: the brief's Tracker section assigns no work-order ids, so no breakdown row can carry a PRD citation; the breakdown's Coverage table maps every Success criterion to its items -->

- **Owner** — the person who set `merge: auto` and answers for what merges unattended.
- **Orchestrator** — the implement-queue skill's own session, which dispatches the reviewer, reads its output and posts the verdict comment.
- **Reviewer** — the distinct agent that scores a worker's diff against the issue's criteria.
- **Merging routine** — `factory-merge-train` and `factory-hourly-improvement`, which merge on the posted verdict.
- **Future analyst** — whoever later checks posted scores for clustering at the threshold (that check is out of scope here).

## User stories

<!-- coverage-waiver: the brief's Tracker section assigns no work-order ids, so no breakdown row can carry a PRD citation; the breakdown's Coverage table maps every Success criterion to its items -->

1. As the Owner, I want the reviewer's prompt to name no pass threshold, so that its score is not pulled toward a line it can see.
2. As the Owner, I want the orchestrator to derive pass or flag from the score in one place, so that the threshold has one owner and cannot drift between a skill and code.
3. As the Owner, I want every verdict comment to show the score, so that I can read for myself how a PR was judged.
4. As a future analyst, I want scores posted on every verdict comment, so that I can check across PRs whether they cluster at the threshold.
5. As a merging routine, I want the verdict I merge on to be the derived one, so that a reviewer's self-reported pass cannot reach `merge: auto`.
6. As the orchestrator, I want every place that reads the reviewer's `verdict` field found and updated, so that no reader breaks when the field moves.

## Success criteria

<!-- coverage-waiver: the brief's Tracker section assigns no work-order ids, so no breakdown row can carry a PRD citation; the breakdown's Coverage table maps every Success criterion to its items -->

- [ ] `skills/implement-queue/references/reviewer-contract.md`, and anything else the reviewer is handed, contains no pass or flag threshold: a search of the reviewer-facing text for "7 or more", "6 or less" and any other statement of the cutoff finds none.
- [ ] The reviewer's output contract no longer asks it for a `verdict` of `pass` or `flag`; it asks for a score, issues and assessment.
- [ ] The orchestrator derives `pass` or `flag` from the reviewer's `score` against one threshold, and the threshold's value appears in exactly one place that the derivation and any consistency check both read. The value is unchanged from today (a score of 7 or more passes, 6 or less flags).
- [ ] The derivation is testable: a test calls it with scores 0 through 10 and asserts that 7 to 10 give `pass` and 0 to 6 give `flag`; the test is written before the code and fails first.
- [ ] A reviewer output that carries no usable `score` (missing, not a number, outside 0 to 10) is recorded as `error`, never as `pass`, and under `merge: auto` does not merge, matching the existing rule that an error is not a pass.
- [ ] If a reviewer still returns its own `verdict`, the orchestrator ignores it for the merge decision; the derived verdict is the only one acted on.
- [ ] Every verdict comment the orchestrator posts on a PR includes the numeric score and the derived verdict, in a form a person can read without running anything.
- [ ] Every reader of the reviewer's `verdict` field is listed in the run's later artifacts, found by search across `skills/`, `docs/`, `factory/`, tools and tests, and each one is either updated to read the derived verdict or recorded as unaffected with the reason.
- [ ] The cutoff is not stated in `skills/implement-queue/SKILL.md`, the contract, or the routine docs in a form that contradicts the single owner: a search of those files for the old "7 or more passes" wording finds nothing stale.
- [ ] `docs/` and routine protocol text that stated the cutoff are updated to describe the derived verdict, or recorded as intentionally unchanged.
- [ ] The rubric bands in the contract (the Scoring table) are either rewritten so that they do not mark where pass becomes flag, or kept with a recorded reason; the decision and its reason are written in `architecture.md`. The rubric's scale (0 to 10) is unchanged either way.
- [ ] No frontmatter `description` of any skill changes. If one does, the routing eval is recorded NOT RUN with its exact command.
- [ ] The repo's battery passes from the worktree: `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`, `python3 gates.py && python3 gates.py --selftest`; and `python3 factory_init.py update-manifest` has been run after any edit under `factory/templates/**` or to a mirrored root file.
- [ ] No paid model run was made: no `claude plugin eval`, `trigger_eval.py`, `charter_replay.py` or `claude -p`. Any criterion that needs one is recorded NOT RUN with the exact command.
- [ ] Anchoring is not claimed to exist: no artifact in this run states that the reviewer anchors, only that the change makes it measurable.

## Out of scope

<!-- coverage-waiver: the brief's Tracker section assigns no work-order ids, so no breakdown row can carry a PRD citation; the breakdown's Coverage table maps every Success criterion to its items -->

- Changing the threshold value or the 0 to 10 rubric scale.
- The `review` pipeline stage and its reviewer (the data rule there shipped in #1141).
- A clustering-analysis tool that reads posted scores and flags scores just above the line (seeded in `docs/backlog.md`; worth building once scores exist).
- A calibration harness that scores labelled diffs blind on a schedule (seeded).
- Any live implement-queue run, and any measurement of whether anchoring happens today.
- Posting scores retroactively on PRs already merged.
- Specialist reviewers' `pass` or `block` output (contract line 35); the seed concerns the scored reviewer.
- Tracker work: no issue seeds the run and no work-order issues are mirrored.

## Open questions

<!-- coverage-waiver: the brief's Tracker section assigns no work-order ids, so no breakdown row can carry a PRD citation; the breakdown's Coverage table maps every Success criterion to its items -->

- Do the rubric bands (7 to 8 "minor nits only", 5 to 6 "a non-trivial issue") still imply the line once the number is withheld, and if so is it enough to rewrite them or should they stay? — Architect, reading the contract's Scoring table; the criteria above hold either way.
- Where does the single owner of the threshold live, and which checker (`one_owner.py` or another) pins it? — Architect.
- What exact form does the score take in the verdict comment, and does any parser, journal or routine doc read that comment today? — Architect, from the reader search the criteria require.
- Does the specialist reviewer's `block` path need the same treatment? — Owner, if the Architect's reader search shows it shares the field; this PRD excludes it.
