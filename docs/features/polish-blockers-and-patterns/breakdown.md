---
stage: decompose
run: feature:polish-blockers-and-patterns
date: 2026-11-04
assumptions:
  - "Interview answered from the autorun brief, prd.md and architecture.md; the skill supplies no named options here, so no default was taken."
  - "No tracker mirror: the brief's Tracker section says Decompose creates no work-order issues, so no item carries a (tracker: #id) reference."
  - "No docs/factory/decompose-lessons.jsonl exists in this worktree; drafted without lessons."
---

# Breakdown: named blockers and code detection patterns in polish

Progress lives in the checkboxes below — Implement checks items off as their
acceptance criteria are met.

## Milestone 1: polish names its blockers, and a test pins them

- [x] **WO-0191** Write the shape pin, red first — size:S, blocked by: — (PRD-0019 §Success criteria). Add `tests/test_polish_shape.py` with `polish_shape_problems(skill_text, moves_text)` returning `polish:`-prefixed problem strings (architecture, Interfaces & contracts), and tests that it is empty on the real files and returns the exact string on mutated copies (7 added blockers, 9 or 16 table rows, a blank WCAG cell on an accessibility row, a missing `### 5.` section, a missing `## inspect` section, a missing table).
  - Accept: `python3 -m unittest tests.test_polish_shape` runs; the real-file test fails (the blocker list and table do not exist yet) and every mutation test asserts its exact problem string; a missing section or table returns one string and raises no exception.
  - Blocked by: —
- [x] **WO-0192** Add the blocker list to `SKILL.md` step 5 — size:S, blocked by: WO-0191 (PRD-0019 §Problem statement, §Solution, §Actors). One lead line saying the list sets severity on sight and adds no rule or step, the six floor items kept as written, and the eight added blockers as eight list items using the anchor phrases (`320` and `200%`, `colour alone`, `confirm or undo`, `truncat`, `scroll edge`, `recovery`, `semantic colour`, `motion alone`), in the file's British spelling.
  - Accept: a reader counts 14 named blockers in step 5; the step count and the frontmatter `description` are unchanged (`git diff origin/main -- skills/polish/SKILL.md` shows no change to the `description:` line or step numbering); the blocker half of `polish_shape_problems` returns no problem on the real `SKILL.md`.
  - Blocked by: Write the shape pin, red first
- [x] **WO-0193** Rank named blockers first in `inspect` — size:S, blocked by: WO-0192 (PRD-0019 §User stories). Edit `inspect`'s **Hand back** line in `skills/polish/references/moves.md` to cite step 5's list and put those findings first, then the rest "by who is locked out"; restate none of the eight.
  - Accept: the Hand back line names step 5's list and ranks it first; `moves.md` holds none of the eight anchor phrases as a second copy of the list (grep for `confirm or undo` and `motion alone` in `moves.md` finds nothing).
  - Blocked by: Add the blocker list to `SKILL.md` step 5

## Milestone 2: inspect carries a code-pattern table

- [x] **WO-0194** Check the candidate WCAG 2.2 ids — size:S, blocked by: — (PRD-0019 §Open questions). Read the WCAG 2.2 success-criterion text for each candidate id in the architecture's row contract and record, per row, the id, the criterion name and whether the text supports it; mark any id that cannot be checked `unverified`.
  - Accept: a list of row → id → criterion name → supported or `unverified` exists in the Implement evidence (the breakdown Notes section or `verification.md` input), with the source URL or text consulted for each; no id is stated from recall alone.
  - Blocked by: —
- [x] **WO-0195** Add the Code patterns table to `moves.md` — size:M, blocked by: WO-0193, WO-0194 (PRD-0019 §Success criteria). Under `inspect`, after the **Do** bullets and before **Hand back**, one table with columns Pattern, Where it shows, WCAG 2.2, What it costs the person; 10 to 15 rows in plain HTML, CSS or ARIA terms; the six PRD-named shapes (rows 1 to 6 of the architecture) included; ids come from the check above; introduced as the code-only reading step 6 requires.
  - Accept: the table has 10 to 15 rows; the six named shapes are present; no row names a framework or library as its only form; every accessibility row's WCAG cell is a checked id, `unverified`, and a non-accessibility row carries `—`; `python3 -m unittest tests.test_polish_shape` passes with no problem strings.
  - Blocked by: Check the candidate WCAG 2.2 ids; Rank named blockers first in `inspect`

## Milestone 3: credit, battery, and what the Owner still owes

