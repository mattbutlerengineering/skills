---
stage: architect
run: feature:decompose-eval-suite
date: 2026-10-20
ux: skipped — CLI text output, eval fixtures and grader code only; no screens or flows (per prd.md).
assumptions:
  - "No live interview: every PRD open question was settled from the code, `claude plugin eval --help` and read-only measurements on this clone, taking the recommended default each time. ADR-0114 (provisional) is written because the dual-membership pin edges and the two-scorer split outlive the commit; every other choice changes in one commit. Nothing is surfaced: nothing here is expensive to reverse without an ADR."
  - "Harness fact (read from `claude plugin eval --help` and `claude plugin eval init` output, 2.1.296 as in ADR-0081; no eval was run): a grader file's `type:` is one of `regex | tool_order | tool_used | file_exists | llm | baseline`. There is no command, script or Python grader, so a stdlib grader cannot run inside a plugin-eval case. Of those types only `regex` can read a produced file (`target: { source: file, path: ... }`, as `plugin-evals/implement/one-item-test-first/graders/item-checked.md` does), and a regex cannot compute coverage, resolve a dependency or count components. The honest design is two scorers that do not pretend to be one: the suite's case uses harness graders on the model-run side, and a standalone offline module scores a produced breakdown.md; the tests exercise the module. Nothing in this run compares the two scorers, because that needs a paid run (follow-up, below)."
  - "Recommended default taken (no plugin.json edit at all): `.claude-plugin/plugin.json` already says `\"experimental\": {\"evals\": \"plugin-evals\"}`, a directory, and the harness finds a case by `plugin-evals/<skill>/<case>/prompt.md`. The new suite is picked up by adding `plugin-evals/decompose/`; the manifest needs no entry, so the brief's phrase 'manifest `experimental.evals`' is satisfied by the existing value. ADR-0095 therefore never comes into play: no edit to the file, version field or otherwise, is allowed or needed on this branch. The PRD's wiring criterion is tested statically by asserting the manifest value is `plugin-evals`, every decompose case is tagged `decompose` and has a case.yaml, prompt.md and graders/. Measured: `git diff main -- .claude-plugin` is empty on this branch; `factory_init.py` hashes plugin.json only for the manifest's plugin name and version, and nothing under plugin-evals/ or the new root module is in `factory_init.MIRRORS`, so no `update-manifest` run is involved."
  - "Recommended default taken (parser reuse, PRD open question 2): rows come from `knowledge_plane.breakdown_rows` (the shared checkbox-row walk; each row record carries `block`, the row plus its Accept and Blocked by sub-bullets) and item keys from `decompose_signals.item_keys` (the one owner of the label/bold-title key grammar). Measured 2026-10-20: `knowledge_plane.parse_row` reads blockers from a lowercase `blocked by:` clause holding WO tokens only (`BLOCKED_BY` is case-sensitive and `WO_TOKEN` only), so on a TEMPLATE-form breakdown row (`  - Blocked by: S1 Lesson operation tests`) it returns `blockers: []` and `title: None`; it cannot see a dangling label. 126 of 324 repo rows with an Accept sub-bullet carry an inline lowercase blocked-by (WO form); 84 carry the TEMPLATE sub-bullet form. So Accept and Blocked by clauses are parsed from `row['block']` in the new module (a clause grammar nobody else owns); the checkbox grammar, size and keys are not re-implemented. `protocol.py` and `work_queue.py` have no breakdown-body parser to reuse (work_queue reads WO-form edges through `knowledge_plane`)."
  - "Recommended default taken (the mis-sized rule, PRD open question 3): over-wide only. An item is mis-sized when its row plus its sub-bullets name more than 3 distinct architecture components (`MAX_SPAN`, a named constant). Measured 2026-10-20 over the 17 feature runs holding both an architecture.md with three or more `###` components and a breakdown.md (205 rows): rows naming 0, 1, 2, 3, 5 components by verbatim heading = 128, 50, 21, 5, 1; a limit of 3 flags 1 of 205 real rows (0.5%), a limit of 2 would flag 6 (2.9%) and would punish the thin end-to-end slice the Decompose skill's Rules prefer. Rejected as a size signal: Accept clause count or word count. Measured per declared band over 324 rows, Accept sentences have median S 4, M 6, L 8 and p90 S 8, M 15, L 37; words median S 65, M 107, L 165.5 (p90 149, 274, 803). The bands overlap too much to calibrate a cap, and a cap would reward short Accept lines. The declared `size:` band is not graded: the Decompose TEMPLATE has no `size:` field (13 of 324 rows have none), so it is not a property of a draft."
  - "Recommended default taken (padded and split items, PRD open question 6; stated limits, not solved): untestable Accept is judged on what an Accept line is anchored to, not on length. A line is untestable when it is empty or absent, holds an unfilled `<...>` slot, or, after deleting known hedge phrases (`works correctly`, `handles errors appropriately`, `is complete`, ...) and every anchor, fewer than 3 words remain. An anchor is a token from the fixture itself: a component heading, an interface heading, a backticked span, or a digit run that appears in the fixture's architecture.md or prd.md. Padding with filler therefore earns nothing, and an invented backtick name earns nothing because it is not in the fixture. Known limits, for Review: (a) a hedge phrase not in the list, plus three other words, passes; (b) an Accept line stuffed with real fixture anchors passes whether or not anyone could test it; (c) the size rule bounds items from above only, so splitting a lump into trivially small items passes every check; coverage still forces every component to be named, which is the only pressure against it. The llm graders in the case are the in-harness check for (a) to (c) and are model judgement, not deterministic."
  - "Recommended default taken (fixtures, PRD open question 4): the fixture architecture and PRD are the existing `evals/fixtures/decompose-feature/docs/features/csv-export/` files, read in place and never edited (four components: Export API, Export Scheduler, CSV Generator, Delivery; five PRD success criteria). They are not copied: the case's scaffold.sh embeds their text in heredocs (a case's scaffold runs in a temp dir and cannot reach the repo), and a test asserts each heredoc body equals the file, so a fixture edit fails loudly and the cuts are re-checked. The cuts are new files under `plugin-evals/decompose/fixtures/csv-export/cuts/`: one known-good cut and four known-bad cuts. Each bad cut is the good cut with one edit, and a test asserts each differs from the good cut by at most 2 lines, so a bad cut fails only its own class by construction. To keep the good cut from merely mirroring TEMPLATE.md, its Accept lines are written against the fixture's own contracts (status codes, retry count, header row, the 5-minute bound), not TEMPLATE slots, and a test asserts the template's `<...>` slots are absent from it."
  - "Recommended default taken (module placement, PRD open question 5): a new root-only leaf module `decompose_grade.py`, not `eval_schema.py` and not a new seam. eval_schema.py owns the eval case/record shape and results naming (ADR-0022, ADR-0024); scoring one skill's artifact is not that, and it would make eval_schema import `knowledge_plane` and `decompose_signals`. CLAUDE.md's seam rule asks for multiple real callers AND observed divergence; there is one caller (the tests, plus the `factory.py` VERBS row), so no seam module is added. No payload tool imports it, so it is root-only. New root-only to mirrored pairs: `decompose_grade` to `cli` (guarded `read_file`, `report`) and to `knowledge_plane` (`breakdown_rows`). The pin moves from 52 to 54 pairs; `decompose_signals` is root-only, so importing `item_keys` adds no pair. Baseline `python3 one_owner.py`: `one-owner: 9 problem(s)`; the acceptance is that it still reads 9 after, none naming decompose_grade."
  - "Recommended default taken (front door, PRD open question 7 and brief): a `factory.py` VERBS row `decompose-grade` (required by tests/test_factory_cli.py for any front-door verb) and one CLAUDE.md on-demand bullet beside `decompose_signals.py`, marked free and offline. No Makefile, workflow or `make check` line: it needs a produced breakdown, which CI never has. Overlap with the unmerged `feat/decompose-placeholder-scan` (SKILL.md step plus one `evals/output/decompose.json` expectation; `git diff origin/main...origin/feat/decompose-placeholder-scan --stat`: 2 files, 21 insertions, 4 deletions): complementary and independent. That branch makes the skill prevent placeholders, vague Accept lines and dangling Blocked by; this grader measures them from outside. Neither imports the other; the grader's hedge list and slot check state what 'untestable' means for the grader and do not parse the skill text. No check is stated twice in code: the model-judged `evals/output/decompose.json` expectations stay prose for a model; the deterministic rules live only in the new module."
  - "Recommended default taken (the real-breakdown caveat, stated so nobody over-reads the score): the grader is calibrated to fixture-spelled breakdowns. On the repo's own history, 35 of 94 architecture components (37%) are not named verbatim in their feature's breakdown (they are named by backticked symbol instead), so pointing the coverage check at past runs would report misses that are not defects. The grader's input contract is therefore a breakdown drafted from the fixture, where the Decompose skill's own rule ('components keep the architecture's spelling') applies; it is not a retroactive audit of shipped runs."
