---
stage: architect
run: maintenance:login-timeout
date: 2026-07-03
---

# Architecture: session store

The session store moves from the in-process cache to the shared store,
so expiry is owned in one place. The work has not been broken down yet —
this run re-entered at architect, so decompose is the next stage and
breakdown.md does not exist.
