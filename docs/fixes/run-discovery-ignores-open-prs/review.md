---
stage: review
run: maintenance:run-discovery-ignores-open-prs
date: 2026-08-25
assumptions:
  - "Scaled per the protocol's maintenance guidance. The change is prose plus one small checker, so the pass is lighter than a refactor's — but the prose IS the deliverable here, so it gets read as carefully as the code, and both findings below are about the code holding the prose up rather than about the prose itself."
  - "Severity: F1 is called major rather than critical because the wrong state it permits is a stale cross-reference, not a wrong build or lost work. A human may reasonably raise it — nothing downstream depends on the call."
---

# Review: ask before starting

## Scope

The run's own diff, `683af4f..f5c561a`, against `origin/main` at 622e7c0.
Nothing else in the tree.

```
 docs/backlog.md              |  2 +-
 docs/pipeline-protocol.md    | 34 ++++
 lint.py                      | 40 ++++
 skills/capture/SKILL.md      | 21 ++-
 skills/idea/SKILL.md         | 16 +-
 tests/test_lint.py           | 96 ++++++++-
```

plus this run's six artifacts. Nothing mirrored, so no manifest —
confirmed against `factory_init.MIRRORS` rather than assumed.

Three passes. The second produced both findings; both are fixed at the
tip, and are recorded here as found rather than as if the diff had always
read this way.

## Findings

### Major — the pin bound the skills to the constant and the constant to nothing

- **Scenario.** Someone renames or deletes `### Work already in flight`
  from `docs/pipeline-protocol.md` — reorganising the doc, folding the
  section elsewhere, or removing it deliberately. `check_skill_recitals`
  still passes, because it compares the two skills against
  `lint.IN_FLIGHT_HEADING`, which is unchanged. `check_protocol` still
  passes, because it only asserted the file exists. `lint: 0 problem(s)`,
  the full battery green — and `capture` step 3 and `idea` step 3 both
  send their reader to a section of the protocol that is no longer there.

  This is the run's own defect one level down. The whole change exists
  because a rule had no owner at one moment; the mechanism built to
  enforce it had no owner for half of its own coupling.

- **Decision: fixed** (I5, `1aa6513`). `check_protocol` now asserts the
  doc still states the heading, reported as
  `docs/pipeline-protocol.md no longer states 'Work already in flight',
  which capture and idea both recite`. Placed there, not in the recital
  pin, because it is a fact about the doc and the doc's checker is that
  one — the two halves stay separately owned.

- **Verified by mutation, not by argument.** With `check_protocol`
  reverted to its one-line form the new case fails against `- []`; with
  the check restored it passes. A test that is green before and after the
  change it supposedly pins is not evidence, and this repo has said so
  three runs running.

### Minor — the wrap-insensitive comparison was written twice

- **Scenario.** No wrong behaviour today; a maintainability claim, stated
  as one. The rule "a statement still counts when it wraps" appeared in
  `_in_flight_problems` and again inside `check_protocol`, four hours
  after this repo shipped a run whose entire subject was a fact with two
  owners. The two would drift the way two copies do: someone tightening
  one comparison — to require the heading at a line start, say — leaves
  the other answering a different question under the same name.
- **Decision: fixed** (`f5c561a`). Folded into `_states(text, phrase)`,
  a private helper with two call sites in one module. The seam bar in
  CLAUDE.md governs new shared *modules* and does not apply; nor does the
  ADR bar, since this is reversible in one commit.

## Passes with no findings

- **Correctness.** `RUN_STARTING` is derived — `(STAGES[0],
  *MAINTENANCE_STAGES)` — so it cannot become a second list of which
  stages start a run; and because `STAGES[0]` *is* the head of the spine,
  a future reordering carries the pin with it rather than stranding it.
  No double-fire: `capture` is absent from `STAGE_ARTIFACTS` and `idea`
  from `MAINTENANCE_STAGES`, so each skill is reached by exactly one loop
  — confirmed by the I2 output showing exactly one problem per skill, not
  two.
- **Design.** Every decision in `architecture.md` survived contact: the
  protocol owns the rule (D1), no tool and no tracker CLI entered a skill
  body (D2), `next` is untouched (D3), the pin extended
  `check_skill_recitals` rather than adding a top-level checker and
  touching `main()` (D4), `work-queue`'s preflight line is untouched and
  the new section names the relationship instead (D5), and the protocol
  says stop rather than warn (D6). The two deviations — whitespace
  normalization and I5 — are logged in `breakdown.md` Notes with the
  reasoning, not folded in silently.
- **Security.** No secrets, no new subprocess, no new external call
  anywhere in the diff. The skills instruct an agent to list work awaiting
  review, but deliberately do not name the command — that is packaging's,
  by the protocol's own rule — so this change adds no injection surface
  and no new credential requirement. `check_protocol`'s new
  `read_text(encoding="utf-8")` can raise on a non-UTF-8 protocol doc
  rather than returning a problem string; every other checker in the
  module reads the same way, so this matches the file's existing posture
  rather than introducing a new failure mode.
- **Conflict surface**, this run's own subject applied to itself: of the
  six files it touches, four are claimed by no open PR. `lint.py` and
  `tests/test_lint.py` are claimed by #324, whose hunks sit at lines
  17/33–82/543–586 and 70/531+ — measured with `gh pr diff`, not guessed.
  The overlap is textual distance rather than the same code.

## Observations, not findings

- **The pin cannot prove obedience** and does not claim to. Its docstring
  says so, and `verification.md`'s "what was NOT verified" says so again.
  Worth repeating here because a green lint line is exactly the kind of
  thing that gets read as "the rule is working".
- **Four pre-existing over-length lines** (`lint.py:533`,
  `tests/test_lint.py:638/651/652/772`) remain non-conforming. Verified
  pre-existing against `origin/main`. Flagged, not fixed — adjacent smells
  are logged, and fixing them here would put unrelated churn in a diff
  whose whole point is that unrelated churn is expensive right now.
- **`capture`'s recital does not appear in a plain `grep`** for the
  heading, because it wraps. That is not a defect — it is the reason
  `_states` exists — but it will surprise the next person who greps for
  who recites what.

## Verdict

**Ready to ship.** No unfixed critical or major findings: F1 is fixed and
re-verified (C7), F2 is fixed, and the battery is green at the tip —
`1349 tests OK`, `lint: 0 problem(s) across 24 skills`,
`gates: 0 problem(s)`, `selftest: ok`, with `one_owner` unchanged against
`origin/main` at 9 groups, none added and none removed.

Ship prepares and stops per the brief. ADR-0036 clause 2 independently
forbids the author merging, and both findings above were found by the
author.
