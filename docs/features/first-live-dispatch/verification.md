---
stage: verify
run: feature:first-live-dispatch
date: 2026-09-25
---

# Verification: first live dispatch

## Summary

**Updated 2026-10-10 (after the Critical fix, ADR-0077):** for the shipped workflow, 5 criteria PASS on evidence the fix does not touch (1, 5, 8, 9, and the cost-report half of 7). Criterion 2 is still FAIL. Criteria 3, 4, 6 and 10, and the inert-label half of 7, have live passes only from the pre-ADR-0077 workflow and are **not re-proven**: they rest on static and local evidence until a live dispatch runs (see Re-verification 2026-10-10). Earlier verdict: **9 PASS, 1 FAIL (2026-09-28).** Criterion 4 now passes on the WO-0076 (PRD-0003 §Success criteria) re-run (see Re-verification below); criterion 2 still fails. Original verdict, kept for the record: 8 PASS, 2 FAIL across 10 criteria (PRD-0003's nine plus one breakdown acceptance no PRD criterion covers). The machinery works end to end: a real order ran from gate labels through a paid dispatch to an agent-authored PR, a human merge, `wo:merged`, and a real breaker trip, at $5.43 of the $10 bound. Two things the run existed to demonstrate are **not** demonstrated: the gates were not human-applied (delegated), and the validator hand-off has not run live and clean.

## Criteria & evidence

### Both secrets exist in Actions (`CLAUDE_CODE_OAUTH_TOKEN`, `FACTORY_PAUSE_TOKEN`), names visible in `gh secret list`

- Check: Listed the repo's Actions secret names.
- Evidence:
  ```
  $ gh secret list
  CLAUDE_CODE_OAUTH_TOKEN
  FACTORY_PAUSE_TOKEN
  ```
- Result: PASS

### The payload order's mirror issue carries the full gate history: `wo:prd-approved` and `wo:blueprint-approved` applied by Matt, then `wo:ready-for-agent`

- Check: Read #536's label timeline.
- Evidence:
  ```
  $ gh api repos/{owner}/{repo}/issues/536/timeline --paginate -q '.[]|select(.event=="labeled")|...'   # gate walk and terminal flips
  2026-09-24T04:31:31Z labeled wo:prd-approved by mattbutlerengineering
  2026-09-24T04:31:35Z labeled wo:blueprint-approved by mattbutlerengineering
  2026-09-24T04:31:39Z labeled wo:ready-for-agent by mattbutlerengineering
  2026-09-24T04:31:50Z unlabeled wo:prd-approved by github-actions[bot]
  2026-09-24T04:31:50Z unlabeled wo:blueprint-approved by github-actions[bot]
  2026-09-25T04:11:29Z labeled wo:needs-review by github-actions[bot]
  2026-09-25T04:20:46Z labeled wo:merged by github-actions[bot]
  2026-09-25T04:20:47Z unlabeled wo:needs-review by github-actions[bot]
  ```
- Result: FAIL. The gate history is complete and in order, but the three labels were not applied by Matt: the owner delegated them to the operating agent session, which applied them through the owner's `gh` login. The timeline cannot tell the two apart, so reading "by mattbutlerengineering" as a human gate review would be wrong. The delegation was owner-authorized, and it is still a deviation from what this criterion exists to demonstrate.

### An assembler run concludes `success` and the dispatched agent's PR closes the mirror issue via `Closes #N`

- Check: Read the successful dispatch's conclusion and the PR's author and first body line.
- Evidence:
  ```
  $ gh run view 36092718537 --json conclusion,event
  issues success
  $ gh pr view 545 --json author,body
  author=app/github-actions
  WO-0074 (PRD-0003 §Success criteria) — Closes #536
  ```
- Result: PASS (attempt 6 of 6; see Failures for the five that preceded it)

### The validator hand-off fires live: a `workflow_dispatch` validator run executes check + review + label jobs, and the order flips to `wo:needs-review` untouched by hands

- Check: Read both validator dispatch runs for #545 and their failing lines.
- Evidence:
  ```
  $ gh run view 36093103416 --json jobs    # automatic hand-off from the assembler
    needs-review-label failure
    check failure
    review failure
    merged-label skipped
  $ gh run view 36093103416 --log-failed | grep V:
  V: gh api pull #545 failed: gh: Resource not accessible by integration (HTTP 403)
  $ gh run view 36093426992 --json jobs    # re-fired by hand after #547
    review failure
    needs-review-label success
    check success
    merged-label skipped
  $ gh run view 36093426992 --log | grep '^review' | grep V:
  V: no pull_request in the CI event payload
  ```
- Result: FAIL. The live hand-off from the assembler (36093103416) failed on every job, on two latent defects (#546). After #547 fixed them, the hand-off was re-fired by hand (36093426992). `needs-review-label` then flipped #536 with no hand on the label, but `review` still failed: #545's branch predates #547, and with no `FACTORY_REVIEW_TOKEN` the reviewer would share the author's identity anyway.

### Matt merges the PR manually and the order reaches `wo:merged` with detector G green

- Check: Read who merged #545, #536's final state, and detector G.
- Evidence:
  ```
  $ gh pr view 545 --json mergedBy,mergedAt
  mattbutlerengineering 2026-09-25T04:20:35Z
  $ gh issue view 536 --json state,labels
  CLOSED wo:merged,size:S,type:chore
  $ python3 gates.py
  gates: 0 problem(s)
  ```
- Result: PASS

### The ledger carries the dispatched run's spend row with real nonzero token counts, committed by the workflow

- Check: Found the commit that added run 36092718537's row, and printed the row.
- Evidence:
  ```
  $ git log --format="%an | %s" -S 36092718537 -- docs/factory/costs.jsonl
  github-actions[bot] | chore(factory): run-spend row (assembler)
  $ python3 -c "import json; [print(json.dumps({k: v for k, v in json.loads(l).items() if k != 'wo'})) for l in open('docs/factory/costs.jsonl') if '36092718537' in l]"
  {"run_id": "36092718537", "model": "claude-sonnet-5", "tokens": 2813411, "cost": 1.3091811000000004, "outcome": "completed", "at": "2026-09-25"}
  ```
- Result: PASS

### The breaker fires once for real: cost-report sets `FACTORY_PAUSED=true` itself, and a subsequent ready label is inert until the flag is cleared

- Check: Read cost-report run 36094902578's verdict and the paused assembler run's conclusion.
- Evidence:
  ```
  $ gh run view 36094902578 --log | grep cr:
  cr: spend $5.43 has reached or exceeded the $0.01 monthly cap — pausing dispatch (FACTORY_PAUSED)
  $ gh run view 36094946935 --json event,conclusion
  issues skipped
  ```
- Result: PASS. The pause was set by automation, and the ready label on #536 while paused gave a `skipped` run. The flag's final clear (2026-09-25T04:35:51Z) was delegated to the operating session rather than done by Matt; that does not change what this criterion tests. `main` was deliberately red between the paired cap PRs #555 and #557, because nine tests read the real cap.

### Total run spend (dispatch + retries + breaker test) ≤ $10, readable from the ledger

- Check: Summed every workflow-recorded row in the ledger (all six are this run's dispatches; cost-report and validator runs record no spend).
- Evidence:
  ```
  $ python3 -c "import json; r = [json.loads(l) for l in open('docs/factory/costs.jsonl')]; d = [x for x in r if x['run_id'].isdigit()]; print(len(d), 'workflow-recorded runs, total $%.2f' % sum(x['cost'] for x in d))"
  6 workflow-recorded runs, total $5.43
  ```
- Result: PASS ($5.43)

### The J-roster fix lands correct: gates.py's docstring and DETECTORS table agree J is claimed, pinned by the battery

- Check: Read the DETECTORS J entry and ran the full battery at 48d29a0.
- Evidence:
  ```
  $ grep -n '"J":' gates.py
  1678:    "J": ("LABEL-WIRING", "gates.py", "offline"),
  $ python3 -m unittest discover tests
  Ran 1791 tests in 20.336s
  OK
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS (landed via #516 on the amended scope, not by a dispatch; see breakdown.md's 2026-09-22 note)

### Breakdown-only: the assembler accepts either credential (the either-credential acceptance, PRD-0003 §Success criteria)

- Check: Confirmed no ANTHROPIC_API_KEY secret exists, that the credential guards accept either, and that the agent step succeeded on OAuth alone.
- Evidence:
  ```
  $ gh secret list
  CLAUDE_CODE_OAUTH_TOKEN
  FACTORY_PAUSE_TOKEN
  $ grep -n "claude_code_oauth_token:\|CLAUDE_CODE_OAUTH_TOKEN != ''" .github/workflows/assembler.yml
  99:          && (env.ANTHROPIC_API_KEY != '' || env.CLAUDE_CODE_OAUTH_TOKEN != '')
  113:          && (env.ANTHROPIC_API_KEY != '' || env.CLAUDE_CODE_OAUTH_TOKEN != '')
  121:          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
  207:          && (env.ANTHROPIC_API_KEY != '' || env.CLAUDE_CODE_OAUTH_TOKEN != '')
  $ gh run view 36092718537 --json jobs -q '...select(.name=="Run the chartered agent")'
  step: Run the chartered agent success
  ```
- Result: PASS

## Re-verification (2026-09-28)

A second traversal, rows WO-0075 and WO-0076 (PRD-0003 §Success criteria), mirror #574, re-tested the two failed criteria with a PR opened after #547's fix and a separate reviewer identity (`FACTORY_REVIEW_TOKEN`, login `mattbutlerengineeringreviewer`).

### The validator hand-off fires live: check + review + label jobs, flip untouched by hands (re-run)

- Check: read the automatic validator dispatch for the agent's PR #579, the review comment's author, and #574's flip. No hand re-fire happened.
- Evidence:
  ```
  $ gh run view 36474781292 --json conclusion     # the dispatch
  success
  $ gh run view 36475022721 --json createdAt,jobs  # automatic hand-off
  created 2026-09-28T19:50:34Z
    check success
    needs-review-label success
    review success
    merged-label skipped
  $ gh pr view 579 --json comments -q '.comments[]|.author.login'
  mattbutlerengineeringreviewer
  $ gh api repos/{owner}/{repo}/issues/574/timeline --paginate -q '...'   # the flip
  2026-09-28T19:50:43Z unlabeled wo:in-progress by github-actions[bot]
  2026-09-28T19:50:43Z labeled wo:needs-review by github-actions[bot]
  ```
- Result: PASS. It now supersedes the FAIL recorded for this criterion above.

### The mirror issue carries the full gate history, applied by Matt (re-run)

- Check: read #574's gate labels.
- Evidence:
  ```
  2026-09-28T19:48:17Z unlabeled wo:draft by mattbutlerengineering
  2026-09-28T19:48:17Z labeled wo:prd-approved by mattbutlerengineering
  2026-09-28T19:48:21Z unlabeled wo:prd-approved by mattbutlerengineering
  2026-09-28T19:48:22Z labeled wo:blueprint-approved by mattbutlerengineering
  2026-09-28T19:48:27Z labeled wo:ready-for-agent by mattbutlerengineering
  2026-09-28T19:48:27Z unlabeled wo:blueprint-approved by mattbutlerengineering
  ```
- Result: FAIL, again. The history is complete, in order, and this time replaces each queue label (ADR-0032), but the owner again delegated the labels to the operating session. A future traversal where the owner applies them by hand still owes this criterion.

Also on record for this re-run: the owner merged #579 **by hand** (2026-09-28T20:32:39Z), and the merged-label job flipped #574 to `wo:merged`. The dispatch's spend row is workflow-committed (868,393 tokens, $0.47), so the six-plus-one dispatch total is $5.90, still within the $10 bound. `one_owner.py` no longer reports the duplicated `ROOT`.

## Re-verification (2026-10-10): after the Critical finding's fix

Review's Critical finding routed back to Implement, which landed
Milestone E: WO-0128 (PRD-0003 §Success criteria) splits assembler.yml
into `dispatch`, `agent` and `deliver` jobs, and WO-0129 (PRD-0003
§Success criteria) keeps only the execution file's result entry and
scrubs the agent's subprocess environment (ADR-0077). This pass verifies
the tree that will ship: the branch `fix/fld-allowlist-boundary` with
`origin/main` merged in (merge commit `4794e76`; the one conflict was
the ADR index, resolved by keeping both the 0076 and 0077 rows in
order; `factory_init.py update-manifest` was a no-op).

No live dispatch ran in this pass. Every criterion's earlier evidence
came from live runs that cannot be repeated here (paid, and the owner
must apply the labels). So each criterion below says whether that
evidence still stands for the shipped workflow, or rested on a workflow
this change rewrote and now has only static and local evidence.

### Per-criterion state

| # | Criterion | Depends on the rewritten workflow? | State now |
|---|---|---|---|
| 1 | Both secrets exist | No | PASS. `gh secret list` today shows `CLAUDE_CODE_OAUTH_TOKEN`, `FACTORY_PAUSE_TOKEN`, `FACTORY_REVIEW_TOKEN` |
| 2 | Gate labels applied by Matt | No (owner act) | **FAIL, open.** Unchanged owner-only proof obligation |
| 3 | Assembler run concludes `success`; agent PR closes the issue | **Yes.** The push and `gh pr create` moved from the agent to the `deliver` job | Live PASS is historical, from the pre-ADR-0077 workflow. **Not re-proven.** Static and local evidence only (below) |
| 4 | Validator hand-off fires live, flip untouched | **Yes.** find-pr and `gh workflow run` moved to `deliver` | Live PASS (2026-09-28) is historical. **Not re-proven.** Static only. `validator.yml` is unchanged |
| 5 | Matt merges; `wo:merged`; detector G green | No. The merge is human and the merged-label job is in the unchanged `validator.yml` | PASS stands. `gates: 0 problem(s)` on the merged tree |
| 6 | Workflow-committed spend row, nonzero tokens | **Yes.** It now reads a jq-filtered `execution.json` in `deliver` | Live PASS is historical. **Not re-proven live.** The filter and `make wo-record` were run locally on a fixture (below) |
| 7 | Breaker fires; ready label inert while paused | Partly. `cost-report.yml` is unchanged, but the pause term now sits on the `dispatch` job's `if:` | The live trip stands. Whether a label is inert under the new job graph is **static only**: `vars.FACTORY_PAUSED != 'true'` is on `dispatch` (line 54); `agent` needs `transitioned == 'true'`; `deliver` is `always() && transitioned == 'true'` |
| 8 | Total run spend ≤ $10 | No (ledger) | PASS. 7 workflow-recorded runs, **$5.91** today. The 2026-09-28 note's "$5.90" summed two rounded figures; the ledger sum is $5.91 |
| 9 | J-roster fix | No | PASS. `gates.py:1678 "J": ("LABEL-WIRING", ...)`; battery green |
| 10 | Breakdown-only: the assembler accepts either credential | **Yes.** The guards moved | **Static only.** Both secrets are in `dispatch`'s job env (lines 71–72). The claim step is gated on either one (line 108). The agent step gets both as action inputs (lines 162–163) and gets them nowhere else in its job. `agent` and `deliver` run only on a true claim |

Tally for the shipped tree: 5 PASS on evidence this change does not
touch (1, 5, 8, 9, plus the cost-report half of 7). 1 FAIL (2). 4
criteria (3, 4, 6, 10) plus the inert-label half of 7 have historical
live passes from a workflow that no longer exists, and only static and
local evidence for the one that ships. They are recorded as **not
re-proven**, not as PASS.

### The fix, statically

Both copies are byte-identical, and the repo's own permissions parser
reads the same grants from each:

```
$ cmp .github/workflows/assembler.yml factory/templates/.github/workflows/assembler.yml && echo IDENTICAL
IDENTICAL
$ python3 -c "...from test_workflow_permissions import job_permissions..."
.github/workflows/assembler.yml {'dispatch': {'contents': 'read', 'issues': 'write'}, 'agent': {'contents': 'read'}, 'deliver': {'contents': 'write', 'pull-requests': 'write', 'issues': 'write', 'actions': 'write'}}
factory/templates/.github/workflows/assembler.yml {<same>}
```

(The workflow-level default is `contents: read`.) Where each secret and
token is used, and where the pushes happen:

```
dispatch: 71:  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}           (job env)
dispatch: 72:  CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }} (job env)
dispatch: 110: GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}                         (claim step)
agent:    160: uses: anthropics/claude-code-action@86180fa9e4d311eed10c9cc49854c53dab5d517a
agent:    162-164: anthropic_api_key / claude_code_oauth_token / github_token  (inputs to that one step)
agent:    140: CLAUDE_CODE_SUBPROCESS_ENV_SCRUB: "1"                          (job env)
deliver:  259, 324, 329, 350: GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
deliver:  264: git push origin "refs/heads/$BRANCH:refs/heads/$BRANCH"
deliver:  310: git -C "$RUNNER_TEMP/spend" push origin HEAD:main          (spend row, from a fresh origin/main worktree)
```

Only the `agent` job runs the claude action. That job holds
`contents: read` and no other grant, and no Anthropic secret sits in its
job env. Both pushes are in `deliver`, whose checkout is `GITHUB_SHA`
and which only fetches the agent's branch ref, never checks it out.
The agent's allowlist (line 178) names no `git push` and no `gh pr`.

actionlint 1.7.12 is installed, with shellcheck on PATH, so the `run:`
scripts were shellchecked too:

```
$ actionlint .github/workflows/assembler.yml factory/templates/.github/workflows/assembler.yml; echo "exit=$?"
exit=0
$ actionlint; echo "all-exit=$?"     # every workflow in .github/workflows
all-exit=0
```

Not checkable offline: how the runner evaluates expressions (`always()`,
job outputs from a failed `agent` job, the default `success()` on
`deliver`'s steps), and artifact upload and download across jobs.

### Implement's source claims, checked against the pinned action

Read from `anthropics/claude-code-action` at
`86180fa9e4d311eed10c9cc49854c53dab5d517a` (committed 2026-08-04),
fetched with `git fetch --depth 1` into a scratch directory.

- **Agent mode writes the `github_token` into the origin URL. Confirmed.**
  `src/modes/agent/index.ts:46` and `:60` call `await configureGitAuth(githubToken, context, user);`.
  In `src/github/operations/git-config.ts`, the
  `if (process.env.ALLOWED_NON_WRITE_USERS)` branch at :54 uses a
  credential helper instead. The `else` branch, which this workflow
  takes because it sets no `allowed_non_write_users`, runs:
  `:78 const remoteUrl = \`https://x-access-token:${githubToken}@${serverUrl.host}/...\`;`
  `:79 await $\`git remote set-url origin ${remoteUrl}\`;`
  So `persist-credentials: false` on the checkout would not take the
  token away from the agent.
