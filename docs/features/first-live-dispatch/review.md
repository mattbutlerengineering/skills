---
stage: review
run: feature:first-live-dispatch
date: 2026-10-10
assumptions:
  - "Re-review after Implement's Milestone E (WO-0128, WO-0129; ADR-0077) answered the 2026-10-02 Critical. The severity rubric is the 2026-10-02 one, unchanged (kept below). The earlier review is superseded, not rewritten: it follows this one under its own heading."
  - "Scope is git diff origin/main...HEAD on fix/fld-allowlist-boundary as of 3613ed4 (WO-0128, WO-0129, the re-verification, one merge of main), plus the validator.yml job the deliver job now dispatches into, read for reachability only."
  - "This stage fixed the new Critical and one new Major on the branch, test-first, as WO-0130 to WO-0132 with $0 owner-session ledger rows matching WO-0129's. The brief authorises fixing criticals and majors here; old Majors 2 to 4 stay owner decisions as the brief directs."
  - "The tag-to-main path was reproduced with real git (2.50.1, macOS) in scratch repos and is replayed by a test that runs the workflow's own lines; it was not run on a GitHub runner. That git's fetch auto-follows tags and that rev-parse prefers refs/tags/<name> over refs/remotes/<name> is long-standing documented git behaviour, not a platform quirk."
  - "Mutation tests ran against the working tree and were restored with git checkout; the tree was clean before each commit."
  - "Standards: docs/standards.json holds four statements, all advisory; none matches a finding, so no finding cites a slug."
  - "verification.md's 2026-10-10 re-verification predates WO-0130 to WO-0132. Their evidence (battery, the replay test, the mutation results) is recorded here; the live-dispatch obligations verification lists are unchanged by them."
---

# Review: first live dispatch

## Re-review (2026-10-10)

### Scope

`git diff origin/main...HEAD` on `fix/fld-allowlist-boundary`, as
Implement left it (`c0eb26c` WO-0128, `77e0c51` WO-0129, `4794e76` a
merge of main, `3613ed4` the re-verification): `assembler.yml` and its
mirror split into `dispatch` / `agent` / `deliver`; `assembler.py`'s
`PR_BODY_FILE` and prompt; the jq-filtered record; the subprocess
scrub; `tests/test_assembler.py`, `tests/test_gates.py`,
`tests/test_workflow_permissions.py`; ADR-0077 and its index row; the
manifest; the two ledger rows; Milestone E in `breakdown.md`. Every
`${{ }}` inside a `run:` block in the three jobs was listed and traced
to its source. `validator.yml` was read because the deliver job now
dispatches into it.

Everything was read adversarially, asking whether code the agent
controls can still reach a write credential or `main`.

### Findings

| # | Severity | Finding | Disposition | Commit |
|---|---|---|---|---|
| R1 | Critical | A tag in the agent's bundle carries the agent's commits onto `main` through the spend-row step | fixed (WO-0130) | `84b4abf` |
| R2 | Major | find-pr can pick an outsider's fork PR, and the validator then runs it with the reviewer PAT | fixed (WO-0131) | `1109b1e` |
| R3 | Major | The agent's code reaches a write credential one hop later: the validator's `review` job runs the agent's branch | open, needs owner decision (this is finding 4 below, re-scoped); ADR-0077 now says so | `84b4abf` (ADR text) |
| R4 | Minor | The boundary tests let a secret in a step env of the agent job through | fixed (WO-0132) | `a333300` |
| R5 | Minor | The agent can pre-populate `$RUNNER_TEMP/handoff`, so `handoff.bundle` can arrive as a directory (a local repo) rather than a bundle | deferred | — |
| R6 | Minor | `Bash(gh issue view:*)` lets the agent read outsider-written issue comments | deferred | — |
| R7 | Minor | The kept record's `permission_denials` carries each denied call's input verbatim | deferred | — |
| 2 | Major (2026-10-02) | ADR-0074 re-emitted gate rows | open, needs owner decision; this change does not touch it | — |
| 3 | Major (2026-10-02) | Criterion 2's gate labels were not applied by the owner | open, needs owner decision; this change does not touch it | — |
| 4 | Major (2026-10-02) | The review job runs PR code under the reviewer PAT | open, needs owner decision; now reachable automatically from every dispatch, see R3 | — |
| 1 | Critical (2026-10-02) | The allowlist was called the push boundary while `python3:*` and `make:*` defeated it | fixed by WO-0128 and WO-0129, plus R1 here | `c0eb26c`, `77e0c51`, `84b4abf` |
| 5 | Minor (2026-10-02) | architecture.md's "zero new factory code" | deferred, unchanged | — |
| 6 | Minor (2026-10-02) | Nothing refuses a payload under `.github/workflows/` | deferred, re-judged below | — |

