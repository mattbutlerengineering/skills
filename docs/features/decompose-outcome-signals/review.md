---
stage: review
run: feature:decompose-outcome-signals
date: 2026-10-18
assumptions:
  - "Autorun stage, no live user: severity is the reviewer's call and every major is either fixed here or deferred to the Owner with its reason, taking the skill's default (majors fixed or explicitly deferred). No critical finding was found, so the fix-before-Ship rule has nothing to hold."
  - "Fixes made in this stage were limited to one-line or one-expression changes, each test-first and committed on its own. Anything that changes a recorded Owner decision (decision 3) or the fixed reason vocabulary in architecture.md was deferred, not fixed."
  - "Diff scope is `git diff main...HEAD` at 95b130d (the Verify commit), plus the four Review fix commits listed under Scope."
  - "Re-run 2026-10-18 after the Architect re-entry on Owner decision 7: diff scope `git diff 38b2feb..HEAD` at c77d9eb (d1a870a, 47c1ee5, 76b59fe, 1d7279e, 4278f94, c77d9eb, and the brief commit 34a3962), plus a re-read of the whole module for regressions. The first pass's findings and decisions below stand except where marked as updated on this date."
  - "Re-run default (skill default, brief silent): a test gap on the new branch is fixed here as tests only, since it changes no code, no reason string and no recorded number; each fix is shown RED by re-applying the mutant it kills, because the behaviour already exists. Neither evals/results record was touched."
  - "The committed record evals/results/decompose-signals-2026-10-18.json was not touched (append-only). The three code fixes were checked against today's refs: the report body is byte-identical before and after them (only the digest moves, because the branch tip moved), so the record's numbers stay what the fixed tool prints."
---

# Review: Decompose outcome signals from git history

## Scope

`git diff main...HEAD` at 95b130d: `decompose_signals.py` (new, 586
lines), `tests/test_decompose_signals.py` (new, 72 tests),
`eval_schema.py` and its tests (a third snapshot kind), `factory.py` (one
`VERBS` row), `tests/test_dual_membership.py` (three new pairs),
CLAUDE.md, CONTEXT.md, `evals/README.md`, ADR-0109, ADR-0110, the status
lines of ADR-0091 and ADR-0106 and their index rows, the committed record,
and the run's artifacts.

Re-run, 2026-10-18, after the Architect re-entry (Owner decision 7):
`git diff 38b2feb..HEAD` at c77d9eb. That is `_implement`'s inferred
pass and `RULE` in `decompose_signals.py`, 14 changed or new test cases,
ADR-0111 (new), ADR-0109's status line and both index rows,
architecture.md's amended Boundary detector, assumptions and accepted
behaviour changes, breakdown S14-S16, verification.md, and the second
record `evals/results/decompose-signals-2026-10-18-2.json`. Examined by
a full re-read of `boundaries`/`_implement` and the callers that read
their result (`replan`, the design-gap window, the aggregate); the
pre-change tool (`git show 38b2feb:decompose_signals.py`) and HEAD run
side by side on this clone's refs; an 8-mutant sweep of the new branch
against its test module, in a `git archive` copy so the working tree was
never mutated, each mutant's `old` string asserted to occur exactly once
and its diff counted before the run; and `adr_status.py .` for the live
ADR list.

How it was examined: a full read of the module and the test file; the
tool run on this clone (1086 refs, 36 runs, 0 problems, 1.5 s); scratch
git repos for each suspected git-semantics bug; a 26-mutant sweep of the
module against its own test module, with every mutant's application
checked (each `old` string occurs exactly once) and the tree restored
(`git status --porcelain` empty afterwards); `python3 one_owner.py` on
this branch and on main; and `adr_status.py` for the live ADR list.

Review commits on this branch:

