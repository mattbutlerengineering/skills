---
stage: review
run: feature:software-factory
date: 2026-08-14
---

# Review: software-factory

## Scope

The run's span: 003f263 (PRD-0001 merge, 2026-07-05) through 5719599 —
107 commits, 57 of them factory/work-order commits across 29 merged PRs.
Every WO was PR-reviewed at merge time, so this run-level review does
not re-read every diff line; it examined the system as built in three
passes (correctness, design conformance, security), each finding
re-verified against the code before being recorded here. Files read:
the dispatch plane (assembler.py/.yml, validator.yml), the money plane
(budget_guard.py, handoff.py, cost_ledger.py, cost_report.py/.yml), the
observation plane (gate_digest.py/.yml, rejection_mining.py, sweeps),
the seams (cli.py, knowledge_plane.py, factory_config.py), gates.py,
factory_init.py and the template payload, against their test files and
architecture.md's contracts.

## Findings

### Critical: agent-opened PRs never trigger validator.yml — gate 3 is silent for exactly the PRs the factory produces

- Scenario: assembler.yml:106 hands the dispatched agent
  `github_token: ${{ secrets.GITHUB_TOKEN }}`; GitHub suppresses
  `push`/`pull_request` workflow events created with that token, so a
  factory-opened PR gets no `check` run, no reviewer job, no
  `wo:needs-review` flip — either permanently unmergeable (if the check
  is required) or mergeable ungated. The repo demonstrably knows the
  property — gate-digest.yml:12 relies on it so its ledger commit
  "cannot recurse into CI" — but no ADR, setup.md, or comment records
  the consequence for the dispatch path.
- Decision: fix before Ship — routes to Implement. Non-trivial: needs
  either a separately-scoped token (PAT/App) for the agent's PR
  creation, or a validator reconciliation trigger. Owner input needed
  (a new secret only the owner can mint).

### Major: the success-path ledger row is appended to the ephemeral runner and never committed

- Scenario: assembler.yml's "Record the run's spend" step runs
  `make wo-record`, appending to docs/factory/costs.jsonl in the
  runner's checkout — and no later step commits or pushes it (contrast
  gate-digest.yml's explicit commit step). Every dispatched run's spend
  row is discarded with the runner; the monthly circuit breaker never
  sees dispatched spend, surviving the very #222 fix that step exists
  to implement. The step's comment names detector G as backstop, but G
  reads repo content — a row that never lands is exactly what it can't
  see until the merge gate, and `continue-on-error: true` keeps the
  step green-ish meanwhile.
- Decision: fix proposed (add a commit step mirroring gate-digest.yml's)
  — operator arbitration pending.

### Major: hard_stop pushes WIP before appending the ledger row, so the exhaustion record never persists

- Scenario: budget_guard.py:155-158 — `push_wip` (add/commit/push)
  runs first, then `cost_ledger.append` writes to the now-already-pushed
  working tree; nothing commits afterward. Even a fully successful hard
  stop leaves ADR-0034's accountability row on the runner disk.
  tests/test_budget_guard.py asserts only local file existence.
- Decision: fix proposed (append before push_wip, plus a persistence
  assertion in the test) — operator arbitration pending.

### Major: fail-closed PAUSE verdicts never set FACTORY_PAUSED

- Scenario: cost_report.py's fail-closed paths (malformed ledger line,
  unresolvable cap) emit `pause=true` to $GITHUB_OUTPUT *and* exit 1;
  the "Recompute spend" step has no `continue-on-error`, so the job
  fails there and "Pause dispatch on a cap breach" (implicit
  `success()`) is skipped. On exactly the paths the module's docstring
  says "can never silently wave spend through unpaused," dispatch stays
  unpaused.
