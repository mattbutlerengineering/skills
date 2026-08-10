# Architecture Decision Records

Decisions live here as sequentially numbered ADRs (`0001-slug.md`). An ADR can
be a single paragraph; the value is recording the decision and its why. Don't
delete or rewrite an old ADR when a decision changes — write a new one that
supersedes it and update the old one's status line.

Statuses: **accepted** (explicitly confirmed), **provisional** (recommended
answer adopted while awaiting confirmation — pivot freely), **superseded by
ADR-NNNN** (fully retired — citing it is drift), **superseded in part by
ADR-NNNN**, and **amended by ADR-NNNN** (both partial: the decision stays live
and citable). The machine-readable authority is `ADR_STATUS` in
`tools/factory/gates.py`, which also allows a parenthesized annotation after
any head.

ADRs 0001–0006 were seeded by `factory-init` and record the decisions the
factory stamp made for this repo. They are yours now: supersede or amend them
like any other. Number 0007 onward for your own decisions.

> Detector D checks every ADR here has a valid status line and an index row
> below, and detector C checks that every `ADR-NNNN` token anywhere under
> `docs/` resolves to a file in this directory — so cite upstream project
> decisions by name or link, never by bare token.

## Index

| ADR | Decision | Status |
|-----|----------|--------|
| [0001](0001-decisions-are-recorded-here.md) | Decisions are recorded as ADRs | accepted |
| [0002](0002-artifacts-are-the-state.md) | Artifacts are the state | accepted |
| [0003](0003-soft-gating.md) | Soft gating: a missing predecessor offers a backfill | accepted |
| [0004](0004-tracker-is-a-one-way-mirror.md) | The issue tracker is a one-way mirror | accepted |
| [0005](0005-three-human-gates.md) | Three human gates | accepted |
| [0006](0006-work-orders-dispatch-from-breakdown-rows.md) | Work orders dispatch from breakdown rows | accepted |
