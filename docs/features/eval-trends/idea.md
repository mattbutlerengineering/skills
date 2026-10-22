---
stage: idea
run: feature:eval-trends
date: 2026-10-21
origin: "Issue #1027 (Improve evals: deep research and measure so that we can track improvements over time), driven by the Owner's three answers recorded in autorun-brief.md in this directory. Not a backlog seed: no matching line is claimed. Interview answered from the brief and the issue; no live interview held."
assumptions:
  - "In-flight check ran, nothing matches: `gh pr list --state open` returned no open PRs. The only open issue about evals is #1027 itself (the rest are permanent journal and queue markers). Branches checked by name (eval, trend, metric): feat/eval-trends is this run; feat/decompose-eval-suite is the Decompose suite already shipped as #1051; feat/plugin-eval-633, fix/eval-id-validity-rule, fix/plugin-eval-skill-tags-862, fix/746-guarded-eval-runner-inputs and agent/plan-002-run-eval-tests, agent/eval-validators-raise-on-non-object-files are older eval-runner or validator work, none a trend view. No one has built this."
  - "Adjacent shipped work, recorded rather than treated as a match. eval_schema.py owns record naming grammar and snapshot kinds (SNAPSHOT_KINDS: trigger, charter, decompose-signals) and validates case sets; it has no reader that aggregates results over time. trigger_eval.py and charter_replay.py write one snapshot per run and print that run only. decompose_signals.py reads git history and prints per-run and aggregate Decompose outcome rates; size_band_calibration.py does the same for size bands; decompose_lessons.py and decompose_grade.py are Decompose-specific. LEDGER.md keeps a per-skill latest-versus-previous trigger score by hand, linked to results files, and its maturity is keyed to real runs (ADR-0012, ADR-0019). dashboard.py and board.py show run placement and gates, not eval history. docs/research/eval-and-memory.md surveys promptfoo, DeepEval, mem0 and Letta as harnesses to adopt and does not treat how to judge or track eval quality over time; no other note in docs/research does. Not a duplicate of any of them; the sibling tools are the style precedent."
  - "Outside corroboration (the optional last30days check) was not run: the skill says never to run it unasked, and no human was present to ask. The interview alone is a complete result."
  - "Ambition ladder (feature-run version): the brief gave no rung pick, so the skill's recommended default, Showstopper, was taken and is logged here. The four tests were run silently and all pass (see Ambition rung). The Moonshot was not chosen and should be seeded to docs/backlog.md; this stage commits only idea.md by instruction, so the seed text is carried in the Not taken line of the brief instead, as the skill allows when the file is not written."
  - "The brief's three Owner answers are binding scope: research note plus a free read-only trend tool; no paid run, no `claude plugin eval`, no trigger_eval.py or charter_replay.py live run, LEDGER maturity does not move; prepare-and-stop release. The rest of the brief is the orchestrator's reading, recorded here as hunch and anecdote."
  - "No evidentiary question was left unanswered by the brief, so nothing was surfaced. The record inventory under Evidence was measured by real commands on 2026-10-21, not taken from the brief."
---

# Idea: A free eval-trend view over the records the repo already holds, with a research note on what to trust

## Problem

"Improve evals. deep research and measure so that we can track improvements
over time." The Owner changes skills and eval suites and cannot say whether
the evals themselves are getting better or only changing. There are several
eval surfaces and no single view across them, no time series, and no
research basis for which numbers deserve trust (flakiness, judge drift,
saturation, contamination, cost per point).

## Who has it

The Owner, who runs the pipeline and decides which paid eval runs to fund.
Today they read individual records and LEDGER rows by hand and compare
scores from memory.

## Why now

