# The reviewer's credential never meets the pull request's code

- Status: provisional
- Date: 2026-10-10

Amends no record. ADR-0033's agent reviewer and ADR-0077's split of the
assembler both stand. This ADR applies ADR-0077's rule to the next hop,
which ADR-0077 names as not closed: the validator's `review` job.

## Context

The validator's `review` job checked out the pull request's code and ran
`make check` on it. It then ran `make review` in the same job, which
means the PR's own `Makefile` and the PR's own `validator.py`, with
`GH_TOKEN` set to `FACTORY_REVIEW_TOKEN` (the reviewer account's PAT,
whose account holds the `write` role). The job's own `GITHUB_TOKEN`
carried `pull-requests: write`, and checkout persisted it into
`.git/config`. The assembler dispatches this job against every agent PR.
So the agent's code could speak as gate 3's reviewer, or post the PAT
inside its own findings
(`docs/fixes/the-reviewer-token-runs-agent-code/defect.md`).

Moving the token to a later step does not close this. GitHub grants a
token per job. Steps in one job also share a runner that the earlier
code controlled: `$GITHUB_ENV`, `$GITHUB_PATH`, the workspace, and
passwordless sudo.

The PAT's scopes are not known. The design therefore has to hold in the
worst case: a classic `repo` PAT.

## Decision

1. **The pull request's code runs only in `check`.** That job holds
   `contents: read` and `pull-requests: read` and nothing else. The old
   `review` job ran `make check` a second time. That run is gone. `check`
   now hands its own output to the reviewer.
2. **What crosses is one job output of plain text, and nothing else.**
   `check` declares a single output, `findings`: the captured output of
   `make check`, capped by the producer. Three things never come from
   that job's data. The verdict is `needs.check.result`, which GitHub
   computes, so it always agrees with the status check. The PR number
   and author come from the trusted job's own reading of the event. The
   work-order heading comes from the base tree's breakdown rows. A job
   output was chosen over an uploaded artifact on purpose. An artifact
   means a zip extraction and an extra action on the trusted runner, and
   it means trusting an artifact name that the code in `check` could
   overwrite with the runner's own Actions token.
3. **The reviewer job runs base code only.** It checks out the base
   commit with `persist-credentials: false`. On `pull_request` that is
   `github.event.pull_request.base.sha`. On `workflow_dispatch` it is
   the default branch by name
   (`refs/heads/<github.event.repository.default_branch>`), never
   `github.sha`. `github.sha` is the tip of whatever ref the dispatcher
   passed, and `gh workflow run validator.yml --ref <pr-branch> -f pr=N`
   is a recorded owner routine for refreshing a stale lifecycle check:
   on that dispatch `github.sha` is the agent's head. The agent cannot
   edit the definition, but it can be the branch the definition runs
   on, so the trusted checkout must not follow the dispatcher's ref.
   The same applies to every write-scoped job (Decision 6). The job runs
   no PR code and fetches no PR ref.
4. **The handed-over text is data at every step.**
   - It reaches the shell only through an `env:` value, never through a
     `${{ }}` inside `run:`.
   - It is written to a file by a step that holds no PAT.
   - It never sits in the environment of a `make` step. `make` imports
     every environment variable as a make variable, so a data variable
     whose name collides with a recipe variable such as `FINDINGS` would
     become shell text.
   - `validator.py`'s review path reads a bounded number of bytes and
     renders them inside a code fence longer than any run of backticks in
     the text. Findings therefore cannot close the fence and write prose
     in the reviewer's voice.
5. **The PAT reaches one step.** It appears only in the posting step's
   `env:`, and that step runs only base code.
6. **The same rule covers every write-scoped job in the workflow.**
   `needs-review-label` used checkout's default ref. On `pull_request`
   that ref is the PR's merge commit, so the PR's `Makefile` ran with
   `issues: write`. It now checks out the same base commit as the
   reviewer.

## Alternatives that lost

- **`workflow_run`, with the poster in a second workflow.** This is
  GitHub's documented pattern, and it would hold even against a PR that
  edits the workflow file. It loses because it adds a mirrored workflow,
  a cross-run artifact download, and an `actions: read` grant. The
  in-file split already holds under the premise stated below. If that
  premise fails, this is the next shape to adopt.
- **`pull_request_target`.** It runs the base definition with write
  tokens on every PR event. That is a larger trust surface than this fix
  needs. The workflow's own comment already rejects it.
- **Drop the reviewer account to `triage`.** Not chosen by the owner. It
  narrows what the PAT can do, but PR code still holds a credential.
- **Keep a separate read-only findings job.** It would leave `check`
  byte-identical, but `make check` would still run twice, and a verdict
  from a second run can disagree with the status check.

## Consequences

- **The reviewer judges a PR with the base's tools.** A PR that changes
  `validator.py`'s review rendering or the `review` target is reviewed
  by the old code. Its change takes effect only after merge. A PR that
  adds its own breakdown row gets the "(no work order resolved)"
  heading, which is cosmetic (`run_review` already tolerates it).
- **Findings that need the PR's tree are all computed in `check`.**
  Detectors, tests and detector B's body read are all there, so the
  reviewer loses no finding.
- **Premise, not proven here:** a branch the assembler's deliver job
  pushes cannot change `.github/workflows/**`, because `GITHUB_TOKEN`
  has no `workflows` permission. On `pull_request`, GitHub runs the
  workflow definition from the PR's merge commit. A PR able to edit
  `validator.yml` would choose its own jobs, and no split inside that
  file could stop it. A dispatched run's definition comes from the
  dispatched ref: the deliver job passes none, so it is the default
  branch. A `--ref <pr-branch>` dispatch runs that branch's copy of
  this file, which the agent cannot have edited, and Decision 3 keeps
  its trusted checkouts off the branch. A branch cut before this ADR
  merged still carries the old file, so dispatching on one runs the old
  review job; rebase such a branch before a `--ref` dispatch, or
  dispatch on the default branch. A human-authored same-repo
  branch is outside the threat model: anyone who can push a branch can
  already add a workflow that reads repository secrets. Closing that is
  an owner action, such as scoping the PAT to a protected environment,
  not a code change.
- **Not closed:**
  - Code in `check` still holds that runner's Actions runtime token.
    On a dispatched run the cache scope is the default branch. As in
    ADR-0077, no workflow here restores a cache today.
  - An oversized output can stop the reviewer's step from starting. The
    job goes red and nothing is posted, so the failure is closed, not
    forged.
- **Unverified until a live run:**
  - A failed `check` still exposes its outputs to a dependent job that
    runs under `always()`.
  - The output survives GitHub's secret redaction for ordinary findings.
  - The base-SHA checkout succeeds on both triggers.
  - The premise above holds.
