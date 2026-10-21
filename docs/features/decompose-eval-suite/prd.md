---
stage: prd
run: feature:decompose-eval-suite
date: 2026-10-20
ux: not-applicable
ux-reason: "CLI text output, eval fixtures and grader code only; no screens or flows."
assumptions:
  - "Interview answered from autorun-brief.md in this directory; no live interview held. The brief holds three Owner answers (drive #989; suite and graders only with no paid run and no optimizer; prepare-and-stop release). Everything else traces to the brief's sections marked as the orchestrator's reading of issue #989, or to idea.md."
  - "No interview question this stage offered named options with a recommended default that the brief left open, so no skill default was taken. No evidentiary question was left unanswered, so nothing was surfaced."
  - "No PRD id assigned: the prd skill and TEMPLATE.md assign none, and the brief rules out work-order mirroring."
  - "The four defect classes (coverage miss, dangling Blocked by, untestable Accept line, mis-sized item) are taken from the brief as requirements. How each is detected, and what 'mis-sized' means, is left to Architect; this PRD fixes only the observable behaviour."
  - "How a deterministic Python grader plugs into the plugin-eval case format (existing graders are regex, tool_used, file_exists, llm), whether it reuses an existing breakdown parser (protocol.py, work_queue.py, knowledge_plane.parse_row), where fixtures live, and whether the grader earns a new module under the CLAUDE.md seam rule (eval knowledge belongs in eval_schema.py) are left to Architect as open questions (orchestrator instruction)."
---

# PRD: A scored, offline-gradable eval suite for Decompose

## Problem statement

