---
stage: prd
run: feature:codex-style-standards-enforcement
date: 2026-09-20
id: PRD-0004
ux: not-applicable
ux-reason: every surface is a JSON file, a CLI regen script, gate detectors, and skill/charter prose — nothing built for a human to look at
assumptions:
  - "No live interview; requirements below are drawn directly from issue #448's own Design/Acceptance sections (migrated from bd, see idea.md) and sized against this repo's actual seams. Gaps in the issue's own spec are called out as Open questions, not silently resolved."
---

# PRD: Codex-style standards enforcement

## Problem statement

`docs/adr/` already holds this repo's decisions with machine-readable
statuses (`ADR_STATUS`, detectors C/D), and `gates.py`/`lint.py` already
mechanically enforce a wide detector roster. What's missing is the
layer Cloudflare's engineering-standards post names: a normative-
statement index that turns "somewhere in ADR-0032's prose" into a
citable, filterable, gate-checkable unit, with a graduated advisory→
enforced lifecycle so new rules can be observed before they block
anything. Reviews (human, the base `review` skill, the
`factory-reviewer` charter) currently re-derive which ADR passages are
hard rules from memory every time; nothing distinguishes a MUST this
repo has decided to enforce from a SHOULD that's still advisory, and
nothing checks that the index itself hasn't drifted from the ADRs it
claims to summarize.

## Solution

When this ships (i.e., when the *design* in `architecture.md` is
approved and later implemented — this run stops at Decompose):
`docs/standards.json` holds a derived, regenerable, slug-addressed
index of normative statements pulled from a new `## Normative
statements` convention in ADRs going forward, plus a small hand-curated
CLAUDE.md back-fill; each statement carries an RFC-2119 level and an
`advisory`/`enforced` status; a new gate detector fails when the
committed index drifts from what regeneration would produce or when an
`enforced` statement's source ADR is no longer `accepted`; the base
`review` skill and the `factory-reviewer` charter cite statement slugs
in findings and block approval on unresolved `enforced` findings; the
`architect` skill and `factory-architect` charter load the same index
filtered to design-relevant statements before drafting; and a new gate
detector checks every maintenance run's `defect.md` for the protocol's
required sections.

## Actors

