# Autorun brief: the-selftest-cannot-see-a-dodge

Not an artifact. Written 2026-10-18 by the orchestrator. The Owner invoked
`/idea-to-prod:autorun` with no description. No run was mid-pipeline, so
the Owner answered three questions one at a time in session, each taking
the recommended option:

1. What to drive: "Dodge rows + zero (Recommended)". That is backlog line
   124, the selftest dodge-shape rows for H, O and M (from:
   session:2026-10-17), plus one zero-count row for H's roll-up. Capture
   of the a-zero-count-names-nothing run noted that row as out of scope
   in its defect.md Notes.
2. Release: "Prepare and stop (Recommended)".
3. Operate: "Skip (Recommended)".

Everything else below is the orchestrator's reading of the seed and the
code, and is marked as such. A stage that needs an answer this brief does
not hold applies the autorun rule: take a skill-supplied default and log
it, or else stop and surface.

## Run scale

Maintenance (fix) run at `docs/fixes/the-selftest-cannot-see-a-dodge/`,
entering at Capture. It is a defect in the gate's self-check. A stamped
repo runs only `python3 tools/factory/gates.py --selftest`, not this
repo's `tests/`, and that selftest exercises none of the three dodges
fixed on 2026-10-17 and 2026-10-18 (#1002, #1018). So a payload change
that reintroduced any of them would leave every stamped repo reporting
`selftest: ok`.

## Capture inputs

- **What is broken.** `gates_selftest.py` (payload copy
  `factory/templates/tools/factory/gates_selftest.py`) has no fixture
  where:
  - O's PRD, M's defect.md or H's verification.md carries a quoted
    post-cutoff `date:` (for example `date: "2026-10-20"`). Its O and M
    fixtures date themselves `{gates.COVERAGE_ADOPTED}`,
    `{gates.CAPTURE_ADOPTED}` or `2026-01-01`.
  - a verification.md Summary counts "0 NOT RUN" over a criterion
    disclosed as NOT RUN. The `rolledup` fixture
    (`evidence_honesty_defect_fixture`) has no zero-count row.
- **Reproduction.** Capture must reproduce this for real, not cite the
  seed. In a scratchpad copy of the repo (never the working tree),
  revert each fix in turn:
  - put back the raw `isinstance(date, str) and date < CUTOFF` compare
    in `gates._grandfathered`'s callers, or make `_grandfathered` compare
    the raw string;
  - make `_names_unknown` ignore the zero check.

  Then run `python3 gates.py --selftest` and quote that it still prints
  `selftest: ok`, while `python3 -m unittest tests.test_gates` fails.
  That is the gap: the repo's tests see the regression and the shipped
  selftest does not.
- **Evidence it bites today.** None observed. This is prevention for
  stamped repos, which upgraded to these fixes in 0.21.0 (#1026). Say
  so plainly.
- **Root cause (hypothesis).** The fixes added tests to `tests/` but no
  selftest rows, and nothing requires a gate rule's dodge test to have a
  selftest twin.
- **Blast radius.** `gates_selftest.py` and its payload copy
  (manifest-pinned). The selftest runs offline and is pure. No gate
  behaviour changes. Each new row must fail against the reverted code and
  pass against today's.
- **Re-entry depth.** Orchestrator's reading: `re-entry: implement`.
  Adding fixture rows follows the existing pattern in `selftest()`. If
  Capture finds a real design question (for example, whether the
  selftest should mutate-check itself), it chooses `architect` and logs
  why.

## Scope

In:
- one selftest row per detector (O, M and H) with a quoted post-cutoff
  `date:` that the detector must refuse;
- one H roll-up row: a Summary reading "N PASS, 0 FAIL, 0 NOT RUN" over a
  disclosed NOT RUN criterion, which H must refuse with the roll-up
  problem;
- proof by mutation that each new row turns the selftest red when its fix
  is reverted (scratchpad copies only);
- the payload mirror and `python3 factory_init.py update-manifest`
  (delete stray `.orig`/`.rej` first);
- claiming backlog line 124:
  `(claimed: maintenance:the-selftest-cannot-see-a-dodge)`.

Out:
- any change to `gates.py` behaviour;
- a meta-rule requiring selftest twins (seed it if Capture thinks it
  matters);
- the other open H seeds (lines 126 to 132);
- `.claude-plugin/plugin.json`, which only a release PR bumps (ADR-0095).

## Success criteria

- `python3 gates.py --selftest` prints `selftest: ok` on the fixed tree.
- For each of the four reverted fixes (O's date, M's date, H's date, H's
  zero count), the selftest prints a failure naming that row, quoted from
  a real run.
- The root and payload `gates_selftest.py` are identical, and detector E
  is clean after `update-manifest`.
- `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`,
  `python3 gates.py && python3 gates.py --selftest` all report 0
  problems.

## Constraints

Stdlib only. Problem-string contracts. Gates scan every markdown file, so
write no literal four-digit work-order or PRD-style id that does not
exist. The selftest's existing fixtures do use a PRD id inside Python
strings, which is fine.

## Tracker

No issues seed the run. At Ship, file one plain `type:defect` issue,
close it from the PR with `Closes #N`, and include a `No work order:`
line. Run `gh pr create` as the first command of its own Bash call, with
the body file written in an earlier call.

## User-facing surface

None.

## Release authorization

Prepare and stop (Owner decision 2). Ship pushes, files the issue, opens
the PR, records `outcome: prepared` with `pending-merge:`, and stops. No
merge, tag or version bump. The payload changes, so a later
`chore(release)` PR is owed (ADR-0095).

## Operate

skip. The Owner decided this run gets no retro (decision 3). The rows
fire only on a regression. The run stays active.

stop-after: ship
