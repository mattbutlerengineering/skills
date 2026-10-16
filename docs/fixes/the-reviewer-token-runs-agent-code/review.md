---
stage: review
run: maintenance:the-reviewer-token-runs-agent-code
date: 2026-10-10
assumptions:
  - "Scope is git diff origin/main...HEAD on fix/reviewer-token-boundary at 4e7267c (verification PASS), read against defect.md's Expected clause, architecture.md, ADR-0098 and breakdown.md. assembler.yml was read for reachability only (who dispatches, with what ref)."
  - "Severity rubric: Critical = the fix's own Expected clause (no step that runs PR code holds the reviewer PAT or a write-scoped token) is violated on a path the factory or its owner actually takes. Major = a real failure scenario that needs an unusual actor or state. Minor = drift, cosmetics, or an unverified runtime behaviour that fails closed."
  - "This stage fixed the one Critical on the branch, test-first, as row 0149 with a $0 owner-session ledger row matching rows 0133 to 0145. The brief authorises fixing criticals and majors here."
  - "The --ref dispatch is not hypothetical: the owner's recorded routine for refreshing a stale lifecycle check is `gh workflow run validator.yml --ref <pr-branch> -f pr=<N>` (used 2026-10-07 on #604 and #600)."
  - "The Makefile header comment drift (Minor 2) is deferred rather than fixed because row 0145's acceptance pins `git diff origin/main -- Makefile factory/templates/Makefile` empty for this run."
  - "Standards: docs/standards.json holds four statements; stdlib-only is honoured and none matches a finding, so no finding cites a slug."
---

# Review: the reviewer token never meets agent code

## Scope

`git diff origin/main...HEAD` (ef7d5e4..4e7267c): `validator.yml` and its
mirror, `validator.py` and its mirror, `tests/test_validator_workflow.py`
(new), `tests/test_validator.py`, `tests/test_gates.py`,
`tests/test_workflow_permissions.py`, ADR-0098, the manifest, the ledger,
and the run artifacts. The adversarial questions from the brief were each
followed to a verdict; they are answered below, finding or not.

## Findings

### Critical: a `--ref <pr-branch>` dispatch put the PR branch's Makefile beside the PAT

- Scenario: `review` and `needs-review-label` checked out
  `github.sha` on `workflow_dispatch`. `github.sha` is the tip of the
  ref the dispatcher passes, not the default branch. The owner's
  recorded routine for a stale lifecycle check is
  `gh workflow run validator.yml --ref <pr-branch> -f pr=N`. On that
  dispatch the workflow definition is the PR branch's copy of
  `validator.yml`. The agent cannot have edited that copy (the
  workflows-permission premise holds), so it is this fixed file, but
  its `review` job then checks out the agent's head and runs the
  agent's `Makefile` (`make pr-event`, `make review`) with
  `GH_TOKEN=FACTORY_REVIEW_TOKEN`. `needs-review-label` runs the agent's
  `make wo-needs-review` with `issues: write`. This violates defect.md's
  Expected clause. Verification filed it as "the stated premise", but
  it is not: the premise is about who writes the definition, and here
  the definition is honest and only its checkout follows the attacker's
  branch. An in-file change closes it. The suite missed it because
  `pr_controlled()` treats only a missing `ref:` or `refs/pull/` as
  PR-controlled, and `github.sha` matched neither.
- Standard: none
- Decision: fixed in 178034d (row 0149). Both trusted jobs now check out
  `github.event.pull_request.base.sha` on `pull_request` and
  `format('refs/heads/{0}', github.event.repository.default_branch)` on
  `workflow_dispatch`. The new test
  `test_no_write_holding_checkout_follows_the_dispatchers_ref` asserts
  that every job holding a write grant or a non-`GITHUB_TOKEN` secret
  (except `merged-label`) checks out that ref and names neither
  `github.sha` nor `github.ref`. Before the fix it was RED with
  `FAILED (failures=3)`: its own two subtests (review and
  needs-review-label) plus the reviewer-token base-checkout test, which
  pins the same ref. The deliver job's no-`--ref` dispatch is
  unchanged: on the default branch the two refs name the same commit.
  ADR-0098 Decision 3 and its premise paragraph were amended to say so.
  Residual risk, stated in the ADR and not closable in-file: a branch cut
  **before** this merges carries the old `validator.yml`, so a `--ref`
  dispatch on it runs the old review job. Rebase such a branch first, or
  dispatch on the default branch.

### Minor 1: one unbounded `inputs.pr` reaches a make recipe unquoted (pre-existing)

- Scenario: `PR: ${{ inputs.pr }}` is passed to `make pr-event PR="$PR"`.
  The recipe expands `--pr $(PR)` unquoted into shell, so
  `-f pr='1; id'` runs `id` in the trusted job, on the runner the PAT
  step later uses. Only a dispatcher can set `inputs.pr`, and dispatching
  needs write. The one automated dispatcher, deliver, passes `find-pr`'s
  numeric API result. No lower-privilege actor reaches it, and an actor
  with write can already push a workflow that reads secrets. The diff
  neither creates nor widens the problem.
- Standard: none
- Decision: deferred. It is out of the brief's scope, and the actor
  already holds a stronger capability. The cheap close is a numeric
  guard (`case "$PR" in ''|*[!0-9]*) exit 2;; esac`) before `make`, in
  all three jobs. That belongs in a seed for its own run, not in this
  diff.

