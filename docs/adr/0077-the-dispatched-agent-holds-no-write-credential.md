# The dispatched agent holds no write credential

- Status: provisional
- Date: 2026-10-10

Amends no record. ADR-0032's dispatch plane, ADR-0033's gates and
ADR-0034's stops stand; this decides where the assembler's write
credential lives relative to the agent it dispatches.

## Context

The first-live-dispatch review (`docs/features/first-live-dispatch/review.md`,
the Critical finding) found that the assembler's tool allowlist was
documented as "the push boundary" while carrying `Bash(python3:*)` and
`Bash(make:*)`. Either runs arbitrary code, and arbitrary code in the
dispatch job reached a `GITHUB_TOKEN` holding `contents`,
`pull-requests`, `issues` and `actions` write. There is no branch
protection on this plan (the protection endpoint answers HTTP 403), so
that token could push to `main`, approve the agent's own PR, flip its
order's labels and dispatch or cancel the validator. The subscription
token sat in the job's env, readable by the same code, and the raw
execution file was kept as a 14-day artifact on a public repo.

Narrowing the allowlist cannot close this. The SWE's job is to write
code and run the tests. Once Edit and any test runner are allowed, the
agent can run code it wrote. Two more facts close the obvious
half-measures. Both come from reading the pinned action
(`anthropics/claude-code-action@86180fa9`):

- `src/modes/agent/index.ts` calls `configureGitAuth`, which removes
  checkout's credential header and writes the action's `github_token`
  into the checkout's `origin` URL. So `persist-credentials: false` on
  checkout changes nothing.
- `src/entrypoints/run.ts` sets `GITHUB_TOKEN` and `GH_TOKEN` to that
  token in the process that launches the agent.

Whatever the token passed to the action can do, the agent's code can do.
GitHub scopes `GITHUB_TOKEN` per job, never per step. Steps in one job
also share a runner where the agent's code ran (with passwordless sudo,
and possibly processes it left running), so a later step cannot be
trusted with a write token either.

## Decision

1. **The assembler is three jobs on three runners.** `dispatch` holds
   `contents: read` and `issues: write`. It resolves the order and
   claims it, running only the repo's own code, before any agent
   exists. `agent` holds `contents: read` and nothing else. It runs the
   agent, then packages the agent's work. `deliver` holds the write
   grants. It starts from a fresh checkout and does every write: the
   push, the PR, the spend row, the failure label and the validator
   hand-off.
2. **The agent's work crosses as data, never as code.** The agent job
   hands over a git bundle of the order's branch, the PR body the
   agent left in `pr-body.md` (`assembler.PR_BODY_FILE`), and the
   execution record. The deliver job fetches exactly
   `refs/heads/<branch>` from the bundle, where the branch is
   `assembler.branch_for` from the dispatch job. It pushes that ref to
   its own name and opens the PR with the agent's body. A bundle that
   carries other refs brings nothing else across.
3. **The agent job runs no repo tool.** After the agent step the
   workspace belongs to the agent, Makefile and modules included. The
   packaging step is plain file and git glue for that reason.
4. **The token's grant is the push boundary, not the allowlist.**
   The allowlist keeps `make:*` and `python3:*`, because the SWE runs
   the gates, the tests and `update-manifest`. It drops the push and
   `gh pr create` entries, since either could only fail from a
   read-only job. The prompt tells the agent the workflow delivers.
5. **The model credential reaches only the action step.** The
   subscription token and API key are inputs to that one step. The
   dispatch job keeps them in its env only for the presence check that
   gates the claim, and it runs no agent code.
6. **What is kept is a record, not a transcript.** The agent job runs
   with `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`, the action's best-effort
   scrub of credentials from the agent's subprocess environments. Of
   the execution file, only the final result entry is handed off and
   kept as the 14-day artifact: cost, usage, turns and denied calls.
   The turn-by-turn tool output, where anything the agent printed
   would land, never leaves the runner.

## Consequences

- The SWE charter's grants ("push feature branches; open PRs") are now
  carried out by the workflow on the agent's behalf under dispatch.
  The charter text is unchanged: in an owner session the agent still
  does them itself.
- Not closed: anything the agent's code can do with what the agent job
  does hold. That includes reading the repo, sending the model
  credential out over the network on purpose, and writing to this
  run's artifact and cache scopes. It also includes misstating its own
  spend in the execution record it hands over, which was already
  possible before this change. These are limits on a deliberately
  hostile agent. The defect fixed here is an ordinary agent's reflex
  reaching `main`.
- Unverified until a live dispatch:
  - the action's write-permission check on the labeler passes with a
    read-only token, through the collaborator-permission endpoint
    under metadata read;
  - a job with `if: always()` runs its default-condition steps after a
    failed `needs` job;
  - a bundle cut in the agent's shallow checkout fetches cleanly into
    the deliver job's full clone (checked locally, not on a runner);
  - the scrub reaches the agent's Bash subprocesses from the job env.
    The action's docs say it reads the switch there, and its effect has
    not been observed. With no bubblewrap on the runner it gives no PID
    isolation, so it stops the reflex and not an adversary.
