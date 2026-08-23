---
stage: ship
run: maintenance:one-fact-one-owner
date: 2026-08-23
authorization: prepare-and-stop
assumptions:
  - "No live user input at any point — this run is driven from autorun-brief.md, so every judgment below is mine, taken against CLAUDE.md, the cited ADRs, the repo's observed conventions and the two precedent releases rather than the operator's. The brief records release authorization as [No preference], which under the autorun default is prepare-and-stop, so this artifact records readiness and the exact steps and executes no externally visible action"
  - "'Production' for this repo is main — confirmed against the repo rather than inherited: `git tag --list` is empty (0 tags ever), `gh release list` is empty, and `\"version\": \"0.1.0\"` in both package.json and .claude-plugin/plugin.json is the only value either file has ever held (`git log -p --follow` shows one `+` line and no `-` line). This diff touches neither packaging manifest. So no version bump and no tag apply, and the release mechanism is a branch, a PR, a green battery and a squash merge"
  - "Branch name `feat/one-fact-one-owner`. Neither input names one. The repo's current convention is `<type>/<slug>` — the six most recent merged PRs are refactor/one-plane-drift-rule, docs/adr-0046-diagnosis-correction, fix/one-checked-row-grammar, feat/optional-recency-evidence, fix/lifecycle-legs-agree, fix/payload-sanitize-seam — and this run's seventeen commits are `feat(one-owner):`, so the type is feat. Recommended, not executed"
  - "PR title `feat(one-owner): a pre-pass that asks whether a fact is stated twice` — conventional-commit per the routine's caps and the observed PR titles. The scope is the run's own (`one-owner`) rather than `factory`, matching all seventeen commit subjects; the tool is a repo-root tool and is not mirrored into the factory payload, so `(factory)` would misdescribe it"
  - "The tracking issue. detector B's Closes-#N half has no waiver, and defect.md's `No tracker interaction. No issues created` clause is unsatisfiable together with it as literally written. Resolved the way this repo has already resolved it twice — #254 for deepening-cli-seams, #301 for deepening-tool-seams — by minting one plain TRACKING issue: no `wo:` label, no dispatch semantics, no breakdown row pointing at it, so ADR-0032 (never a work-order id ahead of its breakdown row) is untouched and the clause's actual subject (work items carry no tracker references — none do) is untouched. Recorded as an operator step, NOT executed: no issue was created"
  - "Squash merge, matching every recent PR (PR #302 carried eighteen commits and landed as `60f867f` with a single parent). The consequence is recorded rather than hidden: the per-item commit history that verification.md scores under D7 does not survive onto main, and its evidence lives on the PR's commits tab and in verification.md"
---

# Release: a pre-pass that asks whether a fact is stated twice — PREPARED, NOT EXECUTED

**Nothing was released.** No branch was created, nothing was pushed, no
issue or PR was opened, no tag was cut, nothing was merged. The brief
records release authorization as `[No preference]`, which under the
autorun default is **prepare and stop**, and `defect.md` restates it
under Constraints. This artifact is the readiness record and the exact
steps for the operator to execute.

State at the moment of writing:

