---
stage: verify
run: maintenance:the-reviewer-token-runs-agent-code
date: 2026-10-10
assumptions:
  - "No PRD of its own: the success criterion is defect.md's Expected clause (a maintenance run), plus breakdown.md's acceptance criteria for rows 0133 to 0145, all checked. No soft-gate gap."
  - "Independence: the static read parses both workflow copies with Ruby's Psych YAML parser (a real YAML parser, not the suite's hand-parse helpers), and the hostile replay is a throwaway script written for this stage in the session scratchpad, not a re-run of tests/test_validator_workflow.py. Neither script is committed: they are evidence generators, and the suite already owns the regression pins."
  - "GitHub's runtime is emulated, not run: steps execute under `bash --noprofile --norc -e` (GitHub's shell for a run: with no shell:), $GITHUB_OUTPUT is parsed with GitHub's documented name<<delim grammar, and CHECK_RC is computed from a stated check result the way its expression reads. What only a runner can prove is listed under Not verified."
  - "origin/main had not moved: `git fetch origin` then `git merge-base --is-ancestor origin/main HEAD` held (origin/main 41f3266, already merged), so no merge commit was needed."
---

# Verification: the reviewer token never meets agent code

Commands run in `.claude/worktrees/reviewer-token` on `fix/reviewer-token-boundary`
at 755dc8c. Output is quoted, not summarised.

## Summary

7 criteria, 7 PASS, 0 FAIL. Statically and in replay, the defect's Expected
clause holds. No step that runs the PR's code holds the reviewer PAT or a
write-scoped token. The PAT reaches one step, in a job that checks out base.
That job takes the findings as inert, bounded data, and its verdict comes from
the check's result. The parts that only a runner can prove are listed under
Not verified and are handed to the owner's combined post-merge live dispatch.
None of them is claimed here. ADR-0098 stays `provisional`.

## Criteria & evidence

### V1. Expected, statically: PR code runs only in a read-only job; the PAT sits in one base-code step

- Check: `git fetch origin`; both `validator.yml` copies compared with `cmp`;
  each copy parsed with Ruby/Psych to JSON, the two parses compared, then
  walked job by job (checkout ref, persist-credentials, grants, secrets per
  step, whether a `run:` invokes `make` or contains `${{`); `actionlint` on
  both copies.
- Evidence:
  ```
  origin/main already merged            (origin/main 41f3266, HEAD 755dc8c)
  cmp .github/workflows/validator.yml factory/templates/.github/workflows/validator.yml -> cmp_rc=0
  parsed-identical
  == job check
    needs: None | permissions: {'contents': 'read', 'pull-requests': 'read'}
    [0] actions/checkout@v4
        checkout ref="${{ github.event_name == 'workflow_dispatch' && format('refs/pull/{0}/head', inputs.pr) || '' }}" persist-credentials=False
    [2] Synthesize the PR event payload   secrets=['GITHUB_TOKEN']  run make=True has${{=False
    [3] Detectors and tests               run make=True has${{=False
    [4] Hand the findings to the review job   run make=False has${{=False
  == job review
    needs: check | permissions: {'contents': 'read', 'pull-requests': 'write'}
    [0] actions/checkout@v4
        checkout ref="${{ github.event_name == 'pull_request' && github.event.pull_request.base.sha || github.sha }}" persist-credentials=False
    [2] Synthesize the PR event payload   secrets=['GITHUB_TOKEN']  run make=True has${{=False
    [3] Write the handed-over findings    run make=False has${{=False   env: ['HANDED_OVER']
    [4] Post findings as a non-authoring actor
        secrets=['FACTORY_REVIEW_TOKEN', 'GITHUB_TOKEN']  run make=True has${{=False
  == job needs-review-label
    needs: None | permissions: {'contents': 'read', 'issues': 'write', 'pull-requests': 'read'}
    [0] actions/checkout@v4
        checkout ref="${{ github.event_name == 'pull_request' && github.event.pull_request.base.sha || github.sha }}" persist-credentials=False
    [2] Synthesize the PR event payload   secrets=['GITHUB_TOKEN']  run make=True
    [3] Flip the work order to wo:needs-review  secrets=['GITHUB_TOKEN']  run make=True
  == job merged-label
    needs: None | permissions: {'contents': 'read', 'issues': 'write'}
    [0] actions/checkout@v4   checkout ref='<default>' persist-credentials='<default true>'
    [2] Flip the work order to wo:merged  secrets=['GITHUB_TOKEN']  run make=True
  actionlint .github/workflows/validator.yml factory/templates/.github/workflows/validator.yml -> actionlint_rc=0
  ```
