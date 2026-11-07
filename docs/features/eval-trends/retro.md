---
stage: operate
run: feature:eval-trends
date: 2026-11-07
users-observed: 1
signal-source: "The Owner's decision comment on issue #1063 (2026-10-26), grounded in the tool's Wilson-interval output, plus the 2026-10-22 runs recorded in docs/fixes/eval-trends-honest-output/defect.md and Operate's own run on 2026-11-07; every recorded execution services the run's own debt or this retro, and no decision-use (funding a paid run off the tool's output) is recorded anywhere"
---

# Retro: A read-only eval pass-rate trend view

Shipped 2026-10-21 (PR 1056 merged same day; write-back recorded, #1057
closed). Root-only tool, so no plugin release was needed. Seventeen days
of history to read, and the tool's own output is the cleanest signal in
it: run on 2026-11-07 against the real tree, it prints the inventory,
two same-day rerun spreads, and a REFUSED line for every surface —
53 records and still not one real trend line, exactly the honest
headline Ship wrote at release.

## Outcomes vs. intent

### Prints trend lines from real records, refuses where n is too small (idea.md's success sentence)

- What happened: half observed, half structurally out of reach. The
  refusal half works and is exercised: today's run refuses every surface
  with a named reason (case sets differ, different suites, same-day
  only), and the eval-trends-honest-output fix (#1066, released
  2026-10-22) tightened it further — a no-records line for an empty
  root, the multi-record hull relabelled `range` instead of `95%`,
  symlinked and oversize records refused. The trend half has never
  printed on real records, only on synthetic fixtures: no surface has
  two same-suite, same-case-set records on different days, and nothing
  in the repo produces one. The three plugin records added 2026-10-26
  made plugin the first two-day surface, but each record is a different
  suite, so it refuses too.
- Signal strength: measured (the 2026-11-07 run, quoted output) for the
  refusal half; unobserved for the trend half

### The Owner reads the output and decides which paid runs to fund (PRD problem statement)

- What happened: one observed engagement, and it was a decision — the
  Owner's #1063 comment (2026-10-26) kept `MIN_CASES=30 / MIN_DAYS=2`
  as a floor, reasoning from the tool's own behaviour ("every rate
  prints with its Wilson 95% interval, so a small-n rate shows its
  width"). No funding decision for a paid eval run has been traced to
  the tool's output; whether it changes those decisions was explicitly
  out of scope to measure, and remains unmeasured.
- Signal strength: anecdote

### Honest output on today's records (PRD criterion 2)

- What happened: still true at 53 records, 17 days and three new
  plugin-eval records later — inventory lines, rerun-spread lines,
  REFUSED lines with need/have counts, exit 0, no invented number. The
  one dishonesty found after release (the multi-record hull wearing the
  single-record `95%` label) was the run's own deferred finding and was
  fixed the next day.
- Signal strength: measured (run on 2026-11-07)

### The research note names the metric set and what n justifies a claim (PRD criterion 11)

- What happened: the note's one soft spot — the 30-case floor no fetched
  source supports — became issue #1063 and got an explicit Owner ruling:
  keep it, it is a convention backed by Wilson arithmetic, revisit when
  a suite grows past ~30 cases per record. The note is also the
  reference the tool's own output points at on every run (its last
  line). No reader outside the run's own actors is recorded.
- Signal strength: anecdote

## Open debt

The run's own debt, counted toward nothing. Most of it already moved —
the contrast with parked-prose debt is this retro's sharpest process
finding:

- Closed: #1062 (review's deferred minors — empty-root wording, hull
  label, symlink/size) fixed by the eval-trends-honest-output
  maintenance run, merged 2026-10-22 (#1066). #1063 (the unsupported
  30/2 floor) decided and closed by the Owner 2026-10-26. #1057 (ship
  write-back) done.
- Still open: ADR-0115 remains `provisional` 17 days after release
  (release.md Owner step 2). The launch brief was never produced
  (`launch_demo.py config` said SHIP).
- Documented non-changes, not debt: future-dated records accepted when
  the name agrees; one first-vs-last comparison per group, no
  multiple-comparison correction — both recorded in review.md and the
  tool's own header.

## Run retrospective

- Keep: debt as tracker issues. This run filed its deferrals as #1062
  and #1063 at ship time; one was fixed and one decided within four
  days. The house-voice run, shipped the same week, parked eight
  deferred items as release.md prose and none moved in 13 days. Same
  factory, same Owner — the carrier made the difference.
- Keep: the honest-headline discipline. Ship wrote "the tool prints an
  inventory and REFUSED lines and no trend" as the outcome, and 17 days
  later that is still exactly what it does; nobody had to walk back a
  claim.
- Change: a reader shipped without a producer. The tool's purpose needs
  comparable records — same suite, same case set, ≥30 cases, two days —
  and nothing in the repo generates them: trigger's case set grew
  47→152→185 (every growth resets the comparison), plugin records are
  one suite each, charter replays landed on one day. REFUSED is
  currently a permanent state, not a waiting state. The next run in this
  area should produce the data, not refine the reader.
- Stop: duplicating issue-tracked decisions as release.md Owner steps.
  Step 3 ("decide whether to raise MIN_CASES/MIN_DAYS") and #1063 were
  the same item; the issue carried it to a decision, the prose step just
  aged.

## Environment

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| A record's `date` field was trusted over its file name, silently re-dating a record | `review.md` §Major date field | mechanical | the name/date agreement check now in `eval_trends.py`, pinned in `tests/test_eval_trends.py` — and the same rule belongs in `eval_schema.py` validation for every record reader |
| An object or list where a scalar belonged aborted the whole view with a traceback | `review.md` §Major object-or-list | mechanical | adversarial-shape fixtures in `tests/test_eval_trends.py` (added at review); `eval_schema.py` shape checks are the shared carrier |
| `casesPassed` greater than `casesTotal` reached `wilson()` as a negative square root | `review.md` §Major plugin counts | mechanical | a bounds check at the reader, pinned by fixture — counts are claims, not facts, until checked against the case list |
| The non-overlap verdict printed without the "descriptive, not a significance test" caveat its sibling carried | `review.md` §Major non-overlap | judgement | the `review` skill's statistics pass reading every printed claim against the research note — it is what caught this |
| The research note put the n=30 non-overlap gap at 34 points; recomputing with the tool's own `wilson()` gives 37 | `review.md` §Minor 34-vs-37 | mechanical | review's recompute-every-number pass, run with the shipped code rather than by prose arithmetic |

## Idea seeds

- Produce the first comparable pair on purpose: rerun one suite
  unchanged (same case set, ≥30 cases) on two separate days so
  eval_trends can print its first real trend line — today every surface
  refuses and nothing in the repo ever generates same-suite,
  same-case-set cross-day records, so REFUSED is permanent, not pending
- A pinned benchmark case set that survives suite growth: trigger's case
  set grew 47→152→185 and every growth resets the trend clock; a frozen
  subset, run beside the growing suite, is what makes a long-run trend
  possible at all
- Emit `costUsd` in trigger_eval.py and charter_replay.py result
  records: only plugin records carry cost, so cost-per-pass can never
  print for the other surfaces no matter how many records accrue

## Run complete

Closed 2026-11-07. The tool does what it promised — including refusing
to say what the data cannot back — and the data is now the bottleneck:
the seeds above are all producers, not readers. ADR-0115's acceptance
and the launch brief remain with the Owner.
