---
stage: architect
run: maintenance:a-timestamp-the-digest-cannot-parse
date: 2026-09-15
assumptions:
  - "prd.md absent by protocol, not by omission — this is a maintenance run with re-entry: architect, whose predecessor is defect.md (pipeline-protocol.md, Maintenance-run orientation). The soft gate is applied the way docs/fixes/one-fact-one-owner/architecture.md applied it. defect.md plus autorun-brief.md are the design source; where they disagree defect.md wins, so none of the four corrections defect.md records under Notes is re-imported here — in particular the never-a-traceback bar is cited to gate_digest.py's own docstring, ADR-0051 and CLAUDE.md, never to ADR-0039"
  - "No ux: echo — the protocol's echo relays a ux-reason FROM prd.md, and a maintenance run has none, so no ux: decision was ever taken and there is nothing to echo. defect.md states the same fact under Constraints (\"User-facing surface: none\"). Recorded here so the absence is not ambiguous downstream"
  - "Four sections beyond TEMPLATE.md: a dedicated design-question section, Measured against the tree, What this design deliberately does not do, and Traceability. The template has none of them; the repo's only other re-entry: architect maintenance architecture carries all four, and defect.md names that run as the artifact-depth precedent. Template section set and order are otherwise unchanged and nothing is dropped"
  - "Scope widening 1 — rejection_mining.py gains one forwarding line. defect.md scopes \"rejection_mining behavior\" out, but label_events' signature change reaches its call site (rejection_mining.py:146) unavoidably, and discarding the problems it now returns would be the one place in the tree that knowingly throws a problem string away. Forwarding is also what \"the asymmetry is removed\" means in defect.md's fourth success criterion: the miner's behavior on well-formed input is byte-identical, and on malformed input it now reports what the digest reports"
  - "Scope widening 2 — dashboard.py gains the same one forwarding line at dashboard.py:158. defect.md scopes the dashboard out and leaves draft backlog-seed text for it. The seam change reaches it by signature, and the third exposure (dashboard._age_seconds) closes as a consequence. dashboard._age_seconds itself is NOT edited and gains no guard: under the new admission invariant it cannot receive an unreadable string, and implementation-discipline forbids defending a state that cannot occur. The seed text in defect.md's Notes is therefore unnecessary and should not be appended — see What this design deliberately does not do"
  - "Problem-string text and parameter names are this stage's proposal, not a quotation. Neither input supplies a string or a signature. The wording follows cli.gh_read's existing family for the same call site (\"gh api timeline for #N returned unparseable JSON\") and the repo's `(s)` plural idiom; Implement's tests pin the exact bytes, and a better sentence found at implementation time is a test edit, not a design change"
  - "The ADR offered below is numbered 0062 — the next free number (docs/adr/ holds 0001 through 0061, and a repo-wide grep for the prefixed 0062 token returns nothing). The number is written bare, without its typed-ID prefix: an ADR- token for a file that does not exist is a dangling reference to detector C (gates.py:376), and this run must leave the battery green. No file is written into docs/adr/ by this stage; the text is a proposal"
---

# Architecture: a timestamp the digest cannot parse

## Approach

The tool has an error channel and this input walks past it, so the design
adds no machinery: it moves one decision — *what counts as a label
event* — the last inch it was always going to have to move. `label_events`
already refuses events on three grounds (wrong `event` kind, no label
name, no `created_at`); it simply stops one test short, admitting a
timestamp on truthiness where every downstream function needs it to
parse. The fix makes that fourth test the same kind of test as the other
three, at the same place, and has the walk **say what it refused** so a
thinner history is never mistaken for a quiet one. Everything below the
door then becomes total by construction: `_parse_ts` never meets a string
it cannot read, `waited_seconds` never subtracts, `dashboard._age_seconds`
never parses, and the two independent call sites in §3 of `defect.md` are
covered by one rule rather than two guards.

The shape that lost is the one the seed line implies: **wrap `_parse_ts`
in a `try` and let each caller cope**. It is smaller and it is the wrong
locality. There are three timestamp consumers behind that helper
(`waited_seconds`, `completed_stays`' string ordering, `waiting_since`'s
return) and four call sites in three tools; a guard at the parse tells a
caller "this one number is missing" at a point where the caller can no
longer tell a missing number from a missing *event*, and it leaves each
of the four sites to invent its own answer separately. That is precisely
how the divergence ADR-0056 exists to close was created — two tools
spelling one window test two ways. Admission has one owner, one test, and
one problem string; the parse guard has four owners and no string at all.

