---
stage: capture
run: maintenance:a-long-line-stalls-the-gate
date: 2026-10-24
re-entry: implement
origin: docs/backlog.md seed (from maintenance:a-zero-count-names-nothing), detector H's zero-count read is quadratic in line length
assumptions: ["Capture: a defect brief, not a condition brief. The brief files it under Defect, and the verdict is never wrong, only slow; the skill offers the two variants with no default, and the brief's heading is taken as the answer", "Capture: the work items' order and shape (a timing pin first, then the window as a named constant beside SUMMARY_ZERO_COUNT, then the payload copy and manifest regen) come from the orchestrator's dispatch and the brief's Defect and Blast radius sections, not from a separate Owner answer", "Capture: the timing pin's form (a wall-clock bound, or a bound that does not depend on the clock) is left to Implement; the brief says test first and does not name the form"]
---

# Defect: a long line stalls the gate

## Defect (or Condition)

Detector H's roll-up read takes time quadratic in the length of a line.

`gates._names_unknown` (`gates.py:1171`) runs
`SUMMARY_ZERO_COUNT.search(line, 0, match.start())` once for every
`SUMMARY_UNKNOWN_TERM` match in the line. Each search scans the whole
prefix before the match, because `SUMMARY_ZERO_COUNT` (`gates.py:265`)
is anchored at its end (`$` at `endpos`) and not at its start. So a line
with *n* matches costs about *n* prefix scans. `verification_sections`
(`gates.py:1180`) calls it on every unfenced line of every section, not
only a Summary's.

- **Observed.** A 22 kB line of zero-preceded matches takes 1.5 s, and
  a 110 kB line takes 37 s (measurements below). Five times the length
  costs about 24 times the time.
- **Expected.** The time grows linearly with line length. The verdict
  is the same for every line any existing test or fixture uses. A zero
  count is only ever a few words long, so the search only needs to look
  at a short window of text before `match.start()`, not the whole
  prefix.

No verdict is wrong today. The cost is time only.

## Reproduction / Evidence

Measured for real on 2026-10-24 at `85e1558`, outside the repo. A
throwaway timing script in the session scratchpad imports this tree's
`gates.py` and times `gates._names_unknown`, and then
`gates.verification_sections` on a minimal artifact whose `## Summary`
holds the line. The line is `0 not run, ` repeated, so every match
follows a zero. Verbatim output:

```
_names_unknown zero-preceded '0 not run, ' len=22000 matches=2000 -> False in 1.530s
_names_unknown zero-preceded '0 not run, ' len=110000 matches=10000 -> False in 36.807s
_names_unknown bare 'not run, ' len=21996 matches=2444 -> True in 0.000s
_names_unknown bare 'not run, ' len=109998 matches=12222 -> True in 0.000s
verification_sections zero-preceded len=22000 -> names_unknown=False in 1.466s
verification_sections zero-preceded len=110000 -> names_unknown=False in 36.633s
```

A second run of the same probe at two more lengths:

```
1131 0.0039s
44000 5.8577s
```

What the numbers show:

- **The worst case is a line whose every match follows a zero.** The
  `any(...)` in `_names_unknown` stops at the first match that is not
  zero-preceded. So a bare "not run" line returns at its first match in
  no measurable time, at either length. Only a line of zero-preceded
  matches (or a long run of them before the first naming one) pays for
  every prefix.
- **`verification_sections` costs the same as `_names_unknown`**
  (1.47 s and 36.6 s). The rest of the per-line parse adds nothing
  measurable, so `_names_unknown` is the whole cost.
- **The growth is quadratic.** Going from 22 kB to 44 kB to 110 kB
  multiplies the time by 3.8 and then 6.3: 24 times in all for 5 times
  the length.
- **The seed's numbers hold up.** It measured 1.57 s and 39 s, and this
  run measured 1.53 s and 36.8 s.

