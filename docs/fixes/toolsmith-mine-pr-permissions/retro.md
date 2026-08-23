---
stage: operate
run: maintenance:toolsmith-mine-pr-permissions
date: 2026-08-22
assumptions:
  - "Step 4 says 'against prd.md's success criteria and idea.md's success-in-one-sentence'. This run has neither — maintenance runs skip both — so outcomes are judged against autorun-brief.md's 'Success criteria' and 'Target state' and defect.md's 'Target state that ends this run'. Same substitution verification.md recorded for the same reason."
  - "Step 3's 'let it breathe' was answered yes rather than deferred. The merge was 2026-08-19T05:21Z and this retro is written 2026-08-22 (repo clock through 2026-08-23T04:10Z UTC): three days, two independent dispatched harvests, four subsequent non-work-order merges exercising the condition this run seeded, and the operator's decisions on all three carried-forward items already taken. That is real post-ship history, not hopes. Nothing further breathes without the Monday schedule, and waiting for it would hold the run open for a signal the retro can name as missing instead."
  - "The seeds this run already owed were verified present in docs/backlog.md rather than re-appended. The workflow-permissions drift detector (defect.md's Notes text, appended during Review per review.md's file table), the merged-label seed, and the run-discovery-should-read-open-PRs seed all already carry '(from: maintenance:toolsmith-mine-pr-permissions)'. Appending them again would duplicate lines in an append-only file."
  - "The pin cap is recorded as CLOSED BY OPERATOR ACTION, not carried forward as an open decision. The instruction for this stage was to carry it forward; the live read contradicts it — #172 was unpinned 2026-08-21T22:14:59Z by mattbutlerengineering and #294 was pinned 44 seconds later by the harvest itself. Reporting a decision as open when the tracker shows it taken would be the same dishonesty in the other direction. Nothing was pinned or unpinned by this stage; the state below is read-only observation."
  - "Run 32532180432 (2026-08-21, workflow_dispatch, head 08d4127, operator-triggered) is counted as evidence for this run's criterion even though this run did not trigger it. It is a second independent observation of the same criterion on a later commit; it is labelled as operator-triggered and manual everywhere it is used, and it does not upgrade the signal past 'two manual dispatches'."
  - "The merged-label condition's closure is credited to ADR-0057 and PR #308, not to this run. This run identified it as inherited, refused to widen into it, and seeded it; four later sessions re-diagnosed it (three of them wrongly, per the backlog's own correction chain) before #308 fixed it. This retro claims the seeding and the correct inherited-vs-owned call, not the fix."
  - "Nothing was committed. The files this stage wrote (this artifact and three appended backlog lines) are left in the working tree for the operator."
---

# Retro: toolsmith-mine.yml grants pull-requests: read

Maintenance run, `re-entry: implement`, seeded by tracker intake #297,
shipped as PR #303 → `73b9d05` on 2026-08-19. This retro is written
2026-08-22 against live tracker and Actions state, read-only.

## Outcomes vs. intent

### Criterion 1 — the live check: a post-merge run with no `rm: gh pr list failed: …` line

This was the brief's whole criterion for the defect being fixed.

**What happened: it is gone, observed twice.** `gh run list
--workflow=toolsmith-mine.yml` returns three runs in the workflow's
entire life:

```
32532180432  success  2026-08-21T22:15:11Z  workflow_dispatch  08d41277
32219180419  success  2026-08-19T05:22:32Z  workflow_dispatch  73b9d05e
31997567430  failure  2026-08-17T05:20:34Z  schedule           663265c2
```

The pre-fix run, `31997567430`, printed (quoted in `defect.md` from the
log):

```
rm: 32 candidate WO(s), 32 correction(s) mined
rm: gh pr list failed: GraphQL: Resource not accessible by integration (repository.pullRequests)
rm: gh issue pin failed: GraphQL: Maximum 3 pinned issues per repository (pinIssue)
rejection_mining: 2 problem(s)
make: *** [Makefile:69: toolsmith-mine] Error 1
```

