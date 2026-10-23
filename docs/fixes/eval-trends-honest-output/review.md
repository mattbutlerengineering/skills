---
stage: review
run: maintenance:eval-trends-honest-output
date: 2026-10-22
assumptions:
  - "Diff scope is git diff origin/main...HEAD at 70275c4 (Verify) plus this stage's three fix commits. origin/main was fetched; the diff is eval_trends.py, the two test files, architecture.md line 170 and this run's docs."
  - "TOCTOU between the glob, symlink check, stat and read is judged noted, not exploitable: the tool is a read-only local reporter over the Owner's own checkout with no privilege boundary, and a swapped file still passes through read_file's guarded parse."
  - "Mutant sweep ran in a git archive copy under the session scratchpad (mutate_review.py), never in the working tree."
---

# Review: eval_trends prints only what it can back

## Scope

`git diff origin/main...HEAD` from `70275c4`: `eval_trends.py` (+50 -8),
`tests/test_eval_trends.py`, `tests/test_eval_trends_render.py`,
`docs/features/eval-trends/architecture.md` line 170, and this run's
docs. Predecessor `verification.md` exists. Reviewed against ADR-0115
(seam, leaf status, pin 55, "the tool only reads") and
`docs/features/eval-trends/review.md` (the Deferred section this run
partly closes). Fix commits added here: `d31820a`, `c0b8f65`, `8bb72eb`.

## Findings

### Major: a directory or FIFO named like a record crashed the tool with a traceback

- Scenario: `evals/results/trigger-2026-07-01.json` is a FIFO (or a
  directory). `cli.read_file` guards with `is_file()`, so it never
  opens the FIFO (no hang) but returns `(None, None)`. `_read_surface`
  then passed `data=None` to the row builder: `AttributeError: 'NoneType'
  object has no attribute 'get'`, exit 1 with a traceback and no output.
  Reproduced on `70275c4`. Pre-existing on main, but this run's brief is
  exactly "refuse unreadable locations as a labelled problem", and the
  size/symlink checks left this sibling hole.
- Standard: none
- Decision: fixed in `d31820a` (test first: both new tests errored red).
  Now `eval-trends: <rel> is not a regular file; not read`, exit 1.

### Minor: architecture.md grammar line 170 showed `95%` in both day slots

- Scenario: line 171 states the multi-record alternation, line 170's
  grammar contradicts it.
- Standard: none
- Decision: fixed in `c0b8f65`: both slots read `{95%|range}`.

### Minor: the symlinked-root-allowed behaviour was unpinned

- Scenario: mutant dropping the `parent != Path(".")` guard survived all
  tests, and would refuse every record under a symlinked root (a
  documented choice in defect.md Notes).
- Standard: none
- Decision: fixed in `8bb72eb` (the mutant is now killed).

### Minor: the refusal text names the bound but not where to change it

- Scenario: a legitimate plugin record above 4 MiB is refused with
  "is N bytes, above the 4194304-byte bound; not read"; the only place
  that says why 4 MiB and that it is a constant is the comment above
  `MAX_RECORD_BYTES` in eval_trends.py. An Owner must grep.
- Standard: none
- Decision: deferred. The largest real record is 70,641 bytes (59x
  headroom), so no record is refused today; the string is pinned by
  tests, and a change is a one-line edit when a real record approaches
  the bound. Seed for the Owner if plugin records start carrying large
  per-case graders.

### Minor: `assertNotIn("95%", day2)` in the render test is vacuous

- Scenario: `day2` is the expected string built in the test itself, so
  the assertion checks the test's own f-string. The real check is the
  `assertIn` of the full line, which does fail if the tool prints `95%`
  (mutant "label always 95" killed). Nothing is loosened: the amended
  pin asserts `range` where it asserted `95%`.
- Standard: none
- Decision: deferred. Harmless redundancy; removing it is churn.

## Hunt results

- **(a) Refusals.** Patterns in `READERS` are non-recursive globs, so
  no cycle or deep-tree recursion is possible. `is_symlink` is lstat on
  the full path; a symlinked parent is caught by the `rel.parents` walk
  (tested), and the root itself may be a link (now pinned). Case
  folding does not matter: nothing compares names. FIFO and directory
  fixed above; a device node behaves the same (`is_file` false). The
  size check and read are separate calls, so a file grown between them
  is read whole; noted, not exploitable here. Memory is bounded per
  file (4 MiB), files are read one at a time and only small rows are
  kept, so many 4 MiB files do not accumulate. Refusal text uses the
  root-relative `rel.as_posix()`, never an absolute path or a link
  target. Residual: `read_file`'s own `cannot read <rel>: <err>` embeds
  the OSError text, which includes the absolute path the user passed
  as root; pre-existing, the Owner's own path, not a leak.
- **(b) No-records line.** `rows` includes decompose-signals
  inventory-only records, so a root holding only those does not print
  it; a root with only refused or malformed files has problems, so it
  does not print it either; exit stays 0 for a truly empty root. `python3
  eval_trends.py docs` prints `no records found under docs` then
  `0 problem(s)`, exit 0. The empty case omits the descriptive header;
  tests pin the exact two lines. Wording says "records", consistent
  with the inventory lines.
- **(c) Hull relabel.** Only `_day_text` prints a label; a single-record
  day is a Wilson interval at Z = 1.96, which is the 95 percent
  interval (wilson(15, 30) = 0.3315 to 0.6685). The docstring of
  `day_interval` calls it a hull (honest). Architecture line 143 and
  line 11 say "hull of Wilson intervals" with no confidence level.
- **(d) Mutants** (git archive copy, 16 sweep mutants plus Verify's 7):
  killed: `>=` at the bound, parent loop off, empty condition on rows
  only or problems only, label `<=2`, label always `95%`, non-regular
  branch off, empty branch skipping `report`, absolute-root print,
  symlink wording, bound 1 KiB, `is_symlink and exists`. Survived:
  the `.` guard (killed after `8bb72eb`); `stat` error returning a
  refusal (unreachable race, not worth a pin); bound 4 GiB (the pin is
  a lower bound only, 50x the largest record; no upper pin is
  intended); `lstat` for `stat` (equivalent after the symlink check).
- **(e) Stale text elsewhere.** grep for `95%` and `hull` across code,
  CLAUDE.md, CONTEXT.md, docs/research and docs/kb finds nothing wrong
  now (the `~95%` in orchestrator.md is unrelated). History artifacts
  (feature release.md, verification.md, review.md) stay as written.
- **(f) Repo checks.** `one_owner.py`: 9 problems, none naming
  eval_trends (baseline 9). kb drift and gates clean.
- **(g) Read-only.** No write path and no import added
  (`git diff` has none); dual-membership pin still 55.
- **(h) Bound.** See the deferred minor; 4 MiB is 59x today's largest.

## Passes with no findings

Design and ADR compliance: ADR-0115 is not reopened (no import, no
source, no write; Consequences make strings commits). Security: no
secrets, no injection surface, errors root-relative. Complexity: one
helper and one constant, no cut-list item. No domain pass selected
(no payment, migration or dependency paths).

## Verdict

Ready to ship. The one major is fixed and tested; the two deferrals are
minors with reasons. Final whole-repo checks after the last fix:

```
tests: 3784 tests across 118 modules in 25.6s on 8 workers, 0 problem(s)
lint: 0 problem(s) across 34 skills
drift: 0 problem(s)
gates: 0 problem(s)
selftest: ok
```
