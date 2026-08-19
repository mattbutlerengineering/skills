# Autorun brief: toolsmith-mine-pr-permissions

Collected once, 2026-08-18, from the operator. This is not a run artifact:
it carries no frontmatter, never counts toward orientation, and is the
source of interview answers for every stage of this run.

## What and why

Tracker issue **#297** seeds this run. The operator named it directly,
which is the user-initiated intake door ADR-0030 opens into capture. The
issue is recorded as `intake: #297` in `defect.md` frontmatter, is never
re-read after seeding, and closes at Ship with a comment referencing the
run directory.

Run scale: **maintenance run**, slug `toolsmith-mine-pr-permissions`,
artifacts at `docs/fixes/toolsmith-mine-pr-permissions/`. Re-entry depth
is **implement** — this is a scoped fix to a workflow's permissions
block, not a design question. So the breakdown lives inline in
`defect.md` as checkboxes, there is no `architecture.md` and no
`breakdown.md`, and the stage sequence is capture → implement → verify →
review → ship.

## The defect

`.github/workflows/toolsmith-mine.yml` runs `make toolsmith-mine`
(`rejection_mining.py`) with a `permissions:` block granting only
`contents: read` and `issues: write` (lines 24-26). Every harvest calls
`gh pr list` — `PR_ARGS` at `rejection_mining.py:57`, reached from
`_change_requests` at `:152` — so the token can list issues but never
pull requests. The change-request half of the weekly harvest fails on
every scheduled run.

### Evidence, verified 2026-08-18

- The first and **only** scheduled `toolsmith-mine` run ever
  (2026-08-17T05:20:34Z, run `31997567430`, commit `663265c`) concluded
  `failure`. `gh run list --workflow=toolsmith-mine.yml` lists exactly
  one run. Quoted from the issue:

  ```
  rm: 32 candidate WO(s), 32 correction(s) mined
  rm: gh pr list failed: GraphQL: Resource not accessible by integration (repository.pullRequests)
  rm: gh issue pin failed: GraphQL: Maximum 3 pinned issues per repository (pinIssue)
  rejection_mining: 2 problem(s)
  ```

- The permissions block still reads `contents: read` / `issues: write` at
  HEAD, so the defect is live.
- **The application code is already correct.** A failing `gh pr list` is
  handled gracefully — `tests/test_rejection_mining.py:262`
  (`test_a_failing_pr_list_still_posts_gate_rejections`) pins that the
  harvest still posts its gate rejections. This is purely an
  infrastructure permissions gap, and the fix must not touch
  `rejection_mining.py`'s behavior.
- Since the issue was filed, `_change_requests` was re-pointed at
  `cli.gh_read` by the `deepening-tool-seams` run (merged `60f867f`).
  The failure path is unchanged — it now arrives as a label-prefixed
  problem string rather than a hand-built one — but any line number the
  issue quotes should be re-checked against HEAD rather than trusted.

### Sibling survey — done, and the answer is "no siblings"

Checked at HEAD so the fix is not narrower than the defect class:

- `assembler.yml` and `validator.yml` already grant `pull-requests:`.
- `sweeps.yml`, `gate-digest.yml`, `cost-report.yml`, `design.yml` and
  `charter-replay.yml` run no tool that calls `gh pr`.
- `dashboard.py` calls `gh pr` but runs in no workflow at all — it is a
  local tool.

`toolsmith-mine.yml` is the only live instance. Fixing it fixes the
class as it exists today.

## Target state

`.github/workflows/toolsmith-mine.yml` grants `pull-requests: read`
alongside its existing permissions, the payload twin and
`factory/manifest.json` are regenerated, and a regression test pins the
grant so it cannot be dropped silently.

## Scope

**In scope:**

1. Add `pull-requests: read` to the workflow's `permissions:` block.
2. Regenerate the mirror and the manifest — `.github/workflows/toolsmith-mine.yml` is a `factory_init.MIRRORS` entry mapped to the same path in the payload, so `python3 factory_init.py update-manifest` must be committed with the change or detector E fails the build.
3. A regression test that fails before the fix and passes after.
4. Post-release: trigger the workflow by `workflow_dispatch` and read the real output (see *Release authorization*).

**Out of scope, and why:**

