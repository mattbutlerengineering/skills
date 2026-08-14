---
stage: architect
run: feature:process-dashboard
date: 2026-08-13
---

# Architecture: Process dashboard v1

## Approach

A local, operator-level console: `python3 dashboard.py serve` starts a
stdlib HTTP server bound to localhost and opens one page,
`dashboard.html` (inline CSS + vanilla JS, no external assets). The
console is mostly a *renderer over seams that already exist* —
`protocol.py` answers run orientation, `knowledge_plane.py` walks
breakdown rows, `cost_ledger.py` reads spend, `gate_digest.py`'s pure
functions compute queue ages, and `cli.py`'s `gh_runner` is the one
GitHub port — so the genuinely new surface is small: serving, a
repo-set config, drift computation, and the backlog write path. Repos
are observed through their local checkouts (disk for the knowledge
plane, authenticated `gh` for the dispatch plane); every gather is
fresh at page load, one request per repo, so the UX's progressive fill
falls out of the request shape. The console observes stamped repos but
is never itself stamped — operator-level tooling, out of
`factory_init.MIRRORS`, no detector-E involvement.

## Components

### `dashboard.py` (new, repo root)

- Responsibility: the CLI (`serve [--port N] [--config PATH]`, plus a
  `gather <repo-path>` leg that prints one repo's state JSON for tests
  and scripting), the localhost HTTP server, and the three endpoints.
  Handlers are thin over pure gather/reorder functions with injected
  `run=gh_runner` and injected clock, per the repo's test discipline.
- Collaborators: `protocol.py`, `knowledge_plane.py`, `cost_ledger.py`,
  `factory_config.py`, `gate_digest.py` (pure functions), `cli.py`.

### `dashboard.html` (new, repo root, served as-is)

- Responsibility: the one-page UI from `ux.md` — needs-you strip, repo
  cards, per-repo backlog with drag + explicit Save, factory output,
  metrics. Fires `GET /api/repo?i=N` per configured repo and renders
  sections as answers land; renders per-repo problem strings in place.
- Collaborators: `dashboard.py`'s endpoints only. No external requests
  besides links out to GitHub.

### Gather (functions in `dashboard.py`)

- Responsibility: one repo path → the per-repo state dict (runs with
  next stage, gate queues with ages, backlog seeds, work-order output,
  metrics, drift flags, problems). Disk reads through the seams; gh
  reads through `gh_json`; every failure becomes a problem string in
  the dict, never a lost section (fail loud, render on).
