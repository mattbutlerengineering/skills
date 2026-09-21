---
stage: ship
run: maintenance:a-dead-cli-scores-as-a-pass
date: 2026-08-28
assumptions:
  - Prepare and stop. The brief authorizes no release, and ADR-0036
    clause 2 makes a non-authoring reviewer's re-executed verification
    the condition for merge, which this run cannot satisfy for itself.
---

# Release — a dead CLI scores as a pass

**Prepared, not executed.**

## Pre-flight

- **Verification green.** `verification.md` records ten passing criteria
  and one explicit NOT RUN (a live model replay, which costs money and is
  on-demand only). No unresolved failures.
- **Review clear.** `review.md` has no unfixed critical or major
  findings; the one major was fixed inside the run.
- **Battery.** 1359 tests OK, `lint: 0 problem(s)`, `gates: 0
  problem(s)`, `selftest: ok`, `one-owner: 9 problem(s)` (unchanged from
  `origin/main`).
- **No secrets in the diff.** Two files changed, both Python, no
  configuration and no credentials.
- **No migration, no data change, no configuration required.** The change
  is one predicate in a pure function.
- **Nothing to mirror.** `charter_replay.py` is not in
  `factory_init.MIRRORS` and no payload tool imports it, so
  `factory/manifest.json` is untouched and detector E is unaffected.

## Release steps (not executed)

1. A non-authoring reviewer re-executes `python3 -m unittest discover
   tests`, `python3 lint.py`, `python3 gates.py`, `python3 gates.py
   --selftest`, and records the output on the PR (ADR-0036 clause 2).
2. Merge the PR.

This run does not touch `docs/adr/**`, `prd.md`, `architecture.md` or
`docs/design/**`, so clause 3's human code-owner requirement does not
additionally apply.

## Rollback

```
git revert <merge-commit>
```

The change is two files and adds no state: no snapshot is rewritten, no
schema changes, and `evals/results/` is untouched. A revert restores the
previous scoring rule exactly, and any snapshot recorded in between stays
valid as the append-only record of what that run actually observed.

## Post-release check

After merge, on `main`:

```
python3 charter_replay.py --cases <forbid-only set> --transcripts <empty set>
```

must print `0/1 passed` and exit 1. The reproduction inputs are in
`defect.md`.

## Follow-ups recorded, not done here

- `cli.harness_run` never reads the child's exit status (review finding
  8) — its own run, on the shared harness seam.
- Whether the case-set validator should require evidence-producing
  expectations (review finding 7) — a case-set design question for a
  human.
