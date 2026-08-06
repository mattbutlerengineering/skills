# The report epilogue joins the cli seam

- Status: accepted
- Date: 2026-08-05

Amends ADR-0042. Its consequences read the ADR-0037 carve-out list as:
"gates.pr_event (as PR interpreter), the problem-string convention, and
the checkbox-regex owners still stand." The convention itself still
stands — checkers return label-prefixed problem strings; callers print
and exit nonzero — but its CALLER half now has one implementation
instead of ten. The 2026-08-05 architecture review surfaced the move.

(Numbering: 0045–0050 are being written on other branches; this ADR was
pre-assigned 0051 and its index row sits directly after 0044 until the
integrator inserts the intervening rows.)

## Context

CLAUDE.md states the checker half of the problem-string contract. The
caller half — print each problem, print `"<label>: N problem(s)"`, exit
1/0 — was retyped in ten epilogues: assembler, cost_report, gate_digest,
validator, label_sync, sweeps (twice — it has two entry paths), gates,
factory_init, budget_guard, and lint. Four forks had already appeared:

- budget_guard's error path hardcoded `"1 problem(s)"` — a literal, not
  a computed count.
- lint decorated its summary with a coda (`across N skills`) and its
  problems with a print-time `LINT: ` prefix.
- sweeps' filing paths decorated theirs with a clause BEFORE the count
  (`N issue(s) filed, `).
- The CliContract suite pinned the summary grammar for only a minority
  of the tools; `gates: 0 problem(s)` — the most load-bearing string in
  the repo, grepped by CI — was owned by no module and pinned by no
  direct test of gates.main.

## Decision

`cli.report(label, problems, prefix="", suffix="")` owns the caller
half: print each problem, print
`"<label>: <prefix>N problem(s)<suffix>"` with the count always computed
from the list, and return the exit code (1 with problems, else 0). It
never calls sys.exit — every main already returns its code to a
`sys.exit(main(...))` block, and report keeps that structure. All ten
epilogues are thin callers; every summary label and every problem line
is byte-identical to before.

The two decorations are not speculative parameters: each is a shipped,
test-pinned summary shape, one on each side of the count clause. prefix
carries sweeps' `N issue(s) filed, ` clause; suffix carries lint's
` across N skills` coda. A suffix alone was considered and rejected —
it cannot express sweeps' clause, which would have left one of the ten
epilogues as exactly the hand-rolled fork the seam retires.

budget_guard's hardcoded count is gone: its error path passes the
one-problem list and the seam computes the 1.

Two line-order deltas, recorded for honesty (every line's bytes are
unchanged; consumers grep lines, and no test pinned these orders):

- budget_guard now prints its verdict (CONTINUE/HARD-STOP) before the
  problem block instead of between the problems and the summary.
- sweeps' filing paths print their `sweeps: filed intake issue for
  <key>` lines before the problem block instead of after it.

What deliberately did NOT move:

- gates' selftest epilogue (`selftest: ok|FAIL`) — a failures list with
  its own grammar, not a problem-string summary.
- The usage epilogues (print `__doc__`, return 2) — per-tool by design,
  already pinned by CliContract.
- validator's write_outputs emission inside run_claim (siblings emit in
  main) — an outputs-placement asymmetry, not an epilogue; out of this
  fold's scope and left visible.

## Consequences

- The ADR-0037 carve-out list is read through ADR-0039, ADR-0040,
  ADR-0042, and this amendment: the problem-string convention still
  stands, but its caller half lives in cli; gates.pr_event (as PR
  interpreter) and the checkbox-regex owners still stand.
- The summary grammar cannot fork per tool again, and an eleventh tool
  starts as a thin caller.
- Pins: tests/test_cli.py TestReport asserts the seam itself (computed
  count, both decorations); tests/cli_contract.py ReportContract pins
  the exact summary line of ALL ten epilogues at their suites —
  gates.main, factory_init.main, and lint.main gain their first direct
  main() coverage, including the CI-grepped `gates: 0 problem(s)`.
- cli.py and the seven mirrored tools were re-mirrored via
  `factory_init.py update-manifest` in the same commit (detector E).
