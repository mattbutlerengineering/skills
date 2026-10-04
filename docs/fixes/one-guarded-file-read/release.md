---
stage: ship
run: maintenance:one-guarded-file-read
date: 2026-10-04
assumptions:
  - "The autorun brief authorizes prepare-and-stop only (no push, no pull request, no merge, no tag, no version bump, no tracker write), so every release step below is marked NOT EXECUTED and none was run. gh was used for reads only."
  - "Production means main. The project has never tagged a release, so landing is: push the branch, open a pull request against main, green checks, a human squash merge. The pull request touches docs/adr/**, so it is a human gate-2 merge (ADR-0036 clause 3) and the author never merges."
  - "The brief says no issue, but detector B requires a Closes #N link on every pull request and has no waiver for it (only the work-order half has one). A tracking issue is therefore an operator-only step, drafted below and not created. Its number is a placeholder."
  - "First preparation (864f1aa): The pairwise test ran every open pull request (11), not only the ones whose files overlap this run, because each takes about 25 seconds. Overlap was CLAUDE.md for 608, 595 and 585, factory/manifest.json and tests/test_work_queue.py for 602, and none for the other six."
  - "origin/main was found at the run's base (661ffc7), so the merge onto current origin/main is the branch itself. The scratch clone was cloned from the worktree and given the GitHub remote as a second remote for read-only fetches; nothing was pushed from it."
  - "First preparation (864f1aa): The state of the open major is taken exactly as review.md leaves it: open, for the owner. This stage does not decide it, fix it or fold any minor in."
  - "Re-preparation 2026-10-04, option (a): the fix loop this release now contains (864f1aa..e46fa71) exists because review.md's recommended option (a) for the open major, dropping the object kind, was taken as the default after the operator re-invoked autorun without naming an option (autorun-brief.md, 'Resume, 2026-10-04'). That is the orchestrating session's reading, not the operator's words. So the operator's confirmation of (a) is release step 1, and no later step is to run before it."
  - "Re-preparation, decided without operator input: the body of this file is rewritten for the state at e46fa71 instead of being appended under the first version, because nothing in the first version was executed and the operator acts from the top of the file. The first version stays readable with git show 864f1aa:docs/fixes/one-guarded-file-read/release.md, and the Preparation history section records what changed. That is the orchestrating session's instruction for this stage, not the operator's."
  - "Re-preparation, decided without operator input: the verdict 'prepared and ready for the operator's steps' is this stage's, on the rule that all eight pre-flight checks pass and the re-review leaves no critical and no open major. Ready means the operator can start at step 1. It does not mean option (a) is confirmed or N1 is decided."
  - "Re-preparation, decided without operator input: this stage does not decide N1 or N2 and changes no code and no ADR text. Step 2 gives both paths and puts the reviewer's recommendation first. The drafted pull request body is true of the branch as it stands, which is the merge-without-the-fix path. Taking the fix means one more Implement, Verify and Review pass and a third preparation of this file."
  - "Re-preparation, decided without operator input: pre-flight ran at e46fa71. The battery ran in the worktree on Python 3.14.6 and 3.12.13. The squash result and the reverted tree ran on both in the scratch clone. The eleven pairwise results ran on 3.14.6 only, as the orchestrating session instructed. The commit that adds this file comes after e46fa71 and changes this one document; the battery was run once more on both Pythons with the file in place, and the pairwise and rollback rehearsals were not repeated for it."
  - "Re-preparation, decided without operator input: the pairwise test again ran all 11 open pull requests. Overlap was measured against each one's merge base with main: CLAUDE.md for 585, 595, 600 and 608, factory/manifest.json and tests/test_work_queue.py for 602, and none for the other six. 600 targets 595's branch and not main; its head was merged as it stands, so that pair carries 595's commits too. The manifest conflict with 602 was resolved by taking this branch's side and regenerating."
  - "Re-preparation, decided without operator input: the tracking issue is drafted as a plain issue with no label, so no workflow that triggers on a label fires. Its title and body, the pull request's title and the reason given in the waiver line are this stage's wording. Precedent: the tracking issues of deepening-cli-seams and deepening-tool-seams."
  - "Re-preparation, decided without operator input: the secret scan's pattern list is this stage's choice and is named in pre-flight 3. The matrix replay, the six-site probe and the ledger probe quoted in pre-flight 4 ran on a git archive export of e46fa71 with the session-local scratch tools (ogfr/matrix.py, diff_matrix.py, probe_six.py) and probes written for this pass under ogfr/ship-d/. They are not durable; the durable evidence is the repo's own tests."
  - "Re-preparation, decided without operator input: the retro seeds are listed here for Operate and none was added to docs/backlog.md. The last three in that list are this stage's own observations, not the reviewer's."
---

# Release: one owner for the guarded local-file read

**Prepared, not executed.** Nothing was pushed, no pull request or issue was
opened, nothing merged, tagged or published, and no tracker was written. The
branch `refactor/one-guarded-file-read` is local only, HEAD `e46fa71`, 35
commits on top of `661ffc7`. The commit that adds this file is the 36th and
changes this document only.

