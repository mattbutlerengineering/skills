# gh_runner and the event read join the cli seam

- Status: accepted
- Date: 2026-07-28

Amends ADR-0040. Its consequences read the ADR-0037 carve-out list as:
"gates.pr_event, problem-string convention, and the checkbox-regex
owners still stand." Two moves land here; the 2026-07-28 architecture
review surfaced both.

## Context

- **gh_runner.** label_sync.py owned the gh stdout port, and validator.py,
  gate_digest.py, and sweeps.py imported it tool-to-tool — the same
  thin-caller-depending-on-thin-caller shape ADR-0040 retired for
  `write_outputs`, now with four real callers.
- **The $GITHUB_EVENT_PATH read.** ADR-0037 kept `pr_event` in gates.py as
  "a dispatch-plane event reader with a documented second caller." Since
  then `assembler.issue_event` shipped a second, independent copy of the
  env-read/parse/error triple with a different error contract (missing
  path: silent skip vs problem; non-object payload: silent skip vs
  problem) — the observed divergence that is the seam bar. The seam owned
  the write half of harness IO (`write_outputs`) but not the read half.

## Decision

- `cli.gh_runner` joins the seam beside `runner`: the stdout port over
  `runner("gh")`. label_sync, validator, gate_digest, and sweeps are thin
  callers; their problem strings are unchanged.
- `cli.read_event(env)` owns the $GITHUB_EVENT_PATH read: `(None, None)`
  when the environment carries no event path — absence is a fact each
  caller judges (detector B skips silently; the assembler calls it a
  problem) — and an unlabeled error string for an unreadable,
  unparsable, or non-object payload, which the caller labels.
- `gates.pr_event` REMAINS in gates.py as the dispatch-plane interpreter
  (extracting `pull_request` from the event), now a thin caller of
  `read_event` — the carve-out's sentence stays true; only the generic
  read moved. `assembler.issue_event` is the same shape.

One behavior delta, recorded for honesty: a non-object JSON payload in a
PR run was a silent detector-B skip and is now
`B: GITHUB_EVENT_PATH <path> is not a JSON object` — a broken event file
is not a non-PR run. Every other message body is byte-identical.

## Consequences

- The ADR-0037 carve-out list is read through ADR-0039, ADR-0040, and
  this amendment: ROW/TRACKER, `write_outputs`, `gh_runner`, and the
  event read have moved; `gates.pr_event` (as PR interpreter), the
  problem-string convention, and the checkbox-regex owners still stand.
- A fifth gh consumer starts as a thin caller of cli; the event-read
  error contract can no longer fork per tool.
- Pins live at the seam's own suite (tests/test_cli.py: TestGhRunner,
  TestReadEvent); caller suites keep their exact-string composition
  tests.
- Same-commit drift fix from the same review: detector G builds the
  ledger path from `cost_ledger.COST_LEDGER` instead of a hardcoded
  copy, so the path it opens and the path its problem strings name can
  no longer disagree.
