---
stage: architect
run: feature:orchestrator
date: 2026-10-10
ux: skipped — CLI and text artifacts only; the decision queue reuses the established one-question-at-a-time format, and plan, ledger and scorecard are text like every other run artifact
assumptions:
  - "Autorun-driven: no live interview. The trade-offs below were settled at this stage's own recommendation, and the one ADR this stage writes (ADR-0084) carries status provisional."
  - "PRD open question, decision queue home: the batch ledger's unanswered ask rows, read oldest first. No pinned issue, because an issue comment cannot be consent. Consent is the Owner's explicit answer in the session that then acts on it."
  - "PRD open question, Worker metering: each Worker run is one headless `claude -p --output-format json` process. Its result event's total_cost_usd is read by the existing cli.read_execution, the same reader `budget_guard record-run` uses. `claude --help` on CLI 2.1.296 (read 2026-10-10, no paid run) lists --model, --effort (low|medium|high|xhigh|max), --max-budget-usd and --output-format. It lists no max-turns flag, so of ADR-0034's three stops the Worker gets the dollar one and the wall-clock one."
  - "PRD open question, item type and policy home: an item type is the charter a step runs under. Its charter's `route:` band resolves the model through factory.json's existing `routing` table and the effort through one new optional `effort` table beside it."
  - "PRD open question, stall rule: escalate on the first failed Worker run with no automatic retry. A second reviewer request for changes stalls the item (the first gets one automatic fix step). Stalls also come from a non-mechanical merge-turn failure, a dead runner, or no state change for twice the step's wall-clock limit. Three consecutive Worker failures pause the batch (work-queue's circuit breaker)."
  - "The Owner's explicit in-session answer, executed by the Conductor, counts as ADR-0036 condition 3's human merge. That is how merges ran on 2026-10-07, and PRD-0013's Solution says consent is confirmed in the Owner's session. One answer may cover an ordered merge train. A gate-path PR rides a train only when its gate files are byte-identical to what the Owner approved at that item's gate asks. Flagged for the Owner, since it touches how gate 3 is given. If the Owner rejects it, every gate-path PR gets its own merge question and nothing else changes."
  - "The merge-queue question stays the Owner's (PRD-0013 open questions). The merge turn checks for a queue at merge time and takes whichever path exists."
  - "The merge turn updates an item branch by merging origin/main into it, not by the rebase PRD story 6 names. A rebase needs a force-push, which the permission classifier refuses. Squash-merge lands the same tree either way."
  - "conductor.py stays root-only in v1 and is not mirrored into the factory payload: PRD-0013 covers one repository. Mirroring waits for a stamped repo to run a batch."
  - "An uncommitted earlier architect draft for this run sits in worktree .claude/worktrees/agent-a69e0f4d056b70568 (written 18:09 2026-10-10, never committed or pushed). It holds an architecture.md and uncommitted ADR files numbered 0084 and 0085. This stage read it as prior art and kept its sound analysis (headless metering, issue-keyed spend, reservation blocks, merging main in). It did not adopt the draft whole. This branch takes ADR-0084 because no branch or PR holds that number. The Owner should discard that worktree, or renumber its files if they are ever committed."
---

# Architecture: the Conductor, a batch orchestrator

## Approach

The Conductor is **one utility skill, `conduct`, plus one stdlib root tool,
`conductor.py`**. The Owner's own session runs the skill and so becomes the
Conductor. The tool holds every rule that can be written as a rule:
pricing, policy lookup, number reservation, the item state machine, the
stall rule, the merge precondition and the scorecard. That leaves the
Conductor's judgement with two jobs, reading Worker output and wording
questions. A Worker is **one headless harness process per step of one
item**, each in that item's own git worktree. `conductor.py run` launches
it with the model, effort and dollar ceiling the Owner's policy names.
Headless runs are the one path where the harness reports dollars and the
model and effort are command-line facts that can be checked afterwards.
All batch state is **one append-only JSONL batch ledger**. The decision
queue is that ledger's unanswered asks, presented one at a time. The work
itself is done by what already exists:

- `autorun` drives a run's spec stages;
- `implement` and the SWE charter build one work order;
- the reviewer charter reviews;
- `cli.read_execution` meters;
- `cost_ledger` records spend;
- `factory_config` resolves policy;
- `work_queue.month_to_date` prices against the cap;
- `knowledge_plane` finds the numbers already in use.

Three other shapes were compared, and each loses:

- **A dynamic workflow** holds the plan in a script and sets the model per
  stage. But it takes no human input mid-run, it is a research preview,
  and it is not stdlib Python.
- **Every Worker through the assembler** would be metered and
  credential-safe. But it runs serially per label event, knows only work
  orders, and cannot run a spec stage that has no work order yet.
- **Extending `work-queue`** breaks that skill's contract: many work orders
  through one stage, and never a merge.

## Components

### `conduct` skill (`skills/conduct/SKILL.md`)

- Responsibility: the Conductor's procedure. It is the only component that
  talks to the Owner. It:
  - opens a batch from the issues the Owner names;
  - asks the plan's spend question;
  - keeps Workers launched up to the concurrency cap;
  - presents pending asks one at a time, recommended option first, with the
    reason;
  - records each answer;
  - drives the merge turns the answers cover.

  It never writes an item's code, never reviews an item, and never
  re-derives a decision the tool made (work-queue's "the planner decides"
  rule). Its body stays harness-neutral. Launching a runner in the
  background and asking a question both name the mechanism, not one
  harness's tool.
- Kind: a utility skill (ADR-0023). It is invoked directly, owns no run
  artifact and is never routed to. It is named `conduct`, not `batch` (a
  harness built-in) and not `conductor` (a marketed product). "Conductor"
  stays the role name.
- Resume: the skill carries nothing between turns. Every entry runs
  `conductor.py next` first, so a closed session loses time, never state.
- Collaborators: `conductor.py`, and `gh`/`git` for merges under an answer
  only.

### `conductor.py` (new root tool, the batch ledger's one owner)

It follows `work_queue.py`'s conventions: pure functions with every input
passed in, a thin `main`, `cd:`-prefixed problem strings, and `cli.report`
for the exit. Each subcommand owns one capability:

- **plan** `<#N>...`: price and order the batch and reserve its numbers.
  It writes nothing. Pure apart from the issue reads and the read of the
  ids in use on `origin/main`.
- **open** `<#N>...`: create the `conductor/<batch>` branch and worktree
  from `origin/main`, write the `plan` and `reserve` rows, and queue the
  spend ask.
- **next** `<batch>`: return the oldest unanswered ask, the steps ready to
  launch under the `wip_cap` slots, and any newly detected stalls, which it
  records as asks.
- **run** `<batch> <item> <step>`: one Worker run, from brief to metered
  rows. The skill launches it in the background.
- **ask** / **answer** `<batch> ...`: the decision queue's two writes.
- **merge** `<batch> <item>`: one merge turn. Refused unless an answer row
  covers the item.
- **close** `<batch>`: carry blocked items' spend rows, append the
  scorecard, commit, and queue the closing merge ask.
- **scorecard** `<batch>`: pure over the ledger. Fails loudly.

If the file grows past the repo's 800-line ceiling, Decompose may split it
by capability into sibling tools that import its row grammar. The grammar
keeps one owner.

### Worker runner (`conductor.py run`)

- Responsibility: turn one ledger step into one metered, policy-bound
  headless run. In order, it:
  1. composes the brief;
  2. spawns the harness under `cli.harness_run`, which owns the process
     group and the wall-clock kill;
  3. keeps the final result event;
  4. reads tokens and cost with `cli.read_execution`;
  5. appends the spend row to the item branch's `costs.jsonl`;
  6. pushes the item branch and opens or updates its PR from the Worker's
     uncommitted `pr-body.md`, the ADR-0077 hand-off shape: the Worker
     commits and the Conductor pushes;
  7. appends `run` and `state` rows.

  Any outcome other than a completed run with its expected output appends a
  stall ask instead of retrying.
