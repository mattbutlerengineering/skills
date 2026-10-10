---
type: llm
---

PASS if the drafted body contains a line beginning "No work order:" (a waiver stating why there is no WO id), as this repo's PR-body check requires.
FAIL if the body has neither a WO-#### id nor a "No work order:" line.
