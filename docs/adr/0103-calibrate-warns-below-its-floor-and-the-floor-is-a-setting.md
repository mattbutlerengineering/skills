# Calibrate warns below its floor, and the floor is a setting

- Status: provisional
- Date: 2026-10-16

Amends the `calibrate` verb of PRD-0013 (issues #799, #830): the floor
stays as a guard on a suggested number, and stops guarding the verdict
the counters already give.

## Context

After three closed consumer batches and about $55 of metered runs,
`conductor.py calibrate` printed `spec attempts 4 ceiling_hits 3` and
`review attempts 2 ceiling_hits 2`, then `step_weights: null` and
"below the floor of 5" (issue #940). Every gate over the same period
re-priced a size-M item 43% to 71% above its plan. The floor of five
was set when one real batch existed, as the fewest samples a suggested
weight could rest on; it was a module constant, and it also silenced
the one reading that needs no sample size.

The suggestion cannot say a weight is too low. It scales the weight in
force by mean spend over the ceiling (ADR-0034's budgets, #830), and a
run that stops at its ceiling spends at most the ceiling: what it would
have spent uncapped is not recorded. From runs that keep hitting the
ceiling the suggestion keeps or lowers the weight, never raises it. The
counters are the only up-signal.

Two row shapes muddied the build sample. Older tools wrote the item
(`#6367`) into a spend row's `wo`, so every build row of that batch
keyed to one unit against one row's ceiling; a runner lost before it
metered is charged its step's full ceiling under the item too (#967).

## Decision

1. **The counters warn, floor or no floor.** A step whose attempts
   spent their ceiling half the time or more, at two attempts or more,
   gets one advisory line — `spec: 3 of 4 attempts spent the ceiling;
   the weight is too low` — in `calibrate`'s `warnings`. The rule and
   the text have one owner, `conductor_calibrate.ceiling_warnings`
   (`WARN_ATTEMPTS`, `WARN_SHARE`, `WARNING`). A warning is output,
   never a problem string: it fails no command.
2. **`plan` and `open` repeat it.** They price the next batch from the
   same weights, so they read the same closed ledgers
   (`conductor_calibrate.warning_lines`) and print each warning as a
   `cd:` line after the plan, before the payload line. A closed batch
   that does not join its spend rows costs the plan one line saying so
   and pointing at `calibrate`, which names the problem; it never
   refuses a plan, because a bad ledger on main is append-only
   evidence (#837) and must not block the next batch.
3. **The floor is `conductor.calibrate_floor`.** A positive integer in
   factory.json's conductor table, 5 when absent
   (`factory_config.DEFAULT_CALIBRATE_FLOOR`), validated in
   `factory_config.conductor_problems` like its neighbours, so
   detector F and `resolve_calibrate_floor` apply one grammar. The
   floor still guards every suggested number; it guards no warning.
4. **A lost runner's ceiling row is a hit.** Its cost is the ceiling,
   so `cost >= ceiling` counts it with no special case: the ceiling
   was spent, whoever spent it.
5. **A build row keyed by its item leaves the sample, not the counts.**
   A build row whose `wo` is an issue key — an older tool's row, a
   breakdown row that named no work order, or a lost runner's — is one
   attempt and, when it spent the ceiling, one hit, but no unit of the
   build sample, and its spend still counts toward its item's size
   budget. `calibrate` prints a `set_aside` line per step saying how
   many rows and why. Only build is keyed per breakdown row; every
   other step runs once per item under the item's key and is never
   set aside.

## Alternatives that lost

- **Lower the default floor.** Two or three would have suggested
  numbers from the consumer's batches, built on the mixed build rows
  above, and still said nothing about a step that spends its ceiling
  every time: the floor was the wrong lever for that reading.
- **Let the suggestion scale a weight up.** There is no number to scale
  from: a capped run's uncapped spend is not recorded. A guess would be
  a number the Owner might adopt; a warning is a verdict they act on.
- **Fail `plan` when a closed batch does not join.** The warning is
  advisory; a ledger inconsistency `calibrate` already refuses must
  not also block every future batch.
- **Key a pre-work-order build row by its run.** One unit per run would
  count a retried row's attempts as separate samples, the opposite of
  what the sample means.

## Consequences

- `calibrate`'s card gains `warnings` and `set_aside`; a step every row
  of which was set aside shows `n: 0` with null mean and max, and the
  existing "no run of <step> to scale its weight from" refusal stands
  beside the `set_aside` line that explains it.
- `plan` output gains zero or more `cd:` warning lines; a reader of the
  plan by line position still finds the payload line last before the
  summary.
- The conduct skill's read-back reports the warnings and set-aside
  lines as printed, and the floor is the Owner's to lower.
