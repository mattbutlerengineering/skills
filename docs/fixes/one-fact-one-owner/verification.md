---
stage: verify
run: maintenance:one-fact-one-owner
date: 2026-08-23
assumptions:
  - "Criteria source: there is no prd.md — this is a maintenance run that entered at capture with re-entry: architect — so the criteria list is defect.md's seven Success criteria (D1-D7) plus every acceptance criterion in breakdown.md's thirteen items (A1-A5, B1-B4, C1-C4). Where an item's clause is already scored under a defect.md criterion the overlap is named rather than scored twice."
  - "B4's 'deleting any single marker makes the group speak' was re-checked against two throwaway `git archive HEAD` copies in a scratch directory, driving one_owner.check(root, run=fake) with an injected runner, rather than by mutating a tracked file. The run's git policy forbids touching the working tree; the experiment is reproducible and is quoted in full below."
  - "The eight remaining findings are scored as TRUE findings on architecture.md's enumeration plus a two-sample spot check (budget_guard.CONTINUE/cost_report.CONTINUE and charter_replay.ROOT/trigger_eval.ROOT, both read and confirmed genuine). Verify did not independently re-adjudicate the other six. Recorded under Not verified."
  - "trigger_eval.py and charter_replay.py were NOT run: both are real model runs that cost money and need the `claude` CLI, and CLAUDE.md puts them on demand only, never CI. Neither is named by any criterion in this run. Recorded under Not verified."
---

# Verification: a pre-pass that asks whether a fact is stated twice

Verified at 14 local commits `a527688..HEAD` (`62a3e56`), working tree
otherwise as the run left it.

## Summary

**20 criteria. 19 PASS, 1 PASS-AS-AMENDED, 0 FAIL.**

The tool exists, runs from two documented commands, and finds the
acceptance fixture unaided while having never been told about it. The
carve-out mechanism has a real user and pays rent in both directions,
proved on the live tree. The full battery is green.

**The one criterion that is not met as written is D4**, and it is not
softened here: `defect.md` asked for "a test that would have caught each
of the three historical instances". The suite catches **two of three**
(miss 1 and miss 3) and **pins the third (miss 2) as a known miss**. The
operator accepted that substitution on 2026-08-23; the amendment is
recorded in `architecture.md` (*Measured against the tree*), carried into
`breakdown.md` C2, and written into the assertion's own comment at
`tests/test_one_owner.py:933-959`. It is scored below against the amended
form, and the amendment is stated rather than hidden.

## The battery — verbatim

```
$ python3 -m unittest discover tests
[one line of 1344 progress dots, elided]
----------------------------------------------------------------------
Ran 1344 tests in 15.525s

OK

$ python3 lint.py
lint: 0 problem(s) across 24 skills
(exit 0)

$ python3 gates.py; echo "gates exit=$?"
gates: 0 problem(s)
gates exit=0

$ python3 gates.py --selftest; echo "selftest exit=$?"
selftest: ok
selftest exit=0

$ python3 one_owner.py; echo "one_owner exit=$?"
one-owner: assembler.py:54 READY_LABEL, validator.py:79 READY_LABEL and work_queue.py:39 READY_LABEL state the same value — one fact, one owner
one-owner: budget_guard.py:167 record and cost_ledger.py:126 row_key read the same payload keys (run_id, wo) — one fact, one owner
one-owner: budget_guard.py:55 CONTINUE and cost_report.py:44 CONTINUE state the same value — one fact, one owner
one-owner: charter_replay.py:49 ROOT and trigger_eval.py:42 ROOT state the same value — one fact, one owner
one-owner: cli.py:376 label_names and plane_drift.py:31 issue_lifecycle read the same payload keys (labels, name) — one fact, one owner
one-owner: dashboard.py:198 _pr_by_issue, gate_digest.py:187 run_daily and rejection_mining.py:192 run_mine read the same payload keys (body, number, state) — one fact, one owner
one-owner: eval_schema.py:182 validate and trigger_eval.py:303 score_case read the same payload keys (expected, id, kind, query) — one fact, one owner
one-owner: gate_digest.py:91 LIST_ARGS and rejection_mining.py:54 ISSUE_ARGS state the same value — one fact, one owner
one-owner: label_sync.py:69 plan, label_sync.py:115 sync and sweeps.py:269 ensure_labels read the same payload keys (color, description, name) — one fact, one owner
one-owner: 9 problem(s)
one_owner exit=1
```

