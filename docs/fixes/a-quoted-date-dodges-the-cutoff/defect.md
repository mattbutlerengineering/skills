---
stage: capture
run: maintenance:a-quoted-date-dodges-the-cutoff
date: 2026-10-17
re-entry: implement
origin: docs/backlog.md seed (from session 2026-10-17), the O/M date dodge
assumptions: ["seed claim spelled (claimed maintenance:a-quoted-date-dodges-the-cutoff),
  not with a fix prefix; the protocol's run-ref grammar has no fix form, and all
  16 existing fix-run claims in docs/backlog.md use the maintenance form, which is
  the format the orchestrator asked to match"]
---

# Defect: a quoted date dodges the cutoff

## Defect (or Condition)

Detectors O (`check_prd_coverage`, `gates.py:1436`) and M
(`check_capture_completeness`, `gates.py:1706`) grandfather an artifact
with `isinstance(date, str) and date < CUTOFF`, a raw string compare of
its frontmatter `date:` against `COVERAGE_ADOPTED` / `CAPTURE_ADOPTED`
(both `"2026-09-21"`).

- **Observed.** A post-cutoff date written double-quoted
  (`date: "2026-10-20"`; `"` sorts before `2`), single-quoted
  (`'` sorts before `2` too), empty (`date:`), or non-ISO
  (`date: 20/10/2026`; `/` sorts before `2`) sorts before the cutoff,
  and the detector returns `[]`: the rule is switched off by the
  spelling of a date.
- **Expected.** The comments beside both constants say a missing or
  unparseable date is not grandfathered (fail closed). Only a
  `YYYY-MM-DD` value before the cutoff (quoted or a datetime is fine)
  should be grandfathered; every other value is judged, the way detector
  H already does since #998.

A missing `date:` key is already judged (the value is `None`, not a
string).

## Reproduction / Evidence

Reproduced for real on 2026-10-17 at `e1dbb9e`, outside the repo
(scratch script `repro_om.py` in the session scratchpad). Each fixture
is a real file on disk read through the detector's real parse (O via
`knowledge_plane.parse_run`, M via `protocol.read_frontmatter`), called
through the public functions `gates.check_prd_coverage(root)` and
`gates.check_capture_completeness(root)`.

- O fixture: `tests/test_gates.py` `TestPrdCoverage.PRD` and `ROWS`
  (an uncovered, unwaived `## Out of scope` section), with only the
  `date:` line changed.
- M fixture: `TestCaptureCompleteness.defect()`'s frontmatter with
  `test_a_missing_section_is_flagged`'s body (four required sections
  missing), with only the `date:` line changed.

Output, verbatim:

```
O  date: 2026-10-20     [control: ISO post-cutoff] -> ['O: docs/features/demo/prd.md:17 PRD-0001 §Out of scope is cited by no breakdown row and carries no coverage waiver']
M  date: 2026-10-20     [control: ISO post-cutoff] -> ["M: docs/fixes/demo/defect.md missing required section 'Reproduction / Evidence'", "M: docs/fixes/demo/defect.md missing required section 'Root-cause hypothesis'", "M: docs/fixes/demo/defect.md missing required section 'Blast radius'", "M: docs/fixes/demo/defect.md missing required section 'Ruled out'"]
O  date: "2026-10-20"   [double-quoted post-cutoff] -> []
M  date: "2026-10-20"   [double-quoted post-cutoff] -> []
O  date: '2026-10-20'   [single-quoted post-cutoff] -> []
M  date: '2026-10-20'   [single-quoted post-cutoff] -> []
O  date:                [empty] -> []
M  date:                [empty] -> []
O  date: 20/10/2026     [non-ISO post-cutoff] -> []
M  date: 20/10/2026     [non-ISO post-cutoff] -> []
O  date: 2026-01-01     [control: ISO pre-cutoff] -> []
M  date: 2026-01-01     [control: ISO pre-cutoff] -> []
```

The ISO post-cutoff control is judged; all four dodge shapes are
silent; the ISO pre-cutoff control is correctly grandfathered.

**Main tree.** Every tracked `prd.md` and `defect.md` on `main` (106
files, 76 under `docs/`, the rest fixtures) parsed with
`protocol.parse_frontmatter`: **0** carry a quoted, empty or non-ISO
`date:`; 1 has no `date:` at all
(`factory/evals/fixtures/planner-issue-before-row/repo/docs/features/demo/prd.md`,
an eval fixture, already judged as missing). `python3 gates.py` on
this branch before any change: `gates: 0 problem(s)`. **This run is
prevention**: no artifact anywhere in the repo uses a dodge shape
today.

