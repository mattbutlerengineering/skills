---
stage: review
run: maintenance:closed-intake-mutes-the-detector
date: 2026-08-25
assumptions: ["Scaled as the protocol's Run scale section asks for a scoped maintenance fix: three passes over this run's diff, with Verify's evidence as the floor rather than re-run. The passes went past the changed lines in two directions — into the state the change CREATES (which surfaced F1) and across the run's own artifacts (which surfaced F2) — because neither is visible from the changed lines alone.", "Every claim about pre-existing behaviour was measured against a detached worktree at ee5532c, not inferred from reading the old code."]
---

# Review: a closed intake stops suppressing its detector

## What was examined

`git diff ee5532c..HEAD` — `sweeps.py`, `tests/test_sweeps.py`, and this
run's artifacts. Three passes: correctness, design, security.

The changed logic is nine lines. The reviewable surface is larger, because
narrowing a dedupe rule changes which states the board can be in — and
because a maintenance run's artifacts are scanned by the same gates as its
code.

## F1 — the fix creates a two-issues-one-key state and nothing pinned it. **Minor. Fixed.**

Before this run a singleton detector key could appear on the board at most
once, ever — that was the defect. After it, the normal steady state is the
key appearing **twice**: the old closed intake, and the new open one filed
when drift returns.

The implementation already handles that correctly, and I did not change it:
`keys` is a set, so the open issue contributes the key whatever the listing
order.

**Failure scenario.** A later change rewrites the loop as a dict keyed by
intake-key, or breaks on the first match, and whichever issue `gh` happened
to list first decides. If that is the closed one the detector is muted
again — the original defect, restored, with a green suite.

**Fix.** `test_an_open_issue_wins_over_a_closed_one_carrying_the_same_key`,
subtested in both listing orders (`901aeb9`). It passed on first run, which
is the point: it pins behaviour that was already right and was one refactor
away from silently reverting.

## F2 — this run's own artifact turned the branch tip red. **Major. Fixed.**

Verify recorded `gates: 0 problem(s)`. At the branch tip, `gates.py` said:

```
C: docs/fixes/closed-intake-mutes-the-detector/verification.md:145 dangling ADR-00NN (no docs/adr file)
C: .../verification.md:163 dangling ADR-00NN (no docs/adr file)
C: .../verification.md:164 dangling ADR-00NN (no docs/adr file)
gates: 3 problem(s)
```

*(paths elided for width, and the four digits elided as `NN` — this file is
scanned by the same detector, so quoting the message verbatim would
reproduce the failure it describes. That is the finding.)*

The cause: Verify's own "contaminated checkout" section quoted a four-digit
ADR number three times — once inside a fence carrying detector D's message,
twice in the prose explaining it — for an ADR that exists only as another
session's untracked file and in PR #333's branch, not on this one. Detector
C (`gates.py:373`) reads line by line with no notion of a fenced block, so
all three read as claims.

**Failure scenario, and it is not hypothetical.** `check.yml` runs `gates.py`
on every push. This branch would have gone red the moment it was pushed, on
an artifact rather than on the fix — and the run that wrote it had recorded
that same command green. The gap is that Verify measured gates *before*
writing the section that describes what gates said.

**Fix** (`689da72`): the digits are elided as `ADR-00NN` with the elision
marked at the fence, the prose names the number instead of writing it, and
verification.md gains a section recording the constraint that forced this.
Gates at the fixed tip:

```
gates: 0 problem(s)
selftest: ok
```

**The constraint itself is the more interesting half**, and it is seeded
rather than fixed here: *a run artifact cannot record a detector-D failure
about a missing ADR*, because writing down what D said makes C fail on the
same file. PR #333 fixes the sibling case one plane over — a quoted
work-order token in a PR body, in `validator.py` — and its diff does not
touch `gates.py`, so this case survives that merge. Out of scope for a run
whose mandate is one dedupe rule in `sweeps.py`; backlog seed appended.

## F3 — a non-object entry in the dedupe listing raises. **Observation, not a finding.**