`one_owner.py` exiting 1 is correct and is **not** part of the battery:
the tool is deliberately outside `make check` and outside every workflow
(`architecture.md`, *Approach*; `breakdown.md` preamble).

**The nine findings reconcile exactly against `architecture.md`'s
measured ten.** The tenth was the `runner('git')` group, which is now
annotated and silent. Two line numbers moved by exactly three —
`budget_guard.py:164 record` to `:167` and `dashboard.py:195
_pr_by_issue` to `:198` — which is the three-line marker comment block
B4 added to each of those two files, and nothing else.

## Criteria and evidence

### D1 — the check exists, runs from a documented command, and its output is label-prefixed problem strings

- Check: run the tool; read the documented commands; confirm the
  problem-string contract (label prefix, `N problem(s)` epilogue,
  nonzero exit).
- Evidence: the battery block above — every line is `one-owner: `-prefixed
  and the epilogue is `one-owner: 9 problem(s)`, printed through
  `cli.report` (`one_owner.py:439`: `return report("one-owner",
  check(repo_root()))`). Two documented entry points:

  ```
  $ git diff a527688^..HEAD -- CLAUDE.md
  +- `python3 one_owner.py` — which facts this repo's own Python modules
  +  state twice (the same value in two modules, or two functions reading
  +  the same payload keys), as `one-owner:` problem strings. It is outside
  +  `make check` and outside every workflow, so a finding never colours
  +  main red — it is a question for a human.

  $ python3 factory.py help | grep -n one-owner
  14:  one-owner         one_owner: a read-only pre-pass asking which facts have two owners.
  ```
- Result: **PASS**

### D2 — it finds `plane_drift.issue_lifecycle` retyping `cli.label_names` without being told about it specifically

- Check: run the tool against the live tree, then grep the tool's own
  source for every token naming the fixture.
- Evidence:

  ```
  $ python3 one_owner.py | grep label_names
  one-owner: cli.py:376 label_names and plane_drift.py:31 issue_lifecycle read the same payload keys (labels, name) — one fact, one owner

  $ grep -n -e label_names -e issue_lifecycle -e plane_drift -e 'cli\.py' one_owner.py
  $ echo "grep exit=$?"
  grep exit=1
  ```

  Exit 1 with no output: the tool names neither the fixture's functions,
  nor its modules, nor `cli.py`, anywhere in its 443 lines. `git diff
  --stat a527688^..HEAD` lists no change to `plane_drift.py`, so the
  fixture is intact.
- Result: **PASS**

### D3 — it stays silent on every recorded deliberate duplicate; zero false positives at HEAD, or every exception carved out with its ADR named

- Check: grep the live output for the canonical pair; count and classify
  the nine remaining findings.
- Evidence:

  ```
  $ python3 one_owner.py | grep -e '_CHECKBOX' -e 'protocol.py' -e 'knowledge_plane.py' -e 'ROW'
  $ echo "grep exit=$? (1 = no such line)"
  grep exit=1 (1 = no such line)
  ```

  `protocol._CHECKBOX` versus `knowledge_plane.ROW` is silent with **no
  marker involved** — the identity rule is exact and their patterns and
  flags differ. The unit case pins the same fact against a fixture:
  `tests.test_one_owner.TestSameValue.test_the_canonical_deliberate_pair_stays_silent_with_no_marker
  ... ok`.

  Of the nine printed findings: one is this run's acceptance fixture
  (D2, deliberately left live and seeded separately at
  `docs/backlog.md:46`); the other eight are the true, undecided pairs
  `architecture.md` enumerated in advance, and `defect.md`'s out-of-scope
  list forbids folding them here. The one recorded deliberate exception —
  the `runner('git')` group — is carved out at its definitions and names
  its ADR:

  ```
  $ python3 -c "import one_owner; ..."   # the tool's own marker reader
  budget_guard.py [Marker(lineno=113, owner='git_runner', counterpart='dashboard.git_runner', adr='ADR-0061', reason='ADR-0037 sanctions the alias')]
  dashboard.py    [Marker(lineno=63,  owner='git_runner', counterpart='one_owner.git_runner',  adr='ADR-0061', reason='ADR-0037 sanctions the alias')]
  one_owner.py    [Marker(lineno=54,  owner='git_runner', counterpart='budget_guard.git_runner', adr='ADR-0061', reason='ADR-0037 sanctions the alias')]
  ```
- Result: **PASS** — with the scope of the claim stated: "false positive"
  here means "a pair the repo has already decided", and the eight are
  scored as true findings on `architecture.md`'s enumeration plus a
  two-sample spot check (see *Not verified*).

