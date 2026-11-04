# Autorun brief: a-brief-the-fast-path-waves-through

Not an artifact. Written 2026-11-03 by the orchestrator. The Owner finished
the faster-sdlc run, then picked "Fix: autorun-brief gate path", the
retro's top seed. In the same session the Owner answered four questions:

1. Scope: "autorun-brief.md only".
2. Tracker: open one issue (filed as #1146, `type:defect`; the taxonomy
   has no `type:bug`).
3. Release: "Prepare and stop".
4. Operate: "minimum-signal: merged".

Everything else below is the orchestrator's reading of the seed, the
faster-sdlc review and the code, and is marked as such. A stage that
needs an answer this brief does not hold applies the autorun rule: take
the skill-supplied default and log it, or stop and surface.

## Run scale

Maintenance (fix) run at `docs/fixes/a-brief-the-fast-path-waves-through/`,
entering at Capture. It is a defect: the fast-path classifier (ADR-0096,
as amended by ADR-0121) lets an edit to the file autorun obeys merge
unreviewed.

## Capture inputs

- **What is broken.** `fast_path.py` classifies a diff that touches only
  `docs/features/<slug>/autorun-brief.md` (or `docs/fixes/<slug>/autorun-brief.md`)
  as `fast-path: low-risk`, exit 0. Under `.claude/implement-queue.md`'s
  `merge: auto`, a PR like that merges on a green `check`. An autorun
  resume follows the brief as its interview answers
  (`skills/autorun/SKILL.md` steps 1 and 5). The brief holds the release
  authorization, the `operate:` section and `stop-after:`, so a docs-only
  PR could turn a prepare-and-stop run into an authorized release.
- **Reproduction.** Capture must reproduce this for real. In a temp git
  repo, edit `docs/features/x/autorun-brief.md`, run the worktree's
  `python3 fast_path.py <base> <head>`, and quote the `low-risk` exit 0.
  Then confirm that the profile's `gate_paths` has no entry matching it.
- **Evidence it bites today.** Orchestrator's reading: none observed.
  Capture should check merged PRs since the merge train's first run
  (2026-10-16 00:38 UTC) for any whose only changed files include an
  `autorun-brief.md` and that merged through the train. Cite the journal
  (#930) or the PRs if any exist, or say plainly that none do.
- **Root cause (hypothesis).** ADR-0121's instruction-doc survey excluded
  `docs/features/**` as "outputs of stages, not instructions". The brief
  is the exception. Finding #6 in `docs/features/faster-sdlc/review.md`
  names it.
- **Blast radius.** `fast_path.py` (root-only, not in
  `factory_init.MIRRORS`; Capture re-checks this), its tests, and
  `.claude/implement-queue.md`'s `gate_paths`. The pin test
  (`TestProfilePin`) keeps the classifier and the profile in step. The
  cost: a PR that edits only a brief, like a resume's brief commit, loses
  the fast path and needs a human merge.
- **Re-entry depth.** Orchestrator's reading: `re-entry: implement`. The
  shape is decided (Owner decision 1), and the change sits inside the
  existing gate list. If Capture finds a real design question, it chooses
  `re-entry: architect` and logs why.

## Fix shape (Owner decision 1)

Every `autorun-brief.md` at any depth is a gate path. In the classifier
that is a basename match, a new kind next to `GATE_PREFIXES`/`GATE_FILES`.
In the profile it is `"**/autorun-brief.md"`, rendered by `gate_globs()` so
the pin test holds. Implement picks the exact matcher and logs the
choice. Out: every other run artifact (`defect.md`, `breakdown.md`,
`release.md`, `retro.md`, and the rest).

## Scope

In:
- the gate entry in `fast_path.py` and `.claude/implement-queue.md`,
  with docstring and USAGE updates if they enumerate paths;
- failing-first tests through the public interface with exact output
  lines: a brief under `docs/features/` and one under `docs/fixes/`
  routed to `review (<path>)` exit 1; a neighbour such as
  `docs/features/x/breakdown.md` still `low-risk`; a rename of a brief
  into or out of the run directory routed to review; the pin test
  passing with the new glob;
- a provisional ADR amending ADR-0121's survey (the brief is an
  instruction source), with its row in `docs/adr/README.md` and ADR-0121's
  status line recording the amendment, the way ADR-0096 recorded
  ADR-0121's;
- marking backlog line 143 claimed:
  `(claimed: maintenance:a-brief-the-fast-path-waves-through)`.

Out: the other faster-sdlc seeds (backlog lines 144 onward); the
implement-queue skill's own GitHub-side `gate_paths` matcher (line 144's
seed); rewriting shipped artifacts.

## Success criteria

- A diff touching only an `autorun-brief.md` prints
  `fast-path: review (<path>)` with exit 1 where it printed `low-risk`
  exit 0 before.
- Other run-artifact files under `docs/features/` and `docs/fixes/` stay
  `low-risk`.
- The profile's `gate_paths` equals `fast_path.gate_globs()` (the pin
  test passes).
- `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`,
  `python3 gates.py && python3 gates.py --selftest` all pass.

## Constraints

Stdlib only. Problem-string contracts; tests assert exact strings. Never
touch `.claude-plugin/plugin.json` (ADR-0095). If a mirrored file changes,
run `python3 factory_init.py update-manifest`, deleting stray
`.orig`/`.rej` first. Gates scan every markdown file, so write no literal
four-digit work-order or PRD-style id that does not exist.

## Tracker

Issue #1146 (`type:defect`) seeds the run as intake (ADR-0030): Capture
records `intake: #1146` in `defect.md`. The PR closes it with
`Closes #1146` and carries a `No work order:` line. Run `gh pr create` as
the first command of its own shell call, with the body file written in an
earlier call, so the preflight hook judges it.

## User-facing surface

None.

## Release authorization

Prepare and stop (Owner decision 3). Ship pushes, opens the PR, records
`outcome: prepared` with `pending-merge:`, and stops. No merge, tag or
version bump. The PR touches `fast_path.py` and `docs/adr/**`, so the
merge train holds it for a human merge.

## Operate

operate:
  minimum-signal: Ship written back as released (the PR merged).

`users-observed:` is counted from the signal Operate finds; this brief
never supplies it.
