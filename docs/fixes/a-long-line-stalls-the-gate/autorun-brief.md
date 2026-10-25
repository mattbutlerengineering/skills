# Autorun brief: maintenance:a-long-line-stalls-the-gate

Not an artifact. The brief autorun collects once, standing in for the
interviews the stages would otherwise run. Collected 2026-10-25, one
question at a time, from the Owner.

## Origin

Backlog seed `docs/backlog.md:131` (from:
maintenance:a-zero-count-names-nothing), to be claimed in place as
`(claimed: maintenance:a-long-line-stalls-the-gate)`.

## Run scale and entry

Maintenance, slug `a-long-line-stalls-the-gate`, artifacts at
`docs/fixes/a-long-line-stalls-the-gate/`. Entry is capture with
`re-entry: implement` (Owner decision): one function and one constant,
no seam or ownership question. Work items go inline in `defect.md`.

## Defect

`gates._names_unknown` runs `SUMMARY_ZERO_COUNT.search(line, 0,
match.start())` over the whole prefix for every SUMMARY_UNKNOWN_TERM
match, so detector H's roll-up is quadratic in line length. The seed
measured 1.57s for a 22 kB line and 39s for a 110 kB line; the longest
tracked `verification.md` line is 1132 characters. These numbers are
the seed's: capture re-measures them for real, never copies them in as
fact.

Fix (from the seed): bound the zero-count search to a fixed window
before `match.start()`, and state the window's width as a named
constant beside `SUMMARY_ZERO_COUNT`. The width is a tuning value:
Implement picks the smallest width that keeps every existing zero-count
fixture green and logs it under `assumptions:`.

## Blast radius

`gates.py` is mirrored into the factory payload, so every stamped
repo's detector H is slow on long lines. No wrong verdict, only time.
A manifest regeneration is expected (`python3 factory_init.py
update-manifest`; delete stray `.orig`/`.rej` first).

## Ruled out

Re-entry at Architect, and a semantics-preserving linear rewrite
(deferred unless the window breaks a fixture).

## Constraints

Stdlib only. Battery: `python3 run_tests.py`, `python3 lint.py`,
`python3 kb.py drift`, `python3 gates.py && python3 gates.py
--selftest`. Test first. Never fabricate evidence.

## Tracker

File one plain issue with a `type:*` label for the run; the PR body
carries a `No work order:` line and `Closes #N`.

## User-facing surface

None.

## Release authorization

**None.** Prepare and stop: Ship pushes, files the issue, opens the PR,
records `outcome: prepared` with `pending-merge:`, and stops. No merge,
tag or version bump (ADR-0095).

## Operate

skip. Prevention with no user signal expected in this repo; the run
stays active.

stop-after: ship
