---
stage: review
run: feature:first-live-dispatch
date: 2026-10-02
assumptions:
  - "Severity rubric, applied with no live user to arbitrate: CRITICAL — a reproducible path by which a principal other than the owner (the dispatched agent included) bypasses a human gate, lands code on main, or reaches a long-lived credential, with no owner action between cause and effect. MAJOR — a PRD success criterion or architecture contract not met, or a defect with a concrete scenario that corrupts the run's evidence or a security property the code itself claims, where an owner action or a further condition sits between cause and effect. MINOR — record or doc drift, or a bounded defect with no evidence or security consequence."
  - "Decision vocabulary, per the brief: every major is recorded 'open — needs owner decision'; minors are deferred with a logged reason; the one critical is 'must fix before Ship — route to Implement' and was not fixed here. This stage's only write is this file."
  - "Scope is the set of PRs and commits breakdown.md's rows and notes and verification.md's evidence cite as this run's own work (listed under Scope), not the repo diff since 2026-08-17. PR #567 (ADR-0074) is examined as ADJACENT: it is not this run's PR, but verification.md's gate-latency reconciliation names its bead and its side effect lands on this run's ledger rows."
  - "Standards: docs/standards.json holds four statements, all `status: advisory`; filtered to the domains the diff touches (factory, pipeline, eval). None of the five findings matches a statement's text, so no finding cites a slug and the enforced-statement must-fix trigger does not fire — the critical is critical on the rubric alone."
  - "The scopes of FACTORY_REVIEW_TOKEN and FACTORY_PAUSE_TOKEN cannot be read from this seat (only secret names list). The reviewer ACCOUNT's repo role was read live (write). Finding 4's severity is conditional on the PAT's scope and says so."
  - "That the dispatched agent's Bash subprocesses inherit the job's environment and git credential is taken from the action's observed behaviour in this run (attempt 5's `git push -u origin wo-0074` succeeded and `gh pr create` reached GitHub's 'not permitted to create or approve pull requests' refusal — both authenticated from the agent's shell), not from reading claude-code-action's source."
  - "Nothing was run live: no dispatch, no `claude` CLI, no workflow, no label. The one reproduction (finding 2) ran against a `git archive HEAD` scratch copy."
---

# Review: first live dispatch

## Scope

The run's change is spread across six weeks and interleaved with other
runs, so the diff reviewed is the set of PRs and commits that
`breakdown.md`'s rows and notes and `verification.md`'s evidence cite —
22 run PRs, one direct commit, and seven bot-authored ledger commits —
each confirmed to exist with `git log`/`gh pr view` before it was
counted. Code-bearing items were read line by line ("in depth"); docs
PRs were read for what they record.

Code-bearing, examined in depth:

- `fbfa3c3` (direct to main, 2026-08-17) — WO-0044 (PRD-0003 §Success
  criteria): assembler job env carries both credentials, three `if:`
  guards accept either, action gets `claude_code_oauth_token`; mirror
  + manifest in the same commit.
- #516 — the J-roster fix (`gates.py` docstring, `DETECTORS["J"]`, the
  unclaimed-letters comment, one test); a standalone maintenance fix
  that disclaims WO-0039's credit and is criterion 9's evidence.
- #540, #541, #542 — the assembler allowlist series closing issue
  #539: `--allowedTools` added; execution file kept as an artifact and
  the push rule moved to the `:*` prefix form; the push rule narrowed to
  the exact `branch_for(wo)` output.
- #545 — the dispatched agent's PR for WO-0074 (PRD-0003 §Success
  criteria): five one-line docstring edits plus manifest.
- #547 — the validator hand-off fix closing issue #546: shims hand the
  synthesized PR event over as `FACTORY_EVENT_PATH`, `cli.read_event`
  prefers it, `check` and `needs-review-label` gain `pull-requests:
  read`.
- #555, #557 — the paired cap PRs for WO-0042 (PRD-0003 §Success
  criteria): `monthly_cap_usd` 300 → 0.01 → 300, manifest regenerated
  both times.
