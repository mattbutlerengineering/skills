---
stage: idea
run: feature:software-factory
date: 2026-07-11
---

# Idea: Software factory — an AFK production line on the lifecycle pipeline

## Problem

The lifecycle pipeline is single-player and synchronous. Every stage needs
Matt at the keyboard: skills produce artifacts, but nothing executes work
while he is away, nothing bounds what an unattended agent may spend or
touch, and his attention goes to execution instead of judgment. The
pipeline has stages and artifacts; it has no dispatch.

## Who has it

Matt, solo operator. Today he copes by running stage skills interactively,
one session at a time, and carrying all coordination in his head.

## Why now

- claude-code-action makes label-triggered AFK execution on GitHub Actions
  practical and auditable.
- The ai-tooling evidence base (33 MEASURED evals) has settled per-stage
  tool picks; the open question is orchestration, not tooling.
- 8090.ai validates the shape commercially (Refinery → Foundry → Planner →
  Assembler → Validator; humans own requirements and architecture, agents
  execute, full audit trail).

## Evidence

- ai-tooling `methodologies/8090-software-factory-sdlc.md` and
  `intent-to-production-recipe.md` map 8090's pipeline onto these skills
  and name the gaps: no dispatch, single-player coordination.
- The recipe has produced real merged work end-to-end (ai-tooling issues
  #172–#174 built the methodology docs through it) — a real run, not an
  anecdote.

## Solution hunch

Keep artifacts-are-the-state (ADR-0004) untouched and add a **dispatch
plane**: work orders as GitHub issues mirrored one-way from breakdown
rows (extending ADR-0026), executed AFK by claude-code-action under
per-order token budgets, bounded by exactly three human gates (PRD,
blueprint/ADR, merge) enforced with CODEOWNERS + branch protection, with
offline drift detectors in CI catching knowledge-plane rot.

## Success in one sentence

A work order labeled ready-for-agent becomes a merged, gate-checked PR
with no human involvement between the three gates.

## Unknowns & risks

- AFK PR acceptance rate is unknown — kill criteria are set at Milestone 1
  exit (acceptance < 40%, cost/WO > 2× class budget, or every run needing
  rescue → stop and rethink).
- Prompt injection into unattended runners via issue text.
- Solo review bandwidth at the merge gate (gate latency is a first-class
  metric for this reason).
