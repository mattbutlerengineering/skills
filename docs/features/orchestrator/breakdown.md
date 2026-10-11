---
stage: decompose
run: feature:orchestrator
date: 2026-10-10
assumptions:
  - "Autorun-driven: no live review of the cut. The milestone boundaries and row sizes below are this stage's recommended default, taken without user input."
  - "Work-order ids start at 0153: the highest on origin/main is 0152 (docs/features/lean-in-the-build/breakdown.md); open PR #670 (this run's architecture) carries none; no local worktree breakdown carries one above 0152; no GitHub issue is titled with one (checked 2026-10-10)."
  - "No tracker mirror: no WO-#### issue is created for any row (ADR-0026, ADR-0032 one-way dispatch, and the brief: this run creates none unattended). Mirroring the rows is the Owner's step."
  - "Owner-session ledger policy (as in docs/features/lean-in-the-build/breakdown.md): each row checked off in Implement appends one zero-cost row to docs/factory/costs.jsonl via budget_guard record, so detector G holds."
  - "One plugin version bump, in the packaging row (row 0164), covers both skills/ changes this run makes (autorun's stop-after line and the new conduct skill): Implement lands as one PR per autorun stage, so one bump reaches main with both."
  - "conductor.py starts as one file. Architecture lets Decompose split it by capability; the default is to split only if Implement pushes it past the 800-line ceiling, into sibling tools that import conductor.py's row grammar, logged under Notes. The grammar keeps one owner either way."
  - "No row runs a paid model. Every Worker, gh and git call in the tests goes through an injected fake (cli's ports). PRD-0013's success criteria are checked on a real batch of four or more issues; that is Verify's, deferred pending the Owner's spend consent, and no row claims it."
  - "Architect's merge-train assumption (one answer covers an ordered train; a gate-path PR rides it only when its gate blobs match) is implemented as designed in row 0160 and stays flagged for the Owner. If the Owner rejects it, row 0160 drops the train branch of the precondition and nothing else changes."
---

# Breakdown: the Conductor, a batch orchestrator

Progress lives in the checkboxes below. Implement checks items off as their
acceptance criteria are met. Rows follow the house grammar: a repo-global
work-order id, size class, blocking edges, and the PRD citation. No tracker
mirror for this run (ADR-0026). Every row is test-first: the `Accept:`
line's behaviour is pinned by a unit test through the public interface
before the code exists, and problem strings are asserted exactly.

Every `conductor.py` row follows `work_queue.py`'s conventions: pure
functions with every input passed in, a thin `main`, `cd:`-prefixed problem
strings, `cli.report` for the exit, and `gh`/`git`/harness calls through
`cli`'s ports so tests inject fakes.

## Milestone 1: Policy and spend accept a batch (the existing ledgers know about the Conductor)

- [x] **WO-0153** Cost ledger admits issue-keyed rows (ADR-0084) — size:S, blocked by: — (PRD-0013 §Success criteria, §Problem statement)
  - Accept: `cost_ledger.line_problems` admits a `wo` of `#<n>` matching `#[1-9][0-9]*` and keeps rejecting every other non-`WO-####` value (`#0`, `#`, `12`, `#12a` each still return their existing problem string); `cost_ledger.wo_token` returns None for an issue-keyed row; `cost_ledger.dispatched`, and through it `work_queue.month_to_date`, counts the row's cost; `cost_report`'s `by_wo` and `dashboard.py`'s per-order spend show `#<n>` keys labelled as issues, beside work orders; detector G passes a fixture ledger holding an issue-keyed row and still fails one holding `wo: "12"`. `factory_init.py update-manifest` is re-run because `cost_ledger.py` and `cost_report.py` are mirrored. ADR-0084's status is unchanged.
- [x] **WO-0154** Effort policy beside routing — size:S, blocked by: — (PRD-0013 §User stories, §Open questions)
  - Accept: `factory_config.resolve_effort(band, config)` returns `(effort, [])` for a band in the `effort` table and fails closed with a `config:` problem string, in `resolve_model`'s shape, for a missing table or band; `config_problems` reports an `effort` value outside `low` / `medium` / `high` / `xhigh` / `max` and is silent when the table is absent; detector F's selftest fails on a planted bad effort value; `factory/templates/factory.json` gains the architecture's `effort` table (mechanical low, implementation medium, architecture_review high) and the manifest is regenerated.

## Milestone 2: A batch can be planned, opened and asked about (no Worker yet)

