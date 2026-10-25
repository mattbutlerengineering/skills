---
stage: review
run: maintenance:a-long-line-stalls-the-gate
date: 2026-10-24
assumptions:
  - "Major 1 is fixed in-stage, not deferred. The skill lets only the user defer a major, and an autorun has no user to ask, so the default is fix. The fix stays inside the brief's chosen shape (a fixed window before match.start()); only the width rule changes. The brief's 'smallest width that keeps every existing fixture green' rule is what produced the fail-open width, so Review sets the width from the grammar instead and records why."
  - "The semantics-preserving linear read (a reverse read of the prefix that finds the last three tokens before each match, then searches only those) is not adopted. The brief rules it out unless the window breaks a fixture, and at 64 no fixture, test or tracked line diverges. It stays the named fix in the lean: marker and the ADR-0108 amendment."
  - "Severity of Major 1 is major, not critical: the gate loosens only for a stale Summary written in a count wider than 17 characters, and no tracked artifact has one (the sweep below). It is not minor because it is a silent fail-open change to a fail-closed rule, reached by ordinary English and by the existing fixture with emphasis added, in a change whose brief promised no verdict change."
  - "ADR-0108 is provisional and its Consequences already carry dated amendment lines, so the window's remaining limit is recorded the same way, as a Consequences line; the Decision section is not touched."
  - "The review's probes live in the session scratchpad, not the repo: review_probe.py and review_sweep.py under /private/tmp/claude-501/-Users-mbutler-github-skills/6bbff111-edf5-461e-a66b-9d173bf4dafa/scratchpad/. The origin/main side is `git show origin/main:gates.py` written there as gates_main.py and loaded with importlib."
---

# Review: a long line stalls the gate

## Scope

`git diff origin/main...HEAD` (origin/main `ec8159f`, the merge base;
HEAD `9f777f6` before this review), five commits from `85e1558` (brief)
to `9f777f6` (verify). The code is `d093dfb`: `SUMMARY_ZERO_COUNT_WINDOW
= 17` and its comment in `gates.py`, `_names_unknown` searching from
`max(0, match.start() - SUMMARY_ZERO_COUNT_WINDOW)`, the byte-identical
payload copy `factory/templates/tools/factory/gates.py`, the manifest
pin, and the timing pin `test_a_long_zero_count_line_reads_in_linear_time`
(16 lines added to `tests/test_gates.py`, 0 deleted). The rest is the
`docs/backlog.md` claim and this run's artifacts.
`.claude-plugin/plugin.json` is not in the diff (ADR-0095).

Predecessor `verification.md` exists: 8 of 8 PASS, with one width
finding handed to Review.

## Maintenance-run checks

- **The regression test pins the reproduction.** The timing pin runs
  Capture's worst case (`"0 not run, " * 4000`, 44 kB) under a 1.0 s
  bound and asserts the verdict `False`. Verify replayed it at 5.97 s
  on the pre-fix module. Not re-run here.
- **The producing boundary.** The one consumer of the window is
  `_names_unknown`, called once per unfenced line from
  `verification_sections` (`gates.py`); no other reader of
  `SUMMARY_ZERO_COUNT` exists. The pin proves the time is gone, not
  that the verdict is kept: the window can only remove a zero-count
  match, never create one (the leading `(?<![\w.])` still sees the text
  before `pos`, and every start at or after `pos` is tried as
  before), so every divergence it causes runs one way, toward naming. That is Major 1.
- **Related cleanup that remains.** The exact linear read (Major 1's
  alternative), recorded in the `lean:` marker and ADR-0108 rather than
  built, per the brief.

## Probes

One Summary over the test fixture's two criteria (one evidenced PASS,
one `- Result: NOT RUN — needs a second account.`), through
`gates.evidence_problems`. `REFUSED` is H's roll-up string, the correct
verdict for every zero count below. `main` is origin/main's `gates.py`
(whole-prefix read); `w=` sets the branch's window:

