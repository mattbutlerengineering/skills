---
stage: decompose
run: maintenance:a-timestamp-the-digest-cannot-parse
date: 2026-09-22
assumptions:
  - "Traceability was re-derived, not copied. architecture.md's Traceability table and 'Measured against the tree' section are accepted as this breakdown's basis only after independently re-running the load-bearing checks in this stage, at the same HEAD (`47b6937`): both PR merge commits (`b6b365c`, `9324d31`) confirmed ancestors of HEAD via `git merge-base --is-ancestor`; the three named regression tests (see 'What Verify owes') run individually and quoted; `tests.test_human_gates`, `tests.test_gate_digest`, `tests.test_dashboard`, `tests.test_rejection_mining` run together (193 tests, OK); the three payload twins re-diffed clean against root; `docs/adr/0056-human-gates-module.md`'s `- Status:` line re-read as `accepted`; `rejection_mining.py`'s import line re-read as `from human_gates import gate_rejections, label_events` (no `refused_timestamps`). No claim below rests on architecture.md's prose alone."
  - "No live review of the cut — this run is autorun-driven (autorun-brief.md), so there was no operator present to confirm milestone boundaries or item sizing. There is exactly one item, so the boundary question mostly does not arise; the sizing (XS) and the item's own acceptance criterion are this stage's judgment call, logged here rather than confirmed live, matching this run's own 2026-09-15 breakdown.md precedent for the same situation."
  - "One checkbox, not zero, and not several. Pipeline-protocol.md's Implement row states explicitly that 'a breakdown with no checkboxes is not yet implemented' — a zero-checkbox breakdown would make orientation-by-file-existence stall on Implement forever, vacuous-truth notwithstanding. A single non-code closure item is included for exactly this reason: it gives Implement one real, checkable, non-fabricated action (re-confirm the tree hasn't drifted since this Decompose stage, immediately before handing to Verify) rather than either inventing busywork code or leaving the breakdown uncheckable. See Notes for the full reasoning, including why this is not the same failure mode as manufacturing a fake work item."
  - "The deferred rejection_mining forwarding decision and the narrower reporting-only asymmetry are restated, not reopened. Both are architecture.md's decisions (backed by an independent, already-reviewed run's own release.md), not open questions this stage is deciding or re-deciding. They are carried into this breakdown's Notes purely so a reader of breakdown.md alone — without also opening architecture.md — does not mistake their absence from the checkbox list for an oversight."
  - "No tracker interaction and no ADR, unchanged from defect.md and architecture.md. No item mints a WO-#### id, opens/edits/closes a tracker issue, or carries a (tracker: #N) reference; no item creates or amends an ADR file. architecture.md's own 'ADRs' section already gives the reasoning (nothing here clears canon.md's bar); this stage adds nothing to it."
---

# Breakdown: a timestamp the digest cannot parse — nothing to implement, one closure item

Progress lives in the checkbox below. Source is `architecture.md` in this
directory (2026-09-22), whose Traceability section this stage independently
re-verified rather than took on faith — see `assumptions` above and
"Independent verification" below.

**The headline fact this breakdown exists to record.** Every gap `defect.md`
was opened to close is already closed, on `main`, by two independently-seeded
runs: PR #326 (`9324d31`, merged 2026-09-20) and PR #499 (`b6b365c`, merged
2026-09-21). Both are confirmed ancestors of this stage's HEAD (`47b6937`).
There is no design left to implement and no code, test, template, manifest,
or ADR file for this run to add, edit, or remove. This is not "mostly done" —
it is done, and this stage's job is to say so in a shape the pipeline's own
orientation rules can act on, not to manufacture work to fill a milestone
table.

## Independent verification (this stage, 2026-09-22, HEAD `47b6937`)

Re-run rather than quoted from architecture.md:

