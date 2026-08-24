---
stage: decompose
run: maintenance:gate-timeline-timestamp-trust
date: 2026-08-23
assumptions:
  - "The cut was not reviewed live — this run is autorun-driven, so the two rows below are read out of architecture.md's Components section rather than from the operator's judgment. A mis-sized row is a note to log at implement time, not a design change."
  - "Rows carry an item letter and a size class (ADR-0034 vocabulary), matching this repo's maintenance-run precedent (docs/fixes/one-fact-one-owner/breakdown.md). No row mints a WO-#### id and no row carries a (tracker: #N) reference — defect.md rules out tracker interaction, and minting a WO- token with no issue behind it would run the dispatch plane ahead of the knowledge plane (ADR-0032). These checkboxes are the whole state (ADR-0026)."
  - "The test-ordering rule is served INSIDE A1 rather than as a standalone pin item: the case is written against today's code, watched to raise ValueError, and that failure is recorded in the commit message before the guard lands. Splitting it across two items would leave the tree red at an item boundary, which the precedent refuses."
  - "A2 carries no test. It changes comments only, so its criterion constrains what a reader can find and what the diff must NOT contain; the battery staying green is what proves it changed no behaviour."
---

# Breakdown: the admission gate rejects a timestamp that is not one

Progress lives in the checkboxes below. Source is `architecture.md` in this
directory, which chose to complete `label_events`' existing drop rule rather
than add a problems channel, harden `_parse_ts`, or guard the two
`waited_seconds` call sites.

**The one thing that must not happen.** No call site changes. The value of
this design is that `gate_digest.py:109`, `dashboard.py:158` and
`rejection_mining.py:146` are untouched and every existing test keeps its
expectations. If a diff in this run edits a caller, the item has been
misread — revert it. The same goes for `human_gates.py`'s shape: every
function in it is pure and returns no problems, and this run does not change
that.

**The battery is green at every item**, in full: `python3 -m unittest
discover tests`, `python3 lint.py` (matching `lint: 0 problem(s)`) and
`python3 gates.py && python3 gates.py --selftest` (matching `gates: 0
problem(s)`).

**Manifest churn — every item has it.** `human_gates.py` IS a
`factory_init.MIRRORS` entry (a payload tool imports it), so any item that
edits it must run `python3 factory_init.py update-manifest` and commit the
regenerated manifest in the same change. This paragraph originally claimed
the opposite; see Notes.

## Milestone A: a malformed timeline stops crashing the digest

Demonstrable at the close: a timeline whose label event carries a
non-ISO `created_at` produces no event, no crash, and no change to any
well-formed result — including through `gate_passages`, the caller path
where the `ValueError` actually surfaced.

- [x] **A1** the drop rule covers an unparseable timestamp — size:S, blocked by: —
  - Accept: with the guard reverted, a `tests/test_human_gates.py` case
    feeding `label_events` an event whose `created_at` is `"yesterday"`
    and calling `gate_passages` on the result raises
    `ValueError: Invalid isoformat string: 'yesterday'`; with the guard
    in place the same input yields `[]` from `gate_passages` and the
    malformed event is absent from `label_events`' output, while a
    sibling case proves a well-formed timeline in the same test file is
    unchanged. Full battery green.
  - Blocked by: —

- [x] **A2** the precondition is recorded where a future reader will look — size:XS, blocked by: A1
  - Accept: `waited_seconds` carries a comment naming `label_events` as
    what establishes its ISO precondition, `label_events`' docstring
    states the third clause of its drop rule, and the module's only
    `except` is the one inside the admission guard — `waited_seconds`
    and both its call sites (`human_gates.py:122`, `gate_digest.py:149`)
    carry no handler, so the policy keeps one owner. Full battery green; no behavioural diff, so no test
    changes in this item.
  - Blocked by: A1

## Design gaps found

None. `architecture.md` answered the one open question (which function owns
the rejection) with a caller count, and nothing in the cut needed a decision
it had not made.

## Notes

**2026-08-23 — A2's criterion was unsatisfiable as written.** It asked
that `grep -n 'try' human_gates.py` find nothing, but line 86 already
contains "re-entry", which matches. The criterion now greps for
`except`, which is what it was actually asserting: no exception handler
in this module. Same intent, checkable — and the intent itself needed narrowing at
implement time: reusing `_parse_ts` to test parseability requires exactly
one `except ValueError`, in the admission guard. What A2 was really
asserting is that neither `waited_seconds` nor its two call sites gains a
handler, which is what the criterion now says.

**2026-08-23 — the "no manifest churn" claim was false.** `human_gates.py`
is a `factory_init.MIRRORS` entry, and A1's edit turned
`test_every_mirrored_root_file_matches_its_payload_copy` red until
`python3 factory_init.py update-manifest` ran. The manifest moved by one
checksum. The preamble above is corrected; the run's diff therefore
includes `factory/manifest.json` and the payload copy of the module.

**2026-08-23 — A1 and A2 landed in one change, not two commits.** A2 is
three comment lines inside the two functions A1 edits; sequencing them as
separate commits would have meant touching the same two docstrings twice
and regenerating the manifest twice for one behavioural change. Both rows'
criteria were checked independently before either box was ticked. The cut
was right that they are separable concerns and wrong that they are
separable diffs.