`label_events`' docstring is the thing that has to give, and it gives less
than it looks. Its operative clause — *"anything that is not a
well-formed label flip is not this module's business"* — already sanctions
dropping, and the walk already drops on it. The clause that delegates —
*"an unusable timeline is the fetcher's problem, never this walk's"* —
is about an unusable *timeline*: a failed, unparseable or wrong-shaped
read, which is exactly `cli.gh_read`'s job and stays there. A
well-formed JSON array with one unreadable field is not an unusable
timeline; it is a timeline with an event that is not a well-formed label
flip. So the change completes the first clause rather than reversing the
second, and the second clause survives untouched. That reading is still a
change to an `accepted` decision's reasoning, which is why an ADR is
offered rather than a one-line record.

## The design question — answered

`defect.md` prices three candidates and refuses to pick. The answer is a
**merge of its 1 and 2, with 3 rejected outright**: the walk refuses the
event *and* returns the problem; the caller prefixes and forwards it into
the list it already carries.

```
label_events(timeline, operation, label=None) -> (events, problems)
```

**Why not 1 alone (drop silently).** It is the smallest change, it fixes
every traceback, it costs the callers nothing, and the repo has an exact
precedent for it — `cli.label_names` drops a nameless label on the
strictest rule all its callers tolerate, reading the same `gh` payload.
It loses on two counts. First, `defect.md`'s first success criterion is
literal: *"produces a `gd:`-prefixed problem string and a nonzero exit"*.
Silent dropping produces neither, so option 1 alone cannot pass this
run's own bar. Second, the precedent does not transfer: a dropped
nameless label removes something no caller could have acted on, whereas
a dropped label flip **silently rewrites the gate history the digest
reports as fact**. Measured — drop an `unlabeled` event and the stay
reads as still open, so the digest prints a queue row for a work order
that left the queue, with an age computed from a stay that ended. A wrong
answer with no line printed is worse than the traceback it replaces.

**Why not 2 alone (each caller reports).** The rule would be written
three times, in `gate_digest._timelines`, `dashboard._timeline` and
`rejection_mining._timelines` — three near-identical fetchers that
ADR-0056 deliberately left un-folded. Two of them are already the pair
whose two spellings of one window test justified ADR-0056. Teaching each
one to validate a field is the same mistake with a different field, and
`defect.md` says so: *"each caller must learn the rule separately, which
is how ADR-0056's original divergence was created"*.

**Why not 3 (the fetcher validates).** `cli.gh_read` shape-checks the top
level only, by design, and its docstring scopes it to transport failure;
it is generic over every `gh` read in the tree, so teaching it about
`created_at` gives a general seam knowledge of one payload's field
semantics. And it would not even localise the rule — the three
`_timelines` are the fetchers, so the check lands in three places again.
No ADR mentions `gh_read` at all, so nothing here is protected by a
decision; it loses on its own merits.

**What the merge costs, stated plainly.** `label_events` returns a pair
instead of a list, which is a breaking signature change at 3 production
call sites and 17 call sites in `tests/test_human_gates.py`. That is the
price, it is mechanical, and it buys the one property the alternatives
cannot: the rule exists once, and no caller can hold it wrong because no
caller holds it at all.

### Sub-question 1 — the asymmetry is removed, not documented