### D4 — a test that would have caught each of the three historical instances, against fixtures, not the live tree — **AMENDED BY THE OPERATOR**

- **The amendment, stated plainly.** `defect.md` asks for a test that
  would have caught **each of the three** historical instances. The
  design does not meet that as written. Miss 2 —
  `sweeps.reconcile_drift` versus `dashboard._drift` — is not findable by
  any cheap syntactic rule: at `fbfa3c3` the two functions are 7
  statements over 69 lines against 3 over 21, share no identical text,
  and carry a narrower rule on one side. Two candidate rules were built
  and **lost on measured evidence** (whole-function-body identity yields
  zero groups at HEAD and at `fbfa3c3`; a seam-call fingerprint fires
  hardest on six correct `main()` adopters and still misses this pair —
  `architecture.md`, *Decisions & alternatives*). Architect surfaced the
  substitution rather than deciding it alone, and:

  > **Resolved 2026-08-23 — the operator accepts the substitution.** The
  > criterion is amended for this run: the suite must catch misses 1 and 3,
  > and **pin miss 2 as a known miss** with the reason recorded, in the
  > shape of `tests/test_knowledge_plane.py:99-107`. […] Verify scores
  > against the amended form and must say plainly that it was amended and
  > why. The rejected alternative — redesigning to reach `_drift` — was
  > declined on the measured evidence in *Decisions & alternatives*, not
  > on cost.
  > — `architecture.md`, *Measured against the tree*

  It is **2 of 3 met, the third pinned as a known miss**. This is not a
  full pass and it is not a plain failure; reporting it as either would
  be dishonest.

- Check: run the historical-instance and known-miss cases; read the
  fixtures for their provenance citations; confirm they run against
  fixture trees, never the live tree.
- Evidence:

  ```
  $ python3 -m unittest tests.test_one_owner -v
  test_miss_1_the_checked_row_grammar_with_two_owners (…TestHistoricalInstances…) ... ok
  test_miss_3_the_labels_walk_with_two_strictnesses (…TestHistoricalInstances…) ... ok
  test_both_misses_in_one_tree_are_two_findings (…TestHistoricalInstances…) ... ok
  test_a_re_implementation_of_a_rule_is_not_found (…TestKnownMiss…) ... ok
  ```

  Miss 1 and miss 3 are pinned by exact string
  (`tests/test_one_owner.py:795-812`):

  ```python
  self.assertEqual(
      check_tree(gates=self.MISS_1_GATES,
                 knowledge_plane=self.MISS_1_KNOWLEDGE_PLANE),
      ["one-owner: gates.py:2 MERGED_ROW and knowledge_plane.py:2"
       " DONE_ROW state the same value — one fact, one owner"])
  …
      ["one-owner: cli.py:2 label_names and sweeps.py:2"
       " issue_lifecycle read the same payload keys (labels, name)"
       " — one fact, one owner"])
  ```

  Each fixture cites the commit and PR from `defect.md`'s evidence table
  it reproduces, so a later reader can tell a fixture from an invention:
  `# gates.py:106 at fbfa3c3 — created 208ffdb (#130)`,
  `# knowledge_plane.py:94 at fbfa3c3 — created 4333370 (#221)`,
  `# cli.py:349 at fbfa3c3 — created 622e2bf (#247)`,
  `# sweeps.py:220 at fbfa3c3 — created f38fbdd (#204)`.

  Miss 2 is pinned as an absence, with the amendment named in the case
  itself (`tests/test_one_owner.py:933-959`):

  ```python
  # THIS IS THE AMENDED SUCCESS CRITERION. defect.md asked for a
  # test that would have caught each of the THREE historical
  # instances; the operator accepted the substitution on 2026-08-23,
  # and architecture.md records it under *Measured against the
  # tree*: the suite catches misses 1 and 3 and PINS miss 2 as a
  # known miss with the reason recorded. …
  self.assertEqual(
      check_tree(sweeps=self.RECONCILE_DRIFT,
                 dashboard=self.DASHBOARD_DRIFT), [],
      "A finding here is WELCOME NEWS, not a broken test: it means"
      " the rules got strong enough to reach a re-implementation."
      " Do not delete this case to make it pass — move it to"
      " TestHistoricalInstances and pin the string it now emits.")
  ```

  The pin cannot pass vacuously: the fixtures are the two functions
  verbatim at `fbfa3c3`, and a fixture that failed to parse would put a
  problem in the list and fail the assertion (the class docstring says
  so). Every case above runs against fixture trees through `check_tree`
  with an injected fake git runner — never the live tree — so the suite
  does not decay as the tree is cleaned.
