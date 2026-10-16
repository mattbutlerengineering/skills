---
stage: prd
run: feature:live-console
date: 2026-10-16
id: PRD-0014
ux: not-applicable
ux-reason: v1 adds one ordered list and one status strip to the existing process console page (PRD-0002) and designs no new flow or screen; UX Design is owed before any action buttons (v2)
assumptions:
  - "Backfill, not a full PRD interview (protocol soft gate, Decompose invoked on a run with only idea.md). The Owner answered two questions in session on 2026-10-16: v1 scope is the read-only headline plus routing plus who-is-doing-what, and the session source is hooks writing events with the session registry as a guarded cross-check. Actors, stories, criteria and exclusions are drafted from idea.md and those two answers."
  - "ux: not-applicable is recorded so the router can hand Decompose off to Implement: protocol.next_stage returns ux-design while prd.md says required and no ux.md exists. The console is a user-facing page; the field records that v1 designs no new flow or screen, not that design is irrelevant. It flips at v2."
  - "Typed id PRD-0014 is the next free id: PRD-0013 is the highest declared in docs/features/*/prd.md on main at 35d0d2e, and no artifact or commit names PRD-0014 (checked 2026-10-16)."
  - "Cloud routines reach the operator only through GitHub: every routine ask the operator can act on is a pull request or an issue the GitHub source lists, so v1 has no journal-comment parser."
---

# PRD: Live console — everything waiting on me, in one place

## Problem statement

<!-- coverage-waiver: context for the requirements below; the Success criteria carry the work every breakdown row cites -->

Decisions wait on the operator unseen. A permission prompt, a question, a
plan approval, a Conductor merge ask or a green pull request sits in one
of several terminals, batch ledgers or GitHub pages until the operator
happens to look, and the work behind it stalls while everything around it
keeps running. Today the only way to learn what is waiting is to read
each terminal and each issue in turn (idea.md). The existing process
console (`dashboard.py serve`, PRD-0002) shows where things stand at rest
— runs, gate queues, spend, drift — not what is happening now, and
nothing records how long a wait took: the cost ledger's 32 gate-wait rows
stop at 2026-09-28, and the waits that happen now (a terminal question, a
Conductor ask, a cross-session hand-off) are recorded nowhere.

## Solution

<!-- coverage-waiver: narrates what the Success criteria check one by one -->

One more view on the existing process console: a headline list of
everything waiting on the operator, oldest first, from three sources —
local Claude Code sessions (reported by hooks), open Conductor batches
(unanswered asks in their ledgers) and GitHub (green open pull requests
awaiting a merge, and the gate queues the console already reads). Each
entry says what is waiting, since when, and where to go to answer it: the
session's name and directory, the `conductor.py answer` command, or the
pull request's URL. Below the headline, a strip shows who is doing what:
each live session with its state and time since its last event. The
console measures the time from asked to answered. It never acts — v1 has
no merge, gate or reply button — so it can never become a way for an
agent to merge on its own.

## Actors

- **Operator** — Matt, the one person every wait is waiting on, at the
  desk with the console on a second monitor.
- **Claude Code session** — a local interactive or headless session,
  including Conductor Workers and loop sessions; a source of waits,
  reported through hooks.
- **Conductor batch** — an open batch whose ledger carries unanswered
  asks; a source of waits.
- **GitHub** — the pull requests and gate issues of the configured repos;
  a source of waits, and the only surface through which a cloud routine
  reaches the operator.

## User stories

1. As the operator, I want every decision waiting on me from any session,
   batch or pull request in one list, oldest first, so that nothing waits
   on me unseen.
2. As the operator, I want each wait to say what is asked and where to
   answer it, so that I go straight to that terminal, batch or pull
   request instead of searching.
3. As the operator, I want to see each live session with its state and
   time since it last made progress, so that I can tell a stall from
   work.
4. As the operator, I want the time from asked to answered measured per
   source, so that I can see whether the waits shrink.

## Success criteria