---

# Architecture: A scored, offline-gradable eval suite for Decompose

## Approach

Two artifacts that share a fixture and nothing else. The first is a
plugin-eval suite, `plugin-evals/decompose/`, with one case: a scaffold
seeds the csv-export PRD and architecture, the prompt asks for the
breakdown with the interview answers pre-supplied, and the harness's own
graders judge the model run (`tool_used` Skill, `file_exists` on the
breakdown, `regex` on the file for row shape, and four `llm` graders, one
per defect class). The harness has no grader that runs code, so this half
is exactly what the harness can host and is never executed here. The second
is `decompose_grade.py`, a root-only stdlib module that reads a produced
breakdown.md, the fixture architecture.md and prd.md, and returns a score
plus one feedback line per defect, which is the signal an optimizer needs
and which the harness cannot give. Its tests run it over one known-good cut
and four single-fault bad cuts held as fixtures, offline, with exact
strings.

The other shape compared was a single scorer: encode the four classes only
as `llm` and `regex` graders inside the case. It loses on three counts: it
is not deterministic, it costs money on every score, and a regex cannot
compute coverage or resolve a dependency, so it could not satisfy the PRD's
exact-string criteria. A third shape, a Python grader invoked from a
scaffold or a `Bash(python3 *)` tool grant inside the case, loses because
the producing model could then read or run the grader and game it, and
because no grader type consumes its output.

