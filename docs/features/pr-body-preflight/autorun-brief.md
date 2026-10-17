# Autorun brief: pr-body-preflight

Not an artifact. Written 2026-10-16 by the orchestrator. The Owner invoked
`/idea-to-prod:autorun` with no description, then answered four questions
one at a time in session, each taking the recommended option:

1. What to drive: "PR-create body hook (Recommended)", the backlog seed
   at `docs/backlog.md` line 107 (from: session:2026-10-16).
2. Scope: "This repo only (Recommended)".
3. On a miss: "Block (Recommended)".
4. Release: "Prepare and stop (Recommended)".

Everything else below is the orchestrator's reading of the seed and of the
repo, marked as such. A stage that needs an answer this brief does not
hold applies the autorun rule: take a skill-supplied default and log it,
otherwise stop and surface.

## What and why

A Claude Code PreToolUse hook in this repo that, before `gh pr create`
runs, applies detector B's two checks to the pull request body:

- a four-digit `WO-` token or a `No work order: <reason>` line, and
- a closing keyword with an issue number (`Closes #N` and its kin).

Detector B (`gates.check_pr_traceability`) reads the body from the CI
event payload, so it skips silently locally and fails only after the PR
is open (`docs/kb/pr-body-contract.md`). Fixing it afterwards costs a body
PATCH through `gh api`, because `gh pr edit` is broken here. Then the
`edited` event re-runs the check. The hook moves the same check to
before the PR exists.

## Idea-stage inputs

- **Problem, from the sufferer's view.** An agent or Owner session opens
  a PR, and minutes later the `check` job is red for a reason that has
  nothing to do with the code: the body is missing a line. It reads like
  flaky CI (memory note `pr-body-no-work-order-waiver`), and the fix is a
  second round-trip.
- **Who has it, and how they cope today.** Every session in this repo
  that opens PRs: Owner sessions, autorun and conduct Workers, and the
  scheduled routines. Today they cope by remembering the rule, through the
  kb page, the memory note and `.github/PULL_REQUEST_TEMPLATE.md` (which
  only applies to PRs opened in the web UI or with `--template`). They
  also cope by patching the body after CI goes red.
- **Why now.** The merge train and the hourly improvement routine
  (created 2026-10-15) open PRs unattended. A red B on an unattended PR
  stalls the train until someone patches it.
- **Evidence (observed, measured 2026-10-16 by the orchestrator).** Of
  the last 20 failed `validator.yml` `pull_request` runs (2026-09-28 to
  2026-10-16), 11 failed on a `B: PR body` problem, across 10 distinct
  branches, including `fix/conflict-avoidance` (#954) on 2026-10-16. The
  seed's own count, 10 of the last 14 readable failed `check` jobs, is
  the same finding from an earlier window.
- **Rough shape of a solution (a hunch).** A small stdlib Python script
  registered as a PreToolUse hook on Bash in `.claude/settings.json`. It
  reads the hook's JSON from stdin, and when the command is a
  `gh pr create`, it finds the body from `--body`/`-b` or
  `--body-file`/`-F`. It runs B's checks with B's own code, so there is
  no second copy of the regexes. On a failure it exits 2 with the
  problems on stderr.
- **Success, in one sentence.** A `gh pr create` whose body would fail
  detector B is refused before the PR exists, and no legitimate PR
  creation is ever blocked.
- **Biggest unknowns, and how this dies.** (a) Command parsing: shell
  quoting, heredoc bodies (`--body "$(cat <<'EOF' ...)"`), `$(cat file)`
  substitutions the hook sees unexpanded, and compound commands (`cd x &&
  gh pr create ...`). (b) A false block on a legitimate PR would teach
  sessions to route around the hook, which is worse than no hook.
  (c) A hook that is never exercised is an untested config, so it needs
  a replay test over fixture commands.

## Scope

In:

- the hook script, its registration in this repo's `.claude/settings.json`,
  and tests that replay fixture hook payloads through it;
- reusing detector B's checks from their owner (`gates.py` /
  `knowledge_plane.py`), with no second copy of the regexes. If a
  refactor in `gates.py` is needed to expose a body-only check, that is
  in scope.

Out:

- shipping the hook to stamped repos (Owner decision 2: this repo only).
  It is root-only and stays out of `factory_init.MIRRORS`, per ADR-0060's
  rule;
- bodies the hook cannot read (`--fill`, `--fill-first`, `--web`, stdin
  with `--body-file -`, an editor). These pass with a one-line note on
  stderr, and CI still catches them;
- `gh pr edit` and `gh api` PATCH bodies;
- changing detector B itself, or the PR template.

## Success criteria

- A `gh pr create` with a literal `--body` or a readable `--body-file`
  that lacks either line is refused: exit 2, with stderr carrying B's own
  problem strings.
- A body that passes B passes the hook (exit 0), as does every
  non-`gh pr create` command.
- Unreadable bodies pass with a note. A parse the hook cannot complete
  fails open, never closed (Owner decision 3 blocks only on a body it read
  and judged).
- The replay test covers at least: passing body, each missing line,
  `--body-file` with a real file, a heredoc-substituted body, a compound
  command, `--fill`, and a non-gh command.
- `python3 run_tests.py`, `python3 lint.py`, `python3 gates.py` and
  `python3 gates.py --selftest` all pass.

## Constraints and already decided

- Stdlib only (CLAUDE.md hard convention).
- The hook is registered in the checked-in `.claude/settings.json`, which
  is today an empty object, not in `settings.local.json`.
- One owner per fact: the check is B's code, imported, not retyped.
  `python3 one_owner.py` is the review pre-pass for this.
- No plugin version bump: no `skills/` change (ADR-0095).
- Owner decision 3, block: exit 2 on a judged body. Decision 2, root-only.

## Tracker

No issues seed the run, and there is no tracker interaction before Ship.
At Ship, the PR needs `Closes #N` (detector B). Ship files one plain
`type:feature` issue for the run if none exists, and closes it from the
PR. The PR body must pass the run's own hook.

## User-facing surface

None in the UX-stage sense. It is a CLI hook with no screens or flows.
The PRD's `ux:` decision is expected to record it as not required.

## Release authorization

Prepare and stop (Owner decision 4). Ship pushes the branch, opens the
PR, records `outcome: prepared` with `pending-merge: <PR url>`, and
stops. No merge. The orchestrator asks the Owner about the merge after
the run.

stop-after: ship
