---
stage: ship
run: maintenance:the-one-fake-is-not-the-only-one
date: 2026-08-30
---

# Release — the one fake is not the only one

**Prepared and stopped.** No merge, no tag, no deploy. The brief
authorized none, and ADR-0036 clause 2 requires a non-authoring reviewer
to re-execute verification on the PR — this run authored the change.

## Pre-flight

| Check | Result |
| --- | --- |
| `verification.md` has no unresolved failures | Yes — six sections, all green |
| Review's critical findings fixed | No criticals; the one major was fixed and the battery re-run |
| No secrets in the diff | Yes — `tests/` only, no token or network anywhere in it |
| Configuration exists in the target environment | Nothing new |
| Migrations / data changes | None |
| Rollback plan | Below |

No manifest regeneration is owed: nothing under `factory/templates/**`
changed and no root file in `factory_init.MIRRORS` was touched. The diff
is three files, all under `tests/`.

## What ships

- `tests/test_work_queue.py` reaches `cli.gh_runner`'s seam through the
  shared fake; `RecordingRunner` and `FailingRunner` are gone, replaced
  by two helpers that declare what gh *says* rather than how a fake
  behaves.
- `tests/fake_gh.py` stops enumerating the suites that use it — the
  enumeration is what went stale — and says where the derived list lives.
- `tests/test_fake_gh.py` is new: fourteen tests pinning the fake's three
  declared behaviours, its prefix-answer rule, and the single-owner claim
  the module opens with.

## Rollback

One commit on one branch, unmerged: close the PR and delete the branch.
After a merge:

```
git revert --no-edit <merge-sha>
python3 -m unittest discover tests
```

Nothing else is needed — no generated file, no manifest, no payload.
The revert restores two self-contained classes and deletes a test
module.

## Not executed

- No merge. Clause 2 blocks this PR as it blocks every open one.
- No change to the six suites that already used the shared fake. They
  are green; nothing else is claimed about them.

## Carry-forward for whoever reviews this

1. **The claim to re-check is `verification.md` §2** — restore
   `tests/test_work_queue.py` from `origin/main`, leave this run's test
   module in place, and watch the roll-call test fail with the two
   private runners named. It is the whole argument in one command.
2. **The judgment call worth a second opinion** is how narrow the
   detector should be. It matches `__call__(self, args)` exactly.
   Widening it to every `__call__` would sweep in `test_dashboard`'s
   `FakeServer` and `test_cli`'s `FakeProcess`, which are not gh fakes;
   `review.md` records why the narrow rule was chosen and
   `test_the_rule_does_not_fire_on_a_callable_that_is_not_the_port` pins
   that side.
3. **This run is evidence for an existing backlog seed**, not a new one:
   `one_owner.py` excludes `tests/**`, and the duplication it could not
   see was real. No seed was appended — the seed from
   `maintenance:one-fact-one-owner` already asks the question, and
   appending a second one that says the same thing is how a backlog
   stops being read.
