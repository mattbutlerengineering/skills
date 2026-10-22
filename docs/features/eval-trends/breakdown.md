---
stage: decompose
run: feature:eval-trends
date: 2026-10-21
assumptions:
  - "No live review of the cut: autorun-brief.md holds the Owner's answers (drive issue 1027; research note plus a read-only, free trend tool; no paid run, no model call in the tool or its tests, no LEDGER change; prepare-and-stop release) and says nothing about milestones or sizing. Milestone boundaries and size bands are the skill's own defaults: each milestone independently demonstrable, one item per sitting, vertical slices where the architecture allows. M1 is the name inverse in eval_schema. M2 is the pure statistics and classification core. M3 is one adapter per surface. M4 is render, the front door and the factory verb. M5 is the honesty checks on today's records. M6 is the research note, in its own milestone because it touches no code and can land in any order after M1. M7 is the docs and the whole-repo verify."
  - "Test-first ordering follows the repo TDD rule: each implementation item is blocked by a tests item whose Accept says its cases run and fail against the tree before the implementation lands. The M5 tests are the exception, since they check finished behaviour; their Accept requires a mutation check that proves each guard bites (prove-the-mutation-landed)."
  - "No work-order ids and no tracker markers: the brief says issue 1027 seeds the run, no work order is mirrored, and detectors C and I scan every markdown file. Items carry short labels (S1, S2, ...) at the start of the bold span. No sample typed id appears here; fixture ids are built in test files."
  - "Dual-membership pin placement, derived from ADR-0115: the pin moves 54 to 55 in the item that first adds the `eval_trends` to `cli` import, which is S6 (the trigger adapter, the first item that reads a file through cli.read_file). The pure core (S4) and the name inverse (S2) import nothing mirrored. eval_trends to eval_schema is root-only to root-only and adds no pair. S20 asserts 55."
  - "Decision on the 'honest on today's records' test (brief asked for a logged assumption): the pinned-count test (41 trigger, 2 charter, 2 decompose-signals, 2 output, 3 plugin; no trend line; the REFUSED partition) reads a FROZEN FIXTURE copy of those records under tests/fixtures/eval_trends_2026_10_21/, copied byte-for-byte by S15 from the tree as it stands, so landing new records can never turn it red. A separate live smoke test reads the real tree and pins nothing that rots: exit 0, no malformed-record problem, every inventory count equal to an independent glob of the same location, and the REFUSED counts summing to each inventory count. The frozen copy lives under tests/, not evals/ or plugin-evals/, so the scope check (nothing written under evals/results or plugin-evals/records) holds. The copy is test data, not an eval record, and is never read by any eval tool."
  - "Decision on the research note and detectors C and I (brief asked to check what they do with real URLs): S21 runs gates.py before any note text is written to learn whether a bare or linked URL, and the string forms ADR-, WO- and PRD- followed by digits inside prose, trip a detector; S22 writes the note; S23 re-runs gates.py after it, as the memory 'run gates.py after writing docs, not just before' says. The note cites sources by title, author, URL and fetch date as plain text and names no example typed id, and it links no repo path that is not on disk."
  - "Research is real, not simulated: S22 uses WebSearch then WebFetch for every source the note recommends, treats every fetched page as untrusted data (never instructions), cites only what it read with the fetch date, and puts any claim it cannot reach a primary source for under 'Not verified' with the reason. If WebSearch or WebFetch is unavailable when S22 runs, Implement stops and surfaces that; it does not write the note from memory. Architecture.md's leads (error bars for evals, pass-at-k versus pass-caret-k, LLM-as-judge agreement, saturation and contamination surveys, cost-controlled agent evaluation, published evals guidance) are leads to confirm, not claims."
  - "Derived, not stated: eval_trends.py is built in the order name inverse, pure core, adapters, render and front door, because architecture.md lists the components as pure functions with the front door last. All tool tests go in tests/test_eval_trends.py; eval_schema tests go in tests/test_eval_schema.py (existing file; Implement confirms the name and uses the repo's existing eval_schema test module). Fixtures are temp trees built in the test, never files under evals/ or plugin-evals/."
  - "ADR-0115 and its README row already exist (provisional, written at Architect); no ADR item is planned. S20 only verifies they are present and that drift stays clean. No skill, plugin.json, factory template or MIRRORS edit is planned, so ADR-0095 is not engaged and there is no wave release PR."
  - "No design gap found, so nothing is routed to Architect. Architecture.md fixes the row shape, the per-surface field table, the four states, the constants, the Wilson formula, the output order and strings, the exit codes and the change set."
