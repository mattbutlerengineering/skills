# Plan 011: Make the circuit breaker actually monthly — timestamped ledger rows, month-windowed cap, automatic un-pause

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 2e63a04..HEAD -- cost_ledger.py cost_report.py budget_guard.py gate_digest.py .github/workflows/cost-report.yml tests/test_cost_ledger.py tests/test_cost_report.py tests/test_budget_guard.py tests/test_gate_digest.py tests/test_gates.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: none
- **Category**: bug (stale-ADR drift)
- **Planned at**: commit `2e63a04`, 2026-08-02

## Why this matters

ADR-0034 (`docs/adr/0034-work-order-budgets-and-routing.md`) promises "a
monthly circuit breaker pauses dispatch repo-wide when spend crosses the
cap." The implementation is a **lifetime** cap: the cost ledger has no
timestamp field, so `cost_report.aggregate()` sums every row ever written,
and the workflow sets the `FACTORY_PAUSED` repo variable to `true` on a
breach but nothing ever sets it back. The first time cumulative spend
crosses `monthly_cap_usd`, the dispatch plane latches off permanently —
every subsequent weekly run recomputes PAUSE from a number that never
decreases. Conversely, a genuine one-month blowout is invisible until the
lifetime total catches up. The owner has decided the cap means **monthly,
as ADR-0034 says** — this plan makes the code agree.

## Current state

- `cost_ledger.py` — the one home of the ledger shape (ADR-0037 seam).
  Lines 27–29:

  ```python
  COST_LEDGER = "docs/factory/costs.jsonl"
  LEDGER_FIELDS = ("wo", "run_id", "model", "tokens", "cost", "outcome")
  LEDGER_TEXT_FIELDS = ("run_id", "model", "outcome")
  ```

  `entry()` (line 37) builds a record with `dict(zip(LEDGER_FIELDS, ...))`.
  `gate_entry()` (line 44) builds a gate-latency row whose `run_id` is
  `f"gate-{gate}-{passed_at}"` where `passed_at` is an ISO timestamp.
  `line_problems()` (line 86) reports **both** missing fields and unknown
  fields against `LEDGER_FIELDS`, so any new field must be threaded there
  or every row carrying it becomes a detector-G CI failure.

- `cost_report.py` — lines 44–69: `aggregate(entries)` sums every entry
  (skipping gate-latency rows via `cost_ledger.gate_wait`); line 106:
  `decide(totals["total_cost"], cap)` compares that total to the cap.
  `run_report` (line 142) already takes an injected `clock` and computes
  `as_of = clock().date().isoformat()`.

- `budget_guard.py` — `hard_stop()` (line 118) is the only in-repo writer
  of dispatched-run rows: `cost_ledger.append(root, cost_ledger.entry(wo,
  run_id, model, tokens, cost, outcome))`.

- `gate_digest.py` — writes gate-latency rows via `cost_ledger.gate_entry`
  (grep `gate_entry` to find the call).

