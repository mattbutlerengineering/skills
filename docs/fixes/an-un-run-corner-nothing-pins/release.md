---
stage: ship
run: maintenance:an-un-run-corner-nothing-pins
date: 2026-08-27
assumptions: []
---

# Release: an un-run corner nothing pins

**Prepared, not executed.** The brief carries no release authorization,
so ship stops here per the autorun default. Nothing was merged, tagged,
published or deployed.

## Pre-flight

- **Verification is green.** `verification.md` records eight checks, all
  PASS, and names four things it did not verify — including that no
  recorder was run against a real CLI.
- **No unfixed critical review findings.** `review.md` records none;
  three majors are accepted with their reasoning, four minors deferred
  or dismissed.
- **No secrets in the diff.** One rewritten test file and the same
  guard function added to two scripts.
- **No configuration required.** Stdlib only.
- **No migration, no data change.** No committed fixture was touched:
  all four `.jsonl` transcripts and both `provenance.json` files are
  unchanged, and the empty-stream reproduction deliberately ran against
  a copy in a temp tree so it could not overwrite pinned eval evidence.
- **No payload mirror, and none needed.** Nothing under `tests/` is in
  `factory_init.MIRRORS`; `update-manifest` was run anyway and changed
  nothing.
- **No money spent.** Every check is offline; no CLI was invoked.

## Release steps, if a human authorizes them

1. Open a pull request from `agent/an-un-run-corner-nothing-pins` to
   `main`.
2. A **non-authoring** reviewer re-executes the battery on the branch and
   records it on the PR — ADR-0036 clause 2. This run cannot satisfy that
   clause for itself, which is why no PR was opened.
3. Squash-merge once CI is green and the review is recorded. No conflict
   is expected: none of the three files appears in an open PR or on
   another agent branch, and no payload byte moves.

## Rollback plan

One commit, three files, no generated artefact:

```
git revert <commit>          # after merge
git push origin main
```

No `update-manifest` step — this change produced no payload bytes.

The two halves are independent and can be rolled back separately if only
one proves troublesome:

```
git checkout <commit>~1 -- tests/test_fixture_recorders.py   # pin only
git checkout <commit>~1 -- tests/fixtures/*/record.py        # guard only
```

Reverting the guard restores the state in which a dead CLI writes a
`fired: null` transcript stamped with a real `cli_version`; reverting the
pin restores a hand-typed enumeration that strands the next recorder
added. Neither is a state worth returning to on convenience alone.

## Post-release check

Not applicable: nothing was released. When it is, the check is that
`python3 -m unittest discover tests` reports 1348 on `main`, and that
`tests.test_fixture_recorders` reports 5 tests rather than 1. The
stronger check needs a human with an authenticated CLI: the next real
re-recording should behave exactly as before, because the guard sits
before the CLI-facing code and refuses only a stream that produced
nothing.
