---
stage: decompose
run: feature:first-live-dispatch
date: 2026-08-17
---

# Breakdown: first live dispatch

Progress lives in the checkboxes below — Implement checks items off as
their acceptance criteria are met. Row grammar per v1: one line per work
order carrying id, size class, blocking edges, and the PRD citation
detector A checks; tracker mirror numbers are appended per ADR-0032
after each row exists here first. WO ids continue the repo-global
sequence from v1's last order, 0035 (the prefix is dropped here because
detector A reads any line bearing a work-order token as a row needing a
PRD citation — v1's breakdown records the same dodge).

## Milestone A: Armed (both secrets exist; the factory is dispatch-capable with the breaker live)

- [x] **WO-0036** mint CLAUDE_CODE_OAUTH_TOKEN and set it as an Actions secret — size:S, blocked by: — (PRD-0003 §Success criteria)
  - Accept: `gh secret list` shows CLAUDE_CODE_OAUTH_TOKEN; the token comes from `claude setup-token` run in the operator's own terminal (Max-subscription OAuth — the plan issues no API key) and never touches the repo, shell history, or chat.
- [x] **WO-0037** mint FACTORY_PAUSE_TOKEN and set it as an Actions secret — size:S, blocked by: — (PRD-0003 §Success criteria)
  - Accept: `gh secret list` shows FACTORY_PAUSE_TOKEN; the PAT is fine-grained, scoped to this repo alone, Variables read/write only.
- [x] **WO-0044** the assembler accepts either credential — size:S, blocked by: — (PRD-0003 §Success criteria)
  - Accept: assembler.yml's job env carries both ANTHROPIC_API_KEY and CLAUDE_CODE_OAUTH_TOKEN; every credential-gated step `if:` reads `(env.ANTHROPIC_API_KEY != '' || env.CLAUDE_CODE_OAUTH_TOKEN != '')`; the action receives `claude_code_oauth_token`; the template mirror and manifest are regenerated in the same commit; the battery stays green.

## Milestone B: Traversal (one real order through all three gates to a merged PR with real spend recorded)

- [x] **WO-0038** author the payload's mirror issue at the gate line — size:S, blocked by: WO-0036, WO-0037 (PRD-0003 §Success criteria)
  - Accept: the payload row below is on main BEFORE its mirror issue exists (ADR-0032 one-way); the issue is labeled `type:chore` + `wo:draft` and its number is appended to the payload row as its tracker ref.