The Decompose loop (#986 to #989), the idea ambition ladder and the
plugin-eval suites just added surfaces whose effect shows only over time,
and the first paid runs are being decided. Spending without knowing what is
already measurable repeats the 2026-07 pattern of one-off snapshots.

## Evidence

- **Anecdote, labelled:** the issue's one line; the brief's reading that the
  Owner compares by hand. Nothing here shows a trend view would change a
  decision.
- **Measured 2026-10-21 (real commands over the working tree).** Eval
  records on disk, by surface:
  - Trigger runs, `evals/results/trigger*.json`: 41 files, 2026-07-01 to
    2026-10-10 (five run days). Shape: model, runs_per_query, confusion,
    results, summary with total/passed and by_kind/by_skill. 36 of the 41
    are small reruns of 1 to 13 cases (07-03, 07-05 widenings). Only 5 are
    full-set runs (n >= 40): 07-01 (34/47, model claude-sonnet-5), 07-05 omp
    (59/70, omp harness), and three on 2026-10-10 (128/152, 159/185,
    163/185; model field absent, harness claude). The case set grew from 47
    to 152 to 185 across them, so pass rates are over different sets. No
    cost field.
  - Charter replays, `evals/results/charter-*.json`: 2 files, both
    2026-09-28, both `control` arm on haiku, 4 charters each, 1 sensitive
    and 3 inconclusive. A sensitivity count, not a pass rate. No cost field.
  - Decompose outcome signals, `evals/results/decompose-signals-*.json`: 2
    files, both 2026-10-18; aggregate rates from git history, not an eval
    run.
  - Output-eval gradings, `evals/results/output/*/grading.json`: 2 files,
    both decompose, 2026-07-01 (-2 suffix the same day); expectations with
    passed/evidence and a summary. No cost field.
  - Plugin evals, `plugin-evals/records/*.json`: 3 files, all 2026-10-10,
    different suites (next, lean+implement, kb-on+kb-off), 2 to 6 cases
    each, with passRate and costUsd (0.40, 0.58, 4.06). The only surface
    with a cost field, and the three runs are not the same suite.
  - Records committed to git on 7 distinct days across the whole history.
- **What this means for a trend:** one surface, trigger, has a same-suite
  pair on two days only loosely (07-01 47 cases versus 10-10 152 or 185),
  and the three 10-10 files are same-day reruns that measure noise, not
  change. No surface today has two same-suite records on different days with
  matching case sets and a cost field. A defensible trend line is mostly
  not measurable yet; that is the finding, not a failure of the idea.
- **None for the target:** no source in this repo shows what metric set
  predicts real skill quality. That is what the research note must source
  and mark unverified where it cannot.

## Ambition rung

Chosen: Showstopper (skill default, brief silent), in the user's words: "Improve evals. deep research and measure so that we can track improvements over time."
Not taken: Solid: the research note and a tool that prints a table of records per surface with dates and n, no trend or refusal logic. Moonshot (seed text, not written to docs/backlog.md by this stage): a continuously refreshed eval-quality dashboard that scores each skill across all surfaces and gates changes on a trend, which needs many paid runs and a settled metric set and drifts into gating.
Demo: pass — running the tool prints one line per surface with n, date span and comparable-pair count, and a REFUSED line naming the missing n or shape mismatch where a trend cannot honestly be shown.
Removes a step: pass — replaces opening forty-odd JSON files and LEDGER rows and comparing scores from memory.
Only this product: pass — it reads this repo's own append-only records and naming grammar (eval_schema.py), which no outside harness holds.
Achievable: pass — the riskiest piece is whether records from different surfaces can be normalised to a comparable pass rate and cost; two-day spike: group trigger and plugin records by case-set identity and print pairs, confirming the shapes parse.

## The demo

Before: to know whether evals are improving the Owner opens individual records and LEDGER rows and guesses. After: one command prints each surface's record count, date span and n, a pass-rate and cost line where two same-set records exist, and an explicit "too few records: need n, have m" where they do not.

## Riskiest piece + spike

Comparing records honestly across shapes and across a changing case set
(47 to 185 trigger cases). Spike of about two days: read every record
through eval_schema.py, key each by suite and case-set identity, and print
which pairs are comparable, without computing any trend. If no pair
qualifies, that is the output.

## Cheapest kill test

Run the spike's grouping over today's records. If zero surfaces have a
comparable same-set pair on different days with a cost field, the trend half
is empty today and the tool should ship as an inventory plus refusal, with
the trend lines gated on future records, rather than inventing a number.
The measured inventory above already leans this way.

## Solution hunch

A hunch, not a design. A dated note in `docs/research/` with cited sources
naming a metric set (per-surface pass rate with a confidence interval,
flake rate from reruns, saturation, judge agreement, cost per point) and
each metric's failure mode, with what could not be verified marked. Then a
stdlib-only, read-only tool in the style of decompose_signals.py and
size_band_calibration.py that reads the existing records, reuses
eval_schema.py rather than a second reader, prints per-surface trend lines,
and refuses below a minimum n. It never writes into evals/results/ or
plugin-evals/records/ and never runs a model.

## Success in one sentence

`python3 <tool>` prints per-surface trend lines from real records, refuses
where n is too small, and every number it prints recomputes by hand from
the records.

## Unknowns & risks

- **Too few records.** Measured above: the honest output may be mostly
  refusals for months. Whether that is still worth shipping is the question
  the cheapest kill test answers.
- **Shapes too different.** Trigger (pass/fail over cases), charter
  (sensitivity counts), plugin (score, pass rate, cost) and output gradings
  do not share a metric. The tool may have to report them side by side
  rather than on one scale.
- **A changing case set.** Trigger pass rate moved over 47, 152 and 185
  cases; a rate over different sets is not a trend. Case-set identity needs
  an owner (eval_schema.py by the seam rule, not a second reader).
- **Missing fields.** Three 10-10 trigger files lack a model field and no
  trigger or charter record has cost; the tool must refuse, not impute.
- **A number read as proof.** A trend line on tiny n can be read as
  improvement; the refusal threshold and a stated interval are the guard,
  and the research note must say what n justifies one.
- **Drift into gating.** The brief forbids gating and LEDGER movement; the
  tool reports only (ADR-0012, ADR-0019).
- **Seam rule.** A new reader of eval_schema.py's shapes needs a reason;
  new import pairs move tests/test_dual_membership.py's pin (currently 54).
  Architect decides whether the tool is root-only.
- **Research quality.** Web sources are untrusted data and some claims may
  not be verifiable; the note must mark what was not.