- Result: **PASS against the operator-amended criterion (2 of 3 caught,
  the third pinned as a known miss). NOT met as `defect.md` wrote it.**

### D5 — the full battery is green

- Check: run all four commands.
- Evidence (the same run quoted in full under *The battery — verbatim*):

  ```
  $ python3 -m unittest discover tests
  ----------------------------------------------------------------------
  Ran 1344 tests in 15.525s

  OK

  $ python3 lint.py
  lint: 0 problem(s) across 24 skills

  $ python3 gates.py; echo "gates exit=$?"
  gates: 0 problem(s)
  gates exit=0

  $ python3 gates.py --selftest; echo "selftest exit=$?"
  selftest: ok
  selftest exit=0
  ```
- Result: **PASS**

### D6 — if the check ships as a detector or a mirrored root tool, `update-manifest` is run and committed in the same change, and detector E is green

- Check: the tool itself is root-only (no payload importer, ADR-0060) —
  but B4's first annotation lands in `budget_guard.py`, which **is** a
  `factory_init.MIRRORS` entry. So the pin is: payload twin identical to
  root, manifest regenerated, detector E green.
- Evidence:

  ```
  $ diff -q budget_guard.py factory/templates/tools/factory/budget_guard.py; echo "diff exit=$?"
  diff exit=0

  $ python3 -m unittest tests.test_factory_init
  ....................................................
  ----------------------------------------------------------------------
  Ran 52 tests in 1.308s

  OK

  $ python3 gates.py
  gates: 0 problem(s)
  ```

  `git diff --stat a527688^..HEAD` shows the three files that must move
  together did: `factory/templates/tools/factory/budget_guard.py | 3 +`
  and `factory/manifest.json | 2 +- ` alongside `budget_guard.py | 3 +`.
  Detector E (manifest↔payload) and `tests/test_factory_init.py`
  (payload↔root) agree.
- Result: **PASS**

### D7 — the test-ordering rule is visible in the history: tests at the intended interface land before the implementation

- Check: read the fourteen commit messages for the recorded red-first
  step. (`breakdown.md`'s third assumption: the rule is served *inside*
  each item, because no test at `one_owner.py`'s interface could land
  green — or even import — against today's code, and a whole red test
  file at an item boundary is what the precedent refuses.)
- Evidence, from `git log a527688^..HEAD`:

  ```
  TestCheck, TestMain and TestFrontDoor landed first and were watched fail
  … `ModuleNotFoundError: No module named 'one_owner'`, 1 error, before check() existed.

  TestMarkers landed first and was watched fail for the right reason:
  … `cannot import name 'Marker'?`, 1 error, before the reader existed.

  TestCoverage landed first and was watched fail for the right reason: 8
  failures, the headline one being … markers were read but joined to
  nothing, so a fully covered group still reported.

  each pin was watched fail with
      FAIL: test_miss_3_the_labels_walk_with_two_strictnesses
      FAIL: test_miss_1_the_checked_row_grammar_with_two_owners
  ```
- Result: **PASS** — the evidence is the commit bodies, which is the form
  `breakdown.md` chose in advance; there are no separate red commits, by
  design.

### A1 — the module and its pure core

- Check: run `TestGroups` and `TestDataModel`; confirm the docstring
  summary reaches the front-door index; confirm the import list.
- Evidence:

  ```
  test_two_members_in_distinct_modules_group ... ok
  test_two_members_in_the_same_module_do_not ... ok
  test_three_members_in_three_modules_group_as_one ... ok
  test_identical_identities_sort_deterministically ... ok
  test_a_lone_member_is_not_a_group ... ok
  test_different_kinds_never_share_a_group ... ok
  test_it_is_total_and_raises_on_nothing ... ok
  test_the_three_shapes_carry_the_declared_fields (…TestDataModel…) ... ok
  test_the_tool_has_a_verb_and_a_docstring_summary (…TestFrontDoor…) ... ok

  $ grep -n '^import \|^from ' one_owner.py
  38:import ast
  39:import io
  40:import re
  41:import sys
  42:import tokenize
  43:from collections import namedtuple
  44:from pathlib import Path
  46:from cli import CLI_FAILURES, detail, report, runner
  47:from knowledge_plane import repo_root

  $ grep -c 'import gates' one_owner.py
  0
  ```

  `TestDataModel` asserts the three namedtuples' fields exactly as
  `architecture.md`'s *Data model* declares them (`FactSite`, `Marker`,
  `Group`). Stdlib plus two seam modules; `gates` is imported nowhere —
  the coupling ADR-0058 removed stays removed.
