---
stage: ship
run: maintenance:the-fourth-split-contract-is-unpinned
date: 2026-08-30
---

# Release: PR opened, merge left to the human gate

## Pre-flight

| Check | Result |
|---|---|
| Verification green | Yes — `verification.md`, seven criteria, a disclosed harness hiccup, and a what-is-not-verified section |
| Full suite | `Ran 1346 tests` OK (1344 on `main` + 2) |
| `lint.py` | `lint: 0 problem(s) across 24 skills` |
| `gates.py` | `gates: 0 problem(s)`; `--selftest: ok` |
| Behaviour change | None — two tests added, no production module and no workflow touched |
| Mirrored files touched | **None.** The only edited file is a test. No `update-manifest`. |
| Rollback plan | Below |

## Blockers on merge

1. **ADR-0036 clause 2** — the review is self-authored.
2. **Merge is gate 3** (ADR-0033), the repo owner's.

## Contention

Low. One class appended to the end of `tests/test_gate_digest.py`, and
no open PR currently touches that file. No production module, no
workflow, no payload, no manifest.

One ordering note rather than a conflict: the test reads
`.github/workflows/gate-digest.yml` and `gate_digest.py`, so any branch
that renames the `changed` key on either side will now fail. That is the
point.

## Rollback

```sh
git revert <the code commit>
```

Nothing else. Reverting restores a repo where renaming one key silently
stops the gate-latency rows from ever being committed, daily, with the
workflow green.
