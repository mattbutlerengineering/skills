# Autorun brief — maintenance:pid-alive-answers-the-wrong-question

**Provenance.** No user-supplied brief exists for this run. It was driven
by a standing autorun instruction, and every answer below comes from this
session's own investigation of the improvement-routine journal (#181) and
from experiments run against this repo — not from a live interview. Where
that leaves a real gap it is named as a gap, never filled with a guess.

## What and why

`pid_alive` — defined identically in `tests/test_cli_process_reaping.py`
and `tests/test_charter_replay.py` — answers "does this PID exist", not
"is my grandchild still running". It is `os.kill(pid, 0)`, which succeeds
for a **zombie**: a process that has terminated but has not yet been
collected. Both files then poll that predicate in a 2-second grace loop
and assert "grandchild survived" when it stays true. So a definitively
dead process can fail the assertion.

## Scale

Maintenance run, slug `pid-alive-answers-the-wrong-question`,
`re-entry: implement` — a scoped predicate fix with no design decision to
make. The breakdown lives inline in `defect.md`.

## Evidence (measured this session, not asserted)

- A child in `ps` state `Z` is reported alive: `pid_alive() says: True`.
  After `wait()` collects it, the same call returns `False`.
- The two definitions are verbatim copies of each other, which is why the
  journal recorded the same failure under different test names.

## Scope

**In:** correct the predicate in both files so a terminated process reads
as dead, plus regression coverage that pins it.

**Out, deliberately:**
- The PID-reuse hypothesis. It is unconfirmed, and this run does not
  pretend to close it.
- Claiming this fixes the observed flakes. It does not — see `Ruled out`
  in `defect.md`. This run fixes a latent defect that the flake hunt
  surfaced; the flake's own cause stays open.
- De-duplicating the two copies. A real smell, logged, not fixed here.

## Success criteria

A process in state `Z` is reported dead by both predicates; a regression
test fails before the fix and passes after; the full battery stays green.

## Constraints

Stdlib only. Must work on macOS and Linux. Tests only — no source module,
no `factory_init.MIRRORS` file, so no manifest regeneration.

## Tracker

Silent — no tracker interaction of any kind.

## User-facing surface

None. Test-internal helper.

## Release authorization

**Not granted.** Ship prepares and stops: pre-flight and `release.md`
only, no merge, tag, publish or deploy.
