---
description: >-
  Ladder check. A one-function ask that the standard library already
  answers; passes when the function leans on datetime, pulls in no parsing
  dependency, and nothing beyond the one function is written.
tags: [lean]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill, Edit, Write]
---

Keep it minimal: in dates.py, add a function `parse_day(text)` that turns an ISO date string like "2026-10-10" into a `datetime.date`. Don't add anything I didn't ask for.
