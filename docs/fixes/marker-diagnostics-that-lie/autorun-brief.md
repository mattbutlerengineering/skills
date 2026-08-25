# Autorun brief: maintenance:marker-diagnostics-that-lie

Not an artifact. The brief autorun collects once, standing in for the
interviews the stages would otherwise run.

## Origin

Backlog seed `docs/backlog.md:55` (from: maintenance:one-fact-one-owner),
claimed as `(claimed: maintenance:marker-diagnostics-that-lie)`. Tracking
issue #336.

## Run scale

Maintenance, slug `marker-diagnostics-that-lie`, artifacts at
`docs/fixes/marker-diagnostics-that-lie/`. Entry is capture with
`re-entry: architect`: fixing diagnostic 1 needs a new field on `FactSite`,
which `tests/test_one_owner.py` pins as "architecture.md's Data model" — a
recorded shape, so changing it is a decision to write down rather than a
typo to correct.

## Scope

**In.** Two `one_owner.py` diagnostics stop stating something false:

1. A `# one-owner:` marker written above a *decorated* definition attaches
   to that definition instead of being rejected as "above no definition".
2. `_rent` distinguishes a counterpart that does not exist from one that
   exists but states no fact this pass reads, and says which.

Plus the test changes those two need, including the `FactSite._fields` pin.

**Out.** Everything else the seed's siblings name. Specifically NOT in
scope: the `ls-files -z` universe fix and the `_adr_ids` listing (seed 54 —
already open as PR #322, and it touches `one_owner.py`); folding
`_stated_value`'s escape-hatch pressure (seed 50); the six undecided
day-one findings (seed 53); the tests/** exclusion (seed 56); running the
pass at Review time (seed 57). None of them is a prerequisite for these two.

Also out: changing what counts as a fact site. The two-key floor, the
module-level-Assign rule and the tests/** exclusion all stay exactly as
they are — this run fixes what the pass *says*, never what it *finds*.

## Constraints already decided

- `one_owner.py` is **not** in `factory_init.MIRRORS`. No payload mirror,
  no `update-manifest`, no manifest conflict added to the eight open PRs.
- ADR-0061 stands: a deliberate second owner is recorded with a
  `# one-owner:` marker **at the definition it excuses**. Diagnostic 1 is a
  case where the pass refuses to honour a marker that already satisfies
  ADR-0061, so this run conforms to that record rather than amending it.
- Stdlib only; problem strings are the contract and the suite asserts them
  exactly through public interfaces.
- PR #322 also edits `one_owner.py` (`source_files`, `_adr_ids`). Different
  functions, so a textual conflict is unlikely but not impossible — whoever
  merges second rebases.

## Success criteria

1. A well-formed marker in the contiguous comment block above a decorated
   definition attaches to that definition and yields no problem.
2. A marker between a decorator and its `def` keeps attaching — today's
   workaround must not become tomorrow's regression.
3. A marker naming a counterpart that exists but states no fact reports
   that, not "is not defined in this repo".
4. A marker naming a counterpart that exists nowhere still reports "is not
   defined in this repo".
5. `python3 one_owner.py` over this repo reports the same findings before
   and after, except where a case above changes one deliberately.
6. Battery green: `python3 -m unittest discover tests`, `python3 lint.py`,
   `python3 gates.py && python3 gates.py --selftest`.

## Release authorization

**None.** Prepare-and-stop: pre-flight, open the PR, write `release.md`,
stop. No merge, no tag, no publish. ADR-0036 clause 2 independently forbids
the author merging — a non-authoring reviewer must re-execute verification
and record it on the PR.

## Tracker

Issue #336 is the tracking issue for the run, created before the branch and
before any artifact. No per-work-order issues: this is a maintenance run,
not a dispatch, so ADR-0032's one-way mirror has nothing to mirror.
