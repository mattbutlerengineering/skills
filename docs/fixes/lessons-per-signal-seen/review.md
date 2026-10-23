---
stage: review
run: maintenance:lessons-per-signal-seen
date: 2026-10-23
assumptions:
  - "Soft gate holds: verification.md exists (26 of 26 PASS), so the review does not invert the usual order."
  - "Scope is `git diff origin/main..HEAD` (14 commits, 11 files, 1,502 insertions, 57 deletions) after `git fetch`. origin/main is an ancestor of HEAD. Maintenance run scaled per the protocol's Run scale section: Verify's regression tests are the floor and were not re-verified; the suite, lint, drift and gates were re-run once as a sanity check, not as a second Verify."
  - "Severity of the three over-79-column lines and the `_ballot` docstring is Reviewer's call, minor, because no linter or gate enforces a column limit and the module's own convention (0 such lines on origin/main) is the only standard. Not an Owner answer."
  - "The Major finding is pre-existing, not introduced by this diff, and its defer-or-fix decision is left undecided here. The review skill gives no named default for a major (the user fixes or defers it) and the brief is silent, so it is surfaced for the Owner rather than guessed."
  - "The size-bound edge Verify flagged as caught by one test is not a finding: the `>` boundary is pinned on both sides by two tests (one byte over refuses, exactly at the bound loads). The one-test observation was about the `>=` mutation, which is the correct single test for a single comparison."
  - "Domain passes: none selected. Changed paths are decompose_lessons.py, its test, docs/adr, docs/features and docs/fixes; none contains a payments, migrations or dependency-manifest word or pattern."
  - "docs/standards.json was read. Statements in the `factory` domain apply (root tool); `stdlib-only` is the one this diff could touch, and it holds (no import added)."
---

# Review: a lessons ledger that keeps a signal that matures later

## Scope

The diff since the run began: `git diff origin/main..HEAD`, 14 commits from
`ab8c94a` (autorun brief) to `aa062e5` (verify). Code and tests:
`decompose_lessons.py` (131 lines changed) and
`tests/test_decompose_lessons.py` (299). Decisions and docs: ADR-0116 (new),
ADR-0113's status line, the `docs/adr/README.md` rows,
`docs/features/decompose-lessons/architecture.md` (two dated notes), and the
run's own capture, architect, decompose and verify artifacts. Nothing under
`skills/` and not `.claude-plugin/plugin.json` (`git diff --name-only
origin/main..HEAD | grep -c "^skills/\|plugin.json"` prints 0).

Re-run for this review: `python3 run_tests.py` (3806 tests, 118 modules, 0
problems), `python3 -m unittest tests.test_decompose_lessons` (101 tests, OK),
`lint.py` (0), `kb.py drift` (0), `gates.py` (0) and `gates.py --selftest`
(ok). I also ran my own reproduction of the finding below on origin/main and
on HEAD, in throwaway directories.

## Findings

### Major: a hit run seen before its clean partner exists never pairs (pre-existing, same class as the fix)

- Scenario: `docs/factory/decompose-lessons.jsonl` already exists. Update 1
  measures a feature re-plan hit run H (2 of 10, observed) and no clean
  feature run of the same label yet, plus an unrelated maintenance pair so
  the file is written. `fold` records `replan:feature:h` in `seen` because
  the signal was measured, whatever its count (`_measured`,
  decompose_lessons.py:573-576). Update 2 adds a clean feature run C (0 of 8,
  observed). `pairs(records, skip=set(seen))` skips H, so no
  `replan/feature/added` lesson is derived. Output, HEAD:
  update 2 `['decompose-lessons: wrote docs/factory/decompose-lessons.jsonl']`
  with no ADD line, against the control (one update over H, the maintenance
  pair and C) `['ADD replan/feature/added', 'ADD replan/maintenance/dropped',
  'wrote ...']`. origin/main behaves identically (header `feature:h`), so this
  diff neither introduced nor worsened it. It is the same silent undercount
  the run fixed, with the maturing input being the clean partner rather than
  the review. Reproduction script:
  `/private/tmp/claude-501/-Users-mbutler-github-skills/2c98a723-2833-4868-8bbf-e4099b478ada/scratchpad/rv/orphan.py`
  (`python3 -I orphan.py <tree>`).
- Contract affected: ADR-0116's Decision says a run is seen for a signal
  "exactly when that signal was measured", and architecture.md's Approach
  says each signal's maturity is independent. Neither covers a hit run whose
  pairing input (a clean run of its kind and label) is absent. The reason
  `seen` must cover a hit run is to stop a lesson dropped at 0 being
  re-derived (ADR-0113 Consequences), which only applies to hit runs that
  already produced a pair; a hit run with no pair has nothing to re-derive.
- Standard: none
- Decision: undecided, needs the Owner. The review skill gives majors no
  named default and the brief is silent, so this stage does not defer it on
  its own. Recommendation: defer, because the behaviour is unchanged from
  main, is outside the brief's scope (#1061 names the review signal, the
  zero-item line and the size bound), and the fix is a design choice (fold a
  hit run only when it produced a pair, which changes the rule ADR-0116 just
  recorded and needs an ADR amendment). File a plain `type:chore` issue and
  do not close it from this PR. Alternative: fix in this run, route to
  Architect, then Implement and re-Verify.

### Minor: three lines in `decompose_lessons.py` exceed 79 columns, in a module that had none

