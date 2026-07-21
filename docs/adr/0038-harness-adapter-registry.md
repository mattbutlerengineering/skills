# ADR-0038: One registration per harness in the trigger-eval runner

- Status: accepted (2026-07-20)

## Decision

Everything harness-specific the trigger-eval runner needs is bundled as
one adapter per harness in `trigger_eval.HARNESSES`: an `invocation`
(which composes the isolated-project builder with the CLI flags and
returns `(project_dir, cmd)`) and the matching stream `detect`or.
`run_single_query` consults only this registry, and the transcript
recorders (`tests/fixtures/transcripts/record.py`,
`tests/fixtures/omp-transcripts/record.py`) obtain their invocation and
detector from the same registrations instead of hand-copying flags.
The registry's key set is pinned to `eval_schema.HARNESSES` — the
vocabulary owner (ADR-0022, ADR-0031) — by test, and the per-harness
e2e twins share one contract mixin (`tests/harness_contract.py`).

## Why

ADR-0027/ADR-0031 made the runner dual-harness, which scattered the
per-harness knowledge across two parallel dicts (`_DETECTORS`,
`_INVOCATIONS`) plus flag copies in each recorder that admitted in
their docstrings that "nothing pins the two." Adding a harness meant
finding every site; a drifted recorder would re-record fixtures under
flags the runner never uses, silently invalidating detection pinning.
One registration per harness makes the seam explicit: a new harness is
one `Harness(...)` entry (plus its `eval_schema.HARNESSES` token, or
the consistency test fails), and recorders cannot drift because they
have nothing of their own to drift.

The project-dir builders stay module functions rather than registry
fields: every caller that needs a project dir needs the flags too, so
`invocation` is the whole external interface and the builders are its
implementation.
