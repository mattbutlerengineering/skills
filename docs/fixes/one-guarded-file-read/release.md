---
stage: ship
run: maintenance:one-guarded-file-read
date: 2026-10-04
assumptions:
  - "The autorun brief authorizes prepare-and-stop only (no push, no pull request, no merge, no tag, no version bump, no tracker write), so every release step below is marked NOT EXECUTED and none was run. gh was used for reads only."
  - "Production means main. The project has never tagged a release, so landing is: push the branch, open a pull request against main, green checks, a human squash merge. The pull request touches docs/adr/**, so it is a human gate-2 merge (ADR-0036 clause 3) and the author never merges."
  - "The brief says no issue, but detector B requires a Closes #N link on every pull request and has no waiver for it (only the work-order half has one). A tracking issue is therefore an operator-only step, drafted below and not created. Its number is a placeholder."
  - "The pairwise test ran every open pull request (11), not only the ones whose files overlap this run, because each takes about 25 seconds. Overlap was CLAUDE.md for 608, 595 and 585, factory/manifest.json and tests/test_work_queue.py for 602, and none for the other six."
  - "origin/main was found at the run's base (661ffc7), so the merge onto current origin/main is the branch itself. The scratch clone was cloned from the worktree and given the GitHub remote as a second remote for read-only fetches; nothing was pushed from it."
  - "The state of the open major is taken exactly as review.md leaves it: open, for the owner. This stage does not decide it, fix it or fold any minor in."
---

# Release: one owner for the guarded local-file read

**Prepared, not executed.** Nothing was pushed, no pull request or issue was
opened, nothing merged, tagged or published, and no tracker was written. The
branch `refactor/one-guarded-file-read` is local only, HEAD `8924ebb`, 24
commits on top of `661ffc7`.

**Verdict: prepared, not ready.** Every check below passes and nothing is
critical, but `review.md` leaves one major open for the owner (the `object`
kind has no caller and its docstring recommends it). Until the owner decides
it, the release is not ready to push. Either fix is one further mirrored
commit followed by a re-verify, so the decision costs one small round, not a
redesign. The run stays active until a retro exists.

## Pre-flight

### 1. Verification is green: PASS

`verification.md` records nine of nine criteria PASS and no unresolved
failure. The battery was re-run at HEAD `8924ebb`:

```
$ python3 -m unittest discover tests > unit.txt 2>&1 ; echo $?
0
Ran 1874 tests in 21.316s
OK
$ python3 lint.py ; echo $?
lint: 0 problem(s) across 25 skills        (exit 0)
$ python3 gates.py ; echo $?
gates: 0 problem(s)                        (exit 0)
$ python3 gates.py --selftest ; echo $?
selftest: ok                               (exit 0)
```

Detector B skips locally (no pull request event payload). It is covered below
by what the body must contain.

### 2. Review state: PASS, with one open major

No unfixed critical. `review.md` decides, exactly:

- **Major (open, needs owner decision): the `object` kind has no caller.**
  The approved design justified a fourth kind by two callers
  (`label_sync`, detector K). The Architect's replay then showed that
  `object` rewrites the `null` cell of every reader with its own wording, so
  all four such readers became hand-fixes and no adopter asks for `object`.
  `cli.read_file`'s docstring and ADR-0075 decision 1 still recommend it.
  Reviewer's recommendation: option (a), drop it.
- **Minor 1 (deferred):** "never raises for a local-file failure" is false
  for an integer literal over 4,300 digits and for 200,000-deep nesting.
  Identical at `661ffc7`; only the claim is new. One line to fix, to fold
  into the major's commit, else a backlog seed.
- **Minor 2 (deferred, same follow-up):** `kind` is not validated, so a
  mistyped kind skips the shape check.
- **Minor 3 (deferred, backlog seed):** hand-fixed `label_sync.load_labels`
  (so detector J) still raises on Python 3.12 under an unsearchable
  `.github/`. Not a regression.
- **Minor 4 (deferred, one sentence in ADR-0075 decision 2):** the non-UTF-8
  wording rule has two unnamed exceptions, `cli.read_event` and
  `dashboard.repo_set`.
- **Minor 5 (deferred, same follow-up if wanted):** only one of nine
  hand-written readers says in code why it does not use `read_file`.
- **Minor 6 (fix, non-blocking):** one test in `tests/test_budget_guard.py`
  builds a work-order id with a format expression where its file uses
  literals. One test-only line; rides with any follow-up or is dropped.

### 3. No secrets in the diff: PASS

