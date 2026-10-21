---
stage: idea
run: feature:decompose-eval-suite
date: 2026-10-20
origin: "Issue #989 (Decompose learning loop, step 4 of 4), driven in session by the Owner's answers recorded in autorun-brief.md in this directory. Not a backlog seed: docs/backlog.md has no matching line, so no seed claim is written. Interview answered from the brief (three Owner answers, the rest the orchestrator's reading); no live interview held."
assumptions:
  - "In-flight check ran, nothing matches: `gh pr list --state open` returned no open PRs. Open issues touching this are #989 itself and #1027 (Improve evals, a generic ask: 'deep research and measure so that we can track improvements over time', no Decompose suite in it). Branches with eval or decompose in the name: feat/decompose-placeholder-scan (not merged; it edits skills/decompose/SKILL.md to add a draft self-check step and one expectation in evals/output/decompose.json, and builds no grader and no plugin-evals suite), feat/decompose-outcome-signals (merged as #1040), feat/decompose-lessons (merged as #1050), feat/plugin-eval-633, fix/plugin-eval-skill-tags-862, fix/746-guarded-eval-runner-inputs, fix/eval-id-validity-rule and agent/plan-002-run-eval-tests (harness work, none holds a Decompose suite), and this run's own feat/decompose-eval-suite. None holds Decompose eval-suite work."
  - "Adjacent shipped work, recorded rather than treated as a match: plugin-evals/ holds suites lean, next, implement and knowledge-base (ADR-0081; none for decompose); each case is case.yaml plus prompt.md plus graders/ of regex, tool_used, file_exists and llm kinds, tagged with its skill (ADR-0093). evals/output/decompose.json already has three Decompose output cases, but its expectations are prose lines judged by a model, with no deterministic grader, no score and no feedback text; evals/routing.json and trigger_eval.py grade which skill fires, not breakdown quality; charter_replay.py replays role charters; eval_schema.py owns evals/results/ naming and output-eval shape, not plugin-evals records (ADR-0081 decision 2, 'no code reads it yet'). lint.py grades no breakdown content. decompose_signals.py (#1040), size_band_calibration.py (#1047) and decompose_lessons.py (#1050) measure outcomes after the fact from git; none scores a draft. The unmerged feat/decompose-placeholder-scan asks the skill to self-check for placeholders, vague Accept lines and dangling Blocked by; the same three defects are what this run's graders would detect from outside, so the two are complementary (the skill change prevents, the grader measures) and overlap in what they name, not in code. Not a duplicate of any of them; whether the grader reuses a breakdown parser already in protocol.py or work_queue.py is for Architect."
  - "Outside corroboration (the optional last30days check on why-now and evidence) was not run: the skill says never to run it unasked, and no human was present to ask. The interview alone is a complete result."
  - "The brief's Owner answer 2 (suite and graders only, no paid run, no optimizer, no LEDGER change) is taken as binding scope for this stage. The brief's other idea-stage inputs are the orchestrator's reading, recorded here as hunches and anecdote, not as Owner decisions."
  - "No interview question this stage offered named options with a recommended default that the brief left open, so no skill default was taken. No evidentiary question was left unanswered by the brief, so nothing was surfaced."
---

# Idea: A scored, offline-gradable eval suite for the Decompose skill

## Problem

The Decompose skill has been changed three times in one wave (#1040, #1047,
#1050, with a self-check step waiting on a branch) and nothing can say
whether a change made the breakdowns better or worse. The only signals are
outcome rates that arrive runs later, from git. Anyone editing the skill
judges a breakdown by reading it.

## Who has it

- **The Owner**, and whoever edits `skills/decompose` next: they compare
  skill versions by eye.
- **Any future prompt optimizer** (the issue names GEPA and TextGrad): it
  needs a score plus text saying why a candidate failed, and none exists
  for Decompose. That optimizer is out of scope here.

## Why now

Steps 1 to 3 of the learning loop shipped (#1040, #1047, #1050), so step 4's
precondition, a scored eval, is the missing piece. `plugin-evals/` exists
(ADR-0081) with four suites and none is for Decompose; LEDGER.md lists
decompose at `used-once`.

## Evidence

- **Anecdote, labelled:** GEPA (arXiv 2507.19457) and TextGrad results, as
  cited in #989. They are about prompt optimization against scored
  feedback, not software decomposition.
- **None for the target:** no verified source shows a suite like this
  improves Decompose. No count of recurring breakdown defects has been
  taken at this stage.
- **Existing mechanism, adjacent:** `evals/output/decompose.json` already
  asserts the same defect classes in prose, judged by a model, which gives
  no number and no line-level reason.

## Solution hunch

A hunch, not a design. Two parts:

- A suite under `plugin-evals/decompose/`, tagged `decompose` so
  `claude plugin eval . --tag decompose` runs it, with fixture
  architectures that hold a known-good cut.
- Stdlib grader code that reads a produced `breakdown.md` against its
  fixture architecture and prints line-level text feedback: coverage
  misses, dangling `Blocked by`, untestable `Accept` lines, mis-sized
  items. It is tested offline and free, through public interfaces with
  exact strings.

This run authors and tests; it does not execute the suite. Owner decision,
in scope: no paid run, so LEDGER maturity does not move and
`plugin-evals/records/` gets nothing (ADR-0012, ADR-0019, ADR-0081).

## Success in one sentence

A grader run on a known-good and a known-bad fixture cut gives different,
explained scores, offline.

## Unknowns & risks

- **Fixtures that only mirror the template.** If the known-good cut is
  written to the skill's own `TEMPLATE.md`, everything passes and the suite
  guards nothing; the known-bad cuts must fail for real reasons.
- **Graders that reward gaming.** A breakdown can pad `Accept` lines with
  checkable-sounding words or split items to look small; whether a
  deterministic check can tell is unproven.
- **Suite shape the harness rejects.** The `claude plugin eval` case format
  is validated only by running it, and this run does not run it; only the
  repo's own offline tests can catch a malformed case.
- **How a deterministic grader plugs into the harness.** The existing graders
  are regex, tool_used, file_exists and llm; whether a Python grader runs
  inside a case, or only a regex over a printed report, is unresolved and
  is Architect's.
- **Mis-sized is a judgment.** A size check needs a rule from the fixture or
  from the Decompose size bands; a bad rule scores good cuts as wrong.
- **Overlap with `evals/output/decompose.json` and the unmerged placeholder
  scan.** Where each check lives, and whether any is stated twice, is open
  under the one-owner and seam rules.
- **A first paid run is a follow-up** needing the Owner's own say-so, so
  this run produces no measured delta and no evidence that the suite
  discriminates on a real model.
