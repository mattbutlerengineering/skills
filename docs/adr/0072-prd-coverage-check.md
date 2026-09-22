# Bidirectional PRD-requirement <-> work-item coverage check

- Status: accepted
- Date: 2026-09-21

## Context

- Epic #439 ratified an adopt/adapt/reject pass over four survey
  shortlists (issue #436). `docs/research/spec-driven-sdlc.md`
  shortlisted GitHub Spec Kit's bidirectional coverage check as
  shortlist item 2, verdict Adopt, "Own ADR? Yes."
- The factory dispatch plane (ADR-0032) already enforces **one
  direction**: "every breakdown work-order row cites a resolving
  `PRD-#### §section`" — detector A (`check_wo_citation` in `gates.py`)
  fails a breakdown row that cites no PRD id. Nothing enforces the
  **reverse**: a PRD success criterion or `§` section that zero
  breakdown rows cite is invisible until Verify — or never, if the
  feature ships without anyone noticing the gap.
- Spec Kit's `/speckit.analyze` names this category precisely: "Coverage
  Gaps: Requirements with zero mapped tasks; tasks with no mapped
  requirement," with zero-coverage-of-core classed CRITICAL
  (`templates/commands/analyze.md`, github/spec-kit, per
  `docs/research/spec-driven-sdlc.md`).
- The survey's own scoping is explicit about what this adopts and what
  it doesn't: "The factory has the harder prerequisite already built
  (typed IDs, `knowledge_plane.py` row grammar), so the reverse check
  is a bounded stdlib extension... The rest of analyze — terminology
  drift, ambiguity scoring — is LLM-judgment work; it belongs in
  skills, not gates, and is not part of this adoption."
- This repo already has a "declared, never assumed" idiom for exactly
  this shape of exemption: detector B's `NO_WO_DECLARATION` — a PR that
  implements no work order says so explicitly (`No work order: <reason>`)
  rather than the absence being silently accepted. OpenSpec's
  `skip_specs: true` exemption is convergent evidence for the same
  pattern (`docs/research/spec-driven-sdlc.md`, "Notable convergences").

## Decision

- Extend detector A's scope (or add a sibling detector, same letter
  family — implementation's call, deferred to the breakdown row) to
  check the **reverse** direction: every `§` section (or, where a PRD
  numbers them, every checkbox line under "Success criteria") in a
  `prd.md` with a declared `id: PRD-####` must be cited by at least one
  breakdown row in that run's `breakdown.md`, **or** carry a declared
  waiver.
- **Waiver grammar**, matching the existing "declared, never assumed"
  idiom rather than inventing a new one: a PRD section not covered by
  any breakdown row may carry an inline note in the PRD itself —
  `<!-- coverage-waiver: <reason> -->` directly under the section
  heading — the same spirit as detector B's `No work order:` line: an
  absence is either covered or explicitly excused, never silently
  invisible. A waiver is a statement the PRD's own author makes about
  their own document, checkable the same way detector B checks a PR
  body's own declaration — no second party's judgment required to
  validate the string is present.
- Scope matches the survey's own boundary exactly: this adopts the
  coverage-gap check alone. Terminology-drift detection and ambiguity
  scoring (the rest of `/speckit.analyze`) are explicitly **not**
  adopted here — that is LLM-judgment work for a skill (if ever
  pursued), not a mechanical gate, and out of frame for this ADR.
- Home: `gates.py`, not `lint.py` — same reasoning `docs/features/
  codex-style-standards-enforcement/architecture.md` already recorded
  for its own detectors: `gates.py` ships to every factory-stamped
  product repo via `factory_init.MIRRORS` and already gates the
  knowledge plane generically (PRD/breakdown pairs in any repo using
  this pipeline, not just this one); `lint.py` is unmirrored and
  specific to this meta-repo's own skill/protocol authoring.

## Consequences

- No code ships with this ADR (planning-only, per epic #439's framing);
  the detector implementation, its selftest fixtures, and the waiver
  syntax's exact regex are follow-up work, tracked by this run's
  breakdown row.
- Detector A's existing behavior (breakdown row -> PRD id, one
  direction) is unchanged; this decision adds the reverse check as new,
  additive coverage, not a rewrite of A's contract (CLAUDE.md: surgical
  changes, don't fold unrelated behavior into an existing detector's
  established contract without cause — here the cause is a distinct
  direction of the same underlying invariant, likely its own detector
  letter rather than silently widening A).
- A PRD section that is genuinely out of scope for Decompose (e.g. this
  very run's own PRD, still pre-implementation) needs its waiver
  written honestly, not to make the detector pass — the same
  eval-honesty discipline (CLAUDE.md) that governs every other
  declared exemption in this repo.
- Serves the map's optimization target (autonomy per human-hour at the
  three gates, ADR-0069): a PRD success criterion silently dropped
  between PRD approval (gate 1) and Verify is exactly the kind of
  rework that costs a human gate-wait hour discovering late what a
  mechanical check could have caught at Decompose.
