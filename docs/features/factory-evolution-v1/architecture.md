---
stage: architect
run: feature:factory-evolution-v1
date: 2026-09-21
ux: skipped — every deliverable is an ADR, a breakdown row, a gate detector, a workflow trigger, or scheduled-routine prose; nothing built for a human to look at
assumptions:
  - "No human blueprint-gate approval exists yet for this design (ADR-0033, amended by ADR-0036) — this run stops at Decompose, so every 'ships as' statement below describes the PLANNED implementation, not code that exists. The three ADRs this run DOES author (0070/0071/0072) are the exception: issue #438 asks this ticket to formalize already-HITL-ratified decisions as real ADR files directly, not defer authoring them the way docs/features/codex-style-standards-enforcement/architecture.md deferred its own ADR-writing to a future breakdown row. Everything else below — detector code, workflow triggers, trigger_eval functions, routine protocol docs — is planned, future implementation."
---

# Architecture: Factory evolution backlog seed

## Approach

Seven backlog items, each formalized to the depth issue #438 actually
asks for at this stage — a citable decision record where the map's
Notes call for one, and a breakdown row everywhere — not a full
component design for each future implementation. Three items
(merge queue, clarification markers, PRD-coverage check) already have
their ADR authored directly by this run (`docs/adr/0070`-`0072`,
`Status: accepted`, since the underlying decision was already ratified
via HITL in issue #436 — this run formalizes, it does not re-decide).
One item (trigger_eval composite metrics) gets a breakdown row and no
ADR, per the eval-and-memory survey's own verdict. Three items (the
routine roster) get breakdown rows and no ADR, per this run's own
judgment call below — argued once, applied consistently to all three.
Nothing here is a new *kind* of artifact this repo doesn't already
have: three more ADRs in the existing sequence, one more PRD, one more
breakdown, following the exact structural precedent
`docs/features/codex-style-standards-enforcement/*.md` already set for
a decompose-only run seeded from external, already-decided inputs.

## Components

### 1. ADR-0070 — GitHub native merge queue (ships as: repo settings + workflow trigger change)

- **Responsibility:** once implemented, enables GitHub's merge queue on
  branch protection and adds `merge_group` as a trigger to every
  required-check workflow mirrored via `factory_init.MIRRORS`
  (`.github/workflows/validator.yml` and siblings), so the queue's
  speculative merge commit is what CI actually validates.
  **Not part of this run's own diff** — `.github/workflows/**` is
  untouched here; the future implementation run does that, and its own
  breakdown row (see `breakdown.md`) is what actually lands it.
- **Collaborators:** ADR-0036 (agent-merge conditions 2 and 3, unchanged
  — the queue owns only condition 1); the reviewer charter
  (`factory/charters/reviewer/CHARTER.md`, unchanged by this run).
- **Decision already recorded:** ADR-0070 itself (full Context/
  Decision/Consequences there, not restated here).

### 2. ADR-0071 — inline `[NEEDS CLARIFICATION]` markers, CI-enforced (ships as: template + skill + detector change)

- **Responsibility:** once implemented, a marker convention in
  `skills/prd/TEMPLATE.md` and `skills/architect/TEMPLATE.md`, a
  bounded clarify pass added to the PRD skill's process, and a new
  `gates.py` detector (letter deferred to that future run's own
  architecture pass, avoiding whatever letter is claimed by then — the
  same discipline `docs/features/codex-style-standards-enforcement/
  architecture.md` already used choosing `K`/`M` over the reserved
  `J`). **Not part of this run's own diff** — this PRD's own text above
  and `idea.md` use plain "Open questions" / `assumptions:` prose, not
  the new marker syntax, since the marker convention does not exist
  yet.
- **Collaborators:** ADR-0005 (soft gating / `assumptions:` — unchanged,
  the marker is additive alongside it); ADR-0011 (interview early,
  draft late — the marker is exactly what lets a drafting stage draft
  past an ambiguity instead of stalling).
- **Decision already recorded:** ADR-0071 itself.

### 3. ADR-0072 — bidirectional PRD-requirement<->work-item coverage check (ships as: detector + waiver grammar change)

