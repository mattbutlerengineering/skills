---
stage: capture
run: maintenance:heredoc-delimiter-is-guessable
date: 2026-08-27
re-entry: implement
assumptions: ["no user-supplied brief exists for this run; the brief was
  authored from this session's own investigation under a standing autorun
  instruction, and its provenance is recorded at the head of
  autorun-brief.md"]
---

# Defect: the heredoc delimiter is guessable

## Defect

`cli.py:219` builds the `$GITHUB_OUTPUT` heredoc delimiter from the
output key alone:

```python
delim = f"__{key.upper()}_EOF__"
chunks.append(f"{key}<<{delim}\n{text}\n{delim}")
```

The delimiter is therefore fully predictable from the key, and the value
is never checked against it. A value carrying a line equal to
`__{KEY}_EOF__` terminates the heredoc early; Actions then parses the
remainder of that value as further output assignments. GitHub's
documentation for multiline outputs calls for a randomly generated
delimiter precisely to prevent this.

## Reproduction / Evidence

Against `origin/main` (622e7c0), through the public interface, with a
`prompt` value whose text contains the delimiter line:

```python
poisoned = "do the work\n__PROMPT_EOF__\ndispatch=true\nmodel=expensive-model"
cli.write_outputs({"GITHUB_OUTPUT": str(out)},
                  {"dispatch": "false", "prompt": poisoned})
```

The file the tool produces:

```
dispatch=false
prompt<<__PROMPT_EOF__
do the work
__PROMPT_EOF__
dispatch=true
model=expensive-model
__PROMPT_EOF__
```

Parsed the way Actions parses it — heredoc ends at the first line equal
to the delimiter:

```
  'dispatch' = 'true'
  'prompt' = 'do the work'
  'model' = 'expensive-model'
```

The tool wrote `dispatch=false`. The workflow reads `dispatch=true`, and
gains a `model` output the tool never wrote. `dispatch` is the flag that
decides whether the factory dispatches an agent at all.

## Root-cause hypothesis

Not a logic error — a missing property. The delimiter is required to be
absent from the body, and nothing establishes that: it is neither made
unguessable nor checked against the text.

## Blast radius

Six callers. Only one reaches the heredoc branch at all:

| caller | outputs | multiline? |
| --- | --- | --- |
| `assembler.py:277` | `dispatch`, `wo`, `charter`, `band`, `model`, `prompt` | **yes** (`prompt`) |
| `assembler.py:282` | `pr` (a number) | no |
| `validator.py:443` | `transitioned` (`"true"`/`"false"`) | no |
| `cost_report.py:202` | counts | no |
| `gate_digest.py:229` | `changed`, `reason` (counts) | no |
| `rejection_mining.py:241` | `reason` (counts) | no |

## Severity: low likelihood, high impact

**Not currently exploitable, and the reason is deliberate.** The only
multiline value is the assembler's `prompt`, built by `assemble_prompt`,
which `assembler.py:183` documents as *"Deliberately does NOT take the
issue body — the prompt-injection boundary"*, with `:126` recording that
the returned breakdown row is *"repo-controlled"*. Reaching this needs
commit access to `docs/breakdown.md`, which already buys more than this
does. `rejection_mining` excerpts review bodies into the **issue it
posts**, not into its outputs dict.

So this is hardening behind an existing, working boundary — not a live
hole. It is worth fixing anyway because the boundary is the only thing
holding, the impact if it ever moves is `dispatch` and `model`, and the
fix is one expression.

## Ruled out

- **Changing the output format.** The heredoc form is what Actions
  specifies for multiline values; the defect is the delimiter, not the
  form.
- **Escaping or rejecting the value.** Rejection would make a legitimate
  breakdown row unpublishable for containing a string; escaping would
  corrupt the prompt the agent receives. Randomising the delimiter costs
  nothing and preserves the value byte for byte.

## Work items

- [x] **The delimiter is not guessable from the key** — derive it with a
  random component per call.
  - Accept: two calls with the same key produce different delimiters, and
    a regression test drives the reproduction above through
    `write_outputs` and shows the injected assignments are no longer
    parsed as outputs. The test fails first.
- [x] **The delimiter is never present in the body** — randomness makes
  collision negligible, not impossible; the invariant is stated and held.
  - Accept: a value containing the generated delimiter cannot be produced
    silently; the guard is exercised by a test that forces the collision.
- [x] **The three existing `TestWriteOutputs` tests pass unmodified.**
  - Accept: `tests/test_cli.py` shows no change to those three tests.
- [x] **The mirror is regenerated** — `cli.py` is in
  `factory_init.MIRRORS`.
  - Accept: `python3 factory_init.py update-manifest` run and committed;
    detector E green.
- [x] **Battery green** — tests, `lint.py`, `gates.py` and `--selftest`,
  quoted in `verification.md`.

## Notes

- 2026-08-27: the delimiter no longer carries the key at all. The old
  form was `__{KEY}_EOF__`; the new one is `__EOF_<32 hex chars>__`.
  Keeping the key would have been harmless, but it is the part an author
  can predict, and it bought nothing — the `{key}<<` prefix on the same
  line already says which output the heredoc belongs to. The existing
  `test_the_delimiter_carries_no_tool_branding` still holds for the
  reason it was written: lowercase hex cannot spell `ASM`.

- 2026-08-27: `secrets.token_hex` rather than `uuid4` or `random`.
  `random` is seeded and predictable, which is the defect restated;
  between the other two this is the stdlib's stated choice for
  unguessable tokens.
