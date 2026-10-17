---
stage: idea
run: feature:pr-body-preflight
date: 2026-10-16
origin: "Backlog seed at docs/backlog.md line 107 (from: session:2026-10-16), the PR-create body hook, chosen by the Owner as the first of four autorun answers. Interview answered from autorun-brief.md in this directory; no live interview held."
assumptions:
  - "In-flight check ran, nothing matches: `gh pr list --state open` returned no open PRs; a title search for preflight / \"pr body\" / hook found only merged, unrelated PRs (#933, #611, #687, #851, #217); `git branch -a` showed feat/open-pr-preflight (e6e8371, the open-PRs-first drain for work-starting skills, touching skills/next, skills/work-queue and tests/test_open_pr_preflight.py), which is a different change and not this one; no open issue matches."
  - "Seed claim not written: the stage skill says to append `(claimed: feature:pr-body-preflight)` to the seed's line in docs/backlog.md, but this stage was told to commit only idea.md, so the claim is left for the orchestrator to apply."
---

# Idea: PR-body preflight hook

## Problem

An agent or Owner session opens a PR, and a few minutes later the `check`
job goes red for a reason that has nothing to do with the code: the PR
body is missing a line. It looks like flaky CI. Fixing it takes a second
round-trip: a body PATCH through `gh api` (`gh pr edit` is broken here),
and then the `edited` event runs the check again. Detector B
(`gates.check_pr_traceability`) reads the body from the CI event payload,
so locally it skips without a word and fails only after the PR is open
(`docs/kb/pr-body-contract.md`).

## Who has it

Every session in this repo that opens PRs: Owner sessions, autorun and
conduct Workers, and the scheduled routines (merge train, hourly
improvement). How they cope today:

- They try to remember the rule, from the kb page, the memory note on
  the "No work order" waiver and `.github/PULL_REQUEST_TEMPLATE.md`. The
  template only applies to PRs opened in the web UI or with `--template`,
  not to `gh pr create --body`.
- They patch the body after CI goes red.

## Why now

The merge-train and hourly improvement routines (created 2026-10-15) now
open PRs unattended. When B goes red on an unattended PR, the train stalls
until someone patches the body.

## Evidence

- **Observed, measured 2026-10-16 by the orchestrator** (per the brief):
  of the last 20 failed `validator.yml` `pull_request` runs (2026-09-28 to
  2026-10-16), 11 failed on a `B: PR body` problem. They span 10 distinct
  branches, including `fix/conflict-avoidance` (#954) on 2026-10-16.
- **Observed, earlier window** (the backlog seed's own count): 10 of the
  last 14 readable failed `check` jobs were `B: PR body has no Closes #N
  link`. This is the same finding over an earlier window.
- **Anecdote:** sessions misread the failure as flaky CI (memory note
  `pr-body-no-work-order-waiver`).

This stage did not re-measure either count.

## Solution hunch

A small stdlib Python script registered as a PreToolUse hook on Bash in
the checked-in `.claude/settings.json` (an empty object today). It reads
the hook JSON from stdin. When the command is a `gh pr create`, it pulls
the body from `--body`/`-b` or `--body-file`/`-F` and runs detector B's
two checks using B's own code, so there is no second copy of the regexes:

- a four-digit `WO-` token or a `No work order: <reason>` line, and
- a closing keyword with an issue number (`Closes #N` and similar).

On a body it read and judged as failing, the hook exits 2 and prints B's
problem strings on stderr (Owner decision: block). It passes any body it
cannot read, with a note. This covers `--fill`, `--web`, stdin and an
editor, and CI still catches those. The hook is for this repo only (Owner
decision) and stays out of `factory_init.MIRRORS`.

## Success in one sentence

A `gh pr create` whose body would fail detector B is refused before the
PR exists, and no legitimate PR creation is ever blocked.

## Unknowns & risks

- **Command parsing.** The hook sees the command before the shell expands
  it. That covers shell quoting, heredoc bodies (`--body "$(cat <<'EOF'
  ...)"`), `$(cat file)` substitutions and compound commands (`cd x && gh
  pr create ...`). Any of these can make the hook misread the body.
- **False blocks kill it.** If the hook blocks one legitimate PR, sessions
  learn to route around it, and that is worse than having no hook. When
  the hook cannot finish a parse, it must fail open, never closed.
- **An untested config.** A hook that never runs in a test is just
  configuration nobody has checked. It needs a replay test over fixture
  hook payloads, or it rots unnoticed.
- **Getting at B's checks.** B reads the body out of an event payload. To
  call a body-only check, `gates.py` may need a small refactor (that is in
  scope). The open question is how small that refactor can be.
