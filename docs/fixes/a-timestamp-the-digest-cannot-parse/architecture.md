---
stage: architect
run: maintenance:a-timestamp-the-digest-cannot-parse
date: 2026-09-22
assumptions:
  - "prd.md absent by protocol, not by omission — unchanged from the 2026-09-15 architecture: this is a maintenance run with re-entry: architect, whose predecessor is defect.md (pipeline-protocol.md, Maintenance-run orientation)."
  - "No ux: echo — unchanged from the 2026-09-15 architecture, for the same reason: no PRD, no ux: decision, nothing to echo. defect.md's Constraints already state \"User-facing surface: none.\""
  - "Extra sections beyond TEMPLATE.md: Measured against the tree, What this design deliberately does not do, and Traceability, following the same precedent the superseded 2026-09-15 architecture.md cited (docs/fixes/one-fact-one-owner/architecture.md, this run's own stated artifact-depth precedent). The design-question section is renamed to match what autorun-brief.md actually asks (four numbered questions, not one open design fork) rather than reused verbatim. Template section set and order otherwise unchanged, nothing dropped."
  - "This run's still-owed Verify stage (never skippable per protocol) may cite the pre-existing regression tests in tests/test_human_gates.py, tests/test_gate_digest.py and tests/test_dashboard.py — several of which literally name \"#491, defect.md §1/§3 shape\" in their own docstrings — as the evidence for defect.md's success criteria, rather than this run authoring duplicate tests under its own commit. No protocol clause requires a maintenance run's regression evidence to be committed by that run's own Implement stage; it requires verification.md to demonstrate the criteria are met. Recorded as an assumption because neither defect.md nor breakdown.md anticipated an independently-seeded run landing the fix first, and Decompose needs this reading to avoid manufacturing intentionally-duplicate coverage."
---

# Architecture: a timestamp the digest cannot parse — closed upstream, nothing left to build

## Approach

**Recommendation: build nothing further. Close this run at Decompose with an
empty-of-code breakdown and let Verify document what already ships.** The
gap this run exists to close was closed twice over while this run sat
between Architect attempts — once for the crash (PR #326, merged
2026-09-20) and once for the residual silent-drop this dispatch was sent to
adjudicate (PR #499, merged 2026-09-21, one day before this brief's own
"current main" checkpoint). Both are now ancestors of `HEAD`
(`47b6937`), verified below with `git merge-base --is-ancestor`, not
assumed from prose.

The old (2026-09-15) `architecture.md` proposed a design that made
`label_events` return `(events, problems)` — a breaking signature change
across three production call sites and seventeen tests — plus an ADR
amending ADR-0056. That design is now moot for a stronger reason than "code
changed underneath it": a **smaller** shape, from an independently-seeded
run that never saw the old `architecture.md`, already shipped, was
reviewed, and closes the same gap without touching `label_events`'s
signature and without an ADR. Comparing the two shapes is the two-shapes
comparison canon.md asks for, except the comparison happened for real, in
production commits, rather than on paper:

