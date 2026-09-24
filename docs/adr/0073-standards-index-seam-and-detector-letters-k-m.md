# Standards index as a seam module; detector letters K and M

- Status: accepted
- Date: 2026-09-21

## Context

- Issue #448 / PRD-0004 (`docs/features/codex-style-standards-enforcement/
  {idea,prd,architecture,breakdown}.md`) designed a Codex-style normative-
  statement index: `docs/standards.json`, a new `standards_index.py`
  seam module, two new `gates.py` detectors, and standards-aware
  load/cite steps in the review and architect skills/charters.
- `architecture.md` recorded three decisions inline, in its own
  "Decisions & alternatives" section, because that design pass stopped
  at Decompose with no human available in-session to clear the gate-2
  blueprint approval (ADR-0033) a real ADR requires: (a) the new module's
  seam justification, (b) which detector letters the two new checks
  claim and why `J` is not one of them, (c) where enforcement status
  lives. `breakdown.md`'s WO-0051 exists precisely to turn those into a
  real, human-approved ADR once that approval exists — this ADR is that
  step, authored in the same session that implements Milestones A and B
  of that breakdown.
- This ADR records the design as `architecture.md` reasoned it, and
  additionally verifies each claim against `gates.py` as it stands at
  authoring time (2026-09-21, after PR #516 "detector J's own roster
  table still called it unused" merged to main) rather than copying
  `architecture.md`'s day-old snapshot forward uncritically.

## Decision

**(a) `standards_index.py` joins the factory's seam-module set
(ADR-0037's convention: multiple real callers AND observed/expected
divergence, not anticipated reuse).** The bar is met the same way
`cost_ledger.py` meets it for detector G: the regeneration script
(`standards_index.py update`) must parse `docs/adr/*.md`'s
`## Normative statements` sections and build the statement shape in
order to *write* `docs/standards.json`, and `gates.py`'s detector `K`
must independently rebuild the same ADR-derived subset in order to
*validate* the committed file against a fresh regeneration — two real
call sites needing the identical parsing/shape logic from the moment
`K` exists, not after a divergence is later observed. A third
consumer — the base `review`/`architect` skills and the
`factory-reviewer`/`factory-architect` charters — reads
`docs/standards.json` directly as data (prose an agent follows, not a
Python import), so it does not count toward the module-boundary bar
itself, but it is the reason the shape has to be a stable, documented
contract rather than a private implementation detail of the two Python
callers. Folding the regen+validate logic straight into `gates.py`
instead was considered and rejected in `architecture.md`: `gates.py`
ships no CLI verbs of its own (`factory.py`'s router is explicitly "a
router, not a seam"), so the regen script would either duplicate the
parsing logic or force `gates.py` to grow a CLI leg — both worse than
one module both callers import.

**(b) Detector letters `K` (`STANDARDS-DRIFT`) and `M`
(`CAPTURE-COMPLETENESS`), not `J`.** Verified against `gates.py` as it
stands today, not merely as `architecture.md` described it yesterday:

- At `architecture.md`'s authoring time (2026-09-20), `J` was reserved
  by a *fully-written docstring entry* for unrelated in-flight work
  (`LABEL-WIRING`, WO-0039) on the unmerged branch
  `feat/first-live-dispatch`. `architecture.md` reasoned that claiming
  `J` for this design would hand a human two competing claims on the
  same letter to reconcile across two unrelated PRs, and chose `K`/`M`
  to avoid that collision entirely.
- As of this ADR, that reasoning has resolved in exactly the direction
  it anticipated: `LABEL-WIRING` merged to `main` (PR #516, commit
  `47b6937`) and `gates.py`'s `DETECTORS` table now reads
  `"J": ("LABEL-WIRING", "gates.py", "offline")` — `J` is not merely
  reserved by an in-flight branch anymore, it is a real, shipped,
  fully-wired detector. The original avoid-a-collision reasoning is
  moot; the practical conclusion (`J` is unavailable to this design) is
  unchanged and now unconditionally true rather than contingent on an
  unmerged PR landing.
- `gates.py`'s `DETECTORS` table marks `"K": (None, None, "unused")`
  and carries no entry for `M` at all — both are genuinely free at this
  ADR's authoring time. `L` is already claimed (`LABEL-SYNC`,
  network-plane, `label_sync.py`). `K` and `M` are claimed here for the
  two new offline detectors `gates.py`'s own module docstring already
  states the letter namespace does not end at any particular letter —
  non-contiguous letters are an established, accepted pattern (`L`
  already breaks contiguity), not a new irregularity this decision
  introduces.
- Two detectors, not one combined check, for the same reason
  `architecture.md` gave: this repo's one-concern-per-letter convention
  (A through J each check exactly one thing) — index drift and
  `defect.md` completeness share no code and fail for unrelated
  reasons, so combining them would make failures harder to triage for
  no savings.

**(c) Enforcement status (`advisory` / `enforced`) lives only in
`docs/standards.json`'s `status` field, never in ADR prose or an ADR's
`Status:` line.** ADRs in this repo are append-only / supersede-only
(`CLAUDE.md`; `docs/adr/README.md`'s own status vocabulary is `accepted`
/ `provisional` / `superseded (in part) by` / `amended by` — none of
which is a promotion mechanism). Routing every advisory-to-enforced
promotion through a new or amended ADR would turn a one-line,
evidence-backed status flip into ADR churn disproportionate to the
decision, and the architect charter's own ADR bar ("an ADR for each
decision that is expensive to reverse") argues the other way: the index
field is the smaller, more reversible surface, so it is the one that
should carry the state that changes. This mirrors an existing pattern
in this repo — `factory.json` already holds a status/config vocabulary
in a JSON field treated as the single source of truth (ADR-0004) rather
than encoded in prose.

## Consequences

- `standards_index.py` ships as a new root module with its own
  `factory_init.MIRRORS` entry (`tools/factory/standards_index.py`,
  identity transform) — it is imported by `gates.py`'s detector `K`,
  which is itself mirrored into every factory-stamped product repo, so
  it must resolve there too, the same reasoning `CLAUDE.md` already
  states for `plane_drift.py`'s root-only exception cutting the other
  way: it ships *because* a payload tool imports it.
- `gates.py`'s `DETECTORS` table, module-docstring roster, and
  `CHECKERS` tuple gain `K` (`STANDARDS-DRIFT`) and `M`
  (`CAPTURE-COMPLETENESS`) as permanently claimed, offline-plane
  letters. A future detector must pick a free letter beyond `M` (or
  wait on `J`); nothing here claims `L` or `N` for anything.
- `docs/standards.json` is derived, regenerable data — like
  `docs/factory/costs.jsonl` and `factory/manifest.json`, it is never a
  hand-maintained parallel source of truth and is not itself mirrored
  as a template; each repo using this pipeline generates its own from
  its own `docs/adr/*.md` (and, later, hand-curated `CLAUDE.md#`
  entries) by running the shipped script locally, the same way it
  customizes its own `factory.json` rather than inheriting this repo's.
- A known open edge this ADR records rather than silently resolves:
  `standards_index.build_index(root)` regenerates the ADR-derived
  subset from ADR content alone and does not read the previously
  committed `docs/standards.json`, so it has no way to know a slug was
  ever promoted — every ADR-derived entry `build_index` emits carries
  `status: advisory` by construction. Decision (c) above makes a
  promotion's durability an explicit, separate concern: `K`'s drift
  check (WO-0054) compares committed-vs-fresh ADR-derived entries on
  every field EXCEPT `status`, precisely so a promoted entry does not
  read as "drifted" forever. Nothing in this session's scope (Milestone
  A/B) makes a promotion durable across a later `standards_index.py
  update` run that re-derives the ADR-derived subset — that is real
  follow-up work for whoever exercises WO-0064 (the human-judgment
  promotion row), recorded here rather than discovered as a silent
  regression later.
- No specific statement's enforcement status changes here — this ADR
  creates the machinery and the field the state will live in; it does
  not itself promote anything (PRD-0004 Out of scope; `breakdown.md`'s
  WO-0064 stays a human-only decision, untouched by this ADR).
- No statement content is back-filled by this ADR — `## Normative
  statements` sections in existing ADRs, and hand-curated
  `CLAUDE.md#`-sourced entries, are `breakdown.md`'s Milestone C
  (WO-0056/WO-0057), not this one.
- **Detector `M` grandfathers every `defect.md` already on disk when it
  ships.** Implementing `M` surfaced a fact `architecture.md` did not
  check against real content: this repo's own `docs/fixes/*/defect.md`
  corpus (57 files, spanning 2026-08 through 2026-09) almost entirely
  predates `skills/capture/TEMPLATE.md`'s current heading set — most
  wrote `## Reproduction`, `## Why it matters`, `## Fix`, never `##
  Root-cause hypothesis`/`## Blast radius`/`## Ruled out` as named
  sections at all. Wiring `M` unconditionally would turn `gates.py`
  permanently red against this repo's own history — the same "a new
  rule cannot retroactively apply to what predates it" problem
  ADR-0043 already solved for detector G, at a scale (57 files) a
  hand-annotation pass does not fit this row's scope. `M` therefore
  exempts a `defect.md` whose own frontmatter `date:` sorts before a
  fixed `CAPTURE_ADOPTED` constant (`gates.py`, "2026-09-21") — a
  comparison against a file's own static field, not against wall-clock
  "now", so it stays deterministic and hermetic; a missing or
  unparseable date is NOT exempted (fail closed). This generalizes
  correctly to every other repo `M` ships to (`factory_init.MIRRORS`):
  a `defect.md` already on disk when a repo takes this factory update
  predates `M` by construction and is exempt the same way; a fresh
  capture from then on carries today's date and is checked in full.
