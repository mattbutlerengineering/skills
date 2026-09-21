---
stage: ship
run: maintenance:nothing-notices-a-dropped-ledger-row
date: 2026-09-20
assumptions:
  - Prepared and stopped, because the brief authorizes no release action
    and merges are a human-only gate (ADR-0033, ADR-0036).
---

# Release — nothing notices a dropped LEDGER.md row

**Prepared, not executed.** This run opens a pull request and stops
there. No merge, no tag, no publish.

## Pre-flight

- **Verification is green.** `verification.md` records eight criteria;
  seven PASS as a verified fix, one PASS as a documented, evidenced
  non-implementation for the README.md half (criterion 7). No unresolved
  failures.
- **Review is clear of criticals.** No majors, no criticals. One design
  question (README.md's reverse direction) recorded as an open follow-up
  rather than forced.
- **No secrets in the diff.** The change adds one function, one regex-free
  set difference, and six tests; it reads one file already in the tree
  and writes nothing.
- **No configuration is required.** `lint.py` is a root-only tool, not in
  `factory_init.MIRRORS` — no stamped product repo runs it, so no
  manifest regeneration is owed and detector E agrees.
- **No migration, no data change.** LEDGER.md is not edited by this run;
  the checker only reads it.

## Battery at the commit under review

```
=== unittest ===
Ran 1623 tests in 20.413s

OK
=== lint ===
lint: 0 problem(s) across 24 skills
=== gates ===
gates: 0 problem(s)
=== selftest ===
selftest: ok
```

## Scope

This run closes the LEDGER.md half of issue #455 only. The README.md
half is a genuine open design question (see `defect.md`); the issue stays
open and this run does not claim `Closes #455`.

## Rollback

One commit on one branch, merged by squash if it is merged at all.

```
git revert <merge-sha>          # after a merge
git push origin main
```

Before a merge there is nothing to roll back: closing the pull request
leaves `main` untouched. Reverting removes `check_ledger_no_orphans` and
its tests; the forward-direction checks (`check_ledger`,
`check_readme_skills`) are untouched either way.

## What a human still owns

Merging, and the README.md design question this run left open. Every
check on this branch is green, but ADR-0036 clause 2 asks for a
non-authoring reviewer to re-execute verification and record it on the
pull request — that is the gate, and it is not one an agent clears.
