---
stage: review
run: product | feature:<slug>
date: YYYY-MM-DD
---

# Review: <title>

## Scope

<What diff was examined — commits/files in this run.>

## Findings

### <Severity>: <one-line defect statement>

- Scenario: <concrete inputs/state → wrong behavior, or the decayed contract>
- Standard: <matching docs/standards.json slug this finding cites, or "none">
- Decision: fixed | deferred — <reason if deferred>

## Passes with no findings

<Which of correctness / design / security / complexity came back clean.>

## Verdict

<Ready to ship, or what blocks it.>
