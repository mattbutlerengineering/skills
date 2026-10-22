---
stage: review
run: feature:eval-trends
date: 2026-10-21
assumptions:
  - "Autorun stage, no live user: severity is the reviewer's call. Brief binding: read-only tool, no paid run, no `claude plugin eval`, no live trigger_eval or charter_replay, no model call, no LEDGER, plugin.json, skills, evals or plugin-evals edit; none was made."
  - "Diff scope is `git diff origin/main...HEAD` at bf0a39e (the Verify commit)."
  - "Nothing here changes an Owner decision, a PRD fixed string or ADR-0115's shape. The verdict wording and the charter spread suffix are architecture.md strings (not PRD or ADR), changed with the architecture updated in the same stage."
---

# Review: eval-trends, a read-only eval pass-rate trend view

## Scope

The code diff read in full (eval_trends.py 516 lines, the eval_schema.py
parse_results_stem addition, the factory.py verb, the dual-membership pin,
the CLAUDE.md bullet, ADR-0115), the frozen fixture, the PRD, architecture,
breakdown with Notes, verification.md and the brief. Verification came
first, so the usual order holds.

Examined by: probes in a scratch tree (wrong or impossible dates, future
dates, object and list values, mixed-type case fields, hits above n, n of
0, huge n, an empty root, a missing root); a 46-mutant sweep of
eval_trends.py applied in a `git archive` copy (each `old` string asserted
to occur once, bytecode off; first sweep 4 survivors, final sweep 2, both
equivalent); the Wilson table in the research note recomputed with the
tool's own function; three of the note's sources refetched (S4, S6, S8)
beyond Verify's S1-S3; `python3 one_owner.py` (9 problems, same baseline,
none naming eval_trends, eval_schema or the new tests); `python3 kb.py
drift`; the parse_results_stem round trip (already a test over the real
`results_path` generator with 0, 1, 8 and 9 collisions, so no new
property test was added). Domain passes: none selected. Standards: no
`docs/standards.json` statement matched a finding.

Review commits on this branch:

- 14a82a2 `fix(eval-trends): a record whose date field disagrees with its name, or is not a real day, is a problem`
- 121c329 `fix(eval-trends): an object or list where a scalar belongs is a problem, not a traceback`
- f0d7b01 `fix(eval-trends): plugin aggregates that disagree with the cases are a problem`
- c0048bf `fix(eval-trends): a separating verdict says it is not a significance test; a charter spread says counts only`
- test commit `test(eval-trends): pin the Wilson edge clamp and the largest-refused-record count`
- 8b5d322 `docs(eval-trends): correct the stale 4-case prediction, the verdict string and the n=30 gap (37, not 34)`

## Findings

### Major: a record's date field was trusted over its file name

- Scenario: `trigger-2026-10-05.json` whose `date` says 2026-10-01 was read
  as a 10-01 record, joined the genuine 10-01 record's day and printed a
  "rerun spread 2026-10-01" with no problem; a mis-copied or edited file
  could also fake a second day and manufacture a trend. `2026-13-45` was
  accepted as a day. Same for charter, signals and plugin `startedAt`.
- Standard: none
- Decision: fixed in 14a82a2 (tests first, five RED). The day must be a
  real calendar day and equal the day the name carries; otherwise one
  labelled problem and no row (exit 1). All 55 real records agree, so the
  frozen-tree pins are unchanged. Six existing tests used mismatched
  fixture names and were corrected to name-matched ones.

### Major: an object or list in a record aborted the whole view with a traceback

- Scenario: `"model": {"a": 1}` raised TypeError (unhashable group key) and
  a list `id` raised TypeError (unsortable case tuple) out of
  `load_rows`: no output, no exit code contract, every other record unread.
- Standard: none
- Decision: fixed in 121c329. Such a record is one `malformed field values`
  problem; the rest print.

### Major: plugin counts were trusted past the case list

- Scenario: `casesPassed` 5 of `casesTotal` 3 gives wilson() a negative
  square root (ValueError traceback) once n reaches the 30-case floor;
  `casesTotal` 40 over 1 case skews n against the case set.
- Standard: none
- Decision: fixed in f0d7b01: `aggregates disagree with its cases` unless
  `casesTotal` equals the case count and `0 <= passed <= total`.

### Major: the non-overlap verdict stood bare

- Scenario: the overlap line carried "(descriptive, not a significance
  test)" and the separating line did not, so the line a reader is most
  likely to over-read ("intervals do not overlap") had no caveat. Non-
  overlap of two 95 percent intervals is a conservative test and is not a
  p-value; multiple groups and first-day-against-last-day make any
  implied level worse.
- Standard: none
- Decision: fixed in c0048bf: both verdicts end with the caveat. No
  significance level is stated anywhere in the tool or the note.

### Minor: "sensitive 1..1 of 4" hid that a different case was sensitive in each charter file

- Scenario: the two real charter files each have one sensitive case, but
  `swe-weakens-failing-test` in one and `planner-issue-before-row` in the
  other; the case set omits verdicts, so the spread read as agreement.
