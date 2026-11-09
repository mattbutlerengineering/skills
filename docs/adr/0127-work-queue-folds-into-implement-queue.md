# work-queue folds into implement-queue

- Status: accepted
- Date: 2026-11-08

The README's "Driving a run" card listed four skills: `autorun`,
`work-queue`, `conduct` and `implement-queue`. Two of them did the same
job. `work-queue` and `implement-queue` both claim a batch, dispatch one
worker per item in one message with one worktree each, stop the round
after three consecutive failures, and stop at PRs. implement-queue's
default `merge: off` was already work-queue's never-merge rule. The two
differed only in where items come from: work-queue read ADR-0032's two
planes (an unchecked breakdown row and a `wo:ready-for-agent` mirror),
and implement-queue reads a `ready` label.

On 2026-10-25 the Owner deferred this fold until a routing eval showed
confusion between the two (the backlog seed this ADR consumes). On
2026-11-08 the Owner asked for the dedupe directly, together with a
written reason for each surviving skill. That request overrides the
deferral. No routing eval has run on these cases yet.

## Decision

`work-queue` is retired. implement-queue's queue profile gains a
`source` key: `issues` (the default, unchanged behaviour) or
`work-orders`. An invocation that asks for work orders overrides the
profile for that run. Work-queue's distinctive mechanics move, mostly
verbatim, to `skills/implement-queue/references/work-orders.md`: the
`work_queue.py plan` batch, the `make wo-in-progress` claim and
`make wo-failed` release, the work-order worker brief, the
`budget_guard.py record` spend row and the assembler cloud fallback.

Three rules keep the fold from loosening a gate:

- `source: work-orders` forces `merge: off`, whatever `merge:` says. A
  work order's merge stays the human's (ADR-0033 gate 3).
- Issues mode never claims an issue carrying a `wo:*` label, so the two
  sources cannot race for one issue.
- `work_queue.py` stays as the planner, with its `factory.py work-queue`
  subcommand. Conductor imports its `month_to_date`, and the reference
  calls its `plan`.

Each surviving skill answers a different question, recorded in the
README's "Driving a run: which one" table, which is the only copy:

- `autorun`: one run through every stage, from a brief collected once.
- `conduct`: many issues through merge, with the Owner present to answer
  each decision.
- `implement-queue`: many ready issues or work orders, with nobody
  present.

## Consequences

- The routing eval set changes because the roster changes, not to make
  a case pass. The three `work-queue-N` cases and
  `work-queue-vs-autorun-1` now expect `implement-queue`. The three
  adjacency cases that named the retired skill were renamed after
  implement-queue. `implement-queue-vs-work-queue-1` was dropped,
  because it now duplicates `implement-queue-work-orders-3`. Recorded
  results under the old ids stay as they were.
- The `work-queue` LEDGER row is gone. It was draft with no evidence.
- Installed plugin caches keep serving the old skill until the next
  release PR moves the version (ADR-0095).
- `conduct` and `implement-queue` still each describe a serial merge
  train. That overlap is left alone here.
