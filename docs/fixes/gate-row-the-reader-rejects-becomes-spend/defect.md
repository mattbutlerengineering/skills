---
stage: capture
run: maintenance:gate-row-the-reader-rejects-becomes-spend
date: 2026-08-27
re-entry: implement
assumptions: ["no user-supplied brief exists for this run; the brief was
  authored from this session's own investigation under a standing autorun
  instruction, and its provenance is recorded at the head of
  autorun-brief.md"]
---

# Defect: a gate row the reader rejects becomes spend

## Defect

The gate-outcome grammar is stated twice in `cost_ledger.py`, and the
two statements disagree about what is well-formed.

The reader constrains both fields:

```python
# cost_ledger.py:47
GATE_OUTCOME = re.compile(r"gate_wait:([a-z]+):(\d+)s")
```

The writer constrains neither:

```python
# cost_ledger.py:64
def gate_entry(wo, gate, waited_seconds, passed_at):
    return entry(wo, f"gate-{gate}-{passed_at}", "none", 0, 0.0,
                 f"gate_wait:{gate}:{int(waited_seconds)}s",
                 at=passed_at[:10])
```

A gate name containing anything but lowercase letters, or a negative
wait, produces a row `gate_wait` refuses.

## Why it matters

A refused row does not simply lose its observation. `dispatched()`
selects spend rows by exclusion:

```python
    return [entry for entry in entries
            if gate_wait(entry) is None
```

so a row `gate_wait` cannot parse is counted as a dispatched run. Its
own docstring states the stakes:

> The ONE row-selection rule behind both month-to-date figures — the
> weekly report's spend breakdown and the work queue's circuit-breaker
> input — so the number ADR-0034's cap is compared against has one
> definition rather than one per caller.

A wait observation is therefore miscounted as a run against ADR-0034's
monthly cap.

## Reproduction

```
$ python3 -c "
import cost_ledger
for gate in ('merge', 'code-review'):
    row = cost_ledger.gate_entry('WO-0001', gate, 120, '2026-08-27T00:00:00Z')
    print(gate, cost_ledger.gate_wait(row), len(cost_ledger.dispatched([row])))
"
merge ('merge', 120) 0
code-review None 1
```

The same for a negative wait:

```
$ python3 -c "
import cost_ledger
row = cost_ledger.gate_entry('WO-0001', 'merge', -30, '2026-08-27T00:00:00Z')
print(row['outcome'], cost_ledger.gate_wait(row), len(cost_ledger.dispatched([row])))
"
gate_wait:merge:-30s None 1
```

## Present reachability

Not reachable from today's shipped gates. `human_gates.GATES` names
`prd`, `blueprint` and `merge`, all of which the reader admits, so no
row in `docs/factory/costs.jsonl` is affected and this run rewrites
nothing.

The trigger is a fourth gate. `GATES` is an extensible tuple of
namedtuples (ADR-0056), and a natural ledger name for a new gate —
`code-review`, `needs-qa` — is exactly the shape the reader refuses.
The failure would be silent: no exception, no problem string, only a
spend figure that is quietly wrong.

This is recorded as a latent defect with a plausible trigger, not as a
live failure. The fix is a guard at the write boundary, not a repair of
existing data.

## Breakdown

- [x] `gate_entry` refuses to build a row `gate_wait` cannot read, with
      `GATE_OUTCOME` itself as the authority so the writer's constraint
      cannot drift from the reader's. Acceptance: a test asserts that
      for every input, either `gate_entry` raises or `gate_wait` parses
      what it returned — never a silent unreadable row.
- [x] The three shipped gate names still round-trip unchanged.
      Acceptance: the existing `cost_ledger`, `cost_report`,
      `gate_digest` and `gates` suites pass unmodified.
- [x] Full battery green.

## Notes

2026-08-27 — the guard checks the composed outcome against
`GATE_OUTCOME` itself rather than restating the constraint. Two
statements of a grammar was the defect; a hand-written second
constraint in the writer would have been the same defect in a new
place.

`cost_ledger.py` is in `factory_init.MIRRORS`, so the payload copy
carries the guard too and the manifest was regenerated.
