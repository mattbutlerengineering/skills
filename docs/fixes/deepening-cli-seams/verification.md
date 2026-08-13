---
stage: verify
run: maintenance:deepening-cli-seams
date: 2026-08-13
assumptions:
  - "no prd.md — maintenance run, so the criteria list is the nine breakdown acceptance criteria plus the defect brief's reproduction; there are no PRD success criteria to trace"
---

# Verification: the deepening run's nine items

## Summary

**9 of 9 criteria PASS**, with two criteria passing under a stated
narrowing (A1 and A6, whose "green against unmodified <file>" clause can
only be attested from implement time, not re-demonstrated now). The
centerpiece regression — the defect brief's reproduction — is verified
behaviorally, by driving the tool and reading its actual output, not only
by a green test.

Whole-repo gate at verification time:

```
lint: 0 problem(s) across 23 skills
gates: 0 problem(s)
selftest: ok
Ran 1105 tests in 15.258s
OK
```

## Criteria & evidence

### Centerpiece regression (defect brief): a truncated listing defers no row for a reason it cannot know

- Check: drove `work_queue.main` against a fixture tree (injected gh
  runner, no network, real repo untouched) in three listing conditions —
  a full 100-entry window with a row whose mirrored issue sits past it, a
  short listing containing that issue, and an outright gh failure.
- Evidence:
  ```
  $ python3 work_queue.py plan    # gh returns a FULL 100-entry window
  wq: 0 work order(s) ready to run in parallel (wip_cap 3)
  wq: gh issue list returned a full 100-entry window — older entries are invisible; raise the window or narrow the query
  wq: 1 problem(s)
  [exit 1]

  $ python3 work_queue.py plan    # gh returns a short listing containing #999
  wq: 1 work order(s) ready to run in parallel (wip_cap 3)
    WO-0001  size:S  $5.00  issue #999  docs/features/demo/breakdown.md:1
    projected $5.00 on top of $0.00 spent this month
  wq: 0 problem(s)
  [exit 0]

  $ python3 work_queue.py plan    # gh fails outright
  wq: 0 work order(s) ready to run in parallel (wip_cap 3)
  wq: gh issue list failed: Command 'gh' returned non-zero exit status 1.
  wq: 1 problem(s)
  [exit 1]
  ```
- Result: PASS. The truncated case reports the truncation and defers
  nothing — the invented `no open issue #999 carries wo:ready-for-agent`
  line recorded in the brief is gone — while the trustworthy listing still
  plans the very same order. That second case is what makes the first one
  a fix rather than a mute button.

### A1 — `work_queue.main`'s summary line is pinned on every leg that emits one

- Check: `python3 -m unittest tests.test_work_queue.TestMain -v`
- Evidence:
  ```
  test_a_clean_run_ends_with_the_exact_summary_line ... ok
  test_a_config_failure_ends_with_the_same_summary_line ... ok
  test_an_untrusted_listing_defers_no_row_for_a_reason_it_cannot_know ... ok
  test_the_json_leg_carries_problems_instead_of_printing_them ... ok
  test_the_json_leg_prints_the_payload_then_the_summary ... ok
  test_the_json_summary_is_the_seam_s_own_grammar ... ok
  test_the_report_leg_prints_problems_above_the_summary ... ok
  Ran 7 tests in 0.008s
  OK
  ```
- Result: PASS, with a narrowing. The criterion's "green against
  unmodified `work_queue.py`" clause was satisfied at implement time and
  cannot be re-demonstrated now that the file is folded; what is verified
  here is that the pins exist and hold. The row's substantive claim —
  that `tests/` called `work_queue.main` zero times before this run — is
  answered by the seven cases above.

### A2 — `budget_guard`'s record legs are pinned alongside the `check` leg

- Check: `python3 -m unittest tests.test_budget_guard.TestRecordCLI
  tests.test_budget_guard.TestRecordRunCLI tests.test_budget_guard.TestMain -v`
