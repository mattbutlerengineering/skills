# Plan 012: The assembler refuses a `budget-exhausted` work order (ADR-0034's no-self-retry stop)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 2e63a04..HEAD -- assembler.py tests/test_assembler.py`
> If either file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug (stale-ADR drift)
- **Planned at**: commit `2e63a04`, 2026-08-02

## Why this matters

ADR-0034 (`docs/adr/0034-work-order-budgets-and-routing.md`, ~line 34):
"The dispatcher refuses a `budget-exhausted` order until the owner clears
the label — no self-retry loops." That refusal is unimplemented. Today a
work order that already burned its budget and hard-stopped (the
`budget_guard.hard_stop` path, which ledgers `outcome:
"budget-exhausted"`) can be re-dispatched at **full budget** by
re-applying `wo:ready-for-agent`, with the `budget-exhausted` flag still
sitting on the issue. Each such re-dispatch is real money. The fix is one
guard in `assembler.run_resolve`, failing in exactly the direction the
ADR already specifies.

## Current state

- `assembler.py` `run_resolve(root, env, agents_dir=None)` (lines
  162–203) checks, in order: the event parses → the label is
  `wo:ready-for-agent` → the sender is the owner (`actor_is_owner`,
  no-op refusal with a `reason`) → the issue number exists → the
  breakdown row resolves → charter/band/model resolve. The issue's
  labels are read only to pick a charter:

  ```python
  labels = [(entry.get("name") or "") for entry in issue.get("labels") or []]
  role = select_charter(labels)
  ```

  No flag label is ever consulted; there is no refusal branch.

- The refusal precedent to copy: a non-owner labeler returns
  `{"dispatch": "false", "reason": ...}, []` — a **no-op with a reason,
  not a problem** (exit 0). See `run_resolve`'s docstring: "A non-owner
  or non-ready label resolves to dispatch=false with no problems (a
  no-op); a genuine misconfiguration is a problem."

- The label taxonomy (`factory/templates/.github/labels.json`) ships
  `budget-exhausted` with the description "Flag: hard stop hit; owner
  must clear to re-dispatch".

- Note (context, not scope): nothing currently *applies* the
  `budget-exhausted` label automatically — ADR-0034 says exhaustion
  "labels the order `budget-exhausted needs-human wo:failed`", and that
  leg lives with the dispatched agent's hard-stop protocol, not here.
  This plan implements the refusal side only; the guard is correct and
  valuable regardless of whether the label was applied by automation or
  by the owner.

- Conventions: `asm:`-prefixed strings; tests assert exact strings
  (`tests/test_assembler.py:96-118` is the pattern — see
  `test_a_non_owner_labeler_is_inert`). `assembler.py` is mirrored into
  `factory/templates/` — after editing it run
  `python3 factory_init.py update-manifest` or detector E fails CI.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Full local gate | `make check` | exit 0 |
| Just this suite | `python3 -m unittest tests.test_assembler -v` | all pass |
| Refresh mirrors + manifest | `python3 factory_init.py update-manifest` | exit 0 |

## Scope

**In scope**:
- `assembler.py`
- `tests/test_assembler.py`
- `factory/templates/**`, `factory/manifest.json` — only via
  `update-manifest`
- `plans/README.md` (status row)

**Out of scope** (do NOT touch):
- `budget_guard.py` / `handoff.py` — applying the labels at hard-stop
  time is a separate, deliberately deferred piece (see Maintenance notes).
- `.github/workflows/assembler.yml` — the job-level `if:` cannot see
  issue labels reliably (the `labeled` event's label is the *applied*
  one); the tested authority lives in `run_resolve`, which is exactly
  where this guard goes.
- `factory/templates/.github/labels.json` — the label already exists.

## Git workflow

- Branch: `advisor/012-assembler-refuses-budget-exhausted`
- Commit style: `fix(assembler): refuse a budget-exhausted work order
  (ADR-0034)`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Add the flag constant and the refusal branch

In `assembler.py`, near `READY_LABEL`, add:

```python
# ADR-0034: a hard-stopped order is re-dispatched only after the owner
# clears this flag — the dispatcher itself enforces the no-self-retry rule.
EXHAUSTED_LABEL = "budget-exhausted"
```

In `run_resolve`, move the `labels = [...]` extraction up so it happens
right after the issue-number check (before `resolve_row` — refusing
before the row walk is cheaper and keeps the guard beside the other
authority checks), then add:

```python
if EXHAUSTED_LABEL in labels:
    return {"dispatch": "false",
            "reason": f"asm: issue #{number} carries {EXHAUSTED_LABEL} —"
            " a hard-stopped order is not re-dispatchable until the owner"
            " clears the flag (ADR-0034)"}, []
```

A no-op with a reason (empty problems), matching the non-owner precedent:
the flag being present is an expected state, not a misconfiguration.

**Verify**: `python3 -m unittest tests.test_assembler -v` → existing
tests still pass (none of their fixture issues carry the flag).

### Step 2: Pin the behavior with tests

In `tests/test_assembler.py`, alongside
`test_an_owner_applied_ready_label_dispatches_the_charter` (line ~241),
add two cases using the same event-fixture helpers that test uses:

1. `test_a_budget_exhausted_order_is_refused` — owner applies the ready
   label to an issue whose labels include `budget-exhausted` (plus a
   `type:*` label, to prove the refusal wins over charter selection);
   assert `outputs["dispatch"] == "false"`, the exact reason string from
   step 1, and `problems == []`.
2. `test_clearing_the_flag_makes_the_order_dispatchable_again` — same
   issue without the flag → `dispatch == "true"` (the positive control,
   proving the guard keys on the flag alone).

**Verify**: `python3 -m unittest tests.test_assembler -v` → all pass,
including 2 new.

### Step 3: Refresh the payload mirror

```
python3 factory_init.py update-manifest
```

**Verify**: `make check` → exit 0; `git status` shows
`factory/templates/tools/factory/assembler.py` and
`factory/manifest.json` updated.

## Test plan

Step 2's two cases (refusal + positive control). Pattern:
`tests/test_assembler.py`'s existing end-to-end resolve tests — build the
event dict, call `assembler.run_resolve(root, env)`, assert on
`(outputs, problems)` exactly.

## Done criteria

- [ ] `make check` exits 0
- [ ] `grep -n "EXHAUSTED_LABEL" assembler.py` → constant + one use in
      `run_resolve`
- [ ] Both new tests exist and pass
- [ ] `factory/manifest.json` regenerated and committed
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- `run_resolve` no longer reads issue labels (the code was restructured
  since planning).
- Any existing test fails after step 1 — that means a fixture issue
  already carries the flag and the semantics need a human decision.
- You find an existing refusal branch keyed on any flag label — the
  finding may have been fixed independently; reconcile instead of
  duplicating.

## Maintenance notes

- **Deferred, deliberately**: (a) automation that *applies*
  `budget-exhausted needs-human wo:failed` at hard-stop time (ADR-0034's
  labeling leg — needs a gh runner in the hard-stop path and an issue
  number resolved from the WO, a bigger change than this guard); (b)
  whether `needs-human` should also refuse dispatch. Both belong to a
  future plan; this one keeps the ADR's minimum enforceable promise.
- Reviewer should scrutinize: the refusal returns exit-0 no-op semantics
  (empty problems) — turning it into a problem would make the scheduled
  workflow red every time an exhausted order is (correctly) left alone.
