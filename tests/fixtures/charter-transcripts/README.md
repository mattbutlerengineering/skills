# Synthetic charter-replay transcripts

**These are hand-authored, not model output.** Unlike
`tests/fixtures/transcripts/` — real recorded `claude -p` runs pinned with
a provenance file — nothing here is evidence of how any model behaved.
They exist to drive the charter regression suite's *scoring* seam offline
(`charter_replay.score_case` / `run_suite`), because the replay itself is
a real model run: on demand only, costs money, never CI (CLAUDE.md).

`synthetic.json` holds, per golden fixture case in
`factory/evals/charters.json`:

- `compliant` — a transcript shaped like a run of a charter that held: it
  trips no forbidden pattern and satisfies every required one.
- `degraded` — a transcript shaped like a run of a **deliberately degraded
  charter** (the "Must never" clause deleted): it pushes to main, merges
  its own PR, skips the failing test, or files a tracker issue with no
  breakdown row.
- `degraded_failures` — the exact expectation ids the degraded transcript
  must trip. `tests/test_charter_replay.py` asserts set equality, so the
  suite cannot pass a degraded run, and cannot fail it for the wrong reason.

## What this does and does not prove

Proves (offline, in CI): the suite's scoring logic detects charter
degradation in a replay transcript, and a clean transcript passes.

Does **not** prove: that a degraded charter actually causes a model to
produce a degraded transcript. That link is only observable in a live
replay (`python3 charter_replay.py`), which spends real money and is never
run by CI. Do not read these fixtures as evidence about model behavior, and
never hand-edit a real recorded transcript to look like one of these.
