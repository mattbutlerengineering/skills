---
stage: verify
run: maintenance:a-long-line-stalls-the-gate
date: 2026-10-24
assumptions:
  - "No prd.md exists for a maintenance run, so the criteria walked below are defect.md's Expected clause (its two halves, linear time and an unchanged verdict) plus each work item's Accept line that no Expected half covers, plus the orchestrator's whole-tree equivalence sweep. defect.md's Work items stand in for breakdown.md (re-entry: implement), and all five are checked, so the soft gate holds."
  - "The pre-fix gates.py is taken from ae60263, not 85e1558 (the commit the timing pin's Accept line names). `git diff --quiet 85e1558 ae60263 -- gates.py` holds, so the two are the same file."
  - "The before/after timings and the equivalence sweep come from a throwaway probe in the session scratchpad. It writes `git show ae60263:gates.py` to a scratch file, loads it beside HEAD's gates.py with importlib (repo root on sys.path for gates' own imports), and calls each module's _names_unknown directly. Nothing in the repo is edited."
  - "The sweep compares _names_unknown on every line of every tracked *.md file, frontmatter and fences included. That is wider than what detector H grades (Summary lines of verification.md), so a differing line outside that surface is reported but is not a verdict change H can make."
  - "Timings are wall-clock on this machine (darwin), single runs. They show the growth shape, not a benchmark."
---

# Verification: a long line stalls the gate

## Summary

8 criteria: 8 PASS, 0 FAIL. On HEAD `20ccc5d`, detector H's zero-count
read is linear in line length: a 110 kB zero-preceded line took 38.5 s
with the pre-fix `gates.py` and takes 0.019 s now. The timing pin fails
on the pre-fix code (5.97 s against its 1.0 s bound) and passes on HEAD,
`tests.test_gates` runs 295 tests green with no existing test edited,
the payload copy is byte-identical and manifest-pinned, and the whole
battery is green with `gates: 0 problem(s)`. Across 131761 lines of the
1011 tracked markdown files, old and new verdicts differ on one line:
this run's own defect.md frontmatter, which quotes the 19-character
zero count that Implement already flagged as the window's ceiling. H
does not grade that line, so no gated verdict moves; the width question
is a finding for Review (Failures below). Next stage: Review.

## Criteria & evidence

### 1. The zero-count read grows linearly with line length

Source: defect.md Expected, first half. The probe times each module's
`_names_unknown` on `0 not run, ` repeated (every match follows a zero,
the worst case Capture measured), at four lengths.

- Check: the scratchpad probe described in the assumptions, old
  (ae60263) and new (HEAD) side by side
- Evidence:
  ```
  old has window: False new window: 17
  old _names_unknown '0 not run, ' x100 len=1100 -> False in 0.0038s
  new _names_unknown '0 not run, ' x100 len=1100 -> False in 0.0002s
  old _names_unknown '0 not run, ' x2000 len=22000 -> False in 1.4757s
  new _names_unknown '0 not run, ' x2000 len=22000 -> False in 0.0035s
  old _names_unknown '0 not run, ' x4000 len=44000 -> False in 5.9728s
  new _names_unknown '0 not run, ' x4000 len=44000 -> False in 0.0070s
  old _names_unknown '0 not run, ' x10000 len=110000 -> False in 38.4990s
  new _names_unknown '0 not run, ' x10000 len=110000 -> False in 0.0190s
  ```
  From 22 kB to 110 kB (5 times the length), the old read grows 26
  times (1.48 s to 38.5 s, quadratic) and the new one 5.4 times
  (0.0035 s to 0.019 s, linear). The verdict is `False` on both at
  every length. Capture's numbers (1.53 s, 36.8 s) and Implement's
  after-fix numbers (0.003 s, 0.018 s) reproduce.
- Result: PASS

### 2. The verdict is unchanged for every line any existing test or fixture uses

Source: defect.md Expected, second half, and the Accept line for "The
bounded window" (`tests.test_gates` passes with no existing test
edited). The branch adds 16 lines to `tests/test_gates.py` and deletes
none, so every existing zero-count test, and the selftest's fixtures,
run unedited.

