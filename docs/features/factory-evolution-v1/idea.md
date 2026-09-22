---
stage: idea
run: feature:factory-evolution-v1
date: 2026-09-21
origin: "GitHub issue #438 (epic #439's final map ticket) — self-answered from decisions already ratified and closed: issue #436's adopt/adapt/reject pass (recorded in docs/backlog.md's tail) and issue #437's closing comment (routine roster v2, 'via direct question to the repo owner'). No live interview was held for this run; AFK drafting, per issue #438's own text."
assumptions:
  - "This run's 'idea' and requirements are drawn entirely from already-closed GitHub issues #434, #435, #436, #437 and the four docs/research/*.md survey documents (autonomous-agent-harnesses.md, review-ci-automation.md, spec-driven-sdlc.md, eval-and-memory.md), not a live interview. Every ratified fact below is cited to its source issue or research doc rather than re-derived."
  - "In-flight check ran (not skipped): gh pr list and gh issue list --search for '438', 'evolution backlog', 'standards.json' (the codex-style-standards-enforcement run's own artifact) came back with nothing already doing this specific ADR-set-plus-breakdown-rows work. Issue #438 itself, epic #439, and its five closed sibling tickets (#431-#437) are the only related history, and none of them already produced the artifacts this ticket asks for."
---

# Idea: Factory evolution backlog seed

## Problem

Epic #439 ("Map: Factory evolution — best AI SDLC workflow") ran five
sub-tickets to completion: three surveys of external mechanism families
(#431 autonomous harnesses, #432 review/CI automation, #433 eval
harnesses/memory — plus the earlier #436-referenced spec-driven-SDLC
survey), a baseline-metric pin (#434, landed as ADR-0069), a paid-eval
funding decision (#435), an adopt/adapt/reject ratification pass over
all four survey shortlists (#436), and a routine-roster decision (#437).
None of that work is yet actionable by this repo's own dispatch loop:
a ratified verdict sitting in `docs/backlog.md`'s tail and a decision
recorded only as a GitHub issue-closing comment are prose, not the
blueprint artifacts (ADRs, a PRD, an architecture, breakdown rows) that
ADR-0032's one-way rule requires before a work order can exist.

## Who has it

Matt, this repo's sole maintainer — as the person who ran the HITL
grilling passes that produced both the ratification (#436) and the
routine-roster decision (#437), and as the operator who will eventually
see whatever breakdown rows this ticket seeds actually dispatched.
Today: four mechanisms have a settled adopt verdict and no ADR number
to cite; three routines have a settled roster and no breakdown row; and
nothing traces any of it back to the map's own optimization target
(autonomy per human-hour at the three gates, now pinned by ADR-0069).

## Why now

Issue #438 is explicitly the last open ticket under epic #439's map:
"Resolving this ticket completes the map." Every upstream decision this
ticket formalizes is already made — #434 pinned the metric formula,
#435 the funding line, #436 the mechanism verdicts, #437 the routine
roster — so the only work left is turning already-ratified prose into
this repo's own artifact conventions, exactly what issue #438 itself
asks for ("AFK drafting").

## Evidence

- `docs/backlog.md`'s tail (issue #436's ratification, commit b7f3ccb
  per issue #438's own text): four mechanisms with settled verdicts —
  three needing their own ADR (GitHub's native merge queue; inline
  `[NEEDS CLARIFICATION]` markers + bounded clarify pass; a
  bidirectional PRD-requirement<->work-item coverage check) and one
  that explicitly does not (deriving per-skill precision/recall/F1 from
  `trigger_eval.py`'s already-recorded confusion matrix — "a function
  in `trigger_eval.py`, extending an existing seam," per
  `docs/research/eval-and-memory.md` shortlist item 5's own verdict).
- Issue #437's closing comment: "Routine roster: weekly retro/reflect
  deepening, queue groomer, doc gardener. Eval runner declined for now.
  Shape: same pattern as the existing `factory-daily-improvement`
  routine — weekly cadence, Sonnet, no MCP connectors, same
  cost-ledger/journal-issue reporting pattern (ADR-0044)."
- ADR-0069 (`docs/adr/0069-autonomy-per-gate-wait-hour.md`): the
  baseline metric formula — "accepted work orders per gate-wait hour"
  — every success criterion in this run's `prd.md` traces to.
- `docs/features/codex-style-standards-enforcement/*.md` (PR #500):
  this repo's own closest precedent for a decompose-only run seeded
  from already-decided external inputs rather than a live interview,
  stopping explicitly before implementation.
- `docs/research/eval-and-memory.md` shortlist item 2 (Letta
  sleep-time agents, "Adapt... No — extend ADR-0044's routine"): direct
  precedent, from the same survey batch, for treating a *second*
  scheduled routine as an extension of ADR-0044's already-decided
  mechanism rather than a fresh ADR-worthy decision — the same
  reasoning this run applies to all three roster routines below.

## Solution hunch

Three new ADRs (numbered after the current max, `docs/adr/0069-*.md`)
recording the three ADR-backed adoptions, each amending or composing
with the standing ADR its mechanism touches (ADR-0036 for the merge
queue, ADR-0005/ADR-0011 for clarification markers, ADR-0032 for the
coverage check). The fourth ratified mechanism (trigger_eval composite
metrics) and the three routine-roster items get breakdown rows without
new ADRs — reasoning recorded in `architecture.md`'s Decisions section,
not re-litigated here. A new feature run at
`docs/features/factory-evolution-v1/` carries the PRD and architecture
that cite ADR-0069 in every success criterion, and `breakdown.md` rows
for all seven backlog items (3 ADR-backed mechanisms, 1 non-ADR
mechanism, 3 routines), each citing its governing PRD section per
detector A's convention.

## Success in one sentence

Every ratified decision from issues #434-#437 has a citable artifact —
an ADR where the map's Notes call for one, a PRD success criterion
traceable to the autonomy-per-human-hour baseline, and a breakdown row
a human or this repo's own dispatch loop can act on — so issue #438,
and epic #439's map, can close.

## Unknowns & risks

- **The routine-ADR judgment call.** Whether the three roster routines
  each need their own ADR, or are instantiations of the already-decided
  ADR-0044 pattern needing only breakdown rows, is not settled by any
  upstream ticket — issue #438 flags it explicitly as this run's one
  judgment call. Resolved in `architecture.md`'s Decisions section,
  argued from the eval-and-memory survey's own precedent (above), not
  silently picked.
- **This run stops at Decompose.** No code, detector, workflow, or
  `factory/charters/**`/`skills/**` prose change ships from this run —
  every "ships as" statement in `architecture.md` describes planned,
  future implementation, mirroring `docs/features/
  codex-style-standards-enforcement/architecture.md`'s own framing for
  the same kind of run.
- **No tracker mirror issues are created.** ADR-0032's one-way rule and
  the planner charter presume a blueprint has already cleared the human
  blueprint gate (ADR-0033) before its rows become dispatch-ready; this
  run's `architecture.md` has not been through that gate. Breakdown
  rows are written; `WO-####` GitHub issues are not — a human or the
  factory's own dispatch loop mirrors them later, per issue #438's own
  instruction.
- **The ADRs themselves are not new decisions requiring re-litigation.**
  Unlike a typical Architect-stage ADR, these three formalize verdicts
  already ratified via HITL (issue #436's grilling pass); the human
  code-owner merge gate (ADR-0033/ADR-0036, since `docs/adr/**` is
  always a gate change) still applies mechanically, but the content is
  not up for renegotiation in this run.
