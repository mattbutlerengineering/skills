# Artifacts are the state

- Status: accepted
- Date: 2026-07-01

No manifest or state file. A skill orients by checking which artifacts exist
in the run's directory. A skipped conditional stage is recorded in the next
artifact's frontmatter (e.g. `ux: skipped — no UI surface`) so absence is
never ambiguous.

Refined by [ADR-0017](0017-conditional-ux-frontmatter.md).

## Normative statements

- **adr0004-typed-ids-in-frontmatter** (pipeline): A run artifact's typed identifier MUST live in that artifact's own frontmatter, never in a separate manifest or parallel tracking tree.