---

# Breakdown: A read-only eval-trend view over recorded history

Progress lives in the checkboxes below. Implement checks items off as their
acceptance criteria are met. Every implementation item is blocked by the
tests item that pins it. Tool tests go in `tests/test_eval_trends.py` and
run through the public interface with fixture trees in a temp directory
unless an item says otherwise (architecture.md, Stack). No test or tool
calls a model, `claude` or the network.

## Milestone 1: the results naming grammar has an inverse with one owner

When this milestone is done, `eval_schema.parse_results_stem` turns any
results file stem or output directory name back into its parts, and a test
pins it against `results_path` for every kind.

- [x] **S1 Name inverse tests** — cases for `parse_results_stem` in the eval_schema test module — size:S
  - Accept: the module holds these cases. For every kind `results_path` can build (each harness token, charter, decompose-signals, decompose, with and without a `-N` suffix), `parse_results_stem(path.stem)` returns the `(kind, harness, date, suffix, slug)` the path was built from, asserted by looping over the same kind list the test uses to build paths. An output directory name with a slug parses to its slug and date. A stem that fits no grammar (empty, a bare date, an unknown harness token, a trailing `-0`) returns `None`. Before the function exists the cases fail on the missing attribute.
  - Blocked by: —
- [x] **S2 Name inverse** — `parse_results_stem` in `eval_schema.py` built from `_HARNESS` and `_SUFFIX` — size:S
  - Accept: the S1 tests pass and every existing eval_schema test still passes. The function is pure and builds its pattern from the module's own `_HARNESS` and `_SUFFIX` pieces; a count of the harness token list in the module shows it appears once. `eval_schema.py` still imports only the standard library and is not in `factory_init.MIRRORS`.
  - Blocked by: S1 Name inverse tests

## Milestone 2: the arithmetic and the four states are pure and hand-checkable

When this milestone is done, `wilson`, `day_interval`, `cost_per_pass` and `classify` give correct values and states over fixture rows with no file read.

- [x] **S3 Core tests** — cases for the constants, `wilson`, `day_interval`, `cost_per_pass` and `classify` over fixture rows — size:M
  - Accept: the module holds these cases with expected values worked by hand in the test, none copied from the tool. `MIN_CASES` is 30 and `MIN_DAYS` is 2. `wilson` gives the architecture's checkpoints for a 50 percent rate (n=10 0.24 to 0.76, n=30 0.33 to 0.67, n=47 0.36 to 0.64, to the printed precision) and the edge cases 0 of n and n of n stay inside 0 to 1. `day_interval` is the hull `[min lower, max upper]` of a day's records. `cost_per_pass` is summed cost over summed passed cases to four decimals, and one record with no cost makes it refused. `classify` gives each record exactly one of `single` (with the `case sets differ` or `different suites` sub-reason), `same-day`, `small`, `trend`, and the state counts of a mixed fixture sum to its record count; a surface with fewer than 2 records is `too few records`; a null model equals only a null model; two records on one day in one group never pair with each other. Before the functions exist the cases fail.
  - Blocked by: S2 Name inverse
- [x] **S4 Core** — `eval_trends.py` with the constants, `wilson`, `day_interval`, `cost_per_pass` and `classify` — size:M
  - Accept: the S3 tests pass. The functions are pure over a list of row dicts and return new values without mutating their input. The module imports the standard library (`hashlib`, `math`, `pathlib`, `re`) and `eval_schema` only, so `tests/test_dual_membership.py` passes unchanged. The case-set fingerprint is the first 8 hex of a sha256 of the sorted tuples, and groups are keyed on the full sorted tuple list. The module docstring's first line states what it does.
  - Blocked by: S3 Core tests

