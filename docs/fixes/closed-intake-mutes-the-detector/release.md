---
stage: ship
run: maintenance:closed-intake-mutes-the-detector
date: 2026-08-25
assumptions: ["Prepare-and-stop, per autorun-brief.md's release authorization: NONE. Pre-flight ran, the PR is open, no merge and no tag. ADR-0036 clause 2 independently forbids the author merging, so this would stop here even if the brief had said otherwise.", "Every pre-flight measurement was taken in a detached worktree at the branch tip (28e4571) whose `git status --porcelain` is empty — the shared checkout carries another session's untracked files, and detector D reads the live tree."]
---

# Release: a closed intake stops suppressing its detector

**Status: prepared, not executed.** PR
[#339](https://github.com/mattbutlerengineering/skills/pull/339) is open
against `main`. Nothing has merged, deployed, or been tagged.

## Pre-flight

| Check | Result |
| --- | --- |
| Verification green | Yes — `verification.md` records no unresolved failures |
| Review findings | 2 found, 2 fixed in-run; 0 critical, 0 unfixed |
| Secrets in the diff | None |
| Configuration required | None — no new env var, secret, or workflow input |
| Data/migration path | None; a **board-state** effect instead, below |
| Rollback plan | Concrete, below |
| Mirror/manifest | Not required — no `factory/` path in the diff |

**Verification.** Battery at `28e4571` in a clean detached worktree:

```
Ran 1349 tests in 15.921s

OK
lint: 0 problem(s) across 24 skills
gates: 0 problem(s)
selftest: ok
```

And the free pre-pass, unchanged from `main` — no new group:

```
one-owner: 9 problem(s)
```

**Secrets.** The code diff carries no secret-shaped string:

```
$ git diff origin/main...28e4571 -- sweeps.py tests/test_sweeps.py | grep -nEi "token|secret|password|api[_-]?key|ghp_|sk-|AKIA|-----BEGIN"
no secret-shaped strings in the code diff
```

And the whole diff, artifacts included, carries no credential literal:

```
$ git diff origin/main...28e4571 | grep -nE "ghp_|ghs_|sk-[A-Za-z0-9]{20}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY"
no credential literals anywhere in the diff
```

**Mirror.** `sweeps.py` is not a mirrored root tool, so no payload copy and
no manifest regeneration:

```
$ python3 -c "import factory_init; print(any('sweeps' in str(m) for m in factory_init.MIRRORS))"
False

$ git diff --name-only origin/main...28e4571 | grep -E "^factory/"
no factory/ paths in the diff — nothing mirrored, no manifest regen needed
```

**Breakdown.** All four items checked, none open.

## No migration — but there is a state change

There is no data to migrate. There *is* a change to what the sweep may do,
and it is the reason this needs a human at the merge button rather than a
rubber stamp:

- **Before:** `sweep:label-drift` and `sweep:reconcile` sat on closed issues
  (#173, #295) and could never be filed again. Both detectors were mute.
- **After:** both keys are released. The sweep files nothing *today* — both
  detectors report clean, and Verify measured that — but the next time
  either detector reports drift, a new issue appears on the board.

So the merger is enabling a filing path, not only fixing a set-membership
test. #173 and #295 remain closed and are superseded by whatever is filed
next; reopening them instead is an operator's call, recorded as an open
question rather than decided here.

## Rollback plan

The change is one function in one non-mirrored module, so the revert is a
single commit and touches nothing else:

```bash
# after a squash merge, from a clean main:
git revert --no-edit <squash-sha>
git push origin main
```

Verify the revert restored the old rule — this prints the two keys again
when their issues are closed:

```bash
python3 -c "import sweeps; print(sorted(sweeps.known_keys()[0]))"
```

**If the sweep filed issues before the revert**, the revert does not close
them. It re-mutes the detectors, so those issues stop being refreshed and
stay open until closed by hand. Check the board for open issues carrying
`intake-key: sweep:label-drift` or `intake-key: sweep:reconcile` and close
them deliberately, or the revert leaves the board holding reports nothing
will update.

## The release steps a merger runs

1. Re-execute the verification per ADR-0036 clause 2 and record it on
   [#339](https://github.com/mattbutlerengineering/skills/pull/339) — the
   author cannot satisfy this.
2. Confirm CI is green on the PR head.
3. Squash-merge #339 into `main`. Issue #338 closes automatically via
   `Closes #338`.
4. Delete the branch `agent/issue-338-closed-intake-mutes-detector`.
5. No tag, no publish, no deploy — this repo ships by merge to `main`, and
   the plugin version is untouched by this change.
6. Watch the next sweep run: expect **zero** issues filed while both
   detectors are clean, and one issue per detector the first time either
   reports drift.

## Not executed, and why

`autorun-brief.md` records the release authorization for this run as
**none** — prepare-and-stop. ADR-0036 clause 2 also requires a non-authoring
reviewer to re-execute verification and record it on the PR before merge,
which independently blocks the author from merging their own change.

## Hand-off

Next stage is Operate, once there is feedback to capture — for this run that
means the first sweep after merge, which is where the fix either files
something or correctly stays quiet. Two items are already owed to it:

- The dedupe listing raises `AttributeError` on a non-object entry
  (pre-existing, identical before and after this run; `review.md` F3).
- `sweeps: 0 issue(s) filed` reads the same for "nothing to report" and
  "everything suppressed" — the class of backlog seed 42, and the reason
  this defect stayed invisible for as long as it did.
