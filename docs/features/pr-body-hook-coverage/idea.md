---
stage: idea
run: feature:pr-body-hook-coverage
date: 2026-11-09
origin: "Backlog seed at docs/backlog.md line 237 (from: feature:pr-body-preflight), bind a heredoc to the file it writes; evidence in issue #1633 and the pr-body-preflight retro. Interview held live with the Owner in session: ladder pick, success sentence and biggest risk were answered by the Owner."
assumptions:
  - "In-flight check ran, nothing matches: gh pr list --state open returned no pull requests; git branch -a --no-merged origin/main and git worktree list showed pr-body branches only for the already merged pr-body-preflight run and its kb pages; agent/heredoc-delimiter-is-guessable (2026-08-27, cli.py) is an unrelated fix; docs/features/ holds no run for this surface."
  - "The problem sentence is quoted from the pr-body-preflight retro, not coined by the Owner in this session; the Owner chose the rung and the success measure."
  - "Who and Why now are taken from the retro and #1633; the Owner was not asked them separately, as the feature-run interview scales down."
---

# Idea: Judge the same-call heredoc body

> The hook judged 9 of 210 historical `gh pr create` commands, "so unattended routines still go red on bad bodies it cannot see." (pr-body-preflight retro, Evidence section; re-measured at 158 of 1805 in #1633)

## Problem

An agent opens a pull request in one Bash call that writes the body and runs `gh pr create`: `cat > F <<'EOF' ... EOF`, then `gh pr create --body-file F`. The PR-body hook reads a body file only from the first command, so at hook time the file is absent or stale and the hook passes the command unjudged. Detector B then fails the PR in CI, after it is open. Of 1805 replayed commands, 681 (38%) are this one shape.

## Who has it

The Owner and the agent sessions and unattended routines that run under the Owner's account (all 319 PRs since 2026-10-17 are from one account). Today they cope by opening the PR, seeing a red B check, and fixing the body through `gh api` (docs/kb/pr-body-contract.md).

## Why now

The hook shipped 2026-10-17 with a measured judged share of about 4%, and its retro left the decision to re-measure and then bind heredocs open. The re-measure is done (8.8%), and it shows the same-call heredoc is the single shape big enough to move the number.

## Evidence

- Measured, one replay: 158 of 1805 unique `gh pr create` commands judged (8.8%); 681 unjudged because the body file is read only from the first command (#1633). The corpus is the Owner's own session transcripts, all sessions, not only unattended routines.
- Anecdote: before the hook, 7 of 266 PRs lacked the B contract; after, 0 of 319. Not attributable to the hook (retro, graded anecdote).
- Unobserved: false blocks in live use, and live coverage. The hook logs nothing.

## Ambition rung

Chosen: Showstopper, in the Owner's words: "Showstopper: judge the same-call heredoc body"
Not taken: Solid: re-measure and log, no parser change; Moonshot: judge every PR body at the forge for any tool, not only through this hook
Demo: pass — a command that writes a bad body to a file by heredoc and runs `gh pr create --body-file` on it is refused with B's own strings, before any PR exists
Removes a step: pass — the agent no longer opens a PR to learn its body fails B
Only this product: pass — it reuses `gates.pr_body_problems`, B's one owner, and this repo's hook registration
Achievable: pass — riskiest piece is a false block; a two-day spike replays the 681 same-call commands and diffs the hook's verdict against B's on each

## The demo

Before: an agent runs `cat > /tmp/b.md <<'EOF'` with no work-order line, then `gh pr create --body-file /tmp/b.md`; the hook passes it, the PR opens, B goes red. After: the same command exits 2 with B's problem strings and the PR is never created.

## Riskiest piece + spike

A false block: binding a heredoc to a file misreads a body B accepts, and a Bash call is refused wrongly. Spike, about two days: replay the 681 same-call commands in the transcript corpus, bind each heredoc to its file, and compare the hook's verdict with detector B's on the same body. Any refusal B would not give is a failure.

## Cheapest kill test

Run the binding over a sample of 50 of the 681 commands and read each refusal against B by hand. One false block in 50 kills the approach as written.

## Solution hunch

Within one Bash command, treat `cat > F <<D` as the writer of F and a later `--body-file F` in the same compound command as reading that heredoc's text. A hunch, not a design: where the binding lives, and what it does when F is rewritten or deleted before `gh pr create`, are for Architect.

## Success in one sentence

The replay judged share rises from 8.8% to at least 40% on the same 1805-command corpus, with no refusal that detector B would not also give.

## Unknowns & risks

- A false block, the Owner's named biggest risk: the binding refuses a body B accepts.
- The shell's real behaviour: F may be rewritten or removed between the heredoc and `gh pr create` inside one compound command, so the judged body is not the one gh reads.
- The 40% target is measured on past commands; live coverage stays unobserved until a refusal log exists (a retro seed).
- Roughly 320 of the unjudged commands name a body file written in an earlier call and gone by hook time; this idea does not reach them.
