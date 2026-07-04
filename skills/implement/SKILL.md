---
name: implement
description: Use when a breakdown exists and it's time to write code — working through work items test-first, checking them off as acceptance criteria are met — or when the user says to start building, start coding, or start working through the breakdown or a defect brief's fix items. The artifact is the code itself; progress lives in the run's checkboxes — breakdown.md, or inline in defect.md when a maintenance run re-enters at Implement.
---

# Implement

Work through the run's breakdown item by item, test-first. This stage
produces no document — the code is the artifact, and progress is the
checkboxes. In a maintenance run the recorded re-entry depth decides where
those checkboxes live: with `re-entry: implement` they are inline in
`defect.md`; with `re-entry: architect` the normal `breakdown.md` applies.

## Process

1. Read `../../docs/pipeline-protocol.md` for run discovery and gating.

2. **Soft gate.** Predecessor artifact: `breakdown.md` — or, in a
   maintenance run with `re-entry: implement` in `defect.md` frontmatter,
   the brief's inline work items. If missing, apply soft gating (for a
   trivial change, the backfill can be a three-item breakdown — but make
   the items and criteria real).

3. **Pick the next item.** The first unchecked item whose blockers are all
   checked. Confirm the pick with the user if several are eligible.

4. **Per item, test-first:**
   - Turn the item's acceptance criterion into a failing test at the highest
     seam the codebase offers (prefer existing test seams over new ones).
   - Watch it fail for the right reason.
   - Write the minimum implementation that passes, matching the
     architecture's contracts and the codebase's existing style.
   - Refactor with the tests green.
   - Check the item off in the run's breakdown (`breakdown.md`, or
     `defect.md` when the items are inline).

   In a maintenance run, the first failing test is the brief's
   reproduction evidence turned into a test — it becomes the regression
   test Verify will center on.

5. **Log deviations.** When reality disagrees with the breakdown — an item splits,
   a contract needs adjusting — log it dated under the breakdown's Notes. A
   design-level disagreement routes back to Architect, not around it.

6. **Hand off.** When every checkbox is checked, the stage is complete; next
   stage is Verify (in a maintenance run, never skippable).

## Rules

- Surgical scope: touch only what the current item requires. Adjacent smells
  get logged, not fixed.
- Never check an item whose acceptance criterion you didn't actually verify.
- Commit at item boundaries with messages naming the item, so the history
  reads like the breakdown.
- Stuck twice on the same item? Stop and re-read the architecture — the bug
  is often upstream of the code.