- [ ] **A session's wait appears within a minute.** With the hooks
  installed at user level, a session that reaches a permission prompt, an
  `AskUserQuestion`, an `ExitPlanMode` approval, an elicitation dialog or
  an `agent_needs_input` notification appears in the headline within 60
  seconds, with the session's name (or its working directory), the kind
  of wait, the hook's message text when the event carries one, and the
  time waiting. When the session resumes — the next prompt is submitted,
  the next tool runs, or the turn ends — the entry leaves the headline
  within 60 seconds. Checked by fixture event files through the gather
  seam, and by one live wait from a real session, timed from the event's
  timestamp to its appearance on the page.
- [ ] **Conductor asks appear.** Every `ask` row with no `answer` row
  naming it, in every batch ledger found in a configured repo's
  worktrees, is an entry naming the batch, item, question, options and
  recommended option, waiting since the row's `at`. Checked by a fixture
  repo with a batch worktree and a ledger holding answered and
  unanswered asks.
- [ ] **GitHub waits appear.** Every open, non-draft pull request in a
  configured repo whose check rollup is green is an entry with its title,
  URL and age; every open gate-queue issue the console already lists
  (`human_gates.open_queues`) is an entry with its age. Red or pending
  pull requests are not waits. Checked by fixture listings.
- [ ] **Oldest first, with a place to go.** The headline is one list over
  all three sources, sorted by time waiting, longest first. Each entry
  names its route: session name, working directory and transcript path
  for a session; the exact `python3 conductor.py answer <batch> <ask-id>`
  command for an ask; the URL for a pull request or issue. Checked over a
  fixture that mixes the three sources.
- [ ] **Who is doing what.** A strip lists each live session with its
  name, working directory, state (`working`, `waiting`, `idle`) and time
  since its last event. When the session registry is absent or its shape
  fails the guard, the strip is labelled `unverified` with the reason and
  shows only sessions the hooks have reported. Checked by fixtures for a
  good registry, a mutated one and none.
- [ ] **Asked to answered is measured.** Each closed wait — a session's
  waiting event followed by its working event, an ask row followed by its
  answer row — yields a duration, and the page shows count, median and
  p90 per source over the last seven days. Checked by fixtures with
  known durations.
- [ ] **The page never acts.** The live endpoint and page issue no write
  to GitHub, no write to a ledger, a batch or a repo, and no message to a
  session; the console's only POST remains the existing backlog reorder.
  Pinned by a test over the handler's routes and a test that the live
  gather receives only the read-only `gh_read` runner.
- [ ] **Battery.** `python3 run_tests.py` reports 0 problems,
  `python3 lint.py` prints `lint: 0 problem(s)`, and `python3 gates.py &&
  python3 gates.py --selftest` prints `gates: 0 problem(s)` and
  `selftest: ok`. No eval definition is edited to pass.

## Out of scope

<!-- coverage-waiver: exclusions, nothing to build -->

- Answering from the page — merge, gate pass, gate reject, reply. That is
  v2, and the UX Design stage runs before it.
- Phone and claude.ai mirrors of the state.
- A pairwise merge test beside each pull request, spend burn, and trends
  beyond the latency figures above.
- Parsing session transcripts (the docs call the format internal),
  reading a session's messaging socket (a per-session inbox, not an
  external interface), and parsing routine journal comments.
- Stamping any of this into consumer repos: like `dashboard.py`, the
  console is operator-level and never mirrored.

## Open questions

<!-- coverage-waiver: questions for the owner, nothing to build -->

- Which hook events fire inside headless `claude -p` Workers. The docs
  state only `PermissionRequest`; the first Conductor batch after the
  hooks are installed settles it, and the install row records the answer.
- Whether `PostToolUse` fires for `AskUserQuestion` once the operator
  answers (the docs are silent). `UserPromptSubmit` covers the common
  case; a live wait during the install row shows which events closed it.
- When v2 adds actions, the `ux:` field flips to `required` and UX Design
  runs on the whole page.
