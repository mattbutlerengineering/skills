---
stage: verify
run: maintenance:closed-intake-mutes-the-detector
date: 2026-08-25
assumptions: ["Every block below is pasted from a command actually run, not written from expectation. The battery was run in a DETACHED WORKTREE at this branch's tip rather than in the working checkout, because another session is writing untracked files into the same checkout (see 'A contaminated checkout' below) and gates.py reads the live tree. The worktree is the honest measurement of this branch; the working checkout measures this branch plus somebody else's unfinished work.", "No stage of this run executed a sweep in a filing mode. autorun-brief.md makes that a standing prohibition, and every command below is either offline or a read-only detector call."]
---

# Verification: a closed intake stops suppressing its detector

Criteria are `autorun-brief.md`'s seven success criteria, mapped onto the
four breakdown items.

## What changed

```
 .../closed-intake-mutes-the-detector/breakdown.md  | 10 +++-
 sweeps.py                                          | 59 +++++++++++++++++-----
 tests/test_sweeps.py                               | 51 ++++++++++++++++++-
 3 files changed, 104 insertions(+), 16 deletions(-)
```

Four test cases added, none deleted:

```
$ echo "+$(git diff ee5532c..HEAD -- tests/test_sweeps.py | grep -c '^+    def test_') -$(git diff ee5532c..HEAD -- tests/test_sweeps.py | grep -c '^-    def test_')"
+4 -0
```

## C1–C4 — the four corners of the rule. **PASS**

The rule is one boolean, so it is pinned at all four of its corners rather
than at the one that was broken:

```
test_a_closed_detector_intake_stops_suppressing_its_detector ... ok
test_an_open_detector_intake_still_suppresses ... ok
test_a_closed_sentry_intake_still_suppresses ... ok
test_only_the_literal_closed_stops_suppression ... ok
```

`test_only_the_literal_closed_stops_suppression` subtests five shapes — a
missing `state`, `None`, `"closed"` lowercase, `"MERGED"`, and the integer
`7` — and every one keeps today's suppressing behaviour.

## C1 measured against the live board, not only fixtures. **PASS**

The strongest evidence available: `known_keys()` asked the real repository
which keys currently suppress filing, before and after.

At `ee5532c`, this run's last commit before any code changed:

```
suppressing keys: ['sweep:label-drift', 'sweep:reconcile']
problems: []
```

At the branch tip:

```
suppressing keys: []
problems: []
```

Both singleton detector keys are released. Nothing else changed: the board
carries no `sentry:` key today, so the Sentry half of the rule has no live
subject and is covered by fixtures only — said here rather than left to
look like coverage it is not.

## C5 — the untouched contracts still hold. **PASS**

Every pre-existing `TestFileIssues` case that guards a contract this run
must not move, run by name:

```
test_a_closed_issue_with_the_same_key_is_not_refiled ... ok
test_a_full_listing_window_is_reported_not_silently_truncated ... ok
test_an_unparseable_dedupe_listing_means_do_not_file ... ok
test_a_non_list_dedupe_listing_means_do_not_file ... ok
test_the_dedupe_listing_asks_for_every_state ... ok
test_the_cap_applies_to_what_is_new_not_to_the_payload ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.005s

OK
```

`test_a_closed_issue_with_the_same_key_is_not_refiled` is worth naming: it
drives a `sentry:` key on a CLOSED issue and expects suppression, and this
run did not write it. It passing unchanged is the Sentry half of the rule
pinned by a test with no stake in this change.

Three pre-existing cases did fail during Implement, all three on
`tests/test_sweeps.py:36`'s `LIST_CALL` — the exact gh argv, which moved
when `state` joined `--json`. None failed on behaviour. Logged in
`breakdown.md`'s Notes.

## C6 — nothing fires on this repo today. **PASS**

The change restores a guarantee; it does not drain a queue. Both detectors,
with the fix in place:

```
$ python3 label_sync.py
label-sync: 0 problem(s)
label_sync exit=0
$ python3 -c "from pathlib import Path; import sweeps; print('reconcile ->', sweeps.reconcile(Path('.')))"
reconcile -> ([], [])
```

So a merge files no issue immediately. The two released keys become
fileable only the next time a detector actually finds drift.

## C7 — the battery is green. **PASS**

```
$ python3 -m unittest discover tests 2>&1 | tail -3
Ran 1348 tests in 15.418s

OK
$ python3 lint.py | tail -1
lint: 0 problem(s) across 24 skills
$ python3 gates.py | tail -1
gates: 0 problem(s)
$ python3 gates.py --selftest | tail -1
selftest: ok
```

Measured at both ends. At `ee5532c`:

```
Ran 1344 tests in 15.395s

OK
```

1344 → 1348 is the four new cases, none removed.

## A contaminated checkout

`python3 gates.py` in the working checkout **fails**, and not because of
this branch:

```
D: docs/adr/README.md has no index row for ADR-0062
gates: 1 problem(s)
exit=1
```

The cause is an untracked file another session created in this same
checkout at 09:52 today:

```
?? docs/adr/0062-a-skill-that-states-repo-facts-runs-a-shipped-tool.md
?? docs/features/pipeline-board/
```

Neither is this run's, neither is staged, and neither is touched. Detector D
reads the live tree, so an untracked ADR with no index row fails it for
whoever runs it. Every measurement above was therefore taken in a detached
worktree at this branch's tip, whose `git status --porcelain` is empty.

Worth surfacing beyond this run: that untracked file claims **ADR-0062**,
and PR #333 already claims ADR-0062 for
`0062-a-quoted-token-is-not-a-claim.md`. Two different decisions, one
number. That is an operator's problem, not this run's, and this run changes
nothing about it.

## What was NOT verified

- **No sweep was executed in a filing mode**, by design — `autorun-brief.md`
  makes that a standing prohibition. So the *end-to-end* claim, that a
  released key now results in an issue actually being created, is verified
  through `file_issues` with a fake runner and never against GitHub. The
  fake-runner path is the same one every other filing case in this suite
  uses.
- **The Sentry half has no live subject.** No `sentry:` key exists on the
  board, so C1's live measurement covers only the detector-derived half.
  Fixtures cover the rest.
- **Whether #173 and #295 should be reopened** rather than superseded by a
  future intake is untouched and unmeasured. It is an operator's call about
  two live issues, and out of scope per `autorun-brief.md`.
- **`python3 trigger_eval.py` and `python3 charter_replay.py` were not
  run.** Real model runs, cost money, never in CI, and touch nothing this
  change reaches.
