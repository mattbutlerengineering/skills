---
stage: verify
run: maintenance:deepening-tool-seams
date: 2026-08-18
assumptions:
  - "no prd.md — maintenance run, so the criteria list is autorun-brief.md's seven success criteria, the fifteen Accept lines in breakdown.md, and defect.md's condition; there are no PRD success criteria to trace"
  - "'observable output is unchanged' is verified against the repo's exact-string test contract (main's suites re-run against this branch's production code) and a full enumeration of detector J's problem strings at both revisions — not by driving any tool against real GitHub. No test in this repo touches a live gh, and this stage added none"
  - "the brief's phrase 'the seven LIST_WINDOW constants collapse to a parameter' is read as architecture.md's recorded decision (per-tool windows stay per-tool and travel as window=), not as 'seven constants become one'. Seven declarations remain and that is the design's answer; the criterion's own test is 'one window rule', which is what was verified"
---

# Verification: one owner each, four times

## Summary

**23 of 23 criteria PASS** — the brief's seven success criteria, the
fifteen Accept lines in `breakdown.md`, and the condition `defect.md`
opened. Three pass under a stated narrowing, and two observations are
recorded for Review rather than as failures. Two standing invariants the
run had to preserve rather than meet — eval honesty and the payload
mirror — were checked separately and are intact.

The centerpiece regression — a gate row that costs money, the case that
makes the month-to-date divergence observable — is verified
behaviorally, by driving `work_queue.py plan` at both revisions against
the same fixture ledger and reading what it printed, not only by a green
test.

Whole-repo battery at verification time, on `deepening-tool-seams`
@ `a4f6310`, clean tree:

```
Ran 1271 tests in 14.552s
OK

lint: 0 problem(s) across 23 skills

gates: 0 problem(s)
selftest: ok
```

**Grep scoping, stated once.** `.claude/worktrees/` holds eighteen
untracked agent checkouts of this repo at unrelated revisions, and a
recursive grep from the repo root walks into all of them (677 stale
`.py` files; 22 of them still declare a `LIST_WINDOW`). Every grep below
is therefore `git grep`, which reads tracked files only. Where a
criterion quotes a plain `grep`, the tracked-only equivalent is what was
run and what is quoted.

---

## Part 1 — the brief's seven success criteria

### S1. Each of the four facts has exactly one owner, demonstrable by grep

- Check: four greps over tracked files, one per fact.
- Evidence:
  ```
  $ git grep -nw -e gh_json -e full_window -- '*.py'
  (none)
  $ git grep -ln -- '--limit' -- '*.py'
  cli.py
  factory/templates/tools/factory/cli.py
  tests/test_cli.py
  tests/test_label_sync.py
  tests/test_sweeps.py
  $ git grep -n "def gh_read" -- '*.py'
  cli.py:325:def gh_read(args, operation, label=None, run=gh_runner, expect=list,
  factory/templates/tools/factory/cli.py:325:def gh_read(...)

  $ git grep -n "from gate_digest import" -- '*.py'
  (none)
  $ git grep -n "^GATES\|def label_events\|def completed_stays\|def gate_passages\|def gate_rejections\|def waiting_since\|def gate_labels" -- '*.py'
  human_gates.py:38,46,60,65,82,118,128,139  (and its payload twin only)
  $ git grep -n "def mirror_map" -- '*.py'
  knowledge_plane.py:183   (and its payload twin only)

  $ git grep -n "def product_form" -- '*.py'
  factory_init.py:59

  $ git grep -n "def dispatched" -- '*.py'
  cost_ledger.py:97        (and its payload twin only)
  $ git grep -n "cost_ledger.dispatched(" -- '*.py' | grep -v ^factory/
  cost_report.py:71:    for entry in cost_ledger.dispatched(entries, month):
  work_queue.py:198:                in cost_ledger.dispatched(entries, month))
  ```
  The three `--limit` hits under `tests/` are argv assertions — the tests
  that pin what the seam sends gh. The only construction site in
  production is `cli.py:353`:
  ```
  argv = list(args) if window is None else [*args, "--limit", str(window)]
  ```
- Result: **PASS**, under one stated narrowing. `LIST_WINDOW` is still
  declared seven times (assembler, dashboard, gate_digest, label_sync,
  rejection_mining, sweeps, work_queue), unchanged in count. That is
  `architecture.md`'s explicit decision — "per-tool window values stay
  per-tool … over one shared constant" — and the fact given one owner is
  the *rule* (how a windowed read is composed and how truncation is
  reported), not the numbers. A reader taking the brief's "the seven
  `LIST_WINDOW` constants collapse to a parameter" literally would call
  this unmet; the design answered that reading before implement, and the
  criterion's own test — one window rule — holds.

### S2. Every changed tool's observable output is unchanged, or the change is stated

