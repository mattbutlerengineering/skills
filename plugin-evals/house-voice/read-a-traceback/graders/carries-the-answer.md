---
type: llm
---

PASS if the reply answers what the KeyError means and states every fact below, in any wording that keeps its meaning, and no sentence in it can be read two ways.
FAIL if any fact below is missing or contradicted, or if a sentence is ambiguous.

The facts the reply must carry:

- has no 'user_id' key
- print(row.keys())
- row.get('user_id')
- instead of raising
