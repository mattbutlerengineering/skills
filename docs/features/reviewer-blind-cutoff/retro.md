---
stage: operate
run: feature:reviewer-blind-cutoff
date: 2026-11-09
users-observed: 1
signal-source: "Two scans on 2026-11-09, window 2026-11-05T06:11Z (merge of #1159) to 2026-11-09T20:41Z. (1) The pull-request comments of this repository: 26 comments opening with the hook's verdict line, on 15 merged pull requests, all written by the Owner's account, so the one person observed is the Owner. (2) 5619 session transcripts (every .jsonl under the Claude Code projects directories of this machine's user and under the omp agent sessions directory): 0 sessions and 0 Bash calls running the verdict hook after the merge. The transcripts do not hold the sessions that wrote the comments, so the second scan counts nothing and says nothing about use."
---

# Retro: Withhold the pass cutoff from the implement-queue reviewer

## Read this first: days, not a settled outcome

#1159 merged on 2026-11-05 and this retro was written on 2026-11-09: four
days, one account, and every posted verdict comment dated 2026-11-09 (none
exists for 2026-11-05 to 2026-11-08). It reflects days of use by the Owner, not
a settled outcome. The soft gate's "let it breathe" offer is moot because the
Owner's queue has already produced real verdicts. What would change this
retro: a second week of posted scores, which lets the clustering check run on
a sample larger than 26 comments (15 pull requests), and any consumer repo
running the skill (none is visible from here).

## Population

Counts only; no comment text, command text, path or repository name is
recorded here.

| Measure | Count |
|---|---|
| People observed (the Owner's account) | 1 |
| Verdict-line comments after the merge (`reviewer-verdict: <pass\|flag\|error> (score N/10)` as first line) | 26 |
| Pull requests carrying at least one | 15, all merged |
| Distinct days with a comment | 1 (2026-11-09) |
| Verdicts `pass` / `flag` / `error` | 15 / 11 / 0 |
| Pull requests whose last verdict was `pass` | 15 of 15 |
| Pull requests with a `flag` before the `pass` (a second review) | 8 of 15 |
| Transcripts scanned | 5619 |
| Transcript sessions running the hook after the merge | 0 |
| Errors, complaints, or workarounds seen | 0 seen; neither scan reads either |

The newest transcript event is from the minute this stage started, so the
window is covered; the 0 transcript sessions are a limit of the scan (the
sessions that wrote the comments are not in the directories scanned), not a
finding that the hook went unused, since 26 comments show it ran. The one
transcript hit for the skill name is this Operate stage's own session and is
not counted.

## Outcomes vs. intent

### The reviewer prompt names no pass threshold (PRD criteria 1, 2, 6; idea's success sentence, first clause)

- What happened: state at release, and nothing about use. Verification grepped
  the contract, skill, routine docs and queue profile for the old wording and
  found none; the contract no longer asks for a `verdict`. Whether the live
  reviewer is blind is not shown: the reviewer can still open
  `reviewer_verdict.py` or the profile in its worktree (a recorded, deferred
  review finding), and no transcript of a reviewer session was reached.
- Signal strength: unobserved.

### The verdict is derived from the score in one place (PRD criteria 3, 4, 5)

- What happened: all 26 comments open with the hook's exact line, so the
  derived verdict is what the queue posted and, on these 15 pull requests,
  what it merged on (15 of 15 merged after a `pass`). The count of
  verdicts that came from a path other than the hook is not measured: no
  comment record says what a reviewer returned. An `error` verdict
  appeared 0 times, so the fail-closed path is exercised only by tests.
- Signal strength: anecdote (one account, one day).

### Every verdict comment carries the score (PRD criterion 7; success sentence, last clause)

- What happened: the 26 comments found carry the score. How many verdict
  comments the queue posted without the line is not measured, since a
  comment without it is not found by a search for it. The clustering check
  the sentence names (the seed "A stdlib check that reads the scores ...")
  is possible by hand now: scores 5 ×3, 6 ×8, 7 ×3, 8 ×7, 9 ×4, 10 ×1. The mode
  sits at 6, just under the line, not at 7; but a flag at 6 is followed by a
  pass at 7 to 9 in 8 of 15 pull requests, so the scores are not independent
  draws, there is no baseline from before the change, and nothing here says
  whether the reviewer anchors. The sentence's purpose ("so clustering can be
  checked") is met in state; the check itself has not run.
- Signal strength: anecdote (26 comments, 15 pull requests, one day, one
  account); not a pattern.

## Open debt

Issues this run itself filed or that cite its artifacts. None is feedback and
none counts toward the population.

- #1158 — the tracker issue Ship filed for the run, closed by #1159 on
  2026-11-05.
- Review's two deferred minors (the threshold stays readable from the
  worktree; a consumer repo with `merge: auto` and no `verdict` hook stops
  merging) filed no issue; they are carried as seeds below.
- #1686 — this Operate stage's own tracking issue, part of #1617.

## Run retrospective

Stages: Idea, PRD, Architect, Decompose, Implement, Verify, Review and Ship
ran in one unattended wave on 2026-11-04 with five parallel runs sharing the
machine; Ship prepared, #1159 merged on 2026-11-05.