| | |
|---|---|
| Local `main` | `ca77b4c`, **17 commits ahead** of `origin/main`, 0 behind |
| `origin/main` | `7650052` (`refactor(factory): one cross-plane drift rule…` #316) |
| Remote `main` (read back via `gh api`) | `7650052ba32b…` — **identical**, so the branch is not behind base and no rebase is needed |
| The diff | `git diff origin/main..HEAD` — 12 files, **+2087 / −1** |
| Working tree | seven uncommitted entries, all left untouched (see *Open decisions*) |

## Pre-flight

- [x] **Verification green (no unresolved failures)** — `verification.md`
      is **20 criteria, 19 PASS, 1 PASS-AS-AMENDED, 0 FAIL**, and its
      `## Failures` section reads "**None.**" The one amended criterion
      is D4: `defect.md` asked for a test that would have caught each of
      the three historical instances; the suite catches two and **pins
      the third as a known miss**, an operator-accepted substitution
      recorded in `architecture.md`, in `breakdown.md` C2 and in the
      assertion's own comment at `tests/test_one_owner.py:933-959`. It is
      carried forward here as an amendment, not restated as a plain pass.
      The battery was **re-run at HEAD by this stage** rather than
      inherited — `verification.md` was written two commits earlier at
      `62a3e56`, and two review fixes (`881787b`, `58db94a`) plus a
      deviation log (`ca77b4c`) have landed since:

      ```
      $ make check
      python3 lint.py
      lint: 0 problem(s) across 24 skills
      python3 gates.py
      gates: 0 problem(s)
      python3 gates.py --selftest
      selftest: ok
      python3 -m unittest discover tests
      Ran 1344 tests in 15.280s
      OK
      [make check exit=0]
      ```

      `python3 one_owner.py` prints its nine findings and exits 1. That is
      the tool's normal output and **is not part of the battery**: it is
      deliberately outside `make check` (verified — the `check` target is
      exactly `lint.py`, `gates.py`, `gates.py --selftest`,
      `unittest discover tests`) and outside every workflow (verified —
      `grep -rn "one_owner\|one-owner" .github/workflows Makefile` returns
      nothing; the only wiring is `factory.py`'s verb row).

- [x] **Review carries no unfixed critical** — read from the artifact,
      not from the prompt. `review.md`'s Findings section opens "**No
      critical findings. Nothing blocks Ship on correctness.**" and its
      Verdict repeats it. Two findings were **fixed** before Ship — the
      routine step's uncomputable delta (`881787b`) and ADR-0061's "pair"
      that is a triple (`58db94a`) — and six are **deferred with logged
      reasons** (one major about the carve-out's ADR-only escape hatch,
      routed to `docs/backlog.md` at Operate; five minors). No unfixed
      critical exists, so no soft-gate override was needed and none was
      taken.

      > **Corrected 2026-08-23.** This line read "nine are deferred"
      > until Operate caught it. `review.md` carries eight findings —
      > two `fix before Ship`, six `deferred` — counted from its
      > `Decision:` lines. The nine came from a word-frequency count of
      > "defer" relayed into this stage's inputs, not from the artifact
      > that owns the number. Left visible rather than silently amended,
      > because `retro.md` cites this discrepancy as the second instance
      > of a restated-count defect and that citation must still resolve.

- [x] **No secrets in the diff** — `git diff origin/main..HEAD`
      (2,197 lines) was written to a scratch file and every **added** line
      scanned against fourteen credential shapes:
      `api[_-]?key`, `secret`, `token`, `password|passwd`, `credential`,
      `private[_-]?key`, `AKIA[0-9A-Z]{16}`, `gh[pousr]_[A-Za-z0-9]{20,}`,
      `sk-[A-Za-z0-9]{20,}`, `xox[abprs]-`, `Bearer `, `-----BEGIN`,
      `authorization`, and a generic `[A-Za-z0-9+/]{40,}={0,2}` base64
      shape. **Zero credential hits.** Every match was benign and each was
      read:

      - `token` — Python's stdlib `tokenize` module (`import tokenize`,
        `tokenize.COMMENT`, `token.start`) in `one_owner.py`'s comment
        reader, plus the string `"# one-owner: dashboard.git_runner (0037)
        — bad token"` in a test fixture, plus the word "tokens" in
        `breakdown.md` prose about `WO-` ids.
      - the base64 shape — the single SHA-256 checksum line in
        `factory/manifest.json`, which is the one intended data change.

      No environment variable is read anywhere in the added lines
      (`os.environ`, `getenv`, `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`, `env:`
      — zero hits), and **no workflow file changed**
      (`git diff --name-only origin/main..HEAD | grep -E '^\.github/'` is
      empty), so no secret reference moved.

- [x] **Required configuration exists** — confirmed, not asserted. This
      change **adds no configuration and no environment dependency**:

      - `one_owner.py`'s entire import list is stdlib plus two repo
        modules — `ast`, `io`, `re`, `sys`, `tokenize`,
        `collections.namedtuple`, `pathlib.Path`, then
        `from cli import CLI_FAILURES, detail, report, runner` and
        `from knowledge_plane import repo_root`. No third party, no
        network, no key, no file outside the repo.
      - `gh secret list` and `gh variable list` for this repo are both
        **empty**. That is irrelevant here and the claim was checked
        against the diff rather than assumed: no workflow file changed, so
        no `secrets.*` reference was added, moved or renamed, and the only
        workflow-adjacent edit in the diff is prose in
        `docs/factory/improvement-routine.md`. The change touches nothing
        that needs a secret.
      - The one environment that receives shipped bytes from this diff is
        a **stamped product repo**, because
        `factory/templates/tools/factory/budget_guard.py` changed. That
        was driven, not argued — stamped from HEAD into a throwaway git
        tree in a scratch directory:

        ```
        $ python3 factory_init.py stamp <scratch>
        factory-init: 0 problem(s)
        $ python3 tools/factory/gates.py
        gates: 0 problem(s)                        [exit 0]
        $ python3 tools/factory/gates.py --selftest
        selftest: ok                               [exit 0]
        ```

        17 payload tools, and `one_owner.py` correctly **absent** from
        them — ADR-0060's mirrored-iff-imported rule holds, since no
        payload tool imports it. The three marker comment lines the
        payload does receive are inert there by construction: they are
        comments, and the reader that would act on them does not ship.

- [x] **Migrations / data changes have a tested forward path** — **there
      are none**, confirmed against the diff rather than expected. No
      persisted shape changed: the cost-ledger record shape, the breakdown
      grammar, `factory.json` and the manifest *format* are all untouched.
      The append-only surfaces were checked and are empty in the diff:

      ```
      $ git diff --stat origin/main..HEAD -- docs/factory/costs.jsonl evals/ LEDGER.md skills/ docs/pipeline-protocol.md .github/
      (empty)
      ```

      **The one data artifact is `factory/manifest.json`**, one line: the
      checksum for the payload twin of `budget_guard.py` moves from
      `bb486bbe…` to `cb91b94a…`. Both pins on it are green, and the
      forward path was proved **read-only**, which closes the gap
      `verification.md` recorded under *Not verified* (it declined to
      re-run `update-manifest` because that writes to the tree):

      - **Detector E (manifest ↔ payload)** — green inside
        `gates: 0 problem(s)`, above.
      - **`tests/test_factory_init.py` (payload ↔ root)** — `Ran 52 tests
        … OK`, run on its own.
      - **`update-manifest` idempotence, without writing a byte** — its
        two write steps were recomputed in memory and compared:
        `gates.manifest_files(root)` reproduces the committed `files` map
        **exactly** (0 differing keys), `plugin`/`version` match
        `.claude-plugin/plugin.json`, and applying every `factory_init.MIRRORS`
        transform to its root file reproduces each payload file
        **byte-identically** (0 drifted mirrors). Re-running
        `update-manifest` would be a no-op.
      - `diff -q budget_guard.py factory/templates/tools/factory/budget_guard.py`
        → identical (this entry's transform is `identity`).

- [x] **Rollback plan concrete** — below, in three stages, because there
      are three distinct points this release can be undone from.

## Rollback plan

The three stages are the three states this change can be in. Only stage A
is true today.

### A — nothing pushed (the state as this artifact is written)

Nothing external exists, so the rollback is entirely local and the
uncommitted files must survive it. If the branch move in step 1 has been
made and the operator wants the starting state back:

```
git switch feat/one-fact-one-owner     # be off main so its ref can be forced
git branch -f main ca77b4c             # main back to the 17-commit tip
git switch main
git branch -D feat/one-fact-one-owner
git status --porcelain                 # must still list the 7 uncommitted entries
git log --oneline -1                   # must read ca77b4c
```

To abandon the work entirely instead — dropping the seventeen commits
from `main` while keeping the uncommitted files:

```
git switch main
git reset --keep 7650052               # --keep, never --hard: --hard destroys
                                       # docs/backlog.md's edit and six untracked files
git reflog                             # the 17 commits stay reachable here
```

### B — branch pushed, PR open or not, nothing merged

`main` on the remote has never been written to at any point, so there is
nothing to revert there. Undo outward first, then run stage A:

```
gh pr close <PR>                         # only if the PR was opened
gh issue close <N> --comment "Closing: the one-fact-one-owner release was rolled back before merge; the condition is unchanged and the run's artifacts stay at docs/fixes/one-fact-one-owner/."
git push origin --delete feat/one-fact-one-owner
```

### C — after the squash merge

The release is **one squash commit** on `main` (single parent — confirmed
against the precedent: PR #302's eighteen commits landed as `60f867f`
with one parent), so the undo is one revert:

```
git switch main && git pull --ff-only
git revert <merge-sha>                    # squash merge = one parent, no -m flag
python3 factory_init.py update-manifest   # payload + manifest travel inside the
                                          # revert; this only re-verifies idempotence
make check                                # must print 0 problem(s) / selftest: ok / OK
git push origin main                      # or open a revert PR, if branch protection
                                          # is ever enabled on this repo (see below)
gh issue reopen <N>                       # a revert does not reopen what Closes closed
```

**What the revert undoes**, in one commit: `one_owner.py`,
`tests/test_one_owner.py`, `docs/adr/0061-…md` and its `docs/adr/README.md`
row, the three `# one-owner:` markers (`budget_guard.py`, `dashboard.py`,
`one_owner.py`), `CLAUDE.md`'s paragraph, `factory.py`'s verb row, step 9
of `docs/factory/improvement-routine.md` §2, the payload twin of
`budget_guard.py`, the one `factory/manifest.json` line, and
`docs/fixes/one-fact-one-owner/breakdown.md`. The daily improvement
routine reads its playbook from `main`, so the revert removes step 9 at
its next run with nothing to undo by hand.

**What the revert does NOT undo:**

- **Any product repo already stamped or refreshed from the new payload.**
  The payload is *pulled* by `factory_init.py stamp|update <target>`,
  never pushed, so a stamped repo keeps the three comment lines until
  someone re-runs `python3 factory_init.py update <target>` from the
  reverted `main`. Today this is a warning about the future, not a step:
  the only stamp made during this stage was a throwaway scratch tree, and
  the payload delta is three comment lines.
- **The closed tracking issue** — hence `gh issue reopen <N>` above.
- **`release.md` itself**, which is a separate commit and should survive:
  a rolled-back release is still a release that happened.

Nothing else needs undoing: no tag was cut, no package was published, no
deployment was triggered, no workflow was dispatched.

## Release steps — recorded, NOT executed

Each command below is exactly what the operator runs. Nothing in this
section has been run.

**Step 0 — confirm the starting state.**

```
git rev-parse --short HEAD              # expect ca77b4c
git rev-parse --short origin/main       # expect 7650052
git rev-list --left-right --count origin/main...HEAD   # expect  0  17
git status --porcelain                  # expect 7 entries, all pre-existing
make check                              # expect 0 problem(s) / selftest: ok / OK
```

**Step 1 — move the seventeen commits onto a branch, leaving `main` where
the remote has it.** The commits are on `main` today; the standing rule is
to branch rather than push the default branch. This is a ref move only —
it touches no file, so all seven uncommitted entries carry across
untouched:

```
git switch -c feat/one-fact-one-owner   # branch at ca77b4c; HEAD moves to it
git branch -f main 7650052              # rewind the main REF only (no worktree change)
git log --oneline -1 main               # must read 7650052
git status --porcelain                  # must still list the same 7 entries
```

**Step 2 — push the branch.** This is the first externally visible action
of the release.

```
git push -u origin feat/one-fact-one-owner
```

**Step 3 — open the tracking issue BEFORE the PR.** Deliberately first:
the `Closes #N` target has to be known when the body is written, because
the body must be right on the first try (see *Detector B* below). This is
a plain tracking issue — no `wo:` label, no work-order id, no breakdown
row pointing at it — exactly as #301 was for `deepening-tool-seams` and
#254 for `deepening-cli-seams`.

```
gh issue create \
  --title "Nothing mechanical asks whether a fact is stated twice" \
  --body "This repo's bar is one fact, one owner, and nothing mechanical checks it. The detector suite covers citations (A), checksums (E), staleness (I) and label taxonomy (J); lint.py covers skill and artifact grammar. The only finder the class has is a human reading the tree during a manual deepening review, and that finder has a measured miss rate of 4 of 7: the review at fbfa3c3 confirmed six candidates and its run fixed four, while three more instances of the same class were already in the same tree — knowledge_plane.DONE_ROW byte-identical to gates.MERGED_ROW (closed by ADR-0058), sweeps.reconcile_drift versus dashboard._drift (closed by ADR-0060), and plane_drift.issue_lifecycle retyping cli.label_names (still open). Two of those needed emergency ADRs four days after a run that was specifically hunting this class shipped. Run artifacts: docs/fixes/one-fact-one-owner/."
```

Record the number it prints as `<N>`.

**Step 4 — open the PR.** Write the body to a file first and pass
`--body-file`; do not retype it inline and do not `gh pr edit` afterwards
(the `deepening-cli-seams` release lost a body edit to the Projects
(classic) deprecation, which failed while silently leaving the body
unchanged).

```
gh pr create \
  --base main \
  --head feat/one-fact-one-owner \
  --title "feat(one-owner): a pre-pass that asks whether a fact is stated twice" \
  --body-file <path-to-the-body-below>
```

**Step 5 — watch the checks.**

```
gh pr checks <PR> --watch
```

Expect `check`, `needs-review-label` and `review` to pass and
`merged-label` to skip — the shape every non-work-order PR has had since
ADR-0057 and #307/#308 fixed the two lifecycle legs' contradiction. The
`check` job runs `make check` **with the real `pull_request` event
payload present**, which is the only place detector B is genuinely
exercised.

**Step 6 — the merge is a HUMAN step, not an agent step.**

```
gh pr merge <PR> --squash --delete-branch     # run by the human code owner
gh pr view <PR> --json state,mergeCommit      # read the result back; the merge
                                              # command prints nothing on success
```

Two independent reasons, and either alone is sufficient:

1. **ADR-0036 clause 3** — an agent may merge only when the change is not
   itself a gate change, and *"any PR touching `docs/adr/**`, a run's
   `prd.md`, `architecture.md`, or `docs/design/**` … still requires a
   human code-owner merge."* This PR **adds `docs/adr/0061-…md` and edits
   `docs/adr/README.md`**. It is squarely inside that clause.
2. **The agent-merge classifier** — an agent-authored PR merge needs
   explicit human authorization, and this run has none: the brief records
   `[No preference]`, which is prepare-and-stop, not a merge mandate.

`CODEOWNERS` names `@mattbutlerengineering` for `*` and again for
`docs/adr/`. **Honest caveat:** branch protection could not be read —
`gh api repos/…/branches/main/protection` returns `403 Upgrade to GitHub
Pro or make this repository public`. On this repo's plan the ADR-0033
"physical control" is therefore **not physically enforced**; CODEOWNERS is
advisory here and the discipline is the operator's.

**Step 7 — sync local `main`.**

```
git switch main && git pull --ff-only
git log --oneline -1        # the squash commit
```

**Step 8 — post-release checks** (see the section below).

**Step 9 — commit the run's artifacts** (see *Open decisions*).

### Ordering note, taken from a live backlog seed

`docs/backlog.md:43` records what happened the last time a Ship stage ran
outward actions before writing its artifact: *"Ship pushed, opened #303,
merged it, closed #297 and dispatched the workflow, then hit an API error
before `release.md` existed, and the whole record had to be rebuilt from
git, `gh` and run logs by the orchestrator."* So when these steps are
executed, **append each one's result to this artifact's Release log before
taking the next step**, rather than writing the log at the end. Steps 2, 3,
4 and 6 are each irreversible-in-the-world.

## The PR body — literal text

Verbatim, with `#<N>` replaced by the issue number from step 3 and nothing
else changed. The first line and the last line are the two detector B
carries; everything between them is description.

````markdown
No work order: a maintenance run captured from two `docs/backlog.md` seeds (lines 19 and 45) and worked through `docs/fixes/one-fact-one-owner/`. No `WO-####` id was minted and none exists: minting one with no breakdown-mirrored issue behind it would run the dispatch plane ahead of the knowledge plane (ADR-0032), and the run's brief rules out tracker interaction for its work items.

## The condition

This repo's stated bar is **one fact, one owner**, and nothing mechanical asked whether a fact had acquired a second one. The detector suite covers citations (A), checksums (E), staleness (I) and label taxonomy (J); `lint.py` covers skill and artifact grammar. The only finder the class had was a human reading the tree during a manual deepening review, and that finder has a measured miss rate of **4 of 7**: the review at `fbfa3c3` confirmed six candidates and its run fixed four, while three more instances of the same class were already in the same tree — two of them needed emergency ADRs (0058, 0060) four days later, and the third is still open.

## What lands

- **`one_owner.py`** (new, 443 lines) — a read-only pre-pass over the repo's own tracked Python. Two rules: `same-value` (two modules bind the same module-level literal) and `same-keys` (two functions read the same payload keys). Output is `one-owner:` problem strings through `cli.report`.
- **`tests/test_one_owner.py`** (new, 975 lines, 61 cases) — every case against literal fact sites or fixture trees, never against the live tree, so the suite does not decay as the tree is cleaned. Two of the three historical misses are pinned as caught; the third is pinned as a **known miss**, in the assertion's own comment.
- **ADR-0061** (provisional) — a carve-out lives at the definition site and must pay rent. A deliberate second owner is annotated `# one-owner: <module>.<name> (ADR-####)` above the definition it excuses; the pass re-derives the carve-out in both directions on every run, so a marker that stops matching starts speaking.
- **Three live annotations** on the `runner('git')` group (`budget_guard.py`, `dashboard.py`, `one_owner.py`) — the mechanism has a real user on day one.
- **Triggers** — `factory.py`'s `one-owner` verb, a `CLAUDE.md` entry, and step 9 in `docs/factory/improvement-routine.md` §2.

## What deliberately does not land

It is **not a gate.** `one_owner.py` is outside `make check` and outside every workflow, so a finding never colours main red — it is a question for a human. Nothing imports it, `gates.py` is untouched (letter `K` still reads `"K": (None, None, "unused")`), and `plane_drift.py` — the acceptance fixture — is not in this diff. Fixing the fixture is seeded separately.

## The acceptance fixture, found unaided

The tool's own source names none of it, and it prints:

```
one-owner: cli.py:376 label_names and plane_drift.py:31 issue_lifecycle read the same payload keys (labels, name) — one fact, one owner
```

Nine findings at HEAD, eight of them true and undecided (folding them is out of scope for this run; they route to `docs/backlog.md` at Operate). Zero false positives among the findings that were adjudicated. The tenth measured group is the annotated `runner('git')` one, now silent — the carve-out paying rent in both directions.

## Evidence

```
python3 -m unittest discover tests   Ran 1344 tests — OK
python3 lint.py                      lint: 0 problem(s) across 24 skills
python3 gates.py                     gates: 0 problem(s)
python3 gates.py --selftest          selftest: ok
python3 one_owner.py                 one-owner: 9 problem(s)  (exit 1 — by design, not a gate)
```

`factory/manifest.json` carries the one regenerated checksum for the payload twin of `budget_guard.py`; `factory_init.py update-manifest` is idempotent on this tree and a repo stamped from this payload passes its own gates.

## Not in this diff, on purpose

`docs/factory/costs.jsonl`, `evals/**`, `LEDGER.md`, `skills/**`, `.github/workflows/**` and `docs/pipeline-protocol.md` are untouched — no commit on this branch reaches any of them. No migration, no persisted-shape change, no new configuration and no environment dependency.

Closes #<N>
````

## Detector B — what was checked, and what remains a prediction

Detector B (`gates.check_pr_traceability`) requires **either** a `WO-####`
token **or** an explicit `No work order: <reason>` waiver, **plus** a
`Closes #N` link — *"the Closes-#N link is required regardless."* This run
minted no `WO-####` id and has no tracker issue, so the body above carries
the waiver as its first line and the `Closes` link as its last.

**This was driven locally, not merely reasoned about.** Detector B reads
`$GITHUB_EVENT_PATH`, so a payload of the real shape
(`{"action": "opened", "pull_request": {…, "body": …}}`) was synthesized in
a scratch directory and the checker called against it:

```
detector B on the body with `Closes #<N>` unreplaced
   → ['B: PR body has no Closes #N link']      (the placeholder is not a number)
detector B on the same body with a real number
   → []                                        PASS
control — the same body with the Closes line removed
   → ['B: PR body has no Closes #N link']
control — the same body with the waiver line replaced by prose
   → ['B: PR body cites no work-order id']
```

Both controls fail, so the checks were genuinely exercised rather than
skipped. The whole suite was then run with that payload present:

```
$ GITHUB_EVENT_PATH=<synthesized> python3 gates.py
gates: 0 problem(s)                            [exit 0]
```

The body also carries **no `WO-####` token** (`\bWO-\d{4}\b` finds none —
the literal `WO-####` in the waiver sentence is not digits). That is
deliberate: `docs/backlog.md:39` records that a body carrying a WO id fails
`needs-review-label` while a body without one used to fail `merged-label`,
so no body satisfied both and every housekeeping PR merged red. ADR-0057
and #307/#308 closed that, and #310/#312/#314/#316 have all merged green on
a token-free body since.

**What is still a prediction, stated plainly.** The local run proves the
body text satisfies detector B's two regexes. It does **not** prove CI will
pass, because:

- the real event payload is GitHub's, delivered against the merge-result
  checkout, not a file this stage wrote;
- `#<N>` must be a **real, open** issue number — the regex accepts any
  digits, so a wrong number passes detector B and still breaks the audit
  trail it exists to protect;
- the other two jobs (`needs-review-label`, `review`) read live tracker
  state through `validator.py` and cannot be exercised locally at all.

The precedent releases both warn about this: `deepening-cli-seams` took a
**red first CI run** on detector B. Decide the `Closes #N` target before
opening the PR (step 3 is ordered that way for exactly this reason), and
never edit the body afterwards.

## Checked against `docs/factory/improvement-routine.md` §8 Non-negotiables

§8 binds the daily routine, not this run, but the plan was read against it
line by line and it constrains three things here:

- *"Never merge any PR, including its own (ADR-0033 gate 3; ADR-0036
  requires a non-authoring reviewer)"* — **held.** Step 6 is a human step
  and is marked as one twice over.
