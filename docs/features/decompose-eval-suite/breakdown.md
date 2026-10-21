---
stage: decompose
run: feature:decompose-eval-suite
date: 2026-10-20
assumptions:
  - "No live review of the cut: autorun-brief.md holds the Owner's answers (drive the last step of the Decompose learning loop; suite and graders only, no paid run, no LEDGER change, no optimizer; prepare-and-stop release) and says nothing about milestones or sizing. Milestone boundaries and sizes are the skill's own defaults: each milestone independently demonstrable, one item per sitting, vertical slices where the architecture allows. Milestone 1 is the five fixture cuts (data, no code). Milestone 2 is the grader module. Milestone 3 is the front door. Milestone 4 is the harness suite case. Milestone 5 is the docs and the whole-repo verify."
  - "Test-first ordering follows the repo's TDD rule: each implementation item is blocked by a tests item whose Accept says its cases run and fail against the tree before the implementation lands. The one exception is the cut-versus-grader table item (S12), which characterizes the assembled parts; it substitutes a mutation check for the red run, as architecture.md's Stack section prescribes."
  - "No work-order ids and no tracker markers: the brief rules out work-order mirroring, and detectors C and I scan every markdown file, including the breakdown-shaped cut fixtures. Items carry short labels (S1, S2, ...) at the start of the bold span, the form decompose-lessons used. S3 runs gates.py over the authored cuts for that reason; the cuts and the suite files carry no typed ids and no real paths."
  - "Dual-membership pin placement, derived from ADR-0114 and the module's import order: the pin moves in the item that first adds each import. The grader core (S5) imports knowledge_plane, so the set grows 52 to 53 there. The front door (S14) first imports cli, so it grows 53 to 54 there. decompose_signals is root-only and crosses nothing, so no item edits the pin for it. S18 asserts the final count of 54 pairs. The grader core must not import cli, so that split holds."
  - "Derived, not stated: the grader is built as one module, decompose_grade.py, in the order cuts, core and score, coverage and dependency, accept, size, table, front door, because architecture.md lists the checks as pure functions with the front door last. Grader tests go in tests/test_decompose_grade.py and suite wiring tests in tests/test_decompose_suite.py, as architecture.md's Stack section says."
  - "Skill, plugin and ledger scope, from the brief and ADR-0095: no item edits skills/, .claude-plugin/plugin.json, factory/templates/, LEDGER.md, plugin-evals/records/ or any existing eval definition. The manifest already points experimental.evals at the plugin-evals directory, so wiring the suite is adding plugin-evals/decompose/ and no manifest entry. S18 checks all of this by diff against main."
  - "Size bands are the skill's calibration by sittings: S is a short edit or a data file under about 50 lines, M is a module piece or test file with several cases, L is more than one sitting. No item is L; the cuts item is M because it authors five files that must differ by at most two lines."
  - "No design gap found, so nothing is routed to Architect. Architecture.md fixes the four checks, their exact feedback strings, the score formula, MAX_SPAN, the exit codes, the case layout and the cut rule, so each Accept line is written from them."
---

# Breakdown: A scored, offline-gradable eval suite for Decompose

Progress lives in the checkboxes below. Implement checks items off as their
acceptance criteria are met. Every implementation item is blocked by the
tests item that pins it. Grader tests go in `tests/test_decompose_grade.py`
and suite wiring tests in `tests/test_decompose_suite.py` unless an item says
otherwise, and they run through the public interface with inline fixture
texts or the cut files (architecture.md, Stack). Nothing here invokes
`claude plugin eval`, calls a model or touches the network.

## Milestone 1: the known-good cut and four single-fault bad cuts exist and are pinned

When this milestone is done, `plugin-evals/decompose/fixtures/csv-export/cuts/` holds a good breakdown and four bad ones, each bad cut differing from the good one by at most two lines, none carrying a template slot or a typed id, and gates.py is clean over them.

- [x] **S1 Cut fixture tests** — cases over the five cut files, no grader yet — size:M
  - Accept: the module holds these cases. The five files `good.md`, `bad-coverage.md`, `bad-dangling.md`, `bad-accept.md` and `bad-sized.md` exist under `plugin-evals/decompose/fixtures/csv-export/cuts/`. Each bad cut differs from `good.md` by at most 2 lines, asserted with a line diff. `good.md` holds none of `TEMPLATE.md`'s `<...>` slots outside backticks, asserted against the slots read from the installed Decompose skill template in this repo's `skills/decompose/TEMPLATE.md`. No cut contains a typed-id token (`PRD-`, `WO-`, `ADR-` followed by digits) or a path under `docs/`. Each cut starts with protocol frontmatter naming the decompose stage. Before the files exist the cases fail on a missing file.
  - Blocked by: —
