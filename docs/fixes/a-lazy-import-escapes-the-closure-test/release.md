---
stage: ship
run: maintenance:a-lazy-import-escapes-the-closure-test
date: 2026-08-30
---

# Release: PR opened, merge left to the human gate

## Pre-flight

| Check | Result |
|---|---|
| Verification green | Yes — `verification.md`, six criteria, a disclosed false-negative mutation, and a what-is-not-verified section |
| Full suite | `Ran 1345 tests` OK (1344 on `main` + 1) |
| `lint.py` | `lint: 0 problem(s) across 24 skills` |
| `gates.py` | `gates: 0 problem(s)`; `--selftest: ok` |
| Behaviour change | None — one test added, no production module touched |
| Mirrored files touched | **None.** The only edited file is a test. No `update-manifest`. |
| Rollback plan | Below |

## Blockers on merge

1. **ADR-0036 clause 2** — the review is self-authored.
2. **Merge is gate 3** (ADR-0033), the repo owner's.

## Contention

`tests/test_factory_init.py` is a busy file. The new method lands at the
end of `TestPayloadToolsImport`, so anything else appending to that
class conflicts textually and merges by union. `#354` and `#355` both
touch this file, in `TestProductForm` and the Makefile tests — different
classes, so a clean auto-merge is likely.

This run does **not** touch `gates.py`, `factory_init.py`, the payload,
or the manifest, which is unusual for this queue and deliberate.

One ordering note rather than a conflict: the test reads `gates.py`'s
source, so a branch that adds a lazy import of an unshipped module will
fail it. That is the point.

## Rollback

```sh
git revert <the code commit>
```

Nothing else. Reverting loses the check and restores a repo where a
module dropping out of MIRRORS switches detector J off silently in every
stamped install.