- #579 — the dispatched agent's PR for WO-0076 (PRD-0003 §Success
  criteria): `charter_replay.py` imports `ROOT` from `trigger_eval`.

Docs and ledger, read for the record: #489 (Milestone A: WO-0036,
WO-0037, WO-0038 checked, three `owner-session:unmetered` rows), #519
(WO-0039 superseded; WO-0073/WO-0074 minted), #538 (#536 recorded),
#544 (WO-0074 re-scoped off workflow files), #549 (WO-0040 checked
with caveats), #553 (WO-0074 and WO-0041 checked), #559 (WO-0042 and
WO-0043 checked; evidence), #561 (verification, 8/2), #565
(gate-latency reconciliation), #573 (WO-0075/WO-0076 minted), #576
(#574 recorded), #578 (WO-0075 checked), #581 (re-verification, 9/1);
the seven `chore(factory): run-spend row (assembler)` commits for runs
35956027401, 35956750804, 36083668042, 36084092173, 36090269361,
36092718537 and 36474781292.

Adjacent, examined for one finding only: #567 (ADR-0074, bead
`wo-ldf`), and the gate-digest ledger commits `bbfe3c8` and `661ffc7`.

Out of scope, named so the exclusion is visible: #506, #511, #513,
#517 and the other PRs merged in the same window belong to other runs;
the owner's repo-setting change ("Allow GitHub Actions to create and
approve pull requests", read live as `can_approve_pull_request_reviews:
true`) is not a commit and is examined only where finding 1 reaches it.

Live state read (read-only `gh`): secrets `CLAUDE_CODE_OAUTH_TOKEN`,
`FACTORY_PAUSE_TOKEN`, `FACTORY_REVIEW_TOKEN`; variable
`FACTORY_PAUSED=false` (updated 2026-09-28T15:31:01Z); branch
protection on `main` returns HTTP 403 ("Upgrade to GitHub Pro");
`mattbutlerengineeringreviewer` holds the `write` role; artifacts
`agent-execution-WO-0074` (106,440 bytes, expires 2026-10-09) and
`agent-execution-WO-0076` (28,385 bytes, expires 2026-10-12) exist.

## Findings

### Critical: the agent allowlist's "push boundary" is defeated by its own `Bash(python3:*)` and `Bash(make:*)` entries

- Scenario: #540 added `--allowedTools` to the agent step and #542
  narrowed the push entry to exactly `Bash(git push -u origin
  <branch>)`; the workflow comment and PR #540's body both state that
  "no branch protection guards main on this plan, so this list is the
  push boundary" (branch protection is confirmed unavailable: HTTP 403
  on the protection endpoint). The same list carries
  `Bash(python3:*)` and `Bash(make:*)`, and a `:*` entry is a prefix
  rule (PR #542's own analysis). So when the agent's sanctioned push is
  denied or the step after it is refused — attempt 3 had its push
  denied, attempt 5 had its `gh pr create` refused — the ordinary
  agent reflex `python3 -c "import subprocess;
  subprocess.run(['git','push','origin','HEAD:main'])"` is allowed;
  `actions/checkout@v4` persists the job's `GITHUB_TOKEN` in the
  workspace by default, the job holds `contents: write`, and the
  commits land on `main` with no gate 3. `Bash(make:*)` plus the
  allowed `Edit` on `Makefile` is the same hole. The job's other
  grants are reachable the same way: `pull-requests: write` with the
  repo setting the owner enabled lets the agent approve its own PR;
  `issues: write` lets it flip its own order's `wo:` labels;
  `actions: write` lets it `gh workflow run` or cancel the validator.
  And `python3 -c 'import os; print(os.environ["CLAUDE_CODE_OAUTH_TOKEN"])'`
  places the roughly one-year subscription token (job-level env since
  WO-0044) in the execution file that #541 now retains as a 14-day
  artifact — GitHub masks secrets in logs, not in artifacts. GitHub's
  own `workflows` scope is the one boundary that still holds (attempt
  4 proved `GITHUB_TOKEN` cannot push `.github/workflows/`).
  `tests/test_assembler.py::TestAgentToolAllowlist` pins the idea
  ("pushes only to a wo- branch, never bare `git push` or `git:*`")
  while REQUIRING `Bash(make:*)` and `Bash(python3:*)` in
  `test_the_swe_exit_is_allowed` — the test encodes the boundary and
  the entries that defeat it in the same list. Nothing in the repo,
  backlog or beads records this.