- 1a7717a `fix(decompose-signals): walk full history so a merge cannot hide a boundary`
- 5558dc3 `fix(decompose-signals): count a copied architect commit as one route`
- ad706a1 `test(decompose-signals): pin the split threshold and the hyphen guard`
- d3bf3ac `fix(decompose-signals): a hyphenated compound is not the stage word`
- 7d25ae8 `docs(adr-0110): list the knowledge_plane names the tool imports`
- 865ed41 `test(decompose-signals): pin the row guard, the window's open end and a mid-walk read failure` (re-run)

## Findings

### Major: git log's history simplification hides boundary commits behind a merge

- Scenario: a run branch commits `docs(x): decompose — …` and
  `docs(x): implement — …`, its trunk squash-merges it and later edits
  the breakdown again, and the branch then merges the trunk taking the
  trunk's breakdown (`-X theirs`, or a conflict resolved that way). The
  merge is TREESAME to its trunk parent only, so default `git log --
  <path>` follows that parent and drops both run commits. Reproduced in
  a scratch repo: the tool printed `decompose none, implement none;
  re-plan unmeasurable — the first version (5dcb5c2) already checks 1 of
  1 rows`, where both boundaries are observed. The run reads as
  unmeasurable (fail-closed, but wrong), and on other shapes an observed
  boundary can fall back to an inferred one.
- Standard: none
- Decision: fixed in 1a7717a. The walk passes `--full-history`; a
  real-repo test reproduces the merge and pins both observed boundaries
  (RED before the flag, GREEN after). On today's refs the report is
  byte-identical with and without the flag, so the committed record is
  unaffected.

### Major: ADR-0109's "the two implement windows agree today" is falsified by this run's own row