- Collaborators: `cli`, `cost_ledger.entry`/`append`,
  `assembler.select_charter`/`charter_band`/`PR_BODY_FILE`,
  `orientation_pack`, `factory_config`.

### Policy (`factory.json`)

- Responsibility: the Owner's written model-and-effort policy.
  - `routing` (band to model, ADR-0034) stays the one home of model ids.
  - One new optional table, `effort` (band to `low` | `medium` | `high` |
    `xhigh` | `max`), sits beside it.
  - A step's band comes from its charter's `route:` frontmatter
    (`assembler.charter_band`).

  The chain is step, charter, band, then (model, effort). Every link but
  `effort` exists today.
- Collaborators: `factory_config.resolve_effort`, new, fail-closed like
  `resolve_model`. `config_problems` validates the table's values when the
  table is present. Detector F reads it.

### Reservation (inside `plan`, `open` and `merge`)

- Responsibility: no two items in a batch, and no item and `main`, hold the
  same shared number.
  - Before dispatch, each item gets a block of PRD, ADR and WO numbers. The
    block starts above the highest number in use on `origin/main` (read
    through `knowledge_plane.parse_run` and the token grammars) and above
    every block already reserved.
  - At each merge turn, every reserved number the item used is confirmed
    still free on `origin/main`.

  The plugin version and the template manifest are **write slots**, not
  numbers. Workers never edit `.claude-plugin/plugin.json`'s version and
  never regenerate the manifest, except to keep their own branch green. The
  Conductor does both, single-threaded, at the merge turn.
- Collaborators: `knowledge_plane`, `factory_init.py update-manifest`.

### Merge turn (`conductor.py merge`)

- Responsibility: land one reviewed item so that `main` is never green
  alone and red together. The steps, in order:
  1. merge `origin/main` into the item branch;
  2. resolve only mechanical conflicts: `costs.jsonl` by union (a new
     `.gitattributes` `merge=union` line) and the manifest by regeneration;
  3. bump the plugin patch version from `main`'s value if the item touched
     `skills/`;
  4. confirm the item's reservations;
  5. run `make check`;
  6. push, never forced;
  7. wait for the PR's checks on the new head;
  8. merge with `gh pr merge --squash`, or enqueue when
     `mergeQueue(branch: "main")` is non-null, and wait for merged or
     ejected.

  Anything non-mechanical stops the turn and becomes a stall ask.
- Collaborators: `gh`, `git` (`cli.runner`, `cli.gh_read`), answer rows.

### Scorecard (`conductor.py scorecard`, `close`)

- Responsibility: compute one batch's numbers from ledger rows alone and
  append them to `docs/factory/scorecards.jsonl`, append-only under the
  `evals/results/` discipline.
- Collaborators: the batch ledger, `cost_ledger.read`.

### Supporting edits to existing files

- `cost_ledger.line_problems`: the `wo` field admits an issue key
  `#<n>` beside `WO-####` (ADR-0084).
- `factory_config`: `resolve_effort`, plus the `effort` value rule in
  `config_problems`.
- `skills/autorun/SKILL.md`: honours a `stop-after: <stage>` line in
  `autorun-brief.md`, so a spec Worker drives a run up to a gate and stops
  there.
- `.gitattributes`: `docs/factory/costs.jsonl merge=union`.
- `CONTEXT.md`: Conductor, Worker, batch, batch ledger, decision queue,
  merge train.
- `protocol.UTILITY_SKILLS`, plus the README, LEDGER and plugin surfaces
  that lint requires for a new skill.

## Data model

The PRD requires these reads and writes, and they chose the shape:

- append a row on every state change, from several processes, to one file;
- read one batch's whole history in order (for `next`, resume and the
  scorecard);
- find the oldest unanswered ask;
- join a run to its spend;
- append one scorecard per batch.

Every one is a sequential scan of a small file. So JSONL with a locked
append is the whole storage design, the same shape as `costs.jsonl`.