- [x] **WO-0155** Batch ledger grammar and the decision queue — size:M, blocked by: — (PRD-0013 §User stories, §Success criteria, §Actors)
  - Accept: `conductor.py` owns the row grammar of architecture.md's batch-ledger table (`plan`, `reserve`, `state`, `run`, `ask`, `answer`, `close`, each with `at`, `kind`, `item`); appends take an exclusive `fcntl.flock` on `ledger.jsonl`; the reader fails with a `cd:` problem naming file and line for a line that does not parse or breaks its kind's field rules, and never skips it. `conductor.py ask` writes an `ask` row with a fresh id; `answer` writes an `answer` row and refuses an unknown ask, an already-answered ask, a choice not among the ask's options, and any call with `CONDUCTOR_WORKER` set, each with its own exact problem string; `next` returns only the oldest unanswered ask.
- [x] **WO-0156** Priced plan, reserved blocks, and opening a batch — size:M, blocked by: WO-0154, WO-0155 (PRD-0013 §User stories, §Success criteria, §Solution)
  - Accept: `conductor.py plan <#N>...`, given injected issue reads, a config and month-to-date spend, prints per item the type, steps, each step's charter, band, model, effort and ceiling (the step-to-charter table fixed in `conductor.py`), the item estimate from `budgets_usd` by its `size:` label, and a reserved PRD/ADR/WO block above the highest id on `origin/main` (read through `knowledge_plane`) and above every earlier block; then the batch estimate against what remains of `monthly_cap_usd`, and one deferral line each for a non-owner author, no `type:` label, no `size:` label, a closed issue, and over the cap. It plans nothing on a `config:` problem and refuses the whole plan on an unreadable or truncated issue read. `conductor.py open` creates the `conductor/<batch>` branch and worktree from `origin/main` (through the git port), writes the `plan` row (with its `routing`/`effort` policy snapshot) and one `reserve` row per block, and queues the spend ask; a test asserts no two items' blocks share a number.

## Milestone 3: One item runs end to end through metered Workers (stalls escalate)

- [x] **WO-0157** Item state machine and the stall rule in `next` — size:M, blocked by: WO-0155 (PRD-0013 §User stories, §Success criteria)
  - Accept: `state` rows move an item only along `planned → spec → awaiting-gate → build → verify → review → reviewed → ship → merging → merged`, with `stalled` from any non-terminal state and `blocked` reachable only through an answer row; a `fix` item skips the gate states its re-entry depth does not reach; an `order` item starts at `build`. `next` returns the steps ready to launch under `wip_cap`, never one for an item with an unanswered ask, and records a `stall` ask (options: retry on the same policy, retry one band up, block with a reason) when a run row's pid is gone with no finishing row, when an item has had no state change for twice its step's wall-clock limit, or on a second reviewer request for changes (the first queues one `build` fix step); three consecutive Worker failures across the batch pause dispatch behind one ask. A `reviewed` pass whose reviewer `run_id` is among the author runs is refused.
- [x] **WO-0158** Worker runner: one metered headless run per step — size:M, blocked by: WO-0153, WO-0156, WO-0157 (PRD-0013 §User stories, §Success criteria, §Actors)
  - Accept: `conductor.py run <batch> <item> <step>`, with an injected harness, composes every harness flag in one function (`--model`, `--effort`, `--max-budget-usd`, `--output-format json`, an `--allowedTools` list containing no `git push` and no `gh` write), sets `CONDUCTOR_WORKER` in the Worker's environment, and runs under `cli.harness_run` with the S 45 / M 90 / L 180 minute timeout; the brief carries objective, output, tools, boundaries (item worktree, reserved block, never the plugin version) and context budget, and includes the issue body only for a `spec` step. Each run writes exactly one `run` row and one `costs.jsonl` row on the item branch (`wo` is the work order for a build step, else `#<n>`; `run_id` is `conductor-<batch>-<item>-<step>-<seq>`; cost from `cli.read_execution`), keeps the result event as `runs/<run_id>.json`, pushes the item branch (never forced) and opens or updates its PR from the uncommitted `pr-body.md`. A missing harness binary records `agent-failed` at cost 0; an unaccountable result event or a wall-clock kill records the ceiling as cost and queues a stall; a failed push or PR open queues a stall; nothing retries.
- [x] **WO-0159** Autorun honours `stop-after:` — size:S, blocked by: — (PRD-0013 §Out of scope, §Actors)
  - Accept: `skills/autorun/SKILL.md` states that a `stop-after: <stage>` line in `autorun-brief.md` makes autorun stop once that stage's artifact or recorded skip exists, without starting the next stage; the skill's `description:` is unchanged; `python3 lint.py` prints `lint: 0 problem(s)`. The version bump rides row 0164.

## Milestone 4: Reviewed items merge in order (never green alone, red together)

