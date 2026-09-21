---
run: maintenance:quoted-token-is-not-a-claim
date: 2026-08-23
scale: maintenance
---

# Autorun brief: a token inside quoted output is not a claim

## What and why

`validator.run_lifecycle` gates its uncited skip on
`not WO_TOKEN.findall(body)`, so any work-order token anywhere in a PR
body — including inside a fenced code block — makes the PR a work-order PR
whose citation must resolve. Three PRs on 2026-08-23 failed
`needs-review-label` for quoting a token they did not implement, and each
was fixed by redacting the digits.

Raised as `docs/backlog.md:38` (from: session:2026-08-21), claimed by this
run.

## Scope

**In:** the skip gate in `run_lifecycle`; a rule for what counts as quoted
material; tests; the ADR amending ADR-0057, which wrote the current gate.

**Out — and this is the important half.** The seed's own proposal, an
`Implements: WO-####` trailer read in preference to a bare-token scan, is
**not** in scope. It is a repo-wide PR-body convention with a migration
cost for every future work-order PR and for the assembler and daily
routine that generate them — an external commitment the autorun rules say
to surface rather than assume. PR #306's case (a provenance mention in
prose) needs that convention and stays open.

Also out: `cited_work_order`'s resolution logic, which is correct and
whose docstring already anticipates quoted material.

## Success criteria

A PR body whose only work-order tokens sit inside fenced blocks is treated
as citing no work order, so both lifecycle legs no-op on it. A PR body that
claims a work order outside quoted material behaves exactly as it does
today. No PR body that passes today starts failing.

## Constraints

Stdlib only. `validator.py` is a `factory_init.MIRRORS` entry, so any edit
needs `python3 factory_init.py update-manifest` in the same commit.
ADR-0057 is accepted and must be amended by a new ADR, never rewritten;
its status line and the index row move together (detector D reads them
byte-for-byte). The full battery is green at every item.

## Tracker

Issue #331 is the run's tracking issue and the PR closes it. No `WO-####`
is minted (ADR-0032).

## Release authorization

None. Ship prepares and stops — merge and tag are not authorized, and
ADR-0036 clause 2 reserves merge to a non-authoring reviewer. Clause 3
also applies: this run touches `docs/adr/**`.
