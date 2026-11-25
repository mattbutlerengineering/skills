# Project goal: faster, higher quality, more autonomy — and it decides priority

- Status: accepted
- Date: 2026-11-22

Targets in the metrics table are placeholders until the first baseline run
(see Consequences); the goal, the metric definitions and the prioritization
rule are confirmed. It supersedes ADR-0069's choice of autonomy metric.

## Context

- No project-wide goal existed. ADR-0069/ADR-0080's "accepted work orders
  per gate-wait hour" covers autonomy on the work-order path only, and no
  tool computes it. The work-order path has had no live traffic since
  2026-08 (the assembler skipped its last 50 runs).
- Work selection ranked by urgency, then age: red main, the oldest ready
  issue, then any "process gap" (the daily and hourly routines, the
  implement-queue default `[security, ci-fix, feature, audit]`). No rule
  named a goal, and "process gap" let the factory keep adding process to
  itself.
- Last 30 days to 2026-11-22: 556 commits, 298 of them `fix:`, most of
  those fixing the factory (tests, detectors, queue, ledgers). Since
  2026-10-01 about 1 commit in 5 touched `skills/`, the product.
- Nothing measured lead time, escapes, or unattended merges.

## Decision

**Goal.** Deliver product outcomes faster, with higher quality, with more
autonomy. Every piece of work and every process must name the metric it
moves. Work that moves none is declined, and process that protects none is
removed.

**Delivered work means product outcomes**: a change plugin users receive —
`skills/**`, `docs/pipeline-protocol.md`, `.claude-plugin/**`, and the
stamped `factory/templates/**` payload. Everything else (detectors, routines,
ledgers, queue and conductor tooling, ADRs, kb pages) is overhead to
minimize; it earns its place only by moving a product metric.

| Metric | Definition | Target |
|--------|------------|--------|
| Speed: lead time | Median hours from issue opened to PR merged, product PRs only | Baseline, then halve within 8 weeks |
| Quality: escape rate | Share of product PRs reverted, or named by a later `fix:` PR (`Fixes-PR: #N`; fallback: a fix PR touching the same shipped files), within 14 days | < 10% |
| Autonomy: unattended share | Product PRs merged with zero Owner touches before the merge (no Owner commit, review or comment); a gate-path merge click is not a touch | >= 80% |
| Guardrail: overhead ratio | Merged PRs touching no shipped path / all merged PRs, 4-week rolling | <= 30% |

**Prioritization rule.** Selectors (the improvement routines,
implement-queue, the backlog) choose in this order; age is only a
tie-breaker, and an issue without a `goal:*` label is not ready:

0. Red main / security (unchanged).
1. An escaped product defect (`goal:quality`).
2. While the overhead ratio is over target: a removal from the sunset list
   (`goal:overhead`).
3. Product work moving the metric furthest from its target, with evidence
   cited, smallest first (`goal:speed`, `goal:quality`, `goal:autonomy`).
4. A new process, only with a register row naming its metric and the
   escape it would have caught.
5. Otherwise a quiet run or a decline with a note.

**Process register and sunset rule.** `docs/process-register.md` lists
every process with the metric it protects and its last evidence of a real
catch (a PR or issue link). A process with no such evidence for 60 days is
flagged by the weekly metrics run and removed by one PR with a superseding
ADR where an ADR exists. Adding a process requires a register row.

## Consequences

- ADR-0069's "accepted work orders per gate-wait hour" is retired as the
  north star; its inputs (`cost_ledger.dispatched`, `gate_wait`) stay.
- Work that follows: `tools/goal_metrics.py` computes the four metrics and
  rides the weekly cost report; `goal:*` labels and the selector rewrites;
  the process register; first-wave removals of zero-traffic processes.
- Baseline and final targets are recorded here by a follow-up commit once
  `goal_metrics.py` has run for real. Success is judged at 8 weeks
  (2027-01-17) from `docs/factory/goal-metrics.jsonl`.
- Work-order machinery also ships to stamped repos, so it leaves through
  the register's sunset rule, not a one-wave cut.