- [x] **WO-0160** Merge precondition — size:S, blocked by: WO-0157 (PRD-0013 §User stories, §Success criteria, §Out of scope)
  - Accept: a pure check refuses `conductor.py merge` with its own problem string unless the item is `reviewed` with a pass verdict from a reviewer run distinct from every author run, and an answer covers it: its own merge ask, or a train ask whose `covers` lists it, answered with the train option, with every earlier item in that train already `merged`. A PR touching `docs/adr/**`, a run's `prd.md` or `architecture.md`, or `docs/design/**` passes on a train only when those files' blob ids equal the `gate_blobs` answered at its gate asks; a fixture with one changed blob is refused.
- [x] **WO-0161** The merge turn — size:M, blocked by: WO-0158, WO-0160 (PRD-0013 §User stories, §Success criteria, §Open questions)
  - Accept: with injected git and gh ports over a scratch repo, `conductor.py merge <batch> <item>` runs the architecture's eight steps in order: merges `origin/main` into the item branch; resolves only `costs.jsonl` (by the new `.gitattributes` line `docs/factory/costs.jsonl merge=union`) and the manifest (by regeneration); bumps the plugin patch version from `main`'s value when the item touched `skills/`; confirms every reserved number the item used is still free on `origin/main`, recording a mechanical renumber as a `reserve` row with `renumbered_from`; runs `make check`; pushes without force; waits up to 30 minutes for the new head's checks; then squash-merges, or enqueues when `mergeQueue(branch: "main")` is non-null and waits for merged or ejected. It writes a `merged` state row with `pr`, `sha` and `checks`. A non-mechanical conflict, a red re-check, an ejection, a timeout, or an unrenumberable collision each queue a stall ask and leave the branch as pushed; no test path force-pushes or retries.

## Milestone 5: A batch closes with a scorecard, and the Owner can drive it

- [x] **WO-0162** Scorecard from ledger rows alone — size:M, blocked by: WO-0158 (PRD-0013 §User stories, §Success criteria)
  - Accept: `conductor.py scorecard <batch>` computes the architecture's scorecard fields (including `owner_touches_per_merged`, `estimate_error_pct` against the plan row, `collisions` from `renumbered_from` rows, `merged_per_owner_wait_hour` by ADR-0080's formula over the batch's ask-to-answer waits, `policy_compliance` against the plan's policy snapshot, and `conductor_session: "unmetered"`) from a fixture ledger and its `costs.jsonl` alone; it exits nonzero with a `cd:` problem naming file and line, and appends nothing, for a malformed ledger line, a `run` row with no `costs.jsonl` row of the same `run_id`, and a missing `plan` row.
- [x] **WO-0163** Close a batch — size:S, blocked by: WO-0161, WO-0162 (PRD-0013 §User stories, §Success criteria)
  - Accept: `conductor.py close <batch>`, with injected ports, appends blocked items' spend rows to the conductor branch's `costs.jsonl`, runs `scorecard` and appends its row to `docs/factory/scorecards.jsonl` only on success, writes the `close` row, commits the ledger, run evidence and scorecard on `conductor/<batch>`, opens its PR, queues its merge ask, and labels each blocked item's issue `needs-human` with a reason comment; a failing scorecard leaves `scorecards.jsonl` byte-identical.
- [x] **WO-0164** The `conduct` skill, vocabulary and packaging — size:M, blocked by: WO-0156, WO-0158, WO-0159, WO-0161, WO-0163 (PRD-0013 §Solution, §Actors, §User stories, §Out of scope)
  - Accept: `skills/conduct/SKILL.md` gives the Conductor's procedure in harness-neutral words: every entry runs `conductor.py next` first; it opens a batch, asks the spend question, launches runners in the background up to the cap, presents one ask at a time with the recommended option first and its reason, writes an answer only straight after the Owner picks it in this session, and drives the merge turns answers cover; it never writes or reviews an item's code and never re-derives a decision the tool made. `conduct` is in `protocol.UTILITY_SKILLS`, with the README, LEDGER and plugin surfaces lint requires; `CONTEXT.md` defines Conductor, Worker, batch, batch ledger, decision queue and merge train; `.claude-plugin/plugin.json`'s minor version is bumped once; `python3 -m unittest discover tests` prints `OK`, `python3 lint.py` prints `lint: 0 problem(s)`, and `python3 gates.py && python3 gates.py --selftest` prints `gates: 0 problem(s)` and `selftest: ok`.

## Coverage

Every PRD-0013 user story has a row: story 1 (priced plan) row 0156;
story 2 (durable queue, one ask at a time) row 0155 and row 0164; story 3
(ledger) row 0155 and row 0157; story 4 (reservations) row 0156 and row 0161;
story 5 (brief and policy) row 0154 and row 0158; story 6 (independent
review, ordered merges) row 0160 and row 0161; story 7 (merged or blocked,
stalls escalate) row 0157 and row 0163; story 8 (scorecard) row 0162 and
row 0163.

