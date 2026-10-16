---
stage: architect
run: feature:live-console
date: 2026-10-16
ux: skipped — v1 adds one ordered list and one status strip to the existing process console page (PRD-0002) and designs no new flow or screen; UX Design is owed before any action buttons (v2)
assumptions:
  - "Backfill at Decompose time (protocol soft gate): the two trade-offs that could have gone another way were put to the Owner in session on 2026-10-16 and are decided below as answered (hooks write events, the registry is a guarded cross-check; v1 is read-only). The remaining decisions are taken against the repo's own conventions and recorded one line each."
  - "Hook facts are the Claude Code docs as read on 2026-10-15/16 (hooks, sessions, cross-session-messaging, statusline, headless): the events, their stdin fields, that a command hook may write files, that hooks at user and project level both run, and that transcripts and the messaging socket are not external interfaces. Where the docs are silent (which events fire under claude -p; whether PostToolUse fires for AskUserQuestion) the design degrades to what the events do carry, and the PRD's Open questions record it."
  - "The session registry (~/.claude/sessions/<pid>.json: name, cwd, pid, sessionId, status in busy|waiting|idle, statusUpdatedAt, messagingSocketPath) is undocumented and observed on this machine only. It is read behind a shape guard and never trusted alone."
  - "No ADR: no decision below passes all three legs of the protocol's bar. Read-only is additive to reverse (buttons are a later addition behind the same data), the events file is operator-local state, and the hook shape is configuration. Each keeps its one-line record in Decisions & alternatives."
---

# Architecture: Live console

## Approach

Grow the process console rather than build a second one. `dashboard.py
serve` already binds localhost, gathers one repo per request through the
seams that own each fact (`human_gates.open_queues` for gate waits,
`cli.gh_read` for GitHub), and renders a page the operator already opens.
The live view adds one source the console has never had — what local
Claude Code sessions are waiting on — and one fold over three sources
into a single list. The session source is the part nothing else can see,
so it is the part this design is careful about: a hook recorder, run by
Claude Code's own hook events at user level, appends one small line per
event to an append-only events file under the operator's Claude config
directory; the console reads that file. Everything else is a read the
repo already knows how to make (ledger rows, `gh` listings), folded by one
pure module, `live_state.py`, and served by one new endpoint. The design
compared two shapes: this one, and a poller that reads the undocumented
session registry and the transcripts directly. The poller loses because
its only inputs are interfaces the docs say may change without notice and
its timing is only as good as its poll; the hooks give the exact moment a
wait began and ended, on a documented, versioned surface, and the registry
is kept as a guarded cross-check for names and liveness.

## Components

### Hook recorder (`live_hook.py`)

- Responsibility: turn one Claude Code hook invocation into one line in
  the events file, fast, and never block or fail the session that fired
  it. Also prints the hooks block the operator merges into
  `~/.claude/settings.json` (`--settings`).
- Collaborators: Claude Code (stdin JSON, one of eight events), the
  events file. Imports nothing from the console; it is an adapter that
  translates and appends.

### Live state (`live_state.py`)

- Responsibility: the policy. Fold event lines into per-session states
  and open waits; read unanswered asks out of batch ledgers; shape
  GitHub listings and gate-queue rows into waits; merge the three into
  one list, oldest first; compute asked-to-answered durations; read the
  session registry behind its guard. Pure functions with every input
  passed in, `dashboard:`-prefixed problem strings, no I/O of its own
  except through injected readers.
- Collaborators: `conductor.py` (the ledger grammar's one owner: row
  kinds `ask` and `answer`, `COMMON_FIELDS`), `human_gates.open_queues`
  (ADR-0090), `cli.read_file` for the guarded local reads (ADR-0075),
  `cli.gh_read` for GitHub.

### Console live view (`dashboard.py`)

- Responsibility: one new GET route, `/api/live`, that calls
  `live_state.gather` over the configured repo set and returns its dict;
  the page's headline list and who-is-doing-what strip, refreshed by the
  client every 60 seconds or less. No new POST route.
- Collaborators: `live_state`, `dashboard.repo_set` (which checkouts the
  console observes — operator state in `~/.process-dashboard.json`, as
  today), the existing `_queues`.

## Data model

Three shapes, chosen from the reads the PRD requires (list waits oldest
first; list sessions; summarise durations), not from the nouns.

