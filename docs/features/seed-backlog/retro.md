---
stage: operate
run: feature:seed-backlog
date: 2026-07-06
---

# Retro: seed backlog

Written immediately after shipping (merged as `605ecb8` today) — this retro
reflects the run and first self-use, not accumulated usage. A honest
outcomes check needs a few future sessions; revisit then if the file isn't
earning its keep.

## Outcomes vs. intent

### Success in one sentence (idea.md): "the next run starts from the backlog instead of memory"

- What happened: not yet observable — the convention shipped minutes ago.
  The mechanism is in place: 6 unclaimed seeds are live in
  `docs/backlog.md` and `next` now lists them in its no-active-run moment.
- Signal strength: anecdote (self-use only; the real test is the next
  session's "what's next").

### Every entry lint-checkable; operate appends; next lists; claim in place

- What happened: all four PRD criteria passed Verify with quoted evidence;
  post-release smoke on main re-confirmed (146 tests OK, lint 0/15, live
  backlog parses 7 entries / 1 claimed / 0 problems). This retro itself
  exercises the operate-appends convention for the first time — the seeds
  below were appended to `docs/backlog.md` per the new protocol section.
- Signal strength: measured (for conformance); anecdote (for the loop).

## Run retrospective

- Keep: dogfooding the pipeline on its own repo — every stage ran for real
  with maintainer interview answers, and it surfaced a genuine process gap
  (see verification.md commit miss below). Draft-first stages moved fast;
  the interview questions that mattered (grammar home, origin form, read
  moments) were exactly the ones Architect flagged as trade-offs.
- Keep: the "no `description:` frontmatter edits" guardrail — trigger evals
  stayed pinned through a 10-commit feature with zero eval churn.
- Change: stage skills say "commit the artifact" implicitly at best —
  `verification.md` was written but never committed on the branch and was
  only caught untracked after merge. Stage skills (or the protocol) should
  make artifact-commit part of the stage's definition of done.
- Change: interview batching — the harness's multi-question prompt
  (AskUserQuestion) batches naturally, while the skills mandate one
  question at a time; the run worked but the mismatch produced awkward
  pacing. Worth reconciling in skill prose.
- Stop: dispatching subagents for long-gate work without a timeout wrapper
  on this platform — two watchdog stalls traced to a headless live-pipe
  test plus git pager; `perl -e 'alarm N; exec @ARGV'` + `--no-pager` +
  stdin from /dev/null is the local recipe (macOS ships neither `timeout`
  nor `gtimeout`).

## Idea seeds

- Make artifact-commit an explicit stage step so run docs can't be left
  untracked (verification.md was missed on the branch this run).
- Reconcile skills' one-question-at-a-time interview rule with harnesses
  that batch questions natively.
- Consider tightening the backlog grammar to reject a mis-ordered
  `(claimed:)` marker absorbed into seed text (deferred review minor).
- Repo-wide lint read_text error policy (decode/OS errors) instead of
  per-checker handling (deferred review minor).

## Run complete

Closed 2026-07-06. Seeds above were appended to `docs/backlog.md`
(`from: feature:seed-backlog`) — the first real use of the convention this
run shipped.
