---
stage: review
run: feature:size-band-calibration
date: 2026-10-20
assumptions:
  - "Autorun stage, no live user: severity is the reviewer's call; every major is fixed here or deferred to the Owner with its reason. No critical finding was found."
  - "Diff scope is `git diff origin/main...HEAD` at 0fd5e9a (the Verify commit): size_band_calibration.py, tests/test_size_band_calibration.py, factory.py, tests/test_dual_membership.py, CLAUDE.md, CONTEXT.md, ADR-0112 and its index row, and the run's artifacts. skills/ diffs against main come only from main moving past the branch point."
  - "Nothing here changes Owner decisions 1-4 or the PRD's fixed strings. The one candidate that would touch the architecture's wording (same-size duplicate tokens) is deferred, not fixed."
  - "Fixes were limited to a guard in main and tests, each test-first (RED shown) and committed alone."
---

# Review: Calibrate S/M/L size bands from past error

## Scope

The code diff above, read in full (the module is 282 lines before the fix),
plus the PRD, architecture.md, ADR-0112, breakdown.md, verification.md and
the brief. Verification came first, so the usual order holds.

Examined by: a full read; the tool on this clone's real ledger (S refused at
n 2, M and L empty, 0 problems); scratch repos with hostile ledgers; a
35-mutant sweep of the module against its own test module, run in a
`git archive` copy so the working tree was never mutated (each mutant's
`old` string asserted to occur exactly once); `python3 one_owner.py` (9
findings repo-wide, none in this branch's files); `python3 kb.py drift`;
`adr_status.py`. Domain passes: none selected (no payments, migrations or
dependency paths). Standards: `docs/standards.json` filters (factory,
eval) matched nothing in the findings.

Review commits on this branch:

- b4e181b `fix(size-band-calibration): a NaN or infinite cost stops the report instead of printing`
- 9d1cb6d `test(size-band-calibration): pin the calibrate-floor config problem path`

## Findings

### Major: a NaN or Infinity cost prints as a figure and exits 0

- Scenario: a ledger line `"cost": NaN` or `"cost": Infinity`. `json.loads`
  accepts both and `cost_ledger.line_problems` only checks "a number, not
  negative", so `read` returns the row clean. Reproduced with five rows (NaN,
  Infinity, 1.0, 2.0, 3.0) at n = 5: the tool printed `BRE P10 -4.000, P50
  -1.500, P90 +inf ... cost $nan mean, $nan total` and `0 problem(s)`, exit
  0. `sorted` over a NaN is also order-dependent, so even the finite
  percentiles were arbitrary. This is the fail-closed violation the PRD
  forbids: unknown printed as a number.
- Standard: none
- Decision: fixed in b4e181b. `non_finite` turns each dispatched row with a
  non-finite cost into a labelled problem and `main` stops before any band
  line, like a rejected ledger line. The test covers NaN and inf and was RED
  first (both subcases printed band lines). The root cause is in the shared
  `cost_ledger.line_problems`; changing it touches a mirrored seam, every
  ledger reader and the manifest, so the upstream fix is DEFERRED to the
  Owner (see Deferred).

### Minor: the calibrate-floor config problem path had no test

- Scenario: mutating `band_stats` to drop `floor_problems` (or its guard)
  survived the whole module. With `conductor.calibrate_floor: 0` in
  factory.json, `main` would then run with a None floor and crash instead of
  stopping with the config problem.
- Standard: none
- Decision: fixed in 9d1cb6d, tests only (the behaviour already existed). Both
  mutants (`return None, problems`, `if problems:`) are KILLED by it.

### Minor: a work-order token under the same size in two runs sums into one sample

- Scenario: the same token in two breakdowns, both `size:S`. `bands` treats it
  as unambiguous, `work_orders` sums both orders' costs into one sample and
  attributes it to `min(seen)`'s run, so two distinct work orders read as one
  expensive one and the re-plan join uses one run only. Only a differing size
  is flagged.
