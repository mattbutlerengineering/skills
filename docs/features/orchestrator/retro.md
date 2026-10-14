---
stage: operate
run: feature:orchestrator
date: 2026-10-14
assumptions:
  - "The outcome evidence is two real consumer batches in mattbutlerengineering/mattbutlerengineering, b20261012 and b20261013, recorded in verification.md §Real consumer batches. Both are smaller than PRD-0013's four-issue condition, so every outcome below is an anecdote or a single measurement, not a pattern."
---

# Retro: the Conductor, a batch orchestrator

## Outcomes vs. intent

### The Owner moves a batch from plan to merged by answering one question at a time

- What happened: the decision queue worked as designed. Twelve asks across the two batches, including spend, gate, five stalls, the circuit breaker and two closing merges, were each presented and answered one at a time, and the asks' `recommended` and `why` fields mapped straight onto the Owner's one-question UI (#713). But **0 items merged** in either batch. Batch 1's three spec runs all hit the even-split $3 ceiling. Batch 2 completed spec, all five build rows and verify, then its review stalled twice at $2.14. The Owner also had to act outside the queue: two setup merges and hand workarounds at close.
- Signal strength: measured (two batch ledgers and scorecards), on batches of 2 and 1 items.

### Cost is metered and estimates are honest (SC 3)

- What happened: every Worker run wrote a spend row (13 runs, $30.97 total). The estimates missed in both directions, by -68.9% and +44.3%. Pricing, not orchestration, was the binding constraint: one even share per step starved spec, and with spec weighted 3 it was review that ran short.
- Signal strength: measured, n = 13 runs.

### It works in a repo that is not this one (the goal the Owner set: "consumed by other repos")

- What happened: it does, but only after a dozen consumer-only defects were found and fixed. None of them reproduces in this repo: no seeded cost ledger (#708), worktrees nested in a linked checkout (#710), tracked bytecode (#705, #726), a missing `needs-human` label, husky hooks failing without `node_modules`, prettier rejecting the run evidence, a consumer's own auto-merge racing the closing merge (#807), and the reservation scan reading the payload's own ADR citations (#821).
- Signal strength: measured. Each one is a filed issue with a repro.

## Run retrospective

- Keep: price before spend, and fail closed. Every refusal, from #708 through the stalls, cost $0 or exactly one ceiling. One question at a time from the ledger. Filing a defect from inside the batch, so the next release fixed it while the batch was still open.
- Change: run the first paid batch only after a **no-spend consumer rehearsal**: a scratch consumer with husky, prettier and auto-merge, driven through plan, open, a stubbed run and close. The dry run on 2026-10-11 stopped at `plan`, and every defect it missed sat in `open`, `run` or `close`.
- Stop: hand-weighting step ceilings from intuition. `conductor.py calibrate` (#809) now joins the ledgers into per-run actuals. Re-weight from it once each step has n ≥ 5 runs.

## Environment

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| The first `run` in any consumer refused, because nothing seeds `costs.jsonl` | #708; verification.md §Real consumer batches | mechanical | `tests/test_factory_init.py` TestAcceptanceStampRealRepo: stamp, then drive `plan`, `open` and a stubbed `run` |
| Compact run-evidence JSON failed the consumer's prettier check | #6383, #6584 fix commits; this retro | mechanical | `conductor_run` writes `runs/*.json` with `indent=2` and a trailing newline. Assert it in `test_conductor_run` |
| The Conductor's commits failed under consumer husky hooks with no `node_modules` | the close of b20261012 and b20261013 (`HUSKY=0`) | judgement | the "Consumer adoption" section of `docs/setup.md`: say that `close` commits in a worktree with no installed hooks |
| The reservation scan counted the payload's own ADR citations | #821 | mechanical | `test_conductor_plan`: a fixture stamped repo whose tools cite ADR-0086 reserves the consumer's next number |
| The closing merge raced the consumer's auto-merge | #807 | mechanical | `test_conductor_close` (the #807 fix) |
| Even-split ceilings starved spec, and weighted ceilings starved review | #724; b20261013 ask-4 and ask-5 | judgement | the `conduct` skill: read `conductor.py calibrate` before trusting default weights on a new repo |

## Idea seeds

- A no-spend consumer rehearsal: stamp a scratch consumer with husky, prettier and an auto-merge workflow, and drive plan, open, run (stubbed harness) and close end to end in CI.
- Re-weight `factory_config.DEFAULT_STEP_WEIGHTS` from `conductor.py calibrate` once each step has n ≥ 5 runs. One batch suggests review ≈ 2 shares, and verify and ship ≈ 0.5.
- A batch of 4+ items in a consumer repo to score PRD-0013 as written (#822).

## Run complete

2026-10-14. #688 closes on the Owner's choice ("Record, retro, close"). The criteria scored on undersized batches are in verification.md, and the 4+ item batch is #822. The seeds above go to docs/backlog.md.
