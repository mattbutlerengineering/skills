---
description: >-
  Decompose, one feature. A scaffold seeds the csv-export PRD and
  architecture; passes when the breakdown is written to the run directory
  as checkbox rows, every architecture component is named by some item,
  every Blocked by names a real item, every Accept line is checkable and no
  item spans more than a sitting of work. The four llm graders judge the
  breakdown the reply prints and are model judgement, not deterministic.
tags: [decompose]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

Break the csv-export feature down into work items. The PRD and the
architecture are in docs/features/csv-export/.

Answers to the questions you would ask me, so do not stop to ask them:
write the breakdown for a single engineer working one item per sitting;
use two or three milestones, each one demonstrable on its own; keep each
component's name exactly as the architecture spells it; label items S1, S2
and so on; do not track items anywhere outside the breakdown. Write it to
docs/features/csv-export/breakdown.md, then print the whole breakdown in
your reply.