- **run.ts exports the token to the agent process. Confirmed.**
  `src/entrypoints/run.ts:184 // Set GITHUB_TOKEN and GH_TOKEN in process env for downstream usage`,
  `:185 process.env.GITHUB_TOKEN = githubToken;`,
  `:186 process.env.GH_TOKEN = githubToken;`. This is unconditional,
  after `setupGitHubToken()` at :172.
- **`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` is documented and reaches the CLI from the job env. Confirmed.**
  `docs/security.md:16`: "When set, Claude does a best-effort scrub of
  Anthropic, cloud, and GitHub Actions secrets from subprocess
  environments. On Linux runners with bubblewrap available, subprocesses
  additionally run with PID-namespace isolation. This reduces but does
  not eliminate prompt injection risk ..."
  `action.yml:290`: `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB: ${{ env.CLAUDE_CODE_SUBPROCESS_ENV_SCRUB || (inputs.allowed_non_write_users != '' && '1') || '' }}`,
  which reads the job env this workflow sets. The bubblewrap install
  (`action.yml`, the step gated at :217 on
  `inputs.allowed_non_write_users != ''`) does **not** run here, so the
  scrub carries no PID isolation. That matches the workflow comment at
  lines 133–140.
- **Not confirmed from source:** whether the Claude Code CLI applies the
  scrub to Bash tool subprocesses. That behaviour is in the CLI, not in
  this action, and was not read. Also unconfirmed: whether the
  write-permission check passes with a read-only token.
  `src/github/validation/permissions.ts:82` calls
  `getCollaboratorPermissionLevel` with this token, and only a live run
  shows whether `contents: read` can make that call. It is guarded by
  `isEntityContext` (`run.ts:189`), which an `issues` event satisfies.

