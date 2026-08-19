---
stage: capture
run: maintenance:toolsmith-mine-pr-permissions
date: 2026-08-18
re-entry: implement
intake: #297
assumptions:
  - "The post-release workflow_dispatch is recorded as a Ship-stage obligation, not as a fourth checkbox. The brief lists it as in-scope item 4, but the protocol completes Implement when every checkbox in the run's breakdown is checked — a box that can only be ticked after merge would stall the run at Implement forever. It is stated below under 'Release obligation' and repeated in Notes so Verify and Ship cannot miss it."
  - "The drift-detector idea the brief says to seed is recorded in Notes rather than appended to docs/backlog.md. Capture is a backlog producer under the protocol's seed-backlog section, but this stage was scoped to write defect.md and nothing else; the seed text is written out verbatim below so appending it is a one-line action for whoever holds write authority outside the run directory."
  - "The regression test's home is left to Implement. The brief names no file and the stage skill supplies no default. The precedent is recorded under Notes — a tool's own test file owns the assertions over its workflow (tests/test_assembler.py holds assembler.yml's) — but naming the file here would be a guess dressed as a decision."
---

# Defect: toolsmith-mine.yml: grant pull-requests:read so the weekly harvest can list PRs

Working title copied from intake issue #297, filed 2026-08-17.

## Defect

`.github/workflows/toolsmith-mine.yml` runs `make toolsmith-mine`
(`rejection_mining.py mine`) under a `permissions:` block that grants
`contents: read` and `issues: write` and nothing else — lines 24-26 at
HEAD. Every harvest reads two correction streams off the dispatch plane,
and one of them is a pull-request listing: `PR_ARGS` at
`rejection_mining.py:57`, sent through `cli.gh_read` from
`_change_requests` at `rejection_mining.py:152` (the call is at `:156`).
The workflow's token can list issues but never pull requests.

- **Observed:** the change-request half of the weekly harvest fails on
  every scheduled run. The queue issue is still posted, carrying gate
  rejections only, so the failure reads as a partial result rather than a
  missing one.
- **Expected:** both streams land in the toolsmith queue — gate rejections
  *and* `CHANGES_REQUESTED` reviews joined to their work orders through
  the `Closes #N` grammar.

**Target state that ends this run:** the workflow grants
`pull-requests: read`, the payload twin and `factory/manifest.json` are
regenerated from it, a test pins the grant so it cannot be dropped
silently, and a dispatched run's log shows the `gh pr list` failure gone.

## Reproduction / Evidence

Every line below was produced at HEAD (`1573285`, branch
`toolsmith-mine-pr-permissions`) on 2026-08-18, not carried over from the
brief or the issue.

**The failing run, read from the log itself.** `gh run list
--workflow=toolsmith-mine.yml` returns exactly one row — the workflow has
run once, ever: run `31997567430`, event `schedule`,
`2026-08-17T05:20:34Z`, head `663265c`, conclusion `failure`.
`gh run view 31997567430 --log` gives:

```
python3 rejection_mining.py mine
rm: 32 candidate WO(s), 32 correction(s) mined
rm: gh pr list failed: GraphQL: Resource not accessible by integration (repository.pullRequests)
rm: gh issue pin failed: GraphQL: Maximum 3 pinned issues per repository (pinIssue)
rejection_mining: 2 problem(s)
make: *** [Makefile:69: toolsmith-mine] Error 1
```

**The grant is still missing at HEAD.** `.github/workflows/toolsmith-mine.yml`
lines 24-26 read `permissions:` / `contents: read` / `issues: write`.
Grepping `pull-requests` across `.github/workflows/` returns only
`assembler.yml:56` and `validator.yml:101`.

**The half-empty queue is visible on the tracker.** Issue #294
("Toolsmith queue — mined rejections", open, body starting with the
`<!-- factory-toolsmith-queue -->` marker) lists 32 corrections and every
single one is a `prd gate rejection`. Zero change-request entries. That is
the partial-failure shape stated above, not an inference.

**The application code is already correct — this is infrastructure only.**
`_change_requests`' docstring states the contract ("a failed listing is a
problem plus an empty stream, never a lost harvest — the gate rejections
still post") and `tests/test_rejection_mining.py:262`
(`test_a_failing_pr_list_still_posts_gate_rejections`) pins it. Nothing in
`rejection_mining.py` should move.

**The tree is green before the fix**, so any red after it is attributable:
`python3 lint.py` → `lint: 0 problem(s) across 23 skills`;
`python3 gates.py` → `gates: 0 problem(s)`; `python3 gates.py --selftest`
→ `selftest: ok`.

**The mirror is already in lockstep.** `.github/workflows/toolsmith-mine.yml`
and `factory/templates/.github/workflows/toolsmith-mine.yml` are
byte-identical today (`diff` is empty), the pair is registered at
`factory_init.py:160-161` as an `identity` mirror, and its checksum sits in
`factory/manifest.json:11`.

### Sibling survey — re-walked, and the answer is still "no siblings"