## Milestone 3: each surface reads into the same row, or into a labelled problem

When this milestone is done, `load_rows` turns a fixture tree of every surface into rows, and each malformed record into `eval-trends: <path> <reason>`, with decompose-signals kept inventory-only.

- [x] **S5 Adapter tests** — cases for `load_rows` per surface, plus the pin test that goes red on purpose — size:L
  - Accept: the module holds these cases over temp trees, one block per surface, expected rows computed by hand in the test. Trigger: row from `date`, `len(results)`, count of `pass`, suite (harness, model, runs_per_query, threshold) and the (id, expected, query) case set; a summary that disagrees with its own `results`, an `errors` above 0, an unparseable name, a non-object file and a missing needed field each yield `eval-trends: <path> <reason>` and no row. Charter: arm, model and charters map suite, (id, role) set, hits are verdict `sensitive`. Output: directory-name date and slug, `expectations` count and `passed` count, text set. Plugin: `startedAt` UTC day, `casesTotal` and `casesPassed`, suite from tagFilters (sorted), ablation, modelOverride, judgeModel, threshold, case set from name, promptMarkdown and grader markdown, `costUsd`; `partial: true` is a problem. Decompose-signals: a row with surface and day and no n. An absent location is an empty surface, not an error. Files are listed in sorted path order. A source grep test is not here. A separate test asserts `tests/test_dual_membership.py`'s expected set contains `(eval_trends, cli)` and its count is 55, and it is red now. Before `load_rows` exists every adapter case fails.
  - Blocked by: S4 Core
- [x] **S6 Trigger adapter and the cli import** — `load_rows` for trigger records, reading through `cli.read_file`, plus the dual-membership pin move — size:M
  - Accept: the S5 trigger cases pass. Files are read through `cli.read_file` with no retyped guarded-read logic. `tests/test_dual_membership.py`'s pin gains `(eval_trends, cli)`, its pair-count comment reads 55 and names ADR-0115, and the S5 pin test and the dual-membership test pass.
  - Blocked by: S5 Adapter tests
- [x] **S7 Charter adapter** — the charter surface reader — size:S
  - Accept: the S5 charter cases pass and the trigger cases and the pin test still pass. The metric is labelled `sensitive`, never a pass rate.
  - Blocked by: S6 Trigger adapter and the cli import
- [x] **S8 Output-gradings adapter** — the output surface reader — size:S
  - Accept: the S5 output cases pass and every earlier case still passes. The slug is taken through `parse_results_stem` on the directory name, with no second regex in `eval_trends.py` (a source grep for `re.compile` of a results-name pattern finds none).
  - Blocked by: S7 Charter adapter
- [x] **S9 Plugin-records adapter** — the plugin surface reader — size:M
  - Accept: the S5 plugin cases pass and every earlier case still passes. `costUsd` is read as recorded, never summed across fields, decomposed or estimated.
  - Blocked by: S8 Output-gradings adapter
- [x] **S10 Decompose-signals inventory-only** — the decompose-signals surface reader that yields inventory rows and no case set — size:S
  - Accept: the S5 decompose-signals cases pass and every earlier case still passes. Its rows carry no n, no suite and no case set, and `classify` is never given them: a test shows the surface can never produce a trend, rerun spread or cost line.
  - Blocked by: S9 Plugin-records adapter

## Milestone 4: one command prints the whole view, exactly as the architecture says

When this milestone is done, `python3 eval_trends.py` and `python3 factory.py eval-trends` print the header, inventory, trend, spread, cost and REFUSED lines, the not-computed line and the problem summary, and exit 0, 1 or 2 as specified.

