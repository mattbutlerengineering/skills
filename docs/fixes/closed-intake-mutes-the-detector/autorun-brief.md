# Autorun brief: maintenance:closed-intake-mutes-the-detector

Not an artifact. The brief autorun collects once, standing in for the
interviews the stages would otherwise run.

## Origin

Backlog seed `docs/backlog.md:35` (from: session:2026-08-21), claimed as
`(claimed: maintenance:closed-intake-mutes-the-detector)`. Tracking issue
#338.

The seed was verified before it was claimed, and one of its claims did not
survive: the label drift it says is "still" live has been fixed. The
mechanism it names is real, and the live fact is sharper than the seed
states — see `defect.md`.

## Run scale

Maintenance, slug `closed-intake-mutes-the-detector`, artifacts at
`docs/fixes/closed-intake-mutes-the-detector/`. Entry is capture with
`re-entry: architect`: `known_keys`' docstring defends deduping across
every issue state at length, and this run narrows that rule. Amending a
decision that is written down gets `architecture.md`, not a straight edit.

## Scope

**In.** `known_keys` (sweeps.py:331) stops suppressing an intake whose
issue is explicitly CLOSED, unless the key's namespace is one whose source
re-reports the signal. Its docstring says the new rule and why. Tests pin
both halves.

**Out.**

- The `sweeps: 0 issue(s) filed, 0 problem(s)` line, which reads the same
  for "nothing to report" and "everything suppressed". That is backlog seed
  42's class, it spans more than this function, and it is a reporting
  decision rather than a dedupe one.
- Whether #173 and #295 should be reopened rather than superseded by a new
  intake. That is an operator's call about two live issues, not a code
  change, and this run touches no issue but its own.
- Sentry dedupe. It stays exactly as it is; the docstring's defence of it
  is correct and is preserved verbatim in substance.
- `MAX_INTAKE`, the window rule, `screen`, `file_issues`' cap arithmetic.

## Constraints already decided

- `sweeps.py` is **not** in `factory_init.MIRRORS`. No payload mirror, no
  `update-manifest`, no manifest conflict added to the nine open PRs.
- The window rule in `known_keys` (a full `LIST_WINDOW` listing is reported,
  because past it old keys are invisible and their intake is re-filed as a
  duplicate) is untouched and must keep passing its existing case.
- Stdlib only; problem strings are the contract and the suite asserts them
  exactly through public interfaces.

## Success criteria

1. A detector-derived key whose only issue is CLOSED no longer suppresses
   filing.
2. The same key whose issue is OPEN still suppresses filing.
3. A `sentry:` key suppresses filing in either state — the documented
   behaviour, unchanged.
4. An issue whose state is anything other than the literal `CLOSED`
   suppresses exactly as today, so no listing quirk can turn the sweep into
   a duplicate factory.
5. The full-window report still fires and still says what it says.
6. Neither detector files anything on this repo today, so merging changes
   no live behaviour immediately — evidenced, not assumed.
7. Battery green: `python3 -m unittest discover tests`, `python3 lint.py`,
   `python3 gates.py && python3 gates.py --selftest`.

## Release authorization

**None.** Prepare-and-stop: pre-flight, open the PR, write `release.md`,
stop. No merge, no tag, no publish. ADR-0036 clause 2 independently forbids
the author merging.

**And a standing prohibition for this run specifically:** no stage may run
`python3 sweeps.py <command>` in a mode that files issues, reopens issues,
or mutates labels. The sweep's read-only paths and offline fixtures are the
only evidence this run collects.

## Tracker

Issue #338 tracks the run, created before the branch and before any
artifact. No per-work-order issues: a maintenance run is not a dispatch, so
ADR-0032's one-way mirror has nothing to mirror.
