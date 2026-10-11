# Autorun brief: orchestrator

Not an artifact. Written 2026-10-10 by the orchestrator. The user's own
words in this run are `/loop complete the orchestrator work` and one
answer to "How far should the loop drive the orchestrator run on its
own?": **"Architect→Review, stop (Recommended)"**. The option they chose
read: autorun from Architect through Implement and Review, one PR per
stage; answer the PRD's open questions with the skills' recommended
defaults and log each as an assumption; prepare the release and stop;
verify on a real paid batch waits for the Owner's spend consent.

## What and why

Everything the early stages need is already in this run's merged
artifacts, and they are the source of truth: `idea.md` (problem, who,
why now, evidence, hunch, success sentence, risks) and `prd.md`
(PRD-0013, the Conductor — actors, eight user stories, success criteria,
out of scope, open questions). This brief adds nothing to them.

## Run scale and slug

Feature run. Slug `orchestrator`. Run directory
`docs/features/orchestrator/`. Idea and PRD are complete; `ux:
not-applicable` is recorded in the PRD. Autorun resumes at Architect.

## Scope boundaries

In and out of scope exactly as `prd.md` states. Repo hard conventions
apply (CLAUDE.md): stdlib-only Python, seam modules with thin callers,
problem-string contracts, plugin.json version bump on any `skills/`
change, manifest regen after any `factory/templates/**` or mirrored-file
edit, typed IDs in run-artifact frontmatter. The idea's own risk —
over-investing in tooling — means the Architect should prefer the thinnest
design that reuses `autorun`, `work-queue` and the factory assembler.

## Open questions in the PRD

Answer each with the stage skill's recommended default where one exists
and log it under `assumptions:`. Where none exists, stop and surface. Not
for the Architect: whether a merge queue can be switched on (the Owner
tries the setting); design for both cases, as the PRD already does.

## Issue tracker

No seeding from existing issues. Work-order mirroring follows the repo's
normal one-way rule (ADR-0032): no `WO-####` issue before its
`breakdown.md` row exists, and this run creates none unattended.

## User-facing surface

None (`ux: not-applicable`, recorded in the PRD).

## Spend

No paid model runs (`claude -p`, `trigger_eval.py`, `charter_replay.py`,
`claude plugin eval`) without the Owner's consent. The PRD's success
criteria need a real batch of four or more issues; that batch is
deferred, not faked. Verify records what can be shown offline and marks
the real-batch criteria unmet and pending Owner consent.

## Release authorization

Prepare and stop. No merge, tag, publish or deploy. Each stage opens a
pull request stacked on the previous stage's branch; the Owner merges.
