---
stage: ship
run: maintenance:json-that-is-not-utf8
date: 2026-08-30
---

# Release: PR opened, merge left to the human gate

## Pre-flight

| Check | Result |
|---|---|
| Verification green | Yes — `verification.md`, five criteria plus a disclosed hiccup and a not-verified section |
| Full suite | `Ran 1350 tests` OK (1344 on `main` + 6) |
| `lint.py` | `lint: 0 problem(s) across 24 skills` |
| `gates.py` | `gates: 0 problem(s)`; `--selftest: ok` |
| Change size | five one-token guard widenings; no message, signature or return-shape change |
| Mirrored files touched | `factory_config.py`, `label_sync.py`, `cli.py`, `gates.py` — mirrored, `update-manifest` ran, manifest committed |
| Rollback plan | Below |

## Blockers on merge

1. **ADR-0036 clause 2** — the review is self-authored.
2. **Merge is gate 3** (ADR-0033), the repo owner's.

## Contention

The queue is 44 deep and this run touches four of the most-edited
modules, so expect conflicts. All of them are additive one-liners in
`except` clauses; taking both sides is almost always right.

- **`factory/manifest.json`** — conflicts with every other merged
  payload change. Not a real conflict: take either side, re-run
  `python3 factory_init.py update-manifest`.
- **`gates.py`** — #320, #326, #377 and #328 all touch it, in other
  detectors.
- **`factory_config.py`** — #391 (`will not decode`), #396
  (`infinite amount`) and #405 (`is not an object`) are the three
  siblings of this defect at the same reader. #391 in particular edits
  the **same line**: it introduced the `except json.JSONDecodeError`
  this run widens. Resolution is the union — its message and location,
  this run's exception tuple.
- **`cli.py`** — #400 (heredoc delimiter) touches a different function.
- **`tests/test_gates.py`** — the new cases land inside the existing
  `TestScaffoldSync` and `TestConfigShape`; anything else appending to
  those classes will conflict textually and merge by union.

## Rollback

```sh
git revert <the code commit>
python3 factory_init.py update-manifest
```

Reverting restores five crashes on a rare input. There is no behaviour
to lose: no valid file changes its verdict, and no problem string
changes its text.