### The bundle hand-off, run locally with the workflow's literal commands

The script is in the session scratchpad. It runs under `bash -euo
pipefail` (a runner's `run:` uses bash, not zsh). It models
actions/checkout@v4's fetch for the agent job (`git init`, then
`fetch --depth=1 origin +$SHA:refs/remotes/origin/main`, then
`checkout --force -B main`). It makes two commits on a `wo-` branch and
runs the package step's `git bundle create` and `cp` verbatim. Then it
makes a non-shallow clone for `deliver` (`fetch-depth: 0`) and runs the
deliver step's `git fetch` and `git push` verbatim against a local bare
origin. `gh pr create` was not run. Only its `--title` expansion was
evaluated.

```
agent clone shallow boundary: 736f54bc3ef6a7c8e0da414ab0cfbc23a8ef8ec6  commits visible: 1
agent tip=bea47239616352550c8f8de7763bd2d736a6066a
bundle heads:
bea47239616352550c8f8de7763bd2d736a6066a refs/heads/wo-0129
deliver clone shallow? false
 * [new branch]      wo-0129    -> wo-0129          (git fetch "$HANDOFF/handoff.bundle" "refs/heads/$BRANCH:refs/heads/$BRANCH")
 * [new branch]      wo-0129 -> wo-0129             (git push origin "refs/heads/$BRANCH:refs/heads/$BRANCH")
origin wo-0129=bea47239616352550c8f8de7763bd2d736a6066a  equals agent tip: yes
PR title would be: docs: second agent commit
deliver HEAD still main@736f54b == GITHUB_SHA: yes
```

