---
stage: ship
run: maintenance:one-guarded-file-read
date: 2026-10-05
assumptions:
  - "The autorun brief authorizes prepare-and-stop only (no push, no pull request, no merge, no tag, no version bump, no tracker write), so every release step below is marked NOT EXECUTED and none was run. gh was used for reads only."
  - "Production means main. The project has never tagged a release, so landing is: push the branch, open a pull request against main, green checks, a human squash merge. The pull request touches docs/adr/**, so it is a human gate-2 merge (ADR-0036 clause 3) and the author never merges."
  - "The brief says no issue, but detector B requires a Closes #N link on every pull request and has no waiver for it (only the work-order half has one). A tracking issue is therefore an operator-only step, drafted below and not created. Its number is a placeholder."
  - "First preparation (864f1aa): The pairwise test ran every open pull request (11), not only the ones whose files overlap this run, because each takes about 25 seconds. Overlap was CLAUDE.md for 608, 595 and 585, factory/manifest.json and tests/test_work_queue.py for 602, and none for the other six."
  - "origin/main was found at the run's base (661ffc7), so the merge onto current origin/main is the branch itself. The scratch clone was cloned from the worktree and given the GitHub remote as a second remote for read-only fetches; nothing was pushed from it."
  - "First preparation (864f1aa): The state of the open major is taken exactly as review.md leaves it: open, for the owner. This stage does not decide it, fix it or fold any minor in."
  - "Second preparation (261e486): Re-preparation 2026-10-04, option (a): the fix loop this release now contains (864f1aa..e46fa71) exists because review.md's recommended option (a) for the open major, dropping the object kind, was taken as the default after the operator re-invoked autorun without naming an option (autorun-brief.md, 'Resume, 2026-10-04'). That is the orchestrating session's reading, not the operator's words. So the operator's confirmation of (a) is release step 1, and no later step is to run before it."
  - "Second preparation (261e486): Re-preparation, decided without operator input: the body of this file is rewritten for the state at e46fa71 instead of being appended under the first version, because nothing in the first version was executed and the operator acts from the top of the file. The first version stays readable with git show 864f1aa:docs/fixes/one-guarded-file-read/release.md, and the Preparation history section records what changed. That is the orchestrating session's instruction for this stage, not the operator's."
  - "Second preparation (261e486): Re-preparation, decided without operator input: the verdict 'prepared and ready for the operator's steps' is this stage's, on the rule that all eight pre-flight checks pass and the re-review leaves no critical and no open major. Ready means the operator can start at step 1. It does not mean option (a) is confirmed or N1 is decided."
  - "Second preparation (261e486): Re-preparation, decided without operator input: this stage does not decide N1 or N2 and changes no code and no ADR text. Step 2 gives both paths and puts the reviewer's recommendation first. The drafted pull request body is true of the branch as it stands, which is the merge-without-the-fix path. Taking the fix means one more Implement, Verify and Review pass and a third preparation of this file."
  - "Second preparation (261e486): Re-preparation, decided without operator input: pre-flight ran at e46fa71. The battery ran in the worktree on Python 3.14.6 and 3.12.13. The squash result and the reverted tree ran on both in the scratch clone. The eleven pairwise results ran on 3.14.6 only, as the orchestrating session instructed. The commit that adds this file comes after e46fa71 and changes this one document; the battery was run once more on both Pythons with the file in place, and the pairwise and rollback rehearsals were not repeated for it."
  - "Re-preparation, decided without operator input: the pairwise test again ran all 11 open pull requests. Overlap was measured against each one's merge base with main: CLAUDE.md for 585, 595, 600 and 608, factory/manifest.json and tests/test_work_queue.py for 602, and none for the other six. 600 targets 595's branch and not main; its head was merged as it stands, so that pair carries 595's commits too. The manifest conflict with 602 was resolved by taking this branch's side and regenerating."
  - "Re-preparation, decided without operator input: the tracking issue is drafted as a plain issue with no label, so no workflow that triggers on a label fires. Its title and body, the pull request's title and the reason given in the waiver line are this stage's wording. Precedent: the tracking issues of deepening-cli-seams and deepening-tool-seams."
  - "Second preparation (261e486): Re-preparation, decided without operator input: the secret scan's pattern list is this stage's choice and is named in pre-flight 3. The matrix replay, the six-site probe and the ledger probe quoted in pre-flight 4 ran on a git archive export of e46fa71 with the session-local scratch tools (ogfr/matrix.py, diff_matrix.py, probe_six.py) and probes written for this pass under ogfr/ship-d/. They are not durable; the durable evidence is the repo's own tests."
  - "Second preparation (261e486): Re-preparation, decided without operator input: the retro seeds are listed here for Operate and none was added to docs/backlog.md. The last three in that list are this stage's own observations, not the reviewer's."
  - "Third preparation, the ledger fix: the second fix loop this release now contains (261e486..c4bbe0b) exists because the operator re-invoked autorun without words after the report asked 'Should I fix the cap-check gap before you push?' and recommended yes (autorun-brief.md, 'Second resume, 2026-10-04 (UTC): the ledger parse guard'). Taking the fix is the orchestrating session's reading, not the operator's words. So the operator's confirmation of that fix is release step 2, beside the confirmation of option (a) in step 1, and no later step is to run before both."
  - "Third preparation, option (a): the first fix loop (864f1aa..e46fa71) still rests on the orchestrating session's reading of a bare re-invocation of autorun (autorun-brief.md, 'Resume, 2026-10-04'). The operator has neither confirmed option (a) in words nor undone it. Its confirmation stays release step 1. The release now contains two fix loops, and git reset --hard 864f1aa discards both."
  - "Third preparation, decided without operator input: the body of this file is rewritten for the state at c4bbe0b instead of being appended under the second version, because nothing in either earlier version was executed and the operator acts from the top of the file. The second version stays readable with git show 261e486:docs/fixes/one-guarded-file-read/release.md and the first with git show 864f1aa:docs/fixes/one-guarded-file-read/release.md, and the Preparation history section records what changed. That is the orchestrating session's instruction for this stage, not the operator's."
  - "Third preparation, decided without operator input: the verdict 'prepared and ready for the operator's steps' is this stage's, on the rule that all eight pre-flight checks pass and the three review passes leave no critical and no open major. Ready means the operator can start at step 1. It does not mean option (a) or the ledger fix is confirmed, or that N4 is decided."
  - "Third preparation, decided without operator input: this stage does not decide N4 and changes no code and no ADR text. Step 3 gives both paths and puts the reviewer's recommendation first: merge, and take the planner's refusal as the first follow-up. The drafted pull request body is written for that path and is true of the branch as it stands. Its wording is this stage's. Taking the fix before the merge means one more Implement, Verify and Review pass and a fourth preparation of this file."
  - "Third preparation, decided without operator input: pre-flight ran at c4bbe0b. The open pull requests were listed afresh and are the same eleven, at the same heads, as the second preparation recorded. The battery ran in the worktree on Python 3.14.6 and 3.12.13. The squash result and the reverted tree ran on both in a new scratch clone (ogfr/ship-e/clone). The eleven pairwise results ran on 3.14.6 only, as the orchestrating session instructed. The commit that adds this file comes after c4bbe0b and changes this one document; the battery was run once more on both Pythons with the file in place, and the pairwise and rollback rehearsals were not repeated for it."
  - "Third preparation, decided without operator input: the secret scan's pattern list is the second preparation's, unchanged, and is named in pre-flight 3. Every probe quoted in this file ran on git archive exports of c4bbe0b, 261e486 and 661ffc7, with the session-local scratch tools (ogfr/matrix.py, diff_matrix.py, probe_six.py) and with probes under ogfr/ship-e/. Four of those probes are the reviewer's scripts (callers_probe.py, siblings.py, nan.py, nan_wq.py), copied unedited and run again on this pass's own exports: the method is the reviewer's and the results quoted are this pass's. None of it is durable; the durable evidence is the repo's own tests."
  - "Third preparation, decided without operator input: beyond the eight checks asked for, this pass ran again N4, the four ledgers the second re-review lists under 'Outside this run', the deferred Minor 3, the eight readers that still raise on the two documents, the five tests under N3 and the reviewer's one-line candidate for N4, because the drafted pull request body states each of them and the body has to be true of something measured. The candidate was applied in a scratch copy of an export only. Nothing was fixed, and no file in the worktree but this one changed."
  - "Third preparation, decided without operator input: step 1's statement that the minor fixes do not cherry-pick back onto 864f1aa was measured again in the scratch clone, and the second fix loop's two commits that carry N1 and N2 (ecf86f0, 19a5070) were tried the same way. All five stop on a conflict."
  - "Third preparation, decided without operator input: the frontmatter date is the UTC date on which this preparation ran, 2026-10-05, by the brief's rule that artifact dates are UTC. The second re-verification and the second re-review carry 2026-10-04 in their headings and were committed at 03:07 and 03:42 UTC on 2026-10-05. This file cites those headings as they are written."
  - "Third preparation, decided without operator input: the four outside-run ledgers are carried into the drafted pull request body as 'Found, not addressed here' and into the retro seeds. This stage opens no run for them, files no issue and adds nothing to docs/backlog.md. Whether they get a maintenance run of their own is the operator's to weigh."
  - "Third preparation, decided without operator input: the retro seeds are listed here for Operate and none was added to docs/backlog.md. The last four in that list are this stage's own observations, not the reviewer's."