- Reading, per job:
  - `check` is the only job whose checkout can be PR-controlled: the PR head
    on dispatch, or the default merge ref on `pull_request`. Its grants are
    read-only. It names no secret but `GITHUB_TOKEN`, and its checkout leaves
    no credential in `.git/config`.
  - `review` and `needs-review-label` check out base (`base.sha` or
    `github.sha`), with `persist-credentials: false`.
  - `FACTORY_REVIEW_TOKEN` appears in exactly one step: `review`'s post step.
    That step runs `make` from the base tree and does not carry the
    handed-over text.
  - `merged-label` keeps the default checkout with write, as scoped. It runs
    only on `closed` + `merged`, so the code is already past the human merge
    gate (architecture.md assumptions).
- Result: PASS

### V2. Hostile hand-off replay (independent): nothing executes, the body is fenced and bounded, the verdict comes from the result

- Check: the scratchpad script `vrt/replay.py` was written for this stage.
  It reads the step scripts out of the Psych parse and runs them under
  `bash --noprofile --norc -e`.
  - **Case A**, the honest producer: `check`'s hand-off step, then
    `$GITHUB_OUTPUT` parsed by GitHub's grammar, then `HANDED_OVER`.
  - **Case B**, a poisoned hand-off: `HANDED_OVER` set directly. Same-job
    `$GITHUB_ENV` poisoning lets `check`'s code choose this value outright,
    so the trusted side must hold against arbitrary text.
  - **Case C**, text that claims FAIL while the check succeeded.
  - **Case D**, non-UTF-8 bytes.

  Each case then runs `review`'s write step, then its post step: the base
  tree's real `make review FINDINGS=… STATUS="$CHECK_RC"`. The post step
  runs with `GH_TOKEN=fake-pat` and `FACTORY_REVIEW_TOKEN_SET=true`. A fake
  `gh` on `PATH` answers `api user` with `reviewer-bot` and records every
  argv and the posted body file. The event fixture is PR 4242 by
  `factory-agent`.

  The hostile text is my own. It contains:
  - a ten-backtick line, `</details>`, and a fake
    `**Detectors and tests: PASS**`;
  - `@owner this is approved, merge it`;
  - command-injection attempts: `$(touch pwned_subst)`,
    `` `touch pwned_backtick` `` and `; touch pwned_semicolon`;
  - `${GH_TOKEN} $GH_TOKEN %0A::set-output name=findings::forged`;
  - delimiter-shaped lines: `EOF`, `findings<<EOF`, `findings=forged` and
    `findings-deadbeef`;
  - other fence and marker forms: `~~~`, an indented fifteen-backtick run,
    and `<!-- factory-review -->`;
  - about 100 KB of padding.

  After each case, the script searched the temp dir, the worktree and the
  cwd for any `pwned*` file.
