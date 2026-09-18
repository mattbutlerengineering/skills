---
stage: review
run: maintenance:a-gate-wait-is-not-spend
date: 2026-08-28
assumptions: []
---

# Review — a gate wait is not spend

Scope: the diff on `agent/a-gate-wait-is-not-spend` against
`origin/main` — `dashboard.py` (one call changed, docstring extended) and
`tests/test_dashboard.py` (+6 tests, two imports).

## Correctness

**1 (minor, accepted) — the dollar totals never moved.** Gate rows carry
`cost: 0.0`, so no sum in the console changes and no cap decision was
ever affected. The defect was which work orders appear with a number at
all, and the fix changes exactly that. `defect.md` says so rather than
overstating the blast radius.

**2 (minor, accepted) — a work order with a dispatched row and gate rows
still shows the same figure.** `test_a_gate_row_does_not_perturb_a_work_
order_that_ran` passed before the fix and after it. It is kept because it
pins the half that must not change, not because it was failing.

**3 (checked, not a finding) — nothing else in the module walks raw
ledger rows.** `gather` reads the ledger once (`dashboard.py:406`) and
hands the list to two places: `_metrics`, which routes spend through
`cost_report.aggregate` and deliberately reads gate rows directly for the
wait median (that is what `cost_ledger.gate_wait` is for), and `_spend`.
`_metrics`'s two uses are correct: the median wants gate rows, the spend
figures do not.

## Design

**4 — the fix is the shared rule, not a local predicate.** `_spend` could
have filtered on `cost_ledger.gate_wait(entry) is None` inline, which
would read the same today. It would also be a second copy of a rule whose
docstring calls itself "The ONE row-selection rule", and `one_owner.py`
exists in this repo to find exactly that. `test_the_rule_is_cost_ledgers_
not_a_second_copy` pins the delegation rather than the outcome, so a
future change to what counts as a spend row reaches the console without a
second edit here.

**5 — no documentation changed, because none was wrong.**
`cost_ledger.dispatched`, `cost_report.aggregate` and `dashboard._metrics`
all already described the fixed behaviour; `_spend`'s own docstring
already promised "never $0". This run brought the code to its docs, and
the added paragraph in `_spend` says which rule it now defers to and why,
in the module where the divergence was.

**6 (deferred, noted) — `dispatched`'s caller list in its docstring is
now short by one.** It says "The ONE row-selection rule behind **both**
month-to-date figures — the weekly report's spend breakdown and the work
queue's circuit-breaker input". There is now a third caller, and it is
not a month-to-date figure. Deferred: `cost_ledger.py` is touched by an
unmerged agent branch, and a one-word docstring edit is not worth a
conflict. Recorded as a follow-up; the sentence is not wrong about what
the rule is, only incomplete about who uses it.

**3b (found by CI, fixed) — the verification artifact quoted a fixture's
work-order token.** `verification.md` reproduced the failing assertion
verbatim, which put a `WO-####` id from the test fixtures into
`docs/**/*.md`. Detector C reads every such token there as a claim about
a real breakdown row and failed the build with a `dangling … (no
breakdown row)` problem naming that line. The local
battery had not caught it because it was run before the artifacts were
written — the run's own ordering mistake, not a detector gap. The
sentence now describes the assertion without spelling the token, and says
why.

## Security

Nothing. The change is a filter over already-validated in-memory rows: no
new input surface, no IO, no subprocess, no path handling. `_spend` was
and remains pure.

## Not addressed

**7 — the console's other operator numbers were not audited.** This run
looked at the ledger readers because that is where the reported symptom
was. `_rates`, `_corrections` and `_queues` compute operator-facing
figures from different sources and were read but not systematically
checked against their own docstrings. Saying so beats letting the run
read as a survey of the module.

## Verdict

No critical or major findings. 1, 2 and 4–5 are accepted as designed; 3
and 7 are recorded observations; 6 is deferred with a reason.