`gate_rejections` survived the timeline that killed the digest because it
reads only `end` and never asks for a duration. That is not a violation
of ADR-0056's partition — the partition over `completed_stays` holds
either way — it is the two halves disagreeing about whether the *input*
is usable. Admission removes it at the root: both halves now walk the
same shortened event list, both report the same refusal through their own
label, and neither can raise. The invariant ADR-0056 states ("two views
of one walk") becomes true of refusals as well as of stays, which is
strictly stronger than what it claims today.

This is the reason the miner takes the forwarding line rather than
`events, _ = label_events(...)`. Discarding would *preserve* the
asymmetry in its new form — the digest reports, the miner stays quiet —
and `defect.md`'s fourth success criterion offers exactly two outs:
removed, or recorded as intentional. Removal is cheaper than an ADR that
argues a durability gap is a feature.

### Sub-question 2 — yes, the fix reaches `dashboard._age_seconds`

`dashboard._age_seconds` has exactly one caller (`dashboard.py:192`), fed
by exactly one `waiting_since` over exactly one `label_events`
(`dashboard.py:158`, verified by `grep -rn "_age_seconds" *.py`). With
admission in place, `waiting_since` can only return a string
`label_events` admitted, and `_age_seconds` spells the identical parse
expression as `_parse_ts`. So the third exposure closes as a consequence
of the same one rule, and the dashboard also gains the `dashboard:`
problem string.

`_age_seconds` is **not** edited and gains no guard. The state it would
defend against cannot occur, and `implementation-discipline.md` says to
note the invariant instead of coding against it — the docstring says
where the guarantee comes from. `defect.md`'s draft backlog seed for this
exposure is therefore **unnecessary and should not be appended**; the
exposure is closed in this run, not deferred.

## Measured against the tree

Every block below is real output from this stage, run in this working
tree at HEAD `622e7c0` on 2026-09-15. The design probe monkeypatches a
prototype of the proposed rule onto the real modules **in-process** and
writes nothing — it is throwaway feasibility evidence, not the
implementation, which Implement writes test-first.

### A fourth exposure class the inputs do not name

`defect.md` characterises the input as "truthy but not ISO-8601". There
is a second class that is *valid* ISO-8601 and still fatal, and it fails
with a different exception:

```
$ python3 - <<'PY'   # abridged
import human_gates as hg, dashboard
from datetime import datetime, timezone
now = datetime(2026, 9, 15, tzinfo=timezone.utc)
print(repr(hg._parse_ts("2026-08-30T10:00:00")))
hg.waited_seconds("2026-08-30T10:00:00", now.isoformat())
dashboard._age_seconds("2026-08-30T10:00:00", now)
PY
datetime.datetime(2026, 8, 30, 10, 0)
  waited_seconds raised TypeError: can't subtract offset-naive and offset-aware datetimes
  dashboard._age_seconds raised TypeError: can't subtract offset-naive and offset-aware datetimes
```

An offset-**naive** timestamp parses cleanly and then poisons the
arithmetic. This decides the admission predicate: a design that catches
only `ValueError` around `fromisoformat` — the obvious reading of the
seed line — still tracebacks on this input, and still fails the
never-a-traceback bar. **Admission requires a parse that yields an
offset-aware datetime**, not merely a parse.

### The prototype, driven through the real `run_daily` and `main`

Same fake `gh` runner and same real mirrored issue number as
`defect.md` §2, so the two runs are comparable line for line:

```
using real mirrored issue: 106 -> WO-0001

--- completed stay, malformed unlabeled ts ---
run_daily -> outputs: {'changed': 'false', 'reason': 'gd: 0 item(s) waiting, 0 new gate-latency row(s)'}
  problem: gd: gh api timeline for #106 returned 1 label event(s) with an unreadable timestamp (first: 'not-a-timestamp') — not counted
gate_digest: 1 problem(s)
main -> exit 1 | GITHUB_OUTPUT: {}

--- open stay, VALID but offset-naive ts ---
run_daily -> outputs: {'changed': 'false', 'reason': 'gd: 1 item(s) waiting, 0 new gate-latency row(s)'}
  problem: gd: gh api timeline for #106 returned 1 label event(s) with an unreadable timestamp (first: '2026-08-30T10:00:00') — not counted
gate_digest: 1 problem(s)
main -> exit 1 | GITHUB_OUTPUT: {}
```

Both of `defect.md` §3's independently reachable call sites are covered
by the one rule: the completed-stay path (`_capture_latency` →
`gate_passages`) and the open-stay path (`_queues` → `waited_seconds`).
Where the same two histories produced `ValueError` out of
`sys.exit(main(...))`, they now produce a `gd:`-prefixed line and exit 1.
The second case is the documented degradation `waiting_since` already
names — the item still lists (`1 item(s) waiting`), just without an age.

### The third exposure, closed by the same rule

```
--- dashboard._age_seconds, same pair ---
  created_at='not-a-timestamp': waiting_since -> None; _age_seconds called: False; problems: ["dashboard: gh api timeline for #106 returned 1 label event(s) with an unreadable timestamp (first: 'not-a-timestamp') — not counted"]
  created_at='2026-08-30T10:00:00': waiting_since -> None; _age_seconds called: False; problems: ["dashboard: gh api timeline for #106 returned 1 label event(s) with an unreadable timestamp (first: '2026-08-30T10:00:00') — not counted"]
```

### The one thing a problem string does not buy back

`defect.md` §5 records that the gate-latency rows are appended on the
runner and then discarded. **This design does not restore them**, and the
reason is in the workflow, not the tool:

```
$ sed -n '/Commit the new gate-latency rows/,+1p' .github/workflows/gate-digest.yml
      - name: Commit the new gate-latency rows
        if: steps.digest.outputs.changed == 'true'
```

A bare `if:` implies `success()`, so a step that exits nonzero skips the
commit. `write_outputs` still runs (it precedes `report` in `main`), so
`changed` is written — but the digest step is red, and the commit step
does not run. The rows survive to the next daily re-scan, which
re-appends them safely (`cost_ledger.row_key` dedup), so the loss is
deferred rather than permanent; it becomes permanent only while the
malformed event stays inside the fetched window. Closing it means
`if: always() && …`, which changes the commit behaviour for **every**
failure mode of the digest — a failed `gh issue edit` included — in a
mirrored workflow that ships to every stamped repo. That is its own
decision with its own evidence, and folding it in is the drive-by
hardening `defect.md` forbids. See *What this design deliberately does
not do* for the seed text.

### Baseline

```
$ python3 -m unittest discover tests
Ran 1344 tests in 17.330s
OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
```

## Components

No new module, no new seam, no new file outside `tests/`. Three existing
functions change and three call sites forward.

### `human_gates.label_events` — the module's admission door

- **Responsibility:** decide what a countable label event is. It owns
  three of those tests today (event kind, label name, timestamp
  presence); it gains the fourth (timestamp readability) and, with it,
  the duty to say what it refused.
- **Collaborators:** `_parse_ts` below; its three callers, which forward
  its problems.
- **Deletion test:** if it vanished, the admission rule reappears at
  every site that reads an event tuple — which is the condition
  `defect.md`'s root-cause hypothesis describes. It does not forward.
- **Why the rule sits here and not one function lower:** the door is the
  only place that still knows the *event*. One function lower, at the
  parse, the context is a bare string and the only honest report is "a
  number is missing".

### `human_gates._parse_ts` — the total timestamp reader

- **Responsibility:** the single expression that says what a readable
  GitHub timestamp is. It becomes total — `datetime` or `None`, never a
  raise — so the predicate and the parse are the same code and cannot
  drift. A separate `is_timestamp()` beside an unchanged `_parse_ts`
  would be one fact with two owners, which `one_owner.py` exists to find.
- **Collaborators:** `label_events` (the only caller that may pass an
  unvetted string) and `waited_seconds` (which may not).
- **Deletion test:** holds — its absence puts `fromisoformat` and a
  `tzinfo` test at four sites in three tools.

### The three `_timelines` fetchers — callers, not components

`gate_digest._timelines:109`, `rejection_mining._timelines:146` and
`dashboard._timeline:158` each gain the same single line: unpack the
pair, pass the `operation` string they already built for `gh_read` one
line above, and `problems.extend(...)` into the list they already carry.
They are named here because the interface change reaches them, not
because the design adds anything to them — a function that only forwards
is not a component, and these forward.

ADR-0056 deliberately left these three un-folded, and this design does
not fold them. It reduces what they have to know, which is the opposite
move and the cheaper one.

### `tests/test_human_gates.py` and `tests/test_gate_digest.py` — the pins

- **Responsibility:** pin the exact problem strings through the public
  interfaces, against literal event lists. `defect.md` §1's repro becomes
  a passing test, §3's open-stay history becomes a second (it is the one
  `gate_passages` returns `[]` for, so a passage-only fix would slip
  past it), and the offset-naive input above becomes a third.
