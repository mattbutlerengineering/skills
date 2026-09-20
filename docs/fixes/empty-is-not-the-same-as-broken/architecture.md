---
stage: architect
run: maintenance:empty-is-not-the-same-as-broken
date: 2026-08-25
ux: skipped — no user-facing surface beyond the issue body the mine already writes
assumptions: ["The queue body gains a line that is ALWAYS present rather than a warning that appears only when something broke. Argued in D2: an absent warning is indistinguishable from an old body, which is the same reasoning failure the run exists to fix, one level up.", "The timeline stream is fixed alongside the change-request stream the seed names. It is the same blindness with the same remedy and the caller already holds the facts needed — leaving it would knowingly ship half a fix. Recorded here rather than smuggled into the diff."]
---

# Architecture: say what was read

## Approach

Stop conflating *did not read* with *read, found nothing*, then state the
distinction in the body.

Two changes, both small:

1. `_change_requests` returns `None` when the listing failed, keeping `[]`
   for a successful empty read.
2. `compose_queue` takes a `sources` line's worth of facts and renders it
   into every body, healthy or not.

## D1 — how "did not read" is represented

**Chosen:** `None` from `_change_requests`, the same sentinel
`gh_read` already uses for exactly this distinction and which this module
already branches on three times (`read.value is None`).

```python
    if read.value is None:
        return None
```

**Rejected — a `(requests, ok)` tuple.** A second convention for a
distinction the module already has one for. Every caller would then unpack
two shapes of "maybe" depending on which function it called.

**Rejected — passing `problems` into `compose_queue`.** The body would
become a second reader of the CLI's problem strings: one fact, two owners,
which is the class this repo has spent three runs removing. `problems` stays
the CLI's; the body gets facts, not strings.

The timeline stream needs no signature change at all: `_timelines` already
returns a dict keyed by the issues it *could* read, so
`set(mirrored) - set(events_by_issue)` is the gap, computed by the caller
that already holds both.

## D2 — always-present, not a warning

**Chosen:** every body carries a `Sources:` line stating what was read.

```
Sources: gate rejections from 12 of 12 issue timelines; change requests from the PR listing.
```

```
Sources: gate rejections from 10 of 12 issue timelines (2 unreadable); change requests NOT READ — the PR listing failed.
```

**Rejected — render a block only when something failed.** It reads cheaper
and it fails the same way the defect does: a body with no warning is
indistinguishable from a body written before the warning existed, so a
reader still cannot tell health from staleness without checking the tool's
version. A line that is always there cannot be confused with its own
absence.

The cost is one line per week on a healthy queue. That is the whole price.

## Components

| Component | Responsibility | Change |
| --- | --- | --- |
| `_change_requests` | Harvest change requests from a live PR listing | returns `None` on a failed listing |
| `_timelines` | `{issue: label events}` for readable timelines | none — its gap is already derivable |
| `compose_queue` | The queue issue's body | new `sources` argument, rendered on every body |
| `run_mine` | Wire the streams, post the queue | computes the two gaps and words them |
| the payload mirror | `factory/templates/tools/factory/rejection_mining.py` | regenerated with the manifest |

## Contracts

**`compose_queue(rejections_by_wo, requests_by_wo, day, sources=None)`**

- `sources`: the already-worded statement of what was read, or `None` for
  callers that have nothing to say. `None` renders no line, which keeps
  every existing test and every direct caller working unchanged.
- Wording lives in `run_mine`, which knows what happened; structure lives in
  `compose_queue`, which owns the body. Same split as the `reason` line the
  CLI already emits.

**`_change_requests(mirror, run, problems) -> list | None`**

- `[]` — the listing was read and no PR carried a change request.
- `None` — the listing failed; `problems` carries the reason, unchanged.

**Unchanged:** the problem strings, the marker, the footer, the ranking, the
upsert, and the `reason` output. This run adds a statement; it removes
nothing.

## Failure modes

- **Both streams fail.** Both halves of the line say so; the body still
  posts, because a queue that says "I read nothing" is worth more than no
  queue. Matches `_post_queue`'s existing posture.
- **The issue listing fails.** `run_mine` already returns early and posts
  nothing. Untouched — there is no body to annotate.
- **A caller passes no `sources`.** Renders exactly today's body. That is
  the compatibility seam for the tests that already pin the body.

## Stack

Nothing new. Stdlib only, no new import, no new dependency.

## Mirroring

`rejection_mining.py` is in `factory_init.MIRRORS`, so the payload copy and
`factory/manifest.json` are regenerated with
`python3 factory_init.py update-manifest` in the same commit.
