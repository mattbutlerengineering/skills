# Autorun brief — run discovery ignores open PRs

Collected once, at the top of the run, from the standing session context.
Every stage answers its interview questions from here; where this is
silent and the stage skill offers a recommended default, the stage takes
it and logs it under `assumptions:`. Where it is silent and no default
exists, the stage stops and surfaces.

## What and why

The pipeline's run discovery enumerates run *directories* in the current
checkout. Work that another agent has already done lives on a branch,
behind an open pull request, and is invisible to that enumeration. On
2026-08-18 a maintenance run captured a defect that had been fixed and
open in PR #298 since 2026-08-17; it rebuilt the fix, merged it as #303,
and #298 was closed unmerged nine hours later. Four files, identical set.

That was one duplicate at two open PRs. There are twelve open now, all
agent-authored and all blocked on human review, so the window in which a
fix sits invisible is measured in days and the number of hiding places has
multiplied by six.

## Scale and slug

Maintenance run. Slug `run-discovery-ignores-open-prs`. Artifacts at
`docs/fixes/run-discovery-ignores-open-prs/`. Entry is Capture with
`defect.md`.

## Origin

Backlog seed, line 29 of `docs/backlog.md`, from
`maintenance:toolsmith-mine-pr-permissions` — the run that did the
rebuilding, seeding the lesson against itself. Claimed in place per the
protocol's seed-backlog section.

## Scope

**In:**

- The moment a run *starts* — Capture from an intake or a seed, Idea from
  a seed — and whether the pipeline asks "is this already in flight?"
  there.
- Whatever the answer costs to check: the protocol's own text, the skills
  that start runs, and a mechanical check if one is cheap and honest.

**Out:**

- The 12 open PRs themselves. This run does not merge, close, retarget or
  review any of them.
- Orientation *within* an active run. The protocol is explicit that
  orientation comes from run artifacts alone; nothing here weakens that.
- The daily improvement routine's protocol
  (`docs/factory/improvement-routine.md`), which CLAUDE.md says is tuned
  by PR and never edited by the routine. If the fix implies a change
  there, this run proposes it and does not assume it.
- Any new gate that can turn CI red. A check that fails a build is a
  policy decision, not a defect fix.

## Success criteria

1. A named, reproducible statement of what the pipeline does today when a
   fix is already open in a PR — evidenced from #298/#303, not asserted.
2. The starting stages ask the question, in a way an agent with only
   `gh` and this repo can actually answer.
3. Whatever lands is verified by the repo's real battery, and any prose
   rule is checked by whatever mechanical check the repo already has for
   prose rules (`lint.py`), not by assertion.
4. No existing orientation behaviour changes.

## Constraints and things already decided

- Stdlib only; every script standalone Python 3.
- The seam bar: a new shared module needs multiple real callers AND
  observed divergence. Anticipated reuse does not qualify.
- Mirrored files move with `python3 factory_init.py update-manifest` in
  the same commit; `factory_init.MIRRORS` is the authority on what is
  mirrored.
- Backlog lines are appended, never rewritten; the `(claimed: ...)`
  suffix is the one sanctioned in-place edit, and no commas in a run-ref.
- Never rewrite an ADR to match a new one — supersede or amend, moving
  the status line and the index row together.
- Work in a dedicated worktree. The primary checkout is being driven by
  another session on a different branch.
- **Conflict discipline, which is this run's own subject:** the twelve
  open PRs claim `gates.py`, `one_owner.py`, `lint.py`, `human_gates.py`,
  `knowledge_plane.py`, `validator.py`, `plane_drift.py`, `sweeps.py`,
  `budget_guard.py`, `rejection_mining.py` and their tests. Measured, not
  remembered — `gh pr view <n> --json files`. Prefer a design that does
  not touch them. `lint.py` is claimed by #324, so a new `lint.py` check
  is a conflict this run should weigh rather than reach for.

## Tracker

An intake issue may be filed for this defect so the PR has something to
close, exactly as previous maintenance runs did. Nothing else: no
breakdown mirror, no `WO-####` dispatch, and never before the row exists
(ADR-0032 is one-way).

## User-facing surface

None. This is pipeline protocol and skill text plus, possibly, a
developer-facing check. `ux: not-applicable`.

## Release authorization

**None.** Prepare-and-stop: pre-flight, open the PR, write `release.md`,
stop. No merge, no tag, no publish. ADR-0036 clause 2 independently
forbids the author merging.

## Standing prohibitions

- No stage may merge, close, reopen or retarget any pull request,
  including the twelve open ones and any this run opens.
- No stage may run a factory tool in a mode that creates, edits or pins a
  live issue — `rejection_mining.py mine`, `sweeps.py` filing, digest
  posting. Read-only `gh` reads and offline fixtures only.
- Issues #178, #181 and #294 are permanent marker-bearing state. Never
  close them; never a `Closes` target.
- Never fabricate run, eval or ledger evidence. `evals/results/` is
  append-only and the cost ledger takes rows only through
  `budget_guard.py record`.
