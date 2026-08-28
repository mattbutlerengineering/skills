---
stage: ship
run: maintenance:the-front-door-miscounts-its-own-tools
date: 2026-08-28
assumptions:
  - Prepare and stop. The brief authorizes no release, and ADR-0036
    clause 2 makes a non-authoring reviewer's re-executed verification
    the condition for merge.
---

# Release — the front door miscounts its own tools

**Prepared, not executed.**

## Pre-flight

- **Verification green.** Six passing criteria and one explicit NOT RUN
  (counts outside the root Python modules).
- **Review clear.** No critical or major findings.
- **Battery.** 1349 tests OK, `lint: 0 problem(s)`, `gates: 0
  problem(s)`, `selftest: ok`, `one-owner: 9 problem(s)` unchanged.
- **No secrets in the diff.** Two files, both Python, and the only
  non-test change is a module docstring.
- **No migration, no data change, no configuration.**
- **Nothing to mirror.** `factory.py` is not in `factory_init.MIRRORS`,
  so `factory/manifest.json` is unchanged and detector E is unaffected.
- **Gates run after the artifacts were written**, not only before — the
  run artifacts live in `docs/**/*.md`, which is detector C's universe.

## Release steps (not executed)

1. A non-authoring reviewer re-executes `python3 -m unittest discover
   tests`, `python3 lint.py`, `python3 gates.py`, `python3 gates.py
   --selftest`, and records the output on the PR (ADR-0036 clause 2).
2. Merge the PR.

No `docs/adr/**`, `prd.md`, `architecture.md` or `docs/design/**` is
touched, so clause 3 does not additionally apply.

## Rollback

```
git revert <merge-commit>
```

A docstring and five tests. Nothing is created, migrated or consumed.

## Post-release check

On `main`:

```
python3 -m unittest tests.test_factory_cli
```

must report `OK`, and `python3 factory.py help` must still list every
verb in `factory.VERBS`.

## Follow-ups recorded, not done here

- The pin covers the router's docstring only (review finding 3).
- Hand-typed counts outside the root Python modules were not enumerated
  (review finding 8).