- Standard: none.
- Decision: must fix before Ship — route to Implement. Not fixed here.
  Candidates for Implement to weigh, not a prescription: narrow the two
  entries to the verification commands the SWE exit actually needs
  (`python3 -m unittest`, `python3 gates.py`, `python3 lint.py`, `make
  check`); stop persisting the checkout credential so only the action's
  own push path authenticates; keep the artifact but strip or stop
  retaining tool output. The subscription token must reach the `claude`
  process to run at all, so the fix is about arbitrary execution and
  persistence, not about removing it from the job.

### Major: ADR-0074's fix re-emitted this run's gate rows under new keys — the ledger now records the first traversal twice

- Scenario: `cost_ledger.row_key` is `(wo, run_id)`, and `gate_entry`
  keys `run_id` on the passage timestamp. #567 (2026-09-28, bead
  `wo-ldf`, ADR-0074) moved a confirmed stay's end to its pass label —
  the structural fix verification.md's reconciliation asked for — so
  every already-recorded passage whose pass label preceded the queue
  label's removal now yields a different key, and the daily digest's
  dedup cannot see the old row. Reproduced in a scratch copy on #536's
  real history: `gate_passages` returns `gate-prd-2026-09-24T04:31:31Z`,
  `gate-blueprint-2026-09-24T04:31:35Z`, `gate-merge-2026-09-25T04:20:46Z`
  against the recorded `...04:31:50Z`, `...04:31:50Z`, `...04:20:47Z`.
  The 2026-09-29 digest run (`661ffc7`) appended exactly those three
  rows (1380s, 4s, 557s) beside the originals (1399s, 19s, 558s), plus a
  historical WO-0034 merge row (47s beside 48s). `docs/factory/costs.jsonl`
  now holds two PRD-gate, two blueprint-gate and two merge-gate rows for
  WO-0074. `dashboard.gate_wait_median` (dashboard.py:289) reads both;
  ADR-0069's `gate_hours` sum, which the fix was made to protect, counts
  the first traversal's wait twice. The ledger is append-only, so the
  duplicates cannot be removed, and ADR-0074's consequence ("rows already
  in the ledger stand as recorded ... corrected in its run's verification,
  not rewritten") did not anticipate the re-emission. verification.md's
  sentence "A structural fix is filed as a bead; this run does not
  implement it" is also now stale — the fix landed two days later and the
  2026-09-28 re-verification did not revisit it. Spend totals are
  unaffected (gate rows carry `cost: 0.0`); criterion 8's $5.90 stands.
- Standard: none (the rows are machine-written, not fabricated).
- Decision: open — needs owner decision. The choices are the owner's and
  Implement's, not this stage's: a supersession rule readers apply (a
  later row for the same `(wo, gate)` replaces an earlier one), a
  stay-identity key (`wo`, gate, stay START) in `cost_ledger.row_key`,
  or an explicit exclusion when ADR-0069's baseline is first computed.
  None of this run's rows covers it.

### Major: criterion 2 — gate labels applied by the owner's hand — is unmet on both traversals, and the dispatch guard cannot tell

