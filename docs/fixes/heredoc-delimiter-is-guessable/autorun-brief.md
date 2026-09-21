# Autorun brief: the heredoc delimiter is guessable

**Provenance.** No user-supplied brief exists for this run. It was
authored from this session's own investigation under a standing autorun
instruction, and the finding was first recorded as a memory
(`cli-write-outputs-deterministic-heredoc-delimiter`) before this run
existed. That memory's severity assessment is carried forward and
sharpened below.

## What and why

`cli.write_outputs` writes multiline values to `$GITHUB_OUTPUT` using
GitHub's heredoc form, with a delimiter derived deterministically from
the output key: `__{KEY}_EOF__`. It never checks whether the value
contains a line equal to that delimiter. One that does ends the heredoc
early, and everything after it is parsed by Actions as **new output
entries**. GitHub's own documentation calls for a random delimiter for
exactly this reason.

## Scale

Maintenance run, `re-entry: implement`. The fix is one expression plus a
guard; the breakdown lives inline in `defect.md` as checkboxes.

## Scope

**In:** `cli.write_outputs`'s delimiter generation, and a regression test
driving the injection through the public interface.

**Out:** changing the `$GITHUB_OUTPUT` format, the set of outputs any
caller writes, or the callers themselves. Also out: `read_event` and the
rest of `cli.py`, which this run does not touch.

## Constraints

- Stdlib only.
- `cli.py` is in `factory_init.MIRRORS`, so the payload copy and
  `factory/manifest.json` must be regenerated with
  `python3 factory_init.py update-manifest` in the same change.
- The three existing `TestWriteOutputs` tests must pass **unmodified** —
  they were checked first, and a random delimiter satisfies all three
  (`prompt<<` still matches, and lowercase hex cannot contain `ASM`).

## Success criteria

A value containing the old delimiter can no longer inject an output; the
existing tests pass unmodified; the battery is green.

## Release authorization

**None.** Ship prepares and stops: no PR, no merge, no release action.
