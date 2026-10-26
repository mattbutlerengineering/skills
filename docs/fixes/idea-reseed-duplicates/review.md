---
stage: review
run: maintenance:idea-reseed-duplicates
date: 2026-10-25
---

# Review: re-running Idea on a run appends its seeds twice

## Scope

`git diff origin/main...fix/idea-reseed-duplicates` at `dc6b734`: three
lines of `skills/idea/SKILL.md` step 4, one case in
`tests/test_idea_ambition_ladder.py`, and the run's `defect.md` and
`verification.md`. A patch-scale change to skill prose, so the review ran
inline by the author (the protocol's Run scale section), read against the
protocol's seed-backlog section. The fix landed in `c4f477b`; on it the
full checks printed `tests: 3936 tests across 124 modules ... 0
problem(s)`, `lint: 0 problem(s) across 35 skills`, `drift: 0
problem(s)`, `gates: 0 problem(s)`, `selftest: ok`.

## Findings

### Major: the check missed a seed another run had already claimed

- Scenario: a Moonshot seeded by this run is later claimed by another
  run, so its line becomes `- <text> (from: <run-ref>) (claimed:
  <other-ref>)`. The first wording read only lines "ending" in `(from:
  <run-ref>)`, which that line no longer does, so a re-run would append
  the Moonshot again.
- Standard: none
- Decision: fixed in `c4f477b`. The skill reads every line "carrying"
  the run-ref, "claimed or not", and the test pins that wording.

### Minor: a re-run that picks a larger rung leaves the old seed in place

- Scenario: the first pass picks Solid and seeds the Showstopper; a
  re-run picks the Showstopper. Its seed line stays in the backlog.
- Standard: none
- Decision: deferred. The protocol forbids producers rewriting a line,
  and the stale seed is advisory noise `next` lists, never state. Removing
  it is an Owner edit; this run only stops new duplicates.

## Passes with no findings

- Correctness: the rule adds a read before the append and changes no
  form, so every existing seed test still passes. Idea already reads the
  backlog as a consumer (claiming a seed), so the protocol's "no other
  skill reads the backlog" holds.
- Security: none; prose only.
- Complexity: one sentence, no tool, no `lean:` marker.
- ADR compliance: ADR-0029 (advisory seed inbox, append only) holds; no
  new ADR is owed.
- Domain passes: none selected.
- Standards: no matching statement.

## Verdict

Ready to ship. No critical finding. One major fixed in `c4f477b`, one
minor deferred with its reason. Criterion 3 of verification.md (a live
re-run) stays NOT RUN.
