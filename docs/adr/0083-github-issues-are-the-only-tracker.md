# GitHub issues are the only tracker; beads is retired

- Status: accepted
- Date: 2026-10-10

Supersedes in part ADR-0032 (its "beads (when adopted) carries the
dependency graph" clause, already amended by ADR-0035), ADR-0035 (its
carve-out letting beads stay for session task-tracking) and ADR-0044
(the routine reading the queue from the beads JSONL export).

## Context

Two trackers held this repo's work. GitHub issues carried the dispatch
plane (ADR-0032, ADR-0035), the sweeps' intake, the gate-queue digest,
the improvement journal and every audit finding. Beads (`bd`, a Dolt
database under `.beads/` synced through `refs/dolt/data`) carried a
handful of issues and 82 `bd remember` notes of agent operating
knowledge, and every Claude Code and Codex session loaded it through a
`bd prime` hook. ADR-0035 kept beads out of the work-order mirror but
let it stay for session task-tracking, and ADR-0044 had the daily
routine read its committed export as the queue. Nothing reconciled the
two: an agent reading `gh issue list` never saw beads, and the routine
reading `.beads/issues.jsonl` never saw the GitHub queue. By 2026-10-10
every open bead was already settled on GitHub, so beads held no live
work — only the notes. Issue #645 asked for beads to go; the owner
chose "archive + propose KB pages" for the notes.

## Decision

1. **GitHub issues are the only tracker.** Work orders stay one-way
   mirrors of `breakdown.md` rows with `wo:*` labels (ADR-0032,
   ADR-0035), dependencies stay `blocked by:` edges on the rows mirrored
   as issue relationships. Any other task is a plain issue with a
   `type:*` label and no `wo:*` label; the reconcile sweep
   (`plane_drift.reconcile_drift`) judges only issues that carry a
   `wo:*` label and the label sweep (detector L) only the taxonomy's
   own labels, so a plain issue trips neither. `docs/backlog.md` stays
   the advisory seed inbox (ADR-0029).
2. **The notes are archived, not migrated.** All 82 `bd remember`
   notes are copied verbatim into
   `docs/research/beads-memories-archive.md`, a frozen, unmaintained
   archive. The issue history stays in git history of
   `.beads/issues.jsonl`. Citations such as "(beads wo-cha)" in code
   comments and run artifacts are history and stay as written.
3. **Durable knowledge goes to `docs/kb/`** through the
   `knowledge-base` skill — verified against current code, one page per
   non-inferable fact — never into an issue or a memory store. A note
   reaches the knowledge base only by that skill's ingest, one page at a
   time, not by bulk promotion from the archive.
4. **Everything that read or wrote beads is removed:** `.beads/`,
   `.agents/skills/beads/`, the Codex hooks under `.codex/`, the managed
   beads blocks in `CLAUDE.md` and `AGENTS.md` (replaced by one "Issue
   tracking" section), the `.gitignore` entries, and the beads mechanics
   in the planner and SWE charters (claim is the issue's
   `wo:in-progress`, ADR-0045). The improvement routine reads the queue
   with `gh issue list` (`docs/factory/improvement-routine.md` §2 item 8
   and §4 rung 2).

## Consequences

- One queue. `gh issue list` is complete; the routine, the audit skill,
  the sweeps and a human all read the same list.
- No factory script ever read beads (ADR-0035), so no tool changes; the
  removal is configuration, instructions and charters.
- The `bd prime` SessionStart hook in `.claude/settings.json` goes too,
  removed by the owner: harness configuration is not an agent's to
  edit. So are the owner's machine-local leftovers — user-level `bd`
  permissions, the local Dolt database under `.beads/`, and the
  remote's `refs/dolt/data` ref.
- If a graph tracker later earns a load-bearing role — a script that
  actually reads it — a new ADR revisits this with that need in hand.
