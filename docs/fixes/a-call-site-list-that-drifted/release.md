---
stage: ship
run: maintenance:a-call-site-list-that-drifted
date: 2026-08-30
---

# Release: PR opened, merge left to the human gate

## Pre-flight

| Check | Result |
|---|---|
| Verification green | Yes — `verification.md`, six criteria plus an explicit not-verified note |
| Full suite | `Ran 1345 tests` OK (1344 on the merge base + 1) |
| `lint.py` | `lint: 0 problem(s) across 24 skills` |
| `gates.py` | `gates: 0 problem(s)`; `--selftest: ok` |
| Behaviour change | None — a docstring and a test |
| Mirrored files touched | `knowledge_plane.py` — `update-manifest` ran, manifest committed |
| Rollback plan | Below |

## Blockers on merge

1. **ADR-0036 clause 2** — the review is self-authored.
2. **Merge is gate 3** (ADR-0033), the repo owner's.

## Contention

- **`knowledge_plane.py`** — open PR **#328** appends to this same
  `row_done` docstring (a `ROW.match` guard and a paragraph explaining
  it) directly below the enumeration this run rewrites. The two will
  conflict textually. **The union is correct**: #328's guard and
  paragraph, this run's corrected and derived call-site listing. Neither
  claim contradicts the other.
- **`factory/manifest.json`** — conflicts with any other merged payload
  change; resolve by re-running `python3 factory_init.py update-manifest`.

## Rollback

```sh
git revert <this branch's commit>
python3 factory_init.py update-manifest
```

Reverting restores a docstring that is wrong. There is no runtime risk
either way.
