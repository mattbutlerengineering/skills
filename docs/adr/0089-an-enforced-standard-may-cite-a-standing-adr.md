# An enforced standard may cite a standing ADR

- Status: accepted (Owner, 2026-10-12)
- Date: 2026-10-12

The Owner chose this on 2026-10-12, in session. It resolves issue #763.

Detector K checks that every `enforced` entry in `docs/standards.json`
comes from an ADR that is still in force. The codex-style standards
enforcement run (`docs/features/codex-style-standards-enforcement/architecture.md`,
§3) set that test as "the status is exactly `accepted`". That is
stricter than how the rest of the factory reads an ADR. `adr_status`,
`review` and detector D all treat an ADR as live when it is accepted,
amended by a later ADR, or superseded only in part. So K refused
standards that every other reader considers in force. ADR-0032
("superseded in part by ADR-0083") is the worked case: its one-way
mirror standard could not be enforced. Neither could any standard from
an ADR that a later ADR amends, such as ADR-0085 or ADR-0087.

## Decision

Detector K accepts an enforced entry whose source ADR's
`knowledge_plane.standing` is `active` (accepted or amended) or
`partial` (superseded in part). A `provisional`, `retired` or
unrecognized source still fails K, and its problem string now ends
"(not in force)".

The enforceable standings are a single tuple in `gates.py`
(`ENFORCEABLE_STANDINGS`), read through the same
`knowledge_plane.adr_record` that detector D and `adr_status` use (#757).

## Consequences

- A partly superseded ADR's standard can be enforced without first
  restating it in a new ADR. The reviewer reads the citation knowing
  that only the superseded part is dead.
- A provisional ADR still cannot source an enforced standard: it was
  recorded without live confirmation.

## If rejected

Return K to `head == "accepted"`. Then any standard whose source ADR is
partly superseded or amended has to be restated in a new ADR before it
can be enforced.