Scanned the added lines of `git diff 661ffc7..HEAD` for AWS key ids, GitHub
tokens (`ghp_`, `gho_`, `github_pat_`), `sk-` keys, Slack tokens, PEM private
key headers, `api_key`/`secret`/`password` assignments with a literal value,
bearer tokens, and URLs carrying credentials or `token=`/`key=` query
strings. No match. No URL at all is added. No configuration file is added and
no network call is introduced.

### 4. Migrations and data changes: PASS, none apply

No schema, no stored data and no config file changes shape. The change only
alters what a reader does when a file cannot be read: 16 of the 19 cells that
raised at `661ffc7` now return a problem string, six sites outside the matrix
do too, and the monthly cap check fails closed on a non-UTF-8 ledger. Three
cells still raise, all in `trigger_eval.print_metrics`, out of scope by
decision.

**Two problem strings changed wording, deliberately**, both for a file that
is not UTF-8:

| Reader | Before | After |
|---|---|---|
| `factory_config.load` | `config: cannot read .github/factory.json: ...` | `config: .github/factory.json is not valid JSON: ...` |
| `label_sync.load_labels` (detector J) | `L: cannot read .github/labels.json: ...` | `L: .github/labels.json is not valid JSON: ...` |

`review.md` checked the consumers: it grepped `*.py`, `*.md`, `*.yml`, `*.json`
and the `Makefile` outside `tests/` and `docs/fixes/`, and found no tool,
workflow, skill body or standing doc that matches on `config: cannot read` or
`L: cannot read`. The only hits are dated run records of earlier runs, which
stay as written. The only code that matched the old wording was the two tests
edited in commits A6 and A7 (`verification.md` criterion 3).

### 5. Is the base still current: PASS

```
$ git fetch origin main        (a read)
$ git ls-remote origin refs/heads/main
661ffc705e18dbc77185ffd498a6cbf943c5d8e8   refs/heads/main
```

`origin/main` has not moved past `661ffc7`, so the test merge onto it is the
branch itself and there is nothing to conflict with. The battery on that
result, in a scratch clone:

```
unit rc=0 (Ran 1874 tests in 20.700s OK)  lint rc=0 (lint: 0 problem(s) across 25 skills)
gates rc=0 (gates: 0 problem(s))          selftest rc=0 (selftest: ok)
```

If `main` moves before the merge and `factory/manifest.json` conflicts, resolve
it by regeneration, never by hand: take either side of the file, delete stray
`*.orig` and `*.rej`, then `python3 factory_init.py update-manifest`, and
commit.

### 6. Pairwise merge test against open pull requests: PASS, one expected manifest conflict

Eleven pull requests were open. Each head was fetched into the scratch clone
(`git fetch gh pull/<n>/head`), merged with this branch there, and the
battery run on the result. Every fetch succeeded. Each row's battery is
unit + lint + gates + selftest, all four green unless noted.

| PR | Overlap with this run | Merge | Battery |
|---|---|---|---|
| #602 fix(work_queue) blocked-by | `factory/manifest.json`, `tests/test_work_queue.py` | **CONFLICT in `factory/manifest.json` only**; `tests/test_work_queue.py` merged clean | green after regenerating: Ran 1881 tests OK |
| #608 queue-groomer docs | `CLAUDE.md` | clean | green, Ran 1874 OK |
| #595 charter_replay control arm | `CLAUDE.md` | clean | green, Ran 1896 OK |
| #585 detector roster docs | `CLAUDE.md` | clean | green, Ran 1874 OK |
| #589 backlog seeds | none | clean | green, Ran 1874 OK |
| #606, #604, #598, #596 | none | clean | green, Ran 1874 OK each |
| #600 charter fixtures | none | clean | green, Ran 1908 OK |
| #597 done-with-concerns | none | clean | green, Ran 1879 OK |

**#602 conflict and its resolution.** Both branches regenerate
`factory/manifest.json` (this one for seven mirrored modules, #602 for
`knowledge_plane.py` and `work_queue.py`). The conflict is the manifest
alone. Resolved in the scratch clone by taking one side, deleting stray
`.orig`/`.rej` (none existed), running `python3 factory_init.py update-manifest`
(`factory-init: 0 problem(s)`), and committing. Result: unit rc=0 Ran 1881
tests OK, lint 0 problem(s), gates 0 problem(s), selftest ok. Whichever of
the two lands second must do this regeneration.

None of the pairs is red. The sweep expires as soon as another pull request
lands; re-run it if the merge waits.

### 7. Rollback plan, concrete and rehearsed: PASS