- Scenario: on #536 (2026-09-24) and again on #574 (2026-09-28) the
  owner delegated `wo:prd-approved`, `wo:blueprint-approved` and
  `wo:ready-for-agent` to the operating agent session, which applied
  them through the owner's `gh` login. The decayed contracts are
  architecture.md phase 3 ("each applied by Matt after actually reading
  what the gate approves — the supervision IS the gate") and PRD-0003's
  out-of-scope note ("this run flips gate labels by hand at the gates,
  which is the point of supervision"). The security reading is the
  sharper one: assembler.yml's only trigger authority is
  `github.event.sender.login == github.repository_owner`, which checks
  WHOSE credential applied the label, not that a human read the gate —
  an agent session holding the owner's credential fires a paid dispatch
  and the timeline cannot distinguish it, which is exactly why Verify's
  FAIL stands. The first delegated walk also used `--add-label` without
  removing the queue labels (ADR-0032's one-lifecycle-label rule), the
  upstream cause of finding 2; the second walk replaced them correctly.
- Standard: none (`adr0032-one-way-mirror` is the issue-after-row rule,
  which held on #430, #536 and #574).
- Decision: open — needs owner decision. Both a finding and a carried
  obligation: the finding is the deviation from the run's own contract;
  the obligation — one future dispatch whose three gate labels the owner
  applies by hand, replacing each queue label — is its only route to
  closure, and no Implement work exists for it. Ship records it open.

### Major: the review job runs the PR's own code under the reviewer PAT, and the reviewer account holds write

- Scenario: validator.yml's `review` job checks out
  `refs/pull/<N>/head` — the agent's branch — and its "Post findings"
  step runs `make review` with `GH_TOKEN: ${{ secrets.FACTORY_REVIEW_TOKEN
  || secrets.GITHUB_TOKEN }}`. `make review` is the PR's `Makefile`
  invoking the PR's `validator.py`, so an agent PR that edits either can
  post any comment or an approving review as `mattbutlerengineeringreviewer`
  (role read live: `write`), or print the PAT into the posted findings.
  The job fires automatically from the assembler's hand-off (and on
  `pull_request` for every same-repo branch) with no owner step before
  the token reaches PR-controlled code. The workflow's own comment says
  the fork guard's concern "cannot arise" because the factory's PRs are
  same-repo branch PRs — but the branch's author is the model, which is
  the concern. PRD-0001's separation of generation from verification is
  the decayed contract. The code path predates this run (WO-0030); this
  run made it live by minting `FACTORY_REVIEW_TOKEN` (WO-0075's
  acceptance) and fixing the hand-off (#547), and the first real post —
  the comment on #579 — ran on it. `FACTORY_REVIEW_LOGIN` is unset, so
  the optional cross-check is not in play. Ranked major, not critical,
  because the owner's own reading of the PR at gate 3 sits between a
  forged review and a merge. It is critical if the PAT is classic
  `repo`-scoped or fine-grained with `contents: write`: a write-role
  account's token can then push and merge, and the agent's PR code
  holds it.
- Standard: none.
- Decision: open — needs owner decision. First: state the PAT's scopes.
  Then Implement's candidates: run `make review` from the base ref's
  tools (check out the PR only for `make check`'s findings, post from a
  `main` checkout), or drop the reviewer account to `triage`.

### Minor: architecture.md's "zero new factory code — one exception" no longer describes the run

- Scenario: the approach section says the run's only human-hands repo
  edits are its artifacts, the payload row and the cap pair, with
  WO-0044 the one factory-code exception. Implement shipped four more by
  hand — #540, #541, #542 (assembler.yml, assembler.py) and #547
  (validator.yml, cli.py) — each under a detector-B "No work order"
  waiver and a dated breakdown note, and PRD-0003 lists "the validator
  dispatch-arm hardening bundle" as out of scope while #547 is exactly
  that. Phase 6's "the clear is deliberately human" also contradicts
  cost-report.yml's resume step, which clears `FACTORY_PAUSED` on any
  under-cap verdict (observed: the 2026-09-28 scheduled run set it
  `false` at 15:31:01Z). The architecture artifact carries no amendment
  for any of this.
- Standard: none.
- Decision: deferred — the deviations are on record in breakdown.md's
  dated notes and the PR bodies; this stage writes only review.md, and
  Ship/Operate can carry a dated amendment if the owner wants the
  artifact to match.

### Minor: nothing refuses a work order whose payload touches `.github/workflows/`

- Scenario: attempt 4 (run 36084092173, $0.73) did WO-0074's original
  payload correctly and was stopped at push — `GITHUB_TOKEN` cannot
  push workflow files. The limitation is unchanged; the control today
  is a hand-written clause in WO-0074's and WO-0076's Accept lines ("no
  file under `.github/workflows/` is touched") and the backlog seed's
  narrowing note. The next row whose fix is under `.github/workflows/`
  that is labelled ready will burn one paid run and end `wo:failed`,
  repeatably.
- Standard: none.
- Decision: deferred — bounded (one run, visible as `wo:failed` with
  its spend row) and the Accept-clause convention is the current
  control; a resolve-time check on the row's text would be anticipated
  reuse, which CLAUDE.md's seam bar refuses until a second instance
  shows divergence.

## Passes with no findings

No pass came back wholly clean; what each examined and cleared:

- **Correctness** — #547's `read_event`: `FACTORY_EVENT_PATH` wins when
  set, an empty or unset value falls through to `GITHUB_EVENT_PATH`,
  errors name the variable actually read, both pinned in
  `tests/test_cli.py`. #542's exact push rule: `--force`, a `:main`
  refspec or any trailing argument fails the exact match (this is the
  sanctioned path's correctness; finding 1 is the unsanctioned ones).
  WO-0044: three `if:` guards and the job env agree, the action gets
  both inputs, and the graceful skip survives (a repo with neither
  secret claims nothing). #555/#557 are symmetric two-line changes with
  the manifest regenerated both times; the 2m46s red-`main` window
  between them is recorded in verification and reverted. #516: the
  docstring, the comment and `DETECTORS["J"]` agree and a test pins it.
  #545 and #579 are the five one-line docstring edits and the one-line
  import their rows describe; `one_owner.py` no longer reports `ROOT`.
  The ledger's seven workflow-committed spend rows sum to $5.90 ≤ $10;
  the eleven `owner-session:unmetered` rows are honest zeros, not
  fabricated spend.
- **Design** — ADR-0032's issue-after-row order held for all three
  mirror issues (#430, #536, #574). The second traversal's label walk
  replaced each queue label. Stdlib-only holds (no dependency added).
  PRD-0003's id lives in `prd.md`'s frontmatter. The validator's
  `check` and `needs-review-label` grants grew by exactly
  `pull-requests: read`, matching `tests/test_workflow_permissions.py`'s
  recorded table.
- **Security** — the dispatch trigger requires `sender.login ==
  repository_owner` and `assembler.actor_is_owner` re-checks it;
  `FACTORY_PAUSE_TOKEN` appears only in cost-report.yml's pause and
  resume steps, never in the agent's job; label flips are claim-gated
  (`transitioned == 'true'`); the review comment on #579 is a comment
  under the reviewer identity with no review (approval) object; secret
  values appear nowhere in the repo — only the three names in `gh
  secret list`. The cap pair never touched a token.

## Verdict

Not ready to ship. Finding 1 is critical under the stated rubric —
the allowlist that the run's own PRs call "the only thing keeping
pushes off `main`" is defeated by two of its entries, with the
subscription token and every job grant in reach — and per the skill's
fix loop it is routed to Implement, then re-verified, before Ship.
Three majors are open for the owner's decision: the duplicated gate
rows (finding 2), the unmet human-gate criterion carried as an open
proof obligation (finding 3), and the reviewer PAT reaching
PR-controlled code (finding 4, whose severity turns on the PAT's
scopes). Two minors are deferred with reasons. The run's headline
claim stands as verification recorded it — a real order traversed the
gates to a paid, agent-authored, human-merged PR at $5.90 — and so
does its honest FAIL.
