---
stage: ship
run: maintenance:deepening-tool-seams
date: 2026-08-18
assumptions:
  - "No live user input at any point — this run is driven from autorun-brief.md, so every judgment below is mine against the brief, CLAUDE.md and the precedent run. The brief's Release authorization section is the mandate for the merge itself; nothing else here was approved live"
  - "'production' for this repo is main: the plugin is vended from the repo and the factory payload is stamped into product repos from factory/templates. There is no deploy step and no version tag — the project has never tagged a release — so shipping is a branch, a PR, a green battery and a squash merge. Same reading as the deepening-cli-seams release"
  - "The brief's 'No tracker interaction' clause and detector B are unsatisfiable together as literally written, and the merge condition wins. Detector B requires a Closes #N link on every PR regardless (its WO-id half is waivable, its Closes half is not), and the brief makes a green battery non-waivable at the merge commit. Resolved the way this repo already resolved it once: opened #301 as the run's TRACKING issue — not a work order, no dispatch semantics, no breakdown row pointing at it, so the clause's actual subject (work items carry no tracker references, none were mirrored) is untouched. Precedent: #254 for deepening-cli-seams"
  - "ADR-0056 stays provisional. review.md's note 5 calls confirming it 'the Ship stage's act, per the run's own precedent (ADR-0054)' — but the observed precedent says otherwise: ADR-0054 shipped provisional on 2026-08-13 and is still provisional today, five days and one release later. Flipping a status the operator never confirmed would be inventing an operator decision, and the authorization covered a merge, not an ADR"
  - "release.md is committed directly on main after the merge, not on the branch before it, because it records the merge commit sha and post-release evidence that cannot exist until the merge lands. Precedent: 9e57327 for deepening-cli-seams"
---

# Release: one owner each, four times (PR #302 → `60f867f`)

## Pre-flight

- [x] **Verification green (no unresolved failures)** — `verification.md`
      is **23/23 PASS** with a `## Failures` section reading "None". Three
      criteria pass under a stated narrowing, and those narrowings are
      carried forward here as narrowings, not restated as passes: `LIST_WINDOW`
      is still declared seven times (S1 — the design decided per-tool
      windows stay per-tool; what got one owner is the window *rule*);
      "observable output unchanged" is proven only for strings the 1,234
      pre-change tests pin plus detector J's complete enumeration (S2);
      and "watched to fail" is attested from commit messages with only the
      *impossibility of passing* re-derived (A1, B4, C1). Two observations
      were recorded rather than softened — B4's Accept line undercounting
      its sanctioned string edits by one, and the copied window comments —
      and Review adjudicated both.
