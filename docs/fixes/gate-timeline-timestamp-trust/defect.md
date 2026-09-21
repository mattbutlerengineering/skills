---
stage: capture
run: maintenance:gate-timeline-timestamp-trust
date: 2026-08-23
re-entry: architect
assumptions: ["re-entry is architect, not implement: the fix changes which function owns rejecting a malformed timestamp, and human_gates.py is the ADR-0056 seam for what a gate is — a contract change there is a decision to record", "Severity is judged on the contract, not on GitHub's behaviour: the honest trigger analysis is in Blast radius, and the run does not claim GitHub emits bad timestamps"]
---

# Defect: a gate timeline's timestamp is trusted by one function and validated by neither

Origin: backlog seed `docs/backlog.md:26`
(from: maintenance:deepening-tool-seams), claimed as
`(claimed: maintenance:gate-timeline-timestamp-trust)`.

## Defect

`human_gates.label_events` (human_gates.py:65) admits a timeline event
when its label name and `created_at` are **truthy**:

```python
        if name and ts:
            events.append((ts, kind, name))
```

Its docstring says "Anything that is not a well-formed label flip is not
this module's business". A non-ISO `created_at` is not well-formed, and it
is admitted anyway.

`human_gates.waited_seconds` (human_gates.py:60) then assumes ISO-8601,
because `_parse_ts` calls `datetime.fromisoformat`. So the two functions
disagree about what a timestamp is: one accepts any truthy string, the
other requires a parseable one, and nothing between them reconciles it.

Expected: a malformed timeline yields a problem string, or is rejected at
the boundary that claims to reject malformed flips. Observed: `ValueError`
escapes as a traceback.

## Reproduction / Evidence

Driven against the tree at `622e7c0`, through the public functions only —
a completed `prd` gate stay (`wo:draft` labeled, `wo:prd-approved`
confirming it, `wo:draft` unlabeled) whose closing timestamp is not ISO:

```
completed_stays: [('2026-08-01T00:00:00Z', 'yesterday', True)]
gate_passages raised ValueError: Invalid isoformat string: 'yesterday'
```

An earlier, incomplete attempt is worth recording because it shows the
guard is narrow rather than absent: the same malformed timestamp on an
*unclosed* stay returns cleanly, because the value never reaches
`waited_seconds`.

```
label_events admitted: [('2026-08-01T00:00:00Z', 'labeled', 'wo:draft'), ('yesterday', 'labeled', 'wo:prd-approved')]
gate_passages -> []
```

Only a **completed, confirmed** stay reaches the parse. That is the exact
shape the seed named.

Nothing on the path catches it:

```
=== every try/except in gate_digest.py:
164:        try:
166:        except GH_FAILURES as err:
170:        try:
172:        except GH_FAILURES:
175:    try:
178:    except GH_FAILURES as err:
181:    try:
183:    except GH_FAILURES as err:

=== and in human_gates.py:
  NONE
```

`gate_digest.run_daily` catches `GH_FAILURES` only, and it is what the
scheduled workflow runs (`Makefile:66`, `python3 gate_digest.py daily`,
invoked by `.github/workflows/gate-digest.yml`).

Two call sites reach `waited_seconds` from timeline data:
`human_gates.py:122` (inside `gate_passages`) and `gate_digest.py:149`.

## Root-cause hypothesis

**Hypothesis, not a finding.** `label_events` was written to be
permissive on purpose — its docstring pushes unusable timelines to "the
fetcher's problem" — and that reading is right for the *fetch* failure
modes it was thinking of (a 404, an empty body, a rate limit), which the
`gh_read` seam does own. It does not cover a well-formed HTTP response
carrying a badly-shaped field, which is a different failure and lands
past the fetcher. The truthiness guard reads as complete and is not.

## Blast radius

Honest version: **the contract is broken; the live trigger is not
GitHub.**

- **Who:** the scheduled `gate-digest` job, and any caller of
  `gate_passages` or `gate_rejections`.
- **How badly:** a traceback instead of a problem string — the failure
  mode this repo's tools are written to avoid, and one that gives an
  operator a stack trace instead of a labelled line.
- **How likely:** GitHub's API emits ISO-8601 `created_at` values, so a
  real dispatch is not expected to trip this. The reachable sources of a
  malformed timestamp are a hand-authored or recorded payload, a fixture,
  and a second-harness adapter (ADR-0027/ADR-0031 keep a non-GitHub path
  live in this repo's future). This run does **not** claim GitHub
  misbehaves.
- **Since:** the behaviour was relocated into `human_gates.py` by the
  ADR-0056 fold and predates it in `gate_digest.py`; it was never
  introduced by a change, which is why no test covers it.

That likelihood is why the run exists at all rather than being a
one-line patch: whether to validate here is a judgment, and the judgment
belongs in `architecture.md`.

## Ruled out

- **Not `_parse_ts`'s `Z` shim.** `datetime.fromisoformat` gained
  `Z` support in 3.11 and the shim covers older locals; it is correct and
  is not the defect.
- **Not the fetch path.** `gh_read` and `GH_FAILURES` already convert
  transport and CLI failures into problem strings. This value arrives
  inside a *successful* response.
- **Not `dashboard.py`'s duration helper.** `dashboard.py:139` explicitly
  records that it is a different calculation from
  `human_gates.waited_seconds`; the deepening run that produced this seed
  already separated them.
- **Not a one-owner duplicate.** The one-owner pre-pass does not group
  these functions, and this is a missing check rather than a fact stated
  twice.

## Work items

None here. `re-entry: architect`, so the `architecture.md` +
`breakdown.md` chain owns them.

## Notes

The competing fixes are named in the architecture, not decided here.
Capture's job was to establish that the crash is real, reachable through
public functions, and unguarded on the scheduled path — all three are
evidenced above.
