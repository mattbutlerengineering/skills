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
