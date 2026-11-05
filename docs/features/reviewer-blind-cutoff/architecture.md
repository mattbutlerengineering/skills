---
stage: architect
run: feature:reviewer-blind-cutoff
date: 2026-11-04
ux: skipped — skill text and, where named, a stdlib check; no screen or flow
assumptions:
  - "Interview answers came from autorun-brief.md and prd.md, not a live interview. The brief names no design trade-off, so the three below were decided from the codebase and are recorded here, not asked."
  - "The threshold's one owner is a new root-only module, reviewer_verdict.py, following fast_path.py's precedent (ADR-0096, ADR-0097): a hook the queue profile names, a pure function tests call, a pin test. The PRD left the home to this stage; the brief names one_owner.py only as the checker."
  - "The skill's default when the profile has no `verdict` hook is fail-closed (record `error`, no merge). The skill offers no named default for this; fail-closed is the existing 'errors are not passes' rule and the `fast-path` hook's own default shape. Evidence that this repo is the only consumer: a search of the tree finds one queue profile, `.claude/implement-queue.md`. Consumers elsewhere are not visible from here."
  - "Scores are accepted as any finite number from 0 to 10 and pass at 7 or more, so 6.5 flags. The rubric is written in whole numbers; the old rule left a fractional score to the reviewer's own verdict. Nothing in the brief says fractions are errors."
  - "The rubric bands are kept as written (decision below). The PRD allowed either; the reason is recorded in Decisions & alternatives."
  - "The specialist reviewers' `pass`/`block` output is unchanged. The reader search found no shared field: specialists return no score, and the PRD's open question to the Owner does not arise."
  - "conductor_flow.record_verdict and the ledger's `verdict` field belong to Conductor's own review step (`pass` or `changes`), a different reviewer from implement-queue's; unaffected."
  - "ADR-0123 is written, provisional, next free number on this branch."
---

# Architecture: Withhold the pass cutoff from the implement-queue reviewer

## Approach

Split the decision from the judgement. The reviewer keeps the judgement:
it returns a 0 to 10 score, issues and an assessment, and is handed no
line. A new root-only module, `reviewer_verdict.py`, holds the one pass
threshold and turns a score into `pass`, `flag` or `error`; the
orchestrator reaches it through a `verdict` hook in the queue profile,
exactly as it reaches `fast_path.py` through the `fast-path` hook. The
same module renders the first line of every verdict comment, which
carries the score, so the comment format has one owner as well. The
threshold value (7) and the rubric scale do not change.

The shape that lost: state the cutoff in the orchestrator's `SKILL.md`
prose and have the orchestrator compare. It needs no new file, but
skill text cannot be called with scores 0 to 10 (PRD criterion 4), and
any test that pinned it would hold a second copy of the number.

## Components

### reviewer_verdict.py (new, root-only, stdlib only)

- Responsibility: the pass threshold, the score-to-verdict rule, and
  the verdict comment's first line. Nothing else; it makes no git,
  network or model call.
- Collaborators: none imported. Called by the queue profile's `verdict`
  hook; read by `tests/test_reviewer_verdict.py`.

### Reviewer contract (`skills/implement-queue/references/reviewer-contract.md`)

- Responsibility: what the reviewer is handed and what it returns. After
  this change it names no threshold and asks for `score`, `issues`,
  `assessment` only.
- Collaborators: the orchestrator (reads the output); the data-rule and
  no-cutoff pin tests.

### Orchestrator wording (`skills/implement-queue/SKILL.md`)

- Responsibility: the gate's step 5 and the hooks table. A `verdict`
  hook row is added; step 5 runs it on the reviewer's score and acts on
  its result only; the verdict comment starts with the line the hook
  printed.
- Collaborators: the reviewer contract (retry table counts derived
  flags); the queue profile.

### This repo's queue profile (`.claude/implement-queue.md`)

- Responsibility: names the `verdict` hook's command, as it names
  `fast-path`.
- Collaborators: `reviewer_verdict.py`.

### Routine protocols (`docs/factory/merge-train-routine.md`, `docs/factory/hourly-improvement-routine.md`)

