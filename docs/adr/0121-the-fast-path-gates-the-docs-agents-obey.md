# The fast path gates the docs agents obey

- Status: amended by ADR-0122 (the run directories' survey: the autorun brief is a gate path; provisional)
- Date: 2026-11-02

Recorded by the `faster-sdlc` feature run
(`docs/features/faster-sdlc/breakdown.md`), unattended, so it is
provisional. Amends [ADR-0096](0096-this-repo-opts-in-to-implement-queue-auto-merge-with-a-docs-fast-path.md):
its decision 2 (the gate paths) and decision 3 (the fast-path rule,
"every changed path is under `docs/` and none is a gate path"). The
Owner chose to fix the finding now, on 2026-11-02, in an autorun resume
session ("Fix now").

## Context

The review of the run (`docs/features/faster-sdlc/review.md`, the Major
finding) found that ADR-0096's rule reads `docs/` as inert prose.
`docs/` also holds files that agents are told to obey, so a docs-only
PR that rewrote one would classify `fast-path: low-risk` and, with a
green `check`, auto-merge with no review and no human:

- `docs/pipeline-protocol.md` — every stage skill's first step is to
  read it (18 references under `skills/`), and it owns run discovery,
  gating and the ADR rule.
- `docs/standards.json` — the Architect and Review skills load it as
  the standards a design or diff is judged against
  (`skills/architect/SKILL.md`, `skills/review/SKILL.md`, "Load
  applicable standards").
- `docs/factory/*-routine.md` and `routine-markers.md` — the protocols
  the scheduled routines execute, including
  `docs/factory/merge-train-routine.md`, which the merge train itself
  runs every 4 hours. `docs/factory/costs.jsonl` sits in the same
  directory: the cost-report workflow reads it to decide PAUSE.

The same review noted that the classifier's gate list (`fast_path.py`)
and the queue profile's `gate_paths` are two copies of one policy with
nothing pinning them equal.

## Decision

1. **Three more gate paths**: `docs/pipeline-protocol.md`,
   `docs/standards.json` and `docs/factory/**`. They join ADR-0096's
   seven, so a diff touching any of them classifies
   `fast-path: review (<path>)`, exit 1, and keeps a human merge.
2. **The profile and the classifier carry the same list.**
   `.claude/implement-queue.md`'s `gate_paths` and `fast_path.py`'s
   gate constants are updated together, and `tests/test_fast_path.py`
   reads the profile's `gate_paths` and asserts it equals the
   classifier's `gate_globs()`. A path added to one and not the other
   fails the test.
3. **Nothing else in ADR-0096 changes**: the `docs/` low-risk prefix,
   the exit codes and strings, the one-at-a-time merge train and
   ADR-0087's four conditions stand.

## Rejected alternatives

- **Defer and accept the risk.** The Owner decided to fix it now; the
  merge train's own protocol being rewritable by an unreviewed PR is
  the case a gate path exists for.
- **Gate all of `docs/` except an allow-list of prose paths.** It is
  the safer default, but it empties the fast path of most of its
  traffic (kb pages, fixes, features and research artifacts), which is
  the merge wait ADR-0096 exists to cut.
- **Also gate `docs/kb/**`, `docs/backlog.md`, `docs/output-evals.md`,
  `docs/launch-demo.json`, `docs/setup.md`.** Surveyed and left out:
  the KB pages are knowledge `AGENTS.md` indexes for agents to consult,
  not procedures they execute; the backlog is the advisory seed inbox
  (ADR-0029); `output-evals.md` is the on-demand procedure for graded
  eval runs, which a human starts and whose results are committed
  records; `launch-demo.json` is configuration read by
  `launch_demo.py`; `setup.md` is human-facing install prose. The
  Owner may add any of them to `gate_paths` later.

## Consequences

- A PR that only edits a routine protocol, the protocol or the
  standards index now waits for an independent review and a human
  merge, as ADR-0087 frames gate paths. The routine and protocol edits
  of this repo are rare, so the cost to the fast path is small.
- A PR that only appends to `docs/factory/costs.jsonl` is also
  review-routed. The assembler and gate-digest workflows push their
  rows to `main` directly, not by PR, so no automated flow loses the
  fast path.
- ADR-0096's status line records the amendment; its Decision stays as
  written.

## If rejected

The classifier and the profile return to ADR-0096's lists, and a
docs-only PR may rewrite the protocol and the routine protocols
unreviewed under `merge: auto`, which is the risk the review named.
