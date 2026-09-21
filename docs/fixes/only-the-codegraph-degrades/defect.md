---
stage: capture
run: maintenance:only-the-codegraph-degrades
date: 2026-08-27
re-entry: implement
assumptions: ["no user-supplied brief exists for this run; the brief was
  authored from this session's own investigation under a standing autorun
  instruction, and its provenance is recorded at the head of
  autorun-brief.md"]
---

# Defect: only the codegraph degrades

## Defect

`orientation_pack.py` builds one best-effort context bundle out of three
kinds of repo file. One of the three degrades when it cannot be read.
The other two raise.

```python
# orientation_pack.py:110 — the stated convention
def _python_structure(path):
    """(docstring headline, [top-level def/class names]) for a .py file,
    read via ast so nothing executes. A file that cannot be read or parsed
    (syntax error, non-UTF-8) degrades to (message, None) rather than
    raising — the codegraph is best-effort orientation, and one unparseable
    file a row names must not crash the assembler CLI (the repo's
    problem-string/degrade convention, not a traceback)."""
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, ValueError, SyntaxError) as err:
        return f"(could not be parsed: {err.__class__.__name__})", None
```

```python
# orientation_pack.py:171 — the same pack, unguarded
    context = (context_path.read_text(encoding="utf-8")
               if context_path.is_file() else "(no CONTEXT.md at repo root)")
    parts = [f"## Orientation pack: {wo}\n", "### CONTEXT.md\n", context]
    for number in cited_adrs(block):
        path = adr_path(root, number)
        if path is None:
            continue
        parts.append(f"### ADR-{number}: {path.stem}\n")
        parts.append(path.read_text(encoding="utf-8"))
```

`orientation_pack` is the module's only public entry and the caller of
`_python_structure`. The `is_file()` guard answers a different question
from the one the read asks, and the ADR read has no guard at all.

## Why it matters

The docstring names the consequence it is preventing: "must not crash
the assembler CLI". That CLI is `assembler.py`, which calls this
function from `assemble_prompt` and contains no `except` anywhere — so
the exception is the process exit, not a handled failure.

The module ships. `orientation_pack.py` is in `factory_init.MIRRORS`
(`tools/factory/orientation_pack.py`), so the CONTEXT.md and
`docs/adr/*.md` it reads belong to whatever product repo adopted the
factory. In this repo they are all ASCII; in a product repo they are
whatever someone wrote. A single latin-1 accent in a CONTEXT.md — or a
file mode nobody meant to set — takes down every dispatch in that repo,
and the failure has nothing to do with the work order being dispatched.

Losing the pack degrades a prompt. Raising loses the dispatch.

## Reproduction

```
=== A. a non-UTF-8 CONTEXT.md ===
  UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 25: invalid continuation byte
=== B. a non-UTF-8 cited ADR ===
  UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 25: invalid continuation byte
=== C. the SAME bytes in a .py file the row names ===
  - demo.py — (could not be parsed: UnicodeDecodeError)
=== D. an unreadable CONTEXT.md (chmod 000) ===
  PermissionError: [Errno 13] Permission denied: '.../CONTEXT.md'
```

C is the whole finding. Identical bytes, identical row, identical
function call — a note when the file is code, a traceback when it is
prose.

## Why the tests did not catch it

`test_an_unparseable_python_file_degrades_and_does_not_crash` exists and
says so in its name. It writes a syntax-error `.py` file and asserts the
note. There is no sibling for CONTEXT.md and none for an ADR: the suite
asserts the invariant on the one path that already holds it. The same
shape this repo keeps turning up.

## Fix

One helper in the module's own idiom, used by both unguarded reads:

- `_read_or_note(path, what)` returns the text, or
  `({what} could not be read: {ErrorClass})` on `OSError`/`ValueError`
  — the two classes covering an unreadable file and a non-UTF-8 one.
- CONTEXT.md and each cited ADR read through it.

A note, not a silent drop: a reader who cannot see a cited ADR's text
should be told it was cited and why it is missing. The heading is
already emitted before the read, so this is the smaller change as well
as the honest one.

## Breakdown

- [x] A CONTEXT.md that cannot be decoded does not raise. Acceptance: a
      tree whose CONTEXT.md is latin-1 produces a pack naming CONTEXT.md
      and the reason it could not be read, and the rest of the pack —
      the ADRs and the codegraph — is still there.
- [x] A cited ADR that cannot be decoded does not raise, and is not
      silently dropped. Acceptance: the pack still carries the ADR's
      heading, followed by the note in place of its body.
- [x] An unreadable file is covered too, not just an undecodable one.
      Acceptance: a mode-000 CONTEXT.md degrades the same way, so the
      `is_file()` guard is no longer the only thing standing between the
      read and the CLI.
- [x] The two halves of the pack now agree. Acceptance: a test puts the
      same undecodable bytes in a `.py` file the row names and in
      CONTEXT.md, and neither raises.
- [x] Payload and manifest regenerated (`orientation_pack.py` is
      mirrored). Acceptance: detector E is green.
- [x] Full battery green.

## Notes

2026-08-27 — the first draft of `verification.md` quoted the pack built
for the tests' fixture work order, and detector C failed the gate on it:
a `WO-####` token in any scannable file that is not a `breakdown.md`
must have a breakdown row, and a fixture id has none. The evidence was
regenerated against WO-0015 — this module's own work order, which does
have a row — rather than edited, and the prose that explained the swap
had to stop naming the fixture id for the same reason. The pack body is
byte-identical; only the heading differs. Worth recording because it is
a real constraint on how these artifacts quote tool output, and it will
catch the next run that pastes a fixture transcript.