Consistency, per interaction:

- an answer row is durable before the action it authorises (the tool writes
  first, then acts);
- concurrent runners serialise appends with an exclusive `fcntl.flock` on
  the ledger;
- a `run` row may lag its process by seconds;
- the scorecard is computed once, after the last merge.

### Batch ledger (`docs/factory/batches/<batch>/ledger.jsonl`)

It lives in the Conductor's worktree on `conductor/<batch>` and reaches
`main` through the closing PR. Workers never see it. Every row has `at`
(UTC ISO timestamp, seconds), `kind`, and `item` (`#<n>`, or null for a
batch-level row).

| kind | fields |
|---|---|
| `plan` | `batch`, `items`: [{`item`, `type` (feature / fix / order), `size`, `steps`: [{`step`, `charter`, `band`, `model`, `effort`, `ceiling_usd`}], `estimate_usd`, `after`}], `policy` (a snapshot of `routing` and `effort`), `estimate_usd`, `month_to_date_usd`, `cap_usd` |
| `reserve` | `what` (prd / adr / wo / plugin-version), `values`, `renumbered_from` (only on a merge-turn collision) |
| `state` | `from`, `to`, `reason`; when `to` is `reviewed`: `verdict`, `author_runs`, `reviewer_run`; when `to` is `merged`: `pr`, `sha`, `checks` |
| `run` | `step`, `charter`, `band`, `model` (passed), `models_reported`, `effort`, `run_id`, `pid`, `outcome` |
| `ask` | `id`, `kind` (spend / gate / merge / stall / clarify), `question`, `options`, `recommended`, `why`, `covers` (ordered items, for a merge train), `gate_blobs` (for a gate ask) |
| `answer` | `ask`, `choice`, `note` |
| `close` | `merged`, `blocked` |

The final result event of each run is kept beside the ledger as
`runs/<run_id>.json`, the evidence behind the spend row.

**Item states:**

```
planned → spec → awaiting-gate → build → verify → review → reviewed → ship → merging → merged
```

- `stalled` is reachable from any non-terminal state.
- `blocked` is terminal, carries a reason, and is reachable only through an
  answer.
- A `fix` item skips the gate states its re-entry depth does not reach.
- An `order` item (an existing `wo:ready-for-agent` work order) starts at
  `build` and is claimed first with `make wo-in-progress`, as in
  `work-queue`.

**Steps to charters.** `conductor.py` fixes this table the way
`assembler.CHARTER_BY_TYPE` fixes type to charter:

| step | charter | detail |
|---|---|---|
| `spec` | `architect` | autorun up to the next gate stage |
| `build` | `assembler.select_charter(issue labels)` | one run per work order |
| `verify` | `qa` | |
| `review` | `reviewer` | |
| `ship` | `qa` | prepares `release.md` only |

**Invariants and their owners.** The state machine owns these:

- no `merging` without a covering answer;
- no Worker step while the item has an unanswered ask;
- no `reviewed` pass when the reviewer's `run_id` is among the author runs.

The reservation step owns "no number in two blocks". The ledger grammar
owns "every row parses": it fails the reader and never skips the row.

### Spend row (`docs/factory/costs.jsonl`, ADR-0034 fields unchanged)

There is one row per Worker run, written on the item branch so that it
merges with the breakdown row that detector G checks it against.

- `wo` is the work order a build step implements, or `#<n>` (the item's
  issue) for every other step (ADR-0084).
- `run_id` is `conductor-<batch>-<item>-<step>-<seq>`.
- `model`, `tokens` and `cost` come from the result event.
- `outcome` is `completed`, `agent-failed`, or `killed:cost-at-ceiling`. A
  wall-clock kill leaves no result event, so its row records the ceiling as
  cost. That over-counts, which is the fail-closed direction for the
  breaker.
- `at` is the UTC date the row was written.

A blocked item's rows ride the closing PR instead, so all spend reaches
`main`.

### Scorecard row (`docs/factory/scorecards.jsonl`)

