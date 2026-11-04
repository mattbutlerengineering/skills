# The fast path gates the autorun brief

- Status: provisional
- Date: 2026-11-03

Recorded by the `a-brief-the-fast-path-waves-through` maintenance run
(`docs/fixes/a-brief-the-fast-path-waves-through/defect.md`, issue
#1146), unattended, so it is provisional. Amends
[ADR-0121](0121-the-fast-path-gates-the-docs-agents-obey.md): its
instruction-doc survey, which left `docs/features/**` and
`docs/fixes/**` out wholesale. The Owner fixed the shape in the issue
(every `autorun-brief.md` at any depth is a gate path; other run
artifacts stay out).

## Context

ADR-0121's survey read the run directories as "outputs of stages, not
instructions". That holds for every file there except one: an autorun
resume follows `autorun-brief.md` as its interview answers
(`skills/autorun/SKILL.md`). The brief carries the run's release
authorization, its `operate:` section and its `stop-after:` line. A
docs-only PR that edited a brief classified `fast-path: low-risk` and,
under `merge: auto`, merged on a green `check` alone, so it could move
a run from "prepare and stop" to an authorized release with no review.
The faster-sdlc run's review named this as finding #6 and deferred it.

## Decision

1. **`autorun-brief.md` at any depth is a gate path.** A diff touching
   one classifies `fast-path: review (<path>)`, exit 1. `fast_path.py`
   matches it by basename in `GATE_NAMES`, beside `prd.md` and
   `architecture.md`, and `gate_globs()` renders `**/autorun-brief.md`.
2. **The profile carries it too.** `.claude/implement-queue.md`'s
   `gate_paths` gains `"**/autorun-brief.md"`; the pin test in
   `tests/test_fast_path.py` keeps the two lists equal.
3. **Nothing else changes.** Other run artifacts (`defect.md`,
   `breakdown.md`, `release.md`, `retro.md`) are state the stages
   re-derive and stay low-risk; ADR-0121's other survey results stand.

## Rejected alternatives

- **Gate all of `docs/features/**` and `docs/fixes/**`.** It empties
  the fast path of its commonest traffic; the Owner narrowed the fix to
  the one file a resume obeys.
- **A `GATE_PREFIXES` entry.** Briefs live under per-slug directories,
  so only a basename match reaches them at any depth.

## Consequences

- A PR that only edits a brief, such as a resume's brief commit, needs
  an independent review and a human merge.
- ADR-0121's status line records the amendment; its Decision stays as
  written.
- The `implement-queue` skill's GitHub-side `gate_paths` matcher is
  out of reach of this change.

## If rejected

The classifier and the profile return to ADR-0121's lists, and a
docs-only PR may edit a brief, and so a run's release authorization,
unreviewed under `merge: auto`.
