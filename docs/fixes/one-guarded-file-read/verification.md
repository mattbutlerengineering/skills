---
stage: verify
run: maintenance:one-guarded-file-read
date: 2026-10-04
assumptions:
  - "No prd.md exists (maintenance run). The criteria list is the nine success criteria in autorun-brief.md plus the breakdown Accept lines not already covered by one of them; the Accept lines are covered below by criteria 2, 3, 4, 5, 7 and 8 and by the extra checks E1 to E3."
  - "The matrix replay, the six-site probe and the AST sweep use the session-local scratch tools under the scratchpad (ogfr/matrix.py, diff_matrix.py, probe_six.py, sites.py). Their output is quoted here; the durable evidence is the repo's own tests, named per cell in criterion 2."
  - "The 'tests watched failing first' claim for each item cannot be read from history, because each reader item is one commit holding the test and the change together. It is replaced here by reverting each fix in a scratch copy and showing the matching tests fail (criterion 8 and the mutation section)."
  - "Unreadable cells ran for real: the verifier ran as uid 501, not root, so every chmod 0 test executed rather than skipping."
  - "Mutations are whole-function or whole-file reverts to the 661ffc7 reader, or a hand-removed clause, applied in scratch copies of HEAD. A reverted mirrored file leaves its payload twin and manifest untouched in the copy, so only the named reader's own test modules were run there."
---

# Verification: one owner for the guarded local-file read

## Summary

Nine of nine brief criteria pass, and all extra Accept checks pass. At HEAD `e974147` the battery is green on 3.14.6 and 3.12.13, the matrix replay against the `661ffc7` baseline ends `cells 144 | identical 123 | fixed 16 | wording changed 2 | still raising 3 | newly raising 0`, none of the six sites outside the matrix raises, and every one of nine reverted fixes made its matching tests fail with the original traceback. Verdict: PASS, route to Review. One honest limit: per-reader "watched failing first" is not readable from history (tests and change share a commit), so it is demonstrated by mutation instead.

## Criteria & evidence

### 6. The battery is green at the last commit

