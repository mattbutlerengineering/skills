---
stage: prd
run: feature:pr-body-preflight
date: 2026-10-16
ux: not-applicable
ux-reason: "CLI hook only (a PreToolUse hook on Bash); no screens or flows."
assumptions:
  - "Interview answered from autorun-brief.md in this directory; no live interview held. Every answer below traces to the brief's Owner decisions or to its sections marked as the orchestrator's reading."
---

# PRD: PR-body preflight hook

## Problem statement

A session in this repo opens a PR, and minutes later the `check` job is
red for a reason unrelated to the code: the body is missing a line that
detector B (`gates.check_pr_traceability`) requires. B reads the body from
the CI event payload, so it skips silently locally and fails only after
the PR exists (`docs/kb/pr-body-contract.md`). The failure reads like
flaky CI, and the fix is a second round-trip: a body PATCH through
`gh api` (`gh pr edit` is broken here), then a re-run on the `edited`
event. Now that the merge train and the hourly improvement routine open
PRs unattended, a red B stalls the train until someone patches it.

Evidence (observed, measured 2026-10-16 by the orchestrator, per the
brief): of the last 20 failed `validator.yml` `pull_request` runs
(2026-09-28 to 2026-10-16), 11 failed on a `B: PR body` problem, across 10
distinct branches. The backlog seed's earlier-window count (10 of the last
14 readable failed `check` jobs) is the same finding. Not re-measured at
this stage.

## Solution

When a session in this repo runs `gh pr create` with a body the hook can
read, the hook applies detector B's two body checks before the command
runs: a four-digit `WO-` token or a `No work order: <reason>` line, and a
closing keyword with an issue number. A body that fails is refused, with
B's own problem strings, so the session fixes the body and retries before
any PR exists. A body the hook cannot read, or a command it cannot parse,
goes through untouched with a one-line note, and CI still checks it.

## Actors

- **Owner session** — the Owner working interactively in this repo.
- **Pipeline Worker** — an autorun stage subagent or a conduct Worker
  that opens a PR as part of a run.
- **Scheduled routine** — an unattended cloud routine (merge train,
  hourly improvement) that opens PRs with no one watching.

## User stories

1. As an Owner session, I want a `gh pr create` with a non-conforming
   body refused locally with the exact missing line named, so that I fix
   it in seconds instead of reading a red CI run as flaky.
2. As a Pipeline Worker, I want the same refusal, so that the PR I open
   at Ship is green on detector B the first time.
3. As a Scheduled routine, I want the refusal before the PR exists, so
   that an unattended PR never stalls the merge train on a body line.
4. As any of these actors, I want a body the hook cannot read or a
   command it cannot parse to pass, so that the hook never blocks a
   legitimate PR creation.

## Success criteria

- [ ] A `gh pr create` with a literal `--body`/`-b` or a readable
      `--body-file`/`-F` that lacks the work-order line, the closing line,
      or both is refused: exit 2, with stderr carrying detector B's own
      problem strings.
- [ ] A body that passes detector B passes the hook (exit 0), and so does
      every command that is not a `gh pr create`.
- [ ] Unreadable bodies (`--fill`, `--fill-first`, `--web`,
      `--body-file -`, an editor) pass (exit 0) with a one-line note on
      stderr, and a parse the hook cannot complete passes too: the hook
      fails open, never closed.
- [ ] The check's patterns have one owner: a test or the `one_owner.py`
      pre-pass shows the hook calls detector B's code rather than
      carrying its own copy of the regexes.
- [ ] A replay test feeds fixture hook payloads through the hook and
      covers at least: a passing body, each missing line, `--body-file`
      with a real file, a heredoc-substituted body, a compound command
      (`cd x && gh pr create ...`), `--fill`, and a non-gh command.
- [ ] The hook is registered in the checked-in `.claude/settings.json`
      (not `settings.local.json`), as a PreToolUse hook on Bash pointing
      at the script.
- [ ] `python3 run_tests.py`, `python3 lint.py`, `python3 gates.py` and
      `python3 gates.py --selftest` all pass.

## Out of scope

- Shipping the hook to stamped repos (Owner decision: this repo only). It
  stays out of `factory_init.MIRRORS`.
- Bodies set by `gh pr edit` or a `gh api` PATCH.
- Changing detector B's rules or the PR template.
- Judging bodies the hook cannot read; those pass and CI catches them.

## Open questions

- How small can the `gates.py` change be that exposes B's checks over a
  body string instead of an event payload? (Refactoring there is in
  scope.) — Architect.
- How does the hook find the body in a heredoc or `$(cat file)`
  substitution it sees unexpanded, and which shapes does it treat as
  unreadable? — Architect, pinned by the replay fixtures.
