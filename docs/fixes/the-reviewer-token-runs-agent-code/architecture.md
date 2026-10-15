---
stage: architect
run: maintenance:the-reviewer-token-runs-agent-code
date: 2026-10-10
ux: not-applicable — a CI workflow, no user-facing surface
assumptions:
  - "No live interview: answers come from autorun-brief.md and defect.md. Where neither covers a question, the architect skill's default was taken and logged here."
  - "Branch fix/reviewer-token-boundary has origin/main (41f3266, which includes #629's merge 1aa5e54) merged into it, as the coordinator instructed. The merge was clean, with no costs.jsonl conflict. After it the full battery was green (2066 tests OK, lint 0, gates 0, selftest ok). ADR-0077 is now on this branch, so it is cited by id."
  - "An ADR is written (0098). It passes the skill's three-part bar. Hard to reverse: every stamped repo inherits the workflow shape. Surprising without context: the reviewer runs base code against a PR, its verdict is another job's result, and no env name may shadow a make variable. A real trade-off: an in-file split against workflow_run, pull_request_target, or a triage role."
  - "Scope reading: defect.md's Expected clause says 'any write-scoped token'. needs-review-label checks out the PR's merge commit on pull_request and runs make with issues: write, so it falls inside that clause. Its fix is a one-line checkout ref. merged-label is left alone: on closed+merged the code it runs has already passed the human merge gate."
  - "Form of the hand-off (left open by the brief): a job output, not an uploaded artifact. The brief's word 'artifact' is read generically, and the trade is recorded under Decisions."
  - "The check job is the producer. There is no separate findings job. This removes the second `make check` run and makes the verdict agree with the status check by construction."
  - "persist-credentials: false goes on the checkouts this run touches (check, review, needs-review-label), not on merged-label. That job runs only merged code, and leaving it alone keeps the change surgical."
  - "The premise that GITHUB_TOKEN cannot push changes to .github/workflows/** is documented GitHub behaviour. This run cannot test it. It is listed under live-only proof."
  - "The reviewer PAT's scopes are still an open owner question. The design holds under a classic `repo` PAT, the worst case, and nothing below depends on the answer."
---

# Architecture: the reviewer token never meets agent code

## Approach

Split by **trust**, not by step. The pull request's code runs only in the
`check` job, which already holds read-only grants. That job hands its
captured `make check` output across as **one job output of plain text**.
The `review` job then checks out the **base** commit, runs only that
code, and posts. It gets the verdict from GitHub (`needs.check.result`),
the PR identity from the event or a base-code `make pr-event`, and the
findings as bounded data rendered inertly. The reviewer PAT appears in
one step's `env:`.

A step reorder was considered and lost. Steps share a runner, so an
earlier step running PR code can poison a later one through
`$GITHUB_ENV`, `$GITHUB_PATH`, `BASH_ENV`, or the workspace. That leaves
the job as the smallest boundary. ADR-0077 reached the same conclusion
for the assembler.

### Job graph