Every success criterion has an acceptance line that makes it checkable
offline; the criteria themselves are judged on a real batch at Verify.
SC 1 answer rows (row 0155, row 0164); SC 2 reservations (row 0156, row 0161);
SC 3 metered rows and the estimate (row 0153, row 0158, row 0162); SC 4 state
rows matching GitHub (row 0157, row 0161, row 0163); SC 5 distinct writer and
reviewer, green checks (row 0157, row 0160, row 0161); SC 6 policy compliance
(row 0154, row 0158, row 0162); SC 7 the scorecard and its failure mode
(row 0162).

Every architecture component appears: the `conduct` skill (row 0164);
`conductor.py`'s `plan` and `open` (row 0156), `next` (row 0155, row 0157),
`run` (row 0158), `ask`/`answer` (row 0155), `merge` (row 0160, row 0161),
`scorecard` (row 0162) and `close` (row 0163); Policy (row 0154);
Reservation (row 0156, row 0161); the supporting edits: `cost_ledger`
(row 0153), `factory_config` (row 0154), autorun's `stop-after:` (row 0159),
`.gitattributes` (row 0161), `CONTEXT.md` and `UTILITY_SKILLS` (row 0164).

## Design gaps found

None. Every contract the rows build against is stated in architecture.md,
and every existing seam it names exists on main (`cli.harness_run`,
`cli.read_execution`, `cost_ledger.entry`/`append`/`dispatched`,
`work_queue.month_to_date`, `assembler.select_charter`/`charter_band`/
`PR_BODY_FILE`, `make wo-in-progress`, the `needs-human` label).

## Notes

- 2026-10-10: this repo's own policy is read from
  `factory/templates/factory.json` (`factory_config.load` falls back to the
  payload copy when no `.github/factory.json` is installed), so row 0154's
  `effort` table edits a checksum-pinned template and owes a manifest
  regeneration. row 0153 owes one too: `cost_ledger.py` and `cost_report.py`
  are in `factory_init.MIRRORS`. `conductor.py` stays root-only (Architect).
- 2026-10-10 (Implement, row 0153): the issue-key grammar is
  `cost_ledger.ISSUE_KEY`; `cost_report.compose_report` and
  `dashboard._output` read it to label a `#<n>` group as
  "issue #<n> (no work order)". The dashboard's issue rows follow the
  work-order rows in the output table. Adjacent, not changed: the
  dashboard's `cost_per_wo` divides lifetime spend by every `by_wo` key,
  so issue groups now count in its denominator as if they were orders.
  Logged here for a later run rather than fixed in this row.
- 2026-10-10 (Implement, row 0155): the architecture's `ask` row lists
  its own `kind` (spend / gate / merge / stall / clarify), which collides
  with every row's `kind` field (here `"ask"`). The ask's field is
  `ask_kind`; the CLI flag stays `--kind`. A rename inside the grammar
  this row owns, not a design change. Ask ids are `ask-<n>`, one past the
  batch's ask count, assigned under the append lock. `conductor.py` is a
  new CLI-bearing root module, so it also gets its `conductor` verb in
  `factory.py`'s table (`tests/test_factory_cli.py` pins one verb per
  such module).
- 2026-10-10 (Implement, row 0156): row 0156 hit seven decisions the
  artifacts did not settle. Implement stopped and recommended a default
  for each. The Owner accepted all seven on 2026-10-10 via the
  orchestrator's question, as assumptions:
  1. Reserved block sizes per item: feature {PRD 1, ADR 3, WO 10}, fix
     {ADR 1, WO 5}, order {} (its ids already exist). Fixed constants
     with a `lean:` marker; a Worker that runs out stops and says so.
  2. Steps per type: feature and fix [spec, build, verify, review,
     ship]; order [build, verify, review, ship].
  3. Type from labels: `wo:ready-for-agent` makes an order;
     `type:feature` a feature; `type:defect` and `type:chore` a fix;
     `type:support` and `type:sweep` are deferred as not plannable.
  4. Step ceilings: the item's `budgets_usd[size]` estimate split
     equally across its steps.
  5. The repo owner is read with `gh repo view --json owner` through
     `cli.gh_read`, failing closed.
  6. The highest ids in use come from `git grep` over `origin/main` with
     knowledge_plane's PRD/ADR/WO token grammars, taking the max of each.
  7. `open` takes a caller-supplied batch slug: `open <batch> <#N>...`.
- 2026-10-10 (Implement, row 0156), choices inside those answers: the
  `git grep` is scoped to `docs/`, because tests and fixtures on
  `origin/main` carry example ids in the nine-thousands that would push every
  block past the 4-digit grammar. The batch worktree is
  `.claude/worktrees/conductor-<batch>` under the repo root. The spend
  ask's options are `approve` / `decline`, recommending `approve`, since
  over-cap items are already deferred. `plan` reads ids from the local
  `origin/main` ref without fetching, because it writes nothing; the
  merge turn's confirmation (row 0161) covers a stale ref.
