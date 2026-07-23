# write_outputs joins the cli seam

- Status: accepted
- Date: 2026-07-21

Amends ADR-0039. Its closing reconciliation read: "The rest of ADR-0037
(seam-module bar, problem-string convention, the `write_outputs` wart,
checkbox-regex owners) stands unchanged." One item of that list has now
changed: the `write_outputs` wart is retired, and this ADR records how.

## Context

ADR-0037 deliberately left `write_outputs` — the `$GITHUB_OUTPUT`
heredoc adapter — in `assembler.py`, calling cost_report's import of it
"a known remaining wart, one caller short of the bar." That rationale
stopped describing the tree the day cost_report.py shipped: two real
tools emitted step outputs through it, and the tool-to-tool import
(`from assembler import write_outputs`) WAS the wart — a thin caller
depending on a thin caller, with an assembler-branded `__ASM_*_EOF__`
delimiter stamped into cost-report output.

## Decision

`cli` owns `write_outputs`, beside `child_env` and `version` — the
harness-IO conventions: what a tool must know to talk to the runner
environment around it. The delimiter is neutral (`__<KEY>_EOF__`).
`assembler.py` and `cost_report.py` are thin callers, importing it the
same direction every other seam is consumed. The pins live at the seam's
own suite (`tests/test_cli.py`), including a no-tool-branding delimiter
test.

Same authorization pattern as ADR-0039: no divergence between copies
fired the move — there was only ever one copy — but the carve-out's
stated rationale ("one caller short") no longer described the tree, so
the fold lands on completed locality.

## Consequences

- ADR-0037's "what deliberately did NOT move" list is read through
  ADR-0039 and this amendment: ROW/TRACKER and `write_outputs` have
  since moved; `gates.pr_event`, problem-string convention, and the
  checkbox-regex owners still stand.
- The step-output convention can no longer drift between the two tools
  that emit it, and a third emitter starts as a thin caller.
- The delimiter carries no tool's name; workflows are unaffected (they
  read step outputs by key, never by delimiter).