The empty case: an agent that commits nothing.

```
fatal: Refusing to create empty bundle.
no commits on wo-0998 to hand off           (package step exits 0, as written)
fatal: '.../handoff.bundle' does not appear to be a git repository
deliver fetch exit=128                      (the deliver step fails, so "Mark the work order failed" fires)
```

This reproduces breakdown Note 2026-10-10 item (3) on this machine's git
2.50.1, not on a runner's git.

### The kept-record filter, run on a fixture

`KEEP` was taken from the YAML folded scalar (lines 194–198, joined
with spaces, as `>-` folds) and run with the step's literal
`jq "$KEEP" "$EXECUTION_FILE"`. The fixture is a five-entry execution
log. A fake `sk-ant-oat01-FAKETOKEN...` value appears three times: in a
tool result, in an assistant text turn, and in the result entry's
`result` text.

```
KEEP=(if type == "array" then . else [.] end) | map(select(type == "object" and .type == "result")) | last | [{type, subtype, is_error, num_turns, total_cost_usd, usage, permission_denials}]
fixture token occurrences:        3
jq exit=0
kept token occurrences: 0
read_execution: ((868393, 0.4712), None)
object-form kept keys: ['is_error', 'num_turns', 'permission_denials', 'subtype', 'total_cost_usd', 'type', 'usage']
$ make -s wo-record WO=WO-0129 RUN_ID=999000111 MODEL=claude-sonnet-5 FILE=<kept execution.json> OUTCOME=completed   # in a git-archive scratch copy
budget_guard: 0 problem(s)
{"wo": "WO-0129", "run_id": "999000111", "model": "claude-sonnet-5", "tokens": 868393, "cost": 0.4712, "outcome": "completed", "at": "2026-10-10"}
```

