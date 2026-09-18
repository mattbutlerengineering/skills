# Autorun brief — a filter rebuilds the redacted id

## Provenance

No user-supplied brief exists for this run. It was authored from this
session's own investigation under a standing autorun instruction. The
candidate came from testing a module's stated convention against its
code: `knowledge_plane.sanitize` promises that "WO ids are redacted
(neither a sweep intake nor a mined queue entry may name a work order —
ADR-0032)", and one of its two callers keeps editing the string after
that promise is made.

## What and why

`sweeps.sentry_intakes` builds an intake's dedupe key from an untrusted
Sentry `shortId`:

```python
short_id = UNSAFE_KEY.sub("", sanitize(entry.get("shortId"), KEY_LIMIT))
```

`UNSAFE_KEY` **deletes** every character outside `[A-Za-z0-9_.:-]`, and
it runs after `sanitize`. Deleting characters can splice a WO token back
together out of text that `sanitize` correctly did not match: a shortId
of `WO-[0042]`, `WO-00 42`, or `W` + backtick + `O-0042` all arrive at
`WO-0042` once the filter has removed the characters that were keeping
them apart.

The reconstructed id then lands in the intake's key, its title, and its
rendered body — a filed GitHub issue naming a work order, which ADR-0032
forbids and which is exactly what `sanitize` exists to prevent.

`sanitize`'s redaction is the last word only if nothing edits its output
afterwards. Here something does.

## Scale and re-entry

Maintenance run, slug `a-filter-rebuilds-the-redacted-id`. Re-entry is
`implement`: the rule exists, has an owner, and is correct; one caller
applies it in the wrong order.

## Scope

In: the composition order at that one call site, so the redaction is the
final transformation rather than an intermediate one.

Out: `knowledge_plane.sanitize` itself — its rule is right. Out: the
`title` and `fields` paths in the same function, which pass `sanitize`'s
output through unedited and are therefore already correct. Out: the
`rejection_mining` caller, same reason. Out: anything in PR #339, which
also edits `sweeps.py` (at `known_keys` and `screen`, not here).

## Constraints

Stdlib only. `sweeps.py` is not in `factory_init.MIRRORS`, so no payload
mirror and no manifest regeneration.

## Release authorization

None. Ship prepares and stops.
