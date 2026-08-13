---
stage: review
run: maintenance:deepening-cli-seams
date: 2026-08-13
assumptions:
  - "review depth set from the brief's blast radius: the changed tools are MIRRORS entries that ship into every stamped repo, so this is a full three-pass review rather than the light pass a patch bump would get (the protocol's Run scale section)"
---

# Review: the deepening run's three landed changes

## Scope

The run's whole diff, working tree against `HEAD` (nothing is committed):

- `work_queue.py` — the report-seam fold, `compose_plan`'s rename, and the
  untrusted-listing refusal in `ready_issue_numbers`
- `budget_guard.py` — the two record legs folded onto `cli.report`
- `factory.py` + `tests/test_factory_cli.py` — ADR-0054's derived
  convention pin and the dead `argv0` branch
- `tests/test_work_queue.py`, `tests/test_budget_guard.py` — the new
  `ReportContract` subclasses and leg pins
- `docs/adr/0054-front-door-routes-humans.md` and its index row
- `factory/manifest.json` + the two mirrored payload copies

Not re-verified here: everything `verification.md` already demonstrated.
This pass looked for what Verify could not — a criterion can pass while the
thing it pins is the wrong thing.

## Findings

### Major: `python3 factory.py charter-replay` could not run at all

- Scenario: `VERBS["charter-replay"]` declared the `bare` convention, so
  `factory.main` called `charter_replay.main()` with no argument. That
  main's signature is `main(argv=None)`, and `parser.parse_args(None)`
  falls back to `sys.argv[1:]` — under the front door, `["charter-replay"]`.
  argparse has no positional to absorb it. Driven, with every expensive
  path stubbed:

  ```
  $ python3 factory.py charter-replay
  usage: factory.py [-h] [--cases CASES] [--model MODEL] [--timeout TIMEOUT]
                    [--only ONLY] [--transcripts TRANSCRIPTS] [--record]
  factory.py: error: unrecognized arguments: charter-replay
  SystemExit: 2
  ```

  The same row made the tool's six flags unreachable from the door: a
  `bare` verb given arguments is refused, so `factory.py charter-replay
  --transcripts recorded.json` printed `factory: charter-replay takes no
  arguments`. The one verb whose flags matter most — `--transcripts` is
  the free, offline scoring path — was the one that could not carry them.
- The contract that decayed: `architecture.md` states each row's
  convention "equals what that module's `main` signature actually
  accepts," with "a row whose convention is wrong" listed as a build
  failure. It was not. The new pin derived `takes_argv` from
  `p.default is p.empty`, so an argv slot carrying a default read as
  *no slot* — the pin agreed with the wrong row. ADR-0054's consequence
  "a changed `main` signature fails the build" was, as written, untrue
  for exactly the case that was already broken.