```
$ git merge-base --is-ancestor b6b365c HEAD && echo "b6b365c is ancestor of HEAD"
b6b365c is ancestor of HEAD
$ git merge-base --is-ancestor 9324d31 HEAD && echo "9324d31 is ancestor of HEAD"
9324d31 is ancestor of HEAD

$ python3 -m unittest tests.test_gate_digest.TestRunDaily.test_a_malformed_closing_timestamp_is_refused_not_swallowed tests.test_gate_digest.TestRunDaily.test_a_malformed_labeled_timestamp_is_refused_not_swallowed tests.test_dashboard.TestQueues.test_a_malformed_timestamp_is_refused_not_swallowed -v
test_a_malformed_closing_timestamp_is_refused_not_swallowed ... ok
test_a_malformed_labeled_timestamp_is_refused_not_swallowed ... ok
test_a_malformed_timestamp_is_refused_not_swallowed ... ok
Ran 3 tests in 0.004s
OK

$ python3 -m unittest tests.test_human_gates tests.test_gate_digest tests.test_dashboard tests.test_rejection_mining
Ran 193 tests in 0.129s
OK

$ for f in human_gates.py gate_digest.py rejection_mining.py; do
    diff "$f" "factory/templates/tools/factory/$f" && echo "$f identical"
  done
human_gates.py identical
gate_digest.py identical
rejection_mining.py identical

$ grep -n "dashboard.py" factory_init.py
(no output — dashboard.py is not a MIRRORS entry, confirming it has no twin)

$ grep -n "^- Status:" docs/adr/0056-human-gates-module.md
3:- Status: accepted

$ grep -n "^from human_gates" rejection_mining.py
42:from human_gates import gate_rejections, label_events
```

`rejection_mining.py` imports only `gate_rejections, label_events` — no
`refused_timestamps` — confirming architecture.md's claim that the
reporting-only asymmetry (question 3, narrower branch) is still exactly as
`a-malformed-timestamp-is-silently-dropped/release.md` deliberately left it,
not something this run's tree has since drifted on either direction.

## Milestone A: closure recorded, nothing built

Demonstrable at the close: Implement re-confirms, at whatever HEAD it
actually runs against, that the tree still matches what this breakdown
describes, and hands off to Verify with zero diff.

- [x] **A1** Re-confirm closure immediately before handing off to Verify — size:XS, blocked by: —
  - Accept: immediately before Verify begins, re-run the four checks below
    against Implement's own HEAD (which may have moved past `47b6937` if time
    has passed) and confirm each still holds:
    1. `git merge-base --is-ancestor b6b365c HEAD` and
       `git merge-base --is-ancestor 9324d31 HEAD` both succeed — #326 and
       #499 are still ancestors.
    2. `python3 -m unittest tests.test_human_gates tests.test_gate_digest tests.test_dashboard tests.test_rejection_mining`
       still reports `OK` (193 tests at this breakdown's HEAD; the count may
       change with an unrelated commit, the result must still read `OK`).
    3. The three payload twins (`human_gates.py`, `gate_digest.py`,
       `rejection_mining.py` against `factory/templates/tools/factory/`)
       still `diff` clean, and `grep -n "dashboard.py" factory_init.py`
       still returns nothing.
    4. `docs/adr/0056-human-gates-module.md`'s `- Status:` line still reads
       `accepted`.

    If all four hold, this item is checked with **no source, test, template,
    manifest, or ADR file added, edited, or removed** — `git status` must
    show no diff this item introduced — and Implement hands off directly to
    Verify with breakdown.md's single checkbox ticked (satisfying
    pipeline-protocol.md's Implement-completion rule).

    If **any** of the four fails — a revert, a force-push, an amended
    ADR-0056, a twin that has drifted from root — that is a new fact this
    architecture.md did not have. This item is **not** checked. Per the
    decompose skill's own rule ("If decomposition exposes a design gap...
    don't design around it here — record the gap and route back to
    Architect"), the same rule applies at Implement: the run stops and routes
    back to Architect rather than either silently writing code to cover the
    drift or silently checking the box anyway.
  - Blocked by: —

## What Verify owes

Verify is **not skippable** for a maintenance run (pipeline-protocol.md).
Per architecture.md's own logged assumption, its job here is to assemble
already-gathered evidence into `verification.md`, not to author new tests —
the pre-existing suite already pins `defect.md`'s exact shapes and already
cites `defect.md` and issue #491 by name in its own docstrings. Concretely,
`verification.md` should, against whatever HEAD it runs at:

