---
stage: capture
run: maintenance:run-discovery-ignores-open-prs
date: 2026-08-25
re-entry: architect
intake: #344
assumptions:
  - "Captured as a DEFECT brief rather than a condition brief. The pipeline produces a wrong outcome — a rebuilt fix and a discarded PR — rather than merely a degraded one, and there is a dated instance with an exact file overlap. The re-entry is still architect, because what the fix should be is genuinely open."
  - "Origin is a backlog seed, not a user report. No human has complained about this; the run that suffered it seeded the lesson against itself, and this run claims that seed. Recorded here because a defect with no complainant is easy to over-scope, and the seed's own wording ('should look at open PRs, not just open issues') is a proposed remedy rather than a statement of the defect — it is not adopted as the design."
---

# Defect: run discovery cannot see work already open in a PR

## Defect

**Observed.** The protocol's run discovery enumerates run *directories* in
the current checkout: `docs/`, every `docs/features/*/`, every
`docs/fixes/*/`. A run is active when it has an artifact and no `retro.md`.
That is the whole of what the pipeline knows about work in progress.

A fix another agent has already written does not live in a directory. It
lives on a branch, behind an open pull request, and no enumeration of the
working tree can see it. Nothing at the moment a run *starts* — Capture
from a tracker intake or a backlog seed, Idea from a seed — asks whether
the thing about to be built already exists.

**Expected.** Starting a run on work that is already finished and awaiting
review should be difficult to do by accident. Not impossible — two agents
may legitimately converge — but the question should be asked somewhere,
once, by a stage that starts runs, and answerable with the tools an agent
already has.

**Not the same as** orientation within an active run. The protocol says
orientation comes from run artifacts alone and the backlog is never read
during it. That rule is correct and this defect does not touch it: the
gap is at the moment *before* a run has artifacts to orient from.

## Reproduction / Evidence

This one has a dated instance rather than a repro script, and the instance
is exact.

| | opened | resolved |
|---|---|---|
| #298, branch `routine/2026-08-17-toolsmith-mine-pr-read` | 2026-08-17T11:53:11Z | **closed unmerged** 2026-08-19T14:53:46Z |
| #303, branch `toolsmith-mine-pr-permissions` | 2026-08-19T05:20:31Z | merged 2026-08-19T05:21:28Z |

Both carried the same fix. The overlapping file set is not similar, it is
identical:

```
.github/workflows/toolsmith-mine.yml
factory/manifest.json
factory/templates/.github/workflows/toolsmith-mine.yml
tests/test_rejection_mining.py
```

`docs/fixes/toolsmith-mine-pr-permissions/defect.md` is dated 2026-08-18
and carries `intake: #297`. So the run captured its defect while #298 had
been open for a day, built the fix, merged it as #303, and #298 was closed
nine hours after that merge.

Both PRs are authored by the same account, because both agents act as the
same GitHub identity — which is precisely why neither could be filtered
out by "not mine".

**Re-derivable today**, and this is the check the pipeline never makes:

```
$ gh pr list --state open --json number --jq 'length'
12
$ gh pr view 341 --json files --jq '[.files[].path] | join(" ")'
budget_guard.py factory/manifest.json factory/templates/tools/factory/budget_guard.py tests/test_budget_guard.py
```

Twelve open PRs, every one agent-authored and blocked on ADR-0036's
non-authoring-reviewer clause. Choosing this run's own seed required
mapping all twelve file sets by hand first, which is the defect stated as
a chore.

## Root-cause hypothesis

**Hypothesis, not a finding.** Run discovery was specified for a single
agent working a single checkout, where "what is in flight" and "what is on
disk" are the same set. That assumption is now false in two directions:
the daily improvement routine opens PRs from cloud runs this checkout
never sees, and human review latency keeps finished work parked on
branches for days.

The protocol's own framing supports the hypothesis — it is careful to say
orientation is derived *entirely* from which artifacts exist, and equally
careful to bound the backlog to two reading moments. Both rules police
what may be read *during* a run. Neither covers the moment before one
starts, so nothing owns the question.

A second, weaker strand: `docs/backlog.md`'s `(claimed: ...)` suffix is the
only in-flight signal the pipeline has, and it only fires when the other
agent started from a seed. #298 came from the improvement routine's own
Orient step, which claims no seed — so the one mechanism that exists could
not have fired here.

## Blast radius

- **Who.** Every agent starting a run in this repo, including the daily
  improvement routine and every `/autorun` invocation.
- **What.** Duplicated work, and worse, a *discarded* PR — #298 was
  reviewed by nobody and closed. The cost is not only the rebuild; it is
  that the losing branch's reasoning and tests are thrown away without
  comparison. #298 and #303 were not byte-identical, and nothing ever
  diffed them.
- **How badly.** One confirmed instance in 8 days at a queue depth of two.
  The queue is now twelve and the review latency is measured in days, so
  the exposure is larger, not smaller. This is an inference from the
  conditions, not a second measurement — there is one instance, and
  claiming a trend from it would be the mistake this repo keeps seeding
  against.
- **Since when.** At least 2026-08-17. Structurally, since run discovery
  was first written — nothing regressed; the environment changed around a
  rule that was correct when made.

## Ruled out

- **"The router should read the backlog more."** It shouldn't, and it
  wouldn't have helped: the backlog is deliberately bounded to two reading
  moments, and #298 claimed no seed to read.
- **"Filter by author."** Both PRs carry the same GitHub account. There is
  no "someone else's work" to detect.
- **"Detect it at Ship."** Too late by definition — the duplicate work is
  already done. #303 merged 57 seconds after it was opened; no gate placed
  at the end of a run can pay back a rebuild.
- **A new CI gate.** Out of scope by the brief. A check that fails a build
  because a *different* PR touches the same file would fire on nearly every
  one of the twelve open PRs today, all legitimately.

## Notes

*(deviations logged here, dated, as they happen)*