Prior evidence, now superseded by the reproduction above: the
factory-evolution-v1 review's Minor 1 (O, quoted dates, deferred to a
maintenance run), the codex-style-standards-enforcement review's
Minor 3 (M, non-ISO dates, deferred), and the fail-closed-roll-up
review (H's identical hole, fixed there in #998 only).

## Root-cause hypothesis

Hypothesis: three detectors each compare a grandfather cutoff on their
own, and the copies have drifted. H's copy was fixed in #998
(`_rollup_applies`, `gates.py:1212`, and `ROLLUP_ISO_DATE`,
`gates.py:260`); O's and M's were not. One fact (what grandfathers an
artifact by its date) has three owners.

Checked, and it holds for the fix shape: all three read `date` from the
same parser, `protocol.parse_frontmatter`, so the value is the same
shape in each (a `str` with any quotes kept, or `None` when the key is
absent):

- H: `parse_frontmatter(text).get("date")` inside `_rollup_applies`.
- O: `entry["prd_date"]`, which `knowledge_plane.parse_run` sets from
  `parse_frontmatter(prd_text).get("date")` (`knowledge_plane.py:757`).
- M: `read_frontmatter(defect).get("date")`, and `read_frontmatter` is
  `parse_frontmatter(path.read_text(...))` (`protocol.py:86`).

So one helper that takes the `date` value and a cutoff serves all three
unchanged.

## Blast radius

- **Code.** `gates.py` and its payload copy
  `factory/templates/tools/factory/gates.py` (byte-identical today,
  manifest-pinned). Stamped repos get the change on their next payload
  update.
- **Behaviour.** Changes only for a `date:` that is quoted, empty,
  non-ISO, or ISO with trailing text. Those become judged. A pre-cutoff
  date with a trailing YAML comment (`date: 2026-01-01 # x`) is
  grandfathered today and becomes judged, as it already is in H. A
  quoted or datetime pre-cutoff date stays grandfathered.
- **Who.** No artifact in this repo changes outcome (count above). A
  stamped repo that hand-wrote a quoted or non-ISO date into a
  post-cutoff `prd.md` or `defect.md` would see new O or M problems
  after the update. These are real, actionable problem strings, not
  silent failures. Severity: low. It is a gate bypass that nobody has
  used yet.
- **Since.** O since #527 and M since #517, both with cutoff
  2026-09-21.

## Ruled out

- **A different parse per detector.** This would have meant a design
  question and `re-entry: architect`. It is not the case: all three use
  `protocol.parse_frontmatter` (see the hypothesis).
- **The earlier deferral reason.** The codex-style review deferred M's
  case because it "needs a date format the protocol's frontmatter does
  not allow, and it only skips a check". The Owner reversed that
  deferral on 2026-10-17 (autorun brief, decision 2). Skipping a check
  is the whole defect.
- **The missing-key case.** Already judged in both O and M; tests
  `test_a_missing_date_is_not_grandfathered` pin it. Nothing to fix.
- **In flight.** The check ran on 2026-10-17 and nothing matches. There
  are 3 open PRs (#1000, #996, #993), and they touch only
  `docs/features/*/release.md` and `docs/kb/gates-scan-every-doc.md`.
  `gh issue list` searches for cutoff, grandfather, `COVERAGE_ADOPTED`
  and `CAPTURE_ADOPTED` returned none. `git log --all -S` over both
  copies of `gates.py` for each compare finds only the commits that
  introduced them, so no branch or worktree removes either compare.

## Work items

Re-entry is Implement, so these checkboxes are the run's breakdown.

- [x] **O dodge tests first (RED)**: in `TestPrdCoverage`, one test
  per dodge shape (double-quoted, single-quoted, empty, non-ISO
  post-cutoff), each through `check()` with `prd_date` set to the
  `parse_frontmatter`-shaped value, e.g. `'"2026-10-20"'`. Add a quoted
  pre-cutoff test and a datetime pre-cutoff test that stay
  grandfathered.
  - Accept: each dodge test asserts the exact existing string
    `O: docs/features/demo/prd.md:17 PRD-0001 §Out of scope is cited by
    no breakdown row and carries no coverage waiver`, and fails before
    the fix.
- [x] **M dodge tests first (RED)**: in `TestCaptureCompleteness`, the
  same shapes. The empty date must be written with `tree.write`
  directly, because `defect()` does `date = date or self.TODAY` and
  would turn `""` into a valid date. Add quoted and datetime pre-cutoff
  tests that stay grandfathered.
  - Accept: each dodge test asserts the four exact
    `M: docs/fixes/demo/defect.md missing required section ...`
    strings and fails before the fix.
- [x] **One helper**: one private function in `gates.py` that takes the
  frontmatter `date` value and a cutoff and answers "grandfathered?". It
  holds H's normalization: a non-string is judged; strip surrounding
  quotes and whitespace; read a datetime by its date part; grandfather
  only a `YYYY-MM-DD` before the cutoff. The ISO-date pattern
  (`ROLLUP_ISO_DATE` or a neutrally named successor) has this as its
  only user. No new module, and no cutoff value changes.
  - Accept: a grep count shows the pattern and the quote-strip appear
    once in `gates.py`. `one_owner.py` cannot see function bodies.
- [x] **Three callers**: H's `_rollup_applies`, O's
  `check_prd_coverage` and M's `check_capture_completeness` call the
  helper. No raw `date < ..._ADOPTED` compare is left.
  - Accept: the O and M tests above go GREEN. H's existing tests,
    including `test_non_iso_or_quoted_post_cutoff_date_is_judged` and
    `test_quoted_or_datetime_pre_cutoff_date_is_grandfathered`, pass
    without edits. `grep -n "date < " gates.py` finds no cutoff compare.
- [x] **Comment and ADR text**: update the `COVERAGE_ADOPTED`,
  `CAPTURE_ADOPTED` and `ROLLUP_ADOPTED` comment blocks (the last one
  says "the way O compares COVERAGE_ADOPTED") and the
  `check_capture_completeness` docstring. Append a dated amendment line
  to ADR-0107's 2026-10-17 amendment, which says "Detectors O and M keep
  their compare", and an amendment to ADR-0073, whose "unparseable date
  is NOT exempted" claim this makes true. ADR-0072 does not describe
  O's compare, so nothing changes there. No new ADR unless Implement
  finds an unrecorded decision.
  - Accept: no text left in `gates.py` or `docs/adr/` describes O or M
    as a raw-string compare.
- [x] **Payload mirror and manifest**: copy `gates.py` to
  `factory/templates/tools/factory/gates.py`. Delete any stray
  `.orig`/`.rej` files, then run `python3 factory_init.py
  update-manifest` and commit the manifest.
  - Accept: the two files are byte-identical, and detector E is clean.
- [x] **Backlog claim**: the claim on the O/M date seed in
  `docs/backlog.md` landed with this capture commit. Confirm it is
  still there and well-formed, then check this box.
  - Accept: the seed line ends in
    `(claimed: maintenance:a-quoted-date-dodges-the-cutoff)`.
- [x] **Whole-repo checks**: `python3 run_tests.py`, `python3 lint.py`,
  `python3 kb.py drift`, and `python3 gates.py && python3 gates.py
  --selftest`.
  - Accept: all pass, and `gates.py` reports `gates: 0 problem(s)` on
    the real tree with no shipped artifact edited.

## Notes

- 2026-10-17 (Capture): the `gates.py --selftest` fixtures for O and M
  are not in the brief's scope, and no work item covers them. Stamped
  repos run only the selftest, so a dodge-shape selftest case is a
  possible follow-up seed. It is not part of this run.
- Next stage: Implement (`re-entry: implement`). The design is decided
  by Owner decision 2, and H's helper is the proven pattern.
- 2026-10-17 (Implement): O RED before the helper, 4 of 4 dodge
  subtests failing, e.g. `FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged
  (tests.test_gates.TestPrdCoverage...) (date='"2026-10-20"')` with
  `AssertionError: Lists differ: [] != ['O: docs/features/demo/prd.md:17 PRD-0001[71 chars]ver']`.
  The quoted and datetime pre-cutoff tests pass before and after (guards).
- 2026-10-17 (Implement): M RED before the helper, 4 of 4 dodge
  subtests failing, e.g. `FAIL: test_non_iso_or_quoted_post_cutoff_date_is_judged
  (tests.test_gates.TestCaptureCompleteness...) (date='')` with
  `AssertionError: Lists differ: [] != ["M: docs/fixes/demo/defect.md missing req[258 chars]ut'"]`.
  The empty date is written with `tree.write` through a `dated()` helper,
  as the work item asks.
- 2026-10-17 (Implement): the helper is `_grandfathered(date, cutoff)`
  in `gates.py`, and the pattern is renamed `FRONTMATTER_ISO_DATE` (the
  brief's "neutrally named successor"). Grep counts on `gates.py`: the
  `\d{4}-\d{2}-\d{2}` pattern 1, the quote-strip test 1,
  `ROLLUP_ISO_DATE` 0, `date < ..._ADOPTED` 0. GREEN: `python3 -m
  unittest tests.test_gates` OK with H's tests unedited. Shipped
  artifacts that name the old constant (the fail-closed-roll-up run's
  architecture, breakdown and review, and the backlog seed) are history
  and stay as written.
- 2026-10-17 (Implement): comment blocks for `ROLLUP_ADOPTED`, the
  pattern, `COVERAGE_ADOPTED` and `CAPTURE_ADOPTED`, and the O and M
  docstrings, now name `_grandfathered` (landed in the fix commit with
  the code). ADR-0107 and ADR-0073 each gained one dated amendment
  paragraph at the end; ADR-0107's earlier "Detectors O and M keep their
  compare" sentence stays as written and is superseded by its new
  amendment, since ADRs are amended, not rewritten. No new ADR.
- 2026-10-17 (Implement): the backlog seed at `docs/backlog.md:123`
  still ends in `(claimed: maintenance:a-quoted-date-dodges-the-cutoff)`.
  Whole-repo checks: `tests: 3312 tests across 106 modules in 17.2s on
  8 workers, 0 problem(s)`; `lint: 0 problem(s) across 34 skills`;
  `drift: 0 problem(s)`; `gates: 0 problem(s)` and `selftest: ok`.
  `git diff --stat origin/main` over every prd.md, defect.md and
  verification.md lists only this run's own defect.md.