- Responsibility: say a flag is the derived one, and that the gate line
  they post carries the score.
- Collaborators: the orchestrator wording they point to.

### Tests (`tests/test_reviewer_verdict.py`, plus a pin in the existing reviewer-contract tests)

- Responsibility: pin the derivation over 0 to 10 and its error cases;
  pin that the reviewer-facing contract states no cutoff and that no
  skill or routine doc keeps the old "7 or more passes" wording.
- Collaborators: `reviewer_verdict.py`, the files they read.

## Data model

No stored data. Two values cross between components:

- `score`: a finite number, 0 to 10 inclusive.
- `verdict`: `pass` (score >= `PASS_AT`), `flag` (below), or `error`
  (no usable score).

`PASS_AT = 7` is the only place the value is written. Access patterns:
one derivation per reviewed PR, on the orchestrator's session, and later
a read of posted comment lines by a future analyst. Consistency: the
comment is posted after the derivation, from the same call's output, so
the line cannot disagree with the verdict acted on.

## Interfaces & contracts

### `reviewer_verdict.derive(score)`

- Input: whatever the reviewer returned in `score`: a number, a numeric
  string, or nothing.
- Output: `("pass" | "flag", score)`, or `("error", reason)` as a
  `reviewer-verdict:`-prefixed problem string (AGENTS.md's
  problem-string contract).
- Failure modes: missing, not a number, NaN or infinite, below 0 or
  above 10, or a bool: all `error`, never `pass`. Pure and
  deterministic; no timeout, retry is safe.

### `python3 reviewer_verdict.py <score>` (the `verdict` hook)

- Input: the score as one argument.
- Output: one line on stdout and an exit code. `reviewer-verdict: pass
  (score 8/10)` exit 0; `reviewer-verdict: flag (score 5/10)` exit 1;
  `reviewer-verdict: error (<reason>)` exit 2. The orchestrator posts the
  line verbatim as the first line of the PR's verdict comment and acts on
  the exit code only.
- Failure modes: wrong argument count is exit 2 with the usage string.
  The orchestrator reads exit 2, a hook that did not run, or a missing
  hook as `error`: re-dispatch the reviewer once, then hold the PR for a
  human, under `merge: auto` no merge. A `verdict` the reviewer returned
  itself is ignored whichever way it points.

### Reviewer output (contract's Output table)

- Input: the reviewer's own packet, unchanged.
- Output: `score`, `issues`, `assessment`. No `verdict`. The contract's
  Scoring bands stay; the sentence naming where pass becomes flag goes.
- Failure modes: a reviewer that returns `verdict` anyway is ignored; one
  that returns no usable `score` is `error` by the rule above.

### Reader list (PRD criterion 8)

Found by search across `skills/`, `docs/`, `factory/`, root tools and
tests for `verdict`, `7 or more`, `6 or less` and `reviewer-contract`:

- `skills/implement-queue/references/reviewer-contract.md` lines 30, 31:
  updated (field and cutoff removed). Line 59 "voids the verdict":
  reworded to "voids the review".
- `skills/implement-queue/SKILL.md`: gate step 4 "invalid verdict" and
  step 5 "Verdict", and the report line near the merge denial:
  updated to the derived verdict.
- `docs/factory/merge-train-routine.md` §3 ("a `flag` or `block`"):
  updated to say the flag is derived.
- `docs/factory/hourly-improvement-routine.md` step 4 and the journal's
  `Gate:` line: updated; the journal line carries the score.
- `docs/research/desloppify-2026-10-31.md` line 98-100 and
  `docs/backlog.md` lines 137, 161: record the old state or seeds;
  unchanged, they are history.
- `conductor.py`, `conductor_flow.py`: unaffected, Conductor's own
  review step, a different reviewer and a different value set.
- No Python tool or test reads the implement-queue reviewer's output or
  the verdict comment today: none is changed for that reason.

## Stack & dependencies

- Python 3 standard library only — `stdlib-only` standard.
- Root-only, not mirrored into the payload — ADR-0060's rule: mirrored
  iff a payload tool imports it, and none does. It imports nothing, so
  `tests/test_dual_membership.py`'s pinned set does not move.