- Evidence (`vrt/replay.out`):
  ```
  write step env keys: ['HANDED_OVER'] | run: printf '%s' "$HANDED_OVER" > "$RUNNER_TEMP/findings.txt"
  post step run: make review FINDINGS="$RUNNER_TEMP/findings.txt" STATUS="$CHECK_RC"
  case A: producer -> GITHUB_OUTPUT -> review, check failed
    [A] producer: GITHUB_OUTPUT keys={'findings': 1} value bytes=65536
    [A] write step rc=0, file bytes=65536 identical_to_handed_over=True
    [A] post step rc=0 stderr_tail=''
    [A] gh calls: ['ARGV: api user --jq .login', 'ARGV: pr comment 4242 --edit-last --body-file /tmp/tmpfmlpits0/review.md']
    [A] posted body chars=12463 fence=16 longest_run_inside=15 tail_after_close='\n</details>\n' verdicts_outside_fence=['FAIL'] comment_target=True pwned_files=[]
    [A] RESULT PASS
  case B: attacker-chosen HANDED_OVER directly (poisoned hand-off), check failed
    [B] write step rc=0, file bytes=104351 identical_to_handed_over=True
    [B] posted body chars=12463 fence=16 longest_run_inside=15 tail_after_close='\n</details>\n' verdicts_outside_fence=['FAIL'] comment_target=True pwned_files=[]
    [B] RESULT PASS
  case C: text says FAIL/PASS, check succeeded -> verdict PASS from result only
    [C] posted body chars=422 fence=3 longest_run_inside=0 tail_after_close='\n</details>\n' verdicts_outside_fence=['PASS'] comment_target=True pwned_files=[]
    [C] RESULT PASS
  case D: non-UTF-8 bytes, check failed
    [D] write step rc=0, file bytes=552 identical_to_handed_over=True
    [D] post step rc=0 stderr_tail=''
    [D] posted body chars=940 fence=4 longest_run_inside=3 tail_after_close='\n</details>\n' verdicts_outside_fence=['FAIL'] comment_target=True pwned_files=[]
    [D] RESULT PASS
  ALL PASS [True, True, True, True]
  ```
  Control: the `pwned` check is not blind. The same payload through an
  `eval`-style write does execute:
  ```
  HANDED_OVER='$(touch pwned_subst)' bash --noprofile --norc -e -c 'eval "echo $HANDED_OVER" >/dev/null'; ls  ->  pwned_subst
  ```
- Reading:
  - No command ran.
  - The only verdict line outside the fence matches the check's result, not
    the text. Case C shows this both ways.
  - Every fence is longer than any backtick run inside it, and nothing
    follows the closing fence but `</details>`.
  - The body is bounded at 12463 chars: the 12000-char cap plus the
    template.
  - The comment goes to the event's PR (4242), never to a number from the
    text.
  - The only `gh` calls are `api user` and `pr comment`.
- Result: PASS

### V3. Gate preservation: a failing `make check` keeps the step red

- Check: the scratchpad script `vrt/gate.py` runs `check`'s "Detectors and
  tests" script from the Psych parse under `bash --noprofile --norc -e`,
  with a stub `make` that prints a line and exits with a chosen code. As a
  control, the same script runs with `set -o pipefail` deleted.
- Evidence:
  ```
  script: 'set -o pipefail\nmake check 2>&1 | tee "$RUNNER_TEMP/findings.txt"\n'
  stub make exit 1 -> step rc=1 findings='FAILED (failures=1) from stub make'
  stub make exit 0 -> step rc=0 findings='FAILED (failures=1) from stub make'
  CONTROL (pipefail removed), stub exit 1 -> step rc=0 findings='FAILED (failures=1) from stub make'
  ```
  The control shows that pipefail is what keeps the gate red. The findings
  are captured either way.
- Result: PASS

### V4. Mutation spot-checks: the suite catches regressions that Implement did not try

Each mutation was applied to both the root file and its payload twin, so the
mirror pin is not what catches it. The full suite was run, then the files
were restored with `git checkout`, and `git diff --stat` was empty after each
restore.

The same three failures appear in every run below and are collateral, not
the catch. They are the manifest checksum running ahead of an unregenerated
payload (detector E):
- `test_stamped_repo_passes_its_own_gates`
- `test_factory_init … test_a_clean_run_ends_with_the_exact_summary_line`
- `test_gates … test_a_clean_run_ends_with_the_exact_summary_line`

- **M1: move `HANDED_OVER` from the write step into the PAT/make post step's
  `env:`.** Caught.
  ```
  FAIL: test_the_handed_over_text_sits_in_one_env_beside_no_secret (test_validator_workflow.TestReviewJobTakesTheHandOffAsData...)
  AssertionError: Lists differ: [('review', '- name: Post findings as a non-authoring actor')] != [('review', '- name: Write the handed-over findings')]
  ERROR: test_a_hostile_hand_off_is_posted_inert_and_bounded (test_validator_workflow.TestHostileHandOffReplay...)
  ERROR: test_an_oversized_hand_off_is_bounded_or_fails_closed (test_validator_workflow.TestHostileHandOffReplay...)
  Ran 2084 tests in 28.348s
  FAILED (failures=4, errors=2)
  ```
