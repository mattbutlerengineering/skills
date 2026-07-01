---
name: decompose
description: Use when a technical design exists and needs breaking into ordered, implementable work items — milestones, issues, dependencies. Drafts from the architecture. Produces breakdown.md.
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

4. **Review the cut.** Present the draft; the user's judgment calls are the
   milestone boundaries and anything that looks mis-sized. Revise.

5. **Write the artifact.** Save as `breakdown.md` in the run directory with
   protocol frontmatter. Items are markdown checkboxes — Implement checks
   them off, and the pipeline reads progress from them.

6. **Hand off.** Next stage is Implement.

## Rules

- If decomposition exposes a design gap (a component with unclear
  responsibility, a missing contract), don't design around it here — record
  the gap and route back to Architect.
- No item without an acceptance criterion. "Do the backend" is not an item.
- Prefer vertical slices (thin end-to-end) over horizontal layers where the
  architecture allows — earlier feedback per item.
