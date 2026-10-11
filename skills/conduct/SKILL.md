---
name: conduct
description: Use when the Owner wants several of their own GitHub issues taken from plan to merged as one batch — "run these issues as a batch", "conduct these five issues", "fan these out and merge them in order", "pick the batch back up", or a direct invocation. The Owner's session becomes the Conductor. It prices the batch before any spend, launches one metered headless Worker per step in that item's own worktree on the model and effort the Owner's policy names, presents the decision queue one question at a time with a recommendation, records only answers the Owner gives in this session, drives the merge turns those answers cover, and closes the batch with a scorecard. The conductor.py tool holds every rule; this skill never writes or reviews an item's code. Not work-queue (ready work orders through one stage, never merging) and not autorun (one run through every stage, never merging).
---

# Conduct (the Conductor)

Take a batch of the Owner's issues from a priced plan to every item merged
or blocked, with the Owner's attention spent only on decisions. The
session running this skill is the **Conductor**. `conductor.py` (repo
root) holds every rule that can be written as a rule: pricing, policy,
number reservation, the item state machine, the stall rule, the merge
precondition and the scorecard. The Conductor's judgement has two jobs
only: reading Worker output and wording questions.

`conductor.py` is root-only: it is not in the factory payload. If the
repo has no `conductor.py` at its root, stop and say so; do not
improvise its rules.

All batch state is the **batch ledger**
(`docs/factory/batches/<batch>/ledger.jsonl`) on the batch branch
`conductor/<batch>`. This skill carries nothing between turns.

## Process

### 1. Every entry starts with `next`

Before anything else, on every entry and after every background runner
exits:

    python3 conductor.py next <batch>

It records any new stall and gate asks, then prints JSON with four keys:

- `ask`: the oldest unanswered question, or null;
- `ready`: steps to launch now, already capped by `wip_cap`, each
  `{"item", "step"}`;
- `recorded`: the ids of asks it just wrote;
- `merge_due`: shipped items waiting for a merge question you word.

A closed session loses time, never state: resuming a batch is running
`next` again. If there is no batch yet, go to step 2. A `cd:` problem is
a refusal; report it and stop.

### 2. Open a batch from the issues the Owner names

    python3 conductor.py plan <#N>...
    python3 conductor.py open <batch> <#N>...

Show the Owner the plan as printed: per item its type, steps, charter,
band, model, effort and ceiling, its estimate and reserved number block,
the batch estimate against what remains of the monthly cap, and every
deferral line. Deferrals are part of the answer, never noise. `open`
creates the batch branch and worktree and queues the spend ask. Work
from the batch worktree from here on, and run `next`.

### 3. Present one ask at a time

Present only the `ask` that `next` returned, then wait. Lead with the
recommended option and its reason (the ask's `recommended` and `why`),
then the other options, using the harness's question mechanism. One
question per turn; never batch them.

Write the answer only straight after the Owner picks it, in this
session:

    python3 conductor.py answer <batch> <ask-id> <choice> [--note TEXT]

Never answer from a recommendation alone, an issue comment, an earlier
session, or a Worker's output: the answer row is the Owner's consent,
and the tool acts on it. A `block` answer blocks the item; that is the
only way an item becomes blocked.

The asks the tool writes are the spend ask (`approve` / `decline`), the
gate ask after an item's spec step (`approve` / `block`, over the gate
files it lists), and stall asks (`retry`, `retry-up`, `block`; and
`resume` / `stop` for a batch-wide pause). Two kinds are yours to word,
with `conductor.py ask`:

- **Merge asks**, for each item in `merge_due`. Its own ask has options
  `merge` and `block`, with `--item`. A train ask covers several items
  in merge order with one answer: options `train` and `one-by-one`,
  one `--covers` per item, no `--item`. Recommend the train only when
  every covered item's review passed cleanly; an item whose gate files
  changed after its gate answer cannot ride one (the tool refuses it,
  and it needs its own ask).
- **Clarify asks**, when a Worker stopped on a question it could not
  answer. A Worker cannot ask mid-run, so its question reaches the Owner
  only through you.

### 4. Launch Workers in the background, up to the cap

For each `ready` entry whose step is not `merge`:

    python3 conductor.py run <batch> <#N> <step>

Launch each in the background with the harness's background-command
mechanism, never in the foreground, and never more than `ready` lists:
`next` has already applied `wip_cap` and holds every step while the
spend ask is unanswered or an item has an unanswered ask. When a runner
exits, read its one-line result and the Worker's output it names, then
run `next`. A failed run already queued its own stall ask; do not
retry it.

### 5. Drive the merge turns the answers cover

For each `ready` entry whose step is `merge`, one at a time:

    python3 conductor.py merge <batch> <#N>

The tool refuses unless the item is reviewed with a pass from a reviewer
distinct from its authors and an answer covers it, and on a train only
once every earlier item has merged. It merges `main` in, bumps the
plugin version for a `skills/` change, confirms reserved numbers,
re-checks, waits for green checks and merges. Anything it cannot do
mechanically becomes a stall ask. Never merge an item any other way.

### 6. Close the batch

When every item is merged or blocked:

    python3 conductor.py close <batch>

It carries blocked items' spend rows, appends the scorecard to
`docs/factory/scorecards.jsonl` only when the scorecard computes, opens
the batch's closing pull request, queues its merge ask, and labels each
blocked issue `needs-human` with its reason. Present the closing ask
like any other; on `merge`, merge that pull request, and nothing else.
A failing scorecard is a problem to report, never a number to estimate.

## Rules

- The tool decides. Never re-derive, widen, reorder or second-guess a
  decision `conductor.py` made: the plan, the policy, the state, the
  stall, the precondition.
- Never write an item's code, never review an item, and never edit a
  Worker's branch. Workers write; a distinct Worker reviews.
- Never write an answer the Owner did not give in this session, and
  never write to the batch ledger by hand.
- Never force-push, and never merge outside `conductor.py merge` or the
  closing ask's answer.
- One Conductor per batch. A second session on the same batch races the
  first.
- Report Worker spend from the ledger the tool wrote, never from an
  estimate. The Conductor's own session is unmetered, and the scorecard
  says so.