Confirmed at HEAD rather than accepted from the brief:

- Tools that shell out to `gh pr`: `rejection_mining.py` (`PR_ARGS`, `pr
  list`), `assembler.py:60,256` (`pr list`, reached by `make find-pr`),
  `validator.py:280` (`pr comment`, reached by `make review`), and
  `dashboard.py:226` (`pr list`).
- `assembler.yml`'s single `dispatch` job — the one that runs `make
  find-pr` at line 190 — grants `pull-requests: write` at line 56.
  `validator.yml`'s `review` job grants it at line 101. Both covered.
- `validator.yml`'s `needs-review-label` and `merged-label` jobs grant
  only `contents: read` / `issues: write`, but they run `validator.py
  lifecycle`, which touches no `gh pr` call. Not a sibling.
- `sweeps.yml`, `gate-digest.yml`, `cost-report.yml`, `design.yml` and
  `charter-replay.yml` run no tool that calls `gh pr`. `charter_replay.py`
  mentions `gh pr merge` only in a comment about a forbidden command it
  *scores*.
- `dashboard.py` runs in no workflow at all — it is a local tool.

`toolsmith-mine.yml` is the only live instance. Fixing it fixes the class
as it exists today.

## Root-cause hypothesis

**Not a hypothesis — a finding, and it is confirmed on three independent
sides.** The tool calls `gh pr list`; the workflow grants no
`pull-requests` scope; GitHub's refusal names the exact resource
(`repository.pullRequests`). The cause is the missing grant.

What remains genuinely unproven is **sufficiency**: that
`pull-requests: read` is the whole of what the listing needs. `PR_ARGS`
requests `number,state,body,reviews` with `--state all`, all of which are
read-only fields, so `read` should suffice — but the only proof is a
dispatched run, which is why the release obligation below exists.

A second, smaller hypothesis, offered as one: nothing caught this before
the first scheduled run because the repo's detectors gate the knowledge
plane and the payload checksums, not the correspondence between a
workflow's grants and the `gh` surface its tools actually reach. That is
the deferred detector idea recorded in Notes.

## Blast radius

- **One workflow file and its payload twin.** No production code, no
  data, no user-facing surface.
- **Who suffers:** the toolsmith charter's Mine stage, whose whole input
  is the queue issue (`rejection_mining.py` module docstring: PRD-0001
  §User stories, WO-0018). Half its correction stream has never arrived.
- **How badly:** the harvest is weekly and has succeeded zero times. The
  worse shape is that it fails *partially* — #294 exists and looks
  populated, so nothing about the tracker announces the gap.
- **Since when:** the workflow's first and only scheduled run,
  2026-08-17. Nothing before that had ever fired it.
- **The risk the fix itself carries:** a regenerated root file with a
  stale manifest, which detector E fails on. Caught by the battery, not by
  a reviewer's attention.

**Scale: small.** Review and Ship scale down accordingly. Verify does not
— the regression test is the point of the run.

## Ruled out

- **`rejection_mining.py` is not at fault.** Its failure path is
  deliberate and tested (`tests/test_rejection_mining.py:262`). Do not
  "fix" the tool.
- **`_change_requests`' recent move is not a regression.** The
  `deepening-tool-seams` run (`60f867f`, merged 2026-08-18, an ancestor of
  HEAD) re-pointed it at `cli.gh_read`. The failure path is unchanged —
  the problem string arrives label-prefixed from the seam instead of
  hand-built — and every line number the issue quotes was re-checked
  against HEAD and still holds.
- **No YAML parser is available to assert with.** This repo is
  stdlib-only. `tests/workflow_parse.py` exists but extracts `run:` steps
  only, so it cannot read a `permissions:` block. The precedent is a text
  assertion: `tests/test_charter_replay.py:640` asserts
  `"permissions:\n  contents: read"` exactly this way.
- **The payload twin does not need a new pin.** One already exists:
  `tests/test_gates.py:1887`
  (`TestLockstep.test_the_payload_toolsmith_workflow_is_the_mirror_of_this_repo_s`)
  asserts byte equality between the root workflow and its payload copy.
  The brief attributes that pin to `tests/test_factory_init.py`; that file
  drives fixture stubs from `factory_init.MIRRORS` and does not compare
  the real repo's pair. Do not add a second byte-mirror test — just keep
  the existing one green.
- **A permissions drift detector is not being built here.** Deferred with
  a reason; see Notes.
- **The pin cap is not this run's to fix.** See below.

## Work items

Dependency-ordered. The test is watched failing before the grant lands —
"fails before, passes after" is a thing to observe, not to assert.

- [ ] **Pin the grant with a failing test** — write a stdlib text
  assertion over `.github/workflows/toolsmith-mine.yml` requiring
  `pull-requests: read` in its `permissions:` block, and run it against
  the unmodified file.
  - Accept: the new test fails on the pre-fix workflow, and its failure
    output is recorded verbatim for Verify to quote.
- [ ] **Grant `pull-requests: read`** — add the one line to the workflow's
  `permissions:` block alongside `contents: read` and `issues: write`.
  Add no command to the YAML: the file deliberately names none, so a
  stamped product repo runs the same file.
  - Accept: `git diff` on `.github/workflows/toolsmith-mine.yml` is
    exactly one added line, and the test from the previous item passes.
- [ ] **Regenerate the payload mirror and the manifest** — run
  `python3 factory_init.py update-manifest` and commit its output with the
  change.
  - Accept: re-running `update-manifest` leaves the tree clean;
    `tests/test_gates.py::TestLockstep::test_the_payload_toolsmith_workflow_is_the_mirror_of_this_repo_s`
    passes; and the full battery is green — `python3 -m unittest discover
    tests`, `python3 lint.py` matching `lint: 0 problem(s)`,
    `python3 gates.py && python3 gates.py --selftest` matching
    `gates: 0 problem(s)` and `selftest: ok`.

### Release obligation (Ship, not Implement)

Deliberately not a checkbox — Implement completes when every box above is
checked, and this one can only be discharged after merge. It is in scope
and it is the only thing that actually proves the fix:

**After merge, trigger `toolsmith-mine` by `workflow_dispatch` and read
the real log.** The criterion is that the line `rm: gh pr list failed: …`
is **absent**. Verify and Ship must quote the log and name every problem
that remains, saying for each whether it is this run's.

**A red run is not automatically a failed ship, and a green run is not
automatically a passed one.** Read the log, not the conclusion. Reporting
a still-red workflow as success because the merge landed — or reporting
success without reading the log at all — is exactly the dishonesty this
repo's eval rules exist to prevent.

**One prediction, offered so it can be checked rather than assumed.** The
brief expects the pin error to fire again and the count to drop from 2
problems to 1. Reading `_post_queue` (`rejection_mining.py:164-190`) says
otherwise: the create path's pin failure *is* a problem, but the edit path
swallows a pin refusal (`except GH_FAILURES: pass`, `:178-179`) because a
human unpin heals it next week. Issue #294 now exists, is open, and its
body starts with `MARKER`, so `run_mine`'s lookup at `:223-226` finds it
and the next run takes the edit path. The dispatched run therefore likely
prints **no** pin line and may conclude green at 0 problems. Do not treat
that prediction as the criterion — read the log and report what is
actually there.

## Notes

- **The pin cap is the operator's console call, and this run never touches
  pinned state.** Verified 2026-08-18 via the tracker's `pinnedIssues`:
  exactly three are pinned — #172 "Factory gate queue", #178 "Factory gate
  queue", #181 "Factory improvement journal" — which is GitHub's cap, so
  #294 could not be pinned and is not pinned today. #172 and #178 share a
  title, which suggests one is stale, but unpinning is a live-tracker
  action on a duplicate-looking pair and belongs to the operator. Surface
  it in the final report; never unpin anything. Note that this stays true
  even under the prediction above: the pin attempt keeps failing silently
  every week, so #294 stays unpinned until a human acts.
- **Deferred seed, to be appended to `docs/backlog.md` by whoever holds
  write authority outside this run directory** (this stage was scoped to
  `defect.md` only). Text, ready to paste:

  `- A drift detector for workflow permissions: every workflow whose tools shell out to a gh surface must grant the matching scope (from: maintenance:toolsmith-mine-pr-permissions)`

  Not built here on purpose: `gates.py`'s roster has unclaimed letters
  (`J` and `K` are `(None, None, "unused")` at `gates.py:1115-1116`), but
  a detector is not the right size of answer to a one-line gap with no
  siblings.
- **Where the regression test should probably live.** Not decided here.
  The repo's shape is that a tool's own test file owns the assertions over
  its workflow — `tests/test_assembler.py` holds `assembler.yml`'s at
  `:356`, `:522`, `:548` — which points at `tests/test_rejection_mining.py`
  for this one. `tests/test_gates.py`'s `TestLockstep` is about
  Makefile/CI lockstep, a different question. Implement decides.
- **Variant.** Defect brief: something is broken, with a recorded
  reproduction. Not a condition brief.
- **Re-entry is implement** because there is no design decision here —
  one grant, one regeneration, one pin. So the work items live above as
  checkboxes and this run has no `architecture.md` and no `breakdown.md`.
- **Tracker: intake only.** #297 seeded this brief and is never re-read
  from here; the brief is the state. It closes at Ship with a comment
  referencing this run directory. No other issue is created or closed, and
  no work item above carries a `(tracker: #N)` reference — detector B's
  `Closes #N` requirement on the PR is satisfied by #297 itself.
- **Capture interviews; this one read a brief.** Every question the stage
  asks was answered up front in `autorun-brief.md`. What is mine rather
  than the operator's: the target-state sentence, the sufficiency caveat
  under Root-cause hypothesis, the two corrections recorded under Ruled
  out (the payload pin's real home) and Release obligation (the pin
  prediction), and the three entries in `assumptions:`. Those are the
  sentences to correct if any of them is wrong.
