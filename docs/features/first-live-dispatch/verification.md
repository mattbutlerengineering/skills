---
stage: verify
run: feature:first-live-dispatch
date: 2026-09-25
---

# Verification: first live dispatch

## Summary

**Updated 2026-09-28: 9 PASS, 1 FAIL.** Criterion 4 now passes on the WO-0076 (PRD-0003 §Success criteria) re-run (see Re-verification below); criterion 2 still fails. Original verdict, kept for the record: 8 PASS, 2 FAIL across 10 criteria (PRD-0003's nine plus one breakdown acceptance no PRD criterion covers). The machinery works end to end: a real order ran from gate labels through a paid dispatch to an agent-authored PR, a human merge, `wo:merged`, and a real breaker trip, at $5.43 of the $10 bound. Two things the run existed to demonstrate are **not** demonstrated: the gates were not human-applied (delegated), and the validator hand-off has not run live and clean.

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

## Failures

- **Criterion 2 (human gate labels).** Not recoverable for this order: #536 is merged, and re-labeling it proves nothing. Route: a future dispatch where the owner applies the three labels by hand. Carry it as an open proof obligation into Review and Ship; no Implement work fixes it.
- **Criterion 4 (live validator hand-off).** Route back to Implement. Two prerequisites: (1) a `FACTORY_REVIEW_TOKEN` secret for a reviewer login that never authors PRs (an owner action, since only the owner can create that credential); (2) one fresh dispatch whose PR is opened after #547, so the automatic hand-off runs the fixed shims without a hand re-fire.
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
- **Review job behavior on a post-#547 PR** has not been observed at all (see Failures, criterion 4).
