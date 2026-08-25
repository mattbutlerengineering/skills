---
stage: ship
run: maintenance:dedup-identity-has-two-owners
date: 2026-08-25
assumptions: ["Prepare-and-stop, per autorun-brief.md's release authorization: NONE. Pre-flight ran, the PR is open, no merge and no tag. ADR-0036 clause 2 independently forbids the author merging.", "Every pre-flight measurement was taken in a detached worktree at the branch tip whose `git status --porcelain` is empty — the shared checkout carries another session's untracked files and detector D reads the live tree."]
---

# Release: fold the dedup identity into its seam

**Status: prepared, not executed.** PR
[#341](https://github.com/mattbutlerengineering/skills/pull/341) is open
against `main`. Nothing has merged, deployed, or been tagged.

## Pre-flight

| Check | Result |
| --- | --- |
| Verification green | Yes — `verification.md` records no unresolved failures |
| Review findings | 1 found, 1 fixed in-run; 0 critical, 0 unfixed |
| Secrets in the diff | None |
| Configuration required | None — no new env var, secret, or workflow input |
| Data/migration path | None — see below |
| Rollback plan | Concrete, below |
| Mirror/manifest | Regenerated and committed with the change |

**Verification.** Battery at the branch tip in a clean detached worktree:

```
Ran 1345 tests in 16.954s

OK
lint: 0 problem(s) across 24 skills
gates: 0 problem(s)
selftest: ok
one-owner: 8 problem(s)
```

**Secrets.** Nothing secret-shaped in the code or payload diff:

```
$ git diff origin/main...HEAD -- budget_guard.py tests/test_budget_guard.py factory/ | grep -nEi "ghp_|ghs_|sk-[A-Za-z0-9]{20}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY|password|secret"
none
```

**Mirror.** `budget_guard.py` is in `factory_init.MIRRORS`, so the payload
copy and the manifest moved in the same commit:

```
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)

 M factory/manifest.json
 M factory/templates/tools/factory/budget_guard.py
```

Detector E reports nothing at the tip, and `tests/test_factory_init.py`
(payload↔root) passes.

**Breakdown.** All three items checked, none open.

**Diff size.** 10 files, +574 / −6 — of which the executable change is 8
lines in `budget_guard.py` and 8 mirrored, the rest tests and run artifacts.

## No migration, and nothing already recorded is affected

The ledger is append-only and this run appends nothing. `record` compares the
same identity it compared before — the regression proves it in both
directions — so no row already in `docs/factory/costs.jsonl` is re-read,
re-keyed, or re-summed by this change. Nothing to migrate and nothing to
backfill.

What changes is **coupling, not behaviour**: from the merge on, a change to
`cost_ledger.row_key` reaches `budget_guard`'s suite. That is the point of
the run, and it is also the only thing a merger is agreeing to.

## Rollback plan

One function in one module plus its mirror; the revert is a single commit:

```bash
# after a squash merge, from a clean main:
git revert --no-edit <squash-sha>
python3 factory_init.py update-manifest   # confirm no drift after the revert
python3 gates.py                          # expect: gates: 0 problem(s)
git push origin main
```

Confirm the revert restored the old rule — this prints the inline comparison
again:

```bash
grep -n 'existing.get("wo")' budget_guard.py
```

**No data cleanup is needed after a revert.** Because the fold is a no-op
under today's identity, any row recorded while the change was live would have
been recorded identically before it. The revert restores the second owner, it
does not orphan anything.

## The release steps a merger runs

1. Re-execute the verification per ADR-0036 clause 2 and record it on
   [#341](https://github.com/mattbutlerengineering/skills/pull/341) — the
   author cannot satisfy this. The mutation runs in `verification.md` and
   `review.md` are the ones worth repeating: they are what distinguish this
   from a cosmetic edit.
2. Confirm CI is green on the PR head.
3. Squash-merge #341 into `main`. Issue #340 closes automatically via
   `Closes #340`.
4. Delete the branch `agent/dedup-identity-two-owners`.
5. No tag, no publish, no deploy — this repo ships by merge to `main`, and
   the plugin version is untouched.
6. If another mirrored PR merges first, regenerate the manifest on this
   branch before merging it — `factory/manifest.json` is the shared line and
   four other open PRs touch it.

## Not executed, and why

`autorun-brief.md` records the release authorization as **none** —
prepare-and-stop. ADR-0036 clause 2 also requires a non-authoring reviewer to
re-execute verification and record it on the PR before merge, which
independently blocks the author from merging their own change.

## Hand-off

Next stage is Operate, once there is feedback to capture — for this run that
means the first time someone changes `cost_ledger.row_key` and finds out
whether `budget_guard`'s suite tells them. One item is already owed to it:
`budget_guard.py:55 CONTINUE` / `cost_report.py:44 CONTINUE`, the second
one-owner pair in this module, left out of scope by the brief and still on
the pre-pass.