- Check: three independent methods, because no single one is sufficient.
  1. Run **main's entire test tree against this branch's production
     code**, and account for every non-pass. This is the exact-string
     contract read as a regression net: the suites were written before
     the change and assert the literal problem strings.
  2. Enumerate **every problem detector J can emit**, at both
     revisions, by pruning each declared label in turn from an otherwise
     correct taxonomy.
  3. An AST-level string-literal diff of every tracked `.py` between
     `main` and `HEAD` as a coarse sweep.
- Evidence — method 1:
  ```
  ### HEAD production code + main's ENTIRE tests/ tree ###
  ERROR: test_a_failed_gh_still_raises_for_the_callers_catch (test_cli.TestGhJson…)
  ERROR: test_a_full_window_is_a_problem_suffix (test_cli.TestFullWindow…)
  ERROR: test_a_partial_window_is_fine (test_cli.TestFullWindow…)
  ERROR: test_a_wrong_top_level_shape_is_a_suffix_not_a_crash (test_cli.TestGhJson…)
  ERROR: test_covers_ran_succeeded_and_said_nonsense (test_cli.TestGhJson…)
  ERROR: test_parsed_json_of_the_expected_shape_passes_through (test_cli.TestGhJson…)
  FAIL: test_a_pruned_label_is_reported_against_every_site_that_names_it (test_gates.TestLabelWiring…)
  FAIL: test_happy_path_writes_manifest_and_syncs (test_factory_init.TestUpdateManifest…)
  FAIL: test_resolves_to_this_git_checkout (test_knowledge_plane.TestRepoRoot…)
  FAIL: test_the_extraction_actually_finds_the_shipped_labels (test_gates.TestLabelWiring…)
  Ran 1234 tests in 15.540s
  FAILED (failures=4, errors=6)

  ### CONTROL: main production + main tests, same .git-less export ###
  FAIL: test_resolves_to_this_git_checkout (test_knowledge_plane.TestRepoRoot…)
  Ran 1234 tests in 14.796s
  FAILED (failures=1)
  ```
  Ten non-passes, every one accounted for: six are `TestGhJson` /
  `TestFullWindow` calling functions A6 deleted; two are the sanctioned
  detector J rename; one is main's `EXPECTED_RELS` not yet naming
  `human_gates.py` (B3); and `TestRepoRoot` fails identically in the
  control, because `git archive` produces a tree with no `.git` — an
  artifact of the export method, not of the change. Narrowed to the eight
  per-caller suites the design named as the net:
  ```
  ### HEAD production code + main's eight per-caller suites ###
  Ran 371 tests in 0.226s
  OK
  ### the two suites whose subject moved (main's versions) ###
  Ran 48 tests in 0.026s
  OK
  ```
- Evidence — method 2 (detector J, every pruned label, both revisions;
  identical label set of eleven at each):
  ```
  ########## MAIN ##########                ########## HEAD ##########
  J: assembler.py names budget-exhausted…   J: assembler.py names budget-exhausted…
  J: assembler.py names type:chore…         J: assembler.py names type:chore…
  J: assembler.py names type:defect…        J: assembler.py names type:defect…
  J: assembler.py names type:feature…       J: assembler.py names type:feature…
  J: assembler.py names type:support…       J: assembler.py names type:support…
  J: gate_digest.py names wo:blueprint-…    J: human_gates.py names wo:blueprint-…
  J: gate_digest.py names wo:draft…         J: human_gates.py names wo:draft…
  J: Makefile:2 names wo:merged…            J: Makefile:2 names wo:merged…
  J: gate_digest.py names wo:merged…        J: human_gates.py names wo:merged…
  J: gate_digest.py names wo:needs-review…  J: human_gates.py names wo:needs-review…
  J: gate_digest.py names wo:prd-approved…  J: human_gates.py names wo:prd-approved…
  J: assembler.py names wo:ready-for-agent… J: assembler.py names wo:ready-for-agent…
  ```
  Twelve problems each, in the same order, with the same trailing
  sentence. Five declaring-site names moved from `gate_digest.py` to
  `human_gates.py` and nothing else differs.
- **Two deliberate output changes, both stated here:**
  1. **Detector J's declaring site.** Priced in `architecture.md`'s
     *Decisions & alternatives* and in ADR-0056, enumerated above. It
     fires only against a broken taxonomy, and the new name is the true
     one.
  2. **`work_queue`'s month-to-date figure, on a ledger carrying a
     nonzero-cost gate row.** This is item 4's entire purpose, so it is
     a designed behavior change rather than a leak from an interface
     move — see D1/D2 below for the driven evidence. Over the live
     ledger nothing changes: 38 rows, 19 of them gate rows, every row
     `$0.00`, so both definitions answer `$0.00` before and after.
- Limits of the method, stated: this proves byte-identity for every
  string the repo's suites pin and for detector J's complete output. It
  does not prove it for a code path no test covers, and nothing here was
  driven against real GitHub. See *Not verified*.
