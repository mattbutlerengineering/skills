---
stage: ship
run: maintenance:one-fence-rule
date: 2026-10-10
released: 2026-10-10 (55d5eae)
assumptions:
  - "Prepare-and-stop, matching this repo's maintenance runs: this stage pushed the branch, opened anchor issue #657 and PR #658, and merged nothing. A squash merge to main is the release mechanism, and it is the owner's gate-3 decision (ADR-0033)."
  - "Executed after preparation: the owner then answered 'Squash-merge now' in-session (2026-10-10), and the merge ran. The prepared state above is kept as written, and the execution is recorded below."
  - "No plugin version bump: nothing under skills/ changed, so the plugin cache has nothing stale to serve."
  - "Scale: a design-touching refactor of three mirrored tools gets the full pre-flight below, including a payload-twin and manifest check."
---

# Release: shipped (PR #658, squash-merged as 55d5eae)

**PR:** #658, `fix: one fence rule — detector D and the validator skip gate use the strict walker`
**Branch:** `docs/one-fence-rule`, on `origin/main` at `008dd34`
**Closes:** #657 (anchor issue; no work order)

## Pre-flight

| Check | Result |
|---|---|
| Verification green | `verification.md`: 6 criteria, 6 PASS, 0 FAIL |
| Review | `review.md`: 0 critical, 0 major, 4 minor (2 fixed, 2 deferred with reasons) |
| Secrets | `git diff origin/main..HEAD` grepped for assigned secret, token, password, API-key or private-key literals: no match |
| Configuration | none needed: no env var, credential or external call is added |
| Migrations / data | none; the functions changed are pure, over strings |
| Payload twins | `knowledge_plane.py`, `gates.py`, `validator.py` byte-identical to their `factory/templates/tools/factory/` twins; `factory_init.py update-manifest` gives 0 problems, and detector E passes inside `gates.py` |
| Local suite | `unittest discover`: 2106 OK; `lint.py`: 0; `gates.py`: 0; `--selftest`: ok |

One hiccup, recorded: the first `git push` was rejected. `origin/docs/one-fence-rule` already held the pre-rebase capture commit `96965c6`, which the local branch had rebased onto `008dd34` as `7da232d`. Force-push is not used here, so the remote commit was merged in (`bc978d6`; tree checked unchanged against its parent) and the push then fast-forwarded. The PR is squash-merged, so the extra merge commit does not reach `main`.

## Rollback

Door: two-way. Blast radius: detector D or the validator's uncited-skip
gate misreads a fenced region. That shows up as a false D problem on CI,
or as a PR the skip gate wrongly skips or flags. Neither mutates an
issue nobody named. These are the same words as the PR body's *Merge
danger* section.

After the squash merge, as `<sha>`:

```
git checkout main && git pull
git revert --no-edit <sha>
python3 factory_init.py update-manifest   # the revert restores the old twins; confirm 0 problems
python3 -m unittest discover tests && python3 gates.py && python3 gates.py --selftest
git push origin main                      # or open the revert as a PR
```

A stamped repo that already ran `factory_init.py update` picks up the
revert the same way on its next update.

## Release steps (owner's to execute)

1. CI green on PR #658 (`gh pr checks 658`).
2. `gh pr merge 658 --squash --delete-branch`.
3. Confirm #657 closed through `Closes #657`.
4. Smoke check on `main`: `python3 gates.py && python3 gates.py --selftest`.

## Release executed

1. CI green on PR #658: `check` and `review` passed; `merged-label` and
   `needs-review-label` were skipped by design on a PR with no work order.
2. `gh pr merge 658 --squash --delete-branch` → `MERGED 55d5eae`.
3. Issue #657: `CLOSED` through `Closes #657`.

## Post-release

Smoke check on `main` at `55d5eae`:

```
gates: 0 problem(s)
selftest: ok
$ grep -nE '^(FENCE_OPEN|FENCE_CLOSE|ARCH_FENCE|FENCES) *=' *.py
knowledge_plane.py:90:FENCE_OPEN = re.co…
knowledge_plane.py:91:FENCE_CLOSE = re.c…
```

Operate (`retro.md`) follows once the change has been on `main` long
enough to show how it behaves.
