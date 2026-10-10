---
stage: decompose
run: feature:lean-and-polish
date: 2026-10-10
assumptions:
  - "Work-order ids start at 0146: the highest on any branch (local or origin) is number 0132, and an uncommitted worktree (.claude/worktrees/reviewer-token) already declares numbers through 0145; detector C cross-checks ids repo-wide once branches merge. Taken without user input."
  - "Owner-session ledger policy (as in docs/features/docs-audit/breakdown.md): each checked row appends one zero-cost row to docs/factory/costs.jsonl via budget_guard record, so detector G holds. Taken without user input."
---

# Breakdown: lean and polish

Progress lives in the checkboxes below. Rows follow the house grammar: a
repo-global work-order id, size class, blocking edges, and the PRD
citation. No tracker mirror for this run (ADR-0026).

## Milestone 1: Landed on main's shape

- [x] **WO-0146** Merge origin/main and put both skills on every roster — size:M, blocked by: — (PRD-0011 §Success criteria)
  - Accept: `origin/main` merged with every conflict resolved keeping both sides (`UTILITY_SKILLS` and mirror, `plugin.json` description, `LEDGER.md`, `evals/routing.json`); `lean` and `polish` as rows in the README utility table and as `<text>` rows in the "Reshaping what's built" card of `docs/assets/skill-map.svg`, the card resized so both fit; the figure rendered and looked at; `plugin.json` at `0.5.0`; `python3 factory_init.py update-manifest` run; `git diff origin/main -- evals/routing.json` shows no removed line.
- [x] **WO-0147** Hold both SKILL.md files to main's conventions — size:S, blocked by: WO-0146 (PRD-0011 §Success criteria)
  - Accept: each description is one bare strict-YAML scalar within 1024 characters (`lint.py` passes `skill_frontmatter_problems`); no harness-specific mechanism (a named harness, its tool names or paths) in either body or its references; no stage artifact, template or soft gate; every reference file linked at the step that reads it. Only what a convention requires is changed.

## Milestone 2: Verified

- [x] **WO-0148** Battery — size:S, blocked by: WO-0146, WO-0147 (PRD-0011 §Success criteria)
  - Accept: `python3 -m unittest discover tests` prints `OK`; `python3 lint.py` prints `lint: 0 problem(s)`; `python3 gates.py && python3 gates.py --selftest` prints `gates: 0 problem(s)` and `selftest: ok`.

## Coverage

Every PRD-0011 Success criterion is covered: Up to date, On every roster,
Figure legible and Packaging by row 0146; Conventions by row 0147; Battery
by row 0148. The other PRD sections carry coverage waivers.

## Notes

- 2026-10-10: the merge is the owner's (brief: no merge). The routing
  eval is owed, not run.
- 2026-10-10 (Implement): row 0146 landed as the merge commit on this
  branch; the figure card was resized from 48 to 80 units and rendered
  headless to check fit. Row 0147 needed no edit: both descriptions are
  bare scalars (980 and 909 characters, no `: ` or ` #`), neither body
  names a harness, neither has a template or soft gate, and each
  reference is linked at the step that reads it (`ladder.md` at step 2,
  `cut-list.md` at step 4; `tells.md` at steps 1 and 4, `moves.md` at
  step 3). Owner-session ledger rows appended for all three rows.
