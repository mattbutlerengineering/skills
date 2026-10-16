# Ship completes on the outcome it recorded, not on release.md existing

- Status: provisional
- Date: 2026-10-15

Amends ADR-0021's completion rule for one stage. "Complete when: file
exists" stands for every other row, and orientation still reads only
the working tree (ADR-0100); this adds one frontmatter read for Ship.

## Context

Under the prepare-and-stop default an unattended Ship writes
`release.md`, pushes the branch, opens the pull request and stops.
Nothing wrote the merge back: five consumer runs each recorded a
`release.md` saying "prepared, not released" days after its pull
request merged (one for six days), and each retro recorded the same
hole (issue #942). Ship's completion rule was "release.md exists", so
the prepared draft counted as a shipped stage, `next` routed to
Operate, and Operate wrote a retro over a release artifact that
disagreed with production. The consumer's backlog had carried the gap
since August because no stage owned it.

## Decision

1. **Ship records the outcome it reached.** `release.md` frontmatter
   carries `outcome: released | rolled-back | prepared`
   (`protocol.SHIP_OUTCOMES`). `released`: the change reached users.
   `rolled-back`: the release failed or came back and the rollback
   plan ran — the ship skill's failed ship, already a complete
   artifact by its own rule. `prepared`: prepared and stopped, waiting
   on the pull request named as `pending-merge: <PR url>`.
2. **Only a reached outcome completes the stage.** `protocol.py`'s
   `_ship_reached` (the one owner, wired into both walk tables) reads
   the field: `released` and `rolled-back` complete Ship; `prepared`
   and any value outside the vocabulary leave it pending, so the walk
   stops at Ship and `stage_states` shows Operate ahead. A `release.md`
   with no `outcome:` field still completes the stage: it predates the
   field — around seventy in this repo alone — and moving every one
   back to Ship on the board and the dashboard would be a louder defect
   than the one being fixed. Strictness there is a later decision,
   taken by backfilling the field, not by changing the rule.
3. **The write-back is a file edit by whoever next touches the run,
   never a network call in orientation.** `next` announces "confirm
   the pull request merged, then record it" and routes to `ship`,
   whose Release step becomes the write-back when the artifact is
   already prepared. `operate` resolves it at its soft gate or stops,
   and never writes a retro over a prepared release. The read is
   through the forge CLI in both its forms (`gh pr view <n> --json
   state,mergedAt`, or the `gh api` REST form that works in a cloud
   session, issue #945); a merged pull request rewrites
   `outcome: released` and adds `released-at:`, keeps `pending-merge:`
   as the record, and commits under the stage-boundary rule. A pull
   request closed unmerged stays `prepared`, at Ship, for a person.
4. **The router restates it, and lint pins the restatement.**
   `lint.ROUTER_CONDITIONALS` gains the `outcome:`/`release.md`
   conditional, so the router's prose and `_ship_reached`'s literals
   drift loudly, as `ux:` and `re-entry:` already do.

## Alternatives that lost

- **A marker only, no predicate change.** `pending-merge:` alone
  records the wait but routes nothing; Operate would still be next.
- **Orientation asks the forge.** `next` reading the pull request's
  state would answer the question live, and would make orientation
  need a network, credentials and a forge — the opposite of ADR-0100,
  and of "artifacts are the state".
- **Absent `outcome:` means pending.** The principled reading by the
  `ux:` precedent (undecided is pending), rejected for the blast
  radius in Decision 2.
- **A post-merge CI job writes the field.** The job cannot know which
  run directory a merged pull request belongs to without reading the
  artifacts it would be editing, and consumer repos run no such job.

## Consequences

- A Conductor-driven run's Ship step is prepare-and-stop by design
  (`conductor_run`'s ship brief), so its `release.md` says `prepared`
  until the next `next` or `operate` pass writes it back; the
  Conductor's merge turn does not do so today.
- Every new `release.md` carries `outcome:`; the template asks for it.
  An agent that omits it gets the legacy reading (complete), which the
  ship skill's step 7 is there to prevent.
- `rolled-back` is new vocabulary for a state the ship skill already
  had in prose. The template's Outcome section now lists it beside
  `prepared`.
