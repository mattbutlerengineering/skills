---
stage: verify
run: feature:polish-blockers-and-patterns
date: 2026-11-04
---

# Verification: named blockers and code detection patterns in polish

## Summary

11 PRD criteria: 10 PASS, 1 NOT RUN, 0 FAIL. The NOT RUN criterion is the
cheapest kill test (a before-and-after code-only `polish` run), which needs a
model call the brief forbids; its exact command is below and the Owner owes
it. The shipped text and its pin meet every other criterion, and the full
battery is green, but the claim that the pattern table finds more in a
code-only run is unknown until that run happens. The WCAG ids were checked
against the WCAG 2.2 text by Implement (evidence quoted from `breakdown.md`
Notes); Verify did not re-fetch the spec.

## Criteria & evidence

### Step 5 names the eight added blockers beside the six floor items, each high severity on sight; 14 countable

- Check: `git diff eff46d2 -- skills/polish/SKILL.md` and read step 5.
- Evidence:
  ```
  +- **Named blockers are high severity on sight.** The six floor items
  +  above and the eight below outrank every other finding, whatever the
  +  surface's job. The list sets severity and adds no rule or step; it
  +  is what makes "ranked by who is locked out" checkable:
  +  - Loss of content or function at 320px wide or at 200% zoom.
  +  - Meaning carried by colour alone.
  +  - A destructive action with no confirm or undo.
  +  - Truncation with no way back to the full text.
  +  - Content hidden past a scroll edge with no cue that more is there.
  +  - An error that names no recovery.
  +  - A semantic colour used against its meaning, such as red for success.
  +  - A state change carried by motion alone.
  ```
  The six floor items precede it in the same step 5 (unchanged lines; the
  lead line says "the six floor items above and the eight below").
- Result: PASS

### `inspect` ranking puts the named blockers first

- Check: `git diff eff46d2 -- skills/polish/references/moves.md`, Hand back line.
- Evidence:
  ```
  +**Hand back.** Findings with the measured value beside the threshold it
  +missed. The named blockers of `SKILL.md` step 5 come first, whatever
  +their measure; the rest follow, ranked by who is locked out.
  ```
- Result: PASS

### Blocker text sets severity only; step count unchanged

- Check: list step headings on the branch and on `eff46d2`; read the lead line.
- Evidence:
  ```
  branch:  1. Find out… 2. Name the surface's job 3. Choose the move 4. Read the tells 5. Change it inside the system 6. Look at it — twice, then stop 7. Report, and hand off
  eff46d2: the same seven headings (lines 24, 50, 65, 86, 98, 113, 134)
  lead line: "The list sets severity and adds no rule or step"
  grep -c -E "confirm or undo|motion alone" skills/polish/references/moves.md -> 0
  ```
- Result: PASS

### `inspect` carries a 10 to 15 row pattern table beside its thresholds

- Check: read the diff of `moves.md`; count table rows (the shape pin does it).
- Evidence:
  ```
  table placed after the Do bullets (thresholds) and before **Hand back**;
  12 data rows (breakdown Notes: "the pattern table has 12 rows";
  tests.test_polish_shape real-file test: 9 tests, OK, no problem strings)
  ```
- Result: PASS

### Table includes the six PRD-named shapes

- Check: read rows 1 to 6 of the table.
- Evidence:
  ```
  | `outline: none` or `outline: 0` with no `:focus-visible` rule for the same element | CSS | 2.4.7 |
  | A click handler (`onclick`, or a click listener) on a `div` or `span` with no `role`, `tabindex` and key handler | HTML, script | 2.1.1; 4.1.2 |
  | `tabindex` greater than 0 | HTML | 2.4.3 |
  | `maximum-scale=1` or `user-scalable=no` in the viewport meta | HTML head | 1.4.4 |
  | `aria-live="assertive"` or `role="alert"` on a success or progress message | HTML, ARIA | 4.1.3 |
  | A submit button `disabled` until the form is valid, with no message saying what is missing | HTML, script | 3.3.1 |
  ```
- Result: PASS

### No row names a framework, library or framework-only attribute as its only form

- Check: read all 12 rows (above and below) for framework terms.
- Evidence:
  ```
  Rows use onclick/click listener, tabindex, aria-live, role, alt, placeholder,
  :hover, overflow, plain CSS values. No JSX/React/Vue/Angular token appears in
  any row (the diff above is the full table).
  ```
- Result: PASS

