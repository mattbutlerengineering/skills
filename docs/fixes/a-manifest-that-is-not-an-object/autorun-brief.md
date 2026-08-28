# Autorun brief — a manifest that is not an object

## Provenance

No user-supplied brief exists for this run. The candidate was recorded
earlier in this session as a beads memory
(`lint-manifest-readers-share-the-non-object-defect`), verified then and
deliberately NOT fixed, because `lint.py` was claimed by two open pull
requests. It is picked up now because those two PRs' hunks are elsewhere
in the file, so the fix and their changes do not touch the same lines.
The finding was re-verified from scratch before this brief was written;
nothing here rests on the memory alone.

## What and why

`lint.check_manifest` and `lint.check_pi_package` each parse a JSON file
and then reach straight for `.get`:

```python
data = json.loads(path.read_text(encoding="utf-8"))
...
return [f"plugin.json missing field: {field}" ... if not data.get(field)]
```

A JSON file's top level is legally an array, string, number, boolean or
null, and `json.loads` hands any of them back untouched. All five raise
`AttributeError` — verified for both functions.

`lint.main` has no exception handling, and these two are the FIRST two
entries in `CHECKERS`. So a `plugin.json` or `package.json` that parses
to anything but an object does not produce a lint problem; it kills the
whole gate with a traceback before any other checker runs, hiding every
other finding in the repo.

`check_pi_package` already knows the idiom — it guards `pi` with
`isinstance(pi, dict)` one level down. Its docstring says it is "guarded
like check_manifest so the dual-target packaging can't silently drift",
and it faithfully reproduced check_manifest's gap at the top level. So
did its test class, whose docstring repeats the same claim.

## Scale and re-entry

Maintenance run, slug `a-manifest-that-is-not-an-object`. Re-entry is
`implement`: the readers exist and are otherwise right; both take the
top-level shape on trust.

## Scope

In: one guard, owned once, applied by both readers, so the copy that
caused the drift has something correct to copy.

Out: `check_output_evals`, which has the SAME symptom from a different
cause — it hands the parsed value to `eval_schema.validate_output` and
`eval_schema.fixture_refs`, and those raise. Verified: `null` gives a
TypeError, a string and a list give AttributeError. That guard belongs
to `eval_schema`, whose validators own what a validator may assume, and
a complete fix for it already exists on the unmerged branch named under
Constraints. Duplicating it at lint's call site would add the third copy
this run exists to prevent. Recorded as an open finding, not fixed here.

Out: `check_evals`, re-checked and sound — it tests for the file's keys
before reaching for them. Out: the remaining eleven checkers, none of
which parses a JSON top level. Out: adding exception handling to
`lint.main`; a checker that raises is a checker bug, and papering over
it in the loop would hide the next one.

## Constraints

Stdlib only. `lint.py` is not in `factory_init.MIRRORS`, so no payload
mirror and no manifest regeneration.

There is an unmerged, PR-less branch,
`agent/eval-validators-raise-on-non-object-files`, which adds
`eval_schema.object_problems` with the identical rule for the eval
validators. `lint.py` already imports `eval_schema`, so if that branch
ever lands the two must collapse into one owner. This run cannot import
a function that is not on `main`, so it states the rule here and records
the dedup for whoever merges both.

## Release authorization

None. Ship prepares and stops.
