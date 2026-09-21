---
stage: verify
run: feature:pipeline-board
date: 2026-08-25
---

# Verification: pipeline board

## Summary

9 criteria checked, 9 pass — one (seam discipline) failed on first
check and passed after a same-day route-back to Implement, recorded
below and in the breakdown's Notes. The board states correct facts,
covers exactly the active runs, passed the operator's glance test, and
renders self-contained in both themes.

Evidence commands ran on this branch at HEAD on 2026-08-25; the
rendered file under test is the delivered live render
(`pipeline-board.svg`, 880×280, generated 2026-08-25T11:40 from
`board.py` output).

## Criteria & evidence

### Placement parity (PRD-0004)

- Check: pinned tests (`tests/test_protocol_stage_states.py` asserts
  `next_stage(run_dir)` equals the first non-done ladder row across
  feature/maintenance/complete fixtures), plus an independent live
  comparison — `board.py`'s stated current stage per run against a
  fresh `run_dirs` + `next_stage` walk written for this check, not
  sharing board.py's code path.
- Evidence:
  ```
  board says: {'docs/features/pipeline-board': 'verify', 'docs/features/first-live-dispatch': 'implement'}
  independent walk says: {'docs/features/first-live-dispatch': 'implement', 'docs/features/pipeline-board': 'verify'}
  PARITY: True
  ```
  The delivered render shows both runs at implement with 1/9 and 5/6 —
  correct at its generation time (this run's own breakdown reached 6/6
  and verify after the render was delivered; the board is an on-demand
  snapshot by design).
- Result: PASS

### Completeness (PRD-0004)

- Check: the same independent walk compared as a set (active = has a
  stage artifact, no retro.md); plus the empty and attention edge
  states exercised live against scratch trees.
- Evidence:
  ```
  COMPLETENESS (same run set): True
  ```
  Empty tree (docs/ exists, no runs):
  ```
  {"generated": "2026-08-25T14:42:19-07:00", "repo": "vtree-empty",
   "runs": [], "attention": []}
  exit=0
  ```
  Attention tree (one run dir whose prd.md is invalid UTF-8):
  ```
  runs: 0 | attention: [{'dir': 'docs/features/broken-run', 'reason':
  "'utf-8' codec can't decode byte 0xff in position 0: invalid start byte"}]
  ```
  The unorientable run lands in `attention` with a bounded reason —
  reported, never guessed, never dropped.
- Result: PASS

### Glance test (PRD-0004)

- Check: the operator, shown only the delivered SVG (no commands, no
  repo), asked "which step is each run on?" for both runs.
- Evidence: the interview exchange, recorded verbatim:
  ```
  Q: looking only at the pipeline-board SVG I sent — no commands, no
     repo — can you answer "which step is each run on?" correctly for
     both runs?
  A (operator, 2026-08-25): "Passes — both clear"
  ```
- Result: PASS

### Aesthetic checklist (PRD-0004; authored in board-grammar.md, applied item by item)

- Check: each of the 8 items from
  `skills/pipeline-board/references/board-grammar.md` against the
  delivered render's source.
- Evidence: the mechanical sweep over the render's source —
  ```
  accent uses: 8 | shadow/filter/glow: 0 | script/animation: 0 | image/font refs: 0
  serif title: 1 | timestamp line: 1 | legend rows: 6
  ```
  — read item by item:
  1. **One accent** — 8 `var(--accent)` uses, all accounted for: the
     two current-at-implement marks (ring + half-fill each), the
     `.count` class, and the legend's three swatches depicting those
     same marks. No other element uses accent. PASS
  2. **Editorial type** — `.title` Georgia serif 20, `.eyebrow`/
     `.colhead`/`.kind`/`.count` mono uppercase/small, `.slug` sans
     600 — the design system's roles, each present in the CSS. PASS
  3. **Hairlines** — `.rule { stroke: var(--rule); stroke-width: 1 }`;
     grep for shadow/filter/blur: 0 matches; no per-kind hue. PASS
  4. **Grid** — structural coordinates on the 8px grid (margins 24,
     rules 112/168/224, glyph centers 136/192, columns 248+64·i) and
     every baseline at the grammar's prescribed offsets (slug top+28,
     kind top+42, header 34/58/76); height 280 = 112+56·2+56. PASS
  5. **Dark flip** — the `@media (prefers-color-scheme: dark)` block
     overrides custom properties only (lines 26–41 of the render);
     both palettes are the family tokens, checked legible in both
     schemes at delivery. PASS
  6. **Self-contained and still** — grep script/animate: 0;
     @font-face/<image>/href: 0; ground rect paints `var(--paper)`.
     PASS
  7. **Legend and timestamp** — legend names all five glyphs the board
     uses (done, current, in-progress n/m, ahead, skipped); subtitle
     carries `snapshot 2026-08-25 11:40`; sort-order note present
     ("sorted furthest-along first"). PASS
  8. **Deliberate layout** — fixed ten-column geometry, shared
     baselines, the grammar's span/chip rules; nothing auto-laid-out.
     Corroborated by the operator's glance verdict. PASS
