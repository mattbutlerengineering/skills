---
stage: decompose
run: maintenance:the-reviewer-token-runs-agent-code
date: 2026-10-10
assumptions:
  - "No live review of the cut: this run is autorun-driven (autorun-brief.md). The rows are read out of architecture.md's Components, Interfaces and 'Test strategy (for Decompose / Implement)' sections and ADR-0098's Decision list. A mis-sized row is a note to log at Implement time, not a design change."
  - "Rows carry work-order ids, continuing the repo-global sequence after row 0132 (the highest across every local branch and origin/main, read 2026-10-10 with git grep over refs/heads and refs/remotes/origin). This follows the coordinator's instruction and docs/features/first-live-dispatch/breakdown.md Milestone E, the precedent this defect comes from, rather than the older maintenance-run habit of letter ids. No tracker mirror: no row gets an issue or a (tracker: #N) reference (brief, 'Tracker'). The ADR-0032 one-way order still holds, because no issue is created."
  - "Every row cites PRD-0003 §Success criteria. A fix run has no PRD of its own, detector A requires a PRD citation on every work-order line, and the defect is finding 4 of PRD-0003's first-live-dispatch review: the validator hand-off criterion ('a workflow_dispatch validator run ... executes check + review + label jobs') is exactly the path this run re-shapes. Outside checkbox lines, ids are written 'row NNNN' so detector A does not read prose as an uncited row."
  - "Ledger: detector G reads a checked work-order row as a merged order that is owed a docs/factory/costs.jsonl line. These rows are worked in an owner/autorun session with no dispatched agent, so each check-off appends one honest zero-cost row through budget_guard record, as Milestone E and docs/features/readme-skill-map/breakdown.md did (ADR-0069). It is never a fabricated spend figure."
  - "RED first, and the battery stays green at every commit. The boundary tests (rows 0133 and 0134) reproduce the defect mechanically: they must be run against the UNMODIFIED validator.yml and seen to fail, with the failure lines quoted in Notes. They cannot be committed alone without turning main red, so they land in the same commit as the YAML rows that turn them green (see 'Commit plan'). This is the repo's established tests-first practice: write the test, watch it fail, commit it with the fix."
  - "The env-shadow pin (architecture.md Test strategy 2, third bullet) is read as: no env key of a step that runs make may equal a variable the root Makefile assigns UNLESS the same step's make command line assigns that variable too. The architecture's own design keeps `PR: ${{ inputs.pr }}` in the env of the base-code `make pr-event PR=\"$PR\"` step. PR is a Makefile variable (Makefile:33), and a make command-line assignment beats an imported environment variable, so that key cannot be shadowed. A literal reading of the pin would fail the architecture's own design. The ADR-0098 rule the pin protects (handed-over data never sits in a make step's env) is pinned separately and literally (row 0134)."
  - "New test homes: the boundary and trusted-job pins (rows 0133 and 0134) and the YAML replays (rows 0141 to 0143) go in tests/test_assembler.py, as a new class beside TestAgentCredentialBoundary and TestBundleCannotReachMain. That file already owns the workflow_jobs hand-parse helper (tests/test_assembler.py:687) and TestValidatorDispatchLockstep, which reads validator.yml. The architecture names the precedent but not the file. If Implement moves them into their own module, it imports the helper and does not copy it; a copy would be a second owner."
  - "Architecture Test strategy item 5 (producer robustness) is its own row (0143), although the coordinator's row list did not name it. The architecture lists it, and the skill rule is that every component and contract maps to a row."
  - "actionlint is installed (/opt/homebrew/bin/actionlint), so the close-out battery runs it on both validator.yml copies. The brief asks for it 'if installed'."
---

# Breakdown: the reviewer token never meets agent code

Progress lives in the checkboxes below. Implement checks items off as
their acceptance criteria are met. Sources are `defect.md` (the
file:line chain and the Expected clause), `architecture.md` (job graph,
data model, the hand-off contract, Test strategy items 1 to 6) and
ADR-0098 (Decisions 1 to 6). Row grammar follows
`docs/features/first-live-dispatch/breakdown.md` Milestone E: one line per
work order with its id, size class, blocking edges and PRD citation.

