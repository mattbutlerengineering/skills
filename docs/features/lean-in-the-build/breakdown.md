---
stage: decompose
run: feature:lean-in-the-build
date: 2026-10-10
assumptions:
  - "Work-order ids start at 0150: the highest anywhere is number 0149 (in a commit message on another branch and in the uncommitted .claude/worktrees/reviewer-token breakdown); open PRs carry none and GitHub issues titled WO-#### stop at 0076 (checked 2026-10-10). Taken without user input."
  - "No tracker mirror: no WO-#### issue is created for any row (ADR-0026, ADR-0032 one-way dispatch); the PR carries a `No work order:` waiver line and `Closes #626`. Taken from the brief."
  - "Owner-session ledger policy (as in docs/features/lean-and-polish/breakdown.md): each checked row appends one zero-cost row to docs/factory/costs.jsonl via budget_guard record, so detector G holds. Taken without user input."
  - "Three rows, cut by file rather than one per PRD criterion: Implement wiring, Review wiring (SKILL.md plus TEMPLATE.md together, since the template's clean-pass prompt names the passes), then packaging plus battery. Recommended default: one sitting per row. Taken without user input."
---

# Breakdown: lean in the build

Progress lives in the checkboxes below. Rows follow the house grammar: a
repo-global work-order id, size class, blocking edges, and the PRD
citation. No tracker mirror for this run (ADR-0026).

## Milestone 1: Both stages consult lean

- [x] **WO-0150** Implement climbs lean's ladder per item — size:S, blocked by: — (PRD-0012 §Success criteria, §User stories, §Actors)
  - Accept: `skills/implement/SKILL.md` step 4 gains exactly one bullet, between "Watch it fail for the right reason." and "Write the minimum implementation that passes…", worded as in architecture.md's Implement component: it names `../lean/references/ladder.md` in backticks (no markdown link, no copied rungs), lists lean's never-cut floor (validation, error handling, security, accessibility), and says a deliberate shortcut carries a `lean:` comment naming its ceiling and upgrade trigger and that nothing about the ladder goes into `breakdown.md`. `git diff origin/main -- skills/implement/TEMPLATE.md skills/decompose/TEMPLATE.md skills/lean` is empty; the skill's `description:` is unchanged; `python3 lint.py` prints `lint: 0 problem(s)`.
- [ ] **WO-0151** Review gains a Complexity pass — size:S, blocked by: — (PRD-0012 §Success criteria, §User stories, §Actors)
  - Accept: `skills/review/SKILL.md` step 4 reads "Review in four passes:" and a **Complexity** bullet follows **Security**, worded as in architecture.md's Review component: it names `../lean/references/cut-list.md` in backticks, files each confirmed cut as a finding (an unenumerated cut is a suspicion), makes a `lean:` marker without a trigger a finding, and hands module-shape concerns to `deepen` in one line, never refactoring inline. `skills/review/TEMPLATE.md`'s clean-pass prompt reads `<Which of correctness / design / security / complexity came back clean.>` and no other template line changes. The skill's `description:` is unchanged; `git diff origin/main -- skills/lean` is empty; `python3 lint.py` prints `lint: 0 problem(s)`.

## Milestone 2: Shipped shape, verified

- [ ] **WO-0152** Packaging and battery — size:S, blocked by: WO-0150, WO-0151 (PRD-0012 §Success criteria)
  - Accept: `.claude-plugin/plugin.json` version is `0.5.1`; `lean` is still in `protocol.py` `UTILITY_SKILLS`; `git diff origin/main --name-only` lists nothing under `factory/templates/` and no file in `factory_init.MIRRORS` (so `factory/manifest.json` is not regenerated), and no file under `evals/` other than appended results; `python3 -m unittest discover tests` prints `OK`; `python3 lint.py` prints `lint: 0 problem(s)`; `python3 gates.py && python3 gates.py --selftest` prints `gates: 0 problem(s)` and `selftest: ok`.

## Coverage

Every PRD-0012 Success criterion is covered: Implement consults the
ladder by row 0150; Review has a Complexity pass by row 0151; lean stays
a utility skill by rows 0150 and 0151 (lean's files unchanged) and row
0152 (`UTILITY_SKILLS`); Packaging and Battery by row 0152. User story 1 and the Implement agent
actor are row 0150; stories 2 and 3, the Review agent and the Owner are
row 0151. Every
architecture component appears: the Implement step-4 bullet (0150), the
Review step-4 pass and TEMPLATE.md prompt (0151), `skills/lean/**`
unchanged (0150, 0151), and `plugin.json` (0152). The other PRD sections
(Problem statement, Solution, Out of scope, Open questions) carry
coverage waivers.

## Design gaps found

None. The unchecked sibling-reference rename (lint's
`check_skill_assets` skips `../<skill>/references/...`) is a known,
pre-existing gap the architecture assigns to Review to seed in
`docs/backlog.md`; it is not a gap in this run's design.

## Notes

- 2026-10-10: the merge is the owner's (brief: no merge, no tag). The
  routing eval (`trigger_eval.py`) and `charter_replay.py` are owed, not
  run (paid).