- [x] **Review carries no unfixed critical** — confirmed from the artifact,
      not from the prompt. `review.md`'s Findings section opens "**Zero
      critical.**" and its Verdict repeats it. One **major** (`human_gates.py`
      missing from CLAUDE.md's shared-module enumeration — the very sentence
      stating the bar it meets): **fixed** in `bc64dd2`. Three **minors**:
      `TestThePartition`'s docstring and architecture.md's false "none raise"
      claim **fixed** in the same commit; B4's Accept-line undercount
      **deferred**, with its reason recorded (the correction already exists in
      `6ec22a5`'s message and in `verification.md`, and rewriting a closed
      Accept line edits the run's history rather than recording it).
- [x] **No secrets in the diff** — `git diff main...HEAD` scanned for
      credential-shaped strings (`sk-…`, `ghp_`/`gho_`/`ghs_`/`github_pat_`,
      `AKIA…`, `-----BEGIN`, `Bearer …`, `aws_secret`, `private_key`): **zero
      hits**. The repo's active feature run involves `CLAUDE_CODE_OAUTH_TOKEN`
      and `FACTORY_PAUSE_TOKEN`; **no token value appears anywhere in this
      diff**, and neither name does either. The only `TOKEN`-matching lines
      are `CLOSES_TOKEN` and `WO_TOKEN` — knowledge-plane regex identifiers.
      No workflow file changed (`git diff --stat main...HEAD -- .github/` is
      empty), so no secret reference moved. Review's security pass reached
      the same place from the other direction: the diff never touches
      `cli.child_env`, `cli.read_event` or `cli.read_execution`, and nothing
      secret can reach a problem string.
- [x] **Required configuration exists in the target environment** — the
      relevant environment is a *stamped product repo*, because this diff adds
      `human_gates.py` to the factory payload, and the check is that a stamped
      repo still passes its own gates. Both prior stages drove it: Verify
      checked the payload three ways (detector E green; `update-manifest`
      idempotent on a clean tree with an empty `git status` after; an
      independent payload-vs-root comparison applying each of the 25 `MIRRORS`
      transforms — **0 mismatches**, including the new row), and Review
      stamped a fresh product repo and drove it (`gates.py` green,
      `--selftest` green, `declared_labels` naming `human_gates.py` for all
      five gate labels, every mirrored tool imported). Review also corrected
      B3's citation: `test_stamped_repo_passes_its_own_gates` is *not* what
      proves the stamp works, because `declared_labels` swallows `ImportError`
      by design; what proves it is the payload `Makefile`'s
      `python3 tools/factory/gates.py --selftest`, which asserts the positive
      string `human_gates.py names wo:merged`. Re-driven independently in
      Post-release below.
- [x] **Migrations/data changes** — **none.** No persisted shape changed:
      the cost ledger's record shape, the breakdown grammar, `factory.json`
      and the manifest format are untouched. `cost_ledger.dispatched` is a
      pure filter over rows already written; the costly gate row that makes
      the divergence observable exists only inside test fixtures.
      `docs/factory/costs.jsonl` was deliberately not written to (eval
      honesty), confirmed:

      ```
      $ git log --oneline main..HEAD -- docs/factory/costs.jsonl
      (no commits)
      $ git diff --stat main...HEAD -- docs/factory/costs.jsonl
      (empty)
      $ git diff --stat main...HEAD -- evals/ skills/ docs/pipeline-protocol.md
      (empty)
      ```

      The only generated file in the diff is `factory/manifest.json`,
      regenerated with `factory_init.py update-manifest` inside each commit
      that touched a `MIRRORS` entry and verified idempotent on a clean tree.
- [x] **Rollback plan concrete** — below.
- [x] **Battery re-run at what was merged**, not taken from Verify. At
      `bc64dd2`, clean tree:

      ```
      Ran 1271 tests in 30.309s
      OK

      lint: 0 problem(s) across 23 skills

      gates: 0 problem(s)
      selftest: ok
      ```

## Rollback plan

The release is one squash commit on `main`, so the undo is one revert:

```
git checkout main && git pull --ff-only
git revert 60f867f                        # squash merge = one parent, no -m flag
python3 factory_init.py update-manifest   # payload + manifest travel inside the
                                          # revert; this only re-verifies idempotence
python3 -m unittest discover tests && python3 lint.py \
  && python3 gates.py && python3 gates.py --selftest
git push origin main
gh issue reopen 301                       # the tracking issue the PR auto-closed
```

**What the revert undoes.** Everything in the 44-file diff, in one commit:
`cli.gh_read` and the fourteen call sites, `human_gates.py` and its four
callers, `knowledge_plane.mirror_map`, detector J's `gate_labels()` call,
`cost_ledger.dispatched`, the deleted `product_form` shadow and the new
`toolsmith-mine` lockstep methods, both payload twins of every mirrored
file, `factory/manifest.json`, ADR-0056, CLAUDE.md's seam-module sentence,
`docs/setup.md`'s payload counts, and the run's own artifacts through
`review.md`. `release.md` is a separate commit and would survive — correctly,
since a rolled-back release is still a release that happened.

**What the revert does NOT undo, and this is the part that matters:**

- **Any product repo already stamped or refreshed from the new payload.** The
  payload is *pulled* by `factory_init.py stamp|update <target>`, never
  pushed, so a stamped repo keeps `human_gates.py` and the deepened tools
  until someone re-runs `python3 factory_init.py update <target>` from the
  reverted `main`. **No real repo was stamped in this release** — the two
  stamps below are throwaway scratch trees — so today this bullet is a
  warning about the future rather than a step to run.
- **The closed tracking issue.** `gh issue reopen 301` is listed above
  because a revert does not reopen what a `Closes` link closed.
- **The two `docs/backlog.md` seeds** would in fact be *removed* by the
  revert (they are in the diff): the stamped payload's dead `toolsmith-mine`
  target and `human_gates.waited_seconds`' `ValueError` path. Both describe
  conditions that survive a revert, so re-append them by hand if this is
  ever run.

Nothing else needs undoing: no tag was cut, no package was published, no
deployment was triggered.

## Release log

Recorded as it happened, hiccups included.

1. `python3 -m unittest discover tests` / `lint.py` / `gates.py` +
   `--selftest` at `bc64dd2` → **green**, quoted in Pre-flight above. Run
   here rather than trusted from `verification.md`, which was written two
   commits earlier at `a4f6310`.
2. Secrets scan of `git diff main...HEAD`, plus the ledger/evals/workflow
   checks → **clean**, quoted above.
3. Confirmed from `review.md` itself that no critical finding is unfixed →
   zero critical; the major and two minors are fixed in `bc64dd2`; the third
   minor is deferred with its reason.
4. `git push -u origin deepening-tool-seams` → new branch pushed, 19 commits.
5. **Opened #301 before the PR, deliberately.** Detector B reads the CI event
   payload and so cannot be pre-flighted locally — the precedent release
   learned this the expensive way, with a red first CI run. This run's
   breakdown carries **no** work-order id in any of its fifteen rows (the
   brief rules out tracker interaction for work items), so the PR body
   declares `No work order: <reason>`, which detector B's waiver exists for.
   The `Closes #N` half has no waiver, and no existing open issue is this
   run's subject: #178 and #181 are the permanent marker-bearing state issues
   that must never be closed by a PR, #294–#296 are automation-posted, and
   #297/#299/#300 are unrelated. So #301 is the run's tracking issue — the
   condition, the blast radius, the ruled-out list — exactly as #254 was for
   `deepening-cli-seams`. The tension with the brief's "no issues are
   created" is logged in `assumptions:` rather than resolved silently.
6. `gh pr create --base main` → **PR #302**, body written right the first
   time: the four deepenings, the evidence classes, the two deliberate output
   changes, Verify's narrowings, the `No work order:` waiver and `Closes #301`.
7. `gh pr checks 302 --watch` → **all green, first run**:

   ```
   check              pass  18s
   needs-review-label pass   6s
   review             pass  29s
   merged-label       skipping
   ```

   The battery inside the `check` job, which runs with the `pull_request`
   event payload present — so `gates: 0 problem(s)` there means **detector B
   passed on this body**, the thing the local gate is structurally blind to:

   ```
   lint: 0 problem(s) across 23 skills
   gates: 0 problem(s)
   selftest: ok
   gate_digest: 0 problem(s)
   selftest: ok
   Ran 1271 tests in 11.889s
   OK
   ```

   and from the `review` job, which reads the same payload through
   `validator.py`: `validator: 0 problem(s)`.

   The only annotations are the standing Node.js 20 deprecation warnings on
   `actions/checkout@v4` and `actions/setup-python@v5` — present on every run
   of this repo, unrelated to this change, not addressed here.
8. `gh pr merge 302 --squash` → merged at 03:35:52Z as **`60f867f`**, with
   **#301 auto-closed** by the `Closes` link. The command printed nothing on
   success; the merge was confirmed by reading it back
   (`gh pr view 302 --json state,mergeCommit` → `MERGED`,
   `60f867fbfa754800cafdfe8b4251f4c9b3bb73cf`) rather than inferred from a
   silent exit.
9. `git checkout main && git pull --ff-only` → local `main` fast-forwarded to
   `60f867f`, working tree clean.
10. Branch `deepening-tool-seams` left alive until the post-release checks
    below came back green, then deleted.

**No retry was needed anywhere.** That is worth stating plainly because the
precedent release needed two — a red first CI run on detector B and a
`gh pr edit` that failed on the Projects (classic) deprecation while
silently leaving the body unchanged. Both were avoided by inheriting that
artifact's closing advice: decide the `Closes #N` target before opening the
PR, and never edit a body after the fact. `gh pr edit` was not invoked.

## Post-release checks

**1. The battery on merged `main`**, not on the branch — `60f867f`, clean tree:

```
Ran 1271 tests in 36.079s
OK

lint: 0 problem(s) across 23 skills

gates: 0 problem(s)
selftest: ok
```

1,271 tests, up from main's 1,234.

**2. A repo stamped from the shipped payload passes its own gates.** This is
the surface product repos actually receive, so it was driven rather than
argued. Stamped into an empty git tree from `main` @ `60f867f`:

```
$ python3 factory_init.py stamp <scratch>
factory-init: 0 problem(s)

$ ls tools/factory/
assembler.py budget_guard.py cli.py cost_ledger.py cost_report.py
factory_config.py gate_digest.py gates.py handoff.py human_gates.py
knowledge_plane.py label_sync.py orientation_pack.py protocol.py
rejection_mining.py validator.py work_queue.py          (17 files)

$ python3 tools/factory/gates.py
gates: 0 problem(s)
$ python3 tools/factory/gates.py --selftest
selftest: ok
[exit 0]
```

`--selftest` is the one that matters, per Review's correction: it asserts the
**positive** string `human_gates.py names wo:merged`, so a payload that
shipped without the module would turn it red in the product repo's own CI
rather than degrading silently.

**3. The shipped module is the declaring site in the stamped repo** —
detector J reading the payload, not this checkout:

```
wo:blueprint-approved        -> ['human_gates.py']
wo:draft                     -> ['human_gates.py']
wo:failed                    -> ['Makefile:45']
wo:in-progress               -> ['Makefile:39']
wo:merged                    -> ['Makefile:36', 'human_gates.py']
wo:needs-review              -> ['Makefile:42', 'human_gates.py']
wo:prd-approved              -> ['human_gates.py']
wo:ready-for-agent           -> ['assembler.py']
```

and the payload's own tools import and expose the deepened interfaces:

```
imported: human_gates | GATES: 3 | gate_labels: ['wo:blueprint-approved',
  'wo:draft', 'wo:merged', 'wo:needs-review', 'wo:prd-approved']
cli.gh_read: True
cost_ledger.dispatched: True
```

**4. The two things that fail in a stamped repo fail identically before this
release** — checked against a control stamp from `fbfa3c3` (the pre-merge
`main`), because a post-release check that reports a failure without a
control is an accusation, not evidence:

| Driven in the stamped repo | Shipped (`60f867f`) | Control (`fbfa3c3`) |
|---|---|---|
| `tools/factory/gates.py` | `gates: 0 problem(s)` | `gates: 0 problem(s)` |
| `tools/factory/gates.py --selftest` | `selftest: ok` | `selftest: ok` |
| `make check` | `ImportError: Start directory is not importable: 'tests'` | identical |
| `tools/factory/rejection_mining.py mine` | `ModuleNotFoundError: No module named 'sweeps'` | identical |
| `tools/factory/` contents | 17 tools, incl. `human_gates.py` | 16 tools, no `human_gates.py` |

Both failures are pre-existing and neither is this release's:

- `make check`'s third line runs `python3 -m unittest discover -q tests`, and
  a repo stamped into an *empty* tree has no `tests/` yet. That is the bare
  stamp's condition, not a payload defect — the first two lines of the same
  target, which are the detector suite, are green.
- `toolsmith-mine` is dead in every stamped repo because the mirrored
  `rejection_mining.py` imports `from sweeps import sanitize` and `sweeps.py`
  is not a `MIRRORS` entry. Review found this while driving the payload and
  seeded it to `docs/backlog.md`; introduced by `663265c` (WO-0035), it
  predates this run and is out of its scope. Named here so nobody reads the
  new `toolsmith-mine` lockstep class as "that target is now covered" — the
  class pins the command *text*, correctly, and the command still does not
  run where it ships.

**5. Two hiccups in the checking itself**, recorded because a clean-looking
log is a lie:

- My first `declared_labels` probe passed a `str` and got
  `TypeError: unsupported operand type(s) for /: 'str' and 'str'`. That is my
  probe calling an internal with the wrong type, not a tool defect — the
  signature takes a `Path`. Re-run with `Path(".")`, which produced the table
  above.
- The first payload file count on the control read 17 and matched the shipped
  tree, which briefly looked like `human_gates.py` had always been there. It
  was `__pycache__`, created by my own earlier imports, counted as a file.
  Listing the names rather than counting them showed 16 real tools on the
  control and no `human_gates.py`. Count files by name, not by `wc -l`.

**6. One thing did go wrong, after the release was already done.** The
`validator` run on this artifact's own commit (`7cc5207`, docs-only) sat
**queued for over seventeen minutes with no runner picking up its single
`check` job**, and was still queued when this note was written. That is
runner starvation, not a broken workflow, and the distinction is evidenced
rather than assumed: the same workflow completed in **21s** on the merge
commit `60f867f` six minutes earlier (run `32212715818`, **success**), and
green on the merge commit is the condition the release authorization
actually names. The artifact commit changes one markdown file and no code;
the full battery was run locally with it present and is green (quoted at the
top of this section plus `gates: 0 problem(s)` / `selftest: ok` /
`lint: 0 problem(s)` / 1,271 tests OK). Nothing was merged on the strength of
a stalled run, and no workflow YAML was touched in response — the standing
rule for this signature is to record it, not to edit CI.

**7. Not smoke-checked, carried forward from Verify's *Not verified* list**,
which Review confirmed it did not close:

- **Nothing was driven against real GitHub, at any stage of this run.** Still
  unproven: that a live rate-limit or auth failure lands in `CLI_FAILURES`
  now the catch moved into `cli.gh_read`, and that `label_sync.live_labels`'
  three callers behave the same against a live failure now they no longer own
  the `except`. The remedy is Verify's and it belongs to whoever is next at
  this repo: **watch one scheduled run of `label-sync`, `gate-digest` and
  `toolsmith-mine` after this merge for a nonzero exit or a changed problem
  line.** Note that `toolsmith-mine` in *this* repo runs from the root, where
  `sweeps.py` exists, so check 4's stamped-repo gap does not affect that
  watch here.
- **`dashboard.py` and `sweeps.py` have no payload twin**, so their stamped
  behavior is untested by construction — unchanged by this run, and the
  dashboard's three re-pointed reads are covered only by
  `tests/test_dashboard.py`, byte-identical to main.

## Outcome

**Shipped cleanly.** On `main` at `60f867f`, green there, with the payload
driven in a freshly stamped repo and the change visible at the surface a
product repo reads.

Four facts have one owner each. Both live divergences named in the brief are
gone — `work_queue`'s duplicate `"100"`, and the six-versus-seven-tool
`product_form` shadow. The two deliberate output changes are the two that
were priced (detector J's declaring-site name; `work_queue`'s month-to-date
figure on a ledger carrying a nonzero-cost gate row, which over the live
ledger changes nothing because every gate row there costs `$0.00` — which is
exactly why the divergence survived unnoticed).

Three things the next release should inherit rather than rediscover:

1. **The precedent's two hiccups are avoidable and were avoided.** Decide the
   `Closes #N` target *before* opening the PR — detector B cannot be
   pre-flighted locally, and #178/#181 are never that target. Write the body
   right the first time; `gh pr edit` still dies on the Projects (classic)
   deprecation on this repo and leaves the body unchanged while reporting an
   error that reads like a warning.
2. **`gh pr merge --squash` prints nothing on success.** Read the merge back
   with `gh pr view <n> --json state,mergeCommit` rather than trusting a
   silent exit.
3. **A run whose brief forbids tracker interaction still owes detector B a
   `Closes #N`.** Either the brief should carve out the tracking issue
   explicitly, or detector B should learn a waiver for the Closes half the
   way it has one for the WO half. Two runs have now hit this and resolved it
   the same ad-hoc way; the third should not have to.

ADR-0056 remains **provisional** and is the operator's to confirm — see
`assumptions:`. Next stage is Operate.
