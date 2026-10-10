---
description: >-
  Knowledge-base paired test, arm on (docs/kb and its inline index present). Passes when the answer says stray .orig/.rej files must be deleted before regenerating the manifest.
tags: [kb-on]
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep]
---

I just applied a patch that touched factory/templates/tools/factory/protocol.py, and the patch tool left a protocol.py.orig next to it. What exactly do I run before I commit, and in what order? Answer from this repo; don't change any files.