Rehearsed in the scratch clone: branched from `origin/main` (`661ffc7`),
`git merge --squash refactor/one-guarded-file-read`, committed as one squash
commit (`117ec3d`), then `git revert --no-edit HEAD`.

```
$ git diff --stat 661ffc7 HEAD          (after the revert)
(empty: the tree equals origin/main, every touched file)
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)              (a no-op: git status clean)
$ battery on the reverted tree
unit rc=0 (Ran 1793 tests OK)  lint 0 problem(s)  gates 0 problem(s)  selftest ok
```

The revert needs no separate manifest step, because the manifest is
reverted in the same commit. Test count falls from 1874 to 1793, the 81 tests
this run added.

**Cost of a revert:** the tracebacks come back. The 16 cells that now return a
problem string raise again (non-UTF-8 and unreadable files in detectors E, F
and K, `foreign_entries`, `check_manifest`, `check_plugin_skills`,
`check_pi_package`, `check_backlog`, `load_case_set`, `read_execution` and
`load_payload`), as do the six dashboard, validator and `problems_for` sites,
and the monthly cap check stops failing closed on a non-UTF-8 ledger. The two
reworded strings revert to the `cannot read` wording. It also deletes this
run's documents and ADR-0075; keep them with a follow-up commit if the run
should stay legible. No data is lost, since nothing here writes data.

### 8. Plugin version: PASS, no bump called for

`git diff --name-only 661ffc7..HEAD -- skills .claude-plugin` lists nothing.
The plugin cache cannot go stale from this change. No tag follows.

## What to read before merging

- `docs/adr/0075-the-guarded-file-read-joins-the-cli-seam.md`. It is
  **provisional**; the major above is about decision 1.
- The `CLAUDE.md` seam-modules line, which now says `cli.py` owns "the
  guarded local-file read (`read_file`, ADR-0075)".
- `CONTEXT.md` gained no term, deliberately.
- `review.md`'s *Major* section, for the owner decision.

## Release steps (prepared, NOT EXECUTED)

1. **NOT EXECUTED. Owner decision on the open major.** Options, from
   `review.md`:
   - (a) **Drop `object`. Reviewer's recommendation.** Delete the
     `value is None` branch and the `object` docstring row, reword the last
     docstring sentence, remove `object` from `TestReadFile.KINDS` and every
     `assert_pairs` row, make ADR-0075 decision 1 name three kinds. No
     recorded cell moves.
   - (b) Keep `object` and make the docstring true; ADR-0075 decision 1
     notes the kind has no caller yet.
   - (c) Leave it. Not recommended.

   Either fix is one further mirrored commit. It can carry the mechanical
   minors (1, 2, 4, 5 and 6), costs one `update-manifest`, and is followed by
   a re-verify (the four-command battery, plus a refreshed `verification.md`
   note). After it, re-run pre-flight 5 and 6 if `origin/main` has moved.

2. **NOT EXECUTED. Push the branch.**
   ```
   git push -u origin refactor/one-guarded-file-read
   ```

3. **NOT EXECUTED. Decide the tracking issue.** Detector B
   (`gates.check_pr_traceability`) fails a pull request body unless **both**
   of these hold:
   - It cites a work-order id, **or** says it implements none with the
     explicit, reasoned declaration. The accepted wording is
     `gates.NO_WO_DECLARATION`: `No work order: <reason>`, matched
     case-insensitively, hyphens or spaces allowed between the words, with a
     colon and then at least one non-space character. A bare marker with no
     reason waives nothing.
   - It has an issue-closing link, `Closes #N` (also `Fixes`, `Resolves`,
     `Closed`, `Closes: #N`). **This half has no waiver.**

   The brief said no issue, and a pull request with the waiver but no
   `Closes #N` still fails with `B: PR body has no Closes #N link`. So the
   operator must either open a tracking issue now or add one afterwards; the
   check re-runs on a body edit. **Never use `Closes` on issues #178 or #181:
   they are permanent state.** A suitable issue:
```
ISSUE=$(gh issue create \
  --title "refactor: one owner for the guarded local-file read (cli.read_file)" \
  --body "Tracking issue for the pull request that adds cli.read_file (ADR-0075). Closed by that pull request." \
  | grep -o '[0-9]*$')
echo "$ISSUE"
```

4. **NOT EXECUTED. Write the body and open the draft pull request.** The body
   goes through a quoted heredoc so backticks in it do not execute; the issue
   number is substituted afterwards. The body states the waiver and the link:
```
cat > "$TMPDIR/pr-body.md" <<'EOF'
## Summary

The rule "read a local file and turn every way it can fail into a problem
string" had no owner: an AST sweep found 67 file-read sites, 28 guarded in
five different exception spellings and 39 unguarded. This adds one entry
point, `cli.read_file(path, shown, kind)`, to the cli seam (ADR-0075,
provisional), adopts it in eleven readers, and hand-fixes nine that cannot
use it. 16 of the 19 cells that raised before now return a problem string,
six sites outside the matrix do too, and the monthly cap check fails
closed on a non-UTF-8 ledger.

No work order: a maintenance refactor of the cli seam driven by a
deepening review, tracked by an issue rather than a work order.

Closes #ISSUE_NUMBER

## Two problem strings change wording

Both are for a config file that is not UTF-8. No tool, workflow, skill or
standing doc matches on either (checked in review.md).

- `config: cannot read .github/factory.json: ...` becomes
  `config: .github/factory.json is not valid JSON: ...`
- `L: cannot read .github/labels.json: ...` becomes
  `L: .github/labels.json is not valid JSON: ...`

## Open major (owner decision before merge)

review.md leaves one major open: the `object` kind of `read_file` has no
caller, and its docstring and ADR-0075 decision 1 still recommend it.
Reviewer recommends dropping it (one further mirrored commit). Six minors
are deferred or optional, as review.md records.

## Test evidence

At HEAD, from a clean tree:

- `python3 -m unittest discover tests`: Ran 1874 tests, OK
- `python3 lint.py`: lint: 0 problem(s) across 25 skills
- `python3 gates.py`: gates: 0 problem(s)
- `python3 gates.py --selftest`: selftest: ok
- Pairwise merge with all 11 open PRs: clean except #602, whose only
  conflict is `factory/manifest.json` (regenerate with
  `python3 factory_init.py update-manifest`); battery green on every pair.
- Rollback rehearsed: squash then revert equals origin/main, battery green.

## Test plan

- [ ] Owner decides the open major and any follow-up commit is verified
- [ ] CI green on this PR, including detector B
- [ ] Non-authoring human reviewer re-runs the battery (ADR-0036 clause 2)
- [ ] Human gate-2 squash merge (this PR touches docs/adr/**)
- [ ] CI green on main after the merge

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
sed -i '' "s/ISSUE_NUMBER/$ISSUE/" "$TMPDIR/pr-body.md"

gh pr create --draft --base main --head refactor/one-guarded-file-read \
  --title "refactor(cli): one owner for the guarded local-file read (read_file, ADR-0075)" \
  --body-file "$TMPDIR/pr-body.md"
```
   `gh pr edit` is unreliable in this repo (it exits 1 and writes nothing).
   Any later body edit goes through the REST API:
```
gh api -X PATCH repos/mattbutlerengineering/skills/pulls/<N> -F body=@"$TMPDIR/pr-body.md"
```

5. **NOT EXECUTED. Wait for green checks**, including the PR-event `check`
   job where detector B runs. If a second pull request lands first and
   `factory/manifest.json` conflicts, regenerate it as in pre-flight 5.

6. **NOT EXECUTED. Human gate-2 merge, squash.** This pull request touches
   `docs/adr/**` (ADR-0036 clause 3), so a human merges it and the author
   never does. Mark it ready for review, have the non-authoring reviewer
   re-run the battery (clause 2), then squash-merge. No tag follows and no
   plugin version bump follows.

## Post-release checks (for the operator, NOT EXECUTED)

- CI green on `main` after the squash merge: `gh run list --branch main
  --limit 3`. Treat zero runs as a possible GitHub Actions outage, not a
  failure.
- A stamped product repo picks up the changed payload at its next factory
  stamp or refresh: seven mirrored tools changed (`cli.py`, `cost_ledger.py`,
  `factory_config.py`, `gates.py`, `label_sync.py`, `standards_index.py`,
  `validator.py`), so the payload manifest changed. In the product repo, run
  the stamp or refresh, then `python3 factory_init.py update-manifest` if the
  product repo keeps its own, and confirm detector E reports
  `gates: 0 problem(s)`. Nothing reaches a product repo until it re-stamps.
- Spot check the behaviour change where it matters: a config file holding
  bytes that are not UTF-8 now yields a `config: ... is not valid JSON`
  problem string from `factory_config.load`, not a traceback.

## Outcome

Prepared, not executed. All eight pre-flight checks pass; the one blocker is
the owner's decision on the open major. Nothing has been released.
