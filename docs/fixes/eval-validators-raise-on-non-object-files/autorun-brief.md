# Autorun brief — eval validators raise on non-object files

## Provenance (read this first)

**No user-supplied brief exists for this run.** The user's instruction was
`/autorun` under a standing loop, with no defect named. This brief was
authored from the session's own investigation: a search for work that is
both evidenced and conflict-free against the 17 open pull requests.

That matters for two reasons, and both are recorded rather than smoothed
over:

- Every "requirement" below is the author's inference, not a stated need.
  Where the pipeline would normally interview, this brief substitutes
  measurement — the defect is demonstrated before it is described.
- The scope boundary was chosen partly by *contention*, not only by
  value. A different, larger defect in `cli.py` was found first and
  deliberately not taken (see Scope, out).

## The work

A maintenance run against `eval_schema.py`, whose validators raise on a
JSON file that parses to something other than an object, in direct
contradiction of the module's own documented contract.

- **Run scale:** maintenance, slug
  `eval-validators-raise-on-non-object-files`.
- **Re-entry depth:** `implement`. The fix restores a contract the module
  already states; it does not change the design, so Architect and
  Decompose are skipped and the breakdown lives inline in `defect.md`.

## Scope

**In.** `eval_schema.py` — `validate`, `validate_output`, `fixture_refs`.
Its regression tests in `tests/test_eval_schema.py`.

**Out.**

- `lint.py`, `trigger_eval.py`, `charter_replay.py`. They are the
  callers that surface the crash, but the defect is not theirs and the
  fix does not need them. `lint.py` is also claimed by two open PRs.
- The `write_outputs` heredoc-delimiter defect in `cli.py`, found in the
  same sweep and genuinely more severe. `cli.py` is mirrored into the
  payload, so touching it forces `factory_init.py update-manifest` and a
  write to `factory/manifest.json`, which nine of the seventeen open PRs
  already claim. Deferred deliberately, not overlooked.
- Running `trigger_eval.py` or `charter_replay.py`. Both cost real model
  spend and are never run by this session.

## Success criteria

1. No validator in `eval_schema.py` raises for any JSON value a file can
   parse to — object, array, string, number, boolean, or null.
2. A non-object file yields **one** clear problem naming the actual
   defect, not a cascade of derived ones.
3. The repo battery is green: full suite, `lint.py` 0, `gates.py` 0 and
   `--selftest` ok.

## Constraints already decided

- Stdlib only; no new dependency.
- Problem-string contract: validators return label-prefixed problem
  strings and never raise.
- `eval_schema.py` is not in `factory_init.MIRRORS`, so no manifest
  regeneration is involved. This was verified, not assumed.

## Release authorization

**None given.** Ship prepares and stops: pre-flight and `release.md`, no
merge, no tag, no PR opened. The 17-PR queue is held pending human
review, and this run does not add to it.