```
                     pull_request (opened|reopened|synchronize|edited, same-repo or fork)
                     push            workflow_dispatch(pr=N)   ← #629's deliver job, unchanged
                          │                │
                          ▼                ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │ check            contents:read  pull-requests:read   ← PR CODE RUNS   │
  │  if: action != 'closed'                                              │
  │  checkout ref: dispatch ? refs/pull/N/head : default (merge ref)     │
  │  persist-credentials: false                                          │
  │  [dispatch] make pr-event  (PR's code, read token — harmless)        │
  │  make check 2>&1 | tee findings   (pipefail: the gate's exit code)   │
  │  [!cancelled()] hand-off → $GITHUB_OUTPUT findings<<random-delim     │
  │  outputs: findings                                                   │
  └───────────────────────────────┬──────────────────────────────────────┘
                                  │ needs: check     (DATA: one string ≤1 MB;
                                  │                   verdict = needs.check.result)
                                  ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │ review           contents:read  pull-requests:write  ← BASE CODE ONLY │
  │  if: always()                                                        │
  │      && (needs.check.result == 'success' || == 'failure')            │
  │      && ( (pull_request && action ∈ {opened,reopened,synchronize}    │
  │            && head.repo == github.repository)                        │
  │           || workflow_dispatch )                                     │
  │  checkout ref: pull_request ? event.pull_request.base.sha : github.sha│
  │  persist-credentials: false                                          │
  │  [dispatch] make pr-event PR=$PR   (base code, GITHUB_TOKEN read)    │
  │  write findings: env HANDED_OVER → printf to $RUNNER_TEMP file       │
  │                  (no PAT, no make)                                   │
  │  post: env GH_TOKEN=PAT, FACTORY_REVIEW_TOKEN_SET, _LOGIN, CHECK_RC  │
  │        make review FINDINGS=<file> STATUS="$CHECK_RC"                │
  └──────────────────────────────────────────────────────────────────────┘

  needs-review-label   (unchanged trigger/grants)  checkout → same base expression,
                       persist-credentials: false
  merged-label         unchanged
```

## Components

### `check` job (`validator.yml`): the only job that runs PR code

- Responsibility: run the gate on the PR's tree and capture what it says.
  Its exit status is still the gate-3 status check (ADR-0033).
- Changes:
  - The "Detectors and tests" step becomes `set -o pipefail` plus `make
    check 2>&1 | tee "$RUNNER_TEMP/findings.txt"`. The explicit pipefail
    is load-bearing: a `run:` with no `shell:` executes as `bash -e {0}`,
    which has no pipefail, so without it the gate would go green on a
    failing check.
  - A new step, "Hand the findings to the review job", with `if: ${{
    !cancelled() }}`. It writes `findings<<$delim` to `$GITHUB_OUTPUT`,
    where the delimiter is random per run and the body is `head -c 65536`
    (the producer cap, kept well under Linux's 128 KiB per-env-string
    limit). Then the job-level `outputs: findings`.
  - `persist-credentials: false`.
- Grants: unchanged (`contents: read`, `pull-requests: read`).
- Collaborators: the `review` job, through `needs`.

### `review` job (`validator.yml`): base code, holds the PAT

- Responsibility: post the reviewer's comment as a non-authoring actor
  (PRD-0001, ADR-0033), using only base-ref code.
- Steps:
  1. Checkout with `ref:` set to the base expression (below) and
     `persist-credentials: false`.
  2. setup-python.
  3. On dispatch only: `make pr-event PR="$PR"`, with `PR: ${{ inputs.pr
     }}` passed through env, as today, but now from the base checkout.
  4. "Write the handed-over findings". Env: `HANDED_OVER: ${{
     needs.check.outputs.findings }}`. Run: `printf '%s' "$HANDED_OVER" >
     "$RUNNER_TEMP/findings.txt"`. No secret and no make in this step.
  5. "Post findings as a non-authoring actor". Env: `GH_TOKEN`,
     `FACTORY_REVIEW_TOKEN_SET` and `FACTORY_REVIEW_LOGIN` as today, plus
     `CHECK_RC: ${{ needs.check.result == 'success' && '0' || '1' }}`.
     Run: `make review FINDINGS="$RUNNER_TEMP/findings.txt"
     STATUS="$CHECK_RC"`.
- Grants: unchanged (`contents: read`, `pull-requests: write`). The write
  grant covers the `GITHUB_TOKEN` fallback when no PAT is set.
- Collaborators: `check` (data only); `validator.py` `run_review` from
  the base tree.

### `validator.py` review path: the parser of the hand-off (base code)

- Responsibility: turn the untrusted findings file into an inert comment
  body.
- Changes, both inside the existing functions:
  - `run_review` reads at most `4 * MAX_FINDINGS_CHARS` bytes, which is
    the worst UTF-8 width of the rendered cap, and decodes them with
    `errors="replace"`. It no longer refuses non-UTF-8 input; it reads
    bytes instead of `read_text`.
  - `render_findings` fences the output with a run of backticks one
    longer than the longest run inside it, minimum three. Today's fixed
    triple fence is gone.
