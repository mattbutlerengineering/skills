---
stage: ship
run: maintenance:a-shadowed-definition-is-invisible
date: 2026-08-30
---

# Release: PR opened, merge left to the human gate

## Pre-flight

| Check | Result |
|---|---|
| Verification green | Yes — `verification.md`, five criteria plus a what-is-not-verified section |
| Full suite | `Ran 1352 tests` OK (1344 on `main` + 8) |
| `lint.py` | `lint: 0 problem(s) across 24 skills` |
| `gates.py` | `gates: 0 problem(s)`; `--selftest: ok` |
| Behaviour change | None — one new test file, no production module touched |
| Mirrored files touched | **None.** Asserted against `factory_init.MIRRORS`, not assumed. No `update-manifest`. |
| Rollback plan | Below |

## Blockers on merge

1. **ADR-0036 clause 2** — the review is self-authored.
2. **Merge is gate 3** (ADR-0033), the repo owner's.

## Contention

**None expected.** This run adds one new file and touches nothing else,
which is unusual for this queue and was part of why the test placement
was chosen over a `gates.py` detector (`review.md` §1) — a detector
would have conflicted with #377 over the DETECTORS table.

The only way this run conflicts is if another open PR also creates
`tests/test_shadowed_definitions.py`, which none does.

One ordering note rather than a conflict: this check will **fail** on
any branch that already contains a shadowed definition. That is the
point, and no open PR currently does — all 98 tracked files on `main`
are clean, and the sweep can be re-run per branch with the new test.

## Rollback

```sh
git revert <the code commit>
```

Nothing else. No manifest, no payload, no production module. Reverting
loses the check and restores a repo where a shadowed definition deletes
tests behind a green suite.
