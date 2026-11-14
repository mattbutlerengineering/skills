# Every driver claims a ready issue through the queue's claim step

- Status: provisional
- Date: 2026-11-13

Proposed on 2026-11-13 for request 2 of #1721, which the Owner kept
open as a design decision across drivers. The Owner asked for it to be
drafted as a proposal. It builds on the label claim and post-claim check
of `implement-queue` (#1714) and on the `Driver: implement-queue` line
that makes queue-driven pull requests attributable (#1741). It moves no
claim rule; it gives the existing one a single owner file that drivers
other than the queue run too.

## Context

A consumer repo ran `implement-queue` beside other drivers: scheduled
routines that drain feature series and open fix pull requests. In the 7
days to 2026-11-11, 4 of its 315 merged pull requests came from a queue
branch (#1721). The other drivers claimed and merged work without the
queue's claim, so the queue's labels did not show what was in flight,
and its batch was guessed from labels and branch names.

The queue's claim is rigorous: `ready` removed first and only on a 200,
`in-progress` added, then a timeline check that exactly one
`in-progress` event follows the last `ready` (#1714). But it lived
inside Phase 1 of the queue's `SKILL.md`, written as the queue's own
step, so another driver had nothing to point at. And the queue's Phase 0
called a pull request its own whenever the issue it closes carries
`in-progress`, so a driver that did adopt the label would have had its
failing pull requests fixed by the queue and would have blocked the
queue's claiming, the problem #1712 had just removed for foreign pull
requests.

## Decision

1. **One claim step, one owner file.** The claim transition moves out of
   Phase 1 into `skills/implement-queue/references/claim.md`, unchanged
   in substance. The queue's Phase 1 runs it, and so does every other
   driver that takes `ready` issues in a repo that runs the queue,
   before it starts any work on an issue. What may be claimed is the
   queue's Phase 1 drop list for every driver.
2. **The zone lock is the profile's `lock` hook for every driver.** A
   driver that updates, rebases or merges an open pull request takes
   that lock for the pull request's zone first, as the queue's merge
   train does, and releases it on any exit.
3. **The `Driver:` line says whose pull request it is.** A driver's pull
   request closes its issue and ends with `Driver: <name>`. The queue's
   Phase 0 treats a pull request whose `Driver:` line names another
   driver as foreign whatever its issue's labels: never fixed, re-run or
   updated by the queue, and never blocking its claiming. A pull request
   closing an `in-progress` issue with no `Driver:` line stays the
   queue's, as before.
4. **A driver finishes the way a queue worker does.** It labels the
   issue by the queue's worker outcome table, and a driver that stops
   before starting work moves the issue back to `ready`.

## Rejected alternatives

- **An executable claim tool in the payload.** It would turn the prose
  into code, which is the better end state (the decision logic as
  prose is a known cost), but no second caller of such a tool exists in
  this repo, and AGENTS.md admits a shared module only with real callers
  and observed divergence. The consumer's drivers are routine prompts
  that point at skill files, so a file is what they can adopt today.
- **The queue inferring other drivers' work from branch names or
  authors.** That is the guess #1721 describes: the consumer's drivers
  use plain `fix/` and `feat/` branches under the Owner's login.
- **A lock service shared by every driver.** It needs infrastructure
  this plugin does not ship, and the label claim with its timeline check
  already makes a collision unlikely and detectable.

## Consequences

- Work another driver claimed is visible to the queue: Phase 1 drops
  its issue, Phase 0 step 4 lists it, and its pull request's files count
  against the queue's batch.
- A driver's red pull request never stops the queue, because its
  `Driver:` line makes it foreign.
- Adoption is per driver and outside this repo: a driver that keeps its
  own claim stays invisible, as today. Nothing here detects a driver
  that skipped the step.
- The claim's guarantee is unchanged: a best-effort mutex between
  sessions, not a lock.

## If rejected

Move the claim transition back into the queue's Phase 1, delete
`references/claim.md`, and drop the `Driver:` clause from Phase 0 step
3; the `Driver: implement-queue` line goes back to being read by
nothing.
