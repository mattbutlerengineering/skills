# Autorun brief: feature:factory-evolution-v1

Collected 2026-09-29 from the owner, one question at a time. Not an
artifact: this file never counts toward orientation or active-run
discovery.

## Run

- Scale: feature. Slug: `factory-evolution-v1`.
- **Resume, not a fresh run.** Idea, PRD (PRD-0006), architecture, and
  breakdown already exist and are the source of truth for the problem,
  scope, success criteria, and constraints. This brief covers only what
  the remaining stages need: Implement (orders 69-72), Verify, Review,
  and Ship.
- UX: already recorded as not-applicable in `prd.md`.

## Owner decisions for this run

- **Routine triggers (orders 69-71): pilot one.** Create only the
  `factory-weekly-queue-groomer` trigger, in the shape its protocol doc
  (`docs/factory/queue-groomer-routine.md` §Trigger) specifies: weekly,
  Sonnet, no MCP connectors, spend reported in the journal and excluded
  from the cost ledger (ADR-0044). This is the owner's explicit approval
  of that one recurring spend. The retro/reflect and doc-gardener
  triggers are **deferred by owner decision**, and their rows are
  checked as deferred, the same way order 65 was on 2026-09-28. Reason:
  one weekly run bounds the new spend while its journal shows real
  cost; the other two follow with one command each once it does.
- **Trigger creation is done by the orchestrating session**, which holds
  the approval, and its id is recorded here and in the protocol doc's
  §Trigger. No stage subagent creates, edits, or runs a trigger.

## Defaults taken, logged as assumptions

- **Release: prepare and stop.** Landing this run means merging a PR to
  `main`, which is gate 3 (ADR-0033 as amended by ADR-0036), and the
  author never merges. Ship writes `release.md` with the exact steps and
  executes nothing.
- **Tracker: no seeding.** Existing issues do not enter the breakdown.
  The run's PR gets one tracking issue to close, which is this repo's
  convention for detector B, not tracker seeding.
- **Spend beyond the one trigger: none.** No paid eval, replay, or
  dispatch runs in any stage. A stage that would need one stops and
  surfaces.

## Trigger record

- `factory-weekly-queue-groomer`: `trig_01W5PgiQb4G2qwMXnNVFtACx`, created
  2026-09-29 04:11 UTC by the orchestrating session. Cron `17 13 * * 3`
  (Wednesdays 13:17 UTC), model `claude-sonnet-5-5`, tools Bash, Read,
  Write, Edit, Glob, Grep, environment `env_012GDG167Tpz55u8MEpDkL2y`, no
  MCP connectors. First run 2026-09-30 13:17 UTC. The create call
  attached every account connector by default (Gmail, Claude Docs,
  Claude Code Remote); they were cleared at 04:11:48 UTC, before any run.

## Resumed 2026-10-03 — Review and Ship (prepare-and-stop)

Autorun invoked with no arguments on the evening of 2026-10-02 PDT
(2026-10-03 UTC; this run dates its artifacts in UTC, per
`verification.md`'s first assumption). Run discovery found four
pre-ship feature runs, so the protocol's ask rule applied. The operator
chose this run from these candidates:

- `first-live-dispatch` — draft PR #606 already carries its `review.md`
  (one critical finding); the protocol's work-in-flight guard would stop
  a second attempt.
- `codex-style-standards-enforcement` — draft PR #604 already carries
  its `verification.md`, `review.md` and `release.md`; same guard.
- `pipeline-board` and every shipped maintenance run wait only on
  Operate, which autorun does not drive.

Orientation at resume, in this worktree (`feat/factory-evolution-queue-groomer`
off `origin/main` at 6742c9f): all eight breakdown rows checked;
`verification.md` exists (14 PASS / 4 FAIL, dated 2026-09-29). None of
the 2026-09-29 Implement or Verify work had been committed. This pass
commits it first, before Review, so the Review pass can scope the diff
against `origin/main`. Next stage is Review, then Ship.

- **Release authorization: unchanged, prepare-and-stop.** Ship writes
  `release.md` with the exact steps and executes none of them: no merge,
  tag, deploy, publish, or plugin version bump. The artifacts go up as a
  draft PR for the operator (gate 3, ADR-0033 as amended by ADR-0036),
  as every earlier resume did; the operator approved commit, push and
  draft PR when choosing this run.
- **Tracker: one tracking issue.** One `type:chore` issue for the PR to
  close (this repo's detector-B convention, which the original brief
  already anticipates). No other issue is created, labelled or closed,
  and no `wo:*` label is touched.
- **Spend: none.** No trigger is created, edited or run; no paid eval or
  replay runs in any stage.
- **The pilot trigger could not be observed directly.** The trigger API
  refused this session's token on both `get` and `list_runs` for
  `trig_01W5PgiQb4G2qwMXnNVFtACx`: `HTTP 401 oauth_scope_insufficient`
  (request ids `req_011CfeDGQbQGam1pPRUbRjTQ`,
  `req_011CfeDGUihvDbAedZPRsaQB`), the same scope error
  `breakdown.md`'s 2026-09-25 note recorded. Indirect evidence the
  orchestrator captured for Review (`gh api` on issue #590, "Factory
  queue-groomer journal", fetched 2026-10-03T04:16Z): a
  `queue-groomer-state` comment at 2026-09-30T13:19:51Z, two minutes
  after the trigger's first scheduled fire (13:17 UTC), reporting a
  propose-only run; and a second comment at 13:20:59Z from a separate
  session reporting an "apparent duplicate run" for the same day and a
  marker-escaping bug it corrected in its own first post. No
  `routine-groom/2026-09-30-*` branch, PR or issue exists, consistent
  with the propose-only verdict. The journals for the two deferred
  routines (#587, #586) carry only their 2026-09-28 one-off entries.
- **The four open failures are carried, not fixed.** WO-0065, WO-0069
  and WO-0071 are owner deferrals, and the epic #439 Destination follows
  from them. No Implement work exists for any of them and none is
  dispatched.
- **Stage subagents.** One fresh context per stage. Each reads this
  brief and the run directory, may run the free battery, and may not run
  paid tools, touch triggers, commit, push, or write to the tracker. The
  orchestrator commits each stage's artifact after gating it.
- **Review took two attempts.** The first Review subagent, dispatched
  2026-10-03 around 04:20 UTC, died on a model usage limit (HTTP 429)
  before writing anything, and left the working tree clean. A second,
  fresh subagent was dispatched 2026-10-04 around 01:25 UTC on a
  different model (Opus) and wrote `review.md`: no critical finding,
  four majors recorded for the owner, six minors deferred. The
  orchestrator gated it before committing: every template section is
  present, the scratch probe behind the first major was re-run and
  returned the same empty result, and gates and lint are clean with the
  file in place.
- **A second trigger-API attempt also failed.** `get` and `list_runs`
  at 2026-10-04T01:22Z returned the same `HTTP 401
  oauth_scope_insufficient` (request ids `req_011CfgKcdBTN4CPcybhCUvtD`,
  `req_011CfgKcdnAnPg3tUGTPT5fK`). Issue #590 held the same three
  comments as the first capture, with nothing newer.