- **Responsibility:** once implemented, extends or adds a sibling to
  detector A (`check_wo_citation` in `gates.py`) checking the reverse
  direction — every PRD `§` section cited by ≥1 breakdown row or
  carrying a declared `<!-- coverage-waiver: ... -->` comment.
  **Not part of this run's own diff** — this PRD's own "Success
  criteria" section above is not itself waiver-annotated, since the
  waiver convention does not exist yet and this run's breakdown does
  cover every criterion (see Traceability below).
- **Collaborators:** ADR-0032 (the one-way dispatch mirror and typed
  cross-link IDs the coverage check extends); detector A (unchanged
  contract, new sibling behavior).
- **Decision already recorded:** ADR-0072 itself.

### 4. `trigger_eval.py` composite precision/recall/F1 (ships as: a new function in an existing seam module, no ADR)

- **Responsibility:** once implemented, a pure function reading
  `summarize()`'s already-computed `confusion` dict (`{expected:
  {fired: count}}`, `trigger_eval.py`'s `summarize`) and deriving
  per-skill precision, recall, and F1 — a second pass over already-
  recorded results, never a re-run of the model and never a rewrite of
  `evals/results/**` (append-only, CLAUDE.md eval honesty). Directly
  answers `docs/backlog.md`'s already-recorded "omp near-miss
  under-triggering: 8/16 near-miss cases under-trigger on omp vs Claude
  Code" seed with a trackable number instead of a raw confusion table.
- **Why no ADR:** `docs/research/eval-and-memory.md` shortlist item 5's
  own verdict is explicit — "No new ADR: a function in `trigger_eval.py`
  ... matching this repo's existing 'extend the seam module' convention
  rather than growing a parallel report path." This run applies that
  verdict as given, not re-derived.
- **Collaborators:** `results/trigger-*.json` (read-only input);
  `docs/backlog.md`'s existing under-triggering seed (the consumer this
  metric answers).

### 5-7. Routine roster v2 — weekly retro/reflect deepening, queue groomer, doc gardener (ships as: three protocol docs + three ADR-0044-style triggers, no new ADR)

- **Responsibility:** once implemented, each routine gets its own
  `docs/factory/<routine>-routine.md` protocol doc (shaped like
  `docs/factory/improvement-routine.md` — preconditions/degrade ladder,
  orient, the routine's own bounded action, report-and-journal,
  non-negotiables, amendment-by-PR — scaled to that routine's mission,
  not copied verbatim) and a scheduled trigger, same shape as
  ADR-0044's `factory-daily-improvement` (Sonnet, no MCP connectors,
  weekly cadence instead of daily, same cost-ledger-exclusion and
  pinned-journal reporting pattern). Per issue #438's own explicit
  scope bound for *this* ticket, this run's breakdown rows stop at
  "design and land this routine's protocol doc + trigger" — they do
  not attempt to author the full ~12-section protocol content now.
- **Why no ADR — this run's one judgment call, decided below.**

## Decisions & alternatives

- **The routine-ADR judgment call.** Issue #438 asks explicitly: do the
  three roster routines each need their own ADR (like the three
  mechanisms above), or are they instantiations of the already-decided
  ADR-0044 pattern needing only breakdown rows? **Decided: no new ADR
  for any of the three.** Reasoning:
  - ADR-0044 already decided the *mechanism* every roster item reuses
    verbatim: a harness-scheduled (not CI-run) cloud routine, its
    complete protocol versioned in the knowledge plane and tuned by PR
    (never self-edited), bounded to one S-sized PR and one issue per
    run, never merging its own work, reporting to a pinned journal
    issue outside the cost ledger. Nothing about a weekly cadence or a
    different mission (retro/reflect vs. queue-grooming vs. doc-
    gardening) changes any of those properties — they are new
    *instances* of one decided pattern, not a new decision about how
    unattended routines are allowed to operate in this repo.
  - Direct precedent, from the same survey batch that produced the
    ratified content this ticket formalizes:
    `docs/research/eval-and-memory.md` shortlist item 2 (Letta
    sleep-time agents — a second, mission-different scheduled
    background job) reached exactly this verdict for a comparable
    case: "Adapt, extending what already exists rather than adding new
    infrastructure... Not a new ADR: it's a scope extension of
    ADR-0044's existing routine, tunable the way that ADR is already
    tuned — by PR, never by the routine editing its own protocol."
    That survey rationale is this run's model, not a coincidence —
    applying it consistently to all three roster items is exactly the
    "whatever you decide, apply consistently" instruction issue #438
    gives.
  - The reversibility test the architect charter already uses for
    "does this need an ADR" cuts the same way: a routine's protocol
    doc and trigger are tunable by ordinary PR (ADR-0044's own
    Consequences: "the routine is tuned by PR, never by editing the
    schedule") — the same low-cost, PR-level reversibility that let
    this repo skip an ADR for `trigger_eval.py`'s composite-metric
    extension above. Three ADR-backed mechanisms above compose with or
    amend a *different* standing ADR each (ADR-0036, ADR-0005/0011,
    ADR-0032) — that is what makes them hard-to-reverse enough to
    record. The three routines compose with the *same* standing ADR
    (0044) in the *same* way its own daily instance already does.
  - Applied consistently: all three roster items get identically-shaped
    breakdown rows below (design + land a protocol doc + trigger),
    none gets an ADR, and this reasoning is restated in the PR body per
    issue #438's own instruction, not left implicit.
- **Three ADRs authored directly by this run, not deferred.** Unlike
  `docs/features/codex-style-standards-enforcement/architecture.md`
  (which explicitly declined to author its own implied ADRs because no
  human had approved that run's design yet), this run's three
  mechanisms were already ratified via HITL (issue #436) *before* this
  run started — issue #438's own text asks this ticket to produce "the
  evolution ADR set," not defer it. The human code-owner merge gate
  (ADR-0033/ADR-0036, `docs/adr/**` is always a gate change) still
  applies to this PR mechanically; what's different is that the
  *content* isn't up for renegotiation, only the merge action is.
- **No mechanical extraction, no letter reservations made now.** Each
  ADR names that a future `gates.py` detector is needed without
  claiming a letter (Open questions, `prd.md`) — claiming one now,
  before any implementation branch exists, would only risk the exact
  collision `docs/features/codex-style-standards-enforcement/
  architecture.md` already had to route around once (`J`).
- **No tracker mirror issues created by this run's Decompose pass.**
  ADR-0032's one-way rule and the planner charter both presume a
  blueprint has already cleared the human blueprint gate before rows
  become dispatch-ready; this design hasn't been through that gate.
  Mirroring now would let the dispatch plane run ahead of an unapproved
  blueprint — exactly the ordering ADR-0032 exists to prevent.

## Traceability (PRD-0006 criterion → component)

ADR-0070 exists, accepted, composes with ADR-0036 → Component 1;
ADR-0071 exists, accepted, defines marker + clarify + enforcement →
Component 2; ADR-0072 exists, accepted, defines coverage + waiver →
Component 3; README index rows for all three → this run's own
`docs/adr/README.md` edit (verified by `gates.py` detector D, not
merely asserted); trigger_eval breakdown row, no ADR → Component 4;
three routine breakdown rows, no ADR → Components 5-7; every breakdown
row cites `PRD-0006 §<section>` → `breakdown.md` (detector A); no
`WO-####` issue created → this run's own Decisions above and
`breakdown.md`'s Notes; full battery green → verified directly, below.

## Follow-on work this design deliberately does not include

- Implementing any of the seven backlog items — each is a future,
  separate implementation run, seeded by this run's breakdown rows
  only.
- The exact detector letters, waiver regex, and cascade-cost parameters
  each ADR-backed mechanism leaves open (see `prd.md`'s Open
  questions) — each future implementation run's own Architect pass
  decides these, with the fuller in-flight-branch context that pass
  will have and this run does not.
- The three routines' full per-routine protocol documents — issue
  #438 explicitly defers this; this run's breakdown rows schedule that
  work, they do not perform it.
- Mirroring any breakdown row to a `WO-####` GitHub issue — a human or
  this repo's own dispatch loop does that once this run's blueprint
  (this `architecture.md`) has cleared its own human gate.
