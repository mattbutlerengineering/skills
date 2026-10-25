---
type: llm
---

PASS if the reply answers how to undo an unpushed commit and states every fact below, in any wording that keeps its meaning, and no sentence in it can be read two ways.
FAIL if any fact below is missing or contradicted, or if a sentence is ambiguous.

The facts the reply must carry:

- git reset --soft HEAD~1
- keeps the changes staged
- git reset --hard HEAD~1
- deletes the changes