- Unchanged: `MAX_FINDINGS_CHARS` stays the one owner of the size rule.
  `reviewer_login`, `actor_conflict`, `declared_conflict`,
  `cited_work_order` and `post_review` are untouched. The PR number and
  author still come only from `_pull_request(env)`, the event, never
  from the findings.

### `needs-review-label` job: same class, one-line fix

- Its checkout gains the base `ref:` expression and `persist-credentials:
  false`. The intent of its existing comment ("the breakdown row the flip
  reads landed on the default branch") was already base. The default ref
  on `pull_request` silently broke that intent.

### Payload mirror and manifest

- `factory/templates/.github/workflows/validator.yml` is an identity
  mirror (`factory_init.MIRRORS`). `tools/factory/validator.py` is also
  identity. The Makefile is untouched: `review` and `pr-event` keep their
  recipes. Implement runs `python3 factory_init.py update-manifest` and
  commits the manifest.

## Data model

There is one crossing, and it has a single shape:

| Field | Source | Trust | Consumer |
|---|---|---|---|
| `needs.check.outputs.findings` | `check` job's `$GITHUB_OUTPUT` | **untrusted** text, ≤1 MB (GitHub cap) | the review job's write step, then the `run_review` bounded read |
| `needs.check.result` | GitHub | trusted enum | the `CHECK_RC` expression (`success`→0, otherwise 1) |
| PR number, author, body | `GITHUB_EVENT_PATH` (pull_request), or base-code `make pr-event` (dispatch) | trusted transport; the body is author prose and is used only by the `cited_work_order` regex | `run_review` |
| `inputs.pr` | dispatcher (write collaborators / deliver job) | validated `isdigit` by `validator.parse` | `make pr-event` |

No other job output is declared on `check`. An undeclared key that the
delimiter trick could inject is therefore invisible to `review`.

## Interfaces & contracts

### Hand-off: `check` → `review`

- Input: the combined stdout and stderr of `make check` on the PR's tree.
- Output: `needs.check.outputs.findings` (string) and
  `needs.check.result`.
- Contract, from the trusted side's point of view:
  - The string is attacker-chosen. It may be empty, oversized,
    non-UTF-8 once written to a file, or full of markdown, backticks,
    `@mentions`, shell metacharacters, or something shaped like a
    delimiter.
  - It is never interpolated by `${{ }}` into `run:`.
  - It is never present in the environment of a `make` invocation (make
    imports env as variables).
  - It is never passed to a step that holds the PAT.
  - It names nothing: not the PR, not the verdict, not the ref.
- Failure modes:
  - `check` cancelled or skipped: `review` is skipped and nothing is
    posted.
  - Output redacted, because it contained a registered secret: the string
    is empty. The reviewer posts the verdict with an empty findings
    block.
  - Output over about 128 KiB (possible only when the producer is
    hostile): the write step cannot exec (E2BIG), the review job goes
    red, and nothing is posted. The failure is closed, never forged.
  - There is nothing to retry. A re-run replays the same event.

### `run_review(root, findings, status, env, run)` (existing signature)

- Input: the findings path (untrusted bytes), `status` 0 or 1 (from
  `CHECK_RC`), and the env carrying the event plus the token provenance.
- Output: the problems list. It posts one comment (edit-last, else new),
  as today.
- Failure modes: unchanged, plus no `UnicodeDecodeError` path. An
  unreadable file is still `V: cannot read findings file …`.

### Base ref per trigger

- `pull_request`: `github.event.pull_request.base.sha`. This is a SHA
  from GitHub's event, on the base branch. It is pinned, and a later push
  to main cannot move it mid-run.
- `workflow_dispatch`: `github.sha`, the tip of the dispatched ref at
  dispatch time, and the same commit the running workflow definition came
  from. #629's deliver job runs `gh workflow run validator.yml -f pr=N`
  with no `--ref`, so this is the default branch. That interface is
  unchanged.
- Both values sit in `with: ref:`, never in `run:`. The review job runs
  no `git fetch` of PR refs, so ADR-0077's tag-follow hazard has no
  surface here.

## Stack & dependencies

- No new action and no new tool. `actions/checkout@v4` and
  `actions/setup-python@v5` as today. No `upload-artifact` or
  `download-artifact` on this path. Stdlib only.

## Decisions & alternatives

- **Job output** over **uploaded artifact**. An artifact needs a zip
  extraction on the PAT runner, which is a path-traversal surface
  (download-artifact's zip-slip history) able to overwrite the base
  checkout before `make review` runs. It also needs another third-party
  action in the trusted job, and an artifact name that code in `check`
  can re-upload using that runner's `ACTIONS_RUNTIME_TOKEN`.
- **Fold into `check`** over **a separate read-only findings job**. A
  separate job keeps `check` byte-identical, but it runs `make check`
  twice and its verdict can disagree with the status check. The fold's
  risk, a broken pipefail turning the gate green, is pinned by a replay
  test.
- **Verdict from `needs.check.result`** over **a self-reported exit
  code** in the hand-off. The data then carries only text, and the
  reviewer's PASS/FAIL can never contradict the gate.
- **In-file split** over **`workflow_run`**. `workflow_run` survives a PR
  that edits `validator.yml`, but it costs a second mirrored workflow, a
  cross-run artifact download, and `actions: read`. The in-file split
  holds under the premise that the agent cannot push workflow edits (see
  live-only proof). ADR-0098 names `workflow_run` as the next shape if
  that premise fails.
- **`pull_request_target`**: rejected. It is not required, and it would
  give write tokens to every PR event (the workflow's own comment).
- **Reviewer to `triage`**: rejected by the owner (brief).
- **`github.sha` for dispatch** over **the PR's `base.sha` read from the
  API**. The checked-out code then matches the running definition, and no
  value derived from data picks the trusted ref.
- **The write step separate from the post step** over **one step**.
  Merging them would put attacker text in the env of the step that holds
  both the PAT and `make`.
- **Fence widening in `render_findings`** over **escaping**. It is
  CommonMark-exact, keeps the output literal, and is a few lines.
- Standards: `stdlib-only` is honoured, with no new dependency.

## What the reviewer can no longer do

- Run the PR's `Makefile` or `validator.py`. A PR that changes the
  review path is reviewed by the base version, and its change applies
  after merge.
- Resolve a work-order heading from a breakdown row the PR itself adds.
  That case now reads "(no work order resolved)", which is cosmetic
  (`run_review`'s own comment).
- Run `make check` itself. Every finding that needs the PR's tree
  (detectors, tests, detector B's body read) is computed in `check` and
  arrives as text.

## Test strategy (for Decompose / Implement)

1. **RED first, the reproduction.** A static boundary test over
   `validator.yml`, modelled on `TestAgentCredentialBoundary`
   (`tests/test_assembler.py`). It parses the jobs with the repo's
   existing hand-parse helpers, and calls a checkout *PR-controlled* when
   it has no `ref:` (the default is the merge ref on `pull_request`) or
   its `ref:` names `refs/pull/`. It asserts four things:
   - no job with a PR-controlled checkout holds a `write` grant;
   - no such job names any `secrets.` other than `GITHUB_TOKEN`;
   - every checkout in `check`, `review` and `needs-review-label` has
     `persist-credentials: false`;
   - `FACTORY_REVIEW_TOKEN` appears in exactly one step, in a job whose
     checkout is the base expression.

   On the current file it goes RED on `review` (both the grant and the
   secret) and on `needs-review-label` (the grant).
2. **Trusted-job static pins.**
   - No `${{` inside any `run:` of `review`.
   - `needs.check.outputs` appears only in the write step's `env:`, and
     that step names no secret and runs no `make`.
   - No step that runs `make` carries an env key equal to a variable the
     root Makefile assigns (parsed from `^NAME ?=`/`=` lines).
   - `review` `needs: check`, and its `if:` admits only `success` or
     `failure` and keeps the fork guard and both triggers.
3. **Hostile hand-off replay.**
   - Run the review job's write step script (read out of the YAML, as
     `TestBundleCannotReachMain` does) under bash with `HANDED_OVER` set
     to a hostile string: nested backtick runs longer than three,
     `</details>`, `@owner`, `$(touch pwned)`, `` `id` ``, a fake
     `**Detectors and tests: PASS**`, delimiter-shaped lines, and over
     200 KB. Then call `validator.main(["review", …, "--status", "1"])`
     with `FakeGh` and an event fixture.
   - Assert that no `pwned` file exists, and that the verdict is FAIL
     (from status, whatever the text says).
   - Assert that the posted body is bounded, and that every hostile line
     sits inside a fence longer than its longest backtick run.
   - Assert that the comment goes to the event's PR number.
   - Add a non-UTF-8 file case: it renders with no refusal.
4. **Gate-preservation replay.** Run `check`'s capture step script with a
   stub `make` on PATH that prints and exits 1. The step must exit
   nonzero and the file must hold the output. With exit 0, it must exit
   zero.
5. **Producer robustness (honest path).** Replay the hand-off step and
   parse `$GITHUB_OUTPUT` as GitHub does. Output containing
   `EOF`/`findings<<` lines yields exactly one `findings` key holding the
   capped text.
6. **Existing suites to update.**
   - `tests/test_workflow_permissions.py`: the recorded grants are
     **unchanged**, so only the `review` and `check` reason strings change
     (review: "posts the review comment from a base checkout; runs no PR
     code"; check: "… and hands its findings to review").
   - `tests/test_gates.py`'s make-only `ALLOWED["validator.yml"]`: the
     `set +e` opener is replaced by the new step openers (`set -o
     pipefail`, the delimiter line, and `printf '%s' "$HANDED_OVER" >
     …`), each with its reason.
   - `TestValidatorDispatchLockstep`: the shim count still equals the
     `make pr-event` count.
   - The payload byte-identity and the manifest, through
     `update-manifest`.
   - `tests/test_validator.py`: `TestRenderFindings` and `TestRunReview`
     gain the fence-widening and bounded-read cases.

## What only a live run proves

The live proof folds into the owner's combined post-merge live dispatch.

- `needs.check.outputs.findings` is populated for a dependent job when
  `check` **failed**, under `always()`.
- Multi-line output with a random delimiter round-trips, and ordinary
  findings are not dropped by secret redaction.
- The base-SHA checkout works on `pull_request`, and `github.sha` on a
  deliver-dispatched run is the default branch.
- The reviewer posts from the base job. The PAT identity check still
  resolves, and the comment lands as the reviewer.
- **Premise:** a `GITHUB_TOKEN` push (the deliver job) of a branch
  touching `.github/workflows/**` is refused. On `pull_request` the
  workflow definition comes from the PR's merge commit, so this premise
  is what makes the in-file split sufficient on that trigger. A dispatched
  run is unaffected.
- `needs-review-label` still flips `wo:needs-review` from the base
  checkout on both triggers.

## Open owner question (does not block)

- What are `FACTORY_REVIEW_TOKEN`'s scopes? A classic PAT with scopes, or
  fine-grained with which repository permissions? The answer settles
  major against critical. The design is unchanged either way.
- Optional hardening (an owner action, out of scope): put the PAT in a
  GitHub environment restricted to the default branch. That would also
  cover the human-pushed-branch residual named in ADR-0098.

## ADRs

- [ADR-0098](../../adr/0098-the-reviewer-credential-never-meets-pr-code.md),
  the reviewer's credential never meets the pull request's code
  (provisional until the live run). It applies ADR-0077's rule to the hop
  ADR-0077 names as not closed.