- **Collaborators:** none. The module is pure; the digest tests already
  inject a fake `gh` runner and an aware clock.

### The payload twins and `factory/manifest.json`

- **Responsibility:** keep every stamped repo running the same three
  files. `human_gates.py`, `gate_digest.py` and `rejection_mining.py` are
  all identity entries in `factory_init.MIRRORS`
  (`factory_init.py:146-148`), so `python3 factory_init.py
  update-manifest` runs in the same commit or detector E fires.
- **`dashboard.py` is not in `MIRRORS`** — verified against the table —
  so its edit touches no checksum, and no stamped repo is affected by
  the dashboard half at all.

## Data model

There is no storage, no state file and no persistence; nothing about the
shape of a row, a ledger entry or an issue changes. The only data model
statement this design makes is an invariant, and the point of the design
is that it now has an owner.

The event triple is unchanged:

```
event = (timestamp, kind, name)
          timestamp  the raw created_at string, as GitHub sent it
          kind       "labeled" | "unlabeled"
          name       the label name
```

**The invariant, and who owns it:** *every `timestamp` in an event triple
is a string that `datetime.fromisoformat` reads into an **offset-aware**
datetime.* `label_events` owns it, because `label_events` is the only
door through which a timeline fact enters the module. Four consumers
depend on it and none of them re-checks it:

| Consumer | What the invariant buys |
|---|---|
| `waited_seconds` | both operands parse and are aware, so the subtraction is total |
| `gate_passages` | cannot raise; the partition's confirmed half is as durable as its rejected half |
| `waiting_since` | returns a readable string or `None`, never a poisoned one |
| `dashboard._age_seconds` | its unguarded parse is unreachable |

**Access pattern, which is what chose the shape:** exactly one — walk a
fetched timeline once, in order, and answer with the events plus whatever
was refused. There is no lookup, no index, no second pass, and no
consistency question: every comparison happens inside one read of one
timeline, so nothing is eventually consistent with anything.

**One pre-existing property, flagged and not touched.**
`completed_stays` orders and windows timestamps by **string** comparison
(`start <= ts`), which is correct for GitHub's single `…Z` spelling and
would be wrong for a mixed set of equally valid spellings (`+00:00`, a
space separator). Admission narrows the admitted set but does not
canonicalise it. Normalising admitted timestamps to one spelling is a
separate decision with its own evidence, and this run does not make it.

## Interfaces & contracts

### `_parse_ts(iso)` — the total timestamp reader

- **Input:** anything the `created_at` field of a `gh` timeline event can
  hold — a string, a number, `None`, a nested object.
