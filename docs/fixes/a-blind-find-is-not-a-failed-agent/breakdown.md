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

- [ ] **I1** `Find` record; `pr_for_issue` carries `looked` — size:S, blocked by: —
      (architecture.md §Contracts, table rows 1-4)
      *Acceptance:* all four rows of the contract table hold, driven
      through `pr_for_issue` with the injected gh fake. In particular the
      truncated row answers `looked=False` and does **not** append the
      sentence blaming the agent.

- [ ] **I2** the `find-pr` leg writes the `looked` output — size:S, blocked by: I1
      (architecture.md §Contracts, step outputs)
      *Acceptance:* driving `main(["find-pr", N])` with a real
      `$GITHUB_OUTPUT` file writes `looked=false` for an unreadable
      listing and `looked=true` for a readable one, in both cases
      alongside the existing `pr` line, and the exit code is unchanged
      from today in every case.

## M2 — the workflow acts on it

- [ ] **I3** `assembler.yml`'s failure step gains the condition — size:S, blocked by: I2
      (architecture.md §Contracts, failure step)
      *Acceptance:* the `Mark the work order failed` step's `if:` carries
      `steps.find.outputs.looked != 'false'`. Verified by reading, not by
      running — see this artifact's second assumption. The `!=` form is
      required so an unset output still flips.

## M3 — the payload stays in lockstep

- [ ] **I4** mirror and regenerate the manifest — size:S, blocked by: I3
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

*(deviations logged here, dated, as Implement proceeds)*
