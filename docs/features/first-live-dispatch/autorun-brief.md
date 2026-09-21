# Autorun brief: first-live-dispatch

Collected 2026-08-31 by the operator through `/idea-to-prod:autorun`.
This is not a run artifact: it carries no frontmatter, never counts
toward orientation or active-run discovery, and is the source of
interview answers for every stage of this run.

## Why this brief exists at Implement, not at Idea

This run was seeded 2026-08-17 and already holds `idea.md`, `prd.md`
(PRD-0003, `ux: not-applicable`), `architecture.md` and `breakdown.md`.
Autorun was invoked against it at **Implement**, so the interview-only
early stages need nothing from this brief — their artifacts exist. What
the brief records instead is the authorization envelope for the stages
that remain, and the blocking analysis below.

Run discovery found **two** active runs (`docs/features/first-live-dispatch/`
and `docs/fixes/isdigit-is-not-an-int-guard/`), so the protocol's
"list the candidates and ask" rule applied rather than the single-active
shortcut. The operator selected this one.

## Scale and location

Feature run, slug `first-live-dispatch`, artifacts at
`docs/features/first-live-dispatch/`. Orientation at collection time:
Idea, PRD, Architect and Decompose complete; **Implement** is the first
incomplete stage — 1 of 9 work orders checked (WO-0044), 8 open.

## Authorization collected

- **Release authorization: prepare-and-stop.** This run may execute no
  externally visible release action — no deploy, publish, tag, or merge.
  Ship writes `release.md` recording readiness and the exact steps, and
  stops. This matches the repo's own gate 3 (ADR-0033) being the owner's.
- **Tracker: no tracker interaction.** No existing issue seeds this run.
  Note this is narrower than the run's own content: WO-0038's acceptance
  is *authoring* a mirror issue, which is a tracker write the run itself
  specifies. That is the run's work, not intake seeding, and it remains
  blocked for the reason below.
- **User-facing surface:** already decided at PRD time — `ux:
  not-applicable`, reason recorded in `prd.md` and echoed in
  `architecture.md`.

## Why autorun stopped without dispatching a stage

**Every open work order is blocked on operator-only action, and the two
roots are credentials autorun must never handle.**

Milestone A's two open rows are the roots of the whole chain:

- **WO-0036** — mint `CLAUDE_CODE_OAUTH_TOKEN`. Its acceptance says the
  token "comes from `claude setup-token` run in the operator's own
  terminal (Max-subscription OAuth — the plan issues no API key) and
  **never touches the repo, shell history, or chat**."
- **WO-0037** — mint `FACTORY_PAUSE_TOKEN`, a fine-grained PAT scoped to
  this repo, Variables read/write only.

Verified at collection time — neither exists:

```
$ gh secret list
(no output)

$ gh variable list
(no output)
```

Every other open row is transitively blocked on those two, and three of
them are additionally owner-only by their own acceptance text:

| Row | Blocked by | Also owner-only because |
|---|---|---|
| WO-0038 author the mirror issue | 0036, 0037 | — |
| WO-0039 the dispatched payload | 0038 | "Delivered by the dispatched agent as a PR closing the mirror issue — **never by hand**" |
| WO-0040 gate walk and supervised dispatch | 0038, 0044 | "**Matt applies** `wo:prd-approved`, `wo:blueprint-approved`, then `wo:ready-for-agent` … each after reading what the gate approves" |
| WO-0041 gate 3: review, merge, close out | 0040 | "**Matt reviews and merges** the agent's PR manually" |
| WO-0042 fire the breaker | 0041 | "Matt clears the flag by hand" |
| WO-0043 evidence bundle and spend rollup | 0042 | — |

This is the skill's stop-and-surface condition on three counts at once:
credentials, real spend, and external commitments. Dispatching a
subagent at WO-0036 could only either fail or improvise around an
acceptance criterion written specifically to keep the credential out of
this channel — so no stage was dispatched.

It is also, separately, incompatible with the authorization collected
above: WO-0041's acceptance *is* a merge, and this brief authorizes
prepare-and-stop.

## State worth knowing at resume

- **WO-0039's payload is still intact.** Its subject is the detector-J
  roster agreement — the roster docstring, the `DETECTORS["J"]` entry and
  the unclaimed-letters comment all agreeing J is claimed. On `main`
  today all three still say unclaimed:

```
gates.py:1110    "J": (None, None, "unused"),
gates.py:46      network calls stay out of this offline gate — and J/K are unclaimed.
gates.py:1097    # J and K are unclaimed — the shared ai-tooling letter namespace assigns
```

  Open PR #377 (`agent/a-broken-taxonomy-passes-the-gate`) changes
  detector J's *behavior* but leaves the roster entry untouched
  (`"J": (None, None, "unused")` on both sides), so it does **not**
  consume this payload. The dispatched agent still has real work to do.

- **WO-0044 is the one checked row** — the assembler's either-credential
  change, executed in an owner session because the dispatch plane cannot
  dispatch the fix that makes it dispatch-capable.

- **The honesty constraint on WO-0042 still stands** (breakdown note,
  2026-08-17): under subscription auth the execution file's cost figure
  is notional and may read `$0.00`, in which case the 0.01-cap breach
  cannot fire honestly and that criterion routes back to arbitration
  rather than around the eval-honesty rule.

## Assumptions logged

None. No stage artifact was produced, so no stage-level assumption was
taken. The two interpretive calls made here are recorded rather than
assumed: that a brief collected at Implement need not re-answer the
interview-only early stages (their artifacts exist), and that WO-0038's
issue authoring is run content rather than tracker intake seeding.

## What unblocks this run

The operator, in their own terminal, mints both credentials and sets them
as Actions secrets — then WO-0036 and WO-0037 are checked with
`gh secret list` output quoted as evidence, and WO-0038 becomes the first
dispatchable row.

## Re-verified 2026-09-12 — still blocked, nothing dispatched

Autorun resumed against this run (selected by the operator from two active
candidates). Every state claim above was re-checked rather than inherited:

```
$ gh secret list
(no output)
$ gh variable list
(no output)
$ grep -n '"J": (\|J/K are unclaimed\|J and K are unclaimed' gates.py
46:network calls stay out of this offline gate — and J/K are unclaimed.
1097:# J and K are unclaimed — the shared ai-tooling letter namespace assigns
1110:    "J": (None, None, "unused"),
$ gh pr view 377 --json state,mergedAt
OPEN, merged=no
```

Breakdown: 1 of 9 checked (WO-0044). The two roots (WO-0036, WO-0037) are
unmet, so the stop-and-surface analysis above applies unchanged and no
stage was dispatched. The unblocking step is the same: the operator mints
both credentials in their own terminal and sets them as Actions secrets.

## Resumed 2026-09-15 — Milestone A closed, mirror issue authorized and authored

The operator answered the orchestrator's ask with "create the mirror
issue" — authorization for exactly one tracker write, no commit. Recorded
here because the original brief said "no tracker interaction" and carved
this row out as the run's own work; this is the explicit yes for it.
Issue #430 mirrors the payload row (WO-0039, PRD-0003 §Success criteria).
Stop line: the gate walk (WO-0040, PRD-0003 §Success criteria) onward is
the operator's — applying `wo:ready-for-agent` fires a real, paid
dispatch, and the branch's `(tracker: #430)` ref must reach main first.
