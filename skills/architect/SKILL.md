---
name: architect
description: Use when requirements exist and the technical design is needed — architecture, data model, stack, interfaces — or when the user asks for technical design directly. Drafts from artifacts and codebase, then asks only about trade-offs. Produces architecture.md.
---

# Architect

Produce the technical design: approach, components, data model, interfaces,
stack. Draft-first — most answers live in the upstream artifacts and the
existing codebase, so draft from those and interview only where a genuine
trade-off exists. Technical design only: no UX (upstream), no scheduling
(downstream).

## Process

1. Read `../../docs/pipeline-protocol.md` for run discovery, gating, and
   frontmatter conventions.

2. **Soft gate.** Predecessor artifacts: `prd.md`, plus `ux.md` when the PRD
   says `ux: required`. If missing, apply soft gating.

3. **Study before drafting.** For feature runs, explore the existing
   codebase: patterns, layering, naming, prior art for similar features. The
   design must read like the codebase wrote it. For product runs, establish
   the ground rules instead (language, framework, storage, deployment
   target) — these are the questions to ask first.

4. **Draft.** Fill `TEMPLATE.md` (in this skill's directory) end to end:
   approach, components and their responsibilities, data model, interfaces/
   contracts between components, stack choices. For every decision that had
   real alternatives, record the alternative and why it lost — one line each.

5. **Surface the trade-offs.** Present the draft with the 2–4 decisions that
   genuinely could have gone another way, each with your recommendation.
   Revise on feedback.

6. **Offer ADRs sparingly.** Offer an ADR only when a decision is all three:
   hard to reverse, surprising without context, and the result of a real
   trade-off. If any is missing, the one-line record in the artifact is
   enough. ADRs go in the target repo's `docs/adr/`.

7. **Write the artifact.** Save as `architecture.md` in the run directory
   with protocol frontmatter. If UX Design was skipped, echo it:
   `ux: skipped — <ux-reason from prd.md>`.

8. **Hand off.** Next stage is Decompose.

## Rules

- Every requirement in the PRD must be traceable to some component in the
  design — check before finishing.
- Prefer boring technology and existing patterns; novelty needs a stated
  reason.
- Interfaces are contracts: name inputs, outputs, and failure modes, not
  just component names.
- No work breakdown, estimates, or sequencing — that's Decompose.