- [x] **S11 Render and front-door tests** — cases for `render` and `main` over fixture trees, one exact string per output line kind — size:L
  - Accept: the module holds these cases, with every number recomputed independently from the fixture files in the test. The demo, as written in the PRD: a fixture with one surface holding a comparable pair (same suite, same case set, two days, 30 or more cases, plugin `costUsd` present) and one surface without prints the inventory lines, a trend line and a `cost per pass` line for the first, and `eval-trends: REFUSED <surface>: too few records: need 2, have <m>; no trend claim` for the second. One fixture and one exact-string assertion per other state: different suites, case sets differ, only same-day records, too few cases (need 30), `cost: REFUSED cost field absent from <k> of <m> record(s); no trend claim`, and `eval-trends: REFUSED decompose-signals: not an eval run: records re-measure one git history; no trend claim`. The header line, the `not computed from any record` line naming the research note path, and the order of lines are asserted exactly. Both verdict wordings (`intervals do not overlap`, `intervals overlap: not distinguishable (descriptive, not a significance test)`) appear for a separating and an overlapping fixture, and the words improved and regressed never appear in any output. Same-day reruns alone give a rerun spread line and a same-day refusal and no trend line; reruns beside another day are compared per day by hull. Every number line ends with the file names it came from. REFUSED counts sum to the inventory count of each surface. A malformed record per surface prints its `eval-trends: <path> <reason>` problem before the summary, is not counted in the inventory, and `main` returns 1; usage errors return 2; a refusal alone returns 0. A byte-for-byte snapshot of the whole temp tree before and after `main` is identical. A source grep finds no `open(` with a write mode, `write_text`, `.mkdir`, `os.replace`, `claude`, `socket` or `urllib` in `eval_trends.py`. Before `render` and `main` exist the cases fail.
  - Blocked by: S10 Decompose-signals inventory-only
- [x] **S12 Render and front door** — `render` and `main(argv)` as architecture.md's Interfaces and contracts fixes them — size:L
  - Accept: the S11 tests pass and every earlier test still passes. `main` takes no argument or one repo-root path, sends every line and problem through `cli.report`, and returns 0, 1 or 2 as S11 asserts. The module is runnable as a script and prints its output on the fixture tree.
  - Blocked by: S11 Render and front-door tests
- [x] **S13 Factory verb** — the `eval-trends` row in `factory.py`'s VERBS table — size:S
  - Accept: `("eval_trends", "argv")` is registered under `eval-trends` in sorted position, `tests/test_factory_cli.py` passes with the verb present and the module existing, and `python3 factory.py eval-trends <fixture root>` prints the same output as the module run directly. Before the row is added, that factory test fails on the module with no row.
  - Blocked by: S12 Render and front door

## Milestone 5: the tool is honest on the records the repo holds today

When this milestone is done, the tool's output on a frozen copy of today's records is pinned, and a separate live test checks the real tree without pinning anything that rots.

- [x] **S14 Frozen-record fixture** — copy today's record files into `tests/fixtures/eval_trends_2026_10_21/` byte-for-byte — size:S
  - Accept: the fixture holds the five locations' files exactly as the tree has them (41 trigger, 2 charter, 2 output grading directories, 3 plugin records, 2 decompose-signals), with the same relative layout, and `cmp` of each copy against its source shows no difference. Nothing under `evals/` or `plugin-evals/` is written or changed. Each fixture file name still parses under `parse_results_stem`.
  - Blocked by: S13 Factory verb
- [x] **S15 Honest-on-today's-records tests** — the frozen-fixture test and the live smoke test — size:M
  - Accept: the frozen test runs `main` on the fixture root and asserts exit 0, the inventory counts 41, 2, 2, 2 and 3 (trigger, charter, output, plugin, decompose-signals as the architecture orders them), no line containing `trend set`, a REFUSED line for every surface with the counts summing to each inventory count, the 185-case same-day pair showing passed 159 and 163 as a rerun spread, and the `not computed` line. The live smoke test runs `main` on the repository root and asserts only: exit 0 with no malformed-record problem, each inventory count equal to an independent glob of its location, and the REFUSED counts summing to each inventory count; it pins no literal count and no absence of a trend line, and its docstring says why. A mutation check is run and logged in Notes: making `classify` return `trend` for a same-day group, and then dropping one REFUSED state from `render`, each turns a named frozen-fixture case red, restored afterwards with `git diff` on the tool clean.
  - Blocked by: S14 Frozen-record fixture