- Decision: fix proposed (`continue-on-error` on the report step, or
  `always() &&` on the pause step's condition) — operator arbitration
  pending.

### Major: ADR-0034's three uncorrelated stops are not wired into the dispatch path

- Scenario: the agent step passes only `--model` (no `--max-turns`),
  the job declares no `timeout-minutes`, and no hook calls
  `budget_guard.py check` — `check` and `hard_stop` have zero runtime
  callers (only the post-hoc `record-run` is wired, Makefile:54). The
  budget stop as built is SWE-charter prose — the self-policing
  ADR-0034's mechanical stops were designed to not rely on. No ADR or
  breakdown Note records the deferral; verification.md §3 attributed
  the gap to "no live dispatch," which understated it.
- Decision: fix proposed in two parts — `--max-turns` +
  `timeout-minutes` now (two lines); the 80%/100% budget hook routed
  to Implement as its own item — operator arbitration pending.

### Major: stamped-repo dispatch is structurally impossible and undisclosed

- Scenario: the payload ships assembler.yml + assembler.py but no
  `factory/agents/` stubs and no `factory/charters/` tree
  (factory/templates/factory/ does not exist), so every stamped-repo
  dispatch fails closed at `charter_band` (assembler.py:144). The
  charters' exclusion predates the workflows entering the payload;
  docs/setup.md's "Deliberately not in scope" list never mentions the
  composition gap.
- Decision: fix proposed (disclose in setup.md now; shipping charter
  stubs in the payload is a scope decision) — operator arbitration
  pending.

### Minor: gates.py's detector roster contradicts itself on J

- Scenario: detector J is implemented and runs in CHECKERS, but
  gates.py:46 still says "J/K are unclaimed" and DETECTORS maps
  `"J": (None, None, "unused")` — the docstring architecture.md names
  as the authority is self-contradictory (PR #215 claimed J without
  updating either spot).
- Decision: deferred — doc-only drift, no behavior at stake; cheap to
  fold into the next gates.py touch.

### Minor: the WIP-cap guard the architecture claims does not exist in the dispatch path

- Scenario: nothing in assembler.py/.yml reads `wip_cap`; concurrency
  groups per-issue, so N ready labels dispatch N parallel paid runs.
  ADR-0037 documents the knob's dormancy, but architecture.md:251's
  guard claim and WO-0005's checked accept line ("WIP-cap guards hold")
  were never amended.
- Decision: deferred — the owner is the only labeler, so the cap is
  currently advisory; needs an architecture.md amendment note rather
  than code.

### Minor: PR-review excerpts flow unsanitized and unfenced into the pinned toolsmith queue

- Scenario: any GitHub user's "request changes" review on a factory PR
  reaches `_excerpt` (rejection_mining.py:92) — no control-char strip,
  no fence, no length cap — and lands verbatim in the repo-owned pinned
  issue, outside the ADR-0032 quoting discipline sweeps.py already
  implements (sanitize + QUOTE_HEADER + fenced block). Bounded
  markdown-injection today; latent prompt text if a toolsmith consumer
  ever automates.
- Decision: deferred — mirror sweeps.py's sanitize/fence pattern in the
  next rejection_mining touch; no automated consumer exists yet.

### Minor: mirrored-issue titles flow unsanitized into the digest the improvement routine reads

- Scenario: compose_digest embeds issue titles raw; the ADR-0044 cloud
  routine reads the pinned digest as context. Requires collaborator
  access plus an owner-reviewed breakdown row, so near the
  "owner-attacks-self" floor.
- Decision: deferred — same sanitize pattern, same next touch.

### Minor: line_problems accepts NaN/Infinity cost — a permanent poison row

- Scenario: `budget_guard.py record WO-X r-1 m 4200 nan` — the cost
  rule checks only `< 0` (NaN comparisons are False); the row appends,
  and the append-only ledger then makes every monthly rollup print
  "$nan" and PAUSE forever. read_execution requires isfinite; the
  hand-typed leg doesn't.
- Decision: deferred — add `math.isfinite` to line_problems in the next
  cost_ledger touch; owner-only entry point today.

### Minor: any gate_digest problem discards the day's appended latency rows

- Scenario: run_daily appends rows (`changed=true`) but one failed
  timeline fetch makes main exit 1; the commit step (implicit
  `success()`) is skipped, discarding the rows. The 1000-entry LIST
  window makes a permanent version of this inevitable as history grows.
- Decision: deferred — same fix shape as the cost-report major
  (`always() &&` gating); lower stakes since rows regenerate next
  passage.

### Minor: duplicate (tracker: #N) rows dispatch ambiguously

- Scenario: two breakdown rows carrying the same tracker number (a
  breakdown copied as template) — resolve_row dispatches the first
  match as prompt substrate while the digest attributes to the last;
  no detector checks tracker uniqueness.
- Decision: deferred — candidate new gates.py detector; no duplicate
  exists in the repo today.

### Minor: write_outputs' predictable heredoc delimiter

- Scenario: the assembler prompt embeds CONTEXT.md and ADRs wholesale;
  a content line exactly `__PROMPT_EOF__` terminates the $GITHUB_OUTPUT
  heredoc early and remaining lines parse as new outputs. GitHub's
  toolkit randomizes delimiters for exactly this.
- Decision: deferred — randomize the delimiter in the next cli.py
  touch; no repo file contains the sentinel today.

### Minor: duplicate Closes refs double-count change-requests in the toolsmith queue

- Scenario: a PR body with "Closes #7 … Fixes #7" mines each
  CHANGES_REQUESTED review once per ref, inflating the recurrence count
  that ranks the toolsmith queue.
- Decision: deferred — dedup `orders` in the next rejection_mining
  touch (same touch as the excerpt fence).

## Passes with no findings

No pass came back empty, but the load-bearing surfaces held: all 16
template mirrors are byte-identical to their root counterparts; seam
discipline is uniform (no typed-ID regexes outside knowledge_plane, no
subprocess outside cli, no factory.json reads outside factory_config,
no ledger-shape knowledge outside cost_ledger); the problem-string
contract holds through cli.report; the dispatch prompt boundary is
sound (breakdown row + repo files only — the issue body/title never
reach the prompt); the owner gate is enforced twice and fails closed;
write-scoped and secret-bearing jobs exclude fork PRs; every gh/git
call uses argv lists; secrets are never echoed; and the stop/pause
decision logic itself (>= boundaries, month windows, passage/rejection
partition, dedup keys) is correct and pinned — every defect found
lives in persistence ordering, workflow step gating, or unpinned input
edges, not in the rules.

## Verdict

Not ready to ship. One critical (factory PRs bypass their own gate 3)
plus five majors — three of which share one theme: the machinery
records its verdicts on ephemeral runner disks or skips its own
enforcement step on the fail-closed path. The critical routes to
Implement per the fix loop. The majors await operator arbitration:
the proposed split is (a) fix now as new breakdown rows alongside the
critical — the ledger-commit step, the hard_stop ordering, the pause
gating, the two-line mechanical stops; (b) decide separately whether
the budget hook and payload charters are v1 scope or deferred with an
ADR note. Minors are deferred with reasons above. This dovetails with
verification.md's routing recommendation: the supervised end-to-end
dispatch it proposes would have surfaced the critical and both
persistence majors on first contact.