### Minor 2: the Makefile header still describes "the review job's exit-code capture"

- Scenario: the root `Makefile` header (lines 6-7) names plumbing the
  workflow no longer has. The workflow's own header was updated, and the
  Makefile's was not. A reader would look for a capture that is gone.
- Standard: none
- Decision: deferred. Row 0145 pins the Makefile byte-identical to main
  for this run. Fold it into the next run that touches the Makefile.

### Minor 3: `head -c 65536` can split a UTF-8 character at the cap

- Scenario: when the output exceeds 64 KiB, the hand-off may end
  mid-character. If the runner refuses or mangles an invalid UTF-8
  output, the reviewer posts a shortened body or none. The trusted side
  already decodes with replacement, so nothing is forged either way.
- Standard: none
- Decision: deferred. It is a runner-only behaviour and fails closed.
  It joins verification's live-only list for the owner's post-merge
  dispatch.

### Minor 4: cosmetics in the new tests

- Scenario: in `tests/test_validator.py`, `TestRenderFindings` has a
  double blank line inside the class and only one before
  `class TestRunReview`. This matters to no behaviour.
- Standard: none
- Decision: deferred. Style only, and the codebase enforces no
  formatter.

## Adversarial questions answered with no finding

- **A PR that edits `validator.yml` on `pull_request`.** Agent PRs reach
  `pull_request` only through a human action (push, reopen, update
  branch), because GITHUB_TOKEN-opened PRs are event-suppressed. Their
  branches are pushed by deliver with `GITHUB_TOKEN`, which GitHub
  refuses for any `.github/workflows/**` change. Humans with write are
  out of the threat model, and ADR-0098 says so honestly with
  `workflow_run` as the fallback. A mechanical guard (review refusing a
  diff that touches `.github/workflows/`) was weighed and rejected: the
  guard would live in the very file the attacker edits, so it stops only
  the honest. The real remedy for the human case is an owner action
  (an environment-scoped PAT), not code.
- **`needs.check.outputs.findings` under `always()`.** The `if:` admits
  exactly `success` and `failure`. `cancelled` and `skipped` (the closed
  action) do not reach the job, and the event allow-list is unchanged.
  Nothing else crosses: the job declares one output, `$GITHUB_ENV`,
  `$GITHUB_PATH` and the workspace are per-runner, no cache is restored,
  no artifact is downloaded, and the verdict is `needs.check.result`,
  which GitHub computes. Hostile code in `check` can forge the
  `findings` text entirely (it owns that runner, including `od` and
  `head`), and the design treats it as attacker-chosen throughout. That
  failed-job outputs are populated is still live-only, as verification
  lists.
- **make env shadowing.** The make steps in `review` carry `GH_TOKEN`,
  `FACTORY_REVIEW_TOKEN_SET`, `FACTORY_REVIEW_LOGIN`, `CHECK_RC` (computed
  by GitHub) and the shim's `PR` (also assigned on the command line,
  which wins). None of them is a recipe variable with untrusted content.
  `HANDED_OVER` sits only in the make-free write step, and a test pins
  that.
- **`render_findings` fence.** It counts every backtick run anywhere in
  the text, after truncation. A CommonMark closer must be a backtick run
  at least as long as the opener: an indented one (up to 3 spaces) or one
  followed by `\r` is still shorter, and a `~~~` line can never close a
  backtick fence. The bounded read (4 bytes x cap) with replacement is
  correct. The `|| true` on `head` covers a check that died before
  `tee` ran; it posts an empty FAIL, which is honest.
- **`persist-credentials: false` on `check`.** `make check` runs lint,
  gates, the selftest and unittest. None of them calls networked git
  (`gates.py` runs no git, and tests use local scratch repos).
- **Tests.** The boundary and replay suites run the workflow's own
  `run:` scripts and the real `validator.py`, not restatements. Mutation
  proofs are recorded in breakdown.md Notes. Importing the parse
  helpers from `test_assembler` keeps one owner of what a job is; it
  holds under `discover` and the `sys.path` insert.

## Passes with no findings

Design: the code matches architecture.md's contracts, except the
dispatch ref that the Critical above corrected (architecture.md's
"`github.sha` for dispatch" decision is superseded by ADR-0098's
amended Decision 3). Security: clean after the fix. The remaining
items are pre-existing (Minor 1) or runner-only and fail closed
(Minor 3).

## Battery (after 178034d)

```
$ python3 -m unittest discover tests 2>&1 | grep -E "^(Ran|OK|FAILED)"
Ran 2085 tests in 28.477s
OK
$ python3 lint.py
lint: 0 problem(s) across 26 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
$ actionlint .github/workflows/validator.yml factory/templates/.github/workflows/validator.yml
(exit 0)
$ cmp .github/workflows/validator.yml factory/templates/.github/workflows/validator.yml
(exit 0)
```

## Verdict

Ready to ship. The one Critical is fixed on the branch. No Critical or
Major is open. Ship adds this to the owner's combined post-merge live
dispatch: one `--ref <pr-branch>` dispatch, to check that `review` and
`needs-review-label` check out the default branch, not the PR head. Open
owner question carried from verification: what are `FACTORY_REVIEW_TOKEN`'s
scopes?
