---
stage: ship
run: maintenance:eval-validators-raise-on-non-object-files
date: 2026-08-27
---

# Release: prepared, not executed

The brief authorizes no release. Ship therefore runs the pre-flight,
records the exact steps, and **stops**. Nothing outward-facing happened:
no merge, no tag, no publish, and no pull request opened.

## Pre-flight

| Check | Result |
|---|---|
| Verification green | Yes — `verification.md`, five criteria, no unresolved failures |
| Full suite | `Ran 1352 tests` OK (1344 on `main` + 8 regression tests) |
| `lint.py` | `lint: 0 problem(s) across 24 skills` |
| `gates.py` | `gates: 0 problem(s)`; `--selftest: ok` |
| `one_owner.py` (pre-pass, not a gate) | `9 problem(s)` — the standing baseline, unmoved |
| Secrets in the diff | None; scan of added lines found no secret-shaped strings |
| Mirrored files touched | None — verified against `factory_init.MIRRORS` directly, so no `update-manifest` and no write to `factory/manifest.json` |
| Migrations / data changes | None; the change is a validation guard |
| Rollback plan | Below, concrete |

## Blockers on merge

Both are for a human; neither is something this run may resolve.

1. **ADR-0036 clause 2.** The review is self-authored. A non-authoring
   reviewer must re-execute the verification and record it on the PR.
   The cheap re-execution is the before/after in `verification.md` §3 —
   corrupt `evals/routing.json` to `null`, run `python3 lint.py` on
   `main` and on this branch, and compare traceback against problem
   string.
2. **No pull request exists, deliberately.** The queue stands at 17 open
   PRs, all awaiting human review, and the standing instruction is to
   hold until it drains. This branch is pushed so CI can run it; opening
   the PR is the user's call.

## The change

Three commits, two of them code:

```
1397f88 fix(eval-schema): validators report a non-object file instead of raising
bc7a596 fix(eval-schema): the loader guarantees validators receive an object
5268947 docs(capture): the eval validators raise on a file that is not an object
```

One guard, `object_problems`, owned by `eval_schema.py` next to the
docstring that promises validators never raise, applied at four points:
`validate`, `validate_output`, `fixture_refs`, and — the one that
matters most — `load_case_set`, before it calls the caller's validator.

## Release steps — NOT executed

Recorded so the person who runs them does not have to reconstruct them:

1. Open the PR against `main` with `gh pr create --body-file` (note:
   `gh pr edit` is broken on this repo — Projects-classic GraphQL
   deprecation — so bodies go in at creation or via
   `gh api ... -X PATCH -F body=@file`).
2. Have a non-authoring reviewer re-run the verification and record it
   on the PR, satisfying ADR-0036 clause 2.
3. Merge. There is no tag, package, or deploy: this repo's "production"
   is `main`, and nothing here changes the plugin payload.

## Rollback

```sh
git revert bc7a596 1397f88      # newest first; code only
python3 -m unittest discover tests
```

Reverting restores the original predicate-free behaviour, which means
restoring the latent defect — acceptable, since the suite was green with
it for months and no incident is being cleaned up. No manifest
regeneration is needed on the way out, for the same reason none was
needed on the way in: no mirrored file is touched.

## Hiccups, recorded

- **The run found a second module with the same defect after Implement
  was already complete.** Review caught `charter_replay.validate`, whose
  string case is worse than the routing one — it reports a corrupted file
  as valid. Rather than widen a scoped run into a second module, the
  guard moved to `load_case_set`, the shared loading seam, which fixes
  the charter path with `charter_replay.py` unmodified. The scope
  boundary held and the fix improved; the deviation is logged in
  `defect.md` Notes and as finding 1 in `review.md`.
- **The same-defect scan that was supposed to catch this did not.** An
  AST heuristic reported only the functions already fixed, because the
  second instance delegates rather than calling `.get` itself. It was
  found by reading. Recorded because the scan looked authoritative and
  was not.
- **A first attempt to read `lint.py`'s exit code measured the wrong
  thing.** `python3 lint.py 2>&1 | tail -6` reports `tail`'s exit status,
  which showed `0` and briefly suggested the gate passed on a corrupted
  file. Re-measured without the pipe: both `main` and this branch exit
  `1`. The corrected figure is what `verification.md` §3 carries, along
  with the explicit note that this fix does **not** turn a green build
  red.
