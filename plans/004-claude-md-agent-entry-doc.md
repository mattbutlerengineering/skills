# Plan 004: Add CLAUDE.md (agent entry doc) and fix the stale lint parenthetical in README

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 79b08fc..HEAD -- CLAUDE.md README.md`
> If `CLAUDE.md` already exists, or README's Development section changed,
> compare against "Current state" before proceeding; on a mismatch, treat
> it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx / docs
- **Planned at**: commit `79b08fc`, 2026-07-03 (refreshed from the 8399f85 original by a /improve re-audit; README line ref, `eval_schema` scope, and utility-skills category updated to HEAD)

## Why this matters

This repo is developed primarily by coding agents, yet has no `CLAUDE.md`
or `AGENTS.md`. Every fresh agent session re-derives the verification
commands, the stdlib-only constraint, the two-seam-module architecture, and
the eval honesty policy from four scattered documents (README, evals/README,
ADR-0021, ADR-0022) — or worse, doesn't, and violates one. A short entry
doc makes the conventions load into every session's context automatically.
Folding in the small README drift fix (the lint parenthetical predates four
newer checkers) keeps both "what the tools do" statements accurate.

## Current state

- No `CLAUDE.md` or `AGENTS.md` exists at the repo root (verify:
  `ls CLAUDE.md AGENTS.md` → both "No such file").
- `README.md:88` (in the Development section) reads:

```markdown
- `python3 lint.py` — structural lint (manifest, frontmatter, templates, router refs); runs in CI on every push/PR
```

  The parenthetical is stale: `lint.py`'s `CHECKERS` tuple now has nine
  checkers (manifest, skills frontmatter, templates, router refs, protocol
  doc, routing eval set, output eval sets, ledger rows, ledger eval-links).
- The facts the new CLAUDE.md must state (all verified at `79b08fc`):
  - **Verification commands** (both run in CI on every push/PR):
    `python3 -m unittest discover tests` and `python3 lint.py`.
    On-demand, costs real model runs, never in CI:
    `python3 trigger_eval.py` (needs the `claude` CLI).
  - **Stdlib-only**: every script is standalone Python 3 stdlib; no
    third-party dependencies, no requirements file.
  - **Seam modules (ADR-0021, ADR-0022, ADR-0024)**: exactly two shared
    modules — `protocol.py` (stage taxonomy, artifact table, frontmatter
    reading, next-stage derivation) and `eval_schema.py`, whose charter
    (ADR-0024) is *all* eval knowledge: routing eval-set shape/kinds/
    load-plus-validate, the output-eval record shape, and the append-only
    results naming grammar. Everything else is a thin caller. The
    graduation bar for creating a new shared module: multiple real callers
    plus observed divergence between their copies — not anticipated reuse.
  - **Skill kinds (ADR-0010, ADR-0023)**: stage skills (own a run
    artifact, routed to by `next`), the `next` router, and utility skills
    (directly-invoked, own no artifact, never routed to;
    `protocol.py` `UTILITY_SKILLS` — `address-pr-review`, `autorun`).
  - **Contracts**: checkers and validators return lists of label-prefixed
    problem strings; tools print them and exit nonzero. Tests assert exact
    problem strings through public interfaces.
  - **Eval honesty policy** (ADR-0012, ADR-0019, `evals/README.md`):
    results files are dated and append-only; never edit an eval definition
    to make a failing case pass; skills graduate LEDGER maturity only via
    real runs — never fabricate run evidence.
  - **Docs map**: `CONTEXT.md` (vocabulary), `docs/adr/` (decisions),
    `docs/pipeline-protocol.md` (protocol spec), `LEDGER.md` (maturity),
    `evals/README.md` (eval layout + policy).

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests   | `python3 -m unittest discover tests` | `OK`, exit 0 |
| Lint    | `python3 lint.py` | `lint: 0 problem(s) across 13 skills`, exit 0 |

## Scope

**In scope**:
- `CLAUDE.md` (create, repo root)
- `README.md` (one line: the lint bullet in the Development section)

**Out of scope** (do NOT touch):
- `CONTEXT.md`, `docs/adr/*`, `evals/README.md` — CLAUDE.md points at
  them; it must not duplicate or rephrase their content at length.
- Any Python file, `LEDGER.md`, anything under `skills/`.

## Git workflow

- Branch: `docs/claude-md-entry-doc` off `main`.
- Conventional Commits, e.g. `docs: add CLAUDE.md agent entry doc; fix stale lint parenthetical`.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Write CLAUDE.md

Create `CLAUDE.md` at the repo root with exactly this content (it encodes
the verified facts from "Current state"; keep it under ~50 lines — the
value is that it's short enough to always be loaded):

```markdown
# skills — agent notes

Idea-to-prod pipeline skills, vended as a Claude plugin. Artifacts are the
state: each stage skill reads/writes `docs/runs/<run>/` artifacts, and
`skills/next` routes by what exists. Spec: `docs/pipeline-protocol.md`.

## Verify (CI runs both on every push/PR)

- `python3 -m unittest discover tests`
- `python3 lint.py` — exit 0 / `lint: 0 problem(s) across 13 skills`

On demand only (real model runs, costs money, never CI):
`python3 trigger_eval.py` (needs the `claude` CLI).

## Hard conventions

- **Stdlib only.** Every script is standalone Python 3 standard library.
  No third-party dependencies.
- **Two seam modules, everything else thin callers**: `protocol.py`
  (ADR-0021 — taxonomy, artifact table, frontmatter, next-stage) and
  `eval_schema.py` (ADR-0022, ADR-0024 — all eval knowledge: routing
  eval-set shape/kinds/validation, output-eval record shape, results
  naming grammar). A new shared module needs multiple real callers AND
  observed divergence between their copies — anticipated reuse doesn't qualify.
- **Three skill kinds**: stage skills (own a run artifact, routed to by
  `next`), the `next` router, and utility skills (ADR-0023 —
  directly-invoked, own no artifact, never routed to; `protocol.py`
  `UTILITY_SKILLS`).
- **Problem-string contracts**: checkers/validators return lists of
  label-prefixed problem strings; callers print and exit nonzero. Tests
  assert the exact strings through public interfaces (see
  `tests/test_lint.py`).

## Eval honesty (non-negotiable)

- `evals/results/` is append-only: dated snapshots, never rewritten.
- Never edit an eval definition to make a failing case pass.
- LEDGER maturity graduates only via a real run — never fabricate run or
  eval evidence. (ADR-0012, ADR-0019; details in `evals/README.md`.)

## Where things are decided

- `CONTEXT.md` — canonical vocabulary (use these terms in code and docs)
- `docs/adr/` — decisions; supersede with a new ADR, don't rewrite
- `LEDGER.md` — per-skill maturity, linked to eval evidence
```

**Verify**: `wc -l CLAUDE.md` → ≤ 55 lines; `python3 lint.py` → exit 0
(CLAUDE.md is not linted, this just confirms nothing broke).

### Step 2: Fix the README parenthetical

In `README.md`, replace the line:

```markdown
- `python3 lint.py` — structural lint (manifest, frontmatter, templates, router refs); runs in CI on every push/PR
```

with:

```markdown
- `python3 lint.py` — structural lint of the install, router, and eval surface (the `CHECKERS` tuple in [`lint.py`](lint.py) is the authoritative list); runs in CI on every push/PR
```

Rationale: pointing at `CHECKERS` instead of enumerating four-of-nine
checkers is what stops this line drifting again.

**Verify**: `grep -n "CHECKERS" README.md` → exactly one match on the
edited line; `grep -c "manifest, frontmatter, templates, router refs" README.md` → `0`.

### Step 3: Full gates and commit

**Verify**: `python3 -m unittest discover tests` → all pass;
`python3 lint.py` → `lint: 0 problem(s) across 13 skills`.

```bash
git add CLAUDE.md README.md
git commit -m "docs: add CLAUDE.md agent entry doc; fix stale lint parenthetical"
```

## Test plan

No unit-testable surface. Verification is the greps in Step 2 plus both CI
gates staying green.

## Done criteria

- [ ] `CLAUDE.md` exists at repo root, ≤ 55 lines
- [ ] `grep -c "manifest, frontmatter, templates, router refs" README.md` → 0
- [ ] `python3 -m unittest discover tests` exits 0
- [ ] `python3 lint.py` exits 0
- [ ] `git status --short` shows only `CLAUDE.md` (new) and `README.md` (modified)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- A `CLAUDE.md` or `AGENTS.md` already exists (someone landed one first —
  reconcile instead of overwriting).
- The README line to replace is absent or already changed.
- Any statement in the CLAUDE.md template contradicts what you observe in
  the live repo (e.g. a third seam module now exists) — the doc must state
  reality, so report the discrepancy rather than shipping a wrong doc.

## Maintenance notes

- CLAUDE.md states counts ("13 skills") only inside the quoted lint output
  line — if the skill roster changes, that line changes with it; everything
  else is deliberately count-free to resist drift.
- Reviewer should check no content was *duplicated* from ADRs at length —
  the doc points, it doesn't mirror.
