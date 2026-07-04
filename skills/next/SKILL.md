---
name: next
description: Use when the user wants to continue the pipeline, asks "what's next", or wants to start or resume a product/feature run without naming a stage. Reads artifact state and routes to the right stage skill.
---

# Next (pipeline router)

Orient the run from its artifacts, announce where it stands, and hand off to
the correct stage skill. This skill never produces an artifact itself.

## Process

1. Read `../../docs/pipeline-protocol.md` (relative to this skill's base
   directory) — it defines run discovery and the orientation table.

2. **Discover the run.** Apply the protocol's run-discovery rules. If no run
   exists at all, the next stage is Idea (ask product or feature first).

3. **Orient.** Walk the orientation table: the next stage is the first stage
   in order that is not complete. Honor the UX conditional (`ux:` field in
   `prd.md` frontmatter), the re-entry conditional (`re-entry:` field in
   `defect.md` frontmatter, maintenance runs), and the Implement checkbox
   rule.

4. **Announce.** Tell the user, in one or two sentences: which run this is,
   what exists, what's next, and why. Example: "Feature run `dark-mode`: PRD
   exists and declares a UI surface, no `ux.md` — next stage is UX Design."

5. **Hand off.** Invoke the matching stage skill and follow it:
   - capture → the `capture` skill (maintenance runs only)
   - idea → the `idea` skill
   - prd → the `prd` skill
   - ux-design → the `ux-design` skill
   - architect → the `architect` skill
   - decompose → the `decompose` skill
   - implement → the `implement` skill
   - verify → the `verify` skill
   - review → the `review` skill
   - ship → the `ship` skill
   - operate → the `operate` skill

   Also mention the direct-entry alternative ("or jump anywhere: any stage
   skill can be invoked directly").

6. **Completed run?** If `retro.md` exists, the run is complete. Offer to
   start the next run — the retro's "seeds for next ideas" section is the
   natural input to a fresh `idea` invocation.

## Rules

- Never re-run a completed stage without being asked; if the user wants to
  revise an existing artifact, route to that stage skill explicitly.
- If two runs are active and the user's intent is ambiguous, ask — don't
  guess.
- Keep the announcement short. The router's job is orientation, not summary.
