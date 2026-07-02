# Stage taxonomy

- Status: accepted
- Date: 2026-07-01

Stages: Idea → PRD → UX Design (conditional) → Architect → Decompose →
Implement → Verify → Review → Ship → Operate.

- UX Design is conditional: skipped when the work has no user-facing surface;
  the decision depends on the feature, not the project.
- Architect = technical design only (architecture, data model, stack, ADRs).
  Decompose = work breakdown only (milestones, issues, sequencing). The names
  deliberately avoid "design" and "plan", which are ambiguous.