A residual, recorded rather than fixed (Verify does not fix code):
`permission_denials` keeps each denied call's `tool_input` verbatim. A
denied command whose text contains a secret value survives the filter.
With a denied `curl -H "Authorization: Bearer sk-ant-oat01-FAKETOKEN..."`
added to the fixture, the kept file holds the token once. The agent has
to have obtained the value first, which the scrub is meant to stop. So
this is defence in depth that the filter does not add, not a regression.

### Battery (merged tree, `4794e76`)

```
$ python3 -m unittest discover tests 2>&1 | grep -E "^(Ran|OK|FAILED)"
Ran 1967 tests in 26.816s
OK
$ python3 lint.py
lint: 0 problem(s) across 25 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
```

`tests/test_assembler.py::TestAgentCredentialBoundary` (10 tests,
including `test_no_write_scoped_job_runs_the_agent`,
`test_the_one_push_is_the_order_branch_from_the_deliver_job` and
`test_the_agent_job_hands_no_credential_to_its_shell`) passes in that
run.

### What only a live dispatch can prove

From breakdown.md's 2026-10-10 note. None of these was observed in this
pass:

1. claude-code-action's write-permission check on the owner passes with
   the `agent` job's read-only token.
2. `deliver`'s default-condition steps run after a failed `agent` job
   under its `if: always()`, and the failed job's outputs
   (`execution_file`, `outcome`) reach `deliver`.
