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
