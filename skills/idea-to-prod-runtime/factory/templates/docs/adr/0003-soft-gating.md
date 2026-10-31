# Soft gating: a missing predecessor offers a backfill, never a refusal

- Status: accepted
- Date: 2026-08-05

Seeded by `factory-init`.

Stages depend on their predecessors — Architect wants a PRD, Implement wants a
breakdown. The strict reading (refuse until the predecessor exists) makes the
pipeline unusable for the cases people actually have: a small fix, a
mid-stream entry, a repo that adopted the pipeline late.

## Decision

A stage whose predecessor artifact is missing offers a quick backfill and
proceeds; it never blocks. For a trivial change the backfill can be three
honest items rather than a full document — but it must be real, because the
downstream stages scale to what it records.

## Consequences

- Any stage can be entered directly. That is a feature, not an abuse.
- The pipeline degrades toward *lighter*, never toward *skipped*: the artifact
  still exists, it is simply smaller.
- A backfill written to satisfy a gate rather than to be true is worse than no
  artifact, because everything downstream trusts it.