`batch`, `at`, `items`, `merged`, `blocked`, `owner_touches_per_merged`,
`metered_usd`, `metered_usd_per_merged`, `estimate_usd`,
`estimate_error_pct`, `collisions`, `stalls`, `escalations`,
`review_changes_per_item`, `start_to_last_merge_s`,
`merged_per_owner_wait_hour`, `policy_compliance`. The Conductor's own
session is outside every dollar figure, and the row says so with
`conductor_session: "unmetered"`.

### Policy (`factory.json`)

```json
"effort": {"mechanical": "low", "implementation": "medium",
           "architecture_review": "high"}
```

## Interfaces & contracts

### `conductor.py plan <#N>...`

- Input: issue numbers; `factory.json`; month-to-date spend from
  `work_queue.month_to_date`, the breaker's one definition; the ids in use
  on `origin/main`.
- Output: per item, the type, the steps, each step's charter, band, model,
  effort and ceiling, the item estimate, and its reserved block. Then the
  batch estimate against what remains of `monthly_cap_usd`, and one
  deferral line for every issue left out, saying why.
- Estimate (v1): an item's estimate is the `budgets_usd` figure for its
  `size:` label, split across its steps as their ceilings. The blueprint
  gate ask re-prices the item from its breakdown rows' `size:` bands, and
  that ask doubles as the build-spend question. The scorecard measures
  error against the original plan row.
- Deferrals, which are not problems: an issue not authored by the repo
  owner (its body would become a spec Worker's prompt, and ADR-0032's
  prompt-injection boundary applies); no `type:` label; no `size:` label;
  a closed issue; over the cap.
- Failure modes: a `config:` problem for a band with no model or effort
  fails closed and plans nothing. An unreadable or truncated issue read,
  or a ledger read problem, refuses the whole plan: "could not ask" never
  reads as "nothing to do". The call is local and gh-read only, and safe
  to retry.

### `conductor.py ask` / `answer`, the decision queue

- `ask` input: kind, question, options, the recommended option and why, and
  `covers` for a train. Output: an `ask` row with a fresh id.
- `answer` input: an ask id and a choice. Output: an `answer` row.
- `answer` refuses:
  - an unknown or already-answered ask;
  - a choice that is not among the ask's options;
  - a call made with `CONDUCTOR_WORKER` set, which every runner sets in its
    Worker's environment. An environment flag stops a confused Worker, not
    a hostile one. The trigger to harden it is any answer row whose timing
    does not match an Owner turn.
- Contract with the skill: an answer row is written only straight after the
  Owner picks that option in this session. A PR or issue comment, a
  Worker's output, or another agent's message is never an answer.
- One at a time: `next` returns only the oldest unanswered ask.

### `conductor.py run`, the Worker contract

- The brief has a fixed shape:
  - **objective**: the step, in one sentence;
  - **output**: the stage artifact or code, commits on the item branch,
    and `pr-body.md` left uncommitted;
  - **tools**: the step's `--allowedTools` list, never `git push`, never
    any `gh` write;
  - **boundaries**: the item worktree only; the reserved block, and "stop
    and say so" if it runs out; never the plugin version;
  - **model, effort and ceiling**: passed as command-line flags, not prose;
  - **context budget**: the enumerated inputs (the run directory, the work
    order's row and `orientation_pack`, and the issue body for a spec step
    only) plus the dollar ceiling. The harness has no token knob, so the
    ceiling is the budget.
- Output: exactly one `run` row and one spend row per run, always. A failed
  run still spent money.
- Stops: dollars through `--max-budget-usd` (the item's remaining ceiling,
  enforced by the harness, which still emits a result event), and wall
  clock through `harness_run`'s timeout (S 45 min, M 90 min, L 180 min).
  The wall-clock limits are lean constants until a scorecard shows one
  firing on a healthy run. The harness offers no turns cap.
