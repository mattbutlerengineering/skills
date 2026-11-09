---
stage: operate
run: feature:review-interface-pass
date: 2026-11-09
users-observed: 0
signal-source: "Scan of the Owner's agent session transcripts (Claude Code project directories and the omp session directory), 2026-11-05 06:06Z (the merge of #1155) to 2026-11-09T20:41Z, the newest event found: 351 transcript files touched in the window. 79 mention the review skill, none outside this repo's own checkouts read the Interface reference or reported an Interface pass; the 10 sessions that did touch it are all this repo's own work (pipeline runs, a retro and tests reading the skill), not a review of an adopter's UI diff. The pass logs nothing when it runs, so a use that left no trace here is not counted."
---

# Retro: An Interface domain pass for review

The release is four days old (merged 2026-11-05), so this retro reflects
days of use, not a steady state. The pass ships to adopters whose repos
have a UI; this repo has almost no UI files, and the Owner's transcripts
show no review of a UI diff. The count is 0 and every outcome below is
`unobserved`: state, not use. A scan limit is not a finding that nobody
used it.

## Outcomes vs. intent

### Success in one sentence: a review of a UI diff that deletes an `aria-label` reports it, a same-selector `outline` to `box-shadow` swap reports nothing, a diff with no UI path does not select the pass, the description is unchanged

- What happened: the state is shipped on main. `domain-reviewers.md` carries the Interface row (extension-only selection), `interface.md` holds the rules and three worked examples, `tests/test_review_domain_table.py` pins the row and the link, and the `description` is byte-identical. `verification.md` records 11 PASS, 0 FAIL, with the three fixture verdicts read by hand from the rules. No reviewer agent has been seen running the pass.
- Signal strength: unobserved. The hand-walk reads the rules; it is not a run (the brief forbade a paid run), and no adopter UI diff was reviewed in the window.

### The pass reads and reports on the diff only, and a diff with no UI path selects nothing

- What happened: pinned by the test (`test_selection_by_path`) and read in the reference; nothing about it has been seen in use.
- Signal strength: unobserved.

### False positives do not teach readers to skip the pass (the Idea's named risk)

- What happened: not measurable. `review.md` deferred a minor that `*.html` and `*.htm` select documentation pages; no review of one has been seen, so the rate is unknown.
- Signal strength: unobserved.

## Open debt

- #1154 — the run's own feature issue, filed by Ship before the merge and closed by it. Counts toward nothing.
- `review.md` Minor, `*.html`/`*.htm` select documentation pages: deferred, no issue filed; it is revisited when a real adopter diff shows the rate.
- `review.md` Minor, the pass is untested under a live reviewer agent; `verification.md` §Not verified names the same unknown. No eval case exists for the pass.

## Run retrospective

- Keep: the Idea's cheapest kill test (three hand-built diffs: a bare deletion, a same-selector swap, a different-selector swap) became the verification fixtures and the reference's worked examples unchanged, so the riskiest piece, the clearing rule, was walked before any code. The extension-only selection bound plus a pin test kept the row from drifting.
- Change: the run proved the rules only by reading them. A live reviewer's behavior on the three fixtures is the one thing the success sentence is about and the one thing never run; a later run should buy that check once, with an eval case.
- Stop: nothing identified. The run was one row, one reference and one test; no stage was skipped or backfilled.

## Environment

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| The PRD of a run with no tracker mirror failed `gates.py` detector O (seven sections cited by no breakdown row), found at Implement and fixed with seven hand-written `coverage-waiver` comments | `breakdown.md` §Notes, 2026-11-04 | mechanical | `gates.py` detector O, which already fired; it fired late and treats a run with no work orders as an error. The exemption belongs in the detector (first seed below) |
| The breakdown's Interface-row line linked `interface.md` relative to the run directory, which does not resolve; fixed to a code span | `breakdown.md` §Notes, 2026-11-04 | mechanical | `gates.py` detector I, which caught it |
| No eval case exists for the pass, so its behavior under a live reviewer is untested and stays an unknown | `verification.md` §Not verified; `review.md` §Minor, untested under a live reviewer | judgement | None fits as a rule: the gap is a missing measurement, carried by the second seed below |
| `*.html`/`*.htm` select docs pages and static sites; the cost is one quick read per such diff | `review.md` §Minor, `*.html` and `*.htm` | judgement | `skills/review/references/domain-reviewers.md` (the row's own bound), revisited only on a measured rate |

Both mechanical mistakes were caught by an existing detector in the
battery, so no new checker is owed; the finding is that the detectors ran
at Implement, after the PRD was written, not that nothing ran.

## Idea seeds

- Make `gates.py` detector O skip a run whose breakdown carries no work-order ids and records no tracker mirror, so a no-tracker run does not need seven hand-written waivers per PRD
- Add an eval case that runs `review` over the three Interface fixture diffs (bare `aria-label` deletion, same-selector `outline` to `box-shadow` swap, different-selector swap) and checks the three verdicts under a live reviewer, then run it once
- Re-scan Owner transcripts two weeks after 2026-11-09 for reviews that selected the Interface pass, counting selections, findings and any `*.html` selection that came back clean, so the false-positive minor gets a rate

## Run complete

2026-11-09. The seeds above are the input to the next Idea-stage run.
