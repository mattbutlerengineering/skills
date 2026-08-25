---
stage: decompose
run: maintenance:a-blind-find-is-not-a-failed-agent
date: 2026-08-25
assumptions:
  - "No tracker mirror. This run implements no work order — intake #348 is a defect issue — so no item carries a (tracker: #NNN) reference and ADR-0032's dispatch mirror is untouched."
  - "I3 has no automated acceptance and says so. assembler.yml executes only on a real dispatch with secrets that are not minted, so the workflow condition is verified by reading it against GitHub's documented expression semantics, not by running it. Naming that here rather than inventing a test that would only assert the YAML text back to itself."
---

# Breakdown: the factory says whether it looked

## M1 — the tool states the fact

- [x] **I1** `Find` record; `pr_for_issue` carries `looked` — size:S, blocked by: —
      (architecture.md §Contracts, table rows 1-4)
      *Acceptance:* all four rows of the contract table hold, driven
      through `pr_for_issue` with the injected gh fake. In particular the
      truncated row answers `looked=False` and does **not** append the
      sentence blaming the agent.

- [x] **I2** the `find-pr` leg writes the `looked` output — size:S, blocked by: I1
      (architecture.md §Contracts, step outputs)
      *Acceptance:* driving `main(["find-pr", N])` with a real
      `$GITHUB_OUTPUT` file writes `looked=false` for an unreadable
      listing and `looked=true` for a readable one, in both cases
      alongside the existing `pr` line, and the exit code is unchanged
      from today in every case.

## M2 — the workflow acts on it

- [x] **I3** `assembler.yml`'s failure step gains the condition — size:S, blocked by: I2
      (architecture.md §Contracts, failure step)
      *Acceptance:* the `Mark the work order failed` step's `if:` carries
      `steps.find.outputs.looked != 'false'`. Verified by reading, not by
      running — see this artifact's second assumption. The `!=` form is
      required so an unset output still flips.

## M3 — the payload stays in lockstep

- [x] **I4** mirror and regenerate the manifest — size:S, blocked by: I3
      (CLAUDE.md §Factory templates are checksum-pinned)
      *Acceptance:* `python3 -B factory_init.py update-manifest` run and
      committed; `python3 gates.py` green and `tests/test_factory_init.py`
      passing. Both `assembler.py` and `assembler.yml` are mirrored, so
      three generated files move.

## Coverage check

Every component in `architecture.md §Components` appears: `pr_for_issue`
(I1), `main`'s find-pr leg (I2), the workflow (I3). Both rows of the
requirement-traceability table that this run fixes map to items; the
third row is marked not-fixed in the architecture and is carried into
`release.md` rather than decomposed.

## Notes

**2026-08-25 — I3 got an automated test after all.** This artifact's
second assumption said the workflow condition could only be verified by
reading, because `assembler.yml` runs only on a real dispatch. That was
half wrong: `TestValidatorDispatchLockstep` already pins workflow YAML by
reading the file in a test, which is this repo's established idiom for
exactly this, and the payload copy is byte-identical so one pin covers
both. `test_the_failure_flip_requires_that_the_find_looked` now asserts
the condition and, deliberately, asserts the `!=` form is NOT rewritten
as `== 'true'` — the difference decides whether a run that died before
the find step still flips the order.

What the assumption got right, and what still stands: no test here
executes the workflow or proves GitHub's expression semantics. The pin
catches deletion and rewording; it cannot catch a misunderstanding of
what `steps.find.outputs.looked` evaluates to on a step that failed.
That gap is carried into `release.md`.