**Main tree.** There are 102 tracked `verification.md` files (`git
ls-files`). The longest line is line 11 of
`docs/features/first-live-dispatch/verification.md`: 1131 characters
(1132 bytes, since it holds one multi-byte character, which is the
seed's 1132). At that length the worst-case probe takes 3.9 ms. **This
run is prevention.** Nothing on main is slow today.

## Root-cause hypothesis

Hypothesis: the zero-count read is given the whole prefix when it only
needs the end of it. `_names_unknown` passes `0` as `pos`, so each
search tries every start position before `match.start()`, and its `$`
only rejects a candidate after it has been tried. A zero count is
bounded in practice: one zero word, at most one word, an optional
`was`/`were`, and separators. But the regex does not bound
`[^\W\d_]+`, `\s+` or the trailing `[\s*_`]*`, so a fixed window is a
small change in meaning only for a zero followed by a very long word or
a long run of spaces or emphasis.

A useful fact for Implement, checked on this machine's Python: a
lookbehind at the `pos` given to `search` still sees the text before
`pos` (`re.compile(r'(?<![\w.])0').search('x0', 1)` returns `None`). So
starting the search at `match.start() - window` does not invent a word
boundary at the window's edge. `SUMMARY_ZERO_COUNT`'s leading
`(?<![\w.])` keeps judging the real text before it.

## Blast radius

- **Code.** `gates.py` and its payload copy
  `factory/templates/tools/factory/gates.py`, which is byte-identical
  today (`cmp`) and manifest-pinned. Stamped repos get the change on
  their next payload update.
- **Behaviour.** Time only. Any repo whose `verification.md` holds one
  very long line of zero-preceded unknown words pays seconds to minutes
  per line on every detector H run, locally and in CI. No verdict
  changes for any shape an existing test pins. The window can change
  the verdict only for a zero count wider than the window, which is the
  tuning question below.
- **Who.** No artifact in this repo is affected: the longest line
  (1131 characters) costs 3.9 ms. A stamped repo hits the slow path only
  with a long generated or pasted line in an artifact. Severity: low.
- **Since.** #1018 (`41d407a`), which added `_names_unknown` and
  `SUMMARY_ZERO_COUNT` (ADR-0108).

## Ruled out

- **Re-entry at Architect.** The fix is one function and one constant
  in one module, with no seam or ownership question (the Owner, in the
  brief).
- **A linear rewrite that keeps the exact meaning** (for example, one
  reverse scan per match, or a single combined pattern). Deferred, per
  the brief, unless the window breaks an existing fixture.
- **The bare-word case.** A line whose first match names the kind
  already returns at once. Only zero-preceded runs are slow (the
  measurements above).
- **The rest of `verification_sections`.** Its time equals
  `_names_unknown`'s, so no other per-line regex is the cause.
- **In flight.** The check ran on 2026-10-24 and nothing matches.
  `gh pr list --state open` lists three PRs (#1073, #1074, #1077), and
  none of them changes a file whose path contains `gates`.
  `gh issue list` searches for `names_unknown`, "quadratic",
  `SUMMARY_ZERO_COUNT` and "long line" returned only #1064 and #181,
  neither about this. `git log --all -S _names_unknown -- gates.py`
  finds only `4cc2ede` and `41d407a`, the commits that introduced it.
  No other local branch matches `*long-line*`.

## Work items

Re-entry is Implement, so these checkboxes are the run's breakdown.

- [ ] **Timing pin first (RED)**: in `tests/test_gates.py`, beside the
  `_names_unknown` coverage in `TestEvidenceRollUp`
  (`tests/test_gates.py:2823`), add a test that runs `_names_unknown`
  (or `verification_sections`) on a long line of zero-preceded matches,
  `0 not run, ` repeated to at least 22 kB, and asserts both the
  verdict (`False`) and a bound loose enough never to flake on a slow
  CI runner but far below the measured 1.5 s. Implement picks the form
  of the bound and records it.
  - Accept: the test fails on `85e1558`'s `gates.py` and passes after
    the fix. Its verdict half passes both before and after.
- [ ] **The bounded window**: add a named constant beside
  `SUMMARY_ZERO_COUNT` in `gates.py` for the width of the zero-count
  window, with a comment saying why it is bounded. Make `_names_unknown`
  search `SUMMARY_ZERO_COUNT` from `max(0, match.start() - <width>)`
  instead of `0`. Choose the smallest width that keeps every existing
  zero-count test and fixture green, and log the chosen width under
  `assumptions:` in this file. Update `_names_unknown`'s docstring and
  the `SUMMARY_ZERO_COUNT` comment if they describe the search range.
  Stdlib only.
  - Accept: the timing pin goes GREEN, and `python3 -m unittest
    tests.test_gates` passes with no existing test edited.
- [ ] **Payload mirror and manifest**: copy `gates.py` to
  `factory/templates/tools/factory/gates.py`. Delete any stray
  `.orig`/`.rej` files first, then run `python3 factory_init.py
  update-manifest` and commit the manifest.
  - Accept: `cmp` shows the two files are identical, and detector E is
    clean.
- [ ] **Backlog claim**: the claim on `docs/backlog.md` line 131 landed
  with this capture commit. Confirm it is still there and well-formed,
  then check this box.
  - Accept: the seed line ends in
    `(claimed: maintenance:a-long-line-stalls-the-gate)`.
- [ ] **Whole-repo checks**: `python3 run_tests.py`, `python3 lint.py`,
  `python3 kb.py drift`, and `python3 gates.py && python3 gates.py
  --selftest`.
  - Accept: all pass, and `gates.py` reports `gates: 0 problem(s)` on
    the real tree.

## Notes

- 2026-10-24 (Capture): the seed and the brief say 1132 for the longest
  line. That is a byte count. In characters it is 1131, which is what
  `_names_unknown` sees.
- 2026-10-24 (Capture): no ADR is planned. The brief names none, and
  the fix changes how long the rule takes, not what it decides. The
  zero-count grammar's accepted limits (the seed at `docs/backlog.md`
  line 130) are a separate seed and out of this run's scope.
- Next stage: Implement.