#### Critical: a tag in the agent's bundle carries the agent's commits onto `main` (R1)

- Scenario: the agent job owns the hand-off. The agent's code runs on
  that runner with passwordless sudo, can write `$GITHUB_ENV` (which
  feeds the packaging step) and can leave processes running. So it can
  ship any bundle it likes; the packaging step's own
  `git bundle create ... refs/heads/$BRANCH` is not a constraint on
  it. The deliver job then ran
  `git fetch "$HANDOFF/handoff.bundle" "refs/heads/$BRANCH:refs/heads/$BRANCH"`.
  The refspec is exact, but a default fetch also auto-follows every
  tag that points into the fetched history. A bundle carrying
  `refs/tags/origin/main` at the agent's commit therefore lands that
  tag. Two steps later the spend-row step runs
  `git worktree add "$RUNNER_TEMP/spend" origin/main`, and git's ref
  lookup tries `refs/tags/origin/main` before
  `refs/remotes/origin/main`, so the worktree is the agent's commit.
  The step appends the spend row, commits, and runs
  `git -C "$RUNNER_TEMP/spend" push origin HEAD:main` with
  `contents: write`. With no branch protection, the agent's commits
  are on `main`, under a "run-spend row" commit, with no gate 3 and no
  owner action in between. It needs only `steps.record.outcome ==
  'success'`, which any well-formed execution record gives. Reproduced
  with real git in scratch repos: origin's `main` became
  `run-spend row` → `evil` → `base`, and git warned only "refname
  'origin/main' is ambiguous". ADR-0077's sentence "A bundle that
  carries other refs brings nothing else across" was false. The
  agent's motive need not be its own: the same agent can read
  outsider-written issue comments (R6).
- Standard: none.
- Decision: fixed (WO-0130, `84b4abf`). The fetch is now
  `git fetch --no-tags ...`, and the spend worktree names
  `refs/remotes/origin/main`. Either alone closes the replay, which
  was checked by reverting each one in turn; both are pinned.
  `TestBundleCannotReachMain` reads the deliver job's own fetch line
  and its whole spend-row step out of the workflow and replays them
  against such a bundle. It failed on the old lines with `main~1` ≠
  base. ADR-0077's decision 2 now records the guard and why it is
  load-bearing.

#### Major: find-pr could hand an outsider's fork PR to the validator (R2)

