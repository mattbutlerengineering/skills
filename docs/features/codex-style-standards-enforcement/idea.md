---
stage: idea
run: feature:codex-style-standards-enforcement
date: 2026-09-20
origin: "GitHub issue #448 — self-answered from the issue's own text (which already carries a Design/Acceptance/Notes brief from its bd migration); no live interview held. Driven autorun-style per skills/autorun/SKILL.md's convention: gaps in the brief become logged assumptions, never silent guesses (see autorun-brief.md in this directory)."
assumptions:
  - "In-flight check ran (not skipped): `gh pr list`/`gh branch -a` for '448', 'standards', 'normative', 'codex' and `gh issue list --search \"normative statement index\"` all came back empty except issue #448 itself and the unrelated #181 journal. Nothing else is already doing this work."
---

# Idea: Codex-style standards enforcement

## Problem

This repo already mechanically enforces a lot — gates.py's detectors A–I
(plus network-side L), lint.py's structural checkers, decision records
with machine-readable statuses (`docs/adr/` + `ADR_STATUS`, detectors C
and D), and three physically-enforced human gates (ADR-0033, amended by
ADR-0036). What it does NOT have is a place those decisions *become*
checkable rules an agent can load without reading whole ADR bodies: a
SHOULD/MUST statement buried in ADR-0032's prose, or in CLAUDE.md's
"Hard conventions" section, is enforced only if the reviewer (human or
the `factory-reviewer` charter) happens to remember it and happens to
re-derive whether it's a hard rule or a preference. Cloudflare's
engineering-standards post
(https://blog.cloudflare.com/engineering-standards-enforcement/)
names the missing piece precisely: a normative-statement index with
stable ids, a graduated advisory→enforced lifecycle, and reviewers
(code, spec/design, incident) that consume the same index instead of
re-deriving judgment calls every time.

## Who has it

Matt, this repo's sole maintainer, in two roles this issue keeps
separate: as a **human reviewer** approving PRs and blueprint gates by
re-reading ADR prose each time to decide whether a deviation is a real
violation or just unfamiliar code; and as the **operator of chartered
agents** (`factory-reviewer`, `factory-architect`, the base `review` and
`architect` skills) that currently load whole ADR files or none at all
— there is no filtered, structured "here are the rules that apply to
this diff" view. Coping today: judgment calls are re-litigated from
scratch each review, findings cite ADR numbers inconsistently (or not
at all), and nothing distinguishes "this is a style preference the
reviewer holds" from "this is a MUST this repo has decided to enforce."

## Why now

Two things line up. First, every prerequisite this issue explicitly
declines to rebuild already ships: mechanical detectors, machine-
readable ADR statuses, local-CLI/CI parity, and the three human gates
— so the marginal work is genuinely the four things Cloudflare's post
adds on top, not a rebuild. Second, this repo already practices the
exact discipline the post's advisory→enforced lifecycle needs
(LEDGER.md's draft→used-once→battle-tested maturity, graduated only on
real-run evidence, never fabricated) — the graduated-enforcement idea
isn't a new philosophy here, it's an existing one (eval-honesty,
CLAUDE.md) that has never been pointed at ADR/CLAUDE.md compliance
before.

## Evidence

The issue itself (#448) already carries a Design and Acceptance section
from its original bd authoring (its own footer says it was migrated
from beads to GitHub issues on 2026-09-17, citing an ADR number whose
file is not present in this checkout — taken on the issue's own word
and not independently verified; noted as an assumption, not restated as
settled fact in prd.md/architecture.md). That existing spec is strong
signal, not invented scope. Beyond the
issue text: `gates.py`'s own docstring already names its detector
letters as a deliberately open namespace ("The letter namespace does
not end at I") — this repo's own tooling anticipated exactly this kind
of extension. And the reviewer/planner/architect charters
(`factory/charters/*/CHARTER.md`) already have "Loadout" and "Actions
per cycle" sections shaped to slot in a new checklist source without a
structural rewrite.

## Solution hunch

Four pieces, sized against what exists (Architect's job to nail down,
not this brief's):

1. A derived, regenerable `docs/standards.json` normative-statement
   index — slug, statement text, RFC-2119 level, source path, status
   (advisory|enforced), domain — extracted deterministically from a new
   `## Normative statements` convention in ADRs going forward, plus a
   small set of hand-backfilled CLAUDE.md-sourced entries (not
   exhaustive; the issue is explicit about this).
2. The status field itself IS the graduated-enforcement mechanism:
   advisory produces non-blocking review findings, enforced MUST
   statements withhold approval. Promotion is a human-only PR, same
   spirit as an ADR status-line edit.
3. The base `review` skill, the `factory-reviewer` charter, and the
   `architect`/`factory-architect` charter (the blueprint gate) load a
   domain-filtered slice of the index and cite slugs in findings.
4. A new gate detector for maintenance-run (`defect.md`) section
   completeness, scaled down from the post's incident-report reviewer.

## Success in one sentence

An agent reviewing a PR or a blueprint can cite `slug: <id>` findings
drawn from a checked, drift-gated index instead of re-deriving ADR
prose from memory, and at least one real MUST has graduated
advisory→enforced on real evidence, not a fabricated one.

## Unknowns & risks

- **Extraction is deterministic only for statements written to be
  extracted.** A regex/heading-based extractor cannot reliably mine
  free-form MUST/SHOULD sentences out of existing ADR prose or
  CLAUDE.md's convention bullets without a lot of false
  positives/negatives. Resolved as a scope decision in prd.md/
  architecture.md: back-fill is small and hand-curated, not exhaustive
  mining — the issue itself says this ("back-fill only statements worth
  enforcing, not exhaustively").
- **The "3 real promotions with prior-advisory evidence" acceptance bar
  (issue Acceptance #4) cannot be satisfied at implementation time** —
  there is no advisory-period history before the index exists. Flagged
  explicitly in breakdown.md as needing a human decision rather than
  quietly reinterpreted or dropped.
- **Letter collision risk in `gates.py`.** Detector letter `J` already
  carries a fully-written docstring entry (LABEL-WIRING) for unrelated,
  already-in-flight work on another branch (`feat/first-live-dispatch`,
  WO-0039) that hasn't landed yet. Picking `J` here would hand a human
  two competing claims to reconcile by hand. architecture.md resolves
  this by skipping to unclaimed letters that avoid the collision.
- **Scope discipline.** The issue explicitly rejects dashboards,
  AI-gateway plumbing, an org-wide RFC process, and a standalone linter
  distribution. Easy to scope-creep into "let's also build a policy
  engine" — architecture.md sizes this against what already exists
  (gates.py/lint.py conventions) specifically to resist that.