`known_keys` calls `issue.get(...)` without checking the entry is a mapping:

```
after: raises AttributeError 'str' object has no attribute 'get'
```

Identical before this run:

```
before: raises AttributeError 'str' object has no attribute 'get'
```

So this run neither introduced it nor worsened it — the new
`issue.get("state")` sits one line above an `issue.get("body")` that has
always made the same assumption.

Recorded because `sweeps.py` carries an explicit `TestUntrustedInputBoundary`
class for the Sentry payload, and the contrast is easy to misread as
coverage this listing also has. It does not: the Sentry payload is
third-party data, this listing is our own GitHub, and the module trusts it.
That is a defensible line and it is nowhere written down. Owed to Operate as
a seed, not fixed here — a shape guard is a behaviour decision about a
listing this run has no mandate over.

## F4 — no new one-owner group. **Checked, clean.**

`RE_REPORTED = ("sentry:",)` is a new module-level constant, and this repo's
own pre-pass is the check for whether it duplicates a fact someone else
already owns:

```
one-owner: 9 problem(s)
```

Nine — the same nine `main` reports, no new group. The `sentry:` prefix also
appears at `sweeps.py:174` as `f"sentry:{short_id}"`, a different value
under `ast.unparse` and correctly not grouped: the constant is the
namespace, the f-string is a key built in it.

## Correctness pass — what was checked and held

- **`str.startswith` accepts a tuple**, so `key.startswith(RE_REPORTED)`
  works as written and extends by adding one entry, with no other edit.
- **The window rule composes.** On a truncated listing the full-window
  problem is still reported and the keys seen are still returned. The new
  filter only ever *removes* keys, which means more re-filing — exactly what
  `full_note` already warns about. No new interaction.
- **An empty marker on a closed issue** (`intake-key:` with nothing after)
  no longer contributes `""` to the set. Inert in both directions: every
  intake key is built at a fixed site — `"sweep:label-drift"`
  (`sweeps.py:198`), `"sweep:reconcile"` (`:218`), `f"sentry:{short_id}"`
  (`:174`) — so none can be empty, and an empty entry could never have
  suppressed anything. (An earlier draft of this review claimed
  `plan_problems` rejected such a plan. It does not: it checks labels and WO
  tokens only. The invariant is at construction, not at validation.)
- **The literal-`CLOSED` comparison** is pinned against five non-matching
  shapes including a non-string, so the branch cannot be entered by accident.

## Design pass

The change matches `architecture.md` with no deviations to the design
itself; the one logged Note is `LIST_CALL`, a test pin that had to move with
the `--json` field list.

D1's constraint — that the rule must read a key *string*, because a closed
issue has no `Intake` anywhere — is what makes the namespace prefix
load-bearing, and the docstring now says so. That is the part most likely to
be undone by someone tidying key formats later, and it is the part carrying
the most words.

No new module, no new import, no new dependency. `sweeps.py` is not in
`factory_init.MIRRORS`, so nothing mirrors and no manifest regenerates —
confirmed, not assumed:

```
$ python3 -c "import factory_init; print(any('sweeps' in str(m) for m in factory_init.MIRRORS))"
False
```

## Security pass

Nothing found. No new input boundary: `state` is read from the same listing
the function already made, compared against a literal, and never rendered
into an issue body. No subprocess, no file write, no new network call.

The one thing worth stating plainly, because it is the risk this change
actually carries: the fix makes the sweep able to **create issues it
previously could not**. It creates none today — both detectors report clean,
and Verify measured that — but whoever merges this is enabling a filing
path, not only fixing a set-membership test.

## State after the fix

Measured in a detached worktree at `689da72`, whose `git status --porcelain`
is empty, because another session's untracked ADR fails detector D in the
shared checkout (`verification.md` records it):

```
Ran 1349 tests in 15.921s

OK
lint: 0 problem(s) across 24 skills
gates: 0 problem(s)
selftest: ok
```

No critical findings. F1 and F2 fixed in this run; F3 recorded as an
observation and owed to Operate; F2's underlying constraint seeded to
`docs/backlog.md`.
