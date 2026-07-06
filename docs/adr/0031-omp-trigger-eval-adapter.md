# The trigger eval drives omp too; results are harness-marked

- Status: accepted
- Date: 2026-07-05
- Amends: ADR-0027

ADR-0027 made oh-my-pi (omp) a supported second harness but deferred an
omp eval driver: `trigger_eval.py` stayed Claude-only, and triggering
under omp rested on a manual smoke test. This ADR resolves that deferred
note — the second adapter exists (issue #88).

## Decision

- **One runner, two harness adapters.** `trigger_eval.py --harness omp`
  runs the same `evals/routing.json` set through `omp -p --mode json`;
  the claude path is unchanged and remains the default. Everything after
  detection (scoring, summary, confusion matrix, recording) is shared —
  the harness differences are confined to an invocation builder and a
  detection state machine per harness.
- **omp runs are isolated by construction.** Descriptions install as
  project `.claude/skills/<slug>-skill-<run-id>/SKILL.md` entries in a
  throwaway project; `--skills '*-skill-<run-id>'` excludes every
  globally installed skill, and `--no-extensions --no-rules --no-session`
  keeps the local omp environment out of the run. (`--no-isolate-settings`
  stays claude-only; omp has no `--setting-sources` equivalent.)
- **Detection watches omp's skill-load signal.** In omp a skill loads
  through the built-in `read` tool with a `skill://<name>` URI, so the
  first completed tool call decides: `toolcall_end` with a matching
  `skill://` path (or a direct SKILL.md path) is a fire, any other tool
  is a no-fire, `agent_end` without a tool call is a no-fire. Recorded
  real omp transcripts (`tests/fixtures/omp-transcripts/`) pin the
  output shape, mirroring the claude fixtures.
- **Results are harness-marked, claude stays unmarked.** eval_schema's
  naming grammar gains a harness token: omp snapshots record as
  `evals/results/trigger-omp-<date>[-N].json`; claude snapshots keep
  `trigger-<date>[-N].json` (every pre-existing snapshot predates
  harness identity and is a claude run). The snapshot body carries a
  `harness` field. Same honesty rules: append-only, dated, never CI.
- **LEDGER maturity stays keyed to Claude evals.** omp snapshots are
  supplementary triggering evidence for the second harness, not a
  graduation path; ADR-0027's "Claude Code primary" stance is unchanged.

## Consequences

- omp triggering is now first-class, measurable evidence instead of a
  smoke test; omp under-triggering shows up as recorded signal.
- An omp CLI output-shape change breaks the transcript replay tests in
  CI instead of silently corrupting eval results.
- Cross-harness comparisons must mind the model field: snapshots pin
  harness, model, and CLI version, and only like-for-like runs compare.
