---
stage: ship
run: maintenance:only-the-codegraph-degrades
date: 2026-08-27
assumptions: []
---

# Release: only the codegraph degrades

**Prepared, not executed.** The brief carries no release authorization,
so ship stops here per the autorun default. Nothing was merged, tagged,
published or deployed.

## Pre-flight

- **Verification is green.** `verification.md` records eight checks, all
  PASS, and names what was not verified. No unresolved failures.
- **No unfixed critical review findings.** `review.md` records none; one
  major is accepted with its reasoning and one minor is deferred with
  its owner named.
- **No secrets in the diff.** One helper function, two call sites, one
  test class, plus the regenerated payload copy and manifest hashes.
- **No configuration required.** Stdlib only; no new environment
  variable, no new file read.
- **No migration, no data change.** The pack is built per dispatch and
  stored nowhere.
- **The payload mirror is regenerated.** `orientation_pack.py` is in
  `factory_init.MIRRORS`; `python3 factory_init.py update-manifest` was
  run and committed with the change, the payload copy is byte-identical
  to the root file, and detector E is green.
- **No money spent.** Every check is offline.

## Release steps, if a human authorizes them

1. Open a pull request from `agent/only-the-codegraph-degrades` to
   `main`.
2. A **non-authoring** reviewer re-executes the battery on the branch and
   records it on the PR — ADR-0036 clause 2. This run cannot satisfy
   that clause for itself, which is why no PR was opened.
3. Rebase if `factory/manifest.json` has moved, then re-run
   `python3 factory_init.py update-manifest` — never hand-merge the
   hashes.
4. Squash-merge once CI is green and the review is recorded.

## Rollback plan

One commit, four files, no state left behind:

```
git revert <commit>          # after merge
python3 factory_init.py update-manifest
git add factory/manifest.json && git commit --amend --no-edit
git push origin main
```

The manifest step is part of the rollback, not an afterthought: the
revert restores the old payload bytes, and detector E compares the
manifest to them.

Before merge, the branch can simply be deleted:

```
git push origin --delete agent/only-the-codegraph-degrades
```

Reverting restores the previous behaviour exactly — an undecodable or
unreadable CONTEXT.md or ADR would again raise out of the assembler —
and nothing else in the repo reads the new note text.

## Post-release check

Not applicable: nothing was released. When it is, the check is that
`python3 -m unittest discover tests` reports 1350 on `main`, that
`python3 gates.py` is green (detector E covers the manifest), and that
`tests.test_orientation_pack.TestAFileThePackCannotReadIsANoteNotACrash`
is present and green.
