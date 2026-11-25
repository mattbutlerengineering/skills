---
stage: architect
run: product | feature:<slug>
date: YYYY-MM-DD
# ux: skipped — <ux-reason from prd.md>   (only when UX Design was skipped)
---

# Architecture: <title>

<!-- Ambiguity mid-draft? Mark it inline at the exact clause:
     `[NEEDS CLARIFICATION: <question>]`. The clarify pass resolves every
     marker before the blueprint gate, and gates.py detector N fails
     an architecture.md that still carries one (ADR-0071). -->

## Approach

<The design in one paragraph: shape of the solution and why this shape.>

## Components

### <Component name>

- Responsibility: <the one thing it owns>
- Collaborators: <components it talks to>

## Data model

<Entities, fields, relationships. Schema sketches welcome.>

## Interfaces & contracts

### <Interface name>

- Input: <what comes in>
- Output: <what goes out>
- Failure modes: <how it fails and what callers see>

## Stack & dependencies

- <Choice> — <why, one line>

## Decisions & alternatives

- **<Decision>** over <alternative> — <why it lost, one line; cite a matching `docs/standards.json` slug alongside any ADR number when the decision bears on one>

## ADRs

<Links to any ADRs created, or "none — no decision met the ADR bar.">