---

# Release: one owner for the guarded local-file read

**Prepared, not executed.** Nothing was pushed, no pull request or issue was
opened, nothing merged, tagged or published, and no tracker was written. The
branch `refactor/one-guarded-file-read` is local only, HEAD `c4bbe0b`, 43
commits on top of `661ffc7`. The commit that adds this file is the 44th and
changes this document only.

**Verdict: prepared and ready for the operator's steps.** All eight
pre-flight checks pass at `c4bbe0b`, and the three review passes leave no
critical and no open major. The first two steps are confirmations, and
both are the operator's. Two parts of this branch rest on the orchestrating
session's reading of a bare re-invocation of autorun, not on the operator's
words: option (a), the dropped `object` kind (step 1), and the
ledger-parser fix (step 2). Step 3 is the operator's decision on N4.
Nothing is pushed before all three. The run stays active until a retro
exists.

This is the third preparation of this file. The second, at `e46fa71`, is
stale: a second fix loop of seven commits has landed since. Everything
below was measured again at `c4bbe0b`, and no number is carried over from
the earlier versions or from the reviewer's list. `## Preparation history`,
near the end, says what changed.

How pre-flight was run. On 2026-10-05 UTC, with Python 3.14.6 (`python3`)
and Python 3.12.13 (`python3.12`), on macOS, as uid 501, with
`PYTHONINTMAXSTRDIGITS` unset. "The battery" is four commands:
`-m unittest discover tests`, `lint.py`, `gates.py` and
`gates.py --selftest`. A scratch script, `battery.sh <tree> <python>
<prefix>`, runs the four in a tree, redirects each to its own file and
records each exit code. A second, `summ.sh <prefix>`, prints the exit codes
and greps the deciding lines out of those files. Nothing was piped to
`tail`. Both scripts are the second preparation's, copied unedited. All
merging and rehearsal happened in a new scratch clone of the worktree under
the session scratchpad (`ogfr/ship-e/clone`). The clone calls GitHub `gh`,
so `gh/main` there is what the worktree calls `origin/main`. Both of the
clone's push URLs were set to a dummy value before anything was fetched.
Older revisions were read from `git archive` exports under `ogfr/ship-e/`:
`head` is `c4bbe0b`, `before` is `261e486` and `base` is `661ffc7`. HEAD in
the worktree never moved, and this file is the only one changed in it.

What went wrong along the way. No pre-flight command was retried. Four
slips were this stage's own. None touched the repository and none was in
a pre-flight check. An unmatched glob aborted one listing. An `echo` of a
row of equals signs aborted the tail of a command that printed the
reviewer's scripts. A loop relied on word-splitting that zsh does not do,
so three comparisons of probe output were made again. And one probe
created two temporary directories outside the session scratch; the first
command to remove them was refused by the harness, because it named them
through a variable, and they were removed by their literal paths. The
non-zero exits among the checks were expected ones, each named where it
happened: the merge with #602, the five cherry-picks tried under step 1,
the three branch-protection reads under step 8, the test runs under
non-default limits in check 2, and the probes that are meant to show a
traceback at an older revision.

## Pre-flight

### 1. Verification is green: PASS