- *"Never touch a gate-change path in a routine PR: `docs/adr/**`…"* —
  **this PR does touch `docs/adr/**`.** That prohibition scopes the
  routine's own PRs; this is an autorun maintenance run, and the sanctioned
  path for a gate-path change is exactly this: a PR a human code owner
  merges. The consequence is not that the PR is forbidden — it is that
  step 6 cannot be delegated (ADR-0036 clause 3, above).
- *"Never edit this file"* — **this PR edits
  `docs/factory/improvement-routine.md`.** Same reading, and CLAUDE.md
  states it directly: the playbook is *"tuned by PR, never edited by the
  routine itself."* This is the PR path, not the routine editing itself.
- *"Never run `trigger_eval.py`, `charter_replay.py` … never write
  `evals/results/**` … never change LEDGER maturity"* — **held.** Neither
  was run; `git diff --stat origin/main..HEAD -- evals/ LEDGER.md` is
  empty; nothing was written to `docs/factory/costs.jsonl` (which takes
  rows only via `budget_guard.py record`).
- *"Never create a work-order issue or write a work-order id ahead of its
  breakdown row (ADR-0032)"* — **held.** Step 3 mints a plain tracking
  issue with no `wo:` label and no work-order semantics; no `WO-####`
  token exists anywhere in this run.
