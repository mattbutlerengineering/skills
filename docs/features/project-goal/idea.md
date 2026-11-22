---
stage: idea
run: feature:project-goal
date: 2026-11-22
---

# Idea: one project goal that decides prioritization, with a factory that prunes itself

> I want to set an overall goal for this project, help me make sure this is how we decide prioritization. The goal is to deliver work faster with higher quality with more autonomy. Remove process that is not adding these values. Add processes that enforces these values. Define how we know we are successful.

## Problem

As the owner, I can't tell whether the factory's work is moving the project
toward faster, better, more autonomous delivery, because nothing states the
goal and nothing measures it. Work gets picked by urgency and age, and the
selectors' "process gap" tier lets the factory keep adding process to itself.
The effort goes into upkeep instead of the product.

## Who has it

The owner (and the unattended routines and queue workers that choose work on
the owner's behalf), plus any repo the factory is stamped into. Today they cope
by manual audits and ad-hoc "is this still needed" questions; the selectors
rank by red main, then oldest issue, and no rule names a goal.

## Why now

The first 30 days of measured upkeep made it visible. Of 556 commits since
2026-10-22, 298 were `fix:` and most of those fixed the factory itself;
about 1 commit in 5 since 2026-10-01 touched `skills/`, the product.
Commits arrive in bursts (142 on one day, 2 to 6 on most others).

## Evidence

- Measured (this session, from git and gh): the commit mix above; the
  assembler skipped its last 50 runs; the work-order gates and journals
  #178 and #294 have had no traffic since 2026-08; LEDGER shows 0
  battle-tested skills with no entry since July.
- Measured: no tool computes lead time, escape rate or unattended share;
  ADR-0069's one baseline was a single hand calculation, 2 accepted over
  2,775.9 gate-wait hours.
- Anecdote: the owner's own sense that the factory is over-invested in
  tooling and scaffolding before shipping (stated in their working-style
  notes). No outside research was run.

## Ambition rung

Chosen: Showstopper, in the user's words: "deliver work faster with higher quality with more autonomy"
Not taken: Moonshot: the pipeline retunes its own selection weights and process set from the metrics in a closed loop, not achievable at this run's scale (seeded); Solid: the metrics, labels, selectors and register with a human opening every removal PR, the fallback
Demo: pass — the weekly run opens a removal PR citing a register row and its zero evidence
Removes a step: pass — the manual "is this still needed" audit is gone
Only this product: pass — it runs on the factory's own ledger, gate and PR history that no outside tool holds
Achievable: pass — riskiest piece is a safe, mergeable removal PR generated from a register row; a two-day spike does it for one real row, the assembler workflow

## The demo

Before, a dead process lingers until the owner happens to audit for it. After,
the weekly metrics run flags a register row with no evidence of a catch for 60
days and opens a pull request deleting that process, with the row and the empty
evidence quoted in its body.

## Riskiest piece + spike

Generating a removal that is safe and mergeable: the process has callers,
tests, docs and checksum-pinned template files. Spike (about two days): do it
by hand-driven script for one real row, the assembler workflow, and see
whether detectors, lint and tests stay green without human repair.

## Cheapest kill test

Run the four metrics once over the last 30 days from git and gh alone. If they
cannot be computed without inventing data, or the numbers are too noisy to rank
anything, the goal rule has nothing to rank on and the idea dies cheaply.

## Solution hunch

One stdlib tool computes the four metrics (lead time, escape rate, unattended
share, overhead ratio) from git and gh and rides the existing weekly cost
report. A process register lists each process with the metric it protects and
its last evidence of a catch. `goal:*` labels let the selectors rank work by
the metric furthest from target. Sunset-flagged rows turn into removal PRs. The
decision is recorded in ADR-0135.

## Success in one sentence

Within eight weeks the weekly report shows lead time halved from baseline,
escapes under 10%, at least 80% of product PRs merged without an owner touch,
and overhead at or below 30% of merged PRs.

## Unknowns & risks

- Owner-touch is hard to measure from git and gh alone; "no owner comment"
  may be noisy where the owner and agents share one account.
- Escape detection depends on `Fixes-PR:` discipline; a fallback heuristic
  (a fix touching the same shipped files) may misattribute.
- Targets are placeholders until a baseline run exists; the 8-week window may
  be too short for escape rate to settle.
- Work-order machinery ships to stamped repos, so removing it is not purely
  local; the sunset rule must not break stamped consumers.
- Most likely way this dies: the metrics become one more upkeep surface the
  factory maintains for itself, which is the overhead the goal exists to cut.
