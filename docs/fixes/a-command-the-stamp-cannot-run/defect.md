---
stage: capture
run: maintenance:a-command-the-stamp-cannot-run
date: 2026-08-27
re-entry: implement
assumptions: ["no user-supplied brief exists for this run; the brief was
  authored from this session's own investigation under a standing autorun
  instruction, and its provenance is recorded at the head of
  autorun-brief.md"]
---

# Defect: a command the stamp cannot run

## Defect

`factory_init.product_form` respells a root command as its product-repo
twin by walking a hand-typed tuple:

```python
# factory_init.py:52
_PRODUCT_TOOLS = ("gates.py", "validator.py", "assembler.py",
                  "budget_guard.py", "cost_report.py", "gate_digest.py",
                  "rejection_mining.py")


def product_form(command):
    """A root command as its product-repo twin spells it. The one
    production statement of the root<->payload command respelling ..."""
    for tool in _PRODUCT_TOOLS:
        command = command.replace(f"python3 {tool}",
                                  f"python3 tools/factory/{tool}")
    return command.replace("unittest discover tests",
                           "unittest discover -q tests")
```

Three definitions below, in the same file, `MIRRORS` already states
which root files land under `tools/factory/` in a stamped repo — the
exact fact `_PRODUCT_TOOLS` restates for seven of them. Ten of the
seventeen mirrored Python tools are missing from the tuple, so a
Makefile command naming one of them is copied into the payload Makefile
unchanged.

## Why it matters

The generated Makefile is what a stamped product repo runs. A command
that was not respelled names a file at the product repo's root that is
not there — the tool is at `tools/factory/`. The target fails with
`python3: can't open file`, in someone else's repo, at whatever moment
the workflow that calls it next fires.

`MIRRORS`' own comment states the invariant and names its enforcement:

> It is absent from `_PRODUCT_TOOLS` on purpose — that tuple respells
> Makefile commands, and no target invokes it.

That is a claim about the root Makefile, and nothing checks it.
`TestLockstep` cannot: it asserts the payload Makefile's recipes against
`[product_form(c) for c in CANONICAL_CHECK]`, so the expectation is
computed by the same function that generated the file — both sides carry
the same mistake and the test stays green. Its target list is
hand-enumerated as well, so a Makefile target added for a new tool is
not compared to anything at all.

`work_queue.py` is the live edge: mirrored into the payload, shipped
with a `main()`, and absent from `_PRODUCT_TOOLS`. Adding the obvious
`make work-queue` target breaks every stamp silently.

## Reproduction

Two recipes appended to the real root Makefile, run through the real
`product_makefile`, land in the payload verbatim:

```
=== the two new recipes as they land in the PAYLOAD Makefile ===
'\tpython3 work_queue.py plan'
'\tpython3 label_sync.py --apply'
```

And the coverage of `product_form` over everything `MIRRORS` puts under
`tools/factory/`:

```
=== which mirrored tools product_form respells ===
  gates.py                 respelled
  protocol.py              PASSED THROUGH
  knowledge_plane.py       PASSED THROUGH
  cli.py                   PASSED THROUGH
  factory_config.py        PASSED THROUGH
  cost_ledger.py           PASSED THROUGH
  label_sync.py            PASSED THROUGH
  validator.py             respelled
  assembler.py             respelled
  budget_guard.py          respelled
  handoff.py               PASSED THROUGH
  orientation_pack.py      PASSED THROUGH
  cost_report.py           respelled
  human_gates.py           PASSED THROUGH
  gate_digest.py           respelled
  rejection_mining.py      respelled
  work_queue.py            PASSED THROUGH
```

Six of the ten pass-throughs are seam modules nothing invokes, which is
why there is no live breakage today. Four — `label_sync.py`,
`handoff.py`, `orientation_pack.py`, `work_queue.py` — are shipped files
with a command line.

## Why the tests did not catch it

`TestProductForm.test_each_factory_tool_moves_under_tools_factory`
exists and checks the respelling, against a hand-typed list of its own:
six tools, `budget_guard.py` missing. So the repo carries three copies
of the same fact — `MIRRORS`, `_PRODUCT_TOOLS`, and the test's tuple —
and the two that could disagree with `MIRRORS` are the two nothing
compares to it.

## Fix

`product_form` reads `MIRRORS` instead of a copy:

```python
for name, rel, _ in MIRRORS:
    if "/" not in name and rel != name:
        command = command.replace(f"python3 {name}", f"python3 {rel}")
```

`"/" not in name` skips the workflows and CODEOWNERS; `rel != name`
skips the Makefile, whose payload home is its root home. What is left is
exactly the root tools whose payload path differs — and the replacement
uses `MIRRORS`' own destination, so a tool mirrored somewhere else would
follow.

`_PRODUCT_TOOLS` is deleted; there is nothing left for it to own.

Then two assertions:

- the derivation itself — every tool `MIRRORS` puts under
  `tools/factory/` is respelled, driven off `MIRRORS` rather than a
  fourth hand-typed list;
- the claim the comment makes — every `python3 <file>` command in the
  **root Makefile** is either respelled by `product_form` or is the one
  documented drop (`lint.py`, which has no product-repo counterpart), so
  the payload Makefile can never name a root-level tool.

## Breakdown

- [x] The respelling has one owner. Acceptance: `_PRODUCT_TOOLS` is gone
      and `product_form` respells every root tool `MIRRORS` mirrors under
      `tools/factory/`, asserted over `MIRRORS` itself.
- [x] The comment's claim about the Makefile is checked. Acceptance: a
      test reads the real root Makefile's recipe lines and fails if any
      `python3 <file>` command survives `product_form` unrespelled,
      excepting the documented `lint.py` drop.
- [x] The payload Makefile cannot name a root-level tool. Acceptance: a
      test asserts no recipe line in the generated payload Makefile runs
      `python3 <bare>.py`.
- [x] No behaviour change today. Acceptance: `factory_init.py
      update-manifest` leaves `factory/templates/Makefile` and
      `factory/manifest.json` byte-identical.
- [x] Full battery green.