- No new third-party or model dependency.

## Decisions & alternatives

- **Threshold and comment-line format owned by `reviewer_verdict.py`**
  over the cutoff in `SKILL.md` prose — a function can be tested over
  0 to 10 before it is written, and a test that pinned prose would hold
  a second copy of the value; `stdlib-only` holds. ADR-0123.
- **Fail closed when the profile has no `verdict` hook** over keeping a
  prose fallback with the number — a fallback is the second owner the
  PRD forbids. Cost: a consumer with `merge: auto` and no hook stops
  merging until it adds one. ADR-0123.
- **Rubric bands kept as written** over rewriting them to hide the
  6-to-7 step. The bands describe a defect, not a disposition ("minor
  nits only", "a non-trivial issue"), and the reviewer must judge that
  distinction to score at all. Blurring or merging the bands would move
  the rubric's scale, which is out of scope, and would change scores,
  not only the leak. The residue is accepted and stated: a reviewer can
  still guess that the line sits near the step from "minor" to
  "non-trivial". Posting the scores is what makes that measurable; the
  clustering check is a seeded follow-up. The "caps it at 6" example in
  the Missing-criteria rule names a score, not the line, and stays.
- **`error` for a fractional or out-of-range score is not chosen;
  fractions are accepted** — any finite number in 0 to 10 derives, and
  6.5 flags, so a decimal score does not cost a re-dispatch.
- **Specialist `pass`/`block` unchanged** over giving them scores — they
  return no score, and the PRD excludes them.
- **No profile key for the threshold** over a configurable
  `pass_score` — the brief puts changing the threshold out of scope, and
  a key invites a per-repo value.

Accepted behaviour changes, from running the old rule (the reviewer's own
`verdict`) and the new one (`derive(score)`) over the inputs where they
differ:

- Reviewer says `pass` with score 0 to 6: old merges, new `flag`.
- Reviewer says `flag` with score 7 to 10: old `flag`, new `pass`.
- Reviewer returns `pass` with no score, or a non-numeric or
  out-of-range score: old merges, new `error` and no merge.
- Reviewer returns a score and no `verdict`: old an invalid output, new
  derived normally.
- Score 6.5: old whatever the reviewer said, new `flag`.
- Specialists, the error/timeout rule, the retry table and the
  hold-label and gate-path rules: no input differs.

## ADRs

- [ADR-0123](../../adr/0123-the-orchestrator-derives-the-reviewer-verdict-from-the-score.md)
  — provisional. It passes all three legs: hard to reverse (a posted
  comment format and a hook name that a later analyst and every consumer
  profile depend on), surprising without context (a vended skill that
  states no threshold and runs a repo tool), a real trade-off (testable
  single owner against self-contained skill text, with the fail-closed
  cost named). The remaining decisions above fail a leg and keep only
  their one-line record.

## PRD traceability

| PRD criterion | Component |
|---|---|
| 1 no threshold in reviewer-facing text | Reviewer contract; no-cutoff pin test |
| 2 no `verdict` requested | Reviewer contract |
| 3 one threshold, unchanged value | `reviewer_verdict.py` |
| 4 testable derivation, test first | `reviewer_verdict.py`; `tests/test_reviewer_verdict.py` |
| 5 unusable score is `error` | `reviewer_verdict.derive`; orchestrator wording |
| 6 reviewer's own `verdict` ignored | Orchestrator wording; contract |
| 7 score and verdict in every comment | `reviewer_verdict.py` comment line; orchestrator and routine wording |
| 8 every reader listed and updated | Reader list above |
| 9 no stale "7 or more passes" | Orchestrator wording; routine protocols; pin test |
| 10 docs and routines updated | Routine protocols |
| 11 rubric decision recorded | Decisions & alternatives |
| 12 no `description` change | none touched |
| 13 battery, manifest regen if mirrored | Stack & dependencies (root-only, no regen owed) |
| 14 no paid run | none |
| 15 anchoring not claimed | all wording |
