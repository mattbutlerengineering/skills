---
stage: decompose
run: feature:software-factory
date: 2026-07-12
assumptions:
  - "architecture.md absent — design source is the approved technical plan's M1 table plus ADR-0032/ADR-0033/ADR-0034, operator-directed at decompose time"
  - "beads adoption timing (PRD open question): adopted now — dependency graph recorded at issue-mirror time"
---

# Breakdown: Software factory v1 (self-host)

Progress lives in the checkboxes below — Implement checks items off as their
acceptance criteria are met. Row grammar is one line per work order carrying
id, size class (ADR-0034), blocking edges, and the PRD citation the
traceability gate (detector A) checks; tracker mirror numbers are appended
per ADR-0032 after each row exists here first.

## Milestone A: Scaffolding + validation line (factory-init stamps a repo; PRs validated; minimal charters exist)

- [ ] **WO-0001** factory-init skill + template payload + manifest regeneration — size:M, blocked by: — (PRD-0001 §Solution)
  - Accept: factory-init stamps the full template payload into a scratch repo; a manifest regen command exists and detector E passes on the stamped tree.
- [ ] **WO-0002** labels.yml + label-sync (detector L) + CODEOWNERS template — size:S, blocked by: WO-0001 (PRD-0001 §Solution)
  - Accept: label-sync recreates the 27-label taxonomy on a bare repo and reports drift; CODEOWNERS ships in the template payload.
- [ ] **WO-0003** Detector B (PR-traceability) + Makefile↔validator lockstep test — size:S, blocked by: WO-0001 (PRD-0001 §Success criteria)
  - Accept: a PR body missing the work-order citation fails B in event context and SKIPs locally; a unit test pins Makefile and CI steps in lockstep.
- [ ] **WO-0004** validator.yml (check + tests + merged-label step + review job) — size:M, blocked by: WO-0003 (PRD-0001 §Solution)
  - Accept: every PR runs detectors and tests; closing a merged PR flips the lifecycle label; the review job posts findings from a non-authoring actor.
- [ ] **WO-0013** minimal charters first: SWE, Reviewer, Planner (agents + SKILL.md) — size:M, blocked by: WO-0001 (PRD-0001 §Actors)
  - Accept: three agent files with `name:` frontmatter plus their SKILL.md charters load cleanly; structural lint passes.

## Milestone B: AFK dispatch (first fully unattended work order lands as a PR)

- [ ] **WO-0005** assembler.yml + claude-code-action + guards — size:L, blocked by: WO-0002, WO-0004 (PRD-0001 §Solution)
  - Accept: an owner-applied ready label triggers a run that opens a PR carrying the work-order citation; a non-owner label does not fire; FACTORY_PAUSED and WIP-cap guards hold.
- [ ] **WO-0006** budget_guard.py + handoff.py + cost ledger — size:M, blocked by: WO-0005 (PRD-0001 §Success criteria)
  - Accept: a deliberately over-budget run hard-stops, pushes WIP, posts a handoff naming remaining work, and appends a costs.jsonl line.
- [ ] **WO-0007** model routing table + resolution — size:S, blocked by: WO-0006 (PRD-0001 §Solution)
  - Accept: each type label resolves to a model id from factory config; a unit test covers all three routes.
- [ ] **WO-0015** orientation pack in assembler prompt — size:S, blocked by: WO-0005 (PRD-0001 §User stories)
  - Accept: the assembler prompt bundles CONTEXT.md, cited ADRs, and a codegraph summary for the dispatched work order via orientation.py.

## Milestone C: Self-observation (weekly report, sweeps, honesty gates)

- [ ] **WO-0008** Detectors D (blueprint-drift) + G (cost-ledger) + I (staleness) — size:M, blocked by: WO-0003 (PRD-0001 §Solution)
  - Accept: planted drift, ledger-gap, and stale-doc fixtures are each caught by selftest; the clean tree stays silent.
- [ ] **WO-0009** cost-report.yml + monthly circuit breaker — size:S, blocked by: WO-0006 (PRD-0001 §User stories)
  - Accept: the weekly report issue posts numbers recomputed from costs.jsonl; a simulated cap breach sets FACTORY_PAUSED.
- [ ] **WO-0010** sweeps.yml + sentry-intake stamping — size:M, blocked by: WO-0002 (PRD-0001 §Success criteria)
  - Accept: a sweep files a triaged draft issue with source and type labels applied, no human transcription.
- [ ] **WO-0011** Detector H (evidence honesty) — size:S, blocked by: WO-0003 (PRD-0001 §Success criteria)
  - Accept: a verification artifact with neither literal command output nor an explicit NOT-RUN disclaimer fails the build; selftest covers both branches.
- [ ] **WO-0012** design pipeline: docs/design template + playwright/web-quality job — size:M, blocked by: WO-0004 (PRD-0001 §Solution)
  - Accept: a PR touching design docs triggers the playwright + web-quality job; the design-system seed ships in the template payload.
- [ ] **WO-0017** gate-queue daily digest + gate-latency capture — size:S, blocked by: WO-0009 (PRD-0001 §User stories)
  - Accept: a pinned digest lists items waiting at each gate; gate-latency rows land in costs.jsonl.

## Milestone D: Charter maturity (full role set, regression CI, feedback mining)

- [ ] **WO-0014** full 9-role charter set + CHARTERS.md + gate checklists — size:L, blocked by: WO-0013 (PRD-0001 §Actors)
  - Accept: all nine agent+skill charter pairs exist; CHARTERS.md indexes them with the three gate checklists; structural lint passes.
- [ ] **WO-0016** charter regression suite (golden fixture replays) — size:M, blocked by: WO-0013 (PRD-0001 §Actors)
  - Accept: golden fixture work orders replay on plugin PRs via a cheap model; a deliberately degraded charter fails the suite.
- [ ] **WO-0018** rejection mining into the toolsmith queue — size:S, blocked by: WO-0009 (PRD-0001 §User stories)
  - Accept: a weekly job harvests gate rejections and PR change-requests into the toolsmith/claude-reflect queue.

## Design gaps found

None — dispatch, gating, and budget design are settled in ADR-0032,
ADR-0033, and ADR-0034 (all accepted).

## Notes

- 2026-07-12: PRD open question "beads adoption timing" answered here —
  adopted at mirror time; the dependency graph above is recorded in beads
  when rows are mirrored to the tracker.
- 2026-07-12: template deviation — blocking edges live on the row line, not
  a `Blocked by:` sub-bullet, because the traceability gate reads any line
  bearing a work-order token as a row requiring a PRD citation.
- 2026-07-12: merge-gate enforcement remains convention + CI on this
  private free-plan repo (PRD open question); physical branch protection
  activates when the repo goes Pro or public.
