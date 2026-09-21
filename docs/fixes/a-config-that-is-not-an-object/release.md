---
stage: ship
run: maintenance:a-config-that-is-not-an-object
date: 2026-08-30
---

# Release: PR opened, merge left to the human gate

## Pre-flight

| Check | Result |
|---|---|
| Verification green | Yes — `verification.md`, seven criteria, no unresolved failures |
| Full suite | `Ran 1350 tests` OK (1344 on the merge base + 6) |
| `lint.py` | `lint: 0 problem(s) across 24 skills` |
| `gates.py` | `gates: 0 problem(s)`; `--selftest: ok` |
| Secrets in the diff | None |
| Mirrored files touched | `factory_config.py` and `gates.py` — `update-manifest` ran, manifest committed |
| Migrations / data changes | None; the change is a validation guard |
| Rollback plan | Below |

## Blockers on merge

1. **ADR-0036 clause 2.** The review is self-authored. A non-authoring
   reviewer must re-execute the verification and record it on the PR.
   The cheap re-execution is §3: `echo 'null' > factory/templates/factory.json`
   then `python3 gates.py`, on `main` and on this branch.
2. **Merge is gate 3** (ADR-0033) and belongs to the repo owner.

## Contention

- `factory_config.py` — also touched by **#391** (catch `OSError` /
  `UnicodeDecodeError` around the read) and **#396** (reject a
  non-finite cap). All three edit `load` or its neighbourhood; none of
  the three addresses the same rule. Merge order does not matter, but
  the second and third in will conflict textually in `load`. The union
  is the correct resolution every time: keep the decode guard, the
  object guard, and the finite-number predicate.
- `gates.py` — also touched by **#320** (`manifest_files`, ~line 656)
  and **#377** (detector J, ~line 1036). Neither is near
  `check_config_shape` at ~line 895.
- `factory/manifest.json` — conflicts with any other merged payload
  change; resolve by re-running `python3 factory_init.py update-manifest`.

## Rollback

```sh
git revert <this branch's code commit>
python3 factory_init.py update-manifest
python3 -m unittest discover tests
```

Reverting restores the latent defect, which is acceptable: the suite was
green with it for months and no incident is being cleaned up.

## Hiccups, recorded

- **The first design was wrong and the reproduction caught it.** Guarding
  `load` alone leaves detector F raising, because F does not use `load`.
  Recorded as finding 1 in `review.md`.
- **The manifest was forgotten until the suite said so.** The first green
  run was 193/194 — `test_a_clean_run_ends_with_the_exact_summary_line`
  failed because the payload checksums no longer matched. That is
  detector E doing exactly its job.
