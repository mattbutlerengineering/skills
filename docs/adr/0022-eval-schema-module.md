# One eval-schema module beside the protocol module

- Status: accepted
- Date: 2026-07-02

The routing eval-set's schema — the kind vocabulary, the case shape
(`{id, kind, expected, query}`), the coverage policy — was known in three
places, and the copies had already diverged: the trigger-eval runner
defined a `KINDS` tuple it never read (a dead copy), the structural lint
redefined the tuple locally as the live validator, and the evals README
described the shape in prose. Divergence between a dead copy and a live
copy is exactly the graduation evidence ADR-0021 set as the bar.

Decision: extract that knowledge into `eval_schema.py`, a second small
seam owning `KINDS`, validation of the case shape and coverage policy,
and `load` (read-plus-validate with a caller-supplied label prefixing
every diagnostic). The structural lint and the trigger-eval runner are
thin callers: lint's `check_evals` output is unchanged, the runner now
refuses a malformed eval set with the same diagnostics lint would print
instead of a raw traceback, and the dead constant is deleted.

This knowledge does not graduate into `protocol.py`: that module owns
pipeline-protocol knowledge (ADR-0021), and the eval-set schema is
eval knowledge — the two change for different reasons. Standalone
scripts remain the convention for tools; shared modules stay
single-purpose and require the same evidence — multiple real callers
plus observed divergence — before anything else moves in.