- *"Never weaken, skip, or delete a test, detector, eval, or charter"* —
  **held.** The diff's single deleted line is the old manifest checksum;
  everything else is additive, and the suite went from 1,282 to 1,344
  tests.
- Caps (`routine/` branch prefix, one PR, one issue, the
  `<!-- improvement-routine -->` body marker) are routine caps and do not
  apply; the branch is `feat/…` per the repo's PR convention.

## No version, no tag — confirmed against the repo

Checked rather than assumed:

```
$ git tag --list | wc -l
0
$ gh release list
(empty)
$ git log -p --follow -- package.json | grep -E '^[+-]\s*"version"'
+  "version": "0.1.0",          # one addition, no modification, ever
```

Both `package.json` and `.claude-plugin/plugin.json` read `0.1.0`, neither
is in this diff, and the repo has never cut a tag or a release. This is
internal tooling vended from the repo, not a published package, so **no
version bump and no tag are part of this release**. Finding recorded either
way, as asked.

## Open decisions for the operator — surfaced, not guessed

1. **When do the run's artifacts get committed?** Five of this run's
   artifacts are uncommitted by the run's own git policy —
   `defect.md`, `architecture.md`, `autorun-brief.md`, `verification.md`,
   `review.md`, and this file — while `breakdown.md` is committed and in
   the diff. Two other runs' `retro.md` files and `docs/backlog.md`'s two
   claim markers are also uncommitted and are **not mine to touch**. The
   precedent (`deepening-tool-seams`) put the run's artifacts through
   `review.md` on the branch and committed `release.md` directly on `main`
   after the merge, because it records the merge sha. Nothing in the skill
   supplies a default, and `docs/backlog.md:10` already carries the
   unclaimed seed *"Make artifact-commit an explicit stage step so run docs
   can't be left untracked."* **Left to the operator.** Evidence that
   either choice is safe: `make check` is green **right now, with all six
   uncommitted artifacts present in the tree** — `lint.py` and `gates.py`
   walk the working tree, not the index — so committing them onto the
   branch will not turn CI red.
