# Adopt GitHub's native merge queue, composing with agent-merge

- Status: accepted
- Date: 2026-09-21

## Context

- Epic #439 (Map: Factory evolution) ratified an adopt/adapt/reject pass
  over four survey shortlists (issue #436). `docs/research/
  review-ci-automation.md` shortlisted GitHub's native, batched
  speculative-merge queue as its **strongest finding**, verdict Adopt,
  "Own ADR? Yes."
- This repo already has direct, first-party evidence of the exact
  problem the queue solves: a documented pairwise-merge audit found
  real cross-PR hazard pairs — "two PRs each green alone, red together,
  invisible to both CIs" — discoverable only by hand-merging every
  contended pair in an isolated worktree and re-running the full triad,
  once, as a manual sweep (`docs/research/review-ci-automation.md`,
  "Rationale 1"). That sweep does not run continuously; it is an audit,
  not a gate.
- Gate 3 (PR merge) is already a **review gate an agent may satisfy**,
  not an unconditional human-hands-on-merge gate (ADR-0033, amended by
  ADR-0036). An agent may merge only when: (1) required status checks
  pass on the merge-result commit, (2) an independent non-authoring
  review is recorded on the PR, and (3) the PR is not itself a gate
  change (`docs/adr/**`, `prd.md`, `architecture.md`, `docs/design/**`
  stay human-merged).
- GitHub's merge queue tests each queued PR against the state it will
  actually land into — "it tests A against main, B against main+A, and
  C against main+A+B" — and a check failure at any position pulls that
  PR and restarts every PR behind it with a fresh speculative commit.
  Required-check workflows must add `merge_group` as a trigger or they
  never run inside the queue.
- Honest accounting, not glossed over: at this repo's actual 40+-open-PR
  backlog volumes, a mid-queue failure's cascade — every PR behind the
  failure gets a fresh speculative commit and reruns — is a real
  operational cost, not a theoretical one. The survey flagged this
  explicitly rather than treating adoption as a free config flip.
- The survey also flagged an unresolved question: how queue admission
  composes with a *review* requirement (ADR-0036 condition 2) rather
  than a plain CI status check — the fetched GitHub docs describe queue
  mechanics and required status checks generically, not how a review
  gate interacts with queue admission specifically.

## Decision

Adopt GitHub's native merge queue for gate 3, as an **addition to**
ADR-0036's agent-merge conditions, not a replacement for the reviewer
charter's judgment:

- The queue owns **condition 1** (required status checks pass on the
  merge-result commit) — continuously and automatically, superseding
  the ad-hoc pairwise-merge sweep as the mechanism that catches
  cross-PR hazards. Required-check workflows (`.github/workflows/
  validator.yml` and siblings mirrored via `factory_init.MIRRORS`) gain
  `merge_group` as a trigger so they execute inside the queue, not only
  on `pull_request`/`push`.
- **Conditions 2 and 3** (independent non-authoring review recorded on
  the PR; the PR is not itself a gate change) stay owned entirely by
  the reviewer charter and CODEOWNERS, exactly as ADR-0036 already
  defines them. A PR enters the queue only after it already satisfies
  those two — the queue never decides review substance, it only
  arbitrates check state at merge time. This repo's adoption rule
  (epic #439 Notes: "adopt = borrow the mechanism, reimplement
  in-house... external tools admissible only at the workflow/action
  seam") is satisfied exactly: the queue is a GitHub-native workflow
  seam, not a vendored dependency, and no repo Python code changes.
- The cascade-cost tradeoff at current backlog volumes is accepted
  deliberately, not ignored: the actual capacity/ordering tuning
  (queue depth limits, whether it is repo-wide or opt-in per branch
  protection rule, how a stuck PR is evicted) is implementation detail,
  deferred to the breakdown row that lands this (see `docs/features/
  factory-evolution-v1/breakdown.md`), not resolved by this ADR.
- The open composition question (review-requirement interaction with
  queue admission) is likewise deferred to that implementation work,
  which must design against it before the queue is enabled — this ADR
  settles *that* adoption happens and *how* responsibility divides
  between the queue and the charter, not every operational parameter.

## Consequences

- No code ships with this ADR — per epic #439's own framing, this map's
  tickets resolve decisions; the factory's dispatch loop executes the
  seeded backlog. Enabling the queue needs a repo-settings change
  (branch protection / merge queue configuration, an operator action)
  plus `merge_group` triggers on the mirrored required-check workflows,
  both named as follow-up implementation work, not performed here.
- ADR-0036 is not amended: this ADR composes with it by dividing
  responsibility (queue: check-state; reviewer charter: review
  substance and gate-change detection), the same division the survey's
  own rationale argues for.
- Closes the adoption half of `docs/backlog.md`'s merge-queue item
  (`docs/research/review-ci-automation.md` shortlist item 1); the
  queue's live cascade-cost and review-composition tuning stay open,
  tracked by this run's breakdown row, resolved when that work is
  actually implemented — not fabricated here.
- Serves the map's optimization target (autonomy per human-hour at the
  three gates, ADR-0069): a continuously-run, automated cross-PR-hazard
  check reduces the gate-3 attention a human or an independent reviewer
  must spend re-discovering hazards a manual sweep already proved exist
  at this repo's real PR volumes.
