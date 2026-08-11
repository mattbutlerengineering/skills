# Plan 014: Advance the work-order lifecycle — `wo:in-progress` at dispatch, `wo:needs-review` at PR open

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 2e63a04..HEAD -- validator.py Makefile factory/templates/Makefile .github/workflows/assembler.yml .github/workflows/validator.yml tests/test_validator.py tests/test_gates.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: plans/013-cli-gh-json-and-windowed-lists.md (the new
  gh call added here must use `cli.gh_json`; if 013 hasn't landed,
  STOP and either land it first or get the operator's explicit call)
- **Category**: bug
- **Planned at**: commit `2e63a04`, 2026-08-02

## Why this matters

ADR-0032 and `docs/features/software-factory/architecture.md` document
the work-order lifecycle `wo:ready-for-agent → wo:in-progress →
wo:needs-review → wo:merged`. In code, the **only** label writer is
`validator.run_lifecycle`, and the only automated invocation is
`make wo-merged` (validator.yml's merged-label job). Nothing ever applies
the two middle labels. Three concrete costs:

1. The documented state machine is fiction between dispatch and merge —
   an issue sits on `wo:ready-for-agent` for its whole life.
2. `gate_digest.gate_passages` measures the merge gate as
   `wo:needs-review` removed + `wo:merged` applied
   (`gate_digest.py:51-55`); since `wo:needs-review` never appears, the
   merge-gate queue is permanently "(empty)" and a third of the
   ADR-0041 gate-latency substrate is never captured.
3. A repeated `labeled` event queues a **second paid dispatch**
   (`assembler.yml`'s `concurrency: cancel-in-progress: false` *queues*
   repeats — its comment claims it dedupes, which is wrong). Flipping to
   `wo:in-progress` immediately after resolve gives dispatch an
   idempotency marker: the claim step detects the order is no longer in
   `ready` state and the agent step is skipped.

## Current state

- `validator.py`:
  - `transition(names, lifecycle, label)` — tested pure helper computing
    `(add, remove)` to leave **exactly one** lifecycle label
    (ADR-0032's invariant); see `tests/test_validator.py:159-161`.
  - `run_lifecycle(root, label, env, run=gh_runner)` (line ~285) — the
    merged-label leg: resolves the PR from `$GITHUB_EVENT_PATH`, the WO
    from the PR body (`cited_work_order`), the issue number from the
    breakdown row (`tracker_issue`), reads live labels
    (`gh issue view --json labels`), computes `transition`, and runs
    `gh issue edit --add-label/--remove-label`. **Strict**: a PR with no
    cited WO is a problem (correct for the mutating merged leg).
  - `parse(argv)` (line ~325): `lifecycle` accepts exactly
    `{"label"}` as options.
- `Makefile`: `wo-merged: python3 validator.py lifecycle --label
  wo:merged`; `FINDINGS ?=`/`STATUS ?=` at the top show the
  variable-passing idiom. `factory/templates/Makefile` is the
  hand-maintained product-repo twin (`tools/factory/validator.py` paths);
  `tests/test_gates.py::TestLockstep` pins both via
  `tests/make_parse.py::make_recipe` and a `product_form` transform.
- `.github/workflows/assembler.yml`: `permissions:` on the dispatch job
  already include `issues: write`. Steps: resolve (`make assembler`,
  id `resolve`, emits `dispatch`/`prompt`/`model` outputs) → agent step
  (`anthropics/claude-code-action@v1`,
  `if: steps.resolve.outputs.dispatch == 'true' && env.ANTHROPIC_API_KEY != ''`).
  Lines 24-27:
  ```yaml
  # Don't dispatch the same work order twice if the label event repeats.
  concurrency:
    group: assembler-${{ github.event.issue.number }}
    cancel-in-progress: false
  ```
  (The comment is wrong: `cancel-in-progress: false` queues, it does not
  drop.)
- `.github/workflows/validator.yml`: three jobs — `check`, `review`
  (on `pull_request` opened/reopened/synchronize, same-repo only),
  `merged-label` (on closed+merged → `make wo-merged`). Both workflows
  are mirrored verbatim into the payload (`factory_init.MIRRORS`);
  editing them requires `python3 factory_init.py update-manifest`.
- `cli.gh_json(args, run, expect)` — from plan 013: returns
  `(value, problem-suffix)`; `CLI_FAILURES` still raise through.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Full local gate | `make check` | exit 0 |
| Affected suites | `python3 -m unittest tests.test_validator tests.test_gates -v` | all pass |
| Refresh mirrors + manifest | `python3 factory_init.py update-manifest` | exit 0 |

## Scope

**In scope**:
- `validator.py`, `Makefile`, `factory/templates/Makefile`
- `.github/workflows/assembler.yml`, `.github/workflows/validator.yml`
- `tests/test_validator.py`, `tests/test_gates.py`
- `factory/templates/**`, `factory/manifest.json` — workflow/tool
  mirrors only via `update-manifest` (the template **Makefile** is
  hand-edited, that's its convention)
- `plans/README.md` (status row)

**Out of scope** (do NOT touch):
- `gate_digest.py` — it already handles these labels; no change.
- `assembler.py` — `run_resolve` stays compute-only (no gh); the claim
  step is a separate workflow step by design.
- `wo:failed` / `wo:blocked` transitions — not part of this plan.
- The `labels.json` taxonomy — both labels already exist.

## Git workflow

- Branch: `advisor/014-dispatch-lifecycle-labels`
- Commit style: `feat(factory): advance wo lifecycle at dispatch and PR
  open (ADR-0032)`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Teach `validator.py` two new lifecycle situations

1. Extend `parse()` so `lifecycle` accepts optional `--issue <N>`
   (digits only, else `(None, None)`) and optional `--uncited skip`:
   - `{"label"}` — current behavior (merged leg), unchanged.
   - `{"label", "issue"}` — flip a *known* issue: skip the PR/WO
     resolution entirely.
   - `{"label", "uncited"}` (value must be `skip`) — PR-shaped, but a PR
     body citing no work order is a silent no-op (`[]`), not a problem.
2. Split `run_lifecycle` so the label-flip tail (issue view →
   `transition` → issue edit) is a helper, e.g.
   `_flip(number, label, lifecycle, run)`, returning
   `(transitioned: bool, problems)`. Use `cli.gh_json(..., expect=dict)`
   for the issue view (013's helper) — keep the `GH_FAILURES` catches
   and existing `V:` strings byte-for-byte.
3. New `run_claim(root, label, issue, env, run=gh_runner)` for the
   `--issue` form: validate the label is in the taxonomy (same
   `lifecycle_labels` check), call `_flip`, and — the idempotency
   contract — write a step output via `cli.write_outputs(env,
   {"transitioned": "true"/"false"})`: `true` only when the flip
   actually removed `wo:ready-for-agent` (i.e. `remove` contained it).
   A repeat event finds the issue already on `wo:in-progress`,
   transition returns no-op, `transitioned=false`.
4. Wire both into `main()`.

**Verify**: `python3 -m unittest tests.test_validator -v` → existing
tests pass; new behavior tested in step 4.

### Step 2: Make targets, both Makefiles, lockstep constants

Root `Makefile` (and its `product_form` twin in
`factory/templates/Makefile` — same targets, `tools/factory/` paths):

```make
ISSUE ?=

wo-in-progress:
	python3 validator.py lifecycle --label wo:in-progress --issue $(ISSUE)

wo-needs-review:
	python3 validator.py lifecycle --label wo:needs-review --uncited skip
```

Add both to `.PHONY`. Update `TestLockstep`'s target table in
`tests/test_gates.py` (grep `VALIDATOR_TARGETS`) so the pair
stays pinned.

**Verify**: `python3 -m unittest tests.test_gates -v -k Lockstep`
→ pass.

### Step 3: Wire the workflows

1. `assembler.yml` — fix the concurrency comment to what the block
   actually does ("a repeat label event queues behind the running
   dispatch; the claim step below is what makes the repeat a no-op"),
   and insert a claim step between resolve and the agent step:

   ```yaml
   # Claim the order: ready -> in-progress (ADR-0032's state machine,
   # advanced by machinery, not memory). transitioned=false means a
   # repeat/stale event — the agent step is skipped, no second paid run.
   - name: Claim the work order
     id: claim
     if: steps.resolve.outputs.dispatch == 'true'
     env:
       GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
     run: make wo-in-progress ISSUE=${{ github.event.issue.number }}
   ```

   and change the agent step's condition to
   `steps.resolve.outputs.dispatch == 'true' && steps.claim.outputs.transitioned == 'true' && env.ANTHROPIC_API_KEY != ''`.

2. `validator.yml` — add a job after `review`:

   ```yaml
   # PR open flips the cited work order to wo:needs-review — the merge
   # gate's queue-entry event (ADR-0041's third gate). --uncited skip:
   # a PR that cites no work order (human housekeeping) is not an error.
   needs-review-label:
     if: >-
       github.event_name == 'pull_request'
       && (github.event.action == 'opened' || github.event.action == 'reopened')
       && github.event.pull_request.head.repo.full_name == github.repository
     runs-on: ubuntu-latest
     permissions:
       contents: read
       issues: write
     steps:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v5
         with:
           python-version: "3.12"
       - name: Flip the work order to wo:needs-review
         env:
           GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
         run: make wo-needs-review
   ```

**Verify**: `python3 -m unittest tests.test_gates -v` — the
"names no command of its own" guards still pass (both new steps go
through `make`).

### Step 4: Tests

`tests/test_validator.py` (RecordingRunner pattern, lines ~580-640):
- `--issue` claim on an issue carrying `wo:ready-for-agent` → gh edit
  called with `--add-label wo:in-progress --remove-label
  wo:ready-for-agent`; `transitioned=true` written to a fake
  `$GITHUB_OUTPUT`.
- Claim on an issue already `wo:in-progress` → no gh edit,
  `transitioned=false` (the idempotency case).
- `--uncited skip` with a PR body citing no WO → `[]`, no gh calls.
- `--uncited skip` with a cited WO → flips to `wo:needs-review`.
- `parse` rejects `--issue abc` and `--uncited yes`.

`tests/test_gates.py`:
- Assembler workflow: agent step's `if:` references
  `steps.claim.outputs.transitioned == 'true'`; claim step runs
  `make wo-in-progress`.
- Validator workflow: `needs-review-label` job exists, runs
  `make wo-needs-review`, and fires only on opened/reopened same-repo
  PRs (assert the `if:` text, same idiom as
  `test_the_merged_label_job_fires_only_on_a_merged_pull_request`).

**Verify**: `python3 -m unittest discover tests` → all pass.

### Step 5: Refresh mirrors

```
python3 factory_init.py update-manifest
```

**Verify**: `make check` → exit 0; payload copies of both workflows and
tools updated in `git status`.

## Test plan

Step 4 in full. Structural patterns: `tests/test_validator.py`'s
RecordingRunner/FailingRunner classes; `tests/test_gates.py`'s
workflow-text assertions.

## Done criteria

- [ ] `make check` exits 0
- [ ] `grep -n "wo-in-progress\|wo-needs-review" Makefile factory/templates/Makefile` → both targets in both files
- [ ] Agent step in `assembler.yml` gated on `claim.outputs.transitioned`
- [ ] The wrong concurrency comment is gone
- [ ] All step-4 tests exist and pass
- [ ] `factory/manifest.json` regenerated and committed
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- Plan 013 has not landed (no `gh_json` in `cli.py`).
- `validator.transition` semantics differ from "exactly one lifecycle
  label" (the invariant this plan builds on).
- The assembler workflow no longer has distinct resolve/agent steps
  with `steps.resolve.outputs.*` conditions.
- Adding the claim step would require new permissions (it must not —
  `issues: write` is already on the dispatch job; if it isn't at HEAD,
  stop).
- You need to change any behavior of the merged-label leg — strict
  no-WO handling there is deliberate and out of scope.

## Maintenance notes

- The first real dispatch after this lands finally exercises
  `gate_digest`'s merge-gate math — check the next daily digest actually
  shows a review-queue entry when a WO PR is open.
- If auto-merge graduation (ADR-0033/0036) later adds `wo:failed`
  transitions, `run_claim`/`_flip` is the machinery to reuse.
- Reviewer should scrutinize: the claim step must not fail the whole
  workflow when the flip is a benign no-op (`transitioned=false` is a
  skip, not an error); and `--uncited skip` must not weaken the merged
  leg's strictness.