2. **The `Closes #N` target** — step 3 mints a tracking issue. If the
   operator would rather point at an existing open issue, the number
   changes and nothing else does. (No existing open issue is this run's
   subject; #178 and #181 are the permanent marker-bearing state issues
   that must never be closed by a PR.)

## Release log

Recorded as it happened. **Every entry is a pre-flight check; not one is a
release action.**

1. Read `pipeline-protocol.md`, the ship skill and its template,
   `CLAUDE.md`, and the run's `defect.md` / `architecture.md` /
   `breakdown.md` / `verification.md` / `review.md` → soft gate satisfied:
   `review.md` exists with **no critical findings**.
2. `make check` at `ca77b4c` → green, quoted above. Re-run here rather
   than trusted from `verification.md`, which was written three commits
   earlier.
3. `python3 one_owner.py` → nine findings, exit 1 — the expected output,
   and confirmed **not** part of `make check` (the `check` target was read)
   and **not** in any workflow (grepped).
4. `python3 -m unittest tests.test_factory_init` → `Ran 52 tests … OK`.
5. Secrets scan of the 2,197-line diff across fourteen credential shapes →
   **zero credential hits**; every benign match read and named above.
   *Hiccup, recorded:* the first scan was a single combined regex and
   `ugrep` rejected it (`exceeds complexity limits`); it was re-run as
   fourteen separate patterns, which is the result quoted.
