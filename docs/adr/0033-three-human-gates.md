# Three human gates

- Status: accepted
- Date: 2026-07-11

The factory's goal is maximum AFK execution, but unbounded autonomy is
how a bad artifact poisons everything downstream of it: a wrong PRD
multiplies into wrong work orders, a wrong merge multiplies into wrong
rebases. 8090's commercial model (humans own requirements and
architecture; agents execute) and the ai-tooling adoption guide (treat
autonomous merges as the *last* graduation, earned on data) agree on
where human judgment pays.

## Decision

Exactly three human gates, each a **physical** control, not a norm:

1. **PRD approval** — PRDs enter only via a PR touching the run's
   `prd.md`; CODEOWNERS plus required code-owner review makes the merged
   PR the approval record. The lifecycle label `wo:prd-approved` is
   derived from it, never the source.
2. **Blueprint/ADR approval** — the same mechanism on `docs/adr/**`,
   `architecture.md`, and `docs/design/**`. Architecture and design
   cannot exist on main un-approved.
3. **PR merge** — branch protection on main: required status checks (the
   detector suite and tests) plus code-owner review. Review is asynchronous
   and batched; agent review pre-chews every PR so the human check is
   judgment, not linting.

Everything between the gates runs unattended.

**Graduation, not exception:** a work-order class (e.g. `type:chore
risk:low`) may graduate to auto-merge only on evidence — ≥ 20 merged PRs,
≥ 90% acceptance rate, zero defect escapes attributed to the class, churn
≤ 10% — recorded as a one-line, owner-gated config change. Required
status checks are never bypassed; only the review requirement relaxes,
and one escape auto-revokes the class.

A **dormant fourth gate** costs nothing while unused: deploy workflows
sit behind a GitHub environment with required-reviewer approval, so
production deployment is human-gated the day a product has real users
without redesigning anything.

## Consequences

- The human is the throughput bound between gates, so **gate latency**
  (median hours an artifact waits at each gate) is a first-class weekly
  metric — it decides where autonomy graduates next.
- Rejections at any gate are comments, never silent edits: the correction
  stream is the raw material the reflect loop turns into charter rules.
- Changing the number or placement of gates is a human-only decision; no
  agent charter may propose-and-apply it.
