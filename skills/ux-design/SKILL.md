---
name: ux-design
description: Use when a PRD declares a user-facing surface (ux required) and flows/screens need designing before technical work, or when the user asks for UX design directly. Interviews the user and produces ux.md.
---

# UX Design

Design what the user sees and does: flows, screens, states, interactions.
Conditional stage — it runs only when the work has a user-facing surface.
Interview-driven: taste and intent live with the user.

## Process

1. Read `../../docs/pipeline-protocol.md` for run discovery, gating, and
   frontmatter conventions.

2. **Soft gate.** Predecessor artifact: `prd.md`. If missing, apply soft
   gating. If `prd.md` says `ux: not-applicable`, stop and say so — this
   stage doesn't apply; route to Architect. If, mid-interview, it turns out
   there is genuinely no UI surface, correct `prd.md` frontmatter to
   `ux: not-applicable` and stop without producing an artifact.

3. **Interview.** One flow at a time:
   - What is the primary flow — the shortest path through the feature for
     its main actor? Walk it step by step.
   - For each screen/surface in the flow: what's on it, what's the one thing
     the user is meant to do there?
   - What are the empty, loading, and error states? (These are where UX
     dies; don't skip them.)
   - What existing UI conventions must this match?
   - What's deliberately NOT being designed (deferred polish)?

4. **Sketch.** Wireframe each screen as an ASCII sketch or a tight textual
   description — enough for Architect and Implement to build from without
   guessing. Confirm each sketch with the user before moving on.

5. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)
   into the run directory as `ux.md`, with protocol frontmatter.

6. **Hand off.** Next stage is Architect.

## Rules

- Flows before screens; screens before pixels. No visual styling decisions
  beyond what conventions demand.
- Every user story in the PRD with a UI surface must be reachable through
  some flow in this artifact — check before finishing.
- No technical design: how it's built is Architect's job.
