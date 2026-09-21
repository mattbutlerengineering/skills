---
stage: ship
run: maintenance:a-forbid-only-case-checks-nothing
date: 2026-09-20
assumptions:
  - "Prepare and stop. ADR-0033/0036 make merge a human-only gate; this
    run opens the PR and does not merge it."
---

# Release — a forbid-only case checks nothing

**Prepared, not executed.**

## Pre-flight

| Check | Result |
|---|---|
| Verification green | Yes — `verification.md`, 8 passing criteria plus one explicit NOT RUN (a live model replay, on-demand only) |
| Full suite | `Ran 1619 tests` OK (`origin/main` + 2) |
| `lint.py` | `lint: 0 problem(s) across 24 skills` |
| `gates.py` | `gates: 0 problem(s)`; `--selftest: ok` |
| Golden case set | unmodified; still loads with zero problems, all four cases already carry a `require` |
| Change size | one guard clause mirroring an existing one, one docstring paragraph, three collateral test fixes |
| Mirrored files touched | none — `charter_replay.py` is not in `factory_init.MIRRORS`; no manifest regeneration owed |
| Secrets in the diff | none — two Python files, no configuration |
| Rollback plan | below |

## Blockers on merge

1. **Merge is gate 3** (ADR-0033), the repo owner's call. Not taken here.
2. **ADR-0036 clause 2** — every commit on this branch is agent-authored,
   so a non-authoring reviewer re-executes the verification and records
   it on the PR before merge.

## Contention

No file this run touches (`charter_replay.py`,
`tests/test_charter_replay.py`, this `docs/fixes/` directory) is touched
by any other open PR at the time of writing. `factory/evals/charters.json`
is read but not written.

## Rollback

```
git revert <merge-commit>
```

The change is two files and adds no state: no snapshot is rewritten, no
schema changes, `evals/results/` is untouched, and the golden case set is
unmodified. A revert restores the previous validation rule exactly.

## Post-release check

After merge, on `main`:

```
python3 charter_replay.py --cases factory/evals/charters.json \
    --transcripts <any recorded set>
```

should print `4/4` and exit according to the recorded transcripts, same
as before this change — the golden set's behavior does not move, only a
previously-legal forbid-only case set now fails to load.
