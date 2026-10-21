---
stage: review
run: feature:decompose-eval-suite
date: 2026-10-20
assumptions:
  - "Autorun stage, no live user: severity is the reviewer's call. Brief binding: suite and graders only, no paid run, no `claude plugin eval`, no model call, no LEDGER/plugin.json/skills edits; none was made."
  - "Diff scope is `git diff origin/main...HEAD` at 2789bd1 (the Verify commit): decompose_grade.py, its two test modules, plugin-evals/decompose/**, factory.py, tests/test_dual_membership.py, CLAUDE.md, ADR-0114 and its index row, and the run's artifacts."
  - "Nothing here changes an Owner decision, the PRD's fixed strings or ADR-0114's shape. The one finding that would (a closing limit line on the CLI output) is deferred."
---

# Review: A scored, offline-gradable eval suite for Decompose

## Scope

The code diff above read in full (the grader is 310 lines), the PRD,
architecture.md, ADR-0114, breakdown.md with its Notes, verification.md and
the autorun brief. Verification came first, so the usual order holds.

Examined by: a full read; probes in scratch (empty, garbage and
all-short-name inputs, a self-edge, a comma label, a 1.2 MB breakdown, 200k
commas, 100k backticks and `<`, 30k hedge repeats); a 28-mutant sweep of
`decompose_grade.py` against `tests/test_decompose_grade.py`, applied in a
`git archive` copy (each `old` string asserted to occur once, bytecode off;
the first sweep left 2 survivors, both pinned, the final sweep left 0); a
mutation of the dual-membership pin in a second copy; `python3 one_owner.py`
(9 problems repo-wide, none naming this branch's files); `python3 kb.py
drift`; the scaffold run once in a fresh temp dir. Domain passes: none
selected (no payments, migrations or dependency paths). Standards: no
`docs/standards.json` statement matched a finding.

Review commits on this branch:

- 66280ad `fix(decompose-eval-suite): a Blocked by label holding a comma is one element, not a fake dangling edge`
- cb18259 `fix(decompose-eval-suite): an architecture with only sub-4-character names is refused, not scored 1.0`
- 3efbddd `test(decompose-eval-suite): pin the Accept word floor and a continued Accept line`
- efcbb5d `docs(decompose-eval-suite): state the Accept rule as implemented (an anchor and 3 words)`

## Findings

### Major: an architecture whose component names are all under 4 characters scored a perfect coverage and sizing

- Scenario: architecture with `### API` and `### DB` under `## Components`
  and any breakdown, however poor. `_graded` drops both names (MIN_NAME), so
  coverage and sizing are `_fraction(0, 0)` = 1.0 and the grade is 0.75 with
  only an Accept line possible. Reproduced: coverage 1.0, sizing 1.0, exit
  0 or 1 on Accept alone. This is the vacuous-1.0 the architecture rules out
  for "no components" (exit 2), reached by a different input.
- Standard: none
- Decision: fixed in cb18259. `grade` raises `ValueError("holds no component
  named 4 or more characters")` when nothing is gradable; `main` already
  turns a ValueError into exit 2. Test first (RED seen). The fixed string
  `holds no components` is unchanged.

### Minor: a Blocked by label that contains a comma was reported as a dangling edge

- Scenario: the Verify finding. `S3` blocked by "S2 Band join, row selection
  and work orders" was cut at the comma into the fake element "row selection
  and work orders": `dangling-blocked-by` on size-band-calibration, exit 1.
- Standard: none
- Decision: fixed in 66280ad. A `;` segment that is wholly inside some
  item's bold label stays one element and resolves by its key; a
  continuation that is not part of a label (`A1 Join, A9`) is still cut and
  still dangling (pinned by a test, so a real dangling edge is not hidden).
  The same command on size-band-calibration now prints score 1.000, exit 0.
  Matching is on the bold label, not the whole row line, so
  "S1, S2" found inside another row's inline `blocked by:` text cannot
  swallow a dangling S2.

### Minor: two load-bearing branches were unguarded by tests

- Scenario: mutants `MIN_WORDS = 2` and a dropped Accept continuation-line
  branch both left the whole grader suite green, so the 3-word floor and a
  multi-line Accept were unpinned.
- Standard: none
- Decision: fixed in 3efbddd (tests only, no behaviour change); both mutants
  now fail.

### Minor: architecture.md's Accept check text contradicted the code

- Scenario: it said untestable when "fewer than 3 words remain", but the code
  (and the assumptions, and Verify's M2) also require at least one anchor.
- Standard: none
- Decision: fixed in efcbb5d, a one-expression doc correction. The reasons,
  strings and exit codes are unchanged.

### Minor (deferred): a score of 1.000 and exit 0 mean "no defect the grader knows", and the CLI output does not say so

- Scenario: four rows each reading `Accept: <component> is basically fine and
  nice overall`, one per fixture component, grade 1.000 with no defect line
  against the csv-export fixture (reproduced). The limits are stated
  honestly in architecture.md ("known limit" tests, an unlisted hedge plus
  three words passes; anchor stuffing; splitting a lump into small items;
  coverage counts a mention anywhere in a row block, so a component named
  only in a `Blocked by` line is covered), and CLAUDE.md says the score is
  fixture-calibrated and not an audit. None is worse than stated. But the
  summary line itself carries no caveat, so an optimizer reading only that
  line could treat 1.000 as "good".
- Standard: none
- Decision: DEFERRED. The summary line and exit-code strings are fixed by the
  PRD and pinned by tests; a footer is the Owner's call. The honest use today
  is the one the harness suite exists for: the grader is a floor of
  detectable defects, never a quality score.

### Minor (deferred): no input size cap, cost grows with rows times edges

- Scenario: a 1.2 MB breakdown with 1000 rows and 30 blockers each takes
  about 2.5 s (the edge-by-item resolution is quadratic); with 300
  components about 15 s. No regex backtracks: 200k commas, 100k backticks
  and `<`, and 30k repeated hedges each return in about 0.1 s or less. The
  input is a file the Owner points the tool at, not a trust boundary.
- Standard: none
- Decision: DEFERRED; no cap without a real file that needs one (same stance
  as the decompose-lessons review).

### Minor (note): `plugin-evals/decompose/fixtures/` has no `case.yaml`

- Scenario: unknown whether harness case discovery skips a sibling directory
  that holds no case. The `knowledge-base` suite's `seed.sh` is a weak
  precedent only.
- Decision: left as is. Settled only by a first paid run, which is out of
  scope; Verify records it as unknown too.

## Passes with no findings

- Grader arithmetic and exits. An empty or unparseable breakdown scores 0.0
  with one `no-items` line, exit 1 (never a perfect score); no components or
  now no gradable component exits 2; `_fraction` has a zero-total arm that a
  mutant to 0.0 or to unguarded division fails a test on; the mean and the
  3-place rounding are each pinned by a mutant; exit 0, 1 and 2 arms are each
  pinned. A breakdown with no `Blocked by` anywhere scores dependencies 1.0
  by the stated rule (no edge to fail).
- Regex safety. All patterns are linear; the probes above ran in milliseconds.
- Suite case. The four `llm` graders are PASS/FAIL rubrics about "the
  breakdown the reply prints"; none addresses the model under test or
  instructs it, and no grader file is a prompt. `scaffold.sh` runs only
  `mkdir`, `cat` heredocs and `git init/add/commit` with a placeholder
  identity; no network, no `cd`, no path outside the cwd; run once in a temp
  dir it wrote only the two seeded docs and `.git`. The heredocs equal the
  fixtures (pinned by the suite test).
- Dual membership. The pin sees the function-level `cli` import: with both
  `from cli import ...` lines replaced in a copy, the pin test fails naming
  `decompose_grade`/`cli`. The pin holds 54 pairs: 52 plus `(decompose_grade,
  cli)` and `(decompose_grade, knowledge_plane)`; `decompose_signals` is a
  root-only edge and not a pair.
- One-owner. `python3 one_owner.py` prints 9 problems, none naming
  decompose_grade, the suite tests or the factory row.
- Docs versus code. `python3 kb.py drift`: 0 problems. CLAUDE.md's bullet
  matches the module (exit codes, offline, calibrated, harness half never
  run).
- Complexity. The one `lean:` marker (function-level `cli` import) names its
  ceiling and its trigger. ADR compliance: ADR-0114 (provisional, live) is
  followed; no decision in the diff lacks an ADR; no edit to an existing ADR's
  Decision section.
- Security. Read-only tool: no write, no network, no subprocess; paths go
  through `cli.read_file`; errors name the file only.

## Verdict

Ready to ship. No critical finding. One major and three minors fixed in this
stage, each test-first or mutation-proven; two minors deferred with reasons
and one unknown noted (the harness case has never run, so the suite's
behaviour under the real harness, including fixtures-dir discovery and the
llm graders, is not verified and not claimed). Whole-repo checks after the
fixes:

```
tests: 3632 tests across 111 modules in 26.0s on 8 workers, 0 problem(s)
lint: 0 problem(s) across 34 skills
drift: 0 problem(s)
gates: 0 problem(s)
selftest: ok
```
