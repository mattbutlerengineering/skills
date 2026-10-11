# The pipeline writes ADRs at its stages, by one test

- Status: accepted
- Date: 2026-10-10

Amends no record. ADR-0001's convention (numbered ADRs in `docs/adr/`,
supersede rather than rewrite) stands; this decides when the pipeline's
own stages produce one in a target repo.

## Context

Issue #634 asked for ADRs to be created as part of the workflow, with
logic for when. Before it, only Architect mentioned ADRs, and only as
something to *offer* when a decision was hard to reverse, surprising
without context, and the result of a real trade-off. Nothing wrote one
when Implement diverged from the design, nothing noticed a missing one at
Review, and nothing checked ADR numbers at Ship, although parallel
branches pick the same next number.

The owner chose option A on the issue: a decision rule in the stages, no
new skill and no CI gate.

## Decision

1. **One rule, in the protocol.** `docs/pipeline-protocol.md` gains
   "When to write an ADR": Architect's three-legged test (all three must
   hold), examples and non-examples, where ADRs live, supersede-or-amend
   instead of rewrite, `provisional` status for an ADR written without
   live confirmation, and the numbering rule below. Stage skills cite it
   and do not restate it.
2. **Four stages apply it.** Architect writes an ADR for each design
   decision that passes (still sparingly). Implement writes one, or
   supersedes one, when a deviation from `architecture.md` passes, and
   records other deviations in the breakdown's Notes as before. Review
   reports a passing decision with no ADR, and an edited Decision section
   where a superseding ADR was owed, as Design-pass findings under its
   usual severity rubric. Ship's pre-flight confirms each new ADR's number
   is free on the base branch and that the index lists it. Autorun's
   report lists ADRs written unattended.
3. **Numbers are provisional until merge.** A draft takes the next free
   number on its branch; the number is confirmed against the base branch
   at merge time, and on a collision the later ADR renumbers its file,
   index row and every in-repo citation together.

## Consequences

- No checker enforces any of this. Detectors C and D already catch a
  dangling `ADR-NNNN` token and a missing index row in a stamped repo;
  nothing catches a decision that deserved an ADR and got none except
  Review's judgment. A gate was set aside on the issue as too blunt for a
  judgment call.
- Capture is untouched: a design-touching maintenance run re-enters at
  Architect, which writes the ADRs, and a scoped fix that turns out to
  carry one is an Implement deviation.
- The test's legs are judgment. Expect the protocol's examples to do more
  work than the definition; revise the examples rather than the legs.