- [x] **S2 Cuts** — author `good.md` and the four bad cuts against the existing csv-export fixture architecture — size:M
  - Accept: the S1 tests pass. `good.md` covers all four architecture components (Export API, Export Scheduler, CSV Generator, Delivery) with Accept lines written against the fixture's own contracts (status codes, retry count, header row, the 5-minute bound), uses TEMPLATE-form `Accept:` and `Blocked by:` sub-bullets, and gives each item a short label. `bad-coverage.md` omits every mention of one component; `bad-dangling.md` names a blocker that is no item; `bad-accept.md` replaces one Accept line with a hedge; `bad-sized.md` makes one item name four components. No file under `evals/` is edited; the architecture and PRD are read in place.
  - Blocked by: S1 Cut fixture tests
- [x] **S3 Gates over the cuts** — run the detectors that scan every markdown file over the authored cuts — size:S
  - Accept: `python3 gates.py` prints `gates: 0 problem(s)` and `python3 lint.py` prints `lint: 0 problem(s)` with the five cuts present. If a detector fires on a cut, the cut is fixed, not the detector. The result is recorded as a dated line in this file's Notes.
  - Blocked by: S2 Cuts

## Milestone 2: a pure grader scores any breakdown against its architecture and explains each defect

When this milestone is done, `decompose_grade.grade(breakdown_text, architecture_text, prd_text)` returns a score, four part fractions and exact feedback lines, and scores the good cut strictly above each bad cut with each bad cut emitting only its own class's line.

- [x] **S4 Grade core tests** — cases for rows, keys, the score formula, the summary line and the no-input failures over inline texts — size:M
  - Accept: the module holds these cases, each asserting exact values. A breakdown with no checkbox rows scores 0.0 with the one line `no-items: breakdown holds no checkbox work items`. An architecture with no `## Components` section or no `###` headings raises `ValueError` whose message reads `holds no components`. The score is the mean of the four part fractions rounded to 3 places, with the dependencies part 1.0 when there are no edges, hand-computed in the test for a two-item inline breakdown. A row with no bold span takes its row text as its key. The same inputs give an equal record twice. An AST check asserts `decompose_grade.py` imports only the standard library, `knowledge_plane` and `decompose_signals`, and none of `socket`, `urllib`, `http`, `subprocess` or a model client, and does not import `cli`. Before the module exists the cases fail on import.
  - Blocked by: —
- [x] **S5 Grade core** — root-level `decompose_grade.py` with `grade`, row and key reading, the score and the summary line — size:M
  - Accept: the S4 tests pass. Rows come from `knowledge_plane.breakdown_rows` and keys from `decompose_signals.item_keys`, with no second checkbox or key grammar. The module's docstring first line states what it does, it is not in `factory_init.MIRRORS`, and no payload tool imports it. `tests/test_dual_membership.py`'s pin gains `(decompose_grade, knowledge_plane)`, its pair-count comment reads 53, and the test passes.
  - Blocked by: S4 Grade core tests
- [ ] **S6 Coverage and dependency tests** — cases for the coverage-miss and dangling-blocked-by checks over inline texts — size:M
  - Accept: the module holds these cases, each asserting exact strings. A component whose name appears in no row block emits `coverage-miss: component "<name>" is named by no item`, matching is case-insensitive, and a component name shorter than 4 characters is not graded. Components are the `###` headings under `## Components` with a trailing parenthetical removed. A `Blocked by:` clause, sub-bullet or inline and case-insensitive, is split on `;` and `,`; `—`, `-`, `none` and an absent clause make no edge; an element that starts at a word boundary with an item key resolves; an element that starts with no key emits `dangling-blocked-by: <item> is blocked by "<element>", which names no item`; an element naming its own item is dangling. The coverage part is covered over total components and the dependencies part resolved over total edges. An item fails a part once however many lines name it. Before the checks exist the cases fail.
  - Blocked by: S5 Grade core
