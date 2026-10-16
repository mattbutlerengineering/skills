# The plugin version moves only in a release PR or at a Conductor merge

- Status: accepted (Owner, 2026-10-15)
- Date: 2026-10-14

The Owner accepted this on 2026-10-15, in session, with ADR-0096.
Recorded by the `faster-sdlc` feature run (`docs/features/faster-sdlc/
breakdown.md`, Milestone 2; issue #906). It supersedes no ADR: the rule
it replaces lives only in CLAUDE.md and AGENTS.md, as the bullet "Bump
`.claude-plugin/plugin.json`'s version with any `skills/` change."

## Context

The stated rule made every branch that touched `skills/` bump the
version. Every such branch then edited the same line and the manifest
that pins it, so each merge of `origin/main` after the first conflicted
or left the branch's version below main's, and the branch bumped again.
On `feat/kb-weknora-lessons` (#722) one feature commit (e6f1aab,
2026-10-11) was followed by seven plumbing commits between 2026-10-11
and 2026-10-13: six merges of `origin/main`, four of them re-bumping the
version (0.11.2, 0.11.3, 0.12.1, 0.12.3), each because main's version
had moved under the branch.

Practice already differs from the rule. Every release since 0.9.0 has
landed as one `chore(release)` PR per wave of merged work (#698, #723,
#752, #766, #788, #802, #826, #843, #853, #892, #901), with the agent
PRs in each wave told not to bump. And a Conductor merge bumps at its
step 3: `conductor_merge.bump_version` sets the branch's version to
`origin/main`'s with the patch part raised, regenerates the manifest and
commits, in the factory source repo only (#678). The version-bump
bullet is the one place that still says otherwise.

## Decision

1. **Feature and fix branches never touch the version.** A PR that
   changes `skills/` or the payload leaves `.claude-plugin/plugin.json`
   as `origin/main` has it. A branch that bumped anyway is not red;
   nothing gates it (see the rejected alternative).
2. **A wave's release PR bumps it once.** After the wave's PRs land,
   one `chore(release)` PR raises the version and regenerates the
   manifest, as every release since 0.9.0 has. A payload-only wave
   (`factory/templates/**`, no `skills/` change) still gets its release
   PR: installed caches refresh only when the version moves, so a
   payload change without a bump never reaches a stamped repo.
3. **A Conductor merge bumps at step 3**, as `bump_version` already
   does: the merge turn, not the item's branch, moves the version, to
   `origin/main`'s patch plus one, at the moment it knows main's value.

## Rejected alternative

A gate that fails a branch for touching the version (or its inverse, a
PR-event detector in detector B's style that fails a `skills/` PR with
no bump, as `docs/research/rea-learnings.md` §5 proposed). A stale
installed cache from a late bump costs less than a false red on a
legitimate release PR, and the Conductor's own step-3 commit would need
an exemption from either shape. The rule is stated and followed, not
enforced; `lint.py` keeps checking only that the field exists.

## Consequences

- Between a merged `skills/` change and its wave's release PR, an
  installed plugin runs the previous version. The Owner cuts the
  release PR at the end of a wave; the merge-wait work in Milestone 3
  does not change that.
- A branch no longer needs a merge of `origin/main` just to move its
  version above main's, and parallel PRs that touch `skills/` no
  longer conflict on the version line or the manifest.
- CLAUDE.md and AGENTS.md's bullet states this rule and cites this
  ADR (issue #907).

## If rejected

The bullet goes back to "bump with any `skills/` change", and every
branch that touches `skills/` bumps and re-bumps as before.