- [x] **WO-0196** Credit jakubkrehel/skills — size:S, blocked by: WO-0195 (PRD-0019 §Success criteria). Add a credit line in `skills/polish/references/moves.md` beside the Impeccable credit, in the same form, saying the named-blocker list and pattern table are restated, not copied, from jakubkrehel/skills (MIT); add `https://github.com/jakubkrehel/skills` to the README credits paragraph.
  - Accept: both files name jakubkrehel/skills and the idea credited; no sentence is copied from the source (restated in this repo's words); `python3 lint.py` accepts the README paragraph.
  - Blocked by: Add the Code patterns table to `moves.md`
- [x] **WO-0197** Run the battery and record the NOT RUN kill test — size:S, blocked by: WO-0196 (PRD-0019 §Success criteria, §Out of scope). From the worktree run `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`, `python3 gates.py && python3 gates.py --selftest`; confirm `skills/polish/SKILL.md`'s `description:` line is byte-identical to `origin/main` at `eff46d2` (`git diff eff46d2 -- skills/polish/SKILL.md` shows no `description:` hunk); write the before-and-after code-only `polish` run down as NOT RUN with its exact command for the Owner. No manifest regeneration is expected (no `factory/templates/**` or mirrored root file is touched); run `python3 factory_init.py update-manifest` only if one is.
  - Accept: all four battery commands exit 0 with their output quoted in the Implement evidence; the description diff is empty; the kill test is recorded NOT RUN with its command, and no `claude plugin eval`, `trigger_eval.py`, `charter_replay.py` or `claude -p` was run.
  - Blocked by: Credit jakubkrehel/skills

## Design gaps found

none.

## Notes

- Implement (2026-11-04), deviation: Decompose wrote rows with no work-order id or PRD citation, so detector O (PRD-COVERAGE) failed on this run's own breakdown before any code landed. Rows now carry WO-0191 to WO-0197 (the highest id on any branch or sibling worktree was 0188) and cite PRD-0019 sections. Still no tracker mirror. The ids are provisional against the sibling runs and renumber at merge on a collision (brief, Parallel runs).
- Implement (2026-11-04), deviation: the pattern table has 12 rows, not 13. Candidate row 11 (animation with no `prefers-reduced-motion` rule, 2.3.3) was dropped: 2.3.3 is Level AAA in the WCAG 2.2 text, and step 5's floor already requires a reduced-motion path. Rows 1 to 6 are the PRD-named shapes, rows 7 to 10 and 12 the architecture's, the last row (colour literal) carries `—`.
- Implement (2026-11-04), deviation: the pin lowercases blocker list items before matching anchors, so "Truncation" matches `truncat`.
- Implement (2026-11-04), WCAG 2.2 check (WO-0194). Source: https://www.w3.org/TR/WCAG22/ fetched 2026-11-04; criterion titles and levels read from its text.
  - 2.4.7 Focus Visible (AA): "Any keyboard operable user interface has a mode of operation where the keyboard focus indicator is visible." Supports row `outline: none`.
  - 2.1.1 Keyboard (A): all functionality operable through a keyboard interface. Supports the click-on-`div` row.
  - 4.1.2 Name, Role, Value (A): name and role programmatically determinable for UI components. Supports the click-on-`div` row and the placeholder-only `input` row.
  - 2.4.3 Focus Order (A): focusable components receive focus in an order that preserves meaning and operability. Supports positive `tabindex`.
  - 1.4.4 Resize Text (AA): text resizable up to 200 percent without loss of content or functionality. Supports `maximum-scale=1` and the fixed-height `overflow: hidden` row.
  - 1.4.10 Reflow (AA): no loss of information or functionality at 320 CSS pixels. Supports the fixed-height row.
  - 4.1.3 Status Messages (AA): status messages programmatically determined through role or properties so assistive technology presents them without focus. Supports the live-region row; that the severity should be polite rather than assertive is a technique, not the criterion text, so the cell cites the criterion only.
  - 3.3.1 Error Identification (A): an automatically detected input error is identified and described in text. Supports the disabled-submit row to the extent a dead button names no error; supported, judged a fit rather than an exact match.
  - 1.1.1 Non-text Content (A): non-text content has a text alternative. Supports the `img` without `alt` row.
  - 1.3.1 Info and Relationships (A) and 3.3.2 Labels or Instructions (A): labels or instructions provided when content requires user input. Support the placeholder-only `input` row.
  - 2.5.8 Target Size (Minimum) (AA): pointer target at least 24 by 24 CSS pixels, with listed exceptions. Supports the under-24px row.
  - 1.4.13 Content on Hover or Focus (AA): content shown on hover or focus is dismissible, hoverable and persistent. Supports the hover-reveal row alongside 2.1.1.
  - 2.3.3 Animation from Interactions (AAA): checked; dropped from the table as above. No id is `unverified`.
- Implement (2026-11-04), NOT RUN (kill test, owed to the Owner; no model call this run): a code-only `polish` run on a UI fixture before and after this change, to see whether the pattern table finds more. Command shape: `claude -p "Use the polish skill, inspect move, on <fixture dir>; the app cannot be rendered. List findings."` once on `origin/main` (`eff46d2`) and once on `feat/polish-blockers-and-patterns`, with the same fixture, then compare the findings against the table's rows.
- Implement (2026-11-04), deviation: detector G reads a checked row as a merged work order owed a `docs/factory/costs.jsonl` line, so each check-off appended one zero-cost `owner-session:unmetered` row via `budget_guard record` (the precedent of the 2026-10-06 and 2026-08-13 Notes in other runs). The tokens and cost are unmetered, not zero spend; the stage agent's own usage is not visible to it.
