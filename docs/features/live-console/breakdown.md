---
stage: decompose
run: feature:live-console
date: 2026-10-16
assumptions:
  - "Work-order ids start at 0165: WO-0164 is the highest token anywhere under docs/ on main at 35d0d2e, and the open consumer batch (sdlc-ci) reserves numbers in its own repo, not this one (checked 2026-10-16)."
  - "No tracker mirror: no WO-#### issue is created for any row (ADR-0026, ADR-0032 one-way dispatch). The run's PR carries a `No work order:` waiver line and closes a plain tracking issue, as the repo's fix runs do."
  - "Owner-session ledger policy, as in docs/features/lean-in-the-build/breakdown.md: each checked row appends one zero-cost owner-session row to docs/factory/costs.jsonl through budget_guard record, so detector G holds."
  - "Rows are cut by component, then by source, then by measurement — nine rows in three milestones — because each component of architecture.md is one sitting and each source is a separate reader with its own fixtures. The milestone boundaries were accepted by the Owner in session on 2026-10-16."
---

# Breakdown: Live console

Progress lives in the checkboxes below — Implement checks items off as
their acceptance criteria are met. Component names are architecture.md's:
the **Hook recorder** (`live_hook.py`), **Live state** (`live_state.py`)
and the **Console live view** (`dashboard.py`).

## Milestone 1: A session's wait shows up on the page

A real session that stops on a permission prompt or a question appears in
the console's headline within a minute, and leaves when it resumes.

- [ ] **WO-0165** Hook recorder — size:S, blocked by: — (PRD-0014 §Success criteria, §Actors)
  - Accept: `python3 live_hook.py` reads one hook invocation's stdin JSON and appends one event line (`v` 1, `at`, `event`, `session_id`, `cwd`, `transcript_path`, and `notification_type`, `tool_name`, `tool_use_id`, `message` truncated to 500 characters when present) to `$CLAUDE_LIVE_DIR/events-<UTC date>.jsonl`, defaulting to `~/.claude/live/`, for the eight events architecture.md's fold names (`PermissionRequest`, `Notification`, `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`, `SessionStart`, `SessionEnd`). On malformed or empty stdin, an unknown event or an unwritable directory it writes one line to stderr, prints nothing to stdout and exits 0. `python3 live_hook.py --settings` prints the hooks block to merge into `~/.claude/settings.json`, with `PreToolUse` matched to `AskUserQuestion|ExitPlanMode` and the other seven unmatched. Tests drive a stdin fixture per event and per failure path and assert the exact line written, the exit code and the empty stdout; verification records one invocation's wall time.
  - Blocked by: —
- [ ] **WO-0166** Live state folds events into sessions and waits — size:M, blocked by: WO-0165 (PRD-0014 §Success criteria, §User stories)
  - Accept: `live_state.sessions(lines, now)` returns one session state per `session_id` with `state` in `working`, `waiting`, `idle`, `ended`, `kind` and `text` when waiting, `since` as the time of the event that set the state, and a `stale` flag after 30 minutes without an event, exactly as architecture.md's table maps each event; a `PermissionRequest` and a `permission_prompt` for the same session keep the earlier `since`. `live_state.session_waits(states)` returns the waiting sessions as waits with `source` `session` and `route` `{name, cwd, transcript_path}`, longest wait first. A line the JSON parser refuses or whose `v` is not 1 is skipped and counted into one `dashboard:` problem string per file; a missing events directory is an empty result and no problem. Fixture-driven tests pin every transition in the table and both failure paths with exact outputs.
  - Blocked by: WO-0165
- [ ] **WO-0167** Console live view: `/api/live` and the page — size:M, blocked by: WO-0166 (PRD-0014 §Success criteria, §User stories)
  - Accept: `GET /api/live` on `dashboard.py serve` returns `live_state.gather`'s dict (`waits`, `sessions`, `latency`, `problems`) as JSON with `Cache-Control: no-store`; the page shows the headline list (kind, text, time waiting, route) longest wait first and the who-is-doing-what strip (name, cwd, state, time since last event), and refreshes both every 60 seconds or less. No new POST route exists: a test over `respond` and `respond_post` pins the route set as the existing GETs plus `/api/live`, and the existing `/api/backlog-order` as the only POST. A test asserts the live gather is handed the read-only `gh_read` runner and no other `gh` entry point. `dashboard.py` stays under the repo's 800-line ceiling, the fold and the readers living in `live_state.py`.
  - Blocked by: WO-0166
- [ ] **WO-0168** Install step and the first live wait — size:S, blocked by: WO-0167 (PRD-0014 §Success criteria, §Open questions)
  - Accept: `docs/setup.md` gains a "Live console" section stating the Owner step in order — run `python3 live_hook.py --settings`, merge the printed block into `~/.claude/settings.json`, start `python3 dashboard.py serve` — and what the page shows when no session has reported yet. The Owner performs the step on this machine in an owner session, and verification.md records one real wait: the event line's `at`, the time the entry appeared on the page, and the difference, under 60 seconds; it also records which events closed the wait, answering or leaving open the PRD's two hook questions with that evidence.
  - Blocked by: WO-0167