**Verdict: prepared and ready for the operator's steps.** All eight
pre-flight checks pass at `e46fa71`, and the re-review leaves no critical and
no open major. The first step is the operator's confirmation of option (a):
the fix loop on this branch rests on the orchestrating session's reading of a
bare re-invocation of autorun, not on the operator's words. The second is the
operator's decision on N1. Nothing is pushed before both. The run stays
active until a retro exists.

How pre-flight was run. Python 3.14.6 (`python3`) and Python 3.12.13
(`python3.12`), on macOS, as uid 501, with `PYTHONINTMAXSTRDIGITS` unset.
"The battery" is four commands: `-m unittest discover tests`, `lint.py`,
`gates.py` and `gates.py --selftest`. A scratch script, `battery.sh <tree>
<python> <prefix>`, runs the four in a tree, redirects each to its own file
and records each exit code. A second, `summ.sh <prefix>`, prints the exit
codes and greps the deciding lines out of those files. Nothing was piped to
`tail`. All merging and rehearsal happened in a scratch
clone of the worktree under the session scratchpad (`ogfr/ship-d/clone`).
The clone calls GitHub `gh`, so `gh/main` there is what the worktree calls
`origin/main`. Both of the clone's push URLs were set to a dummy value before
anything else ran. HEAD in the worktree never moved, and this file is the
only one changed in it. No pre-flight command was retried. The only
non-zero exits among them were expected ones, each named where it happened:
the merge with #602, the three cherry-picks tried under step 1, and the
branch-protection read under step 7. One slip was this stage's own: a check
of this file's frontmatter passed a string where `protocol.read_frontmatter`
takes a path, raised, and was run again with a path.

## Pre-flight

### 1. Verification is green: PASS

`verification.md`'s re-verification, at `b94462b`, ends PASS: the nine brief
criteria again, the seven fix-loop claims, three named mutations and the
history checks. Its `Failures (re-verification, 2026-10-04)` section reads
"none." The two commits since then (`95830fa`, `e46fa71`) change
`verification.md` and `review.md` only.

The battery at HEAD `e46fa71`, in the worktree:

```
$ bash battery.sh <worktree> python3 out/head-314 ; bash summ.sh out/head-314          (Python 3.14.6)
unit_exit=0 lint_exit=0 gates_exit=0 selftest_exit=0
Ran 1877 tests in 21.331s
OK
lint: 0 problem(s) across 25 skills
gates: 0 problem(s)
selftest: ok
$ bash battery.sh <worktree> python3.12 out/head-312 ; bash summ.sh out/head-312       (Python 3.12.13)
unit_exit=0 lint_exit=0 gates_exit=0 selftest_exit=0
Ran 1877 tests in 19.860s
OK
lint: 0 problem(s) across 25 skills
gates: 0 problem(s)
selftest: ok
```

The battery was run once more in the worktree after this file was written,
because the commit that adds it is what gets pushed. On both Pythons all
four exit 0, with `Ran 1877 tests`, `OK`, `lint: 0 problem(s) across 25
skills`, `gates: 0 problem(s)` and `selftest: ok`. Its timings are left out
because quoting them would have changed the file after the run.

Detector B skips locally, because there is no pull-request event. Its rule
is stated from the code under step 4, and the drafted body was run through
it under step 5.

What verification could not show, and a release should know: no CI run
exists yet. Every result here is from one machine, on macOS, and CI runs
Linux on Python 3.12.

### 2. Review state: PASS

No unfixed critical and no open major in code. The re-review's verdict is
"Ready to ship (prepare-and-stop)": zero critical, zero major, three minor,
nothing cites an enforced standard and nothing routes back to Implement.
What it leaves, exactly:

| Finding | State | Decision |
|---|---|---|
| Major: the `object` kind has no caller | closed in code (`e6abfc1`; ADR-0075 in `4fe2983`) | the choice of option (a) itself awaits the operator: step 1 |
| Minor 1: two JSON documents make `read_file` raise | closed (`b121f2c`) | none left |
| Minor 2: `kind` is not validated | closed (`e6abfc1`) | none left |
| Minor 3: `label_sync.load_labels`, and so detector J, raises on Python 3.12 under an unsearchable `.github/` | still deferred, as the first pass decided | a seed for the retro; not a regression |
| Minor 4: ADR-0075's wording rule has two unnamed exceptions | closed (`4fe2983`) | none left |
| Minor 5: one of nine hand-written readers says why | closed (`cb5a75b`) | none left |
| Minor 6: a format expression where the file uses literals | closed (`5ecde58`) | none left |
| N1 (minor, new): a ledger line that the JSON parser refuses with anything but a syntax error still makes the monthly cap check and `budget_guard.record` raise | deferred, and raised to the operator | step 2; the reviewer recommends taking the one-line fix before the merge |
| N2 (minor, new): ADR-0075 does not carry the limit N1 describes | fix, non-blocking | one sentence at the end of decision 5, with step 1 or step 2 |
| N3 (minor, new): two new `TestReadFile` tests pass only under the interpreter's default limits | deferred | a seed for the retro; no configuration in use fails |

### 3. No secrets in the diff: PASS