- Check: the four battery commands at HEAD, plus the suite under Python 3.12 (CI's Python).
- Evidence:
  ```
  $ python3 -m unittest discover tests > out 2>&1; echo $?     (Python 3.14.6)
  exit 0
  Ran 1874 tests in 21.130s
  OK
  $ python3.12 -m unittest discover tests > out 2>&1; echo $?  (Python 3.12.13)
  exit 0
  Ran 1874 tests in 19.887s
  OK
  $ python3 lint.py | tail -1
  lint: 0 problem(s) across 25 skills
  $ python3 gates.py | tail -1
  gates: 0 problem(s)
  $ python3 gates.py --selftest | tail -1
  selftest: ok
  ```
- Result: PASS (at HEAD only; the per-commit "green at every commit" claim was not replayed for all 18 commits, see Not verified)

### 1. `cli.read_file` exists with three parameters and its own tests assert every failure kind for every `kind`

- Check: read the function, ran `tests.test_cli.TestReadFile`, and read the assertions. Commit `5e5f494` (A1) adds `cli.py` (+57), its payload twin, the manifest and `tests/test_cli.py` (+185).
- Evidence:
  ```
  def read_file(path, shown, kind):
  Ran 16 tests in 0.021s
  OK
  ```
  The 16 tests are: absent, directory in place, unreadable, not UTF-8, not JSON, empty, JSON object, array, string, number, true, false, null, non-object top level under `dict`, `shown` echoed, unsearchable parent. The shared helper `assert_pairs` asserts `set(expected) == set(KINDS)` (str, dict, list, object), so every row names all four kinds, compares the exact `(value, problem)` pair and also `assertIs(type(...))`. Example: `str: (None, "cannot read docs/thing.json: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte")` against `dict/list/object: (None, "docs/thing.json is not valid JSON: ...")`.
- Result: PASS

### 2. Every in-scope cell that raised at `661ffc7` returns a problem string, the exact string pinned by a test through the reader's public interface (the regression)

- Check, part one, the matrix: recorded a fresh matrix at HEAD and diffed it against `baseline-661ffc7.json`.
- Evidence:
  ```
  cells 144 | identical 123 | fixed 16 | wording changed 2 | still raising 3 | newly raising 0
    CHANGED  factory_config.load / not utf-8
               now: (None, ["config: .github/factory.json is not valid JSON: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte"])
    CHANGED  label_sync.load_labels / not utf-8
               now: ([], ["L: .github/labels.json is not valid JSON: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte"])
    STILL RAISES  trigger_eval.print_metrics / json array: RAISES AttributeError
    STILL RAISES  trigger_eval.print_metrics / json object: RAISES KeyError
    STILL RAISES  trigger_eval.print_metrics / json string: RAISES AttributeError
  ```
  The 16 FIXED lines: foreign_entries not utf-8; gates K not utf-8; gates E unreadable, json array, json string; gates F unreadable; check_manifest unreadable; check_plugin_skills unreadable and not utf-8; check_pi_package unreadable; check_backlog not utf-8; load_case_set unreadable; read_execution not utf-8; load_payload not utf-8; cost_ledger.load not utf-8; cost_ledger.read not utf-8.
- Check, part two, the six sites outside the matrix: `probe_six.py`, exit 0, no `RAISES` and no `Traceback` in 8 probes.
  ```
  dashboard._corrections / not utf-8     ({}, ["dashboard: cannot read docs/factory/corrections.jsonl: 'utf-8' codec can't decode byte 0xff ..."])
  dashboard._corrections / unreadable    ({}, ["dashboard: cannot read docs/factory/corrections.jsonl: [Errno 13] Permission denied: '<path>'"])
  dashboard._backlog / not utf-8         (None, ["dashboard: cannot read docs/backlog.md: 'utf-8' codec can't decode byte 0xff ..."])
  dashboard.respond('/') / page not utf-8 (500, {'problems': ["dashboard: cannot read dashboard.html: 'utf-8' codec ..."]})
  dashboard.respond_post / backlog not utf-8 (500, {'problems': ["dashboard: cannot read docs/backlog.md: 'utf-8' codec ..."]})
  validator.run_review / findings not utf-8  ["V: cannot read findings file <path>: 'utf-8' codec ..."]   (fake gh calls made before the read: 0)
  lint.check_output_evals / unreadable   ["cannot read evals/output/idea.json: [Errno 13] Permission denied: '<path>'"]
  lint.check_output_evals / not utf-8    ["evals/output/idea.json is not valid JSON: 'utf-8' codec ..."]
  ```
- Check, part three, the pinning test per cell. I read each test body; every one is an `assertEqual` on the whole returned value or the whole problem list through the public function (no `assertIn`, no substring on a traceback; the one exception is noted):

  | Cell | Test (file, name) |
  |---|---|
  | `foreign_entries` not utf-8 | `tests/test_standards_index.py` `TestForeignEntries.test_bytes_that_are_not_utf8_are_a_problem_not_a_crash`; and via `update`, `TestUpdate.test_an_existing_file_that_is_not_utf8_refuses_to_write` (also asserts the file is untouched) |
  | gates K not utf-8 | `tests/test_gates.py` `TestStandardsDrift.test_a_committed_index_that_is_not_utf8_is_a_problem` |
  | gates E unreadable | `tests/test_gates.py` `TestScaffoldSync.test_a_manifest_the_process_may_not_read_is_a_problem` (exact string incl. path) |
  | gates E array, string (and null, number, true) | `TestScaffoldSync.test_a_manifest_that_is_not_an_object_is_one_problem` (5 subtests, `["E: factory/manifest.json is not a JSON object"]`) |
  | gates F unreadable | `tests/test_gates.py` `TestConfigShape.test_a_config_the_process_may_not_read_is_a_problem_per_home` (both homes, exact) |
  | `check_manifest` unreadable | `tests/test_lint.py` `test_a_manifest_the_process_may_not_read_is_a_problem` |
  | `check_plugin_skills` unreadable, not utf-8 | `tests/test_lint.py` `test_an_unreadable_manifest_is_left_to_check_manifest`, `test_a_manifest_that_is_not_utf8_is_left_to_check_manifest` (assert `== []`; the second also pins `len(check_manifest) == 1`) |
  | `check_pi_package` unreadable | `tests/test_lint.py` `test_a_package_json_the_process_may_not_read_is_a_problem` |
  | `check_backlog` not utf-8 | `tests/test_lint.py` `test_a_backlog_that_is_not_utf8_yields_one_problem_string` |
  | `load_case_set` unreadable | `tests/test_eval_schema.py` `TestLoad.test_a_file_the_process_may_not_read` |
  | `read_execution` not utf-8 | `tests/test_cli.py` `TestReadExecution.test_bytes_that_are_not_utf8_are_an_error` (exact tuple) |
  | `load_payload` not utf-8 (file, stdin) | `tests/test_sweeps.py` `test_a_file_that_is_not_utf8_is_a_problem_not_a_traceback`, `test_stdin_that_is_not_utf8_is_a_problem_not_a_traceback` (path None and "-") |
  | `cost_ledger.load`, `.read` not utf-8 | `tests/test_cost_ledger.py` `TestLoad.test_a_ledger_that_is_not_utf8_is_the_callers_problem_string`, `TestRead.test_a_ledger_that_is_not_utf8_is_a_ledger_problem` |
  | `factory_config.load` not utf-8 (changed wording) | `tests/test_factory_config.py` `TestLoad.test_a_config_that_is_not_utf8_is_a_problem` (exact tuple) |
  | `label_sync.load_labels` not utf-8 (changed wording) | `tests/test_label_sync.py` `TestLoadLabels.test_a_taxonomy_that_is_not_utf8_is_flagged` (exact list) |
  | `_corrections`, `_backlog` (via `gather`) | `tests/test_dashboard.py` `test_a_corrections_stream_that_is_not_utf8_is_a_problem`, `test_a_backlog_that_is_not_utf8_is_null_and_a_problem` |
  | `respond`, `respond_post` | `tests/test_dashboard.py` `test_a_page_file_that_is_not_utf8_is_a_500`, `test_a_backlog_that_is_not_utf8_is_500_and_left_alone` (also asserts the bytes unchanged) |
  | `run_review` | `tests/test_validator.py` `test_findings_that_are_not_utf8_are_a_problem_not_a_traceback` (also asserts no `gh` call) |
  | `problems_for` | `tests/test_lint.py` `test_a_record_file_the_process_may_not_read_is_a_problem`, `test_a_directory_named_like_a_record_file_is_a_problem`; its not-UTF-8 arm was already on the JSON arm before the run |

  Gap inside this criterion, small: the dashboard `_corrections` unreadable probe cell and the not-UTF-8 `problems_for` cell are in the probe output but no new test was added for them (the first was already pinned before the run, the second never raised). Neither is in the 16 fixed cells.
- Result: PASS

### 3. No pinned wording changes except the two named

- Check: the matrix summary above (exactly 2 CHANGED, 0 newly raising, only `print_metrics`'s three still raising), plus a removed-line audit of every test file over `661ffc7..HEAD`.
- Evidence:
  ```
  commits removing any test line, across all 15 changed test files:
  tests/test_factory_config.py  729510e (A6)  removed=27
  tests/test_label_sync.py      9f93c0f (A7)  removed=3
  (no other test file in any other commit removes a line)
  ```
  A6 removed `TestObjectProblems` whole (`test_an_object_is_clean`, `test_every_other_json_top_level_is_one_problem`) and moved the not-UTF-8 test into `TestLoad` with the new exact string; the two tests' cells live on in `TestReadFile` (`test_a_json_object`, `test_every_non_object_top_level_is_one_problem_under_dict`), and the wiring stays pinned by `TestLoad.test_a_config_that_is_not_an_object_is_a_problem` and `TestConfigShape.test_a_config_that_is_not_an_object_is_one_problem`, both unedited. A7 changed one assertion, from `startswith("L: cannot read ...")` to the exact `"L: .github/labels.json is not valid JSON: ..."`.
- Result: PASS

### 4. A non-UTF-8 ledger makes `cost_report.guard` and `budget_guard.record` fail closed

- Check: the named tests, then an independent drive in a scratch tree holding `docs/factory/costs.jsonl` = `ff fe 00`.
- Evidence (tests, run as part of the full suite, plus mutated-revert below where each raises `UnicodeDecodeError`): `tests/test_cost_report.py` `TestGuard.test_a_ledger_that_is_not_utf8_fails_closed` (asserts `verdict == PAUSE`, `reason == "cr: unreadable ledger — failing closed"`, `cap is None`, zero totals, the exact problem), `tests/test_budget_guard.py` `TestRecord.test_a_ledger_that_is_not_utf8_fails_closed` (exact refusal and ledger bytes unchanged), and `tests/test_work_queue.py` `test_a_ledger_that_is_not_utf8_is_a_problem_not_a_crash`.
  ```
  guard: PAUSE 'cr: unreadable ledger — failing closed' None ["ledger: cannot read docs/factory/costs.jsonl: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte"]
  record: ["bg: refusing to record <work-order id>: ledger: cannot read docs/factory/costs.jsonl: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte"]
  ledger bytes after: b'\xff\xfe\x00'
  ```
- Result: PASS

### 5. One owner: no in-scope reader types its own `read_text` guard, and each hand-written one is named with its reason

- Check: re-ran the AST sweep at HEAD (`sites.py`).
- Evidence:
  ```
  sites 57 | guarded 18 | unguarded 39 | open() among them 2
  ```
  Each of the 18 guarded sites, against `architecture.md`:

  | Site | Disposition |
  |---|---|
  | `cli.py:305` `read_file` | the owner |
  | `cli.py:345` `read_execution`, `label_sync.py:66` `load_labels`, `gates.py:1458` `check_standards_drift` (K), `lint.py:772` `problems_for`, `lint.py:875` `check_backlog`, `sweeps.py:472` `load_payload`, `dashboard.py:510` `respond`, `dashboard.py:566` `respond_post`, `validator.py:324` `run_review` | "Hand-written exceptions (missing arm added, wording kept)" section, each with its reason in the per-reader notes (absent-file text is an `OSError` message `(None, None)` cannot reproduce; or `null` wording is the loader's own; or a stdin read) |
  | `cli.py:267` `read_event`, `dashboard.py:88` `repo_set`, `one_owner.py:284` `source_files`, `orientation_pack.py:133` and `:146`, `knowledge_plane.py:348` `parse_run`'s verification read, `charter_replay.py:512` `main` | "Untouched" section: "none has a raising cell" |
  | `trigger_eval.py:508` `print_metrics` | "Untouched": deferred, a shape defect after a successful read |

  18 = 1 + 9 + 8. No remaining guarded site is outside these three groups. The unguarded count, 39, equals the architecture's "39 unguarded reads out of scope". `factory_config.object_problems` and `lint.object_problems` are gone; the sole survivor, `eval_schema.object_problems` (line 87), is the one the ADR says stays.
- Result: PASS

### 7. Payload and manifest are level with the root

- Check: detector E, `tests.test_factory_init`, then `update-manifest` and `git status`.
- Evidence:
  ```
  $ python3 gates.py | tail -1
  gates: 0 problem(s)
  $ python3 -m unittest tests.test_factory_init
  Ran 68 tests in 1.621s
  OK
  $ python3 factory_init.py update-manifest
  factory-init: 0 problem(s)
  $ git status --short
  (empty)
  ```
- Result: PASS

### 8. The test ordering is visible in the commit history

- Check: `git show --stat` per commit; archived A2 and B1 into scratch and ran the suite there; also ran A2's test files against the unmodified `661ffc7` source.
- Evidence:
  ```
  5e5f494 A1  cli.py +57, factory/templates/.../cli.py, manifest, tests/test_cli.py +185   (function and its 16 tests, nothing calls it)
  8bbf427 A2  tests only (7 test files, +239) and breakdown.md          git diff --name-only 5e5f494 8bbf427 | grep -v ^tests/  ->  docs/fixes/.../breakdown.md only
  7fc79e7 B1  tests only (5 test files, +179) and breakdown.md          git diff --name-only 7fc79e7~1 7fc79e7 | grep -v ^tests/ ->  docs/fixes/.../breakdown.md only
  A2 archived (8bbf427) into scratch:  Ran 1833 tests ... OK  (exit 0)
  B1 archived (7fc79e7) into scratch:  Ran 1862 tests ... OK  (exit 0)
  661ffc7 source + A2's seven test files copied in:  Ran 1817 tests ... OK  (exit 0)
  ```
  A2 and B1 change no source file (only their own checkbox in `breakdown.md`, which the breakdown Notes record). The net passes against the pre-adoption code: the A2 tree is A1 plus tests, with no reader adopted, and the same test files also pass on the pristine `661ffc7` source. Order of commits: A1, A2, then A3 to A9, then B1, B2 to B7, C1, C2. The two decided pin edits appear only in `729510e` (A6) and `9f93c0f` (A7), and no other pre-existing assertion was edited or deleted except `TestObjectProblems`'s two tests in A6 (criterion 3 audit).

  The mutation results below stand in for "watched failing first" on each reader item.
- Result: PASS, with the limit in the assumptions: reader items hold test and change in one commit, so only A1 and A2 order is readable from history.

### 9. Decision record 0075 exists, is indexed, and passes the ADR detectors

- Check: file, index row, detectors.
- Evidence:
  ```
  docs/adr/0075-the-guarded-file-read-joins-the-cli-seam.md   (Status: provisional, Date: 2026-10-04)
  docs/adr/README.md:98: row for 0075, title 'The guarded local-file read joins the cli seam', status provisional
  $ python3 -m unittest tests.test_gates.TestAdrStatusVocabulary tests.test_gates.TestBlueprintDrift
  Ran 11 tests ... OK
  check_blueprint_drift(root) -> []
  gates: 0 problem(s)
  ```
- Result: PASS

### E1. Do the tests bite? Nine readers reverted in scratch copies of HEAD

- Check: for each, applied the mutation to a scratch copy (`git archive HEAD`, `git init`, `git add -A`), showed the diff, ran the reader's test modules. Every run exited 1 with the original traceback. Kinds covered: `str` (cost_ledger, dashboard), `list` (standards_index), `dict` (gates E, eval_schema), hand-fixed (sweeps, label_sync, validator, lint's two).
- Evidence:
  ```
  str  cost_ledger.py reverted to 661ffc7 (diff: removes `from cli import read_file`, restores is_file + try/except OSError)
       Ran 188 tests, FAILED (errors=5), 5x UnicodeDecodeError
       ERROR: test_cost_ledger TestLoad.test_a_ledger_that_is_not_utf8_is_the_callers_problem_string
       ERROR: test_cost_ledger TestRead.test_a_ledger_that_is_not_utf8_is_a_ledger_problem
       ERROR: test_cost_report TestGuard.test_a_ledger_that_is_not_utf8_fails_closed
       ERROR: test_budget_guard TestRecord.test_a_ledger_that_is_not_utf8_fails_closed
       ERROR: test_work_queue TestRowsAndSpend.test_a_ledger_that_is_not_utf8_is_a_problem_not_a_crash
  str  dashboard.py reverted to 661ffc7 (diff: 4 hunks, `_corrections`, `_backlog`, `respond` and `respond_post` back to OSError-only)
       Ran 110 tests, FAILED (errors=4), 4x UnicodeDecodeError
       ERROR: TestRespondPost.test_a_backlog_that_is_not_utf8_is_500_and_left_alone
       ERROR: TestGatherBacklog.test_a_backlog_that_is_not_utf8_is_null_and_a_problem
       ERROR: TestImprovementRates.test_a_corrections_stream_that_is_not_utf8_is_a_problem
       ERROR: TestPage.test_a_page_file_that_is_not_utf8_is_a_500
  list standards_index.py reverted to 661ffc7 (diff: `read_file(..., list)` replaced by is_file + read_text + json.loads + isinstance)
       Ran 38 tests, FAILED (errors=2), 2x UnicodeDecodeError
       ERROR: TestUpdate.test_an_existing_file_that_is_not_utf8_refuses_to_write
       ERROR: TestForeignEntries.test_bytes_that_are_not_utf8_are_a_problem_not_a_crash
  dict gates.py detector E, hand-edited to `json.loads(mpath.read_text(encoding="utf-8"))` with no guard
       diff: 843,847c843,845  (read_file block replaced by is_file + json.loads(read_text))
       Ran 9 tests (TestScaffoldSync), FAILED (errors=9): AttributeError 'bool'/'int'/'list'/'NoneType'/'str' has no attribute 'get',
       PermissionError ...factory/manifest.json, UnicodeDecodeError 0xe9
       ERROR: test_a_manifest_that_is_not_an_object_is_one_problem (5 subtests: '"x"', '["x"]', '5', 'null', 'true')
       ERROR: test_a_manifest_the_process_may_not_read_is_a_problem
       (also, collaterally: test_a_manifest_whose_bytes_are_not_utf8_is_a_problem, test_a_manifest_that_is_not_json_is_a_problem, test_an_empty_manifest_is_a_problem)
  dict eval_schema.py reverted to 661ffc7 (diff: `read_file(path, label, dict)` replaced by is_file + json.loads + object_problems)
       Ran 66 tests, FAILED (errors=1), PermissionError ...routing.json
       ERROR: TestLoad.test_a_file_the_process_may_not_read
  hand sweeps.py: UnicodeDecodeError clause removed (diff: 475,476d474)
       Ran 100 tests, FAILED (errors=3), 3x UnicodeDecodeError
       ERROR: TestLoadPayload.test_a_file_that_is_not_utf8_is_a_problem_not_a_traceback
       ERROR: TestLoadPayload.test_stdin_that_is_not_utf8_is_a_problem_not_a_traceback (path='-')
       ERROR: TestLoadPayload.test_stdin_that_is_not_utf8_is_a_problem_not_a_traceback (path=None)
  hand label_sync.py reverted to 661ffc7 (diff: `except (OSError, UnicodeDecodeError)` restored, JSON-arm clause removed)
       Ran 36 tests, FAILED (failures=1)
       FAIL: TestLoadLabels.test_a_taxonomy_that_is_not_utf8_is_flagged
       AssertionError: Lists differ: ["L: cannot read .github/labels.json: 'utf-8' [67 chars]yte"] != ["L: .github/labels.json is not valid JSON: 'u[73 chars]yte"]
  hand validator.py reverted to 661ffc7 (diff: 325: `except (OSError, UnicodeDecodeError)` -> `except OSError`)
       Ran 106 tests, FAILED (errors=1), UnicodeDecodeError
       ERROR: TestRunReview.test_findings_that_are_not_utf8_are_a_problem_not_a_traceback
  hand lint.py: check_output_evals `except OSError` clause and check_backlog's UnicodeDecodeError removed (diff: 773,774d772; 876c874)
       Ran 149 tests, FAILED (errors=3)
       ERROR: TestBacklog.test_a_backlog_that_is_not_utf8_yields_one_problem_string  (UnicodeDecodeError)
       ERROR: TestOutputEvals.test_a_directory_named_like_a_record_file_is_a_problem (IsADirectoryError)
       ERROR: TestOutputEvals.test_a_record_file_the_process_may_not_read_is_a_problem (PermissionError)
  ```
  Zero mutations left its test module green. Each failure is the traceback class the defect brief recorded for that cell. The mirrored-file reverts (cost_ledger, standards_index, label_sync, validator, gates E) were run against their root test modules only; the payload and manifest pins would fail separately in `test_factory_init`, which is expected and not part of this check.
- Result: PASS

### E2. Out of scope did not move

- Check: `git diff --name-only 661ffc7..HEAD` against the brief's out-of-scope list.
- Evidence:
  ```
  $ git diff --stat 661ffc7..HEAD | tail -1
   40 files changed, 2919 insertions(+), 291 deletions(-)
  $ git diff --name-only 661ffc7..HEAD | grep -v -E '^(tests/|docs/fixes/one-guarded-file-read/)'
  CLAUDE.md cli.py cost_ledger.py dashboard.py docs/adr/0075-...md docs/adr/README.md eval_schema.py
  factory/manifest.json factory/templates/tools/factory/{cli,cost_ledger,factory_config,gates,label_sync,standards_index,validator}.py
  factory_config.py gates.py label_sync.py lint.py standards_index.py sweeps.py validator.py
  $ git diff --name-only 661ffc7..HEAD | grep -E 'backlog|skills/|evals/|protocol|plugin|trigger_eval|knowledge_plane'
  (empty)
  ```
  `docs/backlog.md`, `trigger_eval.py`, `protocol.py`, `knowledge_plane.py`, `skills/**`, `evals/**`, the pipeline protocol and the plugin version are untouched; `cost_ledger.load`'s signature is unchanged.
- Result: PASS

### E3. CLAUDE.md seam line (breakdown C1)

- Check: `grep -n read_file CLAUDE.md`, and the diff.
- Evidence:
  ```
  $ grep -n read_file CLAUDE.md
  48:  (`read_file`, ADR-0075), `factory_config.py` factory.json
  $ git diff --stat 661ffc7..HEAD -- CLAUDE.md
   CLAUDE.md | 3 +-
  ```
  The diff is the one phrase in the "Seam modules" bullet and nothing else.
- Result: PASS

## Failures

none.

## Not verified

- **Green at every one of the 18 commits.** The battery was run at HEAD and on the A2 and B1 archives only; the breakdown's "green at every commit" rule for the other 15 commits was not replayed. HEAD passing and A2/B1 passing do not prove the intermediate commits.
- **Per-reader tests-first order.** Not readable from history because each reader item is a single commit. Replaced by the mutation evidence, which shows the tests fail without the change.
- **`trigger_eval.print_metrics`'s three cells** still raise by design (deferred, a different defect); this is expected by criterion 3, not verified fixed, and is not a failure.
- **`trigger_eval.py` and `charter_replay.py`** were not run as scripts (paid model calls). The matrix tool only imports `trigger_eval` to call `print_metrics` on scratch files.
- **The mutation of detector K's `UnicodeDecodeError` clause** was prepared but not run; K's cell is covered by the matrix replay and by `test_a_committed_index_that_is_not_utf8_is_a_problem` passing at HEAD, but not by a K-specific mutation.
- **Python 3.13 and other versions** were not run; the suite passed on 3.14.6 and 3.12.13 only.
- **A real CI run** was not observed; no push was made, by the run's authorisation.
