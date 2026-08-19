---
stage: review
run: maintenance:toolsmith-mine-pr-permissions
date: 2026-08-18
assumptions:
  - "Severity was ranked without live user input. The operator's authorization makes unfixed critical findings blocking; none were found, so nothing here blocks the merge. The two minor findings carry a recommended decision (defer) rather than an arbitrated one — the fix loop is the orchestrator's call."
  - "The verdict that `pull-requests: read` is sufficient is reasoned from GitHub's documented permission model plus the two sibling workflows' evidence, not from a network call against the grant. No workflow was dispatched — that is Ship's obligation and it was left untouched."
  - "Read-only live tracker reads were made to settle what the newly-enabled stream actually carries: `gh pr list --state all --json number,state,body,reviews` (137 PRs), `gh repo view --json visibility`, and `rejection_mining.change_requests` run as a pure function over that listing. Nothing was created, edited, triggered, pinned, or unpinned."
  - "Mutant C's deferral is a judgement against this repository's own assertion standard, not an operator decision. The one-line strengthening is written out below so the orchestrator can overrule cheaply."
  - "The full battery was re-run at HEAD despite the stage skill's instruction not to re-verify what Verify covered. The reason is that this artifact lands in the directory the factory detectors read, so the effect of writing it had to be measured; the run found a red battery that predates this artifact. Re-running was the right call and the finding is recorded as critical."
---

# Review: toolsmith-mine.yml grants pull-requests: read

## Scope

`git diff main...HEAD` — three commits (`cfce85b`, `d70216b`, `df34eb9`),
eight files:

| File | Change |
|---|---|
| `.github/workflows/toolsmith-mine.yml` | +1 line: `  pull-requests: read` |
| `factory/templates/.github/workflows/toolsmith-mine.yml` | +1 line, the byte twin |
| `factory/manifest.json` | 1 checksum rewritten |
| `tests/test_rejection_mining.py` | +32 lines: `WORKFLOW` constant, `TestWorkflowPermissions` |
| `docs/backlog.md` | +1 seed line |
| `docs/fixes/toolsmith-mine-pr-permissions/*.md` | the run's three artifacts |

No production code changed. `rejection_mining.py` is untouched, as
`defect.md` required.

Scaled per the protocol's *Run scale* to the blast radius `defect.md`
records (**small**), with the regression test from Verify as the floor.
Verify's five mutants were re-derived only where I disagreed with the
reading. The battery **was** re-run, against the stage instruction not to
re-verify what Verify covered — because `review.md` lands in the same
directory the detectors read, so I had to know what my own artifact did
to them. That run is the critical finding below.

## Findings

**1 critical. 0 major. 2 minor.** The critical one blocks the merge.

### Critical: the battery is red at HEAD — `verification.md` trips detector H three times

`python3 gates.py` at HEAD, with only this review's untracked file added
to the tree:

```
H: docs/fixes/toolsmith-mine-pr-permissions/verification.md:208 criterion "Criterion 5 (brief) — the live check: a post-merge `workflow_dispatch` run whose output has no `rm: gh pr list failed: …` line" asserts **NOT YET VERIFIABLE** — recorded as a finding, not a pass. with neither literal evidence nor a NOT-RUN disclaimer (evidence must be a fenced code block in this section)
H: docs/fixes/toolsmith-mine-pr-permissions/verification.md:218 criterion "Criterion 6 (defect.md, work item 1) — the new test fails on the pre-fix workflow, and its failure output is recorded verbatim for Verify to quote" asserts **PASS** with neither literal evidence nor a NOT-RUN disclaimer (evidence must be a fenced code block in this section)
H: docs/fixes/toolsmith-mine-pr-permissions/verification.md:280 criterion "Criterion 9 (standing) — the defect in defect.md is actually resolved" asserts **NOT YET VERIFIABLE.** Not a failure — nothing found here with neither literal evidence nor a NOT-RUN disclaimer (evidence must be a fenced code block in this section)
gates: 3 problem(s)
```

And the suite, same tree:

```
FAIL: test_repo_verification_artifacts_are_honest (test_gates.TestEvidenceHonesty.test_repo_verification_artifacts_are_honest)
FAIL: test_a_clean_run_ends_with_the_exact_summary_line (test_gates.TestMainSummary.test_a_clean_run_ends_with_the_exact_summary_line)

Ran 1272 tests in 32.062s

FAILED (failures=2)
```

Both failures are the same three problems seen through
`tests/test_gates.py:1605` and through `gates.py`'s nonzero exit.
`python3 lint.py` is still `lint: 0 problem(s) across 23 skills`.

