# Autorun brief — only the codegraph degrades

## Provenance

No user-supplied brief exists for this run. It was authored from this
session's own investigation under a standing autorun instruction. The
candidate came from the technique that has found every defect in this
series: test a module's stated convention against its own code.
`orientation_pack.py` states the convention in one function's docstring
and breaks it in the function that calls it.

## What and why

`_python_structure` states the rule for the pack's codegraph half:

> A file that cannot be read or parsed (syntax error, non-UTF-8)
> degrades to (message, None) rather than raising — the codegraph is
> best-effort orientation, and one unparseable file a row names must not
> crash the assembler CLI (the repo's problem-string/degrade convention,
> not a traceback).

`orientation_pack`, the module's only public entry and the caller of
that function, reads CONTEXT.md and every cited ADR with a bare
`read_text(encoding="utf-8")`. Same best-effort pack, same prompt, same
CLI, no guard. A non-UTF-8 or unreadable CONTEXT.md or ADR raises out of
`assembler.assemble_prompt`, and `assembler.py` has no `except` anywhere
— the traceback the docstring rules out is exactly what the caller gets.

The contrast is inside one function: the same bytes in a `.py` file the
same row names degrade to `- demo.py — (could not be parsed:
UnicodeDecodeError)`, while in CONTEXT.md they crash.

`orientation_pack.py` is mirrored into the factory payload, so the
CONTEXT.md and `docs/adr/*.md` it reads belong to whatever product repo
adopted the factory — not to this repo, where they all happen to be
ASCII.

## Scale and re-entry

Maintenance run, slug `only-the-codegraph-degrades`. Re-entry is
`implement`: the convention is stated, the degradation shape exists in
the same module, and two reads need to adopt it.

## Scope

In: the CONTEXT.md read and the cited-ADR read in `orientation_pack`,
degrading to a note in the module's own idiom.

Out: `_python_structure`'s own catch, which already degrades and whose
message is pinned by an existing test. Out: `adr_path` returning None
for an ADR that is cited but absent, which is a different question
(missing, not unreadable) and is existing, tested behaviour. Out:
anything in `assembler.py` — it is contended by an open PR, and the fix
belongs at the module that states the rule.

## Constraints

Stdlib only. `orientation_pack.py` IS in `factory_init.MIRRORS`, so the
payload copy and `factory/manifest.json` must be regenerated with
`python3 factory_init.py update-manifest`.

## Release authorization

None. Ship prepares and stops.