- **Output:** an offset-aware `datetime`, or `None`.
- **Contract:** `None` means *this is not a GitHub timestamp* and covers
  three cases, deliberately collapsed into one answer because no caller
  distinguishes them: unparseable (`ValueError`), not a string
  (`AttributeError`/`TypeError` from `.replace` — `gh` JSON can carry a
  number where a string is expected), and parseable but offset-naive.
  The last is the class the inputs do not name and the measurement found.
- **Failure modes:** none. It is total; that is the whole change. An
  offset-naive timestamp is refused, never coerced to UTC — coercion
  would invent a fact (*whose* midnight?) to keep a payload we already
  know is not the one this tool was written against.
- **What it hides:** the Z-before-3.11 compat quirk it already hid, plus
  the exception vocabulary of `fromisoformat` and the awareness test.
  What it exposes: one optional datetime.

### `label_events(timeline, operation, label=None)` — the admission door

- **Input:** a decoded `gh` issue timeline (a list of event objects);
  `operation`, the caller's name for the read as it appears in a problem
  string (`"gh api timeline for #106"`); `label`, the caller's
  problem-string label (`"gd"`, `"dashboard"`, `"rm"`), or `None` for a
  reader whose own caller owns the label.
- **Output:** `([(timestamp, kind, name), ...], problems)` — the admitted
  events in timeline order, and a list of already-prefixed problem
  strings.
- **`operation` is passed in, never derived.** It is not derivable from
  the timeline, and the caller already holds the exact string one line
  above for `gh_read`. Both parameters mirror `cli.gh_read`'s, which is
  the same situation solved at the same call sites: a shared reader whose
  callers own their labels.
- **Failure modes:** none — it does not raise, on any input. Refusals are
  reported, not thrown. `problems` is empty or holds **exactly one**
  string naming the count and quoting the first refused value:

  ```
  gd: gh api timeline for #106 returned 1 label event(s) with an
  unreadable timestamp (first: 'not-a-timestamp') — not counted
  ```

  One line per timeline, not per event: a systemic payload change makes
  *every* event unreadable on *every* mirrored issue, and the output must
  stay bounded by the mirrored-issue count — the same bound every other
  problem this tool emits already has.
- **Ordering:** unchanged. Admitted events keep timeline order; refusal
  does not reorder what remains.
- **What a caller must know beyond the signature:** a refusal is a
  *dropped event*, not a dropped field, so a history that loses an
  `unlabeled` event reads as an open stay and a history that loses a
  `labeled` event reads as no stay at all. Both degradations are already
  documented behaviours of `waiting_since` and `completed_stays`; the
  problem string is what stops either being mistaken for the truth.
- **Retry:** safe and pure — same input, same output, no clock, no I/O.

### `waited_seconds(start, end)` — unchanged signature, stated precondition

- **Input:** two ISO-8601 timestamps that `_parse_ts` reads into aware
  datetimes.
- **Output:** whole seconds, `int`.
- **Precondition, and where each half comes from:** `start` is guaranteed
  by `label_events`' admission; `end` is either the same or the caller's
  own clock (`gate_digest._queues` passes `now.isoformat()` from an
  injected `clock`, aware by default and in every test). **The injected
  clock must be timezone-aware** — that is the one obligation this
  contract puts on a caller, and it is what the design substitutes for a
  `None` return.
- **Failure modes:** none reachable. It is deliberately **not** made
  total: returning `None` here would push a `None` branch into
  `gate_passages` and `_queues` to defend a state admission makes
  impossible. The invariant is recorded in the docstring instead.

### `waiting_since(events, queue_label)` — unchanged, guarantee strengthened

- **Output:** unchanged — the current stay's timestamp, or `None`.
- **What changed:** the returned string is now guaranteed readable. `None`
  keeps both of its existing meanings (label not applied; the `labeled`
  event fell off the fetched window) and gains a third (the `labeled`
  event was refused) — which is why the refusal must be reported, or the
  three become indistinguishable.

### `cli.gh_read(...)` — the network seam, restated because it is one

Unchanged by this design, and the seam every byte of this data crosses.

- **Timeout: none.** `cli.runner` calls `subprocess.run(..., check=True,
  capture_output=True, text=True)` with no `timeout`, by design; a hung
  `gh` hangs the daily step until the job's own limit. This design does
  not change that, and does not need to.
- **What the caller sees when it trips:** `gd: gh api timeline for #106
  failed: <detail>` with `value is None`; the issue is skipped and the
  digest still posts.
- **Retry is safe.** The whole daily run is idempotent: the ledger
  dedupes on `cost_ledger.row_key`, and the digest issue is edited in
  place. A re-run after any failure above re-derives everything.
- **What it owns and what it does not:** transport failure, JSON decode,
  top-level shape, window truncation. Field semantics are not its
  business and do not become its business here.

### The three caller edits

Identical at all three sites, and each is one statement:

```python
operation = f"gh api timeline for #{number}"
read = gh_read([...], operation, label="gd", run=run)
...
events[number], walk_problems = label_events(
    [event for page in read.value for event in page], operation, label="gd")
problems.extend(walk_problems)
```

- **Failure modes:** none added. Each caller already holds a `problems`
  list and already extends it from `read.problems`; this is the second
  extend, from the second reader of the same payload.
- **Exit behaviour:** `gate_digest.main` already ends in
  `report("gate_digest", problems)`, which prints each line and returns 1
  when the list is non-empty. `rejection_mining.main` and
  `dashboard.main` do the same with their own labels. The nonzero exit
  `defect.md` demands needs no new code.

## Stack & dependencies

- **Python 3 standard library only** — `datetime` already imported by
  both modules. Nothing new, at root or in the payload. CLAUDE.md's hard
  convention, and this design has no reason to test it.
- **No new shared module and no new seam.** CLAUDE.md's bar is multiple
  real callers *and* observed divergence between their copies; there is
  one rule with one owner here and no copies to diverge. Canon's rule
  points the same way — one adapter is a hypothetical seam.
- **`cli.gh_read`, `cli.report`, `cli.label_names`** — the existing seams,
  used exactly as they are used today. The cost of a dependency is its
  interface, and this design adds nothing to theirs.
- **`factory_init.MIRRORS` + `factory/manifest.json`** — not a dependency
  choice but a shipping obligation: three of the four edited modules are
  identity mirror entries, so `update-manifest` is part of the change,
  not a follow-up.

## Decisions & alternatives

- **Admission in `label_events`** over **a `try/except ValueError` around
  `_parse_ts`** — measured, the naive-timestamp class raises `TypeError`
  and walks straight past a `ValueError` guard, so the small fix does not
  even reach the never-a-traceback bar.
- **Admission in `label_events`** over **each caller validating** — the
  rule would be written three times in the three fetchers ADR-0056
  deliberately left un-folded, two of which are the pair whose duplicated
  window test justified that ADR.
- **Admission in `label_events`** over **`cli.gh_read` validating the
  field** — `gh_read` is generic over every `gh` read in the tree and its
  docstring scopes it to transport; and the fetchers are three, so the
  check would not localise anyway.
- **Refuse *and* report** over **refuse silently, like `cli.label_names`**
  — a dropped nameless label removes nothing a caller could act on; a
  dropped label flip rewrites the gate history the digest prints as fact,
  and `defect.md`'s first success criterion names the problem string
  explicitly.
- **`(events, problems)`** over **a sibling `unreadable_timestamps()`
  the callers also call** — it keeps the 17 test call sites unchanged and
  walks the timeline twice, but a caller that forgets the second call is
  silently back to today's degradation with no signal.
- **`(events, problems)` as a plain pair** over **a `namedtuple` like
  `cli.GhResult`** — `GhResult` earned its name on a third field
  (`truncated`) callers must read rather than infer; there is no third
  fact here, and `(value, problems)` is the tree's dominant shape
  (`cost_ledger.read`, `dashboard._remote`).
- **`operation` required, `label` optional** over **both optional** —
  every caller already holds the string, and a problem line that cannot
  name whose timeline it walked is not actionable across forty mirrored
  issues. `label` defaults to `None` because `cli.gh_read`'s does, for a
  reader whose own caller owns the label.
- **One problem line per timeline** over **one per refused event** — a
  systemic payload change makes every event on every issue unreadable;
  per-event output is unbounded, per-timeline output is bounded by the
  mirrored-issue count, which is the bound this tool's other problems
  already have.
- **Refuse an offset-naive timestamp** over **coercing it to UTC** —
  coercion invents a fact to salvage a payload already known to be
  unlike the one the tool was written against, and it would make the
  `waited_seconds` invariant depend on a guess.
- **`_parse_ts` total (`datetime | None`)** over **a separate
  `is_timestamp()` predicate** — two spellings of one rule is the
  duplication the repo built `one_owner.py` to find.
- **`waited_seconds` left raising-by-invariant** over **made total too** —
  a `None` return would add a branch at `gate_passages` and `_queues` for
  a state admission makes unreachable; `implementation-discipline.md`
  calls for the comment, not the code.
- **The miner forwards** over **`events, _ = label_events(...)`** —
  discarding preserves the digest/miner asymmetry in a new form and would
  be the only place in the tree that knowingly drops a problem string.
- **The dashboard forwards, `_age_seconds` untouched** over **guarding
  `_age_seconds` as well** — the guard would defend a state the invariant
  makes impossible, and two guards for one rule is how the asymmetry
  started.

## What this design deliberately does not do