- 2026-10-10 (Implement, rows 0157 and 0158): the two rows hit nine
  decisions the artifacts did not settle. Implement stopped and
  recommended a default for each. The Owner accepted all nine on
  2026-10-10 via the orchestrator's question:
  1. Launch record: before spawning, `run` appends a `state` row
     entering the step with two optional fields, `run_id` and `pid` (the
     runner's own pid). The run's one `run` row, written at the end, is
     the finishing row. `next` stalls an item whose launch pid is dead
     (an injected probe) with no `run` row of that `run_id`.
  2. Readiness: an item stays in a step's state until the next launch
     moves it; a step is done when its finishing run row's outcome is
     `completed`. `next` reports an item ready for its next step when
     its state is `planned`, `reviewed`, or a finished step, and it has
     no unanswered ask. The launch writes the move.
  3. Gate asks: on a completed `spec` run, `next` moves the item to
     `awaiting-gate` and queues a `gate` ask (`approve` / `block`,
     recommending `approve`) whose `gate_blobs` are the blob ids, read
     through the git port, of the gate paths the item branch changes
     (`docs/adr/**`, `prd.md`, `architecture.md`, `docs/design/**`). An
     `approve` answer makes `build` ready.
  4. A fix item's re-entry depth is inferred from those gate paths: none
     changed skips `awaiting-gate` (spec to build); any gates it. A
     feature always gates.
  5. Review verdict: the review brief requires a `verdict: pass|changes`
     line in the run's `review.md` frontmatter, and overrides the
     reviewer charter's comment, label and merge exit. `pass` writes
     `reviewed` (with `author_runs` and `reviewer_run`); the first
     `changes` writes review to build; the second queues a stall.
  6. `answer` itself appends the `blocked` state row, under the same
     lock, when an item's ask is answered `block`. A `retry` or
     `retry-up` answer makes the stalled step ready again. Stall options
     are `retry`, `retry-up`, `block`; `retry-up` takes the next band in
     mechanical, implementation, architecture_review and is omitted on
     the top band. Recommended: `retry` for a dead runner, an idle item
     or a Worker failure; `block` for a second request for changes. The
     three-failure batch pause is an item-less `stall` ask with options
     `resume` / `stop`, recommending `stop`.
  7. Each build run takes the first unchecked row of the item branch's
     `breakdown.md`, and `wo` is that row's id; the item stays ready for
     `build` while unchecked rows remain. An order item's work order
     comes from its issue.
  8. Item branch `conductor/<batch>-<n>`, worktree
     `.claude/worktrees/conductor-<batch>-<n>`, created from
     `origin/main` by the item's first runner.
  9. Runner defaults: one fixed `--allowedTools` list (Read, Edit, Write,
     Glob, Grep, `Bash(python3 *)`, `Bash(make *)`, and git add, commit,
     status, diff and log; no push, no gh); `--max-budget-usd` is the
     step's planned `ceiling_usd`; `seq` is the item's count of that
     step's runs plus one; the spend row is committed onto the item
     branch before the push; a completed run with no `pr-body.md` is
     missing output and stalls; the spec brief carries
     `stop-after: decompose`.
  The architecture records them under "Amendments (implement-time,
  Owner-accepted)".
- 2026-10-10 (Implement, row 0157): the state machine and the stall
  rule live in `conductor_flow.py`, split from `conductor.py` by
  capability in its own commit before this row (assumption 6;
  `conductor_plan.py` holds plan and open). `conductor.py` keeps the
  grammar and gains what the grammar's writers need: optional `run_id`
  and `pid` on a state row, multi-row appends under one lock,
  `current_state`, `ask_row`, and the `blocked` row `answer` writes. The
  second request for changes stalls through `record_verdict`, the write
  the runner makes after a review step (decision 5), not through `next`:
  the verdict is known only when the review run ends. `next` also holds
  all dispatch while a batch-level ask is unanswered or was answered
  `decline` or `stop`, so no step launches before the spend answer.
  `next` now needs `wip_cap` from factory.json, and its JSON gains
  `ready` and `recorded` beside `ask`.