Scanned the 6,687 added lines of `git diff 661ffc7..HEAD`, the whole run,
for: AWS key ids and secret-key assignments, GitHub tokens (`ghp_`, `gho_`,
`ghu_`, `ghs_`, `ghr_`, `github_pat_`), `sk-` keys, Stripe keys, Slack
tokens, Google API keys, JWTs, PEM private-key headers, bearer tokens,
authorization headers with a value, URLs carrying credentials, `token=` or
`key=` query strings, and assignments of a literal to `api_key`, `secret`,
`password`, `token` and their variants. **No match for any of them.**

Three catch-all patterns were run too, and they did match. None is a
secret:

- Hex runs of 40 characters or more, 9 matches: seven SHA-256 checksums in
  `factory/manifest.json` (public checksums of the payload files), the
  commit id of `origin/main` quoted in the first version of this file, and a
  run of the digit 1 in `verification.md` (the test document with a
  5,000-digit integer).
- Base64-shaped runs of 48 characters or more, 8 matches: the same lines,
  less the commit id.
- Any URL, 1 match: the Claude Code attribution line in the first version of
  this file. No other URL is added.

No configuration file is added and no network call is introduced. This
file's own new text is not in that diff, because it is not committed yet. The
same scan over it matches nothing but the catch-alls: the attribution URL
again, the commit id of `origin/main`, and two git tree ids quoted twice
each under checks 5 and 7.

### 4. Migrations and data changes: PASS, none apply

No schema, no stored data and no config file changes shape. The change
alters only what a reader does when a file cannot be read. Two tracked data
files change, neither by hand: `factory/manifest.json` has seven new
checksums, for the payload copies of the seven mirrored tools, and
`docs/adr/README.md` gains one index row.

The behaviour matrix was replayed for this pass on an export of `e46fa71`,
against the recording taken at `661ffc7` (18 readers, eight kinds of bad
file):

```
cells 144 | identical 123 | fixed 16 | wording changed 2 | still raising 3 | newly raising 0
```

The three that still raise are all `trigger_eval.print_metrics`, out of
scope by decision. None of the six sites outside the matrix raises. On a
ledger that is not UTF-8, `cost_ledger.read` now returns
`ledger: cannot read docs/factory/costs.jsonl: ...`, where the same call
raised `UnicodeDecodeError` on a `661ffc7` export. That the monthly cap
check and `budget_guard.record` fail closed on it is pinned by
`test_a_ledger_that_is_not_utf8_fails_closed` in `tests/test_cost_report.py`
and `tests/test_budget_guard.py`; both were run by name on both Pythons and
pass.

**Two problem strings changed wording, deliberately**, both for a file whose
bytes are not UTF-8 (ADR-0075 decision 3):

| Reader | Before | After |
|---|---|---|
| `factory_config.load` | `config: cannot read .github/factory.json: ...` | `config: .github/factory.json is not valid JSON: ...` |
| `label_sync.load_labels` (detector J) | `L: cannot read .github/labels.json: ...` | `L: .github/labels.json is not valid JSON: ...` |

Checked again for consumers: `git grep` for `config: cannot read` and
`L: cannot read` outside `tests/` and `docs/fixes/` finds one line and its
payload copy, `label_sync.py:68`, which is the producer of the
unreadable-file wording that did not change. Nothing matches on the old
wording. The two test hits are the unreadable-file cells, which keep
`cannot read`.

**One problem string was removed by the fix loop, with its branch:**
`<shown> is null`. This run added it (`5e5f494`) for the `object` kind and
removed it with that kind (`e6abfc1`). No caller ever passed `object`, so no
caller could receive the string, and it was never on `origin/main`: against
`661ffc7` the net change is nothing. `git grep "is null" -- "*.py"` finds
nothing at HEAD.

One thing is new at the call, and it is not a file failure: a `kind` other
than `str`, `dict` or `list` raises `ValueError` before the file is touched.
An AST sweep at HEAD finds 16 calls of `read_file` outside `tests/` (11 in
the root modules, 5 in the payload), each passing one of the three.

### 5. Is the base still current: PASS

```
$ git fetch origin main                          (a read; exit 0)
$ git ls-remote origin refs/heads/main
661ffc705e18dbc77185ffd498a6cbf943c5d8e8	refs/heads/main
$ git rev-list --count HEAD..origin/main
0
$ git rev-list --count origin/main..HEAD
35
```

`origin/main` has not moved past `661ffc7`, so there is nothing to merge and
nothing to conflict with. The squash of this branch onto it was made in the
scratch clone, and its tree is the branch tip's tree:

```
$ git rev-parse HEAD^{tree} refactor/one-guarded-file-read^{tree}       (HEAD is the squash commit, 8f04576)
4b1a4cf92da434a7cf641e64a773586366453405
4b1a4cf92da434a7cf641e64a773586366453405
```

The battery on that squash commit: on Python 3.14.6, all four exit 0,
`Ran 1877 tests in 20.488s`, `OK`, `lint: 0 problem(s) across 25 skills`,
`gates: 0 problem(s)`, `selftest: ok`. On Python 3.12.13 the same, with
`Ran 1877 tests in 19.834s`.

If `main` moves before the merge, this check and check 6 expire. Step 6
gives the commands for a manifest conflict.

### 6. Pairwise merge test against every open pull request: PASS, one expected manifest conflict