- **It does not restore the lost ledger commit (`defect.md` §5).** The
  commit step is gated on the digest step succeeding, and an honest
  problem string exits 1. Fixing it means `if: always() && …` in a
  mirrored workflow, changing commit behaviour for every failure mode of
  the digest. Recorded as seed text for a follow-on session to append to
  `docs/backlog.md` — **not appended here**, since this run's only
  sanctioned backlog write was its own seed claim:

  > `.github/workflows/gate-digest.yml`'s commit step is gated
  > `if: steps.digest.outputs.changed == 'true'`, which implies
  > `success()`, so any `gd:` problem string — not just a crash — skips
  > the commit and discards the gate-latency rows `gate_digest` already
  > appended on the runner; the rows survive to the next clean re-scan
  > (`cost_ledger.row_key` dedup) but are lost for as long as the problem
  > recurs, and `always() &&` would change commit behaviour for every
  > failure mode of the digest in a file every stamped repo runs
  > (from: maintenance:a-timestamp-the-digest-cannot-parse)

- **It does not append `defect.md`'s draft dashboard seed.** That seed's
  own condition — *"whether this is fixed at all depends on where
  maintenance:a-timestamp-the-digest-cannot-parse puts its catch"* — is
  answered: the catch is at admission, and the dashboard exposure closes
  with it. The seed is unnecessary.

- **It does not canonicalise admitted timestamps**, so
  `completed_stays`' string ordering keeps its existing dependence on
  GitHub's single `…Z` spelling. Flagged above, pre-existing, and not
  this run's to change.

- **It does not fold the three `_timelines` fetchers.** ADR-0056 put
  them out of scope with a reason that still holds; this design reduces
  what they must know instead.

- **It does not touch `cli.gh_read`, `cli.CLI_FAILURES`,
  `cost_ledger.py:189`'s already-guarded parse, `gates.py` detector J, or
  any detector, workflow or Makefile target.**

- **It writes no ADR file.** See below.

## ADRs

**One ADR is offered — proposed text only. No file is written into
`docs/adr/` by this stage.** The precedent did exactly this and the file
was written later in the run.

The tool-level fix does not meet the bar on its own (easy to reverse,
unsurprising, barely a trade-off) and is recorded above as one-line
decisions. The **relocation of field-level admission into the walk** meets
all three: it is hard to reverse once three callers and 17 tests take the
new signature; it is surprising without context, because `label_events`'
docstring currently says the opposite in as many words; and it is the
result of a real trade-off between three priced options, one of which has
an exact in-repo precedent (`cli.label_names`) and still loses.

It **amends ADR-0056** rather than superseding it. Everything ADR-0056
decided stands — the module, the `Gate` namedtuple, `completed_stays` as
the executable partition, detector J's reach, the purity stance, the
un-folded fetchers. One sentence of one docstring changes, and the
partition gets stronger. Mechanically that means ADR-0056's Status line
becomes the `amended by` form naming the new number — a status the
`gates.ADR_STATUS` grammar already accepts and which leaves the decision
live and citable — and its row in `docs/adr/README.md` must match
byte-for-byte. **ADR-0056's body is not rewritten**, per CLAUDE.md.

The next free number is **0062** (`docs/adr/` holds 0001–0061 and nothing
cites 0062). It is written bare, without the typed-ID prefix, on purpose:
a prefixed token for a file that does not exist is a dangling reference
to detector C and would turn the battery red on the artifact that
proposes it.

**For the record, a Ship-stage consequence, not a reason to avoid the
ADR:** under ADR-0036 clause 3, any PR touching `docs/adr/**` — or a
run's `architecture.md`, which this run also has — requires a human
code-owner merge. This run is prepare-and-stop, so that is where it
stops anyway.

Proposed as `docs/adr/0062-a-label-event-is-admitted-only-if-its-timestamp-reads.md`:

