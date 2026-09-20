---
stage: review
run: maintenance:empty-is-not-the-same-as-broken
date: 2026-08-25
assumptions: ["Scaled per the protocol's maintenance guidance: a scoped fix to one module gets a lighter pass than a refactor. Verify's regression is the floor and is not re-run here — this pass looks for what Verify could not, which is the case the criteria list never contained.", "Severity is mine to propose, not to settle: F1 is called major rather than critical because the wrong body it produces is a stale-looking artifact, not lost data or a failed harvest. A human may reasonably raise it."]
---

# Review: say what was read

## Scope

The run's own diff, `7fd7859..841bebc` — nothing else in the tree. The
executable part is `738573f..841bebc`:

```
 factory/manifest.json                            |   2 +-
 factory/templates/tools/factory/rejection_mining.py |  82 ++++++++--
 rejection_mining.py                              |  82 ++++++++--
 tests/test_rejection_mining.py                   | 112 +++++++++++++
```

Three passes over that diff. The first produced F1, which sent the run
back to Implement (`breakdown.md` Notes, I5) and then back through Verify
(C7); the second produced F2. Both are fixed at the tip, and the findings
are recorded here as found, not as if the diff had always read this way.

## Findings

### Major — a listing cut at its window read as a complete one

The fix taught the queue body to distinguish a harvest that found nothing
from one that could not look. It knew two ways to fail. There are three.

- **Scenario.** `gh pr list` returns exactly `LIST_WINDOW` entries because
  the repo has more PRs than the window. `cli.gh_read`'s contract is
  explicit that this is a *success*: "a full window leaves the value
  usable and flips `truncated`: the seam states the fact and the CALLER
  decides what it means." So `read.value` is a list, `_change_requests`
  maps it like any other, `requests` is not `None` — and the new line
  said, of a listing it had seen the top of:

  ```
  Sources: gate rejections from 1 of 1 issue timelines; change requests from the PR listing.
  ```

  Byte-identical to a healthy complete harvest. Measured, not predicted:
  driven through `run_mine` with real full windows before the fix. The
  same holds on the issue listing, and is worse there, because truncation
  shortens `mirrored` — so the line understates the *denominator* it
  prints at full confidence: `1 of 1` where the true second number is
  unknown and larger.

  This is the defect the run exists to remove, reproduced inside the run's
  own fix. The failure reached `problems` and the workflow log; the
  artifact a human reads said the same sentence either way — which is
  `defect.md`'s sentence, one state over.

- **Decision: fixed** (I5). Both listings now name themselves in the body
  when cut. The clause cannot recover the true denominator; saying which
  listing was cut is the honest most it can do:

  ```
  Sources: gate rejections from 1 of 1 issue timelines; change requests from the PR listing. TRUNCATED: the issue listing, the PR listing came back full, so older entries were never read.
  ```

  The design's D1 survives intact. `None` still answers exactly one
  question — *was it read* — which truncation does not contradict, since a
  full window is read, usable, and short. The second fact rides a
  caller-owned list, appended the way `problems` already is, rather than a
  second shape of maybe. Two facts, two channels.

- **Why the run missed it.** `defect.md` was written from an observed
  failure — a `gh` that errored — and the criteria list inherited its two
  states. Truncation is the state where nothing fails, so nothing in the
  evidence pointed at it. Worth carrying forward: a criteria list derived
  from a reproduction covers the reproduction.

### Minor — a default argument that bound nothing

- **Scenario.** No wrong behavior; a maintainability claim, stated as one.
  `_sources` was introduced with `truncated=()`, called from exactly one
  site that always passes it. The default was unreachable, so the binding
  it describes was never executed by any test, and it advertised an
  optionality the module does not have — its other three private helpers
  take their out-params required. The one default that survives is
  `compose_queue`'s `sources=None`, which is a compatibility seam a test
  asserts by comparing two calls for equality.
- **Decision: fixed** (`841bebc`). One token, and the private helpers now
  read the same way.

## Passes with no findings

- **Security.** The `Sources:` line interpolates two integers and a join
  over a fixed pair of literals — no field of any `gh` payload reaches it.
  This matters because the *other* new text in this module's neighbourhood
  does carry untrusted data: change-request excerpts are sanitized and
  fenced as untrusted data, never instructions (ADR-0032), and the review
  confirmed the new line adds no second path around that. No secrets in
  the diff; no new subprocess arguments; no new file writes.
- **Blast radius.** `compose_queue` has exactly one production caller —
  its own module — plus the test file; `_change_requests` and `_sources`
  have one each. The queue marker is read only by `rejection_mining.py`
  itself: no workflow, dashboard, or sweep parses the body, so a body that
  gained a line breaks no reader. Enumerated across the tree, not assumed.
- **Design, otherwise.** The change matches the architecture's split —
  `compose_queue` owns structure, `run_mine` owns wording, the same split
  the CLI's reason line already uses — and the body did not become a
  second owner of the CLI's problem strings: the pre-existing exact-string
  assertion on `problems` passes unedited. The `sources`-renders-always
  decision holds under F1's fix: a clause that appeared only when
  something broke would be indistinguishable from a body written before
  the clause existed.

## Observations, not findings

- **`0 of 0 issue timelines`** on a repo with no mirrored work orders is
  accurate and slightly odd to read. It is what the numbers are; inventing
  a special case for it would add a third phrasing to distinguish from the
  two that matter.
- **The wording has never rendered on GitHub.** It is plain text with no
  markdown constructs, and it cannot be checked until this merges and the
  weekly workflow runs — recorded under Verify's "what was NOT verified"
  rather than asserted away here.
- **`sweeps: 0 issue(s) filed`** is the same defect in a sibling tool and
  is out of scope by the brief. It remains a backlog seed; this run did
  not touch it.

## Verdict

**Ready to ship.** No unfixed critical or major findings: F1 is fixed and
re-verified (C7), F2 is fixed, and the battery is green at the tip —
`1350 tests OK`, `lint: 0 problem(s)`, `gates: 0 problem(s)`,
`selftest: ok`, with the free `one_owner` pre-pass at its unchanged 9
groups, none added and none removed.

Ship prepares and stops per the brief: no merge, no tag. ADR-0036's
non-authoring-reviewer clause independently forbids the author merging
this, and every finding above was found by the author.