`gh pr list --state open` (a read) lists eleven. Each head was fetched into
the scratch clone (`git fetch gh pull/<n>/head`, every fetch exit 0, every
head equal to the one `gh` reports), merged with this branch there, one pair
at a time from the branch tip, and the battery run on the result. The
battery ran on Python 3.14.6 only, which is enough to show a pair that
merges clean and goes red. Each row is unit, lint, gates and selftest, all
four exit 0.

| PR (head) | Overlap with this run | Merge | Battery |
|---|---|---|---|
| #585 detector roster docs (`9a599ab`) | `CLAUDE.md` | clean | green, Ran 1877 tests OK |
| #589 backlog seeds (`d6dbd57`) | none | clean | green, Ran 1877 tests OK |
| #595 charter_replay control arm (`55debcb`) | `CLAUDE.md` | clean | green, Ran 1899 tests OK |
| #596 research note (`cff8597`) | none | clean | green, Ran 1877 tests OK |
| #597 done-with-concerns (`79e7c18`) | none | clean | green, Ran 1882 tests OK |
| #598 decompose placeholder scan (`2a07ca1`) | none | clean | green, Ran 1877 tests OK |
| #600 charter fixtures (`ba34095`), which targets #595's branch | `CLAUDE.md`, through #595 | clean | green, Ran 1911 tests OK |
| #602 fix(work_queue) blocked-by (`0d12bf7`) | `factory/manifest.json`, `tests/test_work_queue.py` | **conflict in `factory/manifest.json` only**; `tests/test_work_queue.py` merged clean | green after regenerating, Ran 1884 tests OK |
| #604 standards run docs (`54c7140`) | none | clean | green, Ran 1877 tests OK |
| #606 first-live-dispatch run docs (`bce2ccc`) | none | clean | green, Ran 1877 tests OK |
| #608 queue-groomer run docs (`9f52f56`) | `CLAUDE.md` | clean | green, Ran 1877 tests OK |

Every row also ends `lint: 0 problem(s) across 25 skills`,
`gates: 0 problem(s)` and `selftest: ok`, and every merged tree was clean
after its battery.

**#602's conflict and its resolution.** Both branches regenerate
`factory/manifest.json`. The conflict is that file alone. It was resolved in
the scratch clone in this order: take one side
(`git checkout --ours factory/manifest.json`), look for stray `*.orig` and
`*.rej` and delete them first (there were none), run
`python3 factory_init.py update-manifest` (`factory-init: 0 problem(s)`),
then `git add` and commit, then the battery. Whichever of the two lands
second has to do this.

None of the pairs is red. Two limits: the pairs were tested one at a time,
not in combination, and the sweep expires when any pull request lands or
moves its head.

### 7. Rollback plan, concrete and rehearsed: PASS

Rehearsed in the scratch clone: a branch from `gh/main` (`661ffc7`),
`git merge --squash refactor/one-guarded-file-read`, one commit (`8f04576`,
43 files, +6,687 / -291), then `git revert --no-edit HEAD` (`a815670`).

```
$ git rev-parse HEAD^{tree} gh/main^{tree}            (after the revert)
583f2e978ed3309290250e6b11d374e029f64b06
583f2e978ed3309290250e6b11d374e029f64b06
$ git diff --stat gh/main HEAD | wc -l
       0
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)                            (a no-op: git status stays clean)
```

The battery on the reverted tree: on Python 3.14.6, all four exit 0,
`Ran 1793 tests in 20.123s`, `OK`, `lint: 0 problem(s) across 25 skills`,
`gates: 0 problem(s)`, `selftest: ok`. On Python 3.12.13 the same, with
`Ran 1793 tests in 19.498s`. The count falls from 1877 to 1793: the 84 tests
this run adds.

The revert needs no separate manifest step when nothing else has landed,
because the manifest reverts in the same commit.

**The real rollback, after a real squash merge** (NOT EXECUTED, and only if
needed):

```
git fetch origin main
git switch -c revert/one-guarded-file-read origin/main
git revert --no-edit <sha of the squash commit on main>
python3 factory_init.py update-manifest
python3 -m unittest discover tests && python3 lint.py && python3 gates.py && python3 gates.py --selftest
git push -u origin revert/one-guarded-file-read
```

Then a pull request for that branch, with its own waiver line and its own
closing link to a new issue, and a human squash merge: it deletes ADR-0075,
so it is a `docs/adr/**` change too. If another pull request regenerated the
manifest in between, the revert conflicts in `factory/manifest.json`:
resolve it by regeneration as in check 6, then `git revert --continue`.

**Cost of a revert, in behaviour.** The tracebacks come back. The 16 cells
that now return a problem string raise again: files that are unreadable,
not UTF-8 or the wrong top-level shape in detectors E, F and K,
`foreign_entries`, `check_manifest`,
`check_plugin_skills`, `check_pi_package`, `check_backlog`, `load_case_set`,
`read_execution`, `load_payload` and the cost ledger. So do the six
dashboard, validator and output-eval sites. The monthly cap check and
`budget_guard.record` raise on a ledger that is not UTF-8, where they now
fail closed. The two reworded strings go back to `cannot read`. The revert
also deletes this run's documents and ADR-0075; restore them with a
follow-up commit if the run should stay legible. No data is lost, because
nothing here writes data. A product repo that re-stamped in between keeps
the newer payload until it re-stamps again.

