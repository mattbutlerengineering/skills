---
stage: architect
run: maintenance:a-blind-find-is-not-a-failed-agent
date: 2026-08-25
ux: not-applicable — a CLI step output and a workflow condition, no user-facing surface
assumptions:
  - "An ADR is offered and written. Tested against the architect skill's three-part bar and it passes all three: hard to reverse (it narrows when ADR-0032's terminal state may be applied, and a later run would have to re-derive the trade rather than read it), surprising without context (a red run that deliberately does NOT flip the order reads as a missing step), and a real trade-off (a false terminal verdict versus an order that stays in-progress, which assembler.yml's own comment names as the rot wo:failed exists to prevent)."
  - "The ADR takes number 0063, not the next free 0062. Open PR #333 adds 0062-a-quoted-token-is-not-a-claim.md and an untracked 0062-a-skill-that-states-repo-facts-runs-a-shipped-tool.md sits on the feature/pipeline-board branch. Claiming 0062 a third time would make a two-way collision a three-way one; 0063 costs nothing and leaves the existing dispute exactly as it is."
  - "GitHub records a step's outputs even when the step exits nonzero. write_outputs runs before report() in main, so the looked output is written before the failing exit. This is documented GitHub behaviour rather than something this run can test, because assembler.yml only executes on a real dispatch."
---

# Architecture: the factory says whether it looked

## Approach

`pr_for_issue` answers a question the workflow asks — *did the agent
deliver a PR?* — and answers `None` both when the answer is no and when
the function was unable to ask. One fact is missing from the reply: **did
we actually get to look.** Everything else follows from adding it.

The fact is already computable at the point of the read. `cli.gh_read`
returns `value is None` for an unusable read and `truncated` for a full
window; both mean the same thing to this caller — absence is unproven.
Neither reaches the return value today.

## Components

**`pr_for_issue` (`assembler.py:248`)** — returns a named record instead
of a pair, carrying whether the listing was read. Also stops making the
agent-blaming claim on a truncated listing, where it is unfounded.

**`main`'s `find-pr` leg (`assembler.py:280`)** — writes the new fact as
a step output alongside `pr`. Exit behaviour is unchanged: a find that
could not look is still a failure and still reddens the run.

**`.github/workflows/assembler.yml`** — the `Mark the work order failed`
step gains one condition. Nothing else about the workflow changes.

Unchanged and deliberately so: `cli.gh_read` (the seam already states
both facts), `report`'s exit convention, the claim step, the validator
trigger, and every other consumer of `assembler.py`.

## Contracts

**`pr_for_issue(issue_number, run) -> Find(pr, looked, problems)`**

| listing | match | `pr` | `looked` | problem appended |
|---|---|---|---|---|
| unusable | — | `None` | `False` | the gh failure (unchanged) |
| read, not truncated | found | `N` | `True` | none |
| read, not truncated | none | `None` | `True` | *the dispatched agent delivered no traceable PR* (unchanged) |
| read, **truncated** | none | `None` | `False` | the listing came back full, so no PR closing this issue was **proven** absent |

The fourth row is where the rarer half is fixed: today it takes the third
row's sentence, which asserts something about the agent from a listing
that was never fully seen.

`looked` is a fact the caller reads, never inferred from `pr is None` —
`pr is None` is true in three of the four rows and means something
different in each. Same argument `cli.GhResult` makes for naming
`truncated` rather than leaving it to be deduced.

**Step outputs of `make find-pr`** — `pr` unchanged (`''` or the number),
plus `looked` (`'true'`/`'false'`).

**`assembler.yml`'s failure step** — gains
`&& steps.find.outputs.looked != 'false'`.

The `!=` is deliberate rather than `== 'true'`. When the run dies before
the find step ever executes, the output is unset and reads as `''`, which
must still flip the order — a run that died at the claim or the dispatch
is a failure the order should record. Only an explicit `'false'`, written
by a find that ran and could not look, suppresses the flip.

## What happens after the change

A rate-limited find now produces: a **red run** (unchanged — the operator
still sees it), a work order left on `wo:in-progress`, and a PR that is
still unvalidated. That last part is not fixed here and is not pretended
to be: re-running the workflow is the remedy, and the order being
in-progress is what makes re-running legible.

## Decisions, with the alternatives that lost

**A step output over an exit code.** Distinct exit codes would avoid
touching the workflow, but `cli.report` owns the 0/nonzero convention for
every tool in the repo, and a workflow `if:` cannot read an exit code
without capturing it by hand. Step outputs are the seam `resolve` and
`claim` already use for exactly this — telling the workflow something it
must branch on.

**Suppressing the flip over suppressing the failure.** The alternative
was to let a blind find pass quietly. Rejected: the operator would lose
the only signal, and a green run on a blind find is a worse lie than a
wrong label.

**`looked` over a three-valued verdict.** `found=yes|no|unknown` in one
output was considered and is arguably tidier. `looked` won because the
workflow's existing outputs are boolean-shaped strings, and because the
question the failure step needs answered is genuinely binary — may this
run pronounce on the agent, or not.

## Requirement traceability

| Defect finding | Component |
|---|---|
| A rate-limited read flips the order to `wo:failed` | `Find.looked`, the `looked` output, the workflow condition |
| The delivered PR is never validated | Not fixed; stated above and carried forward |
| A truncated listing claims the agent delivered nothing | `pr_for_issue`'s fourth row |

## Out of scope

The unvalidated PR after a blind find. Re-triggering the validator from a
later run would need a source of truth about which orders have unchecked
deliveries, which does not exist today and is a feature, not a fix.
