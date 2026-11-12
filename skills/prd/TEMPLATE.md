---
stage: prd
run: product | feature:<slug>
date: YYYY-MM-DD
ux: required | not-applicable
# ux-reason: <one-line rationale>   (only when ux is not-applicable)
---

# PRD: <title>

<!-- Ambiguity mid-draft? Mark it inline at the exact clause:
     `[NEEDS CLARIFICATION: <question>]`. The clarify pass resolves every
     marker before the PRD's approval gate, and gates.py detector N fails
     a prd.md that still carries one (ADR-0071). -->

## Problem statement

<The problem from the user's perspective. Inherit and sharpen idea.md.>

## Solution

<The solution from the user's perspective — what exists when this ships.>

## Actors

- **<Actor>** — <who they are in one line>

## User stories

1. As a <actor>, I want <feature>, so that <benefit>.

## Success criteria

- [ ] <Checkable criterion — a person or a test can verify it.>

## Out of scope

- <Real exclusions someone might reasonably have expected in scope.>

## Open questions

- <Question> — <who/what can answer it>