- Collaborators: all seam modules; `gate_digest.GATES`/`label_events`/
  `waiting_since` for queues; `cost_ledger.read` + `gate_wait` for
  metrics; derives acceptance/rework from `gh` review data on WO-cited
  PRs and folds in `docs/factory/corrections.jsonl` when present
  (WO-0018's stream) — absent is normal, not an error.

### Drift check (function in `dashboard.py`)

- Responsibility: cross-plane disagreement per repo: a breakdown row
  unchecked while its `(tracker: #N)` issue is CLOSED (#123's class),
  and the inverse (row checked, mirror still OPEN). Returns
  problem-string-shaped findings rendered in the needs-you strip.
- Collaborators: `knowledge_plane.py` row accessors, `gh_json`.

### Backlog reorder (function in `dashboard.py`)

- Responsibility: apply a posted seed order to a repo's
  `docs/backlog.md` — permutation-only, claim markers intact,
  concurrency-guarded. The file's non-seed lines (header prose) keep
  their positions; only seed lines move.
- Collaborators: the backlog grammar as specified in
  `docs/pipeline-protocol.md` (ADR-0029).

### Operator config (`~/.process-dashboard.json`)

- Responsibility: the repo set — `{"repos": ["/abs/path", ...]}`.
  Argv paths override the file; no config and no argv is the
  "no repos configured" empty state pointing here.
- Collaborators: `dashboard.py` startup only. Deliberately not
  `factory.json` (that is per-repo config; this is operator-level,
  cross-repo).

## Data model

Per-repo state (the `/api/repo` payload; also `gather`'s stdout):

```
{ "repo":     {"path", "name", "remote"},         # remote for links
  "runs":     [{"ref", "dir", "stage", "next"}],  # protocol orientation
  "queues":   [{"gate", "issue", "title", "waited_s", "url"}],
  "backlog":  {"hash", "seeds": [{"line", "text", "claimed"}]} | null,
  "output":   [{"wo", "title", "size", "state", "pr", "url", "spend"}],
  "metrics":  {"month_spend", "cap", "cost_per_wo", "gate_wait_median",
               "acceptance", "rework"},            # trend arrays TBD-simple
  "drift":    ["<finding string>", ...],
  "problems": ["<label>: <what failed>", ...] }
```

`backlog.hash` is a content hash of the file at gather time — the
optimistic-concurrency token the Save posts back. Work-order lifecycle
`state` comes from the mirror's `wo:*` label (dispatch plane) with the
breakdown row (knowledge plane) as the drift cross-check, never a
second source of truth (ADR-0032).

## Interfaces & contracts

### `GET /api/repos`

- Input: none.
- Output: the configured repo list (name + index), so the page knows
  how many `/api/repo` calls to fire.
- Failure modes: unreadable config → 500 with a problem string the
  page shows as the whole-page error state.

### `GET /api/repo?i=N`

- Input: repo index into the configured set.
- Output: the per-repo state dict above. Partial failure is not an
  HTTP failure: a gather problem lands in `problems` (or section-level
  `null`) and the section renders the string.
- Failure modes: out-of-range index → 404; a repo path that no longer
  exists → 200 with `problems` carrying the one finding.

### `POST /api/backlog-order`

- Input: `{"i": N, "hash": "<from gather>", "order": [line indices]}`.
- Output: 204 on success (file rewritten, seed lines in new order,
  claim markers and non-seed lines untouched).
- Failure modes (all render beside the Save button, dirty state kept):
  stale hash → 409 "backlog changed underneath; refresh"; order not a
  permutation of current seed lines → 400 (the console never adds,
  drops, or edits a seed — producers append, ADR-0029); write OSError
  → 500 with the OS detail.

### `dashboard.py gather <repo-path>`

- Input: one repo path.
- Output: the state dict as JSON on stdout — the testable seam and the
  scripting hook; `serve` is the same function behind HTTP.
- Failure modes: problem strings inside the JSON, exit per the repo's
  `cli.report` convention.

## Stack & dependencies

- Python stdlib only (`http.server`, `json`, `hashlib`) — hard repo
  convention; nothing here needs more.
- Vanilla JS + inline CSS in one served file — no CDN, no build step;
  the page works offline except GitHub links.
- `gh` CLI via `cli.gh_runner` — the repo's one GitHub port; tests
  inject `FakeGh`.
- Server binds `127.0.0.1` only; the write endpoint exists, so the
  console is never exposed off-box in v1 (no auth story by design).

## Decisions & alternatives

- **Local stdlib server** over static generation — the backlog Save
  needs a write path and fresh-on-open needs a gather step; a static
  page has neither. Over a hosted page — hosting toil, remote auth,
  and a remote write path fight the stdlib/no-infra grain.
- **Local checkout + gh** over GitHub-API-only — the seams already
  read disk; API-only re-implements them chattily and turns the
  backlog write into a push to main. Consequence accepted: a repo must
  be cloned to be observed.
- **Direct uncommitted write** for backlog Save over auto-commit — the
  backlog is advisory, never orientation state (ADR-0029); the console
  stays out of git entirely.
- **Derive acceptance/rework at gather** over new instrumentation —
  gh review data answers it live, and WO-0018 is already building the
  durable correction stream; a second correction-shaped ledger would
  be the exact drift this factory exists to catch.
- **Operator-level, never stamped** over joining `MIRRORS` — the
  console observes many repos from one seat; stamping copies into
  every repo would multiply detector-E churn for a tool no product
  repo runs in CI. Reversible later if a repo-local console is wanted.
- **One `dashboard.py`** over a package split — matches the
  one-standalone-script-per-tool grain; if it outgrows the repo's
  file-size norms, the split is Implement's to propose, not this
  design's to presuppose.
- **`~/.process-dashboard.json`** for the repo set over `factory.json`
  — factory.json is per-repo; the repo *set* is operator-level state
  no single repo owns.

## ADRs

None — no decision met the ADR bar (all are reversible and locally
explicable; the nearest candidate, operator-level-never-stamped, is
one `MIRRORS` line to reverse).
