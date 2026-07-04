---
stage: capture
run: maintenance:<slug>
date: YYYY-MM-DD
re-entry: implement | architect
---

# Defect: <working title>

<!-- For refactor/upgrade work this is a condition brief: retitle to
     "Condition: <working title>" — the filename stays defect.md. -->

## Defect (or Condition)

<What is broken — observed vs expected behavior. For a condition brief:
what is degraded, and the target state that would end the run.>

## Reproduction / Evidence

<Steps to reproduce, a failing test, logs, user reports. For a condition
brief: the evidence of degradation. If it can't be reproduced yet, say so
— reproducing it is the first work item.>

## Root-cause hypothesis

<Best current hypothesis, labelled as such — or "unknown".>

## Blast radius

<Who and what is affected, how badly, since when. Review and Ship scale
to this.>

## Ruled out

- <Dead ends already investigated and why they're not it — or "none yet".>

## Work items

<!-- Only when re-entry: implement — the breakdown lives here as
     checkboxes. With re-entry: architect, delete this section; the
     architecture.md + breakdown.md chain owns the work items. -->

- [ ] **<Item>** — <what to do, one line>
  - Accept: <checkable acceptance criterion>

## Notes

<Anything that doesn't fit above; deviations discovered downstream get
logged here, dated.>
