# Autorun brief: assembly-line

Resume brief, collected from the Owner on 2026-11-06. The run was
driven live through `/next` from Idea to Implement; it carries no
earlier brief. Idea, PRD, UX Design, Architect and Decompose are
committed and Implement is complete (every `breakdown.md` row checked,
`45cd54d`), so this brief only covers what the remaining stages need.

## Feature

The run's own artifacts are the description:
`docs/features/assembly-line/idea.md`, `prd.md` (PRD-0021, `ux: required`),
`ux.md`, `architecture.md`, `breakdown.md` (WO-0198 to WO-0214).

- Scale: feature run, slug `assembly-line`.
- Branch: `feat/assembly-line`, worktree `~/github/skills-wt-assembly-line`.
- Tracker: the brief says nothing about seeding the run from tracker
  issues, so autorun makes no tracker calls of its own.

## Verify: the four human checks

PRD-0021 has four criteria that only people can judge: style match
against the Owner's three reference images, the cold-viewer test (2 of
3 name the steps and the busiest station within 30 seconds), the Owner
would show it in a real presentation, and the demo script run as written.

Owner's decision: **continue through Ship**. Verify runs every
check a machine can and records these four as NOT RUN, per the
fail-closed roll-up. Review and Ship carry them forward as the
quality bar still open. They are not marked as passed.

## Release authorization

- Mechanism: push `feat/assembly-line`, open a pull request to `main`
  whose body follows the protocol's "Pull request body" section
  (WO ids, `## Merge danger`), and squash-merge it.
- **Authorized: merge the feature PR** once its CI is green, then write
  `release.md` with `outcome: released` and `released-at:`.
- Never merge past unfixed critical review findings: stop and surface.
- Versioning: ADR-0095 applies, so the feature branch never touches
  `.claude-plugin/plugin.json`'s version. A `chore(release)` version-bump
  PR is **not** authorized by this brief. Ship records it as the next
  step for the Owner.
- Open PR #1166 (routine-garden README bullet) is unrelated. The Owner
  chose to leave it unmerged.

## Operate

operate:
  minimum-signal: the Owner has used the assembly-line page in one real presentation

Operate does not run until that signal exists. `users-observed:` is
counted from the signal the stage finds, never from this brief.
