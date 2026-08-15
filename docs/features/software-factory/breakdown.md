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

- [x] **WO-0001** factory-init skill + template payload + manifest regeneration — size:M, blocked by: — (PRD-0001 §Solution) (tracker: #106) (pre-ledger)
  - Accept: factory-init stamps the full template payload into a scratch repo; a manifest regen command exists and detector E passes on the stamped tree.
- [x] **WO-0002** labels.json + label-sync (detector L) + CODEOWNERS template — size:S, blocked by: WO-0001 (PRD-0001 §Solution) (tracker: #107) (pre-ledger)
  - Accept: label-sync recreates the 27-label taxonomy on a bare repo and reports drift; CODEOWNERS ships in the template payload.
- [x] **WO-0003** Detector B (PR-traceability) + Makefile↔validator lockstep test — size:S, blocked by: WO-0001 (PRD-0001 §Success criteria) (tracker: #108) (pre-ledger)
  - Accept: a PR body missing the work-order citation fails B in event context and SKIPs locally; a unit test pins Makefile and CI steps in lockstep.
- [x] **WO-0004** validator.yml (check + tests + merged-label step + review job) — size:M, blocked by: WO-0003 (PRD-0001 §Solution) (tracker: #109) (pre-ledger)
  - Accept: every PR runs detectors and tests; closing a merged PR flips the lifecycle label; the review job posts findings from a non-authoring actor.
- [x] **WO-0013** minimal charters first: SWE, Reviewer, Planner (agents + SKILL.md) — size:M, blocked by: WO-0001 (PRD-0001 §Actors) (tracker: #118) (pre-ledger)
  - Accept: three agent files with `name:` frontmatter plus their SKILL.md charters load cleanly; structural lint passes.

## Milestone B: AFK dispatch (first fully unattended work order lands as a PR)

- [x] **WO-0005** assembler.yml + claude-code-action + guards — size:L, blocked by: WO-0002, WO-0004 (PRD-0001 §Solution) (tracker: #110) (pre-ledger)
  - Accept: an owner-applied ready label triggers a run that opens a PR carrying the work-order citation; a non-owner label does not fire; FACTORY_PAUSED and WIP-cap guards hold.
- [x] **WO-0006** budget_guard.py + handoff.py + cost ledger — size:M, blocked by: WO-0005 (PRD-0001 §Success criteria) (tracker: #111) (pre-ledger)
  - Accept: a deliberately over-budget run hard-stops, pushes WIP, posts a handoff naming remaining work, and appends a costs.jsonl line.
- [x] **WO-0007** model routing table + resolution — size:S, blocked by: WO-0006 (PRD-0001 §Solution) (tracker: #112) (pre-ledger)
  - Accept: each type label resolves to a model id from factory config; a unit test covers all three routes.
- [x] **WO-0015** orientation pack in assembler prompt — size:S, blocked by: WO-0005 (PRD-0001 §User stories) (tracker: #120) (pre-ledger)
  - Accept: the assembler prompt bundles CONTEXT.md, cited ADRs, and a codegraph summary for the dispatched work order via orientation_pack.py.

## Milestone C: Self-observation (weekly report, sweeps, honesty gates)

- [x] **WO-0008** Detectors D (blueprint-drift) + G (cost-ledger) + I (staleness) — size:M, blocked by: WO-0003 (PRD-0001 §Solution) (tracker: #113) (pre-ledger)
  - Accept: planted drift, ledger-gap, and stale-doc fixtures are each caught by selftest; the clean tree stays silent.
- [x] **WO-0009** cost-report.yml + monthly circuit breaker — size:S, blocked by: WO-0006 (PRD-0001 §User stories) (tracker: #114) (pre-ledger)
  - Accept: the weekly report issue posts numbers recomputed from costs.jsonl; a simulated cap breach sets FACTORY_PAUSED.
- [x] **WO-0010** sweeps.yml + sentry-intake stamping — size:M, blocked by: WO-0002 (PRD-0001 §Success criteria) (tracker: #115) (pre-ledger)
  - Accept: a sweep files a triaged draft issue with source and type labels applied, no human transcription.
- [x] **WO-0011** Detector H (evidence honesty) — size:S, blocked by: WO-0003 (PRD-0001 §Success criteria) (tracker: #116) (pre-ledger)
  - Accept: a verification artifact with neither literal command output nor an explicit NOT-RUN disclaimer fails the build; selftest covers both branches.
- [x] **WO-0012** design pipeline: docs/design template + playwright/web-quality job — size:M, blocked by: WO-0004 (PRD-0001 §Solution) (tracker: #117) (pre-ledger)
  - Accept: a PR touching design docs triggers the playwright + web-quality job; the design-system seed ships in the template payload.
- [x] **WO-0017** gate-queue daily digest + gate-latency capture — size:S, blocked by: WO-0009 (PRD-0001 §User stories) (tracker: #122) (pre-ledger)
  - Accept: a pinned digest lists items waiting at each gate; gate-latency rows land in costs.jsonl.

## Milestone D: Charter maturity (full role set, regression CI, feedback mining)

- [x] **WO-0014** full 9-role charter set + CHARTERS.md + gate checklists — size:L, blocked by: WO-0013 (PRD-0001 §Actors) (tracker: #119) (pre-ledger)
  - Accept: all nine agent+skill charter pairs exist; CHARTERS.md indexes them with the three gate checklists; structural lint passes.
- [x] **WO-0016** charter regression suite (golden fixture replays) — size:M, blocked by: WO-0013 (PRD-0001 §Actors) (tracker: #121) (pre-ledger)
  - Accept: golden fixture work orders replay on plugin PRs via a cheap model; a deliberately degraded charter fails the suite.
- [x] **WO-0018** rejection mining into the toolsmith queue — size:S, blocked by: WO-0009 (PRD-0001 §User stories) (tracker: #123)
  - Accept: a weekly job harvests gate rejections and PR change-requests into the toolsmith/claude-reflect queue.

## Milestone E: Review re-entry (gate integrity + first live dispatch)

Added 2026-08-14 from review.md's fix loop — the critical and the
surgical majors the operator routed back to Implement, plus the
supervised live-dispatch exercise verification.md recommended.

- [x] **WO-0030** factory PRs trigger their own validator — size:S, blocked by: WO-0005 (PRD-0001 §Success criteria) (tracker: #280)
  - Accept: validator.yml gains a workflow_dispatch trigger resolving a PR by number; the assembler dispatches it after the agent's PR opens (the GITHUB_TOKEN workflow_dispatch escape hatch), so a factory-opened PR gets check, review, and needs-review-label runs.
- [ ] **WO-0031** run-spend ledger row survives the runner — size:S, blocked by: WO-0006 (PRD-0001 §Success criteria) (tracker: #281)
  - Accept: assembler.yml commits and pushes the costs.jsonl row wo-record appended (gate-digest.yml's commit pattern); a run's spend row lands on main without human touch.
- [ ] **WO-0032** hard_stop records before it pushes — size:S, blocked by: WO-0006 (PRD-0001 §Success criteria) (tracker: #282)
  - Accept: the exhaustion ledger row is appended before push_wip so it is inside the pushed commit; a test pins the persistence ordering, not just local file existence.
- [ ] **WO-0033** fail-closed pause verdicts enforce — size:S, blocked by: WO-0009 (PRD-0001 §Success criteria) (tracker: #283)
  - Accept: when run_report exits nonzero with pause=true, the cost-report workflow still sets FACTORY_PAUSED; a test pins that outputs are written before the failing exit.
- [ ] **WO-0034** mechanical stops on the agent job — size:S, blocked by: WO-0005 (PRD-0001 §Solution) (tracker: #284)
  - Accept: the agent step carries --max-turns and the job carries timeout-minutes (ADR-0034's two uncorrelated mechanical stops); setup.md discloses that the payload ships the dispatch workflow without charters; an ADR records the budget-hook and payload-charter deferrals.
- [ ] **WO-0035** supervised live dispatch: rejection_mining hardening — size:S, blocked by: WO-0030, WO-0031, WO-0033, WO-0034 (PRD-0001 §Success criteria) (tracker: #285)
  - Accept: excerpts in the toolsmith queue are sanitized and fenced per ADR-0032 (sweeps.py's pattern) and duplicate Closes refs are deduped; delivered by a real dispatch the owner drives through wo:draft → wo:prd-approved → wo:blueprint-approved → wo:ready-for-agent to a merged PR — the run's first end-to-end gate traversal.

## Design gaps found

None — dispatch, gating, and budget design are settled in ADR-0032,
ADR-0033, and ADR-0034 (all accepted).

## Notes

- 2026-07-12: PRD open question "beads adoption timing" answered here —
  adopted at mirror time; the dependency graph above is recorded in beads
  when rows are mirrored to the tracker. **Superseded by ADR-0035
  (2026-07-12):** GitHub issues are the single work-order mirror; beads is
  not a work-order mirror. The dependency graph rides the GitHub issues and
  the blocking-edge tokens on the rows, not beads.
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
  `factory/charters/<role>/CHARTER.md`, but Claude Code discovers subagents
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
- 2026-07-12: the sweeps order (WO-0010, PRD-0001 §Success criteria) ships
  self-hosted only — `sweeps.py` and `.github/workflows/sweeps.yml` live at
  the repo root, not in `factory/templates/**`. No workflow is in the
  template payload yet (the validator and assembler orders own the first
  ones), and stamping a sweep tool without the workflow that calls it would
  put a half-feature under detector E's checksum pin. The payload gains the
  workflows when those orders build them.
- 2026-07-12: sweeps file **intake**, never work orders (ADR-0032). The
  triage table maps a sweep kind to exactly one `source:*` plus one `type:*`
  label and can express no `wo:*` lifecycle label; a pre-flight screen
  re-verifies every label against `labels.json` and drops any plan naming
  a work-order id, so the dispatch plane cannot run ahead of a breakdown row.
- 2026-07-12: a sweep cannot file until the labels it stamps exist —
  `gh issue create --label X` resolves X server-side and aborts on an unknown
  one, which would have left the label-drift sweep unable to report the very
  drift that silenced it. `sweeps.py ensure-labels` runs as its own step
  before both sweeps and creates only the *absent* triage labels, so the rest
  of the taxonomy stays drifted for the sweep to report to a human rather
  than being healed away behind its back.
- 2026-07-12: the sweeps order's acceptance criterion (WO-0010, PRD-0001
  §Success criteria) is demonstrated by the offline suite alone
  (`tests/test_sweeps.py`, gh runner injected) — **no scheduled sweep has yet
  run against GitHub**, so no intake issue has been filed by the workflow
  itself. The first Monday run is the live evidence; until then the criterion
  is proven in principle, not in production.
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
- 2026-07-12: orientation-module deviation — the orientation pack
  (WO-0015, PRD-0001 §User stories) ships as `orientation_pack.py`, not
  the `orientation.py` this row's accept line originally named. The repo root
  already carries an unrelated `orientation.py` — ADR-0021's CLI adapter
  over `protocol.py`'s `next_stage`, the idea-to-prod pipeline's "which
  stage is next" tool, with its own `tests/test_protocol_orientation.py` and
  `tests/fixtures/orientation/` — because the factory's tools and the
  idea-to-prod skills share this repo's root namespace. Renaming avoided
  overwriting a shipped, tested, unrelated feature; the row's accept line
  is amended to match what shipped, same as the labels.json deviation
  above.
- 2026-07-19: checkbox reconciliation — five orders merged without their rows
  being ticked (PRs #153, #156, #157, #158, and #152); the boxes above are
  corrected to match `main`. Git is authoritative for merge state; the
  checkboxes are the convenience that had drifted, and only the two open orders
  (trackers #122 and #123) are genuinely unbuilt.
- 2026-08-14: Milestone E added at Review — review.md found 1 critical
  (factory PRs never trigger validator.yml; GITHUB_TOKEN event
  suppression) and 5 majors. The operator arbitrated: the critical and
  the surgical majors route back here as the first five Milestone E
  rows (WO-0030..WO-0034, PRD-0001 §Success criteria), with the
  budget hook and payload charters deferred by ADR instead
  (WO-0034, PRD-0001 §Solution, records the deferral); the last row
  (WO-0035, PRD-0001 §Success criteria) is verification.md's
  supervised live-dispatch exercise, carrying two of the review's
  deferred minors as its payload. The run re-enters Implement; Verify
  and Review re-run after Milestone E.
