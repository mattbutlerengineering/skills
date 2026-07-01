---
stage: architect
run: product | feature:<slug>
date: YYYY-MM-DD
# ux: skipped — <reason>   (only when UX Design was skipped)
---

# Architecture: <title>

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

- **<Decision>** over <alternative> — <why it lost, one line>

## ADRs

<Links to any ADRs created, or "none — no decision met the ADR bar.">
