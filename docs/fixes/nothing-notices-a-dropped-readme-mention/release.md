---
stage: ship
run: maintenance:nothing-notices-a-dropped-readme-mention
date: 2026-09-20
assumptions:
  - Prepared and stopped, because the brief authorizes no release action
    and merges are a human-only gate (ADR-0033, ADR-0036).
---

# Release — nothing notices a dropped README.md mention

**Prepared, not executed.** This run opens a pull request and stops
there. No merge, no tag, no publish.

## Pre-flight

- **Verification is green.** `verification.md` records eight criteria,
  all PASS, including the section-boundary check against the real,
  current `` `claude` `` false positive.
- **Review is clear of criticals.** No majors, no criticals. One design
  call (section-scoped reading of `## Stages`) argued explicitly with its
  accepted residual risk named, not buried.
- **No secrets in the diff.** The change adds two module-level constants,
  one helper function, one checker, and test coverage; it reads one file
  already in the tree and writes nothing.
- **No configuration is required.** `lint.py` is a root-only tool, not in
  `factory_init.MIRRORS` — no stamped product repo runs it, so no
  manifest regeneration is owed and detector E agrees.
- **No migration, no data change.** README.md is not edited by this run;
  the checker only reads it.

## Battery at the commit under review

```
=== unittest ===
Ran 1625 tests in 20.237s

OK
=== lint ===
lint: 0 problem(s) across 24 skills
=== gates ===
gates: 0 problem(s)
=== selftest ===
selftest: ok
```

## Scope

This run closes the README.md half of issue #455 that
`nothing-notices-a-dropped-ledger-row` (PR #501) left open and issue #502
asked a human to resolve. It answers #502's question directly: the
`## Stages` section already has a structural marker (table plus the
utility-skill prose the same lead-in sentence introduces) narrow enough
to avoid the whole-document false positive and wide enough to catch a
retired utility skill's prose-only mention — confirmed against the real
README, not assumed. `Closes #502`.

## Rollback

One commit on one branch, merged by squash if it is merged at all.

```
git revert <merge-sha>          # after a merge
git push origin main
```

Before a merge there is nothing to roll back: closing the pull request
leaves `main` untouched. Reverting removes `check_readme_no_orphans`,
`readme_stage_mentions`, and their tests; `check_readme_skills` and
`check_ledger_no_orphans` are untouched either way.

## What a human still owns

Merging. Every check on this branch is green, but ADR-0036 clause 2 asks
for a non-authoring reviewer to re-execute verification and record it on
the pull request — that is the gate, and it is not one an agent clears.
Also worth a second look: observation 8 in `review.md` (the accepted risk
that a future, unrelated slug-shaped backtick token inside `## Stages`
would misfire) — a human closer to how the README actually gets edited
may weigh that risk differently.
