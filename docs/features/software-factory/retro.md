---
stage: operate
run: feature:software-factory
date: 2026-08-17
---

# Retro: software factory v1 (self-host)

Written the day the close-out shipped — but not on hopes: the factory's
planes have five weeks of live history on this repo (29 merged work
orders, five weekly reports, daily digests, a sweep-filed issue, two
honesty-gate firings on the pipeline's own artifacts). The one surface
with no history is dispatch, and waiting would not have produced any:
it is blocked on a key that was deliberately never minted, not on time.

## Outcomes vs. intent

### The idea's one sentence: "A work order labeled ready-for-agent becomes a merged, gate-checked PR with no human involvement between the three gates"

- What happened: it never did. Zero assembler executions (3 cancelled,
  7 skipped at the job gate); no ANTHROPIC_API_KEY was ever configured;
  no order ever carried a gate-1 or gate-2 approval label. The dispatch
  plane is built, unit-gated, review-hardened (Milestone E), and
  unexercised — the run's headline bet is unrealized, reseeded in the
  backlog as the next run's headline instead.
- Signal strength: measured (run history, label queries, ledger).

### The gates draw blood

- What happened: detector B failed a real PR (#253) until its body was
  corrected; detector H rejected the factory's own verification
  artifact twice (the 2026-08-14 draft's honesty gap noted at review;
  the 2026-08-16 draft failed Ship's pre-flight outright and was raised
  to the bar). Selftests plant and catch broken fixtures on every push.
  The traceability/honesty half of the PRD is not aspiration — it has
  enforcement history against both agent and operator output.
- Signal strength: measured (CI runs, pre-flight logs in release.md).

### Self-observation runs unattended

- What happened: five weekly cost reports posted on schedule with zero
  human touches — the first four with 0 rows (the #222 writer gap,
  honestly recorded as criterion 8's FAIL), this morning's #296 as the
  first recomputed from real rows (18). The gate digest posts daily to
  #178; sweeps filed, labeled, and quoted #173 with no transcription;
  rejection mining maintains the toolsmith queue. The observation plane
  is the half of the factory that already works exactly as designed.
- Signal strength: measured (issues #160/#296/#178/#173, ledger rows).

### Attention moves from execution to judgment

- What happened: partially. 29 work orders merged through the reviewed
  merge gate while the factory built itself, and the digests/reports do
  put judgment surfaces in front of the operator unprompted. But every
  one of those merges was an owner-driven session — with dispatch
  unexercised, throughput is still capped by working hours, which is
  the exact cap the PRD set out to break.
- Signal strength: pattern (five weeks of commit/PR history).

### Budget discipline exists but has never been armed

- What happened: $0.00 lifetime spend; the exhaustion path, circuit
  breaker, and pause verdicts are all test-pinned (and Milestone E made
  their records survive the runner) — but no live exhaustion has run,
  and release.md's pre-flight found the pause step has no
  FACTORY_PAUSE_TOKEN to act with. A real cap breach today would fail
  to set FACTORY_PAUSED.
- Signal strength: measured (ledger, `gh secret list` empty).

## Run retrospective

- Keep: the run-level review after 29 per-PR reviews. It found the
  critical and the shared persistence theme (verdicts recorded on
  ephemeral runners, enforcement skipped on fail-closed paths) that no
  single-PR review could see. Highest-value artifact of the run.
- Keep: honesty gates that bind the pipeline's own artifacts. Detector
  H rejecting the verification draft at Ship pre-flight is the system
  working — the bar held against its author, and the artifact rose to
  it rather than the gate bending.
- Keep: deviations as logged breakdown Notes with amended accept lines
  (labels.json, orientation_pack, on-demand charter replay, WO-0035's
  reseed). Five deviations, zero silent drift.
- Change: prerequisite-check rows at Decompose. WO-0035's supervised
  exercise rode as a row while its true prerequisites — the API key and
  owner time at the gates — were nobody's row, so its accept line had
  to be amended at close. A row whose acceptance needs an external
  precondition should carry it as an explicit blocking edge.
- Change: resolve the gate-1/gate-2 straddle. Approval happens
  in-artifact during owner sessions while the criteria measure approval
  labels nothing flips — so the factory's first two gates are
  unmeasurable by construction. Either session close-out flips the
  labels, or the criterion counts in-artifact approvals. Decide once.
- Stop: prose-cited verification evidence. Two drafts failed detector H
  (one cost a review-cycle note, one a ship pre-flight). The gate now
  enforces what the eval-honesty convention always meant: fenced output
  or an explicit NOT-RUN, nothing in between.

## Idea seeds

Appended to `docs/backlog.md` (the supervised end-to-end traversal was
already seeded at WO-0035's close and is not repeated):

- The cost-report pause step has no token to act with — mint
  FACTORY_PAUSE_TOKEN and live-test the breaker.
- Owner-session approvals never flip the gate-1/gate-2 labels — wire
  the flip or amend the criterion.
- Validator dispatch-arm hardening — review.md 2026-08-16's five
  deferred minors as one bundle.
- ADR-0034's token-budget hook — the third mechanical stop, deferred by
  ADR-0055, scoped for v2.

## Run complete

Closed 2026-08-17. The factory's observation and gating planes are
live and proven on their own repo; the dispatch plane is built and
waiting on exactly two things — a key and an operator at the gates —
both now named seeds. The next run should start where this one's one
sentence stopped.
