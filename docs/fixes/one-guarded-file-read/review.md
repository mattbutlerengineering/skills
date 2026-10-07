---
stage: review
run: maintenance:one-guarded-file-read
date: 2026-10-04
assumptions:
  - "No live operator input: this run is driven from autorun-brief.md, so every severity call and every fix/defer decision below is the reviewer's, taken against CLAUDE.md, ADR-0075, architecture.md and the precedent reviews (deepening-tool-seams, a-utf8-fix-that-stopped-at-the-mirror). A severity the operator disagrees with is a line to correct, not a design change."
  - "The reviewer is a fresh agent that wrote none of this run's code, but it is the same model family as the authoring agents; ADR-0036 clause 2's non-authoring human reviewer still applies at the merge."
  - "Review depth is scaled to a refactor of a mirrored seam module: cli.py and the seven mirrored root tools got a full-depth pass (probed in scratch trees, every adopter re-read, a 204-cell replay at both revisions), the run documents a lighter one. Verify's regression evidence is the floor and is not re-run except where a finding leaned on it."
  - "All probing ran in git-archive copies under the session scratchpad (ogfr/review/), never in the worktree. Nothing was pushed, no tracker was written, and trigger_eval.py and charter_replay.py were not run as scripts."
  - "Only three docs/standards.json statements match this diff's domains (factory, pipeline): adr0004-typed-ids-in-frontmatter, adr0032-one-way-mirror and stdlib-only, all advisory. No finding below cites one; the diff satisfies stdlib-only."
  - "Re-review 2026-10-04, option (a): the fix loop reviewed in the last section (864f1aa..95830fa) exists because this file's recommended option (a) for the open major was taken as the default after the operator re-invoked autorun without naming an option (autorun-brief.md, 'Resume, 2026-10-04'). That is the orchestrating session's reading, not the operator's words. The major is therefore closed IN CODE, while the choice of (a) itself still awaits the operator's confirmation."
  - "Re-review, decided without operator input: the disposition of each first-pass finding (the major and Minors 1, 2, 4, 5 and 6 closed, Minor 3 still deferred) is the reviewer's, on the rule that a finding is closed only when its first-pass scenario no longer reproduces. Each scenario was re-run in scratch on Python 3.14.6 and 3.12.13."
  - "Re-review, decided without operator input: new finding N1 (a ledger line that json.loads refuses with anything but JSONDecodeError still makes the monthly cap check and budget_guard.record raise) is ranked minor, not major, and deferred. The ranking rests on three measured facts: it is identical at 661ffc7, no factory writer can produce such a line, and detector G raises on any change that introduces one. The fence that leaves it out is the Architect's amendment on top of the orchestrating session's scope, not the operator's words, so whether to take the one-line fix before the merge is put to the operator."
  - "Re-review, decided without operator input: new finding N2 (ADR-0075's fence sentence and its Consequences line do not carry the limit N1 describes) is ranked minor, with the decision fix (non-blocking): one sentence in the record, no code."
  - "Re-review, decided without operator input: new finding N3 (two new TestReadFile tests pass only under the interpreter's default digit limit, and on Python 3.14 only with a stack smaller than about 140 MB) is ranked minor and deferred as a seed for the retro, because no configuration in use fails."
  - "Re-review, decided without operator input: correcting ADR-0075 in place is judged to be within CLAUDE.md's supersede-do-not-rewrite rule, because the record is provisional, was written by this run, and has never been on origin/main. If the operator does not confirm option (a), it is corrected again before any merge."
  - "Re-review, depth and method: the fix loop's code, tests, payload and ADR diff got a full pass and the four run documents a lighter one. All probing ran in git-archive copies under the session scratchpad (ogfr/review-d/), never in the worktree, on Python 3.14.6 and 3.12.13. Verify's re-verification is the floor; what was leaned on without a re-run is named in the section. The same three advisory docs/standards.json statements match the diff's domains and no new finding cites one. Nothing was pushed, no tracker was written, and trigger_eval.py and charter_replay.py were not run as scripts."
  - "Second re-review 2026-10-04, taking the fix: the fix loop reviewed in the last section (261e486..6d0bef8) exists because the operator re-invoked autorun with no arguments and no other words after the report asked 'Should I fix the cap-check gap before you push?' and recommended yes (autorun-brief.md, 'Second resume, 2026-10-04 (UTC): the ledger parse guard'). The operator did not say yes. Taking the fix is the orchestrating session's reading, not the operator's words. So N1 is closed IN CODE, while the choice to take the fix, like the choice of option (a) from the first resume, still awaits the operator's confirmation."
  - "Second re-review, decided without operator input: the disposition of the previous re-review's findings (N1 closed in code, N2 closed, N3 still deferred and now covering five tests) is the reviewer's, on the rule that a finding is closed only when its scenario no longer reproduces. N1's scenario was re-run in scratch on Python 3.14.6 and 3.12.13, in-process through cost_report.main(['report']) with a GITHUB_OUTPUT file and as a process. The workflow's pause condition was read, and its text is pinned by an existing test, but the workflow was not run: the branch is not pushed."
  - "Second re-review, decided without operator input: new finding N4 (on a ledger it can only partly read, work_queue.py plan still prints a batch priced on the rows it could read, and this run has moved three ledgers onto that path from a traceback) is ranked minor, not major, and deferred. The ranking rests on these facts: the path is the one a plainly malformed line already took at 661ffc7, the command still exits 1 and prints the problem, the exposure is one batch, and no factory writer can produce either refused line (the previous re-review's measurement, not re-run). The fix is in a tool this run never edited and changes what a plainly malformed line does too, so whether to take it before the merge is put to the operator. A candidate was tried in a scratch copy only."
  - "Second re-review, decided without operator input: that the suite stays green with the arm widened to 'except Exception' (Verify 2F, re-run here, and found to hold for read_file's arm as well) is judged not a finding. No document can tell the two arms apart, a pin would have to patch json.loads, and the wider arm errs toward a pause."
  - "Second re-review, decided without operator input: four ledgers whose every line parses were found to defeat the cap check or the planner (three make the monthly cap check raise before it writes pause=, and a NaN cost, which the record command will write, makes the planner's cap comparison always false). They read the same at 661ffc7, are missing range checks and not reads or parses, and are outside this run's subject and this loop's diff. They are recorded as reproduced observations and a seed for a run of their own, not ranked as findings against this run. Whether that is the right call is the operator's to overrule."
  - "Second re-review, decided without operator input: the verdict 'ready to ship (prepare-and-stop)' is this stage's, on the rule that no finding is critical, none is major and none cites an enforced standards statement. Ready means Ship can refresh release.md. It does not mean option (a), this fix or N4's deferral is confirmed."
  - "Second re-review, on the orchestrating session's instruction: release.md is known stale (prepared at 261e486; Ship refreshes it next). The list of its statements that this loop made untrue is given for Ship and is not counted as a finding."
  - "Second re-review, depth and method: the code, the three tests, the payload and the ADR paragraph got a full pass and the run documents a lighter one. All probing ran in git-archive copies under the session scratchpad (ogfr/review-e/), never in the worktree, on Python 3.14.6 and 3.12.13 with PYTHONINTMAXSTRDIGITS unset. One probe served dashboard's own handler on 127.0.0.1 in scratch, loopback only. One read of the remote was made (git ls-remote origin refs/heads/main). Verify's second re-verification is the floor; what was leaned on without a re-run is named in the section. docs/standards.json holds four statements, all advisory; three match the diff's domains and no finding cites one. Nothing was pushed, no tracker was written, and trigger_eval.py and charter_replay.py were not run as scripts."
  - "Second re-review: every work-order id in the quoted block and in the tables reads <work-order id>. The replacement is made by the command that produced the text (sed -E with a script file), never by hand, because detector C reads this file. The tables are printed by a scratch script from the probes' recordings."
---

# Review: one owner for the guarded local-file read

## Scope

`git diff 661ffc7..HEAD` on `refactor/one-guarded-file-read`, HEAD
`1d93e71`: 23 commits, 41 files, +3,213 / -291. Not the whole repo.

By subject:

- **The seam.** `cli.read_file` (new), its docstring, the `cli.py` module
  docstring sentence, and `TestReadFile` (16 tests).
- **Eleven adopters.** `factory_config.load`, detectors E and F,
  `standards_index.foreign_entries`, `cost_ledger.load`,
  `lint.check_manifest`, `lint.check_plugin_skills`,
  `lint.check_pi_package`, `eval_schema.load_case_set`,
  `dashboard._corrections`, `dashboard._backlog`.
- **Nine hand-fixes.** `label_sync.load_labels`, detector K,
  `lint.check_output_evals`' `problems_for`, `lint.check_backlog`,
  `cli.read_execution`, `sweeps.load_payload`, `dashboard.respond`,
  `dashboard.respond_post`, `validator.run_review`.
- **Two deletions.** `factory_config.object_problems`,
  `lint.object_problems`, and `TestObjectProblems`' two tests.
- **The payload.** Seven mirrored root files, their copies under
  `factory/templates/tools/factory/`, `factory/manifest.json`.
- **The documents.** `CLAUDE.md`'s seam line, ADR-0075 and its index
  row, and the five run documents.

### What was re-derived rather than read

- **Every adopter's `(value, problem)` handling.** Each one tests
  `problem` first, then `value is None` for absence, so none can fall
  through holding `None`. Re-read at HEAD for all eleven.
- **`read_file` against inputs outside every recorded matrix.** Probed
  in a scratch tree on Python 3.14 and 3.12. A symlink to a file is
  followed and read. A dangling symlink, a FIFO, `/dev/null`, a
  directory and a path with a NUL byte are all `(None, None)`, which is
  what every adopter's own `is_file` check gave before. A UTF-8 BOM is
  `is not valid JSON: Unexpected UTF-8 BOM` for the JSON kinds, and kept
  as text for `str`, both as before. A `Path` and a `str` path read the
  same. A `Path` `shown` formats as its text. A too-long file name is
  absent on 3.14 and `cannot read` on 3.12 (the same version split the
  architecture already records for an unsearchable parent). A 5,000-digit
  integer, a deeply nested array and a `kind` outside the four do not
  behave as documented: see Minor 1 and Minor 2.
- **Cells outside the 8-condition matrix, at both revisions.**
  `proto/extra_cells.py`, extended by six conditions (a BOM, a
  5,000-digit integer, 100,000 unclosed brackets, `false`, a JSON
  string, a dangling symlink), run against a `git archive` of `661ffc7` and of
  HEAD for all 17 readers: **204 cells**. Eight cells differ, all from
  a traceback to a problem string. Six are detector E (`null`, number,
  `true`, `false`, a string, `[]`, each now `E: factory/manifest.json is
  not a JSON object`). Two are `check_output_evals` (a directory and a
  dangling symlink, each now `cannot read evals/output/idea.json:
  [Errno ...]`). **No cell went from a string to a traceback, and no
  string changed wording.** The 15 cells still raising at HEAD (the
  5,000-digit integer, for every JSON reader) raise identically at
  `661ffc7`.
- **Dual-home readers.** `factory_config.load` still takes the first
  home that is there and reports a present but broken installed copy,
  never falling through to the payload. Detector F still checks every
  home in payload-first order. Both were read against `artifact_paths`.
  Under an unsearchable `.github/` on Python 3.12, `load` and F went
  from `PermissionError` to a `cannot read` problem. On 3.14 both read
  it as absent, as they did before.
- **`cost_ledger.load`'s return shape.** Unchanged: `(None, [])` absent,
  `(None, ["<label>: cannot read docs/factory/costs.jsonl: ..."])`
  unreadable or not UTF-8, `(rows, [])` otherwise. `shown` stays
  `COST_LEDGER` under a `ledger_path` override, as before.
- **Payload.** `cmp` of each of the seven mirrored root files against
  its payload copy: identical (all seven `MIRRORS` entries are
  `identity`). Every payload tool imports cleanly from inside
  `factory/templates/tools/factory/`. Each of the 16 touched or
  importing root modules imports cleanly: `cli` imports no sibling, so
  the three new edges into it cannot close a cycle.