## Milestone 6: the research note is sourced, honest about what it could not verify, and checked

When this milestone is done, `docs/research/eval-quality-metrics-2026-10-21.md` exists with real cited sources, a failure mode per metric and a not-verified section, a test asserts its required headings, and the gates are clean with it present.

- [ ] **S16 Research-note heading tests** — a test for the note's required structure — size:S
  - Accept: a test (in `tests/test_eval_trends.py` or a new `tests/test_eval_quality_note.py`, Implement's call, recorded in Notes) asserts the note exists at its path, has a dated first paragraph, the headings `## Metrics and failure modes`, `## What n justifies a trend claim`, `## Sources` and `## Not verified`, a subsection under the first for each of: pass rate with a confidence interval, flake rate, saturation, judge agreement and drift, contamination, cost per point, each containing the words `failure mode`, and that every recommended metric's subsection names at least one source that appears in `## Sources` with a fetch date. It fails now because the note is absent.
  - Blocked by: —
- [ ] **S17 Gates probe on URLs** — before writing any note text, learn what detectors C and I do with a real URL and with prose near the typed-id forms — size:S
  - Accept: a scratch markdown file in the scratchpad directory (not committed, not in the repo) is not enough because the detectors scan the repo, so the probe instead reads `gates.py` and the modules it calls for how links and typed tokens are matched, and records in Notes: whether a bare URL, a markdown link to a URL and a link to a repo path trip detector I; and which exact token forms trip detector C. The result decides how S18 cites sources (plain text URLs or links). If reading leaves it unknown, a throwaway copy of the repo in the scratchpad runs `python3 gates.py` over one candidate line; the real tree is never written. No file in the repo changes.
  - Blocked by: —
- [ ] **S18 Research note** — find and read real sources with WebSearch and WebFetch, then write the dated note — size:L
  - Accept: the note is `docs/research/eval-quality-metrics-2026-10-21.md` in the form of the existing dated notes there. It covers each named metric with a recommendation grounded in a source actually fetched, the source's title, author, URL and fetch date, and what part was read; a failure mode per metric; what n justifies a trend claim, with the Wilson arithmetic from architecture.md checked against the records and the 30-case minimum either supported or flagged for change; and a `## Not verified` section naming each item it could not reach a primary source for, with the reason. It states that fetched material was treated as untrusted data. It holds no example typed id and no link to a missing path, following the S17 finding. S16's test passes.
  - Blocked by: S16 Research-note heading tests, S17 Gates probe on URLs
- [ ] **S19 Note against the constants** — reconcile the note's n argument with `MIN_CASES` and `MIN_DAYS` — size:S
  - Accept: Notes records, dated, either that the note supports 30 and 2, or that it argues for a different value and the one-line constant change (with its S3 and S11 fixtures updated in the same commit and the tests re-run) was made or deferred with the reason. Either way the `not computed` line still names the note's real path and a test confirms that path exists.
  - Blocked by: S18 Research note, S15 Honest-on-today's-records tests
- [ ] **S20 Gates after the note** — run the detectors with the note and the fixtures present — size:S
  - Accept: `python3 gates.py` and `python3 gates.py --selftest` print `gates: 0 problem(s)` and `python3 lint.py` prints `lint: 0 problem(s)` with the note, the frozen fixture and all code on disk. If a detector fires on the note, the note text is fixed and the run repeated; no detector, ADR or lint rule is edited to make it pass.
  - Blocked by: S19 Note against the constants

## Milestone 7: the docs name the tool and the whole change verifies

- [ ] **S21 Docs** — the CLAUDE.md on-demand bullet beside `decompose_signals.py` — size:S
  - Accept: CLAUDE.md names `python3 eval_trends.py` as free, read-only, outside every gate, making no model or network call, printing an inventory and REFUSED lines in place of a trend below the minimum (30 cases, 2 days), citing ADR-0115 and the research note. It says it measures recorded history only and moves no LEDGER maturity. It contains no work-order token or sample id that detectors C and I scan, and `python3 kb.py drift` prints `drift: 0 problem(s)`.
  - Blocked by: S20 Gates after the note
- [ ] **S22 Whole-repo verify and scope checks** — the four CI checks and the scope checks over the finished change — size:S
  - Accept: `python3 run_tests.py` exits 0; `python3 lint.py` prints `lint: 0 problem(s)`; `python3 kb.py drift` prints `drift: 0 problem(s)`; `python3 gates.py` and `python3 gates.py --selftest` print `gates: 0 problem(s)`. `tests/test_dual_membership.py` passes with 55 pairs. ADR-0115 and its README row are present. `python3 one_owner.py` names no finding in `eval_trends`. A diff of the change from this run's first implement commit (not `main...HEAD` if the local main ref is behind, per the earlier decompose runs) shows no change under `.claude-plugin/`, `factory/templates/`, `evals/`, `plugin-evals/` or `skills/`, none to `LEDGER.md` or `factory_init.MIRRORS`, and no file written under `evals/results` or `plugin-evals/records`. `python3 eval_trends.py` on the real tree exits 0. The change set equals architecture.md's list plus the frozen fixture and the research note.
  - Blocked by: S21 Docs

## Design gaps found

none.

## Notes


- 2026-10-21 (Implement) Deviation, test files: the tool tests are split
  over four files instead of one, to keep each under the size limit and to
  share one fixture builder: `tests/test_eval_trends.py` (core and
  adapters), `tests/test_eval_trends_render.py` (render, main, factory
  verb, read-only), `tests/test_eval_trends_records.py` (S15), and the
  builder `tests/eval_trends_fixture.py`. The eval_schema cases are in the
  existing `tests/test_eval_schema.py` (`TestParseResultsStem`).
- 2026-10-21 (Implement) Deviation, commit grouping: S6 to S9 landed in
  one commit (the S5 cases drove each reader in turn, so there was no
  honest RED between them); S1/S2 and S3/S4 checkboxes were checked in the
  commit after their code.
- 2026-10-21 (Implement) Clarification, S15 counts: the S15 criterion lists
  "41, 2, 2, 2 and 3" but its own parenthesis and S14 give trigger 41,
  charter 2, output 2, plugin 3, decompose-signals 2. The frozen test pins
  the latter (printed in the architecture's order: trigger, charter,
  output, plugin, decompose-signals).
- 2026-10-21 (Implement) Measured, against architecture.md's prediction:
  the architecture expected the 4-case 07-03 and 07-05 trigger reruns to
  classify as `small`. They do not: the trigger suite key includes
  `runs_per_query`, which is 1 on 07-03 and 3 on 07-05 (and 5 for others),
  so those records are different suites by the architecture's own suite
  key, and the tool prints `case sets differ` for 38 trigger records,
  `different suites` for 1 and `only same-day` for the 185-case pair. No
  group on today's records reaches `small` or `trend`. The architecture
  said the exact partition is the tool's to compute; this is that
  computation, not a design gap.
- 2026-10-21 (Implement) S15 mutation check (prove-the-mutation-landed;
  each mutation shown applied by `git diff --stat` reading 1 insertion, 1
  deletion, then reverted with `git checkout eval_trends.py`, `git diff`
  clean):
  1. `_group_state` same-day test changed to `< 0` (so a same-day group is
     never `same-day`): 9 cases went red, among them
     `TestFrozenRecords.test_no_trend_line_on_these_records`,
     `test_the_185_case_same_day_pair_is_a_rerun_spread` and
     `TestClassify.test_two_records_on_one_day_never_pair_with_each_other`.
  2. the `case sets differ` REFUSED line made unreachable in
     `_refused_lines`: 7 cases went red, among them
     `TestFrozenRecords.test_the_refused_lines_for_the_small_surfaces_exactly`,
     `TestFrozenRecords.test_every_surface_is_refused_and_the_counts_sum_to_the_inventory`
     and `TestRefusalStates.test_case_sets_differ`.