```markdown
# A label event is admitted only if its timestamp reads

- Status: provisional
- Date: 2026-09-15

Amends ADR-0056. Everything that decision made stands — the module, the
Gate namedtuple, completed_stays as the executable partition, detector
J's reach through gate_labels(), the purity stance, and the three
un-folded fetchers. This amends one sentence of one docstring and, with
it, which layer owns field-level validation of a timeline event.

## Context

human_gates.label_events admits a timeline event when its label name and
created_at are merely truthy. Its docstring states a delegation on
purpose: "Anything that is not a well-formed label flip is not this
module's business; an unusable timeline is the fetcher's problem, never
this walk's." The fetchers validate through cli.gh_read, which owns
transport failure and the top-level shape and deliberately owns no field
semantics. So no layer checks the field, and each believes another did.

A created_at that is truthy and unreadable therefore reaches
datetime.fromisoformat unguarded, and the ValueError leaves
waited_seconds, run_daily, main and sys.exit(main(...)) — a Python
traceback where gate_digest.py's own docstring, ADR-0051 and CLAUDE.md
all promise a label-prefixed problem string and a nonzero exit. Two call
sites reach it independently (the completed-stay path through
gate_passages, the open-stay path through waited_seconds), and a third
exposure sits in dashboard._age_seconds, fed from the same pair. A fourth
input class was measured during design: an offset-NAIVE but perfectly
valid ISO-8601 timestamp parses and then raises TypeError on the
subtraction, so a guard written only against ValueError does not clear
the bar.

The asymmetry is the tell. gate_rejections survives the same event list
that kills gate_passages, because it never asks for a duration. ADR-0056
has the two halves partition one list as "two views of one walk"; against
a bad timestamp one view is durable and the other is not. That is the
shape of a validation gap sitting one layer too low.

## Decision

**label_events decides whether a timestamp is readable, and says what it
refused.**

    label_events(timeline, operation, label=None) -> (events, problems)

- **_parse_ts becomes total** — an aware datetime or None, never a raise.
  None covers unparseable, not-a-string, and parseable-but-offset-naive.
  An offset-naive timestamp is refused, not coerced: coercion invents a
  fact to salvage a payload already known to be foreign.
- **Admission gains a fourth test**, alongside the three the walk already
  applies (event kind, label name, timestamp presence). This does not
  reverse the docstring's delegation, it completes it: the operative
  clause — "anything that is not a well-formed label flip is not this
  module's business" — already sanctions dropping, and the clause that
  delegates is about an *unusable timeline*, which remains cli.gh_read's.
  A well-formed array with one unreadable field is not an unusable
  timeline.
- **A refusal is reported, never silent.** The walk answers with one
  already-prefixed problem string per timeline, naming the count and
  quoting the first refused value. Per timeline rather than per event, so
  a systemic payload change stays bounded by the mirrored-issue count.
  operation and label mirror cli.gh_read's parameters, at the same call
  sites, for the same reason: the caller owns its label, and the
  operation string is not derivable from the payload.
- **Everything below the door becomes total by construction.**
  waited_seconds is NOT made to return None; the invariant makes the
  branch unreachable and the docstring records it. dashboard._age_seconds
  gains no guard for the same reason.
- **The callers forward.** gate_digest._timelines,
  rejection_mining._timelines and dashboard._timeline each unpack the
  pair and extend the problems list they already carry. The miner
  forwards rather than discards — discarding would preserve the
  asymmetry in a new form.

## Consequences

- The digest reports and exits nonzero where it used to traceback. Both
  independently reachable call sites are covered by one rule.
- **The asymmetry is removed, not documented as intentional.** Both
  halves of ADR-0056's partition walk the same admitted list and report
  the same refusal, so "two views of one walk" becomes true of refusals
  as well as of stays.
- The third exposure, dashboard._age_seconds, closes as a consequence
  rather than as a separate fix. dashboard.py is not in
  factory_init.MIRRORS, so no stamped repo is affected by that half.
- label_events' signature is breaking: three production call sites and
  seventeen in tests/test_human_gates.py. That is the price of the rule
  existing exactly once.
- human_gates.py, gate_digest.py and rejection_mining.py are identity
  entries in factory_init.MIRRORS, so `python3 factory_init.py
  update-manifest` runs in the same commit (detector E).
- What is NOT restored: the gate-latency rows. The gate-digest workflow
  gates its commit step on the digest step succeeding, so an honest
  problem string still skips the commit. Changing that alters commit
  behaviour for every failure mode of the digest and is left to its own
  decision.
- Status is provisional: this records a mechanism on first use against a
  latent defect with zero production incidence (55 scheduled runs, no
  occurrence), and nothing has been confirmed by a real firing.
```

## Traceability

`defect.md` records no PRD (maintenance runs skip it), so the trace runs
against its Success criteria.

| `defect.md` success criterion | Where it lands |
|---|---|
| Malformed timestamp → `gd:` problem string + nonzero exit, never a traceback | `label_events` admission + the caller forward; measured above, exit 1 |
| **Both** call sites covered — completed-stay and open-stay | one rule above both; both histories measured above |
| §1 repro a passing test, plus the §3 open-stay history | `tests/test_human_gates.py` pins, plus a third for the offset-naive class |
| §6 asymmetry removed **or** recorded as intentional | **removed** — both halves walk one admitted list and both report |
| Payload twins + manifest match root, detector E green | three `MIRRORS` identity entries; `update-manifest` in the same commit |
| Full battery green | baseline quoted above; no detector, workflow or Makefile target changes |
| `one_owner.py` gains no new problems | no new module-level value and no new payload-key reader is introduced |

Two things `defect.md` asked for are answered differently than it framed
them, and both are stated rather than absorbed: `dashboard.py` moves from
out-of-scope to closed-as-a-consequence (assumption 5), and
`rejection_mining.py` takes one forwarding line (assumption 4). One thing
`defect.md` did not know is added: the offset-naive input class, which
decides the admission predicate.

Next stage is Decompose. It owns the work items, their order and their
acceptance criteria; this artifact deliberately contains no breakdown,
no estimate and no sequencing.