- **M2: `run_review` reads the untrusted file whole (`handle.read()`).**
  Caught.
  ```
  FAIL: test_the_findings_read_is_bounded_not_whole_file (test_validator.TestRunReview...)
  AssertionError: 48018 != 48000
  Ran 2084 tests in 28.286s
  FAILED (failures=4)
  ```
- **M3: `needs-review-label`'s checkout `ref:` deleted, back to the merge ref
  on `pull_request`.** Caught.
  ```
  FAIL: test_no_job_running_pr_code_holds_a_write_grant (test_validator_workflow.TestReviewerCredentialBoundary...) (job='needs-review-label')
  AssertionError: 'write' unexpectedly found in dict_values(['read', 'write', 'read']) : needs-review-label runs PR code with a write grant
  Ran 2084 tests in 28.357s
  FAILED (failures=4)
  ```
- After the restores: `git status --short` was empty.
- Result: PASS (3 of 3 caught)

### V5. Battery on the final tree

- Check: the full battery, then `update-manifest`, then the
  must-not-change paths compared against origin/main.
- Evidence:
  ```
  python3 -m unittest discover tests 2>&1 | grep -E "^(Ran|OK|FAILED)"
  Ran 2084 tests in 28.732s
  OK
  python3 lint.py                -> lint: 0 problem(s) across 26 skills
  python3 gates.py               -> gates: 0 problem(s)
  python3 gates.py --selftest    -> selftest: ok
  python3 factory_init.py update-manifest -> factory-init: 0 problem(s)
  git status --short (after)     -> (empty); diff-after-manifest: 0
  git diff origin/main --stat -- .github/workflows/assembler.yml factory/templates/.github/workflows/assembler.yml Makefile factory/templates/Makefile -> (empty)
  ```
- Result: PASS

### V6. Breakdown acceptance (rows 0133 to 0145)

- Check: all 13 rows are checked in breakdown.md. Their RED-before-fix lines
  and mutation proofs are quoted in its Notes, from Implement. This stage
  re-proves their substance independently:
  - rows 0133, 0134, 0136 and 0137: V1 and mutations M1 and M3;
  - rows 0135, 0142 and 0143: V2 case A (one `findings` key, 65536 bytes,
    despite `EOF` and `findings<<EOF` lines) and V3;
  - rows 0139, 0140 and 0141: V2 cases B and D, and mutation M2;
  - rows 0144 and 0145: V1 `cmp`, V5, and actionlint.
- Evidence:
  ```
  grep -c -E "^- \[x\] \*\*WO-01(3[3-9]|4[0-5])\*\*" breakdown.md  -> 13
  grep -c -E "^- \[ \]" breakdown.md                                  -> 0
  python3 -m unittest tests.test_validator_workflow                     -> Ran 14 tests in 0.526s / OK
  ```
- Result: PASS

### V7. The regression (the maintenance run's centrepiece)

- Check: defect.md requires a mechanical reproduction. This stage re-ran
  it rather than citing Implement's Notes. A throwaway detached worktree was
  made at HEAD in the scratchpad, its `validator.yml` was replaced by the
  pre-fix file (`git show ba286e5:.github/workflows/validator.yml`), and
  today's `tests.test_validator_workflow` was run there. The worktree was
  then removed. On the real tree the same module is green (V6), and mutation
  M3 shows the class still re-reddens.