- Result: **PASS**

### A2 — `same-value`

- Check: run `TestSameValue`.
- Evidence:

  ```
  test_two_modules_binding_one_compiled_pattern_are_two_owners ... ok
  test_formatting_and_line_wrapping_do_not_hide_a_copy ... ok
  test_a_bare_numeric_boolean_or_none_is_a_knob_not_a_fact ... ok
  test_a_shared_string_or_call_is_a_fact ... ok
  test_only_module_level_bindings_count ... ok
  test_the_canonical_deliberate_pair_stays_silent_with_no_marker ... ok
  test_a_module_that_cannot_be_parsed_is_reported_never_swallowed ... ok
  test_sites_come_back_in_source_order ... ok
  ```

  Every clause of A2 has a case: the miss-1 shape, `ast.unparse`
  normalisation, the structural floor (bare numeric/boolean/`None`), the
  canonical deliberate pair silent with no marker, and the parse-failure
  problem string with other modules still contributing.
- Result: **PASS**

### A3 — `same-keys`

- Check: run `TestSameKeys`.
- Evidence:

  ```
  test_two_walks_over_the_same_two_keys_are_two_owners ... ok
  test_the_floor_is_two_keys_because_the_fixture_has_exactly_two ... ok
  test_get_and_subscript_are_the_same_read ... ok
  test_key_sets_that_merely_overlap_are_not_one_fact ... ok
  test_a_nested_function_is_reached ... ok
  test_both_kinds_come_back_from_one_module_in_source_order ... ok
  ```

  The floor is asserted at its boundary rather than assumed, which is
  what keeps the acceptance fixture (`{labels, name}`, exactly two keys)
  in range.
- Result: **PASS**

### A4 — the universe comes from git, never from a filesystem walk

- Check: run `TestSourceFiles`.
- Evidence:

  ```
  test_the_universe_is_what_git_tracks_not_what_the_disk_holds ... ok
  test_the_payload_mirror_and_the_suite_are_outside_the_universe ... ok
  test_a_failed_or_missing_git_is_a_problem_not_a_traceback ... ok
  test_a_missing_git_binary_reports_the_os_error ... ok
  test_a_file_that_cannot_be_read_is_reported_and_skipped ... ok
  test_an_empty_universe_is_never_silently_clean ... ok
  test_files_come_back_sorted_by_path_with_their_source ... ok
  ```

  `one_owner.py:195-229` derives the list from `run(["-C", str(root),
  "ls-files", "--", "*.py"])` and from nothing else, with
  `EXCLUDED = ("factory/", "tests/")`. The runner is injected, so the
  suite never shells out. The live run corroborates the exclusions: no
  finding names a `factory/` or `tests/` path, and the payload mirror's
  17 tools do not appear as duplicates of themselves.
- Result: **PASS**

### A5 — `check`, `main`, and the acceptance fixture found unaided

- Check: run `TestCheck`, `TestMain`, `TestFrontDoor`; confirm the verb
  row; confirm the fixture on the live tree (scored under D2); confirm
  the `runner('git')` group is a **triple**, not the design's pair
  (design gap 3).
- Evidence:

  ```
  test_an_uncovered_same_value_group_names_both_owners ... ok
  test_an_uncovered_same_keys_group_names_the_keys ... ok
  test_every_member_is_listed_sorted_by_path_then_line ... ok
  test_the_same_tree_yields_byte_identical_output_twice ... ok
  test_a_tree_with_one_owner_per_fact_reports_nothing ... ok
  test_a_broken_environment_never_reads_as_no_duplicates ... ok
  test_reading_and_parsing_problems_reach_the_caller ... ok
  test_check_raises_on_nothing ... ok
  test_a_clean_tree_exits_zero_with_the_exact_summary_line (…TestMain…) ... ok
  test_a_finding_prints_through_the_report_epilogue (…TestMain…) ... ok
  test_unrecognized_argv_prints_usage_and_exits_2 (…TestMain…) ... ok

  $ grep -n 'one-owner' factory.py
  48:    "one-owner": ("one_owner", "argv"),
  ```

  The `runner('git')` group holds three members on the live tree —
  `budget_guard.py`, `dashboard.py` and `one_owner.py`, the tool's own
  `git_runner` binding included — evidenced by the marker cycle under D3
  and by the scratch experiment under B4, where removing one marker
  names two of the three by file and line.
