---
stage: verify
run: feature:review-interface-pass
date: 2026-11-04
---

# Verification: An Interface domain pass for review

## Summary

11 criteria checked (all ten PRD criteria, with the hand-walk criterion
counting as its three verdicts in one, plus the breakdown's two extra
checks folded into the battery and no-spend criteria): 11 PASS, 0 FAIL.
The battery exits 0 on every command from the worktree. Not verified, and
unknown: the false-positive rate of the pass on real adopter UI diffs (no
such diff exists; the PRD makes it out of scope), and the pass's behavior
when a live reviewer agent runs it (the hand-walk reads the rules, it does
not run a model, because the brief forbids paid runs). NOT RUN: no
criterion needed a paid command, so none is labelled NOT RUN; the one
command the Owner could run later is named under "Not verified". The
`description` is byte-identical, so no routing eval is owed.

## Criteria & evidence

### The Interface row exists in `domain-reviewers.md`, selected by UI paths, and links a reference that resolves

- Check: grep the row; run the pin test (row extensions, link resolution, selection by path).
- Evidence:
  ```
  21:| Interface | a UI file, by extension only: `*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, `*.astro`, `*.css`, `*.scss`, `*.sass`, `*.less`, `*.html`, `*.htm`, `*.erb`, `*.hbs`, `*.ejs`, `*.njk`, `*.twig`, `*.liquid`, `*.jinja`, `*.jinja2`, `*.pug`, `*.cshtml`, `*.razor` | `interface.md` (a link) |
  test_interface_reference_names_signals ... ok
  test_interface_row_extensions ... ok
  test_pass_names ... ok
  test_read_links_resolve ... ok
  test_selection_by_path ... ok
  Ran 5 tests in 0.001s
  OK
  ```
- Result: PASS

### The reference tells the reviewer to read the removed side of every hunk for the eight signals

- Check: read `skills/review/references/interface.md`; grep each signal; the pin test's `test_interface_reference_names_signals` passes (above).
- Evidence:
  ```
  32: 1. **Find.** Read the removed side of every hunk in the selected paths:
  33:    `git diff -U0 -M <base>...HEAD -- <selected paths>`, then take the
  signal hit counts in interface.md: aria-label 5, alt= 2, :focus-visible 4,
  outline 6, tabindex 3, prefers-reduced-motion 2, "logical propert" 1,
  lang= 2, dir= 2, token 6
  ```
- Result: PASS

### The reference clears a removed signal on an equivalent replacement and names the limit (different selector or element never clears)

- Check: read lines 38-59 of the reference.
- Evidence:
  ```
  38: 2. **Clear.** A candidate is cleared when an equivalent replacement is on
  39:    the added side for the same element or selector:
  ...
  56:    A replacement on a different selector or element never clears. It is a
  57:    finding.
  ```
- Result: PASS

### Every finding gets a status by cause, mapped onto the existing severity model with no new severity

- Check: read lines 60-83 of the reference; grep the skill's severity words.
- Evidence:
  ```
  63:   - **Regression**: ...
  65:   - **Introduced**: ... Three forms only ...
  70:   - **Pre-existing**: ... Report at most three, after the other two ...
  75:   Severity is the skill's, set by the scenario, never by the status.
  82:   Pre-existing is **minor** and never blocks. There is no new severity
  83:   and the fix loop does not change.
  skills/review/SKILL.md:70:7. **Rank and verify.** Order findings by severity (critical / major /
  ```
- Result: PASS

### Hand-walked over fixture diffs, the rules give the three verdicts

- Check: manual walk of the three worked examples (reference lines 87-100) against the Find / Clear steps. Reads the rules; no model run.
  1. Diff deletes `aria-label="Close"` from an icon-only `<button>`, no replacement: Find takes the `-` line as a candidate; the element stays (not dropped with its owner); Clear finds no `aria-labelledby`, `<label>` or visible text on the added side; so it is a finding, Regression, Critical (only accessible name of an icon-only control).
  2. `.btn:focus { outline: none }` becomes `.btn:focus-visible { box-shadow: ... }`: candidate is `outline`; a `box-shadow` is added on the same selector and state (and `:focus` to `:focus-visible` counts); cleared, nothing reported.
  3. The same swap on a different selector (`outline` removed from `.btn:focus-visible`, `box-shadow` added to `.card:hover`): Clear requires the same element or selector, line 56 says a different selector never clears; finding, Regression.
- Evidence:
  ```
  87: - **A bare deletion reports.** ... Report `### Critical: interface — regression — close button has no accessible name`.
  92: - **A same-selector swap is silent.** ... The ring is on the same selector and state, so the candidate clears. Report nothing.
  96: - **A different-selector swap reports.** ... The replacement is on another selector, so `.btn` lost its only focus indicator. Report `### Critical: interface — regression — .btn has no focus indicator` ...
  ```
- Result: PASS

### A changed-path list with no UI path selects no Interface pass; the review reports "domain passes: none selected"

- Check: the pin test's `test_selection_by_path` (README.md, `skills/x/templates/TEMPLATE.md`, `src/api.ts`, `package.json`, `migrations/001.sql` do not match; `src/App.tsx`, `styles/main.scss`, `views/show.html.erb`, `a/Button.vue` do); grep the unchanged "none selected" text.
- Evidence:
  ```
  test_selection_by_path (tests.test_review_domain_table.DomainTableTest.test_selection_by_path) ... ok
  35: No match means no domain pass. Say so in "Passes with no findings":
  36: "domain passes: none selected".
  ```
- Result: PASS

### The pass reads and reports on the diff only; no rendered page or browser

- Check: grep the reference for browser/rendered words.
- Evidence:
  ```
  10: The pass reads the diff and the changed files only. It never renders
  11: anything and runs no browser. Whether a rendered surface works (contrast,
  115: - No rendered or browser check. Use `polish` for that.
  ```
- Result: PASS

### `SKILL.md` and the README credits paragraph each credit the source, restated; `NOTICE` unchanged

- Check: grep the credit lines; `git diff --stat eff46d2...HEAD -- NOTICE`. Whether the wording is restated rather than copied is a reading, not a script; the text shares no sentence with the research note.
- Evidence:
  ```
  skills/review/SKILL.md:59:   deleted accessibility signals is restated from jakubkrehel/skills'
  skills/review/SKILL.md:60:   `interface-review` ([jakubkrehel/skills](https://github.com/jakubkrehel/skills),
  README.md:158:[jakubkrehel/skills](https://github.com/jakubkrehel/skills),
  README.md:163:— and each skill says what it borrowed. `review` borrowed jakubkrehel/skills'
  README.md:164:removed-side reading of a diff (MIT, restated).
  git diff --stat eff46d2...HEAD -- NOTICE .claude-plugin/plugin.json | wc -l  -> 0
  ```
- Result: PASS

### `review`'s frontmatter `description` is byte-identical to `origin/main`'s

- Check: diff the `description:` line at the run's base `eff46d2` against the worktree.
- Evidence:
  ```
  diff <(git show eff46d2:skills/review/SKILL.md | grep -m1 '^description:') <(grep -m1 '^description:' skills/review/SKILL.md) && echo IDENTICAL
  IDENTICAL
  ```
- Result: PASS

### The domain table is pinned by a stdlib test that fails when the row or reference goes missing, and the battery passes

- Check: the pin test (written red first per commit `295cf65 test(review): pin the domain table and the Interface selection (red)`; not re-run red here, the commit order is the evidence), then the battery from the worktree.
- Evidence:
  ```
  python3 run_tests.py -j 3
  tests: 3994 tests across 127 modules in 48.7s on 3 workers, 0 problem(s)
  python3 lint.py
  lint: 0 problem(s) across 35 skills
  python3 kb.py drift
  drift: 0 problem(s)
  python3 gates.py
  gates: 0 problem(s)
  python3 gates.py --selftest
  selftest: ok
  ```
- Result: PASS

### No paid model run is made

- Check: the diff against the base touches no eval definition or result and no script; this stage ran only the five battery commands and read-only greps. No `claude plugin eval`, `trigger_eval.py`, `charter_replay.py` or `claude -p` was run by this stage. The earlier stages' commands are not logged anywhere this stage can read; the diff shows none of their effects.
- Evidence:
  ```
  git diff --name-only eff46d2...HEAD
  README.md
  docs/backlog.md
  docs/features/review-interface-pass/{architecture,autorun-brief,breakdown,idea,prd}.md
  skills/review/SKILL.md
  skills/review/references/domain-reviewers.md
  skills/review/references/interface.md
  tests/test_review_domain_table.py
  ```
- Result: PASS

### (Breakdown) No factory-template, mirrored-root, plugin or `polish` change, so no manifest update is owed

- Check: the file list above against `factory/templates/**`, mirrored root files, `.claude-plugin/plugin.json`, `skills/polish/`.
- Evidence:
  ```
  git diff --stat eff46d2...HEAD -- skills/polish factory .claude-plugin NOTICE | wc -l  -> 0
  ```
  The one root file touched, `README.md`, is not a mirrored file in the changed list (`kb.py drift` exits 0 above).
- Result: PASS

### (Breakdown) Every item is checked off

- Check: read `breakdown.md`.
- Evidence:
  ```
  - [x] **Domain-table pin** ... - [x] **Interface reference** ... - [x] **Interface row** ...
  - [x] **Credit lines** ... - [x] **Battery and no-spend check** ...
  ```
- Result: PASS

## Failures

none.

## Not verified

- Unknown: how many false positives the pass produces on real adopter UI diffs. No such diff exists (PRD, Out of scope); the PRD states the criterion as an outcome on hand-walked fixtures, which passed.
- Unknown: whether a live reviewer agent applies the reference as the hand-walk reads it. That needs a model run, which the brief forbids. If the Owner wants it, there is no existing eval case for this pass; one would have to be written, and nothing here runs one.
- The "restated, nothing copied" wording is judged by reading, not by a script.
- The red-first order of the pin test rests on the commit order (`295cf65` before `2d86824`), not a re-run on the old table.
- The status-by-cause section lists "Pre-existing" with a cap of three; the PRD named "the set Architect settles on", and this was checked against `architecture.md`'s set only by the reference's own text, not by a test.
