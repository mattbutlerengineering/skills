---
stage: ship
run: maintenance:heredoc-delimiter-is-guessable
date: 2026-08-27
assumptions: ["the brief carries no release authorization, so ship
  prepares and stops: the branch is pushed and CI-verified, but no PR is
  opened and nothing is merged"]
---

# Release: the heredoc delimiter is not derivable from the key

**Prepared, not released.** No PR was opened; the review queue stands at
17 and this branch does not add an 18th. Nothing was merged, closed,
retargeted, or labelled.

## Pre-flight

- [x] **Verification green.** Five criteria, five PASS, no unresolved
      failures.
- [x] **No secrets in the diff.** The change *adds* a secret-generating
      call (`secrets.token_hex`) but writes no secret anywhere: the
      delimiter is a per-call nonce with no confidentiality requirement,
      and it never leaves `$GITHUB_OUTPUT`. No credential, token, or URL
      is added.
- [x] **Migrations / forward path.** No data shape changes. The one
      externally visible change is the delimiter's *text*, and ADR-0040
      records why that is free: "workflows are unaffected (they read step
      outputs by key, never by delimiter)." Verified independently by
      grepping `_EOF__` across `*.py`, `*.yml`, `*.yaml` and `*.md` —
      nothing in the tree reads it back.
- [x] **Mirror regenerated.** `cli.py` is in `factory_init.MIRRORS`;
      `factory_init.py update-manifest` was run and the payload copy and
      manifest are in the commit. Detector E green.
- [x] **Rollback plan concrete.** Below.

## Rollback plan

The branch is unmerged, so rollback today is deleting it:

```
git push origin --delete agent/heredoc-delimiter-is-guessable
git branch -D agent/heredoc-delimiter-is-guessable
```

If merged by then, revert both commits — contiguous, touching nothing
else — and regenerate the mirror, which the revert also reverts but
which detector E re-checks:

```
git revert --no-edit e8410f6 3d8b642
python3 factory_init.py update-manifest
python3 -m unittest discover tests && python3 lint.py && python3 gates.py
```

Reverting restores the key-derived delimiter, which puts the tree back
in agreement with ADR-0040's Decision text — so a revert needs no
documentation change, whereas keeping the fix does (`review.md`
finding 1).

## Release log

1. `git commit` — 3d8b642, the fix, its three tests, and the regenerated
   mirror → clean.
2. `git commit` — e8410f6, `verification.md` and `review.md` → clean.
3. `git push -u origin agent/heredoc-delimiter-is-guessable` →
   `* [new branch]`, tracking set.
4. **Stop.** No PR opened, per the brief's absent release
   authorization.

## Post-release checks

Not a deployed surface; the check that matters is the battery on a
machine that is not mine. GitHub Actions run
[#33119086149](https://github.com/mattbutlerengineering/skills/actions/runs/33119086149),
workflow `validator`, conclusion **success**:

```
lint: 0 problem(s) across 24 skills
gates: 0 problem(s)
selftest: ok
Ran 1347 tests in 13.964s
OK
```

1347 on Linux against 1347 locally — exact parity, so nothing here is
platform-dependent. That matters slightly more than usual for this
change: `secrets.token_hex` is the one new platform-facing call, and it
behaves identically on both.

## Outcome

Prepared cleanly, released nothing. One decision is queued for a human
and it is documentary, not functional: ADR-0040's Decision section names
the `__<KEY>_EOF__` format this run retires. The code is correct and
CI-green either way, but the ADR record is wrong until amended, and
writing that ADR unattended would mean claiming a number while three
unmerged PRs hold 0062, 0063 and 0064. Proposed text is in `review.md`.

ADR-0036 clause 2 independently blocks self-merge whenever a PR is
opened.