6. In-memory recomputation of `update-manifest`'s two write steps →
   manifest map reproduces exactly (0 differing keys), all `MIRRORS`
   mirrors byte-identical (0 drifted). No byte written.
7. `python3 factory_init.py stamp <scratch>` into a throwaway git tree →
   `factory-init: 0 problem(s)`; the stamped repo's own
   `gates.py` and `gates.py --selftest` both green; `one_owner.py`
   correctly absent from its 17 payload tools.
8. `gh secret list`, `gh variable list`, `git tag --list`,
   `gh release list`, `gh api …/commits/main`,
   `gh api …/branches/main/protection`, `gh pr list --state merged`,
   `gh pr view 302/316`, `gh issue view 315` → all **read-only**. The
   protection call returned `403 Upgrade to GitHub Pro…`, recorded above as
   a caveat rather than worked around.
9. Detector B driven against a synthesized event payload, with two
   controls, then the full suite with that payload present →
   `gates: 0 problem(s)`. Quoted above.
10. `make check` re-run **after** this artifact was written, to confirm the
    artifact itself does not break the tree — `lint.py` and `gates.py` walk
    the working tree, so a new run artifact is in scope for both:
    `lint: 0 problem(s) across 24 skills`, `gates: 0 problem(s)`,
    `selftest: ok`, `Ran 1344 tests … OK`, exit 0.