- Result: **PASS**, with both changes stated.

### S3. The full battery is green

- Check: the three commands from `CLAUDE.md`, run at `a4f6310` on a
  clean tree.
- Evidence:
  ```
  $ python3 -m unittest discover tests
  Ran 1271 tests in 14.552s
  OK

  $ python3 lint.py
  lint: 0 problem(s) across 23 skills

  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: **PASS**. 1,271 tests, up from main's 1,234.

### S4. `work_queue.py`'s duplicate window literal is gone

- Check: the grep A6's Accept line names.
- Evidence:
  ```
  $ git grep -n '"100"' -- work_queue.py
  (none)
  ```
  What replaced it, at `work_queue.py:46`, is one declaration whose
  comment states where the fact now lives:
  ```
  # How far back the ready listing can see. cli.gh_read owns the window —
  # the limit it sends gh and the truncation it reports are the same
  # number — so it can only be typed once, and the duplicate literal this
  # constant used to disagree with has nowhere left to live.
  LIST_WINDOW = 100
  ```
- Result: **PASS**. This was one of the two live divergences the run was
  named for.

### S5. A `toolsmith-mine` lockstep class exists

- Check: run the three new methods.
- Evidence:
  ```
  test_both_makefiles_expose_the_toolsmith_mine_target … ok
  test_the_payload_toolsmith_workflow_is_the_mirror_of_this_repo_s … ok
  test_the_toolsmith_mine_workflow_names_no_command_of_its_own … ok
  ```
  They live in `TestLockstep` (not a class of their own), shaped like the
  gate-digest trio, with `TOOLSMITH_MINE_TARGET = ["python3
  rejection_mining.py mine"]` at `tests/test_gates.py:1666`.
- Result: **PASS**.

### S6. A ledger test covers a nonzero-cost gate row

- Check: run `tests/test_cost_ledger.py` and read the fixture.
- Evidence — the fixture is hand-assembled, because
  `cost_ledger.gate_entry` cannot produce such a row:
  ```
  gate = entry("WO-0001", "gate-merge-2026-08-03T05:17:00Z", "none",
               500, 3.25, "gate_wait:merge:7260s", "2026-08-03")
  self.assertEqual(cost_ledger.line_problems(gate), [])
  self.assertEqual(cost_ledger.gate_wait(gate), ("merge", 7260))
  ```
  ```
  test_the_two_month_totals_agree_on_a_costly_gate_row … ok
  test_a_zero_cost_gate_row_is_excluded_too … ok
  test_gate_rows_are_never_spend … ok
  Ran 52 tests in 0.012s
  OK
  ```
  The row is checked well-formed and gate-shaped first, so nothing but
  the spend rule decides the two numbers.
- Result: **PASS**. This is the regression evidence the brief said the
  run owed.

### S7. The test-ordering rule was followed and is visible in the commit history

- Check: walk `git log main..HEAD` (16 commits) and, per deepening,
  confirm from `git show --stat` that the pin lands before the move and
  that superseded tests die in the same commit that moves the behavior.
- Evidence — the commit order, oldest first:
  ```
  4a287ff docs   80f5496 A1  aae421b A2  873fdc8 A3  a043079 A4
  1c104f2 A5     17592cc A6  9dbe201 B1  1bc344d B2  ddc091e B3
  6ec22a5 B4     05a611f B5  d1eb2f8 B6  9cb0015 C1  33ff563 D1
  a4f6310 D2
  ```
  Per deepening:
  ```
  A1 80f5496  cli.py +63 | tests/test_cli.py +137 | no deletions
  A6 17592cc  cli.py -34 (the halves die) | tests/test_cli.py 45 (TestGhJson,
              TestFullWindow die) — one commit
  A2–A5      aae421b, 873fdc8, a043079, 1c104f2 touch ZERO test files
  B1 9dbe201  tests/test_human_gates.py +226 — tests only, no production file
  B2 1bc344d  tests/test_knowledge_plane.py +47 — tests only
  B5 05a611f  gate_digest -98, rejection_mining -41 | test_gate_digest -88,
              test_rejection_mining -43 — one commit
  B6 d1eb2f8  knowledge_plane +20, gate_digest -18 | test_gate_digest -14,
              test_knowledge_plane re-pointed — one commit
  C1 9cb0015  tests/test_gates.py +27 -16 — the RED lockstep and the shadow
              deletion in one commit
  D1 33ff563  tests/test_cost_ledger.py +58 — tests only
  D2 a4f6310  cost_ledger +18, cost_report, work_queue | the same test flips
  ```
  Every pin precedes its move; no deletion of a superseded test is a
  cleanup item of its own. The commit messages carry the coverage map the
  rule asks for — A6 names each dead case and its replacement by method
  name; B5 lists `TestLabelEvents -> TestLabelEvents`,
  `TestGatePassages`' four to the same four, `TestWaitingSince`'s two,
  `TestGateRejections`' four, "all of it into `tests/test_human_gates.py`".
  I re-derived, rather than trusted, that the pins could not have passed
  earlier:
  ```
  ### HEAD's TestGhRead against main's cli.py ###
  Ran 13 tests … FAILED (errors=13)
  AttributeError: module 'cli' has no attribute 'gh_read'

  ### HEAD's tests/test_human_gates.py against main ###
  ModuleNotFoundError: No module named 'human_gates'

  ### HEAD's tests/test_gates.py against main's gates.py ###
  Ran 163 tests … FAILED (failures=2)
  ```
  and that the pins B1, B2 and D1 were genuinely green against unmodified
  sources at their own commits (below, under B1/B2/D1).
- Result: **PASS**.

---

## Part 2 — the fifteen Accept lines in `breakdown.md`

Verified individually; the clauses already covered above are not
re-quoted.

### A1 — `cli.gh_read` lands beside the halves it will replace

- Check: run `TestGhRead`; confirm `gh_json`/`full_window` and their
  suites survived this commit; confirm the manifest moved with `cli.py`.
- Evidence: 13 cases, all named in the Accept line — five failure modes,
  `label=None`, the trailing `--limit` on the exact argv, `truncated`
  only on a full window, `full_note`:
  ```
  test_a_clean_read_is_the_value_and_no_problems … ok
  test_a_dict_read_names_its_own_expected_shape … ok
  test_a_failed_gh_is_a_problem_not_the_callers_catch … ok
  test_a_full_window_is_truncated_with_the_shared_sentence … ok
  test_a_partial_window_is_not_truncated … ok
  test_a_wrong_top_level_shape_is_a_prefixed_problem … ok
  test_an_unwindowed_read_is_never_truncated … ok
  test_an_unwindowed_read_sends_no_limit … ok
  test_full_note_replaces_the_shared_sentence … ok
  test_no_label_leaves_the_problems_unprefixed … ok
  test_ran_and_said_nonsense_is_a_prefixed_problem … ok
  test_the_callers_args_are_not_mutated … ok
  test_the_window_reaches_gh_as_a_trailing_limit … ok
  Ran 13 tests … OK
  ```
  `80f5496`'s stat shows `cli.py`, its payload twin and
  `factory/manifest.json` moving together, no caller touched.
- Result: **PASS**. Narrowing: "each case written and watched to fail
  before the seam was written" is attested by the commit message ("13
  errors, all `module 'cli' has no attribute 'gh_read'`") and
  independently re-derived above by running the suite against main's
  `cli.py` — 13 errors, same message. The *watching* itself is not
  re-demonstrable after the fact; the impossibility of passing is.

### A2 — validator and assembler

- Evidence:
  ```
  validator.py:322:    read = gh_read(["issue", "view", str(number), "--json", "labels"],
  assembler.py:256:    read = gh_read(list(PR_ARGS), "gh pr list", label="asm", run=run,
  ```
  assembler's attributed copy of the drift warning
  (`(rejection_mining's discipline)`) is gone. `aae421b` touches no test
  file at all, and carries `factory/manifest.json` with both twins.
- Result: **PASS**.

### A3 — label_sync and sweeps, including the one caller that changes shape

- Evidence:
  ```
  $ git grep -n "except CLI_FAILURES\|except cli.CLI_FAILURES" -- '*.py' | grep -v ^factory/
  cli.py:356:    except CLI_FAILURES as err:
  dashboard.py:123:    except CLI_FAILURES:

  $ sed -n '99,113p' label_sync.py
  def live_labels(run=gh_runner):
      """(live label set, problem-suffixes) through gh. … A missing,
      unauthenticated or rate-limited gh is a suffix like any other,
      never a raise; the catch is cli.gh_read's. …"""
      read = gh_read(list(LIST_ARGS), "gh label list", run=run,
                     window=LIST_WINDOW)
      return read.value, list(read.problems)

  $ git show --stat --format='' 873fdc8
   docs/fixes/deepening-tool-seams/breakdown.md  |  2 +-
   factory/manifest.json                         |  2 +-
   factory/templates/tools/factory/label_sync.py | 33 ++++++--------
   label_sync.py                                 | 33 ++++++--------
   sweeps.py                                     | 63 ++++++++++-----------------
   5 files changed, 53 insertions(+), 80 deletions(-)
  ```
  The three `try/except` blocks the callers owned are gone. The two
  `except CLI_FAILURES` left in tracked root modules are `cli.py:356`
  (the seam's own) and `dashboard.py:123`, which catches a **git** call
  in `remote_slug` and is byte-identical to main. `873fdc8` touches no
  test file; `tests/test_label_sync.py` and `tests/test_sweeps.py` are
  byte-identical to main.
- Result: **PASS**.

### A4 — the dashboard's three reads

- Evidence: `a043079` in full —
  ```
  dashboard.py                                 | 71 +++++++-------------
  docs/fixes/deepening-tool-seams/breakdown.md |  2 +-
  2 files changed, 24 insertions(+), 49 deletions(-)
  ```
  Nothing under `factory/`, which is the Accept line's own test that
  `dashboard.py` mirrors nothing. `tests/test_dashboard.py` byte-identical
  to main.
- Result: **PASS**.

### A5 — the digest's and the miner's five reads

- Evidence:
  ```
  $ git grep -n "        read = gh_read\|    read = gh_read" -- gate_digest.py rejection_mining.py
  gate_digest.py:103:        read = gh_read(["api", path, "--paginate", "--slurp"],
  gate_digest.py:197:    read = gh_read(list(LIST_ARGS), "gh issue list", label="gd", run=run,
  rejection_mining.py:141:        read = gh_read(["api", path, "--paginate", "--slurp"],
  rejection_mining.py:156:    read = gh_read(list(PR_ARGS), "gh pr list", label="rm", run=run,
  rejection_mining.py:201:    read = gh_read(list(ISSUE_ARGS), "gh issue list", label="rm", run=run,

  $ git show --stat --format='' 1c104f2
   docs/fixes/deepening-tool-seams/breakdown.md    |  2 +-
   factory/manifest.json                           |  4 +-
   factory/templates/tools/factory/gate_digest.py  | 40 +++++-----
   .../templates/tools/factory/rejection_mining.py | 58 ++++++--------
   gate_digest.py                                  | 40 +++++-----
   rejection_mining.py                             | 58 ++++++--------
   6 files changed, 75 insertions(+), 127 deletions(-)
  ```
  Five reads, both payload twins and the manifest in one commit, and no
  test file. Both suites byte-identical to main at this commit.
- Result: **PASS**.

### A6 — work_queue's read, and the halves die

- Evidence — the milestone's three closing greps, run over tracked files:
  ```
  $ git grep -ln -- '--limit' -- '*.py' | grep -v tests/ | grep -v factory/
  cli.py
  $ git grep -nw -e gh_json -e full_window -- '*.py'
  (none)
  $ git grep -n '"100"' -- work_queue.py
  (none)
  $ git grep -n "read = gh_read" -- work_queue.py
  work_queue.py:180:    read = gh_read(list(LIST_ARGS), "gh issue list", label="wq",
  ```
  `17592cc` deletes 34 lines from `cli.py` and its twin, and edits
  `tests/test_cli.py` in the same commit. Its message states the coverage
  map case by case — each dead case named beside the `TestGhRead` method
  that replaced it.
- Result: **PASS**.

### B1 — pin the gate walk at the intended interface, against today's code

- Check: export the tree at `9dbe201` and run the pin there, against
  unmodified `gate_digest.py` and `rejection_mining.py`.
- Evidence:
  ```
  ########## B1 pin (9dbe201) against UNMODIFIED sources ##########
  Ran 19 tests in 0.000s
  OK
  ```
  The suite includes the partition property neither tool's suite had.
- Result: **PASS**.

### B2 — pin `mirror_map` at the knowledge plane, against today's code

- Evidence:
  ```
  ########## B2 pin (1bc344d), TestMirrorMap only ##########
  test_a_row_carrying_both_maps_its_issue_to_its_work_order … ok
  test_a_row_with_no_tracker_reference_is_in_no_queue … ok
  test_a_tree_with_no_breakdown_mirrors_nothing … ok
  test_an_issue_with_no_row_is_not_a_work_order … ok
  Ran 4 tests … OK
  ```
  The whole-file run at that commit shows one unrelated failure,
  `TestRepoRoot.test_resolves_to_this_git_checkout`, which is the
  `.git`-less export artifact the control run reproduces at main.
- Result: **PASS**.

### B3 — `human_gates.py` lands and ships

- Evidence, clause by clause:
  ```
  $ grep -nE '^(import|from) ' human_gates.py
  25:from collections import namedtuple
  26:from datetime import datetime
  raise sites: 0      wc -l: 149

  factory_init.py:146:    ("human_gates.py", "tools/factory/human_gates.py", identity),
  factory_init.py:122:# … human_gates.py is the gate …          (the MIRRORS comment sentence)

  _PRODUCT_TOOLS = ("gates.py", "validator.py", "assembler.py",
                    "budget_guard.py", "cost_report.py", "gate_digest.py",
                    "rejection_mining.py")            ← human_gates absent, as required

  tests/test_factory_init.py  +"templates/tools/factory/human_gates.py"

  docs/setup.md  -73 files land: the 36-file payload  →  +75 files land: the 37-file payload
                 -| `factory/` | 37 |                 →  +| `factory/` | 38 |
                 -| `tools/factory/` | 16 |           →  +| `tools/factory/` | 17 |

  docs/adr/0056-human-gates-module.md                 (5,962 bytes)
  docs/adr/README.md:79:| 0056 (linked) | The three human gates get a module of their own | provisional |
  ```
  ```
  $ python3 -m unittest tests.test_factory_init.TestAcceptanceStampRealRepo.test_stamped_repo_passes_its_own_gates
  test_stamped_repo_passes_its_own_gates … ok
  Ran 1 test … OK
  ```
- Result: **PASS**.

### B4 — detector J stops counting tuple fields

- Evidence: the slice is gone —
  ```
  -    "gate_digest": lambda mod: {name for gate in mod.GATES
  -                                for name in gate[1:3]},
  +    "human_gates": lambda mod: mod.gate_labels(),
  ```
  and the enumeration under S2 shows the resulting output at both
  revisions.
- Result: **PASS**, with one observation recorded rather than softened.
  The Accept line calls the two assertions in `tests/test_gates.py` "the
  only exact-string edits sanctioned anywhere in this run". A **third**
  string moved in the same commit: `gates.py:1270`, the expectation
  inside `gates.selftest()`. It is an expectation of the very string the
  sanctioned change renames, not a second change, and `6ec22a5`'s
  message discloses it in as many words ("Three sites move with it and no
  others"). Recorded because the Accept line's count is off by one, not
  because anything was concealed.

### B5 — the digest, the miner and the dashboard become thin callers

- Evidence: `gate_digest.py:42` now reads `from human_gates import
  (GATES, gate_passages, label_events, waited_seconds, …)`, and
  `gate_digest.py:149` calls `waited_seconds`. Everything the Accept line
  names as staying put is still there and still defined locally:
  ```
  gate_digest       _timelines 1   _post_digest 1   compose_digest 1   _capture_latency 1
  rejection_mining  _timelines 1   _post_queue 1    compose_queue 1
  dashboard         _timeline 1    _age_seconds 1
  ```
  The two suites' only non-deletion in the whole commit is a module
  docstring naming where the coverage went:
  ```
  +The gate vocabulary and the stay walk are human_gates.py's (ADR-0056),
  +so timeline parsing, passage detection and waiting_since are covered in
  +tests/test_human_gates.py — one frame further out …
  ```
  ```
  $ git diff main..HEAD -- tests/test_gate_digest.py tests/test_rejection_mining.py \
      | grep '^-' | grep -E '"(gd|rm|wq|L|sweeps|asm|V):'
  (none — no tool problem-string assertion was deleted)
  ```
- Result: **PASS**.

### B6 — `mirror_map` moves to the knowledge plane

- Evidence:
  ```
  $ git grep -n "from gate_digest import"   →  (none in any .py)
  knowledge_plane.py:183:def mirror_map(root):
  gate_digest.py:44:from knowledge_plane import mirror_map, repo_root
  rejection_mining.py:43:from knowledge_plane import CLOSES_TOKEN, mirror_map, repo_root
  dashboard.py:53:                             mirror_map, row_done, row_size, row_title,
  ```
  `TestMirrorMap` in `tests/test_gate_digest.py` dies in the same commit
  that moves the function.
- Result: **PASS**. Milestone B's demonstration holds: no module reaches
  into a leaf tool for shared vocabulary.

### C1 — the missing lockstep target, then the shadow

- Check: re-derive the RED without editing anything — recover the deleted
  shadow from `main` and apply both transforms to the one command the new
  assertion pins.
- Evidence:
  ```
  command under lockstep:       'python3 rejection_mining.py mine'
  test shadow (main) respells:  'python3 rejection_mining.py mine'
  factory_init respells:        'python3 tools/factory/rejection_mining.py mine'
  payload Makefile carries:     'python3 tools/factory/rejection_mining.py mine'

  shadow agrees with payload?     False
  production agrees with payload? True
  ```
  which is the failure `9cb0015`'s message records:
  ```
  AssertionError: Lists differ:
  ['python3 tools/factory/rejection_mining.py mine'] !=
  ['python3 rejection_mining.py mine']
  ```
  Corroborated from the other direction: running **this branch's**
  `tests/test_gates.py` against **main's** production code gives 163
  tests and exactly 2 failures — both detector J's — so the three
  toolsmith-mine methods pass against main's `factory_init`. The defect
  was the test-private copy alone, never the production transform. After
  the deletion:
  ```
  $ git grep -n "def product_form" -- '*.py'
  factory_init.py:59
  ```
  and the class docstring at `tests/test_gates.py:1635` ("the assertions
  lean on … `factory_init.product_form`") is now true.
- Result: **PASS**. The red-to-green is the evidence the shadow was a
  live defect.

### D1 — pin the divergence with a nonzero-cost gate row

- Check: export the tree at `33ff563` and read what the pin asserted
  against unmodified sources.
- Evidence:
  ```
  ########## D1 pin (33ff563) against unmodified sources ##########
  Ran 46 tests in 0.011s
  OK
  ```
  ```python
  def test_the_two_month_totals_disagree_on_a_costly_gate_row(self):
      …
      # $12.50 versus $15.75: the report keeps the $3.25 gate row
      # out of the month (ADR-0041), the queue's breaker input
      # counts it as spend.
      self.assertEqual(report_total, 12.50)
      self.assertEqual(queue_total, 15.75)
      self.assertNotEqual(report_total, queue_total)
  ```
  `33ff563` touches no production file.
- Result: **PASS**.

### D2 — `cost_ledger.dispatched`, and the two sums agree

- Check: drive both figures at both revisions against the same fixture
  ledger, then drive `work_queue.py plan` end to end in a self-contained
  fixture repo (the revision's tools copied in, gh faked, the real repo
  untouched).
- Evidence — the module-level figures:
  ```
  ########## MAIN ##########            ########## HEAD ##########
  ledger problems: []                   ledger problems: []
  cost_report month total  ->  $12.50   cost_report month total  ->  $12.50
  work_queue month_to_date ->  $15.75   work_queue month_to_date ->  $12.50
  ```
  and the same thing at the surface a human reads:
  ```
  ########## MAIN (before the fold) ##########
  $ python3 work_queue.py plan
  wq: 1 work order(s) ready to run in parallel (wip_cap 3)
    WO-0001  size:S  $5.00  issue #999  docs/features/demo/breakdown.md:3
    projected $5.00 on top of $15.75 spent this month
  wq: 0 problem(s)
  [exit 0]

  ########## HEAD (after the fold) ##########
  $ python3 work_queue.py plan
  wq: 1 work order(s) ready to run in parallel (wip_cap 3)
    WO-0001  size:S  $5.00  issue #999  docs/features/demo/breakdown.md:3
    projected $5.00 on top of $12.50 spent this month
  wq: 0 problem(s)
  [exit 0]
  ```
  The `$3.25` gate row no longer inflates the number the monthly breaker
  compares against the cap, and it now equals the weekly report's month
  total. The cap comparisons are untouched, each still answering its own
  question:
  ```
  cost_report.py:98:    if total_cost >= cap:
  work_queue.py:153:        elif cap is not None and spent_usd + projected + row["budget"] > cap:
  ```
  `tests/test_cost_report.py` and `tests/test_work_queue.py` are
  byte-identical to main and green, which is the Accept line's "nothing
  dies" clause: no existing test asserted the gate-row-inclusive sum,
  and that is why the divergence survived.
- Result: **PASS**.

---

## Part 3 — the condition `defect.md` opened

### Each of the four facts has exactly one owner, and the copies are gone

- Check: the greps under S1, plus the two live divergences the brief
  named as present in the tree at `fbfa3c3`.
- Evidence — the four owners, and the two live divergences gone:
  ```
  $ git grep -n "def gh_read\|^GATES\|def completed_stays\|def mirror_map\|def product_form\|def dispatched" -- '*.py' | grep -v ^factory/
  cli.py:325:def gh_read(args, operation, label=None, run=gh_runner, expect=list,
  human_gates.py:38:GATES = (
  human_gates.py:82:def completed_stays(events, gate):
  knowledge_plane.py:183:def mirror_map(root):
  factory_init.py:59:def product_form(command):
  cost_ledger.py:97:def dispatched(entries, month=None):

  $ git grep -n '"100"' -- work_queue.py
  (none)                       ← divergence 1: work_queue's duplicate literal
  $ git grep -c "def product_form" -- tests/test_gates.py
  (none)                       ← divergence 2: the 6-vs-7-tool shadow

  $ git grep -n "c >= start" -- '*.py'
  (none)                       ← the digest's spelling of the window test
  $ git grep -n "start <= ts" -- '*.py'
  human_gates.py:112:            start <= ts and (next_start is None or ts < next_start)
  factory/templates/tools/factory/human_gates.py:112: (its twin)
  ```
  One spelling of the window test survives, inside
  `human_gates.completed_stays`, and the invariant that lived as prose in
  `rejection_mining`'s docstring is now the return value both tools
  filter, pinned by `TestThePartition`. The two month-to-date definitions
  are one, at the `cost_ledger` seam, driven under D2.
- Result: **PASS**. The condition is resolved.

### Eval honesty

- Check: the ledger and the eval results are append-only and this run
  wrote to neither.
- Evidence:
  ```
  $ git log --oneline main..HEAD -- docs/factory/costs.jsonl
  (no commits)
  $ git diff --stat main..HEAD -- docs/factory/costs.jsonl
  (empty)
  $ git log --oneline main..HEAD -- evals/
  (no commits)
  $ git diff --stat main..HEAD -- 'skills/' docs/pipeline-protocol.md
  (empty)
  ```
  The costly gate row exists only inside test fixtures and inside the
  temporary trees this stage built; the live ledger still reads 38 rows,
  19 gate rows, every row `$0.00`.
- Result: **PASS**.

### The payload mirror

The brief calls this the run's most likely way to break CI, so it was
checked three ways, not one.

- Detector E, via the battery: `gates: 0 problem(s)`.
- Regeneration is a no-op on a clean tree — the committed manifest and
  payload already agree with the sources:
  ```
  $ git status --porcelain          (empty)
  $ python3 factory_init.py update-manifest
  factory-init: 0 problem(s)
  $ git status --porcelain          (empty)
  ```
- An independent payload-vs-root comparison, applying each `MIRRORS`
  entry's own transform to the root file and diffing against the
  committed twin:
  ```
  MIRRORS entries: 25
  ok   gates.py -> tools/factory/gates.py
  …
  ok   human_gates.py -> tools/factory/human_gates.py
  ok   Makefile -> Makefile

  payload<->root mismatches: 0
  ```
  All 25 entries coherent, including the new row. `test_stamped_repo_passes_
  its_own_gates` is green.

---

## Failures

**None.** No criterion failed.

Two things are recorded rather than softened, neither of which is a
failure of an acceptance criterion:

1. **B4's Accept line undercounts the sanctioned string edits by one.**
   It names two assertions in `tests/test_gates.py` as "the only
   exact-string edits sanctioned anywhere in this run"; a third string —
   the expectation inside `gates.selftest()` — moved with them, because
   it is an expectation of the renamed string. Disclosed in `6ec22a5`'s
   own message. The row's *intent* (one deliberate output change, and
   only that) holds; its count does not.

2. **The copied comment habit survived the change that removed its
   subject.** The old three-line drift warning is gone from all six
   modules, as A2 and A5 required. What replaced it is a new near-
   byte-identical three-line comment in the same six places ("cli.gh_read
   owns the window — the limit it sends gh and the truncation it reports
   are the same number, so the two can no longer drift apart"). It states
   a true fact and warns of nothing, so it is not the coupling the run
   removed. But the propagation-by-copy path `defect.md` named as "the
   warning about drift is itself the thing being duplicated" is still
   the shape of these six files. Out of scope to fix here; noted for
   Review.

---

## Not verified

Stated explicitly, because a silent gap reads as coverage.

- **Nothing was exercised against real GitHub.** Every `gh` call in this
  repo's tests goes through an injected fake runner, and this stage added
  none. What that leaves unproven, concretely: that `gh` accepts
  `--limit` appended in the position `cli.gh_read` now appends it at (the
  argv is asserted against a fake, and all ten sites already placed
  `--limit` last on main, so the constructed argv is byte-identical — but
  no live call confirmed it); that a real rate-limit or auth failure
  still lands in `CLI_FAILURES` now that the catch moved into the seam;
  and that `label_sync.live_labels`' three callers behave the same
  against a live failure now that they no longer own the `except`. This
  cannot and should not be closed here — it would need credentials and a
  live tracker. It would be settled by one scheduled workflow run of
  `label-sync`, `gate-digest` and `toolsmith-mine` after merge, watched
  for a nonzero exit or a changed problem line.
- **"Observable output unchanged" is bounded by the test contract.** The
  method proves byte-identity for every string the repo's 1,234 pre-change
  tests pin and for detector J's complete enumeration. A problem string on
  a path no test covers could have moved and this would not catch it. The
  AST literal sweep was run as a coarse net but is not evidence on its
  own: the composition moved into the seam, so f-string templates changed
  shape in 26 files while the strings they produce did not, and the sweep
  cannot tell those apart.
- **The dashboard and sweeps have no payload twin, so their stamped
  behavior is untested by construction** — correct, and unchanged by this
  run, but it means `dashboard.py`'s three re-pointed reads are covered
  only by `tests/test_dashboard.py`, which is byte-identical to main.
- **"Watched to fail" is attested, not re-demonstrable.** For A1, B4 and
  C1 the commit messages record the observed red. I re-derived the
  *impossibility of passing* against the old code in all three cases,
  which is the verifiable half; the act of watching is not recoverable
  after the fact.
- **ADR-0056 is provisional.** Its status stays provisional until the
  operator confirms at merge, matching ADR-0054's precedent. That
  confirmation is a Ship-stage act, not a Verify one.
- **The eleven-label enumeration for detector J is the taxonomy the
  fixture declares**, not the 28-label shipped taxonomy. It covers every
  label the tools and the Makefile *name*, which is what detector J
  reports on, so no declaring site is missed — but a label named nowhere
  in code could not appear in either column.
- **`TestRepoRoot.test_resolves_to_this_git_checkout` fails in every
  `git archive` export** used for the cross-revision runs above,
  including the main-against-main control. It is an artifact of the
  method, not a finding, and it does not fail in the real checkout.

## Where this routes

No failures, so the next stage is **Review**. Two items above are worth
a reviewer's eye rather than an implementer's: B4's off-by-one Accept
count, and the six replicated window comments.