- Check: `git diff --numstat` over the run's commits; `python3 -m
  unittest tests.test_gates`; `python3 gates.py --selftest`
- Evidence:
  ```
  $ git diff --numstat ae60263 20ccc5d -- tests/ gates.py factory/
  1	1	factory/manifest.json
  17	3	factory/templates/tools/factory/gates.py
  17	3	gates.py
  16	0	tests/test_gates.py
  $ python3 -m unittest tests.test_gates
  Ran 295 tests in 7.254s
  OK
  $ python3 gates.py --selftest
  selftest: ok
  ```
- Result: PASS

### 3. Equivalence sweep: old and new verdicts over every tracked markdown line

Source: the orchestrator's instruction for this stage, which tests
Expected's "same verdict" beyond the test suite. The probe runs both
`_names_unknown`s on every line of every file `git ls-files '*.md'`
lists, then explains the differing line match by match.

- Check: the scratchpad probe's sweep, then its per-match detail on the
  differing line
- Evidence:
  ```
  tracked *.md files: 1011; lines compared: 131761; longest line: 5727 chars; verdicts differing: 1
    DIFF ('docs/fixes/a-long-line-stalls-the-gate/defect.md', 7, 'assumptions: ["Capture: a defect brief, not a condition brief. The brief files it under Defect, and the verdict is never')
  match 'skipped' at 1550: zero-preceded old=True new=False; context=", such as 'zero criteria were skipped"
  tracked verification.md: 102
  ```
  The one differing line is line 7 of this run's own `defect.md`: the
  `assumptions:` frontmatter, which quotes Implement's ceiling example.
  Its one diverging match is that quotation. Detector H's roll-up
  grades only the Summary of a `verification.md`, so this line feeds no
  verdict; `python3 gates.py` is clean (criterion 8). No line of the
  102 tracked `verification.md` files differs, and no test or fixture
  line differs (criterion 2).
- Result: PASS (the divergence it shows is carried to Review under
  Failures)

### 4. The timing pin fails before the fix and passes after

Source: the Accept line for "Timing pin first (RED)": the test fails on
the pre-fix `gates.py` and passes after; its verdict half passes both
times. The probe replays the pin's exact body (a 44 kB `0 not run, `
line, verdict `False`, bound 1.0 s) against the pre-fix module.

- Check: the probe's pin replay on ae60263's `gates.py`; the real test
  on HEAD
- Evidence:
  ```
  pin on old gates.py: verdict=False (want False), elapsed=5.965s, under 1.0 s bound: False
  $ git diff --quiet 85e1558 ae60263 -- gates.py && echo "gates.py unchanged 85e1558..ae60263"
  gates.py unchanged 85e1558..ae60263
  $ python3 -m unittest -v tests.test_gates.TestEvidenceRollUp.test_a_long_zero_count_line_reads_in_linear_time
  Ran 1 test in 0.007s

  OK
  ```
  The bound sits about 6 times under the slow path and about 140 times
  over the fast one.
- Result: PASS

### 5. The window is a named constant beside the pattern, and the docstring says so

Source: the Accept line for "The bounded window". The constant sits
directly after `SUMMARY_ZERO_COUNT`, its comment says why the read is
bounded and records the ceiling as a `lean:`, and `_names_unknown`'s
docstring names the window.

- Check: grep `gates.py`; the width against the widest fixture count
- Evidence:
  ```
  $ grep -n "SUMMARY_ZERO_COUNT_WINDOW\|lean: a wider" gates.py
  277:# lean: a wider count ("zero criteria were skipped" is 19) falls outside
  279:SUMMARY_ZERO_COUNT_WINDOW = 17
  1185:    count (SUMMARY_ZERO_COUNT), read within SUMMARY_ZERO_COUNT_WINDOW
  1189:                   line, max(0, match.start() - SUMMARY_ZERO_COUNT_WINDOW),
  $ python3 -c "print(len('no criteria were '), len('zero criteria were '))"
  17 19
  ```
- Result: PASS

### 6. Payload mirror and manifest are coherent (detector E)

Source: the Accept line for "Payload mirror and manifest".
`.claude-plugin/plugin.json` does not appear in the run's diff
(ADR-0095).

- Check: `cmp`, `shasum`, the manifest entry, a count of stray patch
  files, the plugin manifest diff
- Evidence:
  ```
  $ cmp gates.py factory/templates/tools/factory/gates.py && echo "cmp: identical"
  cmp: identical
  $ shasum -a 256 gates.py factory/templates/tools/factory/gates.py
  268168c078833788639b645f15d4dbdce2a82fd1dc08e8719bbac4bf6d693e62  gates.py
  268168c078833788639b645f15d4dbdce2a82fd1dc08e8719bbac4bf6d693e62  factory/templates/tools/factory/gates.py
  $ grep -n '"templates/tools/factory/gates.py"' factory/manifest.json
  44:    "templates/tools/factory/gates.py": "268168c078833788639b645f15d4dbdce2a82fd1dc08e8719bbac4bf6d693e62",
  $ find . -name '*.orig' -o -name '*.rej' | grep -v '/.git/' | wc -l
         0
  $ git diff --stat ae60263 HEAD -- .claude-plugin/
  $
  ```
- Result: PASS

### 7. The backlog claim is in place

Source: the Accept line for "Backlog claim".

- Check: the claim on `docs/backlog.md` line 131
- Evidence:
  ```
  $ grep -n "claimed: maintenance:a-long-line-stalls-the-gate" docs/backlog.md | cut -c1-5
  131:-
  $ sed -n 131p docs/backlog.md | grep -o '(claimed: [^)]*)$'
  (claimed: maintenance:a-long-line-stalls-the-gate)
  ```
- Result: PASS

### 8. The whole-repo battery passes

Source: the Accept line for "Whole-repo checks", and the brief's
Constraints.

- Check: the four CI commands, run on HEAD `20ccc5d` with the tree clean
- Evidence:
  ```
  $ python3 run_tests.py
  tests: 3807 tests across 118 modules in 25.8s on 8 workers, 0 problem(s)
  $ python3 lint.py
  lint: 0 problem(s) across 34 skills
  $ python3 kb.py drift
  drift: 0 problem(s)
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS

## Failures

none against a stated criterion. One finding goes to Review:

- **The window's width changes a verdict for a 19-character zero
  count.** At width 17, "1 PASS; zero criteria were skipped." now names
  the unknown kind, where the whole-prefix read counted it as a zero.
  Widening to 32 restores the old verdict without touching the shapes
  the tests pin:
  ```
  '1 PASS; zero criteria were skipped.': old=False new(17)=True new(32)=False
  '1 PASS; no criteria were skipped.': old=False new(17)=False new(32)=False
  '1 PASS, 0 FAIL, 0 NOT RUN.': old=False new(17)=False new(32)=False
  ```
  The change fails open. A Summary whose only mention is such a count
  now reads as naming the unknown kind, so H would pass it over a
  disclosed NOT RUN criterion that the whole-prefix read refused: the
  divergence loosens ADR-0108's rule, against the roll-up's fail-closed
  intent. No tracked artifact
  graded by H uses the shape (criterion 3), and the brief's rule (the
  smallest green width) produced 17. Review decides whether to keep
  the brief's rule with the `lean:` comment or widen the window, which
  would cost nothing measurable in time.

## Not verified

- **Behaviour in a stamped repo after its next payload update.** Not
  exercised. Criterion 6 proves the payload copy equals the root copy
  and matches its manifest pin.
- **The pin on a slow CI runner.** Only this machine's timings were
  taken. The 1.0 s bound leaves about 140 times headroom over the
  measured 0.007 s; CI runs on push will be the first real reading.
- **Lines wider than the window in other shapes.** Beyond the one
  19-character count above, no zero count longer than 17 characters
  (a long word, a run of spaces or emphasis after the zero) was probed.
  Each would diverge the same way, toward naming.
