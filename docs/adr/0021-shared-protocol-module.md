# One shared protocol module alongside standalone scripts

- Status: accepted
- Date: 2026-07-01

The repo's tools have been standalone stdlib-Python scripts, each carrying
what it needs. That convention let the pipeline protocol's executable
knowledge — stage order, the artifact table, frontmatter parsing, the UX
conditional, the checkbox rule, the retro short-circuit, next-stage
derivation — spread across three files, with the frontmatter parsers
already divergent on the missing-block case (empty dict vs None vs raise).

Decision: extract that knowledge into `protocol.py`, one deep module with
a small interface (taxonomy constants, `STAGE_ARTIFACTS`,
`read_frontmatter` with a single None-on-missing-block contract,
`next_stage` and its rule helpers). Tools become thin callers: the
orientation CLI is an adapter with unchanged command-line behavior, and
the structural lint and trigger-eval runner convert next. The orientation
fixture suite pins `protocol.next_stage` directly, so
docs/pipeline-protocol.md — which remains the spec — has exactly one
implementation to agree with.

Standalone scripts remain the convention for tools; the exception is this
single shared module for protocol knowledge, justified by three real
callers and an observed behavioural divergence — not a general utilities
module. Nothing else graduates into it without the same evidence.