3. The bundle cut in the agent's shallow checkout fetches into
   `deliver`'s full clone on a runner. This pass reproduced it locally,
   not on a runner.
4. The subprocess scrub reaches the agent's Bash from the job env, so a
   Bash `env` shows no Anthropic credential. The action passes the
   variable through (`action.yml:290`). The CLI's behaviour was not
   read.
5. The pushed branch, the opened PR, find-pr, the validator hand-off and
   the spend row all land as they did for #545.

Until a dispatch shows these, criteria 3, 4, 6 and 10, and the inert
half of 7, are **not re-proven** for the shipped workflow.

## Addendum (2026-10-10, after re-review)

The re-verification above ran on `3613ed4`. The re-review then found R1,
R2 and R4, and Implement landed three fixes: `84b4abf` (WO-0130, PRD-0003
§Success criteria), `1109b1e` (WO-0131, PRD-0003 §Success criteria) and
`a333300` (WO-0132, PRD-0003 §Success criteria). This addendum checks
those three commits on the branch tip `939d9c0`. No live dispatch ran,
so the per-criterion table above does not change.

### What changed since the re-verification

```
$ git diff 3613ed4..HEAD --stat
 .github/workflows/assembler.yml                    |  18 +-
 assembler.py                                       |  11 +-
 ...e-dispatched-agent-holds-no-write-credential.md |  29 +-
 docs/factory/costs.jsonl                           |   3 +
 docs/features/first-live-dispatch/breakdown.md     |   6 +
 docs/features/first-live-dispatch/review.md        | 341 +++++++++++++++++++--
 factory/manifest.json                              |   4 +-
 factory/templates/.github/workflows/assembler.yml  |  18 +-
 factory/templates/tools/factory/assembler.py       |  11 +-
 tests/test_assembler.py                            | 136 +++++++-
 tests/test_gates.py                                |   2 +-
 11 files changed, 532 insertions(+), 47 deletions(-)
```

The workflow change is two command lines plus comments. The deliver
fetch gains `--no-tags`, and the spend-row worktree names
`refs/remotes/origin/main` instead of `origin/main`. `assembler.py` adds
`isCrossRepository` to the listing and a skip in `pr_for_issue`.

### R1 (WO-0130): the tag attack, replayed on old and new lines

A script (session scratchpad) pulled the deliver step's
`git fetch ... handoff.bundle` line and the spend-row step's whole
`run:` block out of the old (`git show 3613ed4:`) YAML and the new YAML
by text. Each extract ran under `bash -e`. The extracted lines:

```
old fetch: git fetch "$HANDOFF/handoff.bundle" "refs/heads/$BRANCH:refs/heads/$BRANCH"
new fetch: git fetch --no-tags "$HANDOFF/handoff.bundle" "refs/heads/$BRANCH:refs/heads/$BRANCH"
old spend: git worktree add "$RUNNER_TEMP/spend" origin/main
new spend: git worktree add "$RUNNER_TEMP/spend" refs/remotes/origin/main
```