- **The pin failure.** `gh issue pin failed: Maximum 3 pinned issues` is
  a separate, non-code condition: the repo has exactly three issues
  pinned right now (#172 "Factory gate queue", #178 "Factory gate
  queue", #181 "Factory improvement journal"), which is GitHub's cap, so
  the toolsmith-queue issue cannot be pinned. #172 and #178 are
  duplicate-titled and one of them is probably the unpin candidate, but
  that is the operator's console call, not this run's. See *What the
  operator must decide* below.
- **A drift detector for workflow permissions** — "every workflow whose
  tools shell out to `gh pr` must grant `pull-requests`" is a real
  detector-shaped idea and `gates.py` has unclaimed letters, but it is
  not needed to fix a one-line gap with no siblings. Seed it, do not
  build it.
- Any change to `rejection_mining.py`'s behavior, to the harvest's
  cadence, or to the other workflows.
- Re-running the harvest by hand to "catch up" the missed week.

## Success criteria

- `.github/workflows/toolsmith-mine.yml` grants `pull-requests: read`,
  and its payload twin is byte-identical to it.
- `python3 factory_init.py update-manifest` leaves the tree clean, and
  detector E is green.
- A regression test exists that **fails against the pre-fix file and
  passes after** — watched failing, not asserted. Note the constraint:
  this repo is stdlib-only and there is no YAML parser available, so the
  precedent is a text assertion on the file's contents
  (`tests/test_charter_replay.py:640` asserts
  `"permissions:\n  contents: read"` exactly this way).
- The full battery is green: `python3 -m unittest discover tests`,
  `python3 lint.py` (matching `lint: 0 problem(s)`), `python3 gates.py &&
  python3 gates.py --selftest` (matching `gates: 0 problem(s)` and
  `selftest: ok`).
- **The live check:** after merge, a `workflow_dispatch` run of
  `toolsmith-mine` produces output in which the line `rm: gh pr list
  failed: …` is **absent**. That is the whole criterion for the defect
  being fixed.

### The honest complication with that live check

The pin error is out of scope and will very likely still fire, so the
dispatched run may still print `rm: gh issue pin failed: …` and still
conclude `failure` with `rejection_mining: 1 problem(s)` instead of `2`.

**A red run is therefore not automatically a failed ship.** The criterion
is the disappearance of the `gh pr list` line and the drop from 2
problems to 1 — not a green conclusion. Verify and Ship must read the
actual log and say precisely which problems remain and why each one is or
is not this run's. Reporting a still-red workflow as success because the
merge landed would be exactly the dishonesty this repo's eval rules
exist to prevent.

## Constraints and things already decided

- **Stdlib only.** No third-party imports, and no YAML parser exists —
  assert on file text.
- **The workflow is checksum-mirrored.** `factory_init.MIRRORS` is the
  authority; detector E gates manifest-vs-payload and
  `tests/test_factory_init.py` pins payload-vs-root. The file's own
  header comment says it: "Editing this file means re-running
  update-manifest; detector E fails the build otherwise."
- **The workflow names no commands of its own** — everything gh-shaped
  goes through `make toolsmith-mine`, deliberately, so a stamped product
  repo runs the same file. Do not add a command to the YAML.
- **Problem-string contracts**: label-prefixed problem strings, asserted
  byte-for-byte by tests. Nothing in this fix should change one.
- Surgical scope. Adjacent smells get logged, not fixed.

## Tracker

**Intake only.** #297 seeds `defect.md` and closes at Ship. No other
issues are created, imported, or closed; no work item carries a
`(tracker: #N)` reference. Detector B's `Closes #N` requirement on the PR
is satisfied by #297 itself — this run needs no separate tracking issue.

## User-facing surface

None. Maintenance runs skip the PRD stage, so no `ux:` decision arises.

## Release authorization

**Full release is authorized** by the operator on 2026-08-18: branch, PR
against `main`, green CI, squash merge. "Production" for this repo is
`main` — the plugin is vended from the repo and the factory payload is
stamped into product repos from `factory/templates`. There is no deploy
step and no version tag.

**The post-release `workflow_dispatch` is also authorized**, explicitly.
It is the only way to prove the fix, it costs nothing (GITHUB_TOKEN, no
model in the loop), and it does what the weekly schedule would do on
Monday anyway. It is outward-facing in one respect and that is expected:
it creates-or-updates the pinned toolsmith-queue issue (#294). That is
the workflow working, not a side effect to avoid.

Two conditions bound the authorization and are not waivable:

- The full battery must be green at the merge commit, and CI green on
  the PR.
- Unfixed **critical** review findings block the merge unconditionally.

## What the operator must decide (do not decide it for them)

The pin cap. Three issues are pinned (#172, #178, #181) and #172/#178
share a title, which suggests one is stale. Unpinning one would let the
toolsmith-queue issue pin itself and clear the second error. That is a
console action on live tracker state with a duplicate-looking pair
involved — surface it in the run's artifacts and in the final report;
never unpin anything.

## Interview answers the stages will need

- **Who suffers, and how do they cope today?** The operator, and the
  daily improvement routine that reads the toolsmith queue. Coping today
  means the change-request half of the harvest silently produces nothing
  — the queue issue is posted, so the failure looks partial rather than
  total, which is the worse shape of broken.
- **Why now?** The harvest is weekly and has never once succeeded. Every
  Monday it fails again, and the corrections it exists to surface are the
  input to the factory's improvement loop.
- **Evidence strength:** direct. One recorded run, its log quoted, its
  conclusion `failure`, and the permissions block still unfixed at HEAD.
- **Blast radius:** one workflow file and its payload twin. No
  production code, no data, no user-facing surface. The risk is a stale
  manifest failing detector E, and it is caught by the battery.
- **How this dies:** the fix lands but nobody triggers the workflow, so
  the run ships on a green battery and an untested claim; or the
  dispatched run comes back red for the out-of-scope pin error and gets
  reported as either a failure or a success instead of what it is.
