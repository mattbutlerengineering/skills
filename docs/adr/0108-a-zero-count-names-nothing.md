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
`was` / `were`, then only spaces or emphasis markers. So "0 NOT
RUN", "0 not run", "zero skipped", "0 N/A", "**0** NOT RUN", "0
criteria skipped", "no criteria were skipped" and "nothing was skipped"
name nothing.

Amended 2026-10-18 by this run's review fix loop (review.md Minors 1
and 3), before the ADR left provisional:

- The whole-word zero is also not read straight after a `.`, so "1.0
  NOT RUN" is one number and still names. The guard was in the code
  from the start; this states it.
- The one word may not be a pass/fail count label (any word starting
  `pass` or `fail`, case-insensitive). "0 FAIL NOT RUN: criterion 9"
  counts failures, then names the criterion; it names.
- A hyphen is not part of the tail. A spaced ASCII dash separates
  clauses as an em or en dash does, so "0 FAIL - NOT RUN: criterion 9"
  and "no regressions - NOT RUN: criterion 9" name. "0-skipped" is
  unaffected: the vocabulary's leading boundary never matches after a
  hyphen, so it names nothing either way.

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
  Amended 2026-10-18 (maintenance run the-selftest-cannot-see-a-dodge):
  the selftest now has two zero-count rows, `H zero count` ("1 PASS, 0
  FAIL, 0 NOT RUN.") and `H none skipped` ("1 PASS; none skipped."),
  each over a criterion disclosed NOT RUN, so a stamped repo's
  `gates.py --selftest` goes red if the zero reading regresses.
- Zero shapes outside "directly precedes" still name the kind, and are
  accepted limits (review.md Minor 2; no tracked artifact uses one over
  a disclosure): a count hard-wrapped onto the next line ("11 PASS, 0
  FAIL, 0" then "NOT RUN."), a count written after its word ("NOT RUN:
  0", "Not run: 0."), table cells (`| NOT RUN | 0 |`, or a header row
  over a counts row), an en dash ("0 – NOT RUN"), "0 (zero) NOT RUN",
  "0: NOT RUN" and "0x NOT RUN". Since the 2026-10-18 amendment a
  spaced hyphen joins them ("0 - NOT RUN"), and so does a zero whose
  one word starts `pass` or `fail` ("nothing passing was skipped").
  Widen on a real artifact, as for the longer negation.
- Amended 2026-10-24 (maintenance run a-long-line-stalls-the-gate):
  `_names_unknown` reads the zero count only within
  `SUMMARY_ZERO_COUNT_WINDOW` (64) characters before each match, so the
  roll-up is linear in line length. Any count of one dictionary word
  fits; a wider one (a long run of spaces or emphasis markers) is cut by
  the window and names. That limit fails open (H passes a stale
  Summary), which is why the window is not narrower; on a real artifact
  that uses one, read the prefix in reverse instead of widening.
