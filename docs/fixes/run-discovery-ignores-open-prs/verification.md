---
stage: verify
run: maintenance:run-discovery-ignores-open-prs
date: 2026-08-25
assumptions:
  - "The centrepiece is not a regression test, because this defect has no failing execution to capture — the pipeline did the wrong thing by not asking a question. What stands in for it is the pin observed going 2 → 1 → 0 across three commits, which is the same evidence a RED/GREEN cycle gives: a checker that never went red proves nothing about what it would catch."
  - "This run was built in a dedicated git worktree cut from origin/main at 622e7c0, not the primary checkout, because another session is driving that checkout on a different branch. Every measurement below comes from that worktree."
---

# Verification: ask before starting

## C1 — the rule has exactly one owner

`docs/pipeline-protocol.md` gains a `### Work already in flight`
subsection immediately after the **Run discovery** paragraph, so a reader
meets the limit where the rule that has it is stated. It is the only place
in the tree that states the rule; `capture` and `idea` name the section
rather than restating it, which is what the pin in C2 enforces.

The one adjacent statement, `work-queue`'s preflight, is deliberately left
alone (D5) and the new section names the relationship in its own words:
*"That one is about order and this one is about duplication; they agree
about what to look at and not about why."* **PASS.**

## C2 — both starting skills recite it, and the pin discriminates

Observed live across three commits, not reconstructed:

```
ffeca82  (I2, pin wired, neither skill reciting)
  LINT: skills/idea/SKILL.md never names the protocol's 'Work already in flight' check, ...
  LINT: skills/capture/SKILL.md never names the protocol's 'Work already in flight' check, ...
  lint: 2 problem(s) across 24 skills

875dfd8  (I3, capture recites)
  LINT: skills/idea/SKILL.md never names the protocol's 'Work already in flight' check, ...
  lint: 1 problem(s) across 24 skills

50173f7  (I4, idea recites)
  lint: 0 problem(s) across 24 skills
```

Two, then one, then zero — each step clearing exactly the skill it
touched. A checker that had never been red would prove nothing about what
it catches, and one that went straight from 2 to 0 would not show that the
two skills are pinned separately.

`test_a_mid_spine_stage_owes_no_recital` carries the discriminating half:
`prd` recites nothing about in-flight work and is **not** flagged. Without
it, a pin that fired on every skill would pass the other cases just as
happily. **PASS.**

## C3 — no existing orientation behaviour changed

The fourth success criterion, and the one with the sharpest available
evidence: the protocol's own orientation suites pass **unedited**.

```
$ python3 -m unittest tests.test_protocol_conformance \
    tests.test_protocol_orientation tests.test_protocol_backlog \
    tests.test_protocol_maintenance_orientation
Ran 23 tests in 0.006s

OK

$ git diff --stat -- tests/          # at the I1 commit
                                     # (no output — no test file touched)
```

`protocol.py` is not in the diff at all. No frontmatter key, no artifact,
no table row was added — this rule is about the moment before an artifact
exists, so orientation has nothing to say about it. **PASS.**

## C4 — a correct recital that wraps is still a recital

Found by the pin failing on `capture`'s correct step: these documents are
hard-wrapped near 72 columns, so the four-word phrase landed across a line
break and a raw substring test read it as missing. Fixed in the checker,
which now normalizes whitespace, rather than in the prose — rewording to
keep the phrase on one line works exactly once and leaves the next author
a trap that fires on a correct edit.

`test_a_recital_that_wraps_still_counts` carries the real wrap from
`capture`, so the case cannot regress into a cosmetic pin. **PASS.**

## C5 — the footprint is what the design said it was

```
$ git diff origin/main --name-only | grep -E '^(factory/|Makefile|\.github/(workflows|CODEOWNERS))'
(no output)
```

Nothing mirrored, so no `factory_init.py update-manifest` and no manifest
line — the breakdown's assumption, checked rather than remembered. The
whole change:

```
 docs/backlog.md              |  2 +-
 docs/pipeline-protocol.md    | 34 ++++
 lint.py                      | 31 ++++
 skills/capture/SKILL.md      | 21 ++-
 skills/idea/SKILL.md         | 16 +-
 tests/test_lint.py           | 81 ++++++++-
```

plus this run's five artifacts. **PASS.**

## C6 — the battery

Re-run after C7's fix; these are the tip's numbers, not the pre-review
ones. Worktree at the branch tip, `git status --porcelain` empty:

```
Ran 1349 tests in 21.709s

OK
lint: 0 problem(s) across 24 skills
gates: 0 problem(s)
selftest: ok
```

Five tests added against the base's 1344, none removed. The free
`one_owner` pre-pass is unchanged against `origin/main` — 9 groups before,
9 after:

```
=== added by this change ===
(empty = none)
=== removed ===
(empty = none)
```

**PASS.**

## C7 — the protocol keeps the section its skills recite

Added by the Review stage. The recital pin binds `capture` and `idea` to
`IN_FLIGHT_HEADING` and binds `IN_FLIGHT_HEADING` to nothing, so deleting
the protocol section left all three agreeing while both skills pointed at
a heading that was gone — this run's own defect one level down.

Verified by mutation, not by argument. With `check_protocol` reverted to
its one-line form and `__pycache__` cleared (a same-length in-place edit
can otherwise serve a stale `.pyc`):

```
- []
+ ["docs/pipeline-protocol.md no longer states 'Work already in flight', which "
+  'capture and idea both recite']

FAILED (failures=1)
```

and with the check restored:

```
Ran 2 tests in 0.045s

OK
```

A test that passes before and after a change proves nothing about the
change; this one was watched failing for the right reason first. **PASS.**

## What was NOT verified

- **That any agent will actually do the check.** This is the honest
  ceiling of the fix and it was named in the architecture before it was
  built (D2): the rule is prose, the pin proves only that the words are
  present, and nothing here measures obedience. What would settle it is a
  second duplicate after this merges — and per the architecture, that
  result is not a disappointment but the missing evidence that would make
  a tool worth an ADR.
- **The check has never run inside the two skills as written.** It ran
  once, by hand, in this session: choosing this run's seed required
  listing all twelve open PRs and mapping their file sets, which is what
  turned up that `lint.py` is claimed by #324 and that nothing else this
  run touches is claimed at all. That is one anecdote from the author of
  the rule, labelled as such, not evidence the instruction reads clearly
  to someone else.
- **The four pre-existing over-length lines** (`lint.py:508`,
  `tests/test_lint.py:622/635/636/756`) are untouched and stay
  non-conforming. Verified as pre-existing against `origin/main`, where
  the same lines sit at 477 and 566/579/580/700. Flagged, not fixed.
- **Whether "review surface" reads clearly on a harness with no pull
  requests.** The wording is deliberately neutral and the greenfield case
  is named in `idea`, but the second harness (ADR-0027) has not been
  exercised against this text.
