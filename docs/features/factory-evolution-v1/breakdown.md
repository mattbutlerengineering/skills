---
stage: decompose
run: feature:factory-evolution-v1
date: 2026-09-21
assumptions:
  - "No tracker mirror issues created for any row below (ADR-0032's one-way rule and the planner charter both presume the blueprint already passed the human blueprint gate; this run's architecture.md has not). See Notes."
  - "WO ids continue the repo-global sequence, starting at order 65 — the highest claimed id found across every docs/features/*/breakdown.md at the time this run started was order 64 (docs/features/codex-style-standards-enforcement/breakdown.md)."
---

# Breakdown: Factory evolution backlog seed

Progress lives in the checkboxes below — Implement checks items off as
their acceptance criteria are met, on whichever future run picks up
each row (this run itself stops at Decompose; see architecture.md).
Row grammar per this repo's existing convention: one line per work
order carrying id, size class, blocking edges, and the PRD citation
detector A checks.

## Milestone A: ADR-backed mechanisms (the three ADRs already exist as of this run — orders 65-67 land their implementation)

- [ ] **WO-0065** implement GitHub native merge queue adoption (ADR-0070) — size:M, blocked by: — (PRD-0006 §Success criteria)
  - Accept: GitHub's merge queue is enabled on the branch-protection rule guarding `main`; every required-check workflow mirrored via `factory_init.MIRRORS` (`.github/workflows/validator.yml` and siblings) gains `merge_group` as a trigger; the cascade-cost and queue-admission-vs-review-requirement questions ADR-0070 and `prd.md`'s Open questions leave open are resolved and recorded in that future run's own `verification.md`; the battery stays green. This is a repo-settings + workflow-trigger change, not a `gates.py`/Python change — no new detector is implied by this row alone.
- [x] **WO-0066** implement inline `[NEEDS CLARIFICATION]` markers + bounded clarify pass + CI enforcement (ADR-0071) — size:M, blocked by: — (PRD-0006 §Success criteria)
  - Accept: `skills/prd/TEMPLATE.md` and `skills/architect/TEMPLATE.md` document the marker syntax; the PRD skill's process gains a bounded clarify step (max 5 questions per pass, taxonomy from the artifact's own section headings, answers written back under a dated `### Clarifications / Session YYYY-MM-DD` heading); a new `gates.py` detector (letter chosen at implementation time, avoiding whatever is claimed by then) fails when a `prd.md` or `architecture.md` carries an unresolved marker, with `python3 gates.py --selftest` coverage; the battery stays green.