```
summary                                    main     w=17  w=32  w=64
'1 PASS; zero criteria were skipped.'      REFUSED  pass    REFUSED REFUSED
'1 PASS; no criteria were **skipped**.'    REFUSED  pass    REFUSED REFUSED
'1 PASS; no requirements were skipped.'    REFUSED  pass    REFUSED REFUSED
'1 PASS; nothing further was skipped.'     REFUSED  pass    REFUSED REFUSED
'1 PASS; zero criterion was skipped.'      REFUSED  pass    REFUSED REFUSED
'1 PASS; no criteria  were skipped.'       REFUSED  pass    REFUSED REFUSED
'1 PASS; 0 acceptance were NOT RUN.'       REFUSED  pass    REFUSED REFUSED
'1 PASS; no criteria were skipped.'        REFUSED  REFUSED REFUSED REFUSED
'1 PASS; nothing else was skipped.'        REFUSED  REFUSED REFUSED REFUSED
'1 PASS, 0 FAIL, 0 NOT RUN.'               REFUSED  REFUSED REFUSED REFUSED
'1 PASS; criterion nine was not run.'      pass     pass    pass    pass
'1 PASS, 1 NOT RUN.'                       pass     pass    pass    pass
spaces 17 main names: False w17 names: True
spaces 64 main names: False w17 names: True
spaces 200 main names: False w17 names: True
```