Each spend block also has the step's `git config`, `git fetch origin
main`, `tail -n 1 ... >>`, `add`, `commit` and `push origin HEAD:main`
lines, unchanged. Setup, per case: a local bare `origin` with one `base`
commit, and an agent clone that commits `evil` on `wo-0130` and tags
it `origin/main`. The packaging step's literal `git bundle create
"$HANDOFF/..." "refs/heads/$BRANCH" "^$GITHUB_SHA"` carries only the
branch. The attack in review R1 assumes the agent owns the hand-off
and ships its own bundle, so the replayed bundle adds
`refs/tags/origin/main` to that same command. The deliver side is a
full clone of origin, with one line appended to `costs.jsonl` in place
of `make wo-record`. git 2.50.1 (Apple Git-155), locally, not on a
runner.

```
[OLD] origin main BEFORE: e7d029c18d131caac92ba7a0241fbaf93340b5a4 (base)
[OLD] workflow-literal bundle heads: refs/heads/wo-0130
[OLD] agent-crafted bundle heads: refs/heads/wo-0130 refs/tags/origin/main
[OLD]   fetch:  * [new branch]      wo-0130     -> wo-0130
[OLD]   fetch:  * [new tag]         origin/main -> origin/main
[OLD]   spend: warning: refname 'origin/main' is ambiguous.
[OLD]   spend: HEAD is now at e295c09 evil
[OLD]   spend:    e7d029c..30f8b28  HEAD -> main
[OLD] origin main AFTER: 30f8b2828c9eb341fdc7e05b7f799895a5ea7fe1
[OLD] origin main log: chore(factory): run-spend row (assembler)|evil|base|
[OLD] RESULT: agent commit e295c099e11cc62bc12c2956b6ad3ad0cadf230b IS on main

