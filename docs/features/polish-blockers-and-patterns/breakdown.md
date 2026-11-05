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

- [ ] **Write the shape pin, red first** — add `tests/test_polish_shape.py` with `polish_shape_problems(skill_text, moves_text)` returning `polish:`-prefixed problem strings (architecture, Interfaces & contracts), and tests that it is empty on the real files and returns the exact string on mutated copies (7 added blockers, 9 or 16 table rows, a blank WCAG cell on an accessibility row, a missing `### 5.` section, a missing `## inspect` section, a missing table).
  - Accept: `python3 -m unittest tests.test_polish_shape` runs; the real-file test fails (the blocker list and table do not exist yet) and every mutation test asserts its exact problem string; a missing section or table returns one string and raises no exception.
  - Blocked by: —
- [ ] **Add the blocker list to `SKILL.md` step 5** — one lead line saying the list sets severity on sight and adds no rule or step, the six floor items kept as written, and the eight added blockers as eight list items using the anchor phrases (`320` and `200%`, `colour alone`, `confirm or undo`, `truncat`, `scroll edge`, `recovery`, `semantic colour`, `motion alone`), in the file's British spelling.
  - Accept: a reader counts 14 named blockers in step 5; the step count and the frontmatter `description` are unchanged (`git diff origin/main -- skills/polish/SKILL.md` shows no change to the `description:` line or step numbering); the blocker half of `polish_shape_problems` returns no problem on the real `SKILL.md`.
  - Blocked by: Write the shape pin, red first
- [ ] **Rank named blockers first in `inspect`** — edit `inspect`'s **Hand back** line in `skills/polish/references/moves.md` to cite step 5's list and put those findings first, then the rest "by who is locked out"; restate none of the eight.
  - Accept: the Hand back line names step 5's list and ranks it first; `moves.md` holds none of the eight anchor phrases as a second copy of the list (grep for `confirm or undo` and `motion alone` in `moves.md` finds nothing).
  - Blocked by: Add the blocker list to `SKILL.md` step 5

## Milestone 2: inspect carries a code-pattern table

- [ ] **Check the candidate WCAG 2.2 ids** — read the WCAG 2.2 success-criterion text for each candidate id in the architecture's row contract and record, per row, the id, the criterion name and whether the text supports it; mark any id that cannot be checked `unverified`.
  - Accept: a list of row → id → criterion name → supported or `unverified` exists in the Implement evidence (the breakdown Notes section or `verification.md` input), with the source URL or text consulted for each; no id is stated from recall alone.
  - Blocked by: —
- [ ] **Add the Code patterns table to `moves.md`** — under `inspect`, after the **Do** bullets and before **Hand back**, one table with columns Pattern, Where it shows, WCAG 2.2, What it costs the person; 10 to 15 rows in plain HTML, CSS or ARIA terms; the six PRD-named shapes (rows 1 to 6 of the architecture) included; ids come from the check above; introduced as the code-only reading step 6 requires.
  - Accept: the table has 10 to 15 rows; the six named shapes are present; no row names a framework or library as its only form; every accessibility row's WCAG cell is a checked id, `unverified`, and a non-accessibility row carries `—`; `python3 -m unittest tests.test_polish_shape` passes with no problem strings.
  - Blocked by: Check the candidate WCAG 2.2 ids; Rank named blockers first in `inspect`

## Milestone 3: credit, battery, and what the Owner still owes

- [ ] **Credit jakubkrehel/skills** — add a credit line in `skills/polish/references/moves.md` beside the Impeccable credit, in the same form, saying the named-blocker list and pattern table are restated, not copied, from jakubkrehel/skills (MIT); add `https://github.com/jakubkrehel/skills` to the README credits paragraph.
  - Accept: both files name jakubkrehel/skills and the idea credited; no sentence is copied from the source (restated in this repo's words); `python3 lint.py` accepts the README paragraph.
  - Blocked by: Add the Code patterns table to `moves.md`
- [ ] **Run the battery and record the NOT RUN kill test** — from the worktree run `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`, `python3 gates.py && python3 gates.py --selftest`; confirm `skills/polish/SKILL.md`'s `description:` line is byte-identical to `origin/main` at `eff46d2` (`git diff eff46d2 -- skills/polish/SKILL.md` shows no `description:` hunk); write the before-and-after code-only `polish` run down as NOT RUN with its exact command for the Owner. No manifest regeneration is expected (no `factory/templates/**` or mirrored root file is touched); run `python3 factory_init.py update-manifest` only if one is.
  - Accept: all four battery commands exit 0 with their output quoted in the Implement evidence; the description diff is empty; the kill test is recorded NOT RUN with its command, and no `claude plugin eval`, `trigger_eval.py`, `charter_replay.py` or `claude -p` was run.
  - Blocked by: Credit jakubkrehel/skills

## Design gaps found

none.

## Notes

None yet. Implement logs dated deviations here.