**Event line** — one JSON object per line, append-only, in
`~/.claude/live/events-<UTC date>.jsonl` (directory overridable by
`CLAUDE_LIVE_DIR`, for tests and for a second machine). Fields: `v` (1),
`at` (UTC ISO-8601), `event` (the hook event name), `session_id`, `cwd`,
`transcript_path`, and when the event carries them `notification_type`,
`tool_name`, `tool_use_id`, `message` (first 500 characters). Nothing
else is kept: no tool inputs, no prompt text, no transcript content. The
reader takes today's and yesterday's files, so the file never needs a
rotation step beyond the date in its name.

**Session state** — derived, never stored: `{session_id, name, cwd,
transcript_path, state, kind, text, since, last_event_at, verified}`.
`state` is one of `working`, `waiting`, `idle`, `ended`. `kind`, present
when waiting, is one of `permission`, `question`, `plan`, `elicitation`,
`agent_needs_input`. The fold is a state machine over the line sequence
of one `session_id`:

| Event | Becomes |
|---|---|
| `PermissionRequest`; `Notification` with `permission_prompt` | `waiting`, kind `permission` |
| `PreToolUse` on `AskUserQuestion` | `waiting`, kind `question` |
| `PreToolUse` on `ExitPlanMode` | `waiting`, kind `plan` |
| `Notification` with `elicitation_dialog` or `elicitation_url_dialog` | `waiting`, kind `elicitation` |
| `Notification` with `agent_needs_input` | `waiting`, kind `agent_needs_input` |
| `UserPromptSubmit`; `PostToolUse`; `PreToolUse` on any other tool; `SessionStart` | `working` |
| `Stop`; `Notification` with `idle_prompt` | `idle` |
| `SessionEnd` | `ended` |

A `waiting` session whose `PermissionRequest` and `permission_prompt`
both arrive keeps the earlier `since`. A session with no event for 30
minutes and no registry liveness is shown as `stale`, a display flag on
top of its last state, never a fifth state. The invariant "a session is
in exactly one state, and `since` is the time of the event that put it
there" is owned by the fold; nothing else writes states.

**Wait** — the headline row, one shape for all three sources:
`{source, key, kind, text, since, waited_s, route}`. `source` is
`session`, `conductor` or `github`; `key` is the session id, `<batch>/<ask
id>`, or `<owner>/<repo>#<number>`; `route` is what the operator does
next — `{name, cwd, transcript_path}` for a session, `{command: "python3
conductor.py answer <batch> <ask-id>", options, recommended, why}` for an
ask, `{url}` for a pull request or gate issue. Sorted by `waited_s`
descending.

**Latency record** — derived on read, never stored separately: for each
closed wait, `(source, kind, started_at, ended_at)`. Session durations
come from a `waiting` event followed by the next `working` event of the
same session; Conductor durations from an `ask` row's `at` to the
`answer` row's `at` that names it. The page shows count, median and p90
per source over the last seven days. Nothing is written: the events file
and the ledgers already hold both ends.

Consistency: every read may settle within one refresh (60 seconds). No
read needs to be true the instant anything returns, which is why the
whole design is files and polling, with no process talking to a session.

## Interfaces & contracts

### Hook invocation → event line

- Input: the hook's stdin JSON (`hook_event_name`, `session_id`, `cwd`,
  `transcript_path`, and the event's own fields), `CLAUDE_LIVE_DIR`.
- Output: one appended line, or nothing. Exit 0 in every case; stdout
  empty (a hook's stdout is read by Claude Code, so the recorder prints
  nothing on the event path).
- Failure modes: malformed or empty stdin, an unknown event, an
  unwritable directory — each writes one line to stderr and exits 0. The
  recorder never returns a decision, never blocks, and does no work that
  can take longer than opening a file and appending to it. A hook that
  times out is discarded by Claude Code; the recorder's budget is far
  under any event's limit.

### `live_state.gather(repos, live_dir, registry_dir, now, read, gh)`

- Input: the configured repo paths, the events directory, the registry
  directory, a clock, the guarded file reader and the read-only `gh`
  runner (both injected, so tests pass fakes).
- Output: `{"waits": [...], "sessions": [...], "latency": {...},
  "problems": [...]}` — the shapes above, waits sorted oldest first, the
  strip carrying `verified: false` and a reason when the registry failed
  its guard.