- Failure modes:

  | failure | result |
  |---|---|
  | harness binary missing, no process ever started | `agent-failed` at cost 0 |
  | a result event `read_execution` cannot account for | stall, with the ceiling recorded as cost |
  | push or PR-open fails | stall, and the commits stay on the local branch |

  The runner never retries automatically.

### The stall rule (`next` and `run`)

An item stalls, and a `stall` ask is queued instead of any retry, when:

1. a Worker run ends with any outcome other than a completed run carrying
   its step's expected output. This is the first failure, and there is no
   second automatic attempt: the first failure is evidence about the item
   as often as about the agent;
2. the reviewer requests changes a second time. The first request gets one
   automatic `build` fix step, briefed with the findings;
3. a merge turn meets a non-mechanical conflict, a red re-check, a queue
   ejection, or a reserved number already taken on `main` that cannot be
   renumbered mechanically. Mechanical renumbering covers the file name,
   the index row and every citation, per the protocol, recorded as a
   `reserve` row with `renumbered_from`;
4. a runner's pid is gone with no finishing `run` row, or the item has had
   no state change for twice its step's wall-clock limit.

The stall ask's options are fixed:

- retry on the same policy;
- retry one band up, which is the Owner's choice and never the Conductor's;
- block with a reason.

Three consecutive Worker failures across the batch pause all dispatch
behind one ask.

### `conductor.py merge <batch> <item>`

- Precondition, enforced in code:
  - the item is `reviewed` with a pass verdict from a reviewer run
    distinct from every author run;
  - an answer covers the item: either its own merge ask, or a train ask
    whose `covers` lists it, answered with the train option, with every
    earlier item in that train already merged.
- Gate-path rule: a PR touching `docs/adr/**`, a run's `prd.md` or
  `architecture.md`, or `docs/design/**` rides a train only when those
  files' blob ids equal the `gate_blobs` the Owner answered at that item's
  gate asks. Otherwise it needs its own merge ask (ADR-0036 condition 3).
- Waits: checks on the new head time out after 30 minutes, which raises a
  stall. A queue wait has the same limit.
- Failure modes: always a stall ask, with the branch left as pushed. Never
  a partial merge, a forced push, or a retry.

### `conductor.py scorecard` / `close`

- `scorecard` output: the scorecard row, from ledger rows alone.
  - It fails when a ledger line does not parse, when a line breaks its
    kind's field rules, when a `run` has no `costs.jsonl` row with the same
    `run_id`, or when the `plan` row is missing. Each failure is a `cd:`
    problem string naming the file and line. The tool exits nonzero and
    appends nothing.
  - `merged_per_owner_wait_hour` applies ADR-0080's formula to the batch:
    merged items, over the summed ask-to-answer wait of every Owner
    question. It is not the repo-wide ADR-0080 figure, which reads mirror
    labels and so cannot come from ledger rows alone.
  - `policy_compliance` counts runs whose passed model and effort match the
    plan row's policy snapshot for that step's band, and whose reported
    models include the passed model, over all runs.
- `close`: appends blocked items' spend rows, runs `scorecard`, appends the
  row only on success, commits the ledger, run evidence and scorecard on
  the conductor branch, opens its PR, and queues its merge ask.

## Stack & dependencies

- Python 3 standard library only (`stdlib-only`), including `fcntl` for the
  append lock. That lock is POSIX-only, which is acceptable: every harness
  this repo supports runs on POSIX.
- The harness's headless CLI is the Worker runtime. It is already behind
  `cli.harness_run` for `trigger_eval.py` and `charter_replay.py`. It is a
  volatile vendor surface, so every flag is composed in one function.
- `gh` and `git` run through the existing `cli` ports.
- Git worktrees isolate items. This is the existing pattern for parallel
  agents.
- GitHub's merge queue is used when present and never required.

## Decisions & alternatives

- **A skill plus one stdlib tool** over a dynamic workflow: workflows take
  no mid-run human input, are a preview, and are not stdlib
  (`stdlib-only`).
- **Headless Worker processes** over in-session subagents: subagents report
  tokens, not dollars, and their model and effort cannot be checked
  afterwards. What it costs: a Worker cannot ask mid-run. It stops, and the
  Conductor queues the question.
