---
stage: idea
run: feature:process-dashboard
date: 2026-08-13
---

# Idea: Process dashboard — a UI that makes the pipeline and factory observable

## Problem

I can't see where anything stands without spelunking. Run state, gate
queues, spend, and drift live in breakdown checkboxes, pinned issues
(the gate digest, the improvement journal), weekly cost-report issues,
`costs.jsonl`, and `LEDGER.md` — orienting means running shell commands
against each surface in turn. There is no overview: no one place that
shows what's going on, what's in the backlog, or what the factory has
produced.

## Who has it

Matt — the solo operator of the idea-to-prod pipeline and the software
factory. Copes today by shell spelunking (`git log`, `gh issue list`,
grepping breakdowns), reading the pinned gate-queue digest and
improvement journal, and opening weekly cost issues one by one. The
audience is about to grow in one dimension: the same operator across
*multiple repos*, as the process is adopted in other
`mattbutlerengineering` repos — same spelunking, multiplied per repo.

## Why now

Two changes, in order:

1. **Going multi-repo.** The process is about to be used for developing
   features in other repos (the plugin travels; `factory_init.py stamp`
   puts the factory tooling into product repos). Orientation that
   barely works for one repo multiplies per repo.
2. **The factory just went unattended.** Daily improvement routine, AFK
   dispatch, scheduled sweeps — agents now act while nobody watches, and
   what happened is learned by reading issue threads after the fact.
   Unattended work is exactly what demands observability.

## Evidence

Anecdote-grade but documented in-repo:

- **Mirror drift went unnoticed for ~2 weeks.** Tracker issue #123
  (WO-0018) sat CLOSED from 2026-07-28 while its breakdown row —
  the source of truth — stayed unchecked and the work unbuilt; noticed
  only when a session happened to orient on that run (2026-08-13).
- **Checkbox reconciliation, 2026-07-19** (`breakdown.md` Notes): five
  work orders merged without their rows being ticked; the drift was
  found and corrected by hand.
- **Orientation cost, observed this session:** locating where two
  active runs stood took several shell commands across breakdowns,
  issues, and frontmatter before work could start.

## Solution hunch

A hunch, not a design: a repo-generic console over the state the
process already writes — the run artifacts (knowledge plane), the
tracker mirror and lifecycle labels (dispatch plane), the cost ledger,
and the gate/correction streams. It would show an overview of runs and
their stages, the seed backlog (with reordering — ordering is the
prioritization, ADR-0029), the factory's output (work orders → PRs),
and improvement metrics over time. Observability data we don't yet
record gets added and powers the UI. Built and vended the way the rest
of the tooling is, so any repo running the process gets it; an
aggregate view spans repos.

## Success in one sentence

A quick glance gives me an overview of what's going on — what's in the
backlog and in what priority order, what the factory has produced, and
metrics showing whether we're improving — without a terminal.

## Unknowns & risks

- **We don't complete the UI.** A console is bigger than anything this
  repo has shipped; the run dies half-built. (Named by the operator as
  the top risk.)
- **The UI doesn't solve the observability problem.** A screen exists
  but the morning questions still need spelunking — effort spent,
  problem intact. (Operator-named, second.)
- Where the UI lives and runs is undecided: this repo is stdlib-only,
  no web stack, vended as a plugin — generated static HTML, a hosted
  page, or something else entirely are all open.
- Backlog prioritization is a *write* — the one interactive verb in an
  otherwise read-only surface; its boundary (and any pull toward
  dispatch/approve buttons, which belong to the human gates, ADR-0033)
  is unsettled.
- Cross-repo aggregation (discovery, auth, freshness) is genuinely new
  machinery; the single-repo view mostly re-renders what exists.
