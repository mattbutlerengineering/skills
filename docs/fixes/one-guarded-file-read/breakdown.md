---
stage: decompose
run: maintenance:one-guarded-file-read
date: 2026-10-04
assumptions:
  - "The cut was not reviewed live; this run is driven from autorun-brief.md, so the milestone lines, item sizes and grouping are read out of architecture.md's disposition tables and Test plan plus the brief's constraints. A mis-sized row is a note to log at implement time, not a design change."
  - "The CLAUDE.md seam line sits in the close-out group (C1), as the brief's cut constraints require. architecture.md's 'Docs that describe the seam' says it lands in the commit that adds the function; the two differ only in which commit carries one phrase of prose, and nothing in either milestone depends on it. The cli.py module docstring sentence, which the architecture also assigns to the function's commit, stays in A1."
  - "One milestone-one reader per commit, except where readers share a file and a rule: gates.py's three detectors (E, F, K) are one item (A5), lint.py's check_manifest and check_plugin_skills are one item (A8), and the two dashboard text adoptions plus its two hand-fixes are one item (B4). Each grouped reader still gets its own raising-cell tests, written and watched failing before the change."
  - "A5 (gates.py) precedes A6 (factory_config.load) so that load is the SECOND of its two callers to adopt, which is the commit architecture.md names for deleting factory_config.object_problems and its two tests. lint.object_problems has two callers, check_manifest (A8) and check_pi_package (B2), so it is deleted in B2, the later milestone, and milestone one leaves it in place."
  - "The later milestone gets its own net item (B1) because architecture.md's Test plan lists net cells for its readers (empty files, unreadable through gather, null payloads, a directory in place of the file) that are not pinned today."
  - "C2 replays the matrix with the scratch tools the brief names (ogfr/matrix.py and diff_matrix.py under the session scratchpad). They are session-local and may not survive; if they are gone, C2's Accept line falls back to the per-cell tests the earlier items pinned plus the expected totals, and the run notes say so."
---

# Breakdown: one owner for the guarded local-file read

