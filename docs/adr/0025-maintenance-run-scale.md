# A third run scale: the maintenance run

- Status: accepted
- Date: 2026-07-03

The pipeline had two run scales (ADR-0003: product and feature), and both
are idea-forward — every run enters at Idea or PRD. That left no honest
on-ramp for the other half of real development work: a reported defect, a
regression, a refactor, or a dependency upgrade starts from existing code
in a broken or aging state, not from a vague thought. Forcing that work
through idea → prd → architecture → decompose is absurd overhead that
models none of it; abandoning the pipeline loses orientation, artifacts,
and the retro loop.

Decision: a **maintenance run** is a third run scale, not a utility skill —
it produces artifacts, benefits from orientation, and participates in the
retro loop, all things ADR-0023's utility-skill definition excludes. The
pipeline spine is unchanged; the maintenance run re-enters it partway:

- It enters at a lightweight **capture step** (interview-style, like Idea)
  whose seed artifact is `defect.md` — a defect brief, generalizing to a
  condition brief for refactor and upgrade work. Artifacts live under
  `docs/fixes/<slug>/`, and orientation treats the brief exactly like any
  other stage artifact (ADR-0004 holds).
- **Re-entry depth is decided at capture time and recorded in the brief's
  frontmatter** as `re-entry: implement | architect`, mirroring the
  conditional-UX pattern (ADR-0017) for conditional stage participation.
- **Verify is mandatory** — the regression test is the point of a fix.
  Review and Ship scale to the blast radius recorded in the brief.

Consequences: run discovery gains `docs/fixes/*/`; the protocol gains the
maintenance orientation rows and the breakdown-placement rule (checkboxes
inline in `defect.md` when re-entry is Implement; the normal
`architecture.md` + `breakdown.md` chain when re-entry is Architect);
recurring defects become first-class seeds for the retro loop.

Supersedes [ADR-0003](0003-two-run-scales.md) in part: the two run scales
become three. ADR-0003's description of the product and feature scales
stands unchanged.