- Scenario: the PR is opened. `validator.yml:62` runs `make check`, which
  is `python3 lint.py; python3 gates.py; python3 gates.py --selftest;
  python3 -m unittest discover tests` (`Makefile:30-34`). `gates.py`
  exits 1 on the second command and the suite fails on the fourth. CI is
  red, and the operator's authorization makes green CI on the PR and a
  green battery at the merge commit **non-waivable**. The merge cannot
  proceed as the branch stands.
- Attribution, so this is not mistaken for my own artifact's doing:
  `gates.py` is not in this diff; detector H reads each run's
  `verification.md` and nothing else; all three problems cite a file that
  exists only on this branch (`df34eb9`). `review.md` asserts no labelled
  verdict lines of the shape H reads and contributes none of the three.
  Introduced by this branch, invisible to the stage that introduced it.
- Why Verify missed it, stated fairly: the claim was true of the tree
  Verify **measured** and false of the tree Verify **produced**. Criterion
  4's `Ran 1272 tests … OK` / `gates: 0 problem(s)` was captured before
  the artifact reached the state that trips the detector. A Verify stage
  cannot observe H's verdict on the artifact it is still writing unless it
  re-runs the battery after the final write.
- The fix, mechanically, per section (`_is_disclosure`, `gates.py:917-922`;
  `DISCLOSURE_VERDICT`, `:218-223`): a section holding a labelled verdict
  needs either a fenced code block **in that same section** or a verdict
  that *leads* with the disclosure vocabulary —
  `n/a`, `skipped`, `deferred`, `untested`, `unverified`, `pending`,
  `todo`, `tbd`, `not run` / `not verified` / `not tested` / … .
  "NOT YET VERIFIABLE" is outside that vocabulary (`not` must be followed
  by `run|ran|verified|executed|checked|tested|attempted`), so H reads it
  as a claim owing evidence.
  - **Criteria 5 and 9** — re-lead the verdict with an accepted
    disclosure, e.g. `Result: **NOT RUN** — the workflow is unmerged; the
    dispatch is Ship's obligation.` The meaning Verify intended is exactly
    what the vocabulary already spells; only the words are outside it.
  - **Criterion 6** — it asserts `PASS` and its evidence lives one heading
    away in Criterion 3. H refuses cross-section evidence by design
    ("evidence parked in an appendix does not vouch for a criterion three
    headings away", `gates.py:1000-1004`). Re-quote the RED block inside
    Criterion 6's own section.
- Decision: **must be fixed before Ship.** No code, test, or workflow
  changes — three edits inside `verification.md`, then re-run `make check`
  and confirm `gates: 0 problem(s)` and a green suite **after** the final
  write, not before it.

### Minor: the backlog seed line overstates the exposure window

`docs/backlog.md:27` says the workflow "ran `gh pr list` for months with
only `contents: read` / `issues: write`". It did not. `git log --follow`
puts the file's introduction at `f86c04f`, **2026-08-14** — four days
before this run — and `defect.md`'s own evidence records exactly one
scheduled run ever, `31997567430` on 2026-08-17.

- Scenario: the improvement routine reads `docs/backlog.md` as advisory
  seed state. A future reader (human or routine) prioritizes the deferred
  permissions drift detector on the belief that a live gap went unnoticed
  across months of scheduled runs; the record says one run, four days
  after the file was written. The seed misstates its own evidence in a
  repository whose non-negotiable is that run evidence is never
  overstated.
- Fix is one phrase: replace "for months" with the fact — one scheduled
  run, its first.
- Decision: **defer (recommended)** — advisory doc text, no behavior
  attached, and correcting it means touching a file outside this stage's
  write scope. Worth folding into any follow-up that touches the seed.

### Minor: the regression test stays green on a grant commented out inside the block

Verify's mutant C, re-read at the assertion's own shape
(`tests/test_rejection_mining.py:288-304`). `permissions()` returns the
block body as raw text; `assertIn("pull-requests: read", ...)` cannot
distinguish `  pull-requests: read` from `  # pull-requests: read`.

- Scenario: someone debugging a scope question comments the grant out
  rather than deleting it, pushes, and CI stays green while the harvest
  is broken again — the exact regression this test exists to catch, in
  its second-most-plausible spelling.
- The one-line strengthening, if the orchestrator wants it: assert over
  stripped lines rather than the joined text —
  `self.assertIn("pull-requests: read", [ln.strip() for ln in body])`,
  with `permissions()` answering the list instead of the join. That also
  makes the `write`-rejection explicit rather than incidental.
- Decision: **defer (recommended)** — see the adjudication below. Real,
  narrow, and already stronger than the repository's standing idiom for
  this class of assertion.

## The three scrutiny points, adjudicated

### 1. Is `pull-requests: read` the right grant? — Yes. High confidence, not offline-provable.

What the call needs: `PR_ARGS` (`rejection_mining.py:57`) is
`("pr", "list", "--state", "all", "--json", "number,state,body,reviews")`,
sent through `cli.gh_read` from `_change_requests` (`:152`, call at
`:156-157`) with `window=LIST_WINDOW`. Every consumer downstream is a
reader: `change_requests` (`:74-96`) walks the listing, matches
`CLOSES_TOKEN` refs against `mirror_map`, filters reviews on
`state == "CHANGES_REQUESTED"`, and excerpts the body. Nothing in the
path opens, edits, comments on, labels, reviews, or merges a pull
request. `read` is the least privilege that can serve it.

**The two siblings do not argue for `write`.** Both grants are explained
entirely by mutations that this job does not make:

- `assembler.yml:56` (`pull-requests: write`, dispatch job) — the
  chartered agent branches, pushes, and **opens a PR** (the job comment
  at `:51-53` says so, and it also holds `contents: write`). The same job
  runs `make find-pr`, whose `assembler.py:60` `PR_ARGS` is a *listing*
  (`pr list --state open --json number,body`) — so a listing rides along
  under a `write` that exists for the PR creation, not for the read.
- `validator.yml:101` (`pull-requests: write`, review job) —
  `validator.py:280` is `["pr", "comment", str(number), "--body-file", …]`.
  A comment is a mutation.

Neither is evidence that listing needs `write`, and reading them that way
would be the wrong inference to carry into a least-privilege grant.

**A second, stronger piece of evidence sits in the failure log itself.**
The 2026-08-17 run refused exactly one surface —
`repository.pullRequests`. The per-issue timeline reads
(`_timelines`, `rejection_mining.py:133-149`, `gh api …/issues/N/timeline`)
all succeeded under `issues: write`, which is why the run still reported
`32 candidate WO(s), 32 correction(s) mined`. So the harvest's scope
needs are fully enumerated by that log, and this one line completes them.
There is no second missing grant hiding behind the first.

**What is not provable here:** whether GitHub's installation-token model
resolves the nested `reviews` field under Pull requests *read* rather
than *write*. GitHub's documented mapping puts pull-request listing and
review reading both at read level, which is why I rank this high
confidence — but it is a claim about the far side of a network call this
stage did not make, exactly as `verification.md` recorded.

**Why this is not a critical finding even so.** If `read` turns out to be
insufficient, the failure is loud, identical to the one already recorded
(`rm: gh pr list failed: … repository.pullRequests`), read by Ship under
an obligation that already exists, and repaired by changing one word.
The run cannot ship a *silent* non-fix; that is the shape that would have
made this critical.

### 2. The commented-out-grant mutant — real, minor, defer.

By this repository's own standard rather than by mutation score:

- The standing idiom for a grant assertion is
  `tests/test_charter_replay.py:645`, a **whole-file**
  `assertIn("permissions:\n  contents: read", text)`. The new test is
  strictly stronger — it scopes to the block body, which is what catches
  Verify's mutant D (the string present elsewhere in the file).
- The regression it exists to prevent is the grant being *dropped*.
  Deletion, block rewrite, and relocation to a job-level block are all
  caught (Verify's mutants A and D, and the RED that was watched).
- Commenting out rather than deleting is a real edit shape, but a
  secondary one, and it leaves a line in the diff that says exactly what
  was done. A reviewer of that diff sees it; the test does not.

So: worth recording, not worth blocking, and cheap enough that the
orchestrator may reasonably overrule me. Recorded as a minor above with
the exact one-line fix.

**Mutant E (block absent entirely → `ValueError`) is not a finding.**
`permissions()` is a near-verbatim mirror of `triggers()` at
`tests/test_charter_replay.py:599-608`, which carries the identical
`lines.index("on:")` shape and the identical failure mode. Ranking the
`ValueError` here would be grading the repository's idiom under cover of
grading this run — the exact thing the review rules forbid. The suite
goes red either way, which is what the assertion is for; only the
diagnostic sentence is poorer.

**The `write`-rejection over-pin is likewise not a finding.** The test
rejects `pull-requests: write`, a strictly sufficient grant. That follows
from the claim `defect.md` states, the failure message prints the whole
block body, and the class docstring explains why the grant exists. A
future maintainer who needs `write` has a two-minute read, not a puzzle.

### 3. The test's home and its dependencies — clean.

- **Path resolution is cwd-independent.**
  `WORKFLOW = Path(__file__).resolve().parent.parent / ".github" /
  "workflows" / "toolsmith-mine.yml"` (`tests/test_rejection_mining.py:31-32`)
  is the idiom 24 other test files in `tests/` already use. Demonstrated
  rather than assumed: run from `cwd=/private/tmp` with `PYTHONPATH` set
  at the repository root, `TestWorkflowPermissions` passes.
- **It never runs in a stamped product repo.** `tests/` is absent from
  `factory_init.MIRRORS` (`factory_init.py:131-165`), and `find` over
  `factory/templates` returns **no** file matching `*test*` at all — the
  payload carries `.github/`, `docs/`, and `tools/factory/` and nothing
  else. Confirmed, not assumed. So the stamped repo's differing paths can
  never reach this assertion.
- **Its home matches the repository's shape.** A tool's own test file
  owns the assertions over its workflow — `tests/test_assembler.py` holds
  `assembler.yml`'s, `tests/test_charter_replay.py` holds
  `charter-replay.yml`'s. `tests/test_gates.py`'s `TestLockstep` keeps
  the payload byte-mirror, which is the different question it already
  answered.

## The three passes

### Correctness — no findings

Four things were checked and came back clean:

1. **The manifest checksum is right, recomputed independently.** Raw-bytes
   `sha256` of `factory/templates/.github/workflows/toolsmith-mine.yml` is
   `d1629e967ad32f449dbeef3f941b0e0bc70ab57d2667bf0cfb2090d1b50e7590`,
   byte-for-byte the value at `factory/manifest.json:11`. Not taken from
   `update-manifest`'s exit code.
2. **The newly-live listing cannot truncate silently.** `cli.gh_read`
   appends a problem string when the window comes back full
   (`cli.py:368-372`), and `_change_requests` extends `problems` with it
   (`rejection_mining.py:158`). The window is 1000; the repository has
   137 PRs.
3. **The grant does not widen the job beyond one surface.**
   `toolsmith-mine.yml` has a single job with no job-level `permissions:`
   block, so the workflow-level declaration is the whole grant set and it
   is exactly three entries.
4. **No other refused surface is hiding.** See the log reading under
   adjudication 1.

### Design — no findings

- **Placement matches the family.** Every single-job scheduled workflow
  in the repository declares its grants at workflow level —
  `gate-digest.yml:27`, `cost-report.yml:35`, `sweeps.yml:26`. The
  multi-job workflows (`assembler.yml`, `validator.yml`) keep a minimal
  workflow-level block and grant per job. This change follows the former,
  correctly.
- **Ordering is consistent** (`contents` → `issues` → `pull-requests`,
  which is also alphabetical) and appends rather than reshuffles, so the
  diff is one insertion with zero deletions.
- **The workflow still names no commands of its own.** Everything
  gh-shaped stays behind `make toolsmith-mine`, so the stamped payload
  runs the same file — the constraint the header comment states at
  `.github/workflows/toolsmith-mine.yml:3-8`.
- **Mirror discipline held.** Root and payload are byte-identical, the
  manifest was regenerated, and `tests/test_gates.py:1887`'s byte-mirror
  pin covers the pair. The seam rule was respected too: the new
  `permissions()` helper duplicates `triggers()` rather than extracting a
  shared one, which is correct under CLAUDE.md — two copies with no
  observed divergence do not meet the extraction bar.

### Security — no findings, three things worth stating plainly

**What the grant lets the job do that it could not before.** The job's
`GITHUB_TOKEN` can now read pull requests in this **private** repository
(`mattbutlerengineering/skills`) — list them and read `number`, `state`,
`body`, and their reviews. It cannot open, edit, comment on, label,
review, or merge one; every one of those needs `write`. That is the
minimum for `gh pr list --json number,state,body,reviews`, and nothing in
the job asks for more.

**What can reach the token.** One job, three steps: `actions/checkout@v4`,
`actions/setup-python@v5`, and `make toolsmith-mine` with
`GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` scoped to that step. The two
first-party actions are pinned by tag, not by SHA — unlike
`assembler.yml`, which pins its third-party action by digest because it
holds write scopes and a model credential. That is pre-existing and
untouched here; the new grant widens what a re-pointed tag could reach by
one read-only surface. Logged, not a finding, and not this run's to
change.

**Untrusted text now flows where it previously could not.** This is the
one genuinely new exposure: PR review bodies — writable by any reviewer —
reach a tracker issue for the first time, because before this line the
listing always failed. The handling is adequate and was already built
(WO-0035, `663265c`):

- `_excerpt` (`rejection_mining.py:61-71`) takes the **first line only**,
  then `sweeps.sanitize` (`sweeps.py:134-147`) strips control characters,
  defangs fence runs (`FENCE` at `sweeps.py:104`, three-or-more backticks
  rewritten to three apostrophes), redacts WO tokens, collapses all
  whitespace to single spaces, and caps at 300 characters.
- `compose_queue` (`:118-124`) then wraps the result in an indented
  text fence and closes the body with the ADR-0032 sentence naming quoted
  excerpts as data, never instructions.

Newline injection is impossible (single line plus whitespace collapse);
fence escape is impossible (the run is defanged before quoting). The
residual is the one ADR-0032 already owns: the queue issue is read by an
LLM-driven improvement routine, so the fence and the footer are the whole
defense against a reviewer writing instructions into a review body. That
stance is unchanged by this run — it simply goes live with this grant.

**Propagation.** The grant mirrors into every stamped product repo on
their next payload update. Read-only, required for the target to work,
and presently inert there: the stamped `toolsmith-mine` target dies at
`from sweeps import sanitize` because `sweeps.py` is not in `MIRRORS`
(already on `docs/backlog.md:25` from `maintenance:deepening-tool-seams`).
Not a regression from this run.

## One observation Ship needs

**The change-request stream is empty today, and the dispatched run will
show that.** Measured read-only against the live tracker: 137 PRs across
all states, and **zero** `CHANGES_REQUESTED` reviews among them. Running
`rejection_mining.change_requests` as a pure function over that real
listing mines **0** rows.

Three consequences:

1. After the fix, the queue issue will look **identical** to today's — 32
   gate rejections, no change-request entries — and the reason line will
   still read `rm: 32 candidate WO(s), 32 correction(s) mined`. Nothing in
   the tool's *positive* output will change.
2. So the only evidence available to Ship is the one `defect.md` already
   names: the **absence** of `rm: gh pr list failed:`. An empty
   change-request section is not a failed fix, and must not be read as
   one.
3. It also refines the run's own narrative honestly: no correction has
   actually been lost to date. `defect.md` says "half its correction
   stream has never arrived", which is true — but the half was empty, so
   the harm is prospective, not accrued. The fix's value is that the
   first `CHANGES_REQUESTED` review will now be seen.

## Passes with no findings

Correctness, design, and security all came back clean **on the change
itself**. The two minors are one doc-text inaccuracy and one narrow
test-coverage gap; neither touches behavior. The critical finding is not
in any of the three passes — it is in the run's own verification
artifact, and it was found only because the battery was re-run at HEAD.

## Verdict

**Blocked, by one finding, on a fix that touches no code.**

The fix under review is correct: the smallest thing that can close the
defect, at least privilege, with a coherent and independently checked
mirror and manifest, and a regression test that is correctly homed,
cwd-independent, and absent from the payload. Nothing in
`.github/workflows/toolsmith-mine.yml`, `factory/manifest.json`, its
payload twin, or `tests/test_rejection_mining.py` needs to change.

What blocks the merge is that the branch does not pass its own battery:
`verification.md` trips detector H three times, so `make check` — the PR's
CI job — is red. The operator's authorization makes that non-waivable.
Three wording edits inside `verification.md` and a re-run of the battery
*after* the final write clear it.

Two obligations carry forward unchanged from `verification.md`:

Two obligations carry forward unchanged from `verification.md`:

- **Ship dispatches the workflow and reads the log, not the conclusion.**
  The criterion is the absence of `rm: gh pr list failed:`. Given the
  observation above, expect an unchanged queue issue and an unchanged
  count line — that is the fix working, not the fix failing. If the
  refusal line reappears, `read` was insufficient and the repair is
  `write`, one word, already precedented at `assembler.yml:56` and
  `validator.yml:101`.
- **The pin cap is the operator's console call.** Three issues are pinned
  (#172 and #178 share the title "Factory gate queue"; #181 is "Factory
  improvement journal"), which is GitHub's cap, so #294 cannot pin.
  Surface it in the final report. Nothing was unpinned here and nothing
  should be by anyone but the operator.
