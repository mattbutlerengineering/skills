---
stage: decompose
run: feature:decompose-outcome-signals
date: 2026-10-18
assumptions:
  - "No live review of the cut: the brief is the only source of answers, and it says nothing about milestones or sizing. Milestone boundaries and sizes are the skill's own defaults (each milestone independently demonstrable, one item per sitting, vertical slices where the architecture allows). Milestone 1 is the boundary policy over real git history, because every signal rests on it and it can be shown alone. Milestone 2 is the three pure signal functions. Milestone 3 is the one command the PRD asks for. Milestone 4 is the append-only record, the docs and the first real numbers."
  - "Test-first ordering follows the repo's TDD rule: each implementation item is blocked by a tests item whose Accept says its cases run and fail against the tree before the implementation lands."
  - "No work-order ids and no (tracker: #N) markers: the brief says issue #986 seeds the run and ADR-0032 mirroring is not used, and detectors C and I scan every markdown file. Items carry short labels (S1, S2, ...) at the start of the bold span, the form recent fix-run breakdowns use and the form architecture.md's work-item key rule reads."
  - "Derived, not stated: a signal that reads an unmeasurable boundary is itself unmeasurable, with that boundary's reason. Architecture states only that a signal is observed when every boundary it read is observed. So with an observed decompose boundary and no implement boundary, both re-plan and design gaps are unmeasurable, because the (D, I] window has no end. With an inferred decompose boundary, design gaps reads only the D version and stays measurable."
  - "Derived from the data model: the design-gap aggregate's denominator is the number of measured runs, because a design-gap RunRecord carries only `routes`. The re-plan aggregate is the sum of counts over the sum of items_at_d. The review-traced aggregate is named findings over findings."
  - "Derived from the data model: a review.md with no heading the grammar reads is a measured run with 0 findings (its record has no `unmeasurable` key), so it counts in the review-traced run total and adds 0/0. Only `no review.md` is unmeasurable."
  - "The dual-membership pin moves in the item that first adds the imports (S2), because tests/test_dual_membership.py derives the crossing pairs from the tree and fails as soon as an unpinned import lands. S8 checks the finished pin against ADR-0110's three pairs and 46-pair count."
  - "Both ADRs stay provisional. Confirming or replacing ADR-0109 is the Owner's call, before the first record is cited (ADR-0109 says so), so no item here changes either ADR's status."
  - "The first record (S13) is taken from the refs this clone holds at that time. The PRD measured 488 PR head refs already fetched under refs/remotes/pr. Fetching is the documented manual step, and no item runs it, because the tool never fetches and the brief rules out network in the tool."
---

# Breakdown: Decompose outcome signals from git history

Progress lives in the checkboxes below. Implement checks items off as their
acceptance criteria are met. Every implementation item is blocked by the
tests item that pins it. All tests go in `tests/test_decompose_signals.py`
unless an item says otherwise, and the fixture tests build real temp git
repos (architecture.md, Decisions).

## Milestone 1: boundaries are found and labelled over real git history

When this milestone is done, `decompose_signals.boundaries` picks each
run's decompose and implement boundaries from one git walk and labels each
one observed or inferred under ADR-0109, or names why there is none.

- [x] **S1 Boundary and history-adapter tests** — a temp-git-repo fixture builder plus cases for `read_history`, `read_version` and `boundaries` — size:M
  - Accept: the module holds these cases, each asserting exact values or strings. Observed decompose: a `docs(<scope>): decompose` subject whose scope differs from the slug and has no em dash, changing the run's `breakdown.md`, is observed. A `docs(x): decompose` commit that changes only another run's `breakdown.md` is not observed for this run. A `docs(x): implement` commit that changes only `architecture.md` is not an observed implement boundary. Inferred decompose is the earliest commit that changes the run's `breakdown.md`. Observed implement is the earliest `docs(<scope>): implement` commit after D that changes `breakdown.md`. Inferred implement is the earliest commit after D whose version has a done row. The fixed reasons print as `no commit on the refs read changes <path>`, `the first version (<sha7>) already checks <n> of <m> rows` and `no implement boundary: no later commit checks a row`. A commit reachable only from `refs/stash` is never a boundary, and the ref listing returns namespace counts plus a 12-hex digest equal to sha256 of the sorted `refname sha` lines. A failing fake `run` gives `decompose-signals: git <verb> failed: <cli.detail>` for `for-each-ref` and `log`. A recording fake shows that no git verb outside `for-each-ref`, `log`, `show`, `rev-parse` and `status` is ever run, so no `fetch`, `ls-remote`, `pull` or `remote`. Before the module exists the test module fails on import.
  - Blocked by: —