### 8. Plugin version: PASS, no bump called for

`git diff --name-only 661ffc7..HEAD -- skills .claude-plugin` lists nothing.
The plugin stays at 0.2.0 and its cache cannot go stale from this change.
The repository has no tags, and none follows.

## What to read before merging

- `docs/adr/0075-the-guarded-file-read-joins-the-cli-seam.md`. It is
  **provisional**. Decision 1 names three kinds. The dropped kind is under
  *Alternatives that lost*. The end of decision 5 is where N2's sentence
  is missing.
- `review.md` from "Re-review (2026-10-04, the fix loop)" to the end, for
  N1, N2 and N3 and for "What still awaits the operator".
- `verification.md`'s "Not verified (re-verification, 2026-10-04)".
- `cli.read_file` itself, 54 lines in `cli.py`.
- The `CLAUDE.md` seam-modules line, which now says `cli.py` owns "the
  guarded local-file read (`read_file`, ADR-0075)".
- `CONTEXT.md` gained no term, deliberately. `AGENTS.md` was not touched
  and still carries an older seam bullet that had already drifted.

## Release steps (prepared, NOT EXECUTED)

Run from the worktree root, in order. None of these was run.

1. **NOT EXECUTED. The operator confirms option (a).** The first review
   left one major open and gave three options:
   - (a) **Drop the `object` kind. The reviewer's recommendation, and what
     this branch now contains.** `read_file` takes `str`, `dict` or `list`
     and refuses anything else at the call.
   - (b) Keep `object` and make its docstring true; ADR-0075 decision 1
     notes that the kind has no caller yet.
   - (c) Leave it as it was. Not recommended.

   The operator was asked "Should I drop the uncalled kind?" and answered by
   invoking autorun again, with no arguments. The orchestrating session read
   that as "keep driving" and took (a) as the default. So (a) has been
   built, verified and reviewed, but not chosen in the operator's words.

   **If (a) is confirmed:** record the operator's words in
   `autorun-brief.md` and go to step 2.

   **If the operator wanted (b) or (c):** put the branch back to what the
   operator was shown. This is safe only while the branch is unpushed, which
   it is until step 3.
```
git branch refactor/one-guarded-file-read-option-a      # optional: keeps the fix loop reachable by name
git reset --hard 864f1aa
```
   The reset discards exactly these ten commits, and the commit that adds
   this file on top of them:
   `c1b3cd5` (the brief's resume), `4fe2983` (the design amendment and the
   ADR-0075 correction), `ad4c812` (Milestone D), `e6abfc1` (D1), `b121f2c`
   (D2), `cb5a75b` (D3), `5ecde58` (D4), `b94462b` (D5), `95830fa` (the
   re-verification) and `e46fa71` (the re-review). The fixes for Minors 1,
   2, 4, 5 and 6 go with them, and they do not come back by cherry-pick.
   Tried in the scratch clone on top of `864f1aa`: `b121f2c` (Minor 1),
   `cb5a75b` (Minor 5) and `5ecde58` (Minor 6) each stop on a conflict, all
   three in `breakdown.md`, the first two in `factory/manifest.json`, and
   the first in `cli.py` and its payload copy. Minor 2 shares its commit
   with the dropped kind (`e6abfc1`), and Minor 4 shares its commit with
   the ADR correction (`4fe2983`). So they are redone in a new fix loop.
   ADR-0075 is then corrected again,
   in place, before any merge: it is provisional and has never been on
   `origin/main`. The run routes back to Implement, then Verify and Review,
   and this file is prepared a third time.

2. **NOT EXECUTED. The operator decides N1, and N2 with it.** N1: a ledger
   line that is valid UTF-8 but that `json.loads` refuses with something
   other than `JSONDecodeError` still makes the monthly cap check and
   `budget_guard.record` raise where they promise to fail closed.
   Reproduced for this pass on exports of `e46fa71` and of `661ffc7`, on
   both Pythons: a line holding a 5,000-digit integer makes
   `cost_ledger.read` and `cost_ledger.load` raise `ValueError` at both
   revisions. So it is not a regression. The fence that left it out is the
   Architect's amendment, not the operator's words.

   **Path A, take the fix before the merge. The reviewer's
   recommendation.** One more work item, in one mirrored commit:
   - Two tests first, through `cost_report.guard` and
     `budget_guard.record`, each watched failing with the `ValueError`.
   - In `cost_ledger.parse` (line 223), `except json.JSONDecodeError as
     err:` becomes `except (ValueError, RecursionError) as err:`, and the
     suffix `is not valid JSON: {err}` stays.
   - `python3 factory_init.py update-manifest`, and the manifest is
     committed with the change.
   - N2's sentence at the end of ADR-0075 decision 5 then names
     `dashboard._corrections` alone, which has the same line; or it goes,
     if that reader is fixed in the same item.
   - Then a re-verify (the battery on both Pythons, and a note in
     `verification.md`), a review of the one commit, and a third
     preparation of this file: checks 1, 5, 6 and 7 are re-run, and the
     pull-request body below loses its "Known limit" section and takes the
     new test count.

   The reviewer tried this fix in a scratch copy of HEAD and reports the
   suite unchanged and green, the cap check pausing, and `record` refusing
   with a problem string. That was not repeated here.

   **Path B, merge without it.** N1 becomes the first follow-up: a seed for
   the retro, or a new maintenance run. Before the push, add N2's sentence
   at the end of ADR-0075 decision 5, in a commit that changes that file
   only (no code, no manifest step). The reviewer's wording: the readers
   that adopted with `str` and parse each line themselves,
   `cost_ledger.load` and `dashboard._corrections`, keep their
   `JSONDecodeError` arm, so a ledger line that raises `ValueError` or
   `RecursionError` still raises through the cap check. Re-run `gates.py`
   after that edit. If the sentence is not added, the gap stays recorded in
   `review.md` and in the pull-request body. The body below is written for
   this path.