The bridge between the two is a follow-up, not built here: a first paid run
with `--keep-temp` leaves each produced breakdown.md on disk, and the Owner
can run `python3 decompose_grade.py` on those files. Until that run exists,
the offline score is validated only against the hand-built cuts.

| PRD success criterion | Where |
|---|---|
| Good cut scores strictly higher than every bad cut, no defect line | Cuts and fixtures, Grade |
| Coverage-miss line names the component | Coverage check |
| Dangling-dependency line names both items | Dependency check |
| Untestable-Accept line names the item; concrete Accept emits none | Accept check |
| Mis-sized line names the item and its size | Size check |
| Each bad cut emits its class's line and no other | Cuts and fixtures |
| `--tag decompose` selects the suite, checked statically | Suite case, Suite wiring test |
| No network, no model call, stdlib only, asserted | Grade (imports), Suite wiring test |
| No existing eval definition edited; LEDGER, records, plugin.json untouched | Suite wiring test, ADR-0114, Verify |
| Five repo checks pass | ADR-0114, VERBS row, pin |

## Components

### Grade (`decompose_grade.grade`)

- Responsibility: pure function from `(breakdown_text, architecture_text,
  prd_text)` to `{score, parts, feedback}`. It owns the four checks, their
  exact feedback strings, and the score. Score is the mean of four part
  fractions (coverage = covered components over components; dependencies =
  resolved edges over edges, 1.0 with no edges; accept = testable items over
  items; sizing = right-sized items over items), rounded to 3 places. An item
  fails a part once, however many lines name it. A breakdown with no rows
  scores 0.0 with one line, `no-items: breakdown holds no checkbox work items`.
- Collaborators: `knowledge_plane.breakdown_rows` (rows and their blocks),
  `decompose_signals.item_keys` (item keys). Imports stdlib, those two and
  `cli` only; no `socket`, `urllib`, `http`, `subprocess` or model client.

### Coverage check

- Responsibility: components are the `###` headings under the fixture
  architecture's `## Components`, with a trailing parenthetical removed. A
  component is covered when its name appears as a case-insensitive phrase in
  some row's block. Names shorter than 4 characters are not graded (a
  deliberate floor against substring hits).
- Collaborators: Grade. Pure.

### Dependency check