- Result: **PASS** (the fixture clause is scored under D2)

### B1 — the marker grammar, read at the definition site

- Check: run `TestMarkers`; confirm the self-reference hazard is closed
  on the live tree.
- Evidence:

  ```
  test_a_marker_directly_above_a_definition_is_read ... ok
  test_a_marker_mid_block_among_ordinary_comments_is_read ... ok
  test_a_blank_line_ends_the_block_so_the_marker_attaches_to_nothing ... ok
  test_an_unreadable_marker_is_a_problem_never_a_permission ... ok
  test_a_bare_marker_waives_nothing ... ok
  test_a_marker_above_something_that_states_no_fact_attaches_to_nothing ... ok
  test_a_marker_problem_silences_nothing ... ok
  test_a_hash_inside_a_string_or_docstring_is_not_a_comment ... ok
  ```

  The self-reference hazard is closed and demonstrated live: the tool's
  own output (nine findings, quoted above) contains **no** line about
  `one_owner.py` carrying a stale or unreadable marker of its own. The
  grammar is held as a string (`MARKER_GRAMMAR`, `one_owner.py:65`) and
  documented in the module docstring, which states the rule outright:
  "THE GRAMMAR IS DOCUMENTED HERE AND IN NO COMMENT IN THIS FILE."
  `budget_guard.py:110-113` is the real three-line block the first
  annotation needed, and it is read (mid-block case, above).
- Result: **PASS**

### B2 — silence is a property of the group, never of one marker

- Check: run `TestCoverage`.
- Evidence:

  ```
  test_a_fully_covered_group_is_silent ... ok
  test_a_third_unmarked_owner_makes_the_group_speak_again ... ok
  test_a_member_no_other_member_names_is_not_vouched_for ... ok
  test_a_marker_pays_rent_or_it_is_a_finding ... ok
  test_a_counterpart_this_repo_does_not_define ... ok
  test_a_citation_must_resolve_to_a_file_in_docs_adr ... ok
  test_a_marker_that_cannot_be_read_never_buys_silence ... ok
  test_status_liveness_is_deliberately_not_checked ... ok
  test_check_still_raises_on_nothing ... ok
  ```

  All five remaining contract shapes are pinned by exact string against
  fixture trees, and both named properties are asserted directly: a fully
  covered group is silent, and a third unmarked member makes that same
  fixture group speak again — ADR-0039's failure, made impossible. The
  deferral is visible in the suite too: a fixture citing a superseded ADR
  produces no problem.
- Result: **PASS**

### B3 — the 0061 decision record is written

- Check: read the file's head; read the index row; run the detectors.
- Evidence:

  ```
  $ sed -n '1,4p' docs/adr/0061-a-carve-out-lives-at-the-definition-site.md
  # A carve-out lives at the definition site and must pay rent

  - Status: provisional
  - Date: 2026-08-23

  $ grep -n '0061' docs/adr/README.md | sed 's/](/] -> (/'
  84:| [0061] -> (0061-a-carve-out-lives-at-the-definition-site.md) | A carve-out lives at the definition site and must pay rent | provisional |

  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```

  The status cell matches the file's `- Status:` line byte for byte,
  which is what detector D compares; detector C finds no dangling
  `ADR-0061` token and detector I no stale link. Seven open provisionals
  now, knowingly.
- Result: **PASS**

### B4 — the first annotation, and the mechanism has a real user

- Check: confirm every member of the live `runner('git')` group carries a
  marker citing 0061 with a non-empty reason naming the ADR-0037
  sanction; confirm the group is silent; **re-run the delete-one-marker
  experiment**; confirm the manifest side (D6) and that `plane_drift.py`
  is untouched with the fixture still reporting.
- Evidence: the three markers are quoted under D3 — a closed cycle,
  `budget_guard → dashboard → one_owner → budget_guard`, so every member
  is marked **and** every member is named by another. The group is absent
  from the nine findings.

  The load-bearing claim of ADR-0061 — that deleting any single marker
  makes the whole group speak — re-checked without touching the working
  tree, by unpacking two `git archive HEAD` copies into a scratch
  directory, deleting line 113 of `budget_guard.py` in one of them, and
  driving `one_owner.check(root, run=fake)` against each:

  ```
  === tree-a (HEAD as committed) ===
  9                       # findings
  (no git_runner lines — the group is silent)

  === tree-b (budget_guard.py marker deleted) ===
  one-owner: budget_guard.py:113 git_runner joins a recorded deliberate group without a marker — a new owner cannot admit itself
  one-owner: dashboard.py:64 git_runner carries a marker but no other owner names it — an existing owner must vouch for a new one
  ```

  Both directions fire from one deletion: the newcomer is not covered,
  and the owner that vouched for it is left vouching for nobody.

  `git diff --stat a527688^..HEAD` lists no `plane_drift.py`, and the
  fixture still reports (D2). Manifest side: `diff -q` clean and
  `tests.test_factory_init` green (D6).