11. **No push, no branch, no tag, no issue, no PR, no merge, no workflow
    dispatch.** `git status --porcelain` at the end of this stage lists the
    same seven entries it listed at the start, plus this file.

## Post-release checks

**None were performed, because nothing was released.** These are the
checks to run after step 6, and each names the evidence it must produce:

1. **`make check` on merged `main`** (not on the branch) → must print
   `lint: 0 problem(s) across 24 skills`, `gates: 0 problem(s)`,
   `selftest: ok`, and `Ran 1344 tests … OK`. 1,344 tests, up from main's
   1,282.
2. **`python3 one_owner.py` on merged `main`** → must print the **same
   nine findings** listed in `verification.md`, and exit 1. A different
   count means something moved during the merge.
3. **`python3 factory.py one-owner`** → must print the same nine, proving
   the verb row is wired.
4. **A repo stamped from the merged payload passes its own gates** —
   `python3 factory_init.py stamp <scratch>` then
   `python3 tools/factory/gates.py` and `--selftest`. This is the surface
   product repos actually receive; drive it, do not argue it. (Pre-driven
   at `ca77b4c` above; re-drive on the merge commit.)
5. **The tracking issue `#<N>` is closed by the `Closes` link** —
   `gh issue view <N> --json state` → `CLOSED`. If it is open, the link
   did not resolve and the audit trail is broken; close it by hand with a
   comment naming the merge sha.
