---
stage: review
run: maintenance:the-fourth-split-contract-is-unpinned
date: 2026-08-30
assumptions: []
---

# Review: the fourth split contract

Self-authored; ADR-0036 clause 2 still wants a non-authoring reviewer.

## Findings

### 1. Intersection instead of union — a deliberate divergence from the two siblings

`test_assembler` and `test_cost_report` both assert
`yaml_refs <= union(emitted_keys over paths)`. This one asserts against
the **intersection**, and `verification.md` §4 shows the mutation that
separates them: a key emitted on two of three paths passes the union
version and fails this one.

The intersection is correct for the general case, not just this one:
the workflow evaluates `steps.<id>.outputs.<key>` on whatever path the
run actually took, so "some path emits it" is not the property the
workflow needs.

**The two siblings could be tightened the same way, and this run does
not touch them.** That is a deliberate scope call — they are green,
their tools' paths all emit their read keys today, and changing three
tests to fix one gap would put this run in conflict with more of a
44-deep queue for no verified defect. Recorded here so the idea is not
lost rather than silently applied or silently dropped.

### 2. The path guards were kept, not deleted — considered

`emitted_keys` asserts `outputs.get("changed") == "false"` / `"true"`
on two of the three paths. Those assertions are what prove the three
fixtures reach three *different* branches instead of the same one three
times — without them the test could collect one path's keys three times
and still pass.

They initially made a renamed key surface as a bare `KeyError` instead
of the lockstep message. The fix was `.get()` plus an explanatory
message, not deletion.

### 3. `steps.find.outputs.pr` left alone — held

`test_assembler` pins it with a literal `assertIn("steps.find.outputs.pr",
text)`, which pins the YAML side only. Deriving it properly means
reaching `assembler.run_find`, and that is a second run's worth of
fixture work for a key whose loss is loud (the dispatch step's
`gh workflow run ... -f pr=` gets an empty value and fails) rather than
silent. The silent one is what this run is for. Stated in
what-is-not-verified.

### 4. A general workflow-output detector — a real idea, deliberately not built

The generalisable check is: find every `steps.<id>.outputs.<key>` across
all workflows, and demand that each has a bridge test. That would have
caught this gap without anyone noticing it by hand, and it would catch
the next one.

It is not built here because it needs a way to know which step ids are
backed by *this repo's* Python (`resolve`, `claim`, `report`, `digest`)
versus a third-party action (`agent`, backed by the Claude action) — and
guessing wrong makes it either noisy or vacuous. That is a design
decision, and design decisions in this repo go through an ADR. Filed as
the open question in the tracking issue instead of being answered by an
agent mid-run.

### 5. Scope: one workflow, one contract — held

The sweep that found this covered all 8 workflows and all 11
`steps.*.outputs.*` references (recorded in the issue). Exactly one had
no bridge. Fixing that one and writing the other findings down is the
whole run.