- **Workers launched by the Conductor's session** over the assembler: the
  assembler is serial per label and knows only work orders. It stays the
  unattended cloud path for single work orders.
- **The Conductor advances while its session is open** over a
  self-advancing daemon: the session wakes when a background runner exits.
  A closed session pauses the batch, and resume is `next`. The trigger to
  move scheduling into the runner is a batch that sat idle because a
  session closed.
- **The decision queue in the batch ledger** over a pinned issue (the gate
  digest pattern): an issue comment cannot be consent, so the issue would
  be a second, non-authoritative copy.
- **One answer may cover an ordered merge train** over one question per
  merge: per-merge questions multiply Owner touches, which is the number
  the PRD drives down. The train stops at the first item that needs more
  than a mechanical update. This is a procedure inside one tool and is
  reversible, so it gets no ADR. It is flagged in `assumptions:` for the
  Owner.
- **Merge `main` into the branch** over the PRD's rebase: a rebase needs a
  force-push, and squash-merge makes the landed tree identical either way.
- **Reserved blocks per item before dispatch** over assigning numbers at
  merge: renumbering after review edits prose that was already reviewed.
  Blocks leave gaps in the sequence, and detectors C and D do not object to
  gaps.
- **Plugin version bumped by the Conductor at each merge turn** over a
  version reserved per item, or one bump at close: per-item versions
  collide whenever merge order differs from plan order, and a bump at close
  leaves `main` carrying unbumped `skills/` changes between merges.
- **Spend stays in `costs.jsonl`, keyed by issue when no work order
  exists** over a second spend file. With two homes for spend, the monthly
  breaker cannot see batch spend (ADR-0084). The one-way mirror is
  untouched: no work-order issue is created (`adr0032-one-way-mirror`).
- **"Item type" means the step's charter** over a new taxonomy: `type:`
  labels, charters and bands already route models. The only new policy
  surface is the `effort` table.
- **Parallel worktrees with sequential merges** over predicting file
  overlap at plan time: worktrees make concurrent writes to one tree
  impossible, and the sequential re-check catches overlap at merge time. An
  Owner-declared `after:` edge serialises two items when overlap is already
  known.
- **Only owner-authored issues enter a batch**: the spec step's prompt is
  the issue body, and ADR-0032 keeps attacker-controllable text out of
  prompts.
- **Root-only tool** over mirroring it into the payload now: the PRD covers
  one repository, and a mirror costs a manifest regeneration and payload
  tests that no batch needs yet.
- **Typed ids stay in run-artifact frontmatter**
  (`adr0004-typed-ids-in-frontmatter`): the reservation block is a ledger
  row, never a parallel id registry.

### Accepted behaviour changes (ADR-0084's grammar change)

The old and new `cost_ledger.line_problems` rules were compared over the
inputs where they differ: `wo` values that match `#[1-9][0-9]*`, which the
old rule rejects and the new rule admits. Every other value gets the same
verdict from both rules.

- Detector G passes a row whose `wo` is `#<n>`. It used to fail it.
- `cost_ledger.wo_token` still returns None for such a row. So G's "a
  recorded order has a breakdown row" check, G's "a merged order has a row"
  check, and ADR-0080's dispatched set all skip it.
- `cost_ledger.dispatched`, and through it `work_queue.month_to_date`, now
  counts the row against the monthly cap. That is the point of the change.
- `cost_report`'s `by_wo` and `dashboard.py`'s per-order spend group
  issue-keyed rows under their own `#<n>` keys beside work orders. They
  should label those keys as issues.

## Traceability

