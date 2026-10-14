---
stage: idea
run: feature:live-console
date: 2026-10-14
---

# Idea: Live console — see and answer what the running work is waiting on

## Problem

Decisions wait on me and I don't know it. A merge ask, a gate, or a
question sits in some terminal, issue or PR until I happen to look, and
the work behind it stalls on me while everything around it keeps
running. With several sessions, loops, Conductor batches and routines
going at once, the only way to learn what is waiting is to read each
terminal and each issue in turn.

## Who has it

Matt — the solo operator of the pipeline and the factory, across this
repo and the stamped consumer repos. Copes today by keeping several
Claude Code terminals open and reading each one, by sessions messaging
each other to coordinate (two sessions did exactly that on 2026-10-14
to split a wave of issues and a release), and by opening GitHub for
PRs and gate issues. The existing process console (`dashboard.py
serve`, feature run `process-dashboard`) shows where things stand at
rest — runs, gate queues, spend, drift — not what is happening now.

## Why now

The work moved from one attended session to many unattended ones:
parallel Claude sessions shipping waves and coordinating by message,
self-paced `/loop` reviews, Conductor batches in a consumer repo (and
the 4+ item batch PRD-0013 states, #822), and cloud routines. They now
outnumber the operator's attention, and the console built for one
repo's state at rest does not see any of it.

## Evidence

- **Measured (2026-10-14, this repo's `docs/factory/costs.jsonl`):** 32
  gate-wait rows, the newest from 2026-09-28. Most merge waits were
  under a minute — sessions where the operator was present and had
  authorized a batch of merges. Three merge gates waited 923 hours (38
  days) each, recorded 2026-08-19. PRD gates waited 0.4–1.7 hours.
- **Measured gap:** nothing after 2026-09-28 is recorded. The waits
  that happen now — a terminal question in one of several sessions, a
  Conductor merge ask, a cross-session handoff — are recorded nowhere,
  so how long they take cannot be measured today. The blind spot is
  part of the problem, not just a hole in the evidence.
- **Anecdote (this session, 2026-10-14):** one session's merge question
  for a green PR waited while another session sent messages asking
  whether it was merged yet, and planned to ask the operator the same
  question a second time.
- **Recorded hazard:** per-PR CI cannot see two PRs that fail together
  (`docs/kb/cross-pr-merge-hazards.md`); a wave open at once (seven PRs
  on 2026-10-14) is where that bites.

## Solution hunch

A hunch, not a design: a live console on the desk's second monitor,
grown from `dashboard.py serve`, whose headline is **everything
waiting on me, from every source, oldest first**.

- **Answer GitHub-backed decisions in place** — merge, gate pass, gate
  reject — with the evidence beside each: CI, diff, cost, and a
  pairwise merge test against the other open PRs.
- **Route the rest** — a question in a Claude Code terminal shows its
  full text and jumps to that session; it is not answered from the page.
- **Beside the decisions:** who is doing what (each session, loop,
  Conductor worker and routine, its current item, time since it last
  made progress, retries), PR collisions before merge, spend burn
  against budget, and trends over time (wait, rework, cost per item)
  so the process can be seen improving.
- **The same state, thinner, everywhere else:** in the terminal, on a
  claude.ai page, and on the phone, where a GitHub decision should be
  answerable in one tap.

## Success in one sentence

Nothing waits on me unseen: every decision waiting on me, from any
session, Conductor batch, routine or PR, shows up in one place within a
minute, and the time from asked to answered is measured.

## Unknowns & risks

- **Can the console see inside sessions? (the one that kills it)**
  Claude Code sessions may not expose "waiting on you" to an outside
  process. Candidate sources — Notification and Stop hooks, the session
  list cross-session messaging reads, transcripts — are unproven. If
  none is reliable, the headline has no data, so it is proven first.
- **It becomes the project.** A "world-class" console can swallow weeks
  that should go to shipping product work; scope has to be cut by the
  success sentence, not by what would be impressive.
- **Noise and staleness.** Polling GitHub across repos can hit rate
  limits or lag, and a console that is sometimes wrong stops being
  trusted.
- **The phone gap.** The state lives on this machine and in GitHub;
  reaching the phone needs it pushed or hosted, a separate problem from
  the desk view.
- **Answering from a page is acting.** A merge from the console is the
  operator's explicit decision; the page must never become a way for an
  agent to merge on its own.