[NEW] origin main BEFORE: b103a7dd00bafa376785cb08cb326d5b85bdd85d (base)
[NEW] agent-crafted bundle heads: refs/heads/wo-0130 refs/tags/origin/main
[NEW]   fetch:  * [new branch]      wo-0130    -> wo-0130
[NEW] tags in deliver clone:
[NEW]   spend: HEAD is now at b103a7d base
[NEW]   spend:    b103a7d..0349337  HEAD -> main
[NEW] origin main AFTER: 03493374a7582b2325c0d3b43714e151e7faa6ff
[NEW] origin main log: chore(factory): run-spend row (assembler)|base|
[NEW] RESULT: agent commit NOT on main; main~1 == base: yes
```

Each guard was also checked alone, by mixing the extracts:

```
[OLDFETCH+NEWSPEND] fetch: * [new tag] origin/main -> origin/main   (tag lands)
[OLDFETCH+NEWSPEND] spend: HEAD is now at 7b62f13 base
[OLDFETCH+NEWSPEND] origin main log: chore(factory): run-spend row (assembler)|base|
[NEWFETCH+OLDSPEND] tags in deliver clone:                          (no tag)
[NEWFETCH+OLDSPEND] spend: HEAD is now at 0c423a3 base
[NEWFETCH+OLDSPEND] origin main log: chore(factory): run-spend row (assembler)|base|
```

The old lines put the agent's commit on `main` under a spend-row
commit. The new lines don't, and neither does either guard alone, which
matches review.md's claim. In the three non-attack cases the script's
ancestry check printed `fatal: Not a valid commit name <evil sha>`
before its RESULT line. That is expected: the replay never pushes the
order branch, so the agent's commit does not exist in origin at all.

### R2 (WO-0131): find-pr on a fork PR, from fixtures

The workflow step is `run: make find-pr ISSUE=${{
github.event.issue.number }}`, which runs `python3 assembler.py find-pr
$(ISSUE)`. It is the same command here. A fake `gh` on `PATH` logged
its arguments and printed a fixture listing (newest first, as gh
answers):

```
gh invoked as: gh pr list --state open --json number,body,isCrossRepository --limit 1000
```

| Fixture (issue #42) | `$GITHUB_OUTPUT` | exit |
|---|---|---|
| #902 `isCrossRepository: true` "Closes #42", then #901 `false` "Closes #42" | `pr=901`, `looked=true` | 0 |
| #902 `true` "Closes #42" only | `pr=`, `looked=true`; "no open PR closes issue #42" | make: 2 |
| #903 with no `isCrossRepository` key, then #901 `false` | `pr=901`, `looked=true` | 0 |
| #903 with no `isCrossRepository` key only | `pr=`, `looked=true`; "no open PR closes issue #42" | make: 2 |
| first row, old `assembler.py` from `3613ed4` | `pr=902` (the fork) | 0 |

Only the same-repo PR is picked. A PR whose listing entry has no
`isCrossRepository` key is skipped (fails closed: the check is `is not
False`). With no other match, find-pr exits nonzero and the order goes
to `wo:failed`, as for any untraceable delivery. The old code handed
the fork's #902 to the validator.

### WO-0132: the step-wide secret pin

```
$ python3 -m unittest tests.test_assembler.TestAgentCredentialBoundary tests.test_assembler.TestBundleCannotReachMain
Ran 13 tests in 0.618s
OK
```

Mutation: one line, `PAUSE: ${{ secrets.FACTORY_PAUSE_TOKEN }}`, added
to the env of the agent job's "Package the agent's hand-off" step.

```
FAIL: test_the_agent_job_names_no_secret_but_the_action_inputs
AssertionError: Lists differ: ['PAUSE: ${{ secrets.FACTORY_PAUSE_TOKEN }}[164 chars] }}'] != ['anthropic_api_key: ${{ secrets.ANTHROPIC_[119 chars] }}']
Ran 11 tests in 0.005s
FAILED (failures=1)
$ git checkout -- .github/workflows/assembler.yml; git diff
(empty)
```

After the restore the class passes again (`OK`).

### Mirrors, actionlint, battery, manifest (tip `939d9c0`)

```
$ cmp .github/workflows/assembler.yml factory/templates/.github/workflows/assembler.yml
assembler.yml copies byte-identical
21c9dd77b337be7123957ddf7e4ff574c56992ad666ae309b841e15bf6c91c6d  (both)
$ actionlint .github/workflows/assembler.yml factory/templates/.github/workflows/assembler.yml
actionlint exit=0
$ python3 -m unittest discover tests 2>&1 | grep -E "^(Ran|OK|FAILED)"
Ran 1971 tests in 27.139s
OK
$ python3 lint.py
lint: 0 problem(s) across 25 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)
$ git diff --stat
(empty)
```

### Criteria

No change. R1, R2 and R4 are fixed, and the fixes are replayed or
mutation-tested locally. Criteria 3, 4, 6 and 10, and the inert-label
half of 7, are still **not re-proven** until a live dispatch runs (see
"What only a live dispatch can prove"). Criterion 2 is still FAIL. The
replays above ran against local repos on this machine's git, not on a
runner with GitHub as origin.

## Failures

- **Criterion 2 (human gate labels).** Not recoverable for this order: #536 is merged, and re-labeling it proves nothing. Route: a future dispatch where the owner applies the three labels by hand. Carry it as an open proof obligation into Review and Ship; no Implement work fixes it.
- **Criterion 4 (live validator hand-off).** Route back to Implement. Two prerequisites: (1) a `FACTORY_REVIEW_TOKEN` secret for a reviewer login that never authors PRs (an owner action, since only the owner can create that credential); (2) one fresh dispatch whose PR is opened after #547, so the automatic hand-off runs the fixed shims without a hand re-fire.
- **Not re-proven (2026-10-10), not a FAIL:** criteria 3, 4, 6 and 10, and the inert half of 7, after the ADR-0077 rewrite. The route is one live dispatch, which needs the owner's labels and real spend. It can be the same dispatch that discharges criterion 2.
- **Also on record, not a criterion failure:** criterion 3 took six dispatches ($5.43 total). Attempts 1-5 failed on the missing `--allowedTools` (#539; #540, #541, #542), the `GITHUB_TOKEN` being unable to push workflow files (payload re-scoped, #544), and the repo setting that blocked Actions from opening PRs (enabled by the owner). Each fix is merged.

## Gate-latency reconciliation (added 2026-09-26)

The ledger's first-ever prd and blueprint gate rows overstate the human
wait. `human_gates` ends a stay when the gate's queue label is removed.
The delegated gate walk applied each pass label with `gh issue edit
--add-label` and never removed the queue label, which breaks ADR-0032's
one-lifecycle-label rule. So `wo:draft` and `wo:prd-approved` stayed on
until the claim step stripped both at 04:31:50Z.

```
$ grep '"gate_wait:\(prd\|blueprint\)' docs/factory/costs.jsonl | grep -o '"outcome": "[^"]*"'
"outcome": "gate_wait:prd:1399s"
"outcome": "gate_wait:blueprint:19s"
$ gh api repos/{owner}/{repo}/issues/536/timeline --paginate -q '...'   # the relevant flips
2026-09-24T04:08:31Z labeled wo:draft by mattbutlerengineering
2026-09-24T04:31:31Z labeled wo:prd-approved by mattbutlerengineering
2026-09-24T04:31:35Z labeled wo:blueprint-approved by mattbutlerengineering
2026-09-24T04:31:50Z unlabeled wo:draft by github-actions[bot]
2026-09-24T04:31:50Z unlabeled wo:prd-approved by github-actions[bot]
```

| Gate | Recorded | Queue label on → pass label on | Overstated by |
|---|---|---|---|
| prd | 1,399s | 1,380s (04:08:31 → 04:31:31) | 19s |
| blueprint | 19s | 4s (04:31:31 → 04:31:35) | 15s |

The merge row (558s: `wo:needs-review` on at 04:11:29, off at 04:20:47)
is correct, because the automated flips keep one lifecycle label. The
ledger is append-only, so the two rows stand as recorded and this section
is the correction. The error is small here but structural: a pass label
added days before the queue label is removed would fold the next gate's
wait into this one, and ADR-0069's metric divides by these rows. A
structural fix is filed as a bead; this run does not implement it.

## Not verified

- **Secret values and provenance** (criterion 1): only the names are checked. That the values were console-set and never in the repo rests on the arming procedure, not on a check here.
- **Review job behavior on a post-#547 PR** has not been observed at all (see Failures, criterion 4). (Superseded 2026-09-28: observed on #579.)
- **The ADR-0077 workflow on a runner** (2026-10-10): no live dispatch has run the three-job assembler. The five items under "What only a live dispatch can prove" are open. Criteria 3, 4, 6 and 10, and the inert half of 7, are not re-proven until one does.