- 2026-10-10 (Implement, row 0158): the runner lives in
  `conductor_run.py` (assumption 6). Choices inside the Owner's answers:
  the `run` row's `model` and `effort` are the plan row's snapshot for
  the step (one band up after `retry-up`, resolved from the snapshot's
  `routing`/`effort`), while the spend row's `model` is the model the
  result event reports when the passed one is absent from it. A result
  event `read_execution` cannot meter is kept as evidence and recorded
  as `unaccounted:cost-at-ceiling` (ADR-0034's open outcome vocabulary);
  a wall-clock kill is `killed:cost-at-ceiling`. A result event whose
  subtype is not `success` is `agent-failed` at its metered cost. Every
  Worker-failure stall recommends `retry`. `run` refuses, before
  creating a worktree or spawning anything, a step the state machine
  would refuse, then re-checks under the lock as it writes the launch
  row. An open PR's body is updated through `gh api -X PATCH`, and a new
  PR is titled `#<n>: conductor batch <batch>`. A failed spend-row
  commit stalls like a failed push.
- 2026-10-10 (Implement, row 0160): the precondition lives in
  `conductor_merge.py` (assumption 6), as `merge_problems(rows, item,
  blobs)`, pure over the ledger rows and the item branch's gate blobs.
  Choices inside the design: a merge ask's consenting choice is `merge`
  for an item's own ask and `train` for a train ask (the `conduct`
  skill, row 0164, words its asks with those options); an item at
  `ship` merges only once its ship run completed, and otherwise the
  move to `merging` goes through `transition_problems`, so an
  unanswered ask or a stall without a retry answer also refuses; the
  author runs a reviewer must be distinct from are the recorded
  `author_runs` plus every non-review run row of the item; when several
  train asks cover an item, the latest consenting one decides; the
  approved gate blobs are the union of the item's approved gate asks,
  a later approval winning per path. The train reading (one answer per
  ordered train, gate-path items only on identical blobs) is built as
  designed and stays flagged for the Owner.
