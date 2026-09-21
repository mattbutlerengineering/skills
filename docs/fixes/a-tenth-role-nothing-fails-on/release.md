---
stage: ship
run: maintenance:a-tenth-role-nothing-fails-on
date: 2026-08-27
assumptions: []
---

# Release: a tenth role nothing fails on

**Prepared, not executed.** The brief carries no release authorization,
so ship stops here per the autorun default. Nothing was merged, tagged,
published or deployed.

## Pre-flight

- **Verification is green.** `verification.md` records seven checks, all
  PASS, and names four things it did not verify — including that these
  three tests do not go red on `origin/main`.
- **No unfixed critical review findings.** `review.md` records none; two
  majors are accepted with their reasoning, four minors deferred or
  recorded with no action.
- **No secrets in the diff.** One test class, three tests.
- **No configuration required.** Stdlib only.
- **No migration, no data change.**
- **No payload mirror, and none needed.** `tests/test_factory_charters.py`
  is not in `factory_init.MIRRORS`; `update-manifest` was run anyway and
  changed nothing.
- **The working tree is clean of the reproduction.** The stray stub,
  stray charter directory and injected index row were removed before
  commit and `git status --short` shows the single modified test file.
- **No money spent.** Every check is offline.

## Release steps, if a human authorizes them

1. Open a pull request from `agent/a-tenth-role-nothing-fails-on` to
   `main`.
2. A **non-authoring** reviewer re-executes the battery on the branch and
   records it on the PR — ADR-0036 clause 2. This run cannot satisfy that
   clause for itself, which is why no PR was opened.
3. Squash-merge once CI is green and the review is recorded. No conflict
   is expected: the file appears in no open PR and on no other agent
   branch, and no payload byte moves.

## Rollback plan

One commit, one file, no generated artefact and no production surface:

```
git revert <commit>          # after merge
git push origin main
```

No `update-manifest` step, because this change produced no payload bytes.
Reverting removes the three assertions and reopens the vocabulary's
domain — it restores the state in which a stray dispatchable stub passes
the whole battery, so it is a step to take only if the assertions
themselves misfire.

Before merge, the branch can simply be deleted:

```
git push origin --delete agent/a-tenth-role-nothing-fails-on
```

A narrower rollback exists and is preferable to a full revert if only one
direction proves troublesome: delete the offending test method and keep
the other two. They are independent — three separate assertions over
three separate places, sharing only the class.

## Post-release check

Not applicable: nothing was released. When it is, the check is that
`python3 -m unittest discover tests` reports 1347 on `main`, and that
`tests.test_factory_charters.TestTheVocabularyIsTheWholeDomain` is
present and green. The stronger check — that it actually catches a stray
stub — is criterion 4 of `verification.md` and can be re-run by anyone:
drop a `factory/agents/factory-<anything>.md` in the tree and watch the
suite fail.