- Responsibility: for each row, the `Blocked by:` clause from its block
  (case-insensitive, sub-bullet or inline), split on `;` and `,`. `—`, `-`,
  `none` and an absent clause mean no edge. An element resolves when it
  starts, at a word boundary, with some item's key. An element that starts
  with no key is dangling, and an element naming its own item is dangling too.
  The key is the label (`E1`) or, for an unlabelled item, its whole bold text,
  as `decompose_signals` defines it; the title text that follows a label is
  not verified. Titles containing a comma split wrongly, so fixtures avoid
  them (limit, below).
- Collaborators: Grade. Pure.

### Accept check

- Responsibility: owns the meaning of untestable for the grader. The Accept
  clause is the sub-bullet `Accept:` in the row's block. Untestable when
  absent, empty, holding an unfilled `<...>` slot outside backticks, or when
  fewer than 3 words remain after deleting hedge phrases and anchors (see the
  assumptions for the anchor definition and the three known limits). The hedge
  list and anchor builder are module constants and a function, not
  configuration.
- Collaborators: Grade. Pure.

### Size check

- Responsibility: an item is mis-sized when the distinct components named in
  its row text and sub-bullets exceed `MAX_SPAN` (3). Reports the count as the
  item's size. Does not read `size:`, Accept length or clause count.
- Collaborators: Coverage check's component list. Pure.

### Report and front door (`main`)

- Responsibility: `python3 decompose_grade.py <breakdown.md> <architecture.md>
  [<prd.md>]` reads each file through `cli.read_file`, prints through
  `cli.report`, and owns exit codes. Also `python3 factory.py decompose-grade`.
- Collaborators: Grade, `cli`.

### Suite case (`plugin-evals/decompose/csv-export-cut/`)

- Responsibility: one case in the existing layout: `case.yaml`
  (`schema_version: "1.1"`, `name`, `context.scaffold_script: scaffold.sh`),
  `prompt.md` (frontmatter `description`, `tags: [decompose]`, `max_turns`,
  `timeout_seconds`, `allowed_tools`), `scaffold.sh` seeding
  `docs/features/csv-export/{prd.md,architecture.md}`, and `graders/`:
  `skill-fired.md` (`tool_used` Skill `decompose`), `breakdown-exists.md`
  (`file_exists` on the breakdown path), `has-rows.md` (`regex` over the
  produced file for a checkbox row, flags `m`), and four `llm` graders named
  `covers-every-component.md`, `blocked-by-names-real-items.md`,
  `accept-is-checkable.md`, `items-are-one-sitting.md`. One case, not several:
  the suite's cost is runs times judge calls, and a second scenario earns its
  place only when the first discriminates on a real run.
- Collaborators: the harness. The case is never executed by this run.

### Cuts and fixtures (`plugin-evals/decompose/fixtures/csv-export/cuts/`)

- Responsibility: `good.md` plus `bad-coverage.md`, `bad-dangling.md`,
  `bad-accept.md`, `bad-sized.md`, each a complete breakdown.md with
  frontmatter. No typed ids (`PRD-`, `WO-`, `ADR-`) and no real paths, so
  detectors C and I and the drift check have nothing to read. The architecture
  and PRD they are graded against are the existing
  `evals/fixtures/decompose-feature/...` files, read in place.
- Collaborators: Grade tests.

## Data model

No stored state. The record that crosses the module's interface:

```
grade(...) -> {"score": float,                  # 0.0 to 1.0, 3 places
               "parts": {"coverage": float, "dependencies": float,
                         "accept": float, "sizing": float},
               "feedback": [str, ...]}           # sorted by class order below, then item order
```