- **Consumers of the two re-worded strings.** Grepped `*.py`, `*.md`,
  `*.yml`, `*.json` and the `Makefile` outside `tests/` and
  `docs/fixes/`. No tool, workflow, skill body or standing doc matches
  on `config: cannot read` or `L: cannot read`, or branches on either
  phrase. The only hits are dated run artifacts of earlier runs, which
  are records and stay as written.
- **Verify's two open gaps.**
  - Detector K's decode clause: removed in a scratch copy, and
    `TestStandardsDrift.test_a_committed_index_that_is_not_utf8_is_a_problem`
    errors with `UnicodeDecodeError`, so the test bites.
  - The battery at every commit: replayed for all 23 commits in
    `661ffc7..HEAD`, each a `git archive` with a fresh git index. See
    *Per-commit battery* below.
- **`python3 one_owner.py`.** Six findings at HEAD, the same six as a
  `661ffc7` archive. The only differences are line numbers in the two
  touched files (`eval_schema.py:241 validate`, `label_sync.py:96
  plan`, `:142 sync`). This diff introduced no finding.

### Per-commit battery

Verify left this open. Each of the 23 commits in `661ffc7..HEAD` was
exported with `git archive` into scratch, given a fresh git index, and
run through all four battery commands (Python 3.14). Every commit is
green: `unittest` OK, `lint: 0 problem(s) across 25 skills`, `gates: 0
problem(s)`, `selftest: ok`. The test count only rises, except at A6:

| commits | tests |
|---|---|
| the four run documents | 1793 |
| A1 | 1809 |
| A2 | 1833 |
| A3, A4, A5 | 1838, 1840, 1844 |
| A6, A7 | 1842 (A6 deletes `TestObjectProblems`' two tests) |
| A8, A9 | 1845, 1846 |
| B1 to B7 | 1862, 1863, 1866, 1870, 1871, 1872, 1874 |
| C1, C2, the verification commit | 1874 |

The breakdown's "green at every commit" rule holds. Gates ran without a
PR event payload, so detector B skipped, as it does locally.

## Findings

**Zero critical. One major, six minor.** Nothing cites an `enforced`
standards statement. Nothing blocks Ship, except that the major is open
for the owner.

### Major: the `object` kind has no caller, and its docstring sends the next reader into the trap this run measured

- Scenario: this is a decayed contract, between the interface's own
  documentation and the run's evidence.
  - The brief's interface, which the operator approved, justified the
    fourth kind by two named callers: "A reader whose shape message is
    its own (`label_sync`, detector K) asks for `object` and keeps its
    check."
  - The Architect's replay then showed that `object` rewrites the `null`
    cell of every reader with its own shape wording that was tried.
    That is four out of four: `label_sync.load_labels`, detector K,
    `problems_for` and `cli.read_execution` (architecture.md,
    *Counterfactual*). All four became hand-fixes. No adopter in this
    run asks for `object`.
  - `cli.read_file`'s shipped docstring still ends with the sentence the
    evidence refuted: "A reader whose shape wording is its own asks for
    object and keeps its own check." ADR-0075 decision 1 still lists
    `object` as a kind, as if it were in use.
  - Concrete recurrence: an agent adds a reader whose wording for a
    `null` document is its own. It follows the docstring, and its
    `null` cell reads `<shown> is null` instead of the reader's own
    wording. Nothing pins that cell for a new reader, so no test
    objects.
  - Reproduced: `read_file(<a file holding null>, "x", object)` returns
    `(None, "x is null")`, pinned in `TestReadFile.test_a_json_null`.
    The architecture's counterfactual shows the rewording reader by
    reader.
- Judged on the deepening's own terms: three of the four kinds earn
  their place (`str` has 3 callers, `dict` has 7, `list` has 1). The
  fourth is one branch, a quarter of every `TestReadFile` row, and a
  docstring paragraph, with no caller. CLAUDE.md's bar for shared code
  says "anticipated reuse doesn't qualify". The architecture defends
  keeping it as "the decided shape and the honest one for a future
  caller". That future caller is the anticipated reuse the bar excludes,
  and the decision it cites was made before the evidence that removed
  its callers.
- Standard: none.
- Decision: **open — needs owner decision.** The operator approved a
  design whose fourth kind had two callers, and it now has none. That is
  the operator's call, not a mechanical fix. Options:
  - **(a) Drop `object`. Recommended.**
    - Delete the `if value is None: return None, f"{shown} is null"`
      branch and the `object` line of the docstring table.
    - Rewrite the docstring's last sentence to: a reader whose shape or
      `null` wording is its own does not adopt; it gets its missing arm
      by hand.
    - Remove `object` from `TestReadFile.KINDS` and from every
      `assert_pairs` row.
    - Make ADR-0075 decision 1 name three kinds. The record is
      provisional and unmerged, so it is corrected in this run rather
      than superseded.
    - Run `update-manifest` (`cli.py` is mirrored).
    - What it costs: no recorded cell moves, because no caller uses the
      kind.
  - **(b) Keep `object` and make the docstring true.** Replace the last
    sentence with: `object` suits only a reader with no `null` wording
    of its own; every reader that had one stayed hand-written
    (ADR-0075 decision 5). ADR-0075 decision 1 would also note that the
    kind has no caller yet. Same manifest step.
  - **(c) Leave it.** Not recommended: the docstring is the first thing
    the next reader of this seam reads, and it says the opposite of
    what this run measured.

### Minor 1: "never raises for a local-file failure" is false for two JSON documents

- Scenario: the next two items show the failure.
  - A JSON file whose text is an integer literal over 4,300 digits makes
    `json.loads` raise `ValueError` ("Exceeds the limit (4300 digits)
    for integer string conversion"). That error is not a
    `JSONDecodeError`, so it escapes `read_file`.
  - Balanced nesting 200,000 arrays deep raises `RecursionError` the
    same way.
  - Reproduced on 3.14 and 3.12 against `read_file` directly. The
    integer case also reproduces through all 15 JSON readers in the
    204-cell replay.
- **The hazard is not this run's.** Every one of those cells raises
  identically at `661ffc7`, because each old guard also caught only
  `JSONDecodeError`. What this run introduced is the *claim*: the
  `read_file` docstring and ADR-0075 decision 1 both say the function
  never raises for a local-file failure. The precedent
  (deepening-tool-seams' "none raise" finding) treats a new false claim
  about relocated behaviour this way.
- Standard: none.
- Decision: **deferred.** No file the factory writes or reads can hold
  such a document. The fix is now one line in one place, which is the
  leverage this run bought: `except (ValueError, RecursionError)` in
  place of `except json.JSONDecodeError`, worded `is not valid JSON`,
  plus one `TestReadFile` row. If the owner takes the major's option
  (a) or (b), fold it into that same commit, since it touches the same
  mirrored file and the same manifest step. Otherwise it is a
  `docs/backlog.md` seed.

### Minor 2: `kind` is not validated, so a mistyped kind silently skips the shape check

- Scenario: `read_file(path, shown, "dict")` (a string, not the type)
  returns any JSON document as a value. `kind=int` and `kind=tuple` do
  the same: a file holding `{"a": 1}` comes back as `({'a': 1}, None)`.
  Reproduced. The brief gave the reason `kind` is required as "so the
  shape check cannot be skipped". A typo skips it with no error, and a
  test would not catch it on well-formed fixture data.
  `factory_config.artifact_paths`' docstring states the codebase's own
  pattern for literal-only arguments: "a typo is a KeyError at test
  time, not a runtime state". `read_file` does not follow it.
- No current caller is affected: all eleven pass `str`, `dict` or
  `list` as literals.
- Standard: none.
- Decision: **deferred** into the same follow-up as the major. The fix
  is to add `if kind not in (str, dict, list, object): raise
  ValueError(f"read_file: unknown kind {kind!r}")` at the top, or the
  three-kind tuple under option (a), with one test. It is a programmer
  error raised at test time, not a file failure, so it does not break
  the never-raises promise.

### Minor 3: hand-fixed `label_sync.load_labels` (and so detector J) still raises on Python 3.12 under an unsearchable `.github/`

- Scenario: on Python 3.12 (CI's version), with `.github/` at mode 000:
  - `factory_config.load` now returns `config: cannot read
    .github/factory.json: [Errno 13] ...`.
  - Detector F now reports it.
  - `label_sync.load_labels` raises `PermissionError` from
    `taxonomy_path`'s bare `is_file`, so detector J, which calls it,
    raises too.
  - Reproduced at HEAD on 3.12. At `661ffc7` all three raised, so this
    is not a regression.
- Why it is worth recording: the architecture moved `read_file`'s
  existence check inside its guard for exactly this reason (Trade-off
  2). The `label_sync` hand-fix added its decode arm but left the
  existence check outside any guard. The cell is outside the 8-condition
  matrix and the brief's scope.
- Standard: none.
- Decision: **deferred.** The condition is contrived (an unsearchable
  `.github/` in a checkout). The fix touches `taxonomy_path`, which has
  other callers, so it is a `docs/backlog.md` seed rather than a change
  folded into a no-wording-change run.

### Minor 4: ADR-0075's non-UTF-8 wording rule has two unnamed exceptions in and beside the seam

- Scenario: the decayed contract is ADR-0075 decision 2, which states
  "the wording rule" for bytes that are not UTF-8: `is not valid JSON`
  for any JSON reader.
  - `cli.read_event`, 30 lines above `read_file` in the same module,
    words the same failure `cannot read {name} {path}: {err}`.
  - `dashboard.repo_set`, a JSON reader, does the same.
  - `tests/test_dashboard.py`'s `test_bytes_that_are_not_utf8_are_a_problem_string`
    argues in its docstring for the opposite rule. A non-UTF-8 config
    "is unreadable, so it belongs in the `cannot read` arm".
  - The earlier review's item 2
    (`a-utf8-fix-that-stopped-at-the-mirror`) called `repo_set`'s shape
    "the most precise of the three".
  - Both readers are correctly left alone under decision 4 (no raising
    cell). But the rule is written as the codebase's, and a reader
    copying its nearest neighbour in `cli.py` gets the other wording.
- Standard: none.
- Decision: **deferred.** Re-wording either reader is a pin change the
  brief forbids. If ADR-0075 is edited for the major, add one sentence
  to decision 2: `read_event` and `repo_set` keep `cannot read` under
  decision 4. That makes the rule honest at no cost.

### Minor 5: only one of the nine hand-written readers says in code why it does not use `read_file`

- Scenario: ADR-0075's last consequence says "a reader that cannot use
  it says why". `label_sync.load_labels` carries that comment. The other
  eight carry a bare extra `except` arm, and `cli.read_execution` sits
  directly below `read_file` in the same module. A maintainer could read
  that as an oversight and "finish" the adoption. That would reword its
  absent and `null` cells.
- Why this is minor and not major: the reason is recorded, by name, for
  all nine in ADR-0075 decision 5. Every distinguishing cell is pinned
  by a test whose docstring gives the reason: K's and `label_sync`'s
  `null`, `problems_for`'s `null`, `read_execution`'s `null` and absent
  cells, `load_payload`'s absent cell, the three OSError-worded absent
  cells, and `check_backlog`'s `is unreadable`. So the mistaken adoption
  fails loudly at test time. The implementer logged this in
  breakdown.md's Notes.
- Standard: none.
- Decision: **deferred.** The reason lives in the record and the tests.
  Adding eight comments touches three mirrored files and the manifest
  for no behavioural change. Fold it into the major's follow-up if the
  owner wants it.

### Minor 6: one test builds the work-order id with a format expression where its file uses literals

- Scenario: `tests/test_budget_guard.py`'s
  `test_a_ledger_that_is_not_utf8_fails_closed` builds its id as a
  `%04d` format of 7. The file's 25 other uses of the same id are string
  literals. The implementer wrote it to obey an orchestrator instruction
  ("no work-order tokens in anything you write") that was aimed at run
  documents, and detector C does not scan `tests/`. Behaviour is
  identical. The cost is that a grep for the literal id across the suite
  misses this test, and an idiom with no stated reason invites copying.
- Standard: none.
- Decision: **fix (non-blocking).** Replace the expression with the
  literal string its neighbours use. It is one test-only line with no
  manifest step, and can ride with any follow-up commit or be dropped if
  none is made.

## Looked at and found sound

- **`AGENTS.md`'s older seam bullet.** It was not touched by this diff
  (its last change predates the run), and it had already drifted
  (it names neither `human_gates.py` nor `plane_drift.py`), and nothing
  checks it against `CLAUDE.md`. Not this run's finding. Recorded as an
  existing drift for a doc-gardener pass.
- **Silent passes.** `check_plugin_skills` now returns `[]` for an
  unreadable or non-UTF-8 manifest. That is correct only because
  `check_manifest`, earlier in the same `CHECKERS` tuple, reports the
  file. Confirmed it does, for both cells. A8's not-UTF-8 test pins
  `len(check_manifest(root)) == 1` beside the `[]`. No other checker
  went from a crash to `[]`.
- **A second statement of the object rule.** `eval_schema.object_problems`
  still words "is not a JSON object" beside `read_file`'s `dict` kind.
  ADR-0075 keeps it deliberately: its validators receive data parsed
  outside `load_case_set`, for example `check_output_evals`. `one_owner.py`
  does not flag it.

## Passes with no findings

- **Security.** Clean. No input crosses a trust boundary it did not
  cross before. No secret is read or written. Problem strings carry
  `OSError` text (with its absolute path) exactly where they already
  did. The new `UnicodeDecodeError` texts carry no path.
  `dashboard.respond` and `respond_post` return the same 500 envelope
  as before. No checker turns a failure into an unreported pass: see
  *Silent passes* above.
- **Correctness**, beyond Minors 1 to 3. The adopters' order of checks,
  the dual-home readers, `cost_ledger.load`'s shape, the payload, import
  edges and the consumers of the two re-worded strings all came back
  clean. That includes the 204-cell before-and-after replay with no
  string re-worded.

## Verdict

*Re-reviewed 2026-10-04 after the fix loop: see "Re-review (2026-10-04,
the fix loop)" at the end of this file. Its verdict is ready to ship
(prepare-and-stop): the major is closed in code, and the choice of
option (a) still awaits the operator's confirmation.*

**Ready to ship once the owner decides the major.** Nothing is
critical, and no finding cites an enforced standard. The change does
what the brief asked:
- 16 of 19 raising cells and all six outside sites return problem
  strings;
- exactly two wordings change;
- a further 8 out-of-matrix cells were fixed with none re-worded;
- the monthly cap check fails closed.

The one open item is the uncalled `object` kind and the docstring
sentence that recommends it. Whichever option the owner picks, Minors 1,
2, 4 and 5 can fold into the same single mirrored commit at no extra
manifest cost. Minor 3 is a backlog seed. Minor 6 is optional.

## Re-review (2026-10-04, the fix loop)

A second pass over this run, by a fresh reviewer that wrote none of
its code. It covers the fix loop that followed the verdict above. The
body above is the first pass, at `1d93e71`, and stays as that record.
"Major" and "Minor 1" to "Minor 6" below are the first pass's
findings. New findings are numbered N1 to N3.

**Why the fix loop exists, and what that limits.** The first pass left
the major open with three options and recommended (a). The operator
then re-invoked autorun without naming an option, and the
orchestrating session took (a) as the default (`autorun-brief.md`,
"Resume, 2026-10-04"). That is the orchestrating session's reading,
not the operator's words. So this section can say the major is closed
in code. It cannot say that (a) is what the operator chose.

**Result: zero critical, zero major, three minor.** Six of the seven
first-pass findings are closed and one stays deferred. Nothing cites
an `enforced` standards statement, and nothing routes back to
Implement.

### Scope

`git diff 864f1aa..HEAD` on `refactor/one-guarded-file-read`, HEAD
`95830fa`: 9 commits, 18 files, +2,210 / -57.

- Three document commits: `c1b3cd5` (the brief's resume), `4fe2983`
  (the Architect's amendment, with ADR-0075 corrected in place),
  `ad4c812` (Milestone D).
- Four change commits: `e6abfc1` (D1), `b121f2c` (D2), `cb5a75b` (D3),
  `5ecde58` (D4).
- Two record commits: `b94462b` (D5) and `95830fa` (the
  re-verification).

By subject:

- **The seam.** `cli.read_file` (three kinds, the kind check, the wider
  parse guard, the docstring) and its payload twin.
- **Tests.** `tests/test_cli.py` (+70 / -20), one docstring in
  `tests/test_lint.py`, one line in `tests/test_budget_guard.py`.
- **Eight comments** in six files, three of them mirrored.
- **The payload.** Three payload twins and three checksums in
  `factory/manifest.json`.
- **ADR-0075** (+39 / -12).
- **Four run documents:** the brief, `architecture.md`,
  `breakdown.md`, `verification.md`.

Standards: the same three advisory `docs/standards.json` statements
match this diff's domains as in the first pass. No new finding cites
one, none is `enforced`, and the diff adds no import, so `stdlib-only`
holds.

### What was re-derived rather than read

Everything in this list was run for this pass, on Python 3.14.6
(`python3`) and Python 3.12.13 (`python3.12`), as uid 501, with
`PYTHONINTMAXSTRDIGITS` unset, in `git archive` copies under the
session scratchpad (`ogfr/review-d/`). `base` is `661ffc7`, `pre` is
`864f1aa`, `head` is HEAD. Verify's re-verification is the floor.
Where one of its results is leaned on without a re-run, the text says
so.

- **Each first-pass scenario,** at `864f1aa` and at HEAD, on both
  Pythons. Results are under *Disposition* below.
- **The function against its design.** `read_file` extracted from
  `cli.py` and from its payload twin: no difference from
  `architecture.md`'s "Final text (2026-10-04)", 54 lines, the longest
  72 columns. `cmp` finds all seven mirrored root files identical to
  their twins. `factory_init.py update-manifest` on a HEAD export
  leaves `factory/manifest.json` byte-identical.
- **The battery at `95830fa`,** which Verify ran one commit earlier. On
  both Pythons: `Ran 1877 tests`, `OK`; `lint: 0 problem(s) across 25
  skills`; `gates: 0 problem(s)`; `selftest: ok`;
  `tests.test_factory_init` `OK`. Detector B skipped, as it does
  locally.
- **The kind check, `kind not in (str, dict, list)`.** Fifteen kinds
  that are not one of the three types. Refused with the `ValueError`:
  `collections.OrderedDict`, a `dict` subclass, `bool`, `bytes`,
  `None`, the instances `{}`, `[]` and `''`, `dict[str, int]`,
  `typing.Dict`, the tuple `(dict, list)` and an unhashable object. An
  object whose `__eq__` raises lets that exception out, at the call.
  Two get through, and neither is a slip a caller can make by
  accident: an object that compares equal to everything, and
  `unittest.mock.ANY`, which is one. Both skip the shape check, because
  tuple membership uses `==`.
- **The parse guard, `except (ValueError, RecursionError)`.** Nineteen
  odd documents under `dict` and `list`: a float and an exponent of
  5,000 digits, `1e99999` and its negative, `NaN`, `Infinity`, an
  integer of 4,300 digits (parses) and of 4,301 (reported), a negative
  5,000-digit integer inside an object, a lone surrogate escape, a NUL
  inside a string, a BOM, UTF-16 bytes, 100,000 unclosed brackets,
  200,000 nested objects, duplicate keys, a 5 MB string, whitespace, a
  trailing comma. Then a seeded fuzz: 4,000 random or mutated byte
  strings under each of the three kinds, 12,000 calls. Nothing escaped
  the guard. Every call returned exactly one `None`, and every value
  was an instance of its kind. The counts were the same on both
  Pythons: 2,532 values and 9,468 problems.
- **The read guard's order.** `UnicodeDecodeError` is a `ValueError`
  and not an `OSError`, and `OSError` is not a `ValueError`, so the two
  arms are disjoint and their order cannot matter. A path holding a NUL
  byte is `(None, None)` under every kind on both Pythons.
- **What is not caught.** `MemoryError` propagates from the read and
  from the parse. That was shown by patching each to raise it, not by
  exhausting memory. The amendment says so and decides it.
- **The interpreter after a caught `RecursionError`.** Every probe
  above kept running after the nested documents, and a later read
  returned its value, on both Pythons.
- **A caller deep in its own recursion.** 755 calls from 850 to 1,000
  plain Python frames down, with `str` and `Path` paths and all three
  kinds: a valid document was never reported as a problem. The calls
  nearest the limit raised `RecursionError` uncaught, from the path
  and the read, which sit outside the parse guard. So the guard does
  not swallow a caller's own overflow. The amendment's measurement
  through C frames was not repeated.
- **Every adopter on the two documents.** The Architect's 60-cell
  replay (`ogfr/amend/extra3.py`, 20 readers, three documents), run
  unedited on `661ffc7` and on HEAD. The HEAD recordings made here are
  byte-identical to Verify's. From `661ffc7` to HEAD 16 cells differ on
  3.14 and 24 on 3.12. All belong to the eight adopters with a JSON
  kind, and none raises at HEAD. Seven adopters return `<shown> is not
  valid JSON: <err>` under their own prefix.
- **The one adopter that returns nothing.** `lint.check_plugin_skills`
  returns `[]` for both documents. `lint.check_manifest` reports the
  same file for both, on both Pythons. `lint.py` run as a process on
  each ends `lint: 1 problem(s) across 25 skills` and exits 1. At
  `864f1aa` all three raised. No adopter turns either document into a
  pass.
- **Every call of `read_file`,** by an AST sweep over the tracked
  `.py` files outside `tests/`: 16 calls (11 root, 5 payload), each
  passing `str`, `dict` or `list` as a bare name with three positional
  arguments, and none inside a `try`. So no caller can swallow the new
  `ValueError`.
- **The eight comments.** Each is verbatim the amendment's text and
  sits directly above its reader's `try:`. The cell each one names was
  run through the reader. See Minor 5 below.
- **The test diff.** `git diff 864f1aa..HEAD -- tests/` read in full
  and classified by script. See *Tests* below.
- **The new tests off the interpreter's defaults,** and **the ledger
  limit with a candidate fix.** See N3 and N1.

Leaned on and not re-run: the 144-cell matrix and the six outside
sites (Verify A3), the mutations that show the new tests bite (Verify
C), the per-commit battery (Verify H2), and the amendment's Proof 6
and Proof 7.

### Disposition of the first-pass findings

A finding is closed only if its first-pass scenario no longer
reproduces.

| finding | disposition | by |
|---|---|---|
| Major: the `object` kind has no caller | closed in code; the choice of option (a) awaits the operator | `e6abfc1` (D1), `4fe2983` (ADR-0075) |
| Minor 1: two JSON documents make `read_file` raise | closed | `b121f2c` (D2) |
| Minor 2: `kind` is not validated | closed | `e6abfc1` (D1) |
| Minor 3: `label_sync.load_labels` raises on 3.12 under an unsearchable `.github/` | still deferred | no commit, as decided |
| Minor 4: ADR-0075's wording rule has two unnamed exceptions | closed | `4fe2983` |
| Minor 5: one of nine hand-written readers says why | closed | `cb5a75b` (D3) |
| Minor 6: a format expression where the file uses literals | closed | `5ecde58` (D4) |

**Major: closed in code.** The scenario was `read_file(<a file holding
null>, "x", object)` returning `(None, "x is null")`, with a docstring
that sent a reader with its own shape wording to that kind. At
`864f1aa` it still returns that pair. At HEAD it raises `ValueError:
read_file kind must be str, dict or list, not <class 'object'>` on
both Pythons. The five bullets of option (a), as the first pass wrote
them:

1. *The `is null` branch and the `object` row of the docstring table
   go.* Done: `grep -n "is null" cli.py` finds nothing, and the table
   has four rows.
2. *The docstring's last sentence is rewritten.* Done. It now reads:
   "A reader whose shape wording or null wording is its own does not
   adopt: it gets its missing arm by hand (ADR-0075 decision 5)."
3. *`object` leaves `TestReadFile.KINDS` and every `assert_pairs`
   row.* Done: `KINDS = (str, dict, list)`. The only `object` left in
   the class is a row of the new unknown-kind test, which pins that it
   is refused.
4. *ADR-0075 decision 1 names three kinds.* Done, in place. The record
   keeps the dropped kind under *Alternatives that lost*, with the five
   readers whose `null` cell it changed.
5. *`update-manifest` is run.* Done: the twin is identical and a fresh
   regeneration changes no byte.

The cost the first pass predicted also holds. No caller passed the
kind, and Verify's 144-cell replay is byte-identical to the recording
taken before the fix loop.

Do the docstring and the record now say what the run measured? Yes
for the kinds. Both say three, both say a reader with its own shape
or `null` wording stays hand-written, and no sentence of either
describes a fourth kind or the `is null` string as live. One gap
remains in the record, and it is about the parse guard, not the kinds:
N2.

**Minor 1: closed.** At `864f1aa`, a 5,000-digit integer raised
`ValueError` and 200,000 balanced arrays raised `RecursionError` out
of `read_file`. At HEAD, under `dict` and `list`, both return `(None,
"x is not valid JSON: ...")`: the same digit-limit text on both
Pythons, `Stack overflow (used 16352 kB) while decoding a JSON array
from a unicode string` on 3.14, and `maximum recursion depth exceeded
while decoding a JSON array from a unicode string` on 3.12. Under
`str` the text comes back. "Never raises for a local-file failure"
now held for every document tried, the fuzz included. Two limits of
that sentence remain that no guard in this function can close:
`MemoryError`, and the small-stack thread recorded under *Looked at*.

**Minor 2: closed.** At `864f1aa`, `"dict"`, `int` and `tuple` each
returned `({'a': 1}, None)`. At HEAD each raises the `ValueError`,
naming what was passed. Verify showed it raises before the path is
touched and that the test fails if the check moves (not re-run).

**Minor 3: still deferred, as the first pass decided.** Re-run on
3.12.13 with `.github/` at mode 000: `factory_config.load` returns
`config: cannot read .github/factory.json: [Errno 13] Permission
denied: ...`, detector F reports it, and `label_sync.load_labels` and
detector J raise `PermissionError`. That is the same at `864f1aa`. On
3.14.6 none raises. Nothing in the fix loop touched it, and
`docs/backlog.md` was not touched. It is a seed for the retro.

**Minor 4: closed.** ADR-0075 decision 2 now ends: "`cli.read_event`
and `dashboard.repo_set` keep `cannot read` for bytes that are not
UTF-8, under 4: neither has a raising cell, so both stay as they
are." Both were run on such bytes and read `cannot read
GITHUB_EVENT_PATH <path>: ...` and `dashboard: cannot read <path>:
...`. The sentence is true of the code.

**Minor 5: closed.** All nine hand-written readers now say why in
code. The eight new comments were each checked three ways: verbatim
against the amendment, placed directly above the read's `try:`, and
true of the code under them, by running the cell each one names.

| reader | what the comment claims | what ran |
|---|---|---|
| detector K | its shape wording covers `null`; bytes that are not UTF-8 join the parse wording | `null` gives `K: docs/standards.json must be a JSON array`; such bytes give `K: docs/standards.json is not valid JSON: ...` |
| `problems_for` | the shape check is `validate_output`'s, reported beside the stem line; a globbed directory is `cannot read` | `null` under a stem that is no skill gives the stem line and `... is not a JSON object`; text that is not JSON gives no stem line; a directory gives `cannot read evals/output/idea.json: [Errno 21] Is a directory: ...` |
| `check_backlog` | its phrase is `is unreadable` | `backlog: docs/backlog.md is unreadable: ...` |
| `cli.read_execution` | absent is an `OSError` message; the log may be an array or one object | absent gives `cannot read execution file <path>: [Errno 2] ...`; one object and an array of one both give `((1, 1.0), None)` |
| `sweeps.load_payload` | absent is an `OSError` message; it also takes stdin | absent gives `sweeps: cannot read payload <path>: [Errno 2] ...`; `-` read the document from stdin |
| `dashboard.respond` | an absent page is an `OSError` message | 500 with `dashboard: cannot read dashboard.html: [Errno 2] ...` |
| `dashboard.respond_post` | an absent backlog is an `OSError` message | 500 with `dashboard: cannot read docs/backlog.md: [Errno 2] ...` |
| `validator.run_review` | an absent findings file is an `OSError` message | read in the code, and pinned by `tests/test_validator.py` (`V: cannot read findings file <path>: ...`); not run separately |

Each agrees with ADR-0075 decision 5. Where a comment adds a fact the
record does not carry (stdin for `load_payload`), the fact is true.
`label_sync.load_labels`' older comment is still true with three
kinds. Its reason is that the shape wording is the loader's own: a
`null` and an empty array both read `L: .github/labels.json must be a
non-empty JSON array of label entries`, where `list` would say `is not
a JSON array`. The two test docstrings that give the same reason
(`tests/test_label_sync.py`, `tests/test_gates.py`) hold for the same
cause, by reading. The one that no longer held, in
`tests/test_lint.py`, was corrected by D3 and now states only what the
test pins.

**Minor 6: closed.** The test writes the literal id its neighbours
use, `grep -c "%04d" tests/test_budget_guard.py` prints 0, and the
commit is one line out and one in.

### New findings

#### Minor (N1): a ledger line that `json.loads` refuses with anything but `JSONDecodeError` still makes the monthly cap check raise where it promises to fail closed

- Scenario: `docs/factory/costs.jsonl` holds one good row, then a row
  whose `tokens` is a 5,000-digit integer. A line of 1,000,000 balanced
  arrays behaves the same, with `RecursionError` for `ValueError`.
  - `cost_ledger.read` raises `ValueError`. So do `cost_report.guard`,
    `budget_guard.record`, `work_queue.month_to_date` and detector G.
  - `cost_report.main(["report"])` raises before it writes anything.
    `$GITHUB_OUTPUT` is left at 0 bytes, with no `pause=` line.
    `cost-report.yml` runs its pause step only when
    `steps.report.outputs.pause == 'true'`, so that step is skipped and
    `FACTORY_PAUSED` is not set. The job is red, and dispatch is not
    paused.
  - The control, in the same probe: a ledger that is not UTF-8
    (criterion 4) gives `PAUSE`, `cr: unreadable ledger — failing
    closed`, `pause=true` written, exit 1, and `record` refuses with a
    problem string.
  - Reproduced at HEAD and at `661ffc7`, on both Pythons. The two
    documents behave identically at both revisions. It is
    pre-existing and outside the fix loop's fence. It is not a
    regression, and the fix loop neither caused it nor was asked to
    fix it.
- Why it is a finding against this run and not only a footnote.
  - The brief names this reader in its blast radius: the monthly cap
    check "raises where it promises to fail closed".
  - `cost_report.guard`'s docstring says "FAILS CLOSED: any read or
    resolution problem decides PAUSE". `budget_guard.record`'s says
    "Fails CLOSED on an unreadable or unparseable ledger". After the
    run, that is true of a ledger that is not UTF-8 and still false of
    these lines.
  - The cause is one arm. `cost_ledger.load` adopted `read_file` with
    `str`, and `cost_ledger.parse` then parses each line itself and
    catches `JSONDecodeError` alone. The wider guard D2 gave `read_file`
    never sees the line.
  - Ten readers still raise on these documents. The ledger's two,
    `cost_ledger.load` and `read`, are the only ones where a traceback
    is not the safe direction. For the others it is a red check or a
    red run. Here it is a pause that does not happen.
    (`sweeps.load_payload` is one of the others: its docstring promises
    "never an exception trace in a scheduled run's log", and it raises
    on the integer too.)
- Why minor and not major. Three things, each measured:
  - No factory writer can produce such a line. All three writers go
    through `cost_ledger.append`, whose `json.dumps` refuses a
    5,000-digit integer on both Pythons. `budget_guard.record` given
    one raises before the write and leaves the ledger's bytes
    unchanged, and the `record` command reports `bg: tokens ... is not
    an integer` and exits 1. The rows the writers build are flat
    objects, so the nested line cannot come from them either (read in
    the code, not run).
  - It cannot arrive through a green pull request. Detector G raises
    on the same ledger. `gates.py`, run as a process on a copy of this
    repo's own ledger with such a row appended, exits 1 with the
    traceback on both Pythons. So the check is red on the change that
    introduces the line.
  - It is loud. Every reader of the ledger goes red at once.

  So it takes a hand edit or a corrupted file pushed past a red gate.
  If either of the first two were false it would be a major. The first
  pass ranked Minor 1, the same two documents one step out, minor on
  the same ground.
- Standard: none.
- Decision: **deferred, and raised to the operator.** Widening the
  fence is not a reviewer's call. But the fence is not the operator's
  either: the resume's scope is the orchestrating session's, and
  extending it to the `str` adopters is the Architect's amendment. The
  operator has not been asked.
  - The fix is the line D2 wrote, in one more place. In
    `cost_ledger.parse`, `except json.JSONDecodeError as err:` becomes
    `except (ValueError, RecursionError) as err:`, keeping the suffix
    `is not valid JSON: {err}`.
  - Tried in a scratch copy of HEAD, with the payload twin and the
    manifest regenerated. The cap check returns `PAUSE` with `cr:
    unreadable ledger — failing closed`, writes `pause=true` and exits
    1. `record` refuses with `ledger: docs/factory/costs.jsonl:2 is not
    valid JSON: ...`. Detector G reports the line. The unedited suite
    stays `Ran 1877 tests`, `OK` on both Pythons, with lint, gates and
    the selftest green. So no pin moves.
  - A real item would add two failing-first tests, through
    `cost_report.guard` and `budget_guard.record`, in one mirrored
    commit. `dashboard._corrections` has the same line and the same
    fix.
  - Recommended as the first follow-up, and before the merge if the
    operator wants the run's headline promise to hold without a
    footnote.

#### Minor (N2): ADR-0075 does not carry the limit N1 describes

- Scenario: a decayed contract, between the record and the run's own
  measurement.
  - The amendment names two groups fenced out of the wider parse
    guard: the hand-written JSON readers, and "a group the brief does
    not name", the readers that adopted with `str` and parse each line
    themselves (`cost_ledger.load`, and so `read`, and
    `dashboard._corrections`). Its frontmatter says decision 5's
    closing "gains one sentence saying the wider parse guard is
    read_file's alone".
  - The sentence that landed says less: "None gets the wider parse
    guard of 1: on those two documents the JSON readers among them
    raise as they did before this record." "None" and "among them" are
    decision 5's hand-written readers. The line-parsing adopters are
    nowhere in the record.
  - *Consequences* still says, with no qualifier, "The monthly cap
    check and `budget_guard.record` reach their fail-closed paths."
  - What a reader of the record concludes: `cost_ledger.load` is an
    adopter, and decision 1 says the function never raises for a
    local-file failure and takes `ValueError` and `RecursionError`, so
    the ledger is covered. It is not (N1). The limit is written down in
    `architecture.md`, `breakdown.md` and `verification.md`. Those are
    run documents. The ADR is what outlives the run, and what the
    gate-2 reviewer reads.
- Standard: none.
- Decision: **fix (non-blocking).** One sentence at the end of
  decision 5: the readers that adopted with `str` and parse each line
  themselves, `cost_ledger.load` and `dashboard._corrections`, keep
  their `JSONDecodeError` arm, so a ledger line that raises
  `ValueError` or `RecursionError` still raises through the cap check.
  No code and no manifest step. If N1's fix is taken, the sentence
  names `dashboard._corrections` alone, or goes if that is fixed too.
  It can ride with N1's commit or with the commit that records the
  operator's confirmation. If neither is made, the gap stays recorded
  here.

#### Minor (N3): two of the three new tests pass only under the interpreter's default limits

- Scenario, part one: the digit limit.
  `test_an_integer_literal_past_the_digit_limit` pins the
  interpreter's text with its default of 4,300 digits. With
  `PYTHONINTMAXSTRDIGITS` set to 0, 10000 or 640, both of its rows fail
  on both Pythons (and with `-X int_max_str_digits=0`, tried on 3.14).
  Under 0 and 10000 the document parses and reads `is not a JSON
  object`. Under 640 the text names another limit. The docstring says
  the variable "must be unset", and nothing in the suite or the
  workflows sets it. But the test neither skips nor adapts, so a shell
  that sets it gets a red suite for a reason that is not the code's.
- Scenario, part two: the stack.
  `test_arrays_nested_past_the_recursion_limit` needs 1,000,000
  balanced arrays to exhaust the interpreter.
  - On 3.12 the limit is a fixed count. The first nesting that raises
    is 9,998, the same in threads with 64 MB, 256 MB and 1 GB stacks,
    and under `sys.setrecursionlimit(5_000_000)`.
  - On 3.14 it is the C stack. The first nesting that raises is
    116,212 on this machine's 16 MB main stack, 465,862 with 64 MB and
    1,863,963 with 256 MB. With 128 MB the document still raises. With
    160 MB it parses.
  - Run in a thread with a 1 GB stack on 3.14, the test fails both
    rows, and the two new tests take 199 seconds where they take 21 ms
    by default. The likely cause is the failure message, which has to
    render a list a million deep. That cause was not timed on its own.
  - This was measured with thread stacks on macOS only. Whether a
    shell with an unlimited stack on Linux gives the main thread such
    a stack was not measured. That part is a hunch.
- Why minor: the default stacks (the usual 8 MB on Linux, 16 MB for
  this build) are roughly 8 to 17 times below the point where the
  document parses. CI runs 3.12, where the stack does not matter.
  Under a raised or a lowered recursion limit both tests pass on both
  Pythons. Together they take 21 ms on 3.14 and 12 ms on 3.12. Both
  bite (Verify's mutations).
- Standard: none.
- Decision: **deferred.** No configuration in use fails. The fix, when
  someone wants it: skip the integer test unless
  `sys.get_int_max_str_digits()` is 4300, or build the expected text
  from it; and pin the nesting arm with a patched `json.loads` that
  raises `RecursionError`, keeping the real document as a second row
  that tolerates a parse. A seed for the retro.

### Looked at and found sound

- **ADR-0075 corrected in place.** CLAUDE.md says decisions are
  superseded, not rewritten, and `docs/adr/README.md` words the rule
  as "Don't delete or rewrite an old ADR". This record is not old. It
  was written by this run (`ded2650`), has only ever been corrected by
  this run (`4fe2983`), is not on `origin/main`, and no remote branch
  holds HEAD. Its status is `provisional`, which the same README
  glosses "pivot freely". Nobody could have cited the first text. The
  dropped kind stays in the record, under *Alternatives that lost*,
  with the measurement that removed it, and `architecture.md`'s
  *Amendments* lists each change to the record. So the correction is
  within the rule. Two things follow. Once the record merges, the rule
  binds. And if the operator does not confirm option (a), the record
  is corrected again before the merge, not superseded.
- **ADR-0075's internal consistency.** No sentence describes four
  kinds, the `is null` string, or a behaviour the code lacks.
  Decisions 1 and 5 and the new alternative agree with each other and
  with the docstring. Decision 5's first bullet gives the reason that
  holds with three kinds. The alternative's five readers match the
  first pass's counterfactual. The one gap is N2.
- **The code against the amendment.** The function is the designed
  text verbatim, the eight comments are verbatim, and each change
  commit holds what its breakdown item names: D1 and D2 are `cli.py`,
  its twin, the manifest and `tests/test_cli.py`; D3 is six files,
  three twins, the manifest and one test docstring; D4 is one test
  line.
- **`cli.py`'s module docstring, CLAUDE.md, `AGENTS.md`.** The module
  docstring's sentence ("unreadable, undecodable, unparsable, or the
  wrong top-level shape") and CLAUDE.md's seam line are still true
  with three kinds and the wider guard. `AGENTS.md` was not touched
  and still carries the older, already drifted seam bullet the first
  pass recorded.
- **The run documents against each other.** The brief's resume, the
  amendment, Milestone D and the re-verification agree on the scope,
  the function's text, the fence and the counts. Three places lag, and
  none is a finding:
  - `release.md` is the first pass's. It still reports HEAD `8924ebb`,
    1874 tests and the major open. Ship refreshes it next, and nobody
    should act on it before then.
  - The brief's "The decided interface" still shows the four-kind
    prototype, and criterion 1 points at it. The resume in the same
    file supersedes it. `architecture.md` got a one-line pointer at its
    interface heading. The brief has none.
  - The first-pass bodies of `architecture.md`, `breakdown.md`,
    `verification.md` and this file describe four kinds. They are
    dated records, and each file's later section says the earlier
    body stays as the record of the first pass.
- **Tests.** The fix loop removed 24 test lines, classified by
  script. In `tests/test_cli.py`: the `KINDS` line, seven `object:`
  rows, three shared rows that come back without `object`, seven
  `list:` rows that come back with the same pair and a closing
  bracket, and two docstring lines. In `tests/test_lint.py`: three
  docstring lines. In `tests/test_budget_guard.py`: one line. Nothing
  else. The only problem string removed and not re-added is `is null`,
  with the branch that returned it. Three test methods were added,
  none removed or renamed, and all three assert through
  `cli.read_file`. No pinned string was edited to make anything pass.
- **A boundary measured, not a finding.** On Python 3.12 the nesting
  limit is a count, not the stack. In a thread whose stack was set to
  512 kB with `threading.stack_size`, `factory_config.load` on a config
  nested 5,000 arrays deep ends the process with exit 138, at `661ffc7`
  and at HEAD alike. No exception is raised, so no guard can catch it.
  3.14 in the same thread returns the problem string. Nothing in the
  repo sets a thread stack size. In a thread with the default stack,
  which is the dashboard's case (`ThreadingHTTPServer`), both Pythons
  return the problem string for 200,000 arrays. It is CPython's, it
  predates the run, and it is recorded so "never raises" is not read
  as "never dies".
- **Verify's dead-branch gap.** Putting the `is null` branch back
  while `object` stays refused leaves the suite green, because the
  branch cannot be reached. Agreed: no behaviour differs, and a grep
  is the right guard.

### Passes with no findings

- **Security.** Clean. No input crosses a trust boundary it did not
  cross before: the same files are read by the same callers. No secret
  is read or written. The new problem texts are the interpreter's own
  (a digit limit, a recursion or stack message with a stack figure)
  and carry no file content and no path. The new `ValueError` shows
  only the `repr` of an argument the calling code wrote. Nothing that
  raised now passes silently: the adopter that returns `[]` has its
  file reported by `check_manifest`. The one reader of untrusted
  input among those still raising, `sweeps.load_payload`, behaves as
  it did at `661ffc7`.
- **Correctness of the amended `read_file`.** No finding in the
  function itself. N1 is one reader further in, and N3 is in its
  tests.

Design has one finding, N2.

### Verdict

*Re-reviewed again 2026-10-04 after the second fix loop: see "Second
re-review (2026-10-04, the ledger parse guard)" at the end of this
file. It closes N1 in code and N2, and adds one minor, N4.*

**Ready to ship (prepare-and-stop).** No critical, no major, and no
finding that cites an enforced standard. The code at `95830fa` does
what option (a) and the folded minors asked. The battery is green on
both Pythons. Nothing routes back to Implement. The three new minors
are deferred or non-blocking, each with its reason above.

What still awaits the operator, whatever the state of the code:

1. **Confirmation of option (a) itself.** The fix loop is the
   orchestrating session's reading of a bare re-invocation. If the
   operator wanted (b) or (c), `git reset --hard 864f1aa` on this
   branch restores the state the operator was shown, as the brief
   records, and ADR-0075 is corrected again before any merge.
2. **Whether to take N1's fix before the merge.** It is one line in
   `cost_ledger.parse`, two tests and a manifest step, shown green in
   scratch. It widens a fence the operator never drew. Recommended.
3. **N2's sentence in ADR-0075,** with either of the above.
4. **Seeds for the retro,** none of them added to `docs/backlog.md` by
   this run: Minor 3; N3; the parse arm for the seven hand-written
   JSON readers still inside the fence; `AGENTS.md`'s drifted seam
   bullet.
5. **Ship's standing operator steps.** `release.md` must be refreshed
   first. Then: a tracking issue for detector B's closing link, and a
   human gate-2 merge by a reviewer who did not author the change,
   because `docs/adr/**` changed (ADR-0036).

## Second re-review (2026-10-04, the ledger parse guard)

A third pass over this run, by a fresh reviewer that wrote none of its
code. It covers the second fix loop, `261e486..HEAD`. Everything above
is the record of the first two passes, at `1d93e71` and at `95830fa`,
and stays as written. N1, N2 and N3 below are the previous re-review's
findings. The one new finding is numbered N4.

**Why this fix loop exists, and what that limits.** The previous
re-review deferred N1 and put it to the operator. The report then
asked "Should I fix the cap-check gap before you push?" and recommended
yes. The operator's reply was to invoke autorun again, with no
arguments and no other words. The orchestrating session read that as
"keep driving" and took the fix (`autorun-brief.md`, "Second resume,
2026-10-04 (UTC): the ledger parse guard"). That is the orchestrating
session's reading, not the operator's words. So this section can say
N1 is closed in code. It cannot say that taking the fix is what the
operator chose. Option (a) from the first resume is still unconfirmed
in words as well.

**Result: zero critical, zero major, one new minor.** N1 is closed in
code, N2 is closed, and N3 stays deferred. The change itself is clean:
one arm, one docstring sentence, three tests and one paragraph of
ADR-0075, with no finding in any of them. The new minor, N4, is in a
caller this run never edited: with the wider arm, two more ledgers
reach a path where `work_queue.py plan` prints a batch priced on spend
it could not total. Nothing cites an `enforced` standards statement,
and nothing routes back to Implement.

### Scope

`git diff 261e486..HEAD` on `refactor/one-guarded-file-read`, HEAD
`6d0bef8`: 6 commits, 11 files, +1,548 / -5.

- Four document commits: `77d0c82` (the brief's second resume),
  `19a5070` (the Architect's second amendment, with one paragraph added
  to ADR-0075), `d7d92cd` (Milestone E) and `a69b3c9` (E2, the replay
  notes).
- One change commit: `ecf86f0` (E1).
- One record commit: `6d0bef8` (the second re-verification).

By subject:

- **The code.** In `cost_ledger.parse` the arm `except
  json.JSONDecodeError` became `except (ValueError, RecursionError)`,
  and the docstring gained one sentence (+6 / -2). The payload twin
  takes the same lines, and `factory/manifest.json` one checksum.
- **Tests.** Three added and no line removed:
  `tests/test_cost_report.py` (+29), `tests/test_budget_guard.py` (+26)
  and `tests/test_cost_ledger.py` (+17).
- **ADR-0075** (+11 / -0): one paragraph closing decision 5.
- **Four run documents:** the brief, `architecture.md`, `breakdown.md`
  and `verification.md`.

Outside the run directory the loop is seven files, +96 / -5.

Standards: `docs/standards.json` holds four statements, all
`advisory`. Three match this diff's domains (factory, pipeline). No
finding cites one, and the diff adds no import, so `stdlib-only` holds.

### What was re-derived rather than read

Everything in this list was run for this pass, on Python 3.14.6
(`python3`) and Python 3.12.13 (`python3.12`), as uid 501, with
`PYTHONINTMAXSTRDIGITS` unset, in `git archive` copies under the
session scratchpad (`ogfr/review-e/`). `base` is `661ffc7`, `before`
is `261e486` and `head` is HEAD. Where a probe needs a git index (the
suite, `gates.py`, a tool run as a process) the copy was given a fresh
one. The probes are session-local and not durable. Verify's second
re-verification is the floor. Where one of its results is leaned on
without a re-run, the text says so.

In the quoted block and in every table below, a work-order id
reads `<work-order id>`. The replacement is made by the command that
produced the text (`sed -E -f mask.sed`), never by hand, because
detector C reads this file. The tables are printed by a script
(`tables.py`) from the probes' recordings. It refuses to print a table
that reads differently from the 3.14 and the 3.12 recording.

- **N1's scenario.** `n1.py` drives `cost_report.main(["report"])`
  with a `GITHUB_OUTPUT` file, then `cost_report.guard` and
  `budget_guard.record`, on five ledgers, at `261e486` and at HEAD.
  `proc.sh` then runs `cost_report.py report` and `gates.py` as
  processes on a copy of this repo's own 92-row ledger with one line
  appended. Results are under *Disposition*.
- **The workflow's condition,** read in
  `.github/workflows/cost-report.yml`. Also under *Disposition*.
- **`parse` against itself, one revision back.** `parse_dump.py` puts
  5,772 single lines through `cost_ledger.parse` at `661ffc7`, at
  `261e486` and at HEAD: 37 chosen by hand and 5,735 from a seeded
  fuzz (random text, mutated rows, integers of 4,299 to 6,000 digits,
  nesting from 10 to 300,000 deep, non-finite numbers, rows with one
  field swapped). `parse_cmp.py` compares the recordings.
  - At `261e486`, 932 lines raise on 3.14 and 1,079 on 3.12: 609
    `ValueError` on both, and 323 and 470 `RecursionError`. No other
    class appears. The `661ffc7` recording is byte-identical.
  - At HEAD none raises. Every line that raised returns exactly one
    tuple, `(1, None, ["is not valid JSON: <text>"])`, where the text
    is the exception's own. Every other line returns the value it
    returned before: 4,839 lines on 3.14 and 4,692 on 3.12, plus one
    blank line that gives no tuple at either revision.
  - No line that raised is kept as a row. 468 lines are kept as rows
    at HEAD, the same 468 on both Pythons. Eleven lines read
    differently on the two Pythons, all nested between the two
    interpreters' limits: a shape problem on 3.14, `is not valid JSON`
    on 3.12. Neither is a kept row.
- **A mixed ledger** of nine lines through `parse`, `read` and
  detector G: three good rows, the integer line, the nested line,
  `{not json`, `[1, 2, 3]`, a row with a negative cost and a blank
  line. At HEAD, on both Pythons, `parse` returns eight tuples, `read`
  keeps exactly the three good rows and returns five problems, one per
  bad line and each located by its line number, and detector G reports
  the same five lines under `G:`. At `661ffc7` and at `261e486` all
  three raise on line 2.
- **Every caller,** by an AST sweep over the 50 `.py` files outside
  `tests/` (`sweep.py`). `parse` has one caller, `load`. `load` has
  two, `read` and detector G. `read` has five: `budget_guard.record`,
  `cost_report.guard`, `dashboard.gather`,
  `gate_digest._capture_latency` and `work_queue.month_to_date`. The
  payload twins repeat them, `dashboard` aside, which is not stamped.
- **What each caller does on the rows it could read,** by running it:
  `callers_probe.py` drives `work_queue.main` and `gate_digest.main`
  with the suites' own fake `gh`, at all three revisions. See N4 and
  *Looked at and found sound*.
- **The arm's width.** `width.py` gives `parse` text and bytes that
  cannot be decoded, and patches `json.loads` to raise five other
  exceptions. The mutant Verify left green, `except Exception`, was
  rebuilt with its twin and manifest and the whole suite run on it,
  and the same widening was tried on `read_file`'s arm.
- **The three tests,** alone: at HEAD, against the `261e486` source,
  under three other digit limits, and in threads with larger stacks.
- **`dashboard._corrections` when it raises.** `dash.py` builds the
  dashboard suite's own fixture repo, calls `gather`, then serves four
  such repos through `dashboard._Handler` on 127.0.0.1 and asks for
  each over HTTP. This is the path Verify could not run.
- **The payload.** `cmp` of root and twin, the twin's SHA-256 against
  the manifest, a fresh `update-manifest` on a HEAD export, and every
  `factory_init.MIRRORS` entry through its own transform.
- **The battery at HEAD `6d0bef8`,** which Verify ran one commit
  earlier. On both Pythons, in an export with a fresh git index: `Ran
  1880 tests`, `OK`; `lint: 0 problem(s) across 25 skills`; `gates: 0
  problem(s)`; `selftest: ok`; `tests.test_factory_init` `Ran 68
  tests`, `OK`. Detector B skipped, as it does locally.
- **A candidate fix for N4,** in a scratch copy only.
- **Ledgers whose every line parses** (`siblings.py`). See *Outside
  this run*.

Leaned on and not re-run: the 144-cell matrix and the six outside
sites (Verify 2C.3); the 60-cell and 204-cell fence replays (2E); the
three named mutations and the mutant that leaves a refused line out
with no problem, each of which fails tests (2F); the per-commit
battery (2G); `dashboard.gather` on a ledger with a refused line
(2B); and the amendment's figures for how deep `parse`'s caller sits.

### Disposition of N1, N2 and N3

A finding is closed only if its scenario no longer reproduces.

| finding | disposition | by |
|---|---|---|
| N1: a ledger line that `json.loads` refuses with anything but `JSONDecodeError` makes the monthly cap check raise | closed in code; the choice to take the fix awaits the operator | `ecf86f0` (E1) |
| N2: ADR-0075 does not carry the limit N1 describes | closed | `19a5070` |
| N3: new tests pass only under the interpreter's default limits | still deferred; it now covers five tests | no commit, as decided |

**N1: closed in code.** The scenario was a ledger of one good row and
one line that `json.loads` refuses with `ValueError` or
`RecursionError`: the cap check raised before it wrote `pause=`. Run
again in-process, with the control beside it:

| revision | ledger | `cost_report.main(["report"])` | `GITHUB_OUTPUT` | `cost_report.guard` | `budget_guard.record` |
|---|---|---|---|---|---|
| `261e486` | good row, then `{not json` | exit 1, no traceback | 451 bytes, `pause=true` | `PAUSE` | refuses, one `bg:` problem; ledger bytes unchanged |
| `261e486` | good row, then a 5,000-digit `tokens` | raises `ValueError` | 0 bytes, no `pause=` line | raises `ValueError` | raises `ValueError`; ledger bytes unchanged |
| `261e486` | good row, then 1,000,000 nested arrays | raises `RecursionError` | 0 bytes, no `pause=` line | raises `RecursionError` | raises `RecursionError`; ledger bytes unchanged |
| HEAD | good row, then `{not json` | exit 1, no traceback | 451 bytes, `pause=true` | `PAUSE` | refuses, one `bg:` problem; ledger bytes unchanged |
| HEAD | good row, then a 5,000-digit `tokens` | exit 1, no traceback | 451 bytes, `pause=true` | `PAUSE` | refuses, one `bg:` problem; ledger bytes unchanged |
| HEAD | good row, then 1,000,000 nested arrays | exit 1, no traceback | 451 bytes, `pause=true` | `PAUSE` | refuses, one `bg:` problem; ledger bytes unchanged |

- The 3.14 and 3.12 recordings give the same table. They differ only
  in the nested line's text: `Stack overflow (used 16352 kB) while
  decoding a JSON array from a unicode string` on 3.14, `maximum
  recursion depth exceeded while decoding a JSON array from a unicode
  string` on 3.12.
- At HEAD the two refused lines read as the control does. The problem
  is `ledger: docs/factory/costs.jsonl:2 is not valid JSON: <text>`,
  the reason is `cr: unreadable ledger — failing closed`, and `record`
  refuses under `bg: refusing to record <work-order id>:` with the
  ledger's bytes unchanged. The control, the good ledger
  (`pause=false`, a row appended) and the ledger that is not UTF-8
  (`pause=true`, `cannot read`) read the same at both revisions.
- As processes, on this repo's own ledger plus one line, on both
  Pythons. At `261e486` `cost_report.py report` exits 1 with a
  traceback and leaves `GITHUB_OUTPUT` at 0 bytes, and `gates.py`
  exits 1 with a traceback. At HEAD both exit 1 with no traceback:
  `pause=true` is written, and `gates.py` prints one `G:` line and
  `gates: 1 problem(s)`. The unedited ledger gives `pause=false` and
  `gates: 0 problem(s)` at both. The copies were clean in git
  afterwards.
- The workflow, read. The report step is `make cost-report`, which is
  `python3 cost_report.py report`, on Python 3.12. The pause step runs
  on `always() && steps.report.outputs.pause == 'true'`. The step that
  posts the report issue runs on `always() &&
  steps.report.outputs.title != ''`. The resume step runs on
  `steps.report.outputs.pause == 'false'`, with no `always()`. So at
  `261e486` the report step dies before any output exists and all
  three are skipped: a red job, and `FACTORY_PAUSED` untouched. At
  HEAD `pause=true` and the title are written before the exit, so the
  pause step runs `gh variable set FACTORY_PAUSED --body true`, or
  fails loudly without its token.
- Two existing tests hold the rest of that chain, and both pass here:
  `TestMain` pins `main` writing `pause=true` and exiting 1 on a ledger
  it cannot parse, and `TestFailClosedPause` pins the `always()`
  condition's text. The workflow and its payload twin are
  byte-identical and no commit of this loop touches them.
- What this does not show: the workflow was not run. The branch is not
  pushed, so the last step rests on how GitHub evaluates `always()`
  and a failed step's outputs. That limit is Verify's, and it stands.

**N2: closed.** Decision 5 of ADR-0075 now closes with a paragraph
that names the two adopters that read with `str` and parse each line
themselves, gives `cost_ledger.parse` the wider guard "because the
monthly cap check must fail closed", and says `dashboard._corrections`
keeps its `JSONDecodeError` arm. Each clause was checked against the
code:

- `cost_ledger.py:227` reads `except (ValueError, RecursionError)`,
  the same classes as `cli.py:322`. `dashboard.py:329` reads `except
  json.JSONDecodeError`, and `dashboard.py` is not in this loop's
  diff.
- "On those two documents it raises as it did before this record":
  `_corrections` raises the same class with the same message at
  `661ffc7` and at HEAD, on both Pythons (`dash.py`).
- The sentence N2 called unqualified, "The monthly cap check and
  `budget_guard.record` reach their fail-closed paths", is now true as
  written for a ledger that is not UTF-8 and for a refused line (the
  table above, and the same probe's not-UTF-8 ledger).

**N3: still deferred, and wider by three tests.** The Architect and
Decompose say so in their own records. Measured here for E1's three:

- The two integer tests fail under `PYTHONINTMAXSTRDIGITS` 0, 10000
  and 640, on both Pythons. Under 0 and 10000 the row parses, and a
  5,000-digit token count is then a valid row. Under 640 the text
  names another limit.
- The nested test passes on the main thread and in a thread with a
  64 MB stack. In a thread with a 512 MB stack on 3.14 the line
  parses, reads `is not a JSON object`, and the test fails. It fails
  in 0.45 seconds with a one-line message, so the 199 seconds the
  previous pass measured for D2's test do not repeat here. On 3.12 it
  passes under every stack tried.
- In every one of those configurations the nested line is still
  refused, under one wording or the other. Only the test's pin moves.

No configuration in use fails. The fix the previous pass sketched
still applies, and it stays a seed for the retro.

### New findings

#### Minor (N4): on a ledger it can only partly read, `work_queue.py plan` still prints a batch priced on the rows it could read, and this run has moved three ledgers onto that path from a traceback

- Scenario: a fixture repo with the cap at $300, `wip_cap` 3 and three
  ready `size:S` orders. The ledger holds a $0.50 row and a $299.75
  row, both dated this month.
  - With both rows readable, `plan` plans nothing. All three orders
    are deferred as "would put the month over its $300.00 cap ($300.25
    spent, ...)", and it exits 0.
  - Make the $299.75 row's `tokens` a 5,000-digit integer. At
    `661ffc7` and at `261e486` `plan` raises `ValueError` and prints
    nothing. At HEAD it prints this and exits 1:

    ```
    $ sed -n '/5,000-digit integer$/,/--json/p' out/cp-head-python3.12.out | grep '^      | ' | sed -E -e 's/^      \| //' -f mask.sed | cut -c1-96
    wq: 3 work order(s) ready to run in parallel (wip_cap 3)
      <work-order id>  size:S  $5.00  issue #1  docs/features/demo/breakdown.md:1
      <work-order id>  size:S  $5.00  issue #2  docs/features/demo/breakdown.md:2
      <work-order id>  size:S  $5.00  issue #3  docs/features/demo/breakdown.md:3
      projected $15.00 on top of $0.50 spent this month
    ledger: docs/factory/costs.jsonl:2 is not valid JSON: Exceeds the limit (4300 digits) for intege
    wq: 1 problem(s)
    ```

  - `plan --json` exits 1 with the same three orders in `batch` and
    the problem in `problems`.
  - A line of 1,000,000 nested arrays in place of that row does the
    same.

  Every ledger tried, by revision, the same on both Pythons:

| ledger | `661ffc7` | `261e486` | HEAD |
|---|---|---|---|
| both rows readable | exit 0; batch of 0; 3 deferred over the cap; 0 problem(s) | exit 0; batch of 0; 3 deferred over the cap; 0 problem(s) | exit 0; batch of 0; 3 deferred over the cap; 0 problem(s) |
| the $299.75 row's `tokens` is a 5,000-digit integer | raises `ValueError`, nothing printed | raises `ValueError`, nothing printed | exit 1; batch of 3 priced on $0.50 spent; 1 problem(s) |
| the $0.50 row, then 1,000,000 nested arrays | raises `RecursionError`, nothing printed | raises `RecursionError`, nothing printed | exit 1; batch of 3 priced on $0.50 spent; 1 problem(s) |
| the $0.50 row, then `{not json` | exit 1; batch of 3 priced on $0.50 spent; 1 problem(s) | exit 1; batch of 3 priced on $0.50 spent; 1 problem(s) | exit 1; batch of 3 priced on $0.50 spent; 1 problem(s) |
| bytes that are not UTF-8 | raises `UnicodeDecodeError`, nothing printed | exit 1; batch of 3 priced on $0.00 spent; 1 problem(s) | exit 1; batch of 3 priced on $0.00 spent; 1 problem(s) |

- What is this loop's doing, and what is not.
  - The path predates the run. A line that is plainly not JSON gives
    this output at `661ffc7`. `month_to_date` returns the readable
    spend beside the problem, and `main` adds the problem to its list,
    still calls `plan_batch` with that spend, prints the plan and
    exits 1. No commit of this run changes `work_queue.py`.
  - What the run changed is which ledgers reach it. This loop's arm
    moved the two refused lines there. The first pass moved the ledger
    that is not UTF-8 there (`733b5f2`, which pinned `month_to_date`
    returning `(0, [problem])`), and that one prices the batch on
    $0.00 spent. Neither earlier pass of this review records running
    `work_queue.main` on it. That miss is this stage's.
  - So for this one caller the traceback was the safer output: it
    printed no batch.
- The decayed contract. `work_queue.py`'s docstring says the batch is
  priced "against month-to-date ledger spend and `monthly_cap_usd`
  (ADR-0034), so an over-cap batch is refused BEFORE any agent is paid
  for". The tool already holds that line in two neighbouring cases,
  each pinned at `main`:
  - an unresolvable cap plans nothing ("refusing to plan a batch it
    cannot price"), and the test's docstring gives the reason: "The
    skill runs what `plan` prints; an unresolvable cap must not put a
    work order on that list";
  - an untrusted listing renders no plan at all.

  A ledger it could not fully read is the third case, and it has no
  refusal. `cost_report.guard` and `budget_guard.record` both refuse
  on the same problem list.
- Why minor and not major. Each point measured or read:
  - The command still fails. It exits 1, prints the problem, and ends
    `wq: 1 problem(s)`, on both legs. The skill tells its reader:
    "`wq:` problems are refusals, not warnings. Stop on them." One
    weakness: the problem line carries the `ledger:` label, and only
    the summary line says `wq:`.
  - It is what a plainly malformed line already did at `661ffc7`. The
    loop makes the two documents behave like every other bad line. It
    does not invent the behaviour.
  - No factory writer can produce either refused line. That is the
    previous re-review's measurement, not re-run. A change that adds
    one is red in CI: `gates.py` exits 1 with the `G:` line.
  - The exposure is one batch: at most `wip_cap` orders at their band
    budgets. That is $15 in the scenario, and $120 under the shipped
    config.

  If the command exited 0, or if the path were new, it would be a
  major.
- Standard: none.
- Decision: **deferred, and raised to the operator.**
  - The fix is not in this loop's file. It belongs in
    `work_queue.main`: when `month_to_date` returns problems, plan
    nothing, as for an untrusted listing. That changes what a plainly
    malformed line does too, which is `661ffc7` behaviour. The
    operator was told "one line in the ledger parser".
  - The fix that is inside this loop's fence is the wrong one.
    Narrowing the arm back re-opens N1: a missed pause, in exchange
    for a traceback at the planner.
  - Tried in a scratch copy of HEAD, with the twin and manifest
    regenerated: one line, `trusted = ready is not None and not
    ledger_problems`. On all four problem ledgers `plan` then prints
    the ledger problem and `wq: 1 problem(s)`, exits 1, and renders no
    batch on either leg. The readable ledger is unchanged. The
    unedited suite stays `Ran 1880 tests`, `OK` on both Pythons, with
    lint, gates and the selftest green. So no test pins today's
    behaviour, and a real item starts with tests at `TestMain`.
    Whether the refusal should also get a `wq:` line of its own is the
    owner's wording to choose.
  - Recommended: name it in the pull-request body as a known limit,
    and take the fix as the first follow-up, as its own small
    maintenance run. Before the merge if the operator prefers. That is
    one more round of Implement, Verify and Review.

### Looked at and found sound

- **Fail closed, in every direction.** With the wider arm no ledger
  line is dropped silently, and no red state turns green.
  - `parse` returns one tuple for every line that is not blank. A
    refused line is `(lineno, None, [one problem])`. `read` keeps a row
    only when its entry is not `None` and it has no problem, so a
    refused line is left out of the sum and its problem returned. The
    5,772-line comparison and the mixed ledger above found no
    exception to either rule.
  - Every caller that was red on a refused line is still red. The
    cap check, `gates.py`, `work_queue.main` and `gate_digest.main`
    each end with exit code 1, where each raised.
    `budget_guard.record` returns its refusal. Verify measured
    `dashboard.gather` listing the problem (2B, not re-run).
  - Two callers go on with the rows they could read. `work_queue.main`
    is N4. `gate_digest.main` is the other, and it is sound: on a
    ledger with a refused line it still posts the digest, appends the
    one new gate row and writes `changed=true`, then exits 1, where it
    raised before any of that. A line that is plainly not JSON does
    exactly the same at `661ffc7`. The row it appends is a wait record
    at $0, outside every spend sum. In the workflow the commit step
    runs on `steps.digest.outputs.changed == 'true'` with no
    `always()`, so after a failing digest step it is skipped and the
    row is not committed. That last part is read, not run.
- **The arm's width.** The `try` holds one call, `json.loads(line)`,
  and `line` is always `str`.
  - In the fuzz the only classes that escaped the old arm were
    `ValueError` and `RecursionError`.
  - `UnicodeDecodeError` is a `ValueError`, but `json.loads` decodes
    only bytes, so no text line can raise it: lone surrogates, raw or
    escaped, parse. `parse` reaches that arm only if a caller hands it
    bytes. Then it reads `is not valid JSON: 'utf-8' codec can't
    decode ...`, where it raised at `261e486`. No caller does: `load`
    passes `read_file`'s decoded text, and bytes that are not UTF-8
    are reported one level up as `cannot read`, which is decision 2's
    wording for a text reader. So the wording is right wherever it can
    be reached.
  - Nothing that should surface is swallowed. With `json.loads`
    patched to raise them, `MemoryError`, `TypeError`, `KeyError`,
    `OverflowError` and `KeyboardInterrupt` each propagate out of
    `parse`.
- **The mutant wider than the design.** Verify's open point, rebuilt
  here: with `except Exception` the suite stays `Ran 1880 tests`, `OK`
  on both Pythons. Not a finding, and the bound is rightly left
  unpinned.
  - The only inputs that tell the two arms apart cannot be built as
    documents. `MemoryError` needs memory to run out, and `TypeError`
    needs a line that is not text, which `splitlines` cannot give. A
    pin would have to patch `json.loads`, which tests the
    implementation and not the interface.
  - The mutant errs in the safe direction for the caller that
    matters: a `MemoryError` reported as `is not valid JSON` is a
    pause.
  - `read_file`'s own arm is unpinned from above in the same way.
    Verify had not tried it. Widened to `except Exception` in a
    scratch copy, with twin and manifest regenerated, it also leaves
    the suite `Ran 1880 tests`, `OK` on both Pythons. So the two arms
    are held alike.
- **The three tests.**
  - Each asserts through a public interface: `cost_report.guard`,
    `budget_guard.record` and `cost_ledger.parse`. The first pins the
    verdict, the reason, the missing cap, both rollups and the exact
    problem list. The second pins the exact problem list and the
    ledger's text unchanged. The third pins the shape of both tuples
    and the problem's prefix, `is not valid JSON: `, as its neighbour
    `test_invalid_json_is_an_unlocated_suffix` does, because the rest
    of the text is the interpreter's and differs by version.
  - They bite. Run against the `261e486` source they end `Ran 3
    tests`, `FAILED (errors=3)` on both Pythons: two `ValueError` and
    one `RecursionError`. At HEAD they end `OK`, in about 18 ms on
    3.14 and 6 ms on 3.12.
  - No existing test is edited. `git diff --numstat 261e486..HEAD --
    tests/` reads 26, 17 and 29 added and 0 removed, and no removed
    line appears in the diff.
  - The cap check has no test of its own for the nested line. That is
    the amendment's decision and it holds: the reader's branch does
    not depend on which exception the line raised, and `parse`'s test
    is the one that fails when the arm narrows to `ValueError`
    (Verify 2F).
  - Their limits under other interpreter settings are N3.
- **The docstring sentence.** True of the code. The arm names the two
  classes, `read_file`'s arm at `cli.py:322` names the same two, and
  the record it cites exists and says the same. "A line `json.loads`
  refuses any other way" reads as the two classes the sentence has
  just named. `MemoryError` is a third way, and it propagates, as the
  first amendment decided for `read_file`.
- **The ADR-0075 paragraph, and the record around it.** The paragraph
  agrees with decision 1 (the same two classes, the same trade-off),
  with decision 2 (a ledger that is not UTF-8 still reads `cannot
  read`), and with the docstring. No sentence of the record claims
  `dashboard._corrections` is guarded, and none describes a behaviour
  the code lacks. The gap N2 named is gone. One reading to avoid:
  "reach their fail-closed paths" is true of a ledger that cannot be
  read or parsed. It does not say the cap check can no longer raise.
  See *Outside this run*.
- **Corrected in place again.** Within the rule, on the previous
  pass's argument: the record is still `provisional`, the remote's
  `main` is still `661ffc7` (one read-only `git ls-remote`), and no
  remote branch holds HEAD.
- **The fence that remains.** The stated reason for leaving
  `dashboard._corrections` alone, "a traceback there is a failed
  dashboard page, not a missed pause", is true of the code. What
  actually happens, the same at `661ffc7` and at HEAD on both Pythons:
  - `gather` raises `ValueError` or `RecursionError` on the two
    documents. On `{nope` it returns with one `dashboard:` problem.
  - Over HTTP, the request for that repo gets no response at all. The
    connection closes (`RemoteDisconnected`), and the server writes
    the traceback to its stderr. It is not a 500. The other repos
    still answer 200, `/api/repos` answers 200 afterwards, and the
    server keeps running.
  - Read, not run: the page fetches each repo on its own and paints a
    failed fetch as that repo's error, so "a failed page" is one
    repo's panel. The command-line leg calls the same `gather`, so
    there it is a traceback.
  - Nothing on a pause or dispatch path touches it. Only
    `tests/test_dashboard.py` imports `dashboard`, `factory.py` lists
    it as an operator command, no workflow or `Makefile` target names
    it, and it is not in `factory_init.MIRRORS`. This repo has no
    `docs/factory/corrections.jsonl` yet.
- **The payload.** `cost_ledger.py` and its twin are byte-identical,
  and the twin's SHA-256 is the one the manifest records. A fresh
  `update-manifest` on a HEAD export reports `factory-init: 0
  problem(s)` and leaves the manifest byte-identical and every other
  file untouched. All 26 `MIRRORS` entries equal their root file
  through the entry's own transform.
- **The code against the amendment.** The diff `ecf86f0` makes to
  `cost_ledger.py` is the amendment's block, line for line, by
  reading. Verify compared the two mechanically (2G). The commit holds
  the seven files its breakdown item names.
- **The run documents against each other.** The brief's second
  resume, the second amendment, Milestone E and the second
  re-verification agree on the scope, the diff, the tests, the fence
  and the counts. `breakdown.md` has no unchecked box. Three things a
  reader should know, none a finding:
  - Three tests landed where the question put to the operator said
    two. `architecture.md` and `breakdown.md` both record why.
  - The brief has no outcome section for this resume yet. The earlier
    two were added with Ship's commit.
  - Older dated sections still describe the cap check raising: the
    brief's "Outcome of the resume", the first re-verification's known
    limit, the first amendment's fence entry and Milestone D's note.
    Each is a dated record, and each file's later section supersedes
    it in words.
- **`one_owner.py`,** the review pre-pass that is not a gate: the same
  six problem strings at `261e486` and at HEAD.

### Outside this run: reproduced, and not findings against it

Probing "fail closed in every direction" turned up four ledgers whose
every line parses, which the line grammar accepts, and which still
defeat the cap check or the planner. Each reads the same at `661ffc7`
and at HEAD, on both Pythons. None is a read or a parse, none is
touched by this run, and none is in this loop's diff. They are
recorded so that "N1 is closed" is not read as "the cap check cannot
raise".

| ledger, every line of which parses | `cost_ledger.read` | detector G | `cost_report.main(["report"])` and `GITHUB_OUTPUT` | `work_queue.month_to_date` |
|---|---|---|---|---|
| one good row (the control) | rows kept: 1; problems: 0 | no problem | exit 0; 470 bytes, `pause=false` | spent `0.5`, no problem |
| cost is a 401-digit integer | rows kept: 2; problems: 0 | no problem | raises `OverflowError`; 0 bytes, no `pause=` line | raises `OverflowError` |
| a gate row waited a 5,000-digit number of seconds | rows kept: 2; problems: 0 | raises `ValueError` | raises `ValueError`; 0 bytes, no `pause=` line | raises `ValueError` |
| two rows whose tokens are 4,300 digits each | rows kept: 3; problems: 0 | no problem | raises `ValueError`; 0 bytes, no `pause=` line | spent `1.5`, no problem |
| cost is NaN | rows kept: 2; problems: 0 | no problem | exit 0; 506 bytes, `pause=true` | spent `nan`, no problem |

- Three of them leave `GITHUB_OUTPUT` at 0 bytes: the integer cost,
  the gate row and the token rows. So by the workflow's text there is
  no pause, as with N1 before this loop. The exception leaves from
  `cost_report.aggregate` (a huge integer added to a float), from
  `cost_ledger.gate_wait` (the wait converted with `int()`) and from
  `cost_report.compose_report` (a sum past the digit limit,
  formatted).
- For the integer cost and the token rows detector G reports nothing.
  That is the protection the previous pass leaned on when it ranked N1
  minor, and it is absent here. On the gate row detector G raises.
- The NaN row is the one a writer can produce. The `record` command
  of `budget_guard.py`, given `nan` as the cost, exits 0 and appends a
  row whose cost is `NaN`. The cap check then pauses, because `decide`
  refuses a spend that is not finite. The planner does not. On a
  ledger holding a $299.75 row and that row, with the cap at $300 and
  three ready `size:L` orders, `work_queue.py plan` exits 0 with `wq:
  0 problem(s)` and prints `projected $120.00 on top of $nan spent
  this month`. Every comparison with NaN is false.
- Which writer could produce the other three was not measured.

These are missing range checks on a row's values. That is a different
defect from the guarded read, as the brief ruled for the shape cells
of `trigger_eval.print_metrics`. They are a seed for a maintenance run
of their own, through `capture`, and the operator's to weigh. Nothing
was added to `docs/backlog.md`.

### `release.md`: what is now untrue (for Ship; not a finding)

`release.md` was prepared at `261e486`, and Ship refreshes it next.
Nobody should act on it before then. What this loop made false or left
behind:

1. **The header.** HEAD `e46fa71`, "35 commits on top of `661ffc7`",
   "the 36th". HEAD is `6d0bef8`, 42 commits, before this section's
   commit and Ship's.
2. **The verdict paragraph and *Outcome*.** "The second is the
   operator's decision on N1" and "All eight pre-flight checks pass at
   `e46fa71`". N1 is fixed in code, the second step is now to confirm
   that fix, and every check has to run again at the new tip.
3. **Two frontmatter entries.** "The drafted pull request body is true
   of the branch as it stands, which is the merge-without-the-fix
   path": the branch is now the path with the fix. And "the fix loop
   this release now contains (864f1aa..e46fa71)": it now contains a
   second one.
4. **Check 1.** The last verification pass is the second
   re-verification at `a69b3c9`, not the one at `b94462b`. `Ran 1877
   tests` at the tip is now 1880, here, in check 5 and in the
   pull-request body.
5. **Check 2.** N1 "deferred, and raised to the operator" is closed in
   code. N2 "fix, non-blocking" is closed. N3 covers five tests, not
   "two new `TestReadFile` tests". The quoted verdict, "three minor",
   is the previous pass's, and N4 is missing.
6. **Check 3.** "The 6,687 added lines" is 8,648 at `6d0bef8`. The
   scan has not covered this loop's lines.
7. **Check 4** and the post-release spot check quote probes "on an
   export of `e46fa71`", and neither carries this loop's behaviour
   change: a ledger line the parser refuses is now a problem string,
   and the cap check pauses on it.
8. **Check 5.** `git rev-list --count origin/main..HEAD` reads 42, not
   35. The squash commit `8f04576` and its tree `4b1a4cf9` are
   `e46fa71`'s. HEAD's tree is `ccd52d83`.
9. **Check 6.** Every pair was merged from `e46fa71`. The sweep has
   expired with the new tip, and its counts with it.
10. **Check 7.** The rehearsed squash is "43 files, +6,687 / -291". At
    `6d0bef8` it is 43 files, +8,648 / -295. "The count falls from
    1877 to 1793: the 84 tests this run adds" is 1880 and 87. The cost
    of a revert does not yet say that the cap check raises again on a
    refused line.
11. **What to read before merging.** "The end of decision 5 is where
    N2's sentence is missing": the paragraph is there. The pointers
    into this file and into `verification.md` stop at the previous
    pass.
12. **Step 1.** "The reset discards exactly these ten commits, and the
    commit that adds this file on top of them". From HEAD the same
    reset, to `864f1aa`, discards 17, this loop's six among them. The
    undo for this loop alone is `git reset --hard 261e486`, and the
    step does not name it.
13. **Step 2, the whole step.** N1 "still makes the monthly cap check
    and `budget_guard.record` raise" is false at HEAD. Path A is what
    the branch now is, with three tests where the step says two and
    the arm at line 227 where it says 223. Path B no longer describes
    the branch.
14. **The drafted pull-request body.** *For the operator*, item 2
    ("Decide N1"). The whole *Known limit* section: the cap check no
    longer raises on those two lines, "that parse was left alone" is
    false, and so is "ADR-0075 does not yet state the limit". *Test
    evidence* ("Measured at `e46fa71`", 1877). The test-plan box
    "Operator decides N1". The summary's sentence on the cap check
    stops at the ledger that is not UTF-8. And the note that the body
    was run through detector B "on an export of `e46fa71`".
15. **Retro seeds.** "N3: two `TestReadFile` tests" is five tests. "N1,
    if the operator merges without it" has one line left,
    `dashboard._corrections`. "N2, if its sentence is not added": it
    is added. N4 and the four ledgers under *Outside this run* are
    missing.
16. **Preparation history** has no entry for this loop.

### Passes with no findings

- **Security.** Clean. No new input crosses a boundary: the same file
  is read by the same callers. No secret is read or written. The new
  problem text is the interpreter's own. Across every line of the fuzz
  that raised before, it is one of three shapes per Python: the
  digit-limit message, which carries two digit counts, and the
  recursion message for an array or for an object, which on 3.14
  carries a stack figure in kB. None carries file content, and the
  only path in the problem is the ledger's fixed relative one. The
  text goes to the job's log, not to `GITHUB_OUTPUT`: the file the cap
  check wrote for the two ledgers holds `pause`, `title`, `body` and
  `reason`, and none of the interpreter's words. Nothing that raised
  now passes silently.
- **Correctness of the change.** No finding in `parse`, in its
  docstring, in the three tests or in the payload. N4 is one caller
  further out, in code this run did not write.

Design has one finding, N4.

### Verdict

**Ready to ship (prepare-and-stop).** No critical, no major, and no
finding that cites an enforced standard. Nothing routes back to
Implement. The code at `6d0bef8` does what the second resume asked,
and no more: the cap check pauses and `record` refuses on a ledger
line the parser refuses, on both Pythons, with no pinned string moved
and no existing test edited. N1 is closed in code and N2 is closed.
N3 stays deferred. The one new minor, N4, is deferred with its reason
above and put to the operator.

What still awaits the operator, whatever the state of the code:

1. **Confirmation of option (a).** Still unsaid. If the operator
   wanted (b) or (c), `git reset --hard 864f1aa` restores the state
   the operator was shown. From HEAD that also discards this loop.
2. **Confirmation of this fix.** Taking N1's fix is the orchestrating
   session's reading of a bare re-invocation. If the operator did not
   want it, `git reset --hard 261e486` restores the branch as the last
   report described it. Part of the same confirmation: three tests
   landed where the question said two.
3. **N4.** Whether the planner's refusal is taken before the merge or
   as the first follow-up. Recommended: the follow-up, with the limit
   named in the pull-request body.
4. **The four ledgers under *Outside this run*.** Whether they get a
   maintenance run of their own. The NaN row is the one to read
   first.
5. **Seeds for the retro,** none of them added to `docs/backlog.md` by
   this run: Minor 3; N3, now five tests; the wider parse arm for
   `dashboard._corrections` and for the seven hand-written JSON
   readers still inside the fence; `AGENTS.md`'s drifted seam bullet;
   the `trigger_eval.print_metrics` shape cells.
6. **Every release step.** `release.md` is refreshed first, from the
   list above. Then the push, a tracking issue for detector B's
   closing link, the draft pull request, and a human gate-2 merge by a
   reviewer who did not author the change, because `docs/adr/**`
   changed (ADR-0036). None of it has been run.