- Scenario: ADR-0109 (Consequences) and architecture.md's last
  assumption say the inferred implement boundary (first tick, the start
  of Implement) and the observed one (the implement commit, its end)
  agree, because the work-item keys match on the 3 runs that have both.
  This run is the fourth, and they do not agree. The committed record
  measured it with `implement inferred a8dbcb9; re-plan 0 of 13 …
  inferred; design gaps 0 inferred`. Today's refs give `implement
  observed 56baba9; re-plan 2 of 13 (added 2 …) observed; design gaps 1
  observed`. The S12a/S12b items and the S13 route back to Architect
  both happened after the first tick, which is where re-plans and design
  gaps happen. So the inferred population (26 of 30 measured re-plan
  runs) measures a window that is near-empty by construction: the
  inferred re-plan aggregate is 7/219, and 6 of those 7 come from one run
  (a-timestamp-the-digest-cannot-parse) whose seven-row plan was replaced
  by a one-row closure stub after supersession. The populations are
  split in the aggregate, so nothing is hidden, but the ADR's stated
  evidence is now wrong, and a calibration step reading the inferred
  figure as "plans rarely change" would be misled.
- Standard: none
- Decision: deferred to the Owner. The first-tick rule is Owner decision
  3, kept as written, so Review does not change it. Before #987 cites
  the record, the Owner should either confirm decision 3 with this
  evidence (and a superseding or amending ADR replacing the stale
  consequence), or choose a different inferred implement boundary (for
  example the last commit before Verify's artifact). ADR-0109 already
  says the Owner confirms it before the first record is cited.
- Resolved (re-run, 2026-10-18). The Owner chose the last tick live
  (brief decision 7). ADR-0111 supersedes ADR-0109 in part (its inferred
  implement boundary and the windows-agree consequence; ADR-0109's
  Decision text is left as written, and its status line and index row
  name the partial supersession). `_implement` now returns the earliest
  version after D with `total and done == total` (76b59fe). Evidence,
  each reproduced here:
  - ADR-0111's Decision, clause by clause: earliest after D, in walk
    order (the loop runs over `later` in walk order and returns on the
    first hit); at least one row (`total and`); unticks and later
    unchecked rows don't move it (first hit wins; two tests); a
    breakdown never fully checked gives the new fixed reason, for
    re-plan and, with D observed, design gaps (unit and `main([])`
    tests); the observed pass still runs first.
  - Its measured claim: on all 4 runs with an observed implement
    boundary (this run, fail-closed-roll-up, pr-body-preflight,
    the-reviewer-token-runs-agent-code) the first all-checked version
    after D is the observed implement commit (56baba9, 27467df, 766292c,
    755dc8c).
  - Its accepted behaviour changes: the 38b2feb tool against HEAD on
    today's refs gives 36 runs, 24 with a moved inferred I, 22 with the
    same figures, and the other 2 are first-live-dispatch (`re-plan 4 of
    8 (added 3, dropped 0, split 1, merged 0; renamed 0)`) and
    faster-sdlc (re-plan unmeasurable with the new reason). The
    aggregate reads `inferred 10/208 over 25 run(s)`, as stated.
  - Mutants of the new branch: reverting to the first tick (`if done:`)
    fails 5 tests, a last-all-checked walk (`reversed(later)`) fails 2, a
    majority threshold fails 5, the old reason string fails 3, and
    dropping the observed pass fails 4. Three survived; see the new
    minor below, fixed in 865ed41.
  - The second record's `rule` equals `RULE`; the first record is
    unchanged by this diff and its `rule` is the old sentence, so the
    two can be told apart, as ADR-0111 says.

### Minor: a cherry-picked or rebased copy of an architect commit counted as a second route

- Scenario: the walk covers every ref, so a rebase or cherry-pick of one
  `docs(x): architect — …` commit onto another ref puts the same route in
  the (D, I] window twice. Reproduced in a scratch repo: `design gaps 2
  observed` for one route. Today's refs hold one duplicated pair touching
  run artifacts (`docs(factory): add retroactive architecture.md …`,
  81aefe4/c954482), which is not an architect subject, so no recorded
  number is affected.
- Standard: none
- Decision: fixed in 5558dc3. Routes count distinct (author date,
  subject) pairs; a unit test inserts a copy into the window. This
  refines architecture.md's "the number of commits in the window" to
  distinct commits by that identity, recorded here rather than by
  editing architecture.md.

### Minor: a hyphenated compound read as the stage word

- Scenario: ADR-0109 requires the stage as a whole word, but `\b`
  matches between a word and a hyphen, so `docs(x): implement-queue
  profile` writing the run's breakdown was an observed implement
  boundary (reproduced with `_observed`, which returned True). The
  finding grammar already guards this with `(?!-)`; the subject pattern
  did not. No subject on today's refs has this shape (checked with `git
  log --all`).
- Standard: none
- Decision: fixed in d3bf3ac, test first; the report
  body is unchanged on today's refs.

### Minor: two mutants survived the test suite

- Scenario: a split threshold of one citation (`> 0` in place of `> 1`
  for a kept row) and the finding grammar without its `(?!-)` guard both
  passed all 72 tests. The other 24 mutants were killed, and two more
  survivors (`- {k}` removed from the citation set, and the window
  including D) are equivalent mutants: added and matched keys are
  disjoint, and a decompose commit cannot match the architect subject.
- Standard: none
- Decision: fixed in ad706a1. One case each; both mutants re-applied and
  each now fails the suite.

### Minor: an empty "Design gaps found" section is reported as a missing one

- Scenario: a breakdown at D with `## Design gaps found` followed
  directly by the next `##` heading gives `design gaps unmeasurable — no
  "Design gaps found" section at the decompose boundary` (reproduced),
  although the section exists. The run is still left out of the
  aggregate, so no number is wrong, only the reason. The section-end rule
  (stop at a level-2 heading) is also untested: a mutant that stops only
  at level 1 survives, and would differ only on this empty-section case.
- Standard: none
- Decision: deferred. The reason strings are a fixed vocabulary in
  architecture.md, so a new reason is a design change for Implement or
  the Owner, not a Review edit. Low impact: no number changes.

### Minor: tests/timings.json has no entry for the new module