| PRD requirement | Component(s) |
|---|---|
| Story 1: a priced plan before any spend | `plan`; `open` queues the spend ask |
| Story 2: a durable queue, one ask at a time, consent in session | `ask` and `answer` rows; `next` returns the oldest; `answer`'s refusals |
| Story 3: the plan plus a row for every state change | `plan` and `state` rows |
| Story 4: reserve shared numbers before dispatch | Reservation (blocks, write slots, merge-turn confirmation) |
| Story 5: a fixed brief, with model and effort from policy | the Worker brief; Policy (step, charter, band, then `routing` and `effort`) |
| Story 6: independent review, green checks, merges in order | the `review` step on the reviewer charter; `merge`'s precondition and both paths |
| Story 7: every item merged or blocked; stalls escalate | the item state machine; the stall rule; `blocked` only through an answer |
| Story 8: a scorecard per batch, with append-only history | `scorecard`; `close`; `scorecards.jsonl` |
| SC 1: every Owner action is an answer, and is logged | `answer` rows are the only Owner writes |
| SC 2: zero collisions | Reservation; `reserve` rows, where `renumbered_from` counts as a collision |
| SC 3: a metered row per run; the estimate within ±50% | the runner's spend row via `read_execution`; the `plan` estimate; `estimate_error_pct` |
| SC 4: timestamped states; the final state matches GitHub | `state` rows; `merged` records the sha `gh` returned; a blocked item's issue gets `needs-human` and a reason comment |
| SC 5: a distinct writer and reviewer; green checks on the merge commit | the `reviewed` row; `merge`'s precondition; the `merged` row's `checks` |
| SC 6: 100% policy compliance | `run` rows against the plan's policy snapshot; `policy_compliance` |
| SC 7: a scorecard from ledger rows alone that fails on a malformed row | `scorecard`'s grammar check and `run_id` join |
| Out of scope | one worktree per item; one Conductor per batch; `merge`'s precondition; one repository per batch; Workers call the existing skills; stdlib; text only; models from policy |

## ADRs

- [ADR-0084](../../adr/0084-the-cost-ledger-keys-a-run-by-issue-when-it-has-no-work-order.md):
  the cost ledger keys a run by its issue when it has no work order.
  Provisional; amends ADR-0034.

## Amendments (implement-time, Owner-accepted)

2026-10-10. Implement rows 0157 and 0158 met nine questions this design
left open. The Owner accepted these answers via the orchestrator's
question; breakdown.md's Notes hold the full text.

1. **Launch record.** `run` appends a `state` row entering the step,
   with optional `run_id` and `pid` (the runner's pid), before it spawns
   the Worker. The one `run` row at the end is the finishing row. A dead
   launch pid with no `run` row of its `run_id` is a stall.
2. **Readiness.** An item stays in a step's state until the next launch
   moves it. A step is done when its finishing run completed. An item is
   ready when it is `planned`, `reviewed` or in a finished step, with no
   unanswered ask.
3. **Gate asks.** A completed `spec` run moves the item to
   `awaiting-gate` and queues a `gate` ask (`approve` / `block`) whose
   `gate_blobs` are the blob ids of the gate paths the item branch
   changes. `approve` makes `build` ready.
4. **Fix depth** is inferred from those gate paths: a fix that changes
   none skips `awaiting-gate`.
5. **Review verdict** is a `verdict: pass|changes` line in the run's
   `review.md` frontmatter; the brief overrides the reviewer charter's
   comment, label and merge exit.
6. **Answers act.** `answer` writes the `blocked` state row for a
   `block` answer. Stall options are `retry`, `retry-up` (the next band
   up, omitted on the top band) and `block`. The three-failure pause is
   an item-less stall ask, `resume` / `stop`.
7. **Build runs** take the first unchecked row of the item branch's
   `breakdown.md`; an order item's work order comes from its issue.
8. **Item branch** `conductor/<batch>-<n>`, worktree
   `.claude/worktrees/conductor-<batch>-<n>`, from `origin/main`.
9. **Runner defaults:** a fixed `--allowedTools` list with no push and
   no gh write; `--max-budget-usd` is the step's `ceiling_usd`; `seq`
   counts that step's runs; the spend row is committed on the item
   branch before the push; a completed run with no `pr-body.md` stalls;
   the spec brief carries `stop-after: decompose`.
