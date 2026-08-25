---
name: pipeline-board
description: Generate the pipeline board — one self-contained theme-aware .svg placing every active run in the current repo on its current pipeline stage: swimlane rows per run, stage columns, done/current/ahead/skipped marks, Implement progress counts, in the family's light editorial style with a dark variant. Use when the user wants to see which tasks or runs are on which step, visualize pipeline progress across runs, or get oriented at a glance without running commands. Placement facts come from the shipped board.py tool, never re-derived. Not the process-dashboard console (a live server) and not a stage skill — directly invoked, owns no run artifact, changes nothing.
---

# Pipeline Board

Produce a single `.svg` — the swimlane board that answers "which step
is each task on?" in one glance. The facts are stated by `board.py`
and rendered verbatim; the taste comes from the family design system.
The board is a snapshot: generated on demand, written outside the
repo's tracked tree, never committed.

Two resources, loaded when reached:

- **`references/board-grammar.md`** — lane geometry, the glyph roster,
  the model's keys, empty/attention states, and the aesthetic
  checklist Verify applies. Shared visual values defer to
  `../architecture-diagram/references/design-system.md`.
- **`assets/boilerplate.svg`** — the working scaffold: theme-aware
  tokens and a complete four-run sample demonstrating every pattern
  (capture span, progress ring, skip marks, attention strip, legend).
  Copy it to the destination and replace the sample; never edit the
  asset itself.

Work these steps in order.

## 1. State the facts

Run the shipped tool — it lives two directories above this skill's
directory in the same checkout:

    python3 <this skill's directory>/../../board.py [repo root]

The repo root defaults to the working directory. The tool prints one
JSON document: `generated`, `repo`, `runs` (pre-sorted; each with
`ref`, `kind`, `slug`, `dir`, `ladder`, `progress`), and `attention`.

**A nonzero exit means no board.** Print the tool's problem output and
stop — never draw from guessed or remembered state, and never derive a
run's stage yourself. The tool is the only owner of placement.

Done when: the JSON is in hand, or the failure has been surfaced and
work has stopped.

## 2. Lay out the board

Read `references/board-grammar.md`. Compute the canvas height from the
run and attention counts per its formula. Note which glyphs this
particular model needs, which rows are maintenance rows (capture span,
1:1 columns from architect on), and whether the attention strip or the
empty state applies.

Done when: height is computed and every run maps to a lane plan with
no leftover states.

## 3. Render from the scaffold

Copy `assets/boilerplate.svg` to a temporary destination outside the
repo's tracked tree (never into the repo). Replace the sample: header
(repo name, active-run count, the model's `generated` timestamp as the
snapshot line), one lane per run **in the model's order**, glyph per
ladder state, progress count under an in-progress implement mark,
attention strip only when non-empty, legend kept. Update `viewBox`,
the ground rect, and the `<title>`/`<desc>` to match the real content.

Done when: the file exists and contains every run from the model
exactly once.

## 4. Verify and hand over

Walk the render against the model: every `runs` entry has one lane,
every lane's marks match its `ladder` states in order, counts equal
`progress`, attention rows match `attention`. Walk the aesthetic
checklist in the grammar reference item by item. Confirm the file
makes no external requests (the only URL is the SVG namespace).

Then show the file — open it or hand its path to the user, whichever
the session supports. Regenerate any time by running the steps again;
the board is disposable by design.

Done when: the user has the rendered board and the repo tree is
untouched.
