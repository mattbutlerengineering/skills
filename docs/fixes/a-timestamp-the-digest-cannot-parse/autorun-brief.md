---
run: maintenance:a-timestamp-the-digest-cannot-parse
date: 2026-09-22
---

# Autorun brief: a-timestamp-the-digest-cannot-parse

This run entered autorun already past Capture (`defect.md`), Architect
(`architecture.md`) and Decompose (`breakdown.md`) — all written 2026-09-15,
`re-entry: architect`. All idea/PRD-shaped interview questions are moot: this
is a maintenance run and those artifacts already carry everything a fresh
interview would ask.

## Why this run is being re-dispatched to Architect

`breakdown.md`'s closing section (dated 2026-09-21) records that a prior
Implement attempt found PR #326 (`fix(gates): a timeline timestamp that is
not one is not a well-formed flip`, merged 2026-09-20, commit `9324d31`,
from an independently-seeded run `docs/fixes/gate-timeline-timestamp-trust/`)
already shipped a fix for the crash this run exists to close — verified
still true against current `main` (`47b6937`, 2026-09-22): `human_gates.py`
now has `_is_timestamp(value)` and `label_events` silently drops an event
whose timestamp fails it.

This is not a minor overlap. `architecture.md`'s own Decisions & alternatives
section explicitly considered and **rejected** exactly this shape — a
separate `is_timestamp()` predicate ("two spellings of one rule ... which
`one_owner.py` exists to find") and silent dropping ("refuse silently, like
`cli.label_names`" — rejected because "a dropped label flip silently
rewrites the gate history the digest reports as fact"). PR #326 shipped both
things this architecture.md argued against. `architecture.md` and
`breakdown.md` as written can no longer be implemented without unilaterally
reverting or restructuring already-reviewed, merged code — which
`breakdown.md` itself says is "not this run's to make unilaterally."

**Task for this Architect dispatch:** read `defect.md`, the existing
(now-stale) `architecture.md`, and `breakdown.md`'s 2026-09-21 closing note
in full, then read PR #326's actual diff and current `human_gates.py`,
`gate_digest.py`, `dashboard.py`, `rejection_mining.py` on `main`. Decide,
with a real recommendation:

1. **Is the residual gap worth closing at all?** `defect.md`'s first
   success criterion ("`gd:`-prefixed problem string and nonzero exit,
   never a traceback") is met by #326 (no traceback). What #326 does *not*
   do is report the refusal via the problem-string contract — a malformed
   timestamp is now silently dropped rather than announced. That is
   narrower than `defect.md` asked for and in tension with the repo's
   problem-string convention (CLAUDE.md; ADR-0051), but it is not a crash.
2. **If worth closing, what shape?** A small additive follow-up threading a
   `problems` return through `_is_timestamp`'s existing call sites (#326's
   design, extended) is the obvious candidate — evaluate it on its own
   merits rather than reintroducing the old architecture.md's rejected
   `_parse_ts`-becomes-total rewrite over already-reviewed code.
3. **The Milestone B asymmetry question** (does `rejection_mining` diverge
   from `gate_digest` under #326's drop rule?) is still open per
   `breakdown.md` and needs answering either way.
4. **ADR-0056 status:** the old `architecture.md` proposed amending it via a
   new ADR-0062. Re-evaluate whether that's still the right vehicle given
   #326 already shipped without one — #326 may itself need addressing in
   the ADR, or the amendment may turn out unnecessary if the gap is judged
   not worth closing.

Write a fresh `architecture.md` (this stage's artifact is not an ADR and is
not subject to the repo's never-rewrite rule — supersede the file's content
outright) that reaches and states a real decision, not a menu. If the
conclusion is "close nothing further, #326 is sufficient as shipped," say so
explicitly with reasoning, and record why the original run's stricter
success criterion is being relaxed (that is itself a decision worth one line
in Decisions & alternatives, not a silent drop).

## Answers already settled in defect.md — do not re-ask

- **Release authorization: prepare-and-stop.** No externally visible release
  action (no deploy, publish, tag, merge) at Ship, regardless of what later
  stages find. Ship runs pre-flight checks and writes `release.md` recording
  readiness and exact steps only.
- **No tracker interaction.** No issue created, edited, or closed. No
  `intake:` recorded. This run was seeded from `docs/backlog.md`, not a
  tracker issue.
- **User-facing surface: none.** CLI/tooling only — maintenance runs skip
  PRD, so no `ux:` decision arises.
- **Stdlib only; problem-string contract; ADR-0056 amend-or-supersede, never
  rewrite** (for the ADR file itself, if one is still offered) — all per
  CLAUDE.md and already stated in `defect.md`'s Constraints.
- **Scope:** `defect.md`'s In scope / Out of scope stand as the outer
  bound; this dispatch may narrow what's actually implemented within it
  (per the questions above) but should not widen beyond `human_gates.py`,
  `gate_digest.py`, `dashboard.py`, `rejection_mining.py`, their payload
  twins, `factory/manifest.json`, and relevant tests.

## After Architect

Once `architecture.md` is rewritten, **Decompose must also be re-run**
before Implement — `breakdown.md` as it stands is the stale, superseded
plan and documents itself as such. Orientation-by-file-existence would
otherwise skip Decompose since `breakdown.md` exists; that would be wrong
here and the orchestrator is handling that explicitly rather than
mechanically.