- Result: **PASS**

### C1 — the two historical instances the tool catches

- Check: run the historical-instance cases; read the fixtures for their
  provenance citations. Scored in full under D4; the literal output is
  repeated here rather than borrowed from that section.
- Evidence:

  ```
  $ python3 -m unittest tests.test_one_owner -v
  test_miss_1_the_checked_row_grammar_with_two_owners (…TestHistoricalInstances…) ... ok
  test_miss_3_the_labels_walk_with_two_strictnesses (…TestHistoricalInstances…) ... ok
  test_both_misses_in_one_tree_are_two_findings (…TestHistoricalInstances…) ... ok

  $ grep -n -e 208ffdb -e 4333370 -e 622e2bf -e f38fbdd tests/test_one_owner.py
  172:# (208ffdb, 2026-07-11, #130) and knowledge_plane.DONE_ROW (4333370,
  273:# this run's acceptance fixture: cli.label_names (622e2bf, 2026-08-10,
  275:# (f38fbdd, 2026-08-10, #204). Two genuinely different walks — one drops
  776:    # Miss 1 — gates.MERGED_ROW (208ffdb, 2026-07-11, #130) and
  777:    # knowledge_plane.DONE_ROW (4333370, 2026-08-10, #221): byte-identical
  780:    MISS_1_GATES = ('# gates.py:106 at fbfa3c3 — created 208ffdb (#130)\n'
  783:        '# knowledge_plane.py:94 at fbfa3c3 — created 4333370 (#221)\n'
  786:    # Miss 3 — cli.label_names (622e2bf, 2026-08-10, #247) and
  787:    # sweeps.issue_lifecycle (f38fbdd, 2026-08-10, #204), created the same
  791:    MISS_3_CLI = ('# cli.py:349 at fbfa3c3 — created 622e2bf (#247)\n'
  793:    MISS_3_SWEEPS = ('# sweeps.py:220 at fbfa3c3 — created f38fbdd (#204)\n'
  ```

  Both cases drive `check_tree(...)` — fixture trees with an injected
  fake git runner — never the live tree.
- Result: **PASS**

### C2 — the third instance, pinned as a known miss

- Check: run the known-miss case; read its comment and its assertion
  message. Scored in full under D4; the literal output is repeated here
  rather than borrowed from that section.
- Evidence:

  ```
  $ python3 -m unittest tests.test_one_owner -v
  test_a_re_implementation_of_a_rule_is_not_found (…TestKnownMiss…) ... ok

  $ sed -n '953,959p' tests/test_one_owner.py
          self.assertEqual(
              check_tree(sweeps=self.RECONCILE_DRIFT,
                         dashboard=self.DASHBOARD_DRIFT), [],
              "A finding here is WELCOME NEWS, not a broken test: it means"
              " the rules got strong enough to reach a re-implementation."
              " Do not delete this case to make it pass — move it to"
              " TestHistoricalInstances and pin the string it now emits.")
  ```

  The case is in the shape of `tests/test_knowledge_plane.py:99-107` — an
  absence asserted on purpose — and its comment (quoted under D4) names
  the amendment, its date, and the measured reason.
- Result: **PASS** (this item is the amendment; see D4 for what it
  substitutes for)

### C3 — `CLAUDE.md` documents the command, and the battery closes the run

- Check: read the diff; confirm the preamble is not left false; run the
  battery; check `git status`.