- **Matt (repo maintainer / human reviewer)** — approves PRs and
  blueprint gates today by re-deriving which ADR passages are hard
  rules; after this ships, cites and promotes statement slugs instead;
  remains the sole authority for advisory→enforced promotion (mirrors
  LEDGER.md's real-evidence-only maturity discipline).
- **The base `review` / `architect` skills** — plugin skills any repo
  using idea-to-prod can invoke, factory or not; load the filtered
  index and cite slugs in `review.md` / `architecture.md`.
- **The `factory-reviewer` / `factory-architect` charters** — the
  chartered-agent versions of the same two roles, for repos running the
  dispatch plane (ADR-0032); same index, same citation and blocking
  rule, plus the reviewer's existing ADR-0036 merge authority.
- **`gates.py`'s new detectors** — the mechanical backstop: index<->
  source drift, MUST-supersession, and `defect.md` completeness.

## User stories

1. As Matt reviewing a PR, I want findings to cite a statement slug
   (`slug: adr0032-one-way-mirror`) instead of a paraphrase of ADR
   prose, so that I can tell at a glance whether a finding is a
   settled MUST or an advisory nudge, and trust that the citation
   resolves to a real, undrifted source.
2. As Matt, I want an `enforced` MUST finding to withhold approval
   automatically (mirroring, not replacing, the human gates — ADR-0033/
   0036 stay unamended), so a reviewer (human or chartered) can't
   quietly wave through a violation of a rule this repo already decided
   to enforce.
3. As Matt approving a blueprint (`architecture.md` / `docs/adr/**`),
   I want the design-relevant slice of the index loaded before drafting
   — not the whole ADR corpus — so the design cites the rules that
   actually constrain it (the post's spec reviewer, scaled down).
4. As Matt running a maintenance run, I want `defect.md` checked for
   the protocol's required sections (Defect/Condition, Reproduction/
   Evidence, Root-cause hypothesis, Blast radius, Ruled out) the same
   way `verification.md` is already checked for evidence (detector H),
   so an incomplete capture brief is caught before Verify, not during
   it.
5. As Matt promoting a statement from advisory to enforced, I want that
   promotion to require the same evidence discipline LEDGER.md already
   holds skills to (a real run, a real prior advisory finding — never a
   fabricated one), so the graduated-enforcement lifecycle can't be
   gamed by relabeling a statement enforced on day one.

## Success criteria

- [ ] `docs/standards.json` exists, one entry per statement:
      `{slug, statement, level, source, status, domain}` with
      `level ∈ {MUST, SHOULD}`, `status ∈ {advisory, enforced}`,
      `domain ∈ {factory, pipeline, eval, docs}` — matching the shape
      issue #448 specifies.
- [ ] A regeneration script (stdlib-only, invoked like
      `factory_init.py update-manifest`) deterministically rebuilds the
      ADR-derived subset of the index from ADRs' `## Normative
      statements` sections; hand-curated CLAUDE.md-sourced entries
      survive regeneration untouched.
- [ ] A new `gates.py` gate detector fails the battery when the
      committed index drifts from a fresh regeneration, and separately
      when an `enforced` statement's source ADR carries any status
      other than `accepted` (reusing the existing `ADR_STATUS`
      machinery detector D already owns — one status vocabulary, not
      two).
- [ ] `python3 gates.py --selftest` covers the new detector(s) with
      planted-defect fixtures, per this repo's existing convention.
- [ ] `skills/review/SKILL.md` and `factory/charters/reviewer/
      CHARTER.md` are updated to load the index (filtered to the PR's
      touched paths' domains), cite slugs in findings, and treat an
      unresolved `enforced` finding as blocking — advisory findings
      stay non-blocking, recorded the same as any other minor.
- [ ] `skills/architect/SKILL.md` and `factory/charters/architect/
      CHARTER.md` are updated to load the index filtered to
      design-relevant domains (`factory`, `pipeline`) before drafting,
      and to cite any statement the design's decisions bear on.
- [ ] A new gate detector (or, if Architect resizes it, a lint-style
      checker — Architect's call, justified either way) validates that
      every maintenance run's `defect.md` carries the protocol's
      required sections, non-placeholder, with exact problem strings
      and unit-test coverage (mirrors `check_ledger`'s test style).
- [ ] `python3 -m unittest discover tests`, `python3 lint.py`, and
      `python3 gates.py && python3 gates.py --selftest` all stay green
      through every work item in the eventual breakdown.
- [ ] No parallel docs tree: `docs/standards.json` is derived data, the
      ADRs and CLAUDE.md stay the sources of truth (ADR-0004) —
      verified by the drift detector itself, not asserted.

## Out of scope

- **Advisory→enforced promotion of any specific statement inside this
  same implementation pass**, unless a human names three statements
  that already have real, pre-existing advisory-flagged evidence (a
  past PR review comment, an audit finding) to point to honestly.
  Fabricating "previously flagged" history to hit the issue's
  Acceptance #4 is exactly what eval-honesty (CLAUDE.md) forbids. See
  Open questions and breakdown.md's flagged item.
- **Mechanical extraction of MUST/SHOULD statements from existing
  free-form ADR prose or from CLAUDE.md's existing bullets.** Only a
  new, explicit `## Normative statements` section convention is
  mechanically extracted; existing statements worth enforcing are
  hand-back-filled, not mined (the issue's own scoping).
- **Dashboards, an AI-gateway-style plumbing layer, an org-wide RFC
  process, or a standalone linter-package distribution** — the issue
  rejects all four explicitly; the cost ledger and gate digest already
  count what this repo needs, and it has one maintainer and one linter
  (`lint.py`).
- **Any new `docs/adr/**` file, tracker mirror issue, or label.** This
  run stops at Decompose (idea → PRD → architecture → breakdown); the
  actual ADR(s) this design implies get authored once a human has
  approved the design, not by this run.
- **The `oh-my-pi`/omp second-harness packaging of any skill/charter
  change** (ADR-0027) — out of this PRD's frame; the stage-skill body
  stays harness-neutral per the protocol either way.
- **Rewriting `check_skill_recitals` or any existing gates.py/lint.py
  detector's behavior.** Already-covered mechanical enforcement per the
  issue's own framing; this PRD adds detectors, it doesn't touch
  existing ones.

## Open questions

- **How does `defect.md` completeness get gated — a new lettered
  `gates.py` detector, or a `lint.py` checker?** This PRD's success
  criteria describe the observable behavior (required sections
  checked, problem strings, tests) and leave the home to Architect,
  who has the fuller seam-boundary context (gates.py ships to every
  factory-stamped product repo via `factory_init.MIRRORS`; lint.py is
  unmirrored, skills-meta-repo-only).
- **Which detector letter(s)?** `gates.py`'s `DETECTORS` table marks
  both `J` and `K` `unused`, but `J`'s docstring entry is already fully
  written for unrelated in-flight work (LABEL-WIRING, WO-0039 on
  `feat/first-live-dispatch`, unmerged as of this PRD). Architect
  decides the letter(s), avoiding that collision.
- **Acceptance #4's three real promotions** — resolved to Out of scope
  above; Architect/Decompose should record the follow-up path (a
  separate, later run once real advisory-period evidence exists) so it
  isn't lost, not silently dropped.
- **CLAUDE.md back-fill mechanics** — CLAUDE.md has no heading-anchor
  convention suited to mechanical `source: CLAUDE.md#anchor`
  resolution. Architect decides whether `source` for a CLAUDE.md-
  sourced statement cites a heading text match, a line-content match,
  or something else that the drift detector can still verify without
  requiring CLAUDE.md itself to be restructured (this PRD does not
  authorize rewriting CLAUDE.md's prose to fit the index).