- 2026-10-10 (Implement, row 0161): the merge turn lives in
  `conductor_merge.py` beside its precondition. Choices inside the
  design, none of them a design change:
  1. Ports: `git` (the existing port; item-worktree calls carry
     `-C <worktree>`), `gh`, a `tool` port for `make -C <worktree> check`
     and `python3 <worktree>/factory_init.py update-manifest`, and the
     clock plus `sleep` for the two 30-minute waits (polled every 30
     seconds). `conductor.main` gains `tool` and `sleep`. The tests run
     the turn over a scratch repo with a local bare origin; gh, make and
     the manifest regeneration are fakes.
  2. Step 1 fetches `origin main` first, so a stale local ref (row 0156's
     note) is refreshed before the merge. A conflict list of exactly the
     manifest is regenerated and committed; any other conflict, or a
     merge that fails with none, runs `git merge --abort` and stalls.
     `costs.jsonl` never conflicts: the new root `.gitattributes`
     merges it by union.
  3. Step 3 also regenerates the manifest, because the manifest pins the
     plugin version, and records the new version as a `reserve` row
     (`what: plugin-version`), the architecture's write slot. The bump
     is idempotent, so a retried turn does not bump twice.
  4. Step 4's "used" numbers are the item's reserved numbers cited in a
     line the item added (a branch line with no unclaimed copy in
     origin/main's version of the file) or naming an ADR file the item
     added. A used number present on origin/main moves to the next
     number above every id on origin/main and every block in the batch;
     the item's ADR file is renamed and only the item's added lines are
     rewritten, then committed. Unrenumberable: a new number past 9999,
     or a rename target that exists. A shared index both sides appended
     to adjacently is a git conflict, so it stalls at step 2 as
     non-mechanical.
  5. After steps 1-4 the answer half of the precondition re-runs on the
     branch's new gate blobs, so a gate file the update or a renumber
     changed no longer rides a train (it stalls for its own merge ask).
  6. Step 7 reads the new head's check runs
     (`repos/{owner}/{repo}/commits/<sha>/check-runs`), stalls at once
     on a run that completed with a conclusion other than success,
     skipped or neutral, and records `checks` as {name: conclusion}.
     Step 8 reads `mergeQueue(branch: "main")` through `gh api graphql`
     and in both paths runs `gh pr merge <n> --squash
     --match-head-commit <head>` (with a queue, gh enqueues and the
     queue owns the strategy), then reads `gh pr view` for merged,
     ejected (`isInMergeQueue` false while open) or a timeout. gh's
     behaviour with `--squash` on a queue-required branch is unverified
     offline.
  7. A stall recommends `block` for a non-mechanical conflict, a red
     make check or check run, an ejection, a collision and a refused
     gate re-check; `retry` for a timeout, a failed push and a failed gh
     or git read. The stall ask keeps the fixed options, so `retry-up`
     is offered on a merge stall too, where it means the same as
     `retry`.
  8. `next` reported a stalled merge's resumed step as `merging`, which
     `run` cannot launch; `conductor_flow` now reports it as `merge`,
     the verb that resumes it.
  Adjacent, not changed: the scratch-repo tests spawn real `git`
  processes, which adds a few minutes to the suite on this machine.
- 2026-10-10 (Implement, row 0162): the scorecard and `close` live in
  `conductor_close.py` (assumption 6). Choices inside the design, none
  of them a design change: `owner_touches_per_merged` counts answer
  rows (SC 1: every Owner action is an answer); `collisions` counts
  renumbered numbers, the sum of every `renumbered_from` list;
  `stalls` counts state rows into `stalled`; `escalations` counts asks
  beyond the planned spend, gate and merge decisions (`stall` and
  `clarify`); `review_changes_per_item` counts review-to-build moves
  plus second-request stalls (their reason is now the constant
  `conductor_flow.CHANGES_AGAIN`), over the plan's items;
  `merged_per_owner_wait_hour` sums the wait of every answered ask;
  `policy_compliance` is a fraction of runs. Ratios round to four
  places and are null over a zero denominator. A malformed
  `costs.jsonl` line fails the scorecard too, with cost_ledger's own
  `ledger:` problem. `conductor.py`'s reader gains `read_text` and
  `numbered` so a run row's problem can name its line.
- 2026-10-10 (Implement, row 0163): `close` in `conductor_close.py`.
  Choices inside the design, flagged here for the Owner:
  1. `close` first merges `origin/main` into `conductor/<batch>` (fetch,
     then a no-edit merge; any failure aborts the merge and refuses the
     close). The architecture has the scorecard read the batch branch's
     `costs.jsonl`, but a merged item's spend rows reach `main` on its
     own PR, never the batch branch; without this step the scorecard
     would fail every real batch on its first merged run. It is the
     merge turn's step 1, applied to the batch branch.
  2. `close` is refused unless every planned item is `merged` or
     `blocked` (PRD story 7; the architecture computes the scorecard
     "once, after the last merge"), and refused for a batch that
     already has a `close` row.
  3. A blocked item's carried spend rows are every row on its branch's
     `costs.jsonl` whose `run_id` starts `conductor-<batch>-<n>-` and is
     not already on the batch branch, so a re-run never doubles one.
  4. The close row and the closing merge ask (`merge` / `hold`,
     recommending `merge`) are written together under one lock before
     the commit, so the committed ledger carries the ask the closing PR
     waits on. The PR body carries `Closes #<n>` for each merged item
     and a `No work order:` line (docs/kb/pr-body-contract.md); a batch
     with no merged item has no issue to close and would fail detector
     B on CI.
  5. A blocked item's `needs-human` comment carries the reason of its
     `blocked` state row. A failure after the close row is written
     (commit, push, PR, label) is reported naming the step and is
     finished by hand; a `lean:` marker names the trigger to resume it
     mechanically.
- 2026-10-10 (Implement, row 0164): the M4 gap is closed here. `next`
  did not report an item at `ship` with a completed ship run as waiting
  for a merge ask, so the skill could not know to word one. `next`'s
  JSON gains `merge_due`: the shipped items with no consenting merge
  answer and no pending merge ask (their own, or a train listing them).
  Once an answer covers one (`merge` on its own ask, or `train` with
  every earlier train item merged), `next` reports it ready as
  `{"step": "merge"}`, the verb `run` cannot launch and `merge` resumes,
  as row 0161 did for a stalled merge. To give that one owner, the
  consent reading (`consents`, `MERGE_CHOICE`, `TRAIN_CHOICE`) moved from
  `conductor_merge` to `conductor_flow`, which the precondition now
  calls. Also changed: an unanswered batch-level `merge` ask (a train,
  or the closing ask) no longer holds Worker dispatch; row 0157's hold
  was for the spend ask and the batch pause, and a train question must
  not idle every other item. Packaging: `conduct` joins
  `protocol.UTILITY_SKILLS` (a mirrored file, so the manifest is
  regenerated), plugin.json's description, the README table, the README
  figure's "Driving a run" card, LEDGER at `draft` with no eval
  evidence, and four routing cases (three cases is lint's floor; none
  has been run). `.claude-plugin/plugin.json` moves 0.7.3 to 0.8.0, the
  one bump covering row 0159's autorun change and the new skill.
  `docs/setup.md`'s "An orchestrator (planned)" section, which this row
  makes false, now describes the Conductor.
- 2026-10-11 (Implement, post-review, review major 1): merged code is
  reviewed code. The Owner chose, via the orchestrator's question, to fix
  review majors 1–3 test-first. The rule chosen as the thinnest sound
  one: the review run's runner reads the item branch head before it
  launches, and the `reviewed` row records it as `reviewed_head` (an
  optional state field; the merge precondition refuses a reviewed row
  without one). A merge turn that starts from `ship` then diffs that
  head's tree against the branch, before any Conductor commit, and
  stalls (recommending `block`) when any path but the run's
  `review.md`, `release.md` or `docs/factory/costs.jsonl` changed. It is
  a tree diff, not a commit walk, so rewritten history is caught and no
  commit authorship has to be trusted (Worker and Conductor commit as
  the same git user, so "Conductor-authored" could not be checked). A
  turn resumed from a `merging` stall skips the check: the state machine
  runs no Worker between that stall and its resumed turn, and the first
  turn already checked before it merged `main` in. A stall rather than a
  bare refusal, because the state machine has no path from `ship` back
  to `review`: the Owner gets a `block` to answer instead of a merge
  that is refused on every `next`. The review and ship briefs now say to
  commit nothing but their artifact. Still trust-based: a change made
  in the worktree by something other than a Worker (a human, a process
  a Worker left running) between the check and the push.
- 2026-10-11 (Implement, post-review, review major 2): build spend is
  re-priced at the gate and capped at run time, as architecture.md's
  Amendments 10 and 11 record. Decisions inside the fix: the price is
  rows × the build ceiling (the most the runs can spend), not band
  prices; the cap is the current `factory.json`'s, not the plan row's
  snapshot, so raising it is how the Owner resumes; in-flight ceilings
  count, and the check runs under the ledger lock, so two runners
  cannot both pass it on the same headroom; an over-cap launch pauses
  dispatch behind a batch-level `spend` ask rather than stalling the
  item, because a stall resumes only into its own state and `planned`,
  `awaiting-gate` and `reviewed` are not steps. The three-failure
  pause now counts only `stall` asks as its reset point, so a cap
  pause does not clear a failure streak. Remaining gaps: a fix that
  skips the gate gets no build re-pricing ask; a review's one
  automatic fix build is not re-asked; and spend landing on main from
  outside the batch counts only from the last fetch. `skills/conduct`
  names the new ask, so plugin.json moves 0.8.0 to 0.8.1 and the
  manifest is regenerated.
- 2026-10-11 (Implement, post-review, review major 3): "no push, no
  gh" is enforced in the Worker's environment (`conductor_run.
  worker_env`, architecture.md amendment 12), and `Bash(make *)` is
  narrowed to `Bash(make check)`, which no gh-writing target shares.
  The combination chosen as the thinnest that blocks every push path a
  confused Worker could take: `GIT_SSH_COMMAND=false` stops any ssh
  push, whatever the host or ssh alias; an env-config
  `url.<impossible path>.pushInsteadOf` for `https://` and `http://`
  rewrites any http(s) push, credentials in the URL or `.netrc`
  included, while fetches are untouched; and `credential.helper` reset
  plus `GIT_TERMINAL_PROMPT=0` and stripped askpass variables keep git
  from handing out a token. For gh: the token variables are stripped
  and `GH_CONFIG_DIR` is an empty temporary directory removed after
  the run (probed 2026-10-11: gh then reports "not logged into any
  GitHub hosts", the macOS keychain token included). Not chosen: a
  `pushurl` on the remote, which lives in the config shared with the
  main checkout and so would break the runner's own push. Local-path
  remotes still push, so `make check` passes under the Worker's
  environment (run 2026-10-11: rc 0, 2336 tests). The tests assert the
  env handed to the harness and run real git pushes against it. Still
  trust-based: a hostile Worker can restore any variable through
  `python3` (`os.environ`, `git -c`), read the keychain or an
  unencrypted key file, or call the GitHub API with a token it finds.
  Ssh fetches from the Worker also fail now, which no step needs.
- 2026-10-11 (Implement, post-review, review major 4): the Owner chose
  to have the ADR-0036 condition-3 reading written up rather than coded
  around. It is drafted as ADR-0085, status provisional, and indexed.
  It would amend ADR-0036 conditions 2 and 3 for merges inside a
  Conductor batch: the Owner's in-session answer, executed by the
  Conductor, is the human merge; one answer may cover a train; a
  gate-path item rides a train only on byte-identical gate blobs; and
  the review pass is recorded in the ledger, with the reviewed head,
  not on the PR. ADR-0036's status line is unchanged until the Owner
  accepts it. Number: 0085 was free on origin/main and on every open PR
  branch (#670, #673, #675) on 2026-10-11. An uncommitted 0085 draft in
  the stale worktree that architecture.md's last assumption names is
  not on any branch.
- 2026-10-11 (Implement, re-review R1): a merge turn that starts from
  `ship` now also stalls, recommending `block`, when `git status
  --porcelain --untracked-files=all` in the item worktree is non-empty,
  checked with the reviewed-tree diff and before any Conductor commit.
  The tree diff sees committed trees only, so a file a Worker left
  uncommitted would otherwise have been swept in by the Conductor's own
  `git add -A -- factory` commits. Those commits now stage by name only
  the files the Conductor writes: `factory/manifest.json`,
  `.claude-plugin/plugin.json` on a version bump, and the payload
  mirrors under `factory/templates/` that `update-manifest` refreshes
  (`factory_init.MIRRORS`). Either half alone closes the reproduced
  route; both are kept, because the second also holds on a resumed
  turn, which skips the first.