1. State plainly, in its own words, that this run's Implement stage added no
   code, and why (point at this file and at `architecture.md`) — so a future
   reader of `verification.md` alone does not wonder whether evidence is
   missing.
2. Walk `defect.md`'s Success criteria one at a time (there is no `prd.md` —
   maintenance runs skip it, so `defect.md`'s own Success criteria section is
   the thing being verified) and for each, re-run and quote real output:
   - **Criterion 1** (`gd:`-prefixed problem string + nonzero exit, never a
     traceback) and **Criterion 2** (both call sites independently) — re-run
     `defect.md` §1's and §3's repro histories through the real
     `gate_digest.run_daily` / `gate_digest.main`, quoting `main -> exit 1`
     and the `gd: timeline for #<n> refused 1 malformed timestamp(s)` line
     for both.
   - **Criterion 3** (§1 repro as a passing test, plus a second for the §3
     open-stay history) — run and quote:
     `tests.test_gate_digest.TestRunDaily.test_a_malformed_closing_timestamp_is_refused_not_swallowed`
     and
     `tests.test_gate_digest.TestRunDaily.test_a_malformed_labeled_timestamp_is_refused_not_swallowed`
     (both confirmed passing by this stage, 2026-09-22); also
     `tests.test_dashboard.TestQueues.test_a_malformed_timestamp_is_refused_not_swallowed`
     covers the same open-stay shape for the dashboard's own reporting path.
     Then the full four-module run:
     `python3 -m unittest tests.test_human_gates tests.test_gate_digest tests.test_dashboard tests.test_rejection_mining`.
   - **Criterion 4** (§6 asymmetry removed, or recorded as intentional) — cite
     that `rejection_mining.run_mine` still returns `problems: []` on the §6
     timeline (the crash-shaped asymmetry §6 evidenced is fully removed, not
     merely documented — neither path raises any more). Separately, cite
     `docs/fixes/a-malformed-timestamp-is-silently-dropped/release.md`'s
     follow-up item 1 as the existing record of the **narrower**,
     reporting-only asymmetry (rejection_mining never calls
     `refused_timestamps`) — do not re-decide or re-record this in
     `verification.md`; cite it and move on, per architecture.md's Decisions
     & alternatives.
   - **Criterion 5** (payload twins + manifest match root, detector E green)
     — re-diff the three twins, and run
     `python3 gates.py && python3 gates.py --selftest`, quoting
     `gates: 0 problem(s)` and `selftest: ok`.
   - **Criterion 6** (full battery green) — run and quote
     `python3 -m unittest discover tests`, `python3 lint.py` (matching
     `lint: 0 problem(s)`), and `python3 gates.py && python3 gates.py --selftest`.
   - **Criterion 7** (`one_owner.py` gains no new problems) — run
     `python3 one_owner.py`, compare the printed count against this stage's
     baseline (7, confirmed by architecture.md on 2026-09-22 — down from 9 at
     this run's own 2026-09-15 capture), and confirm neither finding involves
     `human_gates.py`, `gate_digest.py`, `dashboard.py`, or
     `rejection_mining.py`'s timestamp handling.
3. Not re-litigate the rejection_mining forwarding deferral or the dashboard
   reporting-asymmetry (see Criterion 4 above and Notes below) — both are
   already-made, already-reviewed decisions by other runs; `verification.md`
   cites them, it does not reopen them.

## Design gaps found

**None.** This stage checked architecture.md's Traceability table against
the live tree rather than assuming it (see "Independent verification" above)
and found no criterion left unmet, no caller left unforwarded within this
run's scope, and no shipped shape that diverges from what architecture.md
describes. The two open items architecture.md itself names —
`rejection_mining.py`'s unforwarded reporting path and
`dashboard._age_seconds`'s already-closed third exposure — are not gaps in
architecture.md's design; they are its explicit, reasoned scope boundaries
(the first deferred by an independent run's own considered decision, the
second closed incidentally by #326's admission-gate shape and confirmed
unreachable). Neither needs a work item; see Notes.

## Notes

- **Why one checkbox and not zero.** Pipeline-protocol.md's orientation table
  states, for both the generic and the maintenance-run cases, that Implement
  is complete "when every checkbox in `breakdown.md` is checked (a breakdown
  with no checkboxes is not yet implemented)." Read literally against a
  breakdown with zero rows, "every checkbox is checked" is vacuously true —
  but the protocol's own parenthetical exists specifically to block that
  reading: it says a checkbox-empty breakdown is *not yet implemented*,
  full stop, regardless of the vacuous truth. Leaving this breakdown with no
  checkboxes would therefore either strand the run at Implement forever (if
  orientation takes the parenthetical literally) or let it silently satisfy
  a rule the protocol authors clearly wrote to prevent exactly this shape
  from slipping through. Both outcomes are wrong for a run that has real,
  verified closure to report. A single item resolves this: it is genuinely
  checkable (four concrete commands, quoted before-and-after), it is not
  fabricated busywork (it is the one thing between "verified once, at
  Decompose time" and "still true when Implement actually runs," which is
  exactly the kind of staleness that killed this run's original 2026-09-15
  breakdown), and checking it is what makes orientation-by-file-existence
  correctly read this run as ready for Verify.
