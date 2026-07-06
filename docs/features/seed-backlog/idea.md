---
stage: idea
run: feature:seed-backlog
date: 2026-07-05
---

# Idea: seed backlog — a home for idea seeds between runs

## Problem

As the maintainer, idea seeds and follow-ups surfaced by retros and work
sessions vanish into finished artifacts and session logs. When I sit down to
start the next run, I have to reconstruct "what was I going to do" from
memory — the pipeline advertises that the retro seeds the next idea, but
nothing carries a seed from a completed run to a new one.

## Who has it

The plugin's maintainer today; any user of the pipeline (human or
orchestrating agent) once several runs have completed or are in flight. The
coping mechanisms are memory, scrolling old session transcripts, prose
buried in completed runs' `retro.md`, and ad-hoc GitHub issues filed outside
the pipeline's conventions.

## Why now

ADR-0029 was just accepted provisionally after a gap analysis found the
operate→idea loop is advertised but lossy — and the very session that
produced the ADR demonstrated the pain live (see Evidence). The design is
fresh, and the pipeline is now verified on two harnesses, so subsequent runs
that would consume the backlog are actually going to happen.

## Evidence

Anecdote, same-day (2026-07-05): one working session surfaced roughly six
follow-up signals with nowhere to land except the chat transcript — the
omp `skill://` protocol-doc gap, the failing `next-maintenance-1` routing
case, omp near-miss under-triggering (8/16), the Pi description-limit
chars-vs-bytes question, a ship changelog step, and deprecation/sunset runs.
Structural evidence: `skills/operate/SKILL.md` step 6 turns every retro gap
into "a one-line idea seed", but the seed's only home is the completed run's
`retro.md` — no consumer reads it back.

## Solution hunch

ADR-0029's shape: a derived, strictly advisory `docs/backlog.md` seed inbox —
operate (and possibly capture) append one-line seeds with their originating
run reference; the `next` router and `idea` skill read it when proposing what
to do next; entries are marked claimed when a run picks them up. A hunch to
be designed properly downstream, not a commitment here.

## Success in one sentence

The next time I start a run, I pick the seed from `docs/backlog.md` instead
of reconstructing it from memory — and operate/capture append to it without
being asked.

## Unknowns & risks

- The file drifts from advisory into a second source of truth — the exact
  ADR-0004 violation the spike flagged as this idea's recorded death mode.
- It silently rots because appending is a chore nobody — human skill-follower
  or agent — actually performs when closing a run.
- Seeds mostly appear mid-session outside any run; if operate is the only
  producer, the convention may miss most real seeds (ownership unknown).