- [x] **S2 History adapter and boundary policy** — root-level `decompose_signals.py` with `read_history`, `read_version` and `boundaries` as architecture.md's History adapter and Boundary policy describe — size:M
  - Accept: the S1 tests pass. git is reached only through `cli.runner("git", timeout=60)` injected as `run`, and the module defines no module-level runner alias. The walk is one `git log --stdin --author-date-order --reverse --name-only` over the run artifact pathspecs, fed every ref except `refs/stash`. Stage artifacts come from `protocol.STAGE_ARTIFACTS` and done rows from `knowledge_plane.breakdown_rows`, with no retyped regex for either. The module imports only the standard library, `cli`, `knowledge_plane` and `protocol`, and is not in `factory_init.MIRRORS`. `tests/test_dual_membership.py`'s pin gains a pair for each mirrored module the module now imports, and the test passes.
  - Blocked by: S1 Boundary and history-adapter tests

## Milestone 2: the three signals are pure functions over text

When this milestone is done, `replan`, `design_gaps` and
`review_findings` each return a count or a fixed unmeasurable reason
from plain inputs, with no git.

- [x] **S3 Work-item diff tests** — cases for `item_keys` and `replan` over pairs of breakdown line lists — size:M
  - Accept: the module holds these cases, each asserting exact keys or counts. `item_keys` takes a WO token when the row carries one, else a short leading label in the bold span (`S1`, `A1`, `I2`), else the bold text, else the row text up to the first ` — `. `replan` gives: no change, count 0 and items_at_d equal to the row count; one added row, added 1; one dropped row, dropped 1; a dropped and an added row with equal normalized titles, renamed 1 and count 0; an old row whose I-version cites two added keys, split 1; a dropped row cited by two added rows, split 1; one added row citing two dropped keys, merged 1; a row whose only mention of another key is inside its `blocked by:` clause, split 0. Count is added + dropped + splits + merges. Two rows with the same key in one version give the reason `duplicate work-item key <key> at <sha7>`. Run before S4, the new cases fail.
  - Blocked by: S2 History adapter and boundary policy
- [x] **S4 Work-item diff** — `item_keys` and `replan` as architecture.md's Work-item diff describes — size:M
  - Accept: the S3 tests pass, and the S1 tests still pass. Rows are parsed with `knowledge_plane.parse_row` / `breakdown_rows`, titles come from `knowledge_plane.row_title` for WO rows, and citations are read with the clause `knowledge_plane.BLOCKED_BY` matches removed. `knowledge_plane.WO_TOKEN` is used, and no WO or blocked-by regex is retyped.
  - Blocked by: S3 Work-item diff tests
- [x] **S5 Design-gap and review-tracer tests** — cases for `design_gaps` and `review_findings` — size:M
  - Accept: the module holds these cases, each asserting exact results. `design_gaps` with D observed counts the commits in (D, I] whose subject matches `docs(<scope>): architect` and which change the run's `architecture.md`, labelled observed when I is observed and inferred otherwise; an architect-subject commit that changes another run's `architecture.md` is not counted. With D inferred it reads the D version's `## Design gaps found` section: first word `none` gives 0, other content gives 1, a missing section gives `no "Design gaps found" section at the decompose boundary`, and a section heading inside a fence counts as missing; all three are labelled inferred. A D with no implement boundary gives design gaps unmeasurable with the implement boundary's reason. `review_findings` returns its three shapes: no `review.md`; a `review.md` with no heading the grammar reads; N findings, of which M name an item. Headings of levels 2 to 4 that start with a severity word (critical, major, minor, low, medium, high) or an ordinal label (`F1`, `Finding 1`, `1.`), with emphasis stripped, are findings. A level-1 or level-5 heading, and a heading inside a fence, are not. A finding names an item only when its block holds a current key as a whole token (`S1` does not match inside `S10`). Run before S6, the new cases fail.
  - Blocked by: S4 Work-item diff