## Milestone 2: Every source in one list

Conductor asks and GitHub waits join the session waits in the same list,
and the strip knows every live session by name.

- [ ] **WO-0169** Conductor asks from batch ledgers — size:S, blocked by: WO-0166 (PRD-0014 §Success criteria, §Actors)
  - Accept: `live_state.conductor_waits(repo, run, read)` lists the repo's worktrees through the injected runner (`git worktree list --porcelain`), keeps those on a `conductor/<batch>` branch, reads `docs/factory/batches/<batch>/ledger.jsonl` in each and under the repo's own `docs/factory/batches/`, and returns one wait per `ask` row that no `answer` row names, with `source` `conductor`, `key` `<batch>/<ask id>`, the row's `question`, `since` the row's `at`, and `route` `{command: "python3 conductor.py answer <batch> <ask-id>", options, recommended, why}`. Rows are read through `conductor.py`'s own row grammar, never a second parser. A worktree path that no longer exists is skipped and counted; a ledger the grammar rejects is one problem string and contributes no waits. A fixture repo with one batch worktree and a ledger holding one answered and two unanswered asks pins the output.
  - Blocked by: WO-0166
- [ ] **WO-0170** GitHub waits: green pull requests and gate queues — size:S, blocked by: WO-0166 (PRD-0014 §Success criteria, §Actors)
  - Accept: `live_state.github_waits(slug, listing, queues, now)` returns one wait per open, non-draft pull request whose check rollup is green, with `source` `github`, `key` `<slug>#<number>`, `text` the title, `since` the pull request's `createdAt`, and `route` `{url}`; and one wait per row of the console's existing `_queues` output with the issue's age. Red or pending pull requests and drafts produce no wait. The pull request listing is one `gh_read` call per repo per refresh, and the fixture listing covers green, red, pending and draft. Architecture.md's rate arithmetic (two reads per repo per minute) is restated in the function's docstring.
  - Blocked by: WO-0166
- [ ] **WO-0171** Session registry cross-check — size:S, blocked by: WO-0166 (PRD-0014 §Success criteria)
  - Accept: `live_state.registry(registry_dir, read)` reads every `*.json` under the registry directory through `cli.read_file` and accepts a file only when it is an object carrying `name`, `cwd`, `pid`, `sessionId` and a `status` in `busy`, `waiting`, `idle`; it supplies `name` and `cwd` to the matching session state by `sessionId`, and adds a session with no hook events to the strip with `verified` true and the registry's status. An absent directory or any file failing the guard returns `verified: false` with the reason for the whole strip, and the strip then shows only hook-known sessions. Fixtures cover a good registry, a file with a renamed key, a file with an unknown status, and no directory, each pinning the exact output.
  - Blocked by: WO-0166

## Milestone 3: Measured

The page says how long waits take, and the battery is green.

- [ ] **WO-0172** Asked-to-answered latency — size:S, blocked by: WO-0166, WO-0169 (PRD-0014 §Success criteria, §User stories)
  - Accept: `live_state.latency(lines, ledgers, now)` pairs each session's waiting event with its next working event and each ask row with the answer row that names it, keeps pairs whose end is within the last seven days, and returns per source `{count, median_s, p90_s}`, computed with `statistics` and nothing written anywhere. A session still waiting and an ask still unanswered contribute no pair. Fixtures with known durations pin the three numbers per source and the empty case.
  - Blocked by: WO-0166, WO-0169
- [ ] **WO-0173** Battery and close-out — size:S, blocked by: WO-0167, WO-0168, WO-0169, WO-0170, WO-0171, WO-0172 (PRD-0014 §Success criteria)
  - Accept: `python3 run_tests.py` reports 0 problems, `python3 lint.py` prints `lint: 0 problem(s)`, and `python3 gates.py && python3 gates.py --selftest` prints `gates: 0 problem(s)` and `selftest: ok`; `python3 kb.py drift` prints 0 problems after `docs/setup.md` and any CLAUDE.md or AGENTS.md line about the console are updated; `.claude-plugin/plugin.json`'s version is untouched (no `skills/` change, ADR-0095) and `factory/manifest.json` is unchanged (nothing added is mirrored); each checked row has its owner-session ledger row; no eval definition is edited.
  - Blocked by: WO-0167, WO-0168, WO-0169, WO-0170, WO-0171, WO-0172

## Design gaps found

None. Every component in architecture.md (Hook recorder, Live state,
Console live view) is built by a row above, and every PRD success
criterion is an acceptance line.

## Notes

- 2026-10-16 Backfill: prd.md and architecture.md were written at
  Decompose time under the protocol's soft gate, from idea.md and two
  Owner answers in session; their frontmatter carries the assumptions.
