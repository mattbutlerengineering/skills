---
stage: review
run: maintenance:seen-before-partner
date: 2026-10-24
assumptions:
  - "Soft gate holds: verification.md exists (criteria pass), so the review does not invert the usual order."
  - "Scope is `git diff origin/main..HEAD` after `git fetch origin` (10 files, 1,072 insertions, 7 deletions; 9 commits, 44335fa autorun brief to f289dab verify). Maintenance run scaled per the protocol's Run scale section: Verify's regression tests and mutation table are the floor and were not re-run; the suite, lint, drift and gates were re-run once as a sanity check, not as a second Verify."
  - "Severity of the m5 survivor is Reviewer's call: minor. The behaviour is correct today (Verify criterion 5, identical on origin/main), the loss if it regressed is the exemplar clean run named in a human-read lesson's text and sources, and no gate consumes it. Not an Owner answer."
  - "The m5 gap is in scope for a one-test addition because this run rewrote that exact lookup (inline `next(...)` to `next(iter(_partners(...)), None)`), but it is deferred, not fixed, because this stage records findings and a minor may be deferred freely. Not an Owner answer."
  - "The brief-deviation recorded in architecture.md (seen stays equal to measured; pairing changes who it skips, instead of the brief's fold-on-use rule) is carried as an open Owner confirmation, not ranked as a code finding. The skill gives no default for confirming a deviation and the brief is silent, so it is surfaced, not decided."
  - "Domain passes: none selected. Changed paths are decompose_lessons.py, its test, docs/adr and docs/fixes; none contains a payments, migrations or dependency-manifest word or pattern."
  - "docs/standards.json was read. `stdlib-only` (factory, MUST) is the one statement this diff could touch and it holds (no import added); `eval-honesty` is untouched."
---

# Review: a hit run seen before its clean partner still pairs

## Scope

The diff since the run began: `git diff origin/main..HEAD`, 9 commits.
Code and tests: `decompose_lessons.py` (32 lines changed: new `_partners`
and `_spent`, `pairs` uses `_partners`, `fold` skips `_spent(...)` instead
of `set(seen)`) and `tests/test_decompose_lessons.py` (96 lines added).
Decisions and docs: ADR-0117 (new), ADR-0116's status line, the
`docs/adr/README.md` rows, and the run's own artifacts. Nothing under
`skills/` and not `.claude-plugin/plugin.json` (`git diff --name-only
origin/main..HEAD | grep -c "^skills/\|plugin.json"` prints 0).

Re-run for this review: `python3 run_tests.py` (3814 tests, 118 modules, 0
problems), `lint.py` (0), `kb.py drift` (0), `gates.py` (0) and
`gates.py --selftest` (ok). `adr_status.py` standings: ADR-0113 partial (by
0116), ADR-0116 `superseded in part by ADR-0117 (the pairing skip rule;
provisional)`, ADR-0117 provisional.

## Findings

### Minor: no test pins which clean run `pairs` uses as the exemplar (Verify mutation m5 survives)

- Scenario: H followed by two clean runs C1 and C2 of the same kind and
  label. `pairs` takes the first in record order (`next(iter(_partners(...)),
  None)`), so the lesson text and sources name C1. Change that to the last
  (`_p[-1]`) and all 109 tests stay green (Verify mutation m5), so a
  regression would silently rename the exemplar run in every lesson text and
  `sources` and nothing would turn red. Verify's by-hand check (criterion 5)
  shows HEAD and origin/main agree on the first, in both record orders. The
  same mutation on origin/main's inline form also leaves its 101 tests
  green, so the gap predates this run. It is in scope for a one-test fix
  anyway because this run rewrote that exact lookup. architecture.md calls
  the behaviour "pinned", which no test makes true.
- Standard: none
- Decision: deferred — behaviour is correct today and proven by hand, the
  consumer is a human-read lessons list, and this stage does not edit code.
  The fix is one test: two clean runs of one kind and label ahead of a hit
  run, assert `pairs(...)[0]["clean"]` is the first, in both record orders.
  It can ride along in this PR if the Owner wants it.

### Minor: three over-79-column lines remain in `decompose_lessons.py`

- Scenario: lines 280, 403 (the `pairs` docstring) and 525 are 81, 91 and 88
  columns. All three exist on origin/main
  (`git show origin/main:decompose_lessons.py | awk 'length>79' | wc -l`
  prints 3) and none is added or changed by this diff (the added-lines check
  `git diff -U0 origin/main..HEAD -- decompose_lessons.py
  tests/test_decompose_lessons.py | grep '^+' | awk 'length>80'` prints
  nothing). They carry over from the previous run's review, which deferred
  them. Recorded so they are not mistaken for this run's.
- Standard: none
- Decision: deferred — pre-existing, no gate or standard enforces a column
  limit, and a three-line rewrap is a separate cleanup.

## Passes with no findings