- Standard: none
- Decision: DEFERRED. architecture.md and ADR-0112 define ambiguity as
  conflicting sizes only, and detector C already fails any duplicated work
  order repo-wide (`knowledge_plane.work_orders`' duplicate rule), with none
  today. Widening "ambiguous" to any token seen in two runs changes the
  architecture's stated contract and its exclusion wording; that is the
  Owner's call, not a review edit.

### Minor: `cost_mean`'s `else 0.0` is unreachable output

- Scenario: for an empty band `band_stats` returns `cost_mean` 0.0, but
  `_band_line` takes the `n == 0` branch first and never prints it. The
  survivor (`0.0` to `1.0`) is dead, not a test gap. It exists to avoid a
  ZeroDivisionError in a public function; no 0 is ever shown as a mean.
- Standard: none
- Decision: DEFERRED, no change (a flagged smell; removing it is refactoring).

### Minor: the non-finite guard's scope (dispatched rows) is unpinned

- Scenario: widening `non_finite` to all entries survives. The difference is
  a gate-latency row with a NaN cost, which the tool ignores anyway; scoping
  to dispatched rows is deliberate so an unused row cannot stop the report.
- Standard: none
- Decision: DEFERRED; equivalent for any row the figures use.

## Hunted and clean

- (a) Math. Nearest rank `ceil(p*n/100) - 1` at n = 5 gives ranks 1, 3, 5 (P10
  and P90 are the observed range, and the line says so); n = 10 gives 1, 5, 9.
  Ties sort stably and index by rank. Mutants `ceil` removed, `int`, `round`,
  `<=` on the floor, `max` for `min`, and a flipped sign were all KILLED.
  BRE divides by `min(actual, estimate)`: actual 0 is excluded earlier as
  `zero_cost` (mutant KILLED), negative cost is refused by the ledger shape,
  and `resolve_budget` refuses a non-positive budget, so the divisor is
  positive for every finite input (now enforced for NaN and inf too).
- (b) Join. A token under two sizes is left out and counted `ambiguous`
  (mutants `> 2` and `max(seen)` KILLED). Same-size reuse across runs: see the
  minor above. Retries of one work order are summed deliberately ("over every
  attempt and step", pinned by the `=` for `+=` mutant, KILLED). An issue key
  `#n` or a size-less row falls to `unjoined`, never to a default.
- (c) Fail-closed. Unmeasurable re-plan is named, never 0: the `NO_RUN`,
  `NOT_MEASURED`, `UNREADABLE_HISTORY` and all-unmeasurable branches each
  have a KILLED mutant. An empty band prints the no-row string, not a pass;
  below-floor prints the refusal with n and no interval. Exit codes: 0 on
  data, 1 on problems, 2 on arguments (KILLED). The one hole was NaN/inf,
  fixed above.
- (d) Mutation sweep. 35 applied mutants (each old/new pair is in the sweep output), 32
  killed on first pass; the three survivors are the two floor-problems
  mutants (now killed by 9d1cb6d) and the dead `else 0.0` above. After the
  fixes, the five new mutants: 4 KILLED, 1 SURVIVED (the scope note above).
  The tree was restored each time; `git status --porcelain` was clean.
- (e) One owner. `BANDS` is `factory_config.SIZES`; the gate and owner
  predicates are `cost_ledger`'s; the floor and budget are
  `factory_config`'s. `one_owner.py` reports 9 repo-wide, none naming
  `size_band_calibration`. No new duplicate fact.
- (f) Eval honesty. No literal calibration number in the module; every figure
  is computed from the ledger and breakdowns, and the tool writes nothing
  (a test pins that the live measure runs only `for-each-ref`, `log`, `show`).
  No `evals/results/` file or maturity row was touched.
- (g) Docs vs code. `python3 kb.py drift` prints `drift: 0 problem(s)`. The
  CLAUDE.md bullet (calibrate floor refusal, count-not-estimate exclusion, no
  network call, outside every gate) and the CONTEXT.md term match the code.
  ADR-0112 is provisional and listed live in the index; the dual-membership
  table's 50-pair count matches its four new rows.
- Security. The tool reads local files only; paths come from `run_dirs`, and
  an unreadable file is a labelled problem via `cli.read_file`. Ledger text
  reaches output only through `wo`/`run_id`, which `line_problems` validates
  (the former by pattern, the latter as a non-empty string); no shell or git
  argument is built from them.

## Deferred to the Owner

1. Reject non-finite `cost` in `cost_ledger.line_problems` (the root cause of
   the major). It would protect every reader (weekly report, cap check) and
   needs the mirrored seam, tests and a manifest regen. Not done here: it is
   outside this run's diff.
2. Whether a work-order token seen in two runs should be `ambiguous` even at
   one size (architecture.md's contract says conflicting sizes only).

## Verdict

0 critical, 1 major (fixed), 4 minor (1 fixed, 3 deferred with reasons). Ready
for Ship once the five checks stay green; final lines are in the stage report.
