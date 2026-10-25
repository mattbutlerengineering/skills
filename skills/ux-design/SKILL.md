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

3. **Scenario walkthroughs first.** Before any flow is designed, pick
   the hardest scenarios in `idea.md` and `prd.md` (the edge cases, the
   bulk edits, the one-off exception to a recurring rule) and write each
   as an acceptance walkthrough: the actor, the goal, and the steps that
   reach it. Confirm the list with the user before going on: they know
   which cases hurt. They are the test the flows must pass. Before the
   artifact is written, walk each one again using only controls this doc
   defines.
   A walkthrough that cannot finish is a gap: fix the flow, or record it
   under Deliberately not designed with the reason.

4. **Interview.** One flow at a time:
   - What is the primary flow — the shortest path through the feature for
     its main actor? Walk it step by step.
   - For each screen/surface in the flow: what's on it, what's the one thing
     the user is meant to do there?
   - What are the empty, loading, and error states? (These are where UX
     dies; don't skip them.)
   - What existing UI conventions must this match? If the repo has
     `docs/ux-patterns.md`, read it first: its behaviour rules and its
     Voice & terms answer this question, so ask only what it leaves
     open. If it is absent, suggest running the `ux-patterns` skill first
     — its rules for scope, preview, undo, discard, concurrency and
     permissions are where screens most often disagree. It is a
     suggestion, not a gate: the stage proceeds either way.
   - What's deliberately NOT being designed (deferred polish)?

5. **Code facts before sketches.** For each existing surface a flow
   changes, read the code that implements it today and record what it
   does now under Code facts: the file, and the behaviour the sketch
   depends on (what the form calls, which channels a message goes out
   on, what a component can show, what a role actually enforces). Never
   sketch an existing surface from memory. A fact that contradicts the
   flow means you re-open the affected flow with the user, or record it
   under Dependencies surfaced for Architect when the fix is technical.

6. **Sketch.** Wireframe each screen as an ASCII sketch or a tight textual
   description — enough for Architect and Implement to build from without
   guessing. Confirm each sketch with the user before moving on.

7. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)
   into the run directory as `ux.md`, with protocol frontmatter.

8. **Independent review before hand-off.** Dispatch a fresh reviewer
   (a subagent with its own context) on the written `ux.md`. Give the
   reviewer the files, not your conclusions: `idea.md`, `prd.md`, `ux.md`,
   and the code paths listed under Code facts, with the instruction to
   report Critical and High findings only (a walkthrough that cannot
   finish, a hard scenario left out, a sketch that contradicts its flow,
   a code fact the design ignores, terms that drift). Fix or record each
   finding before committing, re-walk the walkthroughs after the fixes,
   and list each finding under Review with its disposition. Where the
   harness cannot start a fresh agent context, re-read `ux.md` cold
   against the walkthroughs and the code facts yourself, and record
   `review: inline, not independent` under Review; in an unattended run,
   also log it under `assumptions:` in the frontmatter, so the run's
   report shows it. Never present a self-review as an independent one.

9. **Hand off.** Next stage is Architect. Commit the artifact on the run's
   branch — the protocol's "Commit at the stage boundary" section owns the
   rule and the commit subject.

## Rules

- Flows before screens; screens before pixels. No visual styling decisions
  beyond what conventions demand.
- Every user story in the PRD with a UI surface must be reachable through
  some flow in this artifact — check before finishing.
- No technical design: how it's built is Architect's job.