### Every accessibility row carries a WCAG 2.2 id, each checked against the WCAG 2.2 text

- Check: the pin (`polish_shape_problems`) requires a non-blank WCAG cell on accessibility rows; Implement's WO-0194 check read https://www.w3.org/TR/WCAG22/ on 2026-11-04. Verify quotes that record; it did not re-fetch.
- Evidence:
  ```
  2.4.7 Focus Visible (AA) -> outline row; 2.1.1 Keyboard (A) and 4.1.2 Name, Role, Value (A) -> click-on-div;
  2.4.3 Focus Order (A) -> tabindex; 1.4.4 Resize Text (AA) -> viewport; 4.1.3 Status Messages (AA) -> live region;
  3.3.1 Error Identification (A) -> disabled submit ("judged a fit rather than an exact match");
  1.1.1 Non-text Content (A) -> img alt; 1.3.1, 3.3.2, 4.1.2 -> placeholder-only input;
  2.5.8 Target Size (Minimum) (AA) -> 24px; 1.4.13 Content on Hover or Focus (AA) + 2.1.1 -> hover reveal;
  1.4.4 + 1.4.10 Reflow (AA) -> fixed height overflow hidden; colour-literal row carries "—".
  No id is `unverified` (breakdown.md Notes).
  ```
- Result: PASS

### Credit line in `skills/polish/` and the README credits paragraph; restated, not copied

- Check: `git diff eff46d2 -- skills/polish/references/moves.md README.md`.
- Evidence:
  ```
  moves.md: "The named-blocker list in `SKILL.md` step 5 and the code-pattern table under `inspect` borrow an idea from jakubkrehel/skills ([jakubkrehel/skills](https://github.com/jakubkrehel/skills), MIT) ... restated in this pipeline's terms and checked against the WCAG 2.2 text, not copied."
  README.md: +[jakubkrehel/skills](https://github.com/jakubkrehel/skills),   (in the credits paragraph, beside Impeccable)
  ```
  The credit sits beside the Impeccable credit in the same form. Copy-freeness
  is a judgement: the wording is this repo's (British spelling, own row
  phrasing); no source text was available to diff against in this worktree.
- Result: PASS

### `description` byte-identical to `origin/main` at `eff46d2`

- Check: `git diff eff46d2 -- skills/polish/SKILL.md`.
- Evidence:
  ```
  Single hunk "@@ -109,6 +109,18 @@" in step 5; no hunk touches line 3 (the frontmatter description).
  ```
- Result: PASS

### A test pins the shape: eight blockers, 10 to 15 rows, a WCAG id on every accessibility row

- Check: `python3 -m unittest tests.test_polish_shape`.
- Evidence:
  ```
  Ran 9 tests in 0.003s

  OK
  ```
  Per breakdown WO-0191 the module tests the exact problem strings on mutated copies (7 blockers, 9 or 16 rows, blank WCAG cell, missing section, missing table).
- Result: PASS

### `run_tests.py`, `lint.py`, `kb.py drift`, `gates.py` and `gates.py --selftest` pass

- Check: run from the worktree (`run_tests.py -j 3`, five runs share the machine).
- Evidence:
  ```
  tests: 3998 tests across 127 modules in 52.4s on 3 workers, 0 problem(s)
  lint: 0 problem(s) across 35 skills
  drift: 0 problem(s)
  gates: 0 problem(s)        (exit 0)
  selftest: ok
  ```
  No `factory/templates/**` or `.claude-plugin/` path appears in
  `git diff eff46d2 --name-only`, so no manifest regeneration was owed and the plugin version is untouched.
- Result: PASS

### Kill test: `polish` code-only on a real UI file set, before and after

- Check: not run. It needs a model call; the brief's Constraints forbid spend.
- Evidence:
  ```
  NOT RUN. Command for the Owner, same fixture dir on each ref:
  claude -p "Use the polish skill, inspect move, on <fixture dir>; the app cannot be rendered. List findings."
  once on origin/main (eff46d2) and once on feat/polish-blockers-and-patterns, then compare the findings against the table's rows.
  ```
- Result: NOT RUN

## Failures

none.

## Not verified

- Kill test above (NOT RUN, paid): whether the table makes a code-only `polish` run find more is unknown.
- WCAG ids were not re-fetched by Verify; they rest on Implement's recorded check of the W3C text.
- Routing eval not owed: the `description` is unchanged. None was run.
- Verbatim non-copying from jakubkrehel/skills is a reading of the text, not a mechanical diff.