- Scenario: `assembler.pr_for_issue` took the newest open PR whose
  body has `Closes #N`, from any author and any repo. On a public repo
  anyone can open a fork PR citing a dispatched order's issue. If it
  is newer than the deliver job's own PR (open it while the agent is
  running, which takes minutes), find-pr returns its number, and the
  deliver job runs `gh workflow run validator.yml -f pr=<it>`. The
  validator's `workflow_dispatch` arm has no fork guard (its comment
  says the concern "cannot arise" there). Its `review` job checks out
  `refs/pull/<N>/head` and runs that PR's `Makefile` twice: `make
  check` beside checkout's persisted `pull-requests: write` token, and
  `make review` with `GH_TOKEN` set to `FACTORY_REVIEW_TOKEN`, a PAT
  for an account with the `write` role. An outsider's code would get
  the reviewer PAT with no owner action in between. This is Major and
  not Critical because what the PAT can do turns on its scopes, which
  this seat cannot read (as in finding 4).
- Standard: none.
- Decision: fixed (WO-0131, `1109b1e`). The listing requests
  `isCrossRepository` and skips any PR that is not stated to be
  same-repo, failing closed when the field is absent. The tests
  cover a newer fork PR, a PR missing the field, and the same-repo
  match. The real fix for the PAT is finding 4's owner decision; this
  removes the outsider's way into it.

#### Major: the agent's code reaches a write credential one hop later (R3, finding 4 re-scoped)

- Scenario: ADR-0077 moves the boundary for the assembler. The deliver
  job then pushes the agent's branch and dispatches the validator on
  its PR on every successful dispatch. The validator's `review` job
  runs that branch's `Makefile` and modules: `make check` beside a
  persisted `pull-requests: write` GITHUB_TOKEN, and `make review`
  under the reviewer PAT. So an agent that edits the `Makefile` (or
  `validator.py`) on its branch gets the PAT's grants and the
  reviewer identity automatically. That can mean forged approvals or
  findings, and pushes or merges if the PAT has `contents: write`.
  The `pull-requests: write` token cannot approve: its PR author is
  also `github-actions[bot]`, and without `contents: write` it cannot
  merge. Before this review the ADR's "Not closed" list did not
  mention this path.
- Standard: none.
- Decision: open, needs owner decision. It is finding 4, unchanged in
  substance and now known to be reached from every dispatch. ADR-0077's
  Consequences now name it as not closed (in `84b4abf`). The fix
  options are as before: post from a base-ref checkout and check out
  the PR only to produce findings, with `persist-credentials: false`
  on that checkout; or drop the reviewer account to `triage`. It is
  ranked Major, not Critical, for the 2026-10-02 reason: it turns on
  the PAT's scopes, and the owner reads the PR at gate 3 before any
  merge if the PAT cannot write contents.

#### Minor: the boundary tests did not see a secret in a step env (R4)

- Scenario: a mutation adding `PAT: ${{ secrets.FACTORY_REVIEW_TOKEN }}`
  to the packaging step's env broke only the mirror-drift tests, which
  `update-manifest` would silence. Every `TestAgentCredentialBoundary`
  test passed, because they looked at the job-level env and `GH_TOKEN`
  only.
- Standard: none.
- Decision: fixed (WO-0132, `a333300`). The agent job may name exactly
  the action step's three secret inputs and no `github.token`. The
  same mutation now fails.

#### Minor: the hand-off directory is the agent's to pre-populate (R5)

- Scenario: the packaging step runs `mkdir -p "$HANDOFF"` and `||
  echo` past a failed `git bundle create`. An agent that created
  `$RUNNER_TEMP/handoff/handoff.bundle/` as a bare repo would have it
  uploaded (it has no dotfiles), and deliver's `git fetch` would treat
  the path as a local repository and run `upload-pack` in it. With the
  refspec exact and `--no-tags`, nothing beyond the order's ref
  arrives. Git documents `upload-pack` as safe to run in an untrusted
  repo (for example, `uploadpack.packObjectsHook` is honoured only
  from protected config).
- Standard: none.
- Decision: deferred. No scenario gets further than the fetch already
  allows. A `test -f` guard is cheap if a later git release narrows
  that guarantee.

#### Minor: the allowlist lets the agent read outsider-written issue text (R6)

- Scenario: `Bash(gh issue view:*)` allows `--comments`. Anyone can
  comment on a public mirror issue, so the ADR-0032 prompt-injection
  boundary (the row, never the issue) holds for the prompt but not for
  what the agent can read. Text injected that way could steer an agent
  toward R1's bundle trick.
- Standard: none.
- Decision: deferred. After WO-0128 to WO-0131 the payoff is bounded
  to the read-only job and to the gate-3 PR the owner reads. Narrowing
  the entry to the body only, or dropping it, is a charter_replay
  concern: it changes what the SWE can see, and that run is paid and
  on demand.

#### Minor: the kept record's denials carry each denied input verbatim (R7)

- Scenario: the KEEP filter keeps `permission_denials`, including
  `tool_input`. A denied command that embedded a credential literally
  would be kept for 14 days in an artifact, where GitHub does not mask
  it.
- Standard: none.
- Decision: deferred. The denial list is the post-mortem evidence
  WO-0129 kept on purpose (run 35956750804). The scrub keeps the model
  credential out of the agent's subprocesses, and a literal secret in
  a *denied* call needs the agent to have read it first.

#### Old findings re-judged

- **1 (Critical, 2026-10-02): fixed.** WO-0128 moves the boundary to
  the token, and no allowlist entry is load-bearing any more. WO-0129
  stops keeping a transcript. R1 closed the one path from the
  hand-off back to `main`. Mutations confirmed the pins: adding
  `pull-requests: write` to the agent job fails 3 tests (both
  boundary tests and the recorded-grant table); moving a secret into
  the agent job env fails `test_the_agent_job_hands_no_credential_to_its_shell`;
  widening the bundle fetch to `refs/*:refs/*` fails
  `test_the_hand_off_crosses_as_data`; a secret in a step env failed
  nothing until WO-0132 (R4).
- **2, 3 (Major): unchanged, open for the owner.** Nothing in this
  diff touches the ledger keys or the gate-label walk.
- **4 (Major): open, now R3.** It is reached from every dispatch.
  WO-0131 removes the outsider's way in, and the agent's way in
  remains.
- **5 (Minor): deferred, unchanged.** Milestone E's breakdown notes
  and ADR-0077 are the dated record of the new deviation.
- **6 (Minor): deferred, re-judged.** The deliver job's push of a
  branch that touches `.github/workflows/` is still refused, because
  `GITHUB_TOKEN` has no `workflows` scope. The order fails at the
  push step and flips to `wo:failed`, with one paid run spent. That
  refusal is now also a security property: it is why an agent's
  branch can never carry a workflow edit to a runner. The Accept-clause
  convention remains the control.

#### ADR-0077 judged

It belongs as an ADR under CLAUDE.md's bar: it decides where a
credential lives for every stamped repo, it is hard to reverse, it
weighed and rejected alternatives (a narrower allowlist,
`persist-credentials: false`, step-scoped tokens) on evidence read
from the pinned action's source, and it amends no earlier record.
`provisional` is the right status: four runner behaviours are
unverified until a live dispatch, and the ADR names them. It was
inaccurate in two places, both corrected in `84b4abf`. Decision 2
claimed other refs could not cross (R1). The residuals listed "this
run's cache scope", but an `issues` run's cache scope is the default
branch, which every workflow can restore. No workflow here restores a
cache today, so that is a latent residual, and it is now stated. The
residual one hop later (R3) was missing and has been added.

#### Expression-injection audit

Every `${{ }}` inside a `run:` block in the three jobs:
`github.event.issue.number` (an integer), `needs.dispatch.outputs.wo`
and `.model` (from the repo-controlled breakdown row and charter, via
trusted `make assembler`), `github.run_id`, `runner.temp`, a boolean
expression over `needs.agent.outputs.outcome` that can only yield
`completed` or `agent-failed`, and `steps.find.outputs.pr` (written by
trusted find-pr as an int). Nothing derived from issue, comment or PR
text reaches a shell. The branch, handoff path and execution path go
through `env:`. The PR title is `"$(git log -1 --format=%s ...)"`, a
quoted command substitution whose output is not re-parsed, and the
body goes through `--body-file`. The only agent-job outputs deliver
reads are `outcome` (the step conclusion, not settable through
`$GITHUB_OUTPUT`) and `execution_file`, which appears only in `if:`.
An agent writing it to `$GITHUB_OUTPUT` changes nothing deliver
executes. `actions/download-artifact@v4` resolves past the 4.1.3
zip-slip fix and extracts into `runner.temp`, outside the trusted
checkout. Deliver runs only the base checkout's own `make` targets.
The agent's work is never checked out there: the bundle is fetched to
a ref and pushed, and with R1 fixed it never reaches a worktree.
`always()` on deliver and its steps re-gates every write on
`transitioned == 'true'` and on the agent's `outcome` or the record
step's own success.

### Passes with no findings

- **Correctness**: the three-job wiring (needs, outputs, `always()`
  terms, the ADR-0063 `looked` guard) is consistent, and `actionlint`
  is clean on `assembler.yml`. The jq KEEP filter handles both the
  array and the object execution-file shapes, and its test runs real
  jq through `cli.read_execution`. The prompt names the body file and
  no push.
- **Design**: stdlib-only holds. The mirror, the manifest and
  detector E agree. The new step lines are allowlisted in
  `test_gates`'s run-step invariant with reasons. `PR_BODY_FILE` is
  owned once in `assembler.py`.
- **Security**: R1 to R7 above are the only findings. The model
  credential appears in the agent job only as the action's inputs,
  pinned now. No secret value is in the repo.

### Battery (after WO-0132)

```
$ python3 -m unittest discover tests 2>&1 | grep -E "^(Ran|OK|FAILED)"
Ran 1971 tests in 26.476s
OK
$ python3 lint.py
lint: 0 problem(s) across 25 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
$ actionlint .github/workflows/assembler.yml   # exit 0, no output
```

### Verdict

Not ready to ship yet, but nothing critical is open. The 2026-10-02
Critical is fixed, and the new Critical (R1) that this re-review found
in the fix is fixed and replay-tested. One new Major (R2) is fixed.
What remains before Ship: (a) the owner decisions on Majors 2, 3 and
4/R3. R3 matters most, because it is now the shortest path from agent
code to a long-lived credential, and its severity turns on the
reviewer PAT's scopes. (b) Verify should note that WO-0130 to WO-0132
landed after its 2026-10-10 re-verification. Their evidence is above,
and they change none of its live-dispatch obligations. (c) The live
dispatch that ADR-0077 and verification.md already require. Four
minors are deferred with reasons.

## Earlier review (2026-10-02), kept for the record

Superseded by the re-review above; nothing below is rewritten except heading depth. Its frontmatter assumptions were:

- Severity rubric, applied with no live user to arbitrate: CRITICAL — a reproducible path by which a principal other than the owner (the dispatched agent included) bypasses a human gate, lands code on main, or reaches a long-lived credential, with no owner action between cause and effect. MAJOR — a PRD success criterion or architecture contract not met, or a defect with a concrete scenario that corrupts the run's evidence or a security property the code itself claims, where an owner action or a further condition sits between cause and effect. MINOR — record or doc drift, or a bounded defect with no evidence or security consequence.
- Decision vocabulary, per the brief: every major is recorded 'open — needs owner decision'; minors are deferred with a logged reason; the one critical is 'must fix before Ship — route to Implement' and was not fixed here. This stage's only write is this file.
- Scope is the set of PRs and commits breakdown.md's rows and notes and verification.md's evidence cite as this run's own work (listed under Scope), not the repo diff since 2026-08-17. PR #567 (ADR-0074) is examined as ADJACENT: it is not this run's PR, but verification.md's gate-latency reconciliation names its bead and its side effect lands on this run's ledger rows.
- Standards: docs/standards.json holds four statements, all `status: advisory`; filtered to the domains the diff touches (factory, pipeline, eval). None of the five findings matches a statement's text, so no finding cites a slug and the enforced-statement must-fix trigger does not fire — the critical is critical on the rubric alone.
- The scopes of FACTORY_REVIEW_TOKEN and FACTORY_PAUSE_TOKEN cannot be read from this seat (only secret names list). The reviewer ACCOUNT's repo role was read live (write). Finding 4's severity is conditional on the PAT's scope and says so.
- That the dispatched agent's Bash subprocesses inherit the job's environment and git credential is taken from the action's observed behaviour in this run (attempt 5's `git push -u origin wo-0074` succeeded and `gh pr create` reached GitHub's 'not permitted to create or approve pull requests' refusal — both authenticated from the agent's shell), not from reading claude-code-action's source.
- Nothing was run live: no dispatch, no `claude` CLI, no workflow, no label. The one reproduction (finding 2) ran against a `git archive HEAD` scratch copy.

### Scope

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

### Findings

#### Critical: the agent allowlist's "push boundary" is defeated by its own `Bash(python3:*)` and `Bash(make:*)` entries

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

#### Major: ADR-0074's fix re-emitted this run's gate rows under new keys — the ledger now records the first traversal twice

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

#### Major: criterion 2 — gate labels applied by the owner's hand — is unmet on both traversals, and the dispatch guard cannot tell

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

#### Major: the review job runs the PR's own code under the reviewer PAT, and the reviewer account holds write

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

#### Minor: architecture.md's "zero new factory code — one exception" no longer describes the run

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

#### Minor: nothing refuses a work order whose payload touches `.github/workflows/`

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

### Passes with no findings

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

### Verdict

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