**What must not change.** These stay as they are:

- `assembler.yml` and its mirror, and the dispatch interface #629's
  deliver job uses (`gh workflow run validator.yml -f pr=N`, no `--ref`);
- every recorded grant in `tests/test_workflow_permissions.py` (only the
  reason strings move);
- the Makefile's `review` and `pr-event` recipes;
- `merged-label`;
- `validator.py`'s `reviewer_login`, `actor_conflict`,
  `declared_conflict`, `cited_work_order`, `post_review` and
  `MAX_FINDINGS_CHARS`.

If a diff in this run touches any of these, the row has been misread.

**Mirrors.** Both `.github/workflows/validator.yml` and `validator.py` are
`factory_init.MIRRORS` identity entries (`factory_init.py:221`, `:232`).
Every commit that edits either one copies it to its payload twin and runs
`python3 factory_init.py update-manifest` in the same commit. Delete any
`.orig` or `.rej` file first.

**Battery at every commit boundary.**
- `python3 -m unittest discover tests` is OK.
- `python3 lint.py` prints `lint: 0 problem(s)`.
- `python3 gates.py && python3 gates.py --selftest` prints
  `gates: 0 problem(s)` and `selftest: ok`.

## Milestone A: the defect reproduced (the boundary tests fail on today's file)

