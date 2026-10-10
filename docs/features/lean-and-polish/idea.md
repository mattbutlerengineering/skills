---
stage: idea
run: feature:lean-and-polish
date: 2026-10-10
origin: "backlog seed: The lean-and-polish branch must absorb the figure and the table when it rebases onto main (from: feature:readme-skill-map)"
assumptions:
  - "Interview answers came from the owner's dispatch brief (autorun-brief.md), not a live interview. Taken without user input."
---

# Idea: two skills that argue for less and for care

## Problem

An agent left to itself over-builds and under-considers. Asked for a date
field, it ships a picker component with its own stylesheet and a new
dependency; asked to finish a screen, it ships the average of every
screen it has seen — competent, familiar, chosen by nobody. The pipeline's
stages say *what* to build (PRD, architecture) and check that it is
*correct* (verify, review), but no skill argues for building less, and
no skill takes a working interface the last step to a considered one.
`ux-design` deliberately stops at flows and screens, before the pixels.

## Who has it

- **The owner**, reading diffs that are larger than the problem and
  screens that look generated. Today they cope by asking for cuts in
  prose, one review at a time.
- **Agents working any repo with the plugin installed**, who have no
  standing instruction to climb a "does this need to exist" ladder or to
  render and look before calling an interface done.

## Why now

Both skills were written on 2026-09-29 and have sat uncommitted in this
worktree since; main has moved 19 commits (plugin 0.4.0, the README
skill map, a third harness). The README skill-map run left a backlog seed
saying this branch must absorb the figure and table when it lands. And
three open issues on UX and design quality (#624, #626, #627) want a base
to build on; the owner chose to land these two first.

## Evidence

Anecdotal: the owner wrote both skills after reading two open-source
skills that address exactly this (Ponytail for less code, Impeccable for
interface quality), and filed the three UX issues. No measured evidence;
the routing eval cases these skills bring are the first measurable
signal, and running them is owed.

## Solution hunch

Two utility skills (ADR-0023): never routed to, owning no run artifact,
invoked directly. `lean` climbs a fixed ladder before writing, returns a
numbered cut-list for a diff or tree with every deletion's references
enumerated, harvests `lean:` shortcut markers, and never cuts the floor
(trust-boundary validation, data-loss handling, security,
accessibility). `polish` reads what is already decided (audience, design
system, the user's direction), names the surface's job, applies one move
per pass, and renders and looks twice before stopping.

## Success

Both skills ship in the plugin, pass every structural check on main as it
is today, appear on every roster (protocol, plugin manifest, README table
and figure, LEDGER, routing eval), and the pull request is ready for the
owner's merge.

## Unknowns

- Whether the descriptions discriminate against their neighbours
  (`review`, `deepen`, `audit`, `ux-design`) — only the paid routing eval
  can say.
- Whether the gap analysis for #624/#626/#627 wants these skills reshaped;
  out of this run.