- Result: PASS (8/8)

### Self-containment (PRD-0004)

- Check: enumerate every URL and external-resource construct in the
  delivered file.
- Evidence:
  ```
  http://www.w3.org/2000/svg
  ```
  — the only URL is the SVG namespace identifier (never fetched);
  zero `@font-face`, `<image>`, `href`, or script constructs. Fonts
  are named system stacks with fallbacks (Georgia→serif,
  system-ui→sans-serif, ui-monospace→monospace). With nothing to
  fetch, the file renders identically with the network disabled.
- Result: PASS

### Seam discipline — no new one-owner group (breakdown orders 0046–0047; architecture's "second owner" rule)

- Check: `python3 one_owner.py` against the standing nine groups.
- Evidence: first run FAILED —
  ```
  one-owner: board.py:25 _ARTIFACTS and dashboard.py:80 _ARTIFACTS state the same value — one fact, one owner
  one-owner: 10 problem(s)
  ```
  Routed back to Implement same day: the active-run artifact roster
  lifted into the seam as `protocol.RUN_ARTIFACTS` (pinned test added),
  both callers import it, manifest regenerated (protocol.py is
  mirrored). Re-run:
  ```
  one-owner: 9 problem(s)
  ```
  — the standing baseline, no group involving this run's files.
- Result: PASS (after route-back; recorded in breakdown Notes)

### CLI contract (breakdown order 0047)

- Check: live failure path plus the fixture-tree unit tests
  (`tests/test_board.py`: empty, mixed, unorientable, sort, field
  contract).
- Evidence:
  ```
  $ python3 board.py <dir-without-docs>
  board: .../vtree-nodocs has no docs/ tree
  board: 1 problem(s)
  exit=1
  ```
  Success path prints the JSON contract (quoted under Completeness);
  suite result below covers the fixture tests.
- Result: PASS

### Registration (breakdown orders 0048–0049)

- Check: `python3 lint.py` (taxonomy, README, LEDGER, routing-eval
  surface) and plugin manifest inspection.
- Evidence:
  ```
  lint: 0 problem(s) across 25 skills
  ```
  `protocol.UTILITY_SKILLS` lists pipeline-board;
  `.claude-plugin/plugin.json` names it in the description at version
  0.2.0 (bumped so the vendored cache re-copies); routing cases
  pb-1..pb-3 in `evals/routing.json`.
- Result: PASS

### Suites, gates, and the end-to-end render (breakdown orders 0045, 0050)

- Check: full offline suite, lint, gates after all changes above.
- Evidence:
  ```
  Ran 1371 tests in 17.256s
  OK
  lint: 0 problem(s) across 25 skills
  gates: 0 problem(s)
  ```
  The render itself: generated at a temporary path from live board.py
  output, never committed; per-run placement spot-checked against the
  model (parity section); light/dark inspected in CSS (checklist item
  5); zero external references (self-containment section); empty and
  attention cases demonstrated from scratch trees (completeness
  section).
- Result: PASS

## Failures

None outstanding. One first-check failure (the tenth one-owner group)
routed back to Implement and re-verified the same day — see Seam
discipline above.

## Not verified

- **Maintenance-run rendering live** — no maintenance run was active
  at generation time, so the capture chip, the 8-rung ladder, and the
  attention strip appear only in the scaffold sample
  (`assets/boilerplate.svg`) and the grammar, not in a live render.
  The model side is fixture-tested; the drawn treatment awaits the
  first live maintenance run.
- **Viewer portability** — "opens with no repo and no tooling" was
  exercised only on this machine's renderers via the delivered file;
  no second-device or second-browser check.
- **omp invocation** — the skill was exercised under Claude Code only;
  the omp harness path is untested (true of every skill in this repo,
  per LEDGER practice).
- **"Visibly not default-mermaid"** — inherently judgment; evidence is
  the itemized checklist plus the operator's glance verdict rather
  than a mechanical check.
