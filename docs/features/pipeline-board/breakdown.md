---
stage: decompose
run: feature:pipeline-board
date: 2026-08-25
---

# Breakdown: pipeline board

Progress lives in the checkboxes below — Implement checks items off as
their acceptance criteria are met. Rows follow the house grammar: a
repo-global work-order id (continuing from 0044), size class, blocking
edges, and the PRD citation. No tracker mirror for this run (reviewed at
decompose; the checkboxes are the state).

## Milestone A: Facts stated (board.py emits a correct model for this repo, fully tested)

- [ ] **WO-0045** protocol.stage_states — the full-ladder accessor — size:S, blocked by: — (PRD-0004 §Success criteria)
  - Accept: `stage_states(run_dir)` returns each run's own ordered ladder with states done|current|ahead|skipped, honoring the `ux:` conditional, `re-entry:` depth, and the Implement checkbox rule; a pinned test asserts `next_stage(run_dir)` equals the first non-done row across feature/maintenance/complete fixtures; unittest suite green.
- [ ] **WO-0046** protocol.checkbox_progress + run_ref (lifted from dashboard) — size:S, blocked by: — (PRD-0004 §Success criteria)
  - Accept: `checkbox_progress(path)` returns (checked, total) with (0, 0) for a missing file, using the seam's own checkbox grammar; `run_ref(root, run_dir)` returns product / feature:<slug> / maintenance:<slug>; `dashboard._run_ref` is replaced by a call to it with dashboard tests unchanged and green; the one-owner pre-pass reports no new group for the changed files.
- [ ] **WO-0047** board.py — the board-model CLI — size:M, blocked by: WO-0045, WO-0046 (PRD-0004 §Success criteria)
  - Accept: `python3 board.py` on this repo prints the architecture's JSON contract — active runs only, each in `runs` or `attention` and never both or neither, sorted furthest-along-first with slug tie-break, `progress` non-null only at implement, `generated` stamped; no `docs/` tree → exit 1 with a `board:`-prefixed problem string; fixture-tree unit tests cover empty (exit 0, zero runs), mixed, and unorientable cases; `python3 lint.py` and `python3 gates.py` stay green.

## Milestone B: Rendered (the approved figure draws from live facts)

- [ ] **WO-0048** the pipeline-board skill directory — size:M, blocked by: WO-0047 (PRD-0004 §Success criteria)
  - Accept: `skills/pipeline-board/SKILL.md` (frontmatter passes lint's skill checks; render contract states verbatim-JSON consumption and stop-on-tool-failure per ADR-0062), `assets/boilerplate.svg` (theme-aware scaffold demonstrating header, lane grid, capture-span, skip/ahead glyphs, attention strip, legend — tokens pointing at architecture-diagram's design-system.md), and `references/board-grammar.md` (lane geometry, glyph roster, JSON key reference, and the written aesthetic checklist derived from ux.md's conventions for Verify to apply item by item).
- [ ] **WO-0049** registration — size:S, blocked by: WO-0048 (PRD-0004 §Success criteria)
  - Accept: `protocol.UTILITY_SKILLS` includes pipeline-board; README and LEDGER rows exist and `python3 lint.py` reports 0 problems; `.claude-plugin/plugin.json` description names the skill and its version is bumped so the vendored cache re-copies.
- [ ] **WO-0050** end-to-end render on this repo — size:S, blocked by: WO-0049 (PRD-0004 §Success criteria)
  - Accept: invoking the skill in this repo yields one `.svg` at a temporary path, generated from live `board.py` output; for every run shown, its lane placement equals `next_stage` at generation time (spot-checked run by run); the file renders in light and dark (prefers-color-scheme inspected in the CSS); it contains zero external references (no http/https URLs beyond xmlns); the empty-board and attention cases are demonstrated once each from fixture trees.

## Design gaps found

None.

## Notes

(Deviations discovered during Implement get logged here, dated.)