- **Correctness.** `_spent` and `_partners` match architecture.md and ADR-0117.
  `_partners` is exactly the old inline filter (same kind, same label, count
  0, record order), so `pairs` is unchanged when `skip` holds the keys it is
  given. `_spent` returns a seen hit run's key only when a clean run of its
  kind and label is also seen for that signal; the count-0 guard keeps clean
  runs out of it (mutation m7), the seen-partner test keeps an unpartnered
  seen hit run pairing (m1, m2, m6). `pairs(skip=...)` is still called in
  one place (fold) plus `render`, which passes no skip.
  - Two documented behaviour changes, checked against the code. (1) A clean
    run that arrives later but sorts earlier in record order does not re-open
    a pair already made: H and its first partner are both seen, so H is
    spent; lesson sources can therefore differ from a single `update` over
    all the runs. Accepted in ADR-0117 Decision ("even earlier in record
    order, does not re-open the pair") and pinned by
    `test_a_seen_hit_run_with_a_seen_partner_stays_skipped`. (2) A hit run
    and its partner both already folded unpaired under ADR-0116 stay
    stranded: the header cannot tell that from a dropped lesson, ADR-0117
    Consequences records the gap and the delete-and-`update` recovery. Both
    are decisions, not defects, and both are in the ADR.
  - Double-derive and re-vote, traced on every path. `fold` still returns
    `sorted({*seen, *_measured(records)})`, so after any `update` every
    measured (signal, run) is seen; a second `update` over the same records
    finds each hit run seen with its partner seen, so `_spent` covers it and
    nothing is paired. `_apply_candidates` only ADDs an absent id or EDITs on
    grown sources, so a pair that re-forms cannot duplicate a lesson. Votes
    read `seen` at the start of the update (`votes` and `_ballot` skip a
    voter seen for the lesson's signal), which this diff does not touch: a
    seen unpaired hit run still cannot vote, and a source cannot vote on
    its own lesson, so the late pair adds no vote. Verify's idempotence fuzz
    (1,500 sequences x 3 stages, votes on and off) found 0 repeats that change
    the file, on HEAD.
  - A lesson dropped at 0 is not re-derived from the same runs: a hit and
    partner first measured in one `update` pair in it and are both seen after
    it, so they are spent (ADR-0117 Decision, third bullet). A genuinely new
    hit run with the same id still ADDs it, as before this diff.
  - Cost: `_spent` scans the records once per seen hit run, quadratic in the
    record count with no git call; the ledger is tens to hundreds of runs, so
    a note in ADR-0117 Consequences is all it needs.
- **Design.** The diff matches architecture.md: `seen`, `_measured`, `load`,
  `serialize` and the size bound are byte-identical in effect, no new import
  (dual-membership pin stays 55), no skill edit so no wave release PR is owed.
  The decision passes the protocol's ADR test and has one, ADR-0117;
  ADR-0116 got a status-line change only. Its Decision section (and the whole
  body below the status line) is untouched: `git diff --stat
  origin/main..HEAD -- docs/adr/0116*` shows 1 insertion, 1 deletion, the
  status line. The supersession follows ADR-0113's pattern (status line plus
  the README row). The immutability rule holds: `_spent` builds a fresh set,
  `fold` passes `set(seen)` and a new sorted list, and no input is mutated.
  `_spent` is 14 lines and `_partners` 4; no function nears 50 lines.
  - ADR-0117 correction: commit 8d86b0a changed the Rejected alternatives
    figure from "211 of 3,000 sequences" to "211 of 1,500", matching the
    Context paragraph and architecture.md (lines 8 and 55). The ADR now says
    1,500 in both places. The figure is the Architect's own fuzz count; the
    different counts elsewhere (111 of 3,000, 576 of 3,000) measure other
    properties and are labelled so. No discrepancy remains.
  - Open item, not a code finding: architecture.md flags a DEVIATION FROM
    THE BRIEF "for the Owner to confirm". The brief asked to fold a run into
    `seen` only once used; the design keeps `seen` equal to measured and
    changes who pairing skips, because both literal readings were reproduced
    as unsound (fold-on-vote loses the lesson through the vote path; leaving
    an unpaired hit unseen lets it vote on later lessons and changes the file
    on a second update in 211 of 1,500 sequences). The result meets the
    brief's acceptance lines. This stage has no record of the Owner's answer,
    so the confirmation stays open for the Owner at the Ship hand-off.
- **Security.** No input surface changes: same file, same reads through
  `cli.read_file`, no subprocess, no network, no new write path, no new
  string echoed to the user.
- **Complexity.** No cut-list entry confirmed. `_partners` has two callers
  (`pairs`, `_spent`) so it is not speculative; `_spent` has one caller but is
  the named seam the tests pin and decomposes `fold`, not an abstraction
  awaiting reuse. The diff adds no `lean:` marker. Shape concern for
  `deepen`: none.
- **ADR compliance.** ADR-0116 (provisional, partly superseded): the entry
  shape, refusal of the old per-run shape, size bound and vote guard all
  stand and are untouched. ADR-0113 (derived-only file, single writer,
  root-only importer) stands. ADR-0095 active: no `plugin.json` or `skills/`
  change. ADR-0100 (each stage's artifact committed at its boundary): holds,
  one commit per stage. ADR-0075: reads unchanged. No violation.
- **Standards.** `stdlib-only` holds; `eval-honesty` untouched (no eval
  definition or result changed). No finding cites a standards statement.
- **Domain passes:** none selected.

## Verdict

Ready to ship. No critical finding exists and none is unfixed. No major
finding exists, so no Owner arbitration is owed on severity. Two minors are
deferred with reasons (the m5 test gap, with a one-test fix that may ride
along; the three pre-existing long lines). One non-finding stays open for
the Owner: confirm the architecture.md deviation from the brief's fold-on-use
rule (seen stays equal to measured; pairing skips only a seen hit run with a
seen partner). The suite, lint, drift and gates are green. Passes not run or
unknown: none; the payments, migrations and dependencies passes were not
selected by the diff. Nothing was run live (no model, no paid eval), which
is by the brief.
