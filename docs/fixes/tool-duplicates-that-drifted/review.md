---
stage: review
run: maintenance:tool-duplicates-that-drifted
date: 2026-10-25
---

# Review: root tools hold second copies of one fact, and several have drifted

## Scope

`git diff origin/main...fix/tool-duplicates-that-drifted` at `2ac3366`. It
covers:

- `knowledge_plane.py`, `cli.py`, `human_gates.py`;
- the callers: `kb_drift.py`, `md_claims.py`, `gates.py`, `gate_digest.py`,
  `rejection_mining.py`, `cost_ledger.py`, `conductor.py`,
  `conductor_close.py`, `kb_harvest.py`, `dashboard.py`, `board.py`;
- markers in seven modules;
- `docs/backlog.md`, the payload and the manifest;
- new tests in five modules;
- the run's `defect.md` and `verification.md`.

A fresh general-purpose subagent was given the diff and a list of
behaviour changes to probe, not the author's conclusions. It ran the
branch and `origin/main` side by side from `git archive` extracts, under
Python 3.9, 3.11 and 3.14.

The fixes landed in `1493538`. On that commit:

- `tests: 3926 tests across 123 modules in 31.7s on 8 workers, 0 problem(s)`
- `lint: 0 problem(s) across 35 skills`
- `gates: 0 problem(s)`
- `selftest: ok`
- `factory-init: 0 problem(s)`
- `one-owner: 1 problem(s)`, the COSTS pair, which #1106 folds

## Findings

### Major: one unreadable run directory aborted the board under Python 3.13 and earlier

- Scenario:
  - `knowledge_plane.active_runs` checked for artifacts with `is_file()`
    outside its guard. Before, that check sat inside board's per-run
    `try/except Exception`.
  - On Python 3.13 and earlier (CI runs 3.12), `Path.is_file()` raises
    `PermissionError` on a directory the walk cannot enter.
  - The reviewer set up `docs/features/locked` with mode 000. Under 3.11,
    main put it in the board's attention strip, while the branch raised
    `PermissionError` and rendered no board. That breaks PRD-0004's rule
    that a broken run never aborts the board.
- Standard: none
- Decision: fixed in `1493538`. The presence check moved inside the guard.
  A test patches `Path.is_file` to raise for one run and asserts that the
  run is listed with its error. This machine runs 3.14, where `is_file`
  answers False, so the patch is what reproduces it here.

### Minor: a marker excused a real second owner

- Scenario: `conductor_plan.payload_version` and
  `factory_init.tools_only_manifest` are the reader and the writer of the
  same manifest keys (`plugin`, `version`). Renaming one side would
  silently turn `conductor.py --version` into "unversioned". It is one
  fact, not a coincidence.
- Standard: none
- Decision: fixed in `1493538`. `gates.MANIFEST_PAYLOAD_KEYS` sits beside
  `INSTALL_KEY` for the same manifest and owns the keys. Both sides read
  them from there, and the two markers are gone. The output bytes are
  unchanged and `tests.test_factory_init` passes.

### Minor: the path whitelist stopped reading `+` paths

- Scenario: the old rule refused listed characters and the new one allows
  only listed ones. `src/routes/+page.ts` (SvelteKit) stopped being a path,
  so a dangling one would go unreported.
- Standard: none
- Decision: fixed in `1493538`. `PLAIN_PATH` allows `+`, and a case pins
  it. The remaining narrowing (`%`, `!`, `&`, `;`, `^`) and the new coverage
  (a mid-path `@`, uppercase extensions, fragments, ranges) are recorded in
  defect.md's Notes. kb drift and md_claims counts on this repo are
  unchanged by the `+` change: `drift: 0 problem(s)` and `md-claims: 600
  problem(s)`.

### Minor: verification.md overstated the new md_claims findings

- Scenario: it called every added finding a path "no file writes". About
  20 name runtime-written files (`docs/factory/decompose-lessons.jsonl`,
  launch-demo's `title.html` and `outro.html`).
- Standard: none
- Decision: fixed in `1493538`: verification.md now says which kind is
  which.

### Minor: the shared upsert skipped the run's own bar

- Scenario: the two posting functions were identical apart from their
  label and title, with no divergence in their bodies. The bar applied
  elsewhere in Ruled out asks for observed divergence.
- Standard: none
- Decision: recorded in defect.md's Notes. The evidence is one_owner's
  LIST_ARGS/ISSUE_ARGS pair and the body/number/state key group, which
  were already flagged as two owners. `conductor.numbered` is left as a
  small second owner of the non-blank-line rule, also noted there.

## Passes with no findings

- Correctness. The reviewer confirmed each of these:
  - `next_stage` raises only `OSError` or `ValueError` on every path (it
    could build no other);
  - board's re-raised error keeps its attention text;
  - `json_lines` numbering matches `conductor.numbered` and `cost_ledger`,
    so `conductor_close.compute`'s row and line pairing holds;
  - gate_digest's and rejection_mining's gh call order, problem order,
    labels and messages are byte-identical;
  - `truncated` is never read on a failed listing;
  - the `#`-split and suffix-strip order is unchanged.
- Security: no new input boundary. Three readers that raised on a deeply
  nested line now report it.
- Complexity: four shared functions replace about eleven copies. Two
  audit items (month-to-date spend, the PR joins) were dropped rather than
  built, because reading the code showed they were not duplicates. There
  is no `lean:` marker.
- ADR compliance:
  - ADR-0061: markers are paired, and each names the other.
  - ADR-0075: `json_lines` carries the RecursionError guard.
  - ADR-0037 and ADR-0060: payload copies are byte-identical, and no payload
    tool imports a root-only module.
  - ADR-0046/0091: the flat root stays.
  - No new ADR is owed: single ownership is the existing seam rule
    applied.
- Domain passes: none selected (no payment, migration or dependency path).
- Standards: no matching factory statement.

## Verdict

Ready to ship. No critical finding was raised. The one major and four
minors are fixed or recorded in `1493538`. Two things stay open:

- `one_owner.py` reaches 0 only once #1106 merges in. A three-way merge
  simulation (A, then B, then C, on `origin/main`) printed `one-owner: 0
  problem(s)` with every check clean.
- The live scheduled digest and miner runs are NOT RUN (verification.md
  criterion 9).
