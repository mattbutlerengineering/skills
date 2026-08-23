# One cross-plane drift rule; the caller declares what absence means

- Status: provisional
- Date: 2026-08-22

## Context

ADR-0032 makes the breakdown row authoritative and the tracker issue its
one-way mirror. Drift is the two planes disagreeing, and one question
answers it: given the rows and the live issue listing, where do they
contradict each other?

The rule was written inside the first tool that needed it. `sweeps.py`
held `reconcile_drift` (sweeps.py:215-284) with `issue_lifecycle`
(199-209) and `_describe` (211-212) — already pure, already taking the
listing as data, already documenting that it names drift by breakdown
path and issue number rather than by WO id (sweeps.py:48).

The dashboard then needed the same question answered and wrote it a
second time. `dashboard._drift` (dashboard.py:194-215) took
`{number: state}` and covered two of the rule's eight classes.

**The copies disagree, and not only in wording.** Take a checked row
whose mirror is closed but never got `wo:merged`:

- `sweeps.py reconcile` files an intake — *"a checked row mirrors #7,
  which carries no wo: label — the row says merged"*.
- `dashboard._drift` renders nothing at all. Its two branches are
  checked+OPEN and unchecked+CLOSED; checked+CLOSED falls through.

Also silent on the dashboard: an issue carrying two lifecycle labels at
once, an issue mirrored by two rows, a labelled issue no row mirrors,
and the `wo:merged`-aware readings of the two classes it does catch.
One repo, two planes, two answers about whether they agree.

That is multiple real callers AND observed divergence between the
copies: CLAUDE.md's two-part bar, met.

One difference is **not** divergence, and it is why the copies were
never simply merged. Whether a row whose mirror is *absent from the
listing* is drift depends on the listing, and each caller is right about
its own:

- `sweeps.live_issues` aborts — *"A truncated window ABORTS here rather
  than warning… past the window an issue is simply absent, and absence
  is exactly what two of the drift checks read as a finding. A windowed
  reconcile would file a report full of invented drift."*
- `dashboard._listing` reports truncation and renders on, so `_drift`
  declines to guess — *"a mirror outside the listing says nothing — only
  definite disagreement is a finding."*

Merging the copies without naming that difference would either invent
drift on the dashboard or hide it in the sweep.

## Decision

**`plane_drift.py` owns the cross-plane drift rule.** A new root module
holding `reconcile_drift`, `issue_lifecycle` and `_describe`, moved out
of `sweeps.py` unchanged apart from the two points below.

- **`reconcile_drift(rows, issues, absent_is_drift=True)`.** The
  argument is the caller's claim about its own listing: True only if a
  missing issue means gone rather than unread. It gates exactly one
  branch — the membership check. Every other class compares a row
  against an issue the listing actually produced, which is a definite
  fact whatever a window hid, so the conservative caller keeps all of
  them. `sweeps.reconcile` passes the default and earns it by aborting;
  `dashboard.gather` passes False and says why at the call site.
- **The default is the strict reading.** A caller that cannot vouch for
  its listing has to say so out loud; silence should not buy silence.
- **Its problem strings are `drift:`-prefixed, not `sweeps:`.** A seam
  labels itself (ADR-0037's convention) — otherwise the dashboard would
  print another tool's name for its own bad input. One string changes.
- **Root-only. It does not join `factory_init.MIRRORS`.** Neither caller
  ships in the payload — `tools/factory/` contains no `sweeps.py` and no
  `dashboard.py` — so a mirrored copy would be an unread file in every
  stamped repo. This is the first shared root module that is not
  mirrored, and it sets the rule the earlier ones only happened to
  satisfy: a module is mirrored iff a payload tool imports it, not
  because it is shared.
- **The name is `plane_drift`.** ADR-0032 spends "plane" on exactly the
  two authorities this module compares, so the noun is earned here in a
  way it was not for `human_gates` (ADR-0056).

What deliberately did NOT move — this decision is bounded by its
evidence, not by what sits nearby:

- **`sweeps.reconcile_intake`.** It turns drift lines into one intake
  plan: sweep title, sweep labels, sweep triage. One caller, no copy.
- **`sweeps.live_issues` and `dashboard._listing`.** Network reads with
  an owner at the cli seam (ADR-0051), and the difference between them
  is precisely the policy `absent_is_drift` now names — collapsing them
  would delete the reason the parameter exists.
- **`dashboard._queues` and `_output`.** They read the same listing but
  ask about gates and PRs, not about whether the planes agree.
- **`row_work_order`.** It stays in `knowledge_plane`, unused here: the
  rule identifies a row by where it lives, which is where a human goes
  to fix it.

## Consequences

- `dashboard.py` loses `_drift` and gains the six classes it never
  checked, free. The two it already had become label-aware.
- Two output changes, both deliberate: the dashboard's drift lines are
  now path-first and name the lifecycle labels (`docs/…/breakdown.md: an
  unchecked row mirrors #7, which is closed carrying wo:draft — the row
  says the work is outstanding`) instead of `drift: <work order> row is
  unchecked but its mirror #7 is closed`; and the malformed-entry
  problem reads `drift:` rather than `sweeps:` at both callers.
- The absence policy gets its first test, which no copy could have had:
  the same rows and the same empty listing under both settings, plus a
  third case pinning that the policy gates the membership check alone.
- `TestReconcileDrift` moves from `tests/test_sweeps.py` to
  `tests/test_plane_drift.py`; `tests/test_dashboard.py`'s `TestDrift`
  shrinks to what `gather` owns — the right rows, the right policy.
- No payload churn. `MIRRORS`, `factory/manifest.json`, the tool count
  in docs/setup.md and `EXPECTED_RELS` in tests/test_factory_init.py are
  all untouched, and detector E has nothing to say about this change.
- A third tool that wants to know whether the planes agree imports one
  module instead of writing a third partial answer — which is how the
  divergence this ADR closes was created in the first place.
