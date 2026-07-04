---
stage: capture
run: maintenance:login-timeout
date: 2026-07-03
re-entry: implement
---

# Defect: login timeout

Sessions expire after five minutes instead of thirty.

## Fix breakdown

- [ ] **Correct the TTL constant** — session TTL back to thirty minutes
- [ ] **Pin it** — regression test on the session TTL