The last three lines are `"0" + " " * k + "NOT RUN"`: the grammar's
`\s+`, word and `[\s*_`]*` runs are unbounded, so a SUMMARY_ZERO_COUNT
match has no maximum length and any fixed window changes some verdict.
The question is only which inputs, and that it fails open.

## Findings

### Major: the 17-character window fails open on ordinary one-word zero counts

- Scenario: a judged `verification.md` with a criterion disclosed NOT
  RUN and a stale Summary "1 PASS; zero criteria were skipped." (or "no
  criteria were **skipped**", "no requirements were skipped", "nothing
  further was skipped", the probe above). The count is 18 to 22
  characters, the window reads only the last 17, the match fails, so
  `_names_unknown` returns True and H passes the Summary. origin/main
  refuses all of them. This loosens ADR-0107's fail-closed roll-up
  ("unknown never rolls up to pass") and contradicts ADR-0108's
  Decision, whose zero count admits any one word plus `was`/`were` and
  emphasis; the brief's own premise was "no wrong verdict, only time".
  The cause is the brief's width rule: "the smallest width that keeps
  every existing fixture green" lands on the widest fixture exactly
  (`len("no criteria were ") == 17`), so adding emphasis to that very
  fixture already fails open. No tracked artifact has the shape
  (Verify's sweep, and the one below at 64).
- Standard: none
- Decision: fixed in `dc1570f`. Test first:
  `test_a_wide_zero_count_over_a_disclosure_stays_refused` asserts H's
  exact roll-up string for five wide counts, the last one built on the
  longest English dictionary word. RED on `d093dfb`'s window:
  ```
  FAIL: ... (summary='1 PASS; zero criteria were skipped.')
  FAIL: ... (summary='1 PASS; no criteria were **skipped**.')
  FAIL: ... (summary='1 PASS; no requirements were skipped.')
  FAIL: ... (summary='1 PASS; nothing further was skipped.')
  FAIL: ... (summary='1 PASS; nothing pneumonoultramicroscopicsilicovolcanoconiosis were **skipped**.')
  Ran 1 test in 0.002s
  FAILED (failures=5)
  ```
  The width is now derived from the grammar, not the fixtures: 64 =
  `len("nothing")` + 1 + 45 (the longest dictionary word) + 1 +
  `len("were")` + 6 for spaces and emphasis. The new test's last
  subtest needs at least 61 (`17 True, 60 True, 61 False, 64 False`
  for `_names_unknown` on it), so it pins the derivation, not just the
  four short shapes. Payload copied (`cmp` identical), no stray
  `.orig`/`.rej`, `python3 factory_init.py update-manifest` printed
  `factory-init: 0 problem(s)`. No existing test edited. The comment at
  the constant and ADR-0108's Consequences (a dated amendment line) say
  what the window still cannot see.

  Alternatives weighed. A width of 32 restores Verify's example but
  still cuts "nothing further was **skipped**"-style counts with a long
  word; 64 costs nothing measurable. The exact linear read (reverse the
  line once, match the last three tokens and trailing markers before
  each match, search only that span) keeps every verdict, but the brief
  rules it out unless a fixture breaks, and at 64 none does. It is the
  named next step in the `lean:` marker and the ADR line.

  After the fix, the probe's sweep over every tracked markdown line,
  origin/main against the branch, and the worst-case timing:
  ```
  window: 64
  new len=22000 -> False in 0.0098s
  new len=44000 -> False in 0.0197s
  new len=110000 -> False in 0.0489s
  files=1012 lines=132007 differing=0
  ```
  The one line that differed at 17 (this run's defect.md frontmatter)
  no longer differs, and the growth is still linear.

### Minor: a zero count wider than 64 characters still names

- Scenario: "1 PASS; 0" followed by 64 or more spaces or emphasis markers,
  then "NOT RUN", over a disclosed criterion: the window cuts the count
  and H passes it (the `spaces` probe lines). Fail-open, as Major 1,
  but only through a run of whitespace or markers no hand-written
  Summary holds.
- Standard: none
- Decision: deferred. Recorded as an accepted limit in ADR-0108's
  Consequences and in the `lean:` marker at `SUMMARY_ZERO_COUNT_WINDOW`,
  with the reverse read as the fix on a real artifact that uses one.

## Passes with no findings

- **Correctness:** clean apart from Major 1 and the Minor. The window's
  edge invents no word boundary (lookbehind at `pos` sees earlier text,
  Capture's check), `max(0, ...)` handles a match near the line start,
  and `endpos` is unchanged, so `$` still anchors at the match.
- **Timing pin:** not flaky on this evidence. At width 64 it ran ten
  times at 0.020 to 0.024 s against its 1.0 s bound (about 45 times
  headroom), and `run_tests.py` runs it under 8 parallel workers green.
  A quadratic read takes 5.9 s on this machine, so the bound still
  catches a regression on a runner up to about 6 times faster.
- **Design:** clean. The width is a named constant beside the grammar
  it bounds, one owner, read only by `_names_unknown`; `python3
  one_owner.py` reports nothing about it.
- **Security:** clean. Pure functions over artifact text, no I/O,
  stdlib only (standards slug `stdlib-only`, advisory, met).
- **Complexity:** clean. A three-line call change and one constant. The
  diff's one `lean:` marker names its ceiling (a count wider than 64)
  and its trigger (a real artifact that uses one).
- **ADR compliance:** `adr_status.py` reports ADR-0107 `partial`,
  ADR-0108 `provisional`, ADR-0095, ADR-0050 and ADR-0021 `active`.
  ADR-0108's Decision was broken by the 17 window (Major 1, graded on
  its own correctness scenario, not on the provisional ADR) and is
  honoured at 64 for every one-word count; its Decision section is
  untouched and the limit is a dated Consequences line, as its earlier
  amendments were. ADR-0095: `plugin.json` untouched. ADR-0050: the
  payload mirror is identical and manifest-pinned. Other live ADRs are
  out of scope (the diff touches no routing, release, eval or tracker
  surface).
- **Domain passes:** none selected. No changed path matches payments,
  migrations or dependencies; `factory/manifest.json` is a checksum
  pin.

## Final checks (after `dc1570f`)

```
$ python3 run_tests.py
tests: 3808 tests across 118 modules in 30.2s on 8 workers, 0 problem(s)
$ python3 lint.py
lint: 0 problem(s) across 34 skills
$ python3 kb.py drift
drift: 0 problem(s)
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
```

## Verdict

Ready for Ship. All five passes, the timing-pin check and the
maintenance-run checks ran; none was skipped or left unknown, and no
domain pass was selected. No critical finding. The one major, the
fail-open width, is fixed test-first in `dc1570f` with the four checks
green after; the window is now 64 and defect.md carries a dated note
that its 17 is superseded. One minor stays deferred with its reason:
a count wider than 64 characters still names, recorded in ADR-0108 and
the `lean:` marker.