Decompose has changed three times in one wave (#1040, #1047, #1050) and
nothing can say whether a change made breakdowns better or worse. The only
signals are outcome rates that arrive runs later from git; whoever edits
`skills/decompose` judges a breakdown by reading it. A later prompt
optimizer (out of scope) would need a score plus text saying why a
candidate failed, and none exists.

No verified source shows this suite improves Decompose. GEPA (arXiv
2507.19457) and TextGrad, as cited in #989, are anecdote about prompt
optimization, not software decomposition. This run builds the measuring
stick only; it produces no measured delta and no evidence the suite
discriminates on a real model.

## Solution

1. **A Decompose suite under `plugin-evals/`**, tagged `decompose` so
   `claude plugin eval . --tag decompose` selects it (ADR-0081, ADR-0093),
   with fixture architectures each holding a known-good cut and known-bad
   cuts that fail for real reasons.
2. **Deterministic, offline graders** (stdlib only) that read a produced
   `breakdown.md` against its fixture architecture and emit a score plus
   one line of text feedback per defect: a coverage miss, a dangling
   `Blocked by`, an untestable `Accept` line, a mis-sized item.
3. **Offline tests** through public interfaces asserting exact strings.

This run authors and tests; it never executes the suite. No
`claude plugin eval` call, no `plugin-evals/records/` entry, no LEDGER
maturity change (ADR-0012, ADR-0019, ADR-0081).

## Actors

- **Owner**: edits the Decompose skill and wants a score per change; runs
  the offline tests; decides on any first paid run.
- **Skill editor**: whoever changes `skills/decompose` next.
- **Plugin-eval harness**: `claude plugin eval`, which selects the suite by
  tag and runs its cases (not run by this work).
- **Future optimizer (#989 step 2)**: consumes score plus text feedback; out
  of scope here, named only as the reader of the feedback format.
- **Reviewer**: judges at the merge gate whether the graders can be trusted.

## User stories

1. As the Owner, I want a known-good fixture cut to score differently from
   known-bad cuts, so that a score means something.
2. As a skill editor, I want each defect class to produce its own exact
   feedback line naming the offending item, so that I can see why a
   breakdown lost points.
3. As the Owner, I want the graders to run offline with no model or network
   call, so that checking them costs nothing and runs in CI.
4. As the plugin-eval harness, I want the suite wired under the `decompose`
   tag, so that `--tag decompose` selects it.
5. As the Owner, I want LEDGER.md and `plugin-evals/records/` untouched, so
   that maturity moves only on a real run.
6. As the future optimizer, I want a numeric score and text feedback per
   candidate, so that a later run can use them as the signal.
7. As a Reviewer, I want each grader behaviour pinned by tests on exact
   strings, so that I can trust it without a live run.

## Success criteria

Exact feedback wording is fixed by Architect; each criterion is tested by
asserting the exact strings the graders emit.

- [ ] The known-good fixture cut scores differently from, and strictly
      higher than, every known-bad fixture cut; a test asserts the scores
      and that the good cut emits no defect line.
- [ ] A cut that leaves an architecture component with no covering item
      emits the coverage-miss feedback line naming that component. A test
      asserts the exact string.
- [ ] An item whose `Blocked by` names an item that does not exist in the
      breakdown emits the dangling-dependency line naming both items. A test
      asserts the exact string.
- [ ] An item with an `Accept` line that no test could check (empty, or a
      placeholder such as "works correctly") emits the untestable-Accept
      line naming the item. A test asserts the exact string, and that a
      concrete Accept line on the good cut emits none.
- [ ] An item outside the size rule Architect settles emits the mis-sized
      line naming the item and its size. A test asserts the exact string.
- [ ] Each known-bad fixture fails for exactly the defect class it is named
      for; a test asserts each bad cut produces its class's line and no
      other class's line.
- [ ] The suite is wired so `--tag decompose` selects it, checked
      statically: a test reads the case files and the manifest's
      `experimental.evals` entry and asserts every case carries the
      `decompose` tag and the layout matches the existing suites.
- [ ] Graders make no network call and no model call, and import stdlib
      only; a test or lint check asserts it.
- [ ] No existing eval definition is edited: `git diff` against main shows
      no change to files under `evals/` or to the other `plugin-evals/`
      suites.
- [ ] `LEDGER.md` is byte-identical to main, `plugin-evals/records/` gains
      no file, and `.claude-plugin/plugin.json`'s version is unchanged.
- [ ] `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`,
      `python3 gates.py` and `python3 gates.py --selftest` all pass.

## Out of scope

- Any paid run: no `claude plugin eval` call, no `plugin-evals/records/`
  entry. A first paid run needs the Owner's own say-so and is a follow-up.
- Any LEDGER maturity change.
- Prompt optimization (GEPA, TextGrad).
- Editing `skills/decompose`, including the unmerged placeholder-scan
  branch's self-check step.
- Editing any existing eval definition, in `evals/` or `plugin-evals/`, to
  make a case pass.
- A plugin version bump (ADR-0095).
- Mirroring items to work orders; the PR body carries a `No work order:`
  line.
- Grading on a real model's output.

## Open questions

- How does a deterministic Python grader plug into the plugin-eval case
  format, given the existing graders are regex, tool_used, file_exists and
  llm? Does it run inside a case, or only as a regex over a printed report?
  For Architect.
- Does the grader reuse a breakdown parser already in `protocol.py`,
  `work_queue.py` or `knowledge_plane.parse_row`? For Architect.
- How is "mis-sized" ruled: from the Decompose size bands, from the
  fixture, or both? A bad rule scores good cuts as wrong. For Architect.
- Where do the fixtures live, and how are they kept from only mirroring
  the skill's `TEMPLATE.md` (which would make every cut pass)? For
  Architect.
- Does the grader earn a new module under the CLAUDE.md seam rule
  (multiple real callers and observed divergence), or does eval knowledge
  go in `eval_schema.py`? For Architect.
- Can a deterministic check tell a padded Accept line or a split-to-look-
  small item from an honest one? Unproven; for Architect, and a known
  limit for Review.
- Where does each check live relative to `evals/output/decompose.json` and
  the unmerged placeholder scan, so no check is stated twice? For
  Architect.
