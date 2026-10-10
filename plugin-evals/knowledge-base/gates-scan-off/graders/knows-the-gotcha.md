---
type: llm
---

PASS if the reply warns that this will fail CI because the gate detectors scan every repo markdown file, code fences included, so the made-up PRD id and/or the dead sample link get flagged, and suggests a way around it.
FAIL if it says code fences are ignored or that CI will pass.