Progress lives in the checkboxes below. Source is `architecture.md` in this
directory (design), `defect.md` (the condition) and `autorun-brief.md` (the
operator's answers), with ADR-0075 recording the decision. Rows carry an item
id, a size class (ADR-0034 vocabulary) and blocking edges; they carry no
work-order id and no tracker reference, because the brief rules out tracker
interaction for this run. These checkboxes are the whole state (ADR-0026).

**One item is one commit.** Implement commits at item boundaries on
`refactor/one-guarded-file-read`.

**The battery is green at every commit.** `python3 -m unittest discover
tests`, `python3 lint.py` (`lint: 0 problem(s)`) and `python3 gates.py &&
python3 gates.py --selftest` (`gates: 0 problem(s)`, `selftest: ok`).

**The payload rule.** Any item that edits a root file in
`factory_init.MIRRORS` (here: `cli.py`, `factory_config.py`, `gates.py`,
`standards_index.py`, `cost_ledger.py`, `label_sync.py`, `validator.py`)
carries, in the same commit, the five-step sequence from architecture.md's
"Import edges and the payload": edit the root file only; delete any
`*.orig` or `*.rej` under `factory/templates/`; run `python3 factory_init.py
update-manifest` (prints `factory-init: 0 problem(s)`); stage the root file,
`factory/templates/tools/factory/<file>` and `factory/manifest.json`
together; confirm detector E (`python3 gates.py`) and `python3 -m unittest
tests.test_factory_init` are green. A deferred manifest is a red battery at
that commit. Such items are marked **mirrored** below.

**The test ordering, which decides the cut.** A1 lands the function and its own
failure matrix (nothing calls it). A2 is the net: tests through each
milestone-one reader's public interface for every cell that does not raise
today and is not already pinned, passing against today's code, changing no
source file. It lands before any reader moves. Then each reader (or small
same-file group) is one item: a test per raising cell, watched failing for
the right reason (the traceback named in the Accept line), then the adoption
or hand fix that turns it green. Tests die only in the item that removes the
function they test. A pinned string other than the two decided pin changes
(A6 and A7) that needs editing to make a move pass means the move is wrong
for that reader: fall back to the hand fix, never edit the pin.

**Unreadable cells** are built with chmod 000 and skipped when
`os.geteuid() == 0`; existing tests that pin unreadable by patching
`Path.read_text` stay as they are. `{err}` is Python's exception text, for
example `[Errno 13] Permission denied: '<path>'` or `'utf-8' codec can't
decode byte 0xff in position 0: invalid start byte`.

## Milestone A: the function exists and every reader the operator saw replayed uses it or is fixed by hand (12 raising cells return problem strings, 2 wordings change, the monthly cap check fails closed)

The function (`cli.read_file`), its net, and the ten replayed readers per the
architecture's "Milestone one" table. Nothing here depends on Milestone B.

- [x] **A1** land `cli.read_file` with its own full failure matrix — size:M, blocked by: —  (mirrored)
  - Accept: `TestReadFile` in tests/test_cli.py, beside `TestReadEvent`, asserts the exact `(value, problem)` pair for each of `str`, `dict`, `list` and `object` against real temp files, for: absent; a directory in place; unreadable (chmod 000, skipped as root); bytes `b"\xff\xfe"` that are not UTF-8; not JSON; empty; a JSON object, array and string; `null`; a number; `true`; `false`. Pairs use the exact strings of the architecture's failure-mode table: `cannot read {shown}: {err}`, `{shown} is not valid JSON: {err}`, `{shown} is not a JSON object`, `{shown} is not a JSON array`, `{shown} is null`. It also covers the eight non-object top levels (`None, [], ["a"], "factory", 5, 0.5, True, False`) under `dict`, asserts `shown` is echoed verbatim (also as a `Path`), and has one unsearchable-parent test asserting only that nothing raises and `value is None`. Each case is written and watched failing (`AttributeError`, no `cli.read_file`) before the function is written, using the architecture's final text with the existence check inside the guard. `cli.py`'s module docstring gains one sentence naming `read_file` among the harness-IO conventions and citing ADR-0075. No caller changes. `cli.py` is mirrored: payload twin and manifest regenerated in the same commit, detector E green.
- [x] **A2** the net for the milestone-one readers, against today's code — size:L, blocked by: A1
  - Accept: tests only; `git diff --stat` for this commit lists no non-test file. Added through each reader's public interface, all passing against unmodified source: `factory_config.load` unreadable, empty, and a broken installed copy reported rather than skipped for the payload copy (tests/test_factory_config.py); `label_sync.load_labels` unreadable, empty, and JSON string and `null` each reading `must be a non-empty JSON array of label entries` (tests/test_label_sync.py); detector E empty, and `{}` reading `E: factory/manifest.json has no files map`; detector F absent for both homes is `[]`, not JSON and empty exact, a not-JSON installed home reported beside a clean payload home; detector K unreadable, empty, and JSON string and `null` each reading `K: docs/standards.json must be a JSON array` (all in tests/test_gates.py); `standards_index.foreign_entries` unreadable, empty, and string and `null` each reading `docs/standards.json is not a JSON array` (tests/test_standards_index.py); `cost_ledger.read` unreadable reading `ledger: cannot read ...` and empty being `([], [])` (tests/test_cost_ledger.py); `lint.check_manifest` not JSON exact (the existing case asserts only the count) and empty, `lint.check_plugin_skills` array and string being `[]` (tests/test_lint.py); `eval_schema.load_case_set` empty (tests/test_eval_schema.py). `python3 -m unittest discover tests` passes on the commit and on its parent with the new tests present.
- [x] **A3** `cost_ledger.load` adopts `read_file`; the monthly cap check and `budget_guard.record` fail closed on a non-UTF-8 ledger — size:M, blocked by: A1, A2  (mirrored)
  - Accept: tests written first and watched failing with `UnicodeDecodeError`: `cost_ledger.load` and `cost_ledger.read` on a ledger beginning `ff fe 00` return `{label}: cannot read docs/factory/costs.jsonl: {err}` (`ledger: ...` through `read`) in tests/test_cost_ledger.py; `cost_report.guard(root)` returns `verdict == PAUSE`, `reason == "cr: unreadable ledger — failing closed"`, `cap is None`, all-zero `totals` and `month_totals`, and `problems == ["ledger: cannot read docs/factory/costs.jsonl: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte"]` (tests/test_cost_report.py); `budget_guard.record` returns exactly one problem `bg: refusing to record <wo>: ledger: cannot read docs/factory/costs.jsonl: <err>` and the ledger's bytes are unchanged (tests/test_budget_guard.py); `work_queue.month_to_date` returns `(0, [<the same ledger: problem>])` (tests/test_work_queue.py). Then `cost_ledger.load` delegates its read to `cli.read_file(path, COST_LEDGER, str)` (`shown` stays `COST_LEDGER` under a `ledger_path` override), imports `cli`, keeps its signature, `(None, [])` for absent and `parse`'s grammar, and its docstring's "one OSError-to-problem translation" becomes "one guarded read (cli.read_file)". The existing pins (tests/test_cost_ledger.py absent, empty, unreadable; tests/test_cost_report.py guard; tests/test_budget_guard.py record; tests/test_work_queue.py month) pass unedited. `cost_ledger.py` is mirrored: payload and manifest regenerated in the same commit, detector E green.
- [x] **A4** `standards_index.foreign_entries` adopts `read_file` — size:S, blocked by: A1, A2  (mirrored)
  - Accept: tests/test_standards_index.py gains a not-UTF-8 case written first and watched failing with `UnicodeDecodeError`, asserting `docs/standards.json is not valid JSON: {err}` from `foreign_entries`, and through `update` that it refuses to write and prefixes `standards-index: `. Then `foreign_entries` reads through `cli.read_file(Path(root) / STANDARDS_PATH, STANDARDS_PATH, list)` with absence still `([], [])`. Existing pins (tests/test_standards_index.py absent, array, not JSON, object, `update`) pass unedited. `standards_index.py` is mirrored: payload and manifest regenerated in the same commit, detector E green.
- [ ] **A5** gates.py: detectors E and F adopt `read_file`, detector K gets its missing arm by hand — size:L, blocked by: A1, A2  (mirrored)
  - Accept: tests in tests/test_gates.py written first and watched failing for the right reason, then the change. E: unreadable fails with `PermissionError` and must read `E: cannot read factory/manifest.json: {err}`; JSON array and JSON string fail with `AttributeError`, and `null`, a number and `true` also raise today, all must read `E: factory/manifest.json is not a JSON object`. F: unreadable fails with `PermissionError` and must read `F: cannot read factory/templates/factory.json: {err}` (and the `.github/factory.json` home), per home. K: bytes that are not UTF-8 fail with `UnicodeDecodeError` and must read `K: docs/standards.json is not valid JSON: {err}`. Then E reads through `cli.read_file(root / "factory" / "manifest.json", "factory/manifest.json", dict)` with absence still `E: missing factory/manifest.json`; F reads through `read_file(path, rel, dict)` for every home, `(None, None)` meaning `continue`, so which homes are checked and the report order stay as pinned at tests/test_gates.py:1453; K adds `except UnicodeDecodeError` to its read's `try`, joining the JSON arm, and keeps its own shape wording (`K: docs/standards.json must be a JSON array`, pinned at tests/test_gates.py:687). All existing gates pins pass unedited, including :1436 and :1131. `gates.py` is mirrored: payload and manifest regenerated in the same commit, detector E green and the selftest still `selftest: ok`.
- [ ] **A6** `factory_config.load` adopts `read_file`; `factory_config.object_problems` dies with its last caller — size:M, blocked by: A1, A2, A5  (mirrored)
  - Accept: the first of the two decided pin changes, edited here and nowhere else: the not-UTF-8 test at tests/test_factory_config.py:134 (inside `TestObjectProblems` today) is edited to expect `config: .github/factory.json is not valid JSON: {err}`, moved into `TestLoad`, watched failing against today's `config: cannot read .github/factory.json: ...`, then `load` walks `artifact_paths` in installed-first order calling `cli.read_file(path, path.relative_to(root).as_posix(), dict)` per home. The first home returning a value or a problem decides the result (a present-but-broken installed copy is reported, never skipped for the payload copy); only `(None, None)` moves to the next home, and after the last home absence is still `config: missing factory.json (<homes>)`. `object_problems` and `import json` are removed from factory_config.py (`grep -n "object_problems" factory_config.py gates.py` finds nothing). The two tests that die with it, `TestObjectProblems.test_an_object_is_clean` (:123) and `test_every_other_json_top_level_is_one_problem` (:127), are deleted, and the commit message says their cells moved to `TestReadFile`'s `dict` rows (A1), with the wiring kept at tests/test_factory_config.py:91 and tests/test_gates.py:1436. All other factory_config pins pass unedited. `factory_config.py` is mirrored: payload and manifest regenerated in the same commit, detector E green.
- [ ] **A7** `label_sync.load_labels` gets its missing arm by hand (the second decided pin change) — size:S, blocked by: A1, A2  (mirrored)
  - Accept: the second of the two decided pin changes, edited here and nowhere else: the test at tests/test_label_sync.py:114 is edited to expect `L: .github/labels.json is not valid JSON: {err}`, watched failing against today's `L: cannot read .github/labels.json: ...`, then `except (OSError, UnicodeDecodeError)` is split in two: `OSError` keeps `L: cannot read {rel}: {err}`, and `UnicodeDecodeError` takes the JSON arm's wording. `null`, `{}`, `[]` and string cells keep `L: .github/labels.json must be a non-empty JSON array of label entries` (pins at tests/test_label_sync.py:125 and tests/test_gates.py:1131 unedited, and A2's null and string cells still green). The comment `# Decode before parse, guarded separately: see factory_config.load.` is replaced by one naming the ADR-0075 wording rule. `label_sync.py` is mirrored: payload and manifest regenerated in the same commit, detector E green.
- [ ] **A8** `lint.check_manifest` adopts `read_file`; `lint.check_plugin_skills` adopts it and discards the problem — size:S, blocked by: A1, A2
  - Accept: tests/test_lint.py gains, written first and watched failing with `PermissionError`: `check_manifest` on an unreadable `plugin.json` returns `cannot read plugin.json: {err}`, and `check_plugin_skills` on an unreadable file and on a not-UTF-8 file (`UnicodeDecodeError` today) returns `[]`. Then both read through `cli.read_file(root / ".claude-plugin" / "plugin.json", "plugin.json", dict)`, `check_plugin_skills` as `data, _ = read_file(...)`, absence staying `missing .claude-plugin/plugin.json` for `check_manifest` and `[]` for `check_plugin_skills`. Pins at tests/test_lint.py:837, :177, :207, :216, :199, :192, :798 pass unedited. `lint.object_problems` stays (check_pi_package still calls it until B2). `lint.py` is not mirrored: no manifest regeneration.
- [ ] **A9** `eval_schema.load_case_set` adopts `read_file` — size:S, blocked by: A1, A2
  - Accept: tests/test_eval_schema.py gains an unreadable case written first and watched failing with `PermissionError`, asserting `cannot read {label}: {err}`. Then `load_case_set` reads through `cli.read_file(path, label, dict)` with absence still `missing {label}`; `eval_schema` gains `import cli` (no cycle: `cli` imports no sibling) and `eval_schema.object_problems` stays because its validators still use it. Pins at tests/test_eval_schema.py:150, :155, :170, :577, :609, :618, :144, :163, :630 pass unedited. `eval_schema.py` is not mirrored and no payload tool imports it, so `python3 -m unittest tests.test_factory_init` stays green with no new `MIRRORS` entry.

## Milestone B: every remaining reader that crashes today stops crashing, with no pinned wording changed (cuttable: nothing in Milestone A depends on it)

The architecture's "Later milestone" tables: two adoptions in lint, the lint
hand-fixes, the dashboard and validator text reads, `cli.read_execution` and
`sweeps.load_payload`. No pinned string changes anywhere in this milestone.
If this milestone is cut, Milestone A still ends with the matrix showing the
four later-milestone cells (`check_pi_package`, `check_backlog`,
`read_execution`, `load_payload`) raising.

- [ ] **B1** the net for the later-milestone readers, against today's code — size:M, blocked by: A2
  - Accept: tests only; no non-test file in the diff; all pass against unmodified source. Added through public interfaces: `lint.check_pi_package` empty (tests/test_lint.py); `check_output_evals` not JSON, and `null` reading `evals/output/idea.json is not a JSON object`; `lint.check_backlog` empty; `dashboard._corrections` and `_backlog` unreadable through `gather`, `dashboard.respond` unreadable (`PAGE` swapped), `respond_post` unreadable (tests/test_dashboard.py); `validator.run_review` unreadable (tests/test_validator.py); `cli.read_execution` unreadable, empty, `null` reading `has no result entry`, and a directory in place of the file (tests/test_cli.py); `sweeps.load_payload` unreadable, empty, and `null` being `(None, [])` (tests/test_sweeps.py).
- [ ] **B2** `lint.check_pi_package` adopts `read_file`; `lint.object_problems` dies with its last caller — size:S, blocked by: A1, B1
  - Accept: a test in tests/test_lint.py written first and watched failing with `PermissionError`: unreadable `package.json` returns `cannot read package.json: {err}`. Then `check_pi_package` reads through `cli.read_file(root / "package.json", "package.json", dict)`, absence staying `missing package.json`. `lint.object_problems` is removed (its callers `check_manifest` in A8 and `check_pi_package` here are both gone; `grep -n "def object_problems" lint.py` finds nothing; it had no direct test, so nothing else dies). Pins at tests/test_lint.py:232, :237, :245, :253, :263, :270, :277 pass unedited. Not mirrored.
- [ ] **B3** lint.py: `check_output_evals` (`problems_for`) and `check_backlog` get their missing arms by hand — size:S, blocked by: A1, B1
  - Accept: tests in tests/test_lint.py written first and watched failing for the right reason, then the change. `problems_for` on an unreadable file (`PermissionError`) and on a directory named `*.json` (`IsADirectoryError`) returns `cannot read evals/output/<name>.json: {err}` via an added `except OSError`; its `null` cell keeps `... is not a JSON object`. `check_backlog` on bytes that are not UTF-8 (`UnicodeDecodeError`) returns `backlog: docs/backlog.md is unreadable: {err}` via `except (OSError, UnicodeDecodeError)`; the pin at tests/test_lint.py:1274 (`is unreadable`) passes unedited. Pins at :1239, :1201, :1215, :1229, :192, :1257, :1266 pass unedited. Not mirrored.
- [ ] **B4** dashboard.py: `_corrections` and `_backlog` adopt `read_file`; `respond` and `respond_post` get their missing arm by hand — size:M, blocked by: A1, B1
  - Accept: tests in tests/test_dashboard.py written first and watched failing with `UnicodeDecodeError`, then the change. `_corrections` on bytes that are not UTF-8 gains the problem `dashboard: cannot read docs/factory/corrections.jsonl: {err}` and returns `{}`; `_backlog` gains `dashboard: cannot read docs/backlog.md: {err}` and returns `None`; each reads through `cli.read_file(root / <CORRECTIONS or BACKLOG>, <same constant>, str)` with absence staying `{}` and `None`. `respond` for `/` returns `500, {"problems": ["dashboard: cannot read dashboard.html: {err}"]}` and `respond_post` returns `500, {"problems": ["dashboard: cannot read docs/backlog.md: {err}"]}`, each by `except (OSError, UnicodeDecodeError)`; their absent-file wording stays the `OSError` text (pins tests/test_dashboard.py:736 and :1086 unedited). Pins at :612, :626, :649, :1018, :1005, :730, :1046, :1062, :1074 pass unedited. Not mirrored.
- [ ] **B5** `validator.run_review` gets its missing arm by hand — size:S, blocked by: A1, B1  (mirrored)
  - Accept: a test in tests/test_validator.py written first and watched failing with `UnicodeDecodeError`: a findings file that is not UTF-8 returns `V: cannot read findings file {findings}: {err}`, via `except (OSError, UnicodeDecodeError)`. The absent-file wording stays the `OSError` text (pin tests/test_validator.py:433 unedited, as is :316). `validator.py` is mirrored: payload and manifest regenerated in the same commit, detector E green.
- [ ] **B6** `cli.read_execution` gets its missing arm by hand — size:S, blocked by: A1, B1  (mirrored)
  - Accept: a test in tests/test_cli.py written first and watched failing with `UnicodeDecodeError`: an execution file that is not UTF-8 returns `execution file {path} is not valid JSON: {err}`, via a separate `except UnicodeDecodeError` clause. It does not adopt `read_file`: an absent file stays the `OSError` message (pin tests/test_cli.py:775) and `null` stays `has no result entry` (B1's cell). Pins at tests/test_cli.py:783, :764, :769, :792, :799, :807 and tests/test_budget_guard.py:505, :558, :598 pass unedited. `cli.py` is mirrored: payload and manifest regenerated in the same commit, detector E green.
- [ ] **B7** `sweeps.load_payload` gets its missing arm by hand — size:S, blocked by: A1, B1
  - Accept: tests in tests/test_sweeps.py written first and watched failing with `UnicodeDecodeError`: bytes that are not UTF-8, from the file and from stdin, return `sweeps: payload is not valid JSON: {err}`, via a separate `except UnicodeDecodeError` clause in the read's `try` that covers the stdin decode too. An absent file stays the `OSError` message (pin tests/test_sweeps.py:876), `null` stays `(None, [])`. Pins at :885, :868 and :984 pass unedited. Not mirrored.

## Milestone C: close-out (the seam is documented and the whole result is shown)

- [ ] **C1** state the new entry point in CLAUDE.md's seam line — size:S, blocked by: A1
  - Accept: in CLAUDE.md's "Seam modules" bullet, the phrase `` `cli.py` external-CLI + harness-IO conventions, `` is replaced by `` `cli.py` external-CLI + harness-IO conventions and the guarded local-file read (`read_file`, ADR-0075), ``; `grep -n "read_file" CLAUDE.md` finds that one line; `python3 lint.py` ends `lint: 0 problem(s)`. No other line of CLAUDE.md changes, and `CONTEXT.md` is not touched (the architecture adds no term).
- [ ] **C2** replay the behaviour matrix and run the full battery — size:S, blocked by: A1, A2, A3, A4, A5, A6, A7, A8, A9, B1, B2, B3, B4, B5, B6, B7, C1
  - Accept: no source change; the checkbox is the record. Quoted in the commit message or Notes: (a) the 144-cell matrix re-recorded against the 661ffc7 baseline ends `cells 144 | identical 123 | fixed 16 | wording changed 2 | still raising 3 | newly raising 0`, the two changed being `factory_config.load / not utf-8` and `label_sync.load_labels / not utf-8`, the three still raising being `trigger_eval.print_metrics`'s array, object and string cells; (b) `git log --oneline refactor/one-guarded-file-read` shows A1 then A2 before the first reader item, and each reader item's tests in the same commit as its change; (c) a grep shows no in-scope adopted reader still types its own `read_text` guard, and the hand-written ones are exactly those named in architecture.md's "Hand-written exceptions"; (d) `python3 -m unittest discover tests` ends `OK`; `python3 lint.py` ends `lint: 0 problem(s)`; `python3 gates.py && python3 gates.py --selftest` ends `gates: 0 problem(s)` then `selftest: ok`; `python3 -m unittest tests.test_factory_init` ends `OK`; (e) `docs/adr/0075-the-guarded-file-read-joins-the-cli-seam.md` is present, indexed in `docs/adr/README.md` as `provisional`, and detector D is green inside `gates: 0 problem(s)`. `trigger_eval.py` and `charter_replay.py` are not run.

## Success-criteria coverage

| # | Brief criterion | Covered by |
|---|---|---|
| 1 | `read_file` exists, three parameters, every failure for every kind | A1 |
| 2 | every in-scope raising cell returns a pinned problem string | A3, A4, A5, A8, A9 (Milestone A); B2, B3, B4, B5, B6, B7 (Milestone B) |
| 3 | exactly two wordings change, none newly raising, only three `print_metrics` cells raise | A6 and A7 (the only pin edits), C2 (a) |
| 4 | non-UTF-8 ledger: cap check and `budget_guard.record` fail closed | A3 |
| 5 | one owner by grep; hand-written exceptions named | A5, A6, A7, B3 to B7 (the hand fixes), C2 (c) |
| 6 | battery green at the last commit | every item's Accept (green at each commit), C2 (d) |
| 7 | payload and manifest level with the root | every item marked mirrored (A1, A3, A4, A5, A6, A7, B5, B6), C2 (d) |
| 8 | test ordering visible in the commit history | A1, A2, then per-reader items; C2 (b) |
| 9 | ADR-0075 exists, indexed, passes the ADR detectors | C2 (e) (the record was written at Architect) |

## Design gaps found

none. Two placement notes, neither a design gap, are under Notes.

## Notes

- **CLAUDE.md placement.** architecture.md's "Docs that describe the seam" says the CLAUDE.md phrase lands "in the commit that adds the function". The cut constraints put it in the close-out group, so it is C1. The `cli.py` docstring sentence stays in A1. If the operator prefers the architecture's placement, move C1's edit into A1; nothing else changes.
- **Replay tools are session-local.** C2 (a) uses `ogfr/matrix.py` and `diff_matrix.py` and the `baseline-661ffc7.json` recording under the session scratchpad named in the brief. If they are gone at implement time, the per-cell tests added by A2 to B7 are the durable evidence and C2 says so rather than inventing a matrix result.
- **Milestone-one-only fallback.** If Milestone B is cut, the matrix after A9 reads `cells 144 | identical 123 | fixed 12 | wording changed 2 | still raising 7 | newly raising 0` (architecture.md, "Replay"), and C2's expected totals change accordingly.
- **`lint.object_problems` timing.** It has two callers; it is deleted in B2, so Milestone A leaves one orphan-free function in place and Milestone B owns its removal.
- **2026-10-04, implement: the net commits carry one non-test line.** A2's and B1's Accept say the commit's `git diff --stat` lists no non-test file. Each item's checkbox edit in this file rides in the item's own commit (one item, one commit), so those two commits list `breakdown.md` beside the test files. No source file is in either: the tests pass against the unmodified readers, which is what the line is for.