| | Old (superseded) `architecture.md` | Shipped (#326 + #499) |
|---|---|---|
| `label_events` signature | Breaking: `(timeline, operation, label=None) -> (events, problems)` | Unchanged |
| Callers touched | 3 production + 17 tests, for the signature alone | 0 production callers of `label_events` itself; 2 callers (`gate_digest`, `dashboard`) gain one line each calling a *new*, separate function |
| `_parse_ts` | Made total (`datetime \| None`) | Unchanged; a new `_is_timestamp` sits beside it |
| Reporting mechanism | `label_events` grows a `problems` return | A new pure function, `refused_timestamps`, computed by the same private walk (`_admit`) that already backs `label_events`, so the two questions ("which events" / "how many refused") share one pass over the payload and cannot drift apart |
| ADR | Proposed (amends ADR-0056) | None — and #326's own architecture.md considered and declined one for the identical reason canon.md gives: one line to revert, unsurprising given `label_events`'s own docstring, not really a trade-off |
| `rejection_mining.py` | Gains a forwarding line (in scope) | Left untouched, by a considered, reviewed decision (`docs/fixes/a-malformed-timestamp-is-silently-dropped/{defect,review,release}.md`) |

The shipped shape wins on canon.md's own terms — reduced complexity, not
fewer parts: it hides the admission/refusal split behind one private walk,
adds one small pure function with no existing caller to disturb, and never
has to argue an accepted ADR into an `amended by` state for a decision that
doesn't clear the bar. Re-proposing the old design now would mean
unilaterally reverting reviewed, merged, tested code to install a *worse*
answer to the same question — which is not this stage's call to make and
not a good trade even if it were.

## The brief's four questions — answered

autorun-brief.md poses four numbered questions. Answered against the real
tree, in order:

**1. Is the residual gap worth closing at all?** It is already closed — by
someone else, before this dispatch was written. PR #499 (merged
2026-09-21T14:14:03Z, closing issue #491) added exactly the `problems`
reporting the brief describes as missing, to both callers the brief names
(`gate_digest.py`, `dashboard.py`). `git merge-base --is-ancestor` confirms
`b6b365c` (that PR's merge commit on this line of history) is an ancestor
of `HEAD` (`47b6937`, 2026-09-21T20:38:57-0700 = 2026-09-22T03:38:57Z,
*after* #499's merge). The brief's own "verified still true against
current main" paragraph describes `_is_timestamp` (from #326) but not
`refused_timestamps`/`_admit`/the `gd:`/`dashboard:` wiring (from #499) —
that description was already one PR out of date at the moment this brief
was written. See *Measured against the tree* for the repro run fresh
against `HEAD`.

**2. If worth closing, what shape?** Moot — but for the record, the
shipped shape *is* the brief's own suggested "obvious candidate": *"a
small additive follow-up threading a problems return through
`_is_timestamp`'s existing call sites."* That is a fair one-line summary
of what `_admit`/`refused_timestamps` actually does. The brief's warning
against "reintroducing the old architecture.md's rejected
`_parse_ts`-becomes-total rewrite" was heeded — by a different run, for
its own stated reasons, before this dispatch existed.

**3. The Milestone B asymmetry question.** The asymmetry `breakdown.md`'s
§6 evidence named — `gate_rejections` surviving a history that raised out
of `gate_passages` — is **fully removed**, not merely documented, and
removed as a side effect of #326's admission-gate design rather than by
any code this run or #499 wrote: neither path raises any more, because
both walk the same admitted list, so there is no longer a "which one
crashes" question to answer. Measured below.

A **narrower, different** asymmetry exists at the reporting layer, and is
real: `gate_digest` and `dashboard` now emit a `gd:`/`dashboard:` problem
string when `label_events` refuses an event; `rejection_mining` does not,
because it imports `label_events` but never `refused_timestamps`. This was
found, evaluated, and knowingly deferred by #499 itself
(`docs/fixes/a-malformed-timestamp-is-silently-dropped/release.md`,
*Follow-up recorded, not actioned*, item 1: *"Not costing it anything
observable today (it never reaches `waited_seconds`); the same
`refused_timestamps` call is one line to add there if a future caller of
`gate_rejections` starts to need it."*) This run's own `defect.md` scoped
`rejection_mining` behavior **out** from the start (its Scope section:
*"Out of scope. ... rejection_mining behavior..."*), so leaving it alone
is not a new relaxation introduced here — it is consistent with what this
run already said, and reopening an independently reviewed, shipped,
reasoned deferral without new evidence that it is actually costing anyone
anything is the drive-by hardening `defect.md`'s own Scope section
forbids. See *Decisions & alternatives* and *What this design deliberately
does not do*.

**4. ADR-0056 status.** No amendment. `docs/adr/0056-human-gates-module.md`
is unchanged (`- Status: accepted`, verified by reading the file, not
assumed). Neither #326 nor #499 touched it, each for a reason recorded in
its own architecture/review artifact and each still true here: the
admission-gate completion is a small, reversible, unsurprising change to a
docstring's own stated rule, not a new reading of ADR-0056's stay
partition. `ADR-0062` — the number the superseded architecture.md
proposed — is now taken by an unrelated ADR
(`docs/adr/0062-a-skill-that-states-repo-facts-runs-a-shipped-tool.md`,
confirmed by listing `docs/adr/`), which would have forced a renumber even
if an ADR were still wanted. It is not wanted: nothing below clears
canon.md's three-part bar (hard to reverse, surprising without context, a
real trade-off), so per canon.md's own instruction the one-line records in
*Decisions & alternatives* are the right amount of ceremony.

## Measured against the tree

Every block below is real output from this stage, run in this working
tree at `HEAD` `47b6937` on 2026-09-22.

**#499 is already shipped and is an ancestor of `HEAD`:**

```
$ git log --oneline -- human_gates.py
b6b365c fix(human-gates): a refused timeline timestamp gets a gd:/dashboard: problem string (#491) (#499)
9324d31 fix(gates): a timeline timestamp that is not one is not a well-formed flip (#326)
60f867f fix(factory): one owner each, four times — the deepening-tool-seams run (#302)

$ git merge-base --is-ancestor b6b365c HEAD && echo "b6b365c IS ancestor of HEAD"
b6b365c IS ancestor of HEAD
```

**`defect.md`'s own §1 and §3 repro histories, driven through the real
`gate_digest.main` and `rejection_mining.run_mine` against a real mirrored
issue number, exactly as `defect.md` §2 and this run's prior architecture
probed it:**

```
using real mirrored issue: 106 -> WO-0001

=== §1: completed-confirmed stay, malformed closing timestamp ===
gate_digest.run_daily -> {'changed': 'false', 'reason': 'gd: 0 item(s) waiting, 0 new gate-latency row(s)'}
  problems: ['gd: timeline for #106 refused 1 malformed timestamp(s)']
gate_digest.main -> exit 1
rejection_mining.run_mine -> outputs: {'reason': 'rm: 0 candidate WO(s), 0 correction(s) mined'}
  problems: []

=== §3: open stay, malformed labeled timestamp ===
gate_digest.run_daily -> {'changed': 'false', 'reason': 'gd: 0 item(s) waiting, 0 new gate-latency row(s)'}
  problems: ['gd: timeline for #106 refused 1 malformed timestamp(s)']
gate_digest.main -> exit 1
rejection_mining.run_mine -> outputs: {'reason': 'rm: 0 candidate WO(s), 0 correction(s) mined'}
  problems: []
```

No traceback on either shape, on either call site (`_capture_latency` →
`gate_passages` for §1, `_queues` → `waited_seconds` for §3) — the exact
two independently-reachable sites `defect.md` §3 names. `gate_digest.main`
exits 1 with a `gd:`-prefixed line on both, which is `defect.md`'s first
success criterion, literally. `rejection_mining` stays silent on both,
confirming the deferred asymmetry from question 3 is still exactly as
`release.md` described it — not a regression introduced since, not
accidentally worse.

**The pre-existing regression tests already pin these exact shapes, and
already cite this run's own defect.md sections in their docstrings:**

```
$ grep -n "def test_.*malformed\|def test_.*refused\|def test_.*naive" tests/test_human_gates.py
109:    def test_a_malformed_timestamp_does_not_reach_the_parse(self):
120:    def test_a_naive_timestamp_is_not_one_either(self):
152:    def test_a_malformed_timestamp_is_refused(self):
166:    def test_a_naive_timestamp_is_refused_by_the_same_second_clause(self):
173:    def test_a_nameless_flip_is_not_a_refused_timestamp(self):
179:    def test_a_non_flip_event_is_not_a_refused_timestamp(self):
184:    def test_the_refused_count_never_shows_up_in_label_events(self):

$ grep -n "def test_.*malformed" tests/test_gate_digest.py
422:    def test_a_malformed_closing_timestamp_is_refused_not_swallowed(self):
444:    def test_a_malformed_labeled_timestamp_is_refused_not_swallowed(self):
```

`tests/test_gate_digest.py:422`'s own docstring: *"#491, defect.md §1
shape: a completed, confirmed stay whose closing timestamp is not ISO no
longer crashes (#326) — but the refusal itself must still be a gd:
problem string, not silence."* `:444`'s: *"#491, defect.md §3 shape: an
OPEN stay whose only labeled event carries a malformed timestamp..."*
Both assert `problems == ["gd: timeline for #123 refused 1 malformed
timestamp(s)"]` against fixture timelines that are `defect.md`'s own §1
and §3 histories, byte for byte. `tests/test_dashboard.py:296`,
`test_a_malformed_timestamp_is_refused_not_swallowed`, does the same for
the `dashboard:`-prefixed path.

**The payload twins and manifest are in sync — no drift to reconcile:**

```
$ for f in human_gates.py gate_digest.py rejection_mining.py; do
    diff "$f" "factory/templates/tools/factory/$f" && echo "$f identical"
  done
human_gates.py identical
gate_digest.py identical
rejection_mining.py identical
```

`dashboard.py` is not a `factory_init.MIRRORS` entry (confirmed by `grep
-n "dashboard.py" factory_init.py` returning nothing), so it has no twin
and touches no checksum — unchanged from every prior architecture's
finding.

**The full battery, green, with `one_owner.py` at fewer problems than any
prior baseline in this run's history (9 on 2026-09-15, 7 now — both
pre-existing, neither introduced by this investigation):**

```
$ python3 -m unittest discover tests
Ran 1700 tests in 20.755s
OK
$ python3 lint.py
lint: 0 problem(s) across 25 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
$ python3 one_owner.py
one-owner: gate_digest.py:124 LIST_ARGS and rejection_mining.py:54 ISSUE_ARGS state the same value — one fact, one owner
one-owner: label_sync.py:90 plan, label_sync.py:136 sync and sweeps.py:289 ensure_labels read the same payload keys (color, description, name) — one fact, one owner
one-owner: 7 problem(s)
```

Neither `one_owner.py` finding involves `human_gates.py`, `gate_digest.py`
(beyond the pre-existing `LIST_ARGS`/`ISSUE_ARGS` pair, unrelated to
timestamps), `dashboard.py`, or `rejection_mining.py`'s timestamp handling.
This run introduces no code, so it cannot have added to this count; the
number is quoted to show the tree this run would close against is clean,
not to claim credit for it.

## Components

No component changes. Recorded here as the current, already-shipped shape
so Decompose and Verify have one place that states it without re-deriving
it from two other runs' artifacts:

### `human_gates._admit` — the one walk (already shipped, #499)

- Responsibility: read a raw timeline once and answer both "which events
  are admitted" and "how many were refused," so the two questions cannot
  drift apart. Private; not part of the module's public contract.
- Collaborators: `human_gates._is_timestamp`; its two public faces,
  `label_events` and `refused_timestamps`.

### `human_gates.label_events` — the admission gate (already shipped, #326)

- Responsibility: unchanged signature and behavior for every well-formed
  input — `[(timestamp, kind, name)]` from a raw timeline, admitting an
  event only when it is a label flip, carries a name, and carries a
  timestamp `_is_timestamp` accepts. Silent on refusal, by design (module
  stays pure, ADR-0056) — the count lives in `refused_timestamps`, not
  here.
- Collaborators: `_admit`; three production callers, none of which
  changed signature.

### `human_gates.refused_timestamps` — the refusal count (already shipped, #499)

- Responsibility: the count of well-formed-except-for-timestamp label
  flips in a raw timeline, for a caller that already carries a `problems`
  list and wants to say what it lost. No existing caller before #499;
  `gate_digest._timelines` and `dashboard._timeline` are its only callers
  today.
- Collaborators: `_admit`.
- **Deletion test:** if it vanished, `gate_digest` and `dashboard` revert
  to #326's shipped behavior exactly — the silent drop, with no
  traceback and no signal. It is a real component: its callers hold
  strictly less information without it.

### `gate_digest._timelines`, `dashboard._timeline` — callers, not components (already shipped, #499)

Each gained one conditional `problems.append` reading
`refused_timestamps(raw)` before narrowing to `label_events(raw)`. Named
here because they are the two sites `defect.md`'s scope names, not
because either grew a responsibility — they forward a count into a list
they already carried.

### `rejection_mining._timelines` — deliberately unchanged

Imports `gate_rejections, label_events` only (verified by `grep -n
"label_events\|refused_timestamps" rejection_mining.py`). No
`refused_timestamps` call. This is the one open item from question 3,
addressed under *What this design deliberately does not do*.

## Data model

Unchanged from every prior architecture on this defect: no storage, no
schema, no persistence. The event triple is still `(timestamp, kind,
name)`. The one invariant worth restating because it is now load-bearing
in shipped code rather than proposed code: **every timestamp in an
admitted event triple reads as an offset-aware datetime**, enforced once,
at `_admit`, and depended on without re-checking by `waited_seconds`,
`gate_passages`, `waiting_since`, and (transitively, because
`waiting_since`'s `None` case is the only value it ever receives)
`dashboard._age_seconds`.

## Interfaces & contracts

No interface changes proposed. Stated for the record, as the contract
this run's Verify stage measures against:

### `human_gates.refused_timestamps(timeline)` (already shipped)

- Input: a raw, decoded GitHub issue timeline (list of event dicts) —
  the same input `label_events` takes, unnarrowed.
- Output: an `int`, the count of events that are otherwise well-formed
  label flips (kind ∈ {labeled, unlabeled}, name present) but whose
  `created_at` fails `_is_timestamp`.
- Failure modes: none — total over any input `label_events` also accepts
  without raising.
- What a caller must know beyond the signature: this must be called on
  the **raw** timeline, before `label_events` narrows it, or the count is
  always zero. Both current callers (`gate_digest._timelines`,
  `dashboard._timeline`) get this right — verified by reading, not
  assumed.

### `gate_digest.main` / `rejection_mining.main` (unchanged, restated)

- `main` already ends in `report(<label>, problems)`, which prints each
  problem line and returns 1 when the list is non-empty. The nonzero exit
  `defect.md` asks for needed no new code once `problems` carried the new
  line — this is why #499 could close the gap in two call sites of three
  lines each rather than a redesign.

## Stack & dependencies

Unchanged. Stdlib only (`datetime`, already imported). No new module, no
new seam, no change to `factory_init.MIRRORS` beyond what #326 and #499
already committed and regenerated.

## Decisions & alternatives

- **Close this run against already-shipped code** over **re-implementing
  the old architecture.md's `(events, problems)` redesign** — the shipped
  shape is strictly smaller (no breaking signature, no ADR) and already
  reviewed and merged; re-deriving a larger, already-rejected-by-evidence
  design would mean reverting working code to install a worse answer.
- **Accept #499's `refused_timestamps`/`_admit` shape** over **this run
  proposing its own competing mechanism** — two independently-designed
  mechanisms solving the same problem in one module is exactly the
  second-owner shape `one_owner.py` exists to catch; there is nothing to
  gain by a second implementation of the same idea.
- **Leave `rejection_mining.py` unforwarded** over **extending the
  `refused_timestamps` call there now, to fully close the reporting
  asymmetry** — this was evaluated and declined by an independent,
  reviewed run one day before this dispatch
  (`a-malformed-timestamp-is-silently-dropped/review.md` finding 4,
  `release.md` follow-up 1), for a reason that still holds:
  `rejection_mining` never calls `waited_seconds`, so a refused
  timestamp costs it nothing a human or the workflow can observe today,
  and this run's own `defect.md` scoped `rejection_mining` behavior out
  from the start. Reopening a considered, shipped decision without new
  evidence it is wrong is the drive-by hardening `defect.md` forbids.
  **This is the one place this run's original success criterion is
  read more narrowly than it was written**: `defect.md`'s fourth
  criterion asked for the §6 asymmetry to be "removed, or recorded as
  intentional in an ADR." The *crash* asymmetry §6 evidenced is removed,
  in full, with no ADR needed (the criterion's own disjunction is
  satisfied on its "removed" branch). A *narrower, reporting-only*
  asymmetry — not the one §6 measured, but adjacent to it and surfaced by
  this investigation — is left open, recorded in a run artifact
  (`release.md`) rather than promoted to an ADR, because it does not
  clear canon.md's ADR bar (reversible in one line, unsurprising given
  `rejection_mining`'s own "no duration arithmetic" shape, and not a real
  trade-off while it has never fired in production). Stated here as a
  decision rather than a silent narrowing, per this dispatch's
  instruction.
- **No ADR** over **ADR-0062 amending ADR-0056** — matches #326's own
  architecture.md's declined-ADR reasoning exactly (one line to revert,
  unsurprising given the module's own docstring, not a real trade-off),
  and the proposed number is taken by an unrelated ADR regardless.
- **This run's Verify stage cites pre-existing tests** over **authoring
  duplicate regression tests under this run's own commit** — the existing
  tests already pin `defect.md`'s exact §1/§3 shapes and already cite
  `defect.md` by name in their docstrings; writing a second, redundant set
  would be duplication for provenance's sake with no coverage gained.

## What this design deliberately does not do

- **It does not touch `rejection_mining.py`.** See *Decisions &
  alternatives*. The gap is real, narrow, already found and recorded by
  `a-malformed-timestamp-is-silently-dropped/release.md`, and not
  re-recorded a second time here to avoid two competing owners of the
  same deferred-item note. Anyone picking this up later should extend
  *that* run's follow-up, not open a third one.
- **It does not amend, supersede, or otherwise touch
  `docs/adr/0056-human-gates-module.md`.** Verified unchanged (`- Status:
  accepted`).
- **It does not touch `human_gates.py`, `gate_digest.py`, `dashboard.py`,
  or `rejection_mining.py` at all.** Every file `defect.md`'s Scope names
  as in-scope-for-editing already carries the fix; this run's remaining
  work is verification and closure, not code.
- **It does not canonicalize admitted timestamps.** Unchanged,
  pre-existing, flagged by the superseded architecture.md and still true:
  `completed_stays` orders by string comparison, correct for GitHub's
  single `…Z` spelling. Not this run's to change, and #499 didn't change
  it either.
- **It does not revert or restructure #326 or #499.** Both are merged,
  reviewed (per ADR-0036 clause 2, `#499`'s review notes it is
  self-authored and still wants a non-authoring reviewer — a pre-existing
  condition on that PR's own merge, not something this run inherits or
  can discharge).
- **It writes no ADR file and proposes none.** See *ADRs*.

## ADRs

**None — no decision here meets the bar.** The one decision with any real
weight — leaving `rejection_mining.py` unforwarded — is reversible in one
line, unsurprising (the module's own docstring already scopes the
delegation), and was already made and reviewed by an independent run one
day before this dispatch. Everything else in this artifact is a
verification of already-shipped, already-reviewed code, not a new design.
`ADR-0062`, proposed by the superseded 2026-09-15 architecture.md, is not
created; that number now belongs to an unrelated, already-merged ADR.

## Traceability

`defect.md` records no PRD (maintenance runs skip it), so the trace runs
against its Success criteria, read against the tree as it stands today.

| `defect.md` success criterion | Status | Evidence |
|---|---|---|
| Malformed timestamp → `gd:` problem string + nonzero exit, never a traceback | **Met** | `Measured against the tree`, §1 and §3 repros, both `main -> exit 1` |
| **Both** call sites covered — completed-stay and open-stay | **Met** | Same repro block, both paths |
| §1 repro a passing test, plus the §3 open-stay history as a second | **Met** | `tests/test_gate_digest.py:422,444`, both citing `defect.md` by section number in their own docstrings |
| §6 asymmetry removed **or** recorded as intentional in an ADR | **Met on its "removed" branch** for the crash-shaped asymmetry §6 evidenced; a narrower reporting-only asymmetry is left open and recorded in a run artifact rather than an ADR — see *Decisions & alternatives* | `rejection_mining.run_mine` never raises on either repro; `release.md` follow-up 1 |
| Payload twins + manifest match root, detector E green | **Met** | `diff` clean for all three mirrored files; `gates: 0 problem(s)` |
| Full battery green | **Met** | `Ran 1700 tests ... OK`; `lint: 0 problem(s)`; `gates: 0 problem(s)`; `selftest: ok` |
| `one_owner.py` gains no new problems | **Met, with margin** | 7 problems now vs. 9 at this run's 2026-09-15 baseline; neither new nor timestamp-related |

Next stage is Decompose, and autorun-brief.md already flags that
`breakdown.md` must be re-run rather than skipped by file-existence
orientation. What Decompose has left to sequence is not implementation —
there is none — but closure: recording that every work item the old
`breakdown.md` planned is either already done (by #326, #499) or
deliberately not this run's to do (`rejection_mining.py`, per *Decisions &
alternatives*), and routing this run to Verify, which is not skippable and
whose job is now to assemble the evidence already gathered here into
`verification.md` rather than to generate new evidence from scratch.