- Keep: the ambition ladder's honesty. Showstopper failed test 2 twice, Solid
  was recorded, and the demoted rungs became the two backlog seeds the
  clustering and calibration ideas now stand on. Keep the Idea-stage kill test
  (do the rubric bands leak the line?): Architect answered it and recorded the
  reason for keeping them. Keep the independent final Review: it found the one
  real defect, a score pasted into a shell command with no quoting guard,
  that no earlier stage had looked at.
- Change: Implement should quote the failing run when a breakdown item is
  written test-first. PRD criterion 4 asked for "written before the code and
  fails first", the test and module landed in one commit, and Verify could
  mark only half of it. Release should leave one outcome in the artifact: the
  frontmatter says `released` while the Outcome section still reads "Prepared
  and stopped", which a reader of the body takes at face value.
- Stop: seven identical `coverage-waiver` comments, one under each `prd.md`
  section, to satisfy detector O when a run assigns no work-order ids; and
  breakdown assumptions about what a root module needs (the `factory.py`
  VERBS entry) written as prose when a test already knows.

## Environment

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| The reviewer's score, text from a model that read an untrusted diff, was to be filled into a shell line with no instruction to quote it or to check it is a number first | `review.md` §Major: security | judgement | `docs/standards.json`, a statement for the factory plane that text from an untrusted source reaches a shell only as one quoted argument after a shape check; it has no statement on this boundary today. A pin of the SKILL.md wording in `tests/test_reviewer_verdict.py` would hold this one instance |
| `derive(10 ** 400)` raised `OverflowError` instead of returning `error`; as a CLI the traceback exits 1, which reads as `flag` | `review.md` §Minor: correctness | mechanical | `tests/test_reviewer_verdict.py`, whose unusable-score cases now include it; a boundary-magnitude case in the first test list (huge ints, NaN, inf, bool) would have caught it before Review |
| Breakdown assumed no `factory.py` VERBS entry was owed; `tests/test_factory_cli.py` failed the root module with a `__main__` guard and no verb | `breakdown.md` Notes (Implement, point 1) | mechanical | `tests/test_factory_cli.py`, which caught it in Implement as designed; no new carrier |
| Detector O flagged every `prd.md` section as uncited because the run assigns no work-order ids, so seven identical waiver comments were added by hand | `breakdown.md` Notes (Implement, point 2); `prd.md` | mechanical | `gates.py` detector O: accept one run-level waiver when the brief's Tracker assigns no ids, instead of one comment per section |
| PRD criterion 4's "fails first" ordering is not shown: test and module share one commit and no failing run is quoted | `verification.md` §Criterion 4, §Not verified | mechanical | `gates.py`, a check on `breakdown.md`: an item marked test-first whose checked-off line quotes no failing run is a problem string |
| `release.md` frontmatter reads `outcome: released` while the Outcome section reads "Prepared and stopped" | `release.md` §Outcome | mechanical | `gates.py` release check, already seeded as "Check release.md write-back mechanically ..." (backlog, from `size-band-calibration`); no new seed |
| Reviewer can read the threshold in its worktree: `PASS_AT` in `reviewer_verdict.py` and the profile's `verdict` section | `review.md` §Minor: design (deferred) | judgement | `docs/adr/0123` Consequences names the residue; closing it moves the owner out of the checkout (a new ADR). The seed below measures first whether it is ever read |
| A consumer repo with `merge: auto` and no `verdict` hook stops merging, since `reviewer_verdict.py` is a root tool the skill does not vend | `review.md` §Minor: complexity (deferred) | judgement | `skills/implement-queue/SKILL.md` step 5 and its profile section; no check sees a consumer repo from here |

## Idea seeds

- Re-tally the posted `reviewer-verdict:` lines after 2026-11-23, recording the score histogram, how many pull requests got a flag before their pass (8 of 15 on 2026-11-09), the share of 6 against 7, until the clustering check exists (from: feature:reviewer-blind-cutoff)
- Let gates detector O accept one run-level waiver, set when the brief's Tracker assigns no work-order ids, in place of one coverage-waiver comment under each prd.md section (from: feature:reviewer-blind-cutoff)
- Add a gates check on breakdown.md that fails an item marked test-first when its checked-off line quotes no failing run, so criteria like "written before the code and fails first" can be verified (from: feature:reviewer-blind-cutoff)
- Add a docs/standards.json statement for the factory plane that text from an untrusted source reaches a shell only as one quoted argument after a shape check, and pin the implement-queue step-5 wording to it (from: feature:reviewer-blind-cutoff)
- Count how often implement-queue reviewer sessions open reviewer_verdict.py or the profile's verdict section in their worktree, before deciding whether PASS_AT should move outside the checkout under a new ADR (from: feature:reviewer-blind-cutoff)
- Decide how a consumer repo on merge: auto gets a verdict hook: vend reviewer_verdict.py with the implement-queue skill, or state the fail-closed result in the skill's setup text (from: feature:reviewer-blind-cutoff)

## Run complete

Closed 2026-11-09, four days after the merge, on one account's use. The seeds
above are the input to the next Idea-stage run; the first is the real
follow-up, since a sample of 26 comments on one day cannot say whether the
reviewer anchors.