- Evidence:
  ```
  test_a_clean_run_ends_with_the_exact_summary_line (TestRecordCLI) ... ok
  test_a_refused_row_ends_with_the_same_summary_line (TestRecordCLI) ... ok
  test_a_clean_run_ends_with_the_exact_summary_line (TestRecordRunCLI) ... ok
  test_a_refused_run_ends_with_the_same_summary_line (TestRecordRunCLI) ... ok
  test_a_clean_run_ends_with_the_exact_summary_line (TestMain) ... ok
  Ran 17 tests in 0.006s
  OK
  ```
- Result: PASS. All three legs now carry a `ReportContract` clean case and
  the two record legs carry a problem-bearing case, which is what
  distinguishes a computed count from a hand-typed one.

### A3 — the seam's name is free in `work_queue`

- Check: `grep -n "^def report\|^def compose_plan\|^from cli import" work_queue.py`
- Evidence:
  ```
  34:from cli import CLI_FAILURES, full_window, gh_json, gh_runner, report
  35:from cli import detail as gh_detail
  200:def compose_plan(batch, deferred, spent, wip):
  ```
- Result: PASS. No local `report` definition remains; `report` is the
  sixth cli name the file imports; the batch renderer is named for what
  it renders.

### A4 — `work_queue`'s two epilogues are folded

- Check: `grep -n "return report(" work_queue.py`, plus the manifest
  idempotence check below.
- Evidence:
  ```
  work_queue.py:223:        return report("wq", problems)
  work_queue.py:251:    return report("wq", problems)
  ```
