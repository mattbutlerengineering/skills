---
stage: review
run: feature:pipeline-board
date: 2026-08-25
---

# Review: pipeline board

## Scope

The run's diff, `main...HEAD` on `feature/pipeline-board` (merge base
622e7c03, 8 commits): 25 files, +2644/−348. Code examined line by
line: `protocol.py` (five new public accessors + `RUN_ARTIFACTS` +
taxonomy row), `board.py` (new, whole file), `dashboard.py`
(delegation delta), `factory.py` (verb row), the three new test
modules, `skills/pipeline-board/` (SKILL.md, boilerplate.svg,
board-grammar.md), and the registration surfaces (README, LEDGER,
plugin.json, `evals/routing.json`, ADR-0062 + index, costs.jsonl,
mirror manifest). Run artifacts read for contract conformance, not
re-verified.

## Findings

### Minor: appending three routing-eval cases rewrote all 124 existing case definitions' layout

- Scenario: `evals/routing.json` went from a compact two-line-per-case
  format to fully expanded (+807/−311 lines) for what is semantically a
  three-case append. Checked at the JSON level against main: 124 → 127
  cases, zero removed, zero mutated, version unchanged — content is
  intact, so this is blame pollution, not an eval-honesty problem.
- Decision: deferred — re-compacting would churn the same lines a
  second time for zero semantic gain; the JSON-level equivalence check
  above is recorded here as the evidence a future reader needs.

### Minor: `board.gather`'s all-done-ladder skip is unreachable

- Scenario: the `continue  # complete without retro.md` branch can
  never run — operate's artifact IS `retro.md` in both orientation
  tables, so any ladder that reads all-done implies `retro.md` exists,
  and those runs are skipped two lines earlier. House discipline says
  impossible states get an invariant note, not guard code.
- Decision: deferred — the guard is two lines keyed to exactly the
  cross-table invariant that would have to change for it to matter,
  and its comment names the case; removing it buys nothing and costs
  the safety net if a future table edit breaks the invariant.

### Minor: deleting dashboard's `_ARTIFACTS` block left one blank line before `repo_set` where house style uses two

- Scenario: pure style decay from this run's route-back edit; no
  behavior change.
- Decision: fixed — blank line restored in this review's commit; suite
  re-run green.

### Minor (operational, routes to Ship): the installed plugin cache cannot run the skill until main is pushed and the plugin updated

- Scenario: the vendored cache is version 0.1.0 and contains no
  `board.py` (checked live: `.../idea-to-prod/0.1.0/board.py: No such
  file or directory`). Invoking the skill from the cache today would
  fail its step-1 tool run — correctly, per ADR-0062's stop-on-failure
  rule, but the skill is unusable from the cache until the 0.2.0 bump
  (already in this run) propagates via push + `claude plugin update`.
- Decision: deferred to Ship — this is the known version-gated re-copy
  mechanism working as designed; Ship's checklist owns the propagation
  steps. The run's own renders used the working tree, so no evidence
  is invalidated.

## Passes with no findings

- **Correctness** — clean beyond the unreachable-branch note.
  `stage_states`' skip semantics were traced against both completion
  helpers (`skipped` is only consulted when `complete` already holds,
  so a rule-excused stage can never mask a genuinely missing current
  stage); `run_ref`/`checkbox_progress`/`breakdown_path` match their
  dashboard/protocol ancestors exactly; the undecodable-run path was
  re-confirmed live at Verify. The broad `except Exception` in
  `gather` is deliberate, commented, and the architecture's stated
  attention-strip contract.
- **Design** — the code matches architecture.md's contracts: board.py
  stayed a thin caller (every fact it states comes from a seam
  accessor), the one-owner route-back landed in the seam, ADR-0062's
  verbatim-JSON/stop-on-failure rules appear in SKILL.md as written,
  and the SVG grammar defers to the family design system rather than
  restating tokens.
- **Security** — read-only tool over a local tree; no network, no
  shell-out, no secrets; problem strings carry local paths only; the
  SVG output embeds no scripts or external references.

## Verdict

Ready to ship. No critical or major findings; three minors deferred
with reasons, one fixed in place. The one operational dependency —
plugin-cache propagation — is Ship's first checklist item.
