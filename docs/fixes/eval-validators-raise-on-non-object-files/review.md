---
stage: review
run: maintenance:eval-validators-raise-on-non-object-files
date: 2026-08-27
---

# Review: the eval validators report instead of raising

Scope: this run's diff — `eval_schema.py` and `tests/test_eval_schema.py`
— read as a skeptical non-author would, plus one deliberate pass for
instances of the same defect *outside* the diff.

**This pass is self-authored and does not satisfy ADR-0036 clause 2.** A
non-authoring reviewer must still re-execute the verification and record
it on the pull request before this merges.

## Findings

### 1. The review's own scan missed a second instance — major, fixed

The first pass for "same defect elsewhere" was an AST scan for functions
taking a `data`-shaped argument that call `.get` without an `isinstance`
nearby. It reported only the two functions already fixed.

`charter_replay.validate` has the identical defect and the scan did not
see it, because it never calls `.get` itself — it delegates to
`eval_schema.entries` and dies one frame later. Reading the function
found it.

**Failure scenario, and it is the worst one in this run:**
`charter_replay.validate("some string", ...)` returns `[]` — no problems
— so a corrupted charter case set reads as *valid*, and
`load_case_set` then raises `AttributeError` on `data.get("cases")`. A
validator reporting a clean bill of health on a broken file is a worse
outcome than the crash the run started from.

Fixed by guarding `load_case_set` rather than by editing the second
module — see `defect.md` Notes for why that boundary held.

The transferable lesson matches the previous run's finding 5: a
pattern-matching scan finds instances that look like the original, and
the instances that matter are the ones that look different.

### 2. `charter_replay.validate` called directly is still unguarded — minor, deferred

After the fix, the production path is safe: `load_cases` →
`load_case_set` → guard → validator. But called directly,
`charter_replay.validate(None, ...)` still raises `TypeError`, and
`validate("version", ...)` still returns zero problems.

**Deferred, with the reason recorded rather than shrugged at:** the brief
scoped `charter_replay.py` out, and no production caller reaches its
validator except through the now-guarded loader. Fixing it would also
mean editing `tests/test_charter_replay.py`, which this session's other
open branch (`agent/pid-alive-answers-the-wrong-question`) already
modifies in the same region — creating a conflict between two unmerged
branches the user must review, which is exactly what the current hold
exists to avoid.

It is a real defect and it stays a real defect. It belongs in a follow-up
run, not smuggled into this one.

### 3. `validate`'s own object guard is redundant on every production path — minor, accepted

Both production callers of `validate` (`lint.py:470` and
`trigger_eval.py:437`) reach it through `eval_schema.load` →
`load_case_set`, which now guards first. So `validate`'s guard can never
fire in production.

Accepted rather than removed. `validate` is a public function of a seam
module whose docstring states it returns problem strings; the guard is
what makes that true for a direct caller, and the module already has
direct callers in `validate_output` and `fixture_refs` — both of which
`lint.py:488-490` invokes on raw `json.loads` output with no loader in
between, so their guards are load-bearing, not redundant. Removing one
of three consistent guards to save a branch would make the seam less
uniform, not simpler.

### 4. `results_path` ignores an unknown harness for two of three kinds — not a finding here

`results_path` validates `harness` only when `kind == "trigger"`; for
`charter` and `output` an unknown value is silently dropped. Real, but
untouched by this diff and with no evidenced caller. Logged in
`defect.md` Notes rather than fixed, so a later run can pick it up.

## Verified, not assumed

- The claim that `charter_replay`'s path is fixed was **executed**, not
  reasoned: `charter_replay.load_cases` was driven against four corrupted
  files with `charter_replay.py` unmodified (`verification.md` §4). This
  costs nothing — loading a case set is not replaying one, so no model
  spend is involved.
- The claim that a validator is never handed a non-object is pinned by a
  test that records what the validator actually received, not by reading
  the control flow.
- The falsy values `0`, `False` and `""` are in the regression set
  specifically because a truthiness-based guard would pass them while an
  `isinstance` guard rejects them; the test would catch that mistake.

## Not reviewed

- Whether any file in the repo has ever actually held a non-object eval
  set. The defect is a reachable contract violation, not an incident.
- The rest of `eval_schema.py` — `results_path`'s suffix arithmetic, the
  `_RESULTS_LINK` grammar, `duplicate_id_problems`' sort key. Unchanged
  by this run and not examined beyond finding 4.
- Any module outside `eval_schema.py` and `charter_replay.py`. The
  same-defect sweep covered root `*.py`; `factory/`, `skills/` and
  `tests/` were not swept for it.
