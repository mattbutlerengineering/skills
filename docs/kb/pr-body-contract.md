---
summary: A PR body needs a WO id or a "No work order:" line plus Closes #N, or detector B fails on CI only — it skips locally.
sources: gates.py, knowledge_plane.py, .github/workflows/validator.yml
verified: 6aacc5cde45558eacc6d8281fdef6da6ac839bb2
related: gates-scan-every-doc
---

# The PR body is gated, but only on CI

`gates.check_pr_traceability` (detector B) reads the pull request body
from the CI event payload. Locally there is no payload, so B **skips
silently** — `python3 gates.py` passes on your machine and the
`pull_request` run fails. It reads like a flaky check; it is not.

The body must carry both:

1. A work-order id (a four-digit `WO-` token), **or** a waiver line
   matching `No work order: <reason>` (`gates.NO_WO_DECLARATION`; the
   reason must be non-empty).
2. A closing keyword with an issue number — `Closes #N`, `Fixes #N`,
   `Resolves #N` (`knowledge_plane.CLOSES_TOKEN`). The waiver does not
   excuse this half.

Two traps when fixing a red B:

- Issues #178 and #181 are permanent state (the gate queue and the
  improvement journal). Never write `Closes #178` or `Closes #181` to
  satisfy the gate.
- Fix the body, don't re-run the failed job. `edited` is a trigger, so
  the edit itself re-runs the check; a re-run replays the payload it was
  dispatched with, stale body and all (issue #216). A factory-opened PR
  gets no events at all — dispatch `validator.yml` with `-f pr=<N>`.
