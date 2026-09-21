# Autorun brief — the front door miscounts its own tools

## Scale

Maintenance run, `re-entry: implement`. Artifacts at
`docs/fixes/the-front-door-miscounts-its-own-tools/`.

## What and why

`factory.py` is the router over the root tools' CLI legs. Its whole
stated discipline is that it restates nothing the table already owns —
the verb is the module's name, the index line is read from the module's
docstring at print time, and the table is pinned to a mechanical scan.
The one fact it does hand-type in prose, the number of CLI-bearing root
modules, has drifted three behind.

## Scope

In scope: `factory.py`'s module docstring, the matching sentence in
`tests/test_factory_cli.py`, and a pin so the shape cannot recur.

Out of scope: `cli.py`'s "fourteen call sites" and its echo in
`tests/test_cli.py`. Both were checked and are accurate today (14
production `gh_read` call sites), and `cli.py` is touched by an unmerged
agent branch.

Out of scope: adding, retiring, or renaming any verb. The table is
correct; the prose beside it is not.

## Constraints

Stdlib only. `factory.py` stays a router that owns no logic of its own —
the pin lives in the test, where the existing derivations already live.

## Success

The router states no count the table owns, the test file's prose agrees,
and a test would catch the sentence that drifted if it came back.

## Release authorization

None. Prepare and stop.
