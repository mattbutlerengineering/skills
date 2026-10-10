---
description: >-
  Knowledge-base paired test, arm off (docs/kb and its inline index removed). Passes when the drafted PR body carries a No work order waiver line.
tags: [kb-off]
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep]
---

Draft the pull-request body for a branch in this repo that only fixes a typo in README.md. There is no work order for it and no GitHub issue. Give me the body text only; don't change any files.
