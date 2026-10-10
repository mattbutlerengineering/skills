---
stage: idea
run: feature:lean-in-the-build
date: 2026-10-10
origin: "GitHub issue #626 ('Improve architecture as part of our workflow', filed by the owner; body: 'Use a skill like ponytail or something similar to make sure that as we are building that we are generating optimal code and minimizing slop.'). Not a docs/backlog.md seed, so no backlog line is claimed. Idea-stage answers come from the owner-confirmed autorun brief (autorun-brief.md in this directory), collected one question at a time; no live interview was held in this stage."
assumptions:
  - "The optional last30days corroboration was not run: the idea skill says never run it unasked, and the brief does not ask for it, so the brief alone is the complete interview result."
  - "The related backlog seed ('Nothing in the pipeline asks \"does this fact already have an owner?\"', from: maintenance:one-fact-one-owner) is cited as evidence but not claimed. This run starts from #626, not from that seed, and the seed's own remedy (running the one-owner pre-pass over the run's changed files at Review) is a different mechanism from wiring lean's ladder and cut-list into Implement and Review. Claiming it would mark that remedy as being worked on when it is not. Whether lean's cut-list ends up covering part of the seed's class is a question for Review of this run, not a claim to make at Idea."
---

# Idea: lean in the build — Implement and Review consult `lean`

## Problem

Agents in Implement write more than the task needs: speculative helpers,
re-implemented standard library, a second owner of a fact the repo already
states somewhere else. Nothing in the pipeline asks "does this need to
exist?" while the author is still looking at the code. The `lean` utility
skill asks exactly that question, but no stage invokes it, so it only helps
when someone remembers to call it by hand.

## Who has it

- **The owner**, reviewing agent PRs at the merge gate. Today they catch
  bloat by eye, or a later `deepen` / one-owner pass catches it after it has
  already landed on main.
- **Agents running Implement and Review**, which have no step that tells
  them to climb the ladder before writing or to cut-list the diff after.

## Why now

`lean` just landed (PR #632, PRD-0011). Before it existed there was no
skill to wire in; now there is one, and it sits unused by every stage.

## Evidence

- **Anecdote:** the owner's issue #626, asking that the build itself
  generate optimal code and minimize slop.
- **Repo history:** the one-fact-one-owner class recurred at least seven
  times, and two instances needed emergency ADRs (0058, 0060), because
  Review reads only its own run's diff and nothing asks the ownership
  question at the moment of change (recorded in the `docs/backlog.md` seed
  "Nothing in the pipeline asks 'does this fact already have an owner?'").
  That is history of one class of bloat, not a measurement of how much
  bloat agents write in general; no such count exists yet, and its absence
  is recorded as absence.

## Solution hunch

Implement climbs lean's ladder before writing each work-order row and
records the rung it stopped at. Review runs lean's cut-list over the run's
diff and files each cut as a finding. Owner decision (2026-10-10): wire
both stages — not Review-only, and not a CI check or hook. `lean` stays a
utility skill that owns no artifact and is never routed to; the stages
consult it. How the rung and the cut-list are recorded is for later stages.

## Success in one sentence

Every run's `review.md` carries a lean cut-list over its diff, Implement
records which ladder rung each row stopped at, and lint and evals pin both.

## Unknowns & risks

- **Boilerplate nobody acts on.** The cut-list becomes a ritual section that
  says "none" every time, or lists cuts nobody takes.
- **Bloat in the record itself.** Recording a ladder rung per row could
  bloat `breakdown.md` — the opposite of the point.
- **Harness neutrality and eval regression.** Stage skills must stay
  harness-neutral, and their existing evals must not regress when the new
  steps are added.
- **Kind drift.** `lean` must remain a utility skill (ADR-0023) even though
  stages now consult it; a stage that starts treating it as a routed stage,
  or a lint rule that gives it an artifact, breaks the taxonomy.
- **Normative change.** If the protocol is edited to say what Implement and
  Review must record, that is a deliberate contract change for every
  target repo, and must be stated as one.
- **Local base.** This branch is built on `feat/lean-and-polish-skills`
  (PR #632), because it needs `lean` to exist. If #632 changes before it
  merges, this run's base moves under it; no stacked PR is ever opened.

## Work already in flight

The protocol's guard ran on 2026-10-10. `gh pr list --state open` returned
one pull request, #632 (`feat/lean-and-polish-skills`, the lean and polish
utility skills, PRD-0011) — the base this branch builds on locally, not a
duplicate: it adds `lean` but wires it into no stage. A scan of local and
remote branches and worktrees for `lean` found only #632's branch and
worktree and this run's own. The reviewer-token run
(`fix/reviewer-token-boundary`, no PR open yet) changes the validator and
workflow permissions, not Implement or Review's use of `lean`. Outcome:
nothing matches.

Next stage: PRD, via the `prd` skill or the router.