- [x] **S6 Design-gap count and review tracer** — `design_gaps` and `review_findings` as architecture.md describes — size:M
  - Accept: the S5 tests pass, and every earlier test still passes. Fences are read with `knowledge_plane.unfenced`, and review and breakdown texts are read through `cli.read_file(path, shown, str)`, whose problem comes back prefixed with the run label.
  - Blocked by: S5 Design-gap and review-tracer tests

## Milestone 3: one command prints every run and the aggregate

When this milestone is done, `python3 decompose_signals.py` and
`python3 factory.py decompose-signals` print the header, one line per run
with a breakdown, and the three aggregate lines, in the problem-string /
count contract.

- [x] **S7 Report tests** — end-to-end cases that drive `main([])` against temp git repos and assert the exact stdout lines and exit code — size:M
  - Accept: the module holds the five PRD fixture runs, each in a temp repo, each asserting its exact run line: a run with no re-plans (`re-plan 0 of <n>`); a run with a split item (`split 1`); a run routed back to Architect (`design gaps 1 observed`); a run with only inferred boundaries (`decompose inferred <sha7>, implement inferred <sha7>`); an unmeasurable run (`re-plan unmeasurable — no commit on the refs read changes <path>`). One more case shows a run with no `review.md` printing `review-traced unmeasurable — no review.md`, and a run whose `review.md` has no finding heading printing `review-traced 0 findings — review.md has no finding heading`; the two strings differ. The header lines come first, in architecture.md's order (`refs read — …; refs/stash skipped; digest <12 hex>`, then `boundary rule — <sentence>`). Run lines are ordered by run path. Each aggregate line reads `aggregate <signal> — observed <num>/<den> over <r> run(s); inferred …; combined …; unmeasurable <u> run(s)`, and a mixed fixture shows an unmeasurable run left out of every count; review-traced always prints `inferred 0/0 over 0 run(s)`. The last line is the `cli.report` summary. Exit is 0 with unmeasurable runs and no problems, 1 when a git call fails (no run lines printed when `for-each-ref` or `log` fails; a failed `show` gives `read failed` on the affected signals plus one problem), and 2 with the usage text for an unknown argument. Run before S8, the new cases fail.
  - Blocked by: S6 Design-gap count and review tracer
