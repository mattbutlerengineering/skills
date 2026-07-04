---
stage: capture
run: maintenance:login-timeout
date: 2026-07-03
re-entry: architect
---

# Defect: login timeout

Sessions expire after five minutes instead of thirty; the session store
design has to change to fix it.
