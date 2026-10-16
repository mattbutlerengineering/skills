# Every stage commits its artifact at its boundary

- Status: provisional
- Date: 2026-10-15

Amends no record. ADR-0021's rule that orientation derives from which
artifacts exist stands, and the working tree stays what it reads. This
decides what a stage owes before it ends, and what an unattended run
does when that is not met.

## Context

Artifacts are the state (`docs/pipeline-protocol.md`): there is no
manifest, and the next stage is the first whose artifact does not
exist. Nothing said who commits them. Stage skills wrote their file and
handed off; Implement committed at item boundaries because the code
needed it; Ship committed what the release needed. Every other
artifact waited for whichever later stage happened to commit.

In a consumer run driven by `autorun` (issue #943), eight of the run's
nine artifacts, and the brief, sat untracked in one checkout for nine
days until Ship found them by accident. Nothing was lost that time. A
`git clean`, a worktree reap or a second session on the same path
would have erased the run's entire state, and orientation — which
reads the working tree — would have reported a fresh run.

## Decision

1. **The stage contract gains a closing step.** A stage ends by
   committing its own artifact on the run's branch, subject
   `docs(<slug>): <stage> — <one line>`. The protocol doc states the
   rule once, under "Commit at the stage boundary"; each stage skill's
   last step carries one identical sentence pointing at it, and
   `tests/test_stage_boundary_commit.py` pins the section and the
   eleven recitals the way the open-PR pre-flight is pinned.
2. **Orientation is unchanged.** "Complete when: file exists" still
   reads the working tree. `next`, the board and every offline tool
   see a stage the user has finished and not yet committed; the commit
   is a boundary step, not the completion predicate, and `protocol.py`
   gains no predicate for it — the check is one git command the doc
   states, and a stage skill could not call the module anyway
   (ADR-0008: skills depend on nothing but a bare install).
3. **`autorun` gates on the commit.** Its between-stage gate confirms
   the artifact exists, is complete, and is committed (`git status
   --porcelain -- <artifact>` prints nothing). An uncommitted artifact
   is a failed stage: autorun never advances past it, names the
   artifact and what it lacks on re-dispatch and in its report, and
   stops after the second failure as before. It commits its own brief
   the same way, since a resume in a fresh checkout reads nothing else.

## Alternatives that lost

- **Make "committed" the completion predicate.** One rule everywhere,
  but `next` would then hide a stage the user finished a minute ago,
  every working-tree reader (the board, the dashboard, the fixture
  trees under `tests/`) would need a repository, and a stamped repo's
  tools would shell out to git to answer what today is a file stat.
- **Commit at autorun's gate instead of in the stage.** Covers the
  unattended case only. An interactive run through `next` would still
  leave every artifact untracked, and the stage is the one that knows
  what it wrote.
- **Leave it to Ship.** The status quo that lost nine days.

## Consequences

- A run's branch gains one small commit per stage. The history reads
  like the pipeline, which is the point.
- A stage that cannot commit (no repository, a read-only checkout) now
  has to say so; before, it silently left the file behind. An
  interactive stage says it and continues; `autorun` stops.
- Implement's item-boundary commits already carry the breakdown, so
  its closing commit usually has nothing new to carry; the sentence is
  kept identical anyway, because the check (`git status --porcelain`)
  is what matters, not the commit count.
- Not covered: files a stage writes outside the run directory
  (Operate's seed in `docs/backlog.md`, a changelog line at Ship) are
  not the stage's artifact and are not gated. Committing them with the
  artifact is good practice the rule does not require.