- Evidence: the `CLAUDE.md` diff is quoted under D1. The existing
  preamble ("On demand only (real model runs, costs money, never CI;
  both need the `claude` CLI)") is **not** left false — the entry opens
  its own framing rather than joining that list: "Also on demand, but
  free and needing nothing installed — a review pre-pass, deliberately
  **not** a gate:". A reader who has never seen the tool gets the
  command, one line on what it answers, and the statement that it is
  outside `make check` and never colours main red.

  ```
  $ git status --short
   M docs/backlog.md
  ?? docs/fixes/deepening-tool-seams/retro.md
  ?? docs/fixes/one-fact-one-owner/architecture.md
  ?? docs/fixes/one-fact-one-owner/autorun-brief.md
  ?? docs/fixes/one-fact-one-owner/defect.md
  ?? docs/fixes/toolsmith-mine-pr-permissions/retro.md
  ```

  No unregenerated payload and no stray file from this run: every entry
  above pre-dates it (`docs/backlog.md`'s seed claims, two other runs'
  retros, and this run's own upstream artifacts). The battery is quoted
  verbatim above.
- Result: **PASS**

### C4 — OPTIONAL: the daily routine runs the pass

- Check: read the diff; confirm it is §2 Orient and not §3 Health sweep;
  run lint.
- Evidence:

  ```
  $ git diff a527688^..HEAD -- docs/factory/improvement-routine.md
  +9. `python3 one_owner.py` — the one-fact-one-owner pre-pass (ADR-0061).
  +   Read-only intel, like everything else in this section: findings are
  +   report material, and a group that is NEW since the last routine run
  +   is a `docs/backlog.md` seed proposal under Proposals. It lives here
  +   and **not** in §3 Health sweep on purpose — §3 classifies main green
  +   or red, and a one-owner finding must never colour main red; …
  +   The tool exits nonzero whenever it finds anything, so a
  +   nonzero exit here is normal and is not a failure of the run.

  $ python3 lint.py
  lint: 0 problem(s) across 24 skills
  ```

  The hunk lands at line 65 of the file, inside §2 Orient's numbered
  read-list, as item 9. The optional item was taken.
- Result: **PASS**

## Failures

**None.**

One criterion — **D4** — is met only in its operator-amended form: the
suite catches 2 of the 3 historical instances and pins the third as a
known miss. That is a recorded, accepted limitation of the design, not a
defect in the implementation, and it is stated in three places that a
future reader will hit (`architecture.md`, `breakdown.md` C2, and the
assertion's own comment). It routes nowhere; nothing goes back to
Implement.

## Not verified

- **`python3 trigger_eval.py` and `python3 charter_replay.py` were not
  run.** Both are real model runs that cost money and need the `claude`
  CLI; CLAUDE.md puts them on demand only and never in CI. No criterion
  in this run names either, and this run touches no eval definition and
  writes nothing to `evals/results/` (append-only).
- **The eight remaining findings were not each independently
  re-adjudicated** as true findings rather than false positives. They are
  scored on `architecture.md`'s pre-registered enumeration (which
  reconciles exactly, ten minus the now-silent `runner('git')` group,
  with two line numbers shifted by exactly the three-line marker blocks)
  plus a two-sample spot check: `budget_guard.py:55 CONTINUE =
  "CONTINUE"` against `cost_report.py:44 CONTINUE = "CONTINUE"`, and
  `charter_replay.py:49 ROOT = Path(__file__).resolve().parent` against
  `trigger_eval.py:42 ROOT = Path(__file__).resolve().parent` — both
  genuine, both undecided. The other six were read only as tool output.
  Folding any of them is out of scope for this run by `defect.md`;
  routing them to `docs/backlog.md` is Operate's closing act.
- **`python3 factory_init.py update-manifest` was not re-run** to prove
  idempotence, because running it would write to the working tree, which
  this run's git policy forbids. The two pins that would catch a drifted
  manifest were run instead and are green: detector E (via `gates: 0
  problem(s)`) for manifest↔payload, and `tests/test_factory_init.py`
  (52 tests, OK) for payload↔root, plus `diff -q` on the twin.
- **Miss 2 (`sweeps.reconcile_drift` versus `dashboard._drift`) is not
  detected**, by design, and Verify made no independent attempt to find a
  rule that would reach it. The two candidate rules were built and
  measured at Architect time; this stage re-read that evidence rather
  than re-running the probe.
- **Behaviour on a non-git or broken environment was verified only
  through injected fakes**, never by breaking a real environment: the
  `git ls-files failed`, missing-binary, unreadable-file and
  empty-universe paths are covered by `TestSourceFiles` with a fake
  runner.
- **No performance, concurrency or scale check** was made on the tool.
  Nothing asked for one; it is a single-pass read of 96 tracked files.
- **Nothing was committed, pushed, reviewed or shipped.** This artifact
  is uncommitted, and the pre-existing uncommitted files listed under C3
  were left untouched.

## Hand-off

No failures route back to Implement. Next stage is **Review**.
