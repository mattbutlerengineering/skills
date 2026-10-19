---
stage: review
run: feature:decompose-outcome-signals
date: 2026-10-18
assumptions:
  - "Autorun stage, no live user: severity is the reviewer's call and every major is either fixed here or deferred to the Owner with its reason, taking the skill's default (majors fixed or explicitly deferred). No critical finding was found, so the fix-before-Ship rule has nothing to hold."
  - "Fixes made in this stage were limited to one-line or one-expression changes, each test-first and committed on its own. Anything that changes a recorded Owner decision (decision 3) or the fixed reason vocabulary in architecture.md was deferred, not fixed."
  - "Diff scope is `git diff main...HEAD` at 95b130d (the Verify commit), plus the four Review fix commits listed under Scope."
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

### Minor: ADR-0110's Context named an import the module does not make

- Scenario: the Context listed `parse_row` among the knowledge_plane
  imports; the module imports `ROW` instead and never `parse_row`.
- Standard: none
- Decision: fixed in 7d25ae8, Context only (the ADR is this run's, still
  provisional and unmerged; the Decision section is unchanged).

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

## Verdict

Ready for Ship, with one major deferred to the Owner. No critical
finding. Two majors: the history-simplification bug is fixed; the stale
ADR-0109 consequence and what it means for the inferred population are
deferred to the Owner, who already has to confirm ADR-0109 before the
record is cited. Of seven minors, four are fixed and three are deferred
with reasons. Nothing was skipped: all five passes ran, and no domain
pass was selected. The mutation sweep covered only the module's own test
module, not the whole suite; that is enough here, because the other
modules that name it (eval_schema, dual-membership and factory-CLI
tests) pin its name and wiring, not its logic.