`verification.md`'s last pass, "Second re-verification (2026-10-04, the
ledger parse guard)", was made at `a69b3c9` and ends PASS. Its `Failures
(second re-verification, 2026-10-04)` section reads "none." The two commits
since then (`6d0bef8`, `c4bbe0b`) change `verification.md` and `review.md`
only.

The battery at HEAD `c4bbe0b`, in the worktree, with `git status --short`
empty before and after:

```
$ bash battery.sh <worktree> python3 out/head-314 ; bash summ.sh out/head-314          (Python 3.14.6)
unit_exit=0 lint_exit=0 gates_exit=0 selftest_exit=0
Ran 1880 tests in 22.880s
OK
lint: 0 problem(s) across 25 skills
gates: 0 problem(s)
selftest: ok
$ bash battery.sh <worktree> python3.12 out/head-312 ; bash summ.sh out/head-312       (Python 3.12.13)
unit_exit=0 lint_exit=0 gates_exit=0 selftest_exit=0
Ran 1880 tests in 21.116s
OK
lint: 0 problem(s) across 25 skills
gates: 0 problem(s)
selftest: ok
```

The battery was run once more in the worktree after this file was written,
because the commit that adds it is what gets pushed. On both Pythons all
four exit 0, with `Ran 1880 tests`, `OK`, `lint: 0 problem(s) across 25
skills`, `gates: 0 problem(s)` and `selftest: ok`. Its timings are left out
because quoting them would have changed the file after the run.

Detector B skips locally, because there is no pull-request event. Its rule
is stated from the code under step 5, and the drafted body was run through
it under step 6.

What verification could not show, and a release should know:

- No CI run exists yet. Every result here is from one machine, on macOS,
  and CI runs Linux on Python 3.12.
- The pause was not watched happening. The second re-verification shows the
  cap check writing `pause=true`, and reads the pause step's condition from
  `cost-report.yml`. The workflow itself has never run on this code. The
  step also needs the `FACTORY_PAUSE_TOKEN` secret, and neither that pass
  nor this one looked at whether it is set.

### 2. Review state: PASS

No unfixed critical and no open major. `review.md` holds three passes. The
last, "Second re-review (2026-10-04, the ledger parse guard)", ends "Ready
to ship (prepare-and-stop)": zero critical, zero major, one new minor,
nothing cites an enforced standard and nothing routes back to Implement.
Where every finding of the three passes stands:

| Finding | State at `c4bbe0b` | What is left |
|---|---|---|
| Major (first pass): the `object` kind has no caller | closed in code (`e6abfc1`; ADR-0075 in `4fe2983`) | the choice of option (a) itself awaits the operator: step 1 |
| Minor 1: two JSON documents make `read_file` raise | closed (`b121f2c`) | nothing |
| Minor 2: `kind` is not validated | closed (`e6abfc1`) | nothing |
| Minor 3: `label_sync.load_labels`, and so detector J, raises on Python 3.12 under an unsearchable `.github/` | still deferred, as the first pass decided | a seed for the retro; not a regression |
| Minor 4: ADR-0075's wording rule has two unnamed exceptions | closed (`4fe2983`) | nothing |
| Minor 5: one of nine hand-written readers says why | closed (`cb5a75b`) | nothing |
| Minor 6: a format expression where the file uses literals | closed (`5ecde58`) | nothing |
| N1 (second pass): a ledger line that the JSON parser refuses with anything but a syntax error makes the monthly cap check and `budget_guard.record` raise | closed in code (`ecf86f0`) | the choice to take the fix awaits the operator: step 2 |
| N2 (second pass): ADR-0075 does not carry the limit N1 describes | closed (`19a5070`: one paragraph closing decision 5) | nothing |
| N3 (second pass): new tests pass only under the interpreter's default limits | still deferred; it now covers five tests, not two | a seed for the retro |
| N4 (third pass, minor): on a ledger it can only partly read, `work_queue.py plan` still prints a batch priced on the rows it could read | deferred, and raised to the operator | step 3; the reviewer recommends the first follow-up, with the limit named in the pull-request body |

Four of these were run again here, on the exports, on both Pythons:

- Minor 2. `cli.read_file(path, shown, "object")` raises `ValueError:
  read_file kind must be str, dict or list, not 'object'`, with the file
  present and with it absent.
- Minor 3. `label_sync.load_labels` under a `.github/` directory with mode
  0 raises `PermissionError` on Python 3.12, at `c4bbe0b` and at `661ffc7`
  alike. On Python 3.14 it returns the `L: missing labels.json` problem at
  both. So it is not a regression, and it is still open.
- N3. Under the defaults the five tests pass on both Pythons. With
  `PYTHONINTMAXSTRDIGITS=10000` the three that use a 5,000-digit integer
  fail on both. In a thread with a 512 MB stack on Python 3.14 the two
  that use 1,000,000 nested arrays fail; the one in `TestReadFile` took 229
  seconds to do so. On Python 3.12 both pass under that stack.
- N4. Reproduced. The table is under step 3.

**Outside this run, and not findings against it.** The second re-review
reproduced four ledgers whose every line parses, which the line grammar
accepts, and which still defeat the cap check or the planner. They are
missing range checks on a row's values. None is a read or a parse and
none is touched by this run. Run again here on the `c4bbe0b` and `661ffc7`
exports: the two recordings are identical line for line, on both Pythons.

| Ledger, every line of which parses | `cost_ledger.read` | Detector G | The cap check (`cost_report.main(["report"])`) | `work_queue.month_to_date` |
|---|---|---|---|---|
| one good row (the control) | 1 row, no problem | no problem | exit 0; 470 bytes written, `pause=false` | `0.5`, no problem |
| cost is a 401-digit integer | 2 rows, no problem | no problem | raises `OverflowError`; 0 bytes, no `pause=` line | raises `OverflowError` |
| a gate row waited a 5,000-digit number of seconds | 2 rows, no problem | raises `ValueError` | raises `ValueError`; 0 bytes, no `pause=` line | raises `ValueError` |
| two rows whose tokens are 4,300 digits each | 3 rows, no problem | no problem | raises `ValueError`; 0 bytes, no `pause=` line | `1.5`, no problem |
| **cost is NaN** | 2 rows, no problem | no problem | exit 0; 506 bytes written, `pause=true` | `nan`, no problem |

The NaN row is the one a writer can produce, and it is the one to read
first. `budget_guard.main(["record", <id>, "r-1", "m", "100", "nan"])`
exits 0, prints `budget_guard: 0 problem(s)` and appends a row whose cost
is `NaN`. The cap check then pauses. The planner does not. On a ledger
holding a $299.75 row and that row, with the cap at $300 and three ready
`size:L` orders, `work_queue.main(["plan"])` exits 0:

```
wq: 3 work order(s) ready to run in parallel (wip_cap 3)
  <work-order id>  size:L  $40.00  issue #1  docs/features/demo/breakdown.md:1
  <work-order id>  size:L  $40.00  issue #2  docs/features/demo/breakdown.md:2
  <work-order id>  size:L  $40.00  issue #3  docs/features/demo/breakdown.md:3
  projected $120.00 on top of $nan spent this month
