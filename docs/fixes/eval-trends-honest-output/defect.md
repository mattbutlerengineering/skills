---
stage: capture
run: maintenance:eval-trends-honest-output
date: 2026-10-22
re-entry: implement
origin: issue #1062 (docs/features/eval-trends/review.md, section Deferred), scoped by docs/fixes/eval-trends-honest-output/autorun-brief.md
assumptions: ["re-entry: implement, the skill's rule that a scoped fix with no design decision re-enters at Implement, read by the orchestrator in the brief and confirmed here: ADR-0115 is not reopened (see Notes). Not an Owner answer", "Intake is #1062 named by the brief, not an intake-marked label pick (it carries type:chore, not the intake marker), so no intake: field; the issue closes from the PR (Closes #1062)", "The hull label word is Implement's choice per the brief; Capture only fixes the requirement that the printed text claims no confidence level on a multi-record day and keeps '95%' on a single-record day (a lone Wilson interval IS a 95 percent interval). The brief's example 'range lo-hi' is the recommended default and is taken as the candidate", "The size bound's value is Implement's; Capture records the measurement (largest record 70,641 bytes) and the brief's rule (a named constant a clear multiple above it). 4 MiB (about 59x) is a candidate, not a decision", "In-flight check ran (gh pr list --state open returned [], no branch other than the shipped feat/eval-trends and this run's own mentions eval-trends): nothing matched"]
---

# Defect: eval_trends prints output it cannot back

## Defect (or Condition)

