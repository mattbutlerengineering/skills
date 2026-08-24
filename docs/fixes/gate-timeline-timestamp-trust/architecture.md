---
stage: architect
run: maintenance:gate-timeline-timestamp-trust
date: 2026-08-23
assumptions: ["Chosen without live interview: the option comparison below is decided on measured caller counts and the module's existing shape, both stated so the operator can overturn it by reading the evidence rather than re-deriving it", "No ADR is offered — the decision is reversible in one line and surprises nobody who reads label_events' own docstring, so it fails two of the three ADR bars"]
---

# Architecture: one boundary validates the timeline; downstream keeps its precondition

## Approach

Validate the timestamp where the timeline enters the module, and leave
every function downstream unchanged.

`label_events` is already the module's admission gate: it drops events
that are not label flips, and drops flips missing a name or a timestamp.
It just does not check that the timestamp it admits is a timestamp. The
fix completes that existing rule rather than adding a new mechanism —
which is why nothing downstream needs a guard, and why no call site
changes.

`waited_seconds` keeps its ISO-8601 precondition. With the boundary
validating, that precondition is guaranteed for every value reachable
from `label_events`, so the correct treatment downstream is a recorded
invariant, not defensive code for a state that can no longer arrive.

## Components

### `human_gates.label_events` — the admission gate

- Responsibility: turn a raw GitHub timeline into well-formed label-flip
  events, and admit **only** those. Gains one clause: the timestamp must
  parse.
- Collaborators: `_parse_ts` (to test parseability); its three production
  callers, `gate_digest.py:109`, `dashboard.py:158`,
  `rejection_mining.py:146`, none of which change.

### `human_gates.waited_seconds` — the duration calculation

- Responsibility: whole seconds between two GitHub timestamps.
  **Unchanged.** Gains a comment recording that its ISO precondition is
  established by `label_events`, so a future reader does not re-add a
  guard here and quietly create a second owner of the policy.
- Collaborators: `_parse_ts`; called from `gate_passages`
  (human_gates.py:122) and `gate_digest.py:149`.

## Data model

No change. An event stays `(timestamp, kind, label name)`, and the
timestamp stays the raw GitHub string — parsed on demand, never stored
as a `datetime`. Converting at admission was considered and rejected
below.

## Interfaces & contracts

### `label_events(timeline) -> [(ts, kind, name)]`

- Input: the raw decoded GitHub issue-timeline JSON, untrusted field by
  field even when the HTTP call succeeded.
- Output: unchanged in shape and unchanged for every well-formed input —
  no existing caller sees a different value for any timeline GitHub
  actually emits.
- Failure modes: none raised. A malformed event is dropped, exactly as a
  nameless or timestamp-less one already is. **This is not new silence:**
  it extends a drop rule the function already implements and documents,
  rather than swallowing a new class of error.

### `waited_seconds(start, end) -> int`

- Input: two ISO-8601 timestamps. Precondition, now guaranteed upstream.
- Output: unchanged.
- Failure modes: unchanged — still raises on a non-ISO input, which is
  now unreachable from the timeline path and remains correct for a
  programming error at a future call site.

## Stack & dependencies

- Stdlib `datetime.fromisoformat`, via the existing `_parse_ts` — the
  parse that defines "is a timestamp" is already written, and reusing it
  keeps one answer to that question.
- No new module, no new dependency, no change to `factory_init.MIRRORS`.

## Decisions & alternatives

- **Validate in `label_events`** over **a `problems` channel on
  `label_events`** — the channel is the more informative design and it
  loses on measured cost: `human_gates.py` has no problems-returning
  function today (all eight are pure), so it would break the module's
  uniform shape, and it would touch three production callers plus roughly
  fifteen test call sites to thread a list nobody currently reads.
- **Validate in `label_events`** over **`try`/`except` at the two
  `waited_seconds` call sites** — that spreads one policy across
  `human_gates.py:122` and `gate_digest.py:149` and obliges every future
  caller to remember it. It is precisely the second-owner shape ADR-0061
  and the one-owner pass exist to catch.
- **Validate in `label_events`** over **hardening `_parse_ts` to return
  `None`** — that changes the contract of the lowest-level helper and
  pushes `None` handling into `waited_seconds`, `waiting_since` and both
  their callers, converting a crash into a wider blast radius.
- **Keep raw strings** over **parsing to `datetime` at admission** — the
  ordering comparisons in `completed_stays` rely on ISO strings sorting
  lexicographically, and `gate_entry` stores the raw string; converting
  at the boundary would force conversions back at both, for no gain.
- **Do nothing and record the invariant** — genuinely considered, and
  rejected on the repo's own boundary rule: a decoded API response is
  untrusted input, and this one crosses into a module whose admission
  gate already claims to reject malformed flips. The change costs three
  lines and makes an existing docstring true.

## ADRs

None. An ADR wants a decision that is hard to reverse, surprising without
context, and a real trade-off; this one is one line to revert and follows
the function's stated contract, so the record in this artifact is enough.
`human_gates.py` remains the ADR-0056 seam with its charter unchanged —
this run adds no responsibility to it, it completes one the charter
already implies.
