---
stage: decompose
run: maintenance:a-timestamp-the-digest-cannot-parse
date: 2026-09-15
assumptions:
  - "The cut was not reviewed live — this run is driven from autorun-brief.md, so the milestone boundaries, the item sizes and the ordering below are read out of architecture.md's Components and Interfaces & contracts sections rather than from an operator's judgment. docs/fixes/one-fact-one-owner/breakdown.md, this run's stated artifact-depth precedent, logged and did exactly the same. A mis-sized row is a note to log at implement time, not a design change."
  - "Items are lettered and carry a size class (ADR-0034 vocabulary), matching the precedent. No row mints a WO-#### id and no row carries a tracker reference: those tokens are dispatch-plane identifiers that detectors A and C read, minting one with no issue behind it would run the dispatch plane ahead of the knowledge plane (ADR-0032), and defect.md's standing authorization is no tracker interaction at all. These checkboxes are the whole state (ADR-0026)."
  - "The test-ordering rule is served INSIDE each item, never as a standalone red test file — the tree must not be red at an item boundary. Two shapes are needed here because only two items change behavior. A1 and A2 write their cases against today's code and watch them fail. A3, B1 and B2 pin behavior an earlier item already delivered, so there is nothing to watch fail into existence; each is watched to fail by MUTATION — the rule it depends on temporarily removed, the mutation reverted, the failure recorded in the commit message — which is how the precedent's own Implement stage resolved the identical situation (its deviation 2)."
  - "A2 is atomic and cannot be split. label_events(timeline, operation, label=None) is a breaking signature change, so the three production call sites (gate_digest.py:109, rejection_mining.py:146, dashboard.py:158) and the seventeen in tests/test_human_gates.py — both counts confirmed at HEAD 622e7c0 by grep, matching architecture.md — must move in the same change or the tree is red at the boundary. Splitting the mechanical migration from the admission rule was considered and rejected twice over: it would land an `operation` parameter nothing reads for one commit, and for that commit the miner would discard the problems it is handed, which architecture.md names as the one thing the tree must never do."
  - "dashboard._age_seconds: architecture.md says it 'is not edited and gains no guard' and, in the same paragraph, that 'the docstring says where the guarantee comes from'. Read as: its BODY is unchanged — no guard, no try, no None branch — and its docstring records the invariant's owner. B2's criterion is written to satisfy both readings at once, so nothing is chosen here; this is a reading of the architecture, not a decision about it."
  - "Manifest regeneration is folded into each item that edits a factory_init.MIRRORS entry and is never deferred to a closing item, because detector E fires at the boundary otherwise. Verified against the MIRRORS table at HEAD rather than taken from prose: human_gates.py, gate_digest.py and rejection_mining.py are identity entries and their twins are byte-identical today (diff clean for all three); dashboard.py, tests/** and docs/** are not entries at all. So A1 and A2 each run `python3 factory_init.py update-manifest` in their own commit, and A3, B1, B2 and C1 need none."
  - "The proposed ADR's number is written bare throughout this file, without its typed-ID prefix, exactly as architecture.md writes it: detector C reads prefixed tokens out of artifact prose (gates.py:373) and one whose file does not exist is a dangling reference. The prefixed form is written for the first time inside C1's own commit, in ADR-0056's Status line and index row — after the record exists. Referring to the proposed file by path is safe and is what C1 does; a markdown link to it would not be, because detector I reads link targets off disk."
  - "No item is added for the gate-digest workflow's commit step. architecture.md puts it out of scope under `What this design deliberately does not do` and leaves the draft backlog seed there; this run's only sanctioned backlog write was its own seed claim, so the seed stays inside that artifact — not restated here, and not appended to docs/backlog.md. Both earlier stages kept draft seed text inside their own artifacts for the same reason."
---

# Breakdown: a timestamp the digest cannot parse

Progress lives in the checkboxes below. Source is `architecture.md` in this
directory, which answered the catch-site question against a design probe run
at HEAD `622e7c0` on 2026-09-15. Rows carry an item letter, a size class and
blocking edges; they carry no work-order id and no tracker reference.