- **Why not more than one checkbox.** There is no second slice to cut: no
  component changes (architecture.md's own Components section, restated
  "for the record"), no interface changes, no data model changes, no new
  test to author (the existing suite already covers every success
  criterion, confirmed independently by this stage), and no ADR to write
  (architecture.md's ADRs section: "no decision here meets the bar"). Adding
  a second item would mean inventing one, which the decompose skill's own
  rule against manufactured work ("Do the backend" is not an item," by
  extension "confirm it again" is not two items) argues against.
- **The rejection_mining forwarding deferral is carried, not decided, here.**
  `rejection_mining.py` imports only `gate_rejections, label_events` — no
  `refused_timestamps` call (confirmed by this stage's own grep, not just
  architecture.md's) — exactly as
  `a-malformed-timestamp-is-silently-dropped/release.md`'s follow-up item 1
  left it. `defect.md`'s own Scope section put `rejection_mining` behavior
  out of scope for this run from the start. This breakdown adds no item for
  it and takes no position on whether it should ever be forwarded; that
  question belongs to whoever next touches `rejection_mining.py`'s callers,
  citing that run's own follow-up note, not this one.
- **The narrower reporting-asymmetry question (autorun-brief.md's question 3)
  is answered, not reopened.** The *crash*-shaped asymmetry `defect.md` §6
  evidenced is fully removed (neither `gate_passages` nor `gate_rejections`
  raises any more, on any refused-timestamp history). A *narrower*,
  reporting-only asymmetry survives by design and is recorded in
  `a-malformed-timestamp-is-silently-dropped/release.md`, not in an ADR,
  because architecture.md judged it does not clear canon.md's ADR bar
  (reversible in one line, unsurprising, no real trade-off while it has
  never fired in production). This breakdown does not restate that judgment
  as a new decision and does not add a work item to revisit it.
- **`dashboard._age_seconds` needed no follow-up item.** `defect.md`'s own
  Notes section drafted (but deliberately did not append) a backlog seed for
  this third exposure, conditioned on "whether this is fixed at all depends
  on where this run puts its catch." The catch landed at admission
  (`label_events`/`_is_timestamp`, #326), which closes this exposure
  incidentally: `_age_seconds` is never reached with a string `label_events`
  refused, confirmed by `tests/test_dashboard.py`'s own passing coverage.
  The draft seed is therefore moot and stays undrafted; no item revives it.
- **This breakdown's own artifact-depth precedent.** Sized against
  `docs/fixes/gate-timeline-timestamp-trust/breakdown.md` (two small items,
  full evidence quoted, Notes used for anything discovered after the fact)
  rather than against this run's own superseded 2026-09-15 breakdown.md
  (seven items across three milestones) — the earlier document was sized for
  a design that turned out not to ship; sizing this one to match it would
  reintroduce exactly the mismatch between plan and tree that closed the
  2026-09-15 attempt.