- [ ] **S7 Coverage and dependency checks** — the two checks inside `grade` — size:M
  - Accept: the S6 tests pass and every earlier test still passes. Feedback lines are ordered coverage, then dependency, then by item order. The checks are pure and add no import.
  - Blocked by: S6 Coverage and dependency tests
- [ ] **S8 Accept tests** — cases for the untestable-accept check over inline texts — size:M
  - Accept: the module holds these cases, each asserting exact strings. An item with no `Accept:` sub-bullet, an empty one, one holding an unfilled `<...>` slot outside backticks, or one with fewer than 3 words left after deleting the hedge phrases and every anchor emits `untestable-accept: <item> has no checkable Accept line (empty|placeholder|unanchored)` with the matching reason word. An anchor is a component heading, an interface heading, a backticked span or a digit run found in the given architecture or PRD text. Padding with filler words earns nothing, and a backticked name absent from the fixture earns nothing. A concrete Accept line on an item emits no line. A hedge phrase outside the list plus three other words passes, asserted as a stated known limit in a comment, not hidden. Before the check exists the cases fail.
  - Blocked by: S7 Coverage and dependency checks
- [ ] **S9 Accept check** — the untestable-accept check with the hedge list and anchor builder as module constants and a function — size:M
  - Accept: the S8 tests pass and every earlier test still passes. The hedge list is a named constant and the anchor builder a named function, neither read from configuration or from the Decompose skill text.
  - Blocked by: S8 Accept tests
- [ ] **S10 Size tests** — cases for the mis-sized check over inline texts — size:S
  - Accept: the module holds these cases, each asserting exact strings. An item whose row text plus sub-bullets name more than `MAX_SPAN` (3) distinct architecture components emits `mis-sized: <item> names <n> components (limit 3)`; an item naming exactly 3 emits nothing; an item naming 0 emits nothing. A declared `size:` band, Accept length and clause count change nothing, asserted by two otherwise equal items. Before the check exists the cases fail.
  - Blocked by: S9 Accept check
- [ ] **S11 Size check** — the mis-sized check with `MAX_SPAN` as a named constant — size:S
  - Accept: the S10 tests pass and every earlier test still passes. The component list is the one the coverage check builds, with no second parse of the architecture.
  - Blocked by: S10 Size tests
- [ ] **S12 Good-versus-bad table** — cases running `grade` over the five cut files against the existing csv-export architecture and PRD — size:M
  - Accept: the module holds these cases, with the fixture architecture and PRD read in place from `evals/fixtures/decompose-feature/docs/features/csv-export/`. `good.md` emits no feedback line and scores strictly higher than each bad cut, with the scores asserted. Each bad cut emits exactly its class's line (coverage names the omitted component, dangling names both items, accept names the item, sized names the item and its count) and no other class's line, asserted by exact string. A mutation check replaces each check's body in turn with a no-op and asserts its bad cut's output changes, proving the mutation applied. These cases pass on the assembled S7, S9 and S11, so they carry no red run; the mutation check stands in for it.
  - Blocked by: S3 Gates over the cuts; S11 Size check

## Milestone 3: one command grades a produced breakdown

When this milestone is done, `python3 decompose_grade.py <breakdown.md> <architecture.md> [<prd.md>]` prints the summary line and the defect lines with the documented exit codes, and `python3 factory.py decompose-grade` reaches it.

- [ ] **S13 Front door tests** — cases for `main` over temp files — size:M
  - Accept: the module holds these cases, each asserting exact output lines and exit codes. A good cut prints `decompose-grade: score <s> (coverage <c>, dependencies <d>, accept <a>, sizing <z>)` with three-place figures and exits 0. A bad cut prints the summary then its defect line and exits 1. A wrong argument count, a missing file or an unreadable file exits 2 and scores nothing, with the guarded-read message. An architecture with no components prints `decompose-grade: <path> holds no components` and exits 2, never a vacuous 1.0. The PRD argument is optional and only widens the anchor vocabulary. No file is written. `tests/test_factory_cli.py` is run and fails on the missing `decompose-grade` verb. Before `main` exists the cases fail.
  - Blocked by: S12 Good-versus-bad table
- [ ] **S14 Front door** — `main`, the `factory.py` VERBS row `decompose-grade` and the cli import — size:S
  - Accept: the S13 tests pass and every earlier test still passes. Files are read through `cli.read_file` and output goes through `cli.report`. `factory.py`'s VERBS table gains `"decompose-grade": ("decompose_grade", "argv")` beside the decompose-signals row and `tests/test_factory_cli.py` passes. `tests/test_dual_membership.py`'s pin gains `(decompose_grade, cli)`, its pair-count comment reads 54, and the test passes.
  - Blocked by: S13 Front door tests