- Scenario: lines 280 (`serialize`, 81 columns), 379 (the `pairs` docstring,
  91) and 503 (the `votes` docstring, 88), all introduced by commit be914a6.
  `git show origin/main:decompose_lessons.py | awk 'length>79' | wc -l` prints
  0. `decompose_signals.py` has 0 and `cli.py` 1. No linter or gate enforces
  it, so nothing breaks; the module's own convention decays. (A fourth line,
  tests/test_decompose_lessons.py:328, is older, from 5179e5c8, and not part
  of this diff.)
- Standard: none
- Decision: deferred, no gate or standard enforces a column limit and the
  fix is a three-line rewrap that can ride along in the PR if the Owner
  wants it. Not touched here because this stage records findings.

### Minor: the `_ballot` docstring restates its guard and leaves two conditions out

- Scenario: decompose_lessons.py:486-489 says the vote is refused when "the
  voter is seen for the lesson's signal, already voted, or a source". That
  is three of the five conditions in the `if` that follows; the other two (no
  measurable figure for the signal, wrong run kind) are not named, so the
  docstring both repeats the code and under-describes it. A reader who trusts
  it will think a measured clean voter of the right kind is the only
  remaining case. No behaviour is wrong.
- Standard: none
- Decision: deferred, documentation only. Better text: say what the function
  returns (the vote cast, "up" or "down", or None), and let the guard speak.

## Passes with no findings

- **Correctness** (one Major above, nothing introduced by the diff). Checked
  against the code: `_measured` is a superset of the three old fold rules
  (complete runs, hit runs, voters) only where the signal is measured, which
  is the documented accepted change 1 to 5; `_ballot` and `votes`'s prefilter
  agree (a run seen for every signal of its kind's lessons costs no git
  call); a duplicate header entry loads and serializes de-duplicated; an old
  per-run entry never fullmatches `SEEN_ENTRY` and a new one never fullmatches
  `REF`, so the two refusals are disjoint; `_oversize` checks `size >
  MAX_LESSONS_BYTES` with a missing path or stat error left to `read_file`,
  and both sides of the edge are pinned by
  `test_a_file_above_the_bound_is_refused_unread` and
  `test_a_file_at_the_bound_loads`. Verify's one-test observation about the
  `>=` mutation is therefore a pin on the single comparison, not a gap.
  `_verdict` covers treated-empty, untreated-empty and both-empty, and a pool
  with items keeps the old text. Suspicion, not a finding: `update` writes
  without checking the bound, so a header of about 130 bytes per run
  (5,336 bytes over 41 runs) reaches 1 MiB near 8,000 runs and the next
  `load` would refuse the file `update` just wrote. Settled by measuring a
  real ledger at that scale; not reachable at present volume.
- **Design.** The diff matches architecture.md's contracts: one `seen_key`
  owner, strings and constant as specified (Verify matched them), `fold`
  collapsed to the one measured rule, no new import (dual-membership pin
  stays 55), no skill edit so no wave release PR is owed. The three design
  decisions that pass the ADR test are in ADR-0116; the size constant, the
  zero-item wording and seen-equals-measured fail the hard-to-reverse leg and
  carry their one-line records in architecture.md. ADR-0113's status line
  was changed, not its Decision section, which is the supersession pattern
  the brief asked for. The ~3.7x larger header (1,430 to 5,336 bytes over 41
  runs) is architecture.md's accepted change 8 and ADR-0116's Consequences,
  and stays a few KB, so it is recorded, not a finding.
- **Security.** The file is the Owner's own repo file read through
  `cli.read_file`; the size guard adds a bound before the read; the 60
  character echo of a bad header entry shows the Owner's own file content
  back to them, no secret or path beyond the shown name; no subprocess, no
  network, no new write path.
- **Complexity.** No cut-list entry confirmed. `seen_key` has four callers
  (not speculative); `_oversize`, `_entry_problem`, `_header_problem` and
  `_verdict` each have one caller but are named seams for what the tests pin
  (cut-list `speculative` needs a second user it can name, and these are
  decomposition of a long function, not abstraction). The one `lean:`
  marker in the diff is a removal (the stale comment went with its guard);
  the diff adds none. Concern about the module's shape: none to hand to
  `deepen`.
- **ADR compliance.** `adr_status.py` standings: ADR-0113 partial (read
  ADR-0116, which carries the header decision; the lesson-line, derived-only,
  single-writer and root-only parts stand and are untouched), ADR-0116
  provisional (this run's own; no violation to rank), ADR-0095 active (no
  `plugin.json` or `skills/` change), ADR-0100 provisional (each stage's
  artifact is committed at its boundary), ADR-0075 provisional (reads go
  through `cli.read_file`; the added `Path.stat` mirrors
  `eval_trends._refusal`). Other live ADRs name subjects the diff never
  reaches. No violation.
- **Standards.** `stdlib-only` (factory, MUST): holds, the diff adds no
  import. `eval-honesty`: no eval definition or result touched.
- **Domain passes:** none selected.

## Verdict

Ready to ship the diff as scoped: the three defects in the brief are fixed
and proven (Verify: 26 of 26, 34 new or amended tests red on origin/main and
green on HEAD, nine mutations each caught), the suite, lint, drift and gates
are green, and no critical finding exists. One item blocks a clean hand-off:
the Major above needs the Owner's fix-or-defer answer (this review
recommends defer plus a plain issue) before Ship counts it resolved. The two
minors are deferred with reasons. Passes not run or unknown: none; the
payments, migrations and dependencies passes were not selected by the diff.
Nothing was run live (no model, no paid eval), which is by the brief.