- `.github/workflows/cost-report.yml` — lines 67–79: the "Pause dispatch
  on a cap breach" step runs only `if: steps.report.outputs.pause ==
  'true'`, fails loudly when `FACTORY_PAUSE_TOKEN` is unset, and runs
  `gh variable set FACTORY_PAUSED --body true`. There is no `false`
  branch anywhere. `assembler.yml:42` is the variable's one reader
  (`vars.FACTORY_PAUSED != 'true'`).

- `docs/factory/costs.jsonl` — existing rows (16+) have **no** `at`
  field. They are legacy and must keep parsing cleanly. The ledger is
  append-only (CLAUDE.md "Eval honesty" discipline): **never rewrite or
  backfill existing lines.**

- Conventions: functions return label-prefixed problem strings
  (`ledger:`/`cr:` prefixes); tests assert exact strings through public
  interfaces (see `tests/test_lint.py` for the idiom, and the
  existing `tests/test_cost_ledger.py` / `tests/test_cost_report.py`
  suites as the structural pattern). Repo is Python stdlib only.
  `cost_ledger.py`, `cost_report.py`, `budget_guard.py`, `gate_digest.py`,
  and `cost-report.yml` are all mirrored into `factory/templates/` via
  `factory_init.py update-manifest`; detector E fails CI if the payload
  and manifest drift.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Full local gate (exactly what CI runs) | `make check` | exit 0; `lint: 0 problem(s)`, `gates: 0 problem(s)`, all tests OK |
| Just the tests | `python3 -m unittest discover tests` | all pass |
| One suite | `python3 -m unittest tests.test_cost_report -v` | all pass |
| Refresh payload mirrors + manifest | `python3 factory_init.py update-manifest` | exit 0, `factory/manifest.json` rewritten |

## Scope

**In scope** (the only files you should modify):
- `cost_ledger.py`
- `cost_report.py`
- `budget_guard.py`
- `gate_digest.py` (only the `gate_entry` call, if a change is needed there)
- `.github/workflows/cost-report.yml`
- `tests/test_cost_ledger.py`, `tests/test_cost_report.py`,
  `tests/test_budget_guard.py`, `tests/test_gate_digest.py`,
  `tests/test_gates.py` (workflow-shape assertions only)
- `factory/templates/**` and `factory/manifest.json` — **only** via
  `python3 factory_init.py update-manifest`, never by hand
- `plans/README.md` (status row)

**Out of scope** (do NOT touch):
- `docs/factory/costs.jsonl` — append-only; never edit existing lines.
- `docs/adr/0034-work-order-budgets-and-routing.md` — the code is moving
  toward the ADR; the ADR does not change.
- `gates.py` detector G's problem-string format (it consumes
  `cost_ledger.line_problems`; your change flows through automatically).
- `assembler.py` / `assembler.yml` — the variable's reader is untouched.

## Git workflow

- Branch: `advisor/011-monthly-circuit-breaker-window`
- Conventional commits, e.g. `fix(cost): month-window the circuit breaker
  and auto-unpause (ADR-0034)` (match the style of `git log --oneline -10`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Add the optional `at` field to the ledger grammar

In `cost_ledger.py`:

1. Add beside `LEDGER_FIELDS`:

   ```python
   # Optional-on-read, written by every new row (this plan): the UTC date
   # the row was appended, "YYYY-MM-DD". Absent on pre-2026-08 legacy rows,
   # which stay valid — the ledger is append-only and never backfilled.
   LEDGER_OPTIONAL_FIELDS = ("at",)
   ```

2. In `line_problems()`: allow `at` in the unknown-field check
   (`set(entry) - set(LEDGER_FIELDS) - set(LEDGER_OPTIONAL_FIELDS)`), do
   **not** add it to the missing-field check, and add a per-field rule:
   when `"at" in entry`, it must be a string parseable by
   `datetime.date.fromisoformat` — else append
   `f"at {value!r} is not an ISO date (YYYY-MM-DD)"`.

3. Change `entry()` to require the date:

   ```python
   def entry(wo, run_id, model, tokens, cost, outcome, at):
       """... `at` is the UTC date the row is written ("YYYY-MM-DD");
       every NEW row carries it (the monthly circuit breaker windows on
       it), while legacy rows without it stay readable."""
       record = dict(zip(LEDGER_FIELDS, (wo, run_id, model, tokens, cost,
                                         outcome)))
       record["at"] = at
       return record
   ```

   Making `at` a required positional on the **writer** while optional on
   the **reader** is the point: new rows always carry it, old rows never
   fail.

4. `gate_entry()` derives it — `at=passed_at[:10]` (the ISO timestamp's
   date part), so gate rows need no clock:

   ```python
   return entry(wo, f"gate-{gate}-{passed_at}", "none", 0, 0.0,
                f"gate_wait:{gate}:{int(waited_seconds)}s",
                at=passed_at[:10])
   ```

**Verify**: `python3 -m unittest tests.test_cost_ledger -v` → failures
only in tests that call `entry()` with the old arity (fixed in step 4).

### Step 2: Window `cost_report` to the current month

In `cost_report.py`:

1. Give `aggregate` an optional month filter:

   ```python
   def aggregate(entries, month=None):
       """... When `month` ("YYYY-MM") is given, only rows whose `at`
       date falls in that month are counted — rows without `at` are
       legacy (pre-timestamp) and belong to closed months by
       construction, so they are excluded from a windowed total."""
   ```

   Inside the loop, after the gate-row skip:
   `if month is not None and not str(entry.get("at", "")).startswith(month): continue`

2. In `guard()`: compute both — `totals = aggregate(entries)` (lifetime,
   for the report body) and `month_totals = aggregate(entries, month)` —
   and decide on `month_totals["total_cost"]`. Thread `month` in as a
   parameter (`guard(root, config=None, ledger_path=None, month=None)`);
   `run_report` computes `month = clock().date().isoformat()[:7]` and
   passes it. Keep the fail-closed paths exactly as they are (unreadable
   ledger / unresolvable cap still PAUSE).

3. `decide()`'s reason strings already say "monthly cap" — now true.
   Update `compose_report` so the spend line is honest about the window:

   ```
   **Spend this month ({month}):** $X.XX of $CAP.00 monthly cap (lifetime: $Y.YY)
   ```

   Adjust the function signature as needed; keep the rest of the body
   format unchanged so existing assertions need only targeted edits.

**Verify**: `python3 -m unittest tests.test_cost_report -v` → existing
cap tests fail only where they assumed lifetime semantics (fixed in
step 4).

### Step 3: Stamp `at` at the writers and sync the pause variable both ways

1. `budget_guard.py` `hard_stop()`: add a required keyword `at` (beside
   `run_id`, `model`, etc.) and pass it through to `cost_ledger.entry`.
   Docstring: one line noting the caller stamps the UTC date (injected,
   not computed here, to keep the function's IO injected).

2. `.github/workflows/cost-report.yml`: replace the single pause step's
   tail so the variable tracks the verdict in **both** directions. Keep
   the existing breach step exactly as is (loud failure when the token is
   missing), and add after it:

   ```yaml
   # A new month starts under the cap: clear the breaker so dispatch
   # resumes without a human remembering the variable exists. Skipped
   # (not failed) without the token — an unclearable pause is safe,
   # an unenforceable one is not (mirror of the breach step above).
   - name: Resume dispatch when under the cap
     if: steps.report.outputs.pause == 'false'
     env:
       GH_TOKEN: ${{ secrets.FACTORY_PAUSE_TOKEN }}
     run: |
       if [ -n "${GH_TOKEN}" ]; then
         gh variable set FACTORY_PAUSED --body false
       else
         echo "cost-report: no FACTORY_PAUSE_TOKEN — FACTORY_PAUSED left as-is"
       fi
   ```

**Verify**: `python3 -m unittest tests.test_budget_guard -v` → only
arity failures remain (step 4).

### Step 4: Update the tests

- `tests/test_cost_ledger.py`: fix `entry()` call sites to pass `at`
  (e.g. `"2026-08-02"`); add cases — `entry` includes `at`; `gate_entry`
  derives `at` from `passed_at`; `line_problems` accepts a legacy row
  without `at`; rejects `at: "yesterday"` with the exact string
  `at 'yesterday' is not an ISO date (YYYY-MM-DD)`.
- `tests/test_cost_report.py`: update cap tests to write rows with `at`
  in the report's current month (the suites already inject `clock`);
  add: (a) a row in a **previous** month plus a small current-month row →
  CONTINUE (rollover un-latches), (b) current-month rows at the cap →
  PAUSE, (c) legacy rows without `at` are excluded from the monthly total
  but appear in the lifetime figure, (d) `outputs["pause"] == "false"`
  in the new-month case.
- `tests/test_budget_guard.py`: fix `hard_stop` call sites; assert the
  appended ledger line carries `at`.
- `tests/test_gate_digest.py`: assert captured gate rows carry `at`
  equal to the passage date.
- `tests/test_gates.py`: find the cost-report workflow assertions
  (grep `COST_REPORT_WORKFLOW`) and add one test asserting the workflow
  text contains `gh variable set FACTORY_PAUSED --body false` (the
  resume leg exists).

**Verify**: `python3 -m unittest discover tests` → all pass.

### Step 5: Refresh the payload mirrors

```
python3 factory_init.py update-manifest
```

**Verify**: `make check` → exit 0 (detector E green, all suites green).
`git status` shows `factory/templates/` mirrors and `factory/manifest.json`
updated alongside your root edits.

## Test plan

Covered in step 4; the two load-bearing new behaviors are **rollover
un-latches** (previous-month spend over the cap + current month under it
→ CONTINUE and `pause=false`) and **legacy rows stay valid but don't
count monthly**. Model new tests after the existing style in
`tests/test_cost_report.py` (build entries with the module's own `entry()`
helper, inject `clock`).

## Done criteria

- [ ] `make check` exits 0
- [ ] New tests from step 4 exist and pass
- [ ] `grep -n '"at"' cost_ledger.py` shows the optional-field handling
- [ ] `grep -n 'body false' .github/workflows/cost-report.yml` → 1 match
- [ ] `docs/factory/costs.jsonl` is byte-identical to before
      (`git diff --stat docs/factory/costs.jsonl` → empty)
- [ ] `factory/manifest.json` regenerated and committed with the change
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- `cost_ledger.entry` has callers beyond `budget_guard.hard_stop`,
  `cost_ledger.gate_entry`, and tests (`grep -rn "cost_ledger.entry\|ledger.entry(" --include="*.py" .`) — an unplanned caller means the
  arity change breaks something this plan didn't map.
- Existing rows in `docs/factory/costs.jsonl` already carry an `at` or
  timestamp field (the grammar moved since planning).
- Detector G (`gates.py` `check_cost_ledger`) hard-codes the field tuple
  separately from `cost_ledger.LEDGER_FIELDS` — the seam has been
  bypassed and the plan's premise is wrong.
- `make check` fails after step 5 for any reason other than a test you
  are mid-way through fixing.

## Maintenance notes

- Future ledger writers **must** pass `at`; the writer signature enforces
  it. If a second writer appears that can't know the date, revisit the
  optional-on-read rule rather than dropping the field.
- The monthly window excludes legacy (no-`at`) rows. Once a full month of
  timestamped rows exists this is moot; until then the monthly total
  understates the current month only if rows were written between this
  plan landing and its first deploy — acceptable and self-healing.
- If ADR-0034's cap semantics are ever revisited (e.g. rolling 30 days
  instead of calendar month), `aggregate(entries, month)` is the single
  place the window lives.
- Reviewer should scrutinize: the fail-closed paths in `guard()` still
  PAUSE on unreadable ledger/config; the workflow's resume step must
  *skip*, never fail, without the token.