## Milestone 4: the harness suite case is authored and statically checked

When this milestone is done, `plugin-evals/decompose/csv-export-cut/` is a well-formed case in the existing layout, selected by the `decompose` tag, and no run has been made.

- [ ] **S15 Suite wiring tests** — static cases over the case files, the manifest and the scaffold, in `tests/test_decompose_suite.py` — size:M
  - Accept: the module holds these cases. `.claude-plugin/plugin.json`'s `experimental.evals` equals `plugin-evals` and the file is unchanged against main. The case directory holds `case.yaml`, `prompt.md`, `scaffold.sh` and `graders/`, with `case.yaml` carrying schema version 1.1, a name and `context.scaffold_script`. Every decompose case carries the `decompose` tag, read through `tests/test_plugin_eval_tags.case_tags` and not a second parser. The grader files are `skill-fired`, `breakdown-exists`, `has-rows`, `covers-every-component`, `blocked-by-names-real-items`, `accept-is-checkable` and `items-are-one-sitting`, each with a `type:` in the harness's documented set (`regex`, `tool_order`, `tool_used`, `file_exists`, `llm`, `baseline`) and none a code-running type. The scaffold heredocs for the fixture `prd.md` and `architecture.md` each equal the file under `evals/fixtures/decompose-feature/docs/features/csv-export/`. No file under `evals/`, no other `plugin-evals/` suite, `plugin-evals/records/` and `LEDGER.md` differs from main. Before the case exists the cases fail.
  - Blocked by: S14 Front door
- [ ] **S16 Suite case** — author the `csv-export-cut` case in the layout of the existing suites; never run — size:M
  - Accept: the S15 tests pass. `prompt.md` has frontmatter `description`, `tags: [decompose]`, `max_turns`, `timeout_seconds` and `allowed_tools`, and supplies the interview answers up front. `scaffold.sh` seeds `docs/features/csv-export/prd.md` and `architecture.md` from heredocs. The four `llm` graders each name one defect class, and `has-rows` is a `regex` with flags `m` over the produced file. No script or tool grant in the case runs `decompose_grade.py`. `plugin-evals/records/` gains no file and nothing invoked `claude plugin eval`.
  - Blocked by: S15 Suite wiring tests

## Milestone 5: the docs name the tool and the whole change verifies

- [ ] **S17 Docs** — the CLAUDE.md "on demand, free" bullet beside `decompose_signals.py` — size:S
  - Accept: CLAUDE.md names `python3 decompose_grade.py` as free, offline, outside every gate, making no model or network call, taking a produced breakdown and its architecture, and says it is calibrated to fixture-spelled breakdowns and is not a retroactive audit of shipped runs. It mentions the harness suite as authored and never run, with no LEDGER change. It contains no work-order token or sample id that detectors C and I would scan, and `python3 kb.py drift` still prints `drift: 0 problem(s)`.
  - Blocked by: S16 Suite case
- [ ] **S18 Whole-repo verify** — the four CI checks and the scope checks over the finished change — size:S
  - Accept: `python3 run_tests.py` exits 0; `python3 lint.py` prints `lint: 0 problem(s)`; `python3 kb.py drift` prints `drift: 0 problem(s)`; `python3 gates.py` and `python3 gates.py --selftest` print `gates: 0 problem(s)`. `tests/test_dual_membership.py` passes with 54 pairs. `python3 one_owner.py` still prints `one-owner: 9 problem(s)` with none naming `decompose_grade`. `git diff --name-only main...HEAD` shows no change under `skills/`, `.claude-plugin/`, `factory/templates/` or `evals/`, no change to `LEDGER.md` or `factory_init.MIRRORS`, no new file in `plugin-evals/records/`, and no edit to any existing `plugin-evals/` suite. `python3 decompose_grade.py` on the good cut exits 0 and on each bad cut exits 1.
  - Blocked by: S17 Docs

## Design gaps found

none.

## Notes

- 2026-10-20 S3: with the five cuts present, `python3 gates.py` printed `gates: 0 problem(s)` and `python3 lint.py` printed `lint: 0 problem(s) across 34 skills`; no detector fired, no cut changed.
