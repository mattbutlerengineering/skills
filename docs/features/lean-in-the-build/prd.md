---
stage: prd
run: feature:lean-in-the-build
date: 2026-10-10
id: PRD-0012
ux: not-applicable
ux-reason: the deliverable is wording in two stage skills' instruction files; no flow or screen is designed
assumptions:
  - "Interview answers came from the autorun brief (including its 2026-10-10 Amendment, which wins over earlier text) and idea.md, not a live interview. Taken without user input."
  - "Typed id PRD-0012 is the next free id: PRD-0011 is the highest in any commit message on any local or remote branch and in any worktree's docs (checked 2026-10-10). Taken without user input."
  - "The idea's success sentence ('Implement records which ladder rung each row stopped at') is superseded by the Amendment: no per-row rung record in breakdown.md; a `lean:` marker in the code is the record. Taken from the brief."
  - "Whether the stage-to-utility dependency warrants a new ADR, and whether any lint pin is needed, are left to Architect: they are design choices, and the brief makes both conditional. Taken from the brief."
  - "Plugin version goes 0.5.0 -> 0.5.1 (patch, per the Amendment). Taken from the brief."
---

# PRD: lean in the build

## Problem statement

<!-- coverage-waiver: context for the requirements below; the Success criteria carry the work every breakdown row cites -->

Agents in Implement write more than a work item needs, and nothing in the
pipeline asks "does this need to exist?" while the code is being written
or reviewed (idea.md). The `lean` utility skill asks exactly that, but no
stage consults it, so bloat is caught by eye at the merge gate or by a
later pass after it lands.

## Solution

<!-- coverage-waiver: narrates what the Success criteria check one by one -->

Implement climbs lean's ladder before writing each work item and marks
deliberate shortcuts with a `lean:` comment. Review gains a fourth pass,
Complexity, that applies lean's cut-list to the run's diff, audits the
`lean:` markers the diff added, and hands module-shape concerns to
`deepen`. `lean` itself stays a utility skill.

## Actors

- **Implement agent** — the agent working through a run's breakdown.
- **Review agent** — the agent grading a run's diff before Ship.
- **Owner** — reviews agent PRs at the merge gate.

## User stories

1. As an Implement agent, I want a step that sends me up lean's ladder
   before I write an item, so that I write only what the item needs.
2. As a Review agent, I want a Complexity pass over the run's diff, so
   that cuts are filed as findings while the author can still act.
3. As the owner, I want shortcuts to carry a `lean:` marker with its
   trigger, so that I can tell a deliberate ceiling from slop.

## Success criteria

- [ ] **Implement consults the ladder.** `skills/implement/SKILL.md`
  tells the agent to climb the ladder before writing each item, naming
  `../lean/references/ladder.md` in backticks (not copying it), keeps
  lean's never-cut floor (validation, error handling, security,
  accessibility), and says deliberate shortcuts carry a `lean:` marker.
  It adds no per-row rung record to `breakdown.md` (check: the
  breakdown template is unchanged by this run).
- [ ] **Review has a Complexity pass.** `skills/review/SKILL.md` lists
  four passes; the fourth applies `../lean/references/cut-list.md` to the
  run's diff, files each cut as a finding, requires every `lean:` marker
  the diff added to name its trigger, and routes module-shape concerns to
  `deepen` as a hand-off, never an inline refactor.
- [ ] **lean stays a utility skill.** `lean` remains in `UTILITY_SKILLS`,
  owns no artifact, is never routed to, and its files are unchanged
  unless wiring strictly needs it.
- [ ] **Packaging.** `.claude-plugin/plugin.json` is `0.5.1`, and
  `factory/manifest.json` is regenerated if any mirrored file changed.
- [ ] **Battery.** `python3 -m unittest discover tests` prints `OK`,
  `python3 lint.py` prints `lint: 0 problem(s)`, and `python3 gates.py &&
  python3 gates.py --selftest` prints `gates: 0 problem(s)` and
  `selftest: ok`. No eval definition is edited to pass.

## Out of scope

<!-- coverage-waiver: exclusions, nothing to build -->

- A CI check, hook, or new skill for bloat detection (owner chose stage
  wiring).
- Recording a ladder rung per breakdown row.
- Changing `deepen`, `audit`, `polish`, or `lean` beyond strict need;
  issues #624, #625, #627.
- Running `trigger_eval.py` or `charter_replay.py` (paid; owed, not run).

## Open questions

<!-- coverage-waiver: questions for the owner, nothing to build -->

- Does adding a stage-to-utility dependency need its own ADR, and does
  the cross-skill reference need a lint pin? — Architect, against
  ADR-0023 and lint.py's sanctioned `../<skill>/references/` pattern.
- Will the Complexity pass become a boilerplate "none" section? — the
  run's own Operate retro.
