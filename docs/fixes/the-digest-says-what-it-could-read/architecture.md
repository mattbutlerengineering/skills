---
stage: architect
run: maintenance:the-digest-says-what-it-could-read
date: 2026-08-25
ux: not-applicable — the artifact is a GitHub issue body, no interactive surface
assumptions:
  - "No ADR. Tested against the architect skill's three-part bar: the change is trivially reversible, unsurprising once read, and the alternatives lost on clarity rather than on a real trade-off. The rejected alternatives are recorded here instead, which is what the skill prescribes when any of the three is missing."
  - "compose_digest's new parameter is REQUIRED, with no default. A default would let a future caller omit the coverage fact silently, which is the exact defect this run is fixing. The cost is that the three existing direct-call tests must pass it; that is the point."
  - "The two facts get two renderings and neither is repeated in the other. Truncation is a property of the whole digest and renders once in the footer; an unreadable timeline is a property of one line and renders on that line. A footer counting unreadable timelines was rejected because it cannot say WHICH line to distrust, and duplicating it in both places would make the digest a second owner of one fact (ADR-0061's discipline)."
---

# Architecture: the digest states its own coverage

## Approach

The facts already exist inside `run_daily`. Neither needs to be computed,
fetched, or inferred — both are discarded one line after being obtained:

- `cli.gh_read` hands back `truncated` at `gate_digest.py:197`; the line
  binds `read.value` and `read.problems` and drops the third field.
- `_timelines` omits an issue from its returned dict when the fetch
  failed, and keeps it with an empty event list when the fetch succeeded
  and held nothing. `_queues` then erases the distinction with
  `events_by_issue.get(number, [])` — the default is doing the damage.

So this is a plumbing change, not a new capability: carry two known facts
the last few inches to the artifact, and render each once.

## Components

**`_queues` (`gate_digest.py:134`)** — stops defaulting. Distinguishes
"this issue is absent from `events_by_issue`" (the fetch failed) from
"present and empty" (read fine, no gate arrival in its history) and puts
that distinction in the item it emits.

**`compose_digest` (`gate_digest.py:63`)** — the one renderer. Gains a
required `listing_truncated` parameter for the whole-digest fact, and
renders the per-item fact from the item itself. Stays pure and
deterministic; it remains the only place digest text is written.

**`run_daily` (`gate_digest.py:187`)** — passes `read.truncated` through.
One line.

Unchanged and deliberately so: `cli.gh_read` (the seam already states the
fact correctly), `human_gates` (the gate vocabulary and stay walk),
`_capture_latency` (the ledger's dedup identity is independent of
rendering), and `_post_digest`.

## Contracts

**Queue item** — today `(number, title, waited)`, where `waited is None`
carries two incompatible meanings. Becomes a named 4-field record:

```
Item(number, title, waited, aged)
```

`aged` is False only when the issue's timeline could not be read. When
`aged` is True and `waited` is None, the history was read and simply held
no arrival at this gate — the existing, correct, unmarked rendering.

The field is named and read, never inferred from `waited`. That is
`cli.GhResult`'s own stated reason for existing (*"`truncated` is a fact
the caller reads rather than infers from 'a problem on a usable
listing' — that inference is correct today and silently wrong the first
time this seam adds a second advisory problem"*), and the same argument
applies unchanged one layer up.

**`compose_digest(queues, as_of, listing_truncated)`** — three renderings,
one per state, and no state renders in two places:

| state | line |
|---|---|
| `waited` is a number | `- #123 title — waiting 2d 0h` (unchanged) |
| `waited is None`, `aged` | `- #123 title` (unchanged) |
| not `aged` | `- #123 title — age unknown (timeline unreadable)` |

and when `listing_truncated`, one sentence appended to the existing
footer, naming the consequence rather than the mechanism: the listing came
back full, so issues outside it are not represented and an empty section
may mean unseen rather than none.

## Decisions, with the alternatives that lost

**A named record over a 4-tuple.** A bare 4-tuple works and is smaller.
`Item` was chosen because `compose_digest`'s docstring already spends
three lines explaining what the third element means, and a fourth
positional boolean is exactly the parameter that gets passed in the wrong
slot. `cli.GhResult` set the precedent for a namedtuple at a seam whose
fields are easy to confuse.

**A boolean over a coverage list.** `rejection_mining._sources` takes a
list because it has two listings to name. This tool has one windowed read,
so a list would be a container with a permanent maximum of one element —
speculative generality. If a second windowed read ever lands here, the
list is a two-line change at that time.

**Required parameter over a defaulted one.** Recorded above as an
assumption; the short version is that a default reintroduces the defect as
an option.

**Per-item mark over a footer count.** A footer saying "2 timelines were
unreadable" tells a reader that some line is untrustworthy without telling
them which, which is close to useless on a queue they are about to act on.

## Requirement traceability

| Defect finding | Component |
|---|---|
| Truncated listing yields a byte-identical digest | `run_daily` passes `read.truncated`; `compose_digest` renders the footer sentence |
| Unreadable timeline renders identically to a readable one | `_queues` stops defaulting; `Item.aged`; `compose_digest` renders the per-item mark |
| Tests assert the log and never the body | Verify's regression tests assert the body text in both conditions |

## Out of scope

`dashboard.py`, `assembler.py` and `label_sync.py` also ignore
`truncated`. Named in `defect.md`, seeded at Operate, not touched here.
