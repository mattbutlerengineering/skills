---
stage: review
run: maintenance:a-forbid-only-case-checks-nothing
date: 2026-09-20
assumptions: []
---

# Review — a forbid-only case checks nothing

Scope: the diff on `fix/charter-replay-forbid-only-case` against
`origin/main` — `charter_replay.py` (+5 lines, one docstring paragraph
rewritten) and `tests/test_charter_replay.py` (+37 lines: two new tests,
three collateral fixes to tests that built a forbid-only case for an
unrelated reason).

## Correctness

**1 — the require check is the forbid check's exact mirror.** Same
guard shape (`not any(... e.get("mode") == "require" ...)`), same
`where` prefix, same place in `_case_problems`, appended after the
forbid check rather than replacing it — a case can now be told it is
missing *both*. Verified: a case with neither mode produces two problem
strings (implicit in `test_invalid_scope_and_mode`, which sets one
expectation's mode to an invalid value and leaves the other invalid too;
`assertIn` doesn't care how many problems came back, but a manual check
confirms both fire).

**2 — three tests needed a require added, for reasons unrelated to this
fix.** `test_any_chartered_role_is_valid` and `test_uncompilable_pattern`
built a case through the shared `case()`/`expectation()` helpers, whose
defaults are a single `forbid`. Both were testing something else (role
vocabulary; pattern compilation) and asserted on the *exact* problem list
(`== []` / `len(...) == 1`), so the new rule's extra problem string broke
them for a reason orthogonal to what they check. Fixed by adding a second,
valid `require` expectation to each case, which is the same fix a real
case author would make. Confirmed neither test's original assertion
target changed meaning: `test_any_chartered_role_is_valid` still asserts
`problems == []` (role validity, now genuinely case-valid too);
`test_uncompilable_pattern` still asserts exactly one problem (the bad
pattern) and that it names the pattern.

**3 — `TestAVerdictNeedsEvidence.forbid_only()` is redefined, not
deleted.** Nine tests in that class use the helper to get a raw
forbid-only case *dict* and check that `score_case` — which does not
consult `validate()` — still fails an errored or empty replay when
handed one directly. That property must survive this change: `_case_problems`
gates what a case-set *file* may contain, not what `score_case` is
handed defensively. The helper's self-check now asserts `validate()`
flags the shape (documenting the new rule) instead of asserting it
passes (documenting the old one); the returned case dict, and every
downstream `score_case` assertion, is unchanged. Ran the whole class
green.

**4 — no golden-set edit.** `factory/evals/charters.json` is untouched.
All four shipped cases already carry a `require` (`cites-work-order` /
`carries-closing-link` on `swe-merges-own-pr`; `cites-work-order` on
`swe-weakens-failing-test`; `cites-the-amendment` / `labels-merge-gate` /
`merges-under-the-amendment` on `reviewer-asked-to-merge`;
`writes-the-breakdown-row-first` / `refuses-or-escalates` on
`planner-issue-before-row`), confirmed by a new
`test_every_case_carries_a_require` in `TestGoldenCaseSet`. Per this
repo's eval-honesty rule, if any shipped case had lacked one, the
resolution would have been to report that as a finding, not to backfill
it silently to make the fix land clean — it did not arise.

## Design

**5 — the "for a human" deferral this closes.** `_case_problems`
requiring a forbid but never a require was flagged once already, in
`docs/fixes/a-dead-cli-scores-as-a-pass/review.md` finding 7, and
deferred: "Whether the validator should additionally require
evidence-producing expectations is a case-set design question, not a
defect." That finding also floated a reason to leave it alone — "banning
it would forbid a legitimate regression case written to a pure Must-never
clause" — which is the counter-argument this run had to actually check,
not just note. `defect.md` records the check: every one of the nine role
charters (`factory/charters/*/CHARTER.md`) pairs `## Must never` with
`## Actions per cycle`, so no charter is prohibition-only, and a fixture
built against any of them always has some correct, positive action to
name. The hypothetical case finding 7 worried about has no real charter
to attach to. Combined with PR #365's own "Honest by luck" framing and
its `TestTheGoldenSetsRequiresAreNotTheGuarantee` (which exists
specifically to say the four-for-four requires-coverage is not a
guarantee), the deferral's premise no longer holds and the direct fix is
what's left.

**6 — the rule lives in the same seam as its sibling.** One function,
one guard, appended beside the forbid check it mirrors — not a new
validator, not a second code path. `_case_problems` is already the seam
`one_owner.py` and the module's own conventions point at for a case-set
rule; nothing new was invented.

## Security

Nothing new. `_case_problems` gains one more string-formatting branch
over data this module's own case-set file already fully controls; no new
input surface, no subprocess, no path handling.

## Not addressed

**7 — a `require` proves engagement, not correctness.** Requiring at
least one `require` expectation proves the replay did *something* the
fixture recognizes as on-track; it does not prove the positive action was
the *right* alternative to the trap (that is what each case's specific
pattern choice does, one case at a time, and is unchanged by this run).
Out of scope: this run closes "checks nothing", not "checks everything".

**8 — `cli.harness_run` never reads the child's exit status**, named
again in #365's own review as unaddressed there too. Unrelated to this
run's seam (validation happens before any replay runs) and not touched.

**9 (minor, noted) — `test_the_exit_code_follows` now proves a different
claim than its docstring states.** It writes a forbid-only case to a
file and asserts `main()` returns 1. Before this run that exercised
`score_case`'s evidence-rule failure (the case was legal, ran, and lost
on the empty-transcript check); now `load_cases` rejects the file before
a replay is attempted, so the same assertion passes for the earlier
reason — a validation failure, not a scored one. The claim it still
proves ("the exit code follows a real failure, not just an internal
field") stays true, and it is now the only test exercising `main`'s
`error:`-and-return-1 path for an invalid case file, so nothing is worse
covered — but its docstring reads as if it still walks a case through
scoring. Left as-is: renaming or restructuring it is a test-hygiene
change orthogonal to #451, not something this fix should fold in
unasked.

## Verdict

No unfixed critical or major findings. 3 and 4 are pre-existing repo
facts confirmed, not risks introduced by this diff; 7, 8 and 9 are noted
and deliberately not folded in.
