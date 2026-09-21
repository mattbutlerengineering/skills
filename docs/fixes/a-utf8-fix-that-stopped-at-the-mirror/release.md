---
stage: ship
run: maintenance:a-utf8-fix-that-stopped-at-the-mirror
date: 2026-08-31
---

# Release: PR opened, merge left to the human gate

## Pre-flight

| Check | Result |
|---|---|
| Verification green | Yes — `verification.md`, six criteria plus a not-verified section |
| Full suite | `Ran 1350 tests` OK (1344 on `main` + 6) |
| `lint.py` | `lint: 0 problem(s) across 24 skills` |
| `gates.py` | `gates: 0 problem(s)`; `--selftest: ok` |
| `one_owner.py` | nine problems, identical to `main` — unmoved by this run |
| Change size | six handler tuples; no message, signature or return-shape change |
| Mirrored files touched | none — all four modules are absent from `factory_init.MIRRORS`, so no `update-manifest` and no manifest commit |
| Cross-PR overlap | none — every open PR scanned, no diff touches any of these eight files |
| Rollback plan | Below |

## Blockers on merge

1. **ADR-0036 clause 2** — the review is self-authored.
2. **Merge is gate 3** (ADR-0033), the repo owner's call. Not taken here.

## Relationship to PR #410

These two runs partition one defect class and **do not overlap in any
file**:

- PR #410 fixes the five mirrored modules (10 sites incl. payload).
- This run fixes the four root-only modules (6 sites).

Merge order does not matter. Neither depends on the other, and neither
completes the class alone. After both merge the AST sweep that found
this reports zero sites, and the suite is 1344 + 6 + 6 = 1356.

Because `factory/manifest.json` is untouched here, this run avoids the
contention PR #410's own `release.md` warns about — that file conflicts
with nearly every other merged run.

## Rollback

Revert the single commit. The six changed lines are each a widened
`except` tuple; reverting restores the previous, narrower guard and the
six new tests fail again with `errors=6`. Nothing else in the repo reads
these handlers, and no data or artifact shape changes, so a revert is
complete and side-effect free.

## Follow-up recorded, not actioned

`review.md` §3 leaves the "one owner for the JSON-read guard" question
open with a concrete tally — 16 sites, three principled spellings —
rather than building a seam without an ADR. The third run to touch this
guard should decide it.
