---
description: >-
  Knowledge-base paired test, arm on (docs/kb and its inline index present). Passes when the answer warns that example typed ids inside a code fence still fail the gates.
tags: [kb-on]
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep]
---

I'm adding a short how-to under docs/ that shows a sample run artifact inside a fenced code block, including a made-up id like PRD-0099 and a link to docs/features/example/prd.md that doesn't exist. Will CI be fine with that? Answer from this repo; don't change any files.