6. **The next daily improvement-routine run reads step 9 without turning
   red** — the routine reads its playbook from `main`, so the first run
   after the merge is the first execution of the new step. `one_owner.py`
   exits nonzero whenever it finds anything; §2 step 9 says so explicitly,
   but the first live run is the proof. Check the routine's report carries
   the findings under Proposals and its journal's Health section still
   reads green.

## Outcome

**Prepared and stopped — not shipped, by design.**

Every pre-flight gate is green: verification 19 PASS + 1 PASS-AS-AMENDED +
0 FAIL, review with zero criticals and both fix-before-ship items landed,
zero secrets in a fourteen-pattern scan, no configuration or environment
dependency added, no migration, the one data artifact (`factory/manifest.json`)
proved idempotent read-only and green on both its pins, and a three-stage
rollback plan with real commands. The change is **release-ready**; the
release is the operator's to run, and step 6 — the merge — is a human step
under ADR-0036 clause 3 regardless of who runs the rest.

Two things are honestly unproven and are marked as such rather than
smoothed over: **detector B's behaviour in CI** (driven locally against a
synthesized payload, which proves the body's text and not the CI run), and
**branch protection**, which this repo's plan would not let `gh` read.

Next stage is **Operate**.

## Release log — what actually executed, 2026-08-23

Appended step by step as each ran, per the ordering note above. The
release moved from prepare-and-stop to executed after the operator said
so; **the merge did not run** and is still the human code-owner step.

| # | Step | Result |
|---|---|---|
| 1 | `git switch -c feat/one-fact-one-owner` + `git branch -f main 7650052` | Done. `main` back at `origin/main`; 17 commits on the branch; all 10 uncommitted entries carried across. |
| — | Commit the run records | `f85808e docs(fixes): close out three maintenance runs` — 10 files, including this run's artifacts and the two sibling runs' `retro.md`. Battery green after: 1344 OK / lint 0 / gates 0 / selftest ok. |
| 2 | `git push -u origin feat/one-fact-one-owner` | Done, new branch. `origin/main` untouched at `7650052`. |
| 3 | `gh issue create` | **#317**. First attempt was denied by a transient tool classifier error; retried with `--body-file` and succeeded. Recorded because a clean-looking log that omits the retry is a lie to the next release. |
| — | Detector B pre-flight with the real number | `check_pr_traceability` → `[]` PASS; control with the `Closes` line removed → `['B: PR body has no Closes #N link']`. The check was exercised, not trivially passed. |
| 4 | `gh pr create` | **#318**, body taken verbatim from *The PR body — literal text* with only `#<N>` → `#317`. No `gh pr edit` afterwards. |
| 5 | `gh pr checks 318 --watch` | `check` **pass** (22s), `needs-review-label` **pass** (8s), `review` **pass** (21s), `merged-label` **skipping**. Exactly the predicted shape; detector B's prediction held against the real payload. |
| 6 | `gh pr merge` | **NOT RUN — blocked by ADR-0036 clause 3.** |

### Why step 6 stopped

ADR-0036 clause 3: *"any PR touching `docs/adr/**` … still requires a
human code-owner merge. An agent cannot widen its own authority."* This
PR adds `docs/adr/0061-a-carve-out-lives-at-the-definition-site.md` and
edits `docs/adr/README.md` — verified against `gh pr view 318 --json
files`. Operator instruction resolves the agent-merge classifier, but it
does not resolve clause 3, which constrains **who performs the merge**,
not who authorises it.

Clause 2 is also unmet independently: the PR has **0 reviews** and its
author is `mattbutlerengineering`, so no non-authoring reviewer has
re-executed the verification and recorded its pass on the PR.

The command, for the human code owner:

```
gh pr merge 318 --squash --delete-branch
gh pr view 318 --json state,mergeCommit
```

Steps 7–9 (sync `main`, post-release checks, artifact commit — the last
already done early as `f85808e`) follow the merge.
