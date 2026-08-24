# eval_schema's charter covers all eval knowledge, not one file's schema

- Status: accepted
- Date: 2026-07-02

ADR-0022 chartered `eval_schema.py` around evals/routing.json. Two
issues since then moved knowledge in whose second copy was prose rather
than code: the output-eval record shape (issue #25 — docs/output-evals.md
restated the field list, and the copies had drifted by three fields) and
the results naming grammar (issue #26 — the runner's record step held
the only implementation, two docs restated it, and the output-evals doc
contradicted its own anatomy section about the `-N` suffix). Both #25's
and #26's reviews flagged the same tension: ADR-0022's graduation bar
reads "multiple real callers plus observed divergence", and a doc is
not a caller.

Decision: prose counts as a copy. The bar's purpose is evidence that
knowledge is genuinely shared and genuinely drifting; a doc restating a
shape or grammar drifts exactly like a dead constant does, and the fix
is the same — one owner, thin callers, docs that point at the owner
instead of restating it. `eval_schema.py`'s charter is accordingly all
eval knowledge: routing-case schema and coverage policy (ADR-0022),
output-eval record shape (#25), and the append-only results naming
grammar with its collision suffixing (#26). The boundary against
`protocol.py` is unchanged — eval knowledge vs pipeline-protocol
knowledge.

Provisional because it widens an accepted ADR's rule without an
operator decision; it hardens or reverts on the next charter question.
