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

4. **Load applicable standards.** Read `../../docs/standards.json` if
   present (an unbootstrapped repo has none yet — proceed). Filter to
   statements whose `domain` is `factory` or `pipeline` — the
   design-relevant slice. A decision below that bears on one cites its
   `slug` in `TEMPLATE.md`'s "Decisions & alternatives" section.

5. **Draft.** Read [`references/canon.md`](references/canon.md) first — the
   design rules that constrain what you may draft, and the vocabulary they
   are written in. Then fill `TEMPLATE.md` (in this skill's directory) end
   to end: approach, components and their responsibilities, data model,
   interfaces/contracts between components, stack choices. For every
   decision that had real alternatives, record the alternative and why it
   lost — one line each.

6. **Surface the trade-offs.** Present the draft with the 2–4 decisions that
   genuinely could have gone another way, each with your recommendation.
   Revise on feedback.

7. **Write ADRs sparingly.** Apply the protocol's "When to write an ADR"
   test to each decision in the draft. Write an ADR for each one that
   passes all three legs, following the protocol's placement, status and
   numbering rules, and cite it from that decision's line in the artifact.
   A decision that fails any leg keeps only its one-line record.

8. **Write the artifact.** Walk the closing checklist in
   [`references/canon.md`](references/canon.md) against the draft first —
   it is written against the template's own sections, so a miss names the
   line to fix. Then save as `architecture.md` in the run directory with
   protocol frontmatter. If UX Design was skipped, echo it:
   `ux: skipped — <ux-reason from prd.md>`.

9. **Hand off.** Next stage is Decompose.

## Rules

- Every requirement in the PRD must be traceable to some component in the
  design — check before finishing.
- Prefer boring technology and existing patterns; novelty needs a stated
  reason.
- Interfaces are contracts: name inputs, outputs, and failure modes, not
  just component names.
- No work breakdown, estimates, or sequencing — that's Decompose.
