---
stage: ship
run: maintenance:isdigit-is-not-an-int-guard
date: 2026-08-31
---

# Release: PR opened, merge left to the human gate

## Pre-flight

| Check | Result |
|---|---|
| Verification green | Yes — `verification.md`, six criteria plus a disclosed not-fixed row and a not-verified section |
| Full suite | `Ran 1356 tests` OK (1344 on `main` + 12) |
| `lint.py` | `lint: 0 problem(s) across 24 skills` |
| `gates.py` | `gates: 0 problem(s)`; `--selftest: ok` |
| `one_owner.py` | nine problems, identical to `main` |
| Live re-check | raw sockets before and after; server stderr empty after |
| Change size | one guard function, one `do_POST` branch, two one-token conditions |
| Mirrored files touched | `validator.py`, `assembler.py` — `update-manifest` ran (`factory-init: 0 problem(s)`), payload copies and `factory/manifest.json` committed |
| Rollback plan | Below |

## Blockers on merge

1. **ADR-0036 clause 2** — the review is self-authored.
2. **Merge is gate 3** (ADR-0033), the repo owner's call. Not taken here.

## Contention

`factory/manifest.json` is touched, so this conflicts with any other run
that regenerates the manifest. Resolution is the standard one: take both
branch sides for the source files, then re-run
`python3 factory_init.py update-manifest` and commit the regenerated
manifest rather than hand-merging its hashes.

No open PR touches `dashboard.py`, `validator.py` or `assembler.py`
otherwise.

## Rollback

Revert the single commit and re-run `update-manifest`. Every code change
is a guard whose only effect is to turn a traceback into a `400` or a
usage exit, so reverting restores the previous crash and the twelve new
tests fail again — nothing else depends on the new behaviour.

## Follow-up recorded, not actioned

1. **The overstated-`Content-Length` hang** (`verification.md`,
   *Not fixed*) — needs a socket timeout, a change to what the server
   promises every request. Left for the console's owner.
2. **A `non_negative_int` helper** (`review.md` §4) — three identical
   copies of one guard, no divergence yet, so no seam built. A fourth
   site should decide it.