- Scenario: run_tests.py schedules a module with no timing at 0 s, so
  the 11 s `tests.test_decompose_signals` runs last and can stretch the
  wall time (Verify's observation, confirmed: `grep -c decompose
  tests/timings.json` prints 0). Eight of 107 modules have no entry, so
  this is not new to this run.
- Standard: none
- Decision: deferred. `run_tests.py --record` rewrites every entry from
  one machine's run, which is unrelated churn for this branch; it belongs
  to the next timings refresh.

### Minor: the committed baseline measured this run mid-flight

- Scenario: as above, the record's own row for this run reads inferred
  at the first tick; once the implement commit exists it reads observed
  with different numbers. The record is honest for its refs (its digest
  makes that checkable) and is append-only.
- Standard: eval-honesty (advisory)
- Decision: deferred to Ship and #987. A comparison against this record
  should compare per-run rows and exclude this run's row, or a fresh
  dated record should be taken after merge. The existing record is not
  edited.
- Updated (re-run, 2026-10-18): partly addressed. The second record
  (`decompose-signals-2026-10-18-2.json`, S16) reads this run as
  `implement observed 56baba9`, `re-plan 2 of 13` observed. Both records
  stay; ADR-0111 says they are compared run by run, never as one
  series.

### Minor: ADR-0110's Context named an import the module does not make

- Scenario: the Context listed `parse_row` among the knowledge_plane
  imports; the module imports `ROW` instead and never `parse_row`.
- Standard: none
- Decision: fixed in 7d25ae8, Context only (the ADR is this run's, still
  provisional and unmerged; the Decision section is unchanged).

### Minor: three mutants of the ADR-0111 pass survived the suite (re-run)

- Scenario: each passed all 83 tests in `tests.test_decompose_signals`,
  in a `git archive` copy, with its single-occurrence `old` string
  asserted and a 2-line diff confirmed:
  - `if done == total:` (the at-least-one-row guard dropped). A version
    with no rows after D (a breakdown rewritten as prose, or rows moved
    out) would be read as every row checked, and the window would end
    there. ADR-0111 and architecture.md ("A version with no rows is
    never fully checked") both state the guard; no test held it. On
    today's refs the mutant's report is identical to HEAD's, so no
    recorded number depends on it.
  - `n >= d_at` in `boundaries`' `later` (the window includes D). An
    observed decompose commit whose breakdown already checks every row
    would be its own implement boundary, an empty window, where ADR-0111
    says the earliest commit *after* D. This is the "decompose and
    all-checked are the same commit" edge; no run on today's refs has it
    (checked over all 30 runs with a D). Under the first-tick rule the
    same mutant was not called out because the first pass's equivalent
    "window including D" was the design-gap window, a different line.
  - a failed read inside the inferred loop turned into `continue`. The
    new rule reads every version up to the all-checked one, more than
    the first tick did, and a failure on the way would silently pick a
    later version. The only read-failure end-to-end test fails D's read
    first, so this loop's `read failed` was never reached.
- Standard: none
- Decision: fixed in 865ed41, tests only. One case each. Each mutant
  was re-applied after the commit and now fails exactly its new case;
  HEAD passes all 86. No code, reason string or record changed.

## Passes with no findings

- Security: clean. git is reached only through `cli.runner`; every argv
  is a fixed list. Refnames fed to `log --stdin` come from
  `for-each-ref` and always start `refs/`, so none can be read as an
  option. `show` takes `<sha>:<path>`, which cannot start with `-`. The
  pathspecs are constants. `review.md` is read through the guarded
  `cli.read_file` (ADR-0075). Commit subjects and file contents are
  parsed, never printed or executed. No network verb appears in the
  module, and a test pins the verbs run.
- Complexity: one cut-list entry, not worth a change: `dead` —
  `decompose_signals.py` `replan`, the `- {k}` in the citation set
  cannot change a count (the equivalent mutant above). The one `lean:`
  marker the diff adds (the `--name-only` deletion note) names its
  ceiling, today's no-deletion state, and its trigger, a record
  reporting `read failed`. Nothing else to cut.
- ADR compliance: 110 ADRs listed by `adr_status.py` (78 active, 20
  provisional, 12 partial). Checked: ADR-0060 (root-only: no payload
  tool imports the module, no MIRRORS or manifest change), ADR-0061 and
  ADR-0021/0022/0024 (one owner: `one_owner.py` reports the same 9
  problems on this branch and on main, none naming the new module; the
  snapshot naming grammar stays in eval_schema), ADR-0075 (guarded
  read), ADR-0095 (no plugin.json change), ADR-0012/0019 (the record was
  committed once and never edited; it is not LEDGER-linkable, and a test
  pins that), ADR-0091/0106/0110 (the dual-membership pin carries the
  three new pairs, and both older ADRs' status lines record the partial
  supersession), ADR-0109 (the code implements its rule; see the major
  above for its stale consequence). The rest are out of scope: they
  govern skills, workflows, the dispatch plane or the factory payload,
  which the diff does not touch.
- Domain passes: none selected (no payment, migration or dependency
  path in the diff).
- Standards: `stdlib-only` (factory, advisory) holds; `eval-honesty`
  (eval, advisory) holds for the record and is cited above.
  `adr0032-one-way-mirror` does not apply (no work orders).

## Re-run passes (2026-10-18)

- Correctness: clean apart from the test gaps above. Walk order against
  date order: the walk is `--author-date-order --reverse`, which keeps
  parents before children, and ADR-0111 says walk order, so the code and
  the ADR agree. Merges: `--name-only` lists no files for a merge
  commit, so a merge never becomes an inferred I itself; the
  `--full-history` walk still shows the run's own commits behind a merge,
  and the existing merge test passes under the new rule. A read failure
  now aborts the inferred pass wherever it happens (pinned in 865ed41),
  which is the fail-closed reading. The design-gap window widens with I
  but on today's refs no design-gap figure moves (D inferred reads the
  section, not the window).
- Design: matches architecture.md's amended Boundary detector and the
  fixed reason vocabulary; the decision passes the "When to write an
  ADR" test and has one (ADR-0111), with ADR-0109 superseded in part
  rather than rewritten.
- Security: no new input or external call; `show` and `log` argv are
  unchanged.
- Complexity: the diff adds one condition and one string; no cut-list
  entry, no `lean:` marker.
- ADR compliance: `adr_status.py .` lists 111 ADRs; ADR-0109 reads
  `partial` and ADR-0111 `provisional`, matching the README index rows.
  Gates (detector D among them) report 0 problems. ADR-0012/0019: both
  records are byte-unchanged by this review.
- Output honesty: the rule sentence printed and recorded names the new
  rule and both ADRs; ADR-0111's consequence figures reproduce exactly.
  CLAUDE.md and CONTEXT.md still cite only ADR-0109 for the
  observed/inferred labels, which ADR-0111 leaves standing, so they are
  not stale.
- Domain passes: none selected.

## Verdict

Re-run, 2026-10-18: ready for Ship. No critical finding and no open
major: the deferred major is resolved by Owner decision 7 and ADR-0111,
with the evidence above. One new minor (three surviving mutants) is
fixed in 865ed41. The three earlier deferred minors stay deferred, one
of them partly addressed by the second record. ADR-0109 and ADR-0111
are provisional until the Owner confirms them, as both say. All five
passes ran; no domain pass was selected. The mutation sweep again
covered only the module's own test module.

First pass: ready for Ship, with one major deferred to the Owner. No critical
finding. Two majors: the history-simplification bug is fixed; the stale
ADR-0109 consequence and what it means for the inferred population are
deferred to the Owner, who already has to confirm ADR-0109 before the
record is cited. Of seven minors, four are fixed and three are deferred
with reasons. Nothing was skipped: all five passes ran, and no domain
pass was selected. The mutation sweep covered only the module's own test
module, not the whole suite; that is enough here, because the other
modules that name it (eval_schema, dual-membership and factory-CLI
tests) pin its name and wiring, not its logic.