Demonstrable at the close: two test classes exist. Run against the
unmodified `validator.yml`, they fail, and each failure names a
defect.md file:line fact. This milestone is the mechanical reproduction
that defect.md and the brief require ("asserting the defect does not
count").

- [x] **WO-0133** the credential-boundary test over validator.yml — size:S, blocked by: — (PRD-0003 §Success criteria)
  - Accept: a new `TestReviewerCredentialBoundary` class is added, modelled on `TestAgentCredentialBoundary` and parsing jobs with `workflow_jobs`. It treats a job's checkout as PR-controlled when the checkout has no `ref:` (on `pull_request` the default is the merge ref) or its `ref:` names `refs/pull/`. It asserts four things (architecture.md Test strategy 1; ADR-0098 Decisions 1, 3, 5 and 6):
    - (a) no job with a PR-controlled checkout holds any `write` grant;
    - (b) no such job names any `secrets.` other than `GITHUB_TOKEN`;
    - (c) every `actions/checkout` in `check`, `review` and `needs-review-label` carries `persist-credentials: false`;
    - (d) `FACTORY_REVIEW_TOKEN` appears in exactly one step, in a job whose checkout `ref:` is the base expression.

    Run against today's file, it FAILS on `review` for (a) and (b) (defect.md: `validator.yml:106-112` and `:130-135`), on `needs-review-label` for (a), and on all three jobs for (c). The failure lines are quoted in Notes before any YAML edit. Merge-ref exclusion: `merged-label` is out of scope (architecture.md assumptions) and is excluded from (a) by name, with the reason in the test's docstring.
- [x] **WO-0134** trusted-job static pins — size:S, blocked by: WO-0133 (PRD-0003 §Success criteria)
  - Accept: the same class, or a sibling class, asserts these five things (architecture.md Test strategy 2; ADR-0098 Decision 4):
    - (a) no `${{` appears inside any `run:` of `review`;
    - (b) `needs.check.outputs` appears only in the `env:` of the review job's "Write the handed-over findings" step, and that step names no `secrets.` and runs no `make`;
    - (c) no env key of a step that runs `make` equals a variable the root Makefile assigns (parsed from `^NAME ?=` and `^NAME =` lines), unless the same step's make command line assigns it (assumption above);
    - (d) `review` declares `needs: check`;
    - (e) `review`'s `if:` admits only `needs.check.result` of `success` or `failure`, keeps the fork guard (`head.repo.full_name == github.repository`), and keeps both triggers with the `opened`/`reopened`/`synchronize` allow-list.

    Run against today's file, (d) and (e) FAIL (`review` has no `needs:`). (b) fails because no write step exists. The output is quoted in Notes.

## Milestone B: the split (the PAT reaches one step, in a job that runs base code)

Demonstrable at the close: rows 0133 and 0134 pass, and `validator.yml`
matches architecture.md's job graph. Its payload twin is byte-identical,
and `actionlint` is clean.

- [x] **WO-0135** check runs the PR's code and hands its findings over as one output — size:M, blocked by: WO-0133 (PRD-0003 §Success criteria)
  - Accept: the `check` job meets all of the following (architecture.md Components, "`check` job"; ADR-0098 Decisions 1 and 2):
    - Its checkout carries `persist-credentials: false`.
    - The "Detectors and tests" step runs `set -o pipefail` and then `make check 2>&1 | tee "$RUNNER_TEMP/findings.txt"`.
    - A new step, "Hand the findings to the review job", has `if: ${{ !cancelled() }}`. It writes `findings<<$delim` to `$GITHUB_OUTPUT`, with a delimiter that is random per run and a body of `head -c 65536` of the file.
    - The job declares exactly one output, `findings`.
    - Grants are unchanged (`contents: read`, `pull-requests: read`), and the existing dispatch-arm `make pr-event` step stays.

    Row 0133's (a) and (b) for `check` still pass, and its (c) passes for `check`.
- [x] **WO-0136** review checks out base and runs only base code — size:M, blocked by: WO-0134, WO-0135 (PRD-0003 §Success criteria)
  - Accept: the `review` job meets all of the following (architecture.md Components, "`review` job"; Interfaces, "Base ref per trigger"; ADR-0098 Decisions 3 to 5):
    - It declares `needs: check`. Its `if:` is `always()`, AND `needs.check.result` is `success` or `failure`, AND (today's `pull_request` allow-list with the fork guard, OR `workflow_dispatch`).
    - Its checkout `ref:` is `pull_request ? github.event.pull_request.base.sha : github.sha`, with `persist-credentials: false`.
    - On dispatch only, a `make pr-event PR="$PR"` step runs from that base checkout with `GH_TOKEN: secrets.GITHUB_TOKEN`.
    - A "Write the handed-over findings" step takes env `HANDED_OVER: needs.check.outputs.findings`, runs `printf '%s' "$HANDED_OVER" > "$RUNNER_TEMP/findings.txt"`, and holds no secret and no make.
    - The "Post findings as a non-authoring actor" step keeps `GH_TOKEN`, `FACTORY_REVIEW_TOKEN_SET` and `FACTORY_REVIEW_LOGIN` exactly as today. It adds `CHECK_RC: needs.check.result == 'success' && '0' || '1'` and runs `make review FINDINGS="$RUNNER_TEMP/findings.txt" STATUS="$CHECK_RC"`.
    - The old "Collect findings" step (`set +e`, the second `make check`) is gone.
    - Grants are unchanged (`contents: read`, `pull-requests: write`).
    - The job's header comment says the reviewer runs base code and why, citing ADR-0098.

    Rows 0133 and 0134 now pass for `review`.
- [x] **WO-0137** needs-review-label checks out base, not the merge ref — size:S, blocked by: WO-0133 (PRD-0003 §Success criteria)
  - Accept: `needs-review-label`'s checkout gains the same base `ref:` expression as `review`, plus `persist-credentials: false` (architecture.md Components, "`needs-review-label` job"; ADR-0098 Decision 6). Its comment is reworded, because "default checkout on both paths" was wrong on `pull_request`: the code must be the base ref's. Triggers, grants and the `make wo-needs-review` step are unchanged. Row 0133 passes in full.
- [x] **WO-0138** existing suites follow the new shape — size:S, blocked by: WO-0136, WO-0137 (PRD-0003 §Success criteria)
  - Accept: these suites follow the new shape (architecture.md Test strategy 6):
    - `tests/test_workflow_permissions.py`: every recorded grant for `validator.yml` is byte-unchanged. Only the reason strings change: `review` becomes "posts the review comment from a base checkout; runs no PR code", and `check`'s reason gains "and hands its findings to review".
    - `tests/test_gates.py`'s make-only `ALLOWED["validator.yml"]` drops the `set +e` opener. It gains the new step openers (`set -o pipefail`, the delimiter line, and `printf '%s' "$HANDED_OVER" > …`), each with a one-line reason comment.
    - `TestValidatorDispatchLockstep` still finds the shim count equal to the `make pr-event` count.
    - The payload byte-identity pin in `tests/test_factory_init.py` passes after the mirror copy.
    - No assertion is weakened to make a case pass. Any assertion that changes is listed in Notes with why.

## Milestone C: the trusted parser renders untrusted text inertly

Demonstrable at the close: `validator.py review` reads a findings file of
any size and any encoding without refusing. Its rendered body cannot be
closed out of its code fence. Independent of Milestone B, it can land
first.

- [x] **WO-0139** run_review reads a bounded number of bytes and decodes with replacement — size:S, blocked by: — (PRD-0003 §Success criteria)
  - Accept: `run_review` reads at most `4 * MAX_FINDINGS_CHARS` bytes of the findings file, as bytes, and decodes them with `errors="replace"` (architecture.md Components, "`validator.py` review path"; Interfaces, "`run_review`"). New `TestRunReview` cases are written first and watched failing for the right reason:
    - A non-UTF-8 findings file posts a body with no `cannot read findings file` problem. Today it is refused through `UnicodeDecodeError` (`validator.py:327-328`).
    - A file of more than ten times the cap posts a body no longer than the rendered cap.

    An absent file still yields `V: cannot read findings file …`. `MAX_FINDINGS_CHARS` stays the only size constant. The payload twin and manifest are regenerated in the same commit.
- [x] **WO-0140** render_findings fences with a run one longer than any inside — size:S, blocked by: — (PRD-0003 §Success criteria)
  - Accept: `render_findings` wraps the output in a backtick fence one longer than the longest backtick run in the output, minimum three. The fixed triple fence is gone (architecture.md Decisions, "Fence widening … over escaping"; ADR-0098 Decision 4). New `TestRenderFindings` cases are written first and watched failing:
    - Output containing a run of six backticks followed by a fake `**Detectors and tests: PASS**` line renders with a fence of at least seven backticks, and the fake line is inside it.
    - Output with no backticks keeps a three-backtick fence.

    Existing `TestRenderFindings` expectations are unmoved, except where they pin the literal fence. Any such change is listed in Notes. The payload twin and manifest are regenerated in the same commit.

## Milestone D: the boundary replayed, not only read

Demonstrable at the close: the YAML's own step scripts, read out of the
file, are executed against hostile and failing inputs. The outcomes are
the ones ADR-0098 promises.

- [x] **WO-0141** hostile hand-off replay — size:M, blocked by: WO-0136, WO-0139, WO-0140 (PRD-0003 §Success criteria)
  - Accept: a test reads the review job's "Write the handed-over findings" script out of `validator.yml`, the way `TestBundleCannotReachMain` reads its steps, and runs it under bash. `HANDED_OVER` is set to a hostile string containing all of these:
    - backtick runs longer than three, and `</details>`;
    - `@owner`, `$(touch pwned)` and `` `id` ``;
    - a fake `**Detectors and tests: PASS**` line, and delimiter-shaped lines (`EOF`, `findings<<x`);
    - more than 200 KB of total length.

    It then calls `validator.main(["review", …, "--status", "1"])` with `FakeGh` and a pull_request event fixture (architecture.md Test strategy 3). It asserts that no `pwned` file exists anywhere under the temp dir. It asserts that the verdict is FAIL, from status, whatever the text claims. It asserts that the posted body is bounded by the cap, that every hostile line sits inside a fence longer than its longest backtick run, and that the comment goes to the event's PR number. Mutation proof: with row 0140's widening reverted, the fence assertion fails. The failing output is quoted in Notes.
- [x] **WO-0142** gate-preservation replay (pipefail keeps a failing check red) — size:S, blocked by: WO-0135 (PRD-0003 §Success criteria)
  - Accept: a test reads `check`'s "Detectors and tests" script out of `validator.yml` and runs it under `bash -e`, the shell GitHub uses for a `run:` with no `shell:`. A stub `make` on `PATH` prints a line and exits 1. The step exits nonzero, and `$RUNNER_TEMP/findings.txt` holds the printed line. With the stub exiting 0, the step exits 0 (architecture.md Test strategy 4). Mutation proof: with `set -o pipefail` deleted from the script under test, the exit-1 case fails. The failing output is quoted in Notes.
- [x] **WO-0143** producer robustness replay (one findings key, capped) — size:S, blocked by: WO-0135 (PRD-0003 §Success criteria)
  - Accept: a test reads `check`'s hand-off script out of `validator.yml` and runs it with a findings file whose lines include `EOF`, `findings<<EOF` and an extra `key=value` line, plus a body over 65536 bytes. It then parses `$GITHUB_OUTPUT` with GitHub's documented multiline grammar (`name<<delim` up to a line equal to `delim`). The result holds exactly one key, `findings`, whose value is the first 65536 bytes of the file (architecture.md Test strategy 5; Data model, "No other job output is declared"). Mutation proof: with a fixed `EOF` delimiter, the case fails.

## Milestone E: close-out

Demonstrable at the close: the mirrors and manifest agree, the full
battery is green, and the live-only proofs are handed to release
unclaimed.

- [x] **WO-0144** payload mirrors and manifest are current — size:S, blocked by: WO-0138, WO-0139, WO-0140 (PRD-0003 §Success criteria)
  - Accept: these all hold:
    - `cmp .github/workflows/validator.yml factory/templates/.github/workflows/validator.yml` and `cmp validator.py factory/templates/tools/factory/validator.py` both exit 0;
    - `python3 factory_init.py update-manifest`, rerun on the final tree, leaves `git status` clean;
    - no `.orig` or `.rej` file is tracked or pinned;
    - detector E is green.
- [x] **WO-0145** close-out battery — size:S, blocked by: WO-0141, WO-0142, WO-0143, WO-0144 (PRD-0003 §Success criteria)
  - Accept: these all hold on the final tree, with output quoted in Notes:
    - `python3 -m unittest discover tests` prints `OK`, and the test count is above this branch's pre-run baseline;
    - `python3 lint.py` prints `lint: 0 problem(s)`;
    - `python3 gates.py && python3 gates.py --selftest` prints `gates: 0 problem(s)` and `selftest: ok`;
    - `actionlint .github/workflows/validator.yml factory/templates/.github/workflows/validator.yml` exits 0;
    - `git diff origin/main -- .github/workflows/assembler.yml factory/templates/.github/workflows/assembler.yml Makefile factory/templates/Makefile` is empty (the "must not change" list);
    - one zero-cost owner-session ledger row exists per checked row (detector G).

    Notes lists the live-only proofs from architecture.md's "What only a live run proves" for release.md to carry into the owner's combined post-merge live dispatch. None is claimed here. ADR-0098 stays `provisional`.

## Milestone F: review fix (added by Review)

- [x] **WO-0149** trusted checkouts pin the default branch on dispatch, never `github.sha` — size:S, blocked by: WO-0145 (PRD-0003 §Success criteria)
  - Accept: these all hold:
    - `review` and `needs-review-label` check out `github.event.pull_request.base.sha` on `pull_request` and `refs/heads/<github.event.repository.default_branch>` on `workflow_dispatch`, so a `gh workflow run validator.yml --ref <pr-branch>` dispatch does not put the PR branch's Makefile beside the PAT or `issues: write`;
    - `tests/test_validator_workflow.py::TestReviewerCredentialBoundary::test_no_write_holding_checkout_follows_the_dispatchers_ref` fails on the pre-fix file and passes after;
    - the mirror is byte-identical, the manifest is regenerated, and the battery is green;
    - ADR-0098 Decision 3 and its premise paragraph state the dispatch ref and the pre-fix-branch caveat.

## Commit plan

Rows are units of acceptance. Commits are cut so that the battery is
green at each one:

1. **Row 0139**: tests and fix, then mirror and manifest.
2. **Row 0140**: tests and fix, then mirror and manifest.
3. **Rows 0133 to 0138**: one commit.
   - First write the boundary tests and record their RED output against
     the unmodified file.
   - Then edit `check`, `review` and `needs-review-label`, and update the
     existing suites.
   - Then mirror and manifest.

   The commit message quotes the RED lines.
4. **Rows 0141 to 0143**: test-only. Each mutation proof is run and its
   output quoted in Notes; the mutation is not committed.
5. **Rows 0144 and 0145**: Notes, ledger rows, and the checkbox ticks.

## Design gaps found

None. Every component in architecture.md maps to a row:

| Component or contract | Row |
|---|---|
| the `check` job | 0135 |
| the `review` job | 0136 |
| `needs-review-label` | 0137 |
| the `validator.py` review path | 0139, 0140 |
| the payload mirror and manifest | 0144 |
| the hand-off contract | 0134, 0141, 0143 |
| "Base ref per trigger" | 0136 |

Every item in Test strategy 1 to 6 maps to a row. The defect's Expected
clause ("no step that executes code from the PR holds the reviewer PAT
or any write-scoped token") is row 0133's assertions (a) to (d).

The env-shadow pin's literal wording conflicted with the architecture's
own `PR:` env on the base `make pr-event` step. It was settled as an
interpretation, not routed back, because make's command-line precedence
makes it safe and ADR-0098's rule is pinned literally elsewhere (see
assumptions).

## Notes

- 2026-10-10 (decompose): open owner question carried forward, not
  blocking. What are `FACTORY_REVIEW_TOKEN`'s scopes? The answer settles
  major against critical. The design holds under a classic `repo` PAT
  (defect.md, architecture.md).
- 2026-10-10 (decompose): observed while cutting row 0134, out of scope.
  `make pr-event PR="$PR"` expands `$(PR)` into recipe shell text, and
  `inputs.pr` is not validated before make runs. The dispatcher already
  holds write access, so this escalates nothing. It is pre-existing,
  sits on the base-code side after the split, and touches none of
  this run's rows. It is recorded here and not fixed.
- 2026-10-10 (implement, row 0139): one existing assertion was
  replaced, not weakened. `test_findings_that_are_not_utf8_are_a_problem_not_a_traceback`
  pinned the refusal of non-UTF-8 findings that row 0139 removes by design
  (architecture.md, "`run_review`": "no longer refuses non-UTF-8 input"). It
  became `test_findings_that_are_not_utf8_still_post`. RED before the fix:
  `AssertionError: Lists differ: ["V: cannot read findings file …"] != []`,
  and the new bounded-read case `AssertionError: 48018 != 48000` (the whole
  file was read). The "ten times the cap posts a bounded body" case was
  already green before the fix, because `render_findings` truncates; the
  bounded-read case is the one that pins the new read bound.
- 2026-10-10 (implement, row 0140): RED before the fix, on the six-backtick
  case: `ValueError: substring not found` (no seven-backtick fence exists;
  the fixed triple fence was the only one). No existing `TestRenderFindings`
  expectation pinned the literal fence, so none moved. `validator.py` gains
  `import re` for the backtick-run scan.
- 2026-10-10 (implement, rows 0133 and 0134): the defect reproduced
  mechanically. The boundary tests, run against the UNMODIFIED
  `validator.yml` before any YAML edit, failed with exactly these lines
  (`python3 -m unittest tests.test_validator_workflow`, 9 tests, 10
  failures):

  ```
  FAIL: test_no_job_running_pr_code_holds_a_write_grant (job='review')
  AssertionError: 'write' unexpectedly found in dict_values(['read', 'write']) : review runs PR code with a write grant
  FAIL: test_no_job_running_pr_code_holds_a_write_grant (job='needs-review-label')
  AssertionError: 'write' unexpectedly found in dict_values(['read', 'write', 'read']) : needs-review-label runs PR code with a write grant
  FAIL: test_no_job_running_pr_code_names_a_secret_but_its_own_token (job='review')
  AssertionError: {'FACTORY_REVIEW_TOKEN', 'GITHUB_TOKEN'} not less than or equal to {'GITHUB_TOKEN'} : review runs PR code holding {'FACTORY_REVIEW_TOKEN', 'GITHUB_TOKEN'}
  FAIL: test_every_checkout_leaves_no_credential_in_git_config (job='check')
  AssertionError: None != 'false'
  FAIL: test_every_checkout_leaves_no_credential_in_git_config (job='review')
  AssertionError: None != 'false'
  FAIL: test_every_checkout_leaves_no_credential_in_git_config (job='needs-review-label')
  AssertionError: None != 'false'
  FAIL: test_the_reviewer_token_reaches_one_step_on_a_base_checkout
  AssertionError: Lists differ: ["${{[18 chars] == 'workflow_dispatch' && format('refs/pull/{[26 chars] }}"] != ["${{[18 chars] == 'pull_request' && github.event.pull_reques[24 chars] }}"]
  FAIL: test_review_waits_for_check
  AssertionError: Regex didn't match: '(?m)^    needs: check$' not found in '  review:\n    if: >-\n ...
  FAIL: test_review_admits_a_finished_check_on_the_two_triggers_only
  AssertionError: 'always()' not found in "(github.event_name == 'pull_request' && (github.event.action == 'opened' || ...) && github.event.pull_request.head.repo.full_name == github.repository) || github.event_name == 'workflow_dispatch'"
  FAIL: test_the_handed_over_text_sits_in_one_env_beside_no_secret
  AssertionError: Lists differ: [] != [('review', '- name: Write the handed-over findings')]
  ```

  Row 0134's (a) (no `${{` in a review `run:`) and (c) (env shadow)
  already passed on the old file. The breakdown did not predict them to
  fail, and they pin the new shape against regression.
- 2026-10-10 (implement, rows 0133 and 0134): test home. The two classes
  live in a new module, `tests/test_validator_workflow.py`, not in
  `tests/test_assembler.py`, which is already past 1000 lines. As the
  decompose assumption requires, the module imports `workflow_jobs`,
  `run_lines` and `permission_block` from `test_assembler` and copies
  none of them. Its own helpers (`job_steps`, `step_block`, `checkouts`,
  `job_if`) parse step-level structure, which no existing helper does.
- 2026-10-10 (implement, row 0135): detail the architecture left open.
  The hand-off step is `id: handoff`, and the job output reads
  `steps.handoff.outputs.findings`. Its delimiter is `findings-` followed
  by 16 random bytes in hex, from `od -An -N16 -tx1 /dev/urandom`.
  `head -c 65536 … || true` keeps the step from dying when the check
  failed before the findings file existed (a setup failure). The review
  then posts FAIL with an empty block, the closed failure the contract
  names.
- 2026-10-10 (implement, row 0138): changed assertions, none weakened.
  - `test_gates.TestLockstep.test_the_review_job_names_the_actions_it_runs_on`
    pins the action allow-list as an indented substring. The new `if:`
    nests the allow-list one group deeper, so the pinned continuation
    indent moved from 11 to 15 spaces. Same three actions, same strength.
  - `test_gates.TestWorkflowRunStepInvariant.ALLOWED["validator.yml"]`
    drops `set +e` and gains the three new openers (`set -o pipefail`,
    the delimiter line, and the `printf` data step), each with its
    reason. The pre-existing `gh api "repos/${GITHUB_REPOSITORY}/pulls/${PR}" \`
    entry already matches no step in the file (the shim became `make
    pr-event`). It is out of scope, logged here, and not removed.
  - `test_workflow_permissions`: every grant is byte-unchanged; only the
    `check` and `review` reason strings moved, as the row specifies.
- 2026-10-10 (implement, row 0141): the "over 200 KB" case cannot run the
  same way on every platform. The architecture's own failure-mode line
  says why: on Linux, one env string over 128 KiB cannot be exec'd. This
  is test mechanics, not a design disagreement, so the replay is split in
  two:
  - `test_a_hostile_hand_off_is_posted_inert_and_bounded` uses about
    100 KB. That is above the producer cap and the reader's bound, and
    below the exec limit. Every assertion runs on every platform.
  - `test_an_oversized_hand_off_is_bounded_or_fails_closed` uses over
    200 KB. Where exec allows it (macOS), it asserts the same inertness.
    On Linux it asserts `OSError` E2BIG and that no findings file exists,
    which is ADR-0098's closed failure.

  Both branches were exercised. macOS took the bounded branch. In
  `python:3.12-slim` under docker, a 210 KB env string raised `OSError
  errno 7 Argument list too long`, and the whole module passed there
  (14 tests OK).
- 2026-10-10 (implement, rows 0141 to 0143): mutation proofs. Each was
  applied, run, and reverted with `git checkout`; none is committed.
  - Row 0141, `render_findings` back to a fixed triple fence: 18
    failures. The hostile ten-backtick line closes the block, the
    `inside` text is empty, and the tail after the "close" is
    `"\n</details>\n@owner this is approved\n$[12027 chars]s>\n" != '\n\n</details>\n'`.
  - Row 0142, `set -o pipefail` deleted from the check step:
    `FAIL: test_a_failing_check_fails_the_step_and_keeps_its_output`,
    `AssertionError: 0 == 0`. A failing make turns the step green.
  - Row 0143, the delimiter fixed to `EOF`:
    `FAIL: test_delimiter_shaped_findings_stay_inside_one_capped_value`,
    `AssertionError: Lists differ: ['findings', 'findings'] != ['findings']`.
  - Boundary, `GH_TOKEN: ${{ secrets.FACTORY_REVIEW_TOKEN }}` put on
    check's "Detectors and tests" step: 2 failures,
    `check runs PR code holding {'GITHUB_TOKEN', 'FACTORY_REVIEW_TOKEN'}`
    and `AssertionError: 2 != 1 : ['check', 'review']`.
  - Boundary, review's checkout pointed back at
    `refs/pull/{0}/head`: 3 failures. `review runs PR code with a write
    grant`, `review runs PR code holding {...'FACTORY_REVIEW_TOKEN'}`,
    and the base-ref holder mismatch.
- 2026-10-10 (implement, rows 0144 and 0145): close-out on the final tree.
  ```
  cmp .github/workflows/validator.yml factory/templates/.github/workflows/validator.yml   -> 0
  cmp validator.py factory/templates/tools/factory/validator.py                           -> 0
  python3 factory_init.py update-manifest  -> factory-init: 0 problem(s); git status clean after
  .orig/.rej files on disk or in factory/manifest.json  -> none
  python3 -m unittest discover tests       -> Ran 2084 tests ... OK   (pre-run baseline 2066)
  python3 lint.py                          -> lint: 0 problem(s) across 26 skills
  python3 gates.py && python3 gates.py --selftest -> gates: 0 problem(s) / selftest: ok
  actionlint .github/workflows/validator.yml factory/templates/.github/workflows/validator.yml -> exit 0
  git diff origin/main -- assembler.yml (both) Makefile (both)  -> empty
  ```
  Each of the 13 checked rows has one zero-cost
  `owner-session:unmetered` row in `docs/factory/costs.jsonl`
  (detector G green). ADR-0098 stays `provisional`.
- 2026-10-10 (implement): proofs that only a live run can give. These go
  to release.md for the owner's combined post-merge live dispatch, and
  none is claimed here (architecture.md, "What only a live run proves"):
  - `needs.check.outputs.findings` is populated for `review` when
    `check` FAILED, under `always()`.
  - The random-delimiter multi-line output round-trips, and secret
    redaction does not drop ordinary findings.
  - The base-SHA checkout works on `pull_request`, and `github.sha` on a
    run the deliver job dispatched is the default branch.
  - The reviewer posts from the base job: the PAT identity check still
    resolves, and the comment lands as the reviewer.
  - The premise holds: a `GITHUB_TOKEN` push touching
    `.github/workflows/**` is refused.
  - `needs-review-label` still flips `wo:needs-review` from the base
    checkout on both triggers.
  - `persist-credentials: false` on `check` does not break `make check`.
    Nothing in it fetches from the remote, by grep.
