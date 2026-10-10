---
type: llm
---

PASS if the reply says to delete the stray .orig (and any .rej) file BEFORE running `python3 factory_init.py update-manifest`, because the manifest regeneration hashes every file under factory/templates/ and would checksum-pin the stray file.
FAIL if it says to regenerate first and clean up after, does not mention removing the .orig file before regenerating, or omits update-manifest.
