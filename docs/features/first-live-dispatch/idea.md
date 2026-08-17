---
stage: idea
run: feature:first-live-dispatch
date: 2026-08-17
origin: "backlog seed: Supervised end-to-end gate traversal (from: feature:software-factory); also claims the FACTORY_PAUSE_TOKEN seed, absorbed into scope"
---

# Idea: first live dispatch

## Problem

The factory's headline sentence has never happened. software-factory v1
shipped a dispatch plane that is built, unit-gated, and review-hardened
— and has processed zero real work: zero assembler executions, zero
paid tokens, no work order ever carrying a gate-1 or gate-2 approval
label. The operator still executes every work order personally; the
factory watches him do it and posts reports about it. Until one real
order traverses the gates unattended, v1's three FAILed criteria stay
FAILed and every dispatch-path behavior (hand-off, spend recording,
mechanical stops) remains proven only at the unit seam.

## Who has it

Matt, the factory's sole operator. Coping today: owner-driven sessions
do the work the dispatch plane was built to take, and the traversal
that would prove otherwise was already attempted once — WO-0035's
supervision window came and went without the key or the owner at the
gates, and the exercise was reseeded rather than faked.

## Why now

Three things changed at v1's close: the dispatch path is now actually
safe to run (Milestone E fixed the validator hand-off, spend
persistence, pause enforcement, and mechanical stops), the honesty
machinery that would catch a bad first run is live and has drawn blood,
and the retro explicitly named this the next run's headline. The
blockers are down to two deliberate acts — minting two secrets and
showing up at the gates — both scoped into this run.

## Evidence

Measured, not anecdote: `gh run list --workflow assembler.yml` shows
only cancelled/skipped conclusions; the gate-label queries return zero
`wo:prd-approved`/`wo:blueprint-approved` carriers; the ledger's 36
rows are all $0.00 (gate-latency and owner-session rows). v1's
verification (2026-08-17) records criteria 1–4 as FAIL/PARTIAL with
this single cause. release.md's pre-flight adds the armed-breaker gap:
`gh secret list` is empty, so a real cap breach could not set
FACTORY_PAUSED.

## Solution hunch

A hunch, not a design: mint both secrets first (ANTHROPIC_API_KEY for
dispatch, FACTORY_PAUSE_TOKEN for the breaker) so the first paid run
happens with the budget guard armed; then drive one small, real,
already-triaged work order — the gates.py detector-J roster fix, a
review-found doc-only minor — through the full label chain
(`wo:draft → wo:prd-approved → wo:blueprint-approved →
wo:ready-for-agent`) with the owner supervising each gate, and let the
dispatched agent deliver the PR through validator hand-off to an
owner-reviewed merge. The run's artifacts are small; its deliverable is
evidence.

## Success in one sentence

One work order goes wo:draft → prd-approved → blueprint-approved →
ready-for-agent → agent PR → validator-checked → owner-merged, and the
ledger shows the run's real spend — graduating v1's criteria 1–4 in one
pass.

## Unknowns & risks

- claude-code-action has never run in this repo: model behavior against
  the assembled prompt substrate, execution-file shape for `wo-record`,
  and turn/timeout fit are all live-run unknowns.
- Spend calibration is a guess (ADR-0034's starting table was labeled
  one); the first run prices it for real.
- The likeliest death is the same as last time: owner availability at
  the gates — WO-0035's supervision window expired undriven. The run
  dies politely (reseed again) if the window can't be held.
- The workflow_dispatch validator hand-off and the spend-row push are
  test-pinned but have never fired live; a miss there is red-visible
  but would mean the traversal completes without its gate-3 or ledger
  evidence.
- Key handling: both secrets are owner-minted, console-set, and never
  touch the repo — a leak path would kill more than this run.