- Age: the row predates this run (`factory.py` landed 2026-08-10, #246).
  This run is where it belongs anyway — B2's criterion is that the module
  and its test agree with the ADR, and ADR-0054 decided the door's callers
  are humans. This was the verb no human could use.
- Decision: **fixed**, test-first. The derivation now keys on the slot's
  existence, not on callability:

  ```
  positional = [p for p in inspect.signature(...).parameters.values()
                if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
  if positional:
      self.assertEqual(positional[0].name, "argv")
  self.assertEqual(style, "argv" if positional else "bare")
  ```

  Watched it fail on one verb and one verb only before the row moved to
  `("charter_replay", "argv")`:

  ```
  FAIL: test_each_row_declares_the_convention_its_main_accepts (verb='charter-replay')
  AssertionError: 'bare' != 'argv'
  FAIL: test_a_bare_verb_reads_nothing_from_the_process_argv (verb='charter-replay')
  - ['argv']
  + [] : charter-replay is routed bare but its main takes parameters;
         factory.main() would leave them to sys.argv
  ```

  A second test (`test_a_bare_verb_reads_nothing_from_the_process_argv`)
  now states the rule as a rule: a `bare` row's main must take no
  parameters at all. And because every root main that has a positional
  spells it `argv`, the pin asserts that name too — so a future
  `main(root=None)` fails rather than silently reclassifying.

  After, both invocations reach the tool's own code (stub returns 1):

  ```
  $ python3 factory.py charter-replay                    -> returned 1
  $ python3 factory.py charter-replay --only architect   -> returned 1
  ```

  Note the behavior this restores: `factory.py charter-replay` with no
  flags now starts a **live, paid** replay, exactly as `python3
  charter_replay.py` does. That is parity, and parity is the front door's
  whole contract — but it is a real change from "fails safely at
  argparse," and worth knowing before typing it.

### Major: an untrusted listing still announced a batch size

- Scenario: `ready_issue_numbers` refuses a full window and `main` holds
  every row back — but the non-JSON leg still rendered the plan header
  first, so the output opened with a count of a queue the tool had just
  declared it could not see:

  ```
  wq: 0 work order(s) ready to run in parallel (wip_cap 3)
  wq: gh issue list returned a full 100-entry window — older entries are invisible; ...
  wq: 1 problem(s)
  ```

  A reader skims the first line; a CI summary or a pasted excerpt often
  *is* the first line. "0 work order(s) ready" is precisely the sentence
  `ready_issue_numbers`'s own docstring refuses to let a broken listing
  produce — "'nothing is ready' and 'I could not ask' must not look the
  same to the caller, or a broken token reads as a drained backlog." The
  refusal closed that at the function boundary and left it open at the
  CLI boundary.
- Decision: **fixed**, test-first
  (`test_an_untrusted_listing_claims_no_count_either`, which pins the
  whole stdout, not just an absence). The plan is rendered only over a
  listing the tool trusts:

  ```
  $ python3 work_queue.py plan    # gh returns a FULL 100-entry window
  wq: gh issue list returned a full 100-entry window — older entries are invisible; raise the window or narrow the query
  wq: 1 problem(s)
  [exit 1]

  $ python3 work_queue.py plan    # gh returns a short listing containing #999
  wq: 1 work order(s) ready to run in parallel (wip_cap 3)
    WO-0001  size:S  $5.00  issue #999  docs/features/demo/breakdown.md:1
    projected $5.00 on top of $0.00 spent this month
  wq: 0 problem(s)
  [exit 0]
  ```

  The trustworthy case is unchanged, which is what makes this a fix and
  not a mute button.

### Minor: the refusal names a remedy the operator cannot reach

- Scenario: with ≥100 open `wo:ready-for-agent` issues, `work_queue plan`
  now plans nothing at all and advises "raise the window or narrow the
  query." Neither is a runtime option — `LIST_ARGS` and `LIST_WINDOW` are
  module constants, and in a stamped repo the file is a mirrored payload
  copy, so the remedy is a code edit in someone else's tree. The factory
  stalls until a human patches a tool.
- Worth noting alongside: work_queue's 100 is the tightest of the three
  windows in the codebase (`sweeps` 500, `label_sync` 1000), and it is now
  the only one on a hard-stop path.
- Decision: **deferred.** The message belongs to `cli.full_window`, shared
  by five call sites, and giving it a runtime escape hatch is a seam-level
  change — a `--limit` flag or a config key — that would be smuggled in
  under a review. The condition is also still latent: the brief records it
  as unobserved, needing ≥100 open ready-labelled issues, and the repo has
  nothing near that. Stalling is the safe direction to fail. Routed to the
  backlog rather than fixed here.

### Minor: `architecture.md`'s design is four-fifths unimplemented, by design

- The gh-listing component says "each site states its window policy in one
  line and a test pins it," across five sites. The breakdown carried one
  item (C1) covering `work_queue.ready_issue_numbers` only; the other four
  declarations were routed to the design-gap list and never decomposed.
  `verification.md` records this under "Not verified," so nothing is
  overclaimed — but Ship should not describe the run as having landed the
  gh-listing decision, only the one site that disagreed by accident.
- Decision: **deferred**, and named here so the ship note inherits the
  narrower claim. The remaining declarations plus ADRs 2 and 3 from
  `architecture.md`'s recommendation list are the natural next run.

### Minor: the front door miscounted itself

- `factory.py`'s module docstring — which is what `python3 factory.py`
  prints as usage — opened "Fifteen root modules carry a CLI." The
  mechanical scan finds fourteen, and `VERBS` has fourteen rows; fifteen
  is the count of *mirrored* payload files, a different set. `ADR-0054`
  and `architecture.md` had inherited the same number.
- Decision: **fixed** (three one-word edits). Trivial, but it is printed
  to users and it is the kind of number a later reader does arithmetic
  with — ADR-0054's Route A argument turns on "a fifteenth mirrored tool,"
  and having both fifteens mean different things invites a wrong merge of
  the two claims.

## Passes with no findings

- **Security.** No new input surfaces. Both tools' external I/O still goes
  through injected runners (`run=`) with no shell interpolation; the new
  `importlib.import_module` call takes module names from the static
  `VERBS` table, never from user input; no secrets, no new file writes,
  and the cost ledger's append-only path is untouched. Problem strings
  carry `gh`'s own stderr via `cli.detail`, which was already the
  convention and leaks nothing new.
- **Correctness of the seam fold itself.** `cli.report` returns
  `1 if problems else 0` and prints problems above the summary — the
  exact sequence all four folded legs previously hand-rolled, including
  the config leg's unconditional `return 1` (reached only with a non-empty
  list, so the computed code is identical). Exit codes and output order
  are unchanged on every leg. The `--json` carve-out is honest about
  being a carve-out and is held to the seam's grammar by
  `test_the_json_summary_is_the_seam_s_own_grammar`.
- **Design against the codebase's patterns.** The `None` sentinel matches
  `sweeps.live_issues`'s existing contract rather than inventing a
  second one; `compose_plan`'s rename frees the seam's name in the file's
  namespace; the `ReportContract` subclasses use the existing
  `tests/cli_contract.py` seam instead of a new harness. Stdlib only. No
  new shared module — correctly, since the run's own analysis concluded
  the gh-listing rule is already shared.

## Verdict

**Ready to ship, with the two majors fixed in this pass and three minors
deferred with reasons.** The gate after the fixes:

```
Ran 1107 tests in 15.074s
OK
lint: 0 problem(s) across 23 skills
gates: 0 problem(s)
selftest: ok
factory-init: 0 problem(s)      (manifest regenerated; work_queue.py is a MIRRORS entry)
```

Two caveats the ship note should carry rather than bury:

1. `factory.py charter-replay` now runs a paid replay instead of failing
   at argparse. That is the correct behavior and it is new.
2. The run landed the front-door decision and one of five gh-listing
   declarations. The other four, plus ADR-0054's two companion ADRs, are
   open work — not silent debt, but not shipped either.

Nothing routes back to Implement.
