---
stage: architect
run: feature:first-live-dispatch
date: 2026-08-17
ux: skipped — operator's surface is the existing tracker, labels, and PRs — nothing new is built for humans to look at
---

# Architecture: first live dispatch

## Approach

Zero new factory code. The factory's dispatch, validation, spend, and
breaker planes shipped in v1 and were review-hardened in Milestone E;
this run's design is the *exercise* of those planes in an order that
keeps every piece of evidence honest, plus the one tiny code change
that rides as payload (executed by the dispatched agent, not by us).
The only repo edits this run makes with human hands are: the run's own
artifacts, the payload's breakdown row, and a paired, reverted cap
change for the breaker test. Everything else is labels, consoles, and
watching the machinery.

The sequencing is forced by the honesty rule, not preference: with
$0.00 recorded this month, no positive cap can breach, and fabricating
a ledger row is forbidden (eval-honesty, CLAUDE.md). So the breaker's
deliberate firing must come AFTER the paid dispatch, spending that
run's real rows. Arming, however, comes first: both secrets exist
before the first paid token, so first contact happens with the breaker
live at the real $300 cap and the mechanical stops (60-minute
timeout, --max-turns 100) plus the size-S $5 band bounding the blast.

## Components (phases over shipped planes)

1. **Arming** — owner, consoles only. `ANTHROPIC_API_KEY`: Anthropic
   console key → Actions secret. `FACTORY_PAUSE_TOKEN`: fine-grained
   PAT scoped to this repo alone with Variables read/write (the
   Actions-variables API is what GITHUB_TOKEN cannot reach —
   cost-report.yml's header records why). Contract: `gh secret list`
   shows both names; values never touch repo, shell history, or chat.
   Failure mode: a mis-scoped PAT surfaces only when the pause step
   first runs — which is exactly why the breaker test exists.
2. **Payload authoring** — owner session. One breakdown row in this
   run's `breakdown.md` (Decompose writes it; the WO id continues the
   repo-global sequence), citing PRD-0003; mirror issue created only
   after the row exists (ADR-0032, one-way), labeled `type:chore` +
   size S. Routing is settled by shipped policy: `type:chore` →
   SWE charter → `implementation` band → `claude-sonnet-5`
   (assembler.CHARTER_BY_TYPE, factory.json routing) — first contact
   runs on the mid model, not haiku, without any override.
3. **Gate walk** — owner. `wo:draft → wo:prd-approved →
   wo:blueprint-approved → wo:ready-for-agent`, each applied by Matt
   after actually reading what the gate approves (the supervision IS
   the gate; the label straddle stays out of scope per PRD). The
   ready label from the owner is the dispatch trigger.
4. **Dispatch** — automation, watched. assembler.yml: job gate
   (owner sender + not paused) → resolve (row + Accept + orientation
   pack) → claim → agent → `wo-record` + spend-row commit → find-pr →
   validator hand-off. Failure mode: any red flips the order to
   `wo:failed` (claim-gated); retry is an owner re-label; the
   `budget-exhausted` label blocks self-retry (ADR-0034).
5. **Gate 3** — automation + owner. The dispatched validator run
   executes check + review + needs-review-label on the agent's PR;
   Matt reviews and merges manually (v1 policy); the merged-label job
   flips `wo:merged`; detector G holds the merge to its ledger row.
6. **Breaker firing** — owner + automation, after the merge. PR pair:
   (a) lower `monthly_cap_usd` to `0.01` in
   `factory/templates/factory.json` + `factory_init.py
   update-manifest` in the same commit (the config is under detector
   E's checksum pin); merge; `workflow_dispatch` cost-report → real
   rows ≥ $0.01 → PAUSE verdict → the workflow itself sets
   `FACTORY_PAUSED=true` through `FACTORY_PAUSE_TOKEN`. Inertness
   evidence: an owner-applied ready label while paused yields an
   assembler run concluding `skipped`. Then (b) revert the cap PR and
   Matt clears the variable by hand — the clear is deliberately
   human (ADR-0034: no self-retry past a stop).
7. **Evidence capture** — owner session. Each PRD criterion's check is
   a query with quotable output (run conclusions, label timelines,
   ledger rows, `gh secret list` names); Verify fences them per
   detector H's bar.

## Data model

No new shapes. State touched: `factory/templates/factory.json`
(cap, changed and reverted, manifest regenerated both times);
`docs/factory/costs.jsonl` (machine-written rows only — the run's
whole point); this run's artifacts; the payload's one-line fix in
`gates.py` (docstring line ~46, the `"J": (None, None, "unused")`
DETECTORS entry, and the line-1103 comment brought to agreement with
the implemented detector J at line 815 — content authored by the
dispatched agent against the row's Accept criterion); Actions
secrets/variables (out-of-repo state, owner-managed).

## Interfaces exercised (contracts, not new code)

- assembler job gate: label name + sender==owner + `FACTORY_PAUSED !=
  'true'` → run or skip (skip is evidence in phase 6).
- claim transition: `transitioned == 'true'` gates spend recording and
  the failure flip — a run that never claimed changes nothing.
- action execution file → `make wo-record` → ledger row → spend-commit
  push to main; loss shows red and detector G backstops at merge.
- find-pr: `Closes #N` join (knowledge_plane grammar), no-match exits
  nonzero → `wo:failed`.
- validator `workflow_dispatch`: PR number in → synthesized payload →
  check/review/label jobs; verdicts land as comment + label (the
  PR-head check-status gap is a recorded review minor, out of scope).
- cost-report: ledger + cap in → PAUSE/CONTINUE + report issue out;
  PAUSE mutation requires `FACTORY_PAUSE_TOKEN` (fails loudly absent).

## Stack

Unchanged: stdlib Python, GitHub Actions, `gh`. No new dependencies,
no new tools, no template payload changes beyond the cap PR pair.

## Decisions with real alternatives (why they lost)

- Breaker staging via temporary cap PR pair — a test flag in
  cost_report.py lost (new production code whose only caller is test
  theater); waiting for a real $300 breach lost (months away at
  first-dispatch spend; PRD requires the firing this run).
- Dispatch before breaker-firing — firing first lost (no honest breach
  exists at $0.00 spend, and PAUSE would block the dispatch this run
  exists to perform).
- `type:chore` routing as-is (sonnet-5) — forcing the mechanical band
  (haiku) for cheapness lost (first contact optimizes for a clean
  traversal, not cents; the routing table's own policy already says
  chores are SWE work).
- No ADR — the cap dance is fully reversible and recorded here plus in
  the release log; it fails the hard-to-reverse test, so a one-line
  record suffices (the architect skill's own bar).

## Traceability (PRD-0003 criterion → component)

Secrets → 1; gate history → 3; assembler success + traceable PR → 4;
validator hand-off + needs-review flip → 4/5; manual merge +
`wo:merged` + detector G → 5; real spend row → 4; breaker fires +
inert ready label → 6; ≤ $10 total → 4+6 (band $5 + free CI runs +
retry headroom); J-fix correct → 2/4 (Accept criterion) with the
battery as the check.