The first post-merge run, `32219180419` on the merge commit `73b9d05`,
printed the whole of its mine step as:

```
python3 rejection_mining.py mine
rm: 32 candidate WO(s), 32 correction(s) mined
rejection_mining: 0 problem(s)
```

The second, `32532180432` on `08d4127` three days later — a different
commit, a different day, triggered by the operator and not by this run —
printed:

```
python3 rejection_mining.py mine
rm: 35 candidate WO(s), 35 correction(s) mined
rejection_mining: 0 problem(s)
```

**Which problems remain, and whose each is: none remain.** The 2026-08-17
run had two; both are absent from both post-fix runs.

1. `rm: gh pr list failed: …` — **this run's**. Gone, and the grant is
   the only change between `663265c` and `73b9d05` that touches it.
2. `rm: gh issue pin failed: …` — **not this run's**, and gone for two
   different reasons at two different times. On 2026-08-19 it was
   *swallowed*: `_post_queue`'s edit path (`rejection_mining.py:176-180`,
   `except GH_FAILURES: pass`) reports nothing, and #294 already existed,
   so the harvest silently failed to pin and said `0 problem(s)`.
   `defect.md` predicted exactly this and the brief predicted otherwise;
   `defect.md` was right. On 2026-08-21 it was *actually fixed*: a pin
   slot had been freed 12 seconds before that dispatch started, and the
   harvest pinned #294 successfully (see Criterion 5).

**Signal strength: measured, but narrow.** Two direct observations of the
exact criterion, on two commits, from real workflow logs. Both are
`workflow_dispatch`. The brief's framing of a "red run is not a failed
ship" never had to be exercised — the runs came back green.

### Criterion 2 — has the weekly schedule fired since?

**No.** `.github/workflows/toolsmith-mine.yml` carries `cron: "47 4 * * 1"`
— Mondays 04:47 UTC. The run list above has exactly one `schedule` event
ever, and it is the failing pre-fix one. Both post-fix runs are
`workflow_dispatch`, and the second was triggered by the operator by
hand. The next scheduled firing is Monday 2026-08-24.

**This is a real limit on the signal and it is stated as one.** What is
proven is that the token minted for this workflow can now list pull
requests. `permissions:` is declared at the top level of the workflow and
applies identically to both triggers, so the mechanism carries — but
"the weekly harvest now succeeds on its own schedule, unattended" has not
been observed and cannot be until 2026-08-24. Every post-fix data point
is a human pressing a button.

**Signal strength: anecdote for the unattended case.** Zero observations.

### Criterion 3 — intake #297 closed at Ship, with a comment referencing the run directory

**Both verified.**

```
{"closedAt":"2026-08-19T05:21:30Z","state":"CLOSED",
 "title":"toolsmith-mine.yml: grant pull-requests:read so the weekly harvest can list PRs"}
```

Closed at 05:21:30Z — the merge itself, via `Closes #297` on PR #303 —
and a comment was posted at 2026-08-19T05:24:04Z ending:

```
Full run record: `docs/fixes/toolsmith-mine-pr-permissions/` (defect.md,
verification.md, review.md, release.md).
```

The comment also carried the run log, the pin cap and PR #298 forward to
the operator. ADR-0030's intake contract was honoured end to end.

**Signal strength: measured.** Direct tracker read.

### Criterion 4 — the inherited condition this run seeded rather than owned

`release.md` recorded the post-merge `merged-label` job as RED, judged it
pre-existing rather than this run's, seeded it, and refused to widen into
it. That call was correct, and the condition has since been closed by
someone else — which is the strongest outcome signal this run has.

