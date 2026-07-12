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

- [x] **WO-0001** factory-init skill + template payload + manifest regeneration — size:M, blocked by: — (PRD-0001 §Solution) (tracker: #106)
  - Accept: factory-init stamps the full template payload into a scratch repo; a manifest regen command exists and detector E passes on the stamped tree.
- [x] **WO-0002** labels.json + label-sync (detector L) + CODEOWNERS template — size:S, blocked by: WO-0001 (PRD-0001 §Solution) (tracker: #107)
  - Accept: label-sync recreates the 27-label taxonomy on a bare repo and reports drift; CODEOWNERS ships in the template payload.
- [x] **WO-0003** Detector B (PR-traceability) + Makefile↔validator lockstep test — size:S, blocked by: WO-0001 (PRD-0001 §Success criteria) (tracker: #108)
  - Accept: a PR body missing the work-order citation fails B in event context and SKIPs locally; a unit test pins Makefile and CI steps in lockstep.
- [x] **WO-0004** validator.yml (check + tests + merged-label step + review job) — size:M, blocked by: WO-0003 (PRD-0001 §Solution) (tracker: #109)
  - Accept: every PR runs detectors and tests; closing a merged PR flips the lifecycle label; the review job posts findings from a non-authoring actor.
- [x] **WO-0013** minimal charters first: SWE, Reviewer, Planner (agents + SKILL.md) — size:M, blocked by: WO-0001 (PRD-0001 §Actors) (tracker: #118)
  - Accept: three agent files with `name:` frontmatter plus their SKILL.md charters load cleanly; structural lint passes.

## Milestone B: AFK dispatch (first fully unattended work order lands as a PR)

- [ ] **WO-0005** assembler.yml + claude-code-action + guards — size:L, blocked by: WO-0002, WO-0004 (PRD-0001 §Solution) (tracker: #110)
  - Accept: an owner-applied ready label triggers a run that opens a PR carrying the work-order citation; a non-owner label does not fire; FACTORY_PAUSED and WIP-cap guards hold.
- [ ] **WO-0006** budget_guard.py + handoff.py + cost ledger — size:M, blocked by: WO-0005 (PRD-0001 §Success criteria) (tracker: #111)
  - Accept: a deliberately over-budget run hard-stops, pushes WIP, posts a handoff naming remaining work, and appends a costs.jsonl line.
- [ ] **WO-0007** model routing table + resolution — size:S, blocked by: WO-0006 (PRD-0001 §Solution) (tracker: #112)
  - Accept: each type label resolves to a model id from factory config; a unit test covers all three routes.
- [ ] **WO-0015** orientation pack in assembler prompt — size:S, blocked by: WO-0005 (PRD-0001 §User stories) (tracker: #120)
  - Accept: the assembler prompt bundles CONTEXT.md, cited ADRs, and a codegraph summary for the dispatched work order via orientation.py.

## Milestone C: Self-observation (weekly report, sweeps, honesty gates)

- [x] **WO-0008** Detectors D (blueprint-drift) + G (cost-ledger) + I (staleness) — size:M, blocked by: WO-0003 (PRD-0001 §Solution) (tracker: #113)
  - Accept: planted drift, ledger-gap, and stale-doc fixtures are each caught by selftest; the clean tree stays silent.
- [ ] **WO-0009** cost-report.yml + monthly circuit breaker — size:S, blocked by: WO-0006 (PRD-0001 §User stories) (tracker: #114)
  - Accept: the weekly report issue posts numbers recomputed from costs.jsonl; a simulated cap breach sets FACTORY_PAUSED.
- [ ] **WO-0010** sweeps.yml + sentry-intake stamping — size:M, blocked by: WO-0002 (PRD-0001 §Success criteria) (tracker: #115)
  - Accept: a sweep files a triaged draft issue with source and type labels applied, no human transcription.
- [ ] **WO-0011** Detector H (evidence honesty) — size:S, blocked by: WO-0003 (PRD-0001 §Success criteria) (tracker: #116)
  - Accept: a verification artifact with neither literal command output nor an explicit NOT-RUN disclaimer fails the build; selftest covers both branches.
- [ ] **WO-0012** design pipeline: docs/design template + playwright/web-quality job — size:M, blocked by: WO-0004 (PRD-0001 §Solution) (tracker: #117)
  - Accept: a PR touching design docs triggers the playwright + web-quality job; the design-system seed ships in the template payload.
- [ ] **WO-0017** gate-queue daily digest + gate-latency capture — size:S, blocked by: WO-0009 (PRD-0001 §User stories) (tracker: #122)
  - Accept: a pinned digest lists items waiting at each gate; gate-latency rows land in costs.jsonl.

## Milestone D: Charter maturity (full role set, regression CI, feedback mining)

- [x] **WO-0014** full 9-role charter set + CHARTERS.md + gate checklists — size:L, blocked by: WO-0013 (PRD-0001 §Actors) (tracker: #119)
  - Accept: all nine agent+skill charter pairs exist; CHARTERS.md indexes them with the three gate checklists; structural lint passes.
- [x] **WO-0016** charter regression suite (golden fixture replays) — size:M, blocked by: WO-0013 (PRD-0001 §Actors) (tracker: #121)
  - Accept: golden fixture work orders replay on plugin PRs via a cheap model; a deliberately degraded charter fails the suite.
- [ ] **WO-0018** rejection mining into the toolsmith queue — size:S, blocked by: WO-0009 (PRD-0001 §User stories) (tracker: #123)
  - Accept: a weekly job harvests gate rejections and PR change-requests into the toolsmith/claude-reflect queue.

## Design gaps found

None — dispatch, gating, and budget design are settled in ADR-0032,
ADR-0033, and ADR-0034 (all accepted).

## Notes

- 2026-07-12: PRD open question "beads adoption timing" answered here —
  adopted at mirror time; the dependency graph above is recorded in beads
  when rows are mirrored to the tracker.
- 2026-07-12: the template payload carries machine-copied mirrors of
  `gates.py` and `protocol.py` (stamped detectors import their sibling
  frontmatter seam; refreshed by `factory_init.py update-manifest`,
  pinned by detector E) — one source of truth at the repo root, no
  hand-maintained second copy.
- 2026-07-12: template deviation — blocking edges live on the row line, not
  a `Blocked by:` sub-bullet, because the traceability gate reads any line
  bearing a work-order token as a row requiring a PRD citation.
- 2026-07-12: merge-gate enforcement remains convention + CI on this
  private free-plan repo (PRD open question); physical branch protection
  activates when the repo goes Pro or public.
- 2026-07-12: label-taxonomy deviation — the taxonomy ships as
  `labels.json`, not the `labels.yml` the Milestone A label-sync row
  originally named (the row title is renamed to match what shipped; this
  note is written without the work-order token because detector A reads any
  line carrying one as a row needing a PRD citation). Stdlib-only is the
  first hard convention (CLAUDE.md) and Python's standard library has no
  YAML parser, so detector L could never have read a `.yml` taxonomy without
  a third-party dependency; JSON is also what `gh label list --json` returns,
  so the desired and live shapes match.
- 2026-07-12: open gap — the charters (WO-0013, PRD-0001 §Actors) have
  **no load path**. They live at `factory/agents/*.md` +
  `factory/skills/<role>/SKILL.md`, but Claude Code discovers subagents
  only under `.claude/agents/` or `<plugin-root>/agents/`; nothing
  discovers or stamps this path today, so the charters are inert and no
  row owns wiring them up. They stay out of `factory/templates/**`
  deliberately: detector E checksum-pins that tree, and the full charter
  set (WO-0014, PRD-0001 §Actors) will churn them heavily. The assembler
  order (WO-0005, PRD-0001 §Solution) is the natural owner — it builds the
  dispatched run's environment — and the charter regression replays
  (WO-0016, PRD-0001 §Actors) presuppose the load path it would create.
  To be settled when the assembler is implemented; no row is invented
  here (ADR-0032, one-way mirror).
- 2026-07-12: the validator workflow (WO-0004, PRD-0001 §Solution) is BOTH
  this repo's CI and the payload's — one file, machine-mirrored root →
  `factory/templates/.github/workflows/`, joining `gates.py`/`protocol.py`
  in `factory_init.MIRRORS`. It can be one file because it names no command
  of its own: every step calls a `make` target, and each repo's Makefile
  knows where its tools live (root here, `tools/factory/` there). The old
  `checks.yml` is gone — it was the check job, now `make check`. A root
  Makefile is new here, and the template Makefile's "exactly what CI runs"
  comment is finally true.
- 2026-07-12: charter-regression deviation — the golden-fixture replays
  (WO-0016, PRD-0001 §Actors) run **on demand** (`python3
  charter_replay.py`) and through a manual `workflow_dispatch` job, never
  automatically on plugin PRs as that row's accept line says. A replay is a
  real model run, and never-real-models-in-CI is a hard convention
  (CLAUDE.md; `trigger_eval.py` is the precedent) — a PR-triggered replay
  would spend money on every push, and the owner ruled the convention wins
  over the accept line's wording. What CI does cover is the suite's pure
  scoring seam: the model runner is injected, so the transcripts a
  deliberately degraded charter produces are replayed offline in
  `tests/test_charter_replay.py` and fail the suite with no model in the
  loop. The live model↔charter link itself is only observable in an
  on-demand replay, and no such run has been recorded yet.
- 2026-07-12: charters carry a routing *band* (`route: implementation` or
  `architecture_review`), never a model id — the band resolves through
  `factory.json`'s routing table, which the routing order
  (WO-0007, PRD-0001 §Solution) wires up. A `model:` in a charter would be
  a second routing source of truth (ADR-0004), which is the drift this
  factory exists to catch.
- 2026-07-12: the charter index ships as `factory/CHARTERS.md`, beside the
  charters it indexes, not at the repo root — it is factory-internal, and
  the same reasoning keeps the whole set out of `factory/templates/**`
  (detector E checksum-pins that tree; charters churn). The load-path gap
  noted above is unchanged: nine charters now exist and still nothing
  discovers them (WO-0005's assembler, PRD-0001 §Solution, remains the
  natural owner).
- 2026-07-12: bands are assigned by work class, not by seniority —
  `architecture_review` for the roles whose artifact a human gate approves
  as judgment (PM at gate 1, architect and UX at gate 2) plus the review
  that pre-chews gate 3; `implementation` for planner, engineer, QA,
  toolsmith; `mechanical` for support, whose intake and label plumbing is
  the class ADR-0034 names for the cheap model.
- 2026-07-12: the six charters added beyond the first three carry
  `UNRATED` loadout tiers. The `MEASURED`/`RUN` tiers in the first three
  come from the ai-tooling evidence base; no such result exists for the new
  picks, and inventing one would be fabricated evidence (CLAUDE.md). They
  graduate only on a real run.
