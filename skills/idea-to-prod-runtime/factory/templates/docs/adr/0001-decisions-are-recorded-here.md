# Decisions are recorded as ADRs in this directory

- Status: accepted
- Date: 2026-08-05

Seeded by `factory-init`.

A repo that takes factory work orders is read by agents as often as by
people, and an agent has no hallway to ask in. Decisions that live only in
someone's head — or only in a merged PR thread — get re-litigated by the next
contributor, human or otherwise, because nothing tells them the question was
already settled.

## Decision

Every decision that constrains future work is recorded here as a numbered
ADR, and this directory is the approved blueprint the second human gate
(ADR-0005) approves. Supersede, never rewrite: an old ADR keeps its text and
gains a status line pointing at the one that replaced it, so the reasoning
behind a reversal survives alongside the reversal.

Two mechanical consequences, both enforced by the stamped detectors: every
ADR carries a `- Status:` line from the vocabulary in `README.md` and an index
row there, and every `ADR-NNNN` token anywhere under `docs/` must resolve to a
file in this directory.

## Consequences

- Citing a superseded decision is a build failure, not a style note. That is
  the point — drift between the blueprint and the work is caught at the gate.
- References to the upstream idea-to-prod project's own ADRs must be written
  by name or link, never as a bare token, or the detector will read them as
  dangling local citations.
- The seeded ADRs 0002–0006 record what stamping this factory decided on your
  behalf. Disagreeing with one is normal; supersede it here rather than
  quietly working around it.