**Before.** The job failed on non-work-order PR merges. Run `32552945778`
(PR #306's merge, 2026-08-22T04:54:36Z), job `merged-label`, conclusion
`failure`:

```
python3 validator.py lifecycle --label wo:merged
V: PR body cites no work-order id
validator: 1 problem(s)
make: *** [Makefile:40: wo-merged] Error 1
```

Run `32525347492` (2026-08-21T20:47:32Z) failed identically. So did
#302's and this run's own #303's, as `release.md` recorded.

**The fix.** ADR-0057
(`docs/adr/0057-lifecycle-legs-agree-about-an-uncited-pr.md`), PR **#308**,
merged 2026-08-23T00:42:33Z as `bf67fe5`.

**After.** Every non-work-order PR merged since is green on that job:

| Merge event run | PR | `merged-label` |
|---|---|---|
| `32608548586` | #308 (the fix itself) | **success** |
| `32610934941` | #310 | **success** |
| `32614813845` | #312 | **success** |
| `32616686685` | #314 | **success** |
| `32617200904` | #316 | **success** |

#316's log:

```
python3 validator.py lifecycle --label wo:merged --uncited skip
validator: 0 problem(s)
```

**Signal strength: pattern.** Five consecutive green merge events after
four consecutive red ones, across four PRs touching unrelated files.

The uncomfortable half of this outcome: the seed this run left was
*right about the symptom and wrong about the diagnosis*, and the backlog
records four successive re-diagnoses before #308 landed — `--uncited
skip` proposed, refuted as test-deleting, the `if:`-filter alternative
refuted as having no label to filter on, then the real finding that the
two lifecycle legs contradict each other so no PR body satisfies both.
The seed's value was that it existed and named a reproducible condition;
its proposed fix was noise. That is the honest reading of what a
correctly-refused widening buys: a placeholder, not an answer.

### Criterion 5 — the pin cap, which the brief left to the operator

**The operator decided it, and this run did not touch it.** Current
pinned state, read this session:

```
#178  Factory gate queue              OPEN
#181  Factory improvement journal     OPEN
#294  Toolsmith queue — mined rejections  OPEN
```

The timeline says how it happened: **#172** (the stale duplicate — closed
since 2026-07-28, still holding a pin) was **unpinned 2026-08-21T22:14:59Z
by `mattbutlerengineering`**. The operator then dispatched the harvest 12
seconds later, and `github-actions[bot]` **pinned #294 at
2026-08-21T22:15:43Z** — the workflow pinning its own queue issue, 44
seconds after the slot opened. That is the first time the toolsmith queue
has ever been pinned.

**What is still open is not the decision but the detector.** The seed
filed as `session:2026-08-21` asks for a pinned-issues-are-open check in
`sweeps.py`; it is unbuilt. And the swallow is unchanged:
`_post_queue`'s edit path still discards a pin refusal, so the next time
the cap fills, the harvest will report `0 problem(s)` while silently
failing again — exactly as it did on 2026-08-19.

**Signal strength: measured.** Direct GraphQL and timeline reads.

### The standing criterion — is the captured defect actually resolved?

Yes for the call; **unproven for the stream**.

The grant has survived four days and eight merges: at HEAD (`7650052`)
`.github/workflows/toolsmith-mine.yml` still reads `pull-requests: read`,
`cmp` against the payload twin is silent, and
`tests/test_rejection_mining.py:278` `TestWorkflowPermissions` still pins
it. Nothing has silently dropped it, which is what the regression test
was for.

But the newly-working stream has never carried a single item. Checked
this session across every PR the repo has:

```
total PRs: 145
PRs with a CHANGES_REQUESTED review: []
reviewDecision CHANGES_REQUESTED: []
```

And #294's body today is 35 entries, every one of them a
`prd gate rejection` — not one `change request` line. So the queue issue
looks, byte-for-byte in shape, exactly as it looked when the listing was
being refused. `review.md` established the zero-count read-only before
the merge; it is still zero three days later.

**`pull-requests: read` is proven sufficient for the call** — the harvest
listed PRs instead of being refused — and **the change-request half of
the harvest is still unexercised end to end.** The join grammar from a
`CHANGES_REQUESTED` review to its work order via `Closes #N` has never
run against real data in production. If it were wrong, nothing today
would say so.

**Signal strength: no signal.** Not a negative result — an absent one.

## Run retrospective

**Keep**

- **`defect.md` re-verifying the brief at HEAD instead of trusting it.**
  It corrected the brief four times, and the one that mattered was the
  pin prediction: the brief predicted `2 problem(s)` → `1` and a red run,
  `defect.md` predicted `0` and green by reading the swallow at
  `rejection_mining.py:176-180`. `defect.md` was right. A capture stage
  that re-derives its own evidence is worth its cost.
- **Refusing to widen, and seeding instead.** The `merged-label` job was
  red on this run's own merge and it would have been easy to "just fix
  it" inside a one-line permissions run. It was correctly identified as
  inherited (the identical failure on #302's merge the day before, a
  different run, different files), seeded, and left. Four sessions and
  one ADR later that turned out to be a design question about two
  contradicting lifecycle legs — precisely the thing that should not have
  been absorbed into a permissions fix.
- **The evidence bar held under pressure.** `verification.md` recorded
  the two criteria it could not settle as NOT YET VERIFIABLE rather than
  as passes, and detector H caught it when the artifact stated a verdict
  without a fenced block. The repo's own machinery enforced the eval
  rules on the run that was writing about them.

**Change**

- **Look at open PRs before starting a run.** The whole fix already
  existed in open PR #298, opened by the daily improvement routine two
  days earlier with the same one-line grant, the same regeneration, and
  the same `Closes #297`. Run discovery listed open *issues* only.
  Already seeded; the operator closed #298 on 2026-08-19T14:53:46Z
  (CONFLICTING by then, because both PRs added a `TestWorkflowPermissions`
  class). The cost was a duplicated run, not a bad outcome.
- **Write the record as the outward actions land, not after them.** The
  Ship subagent pushed, opened #303, merged it, closed #297 and
  dispatched the workflow, then died on an API error before writing
  `release.md`. Nothing was left half-done in the world; the damage was
  entirely to the record, which had to be rebuilt from git, `gh` and run
  logs by the orchestrator. A stage whose steps are irreversible should
  leave a trace of each one before taking the next.
- **A criterion satisfiable only by a manual dispatch proves the
  mechanism, not the cadence.** The brief's live check was well designed
  and it worked — but three days on, the thing the defect was actually
  about (a *weekly* harvest that has never once succeeded on its
  schedule) still has zero scheduled evidence. Where a fix is about a
  scheduled path, the run should say plainly what the manual proof does
  and does not cover, and name the date the real proof arrives.

**Stop**

- **Stop letting the brief's predictions outrank the code.** The brief
  spent a full section on "the honest complication with that live check"
  — the predicted `2 → 1` and a still-red run — and the prediction was
  simply wrong; a five-line read of `_post_queue` settled it, which is
  what `defect.md` did. The elaborate hedging was wasted words that a
  later stage had to spend effort adjudicating. Predict less; read the
  code.

## Idea seeds

Appended to `docs/backlog.md` this session:

- The toolsmith queue cannot distinguish "no change requests exist" from
  "the listing failed" — both render as an empty change-request section.
- A stage that performs irreversible outward actions before writing its
  artifact leaves no record when the agent dies.
- A resolution note on the closed-issue pin slot: cleared in the world
  for #294, still unbuilt as a check.

Already present from earlier stages of this run, verified and not
duplicated:

- A drift detector for workflow permissions (appended at Review).
- The `merged-label` failure on every non-work-order PR — now closed by
  ADR-0057 / #308, and the backlog already carries that resolution note.
- Run discovery should look at open PRs, not just open issues.

## Run complete

Closed 2026-08-22. The defect is fixed and the fix is proven for the
call, twice, by hand; the scheduled path it exists for gets its first
real test on 2026-08-24, and the stream it unblocked is still empty
because the repo has never had a `CHANGES_REQUESTED` review. All three
items `release.md` carried forward have since been settled by the
operator or by a later run: PR #298 closed, the pin cap resolved and #294
pinned, the `merged-label` condition fixed by ADR-0057. Seeds above are
the input to the next Idea-stage run.