- [x] **WO-0067** implement bidirectional PRD-requirement<->work-item coverage check (ADR-0072) — size:M, blocked by: — (PRD-0006 §Success criteria)
  - Accept: detector A (or a sibling detector, implementation's call per ADR-0072) fails when a `prd.md` `§` section with a declared `id: PRD-####` is cited by zero breakdown rows and carries no `<!-- coverage-waiver: <reason> -->` comment; `python3 gates.py --selftest` covers both the uncovered-and-unwaived failure and the declared-waiver pass case; the battery stays green. Independent of the two rows above — implementable in parallel.

## Milestone B: Non-ADR derived-metric extension

- [ ] **WO-0068** derive per-skill precision/recall/F1 from `trigger_eval.py`'s existing confusion matrix — size:S, blocked by: — (PRD-0006 §Success criteria)
  - Accept: a new pure function in `trigger_eval.py` reads `summarize()`'s `confusion` dict and computes per-skill precision, recall, and F1 as a second pass over already-recorded results — no re-running any eval, no touching `evals/results/**` (append-only, CLAUDE.md eval honesty); unit tests cover the derivation against a fixture confusion matrix; the function is wired to answer `docs/backlog.md`'s existing "omp near-miss under-triggering: 8/16 near-miss cases under-trigger" seed with a trackable number. No new ADR (per `docs/research/eval-and-memory.md` shortlist item 5's own verdict — this row implements it as-is). Independent of every other row in this breakdown — implementable in parallel with any of them.

## Milestone C: Routine roster v2 (design + land the protocol doc + trigger only — issue #438's own scope bound; no new ADR, per architecture.md's Decisions)

- [ ] **WO-0069** design and land the weekly retro/reflect-deepening routine's protocol doc + ADR-0044-style trigger — size:M, blocked by: — (PRD-0006 §Success criteria)
  - Accept: `docs/factory/retro-reflect-routine.md` exists, shaped like `docs/factory/improvement-routine.md` (preconditions/degrade ladder, orient, one bounded action per run, report-and-journal, non-negotiables, amendment-by-PR) but scoped to this routine's own mission — a deeper weekly pass over the correction stream than the daily routine's own §6 Reflect step already does, per issue #437's roster decision; a weekly-cadence Sonnet trigger exists with no MCP connectors, reporting to the same pinned journal issue pattern, cost-ledger-excluded exactly as ADR-0044 already decided for the daily routine. This row does not author the full ~12-section protocol content beyond what "design and land" requires to actually run once — per issue #438's explicit deferral of full protocol rigor to this future run itself.
- [ ] **WO-0070** design and land the queue-groomer routine's protocol doc + ADR-0044-style trigger — size:M, blocked by: — (PRD-0006 §Success criteria)
  - Accept: `docs/factory/queue-groomer-routine.md` exists, same shape as its sibling row above, scoped to grooming the ready queue (stale/blocked `wo:*`-labeled issues, `docs/backlog.md` seed hygiene) rather than reflect-loop mining; same weekly-cadence, Sonnet, no-MCP-connectors, cost-ledger-excluded trigger shape as ADR-0044's daily routine.
- [ ] **WO-0071** design and land the doc-gardener routine's protocol doc + ADR-0044-style trigger — size:M, blocked by: — (PRD-0006 §Success criteria)
  - Accept: `docs/factory/doc-gardener-routine.md` exists, same shape as its two sibling rows above, scoped to documentation hygiene (stale cross-references, drifted `docs/adr/README.md`-style indexes outside what `gates.py`'s own detectors already gate, LEDGER.md upkeep) rather than reflect-loop mining or queue grooming; same weekly-cadence, Sonnet, no-MCP-connectors, cost-ledger-excluded trigger shape.

## Milestone D: Close-out

- [ ] **WO-0072** full battery green across every item above, PRD-0006 traceability re-check — size:S, blocked by: WO-0065, WO-0066, WO-0067, WO-0068, WO-0069, WO-0070, WO-0071 (PRD-0006 §Success criteria)
  - Accept: `python3 -m unittest discover tests`, `python3 lint.py`, and `python3 gates.py && python3 gates.py --selftest` are all green with every prior row's changes present; PRD-0006's success criteria are re-walked one by one against what actually landed (Verify's job, scaled to this feature — the run's own `verification.md`, when this feature run continues past this breakdown); epic #439's map Destination ("Done when nothing is left to decide before building starts") is re-checked against the state of all seven items.

## Design gaps found

None — every one of `architecture.md`'s seven numbered components maps
to exactly one milestone row above (Components 1-3 → Milestone A;
Component 4 → Milestone B; Components 5-7 → Milestone C), and the
close-out row exists purely to re-verify the battery and traceability,
not to cover an unmapped component.

## Notes

- 2026-09-21: **no tracker mirror issues were created for any row
  above.** ADR-0032's one-way rule and the planner charter both
  presume a blueprint has already cleared the human blueprint gate
  (ADR-0033) before its rows become dispatch-ready; `architecture.md`
  has not been through that gate in this run. Mirroring now would let
  the dispatch plane run ahead of an unapproved blueprint — exactly
  the ordering ADR-0032 exists to prevent. Export happens at a real
  Decompose pass, after a human has approved this run's `prd.md` and
  `architecture.md`, not as part of this unattended planning pass —
  matching `docs/features/codex-style-standards-enforcement/
  breakdown.md`'s identical precedent for the same situation.
- 2026-09-21: **the three ADRs this milestone's rows implement
  (0070/0071/0072) already exist as of this run**, unlike
  `codex-style-standards-enforcement`'s own Milestone A (which had to
  schedule authoring its ADR as a future row, order 51, because no
  human had ratified that run's design yet). This run's design was
  already ratified via HITL before it started (issue #436), so issue
  #438 asked this ticket to author the ADRs directly — orders 65-67
  are the *implementation* of what the ADRs already decided, not the
  ADR-authoring step itself.
- 2026-09-21: **orders 69-71 (the routine roster) deliberately carry
  no ADR citation beyond ADR-0044** and no new ADR is authored for any
  of them — `architecture.md`'s Decisions section records the full
  reasoning (extending ADR-0044's already-decided pattern, direct
  precedent from `docs/research/eval-and-memory.md` shortlist item 2's
  own "extend ADR-0044, no new ADR" verdict for a comparable second
  scheduled routine), applied identically to all three so none is
  treated as more or less ADR-worthy than its siblings.
- 2026-09-21: **every row above is unblocked by every other** except
  the close-out row — the seven backlog items were ratified
  independently (different survey sources, different mechanisms) and
  nothing in `architecture.md` makes any one a prerequisite for
  another; sequencing them is a future dispatch-time choice, not a
  dependency this breakdown asserts.
- 2026-09-23: **orders 66-67 landed as detectors N (NEEDS-CLARIFICATION)
  and O (PRD-COVERAGE)** — answering `prd.md`'s first and third Open
  questions. K and M were skipped as reserved by the in-flight
  standards-enforcement work (PR #517), not by anything on `main`. O is
  a sibling letter, not a widening of A (ADR-0072's own lean: A's
  contract stays one-directional). O grandfathers PRDs dated before
  ADR-0072 (2026-09-21) — PRD-0001 through PRD-0005 were decomposed
  before the rule existed — and this run's own PRD-0006, dated on it,
  carries honest `coverage-waiver` comments on the six sections no row
  cites, as ADR-0072's Consequences ask. O skips a run with no
  `breakdown.md` yet: coverage is a Decompose-time property.
