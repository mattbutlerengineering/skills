---
stage: prd
run: feature:seed-backlog
date: 2026-07-05
ux: not-applicable
ux-reason: file convention and skill instructions; no user-facing surface
---

# PRD: seed backlog

## Problem statement

Idea seeds surfaced by retros and working sessions vanish into finished
runs' `retro.md` and session transcripts; starting the next run means
reconstructing intent from memory. The operate→idea loop the pipeline
advertises has no carrier.

## Solution

A strictly advisory `docs/backlog.md` seed inbox in the target repo. Closing
a run appends its retro seeds there; any session may append a well-formed
seed at any time. When someone asks "what's next" with no active run, the
router lists unclaimed seeds and proposes starting from one; a run that picks
a seed marks it claimed in place. The file never influences stage
orientation — artifacts remain the only state (ADR-0004, ADR-0029).

## Actors

- **Maintainer** — the human running the pipeline on a repo (or an
  orchestrating agent acting for them mid-session).
- **Operate skill-follower** — whoever executes the operate stage at
  run close.
- **Next router** — the orientation skill invoked as "what's next".
- **Idea skill-follower** — whoever starts a new run at the Idea stage.

## User stories

1. As the **maintainer**, I want seeds recorded in one durable place, so
   that the next run starts from a list instead of memory.
2. As an **operate skill-follower**, I want an append convention for retro
   seeds, so that closing a run files its seeds with no separate effort.
3. As the **maintainer**, I want any session — mid-run or not — to be able
   to append a well-formed seed line, so that mid-session discoveries
   (the common case) aren't lost just because no run is closing.
4. As the **next router**, I want to read unclaimed seeds when no run is
   active, so that I can propose what to start next.
5. As an **idea skill-follower**, I want a claimed seed to feed the Idea
   interview and be marked `(claimed: <run>)` in place, so that the list
   stays honest and the new run records its origin.

## Success criteria

- [ ] `docs/backlog.md` exists and every entry matches the recorded entry
      grammar — mechanically checkable (lint).
- [ ] `skills/operate/SKILL.md` instructs appending retro seeds to
      `docs/backlog.md` at run close.
- [ ] `skills/next/SKILL.md`: with no active run and unclaimed seeds
      present, the router lists them when proposing what to start.
- [ ] Claiming records `(claimed: <run>)` on the seed line in place — and no
      skill text anywhere treats `backlog.md` as orientation state.

## Out of scope

- Prioritization or scoring of seeds (the list is append-ordered; humans
  choose).
- Mirroring seeds to the issue tracker — ADR-0026's bridge stays
  work-item-only.
- Any portfolio dashboard or cross-run status view.
- Hooks or automation that auto-append seeds.
- Any effect on stage orientation (hard ADR-0004 boundary).

## Open questions

- Exact entry grammar (one line? seed + origin + claim marker?) — Architect,
  guided by ADR-0029's conventions sketch.
- Should lint validate `backlog.md` in target repos, or only in this repo's
  fixtures? — Architect (lint runs here, not in target repos; the checkable
  grammar may live in eval fixtures/tests instead).
- Do claimed entries stay in place forever or get pruned to an archive
  section once their run completes? — Architect; ADR-0029 recommends
  in-place marking, revisit if the file bloats.
- Does `capture` also read the backlog (deferred defects as seeds)? —
  Architect; ADR-0029 lists capture as an optional producer, not consumer.