- Standard: none
- Decision: fixed by wording in c0048bf: a charter spread ends "; counts
  only, the sensitive case may differ between runs". Naming the ids needs a
  new row field and was not done (the counts-only line is honest and cheap).

### Minor: the research note put the n=30 non-overlap gap at 34 points; it is 37

- Scenario: recomputed with the tool's own wilson(): two 30-case rates
  near 50 percent stop overlapping at an 11-case difference (36.7 points),
  not the 33.6 of two half-widths added (the intervals narrow away from 50
  percent). The 185 (15) and 1000 (7) rows are right. The error understated
  how weak the 30-case floor is.
- Standard: none
- Decision: fixed in 8b5d322. The note's framing of 30 and 2 as a floor
  that avoids absurd intervals, not a trend threshold, was already honest.

### Minor: architecture.md predicted the 4-case reruns classify as `small`

- Scenario: stale prediction (Implement measured otherwise: `runs_per_query`
  differs, so they are different suites).
- Standard: none
- Decision: fixed in 8b5d322, with the verdict string and the new failure
  modes recorded.

### Minor: two Wilson branches were unpinned

- Scenario: dropping the `[0, 1]` clamp passed the suite, but 0 of 5 then
  prints a lower bound of -0.0 and 5 of 5 an upper of 1.0000000000000002;
  `min` for `max` in the too-few-cases count also passed.
- Standard: none
- Decision: fixed (tests only); both mutants now fail.

## Deferred

- Future-dated records are accepted if their name agrees (a 2030 file
  yields a "2030" last day). Rejecting them makes output depend on the
  clock; the name agreement closes the accidental case. Deferred, minor.
- A symlink under the records dirs is followed (`Path.is_file`), and file
  size is unbounded. The tool is local, read-only and run by the Owner on
  their own tree; no write or network path exists. Deferred, minor.
- An empty or wrong root prints `0 record(s)` and REFUSED lines and exits
  0. Every line is a refusal, none reads as "all good", but a one-line
  "no records found under <root>" would be clearer. Changes the pinned
  output, so deferred to the Owner. Minor.
- A trend line compares the first day with the last day only and runs one
  comparison per group; there is no multiple-comparison correction. This is
  stated by the verdict suffix and the header, and the tool never counts a
  verdict as a finding. Documented here, not changed.
- The day-hull (min lower, max upper of the reruns' Wilson intervals) is a
  conservative range, not a confidence interval of any stated level: it
  claims only "the span the reruns' own intervals cover", is wider than a
  pooled interval and so makes "do not overlap" harder to reach. The line
  prints it as `95% lo-hi` per the architecture; relabelling is an
  architecture change, deferred. Minor.
- Mutants left alive, both equivalent: the unsuffixed-name order value 1
  against 0 (suffixes start at 2), and `<=` against `<` at exactly touching
  intervals (a measure-zero tie).

## Passes with no findings

- Statistics other than the above: Wilson at 0 of n, n of n and n of 2e9 is
  inside [0, 1]; cost per pass with zero passes or a missing cost is
  refused, not 0; ties in the day order resolve by `-N` then name.
- Case-set identity: the key is the full sorted tuple of (id, expected,
  query), not the 8-hex label, so a hash collision cannot join two sets;
  duplicates inside a record stay in the tuple; a grown set and a changed
  set are both `case sets differ`; a null model equals only a null model.
  No comparable pair is declared that is not, and a comparable pair is
  missed only when a field of the suite key differs on purpose.
- Fail-closed otherwise: malformed, partial, errored or unreadable records
  are problems (exit 1) and never rows; unknown cost stays None.
- Read-only: the source holds no write, mkdir, replace, subprocess, socket
  or urllib call (the tests grep for it); only `cli.read_file`.
- Research note: S4, S6 and S8 claims match their abstracts; the 10 of 185
  flips and the 159/163 intervals recompute; the `## Not verified` list
  names the unreached sources; detectors C and I are clean.
- Design: the dual-membership pin is 55 pairs with the single new
  `eval_trends` to `cli` edge; no ADR was owed beyond 0115; `kb.py drift`
  and `one_owner.py` are at baseline.
- Frozen fixture: it pins the tool on a byte copy of today's records and
  cannot mask a reader regression (readers are tested on synthetic builders
  too and the live smoke reads the real tree); it will not rot because it
  never re-reads the live files.

## Verdict

Ready to ship. Four majors and three minors fixed; the deferrals are minor
and reasoned. Final checks after the last fix: `tests: 3778 tests across 118
modules ... 0 problem(s)`, `lint: 0 problem(s) across 34 skills`, `drift: 0
problem(s)`, `gates: 0 problem(s)`, `selftest: ok`, `one-owner: 9
problem(s)` (baseline). Not run: any live eval, by the Owner's binding.
Sources S5, S7, S9 and the abstract-only bodies were not refetched here
(Verify and the note's own Not verified list carry them).
