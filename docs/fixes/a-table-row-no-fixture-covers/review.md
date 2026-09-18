---
stage: review
run: maintenance:a-table-row-no-fixture-covers
date: 2026-08-30
assumptions:
  - "No live operator input; nothing found is blocking."
  - "Open-PR recon ran before the fix: two open PRs touch protocol.py or orientation files (#401 orientation_pack.py, #351 protocol.py). #351 adds RUN_ARTIFACTS derived from both tables and refactors the checkbox helper; it changes no row and does not touch next_stage's walk. No overlap."
---

# Review: a table row no fixture covers

## Findings

### 1. The assertion is on both tables, one of which was already clean — accepted

Adding an assertion to a table with no hole looks like scope creep. It is
the opposite: the two tables were indistinguishable from outside until
someone computed the coverage, and the one that turned out to be clean
was clean by luck, not by construction. Asserting only the broken one
would leave the same blind spot on the other.

### 2. Both directions in one test — accepted

`reachable - covered` and `covered - reachable` are two halves of one
claim about one pair of sets. Split across two tests, a run can pass the
half that is checked while the other half is the one that broke. Kept
together, with a distinct message per assertion so the failure says which
direction went wrong.

### 3. The reverse direction has no live defect — noted

Nothing today has an `expected` file naming an impossible stage. It is
asserted because `test_decision_table` cannot catch it: an `expected` of
`prd` on a maintenance fixture would make `next_stage` and the file
disagree and fail loudly *only* if `next_stage` does not also return
`prd`. The failure mode it closes is a typo that agrees for the wrong
reason.

### 4. `decompose` and `architect` share a completion rule — noted, not acted on

`_maintenance_stage_complete` returns the same expression for both
(`artifact exists or not a re-entry-at-architect run`). The new fixture
pins `decompose` for one shape only. Enumerating the interaction between
the two rows is a larger job than closing the row, and the closure
assertion will now flag it if either row stops being reachable.

## Not found

- No production-code change. The diff is one fixture tree and two test
  files.
- No mirrored file, so no `update-manifest` and no detector E interaction.
- No conflict with #351 or #401.

## Verdict

Ship.