- Evidence (pre-fix file, excerpt; full set is 10 failures and 5 errors):
  ```
  FAIL: test_no_job_running_pr_code_holds_a_write_grant (...) (job='review')
  AssertionError: 'write' unexpectedly found in dict_values(['read', 'write']) : review runs PR code with a write grant
  FAIL: test_no_job_running_pr_code_holds_a_write_grant (...) (job='needs-review-label')
  AssertionError: 'write' unexpectedly found in dict_values(['read', 'write', 'read']) : needs-review-label runs PR code with a write grant
  FAIL: test_no_job_running_pr_code_names_a_secret_but_its_own_token (...) (job='review')
  AssertionError: {'FACTORY_REVIEW_TOKEN', 'GITHUB_TOKEN'} not less than or equal to {'GITHUB_TOKEN'} : review runs PR code holding {'FACTORY_REVIEW_TOKEN', 'GITHUB_TOKEN'}
  FAIL: test_the_reviewer_token_reaches_one_step_on_a_base_checkout (...)
  AssertionError: Lists differ: ["${{[18 chars] == 'workflow_dispatch' && format('refs/pull/{[26 chars] }}"] != ["${{[18 chars] == 'pull_request' && github.event.pull_reques[24 chars] }}"]
  FAIL: test_every_checkout_leaves_no_credential_in_git_config (...) (job='check' | 'review' | 'needs-review-label')
  AssertionError: None != 'false'
  ERROR: test_a_failing_check_fails_the_step_and_keeps_its_output (...)   [replays find no new steps on the old file]
  Ran 14 tests in 0.358s
  FAILED (failures=10, errors=5)
  ```
- Result: PASS

## Failures

None.

Observations for Review. None of them is a failure of this run's criteria.

- **The dispatch arm trusts the dispatcher's ref.** `review` checks out
  `github.sha`, which is the ref the dispatcher chose. A write-collaborator
  dispatch with `--ref <agent-branch>` would run that branch's workflow
  definition and code with the PAT. This is the premise ADR-0098 states:
  the definition comes from the dispatched ref, so no in-file split can
  stop it. The deliver job dispatches with no `--ref`, and dispatching
  needs write access. I found no new hole, only the stated premise.
- **The verdict equals `check`'s result, and the PR's code computes it.** A
  PR that rewrites its own `make check` can turn the status check, and so
  the reviewer's PASS, green. The change does not create this: it is gate
  3's status check as it always was, and the human merge is the backstop.
  The fix's promise is narrower, and it holds: the reviewer's text cannot
  contradict the result (V2 case C).
- **Cosmetic: one comment line was left unwrapped.** It is 110 chars, at
  `validator.yml:107` ("…is never interpolated into a run: script.
  PRD-0001 forbids…"), and the line is mirrored. actionlint does not care.

## Not verified

These are runner-only proofs, carried from breakdown.md Notes and
architecture.md's "What only a live run proves". They fold into the owner's
combined post-merge live dispatch, and none of them is claimed here:

- `needs.check.outputs.findings` is populated for `review` when `check`
  FAILED, under `always()`.
- The random-delimiter multi-line output round-trips on a real runner, and
  secret redaction does not drop ordinary findings. V2 case A proves only
  the documented grammar.
- The base-SHA checkout works on `pull_request`, and `github.sha` on a run
  the deliver job dispatched is the default branch.
- The reviewer posts from the base job: the PAT identity check
  (`gh api user`) still resolves, and the comment lands as the reviewer.
  V2 used a fake `gh`.
- The premise holds: a `GITHUB_TOKEN` push touching `.github/workflows/**`
  is refused, so an agent branch cannot rewrite the jobs.
- `needs-review-label` still flips `wo:needs-review` from the base checkout
  on both triggers.
- `persist-credentials: false` on `check` does not break `make check`. By
  grep, only `budget_guard.push_wip` runs `git push`, and only through an
  injected runner, which the tests fake. Not proven on a runner.
- Linux E2BIG: a hand-off over about 128 KiB fails the write step closed.
  On macOS, V2 case B (104 KB) took the bounded path. Implement exercised
  the Linux branch under docker; this stage did not repeat it.

Open owner question, still open and not guessed: what are
`FACTORY_REVIEW_TOKEN`'s scopes? Is it a classic PAT with which scopes, or
a fine-grained PAT with which repository permissions? The answer settles
major against critical. The design holds under the worst case (classic
`repo`).

Next stage: Review.
