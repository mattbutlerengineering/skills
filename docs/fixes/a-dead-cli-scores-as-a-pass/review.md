---
stage: review
run: maintenance:a-dead-cli-scores-as-a-pass
date: 2026-08-28
assumptions: []
---

# Review — a dead CLI scores as a pass

Scope: the diff on `agent/a-dead-cli-scores-as-a-pass` against
`origin/main` — `charter_replay.py` (+40 lines, one docstring sentence
rewritten) and `tests/test_charter_replay.py` (+15 tests).

## Correctness

**1 (major, fixed during the run) — whitespace passed as text.** The
first `replay_problem` tested `not transcript.get("text")`, so a
transcript whose text was `"  \n"` counted as evidence and a forbid-only
case passed on it. Reachable: `_flush_block` appends any truthy buffer,
so a stream whose only text delta is blank produces exactly that.
Failure scenario: the CLI emits one empty text frame and dies, the
transcript reads `{"tool_calls": [], "text": " "}`, and the case scores
`pass: true` with nothing anywhere saying the replay failed — the same
hole the fix exists to close, one character narrower. Now
`(transcript.get("text") or "").strip()`, pinned by
`test_whitespace_is_not_text`.

**2 (minor, accepted) — the evidence problem is prepended, so
`failures[0]` changes meaning.** A transcript that both errored and
tripped a forbid now leads with the replay problem rather than the
expectation problem. Nothing reads `failures[0]` except
`test_forbidden_command_fails_and_names_the_expectation`, whose
transcript has no error, and `print_report` prints the whole list. The
order is deliberate: the reason there is no verdict should come before
the verdict-shaped lines.

**3 (minor, deferred) — the error is now printed twice.** For legs A and
B the report shows `replay: the run errored (...)` and then
`print_report`'s existing `error: ...` line. Deferred: suppressing the
second would change `print_report` for require-bearing cases too, which
is outside this fix, and the duplication is redundant rather than wrong
— the raw line carries the error unwrapped.

**4 (minor, deferred) — `failed` is empty on an evidence failure.** A
reader who only looks at `failed` sees a failure with no named
expectation. That is the honest answer (no expectation was evaluated
against a run that did not happen), `failures` carries the reason, and
`test_failed_still_means_expectation_ids_only` pins it so a later change
cannot quietly start putting non-expectation ids there. The degradation
tests read `failed`, and widening it would break what they assert.

## Design

**5 — the rule went into the pure seam, not the runners.** There are two
runners today (`claude_runner`, `recorded_runner`) and the test suite
supplies more as stubs. Marking empty transcripts inside each runner
would have put the same fact in three places — the duplication
`one_owner.py` exists to find — and left it out of the half CI covers.
`score_case` is the seam the module's own docstring says is pure and
CI-covered, and it is where a verdict is decided, so it is where the
question "is there anything to decide from?" belongs. `one_owner`
reports 9 problems, unchanged from `origin/main`, so no new duplicated
fact was introduced.

**6 — the docstring was corrected rather than left.** `claude_runner`
said an incomplete replay "fails its required expectations, which is the
honest verdict", which was true only of cases that have requires and was
part of why the hole survived. It now states the unconditional rule. No
other document describes the scoring contract; `evals/README.md` does not
mention charters, and WO-0016's breakdown note describes what CI covers,
which is unchanged.

**7 (deferred, for a human) — the validator still invites the shape.**
`_case_problems` requires a forbid and never a require. This run makes
that shape safe rather than illegal, which is the right order: banning it
would forbid a legitimate regression case written to a pure "Must never"
clause. Whether the validator should additionally require evidence-
producing expectations is a case-set design question, not a defect.

## Security

Nothing new. `replay_problem` adds no input surface: the error string it
interpolates is produced by this module's own runners, and it reaches
only stderr and `json.dumps`. No secrets, no subprocess, no path
handling.

## Not addressed

**8 — `cli.harness_run` never reads the child's exit status.** That is
what makes leg C possible: a `claude` that exits non-zero with no output
is indistinguishable from a model that did nothing, for every caller of
the harness seam, not just this one. This run does not touch it —
`cli.py` is the shared external-CLI seam (ADR-0039) with six callers per
ADR-0059, and changing what it reports is its own run with its own
blast radius. The fix here holds regardless of what the seam decides,
which is the argument for putting it in the scorer. Recorded as a
follow-up.

## Verdict

No unfixed critical or major findings. Finding 1 was found and fixed
inside the run; 2 and 5–6 are accepted as designed; 3, 4, 7 and 8 are
deferred with reasons.