**The rule this run implements, in one line.** `label_events` gains a fourth
admission test — a timestamp must *read* — and says what it refused;
everything below the door becomes total by construction. There is no new
module, no new seam and no new file outside `tests/` and `docs/adr/`.

**The ordering rule, which decides the cut.** Cases at the intended interface
land with the change that makes them pass, inside one item, and the battery is
green at every item boundary. Two items change behavior (A1, A2) and write
their cases red first; three items pin behavior an earlier item delivered
(A3, B1, B2) and are watched to fail by mutation instead. Read the history for
that pattern, not for separate pin commits.

**The battery is green at every item**, in full: `python3 -m unittest discover
tests`, `python3 lint.py` (matching `lint: 0 problem(s)`) and `python3
gates.py && python3 gates.py --selftest` (matching `gates: 0 problem(s)` and
`selftest: ok`). `python3 one_owner.py` is **not** part of it and never
becomes part of it — it carries nine pre-existing problems on `main`, clearing
them is not this run's job, and this run may not add to them (C2 checks the
count, not the battery).

**Two refused classes, not one, and both are named in every criterion that
covers a timestamp.** `defect.md` knows the garbage string
(`'not-a-timestamp'`, `ValueError`). `architecture.md` measured a second:
`'2026-08-30T10:00:00'` is valid ISO-8601, parses cleanly, is offset-**naive**,
and raises `TypeError` on the subtraction — so a `try/except ValueError` around
the parse does not clear the never-a-traceback bar. A1 refuses it at the parse,
A2 refuses it at admission, A3 and B2 pin it end to end.

**Manifest churn, stated up front.** Exactly two items touch a
`factory_init.MIRRORS` entry — **A1** (`human_gates.py`) and **A2**
(`human_gates.py`, `gate_digest.py`, `rejection_mining.py`) — and each runs
`python3 factory_init.py update-manifest` in its own commit with the
regenerated twins and manifest. `dashboard.py` is not an entry, so the whole
dashboard half of this run touches no checksum and reaches no stamped repo.

## Milestone A: the door refuses, and the digest reports instead of tracebacking

Demonstrable at the close of A3: the two histories that killed the daily run in
`defect.md` §1 and §3, plus the offset-naive class `defect.md` does not name,
each produce a `gd:`-prefixed problem string and exit 1 out of the real
`main` — no traceback, on either independently reachable call site. That is
this run's headline criterion, and it is met before any ADR is written.

- [ ] **A1** `_parse_ts` becomes the total timestamp reader — size:S, blocked by: —
  - Accept: `human_gates._parse_ts(iso)` returns an offset-**aware**
    `datetime` or `None`, and raises on nothing. `tests/test_human_gates.py`
    covers, each case written and watched to fail against today's code before
    the change: a well-formed `…Z` timestamp still parses to the same aware
    datetime it parses to today, so the pre-3.11 `Z` compat quirk the helper
    already hid is not lost; `'not-a-timestamp'` returns `None` where it
    raises `ValueError` today; `'2026-08-30T10:00:00'` — valid ISO-8601,
    offset-naive — returns `None`, **refused and not coerced to UTC**, because
    coercion would invent a fact to salvage a payload already known to be
    foreign; a non-string (`None`, an `int`) returns `None` rather than
    raising `AttributeError` or `TypeError` out of `.replace`. The docstring
    states the total contract and names the three cases it deliberately
    collapses into one answer. No separate `is_timestamp()` predicate is
    added — one rule, one spelling, which is what `one_owner.py` exists to
    find. **The defect is not fixed at this item and nothing claims it is:**
    with admission still absent a refused timestamp now reaches
    `waited_seconds` as `None`, so the traceback changes species (`TypeError`
    rather than `ValueError`) and does not go away; no test asserts it either
    way, because none exists (`defect.md` §9). `human_gates.py` is a
    `factory_init.MIRRORS` identity entry, so `python3 factory_init.py
    update-manifest` runs in this same commit with the regenerated twin and
    manifest; detector E and `tests/test_factory_init.py`'s payload-vs-root
    pin green.
