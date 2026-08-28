---
run: maintenance:an-un-run-corner-nothing-pins
date: 2026-08-27
---

# Autorun brief

**Scale.** Maintenance run, `re-entry: implement` — two located defects
in one file family, both reproduced before any code was written.

**What and why.** The `record.py` scripts under `tests/fixtures/` are the
repo's un-run corner: they are executed only when a human re-records a
pinned transcript, never by CI. `tests/test_fixture_recorders.py` exists
to compensate — it imports each one so a seam move cannot strand it
silently. Two things undercut that. Its enumeration of recorders is
hand-typed, so a third recorder is stranded by construction; and the
recorders themselves will write a transcript from a stream that never
arrived, stamping a crashed CLI as a recorded no-fire.

**Scope, in.** `tests/test_fixture_recorders.py`'s enumeration, and a
refusal in both recorders for the one stream that is never evidence.

**Scope, out.** The wholesale duplication between the two recorders —
they are near-identical files, and folding them into one module is a
deepening, not a fix. Distinguishing a *partial* crash from a genuine
early decision (the runner's own version of this question lives in
`trigger_eval.py`, which is contended by an open branch). The eval
result record's missing `harness` field.

**Success criteria.** A recorder whose imports have drifted fails the
suite regardless of when it was added; a CLI that produces nothing
writes no transcript and no provenance entry, and says why; the battery
stays green and no payload byte moves.

**Constraints.** Stdlib only. The two recorders share no import, so a
guard in both is two copies — acceptable only if the suite asserts they
are identical.

**Release authorization.** None given. Ship prepares and stops.

**Tracker.** No issue interaction — read-only `gh` only.