- Failure modes: a missing events directory is an empty session list and
  no problem (nothing has reported yet); a line the JSON parser refuses or
  with `v` other than 1 is skipped and counted into one problem string per
  file; a ledger `cli.read_file` refuses is one problem string and that
  batch contributes no waits; a `gh` read that fails is reported through
  the existing `gh_read` problem strings and that repo contributes no
  GitHub waits; a registry file that fails the shape guard flips the strip
  to `unverified` for that refresh and the strip shows hook-known sessions
  only. Every failure is visible on the page; none hides a wait silently.
  Rate: two `gh` reads per repo per refresh (pull requests, and the gate
  timelines the console already reads), at one refresh a minute, is 2,880
  calls a day per repo against a 5,000-an-hour limit.

### `GET /api/live`

- Input: none (the repo set comes from the console's config, as today).
- Output: the `gather` dict as JSON; `Cache-Control: no-store`.
- Failure modes: the same as today's `/api/repo` — the page renders what
  came back and lists `problems` beside the data. The console still binds
  `127.0.0.1` only, and this route, like every GET, writes nothing.

### Conductor asks in a configured repo

- Input: a repo path. The batch ledger is uncommitted in its batch
  worktree until `close` (the conduct skill's rule), so the reader lists
  the repo's worktrees (`git worktree list --porcelain`, through the
  injected runner), keeps those on a `conductor/<batch>` branch, and reads
  `docs/factory/batches/<batch>/ledger.jsonl` in each, plus any ledger
  committed under the repo's own `docs/factory/batches/`.
- Output: one wait per `ask` row that no `answer` row names, with the
  row's `question`, `options`, `recommended`, `why`, `item` and `at`.
- Failure modes: a worktree path that no longer exists is skipped and
  counted; a ledger with a row `conductor.py`'s grammar rejects is one
  problem string, and that ledger contributes no waits.

## Stack & dependencies

- Python 3 standard library only — the repo's hard convention
  (`stdlib-only`); `http.server`, `json`, `pathlib`, `statistics` are
  already what `dashboard.py` uses.
- Claude Code hooks as the session source — the one documented interface
  through which a session's waiting moment leaves the process; a large
  surface used through eight events and six fields, so its cost is the
  configuration block, not types spread through the code.
- `gh` through `cli.gh_read` — the existing seam and the existing
  credential; no new network dependency and no MCP server (#844 showed
  what MCP-only GitHub costs a routine).
- No new file format: the events file is JSON lines, the same family as
  `docs/factory/costs.jsonl`, and a reader can parse a day of it in well
  under a second.

## Decisions & alternatives

- **Hooks write events; the registry is a guarded cross-check** over
  registry-only polling and over hooks alone — the Owner's answer,
  2026-10-16. Hooks give the exact asked and answered moments on a
  documented surface; the registry alone is undocumented and poll-grained,
  and hooks alone cannot name a session or see one that has fired no
  event since the console started.
- **Read-only v1** over merge and gate buttons in place — the Owner's
  answer, 2026-10-16. The success sentence is met by seeing and
  measuring; a write path with the operator's credential is a different
  feature with its own audit question, and the page can never become an
  agent's merge route.
- **An append-only JSON-lines file under `~/.claude/live/`** over SQLite
  and over a per-repo file — operator state lives beside
  `~/.process-dashboard.json`, not in any repo; sessions in every repo and
  worktree write to one place; JSON lines is the ledger grammar the repo
  already reads (`stdlib-only` either way).
- **User-level hook configuration** over this repo's
  `.claude/settings.json` — the sessions that wait on the operator run in
  every repo, worktree and consumer checkout, and a repo-level hook would
  see only this repo's. The cost is one Owner step, printed by
  `live_hook.py --settings` and merged by hand.
- **`PermissionRequest` and `Notification` both** over either alone —
  `PermissionRequest` fires at once but only for tool permissions;
  `Notification` lags about six seconds and is the only signal for idle,
  elicitation and `agent_needs_input`. The fold dedupes them on the
  session.
- **No transcript parsing and no socket reads** — the docs call the
  transcript format internal and the messaging socket a per-session
  inbox; the recorder carries `transcript_path` as a locator only.
- **Durations computed on read from the two ends already persisted** over
  a timer in the hook or a second file — hooks are stateless and must
  return fast, and the events file and the ledgers already hold both
  timestamps.
- **Reuse `human_gates.open_queues` and `conductor.py`'s row grammar**
  over a second reading of either — one owner per fact (ADR-0090 for the
  gate timeline read; `conductor.py` is the ledger's one owner).

## ADRs

None — no decision met the ADR bar. Read-only is additive to reverse, the
events file is operator-local state, and the hook shape is
configuration; each keeps its one-line record above.
