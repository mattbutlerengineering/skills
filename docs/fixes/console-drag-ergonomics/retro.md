---
stage: operate
run: maintenance:console-drag-ergonomics
date: 2026-08-14
---

# Retro: console-drag-ergonomics

## Outcomes vs. intent

### The seed's promise: click-to-move controls + one reorder lands

- What happened: both, same day. ▲/▼ controls shipped (PR #278, node-
  harness pinned), and the operator's browser reorder rewrote
  `docs/backlog.md` with every marker intact — the first reorder ever
  to land from the page, closing the gap the process-dashboard retro
  named.
- Signal strength: measured (the diff is in the repo; gather clean).

### The parent retro's Change entry: hand-in-browser check in the same work order

- What happened: honored — item 2 *was* the browser check, and the run
  stayed open until a human completed it. The loop waited ~7 hours on a
  file monitor rather than declaring the item done from the HTTP-layer
  evidence. That discipline is what made "good enough for now" an
  observed verdict instead of a guess.
- Signal strength: measured (one complete wait → act → verify cycle).

## Run retrospective

- Keep: acceptance criteria that require a human act when the defect is
  a human-experience defect. The harness can't fake a pointer; the run
  can wait.
- Keep: the file-monitor + quiet-heartbeat loop shape for human-gated
  items — zero polling spam, instant wake on the save.
- Change: nothing structural — the run was two items and closed in a
  day; the deferred minors ride the seed below.
- Stop: nothing.

## Idea seeds

- Backlog reorder polish — operator verdict "good enough for now":
  drag still rough, move buttons lack aria-labels, repaint drops
  keyboard focus after each nudge; consider drop indicators (from:
  maintenance:console-drag-ergonomics)

## Run complete

Closed 2026-08-14. Seed above appended to `docs/backlog.md`.
