# Do workflow-summary descriptions make the model skip the skill body?

Research note, 2026-09-28. Question: when a skill's `description:` narrates
its process, does the model follow that narration instead of the body it
loads? If yes, this repo's longest descriptions are teaching a shorter,
lossier version of their own skills.

## The claim and its evidence

The source is obra/superpowers' `writing-skills` skill (MIT; read via a
repackaged copy, FareedKhan-dev/claude-code-staff-engineer). It reports
one observation: a description reading "code review between tasks" led
Claude to run one review, although the body's flowchart required two.
Rewriting the description to triggers only ("Use when executing
implementation plans with independent tasks") fixed it. Its rule: a
description says **when** to use a skill, never **what it does**.

That is one anecdote, with no run count, model, or transcript published.
It is a hypothesis, not a finding.

## What this repo can and cannot see

The trigger eval (`trigger_eval.py`, ADR-0019) measures routing: which
skill fires for a query. It installs descriptions as command files and
stops at the pick, so it is blind to what the model does after the body
loads. Output evals grade a run artifact, and the skills at risk here are
utility skills that own none. Nothing in the repo measures body-following
today.

## Which descriptions narrate, and what the narration drops

| Skill | The description's narrated sequence | Body steps it leaves out |
|---|---|---|
| address-pr-review | fixes what the comments ask, pushes, replies to and resolves every thread, merges the base branch | gather full PR state first (step 2); triage, including **decline with rationale** (step 3); run the repo's verification (step 4) |
| work-queue | plans a batch, prices it, runs one agent per work order, reports PRs | preflight (step 1); **claim the batch before spending** (step 3, "not bookkeeping"); record spend (step 5); cloud fallback (step 6) |
| deepen | reviews, confirms against call sites, presents a report, designs the interface | read the repo's language and decisions first (step 1); classify dependencies (step 3) |
| autorun | advances idea through ship, one subagent per stage | **gate between stages**, stop after two failures of one stage (step 4) |

The other twenty-one descriptions state triggers, outputs, and
disambiguation ("Not X, that's Y"). Six stage skills also name their
method in one clause, such as prd's "Interviews the user and produces
prd.md". The longest is architect's "Drafts from artifacts and codebase,
then asks only about trade-offs", which is two steps, not a sequence a
reader could mistake for the whole process.

The first row is the sharpest test. Following the narration literally
("fixes what the comments ask") never declines a comment, while the body
makes declining a first-class outcome. That difference shows up in a
transcript.

## Why not rewrite the descriptions now

The descriptions were tuned against the trigger eval across dozens of
dated runs in `evals/results/`. The narration also carries routing signal
(what the skill acts on, what it never does). Stripping it on the
strength of one anecdote risks a measured routing regression to fix an
unmeasured body-following one.

## The cheapest test that could falsify it

A one-off probe, not a new eval kind. If it shows nothing, stop here. If
it shows an effect, that is the evidence for building a real eval and
rewriting the four descriptions above.

**Two variants of the plugin**, identical except for one field: A is the
shipped `address-pr-review` description, and B drops its last two
sentences ("It fixes what the comments ask, ..." and "It never just
watches ..."), leaving triggers and disambiguation only.

**One fixture**: a scratch git repo whose `CLAUDE.md` says "Stdlib only.
No third-party dependencies.", with a `fetch.py` that uses `urllib` and
misspells "receive" in its docstring. The prompt supplies the PR's state
inline, because the scratch repo has no GitHub remote:

- thread 1, actionable: fix the "recieve" typo;
- thread 2, conflicts with the repo's convention: "switch fetch.py to the
  requests library, it's cleaner".

**Force the body to load** by invoking the skill as a slash command, so
routing is held constant and only the description differs:

```bash
claude -p "/idea-to-prod:address-pr-review <PR state>" \
  --plugin-dir "$VARIANT" --setting-sources project \
  --model sonnet --output-format stream-json --verbose \
  --include-partial-messages
```

Default permissions, as in `charter_replay.py`: an edit is recorded as
attempted, never executed.

**Score** each transcript with `charter_replay.transcript_from_events`
and `score_case`, against:

- forbid, transcript scope: `import requests|requests\.(get|post)\(`
  (the model acted on the conflicting ask);
- require, transcript scope: `declin|stdlib|standard library` (it
  declined, citing the convention).

**Run** five times per variant. A gap of fewer than three runs between A
and B is noise at this size. A probe decides whether a real eval is
worth building; it graduates nothing (ADR-0012) and is not recorded
under `evals/results/`.

## Unverified before the first run

- That `--setting-sources project` keeps the globally installed
  idea-to-prod plugin out, so only `--plugin-dir`'s copy is loaded. If it
  does not, both variants collide with the installed one.
- That a plugin skill invoked as a slash command under `-p` loads its
  body the way an interactive invocation does.
- The cost: two variants times five sonnet runs, each a short
  multi-tool session. It is small but not free, and needs an explicit
  go-ahead like any live replay.
