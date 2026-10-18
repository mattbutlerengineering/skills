# A zero count in a verification Summary names nothing

- Status: provisional
- Date: 2026-10-17

Recorded by the `a-zero-count-names-nothing` maintenance run
(`docs/fixes/a-zero-count-names-nothing/`), unattended, so it is
provisional. Supersedes in part [ADR-0107](0107-a-summary-never-rolls-unknown-up-to-pass.md):
its "Satisfied by naming the kind" clause, and the consequence that a
Summary can satisfy the rule by negation.

## Context

ADR-0107's roll-up is satisfied when a `## Summary` carries any word
from the unknown vocabulary outside a fence. Its premise was that a
count carries its word ("1 NOT RUN"), so naming covers counting. That
holds for every count except zero. The verify template asks for
pass/fail counts, and both artifacts the rule had judged on 2026-10-17
wrote "N PASS, 0 FAIL, 0 NOT RUN". A Summary that says zero items were
not run matched on "NOT RUN" and so counted as naming the kind. When a
criterion was re-run and dropped to NOT RUN with the Summary left as
written, which is the stale-Summary drift the rule exists for, the gate
passed. The fail-closed-roll-up retro reproduced it on a real artifact
in memory. No artifact on main has the shape over a disclosure, so this
is prevention.

## Decision

An unknown-vocabulary match does not name the kind when a zero count
directly precedes it (`gates.SUMMARY_ZERO_COUNT`, read by
`gates._names_unknown`). A zero count is `0`, `zero`, `no`, `none` or
`nothing` as a whole word, then at most one word, then an optional
`was` / `were`, then only spaces, hyphens or emphasis markers. So "0 NOT
RUN", "0 not run", "zero skipped", "0 N/A", "**0** NOT RUN", "0
criteria skipped", "no criteria were skipped" and "nothing was skipped"
name nothing.

Every other match still names: "1 NOT RUN", "10 NOT RUN", "2 skipped",
"criterion 4 was not run". Matches are judged one at a time, so "0 NOT
RUN, 1 skipped" names on its second. A Summary with no disclosed
criterion is never refused by the roll-up, whatever its counts say. The
trigger, the grandfather cutoff, the vocabulary and the problem string
are ADR-0107's, unchanged, and `ROLLUP_ADOPTED` does not move: no judged
artifact on main changes outcome.

## Rejected alternatives

- **The count must match** (compare the Summary's numbers with the
  number of disclosed sections). The Owner rejected it for this run, and
  ADR-0107 already rejected a count requirement. It is a second grammar
  over free prose, and it would push authors toward a number rather than
  toward honesty.
- **Zero as `0` and `zero` only.** It leaves "no criteria were skipped"
  naming the kind, the negation ADR-0107 accepted as a known gap. Adding
  `no`, `none` and `nothing` under the same one-word bound costs one
  alternation and is tested.

## Consequences

- A longer negation ("no live check was skipped", two words between the
  zero and the verb) still names the kind. It is an accepted limit,
  marked `lean:` in `gates.py`; widen the bound on a real artifact that
  uses one.
- An honest Summary whose only unknown-kind mention is a negation of the
  one criterion it disclosed ("nothing was skipped except live
  dispatch") is now refused. It reads as a pass up to the exception, and
  naming the item ("1 skipped") satisfies the rule.
- The verify template's Summary guidance says a zero count names
  nothing.
- `gates.py` ships into stamped repos, so the change reaches them on
  their next payload update. The `gates_selftest.py` fixture has no
  zero-count row.
