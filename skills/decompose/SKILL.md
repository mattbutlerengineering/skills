---
name: decompose
description: Use when a technical design exists and needs breaking into ordered, implementable work items — milestones, dependencies, sequencing — or when the user asks to break the work down. Drafts from the architecture. Produces breakdown.md.
---

# Decompose

Break a finished technical design into dependency-ordered, checkable work
items. Pure work breakdown — no design decisions. Draft-first: the
architecture contains the answers; the user reviews the cut lines.

## Process

1. Read `../../docs/pipeline-protocol.md` for run discovery, gating, and
   frontmatter conventions.

2. **Soft gate.** Predecessor artifact: `architecture.md`. If missing, apply
   soft gating.

3. **Draft the breakdown.** Fill `TEMPLATE.md` (in this skill's directory):
   - Group work into milestones, each independently valuable (something
     works and is demonstrable at each milestone boundary).
   - Within milestones, cut items small: one item = one sitting's work with
     a checkable acceptance criterion derived from the PRD's success
     criteria or the architecture's contracts.
   - Order by dependency; mark the blocking edges explicitly.
   - Every component in the architecture appears in some item; every PRD
     success criterion is covered by some acceptance criterion.
   - Opt-in tracker import: when the user points at existing issues in the
     project's issue tracker (or asks to work the backlog), fold them in
     as work items carrying their issue references in the protocol's
     `(tracker: #123)` form. Imported items still need acceptance
     criteria — derive one from the issue and the PRD, or interview.
   - Opt-in tracker export: when the user wants the breakdown published
     to the project's issue tracker, create a tracker issue for each
     work item (or per milestone, where that reads better), and record
     the item-to-issue mapping on the checkbox line in the protocol's
     `(tracker: #123)` form — the same form imported items already carry.
     The breakdown remains the state; the tracker is the mirror.

4. **Check the draft before presenting it.** Read it as the implementer
   who will pick up one item cold, and fix what you find in place:
   - No template slot survives: no `<...>` placeholder from `TEMPLATE.md`,
     no TBD or TODO, no "same as the item above". An item that cannot be
     written yet is a design gap (see Rules), not a placeholder.
   - Every `Accept:` line states an outcome someone can check. "Works
     correctly" and "handles errors appropriately" are hopes, not
     criteria.
   - Names hold still. Components and interfaces keep the architecture's
     spelling, and every `Blocked by:` names an item that exists, by its
     exact title or its `WO-####` id where rows carry one. A dependency
     that names nothing real orders nothing.

   This check matters most when nobody reviews the cut live: an autorun,
   or a user who accepts the recommended boundaries as-is.

5. **Review the cut.** Present the draft; the user's judgment calls are the
   milestone boundaries and anything that looks mis-sized. Revise.

6. **Write the artifact.** Save as `breakdown.md` in the run directory with
   protocol frontmatter. Items are markdown checkboxes — Implement checks
   them off, and the pipeline reads progress from them.

7. **Hand off.** Next stage is Implement.

## Rules

- If decomposition exposes a design gap (a component with unclear
  responsibility, a missing contract), don't design around it here — record
  the gap and route back to Architect.
- No item without an acceptance criterion. "Do the backend" is not an item.
- Prefer vertical slices (thin end-to-end) over horizontal layers where the
  architecture allows — earlier feedback per item.
- The project's issue tracker mirrors the breakdown, never replaces it
  (ADR-0026): imported or exported, the checkboxes here remain the state.
