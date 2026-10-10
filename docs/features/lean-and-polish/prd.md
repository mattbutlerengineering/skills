---
stage: prd
run: feature:lean-and-polish
date: 2026-10-10
id: PRD-0011
ux: not-applicable
ux-reason: the deliverable is two skill instruction files and their roster entries; no flow or screen is designed
assumptions:
  - "Interview answers came from the autorun brief and idea.md, not a live interview. Taken without user input."
  - "Typed id PRD-0011 is the next free id: PRD-0010 is the highest on any local or remote branch and in any worktree (checked 2026-10-10). Taken without user input."
  - "Plugin version 0.5.0: main is 0.4.0, skills/ changes, and no open pull request claims 0.5.0 (gh pr list showed none open, 2026-10-10). Taken from the brief."
  - "Both skills land with draft LEDGER rows and no evidence; this run's checks are structural, not a real use of either skill, so they graduate nothing (ADR-0012, ADR-0019). Taken from the brief."
---

# PRD: lean and polish

## Problem statement

<!-- coverage-waiver: context for the requirements below; the Success criteria carry the work every breakdown row cites -->

The plugin has no skill that argues for building less and none that takes
a working interface to a considered one (idea.md). Two such skills exist,
written 2026-09-29, but sit unlanded on a branch 19 commits behind main,
where the roster grew a figure and a table they do not appear in.

## Solution

<!-- coverage-waiver: narrates what the Success criteria check one by one -->

Bring the branch up to main, put `lean` and `polish` on every roster main
keeps, hold both `SKILL.md` files to main's current conventions, and open
the pull request. No skill behaviour is redesigned.

## Success criteria

- [ ] **Up to date.** `origin/main` is merged into the branch with no
  conflict marker left and no line of main's side dropped from
  `UTILITY_SKILLS`, the plugin manifest's utility list, `LEDGER.md` or
  `evals/routing.json` (check: `git diff origin/main -- evals/routing.json`
  shows additions only).
- [ ] **On every roster.** `lean` and `polish` are in `UTILITY_SKILLS` in
  `protocol.py` and its payload mirror, in `.claude-plugin/plugin.json`'s
  description, in the README utility table, as literal `<text>` rows in
  the "Reshaping what's built" card of `docs/assets/skill-map.svg`, and
  in `LEDGER.md` as draft rows with no evidence; their routing cases are
  present and no existing case is edited.
- [ ] **Figure legible.** The skill-map figure renders with both new rows
  inside their card and no overlap with the card below (check: render
  it and look).
- [ ] **Conventions.** Both descriptions are one bare strict-YAML scalar
  within 1024 characters; both bodies are harness-neutral; both are
  utility skills per ADR-0023 (no stage artifact, no soft gate, never
  routed to); each reference file is loaded at the step that needs it.
- [ ] **Packaging.** `.claude-plugin/plugin.json` is `0.5.0` and
  `factory/manifest.json` is regenerated.
- [ ] **Battery.** `python3 -m unittest discover tests` prints `OK`,
  `python3 lint.py` prints `lint: 0 problem(s)`, and `python3 gates.py &&
  python3 gates.py --selftest` prints `gates: 0 problem(s)` and
  `selftest: ok`.

## Out of scope

<!-- coverage-waiver: exclusions, nothing to build -->

- Running `trigger_eval.py` (paid; owed, not run).
- Closing or reference-closing #624, #626 or #627.
- Reworking either skill's process beyond what a convention requires.

## Open questions

<!-- coverage-waiver: questions for the owner, nothing to build -->

- Whether the gap analysis for #624/#626/#627 reshapes either skill.