3. **NOT EXECUTED. Push the branch, naming the remote and the branch.**
   The worktree was cut from `origin/main`, so the branch's configured
   upstream is `origin/main`. Never run a bare `git push` here.
```
git ls-remote origin refs/heads/main      # still 661ffc705e18...? if not, redo checks 5 and 6 first
git push -u origin refactor/one-guarded-file-read
```
   `-u` re-points the upstream at the new remote branch. The push starts the
   `validator` workflow as a push event, where detector B skips.

4. **NOT EXECUTED. Create the tracking issue.** Detector B is
   `gates.check_pr_traceability`. Read from the code at HEAD, it reports a
   problem for each of two halves, separately:
   - `B: PR body cites no work-order id`, unless the body holds a
     work-order id **or** matches `gates.NO_WO_DECLARATION`: the words
     `no work order` (any case, spaces or hyphens between them), then a
     colon, then at least one non-space character **on the same line**. A
     bare marker with no reason waives nothing. The accepted form is
     `No work order: <reason>`.
   - `B: PR body has no Closes #N link`, unless the body matches
     `knowledge_plane.CLOSES_TOKEN`: `close`, `closes`, `closed`, `fix`,
     `fixes`, `fixed`, `resolve`, `resolves` or `resolved` (any case), an
     optional colon, whitespace, then `#` and a number. **This half has no
     waiver.**

   The brief said no issue, but a body with the waiver and no closing link
   still fails. So the pull request needs an issue to close. **Issues #178
   and #181 are permanent state: never close them, and never put a closing
   keyword in front of their numbers.** Create a plain issue, with no
   label, so that no label-triggered workflow fires:
```
ISSUE=$(gh issue create \
  --title "refactor: one owner for the guarded local-file read (cli.read_file)" \
  --body "Tracking issue for the pull request that adds cli.read_file (ADR-0075). Closed by that pull request. Not a work order." \
  | grep -o '[0-9]*$')
echo "$ISSUE"
```

5. **NOT EXECUTED. Write the body and open the draft pull request.** The
   body goes to a file through a quoted heredoc, so the backticks in it do
   not execute. The issue number is substituted afterwards. Keep the body
   free of any work-order id: the workflow's label jobs skip a pull request
   that cites none, and go loud on one that names an id it does not
   implement.
