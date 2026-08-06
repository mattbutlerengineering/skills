# Charter replay joins the harness seam

- Status: accepted
- Date: 2026-08-05

Amends ADR-0038 (the harness adapter registry) and extends the cli
seam's harness-IO conventions (ADR-0037, ADR-0040, ADR-0042).

## Context

ADR-0038 made `trigger_eval.HARNESSES` the one home for harness-specific
knowledge, but `charter_replay.py` had grown into an unregistered fourth
`claude` adapter:

- Its hand-built flag list had drifted: no `--include-partial-messages`,
  so no `stream_event` frames — the replay's transcript depended
  exclusively on the legacy full assistant message shape. A CLI that
  stops emitting that shape would replay every `forbid` expectation
  against a silently empty transcript and pass the suite while testing
  nothing: fail-open, against the repo's non-negotiable eval honesty.
- The JSON-lines decode existed in four copies (charter_replay,
  trigger_eval's stream reader, both fixture recorders). An earlier
  review ruled two copies with disjoint control flow below the seam
  bar; four copies behind a registry that exists to own harness
  knowledge is past it.
- The binary name lived in three homes (charter_replay's version probe,
  trigger_eval's key==binary assumption, harness_contract's `BINARY`).
- Plan 001's process-tree reaping (own process group, unconditional
  group kill, drain-after-exit, pipe close) was scoped to trigger_eval
  only; charter_replay's bare `subprocess.run` still orphaned the CLI's
  grandchildren on timeout — replays keep burning API budget after the
  suite moves on. The spawn-kwargs quartet had no seam at all: four
  hand-written copies, and tests could only reach them by
  monkeypatching stdlib.

## Decision

- The `Harness` registration widens to
  `(binary, command, invocation, detect, decode)`: the executable name,
  the flag grammar (`command(prompt, model, isolate, run_id=None)` —
  claude ignores `run_id`, omp ignores `isolate`), the project+command
  composition ADR-0038 defined, the stream detector, and the line
  decode (`cli.decode_events`, shared by both harnesses). `invocation`
  is now a thin composition of the project builder with `command`.
- The streaming spawn joins the cli seam as `cli.harness_run(cmd, cwd,
  timeout, env=None, spawn=None)` — a context manager owning
  `start_new_session`, the drain-after-exit reader (`cli.EventStream`,
  whose `timed_out` flag tells a completed run from a truncated one),
  the unconditional `os.killpg` on exit with the empty-group tolerance
  the reaping fixes pinned, and the pipe close. `spawn` is the
  injectable substitute, so caller tests stop monkeypatching stdlib.
  It is POSIX-only, the stance trigger_eval has always documented.
- charter_replay becomes a registered consumer: command from
  `HARNESSES["claude"].command` (partial frames included), child under
  `cli.harness_run`, and a transcript builder that reads BOTH output
  shapes — frames win when present, never summed — so the legacy-shape
  fail-open is dead. trigger_eval.run_single_query, the recorders, and
  harness_contract read the same registrations; nothing keeps a private
  copy of flags, decode, or binary name.
- The registry stays in trigger_eval: its entries close over the
  eval-plane detectors and project builders, and cli (mirrored into the
  factory payload) must not import eval tooling. cli owns the
  harness-agnostic process lifecycle; the registry owns what differs
  per harness.

## Consequences

- A drifted harness flag, decode, or binary now has nowhere to live but
  the registry, and `--include-partial-messages` is pinned by test at
  charter_replay's own runner.
- A timed-out replay kills the whole process group; the
  leader-dead/timeout grandchild tests run against real subprocesses
  in both suites (tests/test_process_reaping.py, the charter twin in
  tests/test_charter_replay.py) plus the seam's own contract suite
  (tests/test_cli.py TestHarnessRun).
- cli.py's mirror in the factory payload carries the streaming seam;
  the manifest was refreshed in the same commit (detector E).
- The fixture recorders still hold their own Popen/tee (the raw-line
  tee is their whole job) with a leader-only kill; folding them onto
  harness_run — and merging the two into one parameterized recorder —
  is a noted follow-up, not blocked by this decision.