wq: 0 problem(s)
```

That output is the same at `661ffc7`. The ids are masked by the command
that printed it. Whether these four get a maintenance run of their own is
the operator's to weigh. They are listed in the pull-request body as
found and not addressed, and among the retro seeds.

### 3. No secrets in the diff: PASS

Scanned the 9,348 added lines of `git diff 661ffc7..HEAD`, the whole run
(43 files), for: AWS key ids and secret-key assignments, GitHub tokens
(`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`, `github_pat_`), `sk-` keys, Stripe
keys, Slack tokens, Google API keys, JWTs, PEM private-key headers, bearer
tokens, authorization headers with a value, URLs carrying credentials,
`token=` or `key=` query strings, and assignments of a literal to
`api_key`, `secret`, `password`, `token` and their variants. **No match for
any of them.**

Three catch-all patterns were run too, and they did match. None is a
secret:

- Hex runs of 40 characters or more, 15 matches. Seven are the SHA-256
  checksums in `factory/manifest.json` (public checksums of the payload
  files). Two are in `verification.md`, which quotes one of those
  checksums. Five are in the second version of this file: the commit id of
  `origin/main` and two git tree ids quoted twice each. One is a run of the
  digit 1 in `verification.md` (the test document with a 5,000-digit
  integer).
- Base64-shaped runs of 48 characters or more, 10 matches: the same lines,
  less the five in the second version of this file.
- Any URL, 1 match: the Claude Code attribution line in the second version
  of this file. No other URL is added.

No configuration file is added and no network call is introduced. This
file's own new text is not in that diff, because it is not committed yet.
The same scan over the whole of this file matches nothing but the
catch-alls: the attribution URL, the commit id of `origin/main`, two git
tree ids quoted twice each under checks 5 and 7, and the three `gh api`
paths quoted under step 8, which the base64-shaped pattern takes for a
long run.

### 4. Migrations and data changes: PASS, none apply

No schema, no stored data and no config file changes shape. The change
alters only what a reader does when a file cannot be read or a ledger line
cannot be parsed. Two tracked data files change, neither by hand:
`factory/manifest.json` has seven new checksums, for the payload copies of
the seven mirrored tools, and `docs/adr/README.md` gains one index row.

The behaviour matrix was replayed for this pass on an export of `c4bbe0b`,
against the recording taken at `661ffc7` (18 readers, eight kinds of bad
file):

```
cells 144 | identical 123 | fixed 16 | wording changed 2 | still raising 3 | newly raising 0
```

It ends that way on Python 3.14.6 and on Python 3.12.13, and the two
recordings are byte-identical to each other and to the one taken after the
first Implement pass. The three that still raise are all
`trigger_eval.print_metrics`, out of scope by decision. Each of the six
sites outside the matrix raised at `661ffc7` on the one kind of file its
guard did not name. None raises at `c4bbe0b`.

**Behaviour change 1: two problem strings changed wording, deliberately**,
both for a file whose bytes are not UTF-8 (ADR-0075 decision 3):

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

**Behaviour change 2: one problem string was removed, with its branch:**
`<shown> is null`. This run added it (`5e5f494`) for the `object` kind and
removed it with that kind (`e6abfc1`). No caller ever passed `object`, so no
caller could receive the string, and it was never on `origin/main`: against
`661ffc7` the net change is nothing. `git grep "is null" -- "*.py"` finds
nothing at HEAD.

**Behaviour change 3, new in the second fix loop: a ledger line that
`json.loads` refuses is now a located problem string.** `cost_ledger.parse`
catches `ValueError` and `RecursionError` where it caught `JSONDecodeError`
alone (`cost_ledger.py:227`). So the monthly cap check pauses, and
`budget_guard.record` refuses, where both raised. Measured on the three
exports with one probe, which calls `cost_ledger.read`,
`cost_report.guard`, `cost_report.main(["report"])` with a `GITHUB_OUTPUT`
file, and `budget_guard.record`:

| Ledger | `661ffc7` | `261e486` | `c4bbe0b` |
|---|---|---|---|
| a good row alone (the control) | CONTINUE; exit 0, `pause=false`; `record` appends | the same | the same |
| a good row, then `{not json` (the arm `661ffc7` already had) | PAUSE; exit 1, `pause=true`; `record` refuses | the same | the same |
| bytes that are not UTF-8 | all four raise `UnicodeDecodeError`; `GITHUB_OUTPUT` 0 bytes | PAUSE; exit 1, `pause=true`; `record` refuses | the same as `261e486` |
| a good row, then the same row with a 5,000-digit `tokens` | all four raise `ValueError`; `GITHUB_OUTPUT` 0 bytes | all four raise `ValueError`; `GITHUB_OUTPUT` 0 bytes | PAUSE; exit 1, `pause=true`; `record` refuses |
| a good row, then 1,000,000 nested arrays | all four raise `RecursionError`; `GITHUB_OUTPUT` 0 bytes | all four raise `RecursionError`; `GITHUB_OUTPUT` 0 bytes | PAUSE; exit 1, `pause=true`; `record` refuses |

Wherever `record` refuses or raises, the ledger's bytes are unchanged. At
`c4bbe0b` the two refused lines read as follows, with the reason `cr:
unreadable ledger — failing closed`:

```
ledger: docs/factory/costs.jsonl:2 is not valid JSON: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit
ledger: docs/factory/costs.jsonl:2 is not valid JSON: Stack overflow (used 16352 kB) while decoding a JSON array from a unicode string
```

The second line is Python 3.14's. Python 3.12 words it `maximum recursion
depth exceeded while decoding a JSON array from a unicode string`. Nothing
else differs between the two Pythons at any of the three revisions. The
five tests that pin these paths were run by name on both Pythons and pass
(`Ran 5 tests`, `OK`): `test_a_ledger_that_is_not_utf8_fails_closed` and
`test_a_ledger_line_the_parser_refuses_fails_closed`, each in
`tests/test_cost_report.py` and `tests/test_budget_guard.py`, and
`test_a_line_nested_past_the_recursion_limit_is_the_same_suffix` in
`tests/test_cost_ledger.py`.

This change has one side effect an operator should know, and it is N4: the
same two ledgers now reach the planner's old path for a partly readable
ledger, where it prints a batch. Step 3 has the table.

**One thing is new at the call, and it is not a file failure:** a `kind`
other than `str`, `dict` or `list` raises `ValueError` before the file is
touched. An AST sweep at HEAD finds 16 calls of `read_file` outside
`tests/` (11 in the root modules, 5 in the payload), each passing three
arguments and one of the three kinds.

**What did not change, measured.** `dashboard._corrections` and seven JSON
readers keep a `JSONDecodeError` arm: `label_sync.load_labels`, detector
K, `lint.check_output_evals`, `cli.read_execution`, `sweeps.load_payload`,
`cli.read_event` and `dashboard.repo_set`. On a document holding a
5,000-digit integer each raises `ValueError`, and on 1,000,000 nested
arrays each raises `RecursionError`, at `c4bbe0b` as at `661ffc7`, on both
Pythons. Three adopters run beside them as controls (`factory_config.load`,
`standards_index.foreign_entries`, detector F) return `is not valid JSON`
for both documents at `c4bbe0b` and raise at `661ffc7`.

### 5. Is the base still current: PASS

```
$ git fetch origin main                          (a read; exit 0)
$ git ls-remote origin refs/heads/main
661ffc705e18dbc77185ffd498a6cbf943c5d8e8	refs/heads/main
$ git rev-list --count HEAD..origin/main
0
$ git rev-list --count origin/main..HEAD
43
```

`origin/main` has not moved past `661ffc7`, so there is nothing to merge and
nothing to conflict with. The remote has no branch named
`refactor/one-guarded-file-read`, and no remote-tracking branch contains
HEAD. The squash of this branch onto `origin/main` was made in the scratch
clone, and its tree is the branch tip's tree:

```
$ git rev-parse HEAD^{tree} refactor/one-guarded-file-read^{tree}       (HEAD is the squash commit, ea31ce2)
1f220ac245c8808a52b14a37448756ba1f28efae
1f220ac245c8808a52b14a37448756ba1f28efae
```

The battery on that squash commit: on Python 3.14.6, all four exit 0,
`Ran 1880 tests in 20.883s`, `OK`, `lint: 0 problem(s) across 25 skills`,
`gates: 0 problem(s)`, `selftest: ok`. On Python 3.12.13 the same, with
`Ran 1880 tests in 21.257s`.

If `main` moves before the merge, this check and check 6 expire. Step 7
gives the commands for a manifest conflict.

### 6. Pairwise merge test against every open pull request: PASS, one expected manifest conflict

`gh pr list --state open` (a read) was run afresh and lists eleven: the
same eleven, at the same heads, as the second preparation recorded. Each
head was fetched into the scratch clone (`git fetch gh pull/<n>/head`,
every fetch exit 0, every head equal to the one `gh` reports), merged with
this branch there, one pair at a time from the branch tip `c4bbe0b`, and
the battery run on the result. The battery ran on Python 3.14.6 only,
which is enough to show a pair that merges clean and goes red. Each row is
unit, lint, gates and selftest, all four exit 0.

| PR (head) | Overlap with this run | Merge | Battery |
|---|---|---|---|
| #585 detector roster docs (`9a599ab`) | `CLAUDE.md` | clean | green, Ran 1880 tests OK |
| #589 backlog seeds (`d6dbd57`) | none | clean | green, Ran 1880 tests OK |
| #595 charter_replay control arm (`55debcb`) | `CLAUDE.md` | clean | green, Ran 1902 tests OK |
| #596 research note (`cff8597`) | none | clean | green, Ran 1880 tests OK |
| #597 done-with-concerns (`79e7c18`) | none | clean | green, Ran 1885 tests OK |
| #598 decompose placeholder scan (`2a07ca1`) | none | clean | green, Ran 1880 tests OK |
| #600 charter fixtures (`ba34095`), which targets #595's branch | `CLAUDE.md`, through #595 | clean | green, Ran 1914 tests OK |
| #602 fix(work_queue) blocked-by (`0d12bf7`) | `factory/manifest.json`, `tests/test_work_queue.py` | **conflict in `factory/manifest.json` only**; `tests/test_work_queue.py` merged clean | green after regenerating, Ran 1887 tests OK |
| #604 standards run docs (`54c7140`) | none | clean | green, Ran 1880 tests OK |
| #606 first-live-dispatch run docs (`bce2ccc`) | none | clean | green, Ran 1880 tests OK |
| #608 queue-groomer run docs (`9f52f56`) | `CLAUDE.md` | clean | green, Ran 1880 tests OK |

Every row also ends `lint: 0 problem(s) across 25 skills`,
`gates: 0 problem(s)` and `selftest: ok`, and every merged tree was clean
after its battery. Overlap is the set of files a pull request changes
since its merge base with `main` that this run changes too.

**#602's conflict and its resolution.** Both branches regenerate
`factory/manifest.json`. The conflict is that file alone. It was resolved in
the scratch clone in this order: take one side
(`git checkout --ours factory/manifest.json`), look for stray `*.orig` and
`*.rej` and delete them first (there were none), run
`python3 factory_init.py update-manifest` (`factory-init: 0 problem(s)`),
then `git add` and commit, then the battery. Whichever of the two lands
second has to do this.

None of the pairs is red. Three limits. The pairs were tested one at a
time, not in combination. The sweep expires when any pull request lands or
moves its head. And #602 also changes `work_queue.py` and its payload
copy, which this run does not touch: a fix for N4 on this branch (step 3,
the path not recommended) would edit those files, and the pair with #602
would have to be measured again.

### 7. Rollback plan, concrete and rehearsed: PASS

Rehearsed in the scratch clone: a branch from `gh/main` (`661ffc7`),
`git merge --squash refactor/one-guarded-file-read`, one commit (`ea31ce2`,
43 files, +9,348 / -295), then `git revert --no-edit HEAD` (`0b7f3f7`).

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
`Ran 1793 tests in 21.151s`, `OK`, `lint: 0 problem(s) across 25 skills`,
`gates: 0 problem(s)`, `selftest: ok`. On Python 3.12.13 the same, with
`Ran 1793 tests in 19.859s`. The count falls from 1880 to 1793: the 87 tests
this run adds.

The revert needs no separate manifest step when nothing else has landed,
because the manifest reverts in the same commit. The real squash will
differ from the rehearsed one in this file alone, which the next commit
rewrites.

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

**Cost of a revert, in behaviour.** The tracebacks come back.

- The 16 cells that now return a problem string raise again: files that
  are unreadable, not UTF-8 or the wrong top-level shape in detectors E, F
  and K, `foreign_entries`, `check_manifest`, `check_plugin_skills`,
  `check_pi_package`, `check_backlog`, `load_case_set`, `read_execution`,
  `load_payload` and the cost ledger. So do the six dashboard, validator
  and output-eval sites.
- The monthly cap check and `budget_guard.record` raise again on a ledger
  that is not UTF-8, and on a ledger line `json.loads` refuses, where they
  now fail closed. A cap check that raises writes no `pause=` line, and
  the pause step in `cost-report.yml` runs on `always() &&
  steps.report.outputs.pause == 'true'`. So by the workflow's text the
  pause step is skipped: a red job, and the factory not paused.
- The planner goes back to a traceback on those same three ledgers and
  prints no batch. So a revert also removes N4's new cases. What it leaves
  is what `661ffc7` did: a batch printed beside the problem, with exit 1,
  on a ledger line that is plainly not JSON.
- The two reworded strings go back to `cannot read`.
- The revert deletes this run's documents and ADR-0075. Restore them with
  a follow-up commit if the run should stay legible.

No data is lost, because nothing here writes data. A product repo that
re-stamped in between keeps the newer payload until it re-stamps again.

### 8. Plugin version: PASS, no bump called for

`git diff --name-only 661ffc7..HEAD -- skills .claude-plugin` lists nothing
(exit 0, no lines). The plugin stays at 0.2.0 and its cache cannot go stale
from this change. The repository has no tags, locally or on the remote,
and none follows.

## What to read before merging

- `docs/adr/0075-the-guarded-file-read-joins-the-cli-seam.md`. It is
  **provisional**. Decision 1 names three kinds. The dropped kind is under
  *Alternatives that lost*. The paragraph that closes decision 5 is new in
  the second fix loop: it gives `cost_ledger.parse` the wider parse guard
  and says `dashboard._corrections` keeps the narrow one. One reading to
  avoid, from the second re-review: "reach their fail-closed paths" is
  true of a ledger that cannot be read or parsed. It does not say the cap
  check can no longer raise.
- `review.md` from "Second re-review (2026-10-04, the ledger parse guard)"
  to the end: the disposition of N1, N2 and N3, the new minor N4, "Outside
  this run", and the Verdict's list of what awaits the operator. The
  section before it, "Re-review (2026-10-04, the fix loop)", is where N1 to
  N3 were raised.
- `verification.md`'s "Not verified (second re-verification, 2026-10-04)".
- `cli.read_file` itself, 54 lines in `cli.py`, and `cost_ledger.parse`,
  whose arm is at `cost_ledger.py:227`.
- `work_queue.main`, lines 243 to 285 of `work_queue.py`, for N4. The run
  did not edit it.
- The `CLAUDE.md` seam-modules line, which now says `cli.py` owns "the
  guarded local-file read (`read_file`, ADR-0075)".
- `CONTEXT.md` gained no term, deliberately. `AGENTS.md` was not touched
  and still carries an older seam bullet that had already drifted.
- `autorun-brief.md` has no outcome section for the second resume yet. The
  two earlier outcome sections were each added by the orchestrator, in the
  commit that added that preparation of this file.

## Release steps (prepared, NOT EXECUTED)

Run from the worktree root, in order. None of these was run.

1. **NOT EXECUTED. The operator confirms option (a).** The first review
   left one major open and gave three options:
   - (a) **Drop the `object` kind. The reviewer's recommendation, and what
     this branch contains.** `read_file` takes `str`, `dict` or `list`
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
   operator was shown after the first Ship. This is safe only while the
   branch is unpushed, which it is until step 4.
```
git branch refactor/one-guarded-file-read-option-a      # optional: keeps both fix loops reachable by name
git reset --hard 864f1aa
```
   From the current HEAD the reset discards exactly these 18 commits, and
   the commit that adds this file on top of them. **It discards the second
   fix loop too.**
   - The first fix loop, ten commits: `c1b3cd5` (the brief's resume),
     `4fe2983` (the design amendment and the ADR-0075 correction),
     `ad4c812` (Milestone D), `e6abfc1` (D1), `b121f2c` (D2), `cb5a75b`
     (D3), `5ecde58` (D4), `b94462b` (D5), `95830fa` (the re-verification)
     and `e46fa71` (the re-review).
   - The second preparation of this file: `261e486`.
   - The second fix loop, seven commits: `77d0c82` (the brief's second
     resume), `19a5070` (the second amendment and the ADR-0075 paragraph),
     `d7d92cd` (Milestone E), `ecf86f0` (E1, the code and its three tests),
     `a69b3c9` (E2), `6d0bef8` (the second re-verification) and `c4bbe0b`
     (the second re-review).

   The fixes for Minors 1, 2, 4, 5 and 6 and for N1 and N2 go with them,
   and they do not come back by cherry-pick. The second preparation
   measured that for three commits. It was measured again here, in the
   scratch clone on top of `864f1aa`, with the second fix loop's two
   commits added:
   - `b121f2c` (Minor 1) stops on a conflict in `cli.py`, its payload copy,
     `factory/manifest.json` and `breakdown.md`.
   - `cb5a75b` (Minor 5) stops on `factory/manifest.json` and
     `breakdown.md`.
   - `5ecde58` (Minor 6) stops on `breakdown.md`.
   - `ecf86f0` (N1) stops on `factory/manifest.json` and `breakdown.md`.
   - `19a5070` (N2) stops on `architecture.md`.
   - Not tried, because each carries option (a) itself: Minor 2 shares its
     commit with the dropped kind (`e6abfc1`), and Minor 4 shares its
     commit with the ADR-0075 correction (`4fe2983`).

   So they are redone in a new fix loop. ADR-0075 is then corrected again,
   in place, before any merge: it is provisional and has never been on
   `origin/main`. The run routes back to Implement, then Verify and Review,
   and this file is prepared a fourth time.

2. **NOT EXECUTED. The operator confirms the ledger-parser fix.** The
   first re-review found N1: a ledger line that `json.loads` refuses with
   anything but a syntax error made the monthly cap check and
   `budget_guard.record` raise where they promise to fail closed. The
   report after it asked "Should I fix the cap-check gap before you push?",
   recommended yes, and described the fix as "one line in the ledger parser
   plus two tests". The operator's reply was to invoke autorun again, with
   no arguments and no other words. The orchestrating session read that as
   "keep driving" and took the fix. So the fix has been built, verified and
   reviewed, but not chosen in the operator's words.

   Two things landed beyond what the question said, and they are part of
   what is being confirmed:
   - **Three tests, not two.** Two go through `cost_report.guard` and
     `budget_guard.record` with a 5,000-digit integer. The third goes
     through `cost_ledger.parse` with 1,000,000 nested arrays. By the
     second re-verification's mutation (2F, not repeated here) it is the
     one that fails if the arm is narrowed to `ValueError` alone.
     `architecture.md` and `breakdown.md` record the choice in their own
     assumptions.
   - **One docstring sentence beyond "one line".** `cost_ledger.parse`'s
     docstring now says why the arm is wide, so that it does not read as a
     slip to tidy back. The code change itself is the one line,
     `except (ValueError, RecursionError) as err:`. ADR-0075 gained one
     paragraph, which answers N2.

   **If the fix is confirmed:** record the operator's words in
   `autorun-brief.md` and go to step 3.

   **If the operator did not want it:** undo the second fix loop alone.
   Safe only while the branch is unpushed.
```
git branch refactor/one-guarded-file-read-ledger-fix    # optional: keeps the second fix loop reachable by name
git reset --hard 261e486
```
   From the current HEAD that discards exactly the seven commits of the
   second fix loop, listed under step 1 (`77d0c82`, `19a5070`, `d7d92cd`,
   `ecf86f0`, `a69b3c9`, `6d0bef8`, `c4bbe0b`), and the commit that adds
   this file. Option (a) and the first fix loop stay. Then:
   - This file is back at its second version, which was written for that
     state: its step 2, Path B, is the path the branch is then on. Its
     checks 5 and 6 are re-run before anything is pushed.
   - N1 is open again. The cap check and `record` raise on the two refused
     lines, as at `661ffc7`.
   - ADR-0075 loses the paragraph that closes decision 5, so it needs the
     sentence the first re-review asked for under N2 instead: the readers
     that adopted with `str` and parse each line themselves,
     `cost_ledger.load` and `dashboard._corrections`, keep their
     `JSONDecodeError` arm, so a ledger line that raises `ValueError` or
     `RecursionError` still raises through the cap check. That is a commit
     that changes the ADR only; re-run `gates.py` after it.
   - N4 does not go away. It narrows. At `261e486` the two refused lines
     are a traceback at the planner again, but a ledger that is not UTF-8
     still prints a batch priced on $0.00 spent: the first Implement pass
     moved that one (`733b5f2`). The table under step 3 has the column.

3. **NOT EXECUTED. The operator decides N4.** On a ledger it can only
   partly read, `work_queue.py plan` prices a batch on the rows it could
   read, prints it, then prints the ledger problem and exits 1. The path
   predates this run: a ledger line that is plainly not JSON gave that
   output at `661ffc7`. What this run changed is which ledgers reach it.
   No commit of the run edits `work_queue.py`.

   Reproduced for this pass on the three exports, on both Pythons, in a
   fixture repo with the cap at $300, `wip_cap` 3 and three ready `size:S`
   orders. The ledger holds a $0.50 row and a $299.75 row, both dated in
   the month of the probe's clock, and each other row of the table damages
   it in one way:

   | Ledger | `661ffc7` | `261e486` | `c4bbe0b` |
   |---|---|---|---|
   | both rows readable | exit 0; batch of 0; 3 deferred over the cap; `wq: 0 problem(s)` | the same | the same |
   | the $299.75 row's `tokens` is a 5,000-digit integer | raises `ValueError`, nothing printed | raises `ValueError`, nothing printed | exit 1; batch of 3 priced on $0.50 spent; `wq: 1 problem(s)` |
   | the $0.50 row, then 1,000,000 nested arrays | raises `RecursionError`, nothing printed | raises `RecursionError`, nothing printed | exit 1; batch of 3 priced on $0.50 spent; `wq: 1 problem(s)` |
   | the $0.50 row, then `{not json` | exit 1; batch of 3 priced on $0.50 spent; `wq: 1 problem(s)` | the same | the same |
   | bytes that are not UTF-8 | raises `UnicodeDecodeError`, nothing printed | exit 1; batch of 3 priced on $0.00 spent; `wq: 1 problem(s)` | the same as `261e486` |

   What `plan` prints at `c4bbe0b` for the second row, on Python 3.12. The
   ids are masked by the command that printed it, and the probe cuts each
   line at 150 characters:

   ```
   wq: 3 work order(s) ready to run in parallel (wip_cap 3)
     <work-order id>  size:S  $5.00  issue #1  docs/features/demo/breakdown.md:1
     <work-order id>  size:S  $5.00  issue #2  docs/features/demo/breakdown.md:2
     <work-order id>  size:S  $5.00  issue #3  docs/features/demo/breakdown.md:3
     projected $15.00 on top of $0.50 spent this month
   ledger: docs/factory/costs.jsonl:2 is not valid JSON: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.se
   wq: 1 problem(s)
   ```

   `plan --json` exits 1 with the same three orders in `batch` and the
   problem in `problems`. With both rows readable the three orders are
   deferred, because $300.25 is already over the cap. So on these ledgers
   the traceback was the safer output for this one caller: it printed no
   batch. The reviewer ranks it minor because the command still fails and
   says so, because a plainly malformed line already did this, and because
   the exposure is one batch, at most `wip_cap` orders at their band
   budgets. The cap check and `budget_guard.record` refuse on the same
   problem list.

   **Path A, merge and take it as the first follow-up. The reviewer's
   recommendation, and what the drafted pull-request body is written
   for.** The limit is named in the body under "Known limits". The fix
   becomes its own small maintenance run, through `capture`, after the
   merge. Nothing changes on this branch, and step 4 is next.

   **Path B, fix it before the merge.** One more loop on this branch:
   Implement, Verify, Review, and a fourth preparation of this file.
   - The change belongs in `work_queue.main`: when `month_to_date` returns
     problems, plan nothing, as it already does for an untrusted listing.
     That also changes what a plainly malformed ledger line does, which is
     `661ffc7` behaviour, and it is outside "one line in the ledger
     parser". So it wants the operator's words.
   - Tests come first, at `TestMain` in `tests/test_work_queue.py`. No test
     pins today's behaviour, so the new ones must be watched failing.
   - `work_queue.py` is mirrored: payload copy and `factory/manifest.json`
     in the same commit.
   - Whether the refusal gets a `wq:` line of its own is the owner's
     wording to choose. Today the problem line carries the `ledger:` label
     and only the summary line says `wq:`.
   - The pair with #602 is measured again (check 6).

   The reviewer tried a candidate in scratch: one line,
   `trusted = ready is not None and not ledger_problems`. It was tried
   again here, in a scratch copy of a `c4bbe0b` export, with the payload
   copy and the manifest regenerated (`factory-init: 0 problem(s)`). On the
   four damaged ledgers `plan` then prints the ledger problem and `wq: 1
   problem(s)`, exits 1 and renders no batch, on both legs. The readable
   ledger is unchanged. The unedited suite stays `Ran 1880 tests`, `OK` on
   both Pythons, with `lint: 0 problem(s) across 25 skills`, `gates: 0
   problem(s)` and `selftest: ok`. A candidate is not a fix: it has no
   tests, and nothing in the worktree was changed.

   **Narrowing the arm back is not a path.** It re-opens N1: a missed
   pause, in exchange for a traceback at the planner.

4. **NOT EXECUTED. Push the branch, naming the remote and the branch.**
   The worktree was cut from `origin/main`, so the branch's configured
   upstream is `origin/main`. Never run a bare `git push` here.
```
git ls-remote origin refs/heads/main      # still 661ffc705e18...? if not, redo checks 5 and 6 first
git push -u origin refactor/one-guarded-file-read
```
   `-u` re-points the upstream at the new remote branch. The push starts the
   `validator` workflow as a push event, where detector B skips.

5. **NOT EXECUTED. Create the tracking issue.** Detector B is
   `gates.check_pr_traceability` (`gates.py:357`). Read again from the code
   at HEAD, it reports a problem for each of two halves, separately, and
   it needs both to pass:
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
   label, so that no label-triggered workflow fires (the only workflow
   that listens to issues is the assembler, on `labeled`):
```
ISSUE=$(gh issue create \
  --title "refactor: one owner for the guarded local-file read (cli.read_file)" \
  --body "Tracking issue for the pull request that adds cli.read_file (ADR-0075). Closed by that pull request. Not a work order." \
  | grep -o '[0-9]*$')
echo "$ISSUE"
```

6. **NOT EXECUTED. Write the body and open the draft pull request.** The
   body goes to a file through a quoted heredoc, so the backticks in it do
   not execute. The issue number is substituted afterwards. Keep the body
   free of any work-order id: the workflow's label jobs skip a pull request
   that cites none, and go loud on one that names an id it does not
   implement. The body below is complete and is true of the branch at
   `c4bbe0b`, for Path A of step 3.
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
`read_file`. The cost ledger's line parser, `cost_ledger.parse`, takes the
same wide parse guard as `read_file`, so a ledger line the JSON parser
refuses is reported with its line number instead of raising.

Measured at the branch tip against `661ffc7`, over 18 readers and eight
kinds of bad file (144 cells): 123 are identical, 16 that raised now return
a problem string, 2 are reworded (below), 3 still raise
(`trigger_eval.print_metrics`, out of scope by decision) and none newly
raises. Six guarded sites outside that matrix no longer raise.

The monthly cap check and `budget_guard.record` now fail closed on a ledger
that is not UTF-8, and on a ledger line the JSON parser refuses (an integer
of more than 4,300 digits, or nesting past the interpreter's limit). The
cap check writes `pause=true` and exits 1, and `record` refuses and appends
nothing. Both raised on all three at `661ffc7`.

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

Two parts of this branch were built on the orchestrating session's reading
of a bare re-invocation of autorun, not on a recorded choice. Both need a
yes in words. A third point is a decision.

1. **Confirm option (a).** The first review left one major open: a fourth
   kind, `object`, had no caller. It recommended (a), dropping the kind.
   Autorun was then re-invoked with no option named, and (a) was taken as
   the default. If (b) or (c) was wanted, the branch goes back to `864f1aa`
   and ADR-0075 is corrected again first.
2. **Confirm the ledger-parser fix.** The re-review found that a ledger
   line the JSON parser refuses still made the monthly cap check raise. The
   report asked whether to fix that before the push and recommended yes.
   Autorun was re-invoked with no words, and the fix was taken. It was
   described as one line and two tests. What landed is that line, one
   docstring sentence and three tests. If it was not wanted, the branch
   goes back to `261e486`.
3. **Decide N4**, the first known limit below: fix the planner before the
   merge, or merge and take it as the first follow-up. The reviewer
   recommends the follow-up, and this description is written for that
   path.

## Known limits

- **The planner prints a batch on a ledger it could only partly read
  (N4).** On such a ledger `work_queue.py plan` prices the batch on the
  rows it could read, prints it, then prints the ledger problem and exits 1
  with `wq: 1 problem(s)`. A plainly malformed ledger line already did this
  at `661ffc7`. This change moves three more ledgers onto that path, where
  each used to raise and print no batch: a ledger that is not UTF-8, which
  is priced on $0.00 spent, and the two kinds of line the JSON parser
  refuses. The exposure is one batch: at most `wip_cap` orders at their
  band budgets. The cap check and `budget_guard.record` refuse on the same
  problem. The fix belongs in `work_queue.main` and is not in this pull
  request.
- **Eight readers still raise on two unusual documents.**
  `dashboard._corrections` and seven JSON readers keep a narrower parse
  guard: `label_sync.load_labels`, detector K, `lint.check_output_evals`,
  `cli.read_execution`, `sweeps.load_payload`, `cli.read_event` and
  `dashboard.repo_set`. On a document holding an integer of more than 4,300
  digits, or nested past the interpreter's limit, each raises as it did at
  `661ffc7`. ADR-0075 decision 5 records this.
- **Five tests rely on interpreter defaults.** Three tests that use a
  5,000-digit integer fail when `PYTHONINTMAXSTRDIGITS` is raised to 10000.
  Two tests that use 1,000,000 nested arrays fail on Python 3.14 in a
  thread with a 512 MB stack. Under the defaults all five pass on both
  Pythons.
- **One reader still raises on Python 3.12.** `label_sync.load_labels`, and
  so detector J, raises `PermissionError` under a `.github/` directory that
  cannot be searched, as at `661ffc7`. The first review deferred it.

## Found, not addressed here

Probing the cap check turned up four ledgers whose every line parses and
which still defeat the cap check or the planner. Each behaves the same at
`661ffc7` and at the branch tip. None is a file read or a parse, and this
change touches none of them: they are missing range checks on a row's
values, and they want a maintenance run of their own.

- **A cost of NaN.** The `record` command of `budget_guard.py`, given `nan`
  as the cost, exits 0 and appends a row whose cost is `NaN`. The cap check
  then pauses. The planner does not: with a $299.75 row and that row in the
  ledger and the cap at $300, it reports `wq: 0 problem(s)`, exits 0 and
  plans three `size:L` orders, `projected $120.00 on top of $nan spent this
  month`.
- A cost that is a 401-digit integer: the cap check raises `OverflowError`
  and writes no `pause=` line. Detector G reports nothing.
- A gate row whose wait is a 5,000-digit number of seconds: the cap check
  and detector G raise `ValueError`.
- Two rows whose token counts are 4,300 digits each: the cap check raises
  `ValueError`. Detector G reports nothing.

## Test evidence

Measured at `c4bbe0b`, on Python 3.14.6 and Python 3.12.13, on macOS:

- `python3 -m unittest discover tests`: Ran 1880 tests, OK, on both. That
  is 87 more than the 1793 at `661ffc7`.
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
  `origin/main` exactly. Battery green there on both Pythons: Ran 1793
  tests, OK.
- No CI run existed when this was written. Every result above is from one
  machine.

## Test plan

- [ ] Operator confirms option (a)
- [ ] Operator confirms the ledger-parser fix
- [ ] Operator decides N4 (fix before the merge, or first follow-up)
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
   This body was run through detector B for this pass, as extracted from
   this file, on an export of `c4bbe0b`, on both Pythons:
   - with the placeholder still in it: `B: PR body has no Closes #N link`;
   - with a number substituted: no problem;
   - with the waiver paragraph removed: `B: PR body cites no work-order id`.

   With a number substituted, the body holds exactly one closing link, and
   the only other number in it is #602. The validator's two label legs
   (`wo:needs-review`, `wo:merged`) return no problem for it and attempt no
   `gh` call. The `sed -i ''` form is the macOS one.

   By the order of these steps, 1 to 3 are settled before the pull request
   is opened. So edit the body's "For the operator" section and the first
   three test-plan boxes to record what the operator said, and the pull
   request then carries the answers and not the questions. If Path B of
   step 3 was taken, the first "Known limits" entry and the numbers are
   rewritten from the new verification first.

   `gh pr edit` is unreliable in this repo: it exits 1 and writes nothing.
   Any later body edit goes through the REST API, and the `edited` event
   re-runs the check:
```
gh api -X PATCH repos/mattbutlerengineering/skills/pulls/<N> -F body=@"$TMPDIR/pr-body.md"
```

7. **NOT EXECUTED. Wait for green checks.** Opening the pull request starts
   the `validator` workflow as a pull-request event. Its `check` job is
   where detector B runs, on Linux and Python 3.12; the push-event run from
   step 4 does not exercise B. The `review` job posts the findings as a
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

8. **NOT EXECUTED. Human gate-2 squash merge.** The pull request touches
   `docs/adr/**` and a run's `architecture.md`, so under ADR-0036 clause 3
   a human code owner merges it. The agent that authored the change never
   does. Mark it ready (`gh pr ready <N>`), have a reviewer who did not
   author the change re-run the battery and record the pass on the pull
   request (clause 2), then the human squash-merges
   (`gh pr merge <N> --squash`). No tag follows and no plugin version bump
   follows (check 8).

   GitHub does not enforce this gate here. The second preparation found
   that, and the reads were made again for this pass:
```
$ gh api repos/mattbutlerengineering/skills/branches/main/protection        (exit 1)
gh: Upgrade to GitHub Pro or make this repository public to enable this feature. (HTTP 403)
$ gh api repos/mattbutlerengineering/skills/rulesets                        (exit 1, the same 403)
$ gh api repos/mattbutlerengineering/skills/rules/branches/main             (exit 1, the same 403)
$ gh api repos/mattbutlerengineering/skills/branches/main --jq '{protected, protection_enabled: .protection.enabled}'
{"protected":false,"protection_enabled":false}
$ gh api repos/mattbutlerengineering/skills --jq '{private, visibility, delete_branch_on_merge, allow_squash_merge, allow_merge_commit, allow_rebase_merge, default_branch}'
{"allow_merge_commit":true,"allow_rebase_merge":true,"allow_squash_merge":true,"default_branch":"main","delete_branch_on_merge":false,"private":true,"visibility":"private"}
```
   So the branch read says `main` is not protected, and the protection and
   ruleset reads are refused for a private repository on this plan. No
   required check and no required review can be assumed to stop a merge on
   a red check, and `CODEOWNERS` alone does not block one. The gate is the
   human's. All three merge methods are allowed, so the squash is a choice
   made at the merge. The repository does not delete a branch on merge.

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
- Spot check the two behaviour changes that matter most, from the root of
  `main`. Both were run for this pass on the exports. The first printed
  `([], ["ledger: cannot read docs/factory/costs.jsonl: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte"])`
  at `c4bbe0b`, and a `UnicodeDecodeError` traceback at `661ffc7`:
```
d=$(mktemp -d) && mkdir -p "$d/docs/factory" && printf '\xff\xfe' > "$d/docs/factory/costs.jsonl" \
  && python3 -c "import sys, cost_ledger; print(cost_ledger.read(sys.argv[1]))" "$d"
```
  The second printed
  `([], ['ledger: docs/factory/costs.jsonl:1 is not valid JSON: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit'])`
  at `c4bbe0b`, on both Pythons, and a `ValueError` traceback at `661ffc7`:
```
d=$(mktemp -d) && mkdir -p "$d/docs/factory" && python3 -c "print('{\"tokens\": ' + '1' * 5000 + '}')" > "$d/docs/factory/costs.jsonl" \
  && python3 -c "import sys, cost_ledger; print(cost_ledger.read(sys.argv[1]))" "$d"
```
- Watch the first scheduled `cost-report` run after the merge (Mondays,
  07:17 UTC). It is the first time this cap check runs in its workflow.
  Run locally on an export of `c4bbe0b`, `python3 cost_report.py report`
  on this repo's own 92-row ledger exits 0 and writes `pause=false`, on
  both Pythons. The pause path itself has still not been watched in a
  workflow run.
- Then Operate: the retro. The run is active until `retro.md` exists.

## Retro seeds for Operate

None of these was added to `docs/backlog.md`. The first seven are from the
second re-review. The last four are this stage's own.

- Minor 3: `label_sync.load_labels`, and so detector J, raises on Python
  3.12 under an unsearchable `.github/`.
- N3, now five tests: two in `TestReadFile` and three for the ledger pass
  only under the interpreter's default digit limit and a default-sized
  stack.
- The wider parse arm (`ValueError`, `RecursionError`) for
  `dashboard._corrections` and for the seven hand-written JSON readers
  still inside the fence.
- `AGENTS.md`'s seam bullet, which had drifted before this run.
- The shape cells of `trigger_eval.print_metrics`, the three that still
  raise.
- N4, if the operator takes Path A of step 3: the planner's refusal on a
  ledger it could not fully read, in `work_queue.main`, as its own small
  maintenance run.
- The four ledgers under "Outside this run", the NaN cost first: missing
  range checks on a ledger row's values. A maintenance run of their own,
  through `capture`, if the operator wants one.
- From this stage: the brief answered "no issue", and detector B's closing
  link has no waiver. Two earlier runs met the same thing
  (`deepening-cli-seams`, `deepening-tool-seams`). A brief should allow the
  tracking issue up front.
- From this stage: a worktree cut from `origin/main` leaves the new branch
  tracking `origin/main`. Every push step has to name the remote and the
  branch.
- From this stage: the API reports `main` as unprotected, so the merge
  gates are held by people and not by GitHub.
- From this stage: twice in this run a yes-or-no question was answered by
  a bare re-invocation of autorun, and each time the session read it as
  yes and built a fix loop on that reading. Both now wait for the
  operator's words as release steps. A report that ends on a question
  could say what a re-invocation without words will be taken to mean.

## Preparation history

- **First preparation.** Pre-flight ran at `8924ebb`, 24 commits on top of
  `661ffc7`, and the file was committed in `864f1aa`. Verdict: "prepared,
  not ready". All eight checks passed and nothing was critical, but
  `review.md` left one major open for the owner: `read_file`'s `object`
  kind had no caller, and its docstring and ADR-0075 still recommended it.
  Nothing was executed.
- **Between the first and the second.** The orchestrating session asked
  whether to drop the uncalled kind. The operator re-invoked autorun
  without naming an option, and the session took option (a) as the default
  (`autorun-brief.md`, "Resume, 2026-10-04"). A fix loop of ten commits
  followed (`c1b3cd5` to `e46fa71`): the design amendment with ADR-0075
  corrected in place, Milestone D (three kinds and the kind check, the
  wider parse guard, eight comments, one test literal, the replay), a
  re-verification that ends PASS at `b94462b`, and a re-review that closes
  the major in code and Minors 1, 2, 4, 5 and 6, keeps Minor 3 deferred,
  and adds N1, N2 and N3.
- **Second preparation.** Pre-flight ran at `e46fa71`, 35 commits on top
  of `661ffc7`, and the file was committed in `261e486`. Verdict: "prepared
  and ready for the operator's steps". All eight checks passed, and the
  re-review left no critical, no major and three minors. Its first step
  was the operator's confirmation of option (a). Its second was the
  operator's decision on N1, with two paths: take the one-line fix in
  `cost_ledger.parse` before the merge, which the reviewer recommended, or
  merge without it. Its pull-request body was written for the path without
  the fix and carried N1 as a known limit. Nothing was executed.
- **Between the second and the third.** The report asked "Should I fix the
  cap-check gap before you push?" and recommended yes. The operator
  re-invoked autorun without words, and the session took the fix
  (`autorun-brief.md`, "Second resume, 2026-10-04 (UTC): the ledger parse
  guard"). A second fix loop of seven commits followed (`77d0c82` to
  `c4bbe0b`): the Architect's second amendment with one paragraph added to
  ADR-0075, Milestone E, the change itself (`ecf86f0`: one arm, one
  docstring sentence, three tests, the payload copy and the manifest), the
  replay notes, a second re-verification that ends PASS at `a69b3c9`, and a
  second re-review that closes N1 in code and N2, keeps N3 deferred, adds
  the minor N4, and records four ledgers outside the run.
- **What changed in this file since the second version.**
  - HEAD went from `e46fa71` to `c4bbe0b` and the branch from 35 commits to
    43. The suite went from the second version's 1877 tests to 1880, the
    tests the run adds from 84 to 87, and the added lines scanned from
    6,687 to 9,348.
  - The verdict keeps its words. The steps behind it changed. The second
    version's step 2, the decision on N1, became step 2 here, the
    confirmation of a fix that is now on the branch. Step 3, the decision
    on N4, is new. The old steps 3 to 7 are steps 4 to 8.
  - Step 1's undo now discards 18 commits, not ten, and step 2 names the
    undo for the second fix loop alone.
  - The pull-request body was rewritten. Its "Known limit" section about
    the cap check is gone, because the cap check no longer raises on those
    lines. In its place are four known limits (N4 first) and "Found, not
    addressed here". The operator's section has three points where it had
    two.
  - Check 2 lists all three review passes and the outside-run ledgers.
    Check 4 carries the new behaviour change. Check 7's cost of a revert
    covers the refused line and the planner.
  - Every pre-flight check was run again, and every result quoted in this
    file was produced in this pass. `origin/main` was at `661ffc7` all
    three times. The same eleven pull requests were open, at the same
    heads as the second preparation recorded.
  - The second re-review lists sixteen statements of the second version
    that the fix loop made untrue. Each was checked against the repo and
    is corrected here.
- **The frontmatter.** `date` moved to 2026-10-05, the UTC date of this
  pass. Two first-version entries keep the prefix "First preparation
  (864f1aa)". Seven second-version entries now carry "Second preparation
  (261e486)": each describes that version's body, its probes or its
  steps, and this pass made it untrue of the file. Two second-version
  entries stay verbatim because they are still true of this pass: the one
  about the pairwise overlap, which was measured again with the same
  result, and the one about the tracking issue. Twelve entries are new,
  each beginning "Third preparation".
- **Reading the earlier versions.**
  `git show 864f1aa:docs/fixes/one-guarded-file-read/release.md` and
  `git show 261e486:docs/fixes/one-guarded-file-read/release.md`

## Outcome

Prepared, not executed. All eight pre-flight checks pass at `c4bbe0b`, and
the release is ready for the operator's steps. The first two are
confirmations in the operator's own words, of option (a) and of the
ledger-parser fix, and the third is the decision on N4. Nothing has been
released. The run stays active until a retro exists.
