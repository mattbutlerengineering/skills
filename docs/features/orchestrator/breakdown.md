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

- [ ] **WO-0157** Item state machine and the stall rule in `next` — size:M, blocked by: WO-0155 (PRD-0013 §User stories, §Success criteria)
  - Accept: `state` rows move an item only along `planned → spec → awaiting-gate → build → verify → review → reviewed → ship → merging → merged`, with `stalled` from any non-terminal state and `blocked` reachable only through an answer row; a `fix` item skips the gate states its re-entry depth does not reach; an `order` item starts at `build`. `next` returns the steps ready to launch under `wip_cap`, never one for an item with an unanswered ask, and records a `stall` ask (options: retry on the same policy, retry one band up, block with a reason) when a run row's pid is gone with no finishing row, when an item has had no state change for twice its step's wall-clock limit, or on a second reviewer request for changes (the first queues one `build` fix step); three consecutive Worker failures across the batch pause dispatch behind one ask. A `reviewed` pass whose reviewer `run_id` is among the author runs is refused.
- [ ] **WO-0158** Worker runner: one metered headless run per step — size:M, blocked by: WO-0153, WO-0156, WO-0157 (PRD-0013 §User stories, §Success criteria, §Actors)
  - Accept: `conductor.py run <batch> <item> <step>`, with an injected harness, composes every harness flag in one function (`--model`, `--effort`, `--max-budget-usd`, `--output-format json`, an `--allowedTools` list containing no `git push` and no `gh` write), sets `CONDUCTOR_WORKER` in the Worker's environment, and runs under `cli.harness_run` with the S 45 / M 90 / L 180 minute timeout; the brief carries objective, output, tools, boundaries (item worktree, reserved block, never the plugin version) and context budget, and includes the issue body only for a `spec` step. Each run writes exactly one `run` row and one `costs.jsonl` row on the item branch (`wo` is the work order for a build step, else `#<n>`; `run_id` is `conductor-<batch>-<item>-<step>-<seq>`; cost from `cli.read_execution`), keeps the result event as `runs/<run_id>.json`, pushes the item branch (never forced) and opens or updates its PR from the uncommitted `pr-body.md`. A missing harness binary records `agent-failed` at cost 0; an unaccountable result event or a wall-clock kill records the ceiling as cost and queues a stall; a failed push or PR open queues a stall; nothing retries.
- [x] **WO-0159** Autorun honours `stop-after:` — size:S, blocked by: — (PRD-0013 §Out of scope, §Actors)
  - Accept: `skills/autorun/SKILL.md` states that a `stop-after: <stage>` line in `autorun-brief.md` makes autorun stop once that stage's artifact or recorded skip exists, without starting the next stage; the skill's `description:` is unchanged; `python3 lint.py` prints `lint: 0 problem(s)`. The version bump rides row 0164.

## Milestone 4: Reviewed items merge in order (never green alone, red together)

- [ ] **WO-0160** Merge precondition — size:S, blocked by: WO-0157 (PRD-0013 §User stories, §Success criteria, §Out of scope)
  - Accept: a pure check refuses `conductor.py merge` with its own problem string unless the item is `reviewed` with a pass verdict from a reviewer run distinct from every author run, and an answer covers it: its own merge ask, or a train ask whose `covers` lists it, answered with the train option, with every earlier item in that train already `merged`. A PR touching `docs/adr/**`, a run's `prd.md` or `architecture.md`, or `docs/design/**` passes on a train only when those files' blob ids equal the `gate_blobs` answered at its gate asks; a fixture with one changed blob is refused.
- [ ] **WO-0161** The merge turn — size:M, blocked by: WO-0158, WO-0160 (PRD-0013 §User stories, §Success criteria, §Open questions)
  - Accept: with injected git and gh ports over a scratch repo, `conductor.py merge <batch> <item>` runs the architecture's eight steps in order: merges `origin/main` into the item branch; resolves only `costs.jsonl` (by the new `.gitattributes` line `docs/factory/costs.jsonl merge=union`) and the manifest (by regeneration); bumps the plugin patch version from `main`'s value when the item touched `skills/`; confirms every reserved number the item used is still free on `origin/main`, recording a mechanical renumber as a `reserve` row with `renumbered_from`; runs `make check`; pushes without force; waits up to 30 minutes for the new head's checks; then squash-merges, or enqueues when `mergeQueue(branch: "main")` is non-null and waits for merged or ejected. It writes a `merged` state row with `pr`, `sha` and `checks`. A non-mechanical conflict, a red re-check, an ejection, a timeout, or an unrenumberable collision each queue a stall ask and leave the branch as pushed; no test path force-pushes or retries.

## Milestone 5: A batch closes with a scorecard, and the Owner can drive it

- [ ] **WO-0162** Scorecard from ledger rows alone — size:M, blocked by: WO-0158 (PRD-0013 §User stories, §Success criteria)
  - Accept: `conductor.py scorecard <batch>` computes the architecture's scorecard fields (including `owner_touches_per_merged`, `estimate_error_pct` against the plan row, `collisions` from `renumbered_from` rows, `merged_per_owner_wait_hour` by ADR-0080's formula over the batch's ask-to-answer waits, `policy_compliance` against the plan's policy snapshot, and `conductor_session: "unmetered"`) from a fixture ledger and its `costs.jsonl` alone; it exits nonzero with a `cd:` problem naming file and line, and appends nothing, for a malformed ledger line, a `run` row with no `costs.jsonl` row of the same `run_id`, and a missing `plan` row.
- [ ] **WO-0163** Close a batch — size:S, blocked by: WO-0161, WO-0162 (PRD-0013 §User stories, §Success criteria)
  - Accept: `conductor.py close <batch>`, with injected ports, appends blocked items' spend rows to the conductor branch's `costs.jsonl`, runs `scorecard` and appends its row to `docs/factory/scorecards.jsonl` only on success, writes the `close` row, commits the ledger, run evidence and scorecard on `conductor/<batch>`, opens its PR, queues its merge ask, and labels each blocked item's issue `needs-human` with a reason comment; a failing scorecard leaves `scorecards.jsonl` byte-identical.
- [ ] **WO-0164** The `conduct` skill, vocabulary and packaging — size:M, blocked by: WO-0156, WO-0158, WO-0159, WO-0161, WO-0163 (PRD-0013 §Solution, §Actors, §User stories, §Out of scope)
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