Feedback strings, fixed here so tests pin them (item `E3`, component
`Delivery` are the fixture's own names):

```
coverage-miss: component "Delivery" is named by no item
dangling-blocked-by: E4 is blocked by "E9", which names no item
untestable-accept: E3 has no checkable Accept line (empty|placeholder|unanchored)
mis-sized: E2 names 4 components (limit 3)
no-items: breakdown holds no checkbox work items
```

The summary line is `decompose-grade: score 0.875 (coverage 1.000,
dependencies 1.000, accept 1.000, sizing 0.500)`. Access patterns: the tests
call `grade` once per cut; a human calls the command once per breakdown. No
storage and no consistency question.

## Interfaces & contracts

### `python3 decompose_grade.py <breakdown.md> <architecture.md> [<prd.md>]`

- Input: three paths. The PRD is optional and only widens the anchor
  vocabulary. The breakdown should have been drafted from that architecture; a
  breakdown from another architecture will report every component missing.
- Output: the summary line, then one feedback line per defect, in the order
  coverage, dependency, accept, size, then by item order. Exit 0 when there are
  no defect lines, 1 when there is at least one, 2 on usage or an unreadable
  input (printed through `cli.report`, with `cli.read_file`'s guarded-read
  message). No network, no model, no git, no write.
- Failure modes: a missing or unreadable file exits 2 and scores nothing; an
  architecture with no `## Components` section or no `###` headings exits 2
  (`decompose-grade: <path> holds no components`), never a vacuous 1.0. A
  malformed row (a checkbox row with no bold span) takes its row text as its
  key, as `decompose_signals` does.

### `decompose_grade.grade(breakdown_text, architecture_text, prd_text="")`

- Input: the three texts. Output: the record above. Deterministic: same
  inputs, same record. Raises `ValueError` with the same `holds no components`
  message for the no-components case; `main` turns it into exit 2.
- Failure modes: none beyond that; defects are data, not exceptions.

### Suite case contract (harness side)

- Input: `claude plugin eval . --tag decompose` with the flags ADR-0081 fixes.
  Output: the CLI's own aggregate JSON. Failure modes: the harness owns them.
  This run only asserts statically that the case is well formed and selected.

## Stack & dependencies

- Python 3 standard library only — the repo's hard convention.
- `knowledge_plane`, `cli` (mirrored) and `decompose_signals` (root-only), all
  existing; no new seam module, no third-party package.
- Tests: `tests/test_decompose_grade.py` (grader behaviour, exact strings, the
  good-versus-bad score table, single-edit and no-template-slot checks on the
  cuts, a mutation check that deleting each check's body changes its bad cut's
  output) and `tests/test_decompose_suite.py` (static wiring: manifest value,
  case layout, grader `type:` values in the harness's documented set, tags via
  `tests/test_plugin_eval_tags.case_tags` rather than a second parser,
  scaffold heredocs equal the fixture files, import allowlist by AST). Repo
  edits Implement owns: `tests/test_dual_membership.py` pin (52 to 54 pairs and
  its comment), `factory.py` VERBS row, CLAUDE.md bullet. No edit to
  `.claude-plugin/plugin.json`, `LEDGER.md`, `plugin-evals/records/`, `evals/`,
  `skills/` or any existing suite.

## Decisions & alternatives

- **Two scorers (harness graders for the model run, a standalone module for
  the deterministic score)** over one in-harness scorer — the harness has no
  code-running grader type, and a regex or judge cannot compute the four
  classes deterministically. Recorded in ADR-0114.
- **No plugin.json edit** over adding an `experimental.evals` entry — the
  value is already the directory `plugin-evals`; the suite is found by layout.
  This also keeps ADR-0095 out of it.
- **A new root-only leaf module** over placing it in `eval_schema.py` or a seam
  module — eval_schema owns case and results shape, and the seam rule's
  multiple-callers-and-divergence bar is not met. Pin edges recorded in
  ADR-0114.
- **Parse clauses from `breakdown_rows` blocks and take keys from
  `decompose_signals.item_keys`** over reusing `parse_row`'s blockers or
  re-deriving keys — `parse_row` reads lowercase WO-token blockers only
  (measured: empty on TEMPLATE-form rows), and a second key grammar would be a
  second owner.
- **Mis-sized as over-wide (more than 3 components)** over Accept length,
  clause count, or declared `size:` — measured bands overlap and the template
  carries no `size:`; a length cap rewards short Accept lines. Known limit:
  under-size is not graded.
- **Untestable judged by anchoring to the fixture** over a length floor or a
  placeholder list alone — a list alone passes `Delivery works fine`; a length
  floor rewards padding.
- **Existing csv-export fixture read in place, new cuts only** over a new
  fixture architecture — one architecture for both evals, no second copy; the
  scaffold-equality test makes the coupling loud.
- **One suite case** over several — cost scales with cases times runs times
  judges, and discrimination on a real model is unproven.

## ADRs

- [ADR-0114](../../adr/0114-decompose-grade-is-an-offline-scorer-beside-a-harness-suite-and-joins-the-root-only-importers.md)
  — provisional: the two-scorer split (the harness has no code grader) and
  `decompose_grade` joining the root-only importers (pin 52 to 54).