- Result: PASS, stated precisely. Both non-JSON legs return the seam. The
  criterion's blanket phrase "no count is hand-typed" is true of those two
  legs only — the `--json` leg deliberately keeps its own summary print
  (that is A5's decision, below), and a lockstep test holds it to the
  seam's grammar. Reporting this as an unqualified pass would misdescribe
  the code.

### A5 — the `--json` leg is settled and the choice is recorded

- Check: read the leg and its lockstep test; confirm the decision is
  written down, not only coded.
- Evidence:
  ```
      if "--json" in argv:
          # The one leg cli.report does not fit: the problems already ride
          # inside the payload, so printing them again would both duplicate
          # them and put prose above the object a reader parses. Carved out
          # the way ADR-0051 carved out the usage epilogue — the seam does
          # not grow a "summary only" parameter for one caller. The summary
          # line stays in lockstep with the seam's grammar by test, since
          # nothing else bridges the two.
          print(json.dumps({"batch": batch, "deferred": deferred,
                            "problems": problems}, indent=2))
          print(f"wq: {len(problems)} problem(s)")
          return 1 if problems else 0
  ```
  `test_the_json_summary_is_the_seam_s_own_grammar` (green above) asserts
  the leg's last line equals `cli.report`'s own output for the same input.
- Result: PASS. The honest carve-out was taken, not the parameter; the
  reasoning is at the site, the alternative that was rejected is in
  `breakdown.md`'s deviation log, and the fork is held closed by test.

### A6 — `budget_guard`'s record legs are folded

- Check: `grep -n "return report(" budget_guard.py`
- Evidence:
  ```
  budget_guard.py:248:        return report("budget_guard", problems)
  budget_guard.py:256:        return report("budget_guard", problems)
  budget_guard.py:262:            return report("budget_guard",
  budget_guard.py:268:        return report("budget_guard", problems)
  ```
- Result: PASS, same narrowing as A1 on the "against unmodified" clause.
  Four call sites where two were before: the two record legs joined the
  two the `check` leg already had.

### A4/A6 shared criterion — the mirrored payload and its manifest

- Check: both files are `factory_init.MIRRORS` entries, so the payload
  copies and `factory/manifest.json` must be regenerated with the change.
  Ran `update-manifest` again and compared checksums either side.
- Evidence:
  ```
  before: 1d8915776ac4c4cdf64d17ef74b3f5ff5c1449ee
  after:  1d8915776ac4c4cdf64d17ef74b3f5ff5c1449ee
  IDEMPOTENT — payload and manifest are in sync with the root files
  gates: 0 problem(s)
  ```
- Result: PASS. Detector E is green and a fresh regeneration changes
  nothing, which is the actual claim ("leaves no diff") — the payload
  files do differ from `HEAD`, as they must, since the root files did.

### B1 — an ADR records what `factory.py` is for

- Check: `docs/adr/0054-front-door-routes-humans.md` exists; detector D
  cross-checks every ADR against its index row and status.
- Evidence:
  ```
  docs/adr/README.md index row (link markup omitted — a relative ADR link
  quoted from this directory would not resolve):
    0054 | The front door routes humans, not files | provisional
  gates: 0 problem(s)
  ```
- Result: PASS. The ADR records the decision, the two routes that lost,
  and the payload cost that decided it. Status is `provisional` — decided
  inside an autonomous loop without user confirmation, which is what that
  status is for.

### B2 — the module and its test agree with the ADR

- Check: `python3 -m unittest tests.test_factory_cli.TestVerbTableIsDerived -v`;
  `grep -c argv0 tests/test_factory_cli.py`; and a mutation — mislabel
  `lint` as an `argv` verb and confirm the pin catches it.
- Evidence:
  ```
  test_each_row_declares_the_convention_its_main_accepts ... ok
  test_every_cli_bearing_root_module_has_exactly_one_verb ... ok
  test_the_verb_is_the_module_name_hyphenated ... ok
  Ran 3 tests in 0.067s
  OK

  argv0 occurrences in tests/test_factory_cli.py: 0

  (mutation: "lint": ("lint", "argv"))
  FAIL: test_each_row_declares_the_convention_its_main_accepts (verb='lint')
  AssertionError: 'argv' != 'bare'
  ```
- Result: PASS. All three columns of the verb table are now derived from
  the root rather than trusted, the dead branch is gone, and the pin
  demonstrably fails on a wrong row.

### C1 — the truncation policy no longer disagrees between callers

- Check: `python3 -m unittest tests.test_work_queue.TestReadyIssueNumbers -v`,
  plus `grep -n "return None, \[" work_queue.py` to confirm all three
  untrustworthy legs share one sentinel. (The end-to-end behavior is the
  centerpiece section above; this is the unit-level evidence.)
- Evidence:
  ```
  test_a_full_window_is_refused_rather_than_trusted ... ok
  test_an_unreachable_tracker_is_a_problem_not_an_empty_queue ... ok
  test_it_asks_for_open_ready_labelled_issues ... ok
  Ran 3 tests in 0.000s
  OK

  181:        return None, [f"wq: gh issue list failed: {gh_detail(err)}"]
  183:        return None, [f"wq: gh issue list {suffix}"]
  186:        return None, [f"wq: gh issue list {window}"]
  ```
- Result: PASS. All three untrustworthy legs return the same `None`
  sentinel — the contract `sweeps.live_issues` has carried since it was
  written. The two callers with the same hazard now answer it the same
  way.

## Failures

None. Nothing routes back to Implement.

## Not verified

- **The "green against unmodified `<file>`" clauses in A1 and A6.** Those
  were true at implement time and are unrepeatable now without reverting
  the fold. Stated as a narrowing above rather than passed silently.
- **Real `gh` behavior.** Every listing case is an injected runner. What
  is verified is how the tools *read* a truncated or failed listing, not
  that gh truncates at exactly 100 — that is `cli.full_window`'s rule and
  its own tests.
- **The stamped-repo path.** The payload copies are byte-verified against
  the root through the manifest, but no product repo was stamped and run
  in this verification. Detector E plus `tests/test_factory_init.py` are
  the standing pins for that; this run did not exercise a live stamp.
- **The two design gaps.** The gh-silence seam and the `protocol.py`
  split are decisions recorded in `architecture.md`, not code — there is
  nothing built to verify. The split's payload win (~250 lines) is
  therefore unmeasured, because it has not been implemented.
- **`factory.py` as a human tool.** ADR-0054's claim that its callers are
  humans is a decision, not a behavior; `factory.py help` was not driven
  interactively here. Its dispatch and index remain covered by
  `tests/test_factory_cli.py`.
