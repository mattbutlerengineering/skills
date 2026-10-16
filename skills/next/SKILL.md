---
name: next
description: Use when the user wants to continue the pipeline, asks "what's next", or wants to start or resume a product, feature, or maintenance run without naming a stage. Reads artifact state and routes to the right stage skill.
---

# Next (pipeline router)

Orient the run from its artifacts, announce where it stands, and hand off to
the correct stage skill. This skill never produces an artifact itself.

## Process

1. Read `../../docs/pipeline-protocol.md` (relative to this skill's base
   directory) — it defines run discovery and the orientation table.

2. **Discover the run.** Apply the protocol's run-discovery rules. If no run
   exists at all, the next stage is Idea (ask product or feature first) —
   and if `docs/backlog.md` exists, list its unclaimed seeds and offer to
   start from one (the protocol's seed-backlog section). Route the chosen
   seed by what it describes, not by where it is parked: something broken
   or degraded starts a maintenance run through `capture`; a new capability
   starts through `idea`. Capture parks deferred defects in the same
   backlog, so treating every seed as an idea would turn a bug into a
   feature run and quietly drop the mandatory-Verify rule.

3. **Orient.** Walk the orientation table: the next stage is the first stage
   in order that is not complete. Honor the UX conditional (`ux:` field in
   `prd.md` frontmatter), the re-entry conditional (`re-entry:` field in
   `defect.md` frontmatter, maintenance runs), the Ship outcome (`outcome:`
   field in `release.md` frontmatter — `prepared` is Ship not yet complete,
   the protocol's "The Ship outcome" section), the Operate population
   (`users-observed:` field in `retro.md` frontmatter — a retro without
   its population line is Operate not yet complete, the protocol's "The
   Operate population" section), and the Implement checkbox rule.

4. **Announce.** Tell the user, in one or two sentences: which run this is,
   what exists, what's next, and why. Example: "Feature run `dark-mode`: PRD
   exists and declares a UI surface, no `ux.md` — next stage is UX Design."
   A prepared release announces the write-back: "Feature run `dark-mode`:
   `release.md` is `prepared`, waiting on <PR url> — confirm the pull
   request merged, then record it; next stage is Ship."

5. **Hand off — open pull requests first.** When the repo has open pull
   requests, run the protocol's "Open pull requests first" pre-flight
   before the stage: present the green ones for the Owner's merge answer,
   fix or name the red ones, surface the stale ones. The router runs it
   itself; it is a protocol step, not a skill to route to. The stage
   hand-off waits until nothing is left that is mergeable or fixable, and
   a pull request waiting on the Owner is reported, not waited on. Never
   merge without the Owner's answer.

   Then load the matching stage skill through the harness's
   skill-loading mechanism (a skill tool where one exists, otherwise a read
   of the skill file) and follow it; naming the skill in prose does not
   load it.
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

6. **Completed run?** If `retro.md` exists and carries its population
   line, the run is complete (a retro without the line is Operate not yet
   complete, routed in step 5). Offer to start the next run — the retro's "seeds for next ideas" section is the
   natural input to a fresh `idea` invocation, and if `docs/backlog.md`
   exists, list its unclaimed seeds and offer to start from one, routing
   each by what it describes exactly as in step 2.

## Rules

- Never re-run a completed stage without being asked; if the user wants to
  revise an existing artifact, route to that stage skill explicitly.
- If two runs are active and the user's intent is ambiguous, ask — don't
  guess.
- Keep the announcement short. The router's job is orientation, not summary.
- The backlog is advisory and read only in the two moments above (steps 2
  and 6) — never during active-run orientation, which comes from run
  artifacts alone.
