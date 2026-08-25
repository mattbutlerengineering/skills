---
stage: verify
run: maintenance:empty-is-not-the-same-as-broken
date: 2026-08-25
assumptions: ["The centrepiece is the regression from defect.md, inverted: the same two runs that produced byte-identical bodies must now produce different ones, and the difference must name the stream. Everything else is supporting evidence.", "This run was built in a dedicated git worktree, not the primary checkout, because another session is driving that checkout on a different branch. Every measurement below is from that worktree, whose `git status --porcelain` is empty."]
---

# Verification: say what was read

## C1 — a failed listing and an empty one no longer read the same

The regression, driven exactly as `defect.md` drove it — the suite's
injected `gh` fake, once healthy with an empty PR listing and once with
`failing=("pr", "list")`.

**Before this run** (`defect.md`):

```
=== bodies identical: True
```

**After**, the two bodies differ in the line that names the stream:

```
Sources: gate rejections from 1 of 1 issue timelines; change requests from the PR listing.
```

```
Sources: gate rejections from 1 of 1 issue timelines; change requests NOT READ — the PR listing failed.
```

Pinned by `test_a_failed_listing_and_an_empty_one_read_differently`, which
asserts the bodies are unequal and that each names its own condition —
not merely that a string appears somewhere. **PASS.**

## C2 — the timeline stream is counted, not hidden

The stream the seed did not name. Two mirrored issues, every timeline fetch
failing:

```
Sources: gate rejections from 0 of 2 issue timelines (2 unreadable); change requests from the PR listing.
```

`test_an_unreadable_timeline_is_counted_not_hidden` pins both the count and
that the failure is *still* a problem — the assertion on `problems` runs
before the assertion on the body, so a fix that moved the failure out of the
problem list and into the body would fail this test. **PASS.**

## C3 — the problem list is unchanged

`test_a_failing_pr_list_still_posts_gate_rejections` predates this run,
asserts the exact problem string, and passes **unedited**:

```python
            self.assertEqual(problems,
                             ["rm: gh pr list failed: boom"])
```

The body gained a statement; it did not become a second owner of the CLI's
problem strings. **PASS.**

## C4 — the compatibility seam holds

`sources` defaults to `None` and renders nothing, so every existing caller
and every existing body pin is untouched. Asserted rather than assumed, by
`test_a_caller_with_nothing_to_say_gets_todays_body`, which compares the
two calls' output for equality rather than checking for an absent
substring. The three pre-existing `TestComposeQueue` cases pass unedited.
**PASS.**

## C5 — the payload and manifest moved with the root

```
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)

 M factory/manifest.json
 M factory/templates/tools/factory/rejection_mining.py
```

`tests/test_factory_init.py`, which pins payload↔root:

```
Ran 52 tests in 1.262s

OK
```

Detector E reports nothing at the tip — see the battery. **PASS.**

## C6 — the battery

Dedicated worktree at the branch tip, `git status --porcelain` empty:

```
Ran 1348 tests in 15.216s

OK
lint: 0 problem(s) across 24 skills
gates: 0 problem(s)
selftest: ok
```

Four tests added against the base's 1344, none removed or edited. The free
pre-pass is unchanged from the base — no new group, and none removed, which
is expected since this run folds nothing:

```
=== added by this change ===
(empty = none)
=== removed ===
(empty = none)
```

**PASS.**

## What was NOT verified

- **The mine was never run against the live repo.** The brief forbids any
  mode that creates, edits or pins an issue, and no stage ran one. Issue
  #294 was read and not touched; every body above came from the injected
  fake.
- **The `Sources:` line has never appeared on the real queue.** It cannot
  until this merges and the weekly workflow runs. What is verified is what
  the module composes, not what GitHub renders — the line is plain text with
  no markdown constructs, so the risk is small, but it is untested and
  saying otherwise would be a lie.
- **The wording is not pinned character-for-character** in the run-level
  tests, deliberately: they assert the distinction and the counts, so
  rewording the line stays cheap while losing the distinction stays
  expensive. `test_the_sources_line_is_rendered_when_given` pins placement
  at the compose seam, not prose.
- **Every other "nothing happened" line in the repo.** `sweeps: 0 issue(s)
  filed` is the same class and is out of scope by the brief; it remains a
  backlog seed.
