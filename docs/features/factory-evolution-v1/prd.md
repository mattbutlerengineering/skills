---
stage: prd
run: feature:factory-evolution-v1
date: 2026-09-21
id: PRD-0006
ux: not-applicable
ux-reason: every deliverable is an ADR, a breakdown row, a gate detector, a workflow trigger, or scheduled-routine prose — nothing built for a human to look at as a UI
assumptions:
  - "No live interview; requirements below are drawn directly from issue #438's own text, epic #439's map (Destination/Notes/Decisions so far), issue #436's ratification (docs/backlog.md's tail), issue #437's closing comment, and the four docs/research/*.md surveys. Gaps are called out as Open questions, not silently resolved."
  - "This run stops at Decompose: every success criterion below describes what a FUTURE implementation run must satisfy, not code this run ships. This run's own success is producing the ADRs, this PRD, architecture.md, and breakdown.md — see the Out of scope section."
---

# PRD: Factory evolution backlog seed

## Problem statement

Epic #439's map is ratified but not yet formalized: four mechanisms
have a settled adopt verdict (docs/backlog.md's tail, issue #436) and
three routines have a settled roster (issue #437's closing comment),
but none of it exists as a citable ADR, a PRD success criterion, or a
breakdown row this repo's own dispatch loop (ADR-0032) can act on. The
map's own optimization target — autonomy per human-hour at the three
gates, now pinned by ADR-0069 as accepted work orders per gate-wait
hour — has nothing beneath it yet tying any specific backlog item back
to that number.

## Solution

When the *future implementation runs* this PRD's breakdown seeds are
actually built (this run itself stops at Decompose — see Out of
scope): three new ADRs (0070 merge queue, 0071 clarification markers,
0072 PRD-coverage check) exist and are cited by name; `trigger_eval.py`
gains a derived per-skill precision/recall/F1 function over its
existing confusion matrix, with no new ADR; and three new weekly
scheduled routines (retro/reflect deepening, queue groomer, doc
gardener) each get a protocol doc and an ADR-0044-style trigger, also
with no new ADR — each is an instantiation of the pattern ADR-0044
already decided, not a fresh hard-to-reverse decision (see
`architecture.md`'s Decisions section for the full argument). Every one
of the seven items is traceable, in its own success criterion below, to
why it serves autonomy-per-human-hour.

## Actors

- **Matt (repo maintainer)** — ratified all seven items via HITL
  (issues #436, #437) before this run started; approves this run's own
  blueprint gate (`architecture.md`, ADR-0033) and each future
  implementation run's own gates in turn; the human code-owner merge
  this PR itself needs because it touches `docs/adr/**` (ADR-0036
  condition 3).
- **This repo's dispatch loop (ADR-0032)** — the eventual consumer of
  the seven breakdown rows below, once a human mirrors them to
  `WO-####` issues (not performed by this run).
- **The `factory-daily-improvement` routine's three weekly siblings**
  — not yet built; this PRD's success criteria for them stop at "a
  protocol doc and a trigger exist," matching how much issue #438 asks
  this ticket to settle (explicitly not full per-routine protocol
  detail — that is deferred to each routine's own future
  implementation run).

## User stories

1. As Matt closing out epic #439's map, I want every ratified mechanism
   and routine to have a citable artifact (an ADR where one is called
   for, a breakdown row otherwise), so the map's own Destination — "a
   seeded work-order backlog... that the factory's own dispatch loop
   executes" — is actually true, not just decided in prose.
2. As Matt reviewing a future PR that lands one of these seven items, I
   want its breakdown row to cite this PRD's relevant section and, via
   this PRD, ADR-0069's baseline metric, so I can tell at a glance why
   the item is in the backlog and not just that it is.
3. As Matt or an agent authoring the three new ADRs, I want each one to
   compose explicitly with the standing ADR its mechanism touches
   (ADR-0036 for the merge queue, ADR-0005/ADR-0011 for clarification
   markers, ADR-0032 for the coverage check) rather than float
   unanchored, so a future reader sees the decision in the context of
   what it changes.
4. As Matt deciding the routine-ADR judgment call, I want that
   reasoning recorded once, in `architecture.md`, and applied
   consistently to all three routines, so a future reader doesn't have
   to re-derive why routines differ from the three ADR-backed
   mechanisms.
5. As the factory's own dispatch loop, I want no `WO-####` GitHub issue
   created ahead of its breakdown row (ADR-0032), so this run's output
   never lets the dispatch plane run ahead of an unapproved blueprint.

## Success criteria

- [ ] **ADR-0070** (GitHub native merge queue) exists, `accepted`,
      composing explicitly with ADR-0036's agent-merge conditions, with
      an honest accounting of cascade cost at this repo's actual
      40+-open-PR backlog volumes — serves autonomy-per-human-hour by
      replacing a manual pairwise-merge audit (a human task) with a
      continuous, automated check at gate 3.
- [ ] **ADR-0071** (inline `[NEEDS CLARIFICATION]` markers, CI-enforced)
      exists, `accepted`, defining the marker convention, the bounded
      clarify pass, and the gate-1 CI enforcement rule — serves
      autonomy-per-human-hour by resolving an ambiguity before gate 1's
      human approval, instead of costing gate-wait time discovered at
      or after approval.
- [ ] **ADR-0072** (bidirectional PRD-requirement<->work-item coverage
      check) exists, `accepted`, defining the reverse-direction check
      and its declared-waiver grammar — serves autonomy-per-human-hour
      by catching a silently-uncovered PRD criterion at Decompose
      instead of costing rework discovered at Verify or never.
- [ ] `docs/adr/README.md`'s index carries a row for each of the three
      new ADRs, status matching the ADR file's own Status line
      (detector D's existing invariant).
- [ ] A breakdown row exists for deriving per-skill precision/recall/F1
      from `trigger_eval.py`'s existing confusion matrix (no new ADR,
      per `docs/research/eval-and-memory.md` shortlist item 5's own
      verdict) — serves autonomy-per-human-hour by turning an already-
      recorded blind spot (`docs/backlog.md`'s "omp near-miss
      under-triggering: 8/16 near-miss cases under-trigger") into a
      trackable number without spending a human gate-wait hour re-eval-
      uating.
- [ ] A breakdown row exists for each of the three routine-roster items
      (weekly retro/reflect deepening, queue groomer, doc gardener),
      each scoped to "design and land this routine's protocol doc +
      ADR-0044-style trigger" (per issue #438's own explicit scope
      bound for this ticket) — serves autonomy-per-human-hour by
      extending the one mechanism already proven to run unattended
      (ADR-0044) into the three missions #437 ratified, rather than
      inventing a new unattended-operation pattern per routine.
- [ ] Every breakdown row cites a resolving `PRD-0006 §section`
      (detector A's existing invariant) and, through this PRD, traces
      to ADR-0069's baseline metric — no row exists that isn't
      justified against the map's own optimization target.
- [ ] No `WO-####` GitHub issue is created by this run (ADR-0032's
      one-way mirror; this run's `architecture.md` has not cleared the
      human blueprint gate).
- [ ] `python3 -m unittest discover tests`, `python3 lint.py`, and
      `python3 gates.py && python3 gates.py --selftest` all stay green
      through every artifact this run writes.

## Out of scope

- **Implementing any of the seven backlog items.** This run stops at
  Decompose — idea, this PRD, `architecture.md`, `breakdown.md`. No
  `gates.py` detector, no `trigger_eval.py` function, no workflow YAML,
  no `factory/**` protocol doc, and no skill/charter prose change ships
  from this run. Each breakdown row seeds a *future* implementation
  run.
- **Full per-routine protocol documents.** Issue #438 explicitly defers
  "exact per-routine protocol details (like
  `docs/factory/improvement-routine.md`'s ~12-section daily protocol)"
  to when each routine is actually specified and built — this PRD's
  success criteria stop at "a breakdown row exists scoping that future
  work," not the protocol content itself.
- **Re-deciding any of the four ratified mechanisms or the routine
  roster.** Issue #438's own text is explicit: "already decided, do
  not re-decide." This PRD formalizes verdicts already reached via
  HITL (issues #436, #437); it does not reopen them.
- **The nine explicitly-declined mechanisms** (constitution-check gate
  + complexity tracking, pre-dispatch readiness verdict, the living
  current-truth spec, mem0-style memory consolidation, the dashboard
  budget-remaining field, sub-agent budget inheritance, the DORA
  escaped-defect/change-failure distinction, and the two remaining
  items already marked Reject in the survey shortlists) — explicitly
  out of scope for this backlog seed, per issue #438's own text.
- **Computing ADR-0069's actual baseline number.** ADR-0069 itself
  records that real dispatched-work data does not exist yet; this PRD
  cites the *formula*, not a computed value, in every success
  criterion above.
- **Creating any `WO-####` GitHub issue, applying any `wo:*` label, or
  merging this PR.** ADR-0032's one-way rule (breakdown rows before
  issues) and this repo's own merge-authorization convention (a human
  merges any PR touching `docs/adr/**`, ADR-0036 condition 3) both
  apply; this run produces artifacts only.

## Open questions

- **Exact detector letters for the merge-queue's, clarification-
  markers', and coverage-check's new `gates.py` checks** — left to each
  item's own future Architect pass, the same way `docs/features/
  codex-style-standards-enforcement/prd.md` left its detector letters
  to Architect. Each new ADR names *that a detector is needed*, not
  which letter it claims, to avoid colliding with whatever another
  in-flight run has claimed by the time it's actually implemented.
- **Merge queue cascade-cost tuning** (queue depth, eviction policy,
  repo-wide vs. opt-in) — ADR-0070 adopts the mechanism and names the
  tradeoff honestly; the actual parameters are implementation-time
  decisions for that future run, not resolved here.
- **The coverage check's exact waiver regex and whether it lives as an
  extension of detector A or a sibling detector** — ADR-0072 states the
  shape (a declared, checkable waiver comment); the implementation
  choice is deferred to that future run's own architecture pass.
- **Each routine's exact weekly day/time, budget cap, and cloud
  environment specifics** — issue #437's closing comment defers these
  "to when each one is actually specified and built"; this PRD's
  success criteria do not attempt to pin them.
