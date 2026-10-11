---
summary: A PR body needs a WO id or a "No work order:" line plus Closes #N, or detector B fails on CI only — it skips locally.
sources: gates.py, knowledge_plane.py, validator.py, .github/workflows/validator.yml
verified: 55d5eae43e2f6c27dea78200aa71f5d3966bf434
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

## Quoted tokens, and the job an edit does not re-run

Added 2026-10-10 (from #650).

- The needs-review-label job (`validator.py`'s uncited-skip gate) reads
  a four-digit `WO-` token as a **claim** unless it sits inside a fenced
  block or on a `>` blockquote line (`validator._unquoted`, fences by
  `knowledge_plane.fence_open`/`fence_closes`). Inline backticks do
  **not** quote it, so a body that merely mentions an order in prose
  makes the job try to flip that order's mirror.
- That job runs only on `opened`/`reopened` or `workflow_dispatch`, not
  on `edited`. Fixing its body does not re-run it: close and reopen the
  PR, or `gh workflow run validator.yml --ref <branch> -f pr=<N>`.

## Stacked PRs never close their issues

Added 2026-10-10 (from #652). GitHub honours `Closes #N` only when the PR
merges into the **default** branch. A PR merged into a parent branch
never closes its issue, not even after the parent lands on `main`, so
the fixed issue looks open and unfixed to an audit. Close it by hand, or
put the `Closes` line on the PR that reaches `main`.