- [x] **S8 Report and front door** — `measure`, `render` and `main` as architecture.md's Report and front door describes, plus the `factory.py` verb — size:M
  - Accept: the S7 tests pass, and every earlier test still passes. Runs come from `knowledge_plane.breakdown_files` and are labelled with `protocol.run_ref`; output goes through `cli.report`, so the summary prefix is computed. The boundary-rule sentence lives once in the module. `factory.VERBS` gains `"decompose-signals": ("decompose_signals", "argv")`, the module docstring's first line is its `decompose-signals: …` index line, and the docstring names the manual fetch step `git fetch origin '+refs/pull/*/head:refs/remotes/pr/*'`; `tests/test_factory_cli.py` passes unchanged. `tests/test_dual_membership.py`'s pin holds exactly ADR-0110's three new pairs (`decompose_signals` with `cli`, `knowledge_plane` and `protocol`), its comment reads 46 pairs, and the test passes.
  - Blocked by: S7 Report tests

## Milestone 4: the first real numbers are recorded append-only by the tool

When this milestone is done, `--record` writes the result through
`eval_schema`, the docs name the tool, and this repo's first numbers are
committed as the tool wrote them.

- [x] **S9 Record tests** — cases in `tests/test_eval_schema.py` for the new snapshot kind, and in `tests/test_decompose_signals.py` for `--record` — size:M
  - Accept: `eval_schema.results_path(results, "decompose-signals", "2026-10-18")` returns `decompose-signals-2026-10-18.json`, and `-2` once that file exists; `write_snapshot(output, results, "decompose-signals")` writes indented JSON with a trailing newline; `eval_schema.valid_results_link` is false for a `decompose-signals-…` path, so the kind can never be LEDGER evidence. `main(["--record"])` on a clean temp repo writes one snapshot holding `date`, `head`, `refs`, `refs_digest`, `rule`, `runs` and `aggregate`, and prints `decompose-signals: recorded <path>`. It writes nothing and prints a problem when `git status --porcelain -- docs/` is non-empty, and when the run has any problem. Two invocations on the same refs give equal `refs_digest`, `runs` and `aggregate`. Run before S10, the new cases fail.
  - Blocked by: S8 Report and front door
- [x] **S10 eval_schema snapshot kind and --record** — `decompose-signals` joins `results_path` and `SNAPSHOT_KINDS`, its docstring line beside `charter`'s, and `main` gains `--record` — size:S
  - Accept: the S9 tests pass, and every earlier test, including the existing `tests/test_eval_schema.py` cases, still passes. `_RESULTS_LINK` is unchanged. The `-N` grammar has one owner, `eval_schema.results_path`; `decompose_signals.py` builds no results filename itself.
  - Blocked by: S9 Record tests
- [x] **S11 Docs** — the CLAUDE.md "on demand, free" bullet beside `one_owner.py`, an `evals/README.md` results-layout line for `decompose-signals-<date>[-N].json`, and a CONTEXT.md entry for **Outcome signal** — size:S
  - Accept: CLAUDE.md names `python3 decompose_signals.py` as free and outside every gate, says it never fetches, and gives the manual fetch step. `evals/README.md` lists the new kind beside `charter-<date>[-N].json` and says it is factory evidence, not LEDGER evidence. CONTEXT.md defines **Outcome signal** as one of re-plan, design gaps routed to Architect, and review-traced findings, each labelled observed or inferred. No Makefile or workflow line is added. `python3 kb.py drift` prints `drift: 0 problem(s)` and `python3 lint.py` prints `lint: 0 problem(s)`.
  - Blocked by: S10 eval_schema snapshot kind and --record
- [x] **S12 Whole-repo verify** — the four CI checks and the one-owner pre-pass over the finished change — size:S
  - Accept: `python3 run_tests.py` exits 0; `python3 lint.py` prints `lint: 0 problem(s)`; `python3 kb.py drift` prints `drift: 0 problem(s)`; `python3 gates.py` and `python3 gates.py --selftest` print `gates: 0 problem(s)`. `python3 one_owner.py` reports no `one-owner:` problem naming `decompose_signals.py`. No file under `skills/` or `factory/templates/`, and not `.claude-plugin/plugin.json`, `factory_init.MIRRORS` or `LEDGER.md`, changed.
  - Blocked by: S11 Docs
- [ ] **S13 Record the first real numbers** — run `python3 decompose_signals.py --record` on this clone and commit the file it writes, unedited — size:S
  - Accept: every earlier item's breakdown tick is committed first, so `git status --porcelain -- docs/` prints nothing. The command exits 0 and prints `decompose-signals: recorded evals/results/decompose-signals-<date>[-N].json`. That file is committed byte-for-byte as written, with no hand edit (`git diff` between the written file and the committed blob is empty). A rerun without `--record` on the same refs prints the same run and aggregate lines as the recorded `runs` and `aggregate`. The refs namespaces, digest and the observed, inferred and unmeasurable run counts are copied from the tool's output into Notes, dated. LEDGER.md is unchanged.
  - Blocked by: S12 Whole-repo verify

## Design gaps found

None. Every component, interface string and failure mode the items need is
in architecture.md or ADR-0109 / ADR-0110. Three points the architecture
leaves implicit are derived from its stated rules and data model, not
designed here; each is logged in the frontmatter `assumptions:` (a signal
reading an unmeasurable boundary is unmeasurable; the design-gap
aggregate's denominator is measured runs; a `review.md` with no finding
heading is a measured run with 0 findings).

## Notes

Coverage check, 2026-10-18. Components: History adapter and Boundary
policy (S1, S2); Work-item diff (S3, S4); Design-gap count and Review
tracer (S5, S6); Report and front door, with the `factory.py` verb and the
dual-membership pin (S7, S8); the `eval_schema` snapshot kind and
`--record` (S9, S10); the CLAUDE.md, `evals/README.md` and CONTEXT.md
touches (S11). PRD success criteria: one invocation with per-run lines
and an aggregate (S7); observed/inferred labels and populations (S1, S7);
unmeasurable runs named and kept out of aggregates (S7); refs read and
rule named (S1, S7); no network, git only through `cli.py` (S1, S2); the
five fixture cases with exact strings (S7); no `review.md` versus no
finding heading (S5, S7); first numbers recorded append-only and
reproducible (S9, S13); the five repo checks (S12).

<!-- Deviations discovered during Implement get logged here, dated. -->