```
cat > "$TMPDIR/pr-body.md" <<'EOF'
## Summary

The rule "read a local file and turn every way it can fail into a problem
string" had no owner. Each reader typed its own guard, and each guard
forgot a different failure, so a file that could not be read gave a
traceback where the problem-string contract promises a string.

This adds one function, `cli.read_file(path, shown, kind)`, to the cli seam
(ADR-0075, provisional). It takes three kinds, `str`, `dict` and `list`,
and refuses any other at the call. Eleven readers adopt it. Nine readers
stay hand-written, because adopting would change their wording: each got
its missing exception arm, and each says in code why it does not use
`read_file`.

Measured at the branch tip against `661ffc7`, over 18 readers and eight
kinds of bad file (144 cells): 123 are identical, 16 that raised now return
a problem string, 2 are reworded (below), 3 still raise
(`trigger_eval.print_metrics`, out of scope by decision) and none newly
raises. Six guarded sites outside that matrix no longer raise. The monthly
cap check now fails closed on a ledger that is not UTF-8.

No work order: a maintenance refactor of the cli seam that came out of a
deepening review, tracked by an issue rather than a work order.

Closes #ISSUE_NUMBER

## Two problem strings change wording

Both are for a config file whose bytes are not UTF-8 (ADR-0075 decision 3).
Nothing outside the tests matches on the old wording.

- `config: cannot read .github/factory.json: ...` becomes
  `config: .github/factory.json is not valid JSON: ...`
- `L: cannot read .github/labels.json: ...` becomes
  `L: .github/labels.json is not valid JSON: ...`

No other pinned problem string changes.

## For the operator, before the merge

1. **Confirm option (a).** The first review left one major open: a fourth
   kind, `object`, had no caller. It recommended (a), dropping the kind.
   Autorun was then re-invoked with no option named, and (a) was taken as
   the default. That is the orchestrating session's reading, not a recorded
   choice. This branch contains the result. If (b) or (c) was wanted, the
   branch goes back to `864f1aa` and ADR-0075 is corrected again first.
2. **Decide N1** (and N2 with it), from the re-review: take the one-line
   `cost_ledger.parse` fix before the merge, which the reviewer recommends,
   or merge without it and carry it as the first follow-up.

## Known limit

A ledger line that is valid UTF-8 but that the JSON parser refuses with
anything other than a syntax error still makes the monthly cap check and
`budget_guard.record` raise where they promise to fail closed. Two such
lines are known: an integer of more than 4,300 digits, and nesting past the
interpreter's limit. This is the same as before the change. `read_file`
itself reports both as `is not valid JSON`, but the ledger parses each line
itself and that parse was left alone. `review.md` (N1) measured that no
factory writer can produce such a line and that detector G goes red on a
change that adds one. ADR-0075 does not yet state the limit (N2).

## Test evidence

Measured at `e46fa71`, on Python 3.14.6 and Python 3.12.13:

- `python3 -m unittest discover tests`: Ran 1877 tests, OK, on both
- `python3 lint.py`: lint: 0 problem(s) across 25 skills, on both
- `python3 gates.py`: gates: 0 problem(s), on both (detector B skips
  without a pull-request event)
- `python3 gates.py --selftest`: selftest: ok, on both
- `origin/main` was still `661ffc7`, the base, so a squash onto it has the
  same tree as the branch tip.
- Pairwise merge with each of the 11 open pull requests, battery on Python
  3.14: ten merge clean and #602 conflicts in `factory/manifest.json`
  only, green after `python3 factory_init.py update-manifest`. All eleven
  results are green.
- Rollback rehearsed: squash, then `git revert`, gives the tree of
  `origin/main` exactly. Battery green there: Ran 1793 tests, OK.

## Test plan

- [ ] Operator confirms option (a)
- [ ] Operator decides N1 (fix before the merge, or first follow-up)
- [ ] CI green on this pull request, including detector B on the
      pull-request event
- [ ] A reviewer who did not author the change re-runs the battery
      (ADR-0036 clause 2)
- [ ] Human code-owner squash merge: the change touches `docs/adr/**` and
      a run's `architecture.md` (ADR-0036 clause 3)
- [ ] CI green on `main` after the merge

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
test -n "$ISSUE" && sed -i '' "s/ISSUE_NUMBER/$ISSUE/" "$TMPDIR/pr-body.md"
grep -n '^Closes #' "$TMPDIR/pr-body.md"      # must show the issue's number, not the placeholder

gh pr create --draft --base main --head refactor/one-guarded-file-read \
  --title "refactor(cli): one owner for the guarded local-file read (read_file, ADR-0075)" \
  --body-file "$TMPDIR/pr-body.md"
```
   This body was run through detector B for this pass, on an export of
   `e46fa71`. With the placeholder still in it: `B: PR body has no Closes
   #N link`. With a number substituted: no problem, on both Pythons.
   Without the waiver line: `B: PR body cites no work-order id`. The
   validator's two label legs (`wo:needs-review`, `wo:merged`) return no
   problem for it and attempt no `gh` call. If steps 1 and 2 are settled by
   then, edit the body's "For the operator" section and test-plan boxes to
   say so before opening. If path A was taken, the "Known limit" section
   and the numbers are rewritten from the re-verification first.

   `gh pr edit` is unreliable in this repo: it exits 1 and writes nothing.
   Any later body edit goes through the REST API, and the `edited` event
   re-runs the check:
```
gh api -X PATCH repos/mattbutlerengineering/skills/pulls/<N> -F body=@"$TMPDIR/pr-body.md"
```

6. **NOT EXECUTED. Wait for green checks.** Opening the pull request starts
   the `validator` workflow as a pull-request event. Its `check` job is
   where detector B runs, on Linux and Python 3.12; the push-event run from
   step 3 does not exercise B. The `review` job posts the findings as a
   comment, and the label job is a silent no-op for a body that cites no
   work order.
```
gh pr checks <N> --watch
```
   Zero runs can mean a GitHub Actions outage, not a failure: look at
   githubstatus.com before touching any workflow file. If another pull
   request lands first and `factory/manifest.json` conflicts, regenerate it
   as in check 6, on the branch:
```
git fetch origin main
git merge origin/main
git checkout --ours factory/manifest.json
find . -path ./.git -prune -o \( -name '*.orig' -o -name '*.rej' \) -print      # delete whatever this prints, first
python3 factory_init.py update-manifest
git add factory/manifest.json
git commit --no-edit
python3 -m unittest discover tests && python3 lint.py && python3 gates.py && python3 gates.py --selftest
git push origin refactor/one-guarded-file-read
```
   That sequence is for a conflict in the manifest alone. Any other
   conflict is read and resolved by hand before the battery.

7. **NOT EXECUTED. Human gate-2 squash merge.** The pull request touches
   `docs/adr/**` and a run's `architecture.md`, so under ADR-0036 clause 3
   a human code owner merges it. The agent that authored the change never
   does. Mark it ready (`gh pr ready <N>`), have a reviewer who did not
   author the change re-run the battery and record the pass on the pull
   request (clause 2), then the human squash-merges
   (`gh pr merge <N> --squash`). No tag follows and no plugin version bump
   follows (check 8).

   GitHub does not enforce this gate here. A read of the branch protection
   and rulesets on `main` returned HTTP 403, "Upgrade to GitHub Pro or make
   this repository public to enable this feature", so no required check or
   required review can be assumed to stop a merge on a red check. The gate
   is the human's. The repository also does not delete a branch on merge.

## Post-release checks (for the operator, NOT EXECUTED)

- CI green on `main` after the squash merge: `gh run list --branch main
  --limit 3`. Treat zero runs as a possible GitHub Actions outage, not a
  failure.
- The tracking issue is closed by the merge, and #178 and #181 are still
  open.
- A stamped product repo picks up the changed payload at its next factory
  stamp or refresh. Seven mirrored tools changed (`cli.py`,
  `cost_ledger.py`, `factory_config.py`, `gates.py`, `label_sync.py`,
  `standards_index.py`, `validator.py`), so the payload manifest changed.
  In the product repo, after the stamp or refresh, confirm detector E
  reports `gates: 0 problem(s)`. Nothing reaches a product repo until it
  re-stamps.
- Spot check the behaviour change where it matters, from the root of
  `main`. This printed
  `([], ["ledger: cannot read docs/factory/costs.jsonl: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte"])`
  on an export of `e46fa71`, and a `UnicodeDecodeError` traceback on an
  export of `661ffc7`:
```
d=$(mktemp -d) && mkdir -p "$d/docs/factory" && printf '\xff\xfe' > "$d/docs/factory/costs.jsonl" \
  && python3 -c "import sys, cost_ledger; print(cost_ledger.read(sys.argv[1]))" "$d"
```
- Then Operate: the retro. The run is active until `retro.md` exists.

## Retro seeds for Operate

None of these was added to `docs/backlog.md`. The first four are the
re-review's list; N1 and N2 join it if they are not taken before the merge.

- Minor 3: `label_sync.load_labels`, and so detector J, raises on Python
  3.12 under an unsearchable `.github/`.
- N3: two `TestReadFile` tests pass only under the interpreter's default
  digit limit and a default-sized stack.
- The wider parse arm (`ValueError`, `RecursionError`) for the seven
  hand-written JSON readers still inside the fence.
- `AGENTS.md`'s seam bullet, which had drifted before this run.
- N1, if the operator merges without it: the one line in
  `cost_ledger.parse`, and the same line in `dashboard._corrections`.
- N2, if its sentence is not added to ADR-0075.
- From this stage: the brief answered "no issue", and detector B's closing
  link has no waiver. Two earlier runs met the same thing
  (`deepening-cli-seams`, `deepening-tool-seams`). A brief should allow the
  tracking issue up front.
- From this stage: a worktree cut from `origin/main` leaves the new branch
  tracking `origin/main`. Every push step has to name the remote and the
  branch.
- From this stage: `main` has no branch protection the API will show, so
  the merge gates are held by people and not by GitHub.

## Preparation history

- **First preparation.** Pre-flight ran at `8924ebb`, 24 commits on top of
  `661ffc7`, and the file was committed in `864f1aa`. Verdict: "prepared,
  not ready". All eight checks passed and nothing was critical, but
  `review.md` left one major open for the owner: `read_file`'s `object`
  kind had no caller, and its docstring and ADR-0075 still recommended it.
  Nothing was executed.
- **What happened since.** The orchestrating session asked whether to drop
  the uncalled kind. The operator re-invoked autorun without naming an
  option, and the session took option (a) as the default
  (`autorun-brief.md`, "Resume, 2026-10-04"). A fix loop of ten commits
  followed (`c1b3cd5` to `e46fa71`): the design amendment with ADR-0075
  corrected in place, Milestone D (three kinds and the kind check, the
  wider parse guard, eight comments, one test literal, the replay), a
  re-verification that ends PASS at `b94462b`, and a re-review that closes
  the major in code and Minors 1, 2, 4, 5 and 6, keeps Minor 3 deferred,
  and adds N1, N2 and N3.
- **What changed in this file.** HEAD went from `8924ebb` to `e46fa71` and
  the branch from 24 commits to 35. The suite went from the first
  version's 1874 tests to 1877. The verdict went from "prepared, not
  ready" to ready for the operator's steps. The first version's step 1,
  the owner's decision on the open major, became two steps: confirm option
  (a), and decide N1. The pull-request body was rewritten: its "Open
  major" section is gone, and it now carries what the operator still has
  to confirm or decide and the known limit. Every pre-flight check was run
  again, and every result quoted in the pre-flight section was produced in
  this pass. `origin/main` was at `661ffc7` both times, and the same eleven
  pull requests were open.
- **The frontmatter.** Two first-version entries carry the prefix "First
  preparation (864f1aa)". The one about the open major was made untrue by
  the fix loop. The one about the pairwise overlap is prefixed because
  this pass measured #600's overlap differently (through #595, which it
  stacks on), not because the fix loop changed it.
- **Reading the first version.**
  `git show 864f1aa:docs/fixes/one-guarded-file-read/release.md`

## Outcome

Prepared, not executed. All eight pre-flight checks pass at `e46fa71`, and
the release is ready for the operator's steps, the first of which is the
confirmation of option (a). Nothing has been released. The run stays active
until a retro exists.