Three places where `python3 eval_trends.py` (#1056, ADR-0115) says less or
more than it knows. All three came out of the eval-trends review's
Deferred section; none blocks anything (on today's 50 records every
surface refuses, so no trend line prints).

1. **Empty or wrong root reads like a quiet result.** A root with no
   records prints five `0 record(s)` lines and REFUSED lines, then
   `0 problem(s)`, exit 0. Expected: one line, `eval-trends: no records
   found under <root>`, so an empty or mistyped root cannot be mistaken
   for a quiet one.
2. **The day-hull is labelled `95%`.** The printed `95% lo-hi` on a
   multi-record day is min lower / max upper of the reruns' own Wilson
   intervals: the span they cover, not a 95 percent interval of any
   stated level. Expected: a label that claims no confidence level for a
   multi-record day.
3. **Symlinks and size.** A symlinked record, or a symlinked directory
   above one, is followed, and a file of any size is read whole.
   Expected: a symlinked record and any file above a named size bound is
   a labelled problem (exit 1, like other malformed records), never a
   skip.

## Reproduction / Evidence

All run 2026-10-22 on `fc38d14`. Scratch work under
`/private/tmp/claude-501/-Users-mbutler-github-skills/9a27056e-40ad-47c2-a869-dd1e59a7bd2e/scratchpad/`
(`$S` below); nothing written in the repo.

**1. Empty and mistyped root.** `main()` (eval_trends.py:527-543) takes
one optional root, exits 2 only when it is not a directory, then always
renders.

```
$ python3 eval_trends.py $S/empty        # an empty directory
eval-trends: descriptive only; a REFUSED line means the records cannot support a trend claim, not that nothing changed
eval-trends: trigger: 0 record(s)
eval-trends: charter: 0 record(s)
eval-trends: output: 0 record(s)
eval-trends: plugin: 0 record(s)
eval-trends: decompose-signals: 0 record(s)
eval-trends: REFUSED trigger: too few records: need 2, have 0; no trend claim
eval-trends: REFUSED charter: too few records: need 2, have 0; no trend claim
eval-trends: REFUSED output: too few records: need 2, have 0; no trend claim
eval-trends: REFUSED plugin: too few records: need 2, have 0; no trend claim
eval-trends: REFUSED decompose-signals: not an eval run: records re-measure one git history; no trend claim
eval-trends: not computed from any record: judge drift, contamination, saturation, flake rate; see docs/research/eval-quality-metrics-2026-10-21.md
eval-trends: 0 problem(s)
exit=0
```

`python3 eval_trends.py docs` (a real but wrong directory) prints the
identical 13 lines, exit 0. A nonexistent path is already caught:
`eval-trends: '<path>' is not a directory` plus the usage line, exit 2.
So "mistyped root" splits: a path that does not exist is handled; a path
that exists and holds no records is the gap. The pinned line this touches
is the render test's all-empty list, `tests/test_eval_trends_render.py:129-132`
(and `:407` of `tests/test_eval_trends.py`, the absent-location case,
should be re-read for the same reason).

**2. The `95%` wording, exact text and every carrier.** One printing
site builds the trend text, `eval_trends.py:415`:

```
    return f"{counts}{word} ({rate}%, 95% {_pct(lo)}-{_pct(hi)}%)"
```

A single-record day prints a true Wilson interval under that label; a
multi-record day prints the hull under the same label, e.g. the render
test's expected `24..27/30 (<rate>..<rate>%, 95% <lo>-<hi>%)` shape
(`tests/test_eval_trends_render.py:269-270`).
Other `95` wording in the tool is about Wilson itself and is accurate:
`eval_trends.py:7` (module docstring, "Wilson 95 percent interval"),
`:54` (`wilson()` docstring), `:404` (the `_day_text` docstring, "the 95
percent hull": the one docstring that names the hull as 95). Carriers
of the printed label, by `grep -n -E "95%|95 percent"`:

- tests: `tests/test_eval_trends_render.py:53` (`one_day`, 95% in the
  expected string), `:270` (`day2`, the multi-record hull case),
  `:311` (the charter "sensitive" case); `tests/test_eval_trends.py:44`
  only describes Wilson (no change).
- architecture text that names the output: `docs/features/eval-trends/architecture.md:170`
  (the trend-line grammar, both days). `:12` and `:110` describe Wilson
  and stay.
- history that quotes the old label and stays as written:
  `docs/features/eval-trends/verification.md:49` (captured output),
  `docs/features/eval-trends/release.md:84`, `review.md:83,147` (the
  finding itself). The research note
  (`docs/research/eval-quality-metrics-2026-10-21.md:27,250`) says
  "Report passed over total with a 95 percent interval" and "two 95
  percent intervals which overlap": both about the Wilson interval, not
  the hull, so it names no tool output and is left alone.

**3. Symlink followed, large file read whole.** `_read_surface`
(eval_trends.py:189-209) globs, then calls `cli.read_file` (cli.py:299),
whose absence test is `is_file`, which follows links; there is no
`is_symlink` or size check anywhere in `eval_trends.py` or `cli.py`
(`grep -n "symlink"` is empty).

```
$ ls -l $S/sym/evals/results/
trigger-2026-07-01.json -> $S/outside/target.json        # target outside the root
$ python3 eval_trends.py $S/sym
eval-trends: trigger: 1 record(s), 2026-07-01..2026-07-01, 1 day(s), cases 13-13 per record
exit=0
```

The record outside the root was read and counted. A symlinked directory
is followed too: a copy of `decompose-2026-07-01` placed outside the
root and linked in as `evals/results/output/decompose-2026-07-01`
printed `eval-trends: output: 1 record(s), 2026-07-01..2026-07-01 ...`.

Size, a real record padded to 209,719,004 bytes (200 MiB) and run through
the tool, against the same record unpadded:

```
200 MiB record:  trigger: 1 record(s) ... ; 0 problem(s); 0.34 real; 442,597,376 maximum resident set size
unpadded record: trigger: 1 record(s) ... ;                         23,445,504 maximum resident set size
```

Read whole, accepted, no problem: about 19x the resident memory for a
file the tool would parse and then ignore.

**Measured sizes (bytes, `stat -f %z`), the bound's input.**

| Location | files | largest |
|---|---|---|
| `evals/results` (recursive, incl. `output/*/grading.json`) | 47 | 70,641 (`trigger-2026-10-10-3.json`) |
| `plugin-evals/records` | 3 | 48,554 (`2026-10-10-3.json`) |
| `tests/fixtures/eval_trends_2026_10_21` | 50 | 70,641 (the same file frozen) |

Largest real record anywhere: 70,641 bytes (about 69 KiB). Symlinks
among them: 0 (`find ... -type l | wc -l` is 0).

## Root-cause hypothesis

Hypothesis, for all three: the tool was built to be descriptive and
read-only on a trusted local tree, so the review treated each as minor
and the first release took the architecture's strings and the shared
`cli.read_file` as given. (1) The render path has no "nothing was found"
case because the all-REFUSED output was judged unambiguous. (2) The hull
reused the Wilson label because the architecture spec wrote `95% lo-hi`
for both a single record and a hull. (3) `cli.read_file`'s contract
(ADR-0075) is absent-or-regular-file with no link or size policy, and
`_read_surface` adds none. The fix for (3) belongs in `_read_surface`,
not in the shared `cli.read_file`, which has other callers.

## Blast radius

The Owner alone, running a read-only local tool on their own tree.
(1) is a misread on a wrong root; (2) mislabels one number on a
multi-record day (none prints today); (3) is a robustness gap with no
exposure on a tree the Owner controls. No data is written, no gate
reads the tool. Small: Review and Ship scale down.

## Ruled out

- **Future-dated records.** Accepted if the file name agrees: rejecting
  them would make output depend on the clock. Stays a documented decision.
- **Multiple-comparison correction.** One first-vs-last comparison per
  group; the header and verdict suffix already say so. Stays documented.
- **Fixing the symlink and size policy in `cli.read_file`.** Shared by
  other readers (ADR-0075); changing it widens the run. Local to
  `_read_surface`.
- **Changing the Wilson interval or the single-record label.** A lone
  record's interval is a real 95 percent Wilson interval; only the
  multi-record hull is mislabelled.
- **A new ADR.** See Notes.

## Work items

Test first for each, in `tests/test_eval_trends*.py`, with the reason
recorded in the commit body wherever a pinned string changes.

- [ ] **No-records line** — when `load_rows` yields no rows and no
  problems, print `eval-trends: no records found under <root>` (root as
  given); decide in Implement whether the per-surface detail still
  follows (recommended: the one line plus the unchanged `0 problem(s)`
  report, exit 0, since an empty root is not a malformed record).
  - Accept: `python3 eval_trends.py $S/empty` and `... docs` print the
    line naming the root; a root with at least one record is unchanged;
    `tests/test_eval_trends_render.py:129-132` amended with the reason.
- [ ] **Honest hull label** — print a label that claims no confidence
  level for a multi-record day (candidate `range lo-hi`, per the brief),
  keep `95% lo-hi` for a single-record day, and fix the `_day_text`
  docstring ("95 percent hull") at eval_trends.py:404.
  - Accept: a test pins the multi-record text (render test `:270`) with
    no `95%` in it, and the single-record text (`:53`, `:311`) still has
    it; `grep -n "95% " eval_trends.py` shows only the single-record
    path; `architecture.md:170` updated for the new text.
- [ ] **Refuse a symlinked record** — in `_read_surface`, a matched path
  that is a symlink, or has a symlinked parent below the root, is one
  labelled problem, no row, exit 1.
  - Accept: scratch repro of the file link and the directory link each
    print `eval-trends: <rel> ...` problem and exit 1, not a record.
- [ ] **Refuse an oversize record** — a named constant (candidate 4 MiB,
  about 59x the largest real record at 70,641 bytes), checked by `stat`
  before the read; above it is one labelled problem, exit 1, never read.
  - Accept: a file one byte over the bound is refused without being
    parsed; one at the bound is read; the real 50 records still produce
    the unchanged output (`0 problem(s)`); the measurement is recorded
    in the constant's comment.
- [ ] **Docs for the documented non-changes** — state in the tool
  docstring or the research note nothing new; the future-dated and
  multiple-comparison decisions stay where review.md and the header put
  them.
  - Accept: no edit needed beyond the above (checked, not assumed).

## Notes

- **Re-entry depth: implement.** No design decision is open. ADR-0115
  fixes the seam (`eval_schema.parse_results_stem`), the leaf and
  root-only status, the one new import pair (`eval_trends` to `cli`,
  pin 55) and "the tool only reads". Its Consequences say: "A change to
  the pin set or to what the tool reads is a new ADR. A change to a
  threshold, a refusal string or the output order is a commit." This run
  adds no import (pin stays 55), adds no source and writes nothing. The
  no-records line and the relabel are output strings, so by the ADR's own
  sentence they are commits. The symlink and size refusals shrink what
  the tool will read rather than add a source; read strictly that is
  "what the tool reads", so this is a judgement, not a certainty:
  Implement should surface it if it needs a new constant beyond the
  size bound or any new import. The relabel touches the architecture
  text (`architecture.md:170`), which is a feature-run artifact; the
  label is an output string, not a decision of the ADR.
- LEDGER.md unchanged (ADR-0012, ADR-0019); `plugin.json` untouched
  (ADR-0095); stdlib only; no paid run.