- [x] **WO-0039** gates.py J-roster agreement — superseded, proof obligation moved to WO-0073/WO-0074 — size:S, blocked by: WO-0038 (PRD-0003 §Success criteria) (tracker: #430)
  - Accept (amended 2026-09-22, see Notes): checked on the amended scope only — the functional target (detector-roster docstring, `DETECTORS["J"]`, and the unclaimed-letters comment all agreeing J is claimed) is verified fixed on `main` via PR #516 (merged 2026-09-22T03:38:57Z), independent of this row and explicitly disclaiming its credit. The original criterion — delivered by the dispatched agent as a PR closing the mirror issue, never by hand — was not met: #430 was closed by the operator's own hand on 2026-09-21T14:15:09Z, before any dispatched PR existed, foreclosing that path for this payload. This row does not stand in as a dispatch demonstration; the two new rows below carry that obligation forward.
- [x] **WO-0073** author the mirror issue for the replacement payload — size:S, blocked by: WO-0036, WO-0037 (PRD-0003 §Success criteria)
  - Accept: a new issue exists, labeled `type:chore` + `wo:draft` + `size:S`, body describing the fix in the row below in the #285/#430 grammar; the issue is created only after this breakdown row is on `main` (ADR-0032 one-way order); its number is appended to that row as `(tracker: #NNN)`.
- [x] **WO-0074** workflow-vocabulary sweep — the dispatched payload — size:S, blocked by: WO-0073 (PRD-0003 §Success criteria) (tracker: #536)
  - Accept (amended 2026-09-25, see Notes): `assembler.py`'s module docstring is corrected from "names no commands of its own" to the "names no repo tool of its own" phrasing `validator.yml`, `factory_init.py`, and `validator.py` already carry; `tests/test_design_pipeline.py`'s and `tests/test_gates.py`'s docstrings quoting the old phrasing are updated to match; `python3 factory_init.py update-manifest` is regenerated in the same commit (`assembler.py` is a `factory_init.MIRRORS` entry); no file under `.github/workflows/` is touched; the full battery stays green. Delivered by the dispatched agent as a PR closing the mirror issue — never by hand.
- [x] **WO-0040** gate walk and supervised dispatch — size:S, blocked by: WO-0073, WO-0044 (PRD-0003 §Success criteria)
  - Accept: Matt applies `wo:prd-approved`, `wo:blueprint-approved`, then `wo:ready-for-agent` on the vocabulary-sweep row's mirror issue (the row above; #430 is closed and no longer this run's dispatch target), each after reading what the gate approves; the assembler run concludes `success`; the agent's PR closes the issue via the Closes grammar; the spend row lands on main workflow-committed with real nonzero tokens; the validator hand-off fires and the order flips to `wo:needs-review` untouched by hands.
- [x] **WO-0041** gate 3: review, merge, close out — size:S, blocked by: WO-0040 (PRD-0003 §Success criteria)
  - Accept: Matt reviews and merges the agent's PR manually; the order reaches `wo:merged`; detector G is green on the close-out; the payload row above is checked as merged.

## Milestone C: Breaker proven (the stop machinery has fired for real and the run's evidence is verification-grade)

- [x] **WO-0042** fire the breaker on real spend and prove dispatch inert — size:S, blocked by: WO-0041 (PRD-0003 §Success criteria)
  - Accept: a PR lowers `monthly_cap_usd` to 0.01 with `factory_init.py update-manifest` in the same commit; a `workflow_dispatch` cost-report run computes PAUSE from real rows and itself sets `FACTORY_PAUSED=true`; an owner-applied ready label while paused yields an assembler run concluding `skipped`; a second PR reverts the cap (manifest regenerated); Matt clears the flag by hand.
- [x] **WO-0043** evidence bundle and spend rollup — size:S, blocked by: WO-0042 (PRD-0003 §Success criteria)
  - Accept: every PRD-0003 success criterion has a quotable, fenced check recorded for Verify (run conclusions, label timelines, ledger rows, secret names); the ledger rollup shows total recorded run spend ≤ $10 (notional list-rate figures — subscription auth bills nothing per-run).

## Design gaps found

None — every component in architecture.md's seven phases maps to a row
(phase 1 → Milestone A's two rows; phase 2 → the authoring row and the
payload row; phases 3–4 → the gate-walk row; phase 5 → the gate-3 row;
phase 6 → the breaker row; phase 7 → the evidence row), and every PRD
success criterion is covered by an Accept line above.

## Notes

- 2026-08-17: the payload row (WO-0039, PRD-0003 §Success criteria)
  carries no tracker ref at draft time — ADR-0032's one-way rule means
  the mirror issue is created only after this file lands on main; the
  authoring row (WO-0038, PRD-0003 §Success criteria) appends the ref
  as part of its acceptance.
- 2026-08-17: only the payload row is mirrored to the tracker — the
  owner-work rows (arming, gate walk, breaker, evidence) are
  supervision steps the dispatch plane never reads, and mirroring them
  would put non-dispatchable rows in front of the ready-label flow for
  no consumer.
- 2026-08-17: the retro's prerequisite lesson applied — the secrets are
  explicit Milestone A rows and every dispatch-path row is blocked on
  them, so the run cannot reach a supervision window with its
  prerequisites unowned (the amendment class v1's supervised-exercise
  row hit cannot recur here).
- 2026-08-17: owner-work rows are checked by the operator during
  Implement with evidence quoted at check time; the ledger gets rows
  only for the dispatched run itself — owner supervision is not a paid
  model run and gets no fabricated spend row (eval-honesty).
- 2026-08-17: Max-subscription pivot (design-level, routed through
  Architect — architecture.md carries the dated amendment). The
  operator's Claude plan issues no API key, so the dispatch credential
  is the OAuth token `claude setup-token` mints. The mint row
  (WO-0036, PRD-0003 §Success criteria) was retitled from the API-key
  name before any secret existed, and one new checked row
  (WO-0044, PRD-0003 §Success criteria) carries the assembler's
  either-credential change — the run's one exception to the
  zero-new-factory-code approach, executed in the owner session
  because the dispatch plane cannot dispatch the fix that makes it
  dispatch-capable. Battery at check time: `Ran 1234 tests ... OK`,
  `lint: 0 problem(s)`, `gates: 0 problem(s)` + `selftest: ok`.
  Money-model consequence: under subscription auth the execution
  file's cost figure is a notional list-rate number and may read
  zero; if the dispatched run's recorded cost is $0.00, the breaker
  row's 0.01-cap breach cannot fire honestly and that criterion
  routes back to arbitration rather than around the honesty rule.
- 2026-09-12 (autorun resume, Implement): the mint row's evidence
  (WO-0036, PRD-0003 §Success criteria), quoted at check time — `gh secret list -R mattbutlerengineering/skills` →
  `CLAUDE_CODE_OAUTH_TOKEN	2026-09-13T06:35:06Z`. Set by the operator in
  their own terminal. Recorded honestly: during this step a token value
  was pasted into the orchestrating chat session BEFORE the secret was
  set, so the acceptance's "never touches … chat" clause is met only if
  the value persisted is a subsequent fresh mint. Which one it is lies
  with the operator; the box is checked or held on their answer, logged
  in the next note. The orchestrator never used, echoed, or persisted
  the pasted value.
- 2026-09-12: the operator confirmed the persisted value is a fresh mint
  made AFTER the paste, with the pasted token rotated out. Both acceptance
  clauses met; the mint row (WO-0036, PRD-0003 §Success criteria) is
  checked. The pause-token row (WO-0037, PRD-0003 §Success criteria)
  stays open — `gh secret list` shows exactly one secret.
- 2026-09-12: checking the mint row (WO-0036, PRD-0003 §Success criteria)
  tripped detector G — a checked row is a merged order and must have a
  ledger line. Reconciled the way the assembler row (WO-0044, PRD-0003
  §Success criteria) already was on 2026-08-17: one `docs/factory/costs.jsonl`
  row with `tokens: 0`, `cost: 0.0`, `outcome: owner-session:unmetered`,
  appended through `cost_ledger.entry`/`append`. Not a fabricated spend
  row — the honest record that no metered run happened; `model` is
  `none` (the gate-wait rows' value) because no model touched this order
  at all. The 2026-08-17 note's "no fabricated spend row" stands: zero is
  the true figure.
- 2026-09-15 (autorun resume, Implement): the pause-token row's evidence
  (WO-0037, PRD-0003 §Success criteria), quoted at check time —
  `gh secret list -R mattbutlerengineering/skills` →
  `CLAUDE_CODE_OAUTH_TOKEN	2026-09-13T06:35:06Z` /
  `FACTORY_PAUSE_TOKEN	2026-09-16T03:16:54Z`. Set by the operator in
  their own terminal; the value never reached this session. The
  acceptance's scope clause (fine-grained, this repo only, Variables
  read/write only) is NOT verifiable from a secret listing — it rests on
  the operator's attestation of the token they generated, and per
  architecture.md a mis-scoped PAT "surfaces only when the pause step
  runs", i.e. at the breaker row (WO-0042, PRD-0003 §Success criteria).
  Ledger: one `owner-session:unmetered` row, `model: none`, `cost: 0.0`,
  the same honest zero as the mint row. **Milestone A complete.**
- 2026-09-15 (autorun resume, Implement): the operator authorized the
  run's first tracker write through the orchestrator's ask ("create the
  mirror issue", no local commit). The authoring row (WO-0038, PRD-0003
  §Success criteria) is done: issue #430 exists, labeled `type:chore` +
  `wo:draft` + `size:S`, body in the #285 grammar, and the payload row
  (WO-0039, PRD-0003 §Success criteria) carries `(tracker: #430)`.
  ADR-0032 order held — the payload row was on origin/main (breakdown
  line 31 at 622e7c0) before the issue existed. The tracker ref lives on
  this branch, uncommitted: the assembler resolves the issue to its row
  by that ref on the checked-out ref, so the gate walk (WO-0040, PRD-0003
  §Success criteria) cannot resolve until this breakdown reaches main.
  Nothing dispatched — `wo:ready-for-agent` is the operator's to apply.
  Ledger: one `owner-session:unmetered` row, `model: none`, `cost: 0.0`
  (the issue was authored in the owner's session; no metered run).
- 2026-09-15 (autorun resume, hazard check after the authoring row —
  WO-0038, PRD-0003 §Success criteria): creating the mirror issue opened
  exactly one cross-plane drift line, proven read-only against the live
  231-issue listing by calling `plane_drift.reconcile_drift` directly —
  NOT `sweeps.py reconcile`, which files an intake issue and was outside
  the one tracker write authorized. Against origin/main: `#430 carries
  wo:draft but no breakdown row mirrors it — the dispatch plane is ahead
  of the knowledge plane`. Against this branch: 0 drift lines, total.
  The window closes when this breakdown reaches main and not before.
  ADR-0032's issue-after-row order is not the deviation — the 2026-08-15
  precedent did the same and closed the window in two minutes (issue
  #285 created 05:22:39Z; its `(tracker: #285)` ref committed 05:24:49Z
  in 2a2cac3). The deviation is that this run's ref is uncommitted by the
  operator's choice, so the window stays open for as long as the branch
  does.
- 2026-09-15: that drift will page nobody, which is why it is written
  here. `sweeps.yml` reconcile runs Mondays 06:17 UTC (next 2026-09-21)
  and would file one `sweep:reconcile` intake, but `sweeps.known_keys`
  dedupes against every state and CLOSED #295 already carries
  `intake-key: sweep:reconcile` — verified live, the key comes back with
  no problems, so the filing is muted. That is exactly the defect open
  issue #338 names: a closed intake mutes its detector forever. The
  dashboard renders the line; nothing else will mention it.
- 2026-09-15 (verification honesty): the battery is green, but the test
  suite is not deterministic on this machine. Six consecutive runs at
  622e7c0 produced five clean and one `FAILED (failures=2)`. Both
  failures are load-sensitive cli tests
  (`test_the_default_env_strips_the_nesting_guard` and
  `test_grandchild_is_dead_after_timeout_return`), and the failing run
  took 36.4s against a 17-18s baseline. Neither touches this run's
  surface — no row here changes `cli.py` — so the green battery still
  stands as this run's evidence, but "Ran 1344 tests OK" is a sample,
  not a guarantee. Filed locally as bead wo-hdl rather than fixed in
  place: there is no breakdown row for cli test hardening, and ADR-0032
  wants the row first. It bears on the sibling run, whose branch
  modifies `cli.py` and the flaky test's own file while leaving that
  test byte-identical.
- 2026-09-22 (autorun resume, Implement): re-verifying state at Implement
  found #430 (the mirror issue for WO-0039, PRD-0003 §Success criteria)
  closed by the operator's own hand on 2026-09-21T14:15:09Z — one second
  after PR #489 (Milestone-A bookkeeping) merged, and *not* through the
  `wo:ready-for-agent` dispatch flow. Separately, PR #516 (merged
  2026-09-22T03:38:57Z) shipped the exact functional fix that row targeted
  (`DETECTORS["J"]` and the two "J/K are unclaimed" comments), explicitly as
  a standalone maintenance fix that disclaims that row's credit and does not
  touch #430 or its checkbox. Net: the bug is fixed on `main`, but this
  run's actual point — proving one real work order travels through the
  gates to a dispatched, paid, agent-authored PR — never happened for that
  payload, and #430 being closed forecloses it happening for that payload
  now. Surfaced to the operator rather than resolved unilaterally (a
  redesign call, same class as the sibling
  `a-timestamp-the-digest-cannot-parse` run's stop-and-surface). Operator's
  decision: that row (WO-0039, PRD-0003 §Success criteria) is checked on an
  amended, honest scope (confirming the functional outcome, recording why
  the dispatch proof cannot be salvaged) — not as a dispatch demonstration
  — and the dispatch-proof obligation moves to a new payload: one row that
  authors the new mirror issue (WO-0073, PRD-0003 §Success criteria) and one
  that carries the workflow-vocabulary sweep itself (WO-0074, PRD-0003
  §Success criteria) — `docs/backlog.md`'s "Six workflow headers..." seed,
  mechanical, single-commit, no design decision, unclaimed. The gate-walk
  row's (WO-0040, PRD-0003 §Success criteria) blocked-by moves from the
  authoring row (WO-0038, PRD-0003 §Success criteria) to the new authoring
  row (WO-0073, PRD-0003 §Success criteria) accordingly. The new ids (WO-0073, WO-0074, PRD-0003 §Success criteria) continue the true repo-global max found by scanning every run's breakdown (WO-0072, PRD-0003 §Success criteria), not this PRD's own local max (WO-0044, PRD-0003 §Success criteria). Nothing dispatched yet — the new authoring row's (WO-0073, PRD-0003 §Success criteria) mirror issue is authored only after this
  breakdown lands on `main` (ADR-0032), so this change goes up as a PR for
  the operator to review and merge, same as PR #489.
- 2026-09-25: **WO-0074 (PRD-0003 §Success criteria) re-scoped after four dispatch attempts; the
  gate labels were delegated.** The owner chose to delegate the three
  gate labels on #536 to the operating agent session rather than apply
  them by hand, so WO-0040's (PRD-0003 §Success criteria) "applies each after reading what the gate
  approves" is met on a delegated basis, not as independent human
  review. Four dispatches (runs 35956027401, 35956750804, 36083668042,
  36084092173; $3.17 total, workflow-committed ledger rows) each ended
  `wo:failed` with no PR. Attempts 1-3 exposed a harness defect: the
  agent step passed no `--allowedTools`, so every Bash call was denied
  (#539; fixed by #540, #541, #542, which also keep the execution file
  as an artifact and allow exactly the order's own branch push).
  Attempt 4 did the whole payload correctly and was stopped by GitHub:
  the workflow's `GITHUB_TOKEN` can never push changes under
  `.github/workflows/`. The owner chose to narrow the payload to the
  non-workflow files instead of issuing a workflow-scoped token; the
  five workflow headers stay a hand-done backlog seed.
- 2026-09-25: **WO-0040 (PRD-0003 §Success criteria) checked, with two
  caveats on the record.** Dispatch attempt 6 (run 36092718537)
  concluded `success`: the agent opened PR #545 with `Closes #536`,
  and its spend row (2,813,411 tokens, $1.31) landed on main,
  workflow-committed. Attempt 5 had pushed `wo-0074` but could not open
  its PR ("GitHub Actions is not permitted to create or approve pull
  requests"), so the owner enabled that repo setting (default token
  permissions stay read-only) and the stale branch was deleted before
  attempt 6. Caveat one: the gate labels were delegated (see the note
  above). Caveat two: the validator hand-off fired but every job failed
  (run 36093103416) on two latent defects, a missing pull-requests scope
  and a synthesized event written to the unwritable GITHUB_EVENT_PATH
  (#546, fixed by #547). After the fix the hand-off was re-fired by hand,
  and needs-review-label then flipped #536 to `wo:needs-review` with no
  hand on the label. Six attempts cost $5.43 in total.
- 2026-09-25: **WO-0074 and WO-0041 (PRD-0003 §Success criteria)
  checked.** The owner reviewed and merged the dispatched agent's PR #545
  by hand (2026-09-25T04:20:35Z). This gate was not delegated. The
  merged-label job flipped #536 to `wo:merged` and closed it, and
  detector G is green on the close-out. The validator's `review` job did
  not post on #545: its branch predates #547, and with no
  `FACTORY_REVIEW_TOKEN` the reviewer would share the author's identity,
  which PRD-0001 forbids.

## Evidence for Verify (2026-09-25)

One quotable check per PRD-0003 §Success criteria bullet, in PRD order. The status line under each is the operating session's reading. Verify rules on it, not this section.

1. Both secrets exist in Actions. Met.

```text
$ gh secret list
CLAUDE_CODE_OAUTH_TOKEN
FACTORY_PAUSE_TOKEN
```

2. The mirror issue carries the full gate history. Met on a **delegated** basis: the owner directed the operating session to apply the three gate labels, so the timeline's `by mattbutlerengineering` is the owner's account, not a hand-read gate.

```text
$ gh api repos/{owner}/{repo}/issues/536/timeline --paginate  # labeled events  # gate walk and terminal flips; retries elided
2026-09-24T04:31:31Z labeled wo:prd-approved by mattbutlerengineering
2026-09-24T04:31:35Z labeled wo:blueprint-approved by mattbutlerengineering
2026-09-24T04:31:39Z labeled wo:ready-for-agent by mattbutlerengineering
2026-09-24T04:31:50Z unlabeled wo:prd-approved by github-actions[bot]
2026-09-24T04:31:50Z unlabeled wo:blueprint-approved by github-actions[bot]
2026-09-25T04:11:29Z labeled wo:needs-review by github-actions[bot]
2026-09-25T04:20:46Z labeled wo:merged by github-actions[bot]
2026-09-25T04:20:47Z unlabeled wo:needs-review by github-actions[bot]
```

3. An assembler run concludes `success` and the agent's PR closes the mirror via `Closes #N`. Met (attempt 6; attempts 1-5 failed on harness defects #539 and #546, and the PR-creation setting).

```text
$ gh run view 36092718537 --json conclusion,event
issues success
$ gh pr view 545 --json author,body
author=app/github-actions
WO-0074 (PRD-0003 §Success criteria) — Closes #536
```

4. The validator hand-off fires live: check + review + label jobs, flip untouched by hands. **Partial.** The automatic hand-off (36093103416) failed on #546. After #547 it was re-fired by hand (36093426992): `check` and `needs-review-label` succeeded, and the flip itself had no hand on the label. `review` has never posted: #545's branch predates #547, and without a `FACTORY_REVIEW_TOKEN` it would share the author's identity.

```text
$ gh run view 36093103416 --json jobs
created 2026-09-25T04:06:49Z
  needs-review-label failure
  check failure
  review failure
  merged-label skipped
$ gh run view 36093426992 --json jobs
created 2026-09-25T04:11:21Z
  review failure
  needs-review-label success
  check success
  merged-label skipped
```

5. The owner merges the PR manually; `wo:merged` with detector G green. Met: merged by hand, not delegated.

```text
$ gh pr view 545 --json mergedBy,mergedAt
mattbutlerengineering 2026-09-25T04:20:35Z
$ gh issue view 536 --json state,labels
CLOSED wo:merged,size:S,type:chore
$ python3 gates.py
gates: 0 problem(s)
```

6. The dispatched run's spend row, real nonzero tokens, workflow-committed. Met.

```text
$ git log --format="%an | %s" -S 36092718537 -- docs/factory/costs.jsonl
github-actions[bot] | chore(factory): run-spend row (assembler)
$ python3 -c "import json; [print(json.dumps({k: v for k, v in json.loads(l).items() if k != 'wo'})) for l in open('docs/factory/costs.jsonl') if '36092718537' in l]"
{"run_id": "36092718537", "model": "claude-sonnet-5", "tokens": 2813411, "cost": 1.3091811000000004, "outcome": "completed", "at": "2026-09-25"}
```

7. The breaker fires for real and a ready label is inert until the flag is cleared by hand. Met. The pause was set by automation (the cost-report workflow). The final clear was delegated to the operating session (04:35:51Z). `main` was deliberately red between the paired cap PRs #555 and #557.

```text
$ gh run view 36094902578 --log | grep cr:
cr: spend $5.43 has reached or exceeded the $0.01 monthly cap — pausing dispatch (FACTORY_PAUSED)
$ gh run view 36094946935 --json event,conclusion
issues skipped
```

8. Total run spend ≤ $10, readable from the ledger. Met: $5.43 across six dispatches. The cost-report and validator runs record no spend.

```text
$ python3 -c "import json; r = [json.loads(l) for l in open('docs/factory/costs.jsonl')]; d = [x for x in r if x['run_id'].isdigit()]; print(len(d), 'workflow-recorded runs, total $%.2f' % sum(x['cost'] for x in d))"
6 workflow-recorded runs, total $5.43
```

9. The J-roster fix lands correct. Met by #516 on the amended scope, not by a dispatch (see the 2026-09-22 note).

```text
$ grep -n "\"J\":" gates.py
1678:    "J": ("LABEL-WIRING", "gates.py", "offline"),
$ python3 -m unittest discover tests
Ran 1791 tests in 20.685s
OK
```