- [ ] **A2** `label_events` admits on readability, says what it refused, and every call site moves — size:L, blocked by: A1
  - Accept: `label_events(timeline, operation, label=None)` returns
    `([(timestamp, kind, name), ...], problems)`; admitted events keep
    timeline order; refusal reorders nothing; the walk raises on no input at
    all. A **fourth** admission test joins the three the walk already applies
    (event kind, label name, timestamp presence): an event whose `created_at`
    does not read through `_parse_ts` is refused. `problems` is empty, or
    holds **exactly one** string per timeline naming the refused count and
    quoting the first refused value, prefixed with the caller's label through
    the same `prefix = f"{label}: " if label else ""` shape `cli.gh_read`
    uses at these same call sites — and the `label=None` branch is pinned by
    a case of its own, so the default that exists to mirror `gh_read` is not
    dead by omission. Cases in `tests/test_human_gates.py`, written and
    watched to fail first: `defect.md` §1's three-event history yields two
    admitted events, one problem, and `gate_passages` returning `[]`
    **without raising** — the §1 repro becomes a passing regression test;
    §3's one-event open-stay history yields no admitted events, one problem,
    and `waiting_since` returning `None` — the history `gate_passages`
    returns `[]` for, so a passage-only fix would slip past it; the
    offset-naive `'2026-08-30T10:00:00'` history yields the same refusal;
    **two** refused events in one timeline yield ONE problem line naming the
    count and quoting the FIRST, never two lines, because a systemic payload
    change must stay bounded by the mirrored-issue count; a timeline with no
    refusals yields an empty problems list and events byte-identical to
    today's. The three production call sites forward, each in one statement,
    each passing the `operation` string it already built one line above for
    `gh_read`: `gate_digest._timelines` (`gate_digest.py:109`, `label="gd"`),
    `rejection_mining._timelines` (`rejection_mining.py:146`, `label="rm"`)
    and `dashboard._timeline` (`dashboard.py:158`, `label="dashboard"`) unpack
    the pair and `problems.extend(...)` into the list each already carries —
    **the miner forwards, it does not discard**. All seventeen call sites in
    `tests/test_human_gates.py` move with the signature. Three docstrings move
    with it too: `label_events`' operative clause is completed rather than
    reversed and its fetcher-delegation clause survives verbatim (an unusable
    *timeline* is still `cli.gh_read`'s); `waited_seconds` records its
    precondition — both operands parse and are aware, `start` by admission and
    `end` from an aware injected clock — and is deliberately **not** made
    total, because a `None` return would add a branch at `gate_passages` and
    `_queues` for a state admission makes unreachable; `waiting_since` records
    `None`'s third meaning (the `labeled` event was refused), which is why the
    refusal must be reported or the three meanings become indistinguishable.
    `human_gates.py`, `gate_digest.py` and `rejection_mining.py` are `MIRRORS`
    identity entries, so `python3 factory_init.py update-manifest` runs in
    this same commit with the three regenerated twins and the manifest;
    `dashboard.py` is not an entry and touches no checksum. **This item is not
    splittable** — see the fourth assumption.
- [ ] **A3** both of the digest's call sites, pinned end to end — size:M, blocked by: A2
  - Accept: `tests/test_gate_digest.py` pins, through the public interface
    with the injected fake `gh` runner and the injected aware clock the suite
    already has, that each of the two independently reachable call sites
    reports rather than raises: the **completed-stay** path (`_capture_latency`
    → `gate_passages`, `defect.md` §1's history) and the **open-stay** path
    (`_queues` → `waited_seconds`, §3's history), each for **both** refused
    classes — the garbage `'not-a-timestamp'` and the offset-naive
    `'2026-08-30T10:00:00'`. For each: `run_daily` returns its outputs dict
    **alongside** exactly one `gd:`-prefixed problem instead of raising,
    `main` writes those outputs into the injected env before `report` returns
    (the ordering is `gate_digest.py:229-235`) and returns **1**, and nothing
    in the call chain raises. The open-stay case additionally asserts the
    degradation is the documented one rather than a silent wrong answer: the
    item still lists in its queue, with no age. No production code changes in
    this item, so the cases pass the moment they are written; the ordering
    rule is served by mutation — each pin is watched to fail with the fourth
    admission test temporarily removed from `label_events`, the mutation
    reverted, and the failure recorded in the commit message. `factory/`
    untouched; no manifest regeneration.

## Milestone B: both halves of the partition report, and the third exposure closes

Demonstrable at the close: the timeline that killed the digest and left the
miner silent in `defect.md` §6 now produces an `rm:` problem string from
`rejection_mining` and a `dashboard:` one from `dashboard`, so ADR-0056's
"two views of one walk" becomes true of refusals as well as of stays — the
asymmetry is **removed**, not documented as intentional. `dashboard._age_seconds`,
the third exposure, is unreachable rather than guarded.

- [ ] **B1** the miner reports what the digest reports — size:S, blocked by: A2
  - Accept: `tests/test_rejection_mining.py` pins, through `run_mine` with the
    suite's fake `gh`: the identical timeline that produced `problems: []` in
    `defect.md` §6 now produces exactly one `rm:`-prefixed problem naming the
    same refusal in the same shape the digest names it, `main` returns 1, and
    the miner's outputs for that history are otherwise unchanged
    (`0 candidate WO(s), 0 correction(s) mined`). A second case pins the other
    half of `defect.md`'s fourth success criterion: on a **well-formed**
    timeline the miner's behavior is byte-identical to today's — no problem,
    same rejections, same outputs — so the forward costs nothing on the happy
    path. Together these are what *the asymmetry is removed* means: both
    halves of ADR-0056's partition walk the same admitted list and both
    report the same refusal through their own label. The forward itself is not
    re-implemented here (it landed in A2); the pins are watched to fail with
    the miner's `problems.extend(...)` temporarily replaced by a discard, the
    mutation reverted, and the failure recorded in the commit message.
    `factory/` untouched by this item; no manifest regeneration.
- [ ] **B2** the dashboard reports, and `_age_seconds`' parse becomes unreachable — size:M, blocked by: A2
  - Accept: `tests/test_dashboard.py` pins, through `gather` with the suite's
    injected fakes: for **both** refused classes, exactly one
    `dashboard:`-prefixed problem lands in `state["problems"]`, `main` returns
    1, and nothing raises — where `defect.md` §3's last line raised
    `ValueError` out of `_age_seconds`. `waiting_since` returns `None` for the
    refused history, so the queue entry renders with no age and the item still
    lists, and `_age_seconds` is never reached with a string `label_events`
    refused. **`dashboard._age_seconds`' body is unchanged** — no guard, no
    `try`, no `None` branch — because the state it would defend against cannot
    occur under admission and `implementation-discipline.md` calls for the
    comment, not the code; its docstring names where the guarantee comes from
    (`label_events` admits no unreadable timestamp, so `since` is readable or
    `None`, and the `None` case never calls it). Two guards for one rule is
    how the asymmetry started, so a second one is not added here.
    `defect.md`'s draft backlog seed for this exposure is **not** appended to
    `docs/backlog.md`: the seed's own condition — *whether this is fixed at
    all depends on where this run puts its catch* — is answered, the catch is
    at admission, and the exposure closes in this run rather than being
    deferred. `dashboard.py` is not a `factory_init.MIRRORS` entry (verified
    against the table, not taken from prose), so it has no twin, touches no
    checksum, and no stamped repo is affected by this item; no manifest
    regeneration.

## Milestone C: the decision is on the record and the tree ships clean

Demonstrable at the close: the relocation of field-level admission into the
walk is recorded as its own decision; ADR-0056 stays live and citable under the
`amended by` form rather than being rewritten; the three payload twins and the
manifest match root; and the full battery is green with `one_owner.py` carrying
its nine pre-existing problems and no tenth.

- [ ] **C1** the 0062 record, its index row, then ADR-0056's amendment — in that order — size:M, blocked by: A2
  - Accept: three edits, **in this order, inside one commit**, because the
    order is the whole hazard. *First*,
    `docs/adr/0062-a-label-event-is-admitted-only-if-its-timestamp-reads.md`
    is created with the text `architecture.md` proposes under its *ADRs*
    section, status `provisional`, dated 2026-09-15, its `- Status:` line
    satisfying `gates.ADR_STATUS` (detector D). *Second*, a row for it joins
    `docs/adr/README.md` in the same three-column shape as the 0061 row above
    it: a first cell linking the file by its own filename, a title cell
    reading *A label event is admitted only if its timestamp reads*, and a
    status cell matching the file's `- Status:` line **byte for byte**, which
    is what detector D compares. (The row is described rather than quoted
    here: a live markdown link to a file that does not yet exist is a stale
    link to detector I, and the prefixed token for a record that does not yet
    exist is a dangling reference to detector C.) *Third, and only then*,
    `docs/adr/0056-human-gates-module.md`'s `- Status:` line moves from
    `accepted` to the `amended by` form naming the new number — a status
    `gates.ADR_STATUS` already accepts and which leaves ADR-0056 **live and
    citable**, not retired, so every artifact that cites it stays clean — and
    its row in `docs/adr/README.md` is updated so its status cell still
    matches byte for byte. **ADR-0056's body is not rewritten** (CLAUDE.md:
    supersede or amend with a new ADR, never rewrite): one Status line and one
    index cell change, and nothing else in that file moves. The sequencing is
    the point — the `amended by` form names the new number as a prefixed
    token, so the record must exist before the status line names it or the
    status line is itself a dangling reference. This item is blocked on A2 so
    the record's Consequences describe callers that already forward. `python3
    gates.py && python3 gates.py --selftest` green, detectors C, D and I in
    particular. `docs/` is not mirrored; no manifest regeneration. The repo
    gains one more open provisional, knowingly — the mechanism is recorded on
    first use against a latent defect with zero production incidence.
- [ ] **C2** the twins, the manifest, and the closing battery — size:S, blocked by: A3, B1, B2, C1
  - Accept: `diff` is clean between each of `human_gates.py`, `gate_digest.py`
    and `rejection_mining.py` and its twin under
    `factory/templates/tools/factory/`; re-running `python3 factory_init.py
    update-manifest` leaves `git status` clean, because every item that
    touched a mirrored file already regenerated in its own commit and the
    closing run is a no-op; detector E is green and
    `tests/test_factory_init.py`'s payload-vs-root pin is green. The full
    battery from the repo root, output quoted rather than asserted: `python3
    -m unittest discover tests` OK with the new cases counted, `python3
    lint.py` matching `lint: 0 problem(s)`, and `python3 gates.py && python3
    gates.py --selftest` matching `gates: 0 problem(s)` and `selftest: ok`.
    `python3 one_owner.py` reports the **same nine** pre-existing problems and
    no tenth — expected, since this change introduces no new module-level
    value and no new payload-key reader (`label_events`' key set is
    unchanged). `git status` shows no unregenerated payload and no stray file.
    `dashboard.py` has no twin, so nothing is expected under `factory/` for
    it.

## Design gaps found

**None routes back to Architect.** Three things decomposition surfaced are
recorded here rather than absorbed silently, each with the authority that
settled it; all three are readings or pre-existing facts, and none is a
decision this stage took.

### Absorbed 1 — `_age_seconds` is "not edited" and its docstring still gains a sentence

`architecture.md` says in one paragraph that `dashboard._age_seconds` "is
**not** edited and gains no guard" and that "the docstring says where the
guarantee comes from". A docstring is an edit, so the two sentences need a
reading: the **body** is unchanged — no guard, no `try`, no `None` branch,
which is the sentence's substance under `implementation-discipline.md` — and
the docstring records the invariant's owner, which is what the same paragraph
asks for in place of code. B2's criterion is written so both readings are
satisfied by the same diff. Nothing is chosen; if Implement finds the
architecture meant the file to go entirely untouched, dropping one docstring
sentence satisfies B2's remaining clauses unchanged.

### Absorbed 2 — the dashboard's problem line is bounded per gate-queue membership, not per issue

`architecture.md`'s contract says one problem line per timeline, "bounded by
the mirrored-issue count". At the dashboard's call site that bound is one line
per *(gate, issue)* pair, not per issue: `dashboard._queues` (`dashboard.py:174-195`)
loops gates outside issues and calls `_timeline` inside both, so an issue
carrying two queue labels at once would be fetched, refused and reported twice.
The authority that settles it is the same call site: `read.problems` from
`cli.gh_read` already duplicates identically there, today, for a failed fetch —
the multiplicity is pre-existing, not introduced, and `architecture.md` scopes
the dashboard edit to "the same single line". Still bounded, still small (an
issue sits in one gate queue at a time in practice), and folding the three
`_timelines` fetchers is explicitly out of scope. Recorded so Verify does not
read a duplicate line as a new defect.

### Absorbed 3 — `human_gates.py`'s module docstring survives, checked rather than assumed

The module docstring's closing claim — that the timeline *fetch* "stays with
the tools that own its failure meaning (ADR-0051)" — reads like it might be
falsified by a pure module that now emits `gd:`/`rm:`/`dashboard:` problem
strings. It is not: the fetch does stay with the tools, the module stays pure
(no `gh`, no ledger, no filesystem, no clock), and what moved is a judgment
about a payload's field, not the fetch. The "callers are thin" sentence
survives too — the callers gain a forward, which is the thinnest thing a caller
can gain. No item edits that docstring, and none should; `architecture.md`
scopes the docstring change to `label_events`, `waited_seconds`,
`waiting_since` and `_parse_ts`, and those are A1's and A2's.

## Notes

- **Milestone order.** A first, because the run's headline criterion — a
  problem string and exit 1 instead of a traceback, on both call sites — is met
  at A3 and needs nothing from B or C. B second, because the miner and the
  dashboard are *evidence* items: their forwards already landed in A2 by force
  of the signature, and what remains is pinning that the asymmetry is gone. C
  last, because the record describes callers that already forward, and the
  closing battery should measure a tree that is finished.
- **Seven items, one of which is forced to be large.** A2 is the signature,
  the rule, the string, three caller forwards and seventeen test call sites in
  one change; ADR-0034's L class is "cross-cutting slice", which is exactly
  what it is. Everything around it is small because the design put the rule in
  one place: A1 is one helper, A3/B1/B2 are pins, C1 is three ordered edits
  under `docs/adr/`, C2 is verification.
- **Every component in `architecture.md` has an item.** `label_events` → A2.
  `_parse_ts` → A1. The three `_timelines` fetchers (callers, not components)
  → A2, with their evidence at A3, B1 and B2. `tests/test_human_gates.py` and
  `tests/test_gate_digest.py`, the pins → A2 and A3. The payload twins and
  `factory/manifest.json` → A1 and A2 (regeneration in the same commit) and C2
  (the end-state check). The offered ADR → C1. `cli.gh_read` appears in no
  item, correctly: `architecture.md` restates it as unchanged, and this run
  does not teach a generic transport seam about one payload's field semantics.
- **Every `defect.md` success criterion has a home.** `gd:` string + nonzero
  exit, never a traceback → A2 (the rule), A3 (measured through `main`). Both
  call sites, independently → A3, one case per path per refused class. §1's
  repro a passing test plus the §3 open-stay history → A2, with the offset-naive
  class as a third. The §6 asymmetry removed **or** recorded as intentional →
  **removed**, pinned at B1 and recorded as the decision's consequence at C1.
  Payload twins + manifest + detector E → A1, A2, verified at C2. Full battery
  green → every item, closed at C2. `one_owner.py` gains no new problems → C2,
  against the nine on `main`.
- **The exact bytes of the problem string are Implement's to settle, once.**
  `architecture.md` renders it line-wrapped inside markdown prose; the emitted
  string is a single line, and neither input supplies it as a quotation. A2 is
  the item that fixes those bytes and its suite pins them; A3, B1 and B2 assert
  the same shape through their own labels and **must not re-word it**. An
  exact-string test that needs editing after the item that wrote it is the
  signal to revert, not to edit the test.
- **What this breakdown deliberately does not contain.** No item makes the
  gate-digest workflow's commit step `if: always() && …` — `architecture.md`
  puts it out of scope under *What this design deliberately does not do* and
  parks the draft backlog seed there, and note that
  `.github/workflows/gate-digest.yml` is itself a `factory_init.MIRRORS` entry,
  so that change would ship to every stamped repo and wants its own evidence.
  No item appends anything to `docs/backlog.md`: this run's one sanctioned
  backlog write was its own seed claim, already made by Capture. No item folds
  the three `_timelines` fetchers (ADR-0056 left them un-folded for a reason
  that still holds). No item canonicalises admitted timestamps, so
  `completed_stays`' string ordering keeps its existing dependence on GitHub's
  single `…Z` spelling — flagged by `architecture.md` as pre-existing. No item
  touches `cli.gh_read`, `cli.CLI_FAILURES`, `cost_ledger.py:189`'s
  already-guarded parse, `gates.py` detector J, or any detector, workflow or
  Makefile target. No item mints a work-order id or opens, edits or closes a
  tracker issue.
- **How this run dies, restated as a check on these rows.** A2 is split to
  make it smaller and the tree spends a commit either discarding the miner's
  problems or carrying a parameter nothing reads — the two shapes
  `architecture.md` rules out by name. Or a guard is added at `_age_seconds`
  or inside `waited_seconds` "while we are in there", which puts two owners on
  one rule and rebuilds the asymmetry in a new place. Or C1's three edits land
  in the wrong order and the amended-by status line names a record that does
  not exist yet, turning detector C red on the very artifact that proposes it.
  Or a criterion is met for the garbage string only and the offset-naive class
  walks past it, which is the exact failure `architecture.md` measured to
  reject the small fix.

## 2026-09-21 — superseded on its own headline criterion, re-entering blocked

Attempting Implement against current main (`8e074d0`, moved on from this run's
`622e7c0` baseline) found that PR #326 (`fix(gates): a timeline timestamp that
is not one is not a well-formed flip`, commit `9324d31`, merged 2026-09-19 —
one day after this breakdown was written, from an independently-seeded run
`docs/fixes/gate-timeline-timestamp-trust/`) already shipped a fix for the
crash this run exists to close, discovered before any Implement commit landed.

**What #326 did, verified empirically against `defect.md`'s own §1 and §3
repros on current main — neither raises any more:**
`human_gates.label_events` now refuses an event whose `created_at` fails a
new `_is_timestamp(value)` predicate (parses AND carries a UTC offset) and
silently drops it; `gate_digest.run_daily` on the §1 history returns
`{'changed': 'false', 'reason': 'gd: 0 item(s) waiting, 0 new gate-latency
row(s)'}` with `problems: []` — no exception. The §3 open-stay history
renders in `_queues` as `Item(number=106, ..., waited=None, aged=True)`,
again no exception.

**Why this breakdown can no longer be implemented as written, not just
"already partly done":** A1's Accept clause requires `_parse_ts` itself
become the total reader and states explicitly "No separate `is_timestamp()`
predicate is added — one rule, one spelling, which is what `one_owner.py`
exists to find." #326 shipped exactly that separate predicate, named
`_is_timestamp`, reviewed and tested. Implementing A1 as specified now means
reverting or restructuring already-merged, already-reviewed code on a stale
design snapshot — a redesign decision, not an implementation step, and not
this run's to make unilaterally.

**The residual gap, real and not yet closed by #326:** #326's own commit
message says it chose the drop "rather than adding a problems channel" —
confirmed above: the malformed event vanishes with no `gd:`/`dashboard:`
problem string and no nonzero exit anywhere in the chain, which is narrower
than `defect.md`'s stated success criterion ("produces a `gd:`-prefixed
problem string and a nonzero exit — never a traceback") and arguably in
tension with the repo-wide problem-string contract (CLAUDE.md; ADR-0051).
Milestone B's asymmetry question (does `rejection_mining` silently diverge
from `gate_digest`?) is also still open, though now framed against #326's
drop rule rather than against a raise.

**Not decided here, on purpose:** whether the residual gap is worth closing
at all (it is a silent-drop, not a crash, and this repo's honesty rule
means a `problems` channel must not be bolted on as a rushed addition to
someone else's just-reviewed code without its own pass), and if so whether
it is a small additive follow-up on top of #326's `_is_timestamp` (a
`problems` return threaded through the same three call sites, `dashboard`
included) or something else. That call belongs to Architect or to the
operator, not to a fork mid-Implement. This run stops here, uncommitted
beyond landing the pre-existing Capture/Architect/Decompose artifacts.
